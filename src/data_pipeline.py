import pandas as pd
from datetime import datetime, timedelta
from .connection import get_fyers_model
import os

def fetch_historical_data(fyers, symbol, days=250):
    """
    Fetches daily historical OHLCV data using Fyers V3.
    Note: We request 250 days of data to securely cover the 120-day technical lookback window.
    """
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    data = {
        "symbol": f"NSE:{symbol}-EQ",
        "resolution": "D",  # Changed from "5" to "D" for Daily EOD analysis
        "date_format": "1", # YYYY-MM-DD
        "range_from": start_date,
        "range_to": end_date,
        "cont_flag": "1"
    }

    response = fyers.history(data=data)
    
    if response['s'] == 'ok':
        df = pd.DataFrame(response['candles'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        # Convert to IST (UTC+5:30)
        df['timestamp'] = df['timestamp'] + timedelta(hours=5, minutes=30)
        return df
    else:
        print(f"Error fetching historical Daily data for {symbol}: {response['message']}")
        return None

def save_data(df, symbol):
    if df is not None:
        path = f"data/raw/{symbol}_daily.csv"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)
        print(f"Saved {len(df)} daily candles for {symbol}")