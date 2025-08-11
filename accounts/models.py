from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from tools.validators import validate_hex_color
from typing import Any


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
