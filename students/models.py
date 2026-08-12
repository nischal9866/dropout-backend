from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Student(models.Model):
    """Student Model - Detailed student information"""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='student_profile'  # This is now the only one
    )
    
    # Personal Information
    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField(blank=True)
    
    # Academic Information
    enrollment_date = models.DateField(default=timezone.now)
    department = models.CharField(max_length=100)
    current_semester = models.IntegerField(default=1)
    year_of_study = models.CharField(max_length=20, choices=[
        ('Year 1', 'Year 1'),
        ('Year 2', 'Year 2'),
        ('Year 3', 'Year 3'),
        ('Year 4', 'Year 4')
    ])
    
    # Academic Performance (Latest)
    current_gpa = models.FloatField(default=0.0)
    semester_gpa = models.FloatField(default=0.0)
    cgpa = models.FloatField(default=0.0)
    attendance_percentage = models.FloatField(default=0.0)
    course_failures = models.IntegerField(default=0)
    
    # Engagement Metrics
    study_hours_per_day = models.FloatField(default=0.0)
    library_visits_per_week = models.IntegerField(default=0)
    assignment_submission_rate = models.FloatField(default=100.0)
    participation_score = models.FloatField(default=5.0)
    
    # Financial Information
    family_income = models.FloatField(null=True, blank=True)
    scholarship = models.BooleanField(default=False)
    part_time_job = models.BooleanField(default=False)
    tuition_payment_delay_days = models.IntegerField(default=0)
    
    # Additional Info
    parental_education = models.CharField(max_length=50, blank=True)
    internet_access = models.BooleanField(default=True)
    travel_time_minutes = models.IntegerField(default=0)
    stress_index = models.FloatField(default=5.0)
    
    # Dropout Prediction History
    last_prediction_probability = models.FloatField(null=True, blank=True)
    last_prediction_date = models.DateTimeField(null=True, blank=True)
    risk_level = models.CharField(max_length=20, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.student_id} - {self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_risk_color(self):
        if self.risk_level == 'Critical Risk':
            return 'red'
        elif self.risk_level == 'High Risk':
            return 'orange'
        elif self.risk_level == 'Medium Risk':
            return 'yellow'
        else:
            return 'green'
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'students_student'

class TeacherProfile(models.Model):
    """Teacher Profile Model"""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='teacher_profile'  # This is now the only one
    )
    department = models.CharField(max_length=100)
    joining_date = models.DateField(default=timezone.now)
    subjects_taught = models.TextField(help_text="Comma-separated subjects")
    is_class_teacher = models.BooleanField(default=False)
    class_assigned = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return f"Teacher: {self.user.get_full_name() or self.user.username}"
    
    class Meta:
        db_table = 'teachers_teacher_profile'

class DropoutPrediction(models.Model):
    """Store all prediction history"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='predictions')
    predicted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    # Prediction Results
    dropout_probability = models.FloatField()
    risk_level = models.CharField(max_length=20)
    prediction_result = models.BooleanField()
    
    # Model Information
    threshold_used = models.FloatField(default=0.40)
    confidence_score = models.FloatField()
    
    # Input Data at Time of Prediction
    input_data = models.JSONField(default=dict)
    
    # Key Factors
    key_factors = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    shap_explanation = models.JSONField(default=dict, null=True, blank=True)
    
    predicted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student} - {self.predicted_at.strftime('%Y-%m-%d')}"
    
    class Meta:
        db_table = 'students_dropout_predictions'
        ordering = ['-predicted_at']