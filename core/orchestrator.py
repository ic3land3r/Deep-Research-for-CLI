import asyncio
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from agents.planner import planner_agent
from agents.researcher import researcher_agent
from agents.writer import writer_agent

from core.memory import Memory

class Orchestrator:
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.memory = Memory()

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
        Executes the Deep Research workflow: Plan -> Research -> Write.
        """
        print(f"[Orchestrator] Starting research on: {topic}")
        self.memory.clear() # Ensure fresh memory for this run

        try:
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
            
            for i, question in enumerate(sub_questions):
                print(f"[Orchestrator] Researching sub-topic {i+1}/{len(sub_questions)}: {question}")
                note = await self._execute_agent(researcher_agent, question, f"researcher_app_{i}")
                
                # Store in Memory
                self.memory.add(note, metadata={"topic": question})
                print(f"[Orchestrator] Stored {len(note)} chars in memory.")

            # 3. WRITE
            print("[Orchestrator] Phase 3: Writing...")
            # Retrieve relevant context from memory (or all of it if we just want to dump)
            # For Cycle 2, let's query the memory for the original topic to get the most relevant chunks,
            # OR just dump everything if it fits. Let's try a hybrid: Query for each sub-question again?
            # Simpler: Just dump all documents since we have a small number of sub-questions.
            # But `memory.query` is the feature we want to test.
            # Let's query for the main topic.
            
            # Actually, to prove Memory works, let's query for the *original topic* and see what comes back.
            # But since we just put everything in, maybe we should just retrieve all?
            # Chroma doesn't have a "get all" easily without ID tracking.
            # So let's just query for the topic.
            relevant_context = self.memory.query(topic, n_results=10) # Get top 10 chunks
            full_context = f"Original Topic: {topic}\n\nResearch Notes (from Memory):\n" + "\n\n".join(relevant_context)
            
            final_report = await self._execute_agent(writer_agent, full_context, "writer_app")
            
            return final_report
        finally:
            self.memory.clear() # Wipe memory after run

