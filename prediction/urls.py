from django.urls import path
from . import views

app_name = 'prediction'

urlpatterns = [
    path('predict/', views.PredictDropoutView.as_view(), name='predict'),
    path('batch-predict/', views.BatchPredictDropoutView.as_view(), name='batch_predict'),
    path('global-explain/', views.GlobalExplainView.as_view(), name='global_explain'),
]