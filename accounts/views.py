from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from .models import User
from .serializers import (
    UserLoginSerializer, UserRegistrationSerializer, UserSerializer,
    TeacherCreateSerializer, TeacherListSerializer, TeacherUpdateSerializer,
    ChangePasswordSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer
)
from django.conf import settings
import random
import string

class UserLoginView(APIView):
    """Handle user login and return JWT tokens"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            user = authenticate(username=username, password=password)
            
            if user and user.is_active:
                refresh = RefreshToken.for_user(user)
                update_last_login(None, user)
                
                return Response({
                    'success': True,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'user_type': user.user_type,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser,
                        'phone_number': user.phone_number,
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'error': 'Invalid credentials or inactive account'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLogoutView(APIView):
    """Handle user logout by blacklisting token"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'success': True, 'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StudentRegistrationView(APIView):
    """Allow students to register themselves"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create student profile with minimal data
            from students.models import Student
            Student.objects.create(
                user=user,
                student_id=f"STU{random.randint(10000, 99999)}",
                first_name=user.first_name,
                last_name=user.last_name,
                email=user.email,
                phone_number='',
                department='CS',
                year_of_study='Year 1',
            )
            
            return Response({
                'success': True,
                'message': 'Student registered successfully',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    """Get and update user profile"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        data = serializer.data
        
        # Add role-specific data from Student/Teacher models
        if request.user.user_type == 'student':
            try:
                student = request.user.student_profile
                data['student_data'] = {
                    'student_id': student.student_id,
                    'department': student.department,
                    'year_of_study': student.year_of_study,
                    'cgpa': student.cgpa,
                    'attendance_percentage': student.attendance_percentage,
                    'risk_level': student.risk_level,
                }
            except:
                pass
        elif request.user.user_type == 'teacher':
            try:
                teacher = request.user.teacher_profile
                data['teacher_data'] = {
                    'department': teacher.department,
                    'subjects_taught': teacher.subjects_taught,
                    'joining_date': teacher.joining_date,
                }
            except:
                pass
        
        return Response(data, status=status.HTTP_200_OK)
    
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'user': serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserInfoView(APIView):
    """Get current user info for frontend"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.user_type,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'phone_number': user.phone_number,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
        })

class ChangePasswordView(APIView):
    """Change user password"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.validated_data['old_password']):
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({'success': True, 'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'success': False, 'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateTeacherView(APIView):
    """Admin creates teacher account"""
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        # Create a mutable copy of the data
        data = request.data.copy()
        
        # Check if password is provided
        password = data.get('password', '')
        
        # Generate password if not provided
        if not password:
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            data['password'] = password
        
        serializer = TeacherCreateSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            
            return Response({
                'success': True,
                'message': 'Teacher created successfully',
                'teacher': TeacherListSerializer(user).data,
                'generated_password': password
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TeacherListView(APIView):
    """List all teachers (Admin only)"""
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        teachers = User.objects.filter(user_type='teacher').select_related('teacher_profile')
        serializer = TeacherListSerializer(teachers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TeacherDetailView(APIView):
    """Get teacher details"""
    permission_classes = [IsAdminUser]
    
    def get(self, request, teacher_id):
        try:
            teacher = User.objects.get(id=teacher_id, user_type='teacher')
            serializer = TeacherListSerializer(teacher)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=status.HTTP_404_NOT_FOUND)

class UpdateTeacherView(APIView):
    """Update teacher information"""
    permission_classes = [IsAdminUser]
    
    def put(self, request, teacher_id):
        try:
            teacher = User.objects.get(id=teacher_id, user_type='teacher')
            serializer = TeacherUpdateSerializer(teacher, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'success': True, 
                    'teacher': TeacherListSerializer(teacher).data
                }, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=status.HTTP_404_NOT_FOUND)

class DeleteTeacherView(APIView):
    """Delete teacher account"""
    permission_classes = [IsAdminUser]
    
    def delete(self, request, teacher_id):
        try:
            teacher = User.objects.get(id=teacher_id, user_type='teacher')
            teacher.delete()
            return Response({'success': True, 'message': 'Teacher deleted successfully'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=status.HTTP_404_NOT_FOUND)

class ResetTeacherPasswordView(APIView):
    """Reset teacher password"""
    permission_classes = [IsAdminUser]
    
    def post(self, request, teacher_id):
        try:
            teacher = User.objects.get(id=teacher_id, user_type='teacher')
            
            # Get password from request or generate random
            password = request.data.get('password', '')
            if not password:
                password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            elif len(password) < 6:
                return Response({
                    'error': 'Password must be at least 6 characters long'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            teacher.set_password(password)
            teacher.save()
            
            return Response({
                'success': True,
                'message': 'Password reset successfully',
                'generated_password': password if not request.data.get('password') else None
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'Teacher not found'}, status=status.HTTP_404_NOT_FOUND)