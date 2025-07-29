from rest_framework import serializers
from .models import MentorProfile, SelectedTalent, RejectedTalent
from talent.models import TalentProfile, Post
from talent.serializers import TalentProfileSerializer
from userauths.serializers import UserSerializer
from talent.serializers import PostSerializer


class SelectedTalentSerializer(serializers.ModelSerializer):
    talent = serializers.PrimaryKeyRelatedField(queryset=TalentProfile.objects.all())
    class Meta:
        model = SelectedTalent
        fields = ['id', 'talent', 'selected_at']
        read_only_fields = ['id', 'selected_at']

# For ListAvailableTalentsWithPostsAPIView
class TalentWithPostsSerializer(serializers.Serializer):
    talent = TalentProfileSerializer()
    posts = serializers.SerializerMethodField()

    def get_posts(self, obj):
        posts = Post.objects.filter(talent=obj)
        return PostSerializer(posts, many=True).data

# For ListSelectedTalentsAPIView
class SelectedTalentWithPostsSerializer(serializers.Serializer):
    talent = TalentProfileSerializer()
    selected_at = serializers.DateTimeField()
    chat_room_id = serializers.CharField()
    can_chat = serializers.BooleanField()
    posts = serializers.ListField(child=serializers.DictField())

# For ListRejectedTalentsAPIView
class RejectedTalentWithPostsSerializer(serializers.Serializer):
    talent = TalentProfileSerializer()
    rejected_at = serializers.DateTimeField()
    posts = serializers.ListField(child=serializers.DictField())

# For PostLikesCountAPIView and PostViewsCountAPIView
class CountSerializer(serializers.Serializer):
    post_id = serializers.IntegerField()
    count = serializers.IntegerField()

class RejectedTalentSerializer(serializers.ModelSerializer):
    talent = serializers.PrimaryKeyRelatedField(queryset=TalentProfile.objects.all())
    class Meta:
        model = RejectedTalent
        fields = ['id', 'talent', 'rejected_at']
        read_only_fields = ['id', 'rejected_at']

class MentorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = MentorProfile
        exclude = ['selected_talents', 'rejected_talents']
        read_only_fields = ['id', 'user', 'date_of_birth', 'selected_sports', 'created_at', 'updated_at']

class MentorOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MentorProfile
        fields = ['date_of_birth', 'selected_sports', 'social_links', 'city', 'state', 'country']
        extra_kwargs = {
            'date_of_birth': {'help_text': 'Birthdate in YYYY-MM-DD format'},
            'selected_sports': {'help_text': 'List of selected sports (JSON array or object)'},
            'social_links': {'help_text': 'JSON object with keys like facebook, instagram, etc.'},
            'city': {'help_text': 'City of residence'},
            'state': {'help_text': 'State of residence'},
            'country': {'help_text': 'Country of residence'},
        }