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
import ollama


# Load environment variables
load_dotenv()

# Configuration
#PORTFOLIO = ['SBUX', 'MSFT', 'SNOW', 'NVDA', 'TSLA', 'UNH', 'JEPQ', 'NFLX', 'T', 'AAPL', 'META', 'GOOGL']  # Edit your stocks here
#PORTFOLIO = ['SBUX', 'SNOW', 'TSLA']  # Edit your stocks here
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# Initialize LLM model
OLLAMA_MODEL = "gemma3:12b"

# Number of article to analyze
ARTICLE_COUNT = 10

def fetch_news_for_stock(symbol, company_name, max_articles=ARTICLE_COUNT):
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

def fetch_market_news(max_articles=ARTICLE_COUNT): 
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

    # Read portfolio from environment variable
    portfolio_str = os.getenv('PORTFOLIO', '')
    if portfolio_str:
        PORTFOLIO = [s.strip() for s in portfolio_str.split(',') if s.strip()]
    else:
        PORTFOLIO = ['SBUX', 'SNOW', 'TSLA']  # Default fallback
    
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
    data['market_news'] = fetch_market_news(max_articles=ARTICLE_COUNT)
    
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
                
                # Fetch news for this specific stock
                news = fetch_news_for_stock(symbol, company_name, max_articles=ARTICLE_COUNT)
                
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

