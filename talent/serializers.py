from rest_framework import serializers
from .models import TalentProfile, Post, PostLike, PostView


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

class PostSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    views_count = serializers.SerializerMethodField()
    class Meta:
        model = Post
        fields = ['id', 'talent', 'content', 'created_at', 'updated_at', 'likes_count', 'views_count']
        read_only_fields = ['id', 'created_at', 'updated_at', 'likes_count', 'views_count']

    def get_likes_count(self, obj):
        return obj.likes.count()
    def get_views_count(self, obj):
        return obj.views.count()

class PostLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostLike
        fields = ['id', 'post', 'user', 'liked_at']
        read_only_fields = ['id', 'liked_at']

class PostViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostView
        fields = ['id', 'post', 'user', 'viewed_at']
        read_only_fields = ['id', 'viewed_at'] 