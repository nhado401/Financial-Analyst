# 📈 Financial Market Analyst

A powerful Python-based tool for real-time financial market analysis, news aggregation, and AI-powered insights. Track your portfolio, analyze market trends, and get actionable investment recommendations.

## ✨ Features

- **Market Data**: Real-time stock prices, indices, and market trends
- **News Analysis**: Aggregates and analyzes financial news from multiple sources
- **Portfolio Tracking**: Monitor your stock portfolio performance
- **AI-Powered Insights**: Get intelligent analysis using Groq AI
- **Sentiment Analysis**: Understand market sentiment for your stocks
- **Customizable Watchlists**: Track specific stocks and sectors

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip (Python package manager)

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

## 🛠️ Configuration

### Environment Variables

Create a `.env` file in the root directory with the following:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### Portfolio Configuration

Edit the `PORTFOLIO` list in `analyst.py` to track your stocks:

```python
PORTFOLIO = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']  # Add your stocks here
```

## 🏃 Running the Application

```bash
python analyst.py
```

The application will:
- Fetch market data
- Collect relevant news
- Generate analysis
- Display results in the terminal

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

## 🤖 AI-Powered Analysis

The tool uses Groq AI to analyze market conditions and provide:
- Investment opportunities
- Risk assessments
- Actionable insights
- Market trend predictions

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [yfinance](https://pypi.org/project/yfinance/) for market data
- [Groq](https://groq.com/) for AI analysis
- [Feedparser](https://pypi.org/project/feedparser/) for RSS feeds

## 📬 Contact

[Nha Do] - [nhado401@gmail.com]  
Project Link: [https://github.com/nhado401/financial-analyst](https://github.com/nhado401/financial-analyst)
