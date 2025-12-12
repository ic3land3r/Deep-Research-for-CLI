import os
import time
import sys
import asyncio
from google import genai
from google.genai import types

class GoogleDeepResearchClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            # We don't raise immediately to allow instantiation for testing,
            # but execution will fail.
            pass

        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    async def execute(self, topic: str, output_format: str = None) -> str:
        """
        Executes a deep research task using the Google Deep Research Agent.

        Args:
            topic: The research query.
            output_format: Optional formatting instructions.

        Returns:
            The final research report as a string.
        """
        if not self.client:
            raise ValueError("GOOGLE_API_KEY not found in environment")

        agent_name = 'deep-research-pro-preview-12-2025'

        prompt = topic
        if output_format and output_format != "markdown":
            prompt += f"\n\nFormat the output as follows: {output_format}"

        sys.stderr.write(f"[GoogleDeepResearch] Starting interaction for: {topic[:50]}...\n")

        try:
            # Start the interaction in background mode
            # We run this in a thread executor because the synchronous client might block,
            # but `google-genai` is often async-compatible or has async methods.
            # Looking at docs: `client.interactions.create` seems synchronous in the examples unless using `stream`.
            # However, the user provided examples show `import time` and polling loops.
            # Ideally we'd use the async client if available, but for now we'll wrap blocking calls if needed.
            # The `google-genai` V1 SDK often has `client.aio` for async.
            # Let's check if we can use `client.aio`.

            # Use async client if available in this SDK version
            # If `client.interactions` is standard, we assume synchronous for now based on user examples.
            # To avoid blocking the event loop, we should run this in a thread.

            loop = asyncio.get_running_loop()

            # 1. Start Interaction
            interaction = await loop.run_in_executor(
                None,
                lambda: self.client.interactions.create(
                    input=prompt,
                    agent=agent_name,
                    background=True
                )
            )

            interaction_id = interaction.id
            sys.stderr.write(f"[GoogleDeepResearch] Interaction started: {interaction_id}\n")

            # 2. Polling Loop
            while True:
                # Poll status
                interaction_result = await loop.run_in_executor(
                    None,
                    lambda: self.client.interactions.get(id=interaction_id)
                )

                status = interaction_result.status

                if status == "completed":
                    outputs = interaction_result.outputs
                    if outputs:
                        return outputs[-1].text
                    else:
                        return "Research completed but returned no output."

                elif status == "failed":
                    error_msg = getattr(interaction_result, 'error', 'Unknown error')
                    raise RuntimeError(f"Google Deep Research failed: {error_msg}")

                # Wait before polling again
                await asyncio.sleep(10)

        except Exception as e:
            sys.stderr.write(f"[GoogleDeepResearch] Error: {e}\n")
            raise e
