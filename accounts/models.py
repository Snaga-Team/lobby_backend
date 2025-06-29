from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.timezone import now

import re
import uuid
from typing import Any

def validate_hex_color(value: str) -> None:
    """
    Validates that the given string is a proper HEX color code.

    Accepts:
        - 3-digit (e.g. "#fff")
        - 6-digit (e.g. "#ffffff")

    Args:
        value (str): The value to validate.

    Raises:
        ValidationError: If the value is not a valid HEX color.
    """
    # Must be in other file (ex. validators.py)
    if not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', value):
        raise ValidationError(
            "Invalid HEX color code. Example: #fff or #ffffff.",
            code="invalid_hex"
        )

class UserManager(BaseUserManager):
    """
    Manager for the custom user model using email as the unique identifier.

    Provides helper methods for creating regular users and superusers. Ensures
    email normalization and password hashing, and sets required flags for superusers.

    Methods:
        create_user(email, password=None, **extra_fields):
            Creates and returns a user with the given email and password.
            Raises ValueError if email is not provided.

        create_superuser(email, password=None, **extra_fields):
            Creates and returns a superuser with the given email and password.
            Ensures 'is_staff' and 'is_superuser' are set to True.
    """

    def create_user(self, email: str, password: str | None = None, **extra_fields: Any) -> 'User':
        """
        Creates and returns a regular user with the given email and password.

        Args:
            email (str): The user's email address.
            password (str, optional): The user's password.
            **extra_fields: Additional fields for user creation.

        Raises:
            ValueError: If email is not provided.

        Returns:
            User: The created user instance.
        """

        if not email:
            raise ValueError("Email address must be specified")

        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields: Any) -> 'User':
        """
        Creates and returns a superuser with the given email and password.

        Ensures that is_staff and is_superuser are set to True.

        Args:
            email (str): The superuser's email address.
            password (str, optional): The superuser's password.
            **extra_fields: Additional fields for superuser creation.

        Raises:
            ValueError: If required superuser flags are not set.

        Returns:
            User: The created superuser instance.
        """

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError("Superuser must contain is_staff=True.")
        if not extra_fields.get('is_superuser'):
            raise ValueError("Superuser must contain is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for the system with email-based authentication.

    Users authenticate using their email and password. The profile can be customized
    in one of two ways:
        1. Using an emoji and a background color (stored as a HEX code).
        2. Uploading a profile photo (takes priority over emoji+color).

    Fields:
        email (str): Unique email address used for authentication.
        first_name (str): Optional first name of the user.
        last_name (str): Optional last name of the user.
        bio (str): Optional biography or description for the user.
        avatar_background (str): HEX code for background color behind emoji avatar.
        avatar_emoji (str): Emoji used as a simple profile avatar.
        avatar_image (ImageField): Optional uploaded image as a profile avatar.
        is_active (bool): Indicates whether the user account is active.
        is_staff (bool): Designates whether the user can access the admin site.
        date_joined (datetime): Timestamp when the user registered.

    Manager:
        objects (UserManager): Custom user manager for creating users and superusers.

    Authentication:
        USERNAME_FIELD: Uses 'email' as the unique identifier.
        REQUIRED_FIELDS: Requires 'first_name' and 'last_name' for superusers.

    Returns:
        str: The user's email address.
    """

    email = models.EmailField(verbose_name="Email", unique=True)
    first_name = models.CharField(max_length=150, verbose_name="First Name", blank=True)
    last_name = models.CharField(max_length=150, verbose_name="Last Name", blank=True)
    bio = models.TextField(verbose_name="Bio", blank=True, null=True)
    avatar_background = models.CharField(
        max_length=7,
        verbose_name="Avatar Background",
        default="#ffffff", 
        validators=[validate_hex_color], 
        null=True,
        blank=True
    )
    avatar_emoji = models.CharField(max_length=3, verbose_name="Avatar Emoji", default="🚀")
    avatar_image = models.ImageField(
        upload_to="accounts/", 
        verbose_name="Avatar Image",
        null=True,
        blank=True
    )
    is_active = models.BooleanField(verbose_name="Is Active", default=True)
    is_staff = models.BooleanField(verbose_name="Is Staff", default=False)
    date_joined = models.DateTimeField(verbose_name="Date Joined", auto_now_add=True)

    # Join with custom manager
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self) -> str:
        return self.email
 

class PasswordResetCode(models.Model):
    """
    Model for one-time password reset or profile activation code.

    This model is used to:
        - Send a 6-digit code to the user for password reset or account activation.
        - Generate a unique token (UUID) that can be used to create an activation URL.

    Fields:
        user (User): The user associated with the reset code.
        code (str): A 6-digit numeric code sent to the user.
        created_at (datetime): Timestamp of when the code was created.
        token (UUID): A unique token used for activation links.

    Methods:
        is_expired():
            Checks if the code has expired. A code is valid for 10 minutes (600 seconds).
            Returns True if expired, otherwise False.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_codes", verbose_name="User")
    code = models.CharField(max_length=6, verbose_name="Reset Code")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    token = models.UUIDField(default=uuid.uuid4, unique=True, verbose_name="Activation Token")

    def is_expired(self) -> bool:
        """
        Checks whether the code is expired (older than 10 minutes).

        Returns:
            bool: True if expired, otherwise False.
        """
        return (now() - self.created_at).total_seconds() > 600  # 600 sec = 10 min

    def __str__(self) -> str:
        email = self.user.email
        code = self.code
        return f"ResetCode for {email} ({code})"
