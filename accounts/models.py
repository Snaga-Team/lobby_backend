from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError
import re
import uuid
from django.utils.timezone import now
from django.db import models


def validate_hex_color(value):
    """Checks that the string is a valid HEX code (e.g. #ffffff)."""
    if not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', value):
        raise ValidationError("Invalid HEX color code.")


class UserManager(BaseUserManager):
    """Mansger for custom user model/"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email address must be specified")
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if not extra_fields.get('is_staff'):
            raise ValueError("Superuser must contain is_staff=True.")
        if not extra_fields.get('is_superuser'):
            raise ValueError("Superuser must contain is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model."""
    
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    avatar_background = models.CharField(
        max_length=7, 
        default="#ffffff", 
        validators=[validate_hex_color], 
        null=True, blank=True
    )
    avatar_emoji = models.CharField(max_length=3, default="👤")
    avatar_image = models.ImageField(
        upload_to="avatars/", 
        null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Join with custom manager
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email
    

class PasswordResetCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_codes")
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True)

    def is_expired(self):
        """Code is avalible 10 min"""
        return (now() - self.created_at).total_seconds() > 600  # 600 sec = 10 min
