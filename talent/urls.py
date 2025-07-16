from django.urls import path
from .views import TalentOnboardingProfileSaveAPIView

urlpatterns = [
    path('talent/onboarding-profilesave/', TalentOnboardingProfileSaveAPIView.as_view(), name='talent-onboarding-profilesave'),
] 