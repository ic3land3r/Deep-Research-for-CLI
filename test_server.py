import asyncio
from fastmcp import Context
from server import analyze_complexity, get_db_schema, run_integration_suite, describe_data_schema

# Mock Context
class MockSession:
    async def send_request(self, method, params):
        print(f"Mock sending request: {method} with params {params}")
        if method == "sampling/createMessage":
            return {"content": {"type": "text", "text": "Mocked Analysis: Code is simple."}}
        return None

class MockContext:
    def __init__(self):
        self.session = MockSession()
        self.request_id = "test-id"

async def test_tools():
    print("Testing get_db_schema...")
    schema = get_db_schema.fn()
    assert "CREATE TABLE users" in schema
    print("PASS")

    print("Testing describe_data_schema...")
    desc = describe_data_schema.fn()
    assert "CREATE TABLE users" in desc
    print("PASS")

    print("Testing run_integration_suite...")
    suite = run_integration_suite.fn()
    assert "Overall Status: GREEN" in suite
    print("PASS")

    # print("Testing analyze_complexity...")
    # ctx = MockContext()
    # # Create a dummy file to analyze
    # with open("dummy_test.py", "w") as f:
    #     f.write("print('hello')")
    
    # result = await analyze_complexity.fn(ctx, "dummy_test.py")
    # print(f"Result: {result}")
    # assert "Mocked Analysis" in result
    # print("PASS")

if __name__ == "__main__":
    asyncio.run(test_tools())
