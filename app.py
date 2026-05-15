import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from yahooquery import search
import feedparser
import requests


@st.cache_data(ttl=300)
def fetch_stock_data(ticker):

    stock = yf.Ticker(ticker)

    data_1d = stock.history(period="1d")

    history_3mo = stock.history(period="3mo")

    return data_1d, history_3mo


st.set_page_config(page_title="Stock Tracker", layout="wide")

st.title("📈 AI Stock Tracker")
st.caption("AI-powered stock analysis platform")


# AI-ASSISTED STOCK SEARCH

st.subheader("Search Any Stock")

user_query = st.text_input(
    "Search Company Name",
    "reliance"
)

ticker = None

if user_query:

    try:

        search_result = search(user_query)

        quotes = search_result.get("quotes")

        if quotes and len(quotes) > 0:

            stock_options = {}

            for stock in quotes[:10]:

                symbol = stock.get("symbol", "N/A")

                name = stock.get("shortname", "Unknown")

                exchange = stock.get("exchange", "")

                display_text = f"{name} ({symbol}) - {exchange}"

                stock_options[display_text] = symbol

            selected_stock = st.selectbox(
                "Did you mean:",
                list(stock_options.keys())
            )

            ticker = stock_options[selected_stock]

            st.success(f"Selected Stock: {ticker}")

        else:

            st.error("No matching stocks found")

    except:

        st.error("Search failed")

# FETCH STOCK DATA
    data, history = fetch_stock_data(ticker)

    stock = yf.Ticker(ticker)

