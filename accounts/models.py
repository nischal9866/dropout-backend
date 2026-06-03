from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class User(AbstractUser):
    """Custom User model to handle different user types"""
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    
    # For teacher-specific fields
    employee_id = models.CharField(max_length=20, blank=True, null=True)
    qualification = models.CharField(max_length=100, blank=True, null=True)
    
    # For student-specific fields
    roll_number = models.CharField(max_length=20, blank=True, null=True)
    class_name = models.CharField(max_length=20, blank=True, null=True)
    parent_phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Fix the reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',  # Changed from 'user_set'
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',  # Changed from 'user_set'
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

class TeacherProfile(models.Model):
    """Additional teacher information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    department = models.CharField(max_length=100, blank=True, null=True)  # Allow null
    joining_date = models.DateField(auto_now_add=True)  # Auto set to current date
    subjects_taught = models.TextField(blank=True, null=True)  # Allow null
    is_class_teacher = models.BooleanField(default=False)
    class_assigned = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return f"Teacher: {self.user.get_full_name() or self.user.username}"
    
    class Meta:
        db_table = 'teacher_profiles'

class StudentProfile(models.Model):
    """Additional student information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    enrollment_date = models.DateField(default=timezone.now)
    guardian_name = models.CharField(max_length=100)
    guardian_relationship = models.CharField(max_length=50)
    emergency_contact = models.CharField(max_length=15)
    medical_info = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Student: {self.user.get_full_name() or self.user.username}"
    
    class Meta:
        db_table = 'student_profiles'