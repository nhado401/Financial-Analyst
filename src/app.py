# app.py
import streamlit as st
import os
import sys
from dotenv import load_dotenv
import json

# First, set up default stocks and session state
if 'selected_stocks' not in st.session_state:
    st.session_state.selected_stocks = []

# Set the environment variable before importing analyst
os.environ['PORTFOLIO'] = ','.join(st.session_state.selected_stocks)

# Now import the analyst module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.analyst import (
    collect_market_data, analyze_with_ollama,
    run_ives_scan, IVES_AI_30
)

# Page config
st.set_page_config(
    page_title="Market Analysis Dashboard",
    page_icon="📈",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stock-card {
        padding: 1.5rem;
        border-radius: 10px;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .positive {
        color: #2E7D32;
    }
    .negative {
        color: #C62828;
    }
    .analysis-section {
        background-color: #f1f8e9;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)


def display_analysis_results(analysis):
    """Shared display logic for analysis results"""
    # Market Overview
    st.markdown("### 📈 Market Overview")
    st.markdown(analysis.get('market_overview', 'No market overview available.'))

    # News Highlights
    st.markdown("### 📰 Top News Highlights")
    highlights = analysis.get('news_highlights', [])
    if highlights:
        for i, highlight in enumerate(highlights[:5], 1):
            st.markdown(f"{i}. {highlight}")
    else:
        st.info("No news highlights available.")

    # Portfolio Health
    health = analysis.get('portfolio_health', {})
    if health.get('summary'):
        st.markdown("### 🏥 Portfolio Health")
        st.markdown(health['summary'])
        alerts = health.get('alerts', [])
        if alerts and alerts[0] != 'No major alerts detected' and alerts[0] != 'No major alerts':
            for alert in alerts:
                st.warning(alert)


def display_recommendations(analysis, max_recs=None):
    """Display recommendation cards"""
    recommendations = analysis.get('recommendations', [])
    if not recommendations:
        st.info("No specific recommendations available at this time.")
        return

    if max_recs:
        recommendations = recommendations[:max_recs]

    for i, rec in enumerate(recommendations, 1):
        potential = rec.get('potential_return', 0)
        action = rec.get('action', 'Hold')
        color_map = {
            'Strong Buy': '🟢', 'Moderate Buy': '🔵',
            'Hold': '🟡', 'Sell': '🔴'
        }
        icon = color_map.get(action, '⚪')

        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"#### {icon} {i}. {rec.get('ticker', '')} — {action}")
                st.markdown(f"**Current:** ${rec.get('current_price', 'N/A')} → "
                            f"**Target:** ${rec.get('target_price', 'N/A')} "
                            f"({'🟢' if potential > 0 else '🔴'} {potential:+.1f}%)")
                st.markdown(f"**Risk:** {rec.get('risk_level', 'N/A')} | "
                            f"**Timeframe:** {rec.get('timeframe', 'N/A')}")
                if rec.get('news_catalyst'):
                    st.markdown(f"**📰 Catalyst:** {rec['news_catalyst']}")
                st.markdown(f"*{rec.get('rationale', '')}*")
            with col2:
                if potential > 10:
                    st.metric("Potential", f"{potential:+.1f}%", delta=f"{potential:.1f}%")
                elif potential > 0:
                    st.metric("Potential", f"{potential:+.1f}%", delta=f"{potential:.1f}%")
                else:
                    st.metric("Potential", f"{potential:+.1f}%", delta=f"{potential:.1f}%", delta_color="inverse")
            st.divider()


def run_manual_analysis():
    """Original manual stock picker analysis"""
    st.sidebar.header("Stock Selection")

    default_stocks = ['SBUX', 'MSFT', 'SNOW', 'NVDA', 'TSLA', 'UNH', 'JEPQ', 'NFLX', 'T', 'AAPL', 'META', 'GOOGL']

    selected_stocks = st.sidebar.multiselect(
        "Select stocks to analyze (max 10)",
        options=default_stocks,
        default=[],
        max_selections=10
    )

    custom_stock = st.sidebar.text_input("Or add a custom stock symbol (e.g., T, BRK.A):")
    if custom_stock and custom_stock not in selected_stocks and len(selected_stocks) < 10:
        selected_stocks.append(custom_stock.upper())

    analyze_clicked = st.sidebar.button("Analyze Market", type="primary", use_container_width=True)

    if not selected_stocks:
        st.warning("Please select at least one stock to analyze.")
        return

    if analyze_clicked:
        with st.spinner("🔍 Collecting market data and analyzing..."):
            try:
                os.environ['PORTFOLIO'] = ','.join(selected_stocks)
                market_data = collect_market_data()
                analysis = analyze_with_ollama(market_data)

                if analysis:
                    st.markdown("## 📊 Your Daily Market Brief")
                    st.markdown("---")

                    display_analysis_results(analysis)

                    # Stock Analysis
                    st.markdown("### 📊 Stock Analysis")
                    stock_analysis = analysis.get('stock_analysis', [])
                    if stock_analysis:
                        for stock in stock_analysis:
                            with st.expander(f"{stock.get('ticker', '')} - {stock.get('sentiment', '')}"):
                                st.markdown(f"**Key News:** {stock.get('key_news', 'No news available.')}")
                                st.markdown(f"**Analysis:** {stock.get('analysis', 'No analysis available.')}")
                    else:
                        st.info("No stock analysis available for the selected stocks.")

                    st.markdown("### 💡 Investment Recommendations")
                    display_recommendations(analysis, max_recs=3)

                    action_items = analysis.get('action_items', [])
                    if action_items:
                        st.markdown("### ✅ Action Items")
                        for item in action_items:
                            st.markdown(f"- {item}")
                    else:
                        st.markdown("### ℹ️ No specific action items at this time.")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.exception(e)


def run_ives_analysis():
    """Automated IVES AI 30 scan for recovery plays"""
    st.markdown("### 🤖 Wedbush IVES AI Revolution Index 30")
    st.markdown(
        "Scans all 30 stocks in the Dan Ives AI Revolution Index, analyzes momentum, "
        "recovery signals, and news catalysts, then returns the **top 10** highest short-term return opportunities."
    )

    st.markdown("**Index components:** " + ", ".join(IVES_AI_30))

    scan_clicked = st.button("🚀 Run IVES AI 30 Scan", type="primary", use_container_width=True)

    if scan_clicked:
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(current, total, symbol):
            progress_bar.progress(current / total)
            status_text.text(f"Fetching {symbol}... ({current}/{total})")

        with st.spinner("🔍 Scanning all 30 IVES AI stocks..."):
            try:
                market_data, analysis = run_ives_scan(progress_callback=update_progress)
                progress_bar.progress(1.0)
                status_text.text("Analysis complete!")

                if analysis:
                    st.markdown("---")
                    st.markdown("## 🎯 IVES AI 30 — Top 10 Highest Return Picks")

                    display_analysis_results(analysis)

                    st.markdown("### 🏆 Top 10 Short-Term Opportunities")
                    display_recommendations(analysis, max_recs=10)

                    action_items = analysis.get('action_items', [])
                    if action_items:
                        st.markdown("### ✅ Action Items")
                        for item in action_items:
                            st.markdown(f"- {item}")

                    st.markdown("---")
                    st.caption("⚠️ This is not financial advice. Always do your own research before trading.")
                else:
                    st.error("Analysis returned no results. Check that Ollama is running.")

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.exception(e)


def main():
    st.markdown('<h1 class="main-header">📈 Market Analysis Dashboard</h1>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔍 Manual Stock Analysis", "🤖 IVES AI 30 Scanner"])

    with tab1:
        run_manual_analysis()

    with tab2:
        run_ives_analysis()


if __name__ == "__main__":
    load_dotenv()
    main()