if not data.empty:

    price = data["Close"].iloc[-1]

    st.metric("Current Price", f"₹{price:.2f}")

    # USER INPUTS
    buy_price = st.number_input("Enter Buy Price")

    quantity = st.number_input("Enter Quantity", step=1)

    # CALCULATIONS
    investment = buy_price * quantity

    current_value = price * quantity

    profit = current_value - investment

    # DISPLAY VALUES
    col1, col2, col3 = st.columns(3)

    col1.metric("Investment", f"₹{investment:.2f}")

    col2.metric("Current Value", f"₹{current_value:.2f}")

    col3.metric("Profit/Loss", f"₹{profit:.2f}")

    # PROFIT COLORS
    if profit > 0:
        st.success(f"Profit: ₹{profit:.2f}")

    elif profit < 0:
        st.error(f"Loss: ₹{profit:.2f}")

    else:
        st.write(f"No Profit No Loss: ₹{profit:.2f}")

    # SAVE TRADE
    if st.button("Save Trade"):

        trade_data = pd.DataFrame([{
            "Stock": ticker,
            "Buy Price": buy_price,
            "Current Price": price,
            "Quantity": quantity,
            "Investment": investment,
            "Current Value": current_value,
            "Profit/Loss": profit
        }])

        trade_data.to_csv(
            "portfolio.csv",
            mode="a",
            header=False,
            index=False
        )

        st.success("Trade Saved Successfully!")

    # HISTORICAL DATA

    # MOVING AVERAGES
    history["MA20"] = history["Close"].rolling(20).mean()

    history["MA50"] = history["Close"].rolling(50).mean()

    # RSI CALCULATION
    delta = history["Close"].diff()

    gain = delta.where(delta > 0, 0)

    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(14).mean()

    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss

    history["RSI"] = 100 - (100 / (1 + rs))

    # MACD CALCULATION

    ema12 = history["Close"].ewm(span=12, adjust=False).mean()

    ema26 = history["Close"].ewm(span=26, adjust=False).mean()

    history["MACD"] = ema12 - ema26

    history["Signal Line"] = history["MACD"].ewm(
        span=9,
        adjust=False
    ).mean()

    # MACD DISPLAY

    st.subheader("MACD Indicator")

    latest_macd = history["MACD"].iloc[-1]

    latest_signal = history["Signal Line"].iloc[-1]

    m1, m2 = st.columns(2)

    m1.metric("MACD", f"{latest_macd:.2f}")

    m2.metric("Signal Line", f"{latest_signal:.2f}")

    # BUY/SELL SIGNALS

    st.subheader("Trading Signal")

    if latest_macd > latest_signal:

        st.success("BUY SIGNAL → Bullish Momentum")

    elif latest_macd < latest_signal:

        st.error("SELL SIGNAL → Bearish Momentum")

    else:

        st.write("Neutral Momentum")

    # SIMPLE STRATEGY BACKTEST

    st.subheader("Strategy Backtest")

    buy_signals = 0

    sell_signals = 0

    for i in range(1, len(history)):

        prev_macd = history["MACD"].iloc[i - 1]

        prev_signal = history["Signal Line"].iloc[i - 1]

        current_macd = history["MACD"].iloc[i]

        current_signal = history["Signal Line"].iloc[i]

        # BUY SIGNAL

        if prev_macd < prev_signal and current_macd > current_signal:

            buy_signals += 1

        # SELL SIGNAL

        elif prev_macd > prev_signal and current_macd < current_signal:

            sell_signals += 1

    st.write(f"Buy Signals Detected: {buy_signals}")

    st.write(f"Sell Signals Detected: {sell_signals}")

    # BASIC STRATEGY SCORE

    strategy_score = buy_signals - sell_signals

    if strategy_score > 0:

        st.success("Strategy currently shows bullish historical momentum")

    elif strategy_score < 0:

        st.error("Strategy currently shows bearish historical momentum")

    else:

        st.write("Strategy currently appears neutral")

    # NEWS + SENTIMENT ANALYSIS

    st.subheader("Latest Stock News")

    news_url = f"https://news.google.com/rss/search?q={ticker}+stock"

    feed = feedparser.parse(news_url)

    entries = feed.entries[:5]

    positive_words = [
        "surge",
        "gain",
        "bullish",
        "growth",
        "profit",
        "strong",
        "beats",
        "rise",
        "positive"
    ]

    negative_words = [
        "drop",
        "loss",
        "bearish",
        "fall",
        "weak",
        "down",
        "crash",
        "miss",
        "negative"
    ]

    sentiment_score = 0

    news_summary = []

    for entry in entries:

        title = entry.title

        st.write("•", title)

        news_summary.append(title)

        lower_title = title.lower()

        for word in positive_words:

            if word in lower_title:
                sentiment_score += 1

        for word in negative_words:

            if word in lower_title:
                sentiment_score -= 1

    # SENTIMENT RESULT

    st.subheader("News Sentiment")

    if sentiment_score > 0:

        sentiment = "Bullish"

        st.success("Bullish News Sentiment Detected")

    elif sentiment_score < 0:

        sentiment = "Bearish"

        st.error("Bearish News Sentiment Detected")

    else:

        sentiment = "Neutral"

        st.write("Neutral News Sentiment")

    # AI-STYLE NEWS SUMMARY

    st.subheader("AI News Summary")

    summary_text = f"""
    Recent news coverage for {ticker} appears {sentiment.lower()} overall.
    The stock is currently showing a mix of market sentiment,
    technical momentum, and investor reactions based on recent headlines.
    """

    st.info(summary_text)

    # CANDLESTICK CHART
    st.subheader("Candlestick Chart")

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=history.index,
            open=history["Open"],
            high=history["High"],
            low=history["Low"],
            close=history["Close"],
            name="Candles"
        ))

    # MOVING AVERAGES
    fig.add_trace(go.Scatter(
        x=history.index,
        y=history["MA20"],
        mode="lines",
        name="20 MA"
    ))

    fig.add_trace(go.Scatter(
        x=history.index,
        y=history["MA50"],
        mode="lines",
        name="50 MA"
    ))

    st.plotly_chart(fig, use_container_width=True)

    # RSI SECTION
    latest_rsi = history["RSI"].iloc[-1]

    st.subheader("RSI Indicator")

    st.metric("Current RSI", f"{latest_rsi:.2f}")

    if latest_rsi > 70:
        st.error("RSI indicates stock may be OVERBOUGHT")

    elif latest_rsi < 30:
        st.success("RSI indicates stock may be OVERSOLD")

    else:
        st.info("RSI is in normal range")

    # MOVING AVERAGES

    history["MA20"] = history["Close"].rolling(20).mean()

    history["MA50"] = history["Close"].rolling(50).mean()

    ma20 = history["MA20"].iloc[-1]

    ma50 = history["MA50"].iloc[-1]

    # AI STOCK ANALYSIS

    st.subheader("AI Stock Analysis")

    analysis_points = []

    # MOVING AVERAGE ANALYSIS

    if price > ma20:

        analysis_points.append(
            "Price is above 20-day MA indicating short-term bullish momentum."
        )

    else:

        analysis_points.append(
            "Price is below 20-day MA indicating weak short-term momentum."
        )

    if ma20 > ma50:

        analysis_points.append(
            "20-day MA is above 50-day MA showing bullish trend strength."
        )

    else:

        analysis_points.append(
            "20-day MA is below 50-day MA showing bearish trend structure."
        )

    # RSI ANALYSIS

    if latest_rsi > 70:

        analysis_points.append(
            "RSI suggests overbought conditions and possible pullback risk."
        )

    elif latest_rsi < 30:

        analysis_points.append(
            "RSI suggests oversold conditions and possible rebound potential."
        )

    else:

        analysis_points.append(
            "RSI is in healthy range with balanced momentum."
        )

    # MACD ANALYSIS

    if latest_macd > latest_signal:

        analysis_points.append(
            "MACD crossover indicates bullish momentum continuation."
        )

    else:

        analysis_points.append(
            "MACD crossover indicates bearish momentum pressure."
        )

    # NEWS SENTIMENT ANALYSIS

    if sentiment == "Bullish":

        analysis_points.append(
            "Recent news sentiment appears positive for the stock."
        )

    elif sentiment == "Bearish":

        analysis_points.append(
            "Recent news sentiment appears negative for the stock."
        )

    else:

        analysis_points.append(
            "News sentiment currently appears neutral."
        )

    # DISPLAY AI ANALYSIS

    for point in analysis_points:

        st.write("•", point)

    # REAL AI CHAT ANALYST