def analyze_with_ollama_new_v1(market_data):
    """Send data to Ollama for comprehensive analysis including news"""
    print(f"🤖 Analyzing market data and news with Ollama ({OLLAMA_MODEL})...")
    
    # Create a focused summary of news for the LLM
    news_summary = "## Market News:\n"
    for news_item in market_data.get('market_news', [])[:10]:
        news_summary += f"- {news_item['title']} ({news_item['publisher']})\n"
    
    news_summary += "\n## Company-Specific News:\n"
    for symbol, stock_data in market_data.get('portfolio', {}).items():
        news_summary += f"\n### {symbol} ({stock_data['name']}):\n"
        for news_item in stock_data.get('news', [])[:5]:
            news_summary += f"- {news_item['title']}\n"
            if news_item.get('summary'):
                news_summary += f"  Summary: {news_item['summary']}\n"
    
    system_prompt = """You are a professional financial analyst specializing in news-driven market analysis. Always respond with valid JSON only, no markdown formatting. Base recommendations heavily on recent news and events."""
    
    user_prompt = f"""You are an expert financial analyst with deep knowledge of market trends and news analysis. Analyze the following market data and recent news to provide a comprehensive daily brief.

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

Provide exactly 5 stock recommendations. Focus on stocks where recent news provides clear catalysts or signals. Be specific and reference actual news events."""

    try:
        # Call Ollama using the Python library
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': user_prompt
                }
            ],
            options={
                'temperature': 0.3,
                'num_predict': 3000,
            },
            format='json'  # Force JSON output
        )
        
        response_text = response['message']['content']
        
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
        print(f"❌ Error with Ollama: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_with_ollama_new_v2(market_data):
    """Send data to Ollama for comprehensive analysis including news"""
    print(f"🤖 Analyzing market data and news with Ollama ({OLLAMA_MODEL})...")
    
    # Create a focused summary of news for the LLM
    news_summary = "## Market News:\n"
    for news_item in market_data.get('market_news', [])[:10]:
        news_summary += f"- {news_item['title']} ({news_item['publisher']})\n"
    
    news_summary += "\n## Company-Specific News:\n"
    for symbol, stock_data in market_data.get('portfolio', {}).items():
        news_summary += f"\n### {symbol} ({stock_data['name']}):\n"
        news_summary += f"CURRENT PRICE: ${stock_data['price']} (Change: {stock_data['change_percent']:+.2f}%)\n"
        for news_item in stock_data.get('news', [])[:5]:
            news_summary += f"- {news_item['title']}\n"
            if news_item.get('summary'):
                news_summary += f"  Summary: {news_item['summary']}\n"
    
    # Extract current prices explicitly for the prompt
    price_data = "\n## CURRENT STOCK PRICES (USE THESE EXACT VALUES):\n"
    for symbol, stock_data in market_data.get('portfolio', {}).items():
        price_data += f"- {symbol}: ${stock_data['price']} ({stock_data['change_percent']:+.2f}%)\n"
    
    # Build stock_analysis template with actual data
    stock_analysis_template = []
    for symbol, stock_data in market_data.get('portfolio', {}).items():
        stock_analysis_template.append({
            "ticker": symbol,
            "current_price": stock_data['price'],
            "sentiment": "Bullish or Neutral or Bearish",
            "key_news": "Most important news for this stock",
            "analysis": "2-3 sentence analysis"
        })
    
    user_prompt = f"""You are an expert financial analyst. Analyze this market data and news.

{price_data}

{news_summary}

CRITICAL RULES:
1. You MUST use the EXACT current prices provided above - DO NOT make up different prices
2. For recommendations, use the current_price from the data, then estimate a reasonable target_price
3. Base your analysis on the actual news provided
4. Analyze ALL {len(market_data.get('portfolio', {}))} stocks in the portfolio

Respond with ONLY this JSON (use the actual stock symbols and prices from the data):

{{
  "market_overview": "3-4 sentence summary of market conditions and key news",
  "news_highlights": [
    "Key news 1",
    "Key news 2",
    "Key news 3"
  ],
  "portfolio_health": {{
    "summary": "Overall portfolio assessment",
    "alerts": ["Alert 1 if any", "Alert 2 if any"]
  }},
  "stock_analysis": {json.dumps(stock_analysis_template, indent=4)},
  "recommendations": [
    {{
      "ticker": "Pick from portfolio",
      "action": "Strong Buy or Moderate Buy or Hold or Sell",
      "current_price": "USE EXACT PRICE FROM DATA ABOVE",
      "target_price": "Your estimate based on analysis",
      "rationale": "Detailed reasoning referencing specific news",
      "risk_level": "Low or Medium or High",
      "timeframe": "1-3 months or 3-6 months or 6-12 months",
      "news_catalyst": "Specific news driving this"
    }},
    {{
      "ticker": "Pick from portfolio",
      "action": "Strong Buy or Moderate Buy or Hold or Sell",
      "current_price": "USE EXACT PRICE FROM DATA ABOVE",
      "target_price": "Your estimate based on analysis",
      "rationale": "Detailed reasoning referencing specific news",
      "risk_level": "Low or Medium or High",
      "timeframe": "1-3 months or 3-6 months or 6-12 months",
      "news_catalyst": "Specific news driving this"
    }},
    {{
      "ticker": "Pick from portfolio",
      "action": "Strong Buy or Moderate Buy or Hold or Sell",
      "current_price": "USE EXACT PRICE FROM DATA ABOVE",
      "target_price": "Your estimate based on analysis",
      "rationale": "Detailed reasoning referencing specific news",
      "risk_level": "Low or Medium or High",
      "timeframe": "1-3 months or 3-6 months or 6-12 months",
      "news_catalyst": "Specific news driving this"
    }}
  ],
  "action_items": [
    "Action 1",
    "Action 2",
    "Action 3"
  ]
}}

REMEMBER: Use EXACT prices from the data - {', '.join([f'{s}: ${d["price"]}' for s, d in market_data.get('portfolio', {}).items()])}"""

    try:
        # Call Ollama using the Python library
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a financial analyst. You MUST use exact prices from the provided data. Never make up or hallucinate stock prices. Always respond with valid JSON only.'
                },
                {
                    'role': 'user',
                    'content': user_prompt
                }
            ],
            options={
                'temperature': 0.2,  # Lower temperature to reduce hallucination
                'num_predict': 4000,
                'top_k': 10,  # More focused on likely tokens
                'top_p': 0.9,  # Reduce randomness
            },
            format='json'
        )
        
        response_text = response['message']['content'].strip()
        
        # Clean up response
        if response_text.startswith('```json'):
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif response_text.startswith('```'):
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        if '{' in response_text and '}' in response_text:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            response_text = response_text[start:end]
        
        analysis = json.loads(response_text)
        
        # Validate and correct prices if the model still hallucinated
        if 'recommendations' in analysis:
            for rec in analysis['recommendations']:
                ticker = rec.get('ticker', '')
                if ticker in market_data.get('portfolio', {}):
                    actual_price = market_data['portfolio'][ticker]['price']
                    rec_price = rec.get('current_price', 0)
                    
                    # If price is way off (more than 50% difference), correct it
                    if isinstance(rec_price, (int, float)) and actual_price > 0:
                        price_diff = abs(rec_price - actual_price) / actual_price
                        if price_diff > 0.5:
                            print(f"⚠️  Correcting hallucinated price for {ticker}: {rec_price} → {actual_price}")
                            rec['current_price'] = actual_price
                            # Also adjust target price proportionally
                            if rec.get('target_price', 0) > 0:
                                ratio = rec['target_price'] / rec_price if rec_price > 0 else 1.1
                                rec['target_price'] = round(actual_price * ratio, 2)
        
        # Validate stock_analysis prices
        if 'stock_analysis' in analysis:
            for stock in analysis['stock_analysis']:
                ticker = stock.get('ticker', '')
                if ticker in market_data.get('portfolio', {}):
                    actual_price = market_data['portfolio'][ticker]['price']
                    if 'current_price' in stock:
                        stock_price = stock['current_price']
                        if isinstance(stock_price, (int, float)) and actual_price > 0:
                            price_diff = abs(stock_price - actual_price) / actual_price
                            if price_diff > 0.5:
                                print(f"⚠️  Correcting hallucinated price in analysis for {ticker}")
                                stock['current_price'] = actual_price
        
        # Add defaults for missing fields
        if 'market_overview' not in analysis:
            analysis['market_overview'] = "Market analysis based on recent data and news."
        if 'portfolio_health' not in analysis:
            analysis['portfolio_health'] = {'summary': 'Portfolio data analyzed', 'alerts': []}
        if 'stock_analysis' not in analysis:
            analysis['stock_analysis'] = []
        if 'recommendations' not in analysis:
            analysis['recommendations'] = []
        
        print(f"✅ Analysis complete:")
        print(f"   - Market overview: {'✓' if analysis.get('market_overview') else '✗'}")
        print(f"   - Stock analyses: {len(analysis.get('stock_analysis', []))} stocks")
        print(f"   - Recommendations: {len(analysis.get('recommendations', []))} picks")
        
        return analysis
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        print(f"Response preview: {response_text[:500]}...")
        return None
    except Exception as e:
        print(f"❌ Error with Ollama: {e}")
        import traceback
        traceback.print_exc()
        return None


