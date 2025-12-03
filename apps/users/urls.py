from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import RegisterUser, ChangePasswordView, UserProfile


urlpatterns = [
    #reg
    path('register/', RegisterUser. as_view(), name='register'),
    
    # JJJJJWWWTTTTT
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # prof
    path('profile/', UserProfile.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
]