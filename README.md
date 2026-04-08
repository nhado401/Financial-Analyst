# 📈 Financial Market Analyst

A powerful Python-based tool for real-time financial market analysis, news aggregation, and AI-powered insights. Track your portfolio, analyze market trends, and get actionable investment recommendations — available as both a CLI tool and an interactive Streamlit dashboard.

## ✨ Features

- **Market Data**: Real-time stock prices, indices, and market trends
- **News Analysis**: Aggregates and analyzes financial news from multiple sources
- **Portfolio Tracking**: Monitor your stock portfolio performance
- **AI-Powered Insights**: Get intelligent analysis using Ollama (local LLM)
- **Sentiment Analysis**: Understand market sentiment for your stocks
- **Customizable Watchlists**: Track specific stocks and sectors
- **IVES AI 30 Scanner**: Automated scan of all 30 stocks in the Wedbush Dan Ives AI Revolution Index — analyzes momentum, recovery signals, and news catalysts to surface the top 10 short-term return opportunities
- **Streamlit Dashboard**: Interactive web UI with two modes — manual stock analysis and the IVES AI 30 scanner

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip (Python package manager)
- [Ollama](https://ollama.com/) installed and running locally

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/nhado401/financial-analyst.git
   cd financial-analyst
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. Make sure Ollama is running:
   ```bash
   ollama serve
   ```

## 🛠️ Configuration

### Environment Variables

Create a `.env` file in the root directory with the following:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### Portfolio Configuration

Edit the `PORTFOLIO` list in `src/analyst.py` to track your stocks:

```python
PORTFOLIO = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']  # Add your stocks here
```

## 🏃 Running the Application

### CLI Mode

```bash
python src/analyst.py
```

The CLI will fetch market data, collect relevant news, generate analysis, and display results in the terminal.

### Streamlit Dashboard

```bash
streamlit run src/app.py
```

This launches an interactive web dashboard at `http://localhost:8501` with two tabs:

1. **Manual Stock Analysis** — Pick stocks from a default list or enter custom tickers (up to 10), then click "Analyze Market" to get a full market brief with stock-level sentiment, recommendations, and action items.
2. **IVES AI 30 Scanner** — One-click scan of all 30 stocks in the Wedbush Dan Ives AI Revolution Index. The scanner fetches live data with a progress bar, runs AI analysis, and returns the top 10 highest short-term return opportunities with price targets, risk levels, and news catalysts.

## 📊 Features in Detail

### Market Overview
- Real-time S&P 500, NASDAQ, and VIX data
- Market sentiment analysis
- Key news highlights

### Stock Analysis
- Individual stock performance
- News sentiment
- Price targets and recommendations
- Risk assessment

### Portfolio Management
- Track multiple stocks
- Performance metrics
- News aggregation by stock

### IVES AI 30 Index Scanner

The IVES AI 30 scanner covers these stocks:

> NVDA, MSFT, TSM, AMZN, META, GOOGL, AAPL, TSLA, AVGO, MU, AMD, ORCL, PLTR, BABA, IBM, SHOP, GEV, PANW, CRWD, SNOW, NOW, MRVL, DELL, ARM, ADBE, INTU, CRM, DDOG, NET, ZS

For each stock it collects:
- Current price, 52-week high/low, and distance from highs
- RSI, 50-day and 200-day moving averages
- Recent news and catalysts

The AI then ranks all 30 and returns the **top 10** picks with action ratings (Strong Buy / Moderate Buy / Hold / Sell), target prices, potential return percentages, risk levels, and timeframes.

## 🤖 AI-Powered Analysis

The tool uses Ollama (local LLM) to analyze market conditions and provide:
- Investment opportunities
- Risk assessments
- Actionable insights
- Market trend predictions

## 🙏 Acknowledgments

- [yfinance](https://pypi.org/project/yfinance/) for market data
- [Ollama](https://ollama.com/) for local AI analysis
- [Streamlit](https://streamlit.io/) for the interactive dashboard
- [Feedparser](https://pypi.org/project/feedparser/) for RSS feeds

## 📬 Contact

[Nha Do] - [nhado401@gmail.com]
Project Link: [https://github.com/nhado401/financial-analyst](https://github.com/nhado401/financial-analyst)  
