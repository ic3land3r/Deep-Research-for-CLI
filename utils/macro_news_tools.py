"""
Macro/News Tools - World Bank data and RSS news feeds.
Provides economic indicators and real-time news for research context.
"""

import sys
from typing import Optional
from google.adk.tools import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
import urllib.request
import urllib.parse
import json


class WorldBankTool(BaseTool):
    """Tool that fetches macroeconomic data from World Bank Open Data API."""
    
    def __init__(self):
        super().__init__(
            name="get_world_bank_data",
            description="""Fetch macroeconomic data from World Bank.
Available indicators: GDP, inflation, unemployment, interest rates, trade, population.
Use for: economic context, country comparisons, historical trends."""
        )
    
    # Common indicator mappings
    INDICATORS = {
        "gdp": "NY.GDP.MKTP.CD",
        "gdp_growth": "NY.GDP.MKTP.KD.ZG",
        "inflation": "FP.CPI.TOTL.ZG",
        "unemployment": "SL.UEM.TOTL.ZS",
        "population": "SP.POP.TOTL",
        "interest_rate": "FR.INR.RINR",
        "trade_balance": "NE.RSB.GNFS.CD",
        "debt_gdp": "GC.DOD.TOTL.GD.ZS",
    }

    async def run_async(self, *, args: dict, tool_context: Optional[ToolContext] = None) -> str:
        indicator = args.get("indicator", "gdp_growth").lower()
        country = args.get("country", "USA")
        years = args.get("years", 5)
        
        # Map friendly name to API code
        indicator_code = self.INDICATORS.get(indicator, indicator)
        
        try:
            # World Bank API (no auth required)
            url = f"http://api.worldbank.org/v2/country/{country}/indicator/{indicator_code}?format=json&per_page={years}&mrv={years}"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'DeepResearchAgent/1.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            if len(data) < 2 or not data[1]:
                return f"No data found for indicator '{indicator}' in country '{country}'"
            
            records = data[1]
            
            result = [f"# World Bank Data: {indicator.upper()} for {country}\n"]
            result.append(f"**Indicator:** {records[0].get('indicator', {}).get('value', indicator)}")
            result.append(f"**Country:** {records[0].get('country', {}).get('value', country)}\n")
            result.append("| Year | Value |")
            result.append("|:-----|:------|")
            
            for record in records:
                year = record.get('date', 'N/A')
                value = record.get('value')
                if value is not None:
                    if abs(value) > 1e9:
                        formatted = f"${value/1e9:.2f}B"
                    elif abs(value) > 1e6:
                        formatted = f"${value/1e6:.2f}M"
                    else:
                        formatted = f"{value:.2f}%"
                    result.append(f"| {year} | {formatted} |")
            
            result.append(f"\n**Source:** [World Bank Open Data](https://data.worldbank.org/indicator/{indicator_code})")
            return "\n".join(result)
            
        except Exception as e:
            sys.stderr.write(f"[WorldBankTool] Error: {str(e)}\n")
            return f"Error fetching World Bank data: {str(e)}"

    def _get_declaration(self) -> Optional[types.FunctionDeclaration]:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "indicator": types.Schema(
                        type=types.Type.STRING,
                        description="Indicator: gdp, gdp_growth, inflation, unemployment, population, interest_rate, trade_balance, debt_gdp"
                    ),
                    "country": types.Schema(
                        type=types.Type.STRING,
                        description="Country code (e.g., 'USA', 'CHN', 'DEU', 'GBR')"
                    ),
                    "years": types.Schema(
                        type=types.Type.INTEGER,
                        description="Number of years of data (default: 5)"
                    )
                },
                required=["indicator", "country"]
            )
        )


class NewsRssTool(BaseTool):
    """Tool that fetches news from RSS feeds (Reuters, BBC, etc.)."""
    
    def __init__(self):
        super().__init__(
            name="get_news_feed",
            description="""Fetch latest news headlines from major RSS feeds.
Available sources: reuters, bbc, cnbc, google_news.
Use for: current events, breaking news, market sentiment."""
        )
    
    FEEDS = {
        "reuters": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best",
        "bbc": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "cnbc": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "google_news": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    }

    async def run_async(self, *, args: dict, tool_context: Optional[ToolContext] = None) -> str:
        source = args.get("source", "google_news").lower()
        topic = args.get("topic", None)
        max_items = args.get("max_items", 5)
        
        feed_url = self.FEEDS.get(source)
        if not feed_url:
            return f"Unknown source '{source}'. Available: {list(self.FEEDS.keys())}"
        
        # If topic specified, use Google News search
        if topic and source == "google_news":
            feed_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(topic)}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            import xml.etree.ElementTree as ET
            
            req = urllib.request.Request(feed_url, headers={'User-Agent': 'DeepResearchAgent/1.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = response.read().decode('utf-8')
            
            root = ET.fromstring(data)
            
            # Find items (RSS 2.0 format)
            items = root.findall('.//item')[:max_items]
            
            if not items:
                return f"No news items found from {source}"
            
            result = [f"# News Headlines from {source.upper()}\n"]
            if topic:
                result.append(f"**Topic Filter:** {topic}\n")
            
            for i, item in enumerate(items, 1):
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                
                title_text = title.text if title is not None else "No title"
                link_text = link.text if link is not None else "#"
                date_text = pub_date.text[:16] if pub_date is not None else "Unknown"
                
                result.append(f"## {i}. {title_text}")
                result.append(f"- **Published:** {date_text}")
                result.append(f"- **Link:** {link_text}\n")
            
            return "\n".join(result)
            
        except Exception as e:
            sys.stderr.write(f"[NewsRssTool] Error: {str(e)}\n")
            return f"Error fetching news: {str(e)}"

    def _get_declaration(self) -> Optional[types.FunctionDeclaration]:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "source": types.Schema(
                        type=types.Type.STRING,
                        description="News source: reuters, bbc, cnbc, google_news"
                    ),
                    "topic": types.Schema(
                        type=types.Type.STRING,
                        description="Optional topic to search for (only works with google_news)"
                    ),
                    "max_items": types.Schema(
                        type=types.Type.INTEGER,
                        description="Maximum number of headlines (default: 5)"
                    )
                },
                required=[]
            )
        )


def create_world_bank_tool() -> WorldBankTool:
    """Factory function to create World Bank data tool."""
    return WorldBankTool()


def create_news_rss_tool() -> NewsRssTool:
    """Factory function to create news RSS tool."""
    return NewsRssTool()
