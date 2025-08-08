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
    date_joined_to_workspace = serializers.DateTimeField(source="joined_at")

    class Meta:
        model = ProjectMember
        fields = ['id', "user_info", 'project', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', "user_info"]
