# Market Data - Indian Stock Historical Data

## Overview
Historical stock market data for top Indian companies listed on NSE (National Stock Exchange), fetched from Yahoo Finance API.

## Dataset Details

- **Total Records**: 24,655
- **Time Period**: 2006-02-27 to 2026-02-19 (~20 years)
- **Frequency**: Daily
- **Source**: Yahoo Finance
- **Format**: CSV

## Stocks Included

| Symbol | Company | Records |
|--------|---------|---------|
| RELIANCE.NS | Reliance Industries | ~5,000 |
| TCS.NS | Tata Consultancy Services | ~5,000 |
| INFY.NS | Infosys | ~5,000 |
| HDFCBANK.NS | HDFC Bank | ~5,000 |
| WIPRO.NS | Wipro | ~5,000 |

## Data Schema

| Column | Type | Description |
|--------|------|-------------|
| symbol | string | Stock ticker symbol (NSE) |
| date | string | Trading date (YYYY-MM-DD) |
| open | float | Opening price (₹) |
| high | float | Highest price (₹) |
| low | float | Lowest price (₹) |
| close | float | Closing price (₹) |
| volume | integer | Trading volume |

## Sample Data

```csv
symbol,date,open,high,low,close,volume
RELIANCE.NS,2006-02-27,80.35,80.67,79.66,80.02,47238261
TCS.NS,2024-01-15,3500.00,3550.25,3480.50,3525.75,2500000
```

## Usage

### Load with Python (pandas)
```python
import pandas as pd

df = pd.read_csv('stock_data.csv')
df['date'] = pd.to_datetime(df['date'])
print(df.head())
```

### Filter by Stock
```python
reliance = df[df['symbol'] == 'RELIANCE.NS']
```

### Calculate Returns
```python
df['daily_return'] = df.groupby('symbol')['close'].pct_change()
```

## Data Collection Script

Run `fetch_stock_data.py` to refresh data:
```bash
python fetch_stock_data.py
```

## Use Cases

- Technical analysis and backtesting
- Machine learning models for price prediction
- Portfolio optimization
- Risk analysis
- Market trend analysis

## Notes

- All prices are in Indian Rupees (₹)
- Data includes stock splits and dividends adjustments
- Market holidays excluded
- Real-time data fetched from Yahoo Finance API

## License

Data sourced from Yahoo Finance. For educational and research purposes only.
