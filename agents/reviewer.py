"""
Reviewer Agent - The Critic

Role: Verifies that claims in the draft report are supported by source text.
Input: Draft report with claims to verify.
Output: PASS or FAIL status with reasoning and corrections if needed.

If the review fails, the Writer is invoked again with specific feedback.
This implements a self-correction feedback loop (one revision attempt).
"""
from google.adk.agents import LlmAgent

REVIEWER_PROMPT = """
You are a Citation Reviewer. Your goal is to verify that a claim is supported by the provided source text.

Input:
- Claim: [The statement to verify]
- Source: [The source text/snippet]

Output:
- Status: PASS or FAIL
- Reasoning: Brief explanation.
- Correction: If FAIL, provide the corrected claim based on the source.

Rules:
1.  Be strict. If the source doesn't explicitly support the claim, mark it FAIL.
2.  Ignore minor wording differences if the meaning is identical.
"""

reviewer_agent = LlmAgent(
    name="reviewer",
    model="gemini-3-pro-preview",
    static_instruction=REVIEWER_PROMPT
)
