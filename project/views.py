from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404

from project.models import Project, ProjectMember
from project.serializers import ProjectSerializer
from tools.permissions.base import HasWorkspacePermission, HasProjectPermission
from accounts.models import User


class ProjectCreateAPIView(generics.CreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, HasWorkspacePermission]
    required_workspace_permission = "can_create_projects"

    def perform_create(self, serializer):
        project = serializer.save()

        # Добавляем мембера проекта того кто создал.
        ProjectMember.objects.create(
            user=self.request.user,
            project=project,
            is_active=True,
        )


class ProjectListAPIView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(members__user=user).distinct()


class ProjectDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasProjectPermission]

    def get(self, request, project_id: int) -> Response:
        project = get_object_or_404(
            Project.objects.prefetch_related("members__user"),
            id=project_id
        )
        serializer = ProjectSerializer(project)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, project_id: int) -> Response:
        project = get_object_or_404(Project, id=project_id)
        serializer = ProjectSerializer(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
