from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

app_name = 'accounts'

urlpatterns = [
    # Authentication APIs
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('register/', views.StudentRegistrationView.as_view(), name='register'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Add this line

    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Admin - Teacher Management APIs
    path('admin/teachers/', views.TeacherListView.as_view(), name='teacher_list'),
    path('admin/teachers/create/', views.CreateTeacherView.as_view(), name='create_teacher'),
    path('admin/teachers/<int:teacher_id>/', views.TeacherDetailView.as_view(), name='teacher_detail'),
    path('admin/teachers/<int:teacher_id>/update/', views.UpdateTeacherView.as_view(), name='update_teacher'),
    path('admin/teachers/<int:teacher_id>/delete/', views.DeleteTeacherView.as_view(), name='delete_teacher'),
    
    # Password Reset APIs
    path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]