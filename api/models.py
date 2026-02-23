from django.db import models
from django.contrib.auth.models import User
import json

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    clinic_name = models.CharField(max_length=255, blank=True)
    specialization = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=50, blank=True)
    full_name = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    experience_years = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Profile for {self.user.username}"

class Assessment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True) # Allow null for demo/anonymous
    patient_id = models.CharField(max_length=50, default="Unknown", blank=True)
    patient_name = models.CharField(max_length=255, default="Unknown")
    patient_dob = models.CharField(max_length=50, blank=True) # Keeping simple for now, can be DateField
    patient_age = models.IntegerField(default=0)
    embryo_count = models.IntegerField(default=1)
    embryo_day = models.CharField(max_length=50, blank=True)
    culture_duration = models.CharField(max_length=50, blank=True)
    questions_data = models.JSONField(default=dict) # Stores maps of Q1-Q6 answers
    
    # Metabolic Parameters
    glucose_level = models.FloatField(default=0.0)
    lactate_level = models.FloatField(default=0.0)
    pyruvate_level = models.FloatField(default=0.0)
    oxidative_stress = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assessment {self.id} - {self.patient_name} - {self.created_at}"

class Media(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='uploads/')
    file_type = models.CharField(max_length=50, blank=True) # image/jpeg, video/mp4 etc.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Media for Assessment {self.assessment.id}"

class AnalysisResult(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='analysis')
    confidence_score = models.FloatField()
    viability_prediction = models.CharField(max_length=255)
    ai_feedback = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis {self.id} for Assessment {self.assessment.id}"
