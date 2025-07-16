from django.urls import path
from .views import MentorOnboardingProfileSaveAPIView

urlpatterns = [
    path('mentor/onboarding-profilesave/', MentorOnboardingProfileSaveAPIView.as_view(), name='mentor-onboarding-profilesave'),
] 