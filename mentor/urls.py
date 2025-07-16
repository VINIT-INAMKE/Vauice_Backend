from django.urls import path
from .views import MentorOnboardingProfileSaveAPIView, MentorProfileUpdateAPIView

urlpatterns = [
    path('mentor/onboarding-profilesave/', MentorOnboardingProfileSaveAPIView.as_view(), name='mentor-onboarding-profilesave'),
    path('mentor/profile/', MentorProfileUpdateAPIView.as_view(), name='mentor-profile-update'),
] 