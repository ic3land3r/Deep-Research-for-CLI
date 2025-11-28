# Architecture Evaluation: Autonomous Deep Research Agent

## Executive Summary

The proposed "Autonomous Deep Research Agent" architecture represents a significant paradigm shift from the current **Level 2 (Reasoning/Search)** agent to a **Level 4 (Autonomous/Self-Correcting)** system.

While the current implementation provides a functional "Deep Research" capability using Gemini 3.0's inherent reasoning and tool use, the proposed architecture introduces **explicit cognitive structures** and **hierarchical orchestration** that would dramatically increase robustness, depth, and factual accuracy.

## Detailed Component Analysis

### Phase 1: Paradigm Definition (OODA Loop)
*   **Current State**: The current agent relies on an implicit loop managed by the LLM's internal chain-of-thought. It reacts to the user prompt and search results linearly.
*   **Proposed State**: An explicit **OODA Loop (Observe, Orient, Decide, Act)**.
*   **Impact**:
    *   **"Orient" Phase**: The critical addition. Instead of just searching, the agent explicitly identifies *what is missing* or *conflicting* before acting.
    *   **Active vs. Passive**: Transitions the agent from "answering a question" to "solving an information gap."

### Phase 2: Topology (Hierarchical Planner-Executor)
*   **Current State**: Single-threaded execution. The context window fills up with raw search results, leading to "Context Pollution" and degradation of reasoning over long tasks.
*   **Proposed State**: **Hub-and-Spoke** model. A "Planner" delegates to ephemeral "Researchers."
*   **Impact**:
    *   **Infinite Depth**: Sub-agents run in isolated contexts, returning only compressed insights. This allows the system to research massive topics without hitting context limits.
    *   **Parallelism**: Multiple sub-topics (e.g., Financials, Competitors, Regulations) can be researched simultaneously.

### Phase 3: Cognitive Dynamics (System 2 Logic)
*   **Current State**: Relies on the model's "System 1" (fast) generation, with some "System 2" capabilities inherent in Gemini 3.0 Pro.
*   **Proposed State**: Explicit **Tree of Thoughts (ToT)** and **Reflection Loops**.
*   **Impact**:
    *   **Hallucination Defense**: The "Reflection Loop" catches low-confidence results *before* they are used.
    *   **Hybrid Routing**: Optimizes cost/performance by sending simple tasks to faster models and complex reasoning to stronger models.

### Phase 4: Environment & Memory
*   **Current State**: Ephemeral memory (session-based). No long-term recall.
*   **Proposed State**: **Session-Scoped Vector Database** and **Browser Entropy**.
*   **Impact**:
    *   **Deep Context**: The agent stores entities in a temporary Vector DB for the duration of the research session. This allows it to recall specific details found 50 steps ago without polluting the LLM's immediate context window.
    *   **Privacy & Simplicity**: Data is wiped after the session, ensuring no cross-contamination or long-term storage liability.
    *   **Resilience**: "Entropy Injection" prevents the agent from being blocked by anti-bot measures during scraping.

### Phase 5: Synthesis & Validation (The "Truth" Layer)
*   **Current State**: The model synthesizes the final answer based on its context.
*   **Proposed State**: **Bi-Encoder/Cross-Encoder Pipeline** and **Citation Agent**.
*   **Impact**:
    *   **Chain of Density**: Produces highly information-dense summaries ("knowledge nuggets") rather than fluff.
    *   **CLI-Optimized Writer**: The final output is strictly formatted in **clean Markdown** (headers, bullet points, code blocks) specifically tuned for the Gemini CLI's renderer. It avoids conversational filler and focuses on structured data presentation, making it easy for the user (and the Gemini 3.0 Pro model in the CLI) to parse and read.
    *   **NLI Verification**: A dedicated step where a model checks if the citation *actually supports* the claim (Entailment check). This is the gold standard for preventing "citation hallucination."

## Integration Impact: Vector DB & MCP

Adding a Vector Database will **NOT change the external MCP interface**. The Gemini CLI will still see the same tool signature:

```python
perform_deep_research(topic: str) -> str
```

However, the **internal architecture** and **deployment** will change:

1.  **Transparent Complexity**: The Vector DB (e.g., ChromaDB, Qdrant, or embedded DuckDB) runs entirely within the server's process or as a sidecar. The Gemini CLI is unaware of it.
2.  **Session Lifecycle**: The `server.py` must manage the DB lifecycle:
    *   **Start**: Initialize/Connect to DB on tool call.
    *   **Run**: Read/Write embeddings during the loop.
    *   **End**: **Crucial** - Drop the collection/clear data before returning the final string to ensure privacy and session isolation.
3.  **Dependencies**: `pyproject.toml` will need new libraries (e.g., `chromadb`, `sentence-transformers`).

## Implementation Implications

Implementing this architecture would require a significant expansion of the codebase:

1.  **Orchestrator Pattern**: Moving from a single `LlmAgent` to a graph-based orchestrator (likely using `LangGraph` or a custom ADK-based state machine).
2.  **Infrastructure**:
    *   **Vector DB**: Setting up ChromaDB, Pinecone, or pgvector.
    *   **Reranking Service**: Hosting a Cross-Encoder model (e.g., `ms-marco-MiniLM`).
3.  **Agent Specialization**: Writing distinct prompts and toolsets for `Planner`, `Researcher`, `Reviewer`, and `Writer`.

## Conclusion

The proposed architecture is **highly recommended** for production-grade research systems where accuracy and depth are non-negotiable. It solves the fundamental limitations of single-turn RAG: context saturation, lack of planning, and hallucination.

**Recommendation**: Adopt Phase 2 (Hierarchical Planning) and Phase 5 (Verification) as the immediate next steps to yield the highest ROI on quality.
