import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import ccxt

# --- 1. Setup --- #
st.set_page_config(layout="wide")
st.title("📊 Bitget Advanced Trading Dashboard")

# --- 2. Custom Indicator Calculations --- #
def find_extrema(series, window=5):
    """Manual implementation of peak/valley detection"""
    max_idx, min_idx = [], []
    for i in range(window, len(series)-window):
        if series[i] == series[i-window:i+window].max():
            max_idx.append(i)
        elif series[i] == series[i-window:i+window].min():
            min_idx.append(i)
    return max_idx, min_idx

def calculate_rsi(series, period=14):
    """Manual RSI calculation"""
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# --- 3. Data Fetching --- #
@st.cache_data(ttl=30)
def get_ohlcv(tf="15m", pair="BTC/USDT:USDT"):
    exchange = ccxt.bitget()
    ohlcv = exchange.fetch_ohlcv(pair, tf, limit=1000)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

# --- 4. Indicator Processing --- #
def process_indicators(df):
    # Bollinger Bands
    df['MA20'] = df['close'].rolling(20).mean()
    df['Upper'] = df['MA20'] + 2*df['close'].rolling(20).std()
    df['Lower'] = df['MA20'] - 2*df['close'].rolling(20).std()
    
    # Support/Resistance
    highs, lows = df['high'], df['low']
    max_idx, min_idx = find_extrema(highs), find_extrema(lows)
    df['support'] = np.nan
    df['resistance'] = np.nan
    df.loc[min_idx, 'support'] = lows[min_idx]
    df.loc[max_idx, 'resistance'] = highs[max_idx]
    
    # Fibonacci
    high, low = highs.max(), lows.min()
    df['fib_618'] = low + (high-low)*0.618
    df['fib_50'] = low + (high-low)*0.5
    
    # Volume Analysis
    df['buy_vol'] = np.where(df['close'] > df['open'], df['volume'], 0)
    df['sell_vol'] = np.where(df['close'] < df['open'], df['volume'], 0)
    
    # RSI
    df['RSI'] = calculate_rsi(df['close'])
    
    return df

# --- 5. UI Layout --- #
col1, col2 = st.columns([1, 4])

with col1:
    # Timeframe Selector (Vertical) - FIXED RADIO BUTTON
    st.write("")
    tf = st.radio(
        "Timeframe",
        options=["5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h"],
        index=1,  # Default to 15m
        key="timeframe_selector"
    )
    
    # Indicator Values
    st.write("")
    st.markdown("**BOLL:** 5.638")
    st.markdown("**UB:** 6.328")
    st.markdown("**LB:** 4.949")
    
    st.write("")
    st.write("7.710 (Resistance)")
    st.write("6.773 (Fib 0.618)")
    st.write("5.946 (Pivot)")
    st.write("4.838 (Fib 0.5)")
    st.write("3.402 (Support)")
    st.write("1.966 (Target)")
    
    st.write("")
    st.write("07-26 23:00 (Wave 3)")
    st.write("07-27 12:00 (Wave 4)")
    st.write("07-28 01:00 (Wave 5)")
    st.write("07-28 14:00 (Correction)")
    st.write("07-29 03:00 (Entry)")

with col2:
    # Countdown Timer
    def get_next_candle(tf):
        now = datetime.utcnow()
        if 'm' in tf:
            mins = int(tf.replace('m',''))
            next_candle = now + timedelta(minutes=mins - now.minute%mins)
        else:
            hours = int(tf.replace('h',''))
            next_candle = now + timedelta(hours=hours - now.hour%hours)
        return next_candle
    
    countdown = st.empty()
    
    # Get Data
    df = process_indicators(get_ohlcv(tf))
    
    # Main Chart
    fig = go.Figure()
    
    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name="Price"
    ))
    
    # Bollinger Bands
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['Upper'],
        line=dict(color='red', width=1),
        name="Upper Band"
    ))
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['Lower'],
        line=dict(color='blue', width=1),
        name="Lower Band"
    ))
    
    fig.update_layout(
        height=600,
        xaxis_rangeslider_visible=False,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Live Updates
    while True:
        remaining = get_next_candle(tf) - datetime.utcnow()
        mins, secs = divmod(int(remaining.total_seconds()), 60)
        countdown.markdown(
            f"⏳ Next {tf} candle in **{mins}m {secs}s** | "
            f"RSI: {df['RSI'].iloc[-1]:.1f} | "
            f"Buy Vol: {df['buy_vol'].iloc[-1]:.0f}",
            unsafe_allow_html=True
        )
        time.sleep(1)

# --- 6. Run --- #
if __name__ == "__main__":
    st.write("Live dashboard running...")