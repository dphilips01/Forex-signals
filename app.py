import streamlit as st
import pandas as pd
import requests
import datetime as dt

# =============================
# CONFIG
# =============================
ALPHA_VANTAGE_API_KEY = "EDXLMVCBHAFJ1814"
FOREX_BASE_URL = "https://www.alphavantage.co/query"
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# =============================
# STREAMLIT SETTINGS
# =============================
st.set_page_config(page_title="Forex & Crypto Signals", layout="centered")
st.markdown(
    "<h1 style='text-align: center;'>📈 Forex & Crypto Signals</h1>",
    unsafe_allow_html=True
)

st.write("Get simple **BUY**, **SELL**, or **HOLD** signals for Forex & Crypto. Optimized for mobile.")

# =============================
# HELPER FUNCTIONS
# =============================
def fetch_forex_data(pair):
    try:
        from_symbol, to_symbol = pair.split("/")
        url = f"{FOREX_BASE_URL}?function=FX_DAILY&from_symbol={from_symbol}&to_symbol={to_symbol}&apikey={ALPHA_VANTAGE_API_KEY}&outputsize=full"
        r = requests.get(url)
        data = r.json().get("Time Series FX (Daily)", {})
        if not data:
            return None
        df = pd.DataFrame(data).T
        df.columns = ["open", "high", "low", "close"]
        df = df.astype(float)
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        return df
    except:
        return None

def fetch_crypto_data(symbol):
    try:
        url = f"{COINGECKO_BASE_URL}/coins/{symbol}/market_chart?vs_currency=usd&days=90"
        r = requests.get(url)
        prices = r.json().get("prices", [])
        if not prices:
            return None
        df = pd.DataFrame(prices, columns=["date", "close"])
        df["date"] = pd.to_datetime(df["date"], unit="ms")
        df.set_index("date", inplace=True)
        return df
    except:
        return None

def analyze(df):
    if df is None or len(df) < 50:
        return "No Data", "Not enough data to analyze."
    df["SMA20"] = df["close"].rolling(window=20).mean()
    df["SMA50"] = df["close"].rolling(window=50).mean()
    df["RSI"] = compute_rsi(df["close"], 14)
    last = df.iloc[-1]
    signals = []
    if last["SMA20"] > last["SMA50"]:
        signals.append("BUY")
    elif last["SMA20"] < last["SMA50"]:
        signals.append("SELL")
    if last["RSI"] < 30:
        signals.append("BUY")
    elif last["RSI"] > 70:
        signals.append("SELL")
    if signals.count("BUY") >= 2:
        return "BUY", "Multiple bullish signals detected."
    elif signals.count("SELL") >= 2:
        return "SELL", "Multiple bearish signals detected."
    else:
        return "HOLD", "Mixed signals — wait for a clearer trend."

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# =============================
# UI
# =============================
st.subheader("💱 Forex Analysis")
forex_pair = st.text_input("Enter Forex Pair (e.g. EUR/USD)", "EUR/USD")
if st.button("Analyze Forex"):
    data = fetch_forex_data(forex_pair)
    sig, reason = analyze(data)
    st.success(f"Signal: {sig}")
    st.info(reason)

st.subheader("💹 Crypto Analysis")
crypto_coin = st.text_input("Enter CoinGecko coin id (e.g. bitcoin, ethereum)", "bitcoin")
if st.button("Analyze Crypto"):
    data = fetch_crypto_data(crypto_coin)
    if data is not None:
        data["close"] = data["close"].astype(float)
    sig, reason = analyze(data)
    st.success(f"Signal: {sig}")
    st.info(reason)

st.markdown("---")
st.caption("Signals are for educational purposes only — trade responsibly.")
