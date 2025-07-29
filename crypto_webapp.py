import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import ccxt
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="Crypto Futures Dashboard", layout="wide")
st.title("📈 Crypto Futures Dashboard")

# Initialize exchange
exchange = ccxt.bitget()
markets = exchange.load_markets()

# Filter for USDT perpetual futures pairs
futures_pairs = [symbol for symbol in markets if symbol.endswith("_UMCBL")]

# Default pair logic
default_pair = "BTCUSDT_UMCBL" if "BTCUSDT_UMCBL" in futures_pairs else futures_pairs[0]
symbol = st.selectbox("Select a futures pair:", sorted(futures_pairs), index=sorted(futures_pairs).index(default_pair) if default_pair in futures_pairs else 0)

# Timeframe selection
timeframes = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
timeframe = st.selectbox("Select timeframe:", timeframes, index=4)

# Load OHLCV data
def fetch_ohlcv(pair, tf):
    try:
        ohlcv = exchange.fetch_ohlcv(pair, timeframe=tf, limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        st.error(f"Failed to load data for {pair} at {tf}: {e}")
        return pd.DataFrame()

data = fetch_ohlcv(symbol, timeframe)

if not data.empty:
    st.subheader(f"Live chart: {symbol} – {timeframe}")
    
    fig = go.Figure(data=[
        go.Candlestick(
            x=data['timestamp'],
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            name='Candles'
        )
    ])
    fig.update_layout(xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # Live price
    latest_price = data['close'].iloc[-1]
    st.metric(label="Live Price", value=f"{latest_price:.4f} USDT")

    # Countdown timer for next candle
    now = pd.Timestamp.utcnow()
    tf_minutes = int(timeframe[:-1]) if 'm' in timeframe else int(timeframe[:-1]) * 60 if 'h' in timeframe else 1440
    last_timestamp = data['timestamp'].iloc[-1]
    next_candle = last_timestamp + timedelta(minutes=tf_minutes)

    if pd.notnull(next_candle):
        remaining = (next_candle - now).total_seconds()
        remaining = max(0, remaining)
        mins, secs = divmod(int(remaining), 60)
        st.info(f"⏳ Time until next candle: {mins:02d}:{secs:02d}")
    else:
        st.warning("Next candle time unavailable.")
else:
    st.warning("No data available to display chart.")
