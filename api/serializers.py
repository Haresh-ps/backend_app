from rest_framework import serializers
from .models import Profile, Assessment, Media, AnalysisResult
from django.contrib.auth.models import User

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['clinic_name', 'specialization', 'phone_number', 'full_name', 'address', 'experience_years']

class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = ['id', 'patient_id', 'patient_name', 'patient_dob', 'patient_age', 'embryo_count', 'embryo_day', 'culture_duration', 'questions_data', 
                  'glucose_level', 'lactate_level', 'pyruvate_level', 'oxidative_stress', 'created_at']

class MediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = ['id', 'assessment', 'file', 'file_type', 'file_url']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and hasattr(obj.file, 'url') and request:
            return request.build_absolute_uri(obj.file.url)
        return None

class AnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResult
        fields = ['confidence_score', 'viability_prediction', 'ai_feedback']