def analyze_news_sentiment(symbol, stock_data, news_items):
    """Extract sentiment and key insights from news for a single stock"""
    
    if not news_items or len(news_items) == 0:
        print(f"    ⚠️  No news items for {symbol}")
        return {
            'sentiment_score': 0,
            'sentiment': 'Neutral',
            'key_points': ['No recent news available'],
            'catalysts': [],
            'risk_factors': []
        }
    
    news_text = f"Stock: {symbol} ({stock_data['name']})\n"
    news_text += f"Current Price: ${stock_data['price']} ({stock_data['change_percent']:+.2f}%)\n\n"
    news_text += "Recent News:\n"
    
    for i, news in enumerate(news_items[:5], 1):
        news_text += f"{i}. {news['title']}\n"
        if news.get('summary'):
            news_text += f"   {news['summary'][:200]}\n"
    
    prompt = f"""{news_text}

Analyze the sentiment of these news articles about {symbol}. Consider:
- Are the news positive (growth, earnings beat, new products) or negative (layoffs, losses, scandals)?
- What specific events or catalysts are mentioned?
- What risks are highlighted?

Respond with ONLY this JSON (no other text):

{{
  "sentiment_score": -10 to +10 where -10 is very bearish and +10 is very bullish,
  "sentiment": "Bullish" or "Neutral" or "Bearish",
  "key_points": ["key point 1", "key point 2", "key point 3"],
  "catalysts": ["positive catalyst 1", "positive catalyst 2"],
  "risk_factors": ["risk 1", "risk 2"]
}}"""

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{
                'role': 'system',
                'content': 'You are a financial analyst specializing in news sentiment analysis. Respond only with valid JSON.'
            }, {
                'role': 'user',
                'content': prompt
            }],
            options={
                'temperature': 0.2,
                'num_predict': 1000,
                'top_p': 0.9
            },
            format='json'
        )
        
        response_text = response['message']['content'].strip()
        
        # Clean up response
        if response_text.startswith('```json'):
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif response_text.startswith('```'):
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        # Extract JSON if wrapped
        if '{' in response_text and '}' in response_text:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            response_text = response_text[start:end]
        
        result = json.loads(response_text)
        
        # Validate required fields
        if 'sentiment_score' not in result:
            result['sentiment_score'] = 0
        if 'sentiment' not in result:
            result['sentiment'] = 'Neutral'
        if 'key_points' not in result or not result['key_points']:
            result['key_points'] = [news_items[0]['title'][:100] if news_items else 'No analysis']
        if 'catalysts' not in result:
            result['catalysts'] = []
        if 'risk_factors' not in result:
            result['risk_factors'] = []
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"    ❌ JSON parsing failed for {symbol}: {e}")
        print(f"    Response was: {response_text[:200]}...")
        # Return fallback based on news titles
        return {
            'sentiment_score': 0,
            'sentiment': 'Neutral',
            'key_points': [news_items[0]['title'][:100] if news_items else 'Parse error'],
            'catalysts': [],
            'risk_factors': ['Analysis parsing failed']
        }
    except Exception as e:
        print(f"    ❌ Sentiment analysis error for {symbol}: {str(e)}")
        import traceback
        print(f"    Traceback: {traceback.format_exc()[:300]}")
        return {
            'sentiment_score': 0,
            'sentiment': 'Neutral',
            'key_points': [news_items[0]['title'][:100] if news_items else 'Error occurred'],
            'catalysts': [],
            'risk_factors': ['Analysis failed']
        }

