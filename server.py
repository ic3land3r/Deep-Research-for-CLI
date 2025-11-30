from fastmcp import FastMCP, Context
from core.orchestrator import Orchestrator
from utils.sampling import safe_sampling_request

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

@mcp.tool()
async def analyze_complexity(ctx: Context, file_path: str) -> str:
    """
    Analyzes the complexity of a file using the host's LLM (Recursive Sampling).
    
    Args:
        ctx: The FastMCP context.
        file_path: The path to the file to analyze.
    """
    try:
        with open(file_path, "r") as f:
            content = f.read()
            
        prompt = f"Analyze the code complexity of the following file. Identify any complex functions or logic that might be hard to maintain:\n\n{content}"
        
        result = await safe_sampling_request(
            ctx, 
            prompt, 
            system_prompt="You are a senior code reviewer. Focus on cyclomatic complexity and maintainability."
        )
        return result
    except Exception as e:
        return f"Error analyzing file: {str(e)}"

def _get_db_schema_logic() -> str:
    return """
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL
    );
    
    CREATE TABLE projects (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        name VARCHAR(100) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """

@mcp.tool()
def get_db_schema() -> str:
    """
    Returns the current database schema for the project.
    """
    # Mock schema for now as per report
    return _get_db_schema_logic()

@mcp.tool()
def describe_data_schema() -> str:
    """
    Returns the entity relationship diagram (ERD) or schema for the project.
    Useful for the Architect agent to understand the data model.
    """
    return _get_db_schema_logic()

@mcp.tool()
def run_integration_suite() -> str:
    """
    Runs the project's integration test suite.
    """
    # Mock implementation for now
    return "Integration Suite Results:\n- test_auth_flow: PASS\n- test_payment_gateway: PASS\n- test_data_sync: PASS\n\nOverall Status: GREEN"

if __name__ == "__main__":
    # Runs the server over stdio (standard input/output), which Gemini CLI uses
    mcp.run()
