from django.contrib import admin
from .models import Profile, Assessment, Media, AnalysisResult

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'clinic_name', 'phone_number')

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient_id', 'patient_name', 'created_at', 'confidence_score')
    list_filter = ('created_at', 'patient_name')

    def confidence_score(self, obj):
        # Helper to show score in list if analysis exists
        analysis = obj.analysis.first()
        return analysis.confidence_score if analysis else "-"
    readonly_fields = ('formatted_questions',)
    exclude = ('questions_data',)

    def formatted_questions(self, obj):
        import json
        if not obj.questions_data:
            return "No data"
        
        # If it's already a dict, use it. If string, parse it.
        data = obj.questions_data
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except:
                return data
        
        # Build a nice HTML or string representation
        # Using format_html for safety if we used HTML, but simple text for now with newlines
        # Django admin displays newlines if we use specific widget or just text.
        # Let's try to make it keyed.
        
        output = []
        # Mapping of keys to readable labels
        labels = {
            'cytoplasm': 'Question 1: Cytoplasm',
            'zona_pellucida': 'Question 2: Zona Pellucida',
            'fragmentation': 'Question 3: Fragmentation',
            'symmetry': 'Question 4: Symmetry',
            'size': 'Question 5: Size',
            'multi_nucleation': 'Question 6: Multi-nucleation',
            'notes': 'Doctor Notes'
        }
        
        # specific order if possible
        order = ['cytoplasm', 'zona_pellucida', 'fragmentation', 'symmetry', 'size', 'multi_nucleation', 'notes']
        
        for key in order:
            if key in data:
                label = labels.get(key, key.upper())
                output.append(f"{label}: {data[key]}")
        
        # Add any other keys not in strict order
        for key, val in data.items():
            if key not in order:
                output.append(f"{key}: {val}")
                
        return "\n\n".join(output)

    formatted_questions.short_description = "Questions & Notes"

@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('id', 'assessment', 'file_type', 'created_at')

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('assessment', 'confidence_score', 'viability_prediction')
