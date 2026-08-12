from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Student CRUD
    path('', views.StudentListView.as_view(), name='student_list'),  # GET all students
    path('create/', views.CreateStudentView.as_view(), name='create_student'),  # POST create student
    path('<int:pk>/', views.StudentDetailView.as_view(), name='student_detail'),  # GET, PUT, DELETE
    path('me/', views.MyStudentProfileView.as_view(), name='my_profile'),  # GET current student profile
    path('<int:student_id>/predictions/', views.StudentPredictionsView.as_view(), name='student_predictions'),
    
    # Teacher dashboard
    path('teacher/dashboard/', views.TeacherDashboardView.as_view(), name='teacher_dashboard'),
]