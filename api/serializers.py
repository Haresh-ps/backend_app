from rest_framework import serializers
from .models import Profile, Assessment, Media, AnalysisResult
from django.contrib.auth.models import User

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email')
    
    class Meta:
        model = Profile
        fields = ['username', 'email', 'clinic_name', 'specialization', 'phone_number', 'full_name', 'address', 'experience_years']

    def validate_phone_number(self, value):
        if value:
            if len(value) != 10 or not value.isdigit():
                raise serializers.ValidationError("Phone number must be exactly 10 digits.")
        return value

    def validate_email(self, value):
        if value:
            if not value.endswith('@gmail.com'):
                raise serializers.ValidationError("Only @gmail.com addresses are allowed.")
            prefix = value.split('@')[0]
            if len(prefix) < 3 or prefix[0].isdigit():
                raise serializers.ValidationError("Email prefix must be at least 3 characters and must not start with a number.")
        return value

    def update(self, instance, validated_data):
        # Extract user data if present (DRF nests it for source='user.email')
        if 'user' in validated_data:
            user_data = validated_data.pop('user')
            email = user_data.get('email')
            if email:
                user = instance.user
                user.email = email
                user.save()
        
        return super().update(instance, validated_data)

class AnalysisResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisResult
        fields = ['confidence_score', 'viability_prediction', 'ai_feedback', 
                  'glucose_level', 'lactate_level', 'pyruvate_level', 'oxidative_stress',
                  'amino_acids', 'vitamins', 'ammonia', 'ph_change', 'oxygen_uptake', 'co2_release']

class AssessmentSerializer(serializers.ModelSerializer):
    analysis = AnalysisResultSerializer(many=True, read_only=True)
    doctor_info = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = ['id', 'patient_id', 'patient_name', 'patient_dob', 'patient_age', 'embryo_count', 'embryo_day', 'culture_duration', 
                  'culture_medium', 'media_color_change', 'ph_deviation', 'visual_clarity',
                  'questions_data', 'doctor_notes', 'created_at', 'analysis', 'doctor_info']

    def get_doctor_info(self, obj):
        if obj.user:
            try:
                profile = Profile.objects.get(user=obj.user)
                return {
                    "full_name": profile.full_name,
                    "specialization": profile.specialization,
                    "clinic_name": profile.clinic_name,
                    "phone_number": profile.phone_number
                }
            except Profile.DoesNotExist:
                return {"full_name": obj.user.username}
        return None

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


