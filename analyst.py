import os
import yfinance as yf
from groq import Groq
#import schedule
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import requests
import feedparser
import urllib.parse

# Load environment variables
load_dotenv()

# Configuration
PORTFOLIO = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']  # Edit your stocks here
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

def fetch_news_for_stock(symbol, company_name, max_articles=3):  # Reduced from 10 to 3
    """Fetch recent news articles for a specific stock"""
    print(f"  📰 Fetching news for {symbol}...")
    
    news_items = []
    
    try:
        ticker = yf.Ticker(symbol)
        
        # Method 1: Try to get news from the ticker's news property
        try:
            news = ticker.news
            if news:
                for item in news[:max_articles]:
                    try:
                        title = item.get('title', '').strip()
                        if not title:
                            continue
                            
                        published_date = datetime.fromtimestamp(
                            item.get('providerPublishTime', time.time())
                        ).strftime('%Y-%m-%d %H:%M')
                        
                        news_item = {
                            'title': title,
                            'publisher': item.get('publisher', 'Yahoo Finance').strip(),
                            'link': item.get('link', '').strip() or item.get('url', '').strip(),
                            'published': published_date,
                            'summary': (item.get('summary') or item.get('description') or 'No summary available')[:300].strip()
                        }
                        
                        news_items.append(news_item)
                        print(f"    ✓ [{published_date}] {news_item['title'][:60]}... ({news_item['publisher']})")
                        
                    except Exception as e:
                        print(f"    ⚠️  Error processing article: {e}")
        except Exception as e:
            print(f"    ⚠️  Error fetching news (method 1) for {symbol}: {e}")
        
        # Method 2: Try to get news from the ticker's info
        if not news_items:
            try:
                info = ticker.info
                if 'news' in info:
                    for item in info['news'][:max_articles]:
                        try:
                            title = item.get('title', '').strip()
                            if not title:
                                continue
                                
                            published_date = datetime.fromtimestamp(
                                item.get('providerPublishTime', time.time())
                            ).strftime('%Y-%m-%d %H:%M')
                            
                            news_item = {
                                'title': title,
                                'publisher': item.get('publisher', 'Yahoo Finance').strip(),
                                'link': item.get('link', '').strip() or item.get('url', '').strip(),
                                'published': published_date,
                                'summary': (item.get('summary') or item.get('description') or 'No summary available')[:300].strip()
                            }
                            
                            news_items.append(news_item)
                            print(f"    ✓ [{published_date}] {news_item['title'][:60]}... ({news_item['publisher']})")
                            
                        except Exception as e:
                            print(f"    ⚠️  Error processing article (method 2): {e}")
            except Exception as e:
                print(f"    ⚠️  Error fetching news (method 2) for {symbol}: {e}")
        
        # Method 3: Fallback to company name search if no news found
        if not news_items:
            try:
                search_query = f"{company_name} stock news"
                encoded_query = urllib.parse.quote_plus(search_query)
                rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries[:max_articles]:
                    try:
                        title = entry.title.strip()
                        if not title or any(n['title'] == title for n in news_items):
                            continue
                            
                        news_item = {
                            'title': title,
                            'publisher': getattr(entry, 'source', {}).get('title', 'Google News').strip(),
                            'link': entry.link.strip(),
                            'published': entry.get('published', 'Recent'),
                            'summary': (getattr(entry, 'summary', '') or 'No summary available')[:300].strip()
                        }
                        
                        news_items.append(news_item)
                        print(f"    ✓ [{news_item['published']}] {news_item['title'][:60]}... ({news_item['publisher']})")
                        
                        if len(news_items) >= max_articles:
                            break
                            
                    except Exception as e:
                        print(f"    ⚠️  Error processing Google News article: {e}")
                        
            except Exception as e:
                print(f"    ⚠️  Error fetching Google News for {symbol}: {e}")
        
    except Exception as e:
        print(f"    ⚠️  Error in fetch_news_for_stock for {symbol}: {e}")
    
    print(f"    📊 Total: {len(news_items)} articles collected for {symbol}")
    return news_items[:max_articles]

