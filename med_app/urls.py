from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('parse_medical_text', views.parse_medical_text, name='parse_medical_text'),
    path('parse_medical_text_gemma', views.parse_medical_text_gemma, name='parse_medical_text_gemma'),
]