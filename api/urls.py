from django.urls import path
from . import views

urlpatterns = [
    path('auth/login/', views.login_view),
    path('auth/signup/', views.signup_view),
    path('auth/profile/', views.profile_view),
    path('auth/assessments/', views.create_assessment),
    path('auth/assessments/<int:assessment_id>/analyze/', views.analyze_assessment),
    path('auth/upload/', views.upload_media),
]
