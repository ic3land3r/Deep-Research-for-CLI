# Deep Research MCP Server for Gemini CLI

This repository hosts a **Model Context Protocol (MCP)** server that provides a "Deep Research" capability to the Gemini CLI. It leverages **Gemini 3.0 Pro** and **Google Search** to perform exhaustive, multi-step research on complex topics.

## 🏗️ Functional Architecture

The system implements a **Level 3 Autonomous Agent** architecture, featuring hierarchical planning, parallel execution, session-scoped memory, and self-correction loops.

### 1. Core Components

| Component | Role | Implementation Details |
| :--- | :--- | :--- |
| **Orchestrator** | **The Controller** | Manages the lifecycle of the research request. It initializes the session, coordinates agent execution, manages the Vector DB, and enforces the feedback loop. |
| **Intent Extractor** | **The Clarifier** | Analyzes vague user queries (e.g., "batteries") and transforms them into specific, context-aware research goals before planning begins. |
| **Planner Agent** | **The Strategist** | Decomposes complex user queries into a Directed Acyclic Graph (DAG) of sub-questions. Uses `gemini-3-pro-preview` for reasoning. |
| **Researcher Agent** | **The Worker (Local)** | Executed in **PARALLEL** for each sub-question. Delegates search to the Host via `ask_host_for_info`. |
| **Managed Agent** | **The Specialist (API)** | Interfaces with the official `deep-research-pro-preview` model for "Deep" mode queries, bypassing the local loop for maximum depth. |
| **Memory Layer** | **The Context** | A **Session-Scoped Vector Database** (ChromaDB) that stores research notes. Optional (graceful fallback if missing). |
| **Writer Agent** | **The Synthesizer** | Aggregates retrieved context and generates a comprehensive report using **Chain of Density** prompting to maximize information value. |
| **Reviewer Agent** | **The Critic** | Analyzes the draft report for accuracy and completeness. If it rejects the draft ("FAIL"), it triggers a revision cycle. |

### 2. Data Flow & Execution Pipeline

The workflow follows a strict **Plan -> Research -> Write -> Review** cycle:

1.  **Initialization**: The `Orchestrator` creates a fresh `Memory` instance.
2.  **Intent Extraction**: The `IntentExtractor` refines the user's raw topic into a clear research goal.
3.  **Planning Phase**: The `Planner` breaks the refined goal into $N$ sub-questions.
4.  **Research Phase (Parallel)**:
    *   The `Orchestrator` spawns $N$ concurrent `Researcher` tasks.
    *   Each researcher gathers data and calls `memory.add()` to store findings.
5.  **Synthesis Phase**:
    *   The `Orchestrator` queries `Memory` for the top $K$ relevant chunks.
    *   The `Writer` generates a `draft_report`.
5.  **Verification Phase (Feedback Loop)**:
    *   The `Reviewer` evaluates the `draft_report`.
    *   **Pass**: The report is returned to the user.
    *   **Fail**: The `Writer` is invoked again with specific feedback to generate a `final_report`.

## 🚀 Deployment & Setup

### Prerequisites
*   **Linux** (Tested on Nobara Linux)
*   **Python 3.10 - 3.13** (Pinned to <3.14 to avoid dependency issues)
*   **uv**: An extremely fast Python package installer and resolver.

### 1. Clone and Install
```bash
git clone https://github.com/ic3land3r/Deep-Research-for-CLI.git
cd Deep-Research-for-CLI

uv sync
```

### 2. Configure API Key
Create a `.env` file in the project root:
```bash
echo 'GOOGLE_API_KEY="your_api_key_here"' > .env
```
*Note: The `.env` file is gitignored for security.*

### 3. Connect to Gemini CLI
Edit your `~/.gemini/settings.json` file.

**Add this block to `mcpServers`:**

```json
"deep-research": {
  "command": "/ABSOLUTE/PATH/TO/Deep-Research-for-CLI/run_mcp.sh",
  "args": [],
  "env": {}
}
```
*Replace `/ABSOLUTE/PATH/TO/...` with the actual full path to the cloned repository.*

## 🎯 Research Modes

| Mode | Planning | Deep Dive | Review | Best For |
|:-----|:---------|:----------|:-------|:---------|
| **`quick`** | ❌ Skip | ❌ Never | ✅ Yes | Fast lookups, simple facts |
| **`standard`** | ✅ Yes | 🔄 Conditional | ✅ Yes | Balanced research (default) |
| **`deep`** | ✅ Yes | ✅ Always | ✅ Yes | Exhaustive analysis |
| **`hybrid`** | ✅ Yes | 🔄 Smart Routing | ✅ Yes | Best of both (default) |

### Usage

```python
# MCP Tool Call
perform_deep_research(topic="Your topic", mode="hybrid")
```

---

## 📝 Changelog

### v0.7.0 (2025-12-12)
**New Features**
- **Hybrid Research Mode**: Integrated `ManagedResearcherAgent` to leverage the official Gemini Deep Research API.
- **Deep Mode**: `mode="deep"` now delegates the entire task to the `deep-research-pro-preview` model via the Interactions API.
- **Improved Routing**: Intelligent routing between Local Agent (fast/simple) and Managed Agent (complex/deep).
- **Optional ChromaDB**: Vector DB memory is now optional; falls back to simple context if `chromadb` is not installed.

**Improvements**
- **SDK Upgrade**: Upgraded `google-genai` to v1.55.0 to support `Interactions` API.
- **Refined Polling**: optimized status checks for long-running managed research tasks.

### v0.6.0 (2025-12-12)
- **Intent Extraction**: New `IntentExtractor` agent automatically clarifies vague queries.

### v0.5.0 (2025-12-11)
- **Custom Output Formats**: `output_format` parameter supports `markdown`, `json`, or custom schema
- **Current Date Context**: Automatic date injection
- **AI Model Version Detection**: Accurate reporting of current AI models