def fetch_market_news(max_articles=3):  # Reduced from 10 to 3
    """Fetch general market news"""
    print("  📰 Fetching general market news...")
    
    market_news = []
    
    try:
        search_queries = [
            "stock market today",
            "S&P 500 nasdaq",
            "federal reserve interest rates"
        ]
        
        for query in search_queries:
            # URL encode the query
            encoded_query = urllib.parse.quote_plus(query)
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            
            try:
                feed = feedparser.parse(rss_url)
                
                for entry in feed.entries[:4]:  # Take more from each query
                    if not any(n['title'] == entry.title for n in market_news):
                        published_date = entry.get('published', 'Recent')
                        news_item = {
                            'title': entry.title.strip(),
                            'publisher': getattr(entry, 'source', {}).get('title', 'Google News').strip(),
                            'link': entry.link.strip(),
                            'published': published_date,
                            'summary': (getattr(entry, 'summary', '') or 'No summary available')[:300].strip()
                        }
                        market_news.append(news_item)
                        print(f"    ✓ [{published_date}] {news_item['title'][:60]}... ({news_item['publisher']})")
                        
                    if len(market_news) >= max_articles:
                        break
                
                if len(market_news) >= max_articles:
                    break
                    
            except Exception as e:
                print(f"    ⚠️  Error fetching news for query '{query}': {e}")
                
    except Exception as e:
        print(f"    ⚠️  Market news error: {e}")
    
    print(f"    📊 Total: {len(market_news)} market news articles collected")
    return market_news[:max_articles]

def collect_market_data():
    """Collect market data, portfolio data, and news"""
    print("📊 Collecting market data and news...")
    
    data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'market_indices': {},
        'portfolio': {},
        'market_news': []
    }
    
    # Market indices
    indices = {
        '^GSPC': 'S&P 500',
        '^IXIC': 'NASDAQ',
        '^VIX': 'VIX'
    }
    
    for symbol, name in indices.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='5d')
            if not hist.empty:
                current = hist['Close'].iloc[-1]
                previous = hist['Close'].iloc[-2]
                change = ((current - previous) / previous) * 100
                
                data['market_indices'][name] = {
                    'price': round(current, 2),
                    'change_percent': round(change, 2)
                }
        except Exception as e:
            print(f"  ⚠️  Error fetching {name}: {e}")
    
    # Fetch general market news
    data['market_news'] = fetch_market_news(max_articles=10)
    
    # Portfolio stocks with news
    for symbol in PORTFOLIO:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period='5d')
            
            if not hist.empty:
                current = hist['Close'].iloc[-1]
                previous = hist['Close'].iloc[-2]
                change = ((current - previous) / previous) * 100
                
                company_name = info.get('longName', symbol)
                
                # Fetch news for this specific stock - reduced to 3 articles
                news = fetch_news_for_stock(symbol, company_name, max_articles=3)
                
                data['portfolio'][symbol] = {
                    'name': company_name,
                    'price': round(current, 2),
                    'change_percent': round(change, 2),
                    'volume': int(hist['Volume'].iloc[-1]),
                    'market_cap': info.get('marketCap', 'N/A'),
                    'pe_ratio': round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else 'N/A',
                    'sector': info.get('sector', 'N/A'),
                    'industry': info.get('industry', 'N/A'),
                    'news': news,
                    'news_count': len(news)
                }
        except Exception as e:
            print(f"  ⚠️  Error fetching {symbol}: {e}")
    
    print(f"✅ Collected data for {len(data['portfolio'])} stocks with news analysis")
    return data

