import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Crypto Futures Dashboard", layout="wide")
st.title("Crypto Futures Dashboard — Bitget USDT-M Futures")

# Select pair
pairs = ["BTC/USDT", "ETH/USDT", "CRV/USDT", "INJ/USDT", "1000PEPE/USDT"]
pair = st.selectbox("Select Futures Pair", pairs)

# Select timeframe
timeframes = ["1m", "5m", "15m", "1h", "4h", "1d"]
tf = st.selectbox("Select Timeframe", timeframes)

# Fetch OHLCV data from Bitget
exchange = ccxt.bitget()
limit = 100

try:
    ohlcv = exchange.fetch_ohlcv(pair, timeframe=tf, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

# Plot candlestick chart
fig = go.Figure(data=[go.Candlestick(
    x=df["timestamp"],
    open=df["open"],
    high=df["high"],
    low=df["low"],
    close=df["close"]
)])
fig.update_layout(title=f"{pair} - {tf}", xaxis_rangeslider_visible=False, height=600)
st.plotly_chart(fig, use_container_width=True)
