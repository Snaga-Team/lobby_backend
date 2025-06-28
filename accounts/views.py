import random

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.hashers import make_password
from django.template.loader import render_to_string

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User, PasswordResetCode
from accounts.serializers import (
    RegistrationSerializer,
    SetPasswordSerializer,
    ProfileSerializer,
    PasswordResetRequestSerializer,
    PasswordResetCheckSerializer,
    PasswordResetConfirmSerializer,
)

class RegistrationAPIView(APIView):
    """
    API endpoint for user registration.

    Allows any user (authenticated or not) to send a POST request
    with registration data. If the data is valid, a new user is created.

    Methods:
        post(request): Handle registration data and create a new user.
    """

    permission_classes = [AllowAny] 

    def post(self, request, *args, **kwargs):
        """
        Handle POST request to register a new user.

        Args:
            request (Request): The HTTP request with registration data.

        Returns:
            Response: Success message with HTTP 201 status or
                      error details with HTTP 400 status.
        """

        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User registered successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class PasswordResetRequestAPIView(APIView):
    """
    API endpoint to request a password reset.

    Allows a user to request a password reset code, which is sent to their email.

    Methods:
        post(request): Validates email and sends a reset code to the user.
    """

    permission_classes = [AllowAny] 

    def post(self, request):
        """
        Handle POST request to send a password reset code.

        Args:
            request (Request): The HTTP request containing user's email.

        Returns:
            Response: Success message with HTTP 200 status or
                      error details with HTTP 400 status.
        """

        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        user = User.objects.get(email=email)

        code = f"{random.randint(100000, 999999)}"

        PasswordResetCode.objects.filter(user=user).delete()
        PasswordResetCode.objects.create(user=user, code=code)

        html_content = render_to_string(
            "emails/password_reset_email.html",
            {"code": code}
        )

        email_message = EmailMultiAlternatives(
            subject="Password recovery",
            body=f"Your password recovery code: {code}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        email_message.attach_alternative(html_content, "text/html")
        email_message.send()

        return Response(
            {"message": "Password reset code sent to email"},
            status=status.HTTP_200_OK
        )


class PasswordResetCheckAPIView(APIView):
    """
    API endpoint to verify a password reset code.

    Accepts user's email and reset code, validates them, and responds if valid.

    Methods:
        post(request): Validates the provided reset code.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """
        Handle POST request to verify password reset code.

        Args:
            request (Request): The HTTP request containing email and reset code.

        Returns:
            Response: Success message with HTTP 200 if code is valid,
                      or error details with HTTP 400.
        """

        serializer = PasswordResetCheckSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors, 
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"message": "Code is valid"}, 
            status=status.HTTP_200_OK
        )


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
    """
    API endpoint to set a new password after code verification.

    Expects valid email, reset code, and new password.

    Methods:
        post(request): Validates input and sets the new password.
    """

    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        Handle POST request to set a new password.

        Args:
            request (Request): The HTTP request with email, reset code, and new password.

        Returns:
            Response: Success data with HTTP 200 status or error details with HTTP 400.
        """

        serializer = SetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            return Response(
                serializer.validated_data, 
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )


class ProfileAPIView(APIView):
    """
    API endpoint to retrieve and update the authenticated user's profile.

    Methods:
        get(request): Returns the current user's profile data.
        put(request): Partially updates the current user's profile.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Handle GET request to retrieve the user's profile.

        Returns:
            Response: Serialized user data with HTTP 200 status.
        """

        serializer = ProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        """
        Handle PUT request to update the user's profile.

        Allows partial updates of the user object.

        Args:
            request (Request): Contains the updated user data.

        Returns:
            Response: Updated user data with HTTP 200 status,
                      or validation errors with HTTP 400 status.
        """

        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data, 
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )


class UserProfileAPIView(APIView):
    """
    API endpoint to retrieve another user's profile by ID.

    Requires authentication.

    Methods:
        get(request, pk): Returns the profile of the user with the given ID.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """
        Handle GET request to retrieve a user's profile by ID.

        Args:
            request (Request): The HTTP request.
            pk (int): ID of the user whose profile is requested.

        Returns:
            Response: Serialized profile data with HTTP 200 status,
                      or 404 if user is not found.
        """

        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response(
                {"message": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProfileSerializer(user)
        return Response(
            serializer.data, 
            status=status.HTTP_200_OK
        )
