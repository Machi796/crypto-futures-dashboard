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

# --- 2. Fixed Extrema Detection --- #
def find_extrema(series, window=5):
    """Robust peak/valley detection that returns proper indices"""
    max_idx = (series.rolling(window, center=True).max() == series).astype(int)
    min_idx = (series.rolling(window, center=True).min() == series).astype(int)
    return np.where(max_idx)[0], np.where(min_idx)[0]  # Returns numpy arrays

# --- 3. Data Fetching --- #
@st.cache_data(ttl=30)
def get_ohlcv(tf="15m", pair="BTC/USDT:USDT"):
    exchange = ccxt.bitget()
    ohlcv = exchange.fetch_ohlcv(pair, tf, limit=1000)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

# --- 4. Fixed Indicator Processing --- #
def process_indicators(df):
    # Bollinger Bands
    df['MA20'] = df['close'].rolling(20).mean()
    df['Upper'] = df['MA20'] + 2*df['close'].rolling(20).std()
    df['Lower'] = df['MA20'] - 2*df['close'].rolling(20).std()
    
    # Support/Resistance (Fixed Implementation)
    highs, lows = df['high'].values, df['low'].values
    max_idx, min_idx = find_extrema(highs), find_extrema(lows)
    
    df['support'] = np.nan
    df['resistance'] = np.nan
    
    if len(min_idx[0]) > 0:
        df.loc[min_idx[0], 'support'] = lows[min_idx[0]]
    if len(max_idx[0]) > 0:
        df.loc[max_idx[0], 'resistance'] = highs[max_idx[0]]
    
    # Fibonacci Levels
    high, low = highs.max(), lows.min()
    df['fib_618'] = low + (high-low)*0.618
    df['fib_50'] = low + (high-low)*0.5
    
    # Volume Analysis
    df['buy_vol'] = np.where(df['close'] > df['open'], df['volume'], 0)
    df['sell_vol'] = np.where(df['close'] < df['open'], df['volume'], 0)
    
    return df

# --- 5. UI Layout (Same as Before) --- #
col1, col2 = st.columns([1, 4])

with col1:
    st.write("")
    tf = st.radio(
        "Timeframe",
        options=["5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h"],
        index=1,
        key="timeframe_selector"
    )
    
    # Display static values for layout
    st.write("")
    st.markdown("**BOLL:** 5.638")
    st.markdown("**UB:** 6.328")
    st.markdown("**LB:** 4.949")
    st.write("7.710 (Resistance)")
    st.write("6.773 (Fib 0.618)")
    st.write("5.946 (Pivot)")
    st.write("4.838 (Fib 0.5)")
    st.write("3.402 (Support)")
    st.write("1.966 (Target)")
    st.write("07-26 23:00 (Wave 3)")
    st.write("07-27 12:00 (Wave 4)")
    st.write("07-28 01:00 (Wave 5)")
    st.write("07-28 14:00 (Correction)")
    st.write("07-29 03:00 (Entry)")

with col2:
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
    df = process_indicators(get_ohlcv(tf))
    
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name="Price"
    ))
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
    
    # Only plot valid support/resistance points
    if 'support' in df:
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['support'],
            mode='markers',
            marker=dict(color='green', size=8),
            name="Support"
        ))
    if 'resistance' in df:
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['resistance'],
            mode='markers',
            marker=dict(color='red', size=8),
            name="Resistance"
        ))
    
    fig.update_layout(height=600, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    while True:
        remaining = get_next_candle(tf) - datetime.utcnow()
        mins, secs = divmod(int(remaining.total_seconds()), 60)
        countdown.markdown(
            f"⏳ Next {tf} candle in **{mins}m {secs}s** | "
            f"Price: {df['close'].iloc[-1]:.4f}",
            unsafe_allow_html=True
        )
        time.sleep(1)

if __name__ == "__main__":
    st.write("Live dashboard running...")