import asyncio
import re
import sys
from typing import Optional
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from agents.planner import planner_agent
from agents.intent_extractor import intent_extractor_agent
from agents.researcher import get_researcher_agent
from agents.writer import get_writer_agent
from agents.reviewer import reviewer_agent
from agents.managed_researcher import get_managed_researcher

from core.memory import Memory

from utils.host_tools import create_ask_host_tool
from utils.tool_router import augment_prompt_with_routing, detect_domain
from utils.finance_tools import create_finance_tool
from utils.academic_tools import create_arxiv_tool, create_openalex_tool
from utils.macro_news_tools import create_world_bank_tool, create_news_rss_tool

def extract_sources_from_researcher_output(text: str) -> list[str]:
    """Parses researcher output to extract source URLs."""
    sources = []
    sources_match = re.search(r'SOURCES:\s*([\s\S]*?)(?:$|(?=\n\n))', text, re.IGNORECASE)
    if sources_match:
        sources_section = sources_match.group(1)
        urls = re.findall(r'https?://[^\s\)\]]+', sources_section)
        sources.extend(urls)
    
    inline_urls = re.findall(r'https?://[^\s\)\]]+', text)
    for url in inline_urls:
        if url not in sources:
            sources.append(url)
    
    return sources if sources else ["internal://research-notes"]

class Orchestrator:
    def __init__(self, ctx=None, mode: str = "hybrid", output_format: str = "markdown", local_intensity: str = "standard"):
        self.session_service = InMemorySessionService()
        self.memory = Memory()
        self.ctx = ctx
        self.mode = mode 
        self.output_format = output_format
        self.local_intensity = local_intensity
        self.managed_agent = get_managed_researcher()

    async def _execute_agent(self, agent, prompt: str, app_name: str) -> str:
        """Helper to execute a single agent run."""
        user_id = "user"
        session_id = f"session_{app_name}"
        
        try:
            await self.session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
        except Exception:
            pass

        runner = Runner(agent=agent, session_service=self.session_service, app_name=app_name)
        
        response_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=prompt)])
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text
        return response_text

    async def run(self, topic: str) -> str:
        """Executes the Deep Research workflow with Hybrid Routing."""
        from datetime import datetime
        
        current_date = datetime.now().strftime("%B %d, %Y")
        topic_with_context = f"[CURRENT DATE: {current_date}] {topic}"
        
        sys.stderr.write(f"[Orchestrator] Starting research on: {topic} (mode={self.mode})\n")
        
        self.memory.clear() 

        try:
            # DEEP MODE: Delegate entirely to Managed Agent
            if self.mode == "deep":
                sys.stderr.write("[Orchestrator] DEEP MODE: Delegating entire task to Managed Agent.\n")
                result = await self.managed_agent.execute(topic)
                
                if self.output_format.lower() == "json":
                    sys.stderr.write("[Orchestrator] Formatting Managed output to JSON...\n")
                    dummy_context = f"Topic: {topic}\n\nManaged Research Report:\n{result}"
                    json_result = await self._execute_agent(get_writer_agent("json"), dummy_context, "writer_formatter")
                    return json_result
                return result

            # PLANNING PHASE
            sub_questions = [topic_with_context]
            if self.mode != "quick":
                sys.stderr.write("[Orchestrator] Phase 1: Planning...\n")
                refined_goal = await self._execute_agent(intent_extractor_agent, topic_with_context, "intent_extractor_app")
                
                planner_input = f"[CURRENT DATE: {current_date}] {refined_goal}"
                plan_text = await self._execute_agent(planner_agent, planner_input, "planner_app")
                
                sub_questions = []
                try:
                    import json
                    plan_data = json.loads(plan_text)
                    if isinstance(plan_data, dict) and "sub_questions" in plan_data:
                        sub_questions = plan_data["sub_questions"]
                except Exception:
                    for line in plan_text.split("\n"):
                        match = re.match(r'^(?:[-*]|\d+\.)\s+(.+)$', line.strip())
                        if match: sub_questions.append(match.group(1).strip())
                
                if not sub_questions: sub_questions = [topic]

            # EXECUTION PHASE (Hybrid Routing)
            sys.stderr.write("[Orchestrator] Phase 2: Execution (Hybrid Routing)...\n")
            
            async def research_task(index, question):
                router_result = detect_domain(question)
                execution_mode = "local"
                
                if self.mode == "hybrid":
                    if router_result:
                         execution_mode = router_result.get("execution_mode", "local")
                elif self.mode == "standard" or self.mode == "quick":
                    execution_mode = "local"
                
                sys.stderr.write(f"[Orchestrator] Task {index+1}: '{question[:30]}...' -> Mode: {execution_mode}\n")
                
                note = ""
                source_used = "internal"
                
                if execution_mode == "managed":
                    note = await self.managed_agent.execute(question)
                    source_used = "managed-deep-research"
                else:
                    extra_tools = []
                    if self.ctx: extra_tools.append(create_ask_host_tool(self.ctx))
                    
                    if router_result:
                        domain = router_result.get("domain")
                        if domain in ("finance_simple", "finance_complex", "finance"):
                            extra_tools.append(create_finance_tool())
                        elif domain == "science":
                            extra_tools.append(create_arxiv_tool())
                            extra_tools.append(create_openalex_tool())
                        elif domain in ("government", "realtime"):
                            extra_tools.append(create_world_bank_tool())
                            extra_tools.append(create_news_rss_tool())

                    agent = get_researcher_agent(extra_tools=extra_tools)
                    augmented_q = augment_prompt_with_routing(question)
                    
                    note = await self._execute_agent(agent, augmented_q, f"res_{index}")
                    
                    # Escalation check
                    if len(note) < 300 and self.mode == "hybrid":
                        sys.stderr.write(f"[Orchestrator] WARNING: Local result thin ({len(note)} chars). ESCALATING to Managed Agent.\n")
                        note = await self.managed_agent.execute(question)
                        source_used = "managed-escalation"
                    
                    sources = extract_sources_from_researcher_output(note)
                    source_used = sources[0] if sources else "local"

                self.memory.add(text=note, source_url=source_used, topic=question)
                return note

            await asyncio.gather(*[research_task(i, q) for i, q in enumerate(sub_questions)])

            # WRITING PHASE
            sys.stderr.write("[Orchestrator] Phase 3: Writing...\n")
            memory_chunks = self.memory.query(topic, n_results=15)
            
            context_str = "\n".join([f"Source: {c.source_url}\nContent:\n{c.text or ''}" for c in memory_chunks])
            
            draft_report = await self._execute_agent(
                get_writer_agent(self.output_format),
                f"Topic: {topic}\n\nContext:\n{context_str}", 
                "writer_app"
            )
            
            # REVIEW PHASE
            if self.mode != "quick":
                sys.stderr.write("[Orchestrator] Phase 4: Reviewing...\n")
                review = await self._execute_agent(reviewer_agent, f"Review:\n{draft_report}", "reviewer")
                
                if "FAIL" in review:
                    sys.stderr.write("[Orchestrator] Review FAILED. Escalating to Managed Agent for verification.\n")
                    if self.mode in ("hybrid", "standard"):
                         final_report = await self.managed_agent.execute(f"Verify and rewrite this report on {topic}. The draft had issues: {review}. \nDraft:\n{draft_report}")
                         if self.output_format == "json":
                             final_report = await self._execute_agent(get_writer_agent("json"), f"Convert to JSON:\n{final_report}", "fmt")
                         return final_report
                    else:
                        return draft_report
                        
            return draft_report

        finally:
            self.memory.clear()
