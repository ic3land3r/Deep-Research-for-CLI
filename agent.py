import os
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.tools import google_search

# Ensure you have GOOGLE_API_KEY set in your environment
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY environment variable is required")

# 1. Define the System Prompt
# We instruct the agent to be exhaustive, mimicking "Deep Research" behavior.
RESEARCH_SYSTEM_PROMPT = """
You are a Deep Research Specialist. Your goal is to provide exhaustive, citation-backed answers.
When you receive a query:
1. Break it down into sub-questions.
2. Use the Google Search tool multiple times to gather diverse perspectives.
3. Read the search snippets carefully.
4. Synthesize a final comprehensive report with citations.
Do not answer from memory if the topic is current; always verify with search.
"""

# 2. Initialize the Search Tool
# ADK provides a native wrapper for Google Search
search_tool = google_search

# 3. Create the Agent
# We use the specific Gemini 3.0 Pro Preview model ID
research_agent = LlmAgent(
    name="deep_researcher",
    model="gemini-3-pro-preview",  # Valid model ID for Gemini 3.0
    static_instruction=RESEARCH_SYSTEM_PROMPT,
    tools=[search_tool]
)

async def run_research(topic: str) -> str:
    """
    Runs the deep research agent on the given topic.
    """
    session_service = InMemorySessionService()
    runner = Runner(
        agent=research_agent, # Changed from deep_researcher to research_agent
        app_name="deep-research",
        session_service=session_service
    )

    user_id = "user"
    session_id = "session"
    
    # Create a new session
    await session_service.create_session(
        app_name="deep-research",
        user_id=user_id,
        session_id=session_id
    )

    response_text = ""
    
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=topic)])
    ):
        # Collect the text content from the agent's response events
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
    
    return response_text

if __name__ == "__main__":
    import asyncio
    # Simple test
    try:
        result = asyncio.run(run_research("What is the current state of solid state batteries?"))
        print(result)
    except Exception as e:
        print(f"Error: {e}")
