from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Student, DropoutPrediction, TeacherProfile
from .serializers import (
    StudentCreateSerializer, 
    StudentListSerializer,
    StudentDetailSerializer,
    DropoutPredictionSerializer
)
import random
import string

User = get_user_model()

# ============================================
# STUDENT LIST VIEW - GET ALL STUDENTS
# ============================================

class StudentListView(APIView):
    """Get all students list"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get all students
            students = Student.objects.all().order_by('-created_at')
            
            # Check if user is admin or teacher - they can see all students
            if request.user.user_type in ['admin', 'teacher'] or request.user.is_superuser:
                serializer = StudentListSerializer(students, many=True)
                return Response({
                    'success': True,
                    'data': serializer.data,
                    'count': students.count()
                }, status=status.HTTP_200_OK)
            
            # Students can only see their own profile
            if request.user.user_type == 'student':
                try:
                    student = Student.objects.get(user=request.user)
                    serializer = StudentListSerializer(student)
                    return Response({
                        'success': True,
                        'data': [serializer.data],
                        'count': 1
                    }, status=status.HTTP_200_OK)
                except Student.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'Student profile not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            return Response({
                'success': False,
                'error': 'Unauthorized access'
            }, status=status.HTTP_403_FORBIDDEN)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================
# STUDENT DETAIL VIEW
# ============================================

class StudentDetailView(APIView):
    """Get, update, delete a specific student"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            student = Student.objects.get(id=pk)
            
            # Check permissions
            if request.user.user_type == 'student':
                try:
                    own_student = Student.objects.get(user=request.user)
                    if own_student.id != student.id:
                        return Response({
                            'success': False,
                            'error': 'You can only view your own profile'
                        }, status=status.HTTP_403_FORBIDDEN)
                except Student.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'Student profile not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = StudentDetailSerializer(student)
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Student not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, pk):
        """Update student"""
        try:
            student = Student.objects.get(id=pk)
            
            # Only admin or teacher can update
            if request.user.user_type not in ['admin', 'teacher'] and not request.user.is_superuser:
                return Response({
                    'success': False,
                    'error': 'You do not have permission to update students'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = StudentDetailSerializer(student, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Student updated successfully',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Student not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, pk):
        """Delete student"""
        try:
            student = Student.objects.get(id=pk)
            
            # Only admin can delete
            if request.user.user_type != 'admin' and not request.user.is_superuser:
                return Response({
                    'success': False,
                    'error': 'Only admin can delete students'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Delete the user account too
            user = student.user
            student.delete()
            user.delete()
            
            return Response({
                'success': True,
                'message': 'Student deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Student not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================
# CREATE STUDENT VIEW
# ============================================

class CreateStudentView(APIView):
    """Create a new student with user account"""
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request):
        try:
            # Get data from request
            data = request.data
            
            # Generate student_id if not provided
            if not data.get('student_id'):
                data['student_id'] = f"STU{random.randint(10000, 99999)}"
            
            # Create user account
            user_data = {
                'username': data.get('username'),
                'email': data.get('email'),
                'password': data.get('password'),
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name'),
                'user_type': 'student',
                'phone_number': data.get('phone_number', ''),
            }
            
            # Validate required fields
            if not all([user_data['username'], user_data['email'], user_data['password'],
                       user_data['first_name'], user_data['last_name']]):
                return Response({
                    'success': False,
                    'error': 'All required fields must be filled'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if username already exists
            if User.objects.filter(username=user_data['username']).exists():
                return Response({
                    'success': False,
                    'error': 'Username already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if email already exists
            if User.objects.filter(email=user_data['email']).exists():
                return Response({
                    'success': False,
                    'error': 'Email already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create user
            user = User.objects.create_user(**user_data)
            
            # Create student profile
            student = Student.objects.create(
                user=user,
                student_id=data.get('student_id'),
                first_name=data.get('first_name'),
                last_name=data.get('last_name'),
                email=data.get('email'),
                phone_number=data.get('phone_number', ''),
                department=data.get('department', 'CS'),
                year_of_study=data.get('year_of_study', 'Year 1'),
                current_semester=1,
            )
            
            # Send welcome email (optional)
            try:
                send_mail(
                    subject='Welcome to EduTrack - Your Student Account',
                    message=f"""
                    Dear {user.get_full_name()},
                    
                    Your student account has been created successfully!
                    
                    Login Credentials:
                    Username: {user.username}
                    Password: {data.get('password')}
                    
                    Please login at: {settings.SITE_URL}/login
                    
                    Best regards,
                    EduTrack Team
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except:
                pass
            
            return Response({
                'success': True,
                'message': 'Student created successfully',
                'student': {
                    'id': student.id,
                    'student_id': student.student_id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'department': student.department,
                    'year_of_study': student.year_of_study,
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

# ============================================
# MY STUDENT PROFILE VIEW
# ============================================

class MyStudentProfileView(APIView):
    """Get current user's student profile"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            student = Student.objects.get(user=request.user)
            serializer = StudentDetailSerializer(student)
            return Response({
                'success': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Student profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================
# STUDENT PREDICTIONS VIEW
# ============================================

class StudentPredictionsView(APIView):
    """Get prediction history for a student"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, student_id):
        try:
            student = Student.objects.get(id=student_id)
            
            # Check permissions
            if request.user.user_type == 'student':
                try:
                    own_student = Student.objects.get(user=request.user)
                    if own_student.id != student.id:
                        return Response({
                            'success': False,
                            'error': 'You can only view your own predictions'
                        }, status=status.HTTP_403_FORBIDDEN)
                except Student.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': 'Student profile not found'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            predictions = DropoutPrediction.objects.filter(student=student).order_by('-predicted_at')
            
            if predictions.count() == 0:
                from prediction.ml_predictor import predictor
                from django.utils import timezone
                import logging
                logger = logging.getLogger(__name__)
                try:
                    # Construct features from student DB details
                    student_data = {
                        'Age': 20.0,
                        'Gender': student.gender or 'Male',
                        'Department': student.department or 'CS',
                        'Semester': student.year_of_study or 'Year 1',
                        'GPA': student.current_gpa or 0.0,
                        'Semester_GPA': student.semester_gpa or student.current_gpa or 0.0,
                        'CGPA': student.cgpa or 0.0,
                        'Study_Hours_per_Day': student.study_hours_per_day or 0.0,
                        'Attendance_Rate': student.attendance_percentage or 100.0,
                        'Assignment_Delay_Days': float(student.tuition_payment_delay_days) if student.tuition_payment_delay_days else 0.0,
                        'Family_Income': student.family_income or 25000.0,
                        'Scholarship': 'Yes' if student.scholarship else 'No',
                        'Part_Time_Job': 'Yes' if student.part_time_job else 'No',
                        'Internet_Access': 'Yes' if student.internet_access else 'No',
                        'Travel_Time_Minutes': float(student.travel_time_minutes) if student.travel_time_minutes else 30.0,
                        'Stress_Index': student.stress_index or 5.0,
                        'Parental_Education': student.parental_education or 'High School'
                    }
                    
                    if student.date_of_birth:
                        student_data['Age'] = float(timezone.now().year - student.date_of_birth.year)
                        
                    res = predictor.predict(student_data)
                    
                    # Update Student model fields
                    student.last_prediction_probability = res['dropout_probability']
                    student.last_prediction_date = timezone.now()
                    student.risk_level = res['risk_level']
                    student.save()
                    
                    # Create prediction record
                    DropoutPrediction.objects.create(
                        student=student,
                        predicted_by=None,
                        dropout_probability=res['dropout_probability'],
                        risk_level=res['risk_level'],
                        prediction_result=(res['prediction'] == 'At Risk of Dropout'),
                        threshold_used=res['threshold_used'] / 100.0,
                        confidence_score=res['confidence_score'],
                        input_data=student_data,
                        key_factors=res.get('key_factors', []),
                        recommendations=res.get('recommendations', []),
                        shap_explanation=res.get('shap_explanation', {})
                    )
                    
                    # Requery
                    predictions = DropoutPrediction.objects.filter(student=student).order_by('-predicted_at')
                except Exception as pred_err:
                    logger.error(f"Failed to auto-predict student: {str(pred_err)}")
                    
            serializer = DropoutPredictionSerializer(predictions, many=True)
            
            return Response({
                'success': True,
                'data': serializer.data,
                'count': predictions.count()
            }, status=status.HTTP_200_OK)
            
        except Student.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Student not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ============================================
# TEACHER DASHBOARD VIEW
# ============================================

class TeacherDashboardView(APIView):
    """Get teacher dashboard data"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from django.utils import timezone
        from django.db.models import Avg
        try:
            if request.user.user_type != 'teacher' and not request.user.is_superuser:
                return Response({
                    'success': False,
                    'error': 'Only teachers can access this'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Filter students by teacher's department
            try:
                profile = TeacherProfile.objects.get(user=request.user)
                students = Student.objects.filter(department=profile.department)
            except TeacherProfile.DoesNotExist:
                students = Student.objects.all()
            
            stats = {
                'totalStudents': students.count(),
                'atRisk': students.filter(
                    risk_level__in=['Critical Risk', 'High Risk', 'Moderate Risk', 'Critical Risk - Immediate Intervention Needed', 'High Risk - Intensive Support Required', 'Moderate Risk - Monitor Closely']
                ).count(),
                'criticalRisk': students.filter(
                    risk_level__in=['Critical Risk', 'Critical Risk - Immediate Intervention Needed']
                ).count(),
                'averageGPA': round(students.filter(cgpa__gt=0).aggregate(Avg('cgpa'))['cgpa__avg'] or 0.0, 2),
                'predictionsToday': DropoutPrediction.objects.filter(
                    student__in=students, 
                    predicted_at__date=timezone.now().date()
                ).count()
            }
            
            # Recent predictions in teacher's department
            recent_predictions = DropoutPrediction.objects.filter(student__in=students).order_by('-predicted_at')[:10]
            recent_data = []
            for pred in recent_predictions:
                recent_data.append({
                    'id': pred.id,
                    'student_name': pred.student.get_full_name(),
                    'risk_level': pred.risk_level,
                    'probability': pred.dropout_probability,
                    'predicted_by': pred.predicted_by.get_full_name() if pred.predicted_by else 'System',
                    'date': pred.predicted_at
                })
                
            # Urgent attention list (Critical and High risk students)
            critical_list = students.filter(
                risk_level__in=['Critical Risk', 'High Risk', 'Critical Risk - Immediate Intervention Needed', 'High Risk - Intensive Support Required']
            ).order_by('-last_prediction_probability')[:5]
            
            critical_data = []
            for s in critical_list:
                critical_data.append({
                    'id': s.id,
                    'name': s.get_full_name(),
                    'student_id': s.student_id,
                    'cgpa': s.cgpa,
                    'attendance': s.attendance_percentage,
                    'probability': s.last_prediction_probability
                })
            
            return Response({
                'success': True,
                'stats': stats,
                'recent_predictions': recent_data,
                'critical_students': critical_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)