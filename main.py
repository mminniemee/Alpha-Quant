import os
import sys
from src.connection import get_fyers_model
from src.data_pipeline import fetch_historical_data
from src.indicators import apply_indicators, check_signals

# CONFIGURATION
WATCHLIST = ["RELIANCE", "SBIN", "TCS", "INFY"] # Add your symbols here

def run_alphaquant_scanner():
    print("=========================================")
    print("      ALPHAQUANT ML SYSTEM - PHASE 2     ")
    print("=========================================\n")
    
    # 1. Authenticate
    if not os.path.exists("access_token.txt"):
        print("❌ Error: access_token.txt not found. Run auth.py first.")
        return
        
    with open("access_token.txt", "r") as f:
        token = f.read().strip()
    
    fyers = get_fyers_model(token)
    
    # 2. Iterate through Watchlist
    for symbol in WATCHLIST:
        try:
            print(f"🔍 Analyzing: {symbol}...", end="\r")
            
            # Fetch 30 days of 5-minute candles
            df = fetch_historical_data(fyers, symbol, days=30)
            
            if df is not None:
                df = apply_indicators(df)
                result = check_signals(df, symbol)
                
                last_price = df.iloc[-1]['close']
                
                # Professional Console Output
                status_icon = "🟢" if result['entry'] else "🔴" if result['exit'] else "⚪"
                print(f"{status_icon} {symbol.ljust(10)} | Price: {last_price:<8} | Signal: {result['reason']}")
            
        except Exception as e:
            print(f"❌ Error scanning {symbol}: {e}")

if __name__ == "__main__":
    run_alphaquant_scanner()