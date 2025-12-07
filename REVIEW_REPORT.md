# Deep Research MCP Server - Review Report

## 1. Documentation Review

### 1.1 Consistency Checks (README vs Code)

*   **Researcher Agent Tools:**
    *   **Finding:** The `README.md` "Core Components" table states the Researcher Agent uses the `google_search` tool. However, `agents/researcher.py` explicitly notes: `GoogleSearchTool is removed due to incompatibility with Function Calling` and `We rely on ask_host_for_info`.
    *   **Recommendation:** Update `README.md` to reflect that search is performed via `ask_host_for_info` (delegated to Host) rather than a direct tool.

*   **Setup Instructions:**
    *   **Finding:** `pyproject.toml` contains `google-adk = { workspace = true }`. The README notes this, but a user following the "Clone and Install" instructions (`uv sync`) will encounter an error unless they manually edit the file as described in the "NOTE".
    *   **Recommendation:** Comment out the workspace source by default in the repo, or provide a `sed` command in the setup instructions to fix it automatically.

### 1.2 Code Documentation (Docstrings)

*   **Coverage:**
    *   `server.py`: Good coverage for exposed tools.
    *   `core/orchestrator.py`: `run` method is documented, but internal methods like `_execute_agent` are minimal.
    *   `agents/*.py`: Files lack module-level docstrings explaining the agent's role, relying instead on the prompt text to define behavior.
    *   `utils/sampling.py`: Excellent documentation.

*   **Recommendation:** Add module-level docstrings to all files in `agents/` describing the agent's input/output contract and role in the DAG.

## 2. Security Review

### 2.1 Arbitrary File Read Vulnerability (`High Severity`)

*   **Location:** `server.py` -> `analyze_complexity`
*   **Issue:** The tool accepts a `file_path` argument and performs `open(file_path, "r")` without any path validation or sandboxing.
    ```python
    with open(file_path, "r") as f:
        content = f.read()
    ```
*   **Risk:** An attacker (via Indirect Prompt Injection from a search result) could trick the agent into calling this tool with sensitive paths (e.g., `~/.ssh/id_rsa`, `/etc/passwd`). If the agent then "exfiltrates" this data (e.g., by including it in a subsequent search query URL), it leads to information disclosure.
*   **Recommendation:** Restrict file access to the current working directory or a specific allowlist of directories. Use `os.path.abspath` and `os.path.commonpath` to verify the target file is inside the allowed root.

### 2.2 Indirect Prompt Injection (`Medium Severity`)

*   **Location:** `utils/host_tools.py` -> `AskHostTool` and `agents/researcher.py`
*   **Issue:** The `AskHostTool` retrieves information (e.g., search results) from the Host and returns it as a string. This string is then fed directly into the Researcher Agent's context.
*   **Risk:** If the search results contain malicious instructions (Indirect Prompt Injection), the Researcher Agent could be hijacked to perform unintended actions (like the file read mentioned above, or biasing the report).
*   **Mitigation:** The `Researcher` uses a structured output format (`FINDINGS:`), which offers some resistance. However, it is not a complete defense.
*   **Recommendation:**
    *   Consider sanitizing search results (stripping extensive HTML/Markdown).
    *   Use "Delimiters" in the prompt to clearly separate "Trusted Instructions" from "Untrusted Data" (e.g., ` <search_results> ... </search_results>`).

### 2.3 Sampling Request Safety (`Low Severity`)

*   **Location:** `utils/sampling.py`
*   **Observation:** The code correctly uses `include_context="none"` to prevent infinite context loops or leaking the Agent's internal state back to the Host inappropriately.
*   **Status:** **Pass**. This is a good security practice.

### 2.4 Dependency Management

*   **Observation:** `pyproject.toml` pins python to `<3.14`. Dependencies like `fastmcp`, `google-genai` are pinned to minimum versions.
*   **Status:** **Pass**.

## 3. Summary of Actionable Items

1.  **Fix `analyze_complexity`:** Implement path validation immediately.
2.  **Update README:** Correct the Researcher tool description.
3.  **Improve Docstrings:** Add docstrings to `agents/`.
