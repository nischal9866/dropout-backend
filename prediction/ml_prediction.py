import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

class DropoutPredictor:
    """Service class for student dropout prediction using Logistic Regression"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.imputer = None
        self.feature_names = None
        self.categorical_mappings = None
        self.model_info = None
        self.threshold = 0.40  # Optimal threshold from your analysis
        self.load_models()
    
    def load_models(self):
        """Load all saved ML models and artifacts"""
        try:
            model_dir = Path(__file__).parent / 'ml_models'
            
            print(f"📁 Loading models from: {model_dir}")
            
            # Load model
            model_path = model_dir / 'dropout_model.pkl'
            if model_path.exists():
                self.model = joblib.load(model_path)
                print(f"✅ Model loaded: {type(self.model).__name__}")
            else:
                print(f"❌ Model not found at {model_path}")
                return
            
            # Load scaler
            scaler_path = model_dir / 'scaler.pkl'
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
                print("✅ Scaler loaded")
            
            # Load imputer
            imputer_path = model_dir / 'imputer.pkl'
            if imputer_path.exists():
                self.imputer = joblib.load(imputer_path)
                print("✅ Imputer loaded")
            
            # Load feature names
            features_path = model_dir / 'feature_names.pkl'
            if features_path.exists():
                self.feature_names = joblib.load(features_path)
                print(f"✅ Loaded {len(self.feature_names)} features")
            
            # Load label encoders
            encoders_path = model_dir / 'label_encoders.pkl'
            if encoders_path.exists():
                self.categorical_mappings = joblib.load(encoders_path)
                print(f"✅ Loaded {len(self.categorical_mappings)} categorical encoders")
            
            # Load model info
            info_path = model_dir / 'model_info.json'
            if info_path.exists():
                with open(info_path, 'r') as f:
                    self.model_info = json.load(f)
                self.threshold = self.model_info.get('threshold', 0.40)
                print(f"✅ Model info loaded - Threshold: {self.threshold}")
                print(f"   Model: {self.model_info.get('model_name')}")
                print(f"   Strategy: {self.model_info.get('strategy')}")
                print(f"   Recall: {self.model_info.get('performance', {}).get('recall', 'N/A')}")
            
            print("\n🎯 Dropout Prediction System Ready!")
            print("   Using Logistic Regression (Balanced) - 76.86% Recall")
            
        except Exception as e:
            print(f"❌ Error loading models: {str(e)}")
    
    def preprocess_input(self, data):
        """Preprocess input data matching your training"""
        try:
            # Convert to DataFrame
            df = pd.DataFrame([data])
            
            # Apply label encoders for categorical columns
            if self.categorical_mappings:
                for col, encoder in self.categorical_mappings.items():
                    if col in df.columns:
                        try:
                            # Transform using the fitted encoder
                            df[col] = encoder.transform(df[col].astype(str))
                        except:
                            # If value not seen during training, use 0
                            df[col] = 0
            
            # Ensure all features are present
            if self.feature_names:
                full_df = pd.DataFrame(0, index=df.index, columns=self.feature_names)
                for col in df.columns:
                    if col in full_df.columns:
                        full_df[col] = df[col].values
                df = full_df
            
            # Convert to numeric
            df = df.astype(float)
            
            # Handle missing values
            if self.imputer:
                df = pd.DataFrame(
                    self.imputer.transform(df),
                    columns=df.columns,
                    index=df.index
                )
            
            # Scale features
            if self.scaler:
                df = pd.DataFrame(
                    self.scaler.transform(df),
                    columns=df.columns,
                    index=df.index
                )
            
            return df
            
        except Exception as e:
            logger.error(f"Preprocessing error: {str(e)}")
            raise
    
    def predict(self, student_data):
        """Make prediction for a single student"""
        try:
            if self.model is None:
                return self.get_error_response("Model not loaded")
            
            # Preprocess input
            processed_data = self.preprocess_input(student_data)
            
            # Make prediction
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
                'model_used': 'Logistic Regression (Balanced)',
                'recall_rate': '76.86%',
                'timestamp': pd.Timestamp.now().isoformat()
            }
                
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return self.get_error_response(str(e))
    
    def get_error_response(self, error_msg):
        """Return error response"""
        return {
            'dropout_probability': 0,
            'risk_level': 'Error',
            'prediction': 'Unable to predict',
            'error': error_msg,
            'timestamp': pd.Timestamp.now().isoformat()
        }
    
    def get_risk_level(self, probability):
        """Determine risk level based on dropout probability"""
        if probability >= 0.7:
            return 'Critical Risk - Immediate Intervention Needed'
        elif probability >= 0.5:
            return 'High Risk - Intensive Support Required'
        elif probability >= self.threshold:
            return 'Moderate Risk - Monitor Closely'
        else:
            return 'Low Risk - Regular Monitoring'
    
    def generate_recommendations(self, data, probability):
        """Generate personalized recommendations"""
        recommendations = []
        
        # Based on probability
        if probability >= 0.7:
            recommendations.append("🚨 CRITICAL: Schedule emergency academic counseling TODAY")
            recommendations.append("📞 Contact academic advisor and student support services")
            recommendations.append("📚 Enroll in intensive tutoring and remediation programs")
        elif probability >= 0.5:
            recommendations.append("⚠️ Schedule meeting with academic advisor within a week")
            recommendations.append("📖 Join mandatory study groups and tutoring sessions")
            recommendations.append("📊 Create academic improvement plan")
        elif probability >= self.threshold:
            recommendations.append("📅 Regular check-ins with academic advisor (bi-weekly)")
            recommendations.append("📚 Consider joining study groups")
            recommendations.append("🎯 Set specific academic goals")
        
        # GPA based recommendations
        gpa = float(data.get('GPA', 0))
        if gpa < 2.0:
            recommendations.append(f"🔴 Low GPA ({gpa:.2f}) - Required academic counseling")
        elif gpa < 2.5:
            recommendations.append(f"🟡 GPA improvement needed ({gpa:.2f})")
        
        # Attendance based
        attendance = float(data.get('Attendance_Rate', 100))
        if attendance < 75:
            recommendations.append(f"📅 Improve attendance ({attendance}%) - Set daily reminders")
        
        # Study hours
        study_hours = float(data.get('Study_Hours_per_Day', 0))
        if study_hours < 3:
            recommendations.append(f"📚 Increase study time to 3-4 hours per day")
        
        return list(dict.fromkeys(recommendations))[:5]
    
    def get_key_factors(self, data, probability):
        """Identify key contributing factors"""
        factors = []
        
        gpa = float(data.get('GPA', 4.0))
        if gpa < 2.0:
            factors.append(f"Low GPA ({gpa:.2f}) - Major risk factor")
        
        attendance = float(data.get('Attendance_Rate', 100))
        if attendance < 75:
            factors.append(f"Poor attendance ({attendance}%)")
        
        study_hours = float(data.get('Study_Hours_per_Day', 0))
        if study_hours < 3:
            factors.append(f"Insufficient study time ({study_hours} hrs/day)")
        
        failures = float(data.get('Assignment_Delay_Days', 0))
        if failures > 10:
            factors.append(f"Assignment delays ({failures} days)")
        
        return factors[:3]

# Create singleton instance
predictor = DropoutPredictor()