def analyze_stock_recommendation(symbol, stock_data, sentiment_data):
    """Generate detailed recommendation for a single stock"""
    
    prompt = f"""You are analyzing {symbol} ({stock_data['name']}).

CURRENT DATA:
- Price: ${stock_data['price']}
- Change: {stock_data['change_percent']:+.2f}%
- PE Ratio: {stock_data.get('pe_ratio', 'N/A')}
- Sector: {stock_data.get('sector', 'Unknown')}

SENTIMENT ANALYSIS:
- Overall Sentiment: {sentiment_data['sentiment']} (Score: {sentiment_data['sentiment_score']}/10)
- Key Points: {', '.join(sentiment_data['key_points'][:3])}
- Catalysts: {', '.join(sentiment_data.get('catalysts', ['None']))}
- Risks: {', '.join(sentiment_data.get('risk_factors', ['None']))}

Based on this analysis, provide a trading recommendation. Use the EXACT current price ${stock_data['price']}. Respond with JSON:

{{
  "action": "Strong Buy" or "Moderate Buy" or "Hold" or "Sell",
  "current_price": {stock_data['price']},
  "target_price": estimate based on analysis,
  "rationale": "3-4 sentences explaining why, referencing specific news/catalysts",
  "risk_level": "Low" or "Medium" or "High",
  "timeframe": "1-3 months" or "3-6 months" or "6-12 months",
  "news_catalyst": "primary catalyst from the analysis"
}}"""

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{
                'role': 'user',
                'content': prompt
            }],
            options={'temperature': 0.3, 'num_predict': 600},
            format='json'
        )
        
        result = json.loads(response['message']['content'])
        # Ensure exact price is used
        result['current_price'] = stock_data['price']
        result['ticker'] = symbol
        return result
    except Exception as e:
        print(f"  ⚠️  Recommendation failed for {symbol}: {e}")
        return None

