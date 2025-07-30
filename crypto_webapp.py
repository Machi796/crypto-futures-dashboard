import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import ccxt
import numpy as np
import ta
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("📈 Crypto Futures Dashboard (Intraday Pro Pack)")

# Initialize Bitget futures market
bitget = ccxt.bitget()
markets = bitget.load_markets()
symbols = [s for s in markets if '/USDT:USDT' in s and 'SWAP' in markets[s]['id']]

# Sidebar - Coin and Timeframe Selection
symbol = st.sidebar.selectbox("Select Futures Pair", sorted(symbols))
timeframe = st.sidebar.selectbox("Select Timeframe", ["1m", "5m", "15m", "1h", "4h", "1d"])

# Fetch OHLCV data
def get_ohlcv(symbol, timeframe):
    ohlcv = bitget.fetch_ohlcv(symbol, timeframe=timeframe, limit=500)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df

df = get_ohlcv(symbol, timeframe)

# Calculate indicators
df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
df['macd'] = ta.trend.MACD(df['close']).macd_diff()
df['ema9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
df['ema21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
df['ema50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
df['ema200'] = ta.trend.EMAIndicator(df['close'], window=200).ema_indicator()
df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
df['stoch_rsi'] = ta.momentum.StochRSIIndicator(df['close']).stochrsi_k()
df['v_spike'] = df['volume'] > (df['volume'].rolling(20).mean() + 2 * df['volume'].rolling(20).std())

# Plotting
fig = go.Figure()

# Candlesticks
fig.add_trace(go.Candlestick(
    x=df['timestamp'], open=df['open'], high=df['high'],
    low=df['low'], close=df['close'], name='Candles'))

# EMA lines
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ema9'], name="EMA 9", line=dict(color="blue")))
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ema21'], name="EMA 21", line=dict(color="orange")))
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ema50'], name="EMA 50", line=dict(color="green")))
fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ema200'], name="EMA 200", line=dict(color="purple")))

# Volume spikes
spike_times = df[df['v_spike']]['timestamp']
spike_prices = df[df['v_spike']]['close']
fig.add_trace(go.Scatter(
    x=spike_times, y=spike_prices,
    mode="markers", marker=dict(color="red", size=8),
    name="Volume Spike"))

fig.update_layout(height=700, xaxis_rangeslider_visible=False)

st.plotly_chart(fig, use_container_width=True)

# Extra charts: RSI, MACD, ATR, Stochastic RSI
st.subheader("📊 Indicators")

st.line_chart(df.set_index("timestamp")[["rsi"]], height=200)
st.line_chart(df.set_index("timestamp")[["macd"]], height=200)
st.line_chart(df.set_index("timestamp")[["atr"]], height=200)
st.line_chart(df.set_index("timestamp")[["stoch_rsi"]], height=200)
