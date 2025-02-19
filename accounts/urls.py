from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from accounts.views import RegistrationAPIView, SetPasswordAPIView, ProfileAPIView

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegistrationAPIView.as_view(), name='register'),

    path('set-password/', SetPasswordAPIView.as_view(), name='set-password'),
    path('profile/', ProfileAPIView.as_view(), name='profile'),
]