def analyze_with_groq(market_data):
    """Send data to Groq for comprehensive analysis including news"""
    print("🤖 Analyzing market data and news with Groq AI...")
    
    # Create a focused summary of news for the LLM
    news_summary = "## Market News:\n"
    for news_item in market_data.get('market_news', [])[:5]:
        news_summary += f"- {news_item['title']} ({news_item['publisher']})\n"
    
    news_summary += "\n## Company-Specific News:\n"
    for symbol, stock_data in market_data.get('portfolio', {}).items():
        news_summary += f"\n### {symbol} ({stock_data['name']}):\n"
        for news_item in stock_data.get('news', [])[:3]:
            news_summary += f"- {news_item['title']}\n"
            if news_item.get('summary'):
                news_summary += f"  Summary: {news_item['summary']}\n"
    
    prompt = f"""You are an expert financial analyst with deep knowledge of market trends and news analysis. Analyze the following market data and recent news to provide a comprehensive daily brief.

Market Data:
{json.dumps({k: v for k, v in market_data.items() if k != 'market_news'}, indent=2)}

{news_summary}

CRITICAL INSTRUCTIONS:
1. **Base your analysis heavily on the recent news** - this is the most important data
2. Consider how news sentiment affects each stock
3. Identify catalysts (positive or negative) from the news
4. Look for sector trends and correlations
5. Consider both fundamental data AND news sentiment

Please provide your analysis in the following JSON format (respond ONLY with valid JSON, no markdown):
{{
  "market_overview": "3-4 sentence summary of overall market conditions, sentiment, and key news driving the market today",
  "news_highlights": [
    "Key market-moving news item 1",
    "Key market-moving news item 2",
    "Key market-moving news item 3"
  ],
  "portfolio_health": {{
    "summary": "Overall assessment of the portfolio based on recent news and price action",
    "alerts": ["Any concerning signals or risks from news or data - list 2-3 items or empty array if none"]
  }},
  "stock_analysis": [
    {{
      "ticker": "SYMBOL",
      "sentiment": "Bullish|Neutral|Bearish",
      "key_news": "Most important news affecting this stock",
      "analysis": "2-3 sentence analysis based on news and data"
    }}
  ],
  "recommendations": [
    {{
      "ticker": "STOCK_SYMBOL",
      "action": "Strong Buy|Moderate Buy|Hold|Sell",
      "current_price": 123.45,
      "target_price": 135.00,
      "rationale": "3-4 sentence explanation based heavily on recent news, catalysts, and data. Reference specific news items.",
      "risk_level": "Low|Medium|High",
      "timeframe": "1-3 months|3-6 months|6-12 months",
      "news_catalyst": "The specific news or event driving this recommendation"
    }}
  ],
  "action_items": [
    "Specific actionable advice based on news - list 3-5 items"
  ]
}}

Provide exactly 3 stock recommendations. Focus on stocks where recent news provides clear catalysts or signals. Be specific and reference actual news events."""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional financial analyst specializing in news-driven market analysis. Always respond with valid JSON only, no markdown formatting. Base recommendations heavily on recent news and events."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=3000,
        )
        
        response_text = chat_completion.choices[0].message.content
        
        # Clean up response - remove markdown if present
        response_text = response_text.strip()
        if response_text.startswith('```json'):
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif response_text.startswith('```'):
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        analysis = json.loads(response_text)
        print("✅ Analysis complete")
        return analysis
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON response: {e}")
        print(f"Raw response: {response_text[:500]}...")
        return None
    except Exception as e:
        print(f"❌ Error with Groq API: {e}")
        return None

