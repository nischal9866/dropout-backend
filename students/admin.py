from django.contrib import admin
from .models import Student, TeacherProfile, DropoutPrediction

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'first_name', 'last_name', 'department', 'cgpa', 'risk_level')
    list_filter = ('department', 'year_of_study', 'risk_level', 'scholarship')
    search_fields = ('student_id', 'first_name', 'last_name', 'email')
    readonly_fields = ('created_at', 'updated_at', 'last_prediction_date')
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'student_id', 'first_name', 'last_name', 'date_of_birth', 
                      'gender', 'phone_number', 'email', 'address')
        }),
        ('Academic Information', {
            'fields': ('enrollment_date', 'department', 'current_semester', 'year_of_study',
                      'current_gpa', 'semester_gpa', 'cgpa', 'attendance_percentage', 
                      'course_failures')
        }),
        ('Engagement & Financial', {
            'fields': ('study_hours_per_day', 'library_visits_per_week', 
                      'assignment_submission_rate', 'participation_score',
                      'family_income', 'scholarship', 'part_time_job', 
                      'tuition_payment_delay_days')
        }),
        ('Additional Info', {
            'fields': ('parental_education', 'internet_access', 'travel_time_minutes', 
                      'stress_index', 'is_active')
        }),
        ('Prediction Data', {
            'fields': ('last_prediction_probability', 'last_prediction_date', 'risk_level'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'joining_date', 'is_class_teacher')
    list_filter = ('department', 'is_class_teacher')
    search_fields = ('user__username', 'user__email', 'department')

@admin.register(DropoutPrediction)
class DropoutPredictionAdmin(admin.ModelAdmin):
    list_display = ('student', 'risk_level', 'dropout_probability', 'predicted_at')
    list_filter = ('risk_level', 'predicted_at')
    search_fields = ('student__first_name', 'student__last_name')
    readonly_fields = ('predicted_at',)