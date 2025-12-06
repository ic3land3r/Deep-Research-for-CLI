"""
Tool Router: Routes domain-specific queries to specialized data sources.

This module provides a middleware layer that augments the researcher with hints
about where to find authoritative data for specific domains.
"""

import re
from typing import Optional

# Domain patterns and their recommended data sources
DOMAIN_PATTERNS = [
    {
        "name": "finance",
        "patterns": [r"stock", r"market", r"invest", r"portfolio", r"dividend", r"earnings", r"valuation"],
        "sources": ["Yahoo Finance (via yfinance)", "SEC EDGAR", "Federal Reserve (FRED)"],
        "hint": "For financial data, ask the host to query Yahoo Finance or check SEC filings."
    },
    {
        "name": "science",
        "patterns": [r"research paper", r"study shows", r"peer.?review", r"published", r"journal"],
        "sources": ["arXiv", "Semantic Scholar", "PubMed"],
        "hint": "For scientific research, ask the host to search arXiv.org or Semantic Scholar."
    },
    {
        "name": "technology",
        "patterns": [r"github", r"repository", r"open.?source", r"library", r"framework"],
        "sources": ["GitHub API", "NPM Registry", "PyPI"],
        "hint": "For software/tech data, ask the host to query GitHub or package registries."
    },
    {
        "name": "government",
        "patterns": [r"regulation", r"law", r"policy", r"congress", r"senate", r"federal"],
        "sources": ["Congress.gov", "Federal Register", "Regulations.gov"],
        "hint": "For government/policy data, ask the host to check Congress.gov or Federal Register."
    },
    {
        "name": "realtime",
        "patterns": [r"today", r"current", r"latest", r"2024", r"2025", r"breaking"],
        "sources": ["Google News", "Reuters RSS", "Twitter/X"],
        "hint": "For real-time news, ask the host to perform a web search with date filters."
    }
]

def detect_domain(query: str) -> Optional[dict]:
    """
    Analyzes a query to detect its domain and return routing hints.
    
    Returns:
        A dictionary with domain info and hints, or None if no specific domain detected.
    """
    query_lower = query.lower()
    
    for domain in DOMAIN_PATTERNS:
        for pattern in domain["patterns"]:
            if re.search(pattern, query_lower):
                return {
                    "domain": domain["name"],
                    "sources": domain["sources"],
                    "hint": domain["hint"]
                }
    
    return None

def augment_prompt_with_routing(question: str) -> str:
    """
    Augments a research question with domain-specific routing hints.
    
    Args:
        question: The original research question.
        
    Returns:
        The question with appended hints about where to find data.
    """
    domain_info = detect_domain(question)
    
    if domain_info:
        hint = f"\n\n[TOOL ROUTER HINT: This looks like a {domain_info['domain']} query. {domain_info['hint']}]"
        return f"{question}{hint}"
    
    return question


if __name__ == "__main__":
    # Test the router
    test_queries = [
        "What is the stock price of AAPL?",
        "Find recent research papers on transformer models",
        "What is the current inflation rate?",
        "Explain the SEC filing requirements",
    ]
    
    for q in test_queries:
        result = detect_domain(q)
        print(f"Query: {q}")
        print(f"Domain: {result}")
        print()