def generate_terminal_output(market_data, analysis):
    """Generate beautiful terminal output with news highlights"""
    
    # Terminal colors
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    
    output = f"\n\n{'='*80}\n"
    output += f"{BOLD}{MAGENTA}📈 YOUR DAILY MARKET BRIEF{RESET}\n"
    output += f"{CYAN}{datetime.now().strftime('%A, %B %d, %Y - %I:%M %p')}{RESET}\n"
    output += f"{'='*80}\n\n"
    
    # Market Overview with News
    output += f"{BOLD}{BLUE}🌍 MARKET OVERVIEW{RESET}\n"
    output += f"{'-'*80}\n"
    for name, data in market_data['market_indices'].items():
        emoji = "🟢" if data['change_percent'] >= 0 else "🔴"
        color = GREEN if data['change_percent'] >= 0 else RED
        sign = "+" if data['change_percent'] >= 0 else ""
        output += f"{emoji} {BOLD}{name:12}{RESET}: {data['price']:8.2f} ({color}{sign}{data['change_percent']:+6.2f}%{RESET})\n"
    
    if analysis and analysis.get('market_overview'):
        output += f"\n{YELLOW}💡 {analysis['market_overview']}{RESET}\n"
    
    # News Highlights
    if analysis and analysis.get('news_highlights'):
        output += f"\n{BOLD}{BLUE}📰 KEY NEWS HIGHLIGHTS{RESET}\n"
        output += f"{'-'*80}\n"
        for i, highlight in enumerate(analysis['news_highlights'], 1):
            output += f"{CYAN}{i}.{RESET} {highlight}\n"
    
    # Portfolio Health
    output += f"\n{BOLD}{BLUE}📊 YOUR PORTFOLIO{RESET}\n"
    output += f"{'-'*80}\n"
    
    total_change = 0
    for symbol, data in market_data['portfolio'].items():
        emoji = "🟢" if data['change_percent'] >= 0 else "🔴"
        color = GREEN if data['change_percent'] >= 0 else RED
        sign = "+" if data['change_percent'] >= 0 else ""
        total_change += data['change_percent']
        
        output += f"{emoji} {BOLD}{symbol:6}{RESET} | ${data['price']:8.2f} | "
        output += f"{color}{sign}{data['change_percent']:+6.2f}%{RESET} | "
        output += f"{data['news_count']} news items\n"
    
    avg_change = total_change / len(market_data['portfolio']) if market_data['portfolio'] else 0
    avg_color = GREEN if avg_change >= 0 else RED
    output += f"\n{BOLD}Average Portfolio Change: {avg_color}{avg_change:+.2f}%{RESET}\n"
    
    # Stock-by-Stock News Analysis
    if analysis and analysis.get('stock_analysis'):
        output += f"\n{BOLD}{BLUE}🔍 STOCK-BY-STOCK ANALYSIS{RESET}\n"
        output += f"{'-'*80}\n"
        for stock in analysis['stock_analysis']:
            sentiment_colors = {
                'Bullish': GREEN,
                'Neutral': YELLOW,
                'Bearish': RED
            }
            sent_color = sentiment_colors.get(stock['sentiment'], RESET)
            
            output += f"\n{BOLD}{stock['ticker']}{RESET} - {sent_color}{stock['sentiment']}{RESET}\n"
            output += f"  📰 {stock.get('key_news', 'No major news')}\n"
            output += f"  💭 {stock.get('analysis', '')}\n"
    
    # Alerts
    if analysis and analysis.get('portfolio_health', {}).get('alerts'):
        output += f"\n{BOLD}{YELLOW}⚠️  ALERTS{RESET}\n"
        output += f"{'-'*80}\n"
        for alert in analysis['portfolio_health']['alerts']:
            output += f"  • {alert}\n"
    
    # Recommendations
    if analysis and analysis.get('recommendations'):
        output += f"\n{BOLD}{BLUE}🎯 TODAY'S OPPORTUNITIES (NEWS-DRIVEN){RESET}\n"
        output += f"{'-'*80}\n"
        
        for i, rec in enumerate(analysis['recommendations'], 1):
            action_colors = {
                'Strong Buy': GREEN,
                'Moderate Buy': CYAN,
                'Hold': YELLOW,
                'Sell': RED
            }
            action_color = action_colors.get(rec['action'], RESET)
            
            upside = ((rec['target_price'] - rec['current_price']) / rec['current_price']) * 100
            
            output += f"\n{BOLD}{i}. {rec['ticker']} - {action_color}{rec['action']}{RESET}\n"
            output += f"   Price: ${rec['current_price']:.2f} → Target: ${rec['target_price']:.2f} "
            output += f"({GREEN if upside > 0 else RED}+{upside:.1f}%{RESET})\n"
            output += f"   Risk: {rec['risk_level']} | Timeframe: {rec['timeframe']}\n"
            output += f"   📰 Catalyst: {rec.get('news_catalyst', 'N/A')}\n"
            output += f"   💡 {rec['rationale']}\n"
    
    # Action Items
    if analysis and analysis.get('action_items'):
        output += f"\n{BOLD}{BLUE}✅ ACTION ITEMS{RESET}\n"
        output += f"{'-'*80}\n"
        for i, item in enumerate(analysis['action_items'], 1):
            output += f"{i}. {item}\n"
    
    # Recent News Summary
    output += f"\n{BOLD}{BLUE}📱 RECENT NEWS BY STOCK{RESET}\n"
    output += f"{'-'*80}\n"
    for symbol, data in market_data['portfolio'].items():
        if data.get('news'):
            output += f"\n{BOLD}{symbol}{RESET} - {data['name']}\n"
            for news in data['news'][:3]:
                output += f"  • {news['title'][:70]}...\n"
                output += f"    {CYAN}{news['publisher']} - {news['published']}{RESET}\n"
    
    output += f"\n{'='*80}\n"
    output += f"{CYAN}Generated by AI Stock Analyst | Not Financial Advice{RESET}\n"
    output += f"{'='*80}\n\n"
    
    return output

