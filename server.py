from fastmcp import FastMCP, Context
from core.orchestrator import Orchestrator
import sys
import asyncio

# Initialize FastMCP server
mcp = FastMCP("Deep Research")

@mcp.tool()
async def perform_deep_research(
    ctx: Context, 
    topic: str, 
    mode: str = "standard",
    output_format: str = "markdown"
) -> str:
    """
    Performs a deep, multi-step research on a given topic using Gemini 3.0 Pro.
    
    Args:
        ctx: The FastMCP context.
        topic: The research topic or question.
        mode: Research mode - "quick" (fast, grounded search), "standard" (balanced), or "deep" (thorough, forced deep dive).
        output_format: Output format - "markdown" (default report), "json" (structured JSON), or a custom format instruction like "json with schema: {title: str, summary: str, facts: list}".
    """
    # Validate mode
    valid_modes = ["quick", "standard", "deep"]
    if mode not in valid_modes:
        return f"Invalid mode '{mode}'. Must be one of: {valid_modes}"
    
    try:
        orchestrator = Orchestrator(ctx=ctx, mode=mode, output_format=output_format)
        result = await orchestrator.run(topic)
        return result
    except (ConnectionError, TimeoutError, asyncio.TimeoutError) as e:
        sys.stderr.write(f"[Deep Research] Network error: {type(e).__name__}: {e}\n")
        return f"Research failed due to network error: {type(e).__name__}. Please retry."
    except ValueError as e:
        sys.stderr.write(f"[Deep Research] Parsing/validation error: {e}\n")
        return f"Research failed due to parsing error: {str(e)}"
    except Exception as e:
        sys.stderr.write(f"[Deep Research] Unexpected error: {type(e).__name__}: {e}\n")
        return f"Research failed: {type(e).__name__}: {str(e)}"

if __name__ == "__main__":
    # Runs the server over stdio (standard input/output), which Gemini CLI uses
    mcp.run()
