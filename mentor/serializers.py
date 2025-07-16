from rest_framework import serializers
from .models import MentorProfile


class MentorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorProfile
        fields = '__all__'
        read_only_fields = ['id', 'user', 'date_of_birth', 'selected_sports', 'created_at', 'updated_at']

class MentorOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorProfile
        fields = ['date_of_birth', 'selected_sports', 'social_links']
        extra_kwargs = {
            'date_of_birth': {'help_text': 'Birthdate in YYYY-MM-DD format'},
            'selected_sports': {'help_text': 'List of selected sports (JSON array or object)'},
            'social_links': {'help_text': 'JSON object with keys like facebook, instagram, etc.'},
        } 