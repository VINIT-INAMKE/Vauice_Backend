import random
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import User
from .serializers import (
    MyTokenObtainPairSerializer, RegisterSerializer, UserSerializer, 
    ChangePasswordSerializer, CheckUsernameSerializer, CheckEmailSerializer
)
from .utils import validate_avatar_file, send_password_reset_email


def generate_random_otp(length=7):
    """Generate a random OTP of specified length"""
    otp = ''.join([str(random.randint(0, 9)) for _ in range(length)])
    return otp


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        # Update refresh token in database
        if response.status_code == 200:
            # Get user from the request data
            email = request.data.get('email')
            if email:
                try:
                    user = User.objects.get(email=email)
                    if hasattr(response, 'data') and 'refresh' in response.data:
                        user.refresh_token = response.data['refresh']
                        user.save()
                except User.DoesNotExist:
                    pass
        
        return response


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate OTP for verification (optional)
        otp = generate_random_otp()
        user.otp = otp
        user.save()
        
        # Return user data without sensitive information
        user_data = UserSerializer(user).data
        
        return Response({
            'message': 'User registered successfully!',
            'user': user_data,
            'otp': otp  # In production, send this via email/SMS
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_object(self):
        # Check if this is a schema generation request
        if getattr(self, 'swagger_fake_view', False):
            # Return empty user for schema generation
            from django.contrib.auth.models import User
            return User()
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': 'Password changed successfully!'
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Clear refresh token
            user = request.user
            user.refresh_token = None
            user.save()
            
            return Response({
                'message': 'Logged out successfully!'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Logout failed'
            }, status=status.HTTP_400_BAD_REQUEST)


class CheckUsernameView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = CheckUsernameSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        username = serializer.validated_data['username']
        exists = User.objects.filter(username=username).exists()
        
        return Response({
            'username': username,
            'available': not exists,
            'message': 'Username is available' if not exists else 'Username already exists'
        })


class CheckEmailView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = CheckEmailSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        exists = User.objects.filter(email=email).exists()
        
        return Response({
            'email': email,
            'available': not exists,
            'message': 'Email is available' if not exists else 'Email already exists'
        })


class PasswordResetEmailVerifyAPIView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer
    
    def get_object(self):
        email = self.kwargs['email'] 

        user = User.objects.filter(email=email).first()

        if user:
            # Generate OTP for password reset
            otp = generate_random_otp()
            user.otp = otp
            user.save()

            # Send email using SendGrid utility
            success = send_password_reset_email(user, otp)
            
            if success:
                print("Password reset OTP sent successfully ======", otp)
            else:
                print("Failed to send password reset email")
        return user


class PasswordChangeAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        otp = request.data.get('otp')
        password = request.data.get('password')

        if not email or not otp or not password:
            return Response({
                "message": "Email, OTP, and password are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email, otp=otp)
            if user:
                user.set_password(password)
                # Clear OTP after successful password change
                user.otp = ""
                user.save()

                return Response({"message": "Password Changed Successfully"}, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({"message": "Invalid OTP or User Does Not Exist"}, status=status.HTTP_404_NOT_FOUND)



