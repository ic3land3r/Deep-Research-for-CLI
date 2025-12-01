import asyncio
from core.orchestrator import Orchestrator
from utils.host_tools import create_ask_host_tool

# Mock Context
class MockSession:
    async def send_request(self, method, params):
        print(f"Mock sending request: {method} with params {params}")
        if method == "sampling/createMessage":
            return {"content": {"type": "text", "text": "Mocked Host Info: Ubuntu 22.04"}}
        return None

class MockContext:
    def __init__(self):
        self.session = MockSession()
        self.request_id = "test-id"

async def test_host_query_injection():
    print("Testing Host Query Tool Injection...")
    ctx = MockContext()
    
    # Create orchestrator with context
    orchestrator = Orchestrator(ctx=ctx)
    
    # Verify tool creation
    tool = create_ask_host_tool(ctx)
    assert callable(tool)
    print("Tool creation: PASS")
    
    # Verify tool execution
    print("Executing tool...")
    result = await tool("What OS is this?")
    print(f"Tool result: {result}")
    assert "Mocked Host Info" in result
    print("Tool execution: PASS")
    
    # Verify Orchestrator has context
    assert orchestrator.ctx == ctx
    print("Orchestrator context injection: PASS")

if __name__ == "__main__":
    asyncio.run(test_host_query_injection())
