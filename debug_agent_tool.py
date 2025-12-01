import asyncio
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool, google_search
import os
from dotenv import load_dotenv
from utils.host_tools import create_ask_host_tool

load_dotenv()

# Mock Context
class MockSession:
    async def send_request(self, method, params):
        return {"content": {"type": "text", "text": "Mocked Host Info"}}

class MockContext:
    def __init__(self):
        self.session = MockSession()
        self.request_id = "test-id"

async def debug_agent():
    print("Debugging LlmAgent with Google Search (Wrapper Approach)...")
    ctx = MockContext()
    host_tool_instance = create_ask_host_tool(ctx)
    
    # Create agent
    agent = LlmAgent(
        name="debug_researcher",
        model="gemini-3-pro-preview",
        static_instruction="You are a researcher. Use ask_host_for_info for all queries.",
        tools=[host_tool_instance]
    )
    
    print(f"Agent tools: {agent.tools}")

    # Run the agent
    session_service = InMemorySessionService()
    await session_service.create_session(app_name="debug_app", user_id="user", session_id="session_1")
    runner = Runner(agent=agent, session_service=session_service, app_name="debug_app")
    
    print("Sending message...")
    try:
        async for event in runner.run_async(
            user_id="user",
            session_id="session_1",
            new_message=types.Content(role="user", parts=[types.Part(text="What is the latest version of Python?")])
        ):
            print(f"Event: {event}")
    except Exception as e:
        print(f"Caught exception: {e}")

if __name__ == "__main__":
    asyncio.run(debug_agent())
