import streamlit as st
import ccxt
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page config
st.set_page_config(page_title="Crypto Futures Dashboard", layout="wide")
st.title("📊 Crypto Futures Dashboard (Bitget Perpetual)")

# Init exchange
exchange = ccxt.bitget()
markets = exchange.load_markets()

# Filter USDT perpetual futures
futures_pairs = [symbol for symbol in markets if 
    markets[symbol]['linear'] and 
    markets[symbol]['contract'] and 
    symbol.endswith("_UMCBL")]

# Symbol selection
symbol = st.selectbox("Select a futures pair:", sorted(futures_pairs), index=sorted(futures_pairs).index("BTCUSDT_UMCBL"))

# Timeframe selection
timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
timeframe = st.selectbox("Select timeframe:", timeframes, index=3)

# Fetch OHLCV data
def get_ohlcv(symbol, tf):
    try:
        data = exchange.fetch_ohlcv(symbol, tf)
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
    except Exception as e:
        st.error(f"Failed to load data for {symbol} at {tf}: {e}")
        return pd.DataFrame()

# Load data
df = get_ohlcv(symbol, timeframe)

if not df.empty:
    # Live price
    live_price = df["close"].iloc[-1]
    st.metric(label=f"💰 {symbol} Price (Live)", value=f"${live_price:,.2f}")

    # Countdown timer for next candle
    tf_map = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}
    minutes = tf_map.get(timeframe, 60)
    last_ts = df["timestamp"].iloc[-1]
    next_candle = last_ts + timedelta(minutes=minutes)
    remaining = (next_candle.to_pydatetime() - datetime.utcnow()).total_seconds()
    st.caption(f"🕒 Next candle in: {int(remaining // 60)} min {int(remaining % 60)} sec")

    # Plot chart
    fig = go.Figure(data=[
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Candles'
        )
    ])

    fig.update_layout(
        title=f"{symbol} Candlestick Chart ({timeframe})",
        xaxis_rangeslider_visible=False,
        xaxis_title="Time",
        yaxis_title="Price",
        height=600,
        margin=dict(t=50, b=50),
        xaxis=dict(type="date", rangeslider_visible=False),
        yaxis=dict(fixedrange=False),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No data to display.")
