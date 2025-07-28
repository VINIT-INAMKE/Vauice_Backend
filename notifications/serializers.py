from rest_framework import serializers
from .models import Notification
from talent.serializers import TalentProfileSerializer
from mentor.serializers import MentorProfileSerializer
from chat.serializers import ChatRoomSerializer, MessageSerializer
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class NotificationSerializer(serializers.ModelSerializer):
    recipient = UserSerializer(read_only=True)
    sender = UserSerializer(read_only=True)
    talent = TalentProfileSerializer(read_only=True)
    mentor = MentorProfileSerializer(read_only=True)
    chat_room = ChatRoomSerializer(read_only=True)
    message = MessageSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['created_at']
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Format the created_at field
        representation['created_at'] = instance.created_at.isoformat()
        return representation
