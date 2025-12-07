from google.adk.agents import LlmAgent
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

class ResearchPlan(BaseModel):
    """Structured output schema for the Research Planner."""
    sub_questions: List[str] = Field(
        description="List of 3-5 specific, search-friendly sub-questions to research"
    )

PLANNER_PROMPT = """
You are a Research Planner. Your goal is to decompose a complex user query into a structured research plan.

Input: A complex topic or question.
Output: A JSON object with a "sub_questions" array containing specific, search-friendly questions.

Rules:
1. Break down the topic into 3-5 distinct sub-aspects (e.g., History, Current State, Challenges, Future Outlook).
2. Each sub-question must be self-contained and suitable for a Google Search.
3. Do not answer the question yourself. Only plan.
"""

planner_agent = LlmAgent(
    name="planner",
    model="gemini-3-pro-preview",
    static_instruction=PLANNER_PROMPT,
    output_schema=ResearchPlan
)

