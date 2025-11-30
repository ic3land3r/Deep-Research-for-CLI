from fastmcp import Context
from typing import Optional, Dict, Any

async def safe_sampling_request(
    ctx: Context,
    prompt: str,
    max_tokens: int = 1000,
    system_prompt: Optional[str] = None,
    include_context: str = "none"
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

    try:
        # Send the request to the client (host)
        # Note: fastmcp Context.session.send_request is the low-level way to do this
        # We assume ctx.session is available and supports send_request
        result = await ctx.session.send_request("sampling/createMessage", params)
        
        # Parse the result
        # The expected format is: { "model": "...", "role": "assistant", "content": { "type": "text", "text": "..." } }
        # Or sometimes content is a list of objects.
        
        content = result.get("content")
        
        if isinstance(content, dict) and content.get("type") == "text":
             return content.get("text")
        elif isinstance(content, list):
             # Join all text parts
             return "".join([part.get("text", "") for part in content if part.get("type") == "text"])
        else:
             return str(content)

    except Exception as e:
        # Handle cases where the user denies the request or the host doesn't support sampling
        return f"Error during sampling: {str(e)}"
