import os
import sys
import django
import traceback

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from prediction.ml_predictor import DropoutPredictor

def test_trace():
    print("Testing loader trace...")
    try:
        predictor = DropoutPredictor()
    except Exception as e:
        print("OUTER EXCEPTION:")
        traceback.print_exc()

if __name__ == "__main__":
    test_trace()
