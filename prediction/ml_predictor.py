import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from django.conf import settings
import json
import logging
import warnings
warnings.filterwarnings('ignore')  # Add this to suppress warnings

# Monkeypatch pandas StringArray to allow automatic conversion of floats/ints to strings,
# which is required by Dalex breakdown plot in pandas 2.x
from pandas.core.arrays.string_ import StringArray

original_maybe_convert_setitem_value = StringArray._maybe_convert_setitem_value

def patched_maybe_convert_setitem_value(self, value):
    if isinstance(value, (int, float, np.integer, np.floating)):
        return str(value)
    if isinstance(value, np.ndarray) and np.issubdtype(value.dtype, np.number):
        return value.astype(str)
    try:
        return original_maybe_convert_setitem_value(self, value)
    except TypeError:
        if hasattr(value, '__iter__') and not isinstance(value, str):
            return [str(v) if isinstance(v, (int, float, np.integer, np.floating)) else v for v in value]
        raise

StringArray._maybe_convert_setitem_value = patched_maybe_convert_setitem_value

import dalex as dx
from shapash import SmartExplainer
import plotly.io as pio

logger = logging.getLogger(__name__)

class ShapashInverseTransformer:
    def __init__(self, scaler, imputer, categorical_mappings, feature_names):
        self.scaler = scaler
        self.imputer = imputer
        self.categorical_mappings = categorical_mappings
        self.feature_names = feature_names
        
    def inverse_transform(self, X):
        if self.scaler:
            X_inv = self.scaler.inverse_transform(X)
        else:
            X_inv = X
            
        df = pd.DataFrame(X_inv, columns=self.feature_names)
        
        if self.categorical_mappings:
            for col, encoder in self.categorical_mappings.items():
                if col in df.columns:
                    try:
                        encoded_vals = np.clip(np.round(df[col].values).astype(int), 0, len(encoder.classes_) - 1)
                        df[col] = encoder.inverse_transform(encoded_vals)
                    except Exception:
                        pass
        return df


