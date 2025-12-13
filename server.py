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
    mode: str = "hybrid",  # Default changed to hybrid for best experience
    output_format: str = "markdown",
    local_intensity: str = "standard"
) -> str:
    """
    Performs a deep, multi-step research on a given topic using Hybrid Intelligence.
    
    Args:
        ctx: The FastMCP context.
        topic: The research topic or question.
        mode: Research mode - "hybrid" (smart routing), "quick" (local fast), "standard" (local thorough), or "deep" (managed agent).
        output_format: Output format - "markdown" (default report), "json" (structured JSON), or a custom format instruction.
        local_intensity: For hybrid/local modes, controls depth: "simple" (fast tools) or "standard" (plan+review).
    """
    # Validate mode
    valid_modes = ["quick", "standard", "deep", "hybrid"]
    if mode not in valid_modes:
        return f"Invalid mode '{mode}'. Must be one of: {valid_modes}"
    
    try:
        orchestrator = Orchestrator(
            ctx=ctx, 
            mode=mode, 
            output_format=output_format,
            local_intensity=local_intensity
        )
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