def analyze_with_ollama(market_data):
    """Multi-step analysis optimized for smaller models - Focus on recommendations only"""
    print(f"🤖 Analyzing with Ollama ({OLLAMA_MODEL}) - Multi-Step Approach...")
    
    analysis = {
        'market_overview': '',
        'news_highlights': [],
        'portfolio_health': {'summary': '', 'alerts': []},
        'recommendations': [],
        'action_items': []
    }
    
    try:
        # STEP 1: Market Overview
        print("  📊 Step 1/3: Analyzing market overview...")
        market_news_text = "\n".join([f"- {n['title']}" for n in market_data.get('market_news', [])[:5]])
        indices_text = "\n".join([
            f"- {name}: {data['price']} ({data['change_percent']:+.2f}%)"
            for name, data in market_data.get('market_indices', {}).items()
        ])
        
        overview_prompt = f"""Market Indices Today:
{indices_text}

Top Market News:
{market_news_text}

Provide a brief market analysis. Respond with JSON:

{{
  "market_overview": "3-4 sentence summary of market conditions and key drivers",
  "news_highlights": ["highlight 1", "highlight 2", "highlight 3"]
}}"""

        overview_response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{'role': 'user', 'content': overview_prompt}],
            options={'temperature': 0.3, 'num_predict': 500},
            format='json'
        )
        
        overview_data = json.loads(overview_response['message']['content'])
        analysis['market_overview'] = overview_data.get('market_overview', 'Market data collected.')
        analysis['news_highlights'] = overview_data.get('news_highlights', [])
        
        # STEP 2: Analyze ALL stocks with sentiment
        print(f"  📈 Step 2/3: Analyzing {len(market_data.get('portfolio', {}))} stocks for recommendations...")
        stock_sentiments = {}
        
        for symbol, stock_data in market_data.get('portfolio', {}).items():
            print(f"    → Analyzing {symbol}...")
            sentiment = analyze_news_sentiment(symbol, stock_data, stock_data.get('news', []))
            stock_sentiments[symbol] = sentiment
        
        # STEP 3: Generate recommendations for ALL stocks
        print("  🎯 Step 3/3: Generating recommendations for all stocks...")
        
        all_recommendations = []
        
        for symbol, stock_data in market_data.get('portfolio', {}).items():
            print(f"    → Building recommendation for {symbol}...")
            sentiment = stock_sentiments[symbol]
            
            rec = analyze_stock_recommendation(symbol, stock_data, sentiment)
            if rec:
                # Calculate potential return
                potential_return = ((rec['target_price'] - rec['current_price']) / rec['current_price']) * 100
                rec['potential_return'] = round(potential_return, 2)
                all_recommendations.append(rec)
            else:
                # Create fallback recommendation if analysis failed
                print(f"    ⚠️  Using fallback recommendation for {symbol}")
                # Estimate target based on sentiment
                sentiment_multiplier = 1.0
                if sentiment['sentiment'] == 'Bullish':
                    sentiment_multiplier = 1.08  # 8% upside
                elif sentiment['sentiment'] == 'Bearish':
                    sentiment_multiplier = 0.95  # 5% downside
                else:
                    sentiment_multiplier = 1.02  # 2% neutral
                
                target_price = round(stock_data['price'] * sentiment_multiplier, 2)
                potential_return = ((target_price - stock_data['price']) / stock_data['price']) * 100
                
                all_recommendations.append({
                    'ticker': symbol,
                    'action': 'Hold' if sentiment['sentiment'] == 'Neutral' else 'Moderate Buy' if sentiment['sentiment'] == 'Bullish' else 'Sell',
                    'current_price': stock_data['price'],
                    'target_price': target_price,
                    'rationale': f"{sentiment['sentiment']} outlook based on recent news. " + 
                                (sentiment['key_points'][0] if sentiment.get('key_points') else 'Monitoring developments.'),
                    'risk_level': 'Medium',
                    'timeframe': '3-6 months',
                    'news_catalyst': sentiment.get('catalysts', ['Market conditions'])[0] if sentiment.get('catalysts') else 'Market conditions',
                    'potential_return': round(potential_return, 2)
                })
        
        # Sort by potential return (descending)
        all_recommendations.sort(key=lambda x: x['potential_return'], reverse=True)
        
        analysis['recommendations'] = all_recommendations
        
        # Portfolio Health Assessment
        avg_sentiment = sum(s['sentiment_score'] for s in stock_sentiments.values()) / len(stock_sentiments) if stock_sentiments else 0
        
        bearish_stocks = [s for s, d in stock_sentiments.items() if d['sentiment_score'] < -3]
        bullish_stocks = [s for s, d in stock_sentiments.items() if d['sentiment_score'] > 3]
        
        portfolio_summary = f"Portfolio shows {'positive' if avg_sentiment > 2 else 'neutral' if avg_sentiment > -2 else 'negative'} sentiment overall. "
        portfolio_summary += f"{len(bullish_stocks)} stocks with bullish signals, {len(bearish_stocks)} with bearish signals."
        
        alerts = []
        for symbol in bearish_stocks[:3]:
            risks = stock_sentiments[symbol].get('risk_factors', [])
            if risks:
                alerts.append(f"{symbol}: {risks[0]}")
        
        analysis['portfolio_health'] = {
            'summary': portfolio_summary,
            'alerts': alerts if alerts else ['No major alerts detected']
        }
        
        # Generate Action Items
        action_items = []
        
        # Top opportunities
        if len(all_recommendations) > 0:
            top_pick = all_recommendations[0]
            if top_pick['potential_return'] > 5:
                action_items.append(f"Strong opportunity in {top_pick['ticker']} with {top_pick['potential_return']:.1f}% upside potential")
        
        # Warning for underperformers
        bottom_picks = [r for r in all_recommendations if r['potential_return'] < -3]
        if bottom_picks:
            action_items.append(f"Review positions in {', '.join([r['ticker'] for r in bottom_picks[:2]])} showing negative outlook")
        
        # Actions based on alerts
        if analysis['portfolio_health']['alerts'] and analysis['portfolio_health']['alerts'][0] != 'No major alerts detected':
            action_items.append(f"Monitor risks: {analysis['portfolio_health']['alerts'][0]}")
        
        # General action based on market
        if avg_sentiment > 3:
            action_items.append("Overall market sentiment is positive - consider deploying capital in top picks")
        elif avg_sentiment < -3:
            action_items.append("Market showing caution - consider defensive positioning or profit-taking")
        
        if not action_items:
            action_items = [
                "Continue monitoring portfolio positions",
                "Review upcoming earnings calendar",
                "Stay updated on market news"
            ]
        
        analysis['action_items'] = action_items
        
        print(f"\n✅ Multi-step analysis complete!")
        print(f"   - Recommendations: {len(analysis['recommendations'])} stocks analyzed")
        print(f"   - Top opportunity: {all_recommendations[0]['ticker']} (+{all_recommendations[0]['potential_return']:.1f}%)")
        print(f"   - Avg sentiment score: {avg_sentiment:.1f}/10")
        
        return analysis
        
    except Exception as e:
        print(f"\n❌ Error in multi-step analysis: {e}")
        import traceback
        traceback.print_exc()
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
    
    if analysis and analysis.get('portfolio_health', {}).get('summary'):
        output += f"\n{YELLOW}💭 {analysis['portfolio_health']['summary']}{RESET}\n"
    
    # Alerts
    if analysis and analysis.get('portfolio_health', {}).get('alerts'):
        alerts = analysis['portfolio_health']['alerts']
        if alerts and alerts[0] != 'No major alerts detected':
            output += f"\n{BOLD}{YELLOW}⚠️  ALERTS{RESET}\n"
            output += f"{'-'*80}\n"
            for alert in alerts:
                output += f"  • {alert}\n"
    
    # ALL RECOMMENDATIONS (Ordered by Return)
    if analysis and analysis.get('recommendations'):
        output += f"\n{BOLD}{BLUE}🎯 STOCK RECOMMENDATIONS (Ordered by Potential Return){RESET}\n"
        output += f"{'-'*80}\n"
        
        for i, rec in enumerate(analysis['recommendations'], 1):
            action_colors = {
                'Strong Buy': GREEN,
                'Moderate Buy': CYAN,
                'Hold': YELLOW,
                'Sell': RED
            }
            action_color = action_colors.get(rec['action'], RESET)
            
            return_color = GREEN if rec['potential_return'] > 0 else RED
            
            output += f"\n{BOLD}{i}. {rec['ticker']} - {action_color}{rec['action']}{RESET}\n"
            output += f"   Price: ${rec['current_price']:.2f} → Target: ${rec['target_price']:.2f} "
            output += f"({return_color}{rec['potential_return']:+.1f}%{RESET})\n"
            output += f"   Risk: {rec['risk_level']} | Timeframe: {rec['timeframe']}\n"
            output += f"   📰 Catalyst: {rec.get('news_catalyst', 'N/A')}\n"
            output += f"   💡 {rec['rationale']}\n"
    
    # Action Items
    if analysis and analysis.get('action_items'):
        output += f"\n{BOLD}{BLUE}✅ ACTION ITEMS{RESET}\n"
        output += f"{'-'*80}\n"
        for i, item in enumerate(analysis['action_items'], 1):
            output += f"{i}. {item}\n"
    
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

