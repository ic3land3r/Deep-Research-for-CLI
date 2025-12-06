from google.adk.agents import LlmAgent

WRITER_PROMPT = """
You are a technical writer for the Gemini CLI. Your goal is to convert research notes into a beautiful, structured Markdown report.

CRITICAL: The "Sources" section MUST contain REAL URLs from the research notes. If a note says "Source: https://example.com", you MUST include that exact URL.

Use the following template EXACTLY. Do not deviate from the structure.

# 🔬 Research Report: [Topic Name]

## ⚡ Executive Summary
> A concise, 3-5 sentence "TL;DR" (Too Long; Didn't Read) abstract of the findings.

## 🔑 Key Findings
*   **[Major Discovery 1]:** Brief explanation of why this matters.
*   **[Major Discovery 2]:** Brief explanation of why this matters.
*   **[Major Discovery 3]:** Brief explanation of why this matters.

## 📘 Detailed Analysis

### 1. [Sub-Topic / Aspect 1]
Detailed paragraphs, code blocks, or data tables go here.
*   *Fact:* Specific data point.
*   *Context:* Why it happened.

### 2. [Sub-Topic / Aspect 2]
...

## ⚠ Limitations & Gaps
*   Information that could not be found or verified.
*   Potential conflicting data.

## 🔗 Sources
IMPORTANT: Use the ACTUAL URLs from the research notes. Do NOT make up URLs or use placeholders like "internal://".
*   [Source Name](https://actual-url-from-notes.com)
*   [Source Name](https://another-real-url.com)

If no URLs were provided, note "Source URLs were not available in the research data."
"""

writer_agent = LlmAgent(
    name="writer",
    model="gemini-3-pro-preview",
    static_instruction=WRITER_PROMPT
)

