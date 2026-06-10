"""
Run this script in the same environment where you trained your model
This will export your model so Django can use it
"""

import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

def export_model_for_django():
    """
    Export your trained model with all preprocessing objects
    """
    
    # Load your trained model and preprocessing objects
    # Method 1: If you saved them separately
    try:
        # Load your trained pipeline
        pipeline = joblib.load('dropout_final_model.pkl')
        
        # If pipeline is a dict
        if isinstance(pipeline, dict):
            model = pipeline['model']
            scaler = pipeline['scaler']
            imputer = pipeline['imputer']
        else:
            # If pipeline is a full sklearn pipeline
            model = pipeline
            scaler = StandardScaler()
            imputer = SimpleImputer()
            
    except:
        # Method 2: Train a quick model (for testing)
        print("Training a sample model for testing...")
        
        # Create sample data (replace with your actual data)
        X_train = np.random.rand(1000, 17)
        y_train = np.random.randint(0, 2, 1000)
        
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        scaler = StandardScaler()
        scaler.fit(X_train)
        
        imputer = SimpleImputer()
        imputer.fit(X_train)
    
    # Save all components
    joblib.dump(model, 'dropout_model.pkl')
    joblib.dump(scaler, 'scaler.pkl')
    joblib.dump(imputer, 'imputer.pkl')
    
    feature_names = [
        'Age', 'Gender', 'Family_Income', 'Internet_Access',
        'Study_Hours_per_Day', 'Attendance_Rate', 'Assignment_Delay_Days',
        'Travel_Time_Minutes', 'Part_Time_Job', 'Scholarship', 'Stress_Index',
        'GPA', 'Semester_GPA', 'CGPA', 'Semester', 'Department', 'Parental_Education'
    ]
    joblib.dump(feature_names, 'feature_names.pkl')
    
    print("✅ Model exported successfully!")
    print("Files created:")
    print("  - dropout_model.pkl")
    print("  - scaler.pkl")
    print("  - imputer.pkl")
    print("  - feature_names.pkl")
    
    # Instructions to move files
    print("\n📁 Next steps:")
    print("1. Copy these files to: prediction/ml_models/")
    print("2. Run: python prediction/save_trained_model.py")

if __name__ == "__main__":
    export_model_for_django()