class DropoutPredictor:
    """Service class for student dropout prediction using Logistic Regression"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.imputer = None
        self.feature_names = None
        self.categorical_mappings = None
        self.model_info = None
        self.threshold = 0.40
        self.load_models()
    
    def load_models(self):
        """Load all saved ML models and artifacts"""
        try:
            model_dir = Path(__file__).parent / 'ml_models'
            
            print(f"[INFO] Loading models from: {model_dir}")
            
            # Load model
            model_path = model_dir / 'dropout_model.pkl'
            if model_path.exists():
                self.model = joblib.load(model_path)
                print(f"[SUCCESS] Model loaded: {type(self.model).__name__}")
            else:
                print(f"[ERROR] Model not found at {model_path}")
                return
            
            # Load scaler
            scaler_path = model_dir / 'scaler.pkl'
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
                print("[SUCCESS] Scaler loaded")
            
            # Load imputer
            imputer_path = model_dir / 'imputer.pkl'
            if imputer_path.exists():
                self.imputer = joblib.load(imputer_path)
                print("[SUCCESS] Imputer loaded")
            
            # Load feature names
            features_path = model_dir / 'feature_names.pkl'
            if features_path.exists():
                self.feature_names = joblib.load(features_path)
                print(f"[SUCCESS] Loaded {len(self.feature_names)} features")
            
            # Load label encoders
            encoders_path = model_dir / 'label_encoders.pkl'
            if encoders_path.exists():
                self.categorical_mappings = joblib.load(encoders_path)
                print(f"[SUCCESS] Loaded {len(self.categorical_mappings)} categorical encoders")
            
            # Load model info
            info_path = model_dir / 'model_info.json'
            if info_path.exists():
                with open(info_path, 'r') as f:
                    self.model_info = json.load(f)
                self.threshold = self.model_info.get('threshold', 0.40)
                print(f"[SUCCESS] Model info loaded - Threshold: {self.threshold}")
                print(f"   Model: {self.model_info.get('model_name')}")
                print(f"   Strategy: {self.model_info.get('strategy')}")
                perf = self.model_info.get('performance', {})
                print(f"   Recall: {perf.get('recall', 'N/A')}")
            
            # Load background data and initialize explainers (SHAP, Dalex, Shapash)
            background_path = model_dir / 'background_data.pkl'
            if background_path.exists():
                self.background_data = joblib.load(background_path)
                
                # 1. SHAP Explainer
                try:
                    import shap
                    # LinearExplainer expects the background data matrix (can be a subset or full)
                    # Let's pass a small subset (e.g. 200 samples) or full for linear model
                    bg_matrix = self.background_data['X_train_scaled']
                    if isinstance(bg_matrix, pd.DataFrame):
                        bg_matrix = bg_matrix.values
                    self.explainer = shap.LinearExplainer(self.model, bg_matrix[:200])
                    print("[SUCCESS] SHAP LinearExplainer initialized successfully!")
                except Exception as shap_init_err:
                    self.explainer = None
                    print(f"[WARNING] SHAP initialization failed: {str(shap_init_err)}")
                
                # 2. Dalex Explainer
                try:
                    def dx_predict_proba(model, data):
                        if isinstance(data, np.ndarray):
                            data = pd.DataFrame(data, columns=self.feature_names)
                        df = data.copy()
                        if self.categorical_mappings:
                            for col, encoder in self.categorical_mappings.items():
                                if col in df.columns:
                                    if df[col].dtype == object or (len(df[col]) > 0 and isinstance(df[col].iloc[0], str)):
                                        try:
                                            df[col] = encoder.transform(df[col].astype(str))
                                        except Exception:
                                            df[col] = 0
                        df = df[self.feature_names]
                        if self.imputer:
                            df_imputed = self.imputer.transform(df)
                        else:
                            df_imputed = df.values
                        if self.scaler:
                            df_scaled = self.scaler.transform(df_imputed)
                        else:
                            df_scaled = df_imputed
                        return self.model.predict_proba(df_scaled)[:, 1]

                    self.dalex_explainer = dx.Explainer(
                        self.model,
                        self.background_data['X_train_raw'],
                        self.background_data['y_train'],
                        predict_function=dx_predict_proba,
                        label="Student Dropout Predictor",
                        verbose=False
                    )
                    print("[SUCCESS] Dalex Explainer initialized successfully!")
                except Exception as dalex_init_err:
                    self.dalex_explainer = None
                    print(f"[WARNING] Dalex initialization failed: {str(dalex_init_err)}")
                    
                # 3. Shapash SmartExplainer
                try:
                    features_dict = {
                        'Age': 'Age',
                        'Gender': 'Gender',
                        'Family_Income': 'Family Income',
                        'Internet_Access': 'Internet Access',
                        'Study_Hours_per_Day': 'Daily Study Hours',
                        'Attendance_Rate': 'Attendance Rate',
                        'Assignment_Delay_Days': 'Assignment Delay Days',
                        'Travel_Time_Minutes': 'Travel Time',
                        'Part_Time_Job': 'Part-Time Job',
                        'Scholarship': 'Scholarship',
                        'Stress_Index': 'Stress Index',
                        'GPA': 'Current GPA',
                        'Semester_GPA': 'Semester GPA',
                        'CGPA': 'Cumulative GPA',
                        'Semester': 'Semester',
                        'Department': 'Department',
                        'Parental_Education': 'Parental Education'
                    }
                    self.shapash_xpl = SmartExplainer(model=self.model, features_dict=features_dict)
                    
                    X_scaled_df = self.background_data['X_train_scaled'].head(200)
                    y_pred_series = pd.Series(self.model.predict(X_scaled_df), index=X_scaled_df.index)
                    
                    self.shapash_xpl.compile(
                        x=X_scaled_df,
                        y_pred=y_pred_series
                    )
                    print("[SUCCESS] Shapash SmartExplainer initialized successfully!")
                except Exception as shapash_init_err:
                    self.shapash_xpl = None
                    print(f"[WARNING] Shapash initialization failed: {str(shapash_init_err)}")
            else:
                self.background_data = None
                self.explainer = None
                self.dalex_explainer = None
                self.shapash_xpl = None
                print("[WARNING] Background data not found. Explanations will be disabled.")
            
            print("\n[INFO] Dropout Prediction Ready with Dalex & Shapash!")
            
        except Exception as e:
            print(f"[ERROR] Error loading models: {str(e)}")

    
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
            
            # Scale features - Convert to numpy array to avoid feature name warning
            if self.scaler:
                # Use numpy array instead of DataFrame to avoid feature name warning
                df_scaled = self.scaler.transform(df)
                # Don't convert back to DataFrame, keep as numpy array
                return df_scaled
            
            return df.values  # Return as numpy array
            
        except Exception as e:
            logger.error(f"Preprocessing error: {str(e)}")
            raise
    
    def predict(self, student_data):
        """Make prediction for a single student"""
        try:
            if self.model is None:
                return self.get_error_response("Model not loaded")
            
            # Preprocess input (returns numpy array)
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
            
            # Calculate SHAP values for Explainable AI
            shap_explanation = None
            shap_features = None
            if hasattr(self, 'explainer') and self.explainer is not None:
                try:
                    explanation = self.explainer(processed_data)
                    raw_shap_values = explanation.values[0]
                    
                    if len(raw_shap_values.shape) > 1 and raw_shap_values.shape[-1] == 2:
                        raw_shap_values = raw_shap_values[:, 1]
                        
                    base_value = explanation.base_values
                    if isinstance(base_value, np.ndarray) or hasattr(base_value, '__len__'):
                        base_value = base_value[0]
                        if hasattr(base_value, '__len__') and len(base_value) == 2:
                            base_value = base_value[1]
                            
                    feature_contribs = []
                    for idx, feat_name in enumerate(self.feature_names):
                        actual_val = student_data.get(feat_name, 0.0)
                        if isinstance(actual_val, (np.integer, np.floating)):
                            actual_val = actual_val.item()
                        elif not isinstance(actual_val, (int, float)):
                            try:
                                actual_val = float(actual_val)
                            except:
                                pass
                                
                        shap_val = float(raw_shap_values[idx])
                        feature_contribs.append({
                            'name': feat_name,
                            'value': actual_val,
                            'shap_value': round(shap_val, 4)
                        })
                        
                    # Sort by absolute SHAP value desc
                    feature_contribs = sorted(feature_contribs, key=lambda x: abs(x['shap_value']), reverse=True)
                    prediction_val = float(base_value + np.sum(raw_shap_values))
                    
                    shap_explanation = {
                        'base_value': round(float(base_value), 4),
                        'prediction_value': round(prediction_val, 4),
                        'features': feature_contribs
                    }
                    shap_features = feature_contribs
                except Exception as shap_err:
                    logger.error(f"Error computing SHAP values: {str(shap_err)}")
            
            # Calculate Dalex and Shapash explanation plots
            dalex_breakdown_html = None
            dalex_whatif_html = None
            shapash_local_html = None
            
            if hasattr(self, 'dalex_explainer') and self.dalex_explainer is not None:
                try:
                    student_encoded_df = pd.DataFrame([student_data])
                    student_encoded_df = student_encoded_df[self.feature_names]
                    if self.categorical_mappings:
                        for col, encoder in self.categorical_mappings.items():
                            if col in student_encoded_df.columns:
                                try:
                                    student_encoded_df[col] = encoder.transform(student_encoded_df[col].astype(str))
                                except Exception:
                                    student_encoded_df[col] = 0
                    
                    bd = self.dalex_explainer.predict_parts(student_encoded_df, type='break_down')
                    fig_bd = bd.plot(show=False)
                    fig_bd.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#374151', size=11),
                        title=dict(text='Prediction Breakdown (Dalex XAI)', font=dict(size=14, color='#111827')),
                        margin=dict(l=40, r=40, t=50, b=40)
                    )
                    dalex_breakdown_html = pio.to_html(fig_bd, include_plotlyjs='cdn', full_html=False)
                except Exception as dex_err:
                    logger.error(f"Error computing Dalex breakdown: {str(dex_err)}")
                    
                try:
                    student_encoded_df = pd.DataFrame([student_data])
                    student_encoded_df = student_encoded_df[self.feature_names]
                    if self.categorical_mappings:
                        for col, encoder in self.categorical_mappings.items():
                            if col in student_encoded_df.columns:
                                try:
                                    student_encoded_df[col] = encoder.transform(student_encoded_df[col].astype(str))
                                except Exception:
                                    student_encoded_df[col] = 0
                                    
                    cp = self.dalex_explainer.predict_profile(student_encoded_df, variables=['GPA', 'Attendance_Rate', 'Study_Hours_per_Day'])
                    fig_cp = cp.plot(show=False)
                    fig_cp.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#374151', size=11),
                        title=dict(text='What-If Analysis (Dalex CP Profile)', font=dict(size=14, color='#111827')),
                        margin=dict(l=40, r=40, t=50, b=40)
                    )
                    dalex_whatif_html = pio.to_html(fig_cp, include_plotlyjs='cdn', full_html=False)
                except Exception as dex_cp_err:
                    logger.error(f"Error computing Dalex CP: {str(dex_cp_err)}")
                    
            if hasattr(self, 'shapash_xpl') and self.shapash_xpl is not None:
                try:
                    bg_subset = self.background_data['X_train_scaled'].head(100)
                    student_scaled_df = pd.DataFrame(processed_data, columns=self.feature_names)
                    student_scaled_df.index = ['new_student']
                    
                    combined_x = pd.concat([bg_subset, student_scaled_df])
                    combined_y_pred = pd.Series(self.model.predict(combined_x), index=combined_x.index)
                    
                    temp_xpl = SmartExplainer(model=self.model, features_dict=self.shapash_xpl.features_dict)
                    temp_xpl.compile(x=combined_x, y_pred=combined_y_pred)
                    
                    fig_local = temp_xpl.plot.local_plot(index='new_student')
                    fig_local.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#374151', size=11),
                        title=dict(text='Local Feature Contributions (Shapash XAI)', font=dict(size=14, color='#111827')),
                        margin=dict(l=40, r=40, t=50, b=40)
                    )
                    shapash_local_html = pio.to_html(fig_local, include_plotlyjs='cdn', full_html=False)
                except Exception as shp_err:
                    logger.error(f"Error computing Shapash local: {str(shp_err)}")
            
            # Generate recommendations driven directly by SHAP
            recommendations = self.generate_recommendations(student_data, dropout_prob, shap_features)
            
            # Get key factors driven directly by SHAP
            key_factors = self.get_key_factors(student_data, dropout_prob, shap_features)
            
            return {
                'dropout_probability': round(dropout_prob * 100, 2),
                'risk_level': risk_level,
                'prediction': 'At Risk of Dropout' if final_prediction == 1 else 'On Track',
                'confidence_score': round(max(probability) * 100, 2),
                'recommendations': recommendations,
                'key_factors': key_factors,
                'shap_explanation': shap_explanation,
                'dalex_breakdown_html': dalex_breakdown_html,
                'dalex_whatif_html': dalex_whatif_html,
                'shapash_local_html': shapash_local_html,
                'threshold_used': round(self.threshold * 100, 2),
                'model_used': self.model_info.get('model_name', 'Logistic Regression') if self.model_info else 'Logistic Regression (Balanced)',
                'recall_rate': f"{self.model_info.get('performance', {}).get('recall', 0.7686)*100:.2f}%" if self.model_info else '76.86%',
                'timestamp': pd.Timestamp.now().isoformat()
            }
                
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return self.get_error_response(str(e))
            
    def get_global_explanations(self):
        """Generate global explainability plots using Shapash and Dalex"""
        global_plots = {}
        
        # 1. Shapash Global Feature Importance
        if hasattr(self, 'shapash_xpl') and self.shapash_xpl is not None:
            try:
                fig_imp = self.shapash_xpl.plot.features_importance()
                fig_imp.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#374151', size=11),
                    title=dict(text='Global Feature Importance (Shapash XAI)', font=dict(size=14, color='#111827')),
                    margin=dict(l=40, r=40, t=50, b=40)
                )
                global_plots['shapash_importance'] = pio.to_html(fig_imp, include_plotlyjs='cdn', full_html=False)
            except Exception as e:
                logger.error(f"Error generating Shapash global importance: {str(e)}")
                
        # 2. Dalex Variable Importance
        if hasattr(self, 'dalex_explainer') and self.dalex_explainer is not None:
            try:
                vi = self.dalex_explainer.model_parts()
                fig_vi = vi.plot(show=False)
                fig_vi.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#374151', size=11),
                    title=dict(text='Model-Agnostic Variable Importance (Dalex XAI)', font=dict(size=14, color='#111827')),
                    margin=dict(l=40, r=40, t=50, b=40)
                )
                global_plots['dalex_importance'] = pio.to_html(fig_vi, include_plotlyjs='cdn', full_html=False)
            except Exception as e:
                logger.error(f"Error generating Dalex global importance: {str(e)}")
                
            # 3. Dalex Partial Dependence Plot (PDP) for GPA and Attendance
            try:
                pdp = self.dalex_explainer.model_profile(variables=['GPA', 'Attendance_Rate'])
                fig_pdp = pdp.plot(show=False)
                fig_pdp.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#374151', size=11),
                    title=dict(text='Partial Dependence Profiles: GPA & Attendance Rate (Dalex XAI)', font=dict(size=14, color='#111827')),
                    margin=dict(l=40, r=40, t=50, b=40)
                )
                global_plots['dalex_pdp'] = pio.to_html(fig_pdp, include_plotlyjs='cdn', full_html=False)
            except Exception as e:
                logger.error(f"Error generating Dalex global PDP: {str(e)}")
                
        return global_plots
    
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
    
    def generate_recommendations(self, data, probability, shap_features=None):
        """Generate personalized recommendations driven directly by SHAP feature impacts"""
        recommendations = []
        
        # 1. Base probability warning
        if probability >= 0.7:
            recommendations.append("🚨 CRITICAL: Schedule emergency academic counseling TODAY")
        elif probability >= 0.5:
            recommendations.append("⚠️ Schedule meeting with academic advisor within a week")
        elif probability >= self.threshold:
            recommendations.append("📅 Schedule a check-in with your academic advisor (bi-weekly)")
            
        # 2. SHAP-driven recommendations
        if shap_features:
            # Filter for features that are driving up the risk (SHAP > 0)
            positive_factors = [f for f in shap_features if f['shap_value'] > 0]
            # Sort by contribution descending
            positive_factors = sorted(positive_factors, key=lambda x: x['shap_value'], reverse=True)
            
            # Map top 3 positive contributors to recommendations
            for factor in positive_factors[:3]:
                feat_name = factor['name']
                feat_val = factor['value']
                shap_val = factor['shap_value']
                
                if feat_name in ['GPA', 'Semester_GPA', 'CGPA']:
                    recommendations.append(
                        f"🔴 Academic Performance ({feat_name}: {feat_val}) is driving up your risk (+{shap_val:.2f}). Priority: Join intensive tutoring and set up a study improvement plan."
                    )
                elif feat_name == 'Attendance_Rate':
                    recommendations.append(
                        f"📅 Poor Attendance ({feat_val}%) is a major risk factor (+{shap_val:.2f}). Priority: Improve class attendance and set daily attendance reminders."
                    )
                elif feat_name == 'Assignment_Delay_Days':
                    recommendations.append(
                        f"📝 Assignment delays ({feat_val} days) are impacting your progress (+{shap_val:.2f}). Priority: Attend time-management and assignment planning workshops."
                    )
                elif feat_name == 'Stress_Index':
                    recommendations.append(
                        f"🧠 High Stress levels (Index: {feat_val}/10) are contributing to academic pressure (+{shap_val:.2f}). Priority: Schedule a session with student wellness or counseling services."
                    )
                elif feat_name == 'Study_Hours_per_Day':
                    recommendations.append(
                        f"📚 Insufficient Study Time ({feat_val} hrs/day) is increasing risk (+{shap_val:.2f}). Priority: Increase daily study hours to at least 3-4 hours."
                    )
                elif feat_name == 'Part_Time_Job' and feat_val == 'Yes':
                    recommendations.append(
                        f"💼 Part-time job commitments are affecting your academic balance (+{shap_val:.2f}). Priority: Discuss work-study balancing strategies with an advisor."
                    )
                elif feat_name == 'Scholarship' and feat_val == 'No':
                    recommendations.append(
                        f"💵 Lack of Scholarship aid is adding financial pressure (+{shap_val:.2f}). Priority: Consult the financial aid office to explore scholarship/grant options."
                    )
                elif feat_name == 'Family_Income':
                    recommendations.append(
                        f"💰 Financial constraints (Income: ${feat_val:,}) are contributing to academic risk (+{shap_val:.2f}). Priority: Review student support services and emergency grants."
                    )
                elif feat_name == 'Travel_Time_Minutes':
                    recommendations.append(
                        f"🚗 Commute time ({feat_val} minutes) is reducing study availability (+{shap_val:.2f}). Priority: Study during transit or explore nearby student housing options."
                    )
                elif feat_name == 'Internet_Access' and feat_val == 'No':
                    recommendations.append(
                        f"🌐 Lack of Internet Access is impeding digital learning (+{shap_val:.2f}). Priority: Utilize university library computers and check for local internet packages."
                    )
                    
        # 3. Fallback recommendations if no positive SHAP factors or empty list
        if len(recommendations) <= 1:
            gpa = float(data.get('GPA', 4.0))
            if gpa < 2.5:
                recommendations.append("📚 Set up academic coaching sessions for GPA improvement.")
            else:
                recommendations.append("🎯 Maintain your current study routine and check in with your mentor regularly.")
                
        # Limit to 5 unique recommendations
        return list(dict.fromkeys(recommendations))[:5]
    
    def get_key_factors(self, data, probability, shap_features=None):
        """Identify key contributing factors driven directly by SHAP"""
        factors = []
        if shap_features:
            # Filter for features driving up risk (SHAP > 0)
            positive_factors = [f for f in shap_features if f['shap_value'] > 0]
            # Sort by contribution descending
            positive_factors = sorted(positive_factors, key=lambda x: x['shap_value'], reverse=True)
            
            for factor in positive_factors[:3]:
                feat_name = factor['name'].replace('_', ' ')
                feat_val = factor['value']
                shap_val = factor['shap_value']
                factors.append(f"{feat_name} ({feat_val}) is driving up risk (+{shap_val:.2f})")
                
        if not factors:
            # Fallback
            gpa = float(data.get('GPA', 4.0))
            if gpa < 2.5:
                factors.append(f"GPA ({gpa:.2f}) is a contributing risk factor")
            else:
                factors.append("No significant individual risk factors identified")
                
        return factors[:3]

# Create singleton instance
predictor = DropoutPredictor()