import pandas as pd
import numpy as np
import glob
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.indicators import apply_indicators
from src.ml_preprocessor import extract_features, strict_label_forward

def generate_master_dataset():
    raw_files = glob.glob("data/raw/*.csv")
    master_list = []
    
    print("🔄 Building balanced technical entry dataset...")
    
    for file in raw_files:
        symbol = os.path.basename(file).replace(".csv", "")
        df = pd.read_csv(file)
        
        df = apply_indicators(df)
        if df is None or len(df) < 52:
            continue
            
        df = extract_features(df)
        
        # Chronological technical condition assignment
        df['prev_close'] = df['close'].shift(1)
        df['prev_sma20'] = df['sma20'].shift(1)
        df['prev_high'] = df['high'].shift(1)
        
        crossed_20 = (df['prev_close'] <= df['prev_sma20']) & (df['close'] > df['sma20'])
        st_buy = df['st_direction'] == 1
        high_broken = df['close'] > df['prev_high']
        
        # Locate exact setup triggers
        trigger_indices = df[crossed_20 & st_buy & high_broken].index.tolist()
        
        valid_rows = []
        for idx in trigger_indices:
            if idx < len(df) - 51:
                target_label = strict_label_forward(df, idx, target_pct=1.0, stop_pct=0.5)
                row_data = df.loc[idx].copy()
                row_data['target'] = target_label
                row_data['symbol_name'] = symbol
                valid_rows.append(row_data)
                
        if valid_rows:
            symbol_df = pd.DataFrame(valid_rows)
            master_list.append(symbol_df)
            print(f"✅ Extracted {len(symbol_df)} true setups for {symbol}")

    if not master_list:
        print("❌ Zero setups matched your criteria across all data files.")
        return

    final_df = pd.concat(master_list, ignore_index=True)
    
    # Drop rows with NaN values in the newly computed features
    feature_cols = [col for col in final_df.columns if col.startswith('feat_')]
    final_df = final_df.dropna(subset=feature_cols + ['target'])
    
    os.makedirs("data/processed", exist_ok=True)
    final_df.to_csv("data/processed/training_data.csv", index=False)
    
    print(f"\n✨ Dataset saved! Total entries: {len(final_df)}")
    print(f"📊 Class Distribution:\n{final_df['target'].value_counts()}")

if __name__ == "__main__":
    generate_master_dataset()
