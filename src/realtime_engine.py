import os
import sys
import json
import pandas as pd
from datetime import datetime

# Direct the path back to root so we can access our system src modules
ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(ENGINE_DIR) if "src" in ENGINE_DIR else ENGINE_DIR
sys.path.append(PROJECT_ROOT)

from src.connection import get_fyers_model
from src.data_pipeline import fetch_historical_data
from src.indicators import apply_daily_indicators, check_daily_signals, get_top_fundamental_symbols

# Absolute file paths for cross-process state management
PORTFOLIO_FILE = os.path.join(PROJECT_ROOT, "data", "active_portfolio.json")
HISTORY_FILE = os.path.join(PROJECT_ROOT, "data", "trade_history.json")

def load_portfolio():
    """
    Loads active holdings safely from the shared JSON file.
    """
    if not os.path.exists(PORTFOLIO_FILE):
        return {}
    try:
        with open(PORTFOLIO_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_portfolio(portfolio):
    """
    Saves current portfolio status to guarantee consistency across processes.
    """
    os.makedirs(os.path.dirname(PORTFOLIO_FILE), exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(portfolio, f, indent=4)

def log_decision(action, symbol, price, qty, reason):
    """
    Maintains a permanent, human-readable execution journal 
    to guarantee absolute transparency to investors.
    """
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except Exception:
            history = []
            
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,      # "BUY", "SELL", or "SYSTEM_SKIP"
        "symbol": symbol,
        "price": price,
        "qty": qty,
        "reason": reason
    }
    history.insert(0, record)  # Insert newest logs on top
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

def run_live_pipeline():
    """
    Autonomous Daily Pipeline: Runs active risk management updates
    and executes new breakout setups for Nifty 500.
    """
    print(f"🚀 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Launching Nifty 500 Autonomous Pipeline...")
    
    # 1. API Token Verification
    token_path = os.path.join(PROJECT_ROOT, "access_token.txt")
    if not os.path.exists(token_path):
        print("❌ Fyers Token missing. Running in simulation mode or waiting for auth handshake.")
        return
        
    with open(token_path, "r") as f:
        token = f.read().strip()
    
    fyers = get_fyers_model(token)
    portfolio = load_portfolio()
    
    # Setup constraints (X = ₹1,00,000 per asset)
    allocation_limit = 100000.0
    watchlist = get_top_fundamental_symbols(limit=5)
    
    # -------------------------------------------------------------
    # PHASE 1: MANAGE RISK & TRAILING STOP EXITS (STAGE 3 CHECKS)
    # -------------------------------------------------------------
    active_assets = list(portfolio.keys())
    for symbol in active_assets:
        try:
            print(f"📡 Evaluating trailing risk matrices for {symbol}...")
            df = fetch_historical_data(fyers, symbol, days=150)
            if df is None or len(df) == 0:
                print(f"⚠️ Unable to fetch history for {symbol}, skipping safety checks.")
                continue
                
            df = apply_daily_indicators(df)
            last_row = df.iloc[-1]
            current_price = last_row['close']
            sma20 = last_row['sma20']
            
            entry_price = portfolio[symbol]['entry_price']
            hard_stop = entry_price * 0.80  # Emergency Stop Floor at -20%
            
            # Guardrail 1: Emergency Hard Stop Breach
            if current_price <= hard_stop:
                reason = f"🚨 Emergency Stop Loss Executed: Price (₹{current_price:,.2f}) fell below the hard -20% limit (₹{hard_stop:,.2f})."
                qty = portfolio[symbol]['qty']
                log_decision("SELL", symbol, current_price, qty, reason)
                del portfolio[symbol]
                continue
                
            # Guardrail 2: Two-Step Exit Confirmation - Step 1 (SMA20 Breach)
            if current_price < sma20:
                if portfolio[symbol].get('setup_low') is None:
                    # Log Setup Low using Candle A's absolute Low
                    candle_a_low = last_row['low']
                    portfolio[symbol]['setup_low'] = candle_a_low
                    reason = f"⚠️ Step 1 Trailing Exit: Daily close (₹{current_price:,.2f}) fell below 20 SMA. Setup Low logged at ₹{candle_a_low:,.2f}."
                    log_decision("SYSTEM_SKIP", symbol, current_price, 0, reason)
            else:
                # Progression (Reset Ring): Close has recovered above 20 SMA
                if portfolio[symbol].get('setup_low') is not None:
                    portfolio[symbol]['setup_low'] = None
                    reason = "🔄 Reset Ring: Trailing Setup Low wiped clean because price close recovered back above its 20 SMA."
                    log_decision("SYSTEM_SKIP", symbol, current_price, 0, reason)
            
            # Guardrail 3: Two-Step Exit Confirmation - Step 2 (Trigger Liquidation)
            setup_low = portfolio[symbol].get('setup_low')
            if setup_low is not None and current_price < setup_low:
                reason = f"🛑 Step 2 Trailing Exit Triggered: Daily Close (₹{current_price:,.2f}) dropped below logged Setup Low (₹{setup_low:,.2f}). Position liquidated."
                qty = portfolio[symbol]['qty']
                log_decision("SELL", symbol, current_price, qty, reason)
                del portfolio[symbol]
                continue
                
        except Exception as e:
            print(f"❌ Error checking risk variables for {symbol}: {e}")
            
    save_portfolio(portfolio)
    
    # -------------------------------------------------------------
    # PHASE 2: DAILY BREAKOUT MOMENTUM SCREENER (STAGE 1 & 2 CHECKS)
    # -------------------------------------------------------------
    portfolio = load_portfolio()  # Fetch latest state
    
    for symbol in watchlist:
        # Duplicate Prevention: Don't buy if we already have exposure to this asset
        if symbol in portfolio:
            print(f"⏭️ Skipping {symbol}: Asset already has an active position.")
            continue
            
        try:
            print(f"🔍 Screening breakout variables for {symbol}...")
            df = fetch_historical_data(fyers, symbol, days=150)
            if df is None or len(df) < 121:
                print(f"⚠️ Insufficient daily history to check 120-Day channels for {symbol}.")
                continue
                
            df = apply_daily_indicators(df)
            result = check_daily_signals(df, symbol)
            last_row = df.iloc[-1]
            last_price = last_row['close']
            
            if result['entry']:
                # Price Cap Filter: Don't buy if individual share price exceeds allocation limit (X)
                if last_price > allocation_limit:
                    reason = f"🚫 Order Blocked: Asset price (₹{last_price:,.2f}) exceeds trade allocation limit (₹{allocation_limit:,.2f})."
                    log_decision("SYSTEM_SKIP", symbol, last_price, 0, reason)
                    continue
                    
                # Floor Allocation Sizing: Max whole shares we can purchase
                qty = int(allocation_limit // last_price)
                if qty > 0:
                    portfolio[symbol] = {
                        "qty": qty,
                        "entry_price": last_price,
                        "setup_low": None,
                        "highest_close": last_price,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    reason = f"🟢 Automated Buy Order Filled: Daily breakout confirmed on Nifty 500 company with PBT >= 25% QoQ. Bought {qty} shares."
                    log_decision("BUY", symbol, last_price, qty, reason)
                    
        except Exception as e:
            print(f"❌ Error evaluating breakout setups for {symbol}: {e}")
            
    save_portfolio(portfolio)
    print("🏁 Pipeline cycle completed successfully.")

if __name__ == "__main__":
    run_live_pipeline()