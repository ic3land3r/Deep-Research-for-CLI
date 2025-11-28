from fastmcp import FastMCP
from core.orchestrator import Orchestrator

# Initialize FastMCP server
mcp = FastMCP("Deep Research")

@mcp.tool()
async def perform_deep_research(topic: str) -> str:
    """
    Performs a deep, multi-step research on a given topic using Gemini 3.0 Pro.
    
    Args:
        topic: The research topic or question.
    """
    try:
        orchestrator = Orchestrator()
        result = await orchestrator.run(topic)
        return result
    except Exception as e:
        return f"Research failed due to error: {str(e)}"

if __name__ == "__main__":
    # Runs the server over stdio (standard input/output), which Gemini CLI uses
    mcp.run()
