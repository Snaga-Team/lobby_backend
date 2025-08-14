from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404

from project.models import Project, ProjectMember
from project.serializers import (
    ProjectSerializer, 
    MemberSerializer, 
    CreateProjectMemberSerializer
)
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
        serializer.is_valid(raise_exception=True)
        
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

class AddProjectMemberAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasProjectPermission]
    required_project_permission = "can_invite_users_to_project"

    def post(self, request, project_id):
        # !!! Если пользователь уже был мембером, то деактивировав его мы не сможем его активировать снова. !!!

        project = (
            Project.objects
            .filter(id=project_id)
            .prefetch_related("members__user")
            .first()
        )
        if not project:
            return Response(
                {"detail": "Project is not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_member_email = request.data.get("email")
        if not new_member_email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        new_member_user = User.objects.filter(email=new_member_email).first()
        
        if new_member_user:
            is_already_member = any(
                member.user_id == new_member_user.id for member in project.members.all()
            )
            if is_already_member:
                return Response(
                    {"detail": "User is already a member of this project."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response({"detail": "User is not found"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = CreateProjectMemberSerializer(
            data=request.data, 
            context={'project': project}
        )
        serializer.is_valid(raise_exception=True)
        member = serializer.save(user=new_member_user)

        response_serializer = MemberSerializer(member)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
