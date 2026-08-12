from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication APIs
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('register/', views.StudentRegistrationView.as_view(), name='register'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('me/', views.UserInfoView.as_view(), name='user_info'),  # Add this
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    
    # Admin - Teacher Management APIs
    path('admin/teachers/', views.TeacherListView.as_view(), name='teacher_list'),
    path('admin/teachers/create/', views.CreateTeacherView.as_view(), name='create_teacher'),
    path('admin/teachers/<int:teacher_id>/', views.TeacherDetailView.as_view(), name='teacher_detail'),
    path('admin/teachers/<int:teacher_id>/update/', views.UpdateTeacherView.as_view(), name='update_teacher'),
    path('admin/teachers/<int:teacher_id>/delete/', views.DeleteTeacherView.as_view(), name='delete_teacher'),
    path('admin/teachers/<int:teacher_id>/reset-password/', views.ResetTeacherPasswordView.as_view(), name='reset_teacher_password'),
    

]