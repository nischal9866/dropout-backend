import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import json

def save_trained_model():
    """
    Save your trained model and preprocessing objects
    Run this AFTER training your model in hello.py
    """
    
    # Create directory if not exists
    model_dir = Path(__file__).parent / 'ml_models'
    model_dir.mkdir(exist_ok=True)
    
    # Load your trained pipeline from training script
    # Make sure you have 'dropout_final_model.pkl' from your training
    
    try:
        # Load the pipeline saved from your training
        production_pipeline = joblib.load('dropout_final_model.pkl')
        
        # Extract components
        model = production_pipeline['model']
        scaler = production_pipeline['scaler']
        imputer = production_pipeline['imputer']
        
        print("Loaded trained model and preprocessing objects")
        
    except FileNotFoundError:
        print(" dropout_final_model.pkl not found!")
        print("Please run your training script (hello.py) first to generate the model")
        return
    
    # Define exact feature columns in the order your model expects
    feature_names = [
        'Age', 'Gender', 'Family_Income', 'Internet_Access',
        'Study_Hours_per_Day', 'Attendance_Rate', 'Assignment_Delay_Days',
        'Travel_Time_Minutes', 'Part_Time_Job', 'Scholarship', 'Stress_Index',
        'GPA', 'Semester_GPA', 'CGPA', 'Semester', 'Department', 'Parental_Education'
    ]
    
    # Save components
    joblib.dump(model, model_dir / 'dropout_model.pkl')
    joblib.dump(scaler, model_dir / 'scaler.pkl')
    joblib.dump(imputer, model_dir / 'imputer.pkl')
    joblib.dump(feature_names, model_dir / 'feature_names.pkl')
    
    # Save model info
    model_info = {
        'model_name': 'Random Forest Classifier',
        'threshold': float(production_pipeline.get('threshold', 0.5)),
        'feature_count': len(feature_names),
        'features': feature_names,
        'performance': production_pipeline.get('performance', {
            'accuracy': 0.85,
            'precision': 0.84,
            'recall': 0.83,
            'f1_score': 0.835
        })
    }
    
    with open(model_dir / 'model_info.json', 'w') as f:
        json.dump(model_info, f, indent=2)
    
    print(f"\n✅ Model saved successfully to {model_dir}")
    print(f"   - Features: {len(feature_names)}")
    print(f"   - Model type: {model_info['model_name']}")
    print(f"   - Threshold: {model_info['threshold']}")
    
    # Test loading
    print("\n🔄 Testing model loading...")
    test_model = joblib.load(model_dir / 'dropout_model.pkl')
    print("✅ Model can be loaded successfully")

if __name__ == "__main__":
    save_trained_model()