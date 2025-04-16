import streamlit as st

# Set page config - MUST be the first Streamlit command
st.set_page_config(
    page_title="Stock Analysis with Gemini Flash 2.0",
    page_icon="📈",
    layout="wide"
)

import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

from mount.src.stockanalysis.utils.stock_data import get_stock_data, get_company_info, get_financial_metrics
from mount.src.stockanalysis.utils.gemini_analysis import generate_stock_analysis
from mount.src.stockanalysis.utils.visualization import plot_stock_chart
from mount.src.stockanalysis.utils.news_collector import get_news_for_asset, summarize_news_sentiment

# Main title
st.title("📊 Financial Asset Analysis with Gemini AI")

# Description
st.markdown("""
This application provides in-depth analysis for stocks and cryptocurrencies using Google's Gemini AI.
Enter a symbol to get buy/sell recommendations and detailed information:

**Stocks**:
- US Stocks: Enter the ticker symbol (e.g., AAPL, MSFT, GOOGL)
- Indonesian Stocks: Use IDX: prefix (e.g., IDX:BBCA, IDX:ADRO)

**Cryptocurrencies**:
- Enter the crypto symbol with USD suffix (e.g., BTC-USD, ETH-USD, SOL-USD)
""")

# Initialize session state for API key
if 'GEMINI_API_KEY' not in st.session_state:
    st.session_state['GEMINI_API_KEY'] = ""

# API key input in a collapsible section
with st.expander("Configure Google Gemini API", expanded=not st.session_state['GEMINI_API_KEY']):
    st.write("To use the AI analysis features, you need to provide a Google Gemini API key.")
    
    # Add a form for the API key
    with st.form("api_key_form"):
        api_key_input = st.text_input(
            "Enter your Google Gemini API key",
            value=st.session_state['GEMINI_API_KEY'],
            type="password",
            help="Get your API key from https://aistudio.google.com/"
        )
        
        submitted = st.form_submit_button("Save API Key")
        
        if submitted and api_key_input:
            st.session_state['GEMINI_API_KEY'] = api_key_input
            st.success("API key saved successfully! You can now use AI analysis features.")
    
    st.info("Your API key is stored in your session only and will be cleared when you close the browser. It is not stored on our servers.")

# Input for stock symbol
with st.form(key='stock_form'):
    col1, col2 = st.columns([3, 1])
    
    with col1:
        stock_symbol = st.text_input(
            "Enter Symbol (e.g., AAPL, IDX:BBCA, BTC-USD)",
            placeholder="Stocks or Crypto"
        )
    
    with col2:
        submit_button = st.form_submit_button(label="Analyze Asset", use_container_width=True)

