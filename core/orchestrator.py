import asyncio
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from agents.planner import planner_agent
from agents.planner import planner_agent
from agents.researcher import get_researcher_agent
from agents.writer import writer_agent
from agents.writer import writer_agent
from agents.reviewer import reviewer_agent

from core.memory import Memory

from utils.host_tools import create_ask_host_tool

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

            # 2. RESEARCH (Parallel for Cycle 3)
            sys.stderr.write("[Orchestrator] Phase 2: Researching (Parallel)...\n")
            
            # Define a helper for parallel execution
            async def research_task(index, question):
                print(f"[Orchestrator] Starting research on sub-topic {index+1}: {question}")
            async def research_task(index, question):
                sys.stderr.write(f"[Orchestrator] Starting research on sub-topic {index+1}: {question}\n")
                
                # Create a researcher agent with access to the host tool if context is available
                extra_tools = []
                if self.ctx:
                    extra_tools.append(create_ask_host_tool(self.ctx))
                
                agent = get_researcher_agent(extra_tools=extra_tools)
                
                note = await self._execute_agent(agent, question, f"researcher_app_{index}")
                self.memory.add(note, metadata={"topic": question})
                sys.stderr.write(f"[Orchestrator] Finished sub-topic {index+1}. Stored {len(note)} chars.\n")
                return f"### Sub-topic: {question}\n{note}"

            # Execute all tasks concurrently
            await asyncio.gather(*[
                research_task(i, q) for i, q in enumerate(sub_questions)
            ])

            # 3. WRITE
            sys.stderr.write("[Orchestrator] Phase 3: Writing...\n")
            relevant_context = self.memory.query(topic, n_results=10)
            full_context = f"Original Topic: {topic}\n\nResearch Notes (from Memory):\n" + "\n\n".join(relevant_context)
            
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
