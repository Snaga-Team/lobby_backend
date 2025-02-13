from rest_framework import serializers
from accounts.models import CustomUser
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.tokens import AccessToken

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError("Passwords must match.")
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        return CustomUser.objects.create_user(**validated_data)


class SetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        token = data.get('token')
        password = data.get('password')

        try:
            access_token = AccessToken(token)
            user = CustomUser.objects.get(id=access_token['user_id'])
        except Exception:
            raise serializers.ValidationError({"token": "Invalid or expired token"})

        if not user.is_active:
            user.is_active = True
        user.password = make_password(password)
        user.save()

        return {"message": "Password successfully set"}