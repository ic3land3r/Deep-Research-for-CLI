"""
Tool Router: Routes domain-specific queries to specialized data sources.
"""

import re
from typing import Optional, Literal

ExecutionMode = Literal["local", "managed"]

DOMAIN_PATTERNS = [
    {
        "name": "finance_simple",
        "patterns": [
            r"price of", r"stock price", r"quote for", r"current value", 
            r"market cap", r"beta", r"pe ratio", r"dividend yield",
            r"RSI", r"MACD", r"moving average", r"technical indicator"
        ],
        "sources": ["yfinance (local)", "TradingView"],
        "hint": "Use get_financial_data for specific metrics/quotes.",
        "tool": "get_financial_data",
        "execution_mode": "local"
    },
    {
        "name": "finance_complex",
        "patterns": [
            r"compare", r"evaluate", r"outlook", r"forecast", r"analysis of",
            r"why is", r"impact of", r"strategy", r"competitor", r"vs",
            r"financial crisis", r"history of", r"bull case", r"bear case"
        ],
        "sources": ["SEC EDGAR", "News Analysis", "Historical Data"],
        "hint": "Complex analysis requires Deep Research.",
        "execution_mode": "managed"
    },
    {
        "name": "science",
        "patterns": [r"research paper", r"study shows", r"peer.?review", r"published", r"journal"],
        "sources": ["arXiv", "Semantic Scholar", "PubMed"],
        "hint": "Scientific research benefits from Deep Research reasoning.",
        "execution_mode": "managed" 
    },
    {
        "name": "technology",
        "patterns": [r"github", r"repository", r"open.?source", r"library", r"framework"],
        "sources": ["GitHub API", "NPM Registry", "PyPI"],
        "hint": "For software/tech data, ask the host to query GitHub or package registries.",
        "execution_mode": "local" 
    },
    {
        "name": "government",
        "patterns": [r"regulation", r"law", r"policy", r"congress", r"senate", r"federal"],
        "sources": ["Congress.gov", "Federal Register", "Regulations.gov"],
        "hint": "Policy analysis requires Deep Research.",
        "execution_mode": "managed"
    },
    {
        "name": "realtime",
        "patterns": [r"today", r"current", r"latest", r"2024", r"2025", r"breaking", r"news"],
        "sources": ["Google News", "Reuters RSS", "Twitter/X"],
        "hint": "Use news tools for real-time updates.",
        "execution_mode": "local"
    },
    {
        "name": "ai_models",
        "patterns": [r"gemini", r"gpt.?4", r"gpt.?5", r"claude", r"llama", r"mistral", r"openai", r"anthropic", r"language model", r"LLM version"],
        "sources": ["Google AI Blog", "OpenAI Blog"],
        "hint": "AI model specs change fast. Use Deep Research for latest verification.",
        "execution_mode": "managed",
        "force_search": True
    }
]

def detect_domain(query: str) -> Optional[dict]:
    query_lower = query.lower()
    
    for domain in DOMAIN_PATTERNS:
        for pattern in domain["patterns"]:
            if re.search(pattern, query_lower):
                return {
                    "domain": domain["name"],
                    "sources": domain["sources"],
                    "hint": domain["hint"],
                    "execution_mode": domain.get("execution_mode", "managed")
                }
    
    return {
        "domain": "general",
        "sources": ["Google Search"],
        "hint": "General topic.",
        "execution_mode": "managed"
    }

def augment_prompt_with_routing(question: str) -> str:
    domain_info = detect_domain(question)
    
    if domain_info and domain_info.get("hint"):
        hint = f"\n\n[TOOL ROUTER HINT: This looks like a {domain_info['domain']} query. {domain_info['hint']}]"
        return f"{question}{hint}"
    
    return question
