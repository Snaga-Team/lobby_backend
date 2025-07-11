from rest_framework import serializers
from workspace.models import Workspace, WorkspaceMember, WorkspaceRole
from accounts.models import User
from accounts.serializers import ProfileSerializer
from tools.email import send_invite_email


class WorkspaceSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.id')
    
    class Meta:
        model = Workspace
        fields = [
            'id', 
            'name', 
            'description',
            'owner', 
            'currency', 
            'avatar_background', 
            'avatar_emoji', 
            'avatar_image', 
            'is_active', 
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated")

        return Workspace.objects.create(owner=request.user, **validated_data)


class RoleSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = WorkspaceRole
        fields = ['id', 'name', 'description', 'settings']
        read_only_fields = ['id']


class RoleSubSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkspaceRole
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']


class MemberSerializer(serializers.ModelSerializer):
    user_info = ProfileSerializer(source="user")
    role_info = RoleSubSerializer(source="role")
    date_joined_to_workspace = serializers.DateTimeField(source="joined_at")

    class Meta:
        model = WorkspaceMember
        fields = ['id', "user_info", 'workspace', 'role_info', 'status', 'hour_rate', 'date_joined_to_workspace', 'is_active']
        read_only_fields = ['id', 'date_joined_to_workspace', "user_info"]


class CreateWorkspaceMemberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    role_id = serializers.IntegerField(write_only=True, required=False)
    role_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = WorkspaceMember
        fields = ['email', 'role_id', 'role_name', 'joined_at']
        read_only_fields = ['joined_at']

    def save(self, **kwargs):
        self._user = kwargs.pop('user', None)
        self._role = kwargs.pop('role', None)
        return super().save(**kwargs)

    def create(self, validated_data):
        email = validated_data.pop('email')
        workspace = self.context.get('workspace')

        user = self._user
        role = self._role

        if not user:
            user = User.objects.create(email=email, is_active=False)
            send_invite_email(user, workspace)

        membership = WorkspaceMember.objects.create(user=user, workspace=workspace, role=role)
        return membership
