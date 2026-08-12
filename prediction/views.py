from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
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
            student_db_id = student_data.pop('student_db_id', None)
            
            # Make prediction
            prediction_result = predictor.predict(student_data)
            
            # If student exists in system, save prediction and update student profile
            if student_db_id:
                from students.models import Student, DropoutPrediction
                from django.utils import timezone
                try:
                    student = Student.objects.get(id=student_db_id)
                    
                    # Update student model risk fields
                    student.last_prediction_probability = prediction_result['dropout_probability']
                    student.last_prediction_date = timezone.now()
                    student.risk_level = prediction_result['risk_level']
                    student.save()
                    
                    # Create prediction history record
                    DropoutPrediction.objects.create(
                        student=student,
                        predicted_by=request.user,
                        dropout_probability=prediction_result['dropout_probability'],
                        risk_level=prediction_result['risk_level'],
                        prediction_result=(prediction_result['prediction'] == 'At Risk of Dropout'),
                        threshold_used=prediction_result['threshold_used'] / 100.0,
                        confidence_score=prediction_result['confidence_score'],
                        input_data=student_data,
                        key_factors=prediction_result.get('key_factors', []),
                        recommendations=prediction_result.get('recommendations', []),
                        shap_explanation=prediction_result.get('shap_explanation', {})
                    )
                except Student.DoesNotExist:
                    logger.error(f"Student with id {student_db_id} not found to save prediction.")
            
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

class GlobalExplainView(APIView):
    """API endpoint to get global model explanations (Shapash and Dalex)"""
    permission_classes = [IsAuthenticated]
    
    @method_decorator(cache_page(60 * 60 * 24))  # Cache for 24 hours
    def get(self, request):
        try:
            plots = predictor.get_global_explanations()
            return Response({
                'success': True,
                'data': plots
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Global explain error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Failed to generate global explanations',
                'details': str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)