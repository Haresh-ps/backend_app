from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from .models import Profile, Assessment, Media, AnalysisResult
from .serializers import ProfileSerializer, AssessmentSerializer, MediaSerializer, AnalysisResultSerializer
import json

# --- AUTH ---
# Since Android code sends "username" and "password" to /api/auth/login/
# And we want to simulate a token response. In a real app we'd use simplejwt.
# Here we'll just mock it or create a real user and return a fake token to satisfy the client.

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(req):
    username = req.data.get('username')
    password = req.data.get('password')

    if not username or not password:
        return Response({"error": "Please provide both username and password"}, status=status.HTTP_400_BAD_REQUEST)

    # 1. Try to find user by username
    user = User.objects.filter(username=username).first()
    
    # 2. If not found, try to find by email
    if not user:
        user = User.objects.filter(email=username).first()

    # 3. If user found, verify password
    if user:
        # We use the found user's actual username for authentication
        from django.contrib.auth import authenticate
        user = authenticate(username=user.username, password=password)

    if user:
        # Provide a mock token that the Android app will store
        # In a production app, use rest_framework_simplejwt
        return Response({
            "access": f"mock_access_token_for_{user.username}",
            "refresh": "mock_refresh_token"
        })
    else:
        return Response({"error": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view(req):
    username = req.data.get('username')
    email = req.data.get('email')
    password = req.data.get('password')
    
    if not username or not password:
         return Response({"error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"error": "User already exists. Please login."}, status=status.HTTP_400_BAD_REQUEST)
    
    # Also check if email exists (if username != email)
    if email and User.objects.filter(email=email).exists():
         return Response({"error": "Email already registered. Please login."}, status=status.HTTP_400_BAD_REQUEST)

    User.objects.create_user(username=username, email=email, password=password)
    return Response({"message": "Signup successful"}, status=status.HTTP_201_CREATED)

# --- PROFILE ---
# Android sends GET and POST/PUT to /api/auth/profile/

@api_view(['GET', 'POST', 'PUT'])
@permission_classes([AllowAny]) # In real app IsAuthenticated
def profile_view(req):
    # For demo, since we use mock tokens, we need to pick a user.
    # We'll pick the first user or a hardcoded one.
    user = User.objects.first()
    if not user:
        # If no user exists yet, create a default one to prevent errors
        user = User.objects.create_user(username="testuser", password="password")
    
    if req.method == 'GET':
        profile, created = Profile.objects.get_or_create(user=user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    
    elif req.method in ['POST', 'PUT']:
        profile, created = Profile.objects.get_or_create(user=user)
        serializer = ProfileSerializer(profile, data=req.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- ASSESSMENTS ---

@api_view(['POST'])
@permission_classes([AllowAny])
def create_assessment(req):
    user = User.objects.first() # specific user handling needs token parsing
    
    data = req.data.copy()
    # Ensure questions_data is a dict (if sent as string)
    # Android sends a Map, DRF sees it as dict usually. Models handles JSONField.
    
    serializer = AssessmentSerializer(data=data)
    if serializer.is_valid():
        assessment = serializer.save(user=user)
        return Response({"id": assessment.id, "created_at": assessment.created_at}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def analyze_assessment(req, assessment_id):
    try:
        assessment = Assessment.objects.get(id=assessment_id)
    except Assessment.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        
    # Update assessment with any metabolic data sent in request
    if 'glucose_level' in req.data: assessment.glucose_level = float(req.data['glucose_level'])
    if 'lactate_level' in req.data: assessment.lactate_level = float(req.data['lactate_level'])
    if 'pyruvate_level' in req.data: assessment.pyruvate_level = float(req.data['pyruvate_level'])
    if 'oxidative_stress' in req.data: assessment.oxidative_stress = float(req.data['oxidative_stress'])
    assessment.save()
    
    # Logic to calculate score based on questions
    # Q1: Embryo Day (Blastocyst/D5/D6 = 10, D3 = 5)
    # Q2: Culture Duration (5 days = 10, else = 5)
    # Q3: Culture Medium (Vitrolife = 10, Origio = 8, Stage 1 = 8, Other = 5)
    # Q4: Media Color Change (None = 10, Mild = 5, Significant = 0)
    # Q5: pH Deviation (Normal = 10, Slight = 5, High = 0)
    # Q6: Visual Clarity (Clear = 10, Slightly Turbid = 5, Turbid = 0)
    
    score = 0
    feedback = []
    
    q_data = assessment.questions_data
    if isinstance(q_data, str):
        try:
            q_data = json.loads(q_data)
        except:
            q_data = {}

    # 1. Day & Duration (from Assessment model fields)
    day = str(assessment.embryo_day).lower()
    if 'd5' in day or 'd6' in day or 'blastocyst' in day:
        score += 10
    else:
        score += 5
        feedback.append("Early stage embryo (D3) assessment.")

    duration = str(assessment.culture_duration).lower()
    if '5' in duration:
        score += 10
    else:
        score += 5

    # 2. Culture Medium (Q3)
    val3 = str(q_data.get('culture_medium', "")).lower()
    if 'vitrolife' in val3: score += 10
    elif 'origio' in val3 or 'stage 1' in val3: score += 8
    else: 
        score += 5
        if val3: feedback.append(f"Using {val3} culture medium.")

    # 3. Media Color Change (Q4)
    val4 = str(q_data.get('media_color_change', "")).lower()
    if 'none' in val4: score += 10
    elif 'mild' in val4: 
        score += 5
        feedback.append("Mild color change in spent media.")
    elif 'significant' in val4:
        score += 0
        feedback.append("Significant color change in media; check metabolic activity.")

    # 4. pH Deviation (Q5)
    val5 = str(q_data.get('ph_deviation', "")).lower()
    if 'normal' in val5: score += 10
    elif 'slight' in val5:
        score += 5
        feedback.append("Slight pH deviation observed.")
    else:
        score += 0
        feedback.append("High pH deviation; potential stress indicator.")

    # 5. Visual Clarity (Q6)
    val6 = str(q_data.get('visual_clarity', "")).lower()
    if 'clear' in val6: score += 10
    elif 'slightly turbid' in val6:
        score += 5
        feedback.append("Slightly turbid media.")
    else:
        score += 0
        feedback.append("Turbid media observed.")

    # Metabolic Analysis (Max 20 pts)
    g_level = assessment.glucose_level
    l_level = assessment.lactate_level
    p_level = assessment.pyruvate_level
    o_stress = assessment.oxidative_stress
    
    metabolic_score = 0
    if g_level > 0:
        if 2.5 <= g_level <= 5.5: metabolic_score += 5
        elif g_level < 2.5: feedback.append("Low glucose consumption.")
        else: feedback.append("High glucose consumption.")
            
    if l_level > 0:
        if l_level < 2.0: metabolic_score += 5
        else: feedback.append("Elevated lactate levels.")
            
    if p_level > 0:
        metabolic_score += 5
        
    if o_stress > 0:
        if o_stress <= 5.0: metabolic_score += 5
        else: feedback.append("High oxidative stress detected.")
    
    score += metabolic_score

    # Visual Analysis (Max 20 pts)
    media_count = Media.objects.filter(assessment=assessment).count()
    if media_count > 0:
        score += 20
        feedback.append(f"Visual analysis confirms morphological viability.")
    
    # Final Calculation
    # Questions (60) + Metabolic (20) + Visual (20) = 100
    max_score = 100 
    final_score = (score / max_score) * 100
    if final_score > 100: final_score = 100
    
    prediction = "Good Viability"
    if final_score < 40: prediction = "Low Viability"
    elif final_score < 75: prediction = "Moderate Viability"
    
    ai_feedback_str = " ".join(feedback) if feedback else "Overall assessment indicates optimal embryo development and metabolic activity."

    result_data = {
        "confidence_score": round(final_score, 1),
        "viability_prediction": prediction,
        "ai_feedback": ai_feedback_str
    }
    
    # Update or Create
    AnalysisResult.objects.update_or_create(
        assessment=assessment,
        defaults={
            'confidence_score': result_data['confidence_score'],
            'viability_prediction': result_data['viability_prediction'],
            'ai_feedback': result_data['ai_feedback']
        }
    )
    
    return Response(result_data)

# --- MEDIA UPLOAD ---

from django.core.files.storage import default_storage

@api_view(['POST'])
@permission_classes([AllowAny])
def upload_media(req):
    assessment_id = req.data.get('assessment_id')
    # Cleanup quotes if sent with string
    if assessment_id and isinstance(assessment_id, str):
        assessment_id = assessment_id.replace('"', '')

    file_obj = req.FILES.get('file')
    
    if not file_obj or not assessment_id:
        return Response({"error": "Missing file or assessment_id"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        assessment = Assessment.objects.get(id=assessment_id)
    except Assessment.DoesNotExist:
        return Response({"error": "Assessment not found"}, status=status.HTTP_404_NOT_FOUND)
        
    media = Media.objects.create(
        assessment=assessment,
        file=file_obj,
        file_type=file_obj.content_type
    )
    
    serializer = MediaSerializer(media, context={'request': req})
    return Response(serializer.data, status=status.HTTP_201_CREATED)
