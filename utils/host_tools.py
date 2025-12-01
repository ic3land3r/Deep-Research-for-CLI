from fastmcp import Context
from google.adk.tools import BaseTool
from utils.sampling import safe_sampling_request
from google.genai import types
from typing import Optional

from google.adk.tools.tool_context import ToolContext

class AskHostTool(BaseTool):
    def __init__(self, ctx: Context):
        super().__init__(
            name="ask_host_for_info",
            description="Asks the user (via the Gemini CLI host) for specific information needed for the research. Use this to get information about the local environment, OS, hardware, OR to perform Google Searches via the host's capabilities."
        )
        self.ctx = ctx

    async def run_async(self, *, args: dict, tool_context: Optional[ToolContext] = None) -> str:
        question = args.get("question")
        if not question:
            return "Error: No question provided."

        prompt = f"The research agent needs information from you/the host environment:\n\n{question}\n\nPlease provide this information so the research can continue."
        
        # We use 'includeContext="none"' to avoid confusing the model with the agent's internal monologue
        response = await safe_sampling_request(
            self.ctx, 
            prompt, 
            max_tokens=2000, 
            system_prompt="You are an intelligent host agent. Use your tools (like terminal) to find the requested information if possible, or ask the user.",
            include_context="none"
        )
        return response

    def _get_declaration(self) -> Optional[types.FunctionDeclaration]:
        # Debug logging removed to prevent stdout pollution
        pass
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "question": types.Schema(
                        type=types.Type.STRING,
                        description="The question to ask the host/user."
                    )
                },
                required=["question"]
            )
        )



def create_ask_host_tool(ctx: Context) -> AskHostTool:
    """
    Creates a tool that allows the agent to ask the host (Gemini CLI) for information.
    Returns an instance of AskHostTool (which inherits from BaseTool).
    """
    return AskHostTool(ctx)
