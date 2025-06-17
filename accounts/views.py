from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.serializers import (
    RegistrationSerializer, SetPasswordSerializer, 
    ProfileSerializer, PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer, PasswordResetCheckSerializer
)
from accounts.models import User, PasswordResetCode
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.hashers import make_password
from django.template.loader import render_to_string
from django.conf import settings
import random


class RegistrationAPIView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request, *args, **kwargs):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class PasswordResetRequestAPIView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        user = User.objects.get(email=email)

        code = f"{random.randint(100000, 999999)}"

        PasswordResetCode.objects.filter(user=user).delete()

        reset_code = PasswordResetCode.objects.create(user=user, code=code)

        html_content = render_to_string("emails/password_reset_email.html", {"code": code})

        email_message = EmailMultiAlternatives(
            subject="Password recovery",
            body=f"Your password recovery code: {code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send()

        return Response({"message": "Password reset code sent to email"}, status=status.HTTP_200_OK)


class PasswordResetCheckAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetCheckSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Code is valid"}, status=status.HTTP_200_OK)


class PasswordResetConfirmAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]
        reset_code = serializer.validated_data["reset_code"]
        new_password = serializer.validated_data["password"]

        user.password = make_password(new_password)
        user.save()

        reset_code.delete()

        return Response({"message": "Password successfully reset"}, status=status.HTTP_200_OK)


class SetPasswordAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    def put(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProfileSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
