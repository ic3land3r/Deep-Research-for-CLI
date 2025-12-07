from fastmcp import Context
from typing import Optional, Dict, Any
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
    
    # Construct the message payload
    messages = [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": prompt
            }
        }
    ]
    
    # Build the sampling parameters
    params = {
        "messages": messages,
        "maxTokens": max_tokens,
        "includeContext": include_context
    }
    
    if system_prompt:
        params["systemPrompt"] = system_prompt

    last_error = None
    for attempt in range(retries):
        try:
            # Send the request to the client (host)
            result = await ctx.session.send_request("sampling/createMessage", params)
            
            # Handle pydantic models vs dicts
            if hasattr(result, 'model_dump'):
                result = result.model_dump()
            elif hasattr(result, '__dict__'):
                result = vars(result)
            
            # Parse the result
            content = result.get("content") if isinstance(result, dict) else None
            
            if content is None:
                # Try direct text extraction
                if isinstance(result, str):
                    return result
                return str(result)
            
            if isinstance(content, dict) and content.get("type") == "text":
                 return content.get("text", "")
            elif isinstance(content, list):
                 # Join all text parts
                 return "".join([part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"])
            elif isinstance(content, str):
                 return content
            else:
                 return str(content)

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

