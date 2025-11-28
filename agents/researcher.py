from google.adk.agents import LlmAgent
from google.adk.tools import google_search

RESEARCHER_PROMPT = """
You are a Fact-Gathering Researcher. Your goal is to find accurate information to answer a specific sub-question.

Input: A specific sub-question.
Output: A concise summary of the facts found, with citations if possible.

Rules:
1.  Use the Google Search tool to find information.
2.  Synthesize the search results into a clear, factual summary.
3.  If you cannot find information, state that clearly.
4.  Focus on "hard facts" (dates, numbers, names, events).
"""

researcher_agent = LlmAgent(
    name="researcher",
    model="gemini-3-pro-preview",
    static_instruction=RESEARCHER_PROMPT,
    tools=[google_search]
)
