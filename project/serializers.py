from rest_framework import serializers

from project.models import Project, ProjectMember
from accounts.serializers import ProfileSerializer


class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.id')
 
    class Meta:
        model = Project
        fields = [
            'id', 
            'name', 
            'key', 
            'description',
            'owner', 
            'workspace', 
            'avatar_background', 
            'avatar_emoji', 
            'avatar_image',
            'is_public', 
            'is_billable', 
            'is_active', 
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner']

    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated")

        return Project.objects.create(owner=request.user, **validated_data)


class MemberSerializer(serializers.ModelSerializer):
    user_info = ProfileSerializer(source="user")
    date_joined_to_project = serializers.DateTimeField(
        source="created_at",
        format="%Y-%m-%d %H:%M:%S", 
        read_only=True
    )
    date_update_in_project = serializers.DateTimeField(
        source="updated_at",
        format="%Y-%m-%d %H:%M:%S", 
        read_only=True
    )

    class Meta:
        model = ProjectMember
        fields = ['id', "user_info", 'project', 'is_active', 'date_joined_to_project', 'date_update_in_project']
        read_only_fields = ['id', 'date_joined_to_project', 'date_update_in_project', "user_info"]


class CreateProjectMemberSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)

    class Meta:
        model = ProjectMember
        fields = ['email', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def save(self, **kwargs):
        self._user = kwargs.pop('user', None)
        return super().save(**kwargs)

    def create(self, validated_data):
        email = validated_data.pop('email')
        project = self.context.get('project')

        user = self._user
        member = ProjectMember.objects.create(user=user, project=project)
        return member