from rest_framework import serializers
from workspace.models import Workspace, WorkspaceMembership, WorkspaceRole
from accounts.models import CustomUser


class WorkspaceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Workspace
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated")

        return Workspace.objects.create(owner=request.user, **validated_data)
    

class WorkspaceMembershipSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    role = serializers.PrimaryKeyRelatedField(queryset=WorkspaceRole.objects.all(), required=False, allow_null=True)

    class Meta:
        model = WorkspaceMembership
        fields = ['email', 'role', 'joined_at']
        read_only_fields = ['joined_at']

    def validate(self, data):
        """
        Проверяем, что пользователь не является владельцем или уже не добавлен в workspace.
        """
        email = data.get('email')
        workspace = self.context.get('workspace')
        
        if not workspace:
            raise serializers.ValidationError({"workspace": "Workspace is required."})

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            user = None  # Позже отправим письмо

        if user:
            if user == workspace.owner:
                raise serializers.ValidationError("Owner cannot be added as a member.")
            if WorkspaceMembership.objects.filter(workspace=workspace, user=user).exists():
                raise serializers.ValidationError("User is already a member.")

        data['user'] = user
        return data

    def create(self, validated_data):
        email = validated_data.pop('email')
        workspace = self.context.get('workspace')
        role = validated_data.pop('role', None)

        user = validated_data.get('user')

        # Если пользователя нет, отправляем приглашение по email
        if not user:
            from django.core.mail import send_mail
            send_mail(
                subject="Приглашение в рабочее пространство",
                message=f"Вас пригласили в workspace {workspace.name}. Пройдите регистрацию.",
                from_email="snagadevteam@gmail.com",
                recipient_list=[email],
                fail_silently=False,
            )
            return {"message": "Invitation email sent"}

        membership = WorkspaceMembership.objects.create(user=user, workspace=workspace, role=role)
        return membership