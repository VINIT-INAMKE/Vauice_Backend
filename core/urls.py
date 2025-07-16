from django.urls import path
from .views import SportsListAPIView, OnboardingStatusAPIView

urlpatterns = [
    path('core/fetch-sports-list/', SportsListAPIView.as_view(), name='fetch-sports-list'),
    path('core/onboarding-status/<int:user_id>/', OnboardingStatusAPIView.as_view(), name='onboarding-status'),
]  