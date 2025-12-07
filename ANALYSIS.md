# Deep Research MCP Server - Architecture & Code Analysis

## 1. Executive Summary

The **Deep Research MCP Server** implements a sophisticated "Level 3" agentic workflow that effectively leverages the Model Context Protocol (MCP) to delegate complex research tasks. The architecture successfully orchestrates multiple agents (Planner, Researcher, Writer, Reviewer) to perform parallelized work.

However, the current implementation faces challenges regarding **robustness, error handling, and deployment configuration**. Specifically, the dependency management prevents standalone execution, and the agent coordination logic is brittle in face of malformed LLM outputs.

## 2. Architecture Review

### 2.1. Orchestrator Logic (`core/orchestrator.py`)
*   **Strengths:**
    *   **Parallel Execution:** correctly uses `asyncio.gather` to parallelize research tasks, significantly reducing total latency.
    *   **Feedback Loop:** Implements a Reviewer-Writer cycle to improve output quality.
    *   **Tool Injection:** The dynamic injection of tools based on domain detection (`utils/tool_router.py`) is a smart design pattern that keeps the context window clean.
*   **Weaknesses:**
    *   **Fragile Parsing:** The Plan parsing logic (`plan_text.split("\n")`) assumes the Planner agent outputs a perfectly formatted list. If the model adds a preamble ("Here is the plan:"), the parsing may fail or include garbage data.
    *   **Failure Propagation:** The `asyncio.gather` call does not specify `return_exceptions=True`. If a single researcher sub-task raises an unhandled exception, the entire research session crashes.
    *   **State Management:** The session state is entirely in-memory. If the server restarts, all context is lost.

### 2.2. Memory Management (`core/memory.py`)
*   **Strengths:**
    *   **Source Tracking:** The `MemoryChunk` data class correctly preserves source URLs, ensuring citations are not lost during synthesis.
*   **Weaknesses:**
    *   **Heavyweight Initialization:** Using `embedding_functions.DefaultEmbeddingFunction()` triggers a model download (all-MiniLM-L6-v2) on the first run. This is resource-intensive for a CLI tool and may fail in air-gapped environments.
    *   **Inefficient Clearing:** The `clear()` method deletes and recreates the entire ChromaDB collection. A better approach would be to use `session_id` in metadata and filter queries/deletions by session, allowing for concurrent sessions in the future.

### 2.3. Agent Patterns (`agents/*.py`)
*   **Strengths:**
    *   **Specialized Prompts:** Each agent has a distinct, well-scoped prompt (Planner vs. Researcher vs. Writer).
    *   **Recursive Host Query:** The usage of `ask_host_for_info` allows the server to break out of its sandbox, which is innovative.
*   **Risks:**
    *   **Infinite Loops:** While `MAX_DEEP_DIVE_DEPTH` limits the research recursion, there is no hard limit on the *Reviewer-Writer* loop. If the Reviewer consistently rejects the draft, the agents could loop indefinitely (though the code currently appears to limit it to *one* revision).

## 3. Code Quality & Robustness

### 3.1. Dependency & Build Configuration
**CRITICAL:** The `pyproject.toml` defines `google-adk` as a workspace dependency (`{ workspace = true }`).
```toml
[tool.uv.sources]
google-adk = { workspace = true }
```
This fails in a standalone clone of the repository because the workspace root is missing. This prevents `uv sync` from working out-of-the-box for new users.

### 3.2. Error Handling
*   **Generic Catch-Alls:** The `perform_deep_research` tool wraps the entire execution in a broad `try...except Exception`. While this prevents the server from crashing, it masks the root cause of failures (e.g., API timeouts vs. Parsing errors).
*   **Missing Retries:** There is no retry logic for network calls or LLM sampling requests. Transient API failures will cause the research task to fail.

## 4. Security Analysis

### 4.1. The "Ask Host" Mechanism
The `ask_host_for_info` tool enables the server to execute commands or searches on the host machine via the Gemini CLI.
*   **Risk:** If the Host (Client) is configured to auto-approve sampling requests, a compromised or hallucinating agent could execute harmful commands.
*   **Mitigation:** The current implementation relies entirely on the Host's user confirmation dialogs.

## 5. Proposed Roadmap

### Phase 1: Stabilization (Immediate)
1.  **Fix `pyproject.toml`:** Change `google-adk` to a PyPI version (e.g., `">=0.3.0"`) or a Git dependency to ensure `uv sync` works.
2.  **Robust Parsing:** Implement a robust parser for the Planner's output (using regex to find lines starting with `- ` or `* `) and strip preambles.
3.  **Exception Handling:** Update `asyncio.gather` to handle individual task failures gracefully (log the error and continue with partial results).

### Phase 2: Performance & Efficiency
4.  **Lightweight Embeddings:** Switch to a lighter embedding model or allow the use of the Host's embedding API to remove the heavy local dependency.
5.  **Session Scoping:** Update `Memory` to support `session_id` metadata instead of wiping the collection.

### Phase 3: Enhanced Capability
6.  **Structured Output:** Use JSON schema constraints (if available in the underlying ADK/Gemini API) to force the Planner to output valid JSON, eliminating parsing errors.
7.  **Retry Logic:** Add a decorator for automatic retries on `safe_sampling_request` and tool execution.

## 6. Conclusion
The codebase is a strong proof-of-concept for Agentic MCP servers. With the fixes proposed in Phase 1, it will be production-ready for developer use.
