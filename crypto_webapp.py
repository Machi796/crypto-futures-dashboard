import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import ta

st.set_page_config(page_title="Crypto Futures Pro Dashboard", layout="wide")
st.title("💹 Crypto Futures Pro Dashboard — Bitget USDT-M")

# --- Get all USDT futures pairs from Bitget
@st.cache_data(ttl=600)
def get_futures_pairs():
    exchange = ccxt.bitget()
    markets = exchange.load_markets()
    return sorted([m for m in markets if "/USDT" in m and markets[m]["contract"]])

# --- Fetch OHLCV data
def get_ohlcv(pair, tf, limit=500):
    exchange = ccxt.bitget()
    data = exchange.fetch_ohlcv(pair, timeframe=tf, limit=limit)
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

# --- Fibonacci retracement levels
def draw_fib(df):
    high = df["high"].max()
    low = df["low"].min()
    diff = high - low
    levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
    lines = []
    for lvl in levels:
        y = high - diff * lvl
        lines.append(dict(type="line", xref="paper", x0=0, x1=1, y0=y, y1=y,
                          line=dict(color="purple", dash="dot"), name=f"{lvl*100:.1f}%"))
    return lines

# --- Support & Resistance Zones
def get_sr_levels(df, threshold=0.02):
    levels = []
    for i in range(2, len(df) - 2):
        if df["low"][i] < df["low"][i - 1] and df["low"][i] < df["low"][i + 1]:
            levels.append(df["low"][i])
        elif df["high"][i] > df["high"][i - 1] and df["high"][i] > df["high"][i + 1]:
            levels.append(df["high"][i])
    levels = sorted(set(levels))
    # Filter nearby zones
    filtered = []
    for level in levels:
        if not any(abs(level - l) / l < threshold for l in filtered):
            filtered.append(level)
    return filtered

# --- Add RSI & MACD
def add_indicators(df):
    rsi = ta.momentum.RSIIndicator(df["close"]).rsi()
    macd = ta.trend.MACD(df["close"])
    df["rsi"] = rsi
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    return df

# --- UI Sidebar
with st.sidebar:
    pair = st.selectbox("Select Perpetual Futures Pair", get_futures_pairs(), index=0)
    tf = st.selectbox("Select Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"])
    st.markdown("Made for Bitget USDT-margined futures traders 💹")

df = get_ohlcv(pair, tf)
df = add_indicators(df)

# --- Plot Chart
fig = go.Figure()

# Candlesticks
fig.add_trace(go.Candlestick(
    x=df["timestamp"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"],
    name="Price"
))

# Fibonacci
fig.update_layout(shapes=draw_fib(df))

# SR Zones
for lvl in get_sr_levels(df):
    fig.add_hline(y=lvl, line=dict(color="gray", width=1, dash="dot"))

# Layout
fig.update_layout(title=f"{pair} — {tf}", xaxis_rangeslider_visible=False, height=700)
st.plotly_chart(fig, use_container_width=True)

# --- RSI & MACD Charts
st.subheader("📊 RSI & MACD Indicators")

col1, col2 = st.columns(2)
with col1:
    st.line_chart(df.set_index("timestamp")["rsi"], height=200)
with col2:
    st.line_chart(df.set_index("timestamp")[["macd", "macd_signal"]], height=200)

st.success("Core TA tools loaded ✅ — Elliott Wave, CME gaps & projections coming next.")
