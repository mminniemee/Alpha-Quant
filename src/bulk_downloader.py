import os
import pandas as pd
from datetime import datetime, timedelta
from fyers_apiv3 import fyersModel
from dotenv import load_dotenv
import time

load_dotenv()

SYMBOLS = [
    "NSE:ADANIENT-EQ", "NSE:ADANIPORTS-EQ", "NSE:APOLLOHOSP-EQ", "NSE:ASIANPAINT-EQ", "NSE:AXISBANK-EQ",
    "NSE:BAJAJ-AUTO-EQ", "NSE:BAJAJFINSV-EQ", "NSE:BAJFINANCE-EQ", "NSE:BEL-EQ", "NSE:BHARTIARTL-EQ",
    "NSE:BPCL-EQ", "NSE:BRITANNIA-EQ", "NSE:CIPLA-EQ", "NSE:COALINDIA-EQ", "NSE:DIVISLAB-EQ",
    "NSE:DRREDDY-EQ", "NSE:EICHERMOT-EQ", "NSE:GRASIM-EQ", "NSE:HCLTECH-EQ", "NSE:HDFCBANK-EQ",
    "NSE:HEROMOTOCO-EQ", "NSE:HINDALCO-EQ", "NSE:HINDUNILVR-EQ", "NSE:ICICIBANK-EQ", "NSE:INDUSINDBK-EQ",
    "NSE:INFY-EQ", "NSE:ITC-EQ", "NSE:JSWSTEEL-EQ", "NSE:KOTAKBANK-EQ", "NSE:LT-EQ",
    "NSE:LTIM-EQ", "NSE:M&M-EQ", "NSE:MARUTI-EQ", "NSE:NESTLEIND-EQ", "NSE:NTPC-EQ",
    "NSE:ONGC-EQ", "NSE:POWERGRID-EQ", "NSE:RELIANCE-EQ", "NSE:SBILIFE-EQ", "NSE:SBIN-EQ",
    "NSE:SHRIRAMFIN-EQ", "NSE:SUNPHARMA-EQ", "NSE:TATACONSUM-EQ", "NSE:TATAMOTORS-EQ", "NSE:TATASTEEL-EQ",
    "NSE:TCS-EQ", "NSE:TECHM-EQ", "NSE:TITAN-EQ", "NSE:TRENT-EQ", "NSE:ULTRACEMCO-EQ", "NSE:WIPRO-EQ"
]
def get_fyers_client():
    # Read token directly from the file to ensure it's fresh
    if not os.path.exists("access_token.txt"):
        print("❌ access_token.txt not found! Run auth.py first.")
        return None
        
    with open("access_token.txt", "r") as f:
        access_token = f.read().strip()
        
    client_id = os.getenv("FYERS_CLIENT_ID")
    return fyersModel.FyersModel(client_id=client_id, token=access_token, is_async=False, log_path="")

def download_stock_data(fyers, symbol, days=365):
    all_candles = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    current_to = end_date
    while current_to > start_date:
        current_from = max(start_date, current_to - timedelta(days=90))
        
        data = {
            "symbol": symbol,
            "resolution": "5",
            "date_format": "1",
            "range_from": current_from.strftime("%Y-%m-%d"),
            "range_to": current_to.strftime("%Y-%m-%d"),
            "cont_flag": "1"
        }
        
        response = fyers.history(data=data)
        
        if response.get("s") == "ok":
            all_candles.extend(response.get("candles"))
            # Success! Move to the next chunk
            current_to = current_from - timedelta(days=1)
            time.sleep(1.2) # Increased delay to prevent Code 429
        elif response.get("code") == 429 or "limit" in str(response).lower():
            print(f"⚠️ Rate limited on {symbol}. Sleeping for 30 seconds...")
            time.sleep(30)
            continue # Try the same chunk again
        else:
            print(f"❌ Error on {symbol}: {response}")
            return None

    if not all_candles:
        return None
        
    df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df = df.sort_values('timestamp').drop_duplicates()
    return df

# ... (SYMBOLS list goes here) ...

if __name__ == "__main__":
    fyers = get_fyers_client()
    if fyers:
        os.makedirs("data/raw", exist_ok=True)
        for symbol in SYMBOLS:
            df = download_stock_data(fyers, symbol)
            if df is not None and not df.empty:
                filename = f"data/raw/{symbol.replace(':', '_')}.csv"
                df.to_csv(filename, index=False)
                print(f"✅ Saved {len(df)} rows for {symbol}")
                time.sleep(2) # Gap between different stocks