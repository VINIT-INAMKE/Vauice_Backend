"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


schema_view = get_schema_view(
   openapi.Info(
      title="Vauice Sports App Backend APIs",
      default_version='v1',
      description="""
      This is the API documentation for the Vauice Sports App backend. 
      
      The Vauice platform connects Talents and Mentors in the sports industry, enabling profile building, media uploads, real-time chat, and a unique matching system. 
      
      Features include:
      - Custom user types (Talent, Mentor, Admin)
      - Instagram-style Talent profiles
      - Bumble-style Mentor interface
      - Real-time chat and notifications
      - JWT authentication
      - Cloudinary media storage
      - Admin dashboard for company employees
      """,
      terms_of_service="https://vauice.com/terms/",
      contact=openapi.Contact(email="support@vauice.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('swagger<format>/', schema_view.with_ui(cache_timeout=0), name='schema-json'),
    path('', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('admin/', admin.site.urls),
    path("api/v1/", include("userauths.urls")),
    path("api/v1/", include("core.urls")),
    path("api/v1/", include("mentor.urls")),
    path("api/v1/", include("talent.urls")),
    path("api/v1/chat/", include("chat.urls")),
    path("api/v1/notifications/", include("notifications.urls")),

    path("ping/", lambda request: HttpResponse("pong"))
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
