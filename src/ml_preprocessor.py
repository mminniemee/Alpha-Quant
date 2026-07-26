import pandas as pd
import numpy as np
import pandas_ta as ta

def extract_features(df):
    """
    Advanced Quant Feature Engineering: Adds Volatility and Momentum context.
    """
    # Safeguard for length
    if len(df) < 20:
        return df

    # --- Existing Base Features ---
    df['feat_sma20_dist'] = ((df['close'] - df['sma20']) / df['sma20']) * 100
    
    candle_range = df['high'] - df['low']
    candle_range = np.where(candle_range == 0, 0.01, candle_range)
    df['feat_body_size'] = (df['close'] - df['open']).abs() / candle_range
    df['feat_vol_change'] = df['volume'].pct_change(5)
    
    # --- NEW: Institutional Context Features ---
    # 1. RSI (Momentum)
    df['feat_rsi'] = ta.rsi(df['close'], length=14)
    
    # 2. ATR Percent (Volatility relative to stock price)
    atr = ta.atr(df['high'], df['low'], df['close'], length=14)
    if atr is not None:
        df['feat_atr_pct'] = (atr / df['close']) * 100
    else:
        df['feat_atr_pct'] = 0.0
        
    return df

def strict_label_forward(df, entry_idx, target_pct=3.0, stop_pct=1.5):
    entry_price = df.loc[entry_idx, 'close']
    take_profit = entry_price * (1 + target_pct / 100.0)
    stop_loss = entry_price * (1 - stop_pct / 100.0)
    
    max_lookahead = min(entry_idx + 51, len(df))
    
    for future_idx in range(entry_idx + 1, max_lookahead):
        row = df.iloc[future_idx]
        if row['high'] >= take_profit:
            return 1
        if row['low'] <= stop_loss:
            return 0
            
    return 0
