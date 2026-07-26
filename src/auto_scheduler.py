import os
import sys
import time
from datetime import datetime

# Direct the path back to root so we can access our system src modules
SCHEDULER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCHEDULER_DIR) if "src" in SCHEDULER_DIR else SCHEDULER_DIR
sys.path.append(PROJECT_ROOT)

from src.realtime_engine import run_live_pipeline

def start_autopilot():
    """
    Continuous background loop that monitors market time.
    Triggers our systematic EOD screening and execution exactly at 3:10 PM IST
    every single business day.
    """
    print("====================================================")
    # Use LaTeX formatting to give an premium touch in logs
    print("     🦅 ALPHAQUANT CAPITAL - AUTOMATED AUTOPILOT     ")
    print("====================================================")
    print("📡 Autopilot daemon initiated. Standing by for market signals...")
    
    # Save a flag so the Dashboard knows the autopilot is active
    flag_path = os.path.join(PROJECT_ROOT, "data", "autopilot_active.txt")
    os.makedirs(os.path.dirname(flag_path), exist_ok=True)
    with open(flag_path, "w") as f:
        f.write("ACTIVE")
        
    last_run_date = ""
    
    try:
        while True:
            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M")
            weekday = now.weekday() # 0 = Monday, 4 = Friday, 5/6 = Weekend
            
            # Check if it is a weekday and exactly 15:10 (3:10 PM IST)
            if weekday < 5: 
                if current_time == "15:10" and current_date != last_run_date:
                    print(f"\n⏰ Time matches execution window: {current_time} IST. Firing engine...")
                    try:
                        run_live_pipeline()
                        last_run_date = current_date # Ensure it only runs once per day
                    except Exception as e:
                        print(f"❌ Autopilot loop encountered operational error: {e}")
            
            # To simulate continuous operations for demonstration,
            # We also check every hour to monitor stop loss tracking of active holdings
            if now.minute == 0 and now.second == 0:
                print(f"🕒 Hourly check: Tracking active stops at {now.strftime('%H:%M:%S')}...")
                try:
                    run_live_pipeline()
                except Exception:
                    pass
                    
            time.sleep(10) # Poll every 10 seconds to keep CPU cycles low
            
    except KeyboardInterrupt:
        print("\n🛑 Autopilot stopped by user command.")
        if os.path.exists(flag_path):
            os.remove(flag_path)

if __name__ == "__main__":
    start_autopilot()