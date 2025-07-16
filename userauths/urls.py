from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'userauths'

urlpatterns = [
    # Authentication endpoints
    path("user/token/", views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path("user/token/refresh/", TokenRefreshView.as_view(), name='token_refresh'),
    path("user/register/", views.RegisterView.as_view(), name='register'),
    path("user/logout/", views.LogoutView.as_view(), name='logout'),
    path("user/change-password/", views.ChangePasswordView.as_view(), name='change_password'),
    path("user/profile/", views.UserProfileView.as_view(), name='user_profile'),
    

    # Password reset endpoints
    path("user/password-reset/<str:email>/", views.PasswordResetEmailVerifyAPIView.as_view(), name='password_reset_email'),
    path("user/password-change/", views.PasswordChangeAPIView.as_view(), name='password_change'),
    
    # Validation endpoints
    path("user/check-username/", views.CheckUsernameView.as_view(), name='check_username'),
    path("user/check-email/", views.CheckEmailView.as_view(), name='check_email'),
] 