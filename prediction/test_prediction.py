import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from ml_predictor import predictor

def test_prediction():
    """Test the prediction with sample data"""
    
    # Sample student data (modify based on your dataset)
    sample_student = {
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
    
    print("="*60)
    print("Testing Dropout Prediction")
    print("="*60)
    
    print("\n📊 Student Data:")
    for key, value in sample_student.items():
        print(f"   {key}: {value}")
    
    # Make prediction
    result = predictor.predict(sample_student)
    
    print("\n🎯 Prediction Result:")
    print(f"   Dropout Probability: {result.get('dropout_probability', 'N/A')}%")
    print(f"   Risk Level: {result.get('risk_level', 'N/A')}")
    print(f"   Prediction: {result.get('prediction', 'N/A')}")
    print(f"   Confidence: {result.get('confidence_score', 'N/A')}%")
    
    if result.get('key_factors'):
        print("\n⚠️ Key Risk Factors:")
        for factor in result['key_factors']:
            print(f"   • {factor}")
    
    if result.get('recommendations'):
        print("\n💡 Recommendations:")
        for rec in result['recommendations']:
            print(f"   • {rec}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_prediction()