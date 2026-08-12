import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

def generate_shap_background_data():
    # Load model artifacts
    model_dir = Path(__file__).parent.parent / 'ml_models'
    
    label_encoders_path = model_dir / 'label_encoders.pkl'
    imputer_path = model_dir / 'imputer.pkl'
    scaler_path = model_dir / 'scaler.pkl'
    feature_names_path = model_dir / 'feature_names.pkl'
    
    if not (label_encoders_path.exists() and imputer_path.exists() and scaler_path.exists() and feature_names_path.exists()):
        print("[ERROR] Model artifacts are missing in ml_models. Please train/save them first.")
        return
        
    label_encoders = joblib.load(label_encoders_path)
    imputer = joblib.load(imputer_path)
    scaler = joblib.load(scaler_path)
    feature_names = joblib.load(feature_names_path)
    
    # Find dataset
    dataset_path = Path('D:/sklearn/dataset.csv')
    if not dataset_path.exists():
        print(f"[ERROR] dataset.csv not found at {dataset_path}")
        return
        
    print(f"[INFO] Loading dataset from {dataset_path}...")
    df = pd.read_csv(dataset_path)
    X = df.drop(['Dropout', 'Student_ID'], axis=1, errors='ignore')
    
    print("[INFO] Preprocessing data...")
    # Encode categorical columns
    for col, encoder in label_encoders.items():
        if col in X.columns:
            # Safely transform values, using 0 for unseen or errors
            classes_set = set(encoder.classes_)
            X[col] = X[col].astype(str).map(lambda val: encoder.transform([val])[0] if val in classes_set else 0)
                
    # Ensure correct columns order
    X = X[feature_names]
    
    # Impute missing values
    X_imputed = imputer.transform(X)
    
    # Scale features
    X_scaled = scaler.transform(X_imputed)
    
    # Summarize the background data to 100 samples
    np.random.seed(42)
    sample_size = min(100, X_scaled.shape[0])
    indices = np.random.choice(X_scaled.shape[0], size=sample_size, replace=False)
    background_data = X_scaled[indices]
    
    # Save background data
    output_path = model_dir / 'background_data.pkl'
    joblib.dump(background_data, output_path)
    print(f"[SUCCESS] Generated background data for SHAP at {output_path} with shape {background_data.shape}")

if __name__ == "__main__":
    generate_shap_background_data()
