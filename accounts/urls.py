from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from accounts.views import (
    RegistrationAPIView, SetPasswordAPIView, 
    ProfileAPIView, UserProfileAPIView,
    PasswordResetRequestAPIView, PasswordResetConfirmAPIView,
    PasswordResetCheckAPIView
)


urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegistrationAPIView.as_view(), name='register'),
    
    path("password-reset/", PasswordResetRequestAPIView.as_view(), name="password-reset"),
    path("password-reset/check/", PasswordResetCheckAPIView.as_view(), name="password-reset-check"),
    path("password-reset/confirm/", PasswordResetConfirmAPIView.as_view(), name="password-reset-confirm"),

    path('set-password/', SetPasswordAPIView.as_view(), name='set-password'),
    path('profile/', ProfileAPIView.as_view(), name='profile'),
    path('user/<int:pk>/', UserProfileAPIView.as_view(), name='user-profile'),
]

