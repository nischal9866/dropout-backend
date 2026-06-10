import joblib
import pandas as pd
import numpy as np
from pathlib import Path
import json
import logging
import os

# Set Django settings module for standalone runs
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings

logger = logging.getLogger(__name__)

class DropoutPredictor:
    """Service class for student dropout prediction"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.imputer = None
        self.feature_names = None
        self.model_info = None
        self.threshold = 0.5
        self.load_models()
    
    def load_models(self):
        """Load all saved ML models and artifacts"""
        try:
            # Define paths
            model_dir = Path(__file__).parent / 'ml_models'
            
            model_path = model_dir / 'dropout_model.pkl'
            scaler_path = model_dir / 'scaler.pkl'
            imputer_path = model_dir / 'imputer.pkl'
            features_path = model_dir / 'feature_names.pkl'
            info_path = model_dir / 'model_info.json'
            
            # Load model
            if model_path.exists():
                self.model = joblib.load(model_path)
                print(f"✅ Model loaded from {model_path}")
            else:
                print(f"⚠️ Model not found at {model_path}")
                return
            
            # Load scaler
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
                print("✅ Scaler loaded")
            
            # Load imputer
            if imputer_path.exists():
                self.imputer = joblib.load(imputer_path)
                print("✅ Imputer loaded")
            
            # Load feature names
            if features_path.exists():
                self.feature_names = joblib.load(features_path)
                print(f"✅ Loaded {len(self.feature_names)} features")
            
            # Load model info
            if info_path.exists():
                with open(info_path, 'r') as f:
                    self.model_info = json.load(f)
                self.threshold = self.model_info.get('threshold', 0.5)
                print("✅ Model info loaded")
                
        except Exception as e:
            print(f"Error loading models: {str(e)}")
    
    def preprocess_input(self, data):
        """Preprocess input data matching your dataset"""
        try:
            # Create DataFrame with exact feature order
            feature_dict = {}
            
            # Define mappings for categorical variables
            gender_map = {'Male': 1, 'Female': 0}
            yes_no_map = {'Yes': 1, 'No': 0}
            dept_map = {'CS': 0, 'Engineering': 1, 'Business': 2, 'Arts': 3, 'Science': 4}
            semester_map = {'Year 1': 1, 'Year 2': 2, 'Year 3': 3, 'Year 4': 4}
            edu_map = {
                'No Formal Education': 0, 
                'High School': 1, 
                'Bachelor': 2, 
                'Master': 3, 
                'PhD': 4
            }
            
            # Map input data to expected features
            for feature in self.feature_names:
                if feature in data:
                    value = data[feature]
                    
                    # Handle categorical variables
                    if feature == 'Gender':
                        feature_dict[feature] = gender_map.get(value, 0)
                    elif feature in ['Internet_Access', 'Part_Time_Job', 'Scholarship']:
                        feature_dict[feature] = yes_no_map.get(value, 0)
                    elif feature == 'Department':
                        feature_dict[feature] = dept_map.get(value, 0)
                    elif feature == 'Semester':
                        feature_dict[feature] = semester_map.get(value, 1)
                    elif feature == 'Parental_Education':
                        feature_dict[feature] = edu_map.get(value, 1)
                    else:
                        # Numerical features
                        try:
                            feature_dict[feature] = float(value) if value not in [None, ''] else 0
                        except:
                            feature_dict[feature] = 0
                else:
                    feature_dict[feature] = 0
            
            # Create DataFrame
            df = pd.DataFrame([feature_dict])
            
            # Reorder columns to match training
            df = df[self.feature_names]
            
            # Handle missing values
            if self.imputer:
                df = pd.DataFrame(
                    self.imputer.transform(df),
                    columns=df.columns
                )
            
            # Scale features
            if self.scaler:
                df = pd.DataFrame(
                    self.scaler.transform(df),
                    columns=df.columns
                )
            
            return df
            
        except Exception as e:
            logger.error(f"Preprocessing error: {str(e)}")
            raise
    
    def predict(self, student_data):
        """Make prediction for a single student"""
        try:
            if self.model is None:
                return {
                    'dropout_probability': 0,
                    'risk_level': 'Model Not Loaded',
                    'prediction': 'Error',
                    'confidence_score': 0,
                    'recommendations': ['Model not properly configured'],
                    'key_factors': [],
                    'timestamp': pd.Timestamp.now().isoformat()
                }
            
            processed_data = self.preprocess_input(student_data)
            
            if hasattr(self.model, 'predict_proba'):
                probability = self.model.predict_proba(processed_data)[0]
                prediction = self.model.predict(processed_data)[0]
                
                # Dropout probability (class 1 is dropout)
                dropout_prob = float(probability[1])
                
                # Apply threshold
                final_prediction = 1 if dropout_prob >= self.threshold else 0
                
                # Determine risk level
                risk_level = self.get_risk_level(dropout_prob)
                
                # Generate recommendations
                recommendations = self.generate_recommendations(student_data, dropout_prob)
                
                # Get key factors
                key_factors = self.get_key_factors(student_data, dropout_prob)
                
                return {
                    'dropout_probability': round(dropout_prob * 100, 2),
                    'risk_level': risk_level,
                    'prediction': 'At Risk of Dropout' if final_prediction == 1 else 'On Track',
                    'confidence_score': round(max(probability) * 100, 2),
                    'recommendations': recommendations,
                    'key_factors': key_factors,
                    'threshold_used': round(self.threshold * 100, 2),
                    'timestamp': pd.Timestamp.now().isoformat()
                }
            else:
                return {
                    'dropout_probability': 0,
                    'risk_level': 'Unknown',
                    'prediction': 'Unable to predict',
                    'error': 'Model not properly loaded'
                }
                
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return {
                'dropout_probability': 0,
                'risk_level': 'Error',
                'prediction': 'Error',
                'error': str(e),
                'timestamp': pd.Timestamp.now().isoformat()
            }
    
    def get_risk_level(self, probability):
        """Determine risk level based on dropout probability"""
        if probability < 0.3:
            return 'Low Risk'
        elif probability < 0.6:
            return 'Medium Risk'
        elif probability < 0.8:
            return 'High Risk'
        else:
            return 'Critical Risk'
    
    def generate_recommendations(self, data, probability):
        """Generate personalized recommendations"""
        recommendations = []
        
        # GPA related
        gpa = float(data.get('GPA', 0))
        if gpa < 1.5:
            recommendations.append("🔴 CRITICAL: Schedule emergency academic counseling immediately")
            recommendations.append("📚 Enroll in intensive tutoring programs")
        elif gpa < 2.0:
            recommendations.append("🟡 Meet with academic advisor weekly")
            recommendations.append("📖 Join study groups")
        
        # Attendance
        attendance = float(data.get('Attendance_Rate', 0))
        if attendance < 70:
            recommendations.append("📅 Critical attendance issue - Required meeting required")
            recommendations.append("⏰ Set daily attendance reminders")
        elif attendance < 85:
            recommendations.append("📊 Improve attendance - Aim for 90%+")
        
        # Assignment delays
        delays = float(data.get('Assignment_Delay_Days', 0))
        if delays > 10:
            recommendations.append("📝 Chronic assignment delays - Time management workshop required")
        elif delays > 5:
            recommendations.append("⏰ Create structured assignment submission schedule")
        
        # Study hours
        study_hours = float(data.get('Study_Hours_per_Day', 0))
        if study_hours < 2:
            recommendations.append("📚 Increase study time - Minimum 3-4 hours recommended")
        
        # Part-time job impact
        if data.get('Part_Time_Job') == 'Yes':
            recommendations.append("💼 Balance work and study - Consider reducing work hours")
        
        # Scholarship
        if data.get('Scholarship') == 'No':
            recommendations.append("💰 Apply for scholarships and financial aid")
        
        # High risk recommendations
        if probability > 0.7:
            recommendations.append("🚨 IMMEDIATE INTERVENTION REQUIRED")
            recommendations.append("📞 Contact student support services")
        
        return list(dict.fromkeys(recommendations))[:5]
    
    def get_key_factors(self, data, probability):
        """Identify key contributing factors"""
        factors = []
        
        # GPA factors
        gpa = float(data.get('GPA', 4.0))
        if gpa < 1.5:
            factors.append(f"Critically low GPA ({gpa:.2f}) - Primary risk factor")
        elif gpa < 2.0:
            factors.append(f"Low GPA ({gpa:.2f})")
        
        # CGPA factor
        cgpa = float(data.get('CGPA', 4.0))
        if cgpa < 1.8:
            factors.append(f"Low cumulative GPA ({cgpa:.2f})")
        
        # Attendance factor
        attendance = float(data.get('Attendance_Rate', 100))
        if attendance < 70:
            factors.append(f"Critical absenteeism ({attendance}%)")
        elif attendance < 85:
            factors.append(f"Below average attendance ({attendance}%)")
        
        # Assignment delays
        delays = float(data.get('Assignment_Delay_Days', 0))
        if delays > 15:
            factors.append(f"Severe assignment delays ({delays} days)")
        
        # Study habits
        study_hours = float(data.get('Study_Hours_per_Day', 0))
        if study_hours < 2:
            factors.append(f"Insufficient study time ({study_hours} hrs/day)")
        
        return factors[:4]

# Create singleton instance
predictor = DropoutPredictor()