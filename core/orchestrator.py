import asyncio
import re
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from agents.planner import planner_agent
from agents.researcher import get_researcher_agent
from agents.writer import writer_agent
from agents.reviewer import reviewer_agent

from core.memory import Memory

from utils.host_tools import create_ask_host_tool
from utils.tool_router import augment_prompt_with_routing

def extract_sources_from_researcher_output(text: str) -> list[str]:
    """Parses researcher output to extract source URLs."""
    sources = []
    # Look for SOURCES: section
    sources_match = re.search(r'SOURCES:\s*([\s\S]*?)(?:$|(?=\n\n))', text, re.IGNORECASE)
    if sources_match:
        sources_section = sources_match.group(1)
        # Extract URLs from the section
        urls = re.findall(r'https?://[^\s\)\]]+', sources_section)
        sources.extend(urls)
    
    # Also look for inline URLs throughout the text
    inline_urls = re.findall(r'https?://[^\s\)\]]+', text)
    for url in inline_urls:
        if url not in sources:
            sources.append(url)
    
    return sources if sources else ["internal://research-notes"]

class Orchestrator:
    def __init__(self, ctx=None):
        self.session_service = InMemorySessionService()
        self.memory = Memory()
        self.ctx = ctx

    async def _execute_agent(self, agent, prompt: str, app_name: str) -> str:
        """Helper to execute a single agent run."""
        user_id = "user"
        session_id = f"session_{app_name}"
        
        # Ensure session exists
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
        """
        Executes the Deep Research workflow: Plan -> Research -> Write -> Review.
        """
        import sys
        sys.stderr.write(f"[Orchestrator] Starting research on: {topic}\n")
        self.memory.clear() # Ensure fresh memory for this run

        try:
            # 1. PLAN
            sys.stderr.write("[Orchestrator] Phase 1: Planning...\n")
            plan_text = await self._execute_agent(planner_agent, topic, "planner_app")
            
            # Parse the plan (simple line splitting for Cycle 1)
            sub_questions = [line.strip().replace("- ", "") for line in plan_text.split("\n") if line.strip().startswith("-")]
            sys.stderr.write(f"[Orchestrator] Generated Plan: {sub_questions}\n")

            if not sub_questions:
                sys.stderr.write("[Orchestrator] Failed to generate a valid plan. Falling back to single query.\n")
                sub_questions = [topic]

            # 2. RESEARCH (Parallel with Deep Dive for thin answers)
            sys.stderr.write("[Orchestrator] Phase 2: Researching (Parallel with Deep Dive)...\n")
            
            # Configuration for Deep Dive (HYBRID: char count + fact density)
            MIN_CHARS_THRESHOLD = 300  # Raised threshold
            MIN_FACTS_THRESHOLD = 3    # Minimum bullet points, stats, or URLs
            MAX_DEEP_DIVE_DEPTH = 1    # Maximum recursion depth
            
            def count_facts(text: str) -> int:
                """Count substantive facts in researcher output."""
                import re
                bullets = len(re.findall(r'^[\s]*[-*•]\s', text, re.MULTILINE))  # Bullet points
                stats = len(re.findall(r'\d+(?:\.\d+)?%|\$[\d,]+(?:\.\d+)?[BMK]?|\d{4}', text))  # Percentages, money, years
                urls = len(re.findall(r'https?://', text))  # URLs
                return bullets + stats + urls
            
            def is_thin_answer(text: str) -> bool:
                """Determine if answer lacks substance (hybrid metric)."""
                char_count = len(text)
                fact_count = count_facts(text)
                is_thin = char_count < MIN_CHARS_THRESHOLD or fact_count < MIN_FACTS_THRESHOLD
                return is_thin, char_count, fact_count
            
            # Define a helper for parallel execution with deep dive
            async def research_task(index, question, depth=0):
                sys.stderr.write(f"[Orchestrator] Research sub-topic {index+1} (depth {depth}): {question}\n")
                
                # Create a researcher agent with access to the host tool if context is available
                extra_tools = []
                if self.ctx:
                    extra_tools.append(create_ask_host_tool(self.ctx))
                
                agent = get_researcher_agent(extra_tools=extra_tools)
                
                # IMPROVEMENT C: Augment question with domain-specific routing hints
                augmented_question = augment_prompt_with_routing(question)
                
                note = await self._execute_agent(agent, augmented_question, f"researcher_app_{index}_d{depth}")
                
                # Deep Dive: Check if answer is "thin" using HYBRID metric
                thin, chars, facts = is_thin_answer(note)
                if thin and depth < MAX_DEEP_DIVE_DEPTH:
                    sys.stderr.write(f"[Orchestrator] DEEP DIVE triggered for '{question}' (chars={chars}, facts={facts})\n")
                    
                    # Generate a more specific follow-up question
                    follow_up = f"Provide MORE DETAILED information about: {question}. Include specific facts, data, and statistics."
                    deep_note = await self._execute_agent(agent, follow_up, f"researcher_app_{index}_deep")
                    note = f"{note}\n\n[DEEP DIVE EXPANSION]\n{deep_note}"
                
                # Extract sources from the researcher's output
                sources = extract_sources_from_researcher_output(note)
                primary_source = sources[0] if sources else "internal://research-notes"
                
                # Store with source URL tracking
                self.memory.add(
                    text=note,
                    source_url=primary_source,
                    topic=question
                )
                sys.stderr.write(f"[Orchestrator] Finished sub-topic {index+1}. Stored {len(note)} chars. Source: {primary_source}\n")
                return f"### Sub-topic: {question}\n{note}"

            # Execute all tasks concurrently
            await asyncio.gather(*[
                research_task(i, q) for i, q in enumerate(sub_questions)
            ])

            # 3. WRITE
            sys.stderr.write("[Orchestrator] Phase 3: Writing...\n")
            memory_chunks = self.memory.query(topic, n_results=10)
            
            # Build context with explicit source citations
            context_parts = [f"Original Topic: {topic}\n\nResearch Notes (with Sources):"]
            for chunk in memory_chunks:
                context_parts.append(f"\n---\nTopic: {chunk.topic}\nSource URL: {chunk.source_url}\nContent:\n{chunk.text}")
            
            full_context = "\n".join(context_parts)
            
            draft_report = await self._execute_agent(writer_agent, full_context, "writer_app")
            
            # 4. REVIEW (Feedback Loop)
            sys.stderr.write("[Orchestrator] Phase 4: Reviewing...\n")
            
            review_prompt = f"""
            Review the following report for accuracy and completeness based on the topic '{topic}'.
            Report:
            {draft_report}
            """
            review_result = await self._execute_agent(reviewer_agent, review_prompt, "reviewer_app")
            
            if "FAIL" in review_result:
                sys.stderr.write("[Orchestrator] Review failed. Revising...\n")
                sys.stderr.write(f"[Orchestrator] Feedback: {review_result}\n")
                
                revision_prompt = f"""
                The previous draft was rejected.
                Feedback: {review_result}
                
                Please rewrite the report to address this feedback.
                Original Context:
                {full_context}
                """
                final_report = await self._execute_agent(writer_agent, revision_prompt, "writer_app_revision")
            else:
                sys.stderr.write("[Orchestrator] Review passed.\n")
                final_report = draft_report
            
            return final_report
        finally:
            self.memory.clear() # Wipe memory after run

