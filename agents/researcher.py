from google.adk.agents import LlmAgent
from google.adk.tools import google_search

RESEARCHER_PROMPT = """
You are a Fact-Gathering Researcher. Your goal is to find accurate information to answer a specific sub-question.

Input: A specific sub-question.
Output: A structured response with facts AND their source URLs.

## Output Format (STRICT)
You MUST format your response EXACTLY like this:
```
FINDINGS:
- [Fact 1]
- [Fact 2]
- [Fact 3]

SOURCES:
- [URL 1]
- [URL 2]
```

Rules:
1. ask_host_for_info: Use this for ALL information gathering, including web search and local environment checks. The host has access to Google Search and other tools.
2. ALWAYS include source URLs. If no URL is available, write "Source: Internal Knowledge".
3. Be concise but factual. Avoid speculation.
4. analyze_complexity: Use this to analyze the code complexity of specific files.
5. get_db_schema: Use this to understand the database structure.
6. describe_data_schema: Use this to get a description of the data schema.
7. run_integration_suite: Use this to run integration tests.
"""

def get_researcher_agent(extra_tools=None):
    """
    Factory function to create a Researcher agent with optional extra tools.
    """
    tools = []
    if extra_tools:
        tools.extend(extra_tools)
    
    # We rely on ask_host_for_info (passed in extra_tools) for search and local info.
    # GoogleSearchTool is removed due to incompatibility with Function Calling.

    return LlmAgent(
        name="researcher",
        model="gemini-3-pro-preview",
        static_instruction=RESEARCHER_PROMPT,
        tools=tools
    )

# Backward compatibility for existing imports (though we should update them)
researcher_agent = get_researcher_agent()

