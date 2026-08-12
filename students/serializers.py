from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Student, DropoutPrediction

User = get_user_model()

class StudentCreateSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, min_length=6)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    student_id = serializers.CharField(required=False, allow_blank=True)
    department = serializers.CharField(required=False, default='CS')
    year_of_study = serializers.CharField(required=False, default='Year 1')

class StudentListSerializer(serializers.ModelSerializer):
    """Simplified student serializer for list view"""
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = [
            'id', 'student_id', 'username', 'email', 'first_name', 'last_name',
            'department', 'year_of_study', 'cgpa', 'attendance_percentage',
            'risk_level', 'last_prediction_probability', 'created_at'
        ]
    
    def get_username(self, obj):
        return obj.user.username if obj.user else None
    
    def get_email(self, obj):
        return obj.user.email if obj.user else None

class StudentDetailSerializer(serializers.ModelSerializer):
    """Detailed student serializer with all fields"""
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    phone_number = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = '__all__'
    
    def get_username(self, obj):
        return obj.user.username if obj.user else None
    
    def get_email(self, obj):
        return obj.user.email if obj.user else None
    
    def get_phone_number(self, obj):
        return obj.user.phone_number if obj.user else None

class DropoutPredictionSerializer(serializers.ModelSerializer):
    """Serializer for dropout predictions"""
    student_name = serializers.SerializerMethodField()
    predicted_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = DropoutPrediction
        fields = '__all__'
    
    def get_student_name(self, obj):
        return obj.student.get_full_name()
    
    def get_predicted_by_name(self, obj):
        return obj.predicted_by.get_full_name() if obj.predicted_by else 'System'