# Process the stock analysis when form is submitted
if submit_button and stock_symbol:
    
    with st.spinner(f"Analyzing {stock_symbol}..."):
        try:
            # Get stock data
            # Get fresh data with the latest period
            stock_data = get_stock_data(stock_symbol, period="max")
            
            if stock_data is not None:
                # Focus on the most recent data for display (last 1 year)
                if len(stock_data) > 252:  # Approx 1 year of trading days
                    display_data = stock_data.tail(252)
                else:
                    display_data = stock_data
                # Create tabs for different sections
                tab1, tab2, tab3, tab4 = st.tabs(["Analysis & Recommendation", "Company Information", "Financial Metrics", "News & Sentiment"])
                
                with tab1:
                    # Display stock chart
                    st.subheader(f"{stock_symbol} Price Chart")
                    fig = plot_stock_chart(display_data)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Generate and display AI analysis
                    is_crypto = "-" in stock_symbol.upper()
                    asset_type = "Cryptocurrency" if is_crypto else "Stock"
                    st.subheader(f"Gemini AI {asset_type} Analysis")
                    
                    # Get company info and metrics for better analysis
                    company_info = get_company_info(stock_symbol)
                    financial_metrics = get_financial_metrics(stock_symbol)
                    
                    # Get news articles for better analysis
                    news_articles = get_news_for_asset(stock_symbol, max_articles=5)
                    
                    # Generate analysis with news articles included
                    analysis_result = generate_stock_analysis(stock_symbol, stock_data, company_info, financial_metrics, news_articles)
                    
                    # Display recommendation prominently
                    recommendation = analysis_result.get("recommendation", "NEUTRAL")
                    
                    # Color-code recommendation
                    if recommendation == "BUY":
                        st.success(f"## Recommendation: {recommendation} 📈")
                    elif recommendation == "SELL":
                        st.error(f"## Recommendation: {recommendation} 📉")
                    else:
                        st.info(f"## Recommendation: {recommendation} ⚖️")
                    
                    # Display analysis summary
                    st.markdown("### Analysis Summary")
                    st.write(analysis_result.get("summary", "No summary available"))
                    
                    # Display risk factors
                    st.markdown("### Risk Factors")
                    risk_factors = analysis_result.get("risk_factors", [])
                    for factor in risk_factors:
                        st.markdown(f"- {factor}")
                    
                    # Display supporting data
                    with st.expander("Detailed Analysis"):
                        st.write(analysis_result.get("detailed_analysis", "No detailed analysis available"))
                
                with tab2:
                    is_crypto = "-" in stock_symbol.upper()
                    if is_crypto:
                        st.subheader(f"About {stock_symbol}")
                        
                        if company_info:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**Name:**", company_info.get("longName", stock_symbol))
                                st.write("**Category:**", "Cryptocurrency")
                                st.write("**Symbol:**", stock_symbol)
                                st.write("**Market:**", "Cryptocurrency")
                            
                            with col2:
                                st.write("**Market Cap:**", company_info.get("marketCap", "N/A"))
                                st.write("**Volume (24h):**", company_info.get("volume24Hr", "N/A"))
                                st.write("**Circulating Supply:**", company_info.get("circulatingSupply", "N/A"))
                            
                            st.markdown("### Description")
                            st.write(company_info.get("description", company_info.get("longBusinessSummary", "No description available")))
                        else:
                            st.warning("Cryptocurrency information not available")
                    else:
                        st.subheader(f"About {stock_symbol}")
                        
                        if company_info:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**Company Name:**", company_info.get("longName", "N/A"))
                                st.write("**Sector:**", company_info.get("sector", "N/A"))
                                st.write("**Industry:**", company_info.get("industry", "N/A"))
                                st.write("**Country:**", company_info.get("country", "N/A"))
                                st.write("**Exchange:**", company_info.get("exchange", "N/A"))
                            
                            with col2:
                                st.write("**Market Cap:**", company_info.get("marketCap", "N/A"))
                                st.write("**Employees:**", company_info.get("fullTimeEmployees", "N/A"))
                                st.write("**Website:**", company_info.get("website", "N/A"))
                            
                            st.markdown("### Business Summary")
                            st.write(company_info.get("longBusinessSummary", "No business summary available"))
                        else:
                            st.warning("Company information not available")
                
                with tab3:
                    is_crypto = "-" in stock_symbol.upper()
                    asset_type = "Cryptocurrency" if is_crypto else "Financial"
                    st.subheader(f"{stock_symbol} {asset_type} Metrics")
                    
                    if financial_metrics:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            is_crypto = "-" in stock_symbol.upper()
                            
                            st.metric("Current Price", financial_metrics.get("currentPrice", "N/A"))
                            
                            if is_crypto:
                                st.metric("24h Change", f"{financial_metrics.get('regularMarketChangePercent', 0) * 100:.2f}%" if financial_metrics.get('regularMarketChangePercent') else "N/A")
                                st.metric("24h Volume", financial_metrics.get("volume24Hr", financial_metrics.get("volume", "N/A")))
                                st.metric("Market Cap", financial_metrics.get("marketCap", "N/A"))
                                st.metric("Circulating Supply", financial_metrics.get("circulatingSupply", "N/A"))
                            else:
                                st.metric("P/E Ratio", financial_metrics.get("trailingPE", "N/A"))
                                st.metric("Dividend Yield", f"{financial_metrics.get('dividendYield', 0) * 100:.2f}%" if financial_metrics.get('dividendYield') else "N/A")
                                st.metric("52 Week High", financial_metrics.get("fiftyTwoWeekHigh", "N/A"))
                                st.metric("52 Week Low", financial_metrics.get("fiftyTwoWeekLow", "N/A"))
                        
                        with col2:
                            is_crypto = "-" in stock_symbol.upper()
                            
                            if is_crypto:
                                st.metric("All-Time High", financial_metrics.get("fiftyTwoWeekHigh", "N/A"))
                                st.metric("All-Time Low", financial_metrics.get("fiftyTwoWeekLow", "N/A"))
                                st.metric("Max Supply", financial_metrics.get("maxSupply", "N/A"))
                                st.metric("Total Supply", financial_metrics.get("totalSupply", "N/A"))
                                st.metric("Volume Ratio", financial_metrics.get("averageDailyVolume10Day", "N/A"))
                            else:
                                st.metric("EPS", financial_metrics.get("trailingEps", "N/A"))
                                st.metric("Price to Book", financial_metrics.get("priceToBook", "N/A"))
                                st.metric("Return on Equity", f"{financial_metrics.get('returnOnEquity', 0) * 100:.2f}%" if financial_metrics.get('returnOnEquity') else "N/A")
                                st.metric("Profit Margins", f"{financial_metrics.get('profitMargins', 0) * 100:.2f}%" if financial_metrics.get('profitMargins') else "N/A")
                                st.metric("Debt to Equity", financial_metrics.get("debtToEquity", "N/A"))
                        
                        # Add additional financial metrics in an expander
                        with st.expander("More Financial Metrics"):
                            is_crypto = "-" in stock_symbol.upper()
                            
                            if is_crypto:
                                # Cryptocurrency specific metrics
                                st.write("**Market Dominance:**", financial_metrics.get('marketDominance', 'N/A'))
                                st.write("**Trading Volume:**", financial_metrics.get('volume', 'N/A'))
                                st.write("**Avg Volume (3m):**", financial_metrics.get('averageVolume3Months', 'N/A'))
                                st.write("**Avg Volume (10d):**", financial_metrics.get('averageDailyVolume10Day', 'N/A'))
                                st.write("**Beta:**", financial_metrics.get('beta', 'N/A'))
                                st.write("**YTD Return:**", financial_metrics.get('ytdReturn', 'N/A'))
                            else:
                                # Stock specific metrics
                                revenueGrowth = f"{financial_metrics.get('revenueGrowth', 0) * 100:.2f}%" if financial_metrics.get('revenueGrowth') is not None else "N/A"
                                grossMargins = f"{financial_metrics.get('grossMargins', 0) * 100:.2f}%" if financial_metrics.get('grossMargins') is not None else "N/A"
                                operatingMargins = f"{financial_metrics.get('operatingMargins', 0) * 100:.2f}%" if financial_metrics.get('operatingMargins') is not None else "N/A"
                                
                                st.write("**Revenue Growth:**", revenueGrowth)
                                st.write("**Gross Margins:**", grossMargins)
                                st.write("**Operating Margins:**", operatingMargins)
                                st.write("**Quick Ratio:**", financial_metrics.get('quickRatio', 'N/A'))
                                st.write("**Current Ratio:**", financial_metrics.get('currentRatio', 'N/A'))
                                st.write("**Beta:**", financial_metrics.get('beta', 'N/A'))
                                st.write("**Shares Outstanding:**", financial_metrics.get('sharesOutstanding', 'N/A'))
                                st.write("**Book Value:**", financial_metrics.get('bookValue', 'N/A'))
                                st.write("**Target Mean Price:**", financial_metrics.get('targetMeanPrice', 'N/A'))
                    else:
                        st.warning("Financial metrics not available")
                
                with tab4:
                    st.subheader(f"{stock_symbol} News & Sentiment Analysis")
                    
                    with st.spinner("Fetching latest news..."):
                        # Get news articles
                        news_articles = get_news_for_asset(stock_symbol, max_articles=5)
                        
                        if news_articles:
                            # Get sentiment analysis
                            sentiment_results = summarize_news_sentiment(news_articles)
                            sentiment_score = sentiment_results.get("sentiment_score", 0)
                            sentiment_trend = sentiment_results.get("trend", "neutral")
                            sentiment_summary = sentiment_results.get("summary", "No news analysis available")
                            
                            # Display sentiment summary
                            st.markdown("### Market Sentiment")
                            
                            # Create a color for the sentiment
                            if sentiment_trend == "strongly positive":
                                sentiment_color = "darkgreen"
                            elif sentiment_trend == "positive":
                                sentiment_color = "green"
                            elif sentiment_trend == "strongly negative":
                                sentiment_color = "darkred"
                            elif sentiment_trend == "negative":
                                sentiment_color = "red"
                            else:
                                sentiment_color = "grey"
                            
                            st.markdown(f"<h4 style='color: {sentiment_color};'>Sentiment: {sentiment_trend.title()} ({sentiment_score:+.2f})</h4>", unsafe_allow_html=True)
                            st.write(sentiment_summary)
                            
                            # Display key topics
                            key_topics = sentiment_results.get("key_topics", [])
                            if key_topics:
                                st.markdown("### Key Topics in News")
                                st.write(", ".join(key_topics))
                            
                            # Display news articles
                            st.markdown("### Recent News Articles")
                            
                            for i, article in enumerate(news_articles):
                                title = article.get('title', 'No title')
                                source = article.get('source', 'Unknown')
                                date = article.get('date', 'Unknown date')
                                url = article.get('url', '#')
                                summary = article.get('summary', 'No summary available')
                                
                                with st.expander(f"{i+1}. {title} ({source})"):
                                    st.markdown(f"**Date:** {date}")
                                    st.markdown(f"**Source:** {source}")
                                    st.write(summary)
                                    st.markdown(f"[Read full article]({url})")
                        else:
                            st.info(f"No recent news found for {stock_symbol}")
                            st.write("Try a different symbol or check back later for updated news.")
            else:
                st.error(f"Could not retrieve data for {stock_symbol}. Please check the symbol and try again.")
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.info("Please check if the stock symbol is correct. For IDX stocks, use the format 'IDX:SYMBOL' (e.g., IDX:ADRO).")

# Footer
st.markdown("---")
st.markdown("**Disclaimer:** This application provides analysis for informational purposes only. It does not constitute financial advice.")
