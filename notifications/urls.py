from django.urls import path
from .views import (
    NotificationListView,
    NotificationDetailView,
    MarkAllAsReadView,
    UnreadNotificationsCountView
)

urlpatterns = [
    path('', NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('mark-all-read/', MarkAllAsReadView.as_view(), name='mark-all-read'),
    path('unread-count/', UnreadNotificationsCountView.as_view(), name='unread-count'),
]
