from rest_framework import serializers

from project.models import Project


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

