import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objs as go
import time
from datetime import datetime, timedelta

# ------------------------
# STREAMLIT CONFIG
# ------------------------
st.set_page_config(page_title="Crypto Futures Dashboard", layout="wide")
st.title("🚀 Crypto Futures Dashboard (Bitget)")

# ------------------------
# FETCH BITGET DATA
# ------------------------
def get_bitget_symbols():
    exchange = ccxt.bitget()
    markets = exchange.load_markets()
    usdt_pairs = [symbol for symbol in markets if symbol.endswith("/USDT:USDT")]
    return sorted(usdt_pairs)

def fetch_ohlcv(symbol, timeframe='1h', limit=200):
    exchange = ccxt.bitget()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def get_live_price(symbol):
    exchange = ccxt.bitget()
    ticker = exchange.fetch_ticker(symbol)
    return ticker['last']

# ------------------------
# USER INPUTS
# ------------------------
symbols = get_bitget_symbols()
symbol = st.selectbox("Select Futures Pair", symbols, index=symbols.index("BTC/USDT:USDT"))
timeframe = st.selectbox("Timeframe", ['1m', '5m', '15m', '1h', '4h', '1d'])

# ------------------------
# DATA + LIVE PRICE + COUNTDOWN
# ------------------------
with st.spinner("Fetching data and live price..."):
    df = fetch_ohlcv(symbol, timeframe)
    price = get_live_price(symbol)

st.markdown(f"### 📈 {symbol} | Live Price: **${price:,.2f}**")

# Countdown bar
interval_seconds = {
    '1m': 60, '5m': 300, '15m': 900, '1h': 3600, '4h': 14400, '1d': 86400
}[timeframe]
latest_timestamp = df['timestamp'].iloc[-1]
next_candle = latest_timestamp + pd.Timedelta(seconds=interval_seconds)
remaining = (next_candle - pd.Timestamp.utcnow()).total_seconds()
remaining = max(0, remaining)

progress_text = f"Next candle in {int(remaining)}s"
st.progress(int(100 * remaining / interval_seconds), text=progress_text)

# ------------------------
# PLOTLY CANDLE CHART
# ------------------------
candles = go.Figure()
candles.add_trace(go.Candlestick(
    x=df['timestamp'], open=df['open'], high=df['high'],
    low=df['low'], close=df['close'], name='Candles'))
candles.update_layout(
    xaxis_rangeslider_visible=False,
    xaxis_title='Time', yaxis_title='Price',
    template='plotly_dark', height=600,
    hovermode='x unified',
    margin=dict(l=20, r=20, t=40, b=20),
    dragmode='zoom',
    title=dict(text=f"{symbol} - {timeframe} Chart", x=0.5, xanchor='center'),
)

st.plotly_chart(candles, use_container_width=True)

# Optional: Auto-refresh every minute if on 1m chart
if timeframe == '1m':
    time.sleep(5)
    st.experimental_rerun()
