from rest_framework import serializers
from .models import MentorProfile, SelectedTalent, RejectedTalent
from talent.models import TalentProfile


class SelectedTalentSerializer(serializers.ModelSerializer):
    talent = serializers.PrimaryKeyRelatedField(queryset=TalentProfile.objects.all())
    class Meta:
        model = SelectedTalent
        fields = ['id', 'talent', 'selected_at']
        read_only_fields = ['id', 'selected_at']

class RejectedTalentSerializer(serializers.ModelSerializer):
    talent = serializers.PrimaryKeyRelatedField(queryset=TalentProfile.objects.all())
    class Meta:
        model = RejectedTalent
        fields = ['id', 'talent', 'rejected_at']
        read_only_fields = ['id', 'rejected_at']

class MentorProfileSerializer(serializers.ModelSerializer):
    selected_talents = SelectedTalentSerializer(source='selected_talent_links', many=True, read_only=True)
    rejected_talents = RejectedTalentSerializer(source='rejected_talent_links', many=True, read_only=True)
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