# Wedbush IVES AI 30 Index components
IVES_AI_30 = [
    'NVDA', 'MSFT', 'TSM', 'AMZN', 'META', 'GOOGL', 'AAPL', 'TSLA', 'AVGO', 'MU',
    'AMD', 'ORCL', 'PLTR', 'BABA', 'IBM', 'SHOP', 'GEV', 'PANW', 'CRWD', 'SNOW',
    'BIDU', 'RBLX', 'MDB', 'ZS', 'CRWV', 'NBIS', 'IREN', 'PEGA', 'OKLO', 'INOD'
]


def collect_ives_data(progress_callback=None):
    """Collect market data and technical indicators for all IVES AI 30 stocks"""
    print("📊 Collecting IVES AI 30 data...")

    data = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'market_indices': {},
        'portfolio': {},
        'market_news': []
    }

    # Market indices
    indices = {'^GSPC': 'S&P 500', '^IXIC': 'NASDAQ', '^VIX': 'VIX'}
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

    data['market_news'] = fetch_market_news(max_articles=ARTICLE_COUNT)

    total = len(IVES_AI_30)
    for idx, symbol in enumerate(IVES_AI_30, 1):
        if progress_callback:
            progress_callback(idx, total, symbol)
        try:
            print(f"  [{idx}/{total}] Fetching {symbol}...")
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get 1 month of history for trend analysis
            hist = ticker.history(period='1mo')
            if hist.empty or len(hist) < 5:
                print(f"    ⚠️  Insufficient data for {symbol}")
                continue

            current = hist['Close'].iloc[-1]
            previous = hist['Close'].iloc[-2]
            daily_change = ((current - previous) / previous) * 100

            # Technical indicators for downtrend/recovery detection
            month_high = hist['Close'].max()
            month_low = hist['Close'].min()
            drawdown_from_high = ((current - month_high) / month_high) * 100

            # Simple moving averages
            sma_5 = hist['Close'].iloc[-5:].mean()
            sma_20 = hist['Close'].mean()  # ~20 trading days in a month

            # Recent momentum: last 3 days vs prior 3 days
            if len(hist) >= 6:
                recent_avg = hist['Close'].iloc[-3:].mean()
                prior_avg = hist['Close'].iloc[-6:-3].mean()
                momentum = ((recent_avg - prior_avg) / prior_avg) * 100
            else:
                momentum = 0

            # Volume trend
            if len(hist) >= 10:
                recent_vol = hist['Volume'].iloc[-5:].mean()
                prior_vol = hist['Volume'].iloc[-10:-5].mean()
                volume_change = ((recent_vol - prior_vol) / prior_vol) * 100 if prior_vol > 0 else 0
            else:
                volume_change = 0

            company_name = info.get('longName', symbol)
            news = fetch_news_for_stock(symbol, company_name, max_articles=ARTICLE_COUNT)

            data['portfolio'][symbol] = {
                'name': company_name,
                'price': round(current, 2),
                'change_percent': round(daily_change, 2),
                'volume': int(hist['Volume'].iloc[-1]),
                'market_cap': info.get('marketCap', 'N/A'),
                'pe_ratio': round(info.get('trailingPE', 0), 2) if info.get('trailingPE') else 'N/A',
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'news': news,
                'news_count': len(news),
                # Technical indicators
                'month_high': round(month_high, 2),
                'month_low': round(month_low, 2),
                'drawdown_from_high': round(drawdown_from_high, 2),
                'sma_5': round(sma_5, 2),
                'sma_20': round(sma_20, 2),
                'sma_crossover': 'bullish' if sma_5 > sma_20 else 'bearish',
                'momentum_3d': round(momentum, 2),
                'volume_change': round(volume_change, 2),
            }

        except Exception as e:
            print(f"  ⚠️  Error fetching {symbol}: {e}")

    print(f"✅ Collected data for {len(data['portfolio'])} IVES stocks")
    return data


