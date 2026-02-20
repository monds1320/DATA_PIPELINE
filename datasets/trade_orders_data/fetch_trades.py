import requests
import pandas as pd
import time
from datetime import datetime
import random

print("Fetching Trade Orders & Execution Data...\n")

def get_intraday_data(symbol):
    """Fetch intraday trade data (1-minute intervals)"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    result = data['chart']['result'][0]
    timestamps = result['timestamp']
    quotes = result['indicators']['quote'][0]
    
    trades = []
    order_id = 1
    
    for i, ts in enumerate(timestamps):
        if quotes['close'][i] is not None:
            # Simulate order execution from price data
            price = quotes['close'][i]
            volume = quotes['volume'][i] if quotes['volume'][i] else 0
            
            # Generate realistic order data
            trades.append({
                'order_id': f'ORD{order_id:010d}',
                'symbol': symbol,
                'timestamp': datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'),
                'order_type': random.choice(['MARKET', 'LIMIT', 'STOP']),
                'side': random.choice(['BUY', 'SELL']),
                'quantity': random.randint(1, 1000),
                'order_price': round(price, 2),
                'execution_price': round(price + random.uniform(-0.5, 0.5), 2),
                'executed_quantity': random.randint(1, 1000),
                'order_status': random.choice(['FILLED', 'FILLED', 'FILLED', 'PARTIAL', 'CANCELLED']),
                'exchange': 'NSE',
                'order_time': datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'),
                'execution_time': datetime.fromtimestamp(ts + random.randint(1, 60)).strftime('%Y-%m-%d %H:%M:%S'),
                'trader_id': f'TRD{random.randint(1000, 9999)}',
                'volume': volume
            })
            order_id += 1
    
    return trades

# Fetch data for multiple stocks
stocks = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'WIPRO.NS']
all_trades = []

print("Downloading trade execution data...\n")
for stock in stocks:
    print(f"Fetching {stock}...")
    trades = get_intraday_data(stock)
    all_trades.extend(trades)
    print(f"  ✓ {len(trades)} orders")
    time.sleep(1)

df = pd.DataFrame(all_trades)

# Save in required formats
print("\nSaving in real-world formats...")

# JSON (streaming/line-delimited)
df.to_json('trade_orders.json', orient='records', lines=True)
print("✓ JSON: trade_orders.json (streaming)")

# Parquet
df.to_parquet('trade_orders.parquet', index=False)
print("✓ Parquet: trade_orders.parquet")

print(f"\n✓ Total Orders: {len(df)}")
print(f"✓ Filled Orders: {len(df[df['order_status'] == 'FILLED'])}")
print(f"✓ Cancelled Orders: {len(df[df['order_status'] == 'CANCELLED'])}")

print("\nSample Orders:")
print(df[['order_id', 'symbol', 'side', 'quantity', 'execution_price', 'order_status']].head(5))
