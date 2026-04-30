import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import os
import glob

# Configuration
HISTORICAL_DIR = 'data/historical'
OUTPUT_FILE = 'dashboard.html'

def load_kline_data(symbol):
    file_path = os.path.join(HISTORICAL_DIR, f'{symbol.lower()}usdt_raw_klines.json')
    if not os.path.exists(file_path): return None
    with open(file_path, 'r') as f: data = json.load(f)
    df = pd.DataFrame(data, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'ct', 'qav', 'nt', 'tbb', 'tbq', 'i'])
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].apply(pd.to_numeric)
    return df

def generate_dashboard():
    print("Generating Dashboard HTML...")
    
    # 1. Main Price Chart (BTC)
    btc_df = load_kline_data('btc')
    if btc_df is None: return
    
    fig = make_subplots(rows=3, cols=2, 
                        specs=[[{"colspan": 2, "type": "domain"}, None],
                               [{"type": "xy"}, {"type": "xy"}],
                               [{"colspan": 2, "type": "xy"}, None]],
                        subplot_titles=("Market Sentiment Gauge", "Bitcoin Trend", "Ethereum Trend", "Assets Performance Comparison"),
                        vertical_spacing=0.1)

    # --- Gauge ---
    fig.add_trace(go.Indicator(
        mode = "gauge+number",
        value = 65,
        title = {'text': "Market Sentiment Index (Greed)"},
        gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "green"},
                 'steps': [{'range': [0, 40], 'color': "red"}, {'range': [40, 60], 'color': "gray"}, {'range': [60, 100], 'color': "green"}]}
    ), row=1, col=1)

    # --- BTC Chart ---
    fig.add_trace(go.Scatter(x=btc_df['open_time'], y=btc_df['close'], name='BTC/USDT', line=dict(color='orange')), row=2, col=1)

    # --- ETH Chart ---
    eth_df = load_kline_data('eth')
    if eth_df is not None:
        fig.add_trace(go.Scatter(x=eth_df['open_time'], y=eth_df['close'], name='ETH/USDT', line=dict(color='blue')), row=2, col=2)

    # --- Comparison Chart ---
    symbols = ['btc', 'eth', 'bnb', 'sol', 'ada']
    for s in symbols:
        df = load_kline_data(s)
        if df is not None:
            # Normalize to 100 for comparison
            normalized_price = (df['close'] / df['close'].iloc[0]) * 100
            fig.add_trace(go.Scatter(x=df['open_time'], y=normalized_price, name=s.upper()), row=3, col=1)

    fig.update_layout(height=1200, title_text="CryptoPulse Professional Analytics Dashboard", template="plotly_dark", showlegend=True)
    
    # Save as HTML
    fig.write_html(OUTPUT_FILE)
    print(f"Dashboard saved successfully to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_dashboard()
