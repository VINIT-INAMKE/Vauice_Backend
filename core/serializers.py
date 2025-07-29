from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import TalentPool, MentorTalentSelection, MentorTalentRejection
from talent.models import TalentProfile, Post
from talent.serializers import TalentProfileSerializer, PostSerializer
from mentor.serializers import MentorProfileSerializer

User = get_user_model()


class MentorTalentSelectionSerializer(serializers.ModelSerializer):
    """Serializer for mentor talent selections with nested data"""
    talent_profile = serializers.SerializerMethodField()
    mentor_profile = serializers.SerializerMethodField()
    posts = serializers.SerializerMethodField()
    chat_room_id = serializers.SerializerMethodField()
    can_chat = serializers.SerializerMethodField()
    
    class Meta:
        model = MentorTalentSelection
        fields = [
            'id', 'mentor', 'talent', 'selected_at',
            'talent_profile', 'mentor_profile', 'posts', 
            'chat_room_id', 'can_chat'
        ]
        read_only_fields = ['id', 'selected_at']
    
    def get_talent_profile(self, obj):
        """Get talent profile data"""
        try:
            return TalentProfileSerializer(obj.talent.talent_profile).data
        except TalentProfile.DoesNotExist:
            return None
    
    def get_mentor_profile(self, obj):
        """Get mentor profile data"""
        try:
            return MentorProfileSerializer(obj.mentor.mentor_profile).data
        except:
            return None
    
    def get_posts(self, obj):
        """Get talent's posts"""
        try:
            posts = Post.objects.filter(talent=obj.talent.talent_profile)
            return PostSerializer(posts, many=True).data
        except:
            return []
    
    def get_chat_room_id(self, obj):
        """Get chat room ID if exists"""
        try:
            from chat.models import ChatRoom
            chat_room = ChatRoom.objects.filter(
                room_type='private',
                participants=obj.mentor
            ).filter(
                participants=obj.talent
            ).first()
            return str(chat_room.id) if chat_room else None
        except:
            return None
    
    def get_can_chat(self, obj):
        """Check if chat is available"""
        return self.get_chat_room_id(obj) is not None


class MentorTalentRejectionSerializer(serializers.ModelSerializer):
    """Serializer for mentor talent rejections with nested data"""
    talent_profile = serializers.SerializerMethodField()
    mentor_profile = serializers.SerializerMethodField()
    posts = serializers.SerializerMethodField()
    
    class Meta:
        model = MentorTalentRejection
        fields = [
            'id', 'mentor', 'talent', 'rejected_at',
            'talent_profile', 'mentor_profile', 'posts'
        ]
        read_only_fields = ['id', 'rejected_at']
    
    def get_talent_profile(self, obj):
        """Get talent profile data"""
        try:
            return TalentProfileSerializer(obj.talent.talent_profile).data
        except TalentProfile.DoesNotExist:
            return None
    
    def get_mentor_profile(self, obj):
        """Get mentor profile data"""
        try:
            return MentorProfileSerializer(obj.mentor.mentor_profile).data
        except:
            return None
    
    def get_posts(self, obj):
        """Get talent's posts"""
        try:
            posts = Post.objects.filter(talent=obj.talent.talent_profile)
            return PostSerializer(posts, many=True).data
        except:
            return []


class MentorTalentSelectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating mentor talent selections"""
    
    class Meta:
        model = MentorTalentSelection
        fields = ['mentor', 'talent']
    
    def create(self, validated_data):
        """Create or get existing selection"""
        selection, created = MentorTalentSelection.objects.get_or_create(
            mentor=validated_data['mentor'],
            talent=validated_data['talent']
        )
        return selection


class MentorTalentRejectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating mentor talent rejections"""
    
    class Meta:
        model = MentorTalentRejection
        fields = ['mentor', 'talent']
    
    def create(self, validated_data):
        """Create or get existing rejection"""
        rejection, created = MentorTalentRejection.objects.get_or_create(
            mentor=validated_data['mentor'],
            talent=validated_data['talent']
        )
        return rejection


class TalentPoolSerializer(serializers.ModelSerializer):
    """Serializer for talent pool entries"""
    mentor_profile = serializers.SerializerMethodField()
    talent_profile = serializers.SerializerMethodField()
    
    class Meta:
        model = TalentPool
        fields = ['id', 'mentor', 'talent', 'added_at', 'mentor_profile', 'talent_profile']
        read_only_fields = ['id', 'added_at']
    
    def get_mentor_profile(self, obj):
        """Get mentor profile data"""
        try:
            return MentorProfileSerializer(obj.mentor.mentor_profile).data
        except:
            return None
    
    def get_talent_profile(self, obj):
        """Get talent profile data"""
        try:
            return TalentProfileSerializer(obj.talent.talent_profile).data
        except:
            return None