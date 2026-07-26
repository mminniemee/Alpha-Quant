import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import os

def train_alphaquant_brain():
    dataset_path = "data/processed/training_data.csv"
    
    if not os.path.exists(dataset_path):
        print(f"❌ Error: Dataset file missing at {dataset_path}")
        return
        
    df = pd.read_csv(dataset_path)
    
    df = df.replace([np.inf, -np.inf], np.nan)
    feature_cols = [col for col in df.columns if col.startswith('feat_')]
    df = df.dropna(subset=feature_cols + ['target'])
    
    X = df[feature_cols]
    y = df['target'].astype(int)
    
    num_zeros = np.sum(y == 0)
    num_ones = np.sum(y == 1)
    
    if num_ones == 0:
        print("❌ Error: No successful trades (Class 1) found in the dataset. Increase your data history or loosen target rules.")
        return
        
    imbalance_ratio = num_zeros / num_ones
    
    print(f"📊 Dataset check: {num_zeros} Losses (0), {num_ones} Wins (1).")
    print(f"⚖️ Applying imbalance multiplier scale factor: {imbalance_ratio:.2f}x")
    
    # Uniform, stratified split to guarantee Class 1 is represented in validation
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        scale_pos_weight=imbalance_ratio,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss'
    )
    
    print("🏋️ Training balanced brain model...")
    model.fit(X_train, y_train)
    
    predictions = model.predict(X_test)
    
    print("\n=========================================")
    print(f"🎯 CORRECTED MODEL PERFORMANCE REPORT")
    print("=========================================")
    print(classification_report(y_test, predictions, zero_division=0))
    print("=========================================\n")
    
    os.makedirs("models", exist_ok=True)
    model.save_model("models/alphaquant_xgb.json")
    print("💾 Balanced model binary successfully compiled and saved!")

if __name__ == "__main__":
    train_alphaquant_brain()
