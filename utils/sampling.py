from fastmcp import Context
from mcp.types import SamplingMessage, TextContent as MCPTextContent
from typing import Optional
import asyncio
import sys

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds

async def safe_sampling_request(
    ctx: Context,
    prompt: str,
    max_tokens: int = 1000,
    system_prompt: Optional[str] = None,
    include_context: str = "none",
    retries: int = MAX_RETRIES
) -> str:
    """
    Sends a sampling request to the host (Gemini CLI or Antigravity) to perform recursive reasoning.
    
    Args:
        ctx: The FastMCP context.
        prompt: The user prompt to send to the model.
        max_tokens: The maximum number of tokens to generate.
        system_prompt: Optional system prompt to guide the model.
        include_context: How much context to include ("none", "thisServer", "all"). 
                         Defaults to "none" to prevent infinite loops.
                         
    Returns:
        The generated text from the model.
    """

    # Construct messages using proper MCP types (not raw dicts or strings)
    messages = [
        SamplingMessage(
            role="user",
            content=MCPTextContent(type="text", text=prompt)
        )
    ]

    last_error = None
    for attempt in range(retries):
        try:
            # Use session.create_message for sampling
            result = await ctx.session.create_message(
                messages=messages,
                max_tokens=max_tokens,
                system_prompt=system_prompt
            )
            
            # result.content is a LIST of content objects - must index into it
            if hasattr(result, 'content'):
                content = result.content
                # Handle list of content objects
                if isinstance(content, list) and len(content) > 0:
                    first_content = content[0]
                    if hasattr(first_content, 'text'):
                        return first_content.text
                    return str(first_content)
                # Handle single content object
                elif hasattr(content, 'text'):
                    return content.text
                else:
                    return str(content)
            
            return str(result)

        except (ConnectionError, TimeoutError, asyncio.TimeoutError) as e:
            # Transient errors - retry with backoff
            last_error = e
            backoff = INITIAL_BACKOFF * (2 ** attempt)
            sys.stderr.write(f"[Sampling] Attempt {attempt+1}/{retries} failed: {e}. Retrying in {backoff}s...\n")
            await asyncio.sleep(backoff)
        except Exception as e:
            # Non-transient errors - fail immediately
            sys.stderr.write(f"[Sampling Error] {str(e)}\n")
            return f"Error during sampling: {str(e)}"
    
    # All retries exhausted
    sys.stderr.write(f"[Sampling] All {retries} attempts failed. Last error: {last_error}\n")
    return f"Error during sampling after {retries} attempts: {str(last_error)}"


