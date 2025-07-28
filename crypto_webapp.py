
import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Setup
st.set_page_config(page_title="Bitget Futures Dashboard", layout="wide")
st.title("📊 Bitget USDT-M Futures Dashboard")

# Connect to Bitget Futures
exchange = ccxt.bitget({
    'options': {'defaultType': 'swap'}  # Required for USDT-M Futures
})

# Fetch all USDT-margined futures markets
markets = exchange.load_markets()
futures_pairs = sorted([m for m in markets if '/USDT' in m and markets[m]['type'] == 'swap'])

# UI - Pair & Timeframe Selection
pair = st.selectbox("🔗 Select Futures Pair", futures_pairs, index=futures_pairs.index("BTC/USDT"))
timeframes = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '12h', '1d', '1w']
tf = st.selectbox("🕒 Select Timeframe", timeframes)

# Fetch OHLCV Data
limit = 100
try:
    ohlcv = exchange.fetch_ohlcv(pair, timeframe=tf, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
except Exception as e:
    st.error(f"⚠️ Error fetching data: {e}")
    st.stop()

# Calculate EMAs
df["ema9"] = df["close"].ewm(span=9).mean()
df["ema21"] = df["close"].ewm(span=21).mean()

# Entry Signal: EMA Crossover
df["signal"] = ""
for i in range(1, len(df)):
    if df["ema9"].iloc[i] > df["ema21"].iloc[i] and df["ema9"].iloc[i - 1] <= df["ema21"].iloc[i - 1]:
        df.at[i, "signal"] = "buy"
    elif df["ema9"].iloc[i] < df["ema21"].iloc[i] and df["ema9"].iloc[i - 1] >= df["ema21"].iloc[i - 1]:
        df.at[i, "signal"] = "sell"

# Entry Signal: Breakout
high_10 = df["high"].rolling(10).max()
low_10 = df["low"].rolling(10).min()
df["breakout"] = ""
for i in range(1, len(df)):
    if df["close"].iloc[i] > high_10.iloc[i - 1]:
        df.at[i, "breakout"] = "breakout_buy"
    elif df["close"].iloc[i] < low_10.iloc[i - 1]:
        df.at[i, "breakout"] = "breakout_sell"

# Plot Candlestick Chart
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df["timestamp"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"],
    name="Candles"
))

# Signal markers
buy_signals = df[df["signal"] == "buy"]
sell_signals = df[df["signal"] == "sell"]
breakout_buy = df[df["breakout"] == "breakout_buy"]
breakout_sell = df[df["breakout"] == "breakout_sell"]

# Add signal traces
fig.add_trace(go.Scatter(
    x=buy_signals["timestamp"],
    y=buy_signals["low"] * 0.995,
    mode="markers",
    marker=dict(color="green", symbol="arrow-up", size=12),
    name="EMA Buy"
))

fig.add_trace(go.Scatter(
    x=sell_signals["timestamp"],
    y=sell_signals["high"] * 1.005,
    mode="markers",
    marker=dict(color="red", symbol="arrow-down", size=12),
    name="EMA Sell"
))

fig.add_trace(go.Scatter(
    x=breakout_buy["timestamp"],
    y=breakout_buy["high"] * 1.002,
    mode="markers",
    marker=dict(color="lime", symbol="circle", size=10),
    name="Breakout Buy"
))

fig.add_trace(go.Scatter(
    x=breakout_sell["timestamp"],
    y=breakout_sell["low"] * 0.998,
    mode="markers",
    marker=dict(color="orange", symbol="circle", size=10),
    name="Breakout Sell"
))

fig.update_layout(
    title=f"{pair} ({tf})",
    xaxis_rangeslider_visible=False,
    xaxis_title="Time",
    yaxis_title="Price (USDT)",
    template="plotly_dark",
    height=600,
    margin=dict(l=10, r=10, t=40, b=10)
)

# Display chart
st.plotly_chart(fig, use_container_width=True)

# Candle countdown timer
tf_map = {
    '1m': 60, '3m': 180, '5m': 300, '15m': 900,
    '30m': 1800, '1h': 3600, '2h': 7200, '4h': 14400,
    '6h': 21600, '12h': 43200, '1d': 86400, '1w': 604800
}
timeframe_seconds = tf_map[tf]
last_timestamp = df["timestamp"].iloc[-1]
next_candle_time = last_timestamp + timedelta(seconds=timeframe_seconds)

remaining = (next_candle_time - datetime.utcnow()).total_seconds()
remaining = max(0, int(remaining))

# Display Timer
st.markdown("⏱️ **Time until next candle:**")
progress_bar = st.progress(0)
countdown_placeholder = st.empty()

for i in range(remaining):
    countdown_placeholder.markdown(f"**{remaining - i} seconds**")
    progress_bar.progress((i + 1) / remaining)
    time.sleep(1)

countdown_placeholder.markdown("🔄 Candle closed. Please refresh.")