def generate_html_file(market_data, analysis):
    """Generate enhanced HTML file with news analysis"""
    
    # Market overview section
    market_html = ""
    for name, data in market_data['market_indices'].items():
        emoji = "🟢" if data['change_percent'] >= 0 else "🔴"
        sign = "+" if data['change_percent'] >= 0 else ""
        market_html += f"{emoji} <strong>{name}</strong>: {data['price']} ({sign}{data['change_percent']}%)<br>"
    
    # News highlights
    news_highlights_html = ""
    if analysis and analysis.get('news_highlights'):
        for highlight in analysis['news_highlights']:
            news_highlights_html += f"<li>📰 {highlight}</li>"
    
    # Portfolio section
    portfolio_html = ""
    total_change = 0
    for symbol, data in market_data['portfolio'].items():
        emoji = "🟢" if data['change_percent'] >= 0 else "🔴"
        sign = "+" if data['change_percent'] >= 0 else ""
        total_change += data['change_percent']
        portfolio_html += f"""
        <tr>
            <td>{emoji} <strong>{symbol}</strong></td>
            <td>${data['price']}</td>
            <td style="color: {'green' if data['change_percent'] >= 0 else 'red'}">{sign}{data['change_percent']}%</td>
            <td>{data['news_count']} articles</td>
        </tr>
        """
    
    avg_change = total_change / len(market_data['portfolio']) if market_data['portfolio'] else 0
    
    # Stock analysis section
    stock_analysis_html = ""
    if analysis and analysis.get('stock_analysis'):
        for stock in analysis['stock_analysis']:
            sentiment_colors = {
                'Bullish': '#10b981',
                'Neutral': '#f59e0b',
                'Bearish': '#ef4444'
            }
            sent_color = sentiment_colors.get(stock['sentiment'], '#6b7280')
            
            stock_analysis_html += f"""
            <div style="background: #f9fafb; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid {sent_color};">
                <h3 style="margin: 0 0 10px 0; color: {sent_color};">{stock['ticker']} - {stock['sentiment']}</h3>
                <p style="margin: 5px 0;"><strong>📰 Key News:</strong> {stock.get('key_news', 'No major news')}</p>
                <p style="margin: 5px 0;">{stock.get('analysis', '')}</p>
            </div>
            """
    
    # Alerts section
    alerts_html = ""
    if analysis and analysis.get('portfolio_health', {}).get('alerts'):
        for alert in analysis['portfolio_health']['alerts']:
            alerts_html += f"<li>⚠️ {alert}</li>"
    else:
        alerts_html = "<li>✅ No major alerts detected</li>"
    
    # Recommendations section
    recommendations_html = ""
    if analysis and analysis.get('recommendations'):
        for i, rec in enumerate(analysis['recommendations'], 1):
            action_color = {
                'Strong Buy': '#10b981',
                'Moderate Buy': '#3b82f6',
                'Hold': '#f59e0b',
                'Sell': '#ef4444'
            }.get(rec['action'], '#6b7280')
            
            upside = ((rec['target_price'] - rec['current_price']) / rec['current_price']) * 100
            
            recommendations_html += f"""
            <div style="background: #f9fafb; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid {action_color};">
                <h3 style="margin: 0 0 10px 0; color: {action_color};">{i}. {rec['ticker']} - {rec['action']}</h3>
                <p style="margin: 5px 0;"><strong>Price:</strong> ${rec['current_price']} → Target: ${rec['target_price']} (+{upside:.1f}%)</p>
                <p style="margin: 5px 0;"><strong>Risk:</strong> {rec['risk_level']} | <strong>Timeframe:</strong> {rec['timeframe']}</p>
                <p style="margin: 5px 0; background: #fef3c7; padding: 8px; border-radius: 4px;"><strong>📰 News Catalyst:</strong> {rec.get('news_catalyst', 'N/A')}</p>
                <p style="margin: 5px 0;">{rec['rationale']}</p>
            </div>
            """
    
    # Action items section
    action_items_html = ""
    if analysis and analysis.get('action_items'):
        for item in analysis['action_items']:
            action_items_html += f"<li>{item}</li>"
    
    # Recent news section
    news_by_stock_html = ""
    for symbol, data in market_data['portfolio'].items():
        if data.get('news'):
            news_by_stock_html += f"""
            <div style="margin: 15px 0;">
                <h3 style="color: #1f2937; margin-bottom: 10px;">{symbol} - {data['name']}</h3>
            """
            for news in data['news'][:3]:
                news_by_stock_html += f"""
                <div style="background: #f3f4f6; padding: 10px; margin: 5px 0; border-radius: 5px;">
                    <p style="margin: 0; font-weight: 600;">{news['title']}</p>
                    <p style="margin: 5px 0 0 0; font-size: 12px; color: #6b7280;">
                        {news['publisher']} - {news['published']}
                        {f' | <a href="{news["link"]}" target="_blank" style="color: #3b82f6;">Read more →</a>' if news.get('link') else ''}
                    </p>
                </div>
                """
            news_by_stock_html += "</div>"
    
