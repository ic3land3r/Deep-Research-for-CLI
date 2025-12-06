"""
Finance Tools - No-auth financial data using yfinance and ta libraries.
Provides technical analysis (RSI, MACD, MAs) and fundamental data.
"""

import sys
from typing import Optional, Dict, Any
from google.adk.tools import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

class FinanceDataTool(BaseTool):
    """Tool that provides real financial data using yfinance."""
    
    def __init__(self):
        super().__init__(
            name="get_financial_data",
            description="""Get real financial market data for stocks. 
Use this for: stock prices, technical indicators (RSI, MACD, Moving Averages), fundamentals (P/E, margins), or analyst targets.
Required: ticker symbol (e.g., 'TSLA', 'AAPL', 'NVDA').
Optional: data_type ('quote', 'technical', 'fundamentals', 'all')."""
        )

    async def run_async(self, *, args: dict, tool_context: Optional[ToolContext] = None) -> str:
        ticker = args.get("ticker", "").upper()
        data_type = args.get("data_type", "all").lower()
        
        if not ticker:
            return "Error: No ticker symbol provided. Use format: ticker='TSLA'"
        
        try:
            import yfinance as yf
            import pandas as pd
        except ImportError:
            return "Error: yfinance not installed. Run: pip install yfinance pandas"
        
        try:
            stock = yf.Ticker(ticker)
            result_parts = []
            
            # Get quote/price data
            if data_type in ("quote", "price", "all"):
                info = stock.info
                quote_data = {
                    "Symbol": ticker,
                    "Current Price": info.get("currentPrice") or info.get("regularMarketPrice"),
                    "Previous Close": info.get("previousClose"),
                    "Open": info.get("open") or info.get("regularMarketOpen"),
                    "Day High": info.get("dayHigh") or info.get("regularMarketDayHigh"),
                    "Day Low": info.get("dayLow") or info.get("regularMarketDayLow"),
                    "52W High": info.get("fiftyTwoWeekHigh"),
                    "52W Low": info.get("fiftyTwoWeekLow"),
                    "Volume": info.get("volume") or info.get("regularMarketVolume"),
                    "Avg Volume": info.get("averageVolume"),
                    "Market Cap": info.get("marketCap"),
                }
                result_parts.append("## Price Data")
                for k, v in quote_data.items():
                    if v is not None:
                        if isinstance(v, (int, float)) and v > 1000000:
                            result_parts.append(f"- **{k}:** ${v:,.0f}" if k == "Market Cap" else f"- **{k}:** {v:,.2f}")
                        else:
                            result_parts.append(f"- **{k}:** {v}")
            
            # Get technical indicators
            if data_type in ("technical", "ta", "all"):
                hist = stock.history(period="3mo")
                if len(hist) > 0:
                    result_parts.append("\n## Technical Indicators")
                    
                    # Calculate indicators
                    close = hist['Close']
                    
                    # Moving Averages
                    ma_50 = close.rolling(window=50).mean().iloc[-1] if len(close) >= 50 else None
                    ma_20 = close.rolling(window=20).mean().iloc[-1] if len(close) >= 20 else None
                    ma_200 = None  # Need 6mo+ data
                    
                    # RSI (14-period)
                    delta = close.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    current_rsi = rsi.iloc[-1] if len(rsi) >= 14 else None
                    
                    # MACD (12, 26, 9)
                    ema_12 = close.ewm(span=12, adjust=False).mean()
                    ema_26 = close.ewm(span=26, adjust=False).mean()
                    macd_line = ema_12 - ema_26
                    signal_line = macd_line.ewm(span=9, adjust=False).mean()
                    macd_histogram = macd_line - signal_line
                    
                    current_price = close.iloc[-1]
                    
                    result_parts.append(f"- **Current Price:** ${current_price:.2f}")
                    if ma_20:
                        result_parts.append(f"- **20-Day MA:** ${ma_20:.2f} ({'above' if current_price > ma_20 else 'below'})")
                    if ma_50:
                        result_parts.append(f"- **50-Day MA:** ${ma_50:.2f} ({'above' if current_price > ma_50 else 'below'})")
                    if current_rsi:
                        rsi_signal = "overbought" if current_rsi > 70 else "oversold" if current_rsi < 30 else "neutral"
                        result_parts.append(f"- **RSI (14):** {current_rsi:.1f} ({rsi_signal})")
                    
                    macd_val = macd_line.iloc[-1]
                    signal_val = signal_line.iloc[-1]
                    hist_val = macd_histogram.iloc[-1]
                    macd_signal = "bullish" if macd_val > signal_val else "bearish"
                    result_parts.append(f"- **MACD:** {macd_val:.3f}")
                    result_parts.append(f"- **MACD Signal:** {signal_val:.3f} ({macd_signal})")
                    result_parts.append(f"- **MACD Histogram:** {hist_val:.3f}")
                    
                    # Support/Resistance (simple: recent lows/highs)
                    recent_high = hist['High'].tail(20).max()
                    recent_low = hist['Low'].tail(20).min()
                    result_parts.append(f"- **20-Day Resistance:** ${recent_high:.2f}")
                    result_parts.append(f"- **20-Day Support:** ${recent_low:.2f}")
            
            # Get fundamental data
            if data_type in ("fundamentals", "fundamental", "all"):
                info = stock.info
                result_parts.append("\n## Fundamental Data")
                
                fundamentals = {
                    "P/E Ratio (Trailing)": info.get("trailingPE"),
                    "P/E Ratio (Forward)": info.get("forwardPE"),
                    "PEG Ratio": info.get("pegRatio"),
                    "Price/Book": info.get("priceToBook"),
                    "Profit Margin": f"{info.get('profitMargins', 0) * 100:.1f}%" if info.get('profitMargins') else None,
                    "Revenue Growth (YoY)": f"{info.get('revenueGrowth', 0) * 100:.1f}%" if info.get('revenueGrowth') else None,
                    "Earnings Growth (YoY)": f"{info.get('earningsGrowth', 0) * 100:.1f}%" if info.get('earningsGrowth') else None,
                    "Debt/Equity": info.get("debtToEquity"),
                    "Target Mean Price": f"${info.get('targetMeanPrice')}" if info.get('targetMeanPrice') else None,
                    "Target High": f"${info.get('targetHighPrice')}" if info.get('targetHighPrice') else None,
                    "Target Low": f"${info.get('targetLowPrice')}" if info.get('targetLowPrice') else None,
                    "Analyst Recommendation": info.get("recommendationKey"),
                }
                
                for k, v in fundamentals.items():
                    if v is not None:
                        result_parts.append(f"- **{k}:** {v}")
            
            if not result_parts:
                return f"No data available for {ticker}"
            
            return f"# Financial Data: {ticker}\n\n" + "\n".join(result_parts)
            
        except Exception as e:
            sys.stderr.write(f"[FinanceDataTool] Error: {str(e)}\n")
            return f"Error fetching data for {ticker}: {str(e)}"

    def _get_declaration(self) -> Optional[types.FunctionDeclaration]:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "ticker": types.Schema(
                        type=types.Type.STRING,
                        description="Stock ticker symbol (e.g., 'TSLA', 'AAPL', 'NVDA')"
                    ),
                    "data_type": types.Schema(
                        type=types.Type.STRING,
                        description="Type of data: 'quote', 'technical', 'fundamentals', or 'all' (default: 'all')"
                    )
                },
                required=["ticker"]
            )
        )


def create_finance_tool() -> FinanceDataTool:
    """Factory function to create the finance data tool."""
    return FinanceDataTool()
