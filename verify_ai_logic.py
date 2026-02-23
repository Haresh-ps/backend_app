import os
import django
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'doctor_backend.settings')
django.setup()

from api.models import Assessment, AnalysisResult, Media
from django.contrib.auth.models import User
from api.views import analyze_assessment
from rest_framework.test import APIRequestFactory
from rest_framework.response import Response

def test_scoring():
    print("Starting AI Logic Verification...")
    
    # 1. Setup Mock User and Assessment
    user, _ = User.objects.get_or_create(username='test_verify')
    
    # Test Case 1: Optimal Answers (High Score)
    assessment_optimal = Assessment.objects.create(
        user=user,
        patient_name="Optimal Patient",
        embryo_day="Blastocyst",
        culture_duration="5 days",
        questions_data={
            "culture_medium": "G - 1 PLUS (Vitrolife)",
            "media_color_change": "None",
            "ph_deviation": "Normal",
            "visual_clarity": "Clear"
        },
        glucose_level=3.5,
        lactate_level=1.5,
        pyruvate_level=0.3,
        oxidative_stress=2.0
    )
    
    # Mock visual analysis (add a media object)
    Media.objects.create(assessment=assessment_optimal, file="dummy.jpg")
    
    factory = APIRequestFactory()
    request = factory.post(f'/api/auth/assessments/{assessment_optimal.id}/analyze/', {}, format='json')
    
    response = analyze_assessment(request, assessment_optimal.id)
    print(f"Optimal Case - Score: {response.data['confidence_score']}, Prediction: {response.data['viability_prediction']}")
    assert response.data['confidence_score'] == 100.0
    assert response.data['viability_prediction'] == "Good Viability"

    # Test Case 2: Poor Answers (Low Score)
    assessment_poor = Assessment.objects.create(
        user=user,
        patient_name="Poor Patient",
        embryo_day="D3",
        culture_duration="3 days",
        questions_data={
            "culture_medium": "Other",
            "media_color_change": "Significant",
            "ph_deviation": "High",
            "visual_clarity": "Turbid"
        },
        glucose_level=1.0, # Low
        lactate_level=5.0, # High
        pyruvate_level=0.0, # Missing
        oxidative_stress=12.0 # High
    )
    
    request_poor = factory.post(f'/api/auth/assessments/{assessment_poor.id}/analyze/', {}, format='json')
    response_poor = analyze_assessment(request_poor, assessment_poor.id)
    
    print(f"Poor Case - Score: {response_poor.data['confidence_score']}, Prediction: {response_poor.data['viability_prediction']}")
    # Calculation: 
    # Q: Day(5)+Dur(5)+Med(5)+Color(0)+pH(0)+Clar(0) = 15
    # Met: 0 (all out of range or 0)
    # Vis: 0
    # Total: 15 / 100 = 15%
    assert response_poor.data['confidence_score'] == 15.0
    assert response_poor.data['viability_prediction'] == "Low Viability"

    print("AI Logic Verification Successful!")

if __name__ == "__main__":
    try:
        test_scoring()
    except Exception as e:
        print(f"Verification Failed: {e}")
        import traceback
        traceback.print_exc()
