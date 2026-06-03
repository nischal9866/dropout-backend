from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from .models import User, TeacherProfile, StudentProfile
from .serializers import (
    UserLoginSerializer, UserRegistrationSerializer, UserSerializer,
    TeacherCreateSerializer, TeacherListSerializer, TeacherUpdateSerializer,
    ChangePasswordSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer
)
from django.core.mail import send_mail
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
                        'is_superuser': user.is_superuser
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
            
            # Create student profile
            StudentProfile.objects.create(
                user=user,
                guardian_name=serializer.validated_data.get('guardian_name', ''),
                guardian_relationship='Parent',
                emergency_contact=serializer.validated_data.get('parent_phone', '')
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
        
        # Add role-specific data
        if request.user.user_type == 'teacher' and hasattr(request.user, 'teacher_profile'):
            data['teacher_profile'] = {
                'department': request.user.teacher_profile.department,
                'joining_date': request.user.teacher_profile.joining_date,
                'subjects_taught': request.user.teacher_profile.subjects_taught,
                'is_class_teacher': request.user.teacher_profile.is_class_teacher,
                'class_assigned': request.user.teacher_profile.class_assigned
            }
        elif request.user.user_type == 'student' and hasattr(request.user, 'student_profile'):
            data['student_profile'] = {
                'date_of_birth': request.user.student_profile.date_of_birth,
                'enrollment_date': request.user.student_profile.enrollment_date,
                'guardian_name': request.user.student_profile.guardian_name,
                'guardian_relationship': request.user.student_profile.guardian_relationship,
                'emergency_contact': request.user.student_profile.emergency_contact
            }
        
        return Response(data, status=status.HTTP_200_OK)
    
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'user': serializer.data}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
                return Response({'success': False, 'error': 'Wrong old password'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateTeacherView(APIView):
    """Admin creates teacher account"""
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        # Get the data from request
        data = request.data.copy()  # Create a mutable copy
        
        # Check if password is provided
        password = data.get('password', '')
        
        # Generate password if not provided
        if not password:
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            data['password'] = password
        
        serializer = TeacherCreateSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Return the generated password in response
            return Response({
                'success': True,
                'message': 'Teacher created successfully',
                'teacher': TeacherListSerializer(user).data,
                'generated_password': password  # Send password back to frontend
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
                return Response({'success': True, 'teacher': TeacherListSerializer(teacher).data}, status=status.HTTP_200_OK)
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

class PasswordResetView(APIView):
    """Request password reset"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                # Generate reset token (implement your own token generation)
                # Send email with reset link
                return Response({'success': True, 'message': 'Password reset email sent'}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({'success': True, 'message': 'If email exists, reset link sent'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    """Confirm password reset"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            # Implement password reset logic
            return Response({'success': True, 'message': 'Password reset successful'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)