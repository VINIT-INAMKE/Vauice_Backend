from django.urls import path
from .views import TalentOnboardingProfileSaveAPIView, TalentProfileUpdateAPIView

urlpatterns = [
    path('talent/onboarding-profilesave/', TalentOnboardingProfileSaveAPIView.as_view(), name='talent-onboarding-profilesave'),
    path('talent/profile/', TalentProfileUpdateAPIView.as_view(), name='talent-profile-update'),
] 