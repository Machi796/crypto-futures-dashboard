import streamlit as st
import pandas as pd
import ccxt
import plotly.graph_objs as go

st.set_page_config(layout="wide")
st.title("📈 Crypto Futures Dashboard — Bitget")

exchange = ccxt.bitget()
markets = exchange.load_markets()

# Filter only USDT perpetual futures markets
futures_pairs = [m for m in markets if markets[m].get("contract", False) and ":USDT" in m]
futures_pairs.sort()

# Set default symbol safely
default_symbol = "BTCUSDT_UMCBL" if "BTCUSDT_UMCBL" in futures_pairs else futures_pairs[0]
symbol = st.selectbox("Select a futures pair:", futures_pairs, index=futures_pairs.index(default_symbol))

# Timeframe selection
timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
timeframe = st.selectbox("Select timeframe:", timeframes, index=4)

# Load OHLCV data
data = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=200)
df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

# Live price
live_ticker = exchange.fetch_ticker(symbol)
live_price = live_ticker["last"]
st.markdown(f"## 💰 Live Price: **{live_price:.4f} USDT**")

# Candlestick chart
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df["timestamp"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"],
    name="Candles"
))

fig.update_layout(
    xaxis_rangeslider_visible=False,
    title=f"{symbol} — {timeframe} Chart",
    yaxis_title="Price (USDT)",
    xaxis_title="Time",
    dragmode="pan",
    height=600
)

st.plotly_chart(fig, use_container_width=True)

# Countdown to next candle
import time
duration = exchange.timeframes[timeframe]
interval = pd.to_timedelta(duration.replace("m", "min").replace("h", "hour").replace("d", "day"))
last_candle = df["timestamp"].iloc[-1]
next_candle = last_candle + interval
remaining = (next_candle - pd.Timestamp.utcnow()).total_seconds()

if remaining > 0:
    mins, secs = divmod(int(remaining), 60)
    st.info(f"⏳ Next candle in: {mins:02d}:{secs:02d}")
