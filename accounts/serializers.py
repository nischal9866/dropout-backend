from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from students.models import Student
import re

User = get_user_model()

# Simple password validator
def simple_password_validation(password):
    """Simple password validation - only check length"""
    if len(password) < 6:
        raise serializers.ValidationError("Password must be at least 6 characters long")
    return password

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model - only fields that exist in User"""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'user_type', 'phone_number', 'address', 'profile_picture',
            'employee_id', 'qualification', 'is_active', 'is_staff', 'is_superuser'
        ]
        read_only_fields = ['id', 'user_type', 'is_staff', 'is_superuser']

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for student registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[simple_password_validation])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'email', 'first_name', 'last_name']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        validated_data['user_type'] = 'student'
        user = User.objects.create_user(**validated_data)
        return user

class TeacherCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating teachers - only for admin"""
    department = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    subjects_taught = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, validators=[simple_password_validation])
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number',
                  'employee_id', 'qualification', 'department', 'subjects_taught', 'password']
    
    def create(self, validated_data):
        # Extract teacher profile data
        department = validated_data.pop('department', 'General')
        subjects_taught = validated_data.pop('subjects_taught', '')
        password = validated_data.pop('password', None)
        
        # Set user type
        validated_data['user_type'] = 'teacher'
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Set password if provided
        if password:
            user.set_password(password)
            user.save()
        
        # Create teacher profile
        from students.models import TeacherProfile
        TeacherProfile.objects.create(
            user=user,
            department=department or 'General',
            subjects_taught=subjects_taught or '',
            is_class_teacher=False,
            class_assigned=None
        )
        
        return user

class TeacherListSerializer(serializers.ModelSerializer):
    """Serializer for listing teachers with profile info"""
    department = serializers.SerializerMethodField()
    subjects_taught = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'phone_number', 'employee_id', 'qualification', 'is_active',
                  'department', 'subjects_taught']
    
    def get_department(self, obj):
        if hasattr(obj, 'teacher_profile'):
            return obj.teacher_profile.department
        return None
    
    def get_subjects_taught(self, obj):
        if hasattr(obj, 'teacher_profile'):
            return obj.teacher_profile.subjects_taught
        return None

class TeacherUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating teachers"""
    department = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    subjects_taught = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number',
                  'employee_id', 'qualification', 'department', 'subjects_taught', 'is_active']
    
    def update(self, instance, validated_data):
        # Extract teacher profile data
        department = validated_data.pop('department', None)
        subjects_taught = validated_data.pop('subjects_taught', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update teacher profile if data provided
        if department is not None or subjects_taught is not None:
            if hasattr(instance, 'teacher_profile'):
                profile = instance.teacher_profile
                if department is not None:
                    profile.department = department
                if subjects_taught is not None:
                    profile.subjects_taught = subjects_taught
                profile.save()
        
        return instance

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[simple_password_validation])
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords don't match"})
        if len(attrs['new_password']) < 6:
            raise serializers.ValidationError({"new_password": "Password must be at least 6 characters long"})
        return attrs

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[simple_password_validation])
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords don't match"})
        return attrs