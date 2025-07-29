import streamlit as st
import pandas as pd
import ccxt
import plotly.graph_objects as go
import time
from datetime import datetime, timedelta

# --------- CONFIG ---------
st.set_page_config(page_title="Crypto Futures Dashboard", layout="wide")

# --------- HEADER ---------
st.markdown("""
    <style>
    .main-title {
        font-size: 36px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0px;
    }
    .live-price {
        font-size: 20px;
        color: lime;
        text-align: center;
        margin-top: 5px;
    }
    .timer {
        font-size: 14px;
        color: gray;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊 Crypto Futures Dashboard (Bitget)</div>', unsafe_allow_html=True)

# --------- SETTINGS ---------
timeframes = {
    '1m': 60,
    '5m': 300,
    '15m': 900,
    '1h': 3600,
    '4h': 14400,
    '1d': 86400,
    '1w': 604800
}

pair = st.sidebar.text_input("Enter Pair (e.g., BTC/USDT)", "BTC/USDT")
tf = st.sidebar.selectbox("Timeframe", list(timeframes.keys()), index=3)

# --------- FETCH DATA ---------
def get_ohlcv(symbol, timeframe):
    exchange = ccxt.bitget()
    markets = exchange.load_markets()
    market = symbol.replace("/", "-").upper()
    ohlcv = exchange.fetch_ohlcv(market, timeframe)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

try:
    df = get_ohlcv(pair, tf)
    current_price = df.iloc[-1]['close']
    st.markdown(f'<div class="live-price">Live Price: {current_price:.2f} USDT</div>', unsafe_allow_html=True)

    # Countdown Timer
    last_ts = df['timestamp'].iloc[-1]
    tf_seconds = timeframes[tf]
    next_candle = last_ts + timedelta(seconds=tf_seconds)
    remaining = (next_candle.to_pydatetime() - datetime.utcnow()).total_seconds()

    if remaining > 0:
        mins, secs = divmod(int(remaining), 60)
        st.markdown(f'<div class="timer">Next candle in: {mins}m {secs}s</div>', unsafe_allow_html=True)

    # Plot chart
    fig = go.Figure(data=[
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name="Candles"
        )
    ])

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        xaxis_title='Time',
        yaxis_title='Price (USDT)',
        template="plotly_dark",
        dragmode='zoom',
        height=600,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Failed to load data for {pair} at {tf}: {e}")
