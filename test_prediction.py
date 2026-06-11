import os
import sys
import django

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Setup Django
django.setup()

from prediction.ml_predictor import predictor

def test_prediction():
    print("="*60)
    print("Testing Dropout Prediction System")
    print("="*60)
    
    # Check if model is loaded
    if predictor.model is None:
        print("\n❌ Model not loaded!")
        print("Please make sure model files are in prediction/ml_models/")
        return
    
    print("\n✅ Model loaded successfully!")
    print(f"   Model type: {type(predictor.model).__name__}")
    print(f"   Features: {len(predictor.feature_names) if predictor.feature_names else 0}")
    
    # Test student data (using your exact feature names)
    test_student = {
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
    
    print("\n📊 Test Student Data:")
    for key, value in test_student.items():
        print(f"   {key}: {value}")
    
    # Make prediction
    print("\n🔄 Making prediction...")
    result = predictor.predict(test_student)
    
    print("\n" + "="*60)
    print("🎯 PREDICTION RESULT")
    print("="*60)
    print(f"   Dropout Probability: {result.get('dropout_probability', 'N/A')}%")
    print(f"   Risk Level: {result.get('risk_level', 'N/A')}")
    print(f"   Prediction: {result.get('prediction', 'N/A')}")
    print(f"   Confidence: {result.get('confidence_score', 'N/A')}%")
    print(f"   Model Used: {result.get('model_used', 'N/A')}")
    
    if result.get('key_factors'):
        print("\n⚠️ Key Risk Factors:")
        for factor in result['key_factors']:
            print(f"   • {factor}")
    
    if result.get('recommendations'):
        print("\n💡 Recommendations:")
        for rec in result['recommendations']:
            print(f"   • {rec}")
    
    print("\n" + "="*60)
    
    # Check if files exist
    print("\n📁 Checking model files:")
    import os
    from pathlib import Path
    
    model_dir = Path(__file__).parent / 'prediction' / 'ml_models'
    if model_dir.exists():
        files = list(model_dir.glob('*.pkl')) + list(model_dir.glob('*.json'))
        for f in files:
            size = f.stat().st_size
            print(f"   ✅ {f.name} ({size:,} bytes)")
    else:
        print(f"   ❌ Model directory not found: {model_dir}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_prediction()