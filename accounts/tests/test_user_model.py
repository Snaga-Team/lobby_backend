from django.test import TestCase
from django.core.exceptions import ValidationError
from accounts.models import User


class UserModelTest(TestCase):

    def test_str_representation_returns_email(self):
        user = User.objects.create_user(email='a@example.com', password='123')
        self.assertEqual(str(user), 'a@example.com')

    def test_custom_avatar_emoji_is_saved(self):
        user = User.objects.create_user(email='emoji@example.com', password='123', avatar_emoji='🐍')
        self.assertEqual(user.avatar_emoji, '🐍')

    def test_default_avatar_emoji_is_used(self):
        user = User.objects.create_user(email='default@example.com', password='123')
        self.assertEqual(user.avatar_emoji, '🚀')

    def test_valid_hex_background_passes_validation(self):
        user = User(email='valid@example.com', password='123', avatar_background='#1A2B3C')
        try:
            user.full_clean()
        except ValidationError:
            self.fail("Valid HEX color raised ValidationError")

    def test_invalid_hex_background_raises_validation_error(self):
        user = User(email='invalid@example.com', password='123' , avatar_background='123456')
        with self.assertRaises(ValidationError):
            user.full_clean()