import asyncio
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from agents.planner import planner_agent
from agents.researcher import researcher_agent
from agents.writer import writer_agent

class Orchestrator:
    def __init__(self):
        self.session_service = InMemorySessionService()

    async def _execute_agent(self, agent, prompt: str, app_name: str) -> str:
        """Helper to execute a single agent run."""
        user_id = "user"
        session_id = f"session_{app_name}"
        
        # Ensure session exists
        try:
            await self.session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
        except Exception:
            # Session might already exist, which is fine
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
        Executes the Deep Research workflow: Plan -> Research -> Write.
        """
        print(f"[Orchestrator] Starting research on: {topic}")

        # 1. PLAN
        print("[Orchestrator] Phase 1: Planning...")
        plan_text = await self._execute_agent(planner_agent, topic, "planner_app")
        
        # Parse the plan (simple line splitting for Cycle 1)
        sub_questions = [line.strip().replace("- ", "") for line in plan_text.split("\n") if line.strip().startswith("-")]
        print(f"[Orchestrator] Generated Plan: {sub_questions}")

        if not sub_questions:
            print("[Orchestrator] Failed to generate a valid plan. Falling back to single query.")
            sub_questions = [topic]

        # 2. RESEARCH (Sequential for Cycle 1)
        print("[Orchestrator] Phase 2: Researching...")
        research_notes = []
        
        for i, question in enumerate(sub_questions):
            print(f"[Orchestrator] Researching sub-topic {i+1}/{len(sub_questions)}: {question}")
            note = await self._execute_agent(researcher_agent, question, f"researcher_app_{i}")
            research_notes.append(f"### Sub-topic: {question}\n{note}")

        # 3. WRITE
        print("[Orchestrator] Phase 3: Writing...")
        full_context = f"Original Topic: {topic}\n\nResearch Notes:\n" + "\n\n".join(research_notes)
        
        final_report = await self._execute_agent(writer_agent, full_context, "writer_app")
        
        return final_report
