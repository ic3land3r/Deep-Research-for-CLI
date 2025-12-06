"""
Academic Research Tools - No-auth access to arXiv and OpenAlex.
Provides paper search, citation graphs, and author information.
"""

import sys
from typing import Optional
from google.adk.tools import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET


class ArxivSearchTool(BaseTool):
    """Tool that searches arXiv for academic papers."""
    
    def __init__(self):
        super().__init__(
            name="search_arxiv",
            description="""Search arXiv for academic papers in CS, Physics, Math, etc.
Returns titles, abstracts, authors, and PDF links.
Use for: research papers, preprints, scientific literature."""
        )

    async def run_async(self, *, args: dict, tool_context: Optional[ToolContext] = None) -> str:
        query = args.get("query", "")
        max_results = args.get("max_results", 5)
        
        if not query:
            return "Error: No query provided."
        
        try:
            # arXiv API endpoint
            base_url = "http://export.arxiv.org/api/query"
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": min(max_results, 10),
                "sortBy": "relevance"
            }
            url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            with urllib.request.urlopen(url, timeout=15) as response:
                data = response.read().decode('utf-8')
            
            # Parse XML response
            root = ET.fromstring(data)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            entries = root.findall('atom:entry', ns)
            if not entries:
                return f"No papers found for query: {query}"
            
            results = [f"# arXiv Search Results: '{query}'\n"]
            
            for i, entry in enumerate(entries[:max_results], 1):
                title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
                summary = entry.find('atom:summary', ns).text.strip()[:300] + "..."
                published = entry.find('atom:published', ns).text[:10]
                
                # Get authors
                authors = [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)]
                author_str = ", ".join(authors[:3]) + ("..." if len(authors) > 3 else "")
                
                # Get PDF link
                pdf_link = ""
                for link in entry.findall('atom:link', ns):
                    if link.get('title') == 'pdf':
                        pdf_link = link.get('href')
                        break
                
                arxiv_id = entry.find('atom:id', ns).text.split('/')[-1]
                
                results.append(f"""
## {i}. {title}
- **Authors:** {author_str}
- **Published:** {published}
- **arXiv ID:** {arxiv_id}
- **PDF:** {pdf_link}
- **Abstract:** {summary}
""")
            
            return "\n".join(results)
            
        except Exception as e:
            sys.stderr.write(f"[ArxivSearchTool] Error: {str(e)}\n")
            return f"Error searching arXiv: {str(e)}"

    def _get_declaration(self) -> Optional[types.FunctionDeclaration]:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="Search query for papers (e.g., 'transformer attention mechanism')"
                    ),
                    "max_results": types.Schema(
                        type=types.Type.INTEGER,
                        description="Maximum number of results (default: 5, max: 10)"
                    )
                },
                required=["query"]
            )
        )


class OpenAlexSearchTool(BaseTool):
    """Tool that searches OpenAlex for academic works with citation data."""
    
    def __init__(self):
        super().__init__(
            name="search_openalex",
            description="""Search OpenAlex database of 240M+ academic works.
Returns papers with citation counts, DOIs, and open access links.
Use for: citation analysis, literature review, finding influential papers."""
        )

    async def run_async(self, *, args: dict, tool_context: Optional[ToolContext] = None) -> str:
        query = args.get("query", "")
        max_results = args.get("max_results", 5)
        
        if not query:
            return "Error: No query provided."
        
        try:
            # OpenAlex API (no auth required, but polite email helps)
            base_url = "https://api.openalex.org/works"
            params = {
                "search": query,
                "per_page": min(max_results, 10),
                "sort": "cited_by_count:desc",
                "mailto": "research@example.com"  # Polite pool
            }
            url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'DeepResearchAgent/1.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            results_list = data.get('results', [])
            if not results_list:
                return f"No papers found for query: {query}"
            
            results = [f"# OpenAlex Search Results: '{query}'\n"]
            
            for i, work in enumerate(results_list[:max_results], 1):
                title = work.get('title', 'Unknown Title')
                citations = work.get('cited_by_count', 0)
                year = work.get('publication_year', 'N/A')
                doi = work.get('doi', 'N/A')
                
                # Get authors
                authorships = work.get('authorships', [])
                authors = [a.get('author', {}).get('display_name', '') for a in authorships[:3]]
                author_str = ", ".join(authors) + ("..." if len(authorships) > 3 else "")
                
                # Get open access PDF
                oa = work.get('open_access', {})
                pdf_url = oa.get('oa_url', 'Not available')
                
                results.append(f"""
## {i}. {title}
- **Authors:** {author_str}
- **Year:** {year}
- **Citations:** {citations:,}
- **DOI:** {doi}
- **Open Access PDF:** {pdf_url}
""")
            
            return "\n".join(results)
            
        except Exception as e:
            sys.stderr.write(f"[OpenAlexSearchTool] Error: {str(e)}\n")
            return f"Error searching OpenAlex: {str(e)}"

    def _get_declaration(self) -> Optional[types.FunctionDeclaration]:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="Search query for papers"
                    ),
                    "max_results": types.Schema(
                        type=types.Type.INTEGER,
                        description="Maximum number of results (default: 5)"
                    )
                },
                required=["query"]
            )
        )


def create_arxiv_tool() -> ArxivSearchTool:
    """Factory function to create arXiv search tool."""
    return ArxivSearchTool()


def create_openalex_tool() -> OpenAlexSearchTool:
    """Factory function to create OpenAlex search tool."""
    return OpenAlexSearchTool()