st.subheader("Ask AI About This Stock")

user_question = st.text_input(
    "Ask anything about the stock",
    "Is this a good buy right now?"
)

if st.button("Ask AI"):

    prompt = f"""
    You are a professional stock market AI analyst.

    Analyze this stock using the following data:

    Stock: {ticker}

    Current Price: ₹{price:.2f}

    RSI: {latest_rsi:.2f}

    MACD: {latest_macd:.2f}

    Signal Line: {latest_signal:.2f}

    20 MA: {ma20:.2f}

    50 MA: {ma50:.2f}

    News Sentiment: {sentiment}

    User Question:
    {user_question}

    Only use the provided data.
    Do not invent indicators or values.
    Keep the response concise, analytical, and realistic.
    """

try:

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",

        headers={
            "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json"
        },

        json={
            "model": "openai/gpt-3.5-turbo",

            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
    )

    result = response.json()

    ai_reply = result["choices"][0]["message"]["content"]

    st.info(ai_reply)

except Exception as e:

    st.error(f"Error: {e}")
# DISPLAY SAVED TRADES
st.subheader("Saved Trades")

try:

    saved_data = pd.read_csv("portfolio.csv")

    saved_data.columns = [
        "Stock",
        "Buy Price",
        "Current Price",
        "Quantity",
        "Investment",
        "Current Value",
        "Profit/Loss"
    ]

    st.dataframe(saved_data)

    # TOTAL PORTFOLIO
    total_investment = saved_data["Investment"].sum()

    total_current = saved_data["Current Value"].sum()

    total_profit = saved_data["Profit/Loss"].sum()

    st.subheader("Portfolio Summary")

    p1, p2, p3 = st.columns(3)

    p1.metric("Total Investment", f"₹{total_investment:.2f}")

    p2.metric("Current Portfolio Value", f"₹{total_current:.2f}")

    p3.metric("Net Profit/Loss", f"₹{total_profit:.2f}")

    # PORTFOLIO PERFORMANCE GRAPH

    st.subheader("Portfolio Performance")

    saved_data["Cumulative Profit"] = saved_data["Profit/Loss"].cumsum()

    st.line_chart(saved_data["Cumulative Profit"])

    # DELETE TRADES
    st.subheader("Delete Trade")

    delete_index = st.number_input(
        "Enter row index to delete",
        min_value=0,
        step=1
    )

    if st.button("Delete Selected Trade"):

        saved_data = saved_data.drop(delete_index)

        saved_data.to_csv(
            "portfolio.csv",
            index=False,
            header=False
        )

        st.success("Trade Deleted Successfully!")

except:
    st.write("No saved trades yet")
