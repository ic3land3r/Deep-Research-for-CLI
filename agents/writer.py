"""
Writer Agent - The Synthesizer

Role: Aggregates research findings into a comprehensive report.
Input: Research context with findings and source URLs.
Output: Structured report (Markdown default, or JSON/custom format if specified).

Uses Chain of Density prompting to maximize information value.
CRITICAL: Sources section must contain REAL URLs from research notes.
"""
from google.adk.agents import LlmAgent

WRITER_PROMPT_MARKDOWN = """
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

WRITER_PROMPT_JSON = """
You are a data engineer. Your goal is to convert research notes into a structured JSON response.

CRITICAL: Output ONLY valid JSON. No markdown, no explanations, just JSON.

Use the following schema EXACTLY:
{
  "topic": "The research topic",
  "executive_summary": "A concise 3-5 sentence TL;DR",
  "key_findings": [
    {"finding": "Discovery description", "importance": "Why it matters"}
  ],
  "detailed_analysis": [
    {"section": "Topic name", "content": "Detailed text", "facts": ["fact1", "fact2"]}
  ],
  "limitations": ["List of gaps or unverified information"],
  "sources": ["https://real-url-1.com", "https://real-url-2.com"]
}

IMPORTANT: The "sources" array MUST contain REAL URLs from the research notes. Do NOT make up URLs.
"""

def get_writer_agent(output_format: str = "markdown"):
    """
    Factory function to create a Writer agent with the specified output format.
    
    Args:
        output_format: "markdown" (default), "json", or a custom format instruction.
    """
    if output_format.lower() == "json":
        prompt = WRITER_PROMPT_JSON
    elif output_format.lower() == "markdown":
        prompt = WRITER_PROMPT_MARKDOWN
    else:
        # Custom format - use the output_format as the instruction
        prompt = f"""
You are a technical writer. Your goal is to convert research notes into the requested format.

OUTPUT FORMAT REQUIREMENT:
{output_format}

CRITICAL: Include REAL URLs from the research notes in your output. Do NOT make up URLs.
If the format specifies a schema, follow it exactly.
"""

    return LlmAgent(
        name="writer",
        model="gemini-3-pro-preview",
        static_instruction=prompt
    )

# Backward compatibility - default markdown writer
writer_agent = get_writer_agent("markdown")
