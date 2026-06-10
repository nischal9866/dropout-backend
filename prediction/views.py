from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
import logging
from .ml_predictor import predictor
from .serializers import PredictionInputSerializer, BatchPredictionSerializer

logger = logging.getLogger(__name__)

class PredictDropoutView(APIView):
    """API endpoint for dropout prediction"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Validate input
            serializer = PredictionInputSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            student_data = serializer.validated_data
            
            # Make prediction
            prediction_result = predictor.predict(student_data)
            
            return Response({
                'success': True,
                'data': prediction_result
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Prediction failed. Please check input data.',
                'details': str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BatchPredictDropoutView(APIView):
    """Batch prediction endpoint"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = BatchPredictionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            students_data = serializer.validated_data['students']
            results = []
            
            for student in students_data:
                result = predictor.predict(student)
                results.append(result)
            
            return Response({
                'success': True,
                'data': results,
                'total': len(results)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Batch prediction error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Batch prediction failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)