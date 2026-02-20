import requests
import csv
from datetime import datetime
import time

def get_historical_data(symbol, period1, period2):
    """Fetch historical data using Unix timestamps"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={period1}&period2={period2}&interval=1d"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    result = data['chart']['result'][0]
    timestamps = result['timestamp']
    quotes = result['indicators']['quote'][0]
    
    history = []
    for i, ts in enumerate(timestamps):
        if quotes['close'][i] is not None:
            history.append({
                'symbol': symbol,
                'date': datetime.fromtimestamp(ts).strftime('%Y-%m-%d'),
                'open': quotes['open'][i],
                'high': quotes['high'][i],
                'low': quotes['low'][i],
                'close': quotes['close'][i],
                'volume': quotes['volume'][i]
            })
    
    return history

def save_to_csv(data, filename):
    """Save data to CSV file"""
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['symbol', 'date', 'open', 'high', 'low', 'close', 'volume'])
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    stocks = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'WIPRO.NS']
    
    # Get data from last 20 years (Unix timestamp)
    period2 = int(time.time())  # Now
    period1 = period2 - (20 * 365 * 24 * 60 * 60)  # 20 years ago
    
    all_data = []
    
    print("Fetching historical data...\n")
    for stock in stocks:
        print(f"Downloading {stock}...")
        history = get_historical_data(stock, period1, period2)
        all_data.extend(history)
        print(f"  ✓ {len(history)} records")
    
    save_to_csv(all_data, 'stock_data.csv')
    
    print(f"\n✓ Total records: {len(all_data)}")
    print(f"✓ Saved to: stock_data.csv")
