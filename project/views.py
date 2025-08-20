from typing import Optional, Tuple

from rest_framework.views import APIView
from rest_framework.response import Response
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


class BaseToggleProjectMemberAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasProjectPermission]
    # Перенастроить права, пока разрешаем всем кто имеет право на 
    # создание юзеров, деактиивировать их. 
    # Потом поменять на права "can_deactivate_users"
    required_workspace_permission = "can_invite_users_to_project"

    is_active_target: bool = None
    action_word: str = ""

    def patch(self, request, project_id):
        project = Project.objects.select_related("owner", "workspace").get(id=project_id)
        if not project:
            return Response({"detail": "Project is not found"}, status=status.HTTP_400_BAD_REQUEST)

        user_id = request.data.get("user_id")
        email = request.data.get("email")

        if sum(bool(x) for x in [user_id, email]) != 1:
            return Response(
                {"detail": "You must provide exactly one of: user_id or email."},
                status=status.HTTP_400_BAD_REQUEST
            )

        target_user = User.objects.filter(id=user_id).first() if user_id else User.objects.filter(email=email).first()

        if not target_user:
            return Response({"detail": "User is not found."}, status=status.HTTP_400_BAD_REQUEST)

        target_member = ProjectMember.objects.filter(project=project, user=target_user).first()

        if not target_member:
            return Response({"detail": "User is not member in this project."}, status=status.HTTP_400_BAD_REQUEST)

        if target_member.is_active == self.is_active_target:
            return Response(
                {"detail": f"User is already {self.action_word}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        target_member.is_active = self.is_active_target
        target_member.save(update_fields=["is_active"])

        serializer = MemberSerializer(target_member)

        return Response(
            {
                "message": f"User has been {self.action_word}.",
                "member": serializer.data
            },
            status=status.HTTP_200_OK
        )


class DeactivateProjectMemberAPIView(BaseToggleProjectMemberAPIView):
    """
    API endpoint to deactivate a Project member.
    """
    is_active_target = False
    action_word = "deactivated"


class ActivateProjectMemberAPIView(BaseToggleProjectMemberAPIView):
    """
    API endpoint to activate a Project member.
    """
    is_active_target = True
    action_word = "activated"


class ProjectMembersListAPIView(generics.ListAPIView):
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        project_id = self.kwargs.get("project_id")
        return ProjectMember.objects.filter(project_id=project_id)


class BaseToggleProjectActivationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasProjectPermission]
    required_workspace_permission = "can_delete_projects"

    is_active_target: bool = None
    action_word: str = ""

    def patch(self, request, project_id):
        project = Project.objects.select_related("owner", "workspace").get(id=project_id)
        if not project:
            return Response({"detail": "Project is not found"}, status=status.HTTP_400_BAD_REQUEST)

        if project.is_active == self.is_active_target:
            return Response(
                {"detail": f"Project is already {self.action_word}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        project.is_active = self.is_active_target
        project.save(update_fields=["is_active"])

        serializer = ProjectSerializer(project)

        return Response(
            {
                "message": f"Project has been {self.action_word}.",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )


class DeactivateProjectAPIView(BaseToggleProjectActivationAPIView):
    """
    API endpoint to deactivate a Project.
    """
    is_active_target = False
    action_word = "deactivated"


class ActivateProjectAPIView(BaseToggleProjectActivationAPIView):
    """
    API endpoint to activate a Project.
    """
    is_active_target = True
    action_word = "activated"


class ChangeProjectOwnerAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, HasProjectPermission]
    # пока могут только владельцы могут менять владельца проекта
    required_project_permission = "can_change_project_owner"

    @staticmethod
    def get_user_and_member(
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        member_id: Optional[int] = None,
        project: object = None
    ) -> Tuple[Optional[User], Optional[ProjectMember], Optional[str]]:
        """
        Returns a tuple (user, member, error_message) based on the provided input.

        If:
        - member_id is provided: searches for the project member directly.
        - email or user_id is provided: first searches for the user, then checks if they are a member of the project.

        :param user_id: ID of the user
        :param email: Email of the user
        :param member_id: ID of the ProjectMember
        :param project: Project object
        :return: (User | None, ProjectMember | None, error_message | None)
        """

        if member_id:
            member = ProjectMember.objects.filter(id=member_id, project=project).select_related("user").first()
            if not member:
                return None, None, "The specified user was found, but they are not a member of this project."
            return member.user, member, None

        if email:
            user = User.objects.filter(email=email).first()
        elif user_id:
            user = User.objects.filter(id=user_id).first()

        if not user:
            return None, None, "User not found."

        member = ProjectMember.objects.filter(user=user, project=project).select_related("user").first()
        if not member:
            return user, None, "The specified user was found, but they are not a member of this project."

        return user, member, None

    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)

        new_owner_id = request.data.get("new_owner_id")
        new_owner_email = request.data.get("new_owner_email")
        new_member_id = request.data.get("new_member_id")

        provided = [new_owner_id, new_owner_email, new_member_id]
        if sum(bool(x) for x in provided) != 1:
            return Response(
                {"detail": "You must provide exactly one of: new_owner_id, new_owner_email, or new_member_id."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user, member, error = self.get_user_and_member(
            user_id=new_owner_id if new_owner_id else None,
            email=new_owner_email if new_owner_email else None,
            member_id=new_member_id if new_member_id else None, 
            project=project
        )

        if error:
            return Response({"detail": error}, status.HTTP_400_BAD_REQUEST)

        project.owner = user
        project.save(update_fields=["owner"])

        serializer = ProjectSerializer(project)
        return Response(serializer.data, status=status.HTTP_200_OK)
