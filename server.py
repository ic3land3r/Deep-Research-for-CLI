from fastmcp import FastMCP
from agent import run_research

# Initialize the MCP Server
mcp = FastMCP("Gemini 3.0 Deep Research Agent")

@mcp.tool()
async def perform_deep_research(topic: str) -> str:
    """
    Performs deep, multi-step research on a complex topic using a Gemini 3.0 agent.
    Use this tool when the user asks for a "report", "deep dive", or "comprehensive analysis".
    
    Args:
        topic: The research query or topic to investigate.
    """
    try:
        # Delegate execution to the ADK agent
        result = await run_research(topic)
        return result
    except Exception as e:
        return f"Research failed due to error: {str(e)}"

if __name__ == "__main__":
    # Runs the server over stdio (standard input/output), which Gemini CLI uses
    mcp.run()