# Complete HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Daily Market Brief - {datetime.now().strftime('%B %d, %Y')}</title>
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
        
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h1 style="margin: 0; font-size: 32px;">📈 Your Daily Market Brief</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 18px;">{datetime.now().strftime('%A, %B %d, %Y')}</p>
            <p style="margin: 5px 0 0 0; opacity: 0.8; font-size: 14px;">📰 Powered by Real-Time News Analysis</p>
        </div>
        
        <div style="background: white; margin: 20px 0; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin-top: 0;">🌍 Market Overview</h2>
            <div style="background: #f3f4f6; padding: 15px; border-radius: 8px;">
                {market_html}
                <p style="margin-top: 15px; font-style: italic; color: #6b7280;">
                    {analysis.get('market_overview', 'Market data collected successfully.') if analysis else 'Market data collected successfully.'}
                </p>
            </div>
            
            {f'''
            <div style="margin-top: 20px; background: #eff6ff; padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6;">
                <h3 style="margin: 0 0 10px 0; color: #1e40af;">📰 Key News Highlights</h3>
                <ul style="margin: 0; padding-left: 20px;">
                    {news_highlights_html}
                </ul>
            </div>
            ''' if news_highlights_html else ''}
        </div>
        
        <div style="background: white; margin: 20px 0; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin-top: 0;">📊 Your Portfolio</h2>
            <p style="background: {'#d1fae5' if avg_change >= 0 else '#fee2e2'}; padding: 15px; border-radius: 8px; text-align: center; font-size: 18px;">
                <strong>Average Change: {'🟢' if avg_change >= 0 else '🔴'} {'+' if avg_change >= 0 else ''}{avg_change:.2f}%</strong>
            </p>
            <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                <thead>
                    <tr style="background: #f3f4f6;">
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Stock</th>
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Price</th>
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">Change</th>
                        <th style="padding: 12px; text-align: left; border-bottom: 2px solid #e5e7eb;">News</th>
                    </tr>
                </thead>
                <tbody>
                    {portfolio_html}
                </tbody>
            </table>
            
            <div style="margin-top: 20px; background: #fef3c7; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b;">
                <h3 style="margin: 0 0 10px 0; color: #92400e;">⚠️ Alerts</h3>
                <ul style="margin: 0; padding-left: 20px;">
                    {alerts_html}
                </ul>
            </div>
        </div>
        
        {f'''
        <div style="background: white; margin: 20px 0; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin-top: 0;">🔍 Stock-by-Stock Analysis</h2>
            {stock_analysis_html}
        </div>
        ''' if stock_analysis_html else ''}
        
        <div style="background: white; margin: 20px 0; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin-top: 0;">🎯 Today's Opportunities</h2>
            <p style="color: #6b7280; font-style: italic;">Based on recent news and market analysis</p>
            {recommendations_html}
        </div>
        
        <div style="background: white; margin: 20px 0; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin-top: 0;">💡 Action Items</h2>
            <ul style="background: #eff6ff; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6; margin: 0;">
                {action_items_html}
            </ul>
        </div>
        
        <div style="background: white; margin: 20px 0; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="color: #1f2937; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; margin-top: 0;">📱 Recent News by Stock</h2>
            {news_by_stock_html}
        </div>
        
        <div style="margin-top: 30px; padding: 20px; background: #f9fafb; border-radius: 8px; text-align: center; font-size: 12px; color: #6b7280;">
            <p style="margin: 0;"><strong>Disclaimer:</strong> This analysis is for informational purposes only and does not constitute financial advice. Always do your own research before making investment decisions.</p>
            <p style="margin: 10px 0 0 0;">Generated by AI Stock Analyst | {datetime.now().strftime('%I:%M %p')}</p>
        </div>
        
    </body>
    </html>
    """
    
    # Save to file
    filename = f"market_brief_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return filename

def run_daily_analysis():
    """Main workflow"""
    print(f"\n{'='*80}")
    print(f"🚀 Starting Daily Analysis with News")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    try:
        # Step 1: Collect data and news
        market_data = collect_market_data()
        
        # Step 2: Analyze with AI
        analysis = analyze_with_groq(market_data)
        
        # Step 3: Generate terminal output
        terminal_output = generate_terminal_output(market_data, analysis)
        print(terminal_output)
        
        # Step 4: Generate HTML file
        #html_filename = generate_html_file(market_data, analysis)
        #print(f"💾 Report saved to: {html_filename}")
        #print(f"📂 Open this file in your browser to view the formatted report\n")
        
        print(f"{'='*80}")
        print("✅ Daily analysis complete!")
        print(f"{'='*80}\n")
            
    except Exception as e:
        print(f"\n❌ Error in daily analysis: {e}\n")
        import traceback
        traceback.print_exc()

# Schedule the job
# schedule.every().day.at("06:30").do(run_daily_analysis)

if __name__ == "__main__":
    print("🤖 Stock Analyst Bot Started (with News Analysis)")
    print(f"📊 Tracking portfolio: {', '.join(PORTFOLIO)}")
    print(f"⏰ Scheduled for: 6:30 AM daily")
    print(f"💾 Reports will be saved as HTML files")
    print(f"📰 Now analyzing real financial news for each stock!")
    print("\nRunning first analysis now...\n")
    
    # Run immediately for testing
    run_daily_analysis()
    
    print("\n⏰ Waiting for scheduled time (6:30 AM)...")
    print("Press Ctrl+C to stop\n")
    
    # Keep running
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)