def screen_ives_candidates(market_data):
    """Screen all IVES stocks for highest short-term return potential (any pattern)"""
    print("🔍 Screening IVES stocks for top opportunities...")

    candidates = []
    for symbol, sd in market_data.get('portfolio', {}).items():
        score = 0

        momentum = sd.get('momentum_3d', 0)
        drawdown = sd.get('drawdown_from_high', 0)
        vol_change = sd.get('volume_change', 0)
        daily = sd.get('change_percent', 0)
        bullish_cross = sd.get('sma_crossover') == 'bullish'

        # --- Uptrend / strong momentum stocks ---
        if momentum > 3:
            score += 4  # strong upward momentum
        elif momentum > 1:
            score += 2

        # Near month high = strong uptrend
        if drawdown > -2:
            score += 2  # trading near highs, trend intact

        # --- Recovery / bounce-back stocks ---
        if drawdown < -5 and momentum > 0:
            score += 4  # meaningful pullback + turning around
        elif drawdown < -3 and momentum > 0:
            score += 2

        # --- Common positive signals ---
        if bullish_cross:
            score += 2

        if vol_change > 20:
            score += 2  # strong accumulation
        elif vol_change > 0:
            score += 1

        if daily > 1:
            score += 2
        elif daily > 0:
            score += 1

        candidates.append({
            'symbol': symbol,
            'score': score,
            'data': sd
        })

    candidates.sort(key=lambda x: x['score'], reverse=True)
    top_candidates = candidates[:15]

    print(f"  Top candidates: {', '.join([c['symbol'] for c in top_candidates])}")
    return top_candidates


