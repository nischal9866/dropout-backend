import os
import sys
import django
import traceback

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from prediction.ml_predictor import predictor
import pandas as pd

def test_dalex_trace():
    print("Running Dalex trace test...")
    student_data = {
        'Age': 20.5,
        'Gender': 'Male',
        'Department': 'CS',
        'Semester': 'Year 2',
        'GPA': 2.2,
        'Semester_GPA': 2.0,
        'CGPA': 2.1,
        'Study_Hours_per_Day': 3.5,
        'Attendance_Rate': 65.0,
        'Assignment_Delay_Days': 8.0,
        'Family_Income': 25000,
        'Scholarship': 'No',
        'Part_Time_Job': 'Yes',
        'Internet_Access': 'Yes',
        'Travel_Time_Minutes': 45,
        'Stress_Index': 7.5,
        'Parental_Education': 'High School'
    }
    
    try:
        student_encoded_df = pd.DataFrame([student_data])
        student_encoded_df = student_encoded_df[predictor.feature_names]
        if predictor.categorical_mappings:
            for col, encoder in predictor.categorical_mappings.items():
                if col in student_encoded_df.columns:
                    student_encoded_df[col] = encoder.transform(student_encoded_df[col].astype(str))
                    
        print("Input encoded shape:", student_encoded_df.shape)
        print("Dalex explainer:", predictor.dalex_explainer)
        
        print("Computing predict_parts break_down...")
        bd = predictor.dalex_explainer.predict_parts(student_encoded_df, type='break_down')
        print("Breakdown successfully calculated!")
        print("Plotting breakdown...")
        fig_bd = bd.plot(show=False)
        print("Breakdown plot successfully generated!")
        
    except Exception as e:
        print("ERROR OCCURRED:")
        print(str(e))
        traceback.print_exc()

if __name__ == "__main__":
    test_dalex_trace()
