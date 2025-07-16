from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User
from talent.models import TalentProfile
from mentor.models import MentorProfile


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Include only the requested fields
        token['username'] = user.username
        token['email'] = user.email
        token['user_type'] = user.user_type
        token['date_joined'] = str(user.date_joined)
        token['last_login'] = str(user.last_login) if user.last_login else None
        # onboarding_done removed from token
        return token


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        help_text="Password must be at least 8 characters long"
    )
    password2 = serializers.CharField(
        write_only=True, 
        required=True,
        help_text="Confirm password"
    )
    
    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'firstname', 'lastname', 
                 'gender', 'age', 'user_type', 'phone_number')
        extra_kwargs = {
            'firstname': {'required': True, 'help_text': 'User first name'},
            'lastname': {'required': True, 'help_text': 'User last name'},
            'email': {'required': True, 'help_text': 'User email address'},
            'username': {'required': True, 'help_text': 'Unique username'},
            'gender': {'help_text': 'Gender: male, female, or other'},
            'age': {'help_text': 'User age in years'},
            'user_type': {'required': True, 'help_text': 'User type: talent or mentor'},
            'phone_number': {'help_text': 'Phone number in format: +999999999'},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Check if username is unique
        username = attrs.get('username')
        if username and User.objects.filter(username=username).exists():
            raise serializers.ValidationError({"username": "Username already exists."})
        
        # Check if email is unique
        email = attrs.get('email')
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "Email already exists."})
        
        # Prevent admin registration through API
        user_type = attrs.get('user_type')
        if user_type == 'admin':
            raise serializers.ValidationError({
                "user_type": "Admin users cannot be registered through this API. Please contact the system administrator."
            })
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        # Create profile based on user_type
        if user.user_type == 'talent':
            TalentProfile.objects.create(user=user)
        elif user.user_type == 'mentor':
            MentorProfile.objects.create(user=user)
        return user


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'firstname', 'lastname', 'gender', 'age', 
                 'user_type', 'phone_number', 'full_name', 'is_superuser', 
                 'is_staff', 'is_active', 'date_joined', 'last_login', 'avatar_url')
        read_only_fields = ('id', 'is_superuser', 'is_staff', 'is_active', 'date_joined', 'last_login')
        extra_kwargs = {
            'username': {'help_text': 'Unique username'},
            'email': {'help_text': 'User email address'},
            'firstname': {'help_text': 'User first name'},
            'lastname': {'help_text': 'User last name'},
            'gender': {'help_text': 'Gender: male, female, or other'},
            'age': {'help_text': 'User age in years'},
            'user_type': {'help_text': 'User type: talent or mentor'},
            'phone_number': {'help_text': 'Phone number'},
            'full_name': {'help_text': 'Full name of the user'},
        }
    
    def get_avatar_url(self, obj):
        return obj.get_avatar_url()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct.")
        return value


class CheckUsernameSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=True,
        help_text="Username to check for availability"
    )


class CheckEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        help_text="Email to check for availability"
    ) 