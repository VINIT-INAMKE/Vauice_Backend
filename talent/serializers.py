from rest_framework import serializers
from .models import TalentProfile, TalentPortfolio

class TalentPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentPortfolio
        fields = '__all__'
        read_only_fields = ['id', 'talent', 'created_at', 'updated_at']

class TalentProfileSerializer(serializers.ModelSerializer):
    portfolio_items = TalentPortfolioSerializer(many=True, read_only=True)
    class Meta:
        model = TalentProfile
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'portfolio_items']

class TalentOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentProfile
        fields = ['date_of_birth', 'selected_sports', 'social_links']
        extra_kwargs = {
            'date_of_birth': {'help_text': 'Birthdate in YYYY-MM-DD format'},
            'selected_sports': {'help_text': 'List of selected sports (JSON array or object)'},
            'social_links': {'help_text': 'JSON object with keys like facebook, instagram, etc.'},
        } 