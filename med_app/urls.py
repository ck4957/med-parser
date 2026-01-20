from django.urls import path

from . import views
from . import mlx_views

urlpatterns = [
    path("", views.index, name="index"),
    path('parse_medical_text', views.parse_medical_text, name='parse_medical_text'),
    path('parse_medical_text_gemma', views.parse_medical_text_gemma, name='parse_medical_text_gemma'),
    
    # MLX Local Inference Endpoints (M4 Max)
    path('api/process-medical-text/', mlx_views.process_medical_text, name='mlx_process'),
    path('api/health/', mlx_views.health_check, name='mlx_health'),
    path('api/model-info/', mlx_views.model_info, name='mlx_model_info'),
]