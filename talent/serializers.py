from rest_framework import serializers
from .models import TalentProfile


class TalentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentProfile
        fields = [
            'id', 'user', 'bio', 'date_of_birth', 'location', 'selected_sports',
            'experience_years', 'profile_picture', 'cover_photo', 'is_verified',
            'is_featured', 'social_links', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'date_of_birth', 'selected_sports', 'created_at', 'updated_at']

class TalentOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentProfile
        fields = ['date_of_birth', 'selected_sports', 'social_links']
        extra_kwargs = {
            'date_of_birth': {'help_text': 'Birthdate in YYYY-MM-DD format'},
            'selected_sports': {'help_text': 'List of selected sports (JSON array or object)'},
            'social_links': {'help_text': 'JSON object with keys like facebook, instagram, etc.'},
        } 