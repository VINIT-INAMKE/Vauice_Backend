from rest_framework import serializers
from .models import TalentProfile, Post, PostLike, PostView
from userauths.serializers import UserSerializer


class TalentProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = TalentProfile
        fields = '__all__'

class TalentOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentProfile
        fields = ['date_of_birth', 'selected_sports', 'social_links', 'city', 'state', 'country']
        extra_kwargs = {
            'date_of_birth': {'help_text': 'Birthdate in YYYY-MM-DD format'},
            'selected_sports': {'help_text': 'List of selected sports (JSON array or object)'},
            'social_links': {'help_text': 'JSON object with keys like facebook, instagram, etc.'},
            'city': {'help_text': 'City of residence'},
            'state': {'help_text': 'State of residence'},
            'country': {'help_text': 'Country of residence'},
        }

class PostSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    views_count = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False, allow_null=True)
    video = serializers.FileField(required=False, allow_null=True)
    caption = serializers.CharField(required=False, allow_blank=True)
    class Meta:
        model = Post
        fields = ['id', 'talent', 'content', 'image', 'video', 'caption', 'created_at', 'updated_at', 'likes_count', 'views_count']
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