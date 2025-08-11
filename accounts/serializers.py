from typing import Any, Dict

from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import AccessToken

from core.services.auth_codes import peek_code

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    This serializer handles user creation by validating password confirmation,
    checking password strength using Django's built-in password validators,
    and ensuring the email is unique.
    """

    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=User.objects.all())],)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['email', 'password', 'password2', 'first_name', 'last_name', 'bio']

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that passwords match and meet strength requirements.

        Args:
            data: The incoming validated data.

        Returns:
            The validated data dictionary.

        Raises:
            ValidationError: If passwords do not match or are too weak.
        """

        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords must match.")
        
        # Validate password strength using Django's built-in system
        validate_password(data['password'])

        return data

    def create(self, validated_data: Dict[str, Any]):
        """
        Create a new user instance with a hashed password.

        Args:
            validated_data: Cleaned and validated data from the request.

        Returns:
            A new User object.
        """

        validated_data.pop('password2')
        return User.objects.create_user(**validated_data)


class SetPasswordSerializer(serializers.Serializer):
    """
    Serializer for setting a new password using a JWT access token.

    This serializer:
    - Verifies the token is valid and corresponds to an existing user.
    - Sets a new password (with hashing) for the user.
    - Optionally activates the user account if it was inactive.
    """

    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        """
        Validate the token and set the new password.

        Args:
            data: Dictionary with 'token' and 'password' fields.

        Returns:
            A message indicating success.

        Raises:
            ValidationError: If the token is invalid or user does not exist.
        """

        token = data.get('token')
        password = data.get('password')

        try:
            access_token = AccessToken(token)
            user = User.objects.get(id=access_token['user_id'])
        except Exception:
            raise serializers.ValidationError({"token": "Invalid or expired token"})

        # Activate user if not active
        if not user.is_active:
            user.is_active = True

        # Set hashed password
        user.password = make_password(password)
        user.save()

        return {"message": "Password successfully set"}


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving user profile data.

    Includes personal information, avatar fields, and account metadata
    such as staff status and date joined.
    """

    date_joined_to_system = serializers.DateTimeField(
        source="date_joined", 
        format="%Y-%m-%d %H:%M:%S", 
        read_only=True
    )
    avatar_image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'bio', 
            'avatar_background', 'avatar_emoji', 'avatar_image' , 
            'is_active', 'is_staff', 'date_joined_to_system',
        ]
        read_only_fields = ['id', 'email', 'date_joined_to_system', 'is_staff']

    def get_avatar_image(self, obj):
        """
        Return the absolute URL of the user's avatar image if it exists.

        Args:
            obj: The user instance being serialized.

        Returns:
            Full URL to the avatar image or None.
        """

        request = self.context.get('request')
        if obj.avatar_image:
            return request.build_absolute_uri(obj.avatar_image.url) if request else obj.avatar_image.url
        return None


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset via email.

    Validates that the provided email exists in the system.
    """

    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        """
        Check if a user with the provided email exists.

        Args:
            value: The email entered by the user.

        Returns:
            The validated email address.

        Raises:
            serializers.ValidationError: If the email is not associated with any user.
        """

        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class PasswordResetCheckSerializer(serializers.Serializer):
    """
    Serializer for checking a password reset confirmation code.

    Verifies that the user exists, the reset code is correct and not expired.
    Attaches the validated user and reset code to the validated data.
    """

    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that the email and code match a valid, unexpired password reset request.

        Args:
            data: Dictionary containing 'email' and 'code'.

        Returns:
            The validated data with attached 'user' and 'reset_code'.

        Raises:
            ValidationError: If the user is not found, the code is invalid or expired.
        """

        email = data.get("email")
        code = data.get("code")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User not found."})

        if not peek_code(user.id, code):
            raise serializers.ValidationError({"code": "Invalid or expired code."})

        data["user"] = user
        return data


class PasswordResetConfirmSerializer(PasswordResetCheckSerializer):
    """
    Serializer for confirming password reset by providing a new password.

    Inherits email and code validation from PasswordResetCheckSerializer,
    and adds validation for the new password field.
    """

    password: serializers.CharField = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"}
    )

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate email, code, and presence of password.

        Args:
            data: The input data including email, code, and password.

        Returns:
            The validated data with user, reset_code, and password.

        Raises:
            ValidationError: If password is missing or other validation fails.
        """

        data = super().validate(data)

        if "password" not in data:
            raise serializers.ValidationError({"password": "Password is required."})

        return data
