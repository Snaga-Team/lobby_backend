from rest_framework import serializers
from accounts.models import CustomUser, PasswordResetCode
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
    

class ProfileSerializer(serializers.ModelSerializer):
    date_joined_to_system = serializers.DateTimeField(source="date_joined", format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'avatar_background', 
            'avatar_emoji', 'avatar_image' , 'is_active', 'is_staff', 
            'date_joined_to_system',
        ]
        read_only_fields = ['id', 'email', 'date_joined_to_system', 'is_staff']

    def get_avatar_image(self, obj):
        """Returns the full URL for the avatar image if it is loaded."""
        request = self.context.get('request')
        if obj.avatar_image:
            return request.build_absolute_uri(obj.avatar_image.url) if request else obj.avatar_image.url
        return None


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class PasswordResetCheckSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data.get("email")
        code = data.get("code")

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({"email": "User not found."})

        try:
            reset_code = PasswordResetCode.objects.get(user=user, code=code)
        except PasswordResetCode.DoesNotExist:
            raise serializers.ValidationError({"code": "Invalid code."})

        if reset_code.is_expired():
            raise serializers.ValidationError({"code": "Code expired."})

        data["user"] = user
        data["reset_code"] = reset_code
        return data


class PasswordResetConfirmSerializer(PasswordResetCheckSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        data = super().validate(data)

        if "password" not in data:
            raise serializers.ValidationError({"password": "Password is required."})

        return data
