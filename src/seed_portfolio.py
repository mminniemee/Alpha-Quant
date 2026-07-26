import json
import os

PORTFOLIO_FILE = "data/active_portfolio.json"

def seed_mock_trades():
    print("====================================================")
    print("         ALPHAQUANT PORTFOLIO SEEDER UTILITY        ")
    print("====================================================\n")
    
    # Define realistic mock active trades to seed
    # TRENT has had high growth and is an ideal mock target
    mock_portfolio = {
        "TRENT": {
            "entry_price": 4000.00,
            "highest_close": 4150.00,
            "qty": 25,          # floor(100,000 / 4000)
            "setup_low": None   # Currently running in a strong bullish trend
        },
        "SBIN": {
            "entry_price": 950.00,
            "highest_close": 980.00,
            "qty": 105,         # floor(100,000 / 950)
            "setup_low": 930.00 # A pullback below the 20 SMA occurred, establishing this anchor
        }
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(PORTFOLIO_FILE), exist_ok=True)
    
    # Write to active portfolio JSON
    with open(PORTFOLIO_FILE, 'w') as f:
        json.dump(mock_portfolio, f, indent=4)
        
    print(f"✨ Success! Seeded mock trades into: {PORTFOLIO_FILE}")
    print("👉 Active Position 1: TRENT (Bullish Run mode)")
    print("👉 Active Position 2: SBIN (Setup Low Logged - Step 1 Exit active)")
    print("\nNext, launch your Streamlit dashboard to visualize the risk states!")

if __name__ == "__main__":
    seed_mock_trades()