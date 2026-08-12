"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from dashboard import views as dashboard_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/accounts/', include('accounts.urls')),  
    path('api/prediction/', include('prediction.urls')),
    path('api/students/', include('students.urls')),  
    path('api/dashboard/stats/', dashboard_views.DashboardStatsView.as_view(), name='dashboard_stats'),
    path('api/analytics/', dashboard_views.AnalyticsView.as_view(), name='analytics'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)