def analyze_ives_top_picks(market_data, candidates):
    """Use LLM to analyze top candidates and produce final top 10 picks"""
    print(f"🤖 Analyzing top IVES candidates with Ollama ({OLLAMA_MODEL})...")

    analysis = {
        'market_overview': '',
        'news_highlights': [],
        'portfolio_health': {'summary': '', 'alerts': []},
        'recommendations': [],
        'action_items': []
    }

    try:
        # Step 1: Market overview
        print("  📊 Step 1/3: Market overview...")
        market_news_text = "\n".join([f"- {n['title']}" for n in market_data.get('market_news', [])[:5]])
        indices_text = "\n".join([
            f"- {name}: {d['price']} ({d['change_percent']:+.2f}%)"
            for name, d in market_data.get('market_indices', {}).items()
        ])

        overview_response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{'role': 'user', 'content': f"""Market Indices Today:
{indices_text}

Top Market News:
{market_news_text}

Provide a brief AI sector market analysis focusing on the Wedbush AI Revolution theme. Respond with JSON:

{{
  "market_overview": "3-4 sentence summary of AI sector conditions and key drivers",
  "news_highlights": ["highlight 1", "highlight 2", "highlight 3"]
}}"""}],
            options={'temperature': 0.3, 'num_predict': 500},
            format='json'
        )
        overview_data = json.loads(overview_response['message']['content'])
        analysis['market_overview'] = overview_data.get('market_overview', '')
        analysis['news_highlights'] = overview_data.get('news_highlights', [])

        # Step 2: Sentiment for each candidate
        print(f"  📈 Step 2/3: Analyzing {len(candidates)} candidates...")
        sentiments = {}
        for c in candidates:
            sym = c['symbol']
            sd = c['data']
            print(f"    → Analyzing {sym}...")
            sentiment = analyze_news_sentiment(sym, sd, sd.get('news', []))
            sentiments[sym] = sentiment

        # Step 3: Ask LLM to pick top 10 highest-return plays
        print("  🎯 Step 3/3: Selecting top 10 picks...")

        candidate_summary = ""
        for c in candidates:
            sym = c['symbol']
            sd = c['data']
            s = sentiments[sym]
            candidate_summary += f"""
{sym} ({sd['name']}):
  Price: ${sd['price']} | Daily: {sd['change_percent']:+.2f}% | Drawdown from high: {sd['drawdown_from_high']:.1f}%
  SMA5: ${sd['sma_5']} | SMA20: ${sd['sma_20']} | Crossover: {sd['sma_crossover']}
  3-day momentum: {sd['momentum_3d']:+.2f}% | Volume change: {sd['volume_change']:+.1f}%
  Sentiment: {s['sentiment']} ({s['sentiment_score']}/10)
  Key news: {s['key_points'][0] if s.get('key_points') else 'None'}
  Catalysts: {', '.join(s.get('catalysts', ['None'])[:2])}
  Risks: {', '.join(s.get('risk_factors', ['None'])[:2])}
"""

        pick_prompt = f"""You are a short-term trading analyst. From these Wedbush AI Revolution Index stocks, select exactly 10 that have the HIGHEST potential for short-term returns (1-4 weeks).

Consider ALL types of opportunities:
1. RECOVERY PLAYS: Stocks in a pullback showing signs of reversal (negative drawdown but positive momentum, bullish SMA crossover, positive news catalysts)
2. MOMENTUM PLAYS: Stocks in a strong uptrend with continuing momentum (near monthly highs, strong 3-day momentum, increasing volume)
3. CATALYST-DRIVEN: Stocks with strong positive news catalysts regardless of current trend

Pick the 10 stocks with the highest expected short-term return from ANY of these patterns.

CANDIDATES:
{candidate_summary}

For each pick, use the EXACT current price provided. Estimate a realistic target price for a 1-4 week timeframe.

Respond with ONLY this JSON:
{{
  "picks": [
    {{
      "ticker": "SYMBOL",
      "action": "Strong Buy" or "Moderate Buy",
      "current_price": exact price from data,
      "target_price": your estimate,
      "rationale": "2-3 sentences explaining the opportunity thesis and catalysts",
      "risk_level": "Low" or "Medium" or "High",
      "timeframe": "1-2 weeks" or "2-4 weeks",
      "news_catalyst": "primary catalyst"
    }}
  ]
}}

Return exactly 10 picks ordered by highest expected return first."""

        pick_response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{
                'role': 'system',
                'content': 'You are a short-term trading analyst specializing in AI sector recovery plays. Use exact prices from data. Respond only with valid JSON.'
            }, {
                'role': 'user',
                'content': pick_prompt
            }],
            options={'temperature': 0.3, 'num_predict': 4000, 'top_p': 0.9},
            format='json'
        )

        pick_text = pick_response['message']['content'].strip()
        if '{' in pick_text:
            pick_text = pick_text[pick_text.find('{'):pick_text.rfind('}') + 1]
        pick_data = json.loads(pick_text)

        picks = pick_data.get('picks', [])[:10]

        # Validate and enrich
        for rec in picks:
            ticker = rec.get('ticker', '')
            if ticker in market_data.get('portfolio', {}):
                actual_price = market_data['portfolio'][ticker]['price']
                rec['current_price'] = actual_price
                if isinstance(rec.get('target_price'), (int, float)) and actual_price > 0:
                    rec['potential_return'] = round(((rec['target_price'] - actual_price) / actual_price) * 100, 2)
                else:
                    rec['potential_return'] = 0
            else:
                rec['potential_return'] = 0

        picks.sort(key=lambda x: x.get('potential_return', 0), reverse=True)
        analysis['recommendations'] = picks

        # Portfolio health
        avg_sentiment = sum(s['sentiment_score'] for s in sentiments.values()) / len(sentiments) if sentiments else 0
        bearish = [s for s, d in sentiments.items() if d['sentiment_score'] < -3]
        bullish = [s for s, d in sentiments.items() if d['sentiment_score'] > 3]
        analysis['portfolio_health'] = {
            'summary': f"IVES AI 30 scan shows {len(bullish)} bullish, {len(bearish)} bearish stocks. Average sentiment: {avg_sentiment:.1f}/10.",
            'alerts': [f"{s}: bearish signals" for s in bearish[:3]] or ['No major alerts']
        }

        # Action items
        if picks:
            analysis['action_items'] = [
                f"Top recovery play: {picks[0]['ticker']} with {picks[0].get('potential_return', 0):.1f}% upside potential",
                f"Monitor these AI sector recovery candidates for entry points",
                f"Set stop-losses given short-term nature of these trades"
            ]
        else:
            analysis['action_items'] = ['No strong recovery candidates found - wait for better setups']

        print(f"\n✅ IVES analysis complete! Top pick: {picks[0]['ticker'] if picks else 'None'}")
        return analysis

    except Exception as e:
        print(f"\n❌ Error in IVES analysis: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_ives_scan(progress_callback=None):
    """Run complete IVES AI 30 scan and return top 10 recovery picks"""
    print(f"\n{'='*80}")
    print("🚀 Starting Wedbush IVES AI 30 Recovery Scan")
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    market_data = collect_ives_data(progress_callback=progress_callback)
    candidates = screen_ives_candidates(market_data)
    analysis = analyze_ives_top_picks(market_data, candidates)
    return market_data, analysis


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
        analysis = analyze_with_ollama(market_data)
        
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