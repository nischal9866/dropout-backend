import os
import sys
import django
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Setup Django
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from dashboard.views import DashboardStatsView, AnalyticsView
from django.contrib.auth import get_user_model

User = get_user_model()

def test_dashboard_endpoints():
    print("="*60)
    print("Testing Django Dashboard and Analytics Endpoints")
    print("="*60)
    
    # Get or create a superuser for authentication
    try:
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            # Create a mock user
            user = User.objects.create_superuser('testadmin', 'admin@test.com', 'password123')
            print("[INFO] Created temporary superuser for testing.")
    except Exception as e:
        print(f"[ERROR] Failed to get/create superuser: {str(e)}")
        return
        
    factory = APIRequestFactory()
    
    # 1. Test Dashboard Stats View
    print("\n[INFO] Testing DashboardStatsView...")
    request = factory.get('/api/dashboard/stats/')
    force_authenticate(request, user=user)
    view = DashboardStatsView.as_view()
    
    try:
        response = view(request)
        print(f"[SUCCESS] Status Code: {response.status_code}")
        print("Response JSON:")
        print(json.dumps(response.data, indent=2))
    except Exception as e:
        print(f"[ERROR] DashboardStatsView crashed: {str(e)}")
        
    # 2. Test Analytics View
    print("\n[INFO] Testing AnalyticsView...")
    request = factory.get('/api/analytics/')
    force_authenticate(request, user=user)
    view = AnalyticsView.as_view()
    
    try:
        response = view(request)
        print(f"[SUCCESS] Status Code: {response.status_code}")
        print("Response JSON Summary:")
        # Summarize rather than printing the whole thing if it's very large
        data = response.data
        summary = {
            'total_students': data.get('total_students'),
            'at_risk': data.get('at_risk'),
            'risk_percentage': data.get('risk_percentage'),
            'average_gpa': data.get('average_gpa'),
            'average_attendance': data.get('average_attendance'),
            'department_risks_count': len(data.get('department_risks', [])),
            'trends_count': len(data.get('trends', [])),
            'global_shap_importance_count': len(data.get('global_shap_importance', [])),
            'top_3_global_shap': data.get('global_shap_importance', [])[:3]
        }
        print(json.dumps(summary, indent=2))
    except Exception as e:
        print(f"[ERROR] AnalyticsView crashed: {str(e)}")
        
    print("\n" + "="*60)
    print("Verification Completed!")
    print("="*60)

if __name__ == "__main__":
    test_dashboard_endpoints()
