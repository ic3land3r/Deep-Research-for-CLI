from google.adk.agents import LlmAgent

WRITER_PROMPT = """
    *   **Conclusion**: A brief wrap-up.
4.  **Audience**: The output will be displayed in a CLI, so keep it readable and structured.
"""

writer_agent = LlmAgent(
    name="writer",
    model="gemini-3-pro-preview",
    static_instruction=WRITER_PROMPT
)
