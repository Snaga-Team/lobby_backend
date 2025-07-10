from typing import Optional, Tuple

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from rest_framework import generics, permissions

from django.shortcuts import get_object_or_404
from django.db.models import Q

from workspace.models import Workspace, WorkspaceMember, WorkspaceRole
from workspace.serializers import (
    WorkspaceSerializer, 
    WorkspaceMemberSerializer, 
    RoleSerializer
)
from tools.permissions.base import HasWorkspacePermission
from accounts.models import User


class WorkspaceCreateAPIView(generics.CreateAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        workspace = serializer.save()

        admin_role = WorkspaceRole.objects.filter(name="admin", workspace=workspace).first()
        if not admin_role:
            raise ValueError("Admin role not found in the system.")

        # Выдаем роль админа создателю воркспейса.
        WorkspaceMember.objects.create(
            user=self.request.user,
            workspace=workspace,
            role=admin_role,
            is_active=True,
        )


class WorkspaceListAPIView(generics.ListAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Workspace.objects.filter(member__user=user).distinct()


class WorkspaceRoleListAPIView(generics.ListAPIView):
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        workspace_id = self.kwargs['workspace_id']
        workspace = get_object_or_404(Workspace, id=workspace_id)

        is_owner = workspace.owner == user
        is_member = WorkspaceMember.objects.filter(user=user, workspace=workspace).exists()

        if not (is_owner or is_member):
            raise PermissionDenied("You do not have access to this workspace.")

        return WorkspaceRole.objects.filter(workspace=workspace).distinct()


class AddWorkspaceMemberAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, id=workspace_id)

        if not self.has_permission_to_add(request.user, workspace, request.data):
            return Response({"error": "You do not have permission to add users."}, status=status.HTTP_403_FORBIDDEN)

        serializer = WorkspaceMemberSerializer(
            data=request.data, 
            context={"request": request, "workspace": workspace}
        )
        if serializer.is_valid():
            result = serializer.save()
            return Response({"message": "User added to workspace"} if isinstance(result, WorkspaceMember) else result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def has_permission_to_add(self, user, workspace, request_data):
        """
        Checks whether the user can add participants to `Workspace`
            - The owner can add any users
            - Admin can only add ordinary participants (not other admins)
        """
        if workspace.owner == user:
            return True

        user_membership = WorkspaceMember.objects.filter(user=user, workspace=workspace, role__name="admin").first()
        if user_membership:
            new_role_name = request_data.get("role", "").lower()
            return new_role_name != "admin"
        
        return False


class DeactivateWorkspaceMemberAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, workspace_id):
        workspace = get_object_or_404(
            Workspace.objects.filter(Q(owner=request.user) | Q(memberships__user=request.user)).distinct(),
            id=workspace_id
        )
        
        user_id = request.data.get("user_id")
        email = request.data.get("email")
        if user_id and email:
            return Response({"error": "Provide either user_id or email, not both."}, status=status.HTTP_400_BAD_REQUEST)
        
        if user_id:
            target_membership = get_object_or_404(WorkspaceMember, workspace=workspace, user_id=user_id)
        else:
            target_membership = get_object_or_404(WorkspaceMember, workspace=workspace, user__email=email)

        if not self.has_permission_to_deactivate(request.user, workspace, target_membership):
            return Response({"error": "You do not have permission to deactivate this user."}, status=status.HTTP_403_FORBIDDEN)

        if not target_membership.is_active:
            return Response({"message": "User is already deactivated."}, status=status.HTTP_400_BAD_REQUEST)

        target_membership.is_active = False
        target_membership.save()

        return Response({"message": "User has been deactivated."}, status=status.HTTP_200_OK)

    def has_permission_to_deactivate(self, user, workspace, target_membership):
        """ Checks whether it is possible to deactivate the participant """
        if workspace.owner == user:
            return True

        user_membership = WorkspaceMember.objects.filter(user=user, workspace=workspace).first()
        if user_membership and user_membership.role and user_membership.role.name == "admin":
            # Admin can deactivate only ordinary users (not admins)
            return target_membership.role is None or target_membership.role.name not in ["admin", ]

        return False


class ChangeWorkspaceRoleAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, workspace_id):
        """Changing user roles in the `Workspace`"""
        workspace = get_object_or_404(
            Workspace.objects.filter(Q(owner=request.user) | Q(memberships__user=request.user)).distinct(),
            id=workspace_id
        )
        
        user_id = request.data.get("user_id")
        email = request.data.get("email")
        new_role_name = request.data.get("new_role", "").strip().lower()

        if user_id and email:
            return Response({"error": "Provide either `user_id` or `email`, not both."}, status=status.HTTP_400_BAD_REQUEST)
        if not new_role_name:
            return Response({"error": "`new_role` is required."}, status=status.HTTP_400_BAD_REQUEST)

        if user_id:
            target_membership = get_object_or_404(WorkspaceMember, workspace=workspace, user_id=user_id)
        else:
            target_membership = get_object_or_404(WorkspaceMember, workspace=workspace, user__email=email)

        if not target_membership.is_active:
            return Response({"error": "Cannot change role of a deactivated user."}, status=status.HTTP_400_BAD_REQUEST)

        new_role = get_object_or_404(WorkspaceRole, workspace=workspace, name=new_role_name)

        if not self.has_permission_to_change_role(request.user, workspace, target_membership, new_role_name):
            return Response({"error": "You do not have permission to change this user's role."}, status=status.HTTP_403_FORBIDDEN)

        target_membership.role = new_role
        target_membership.save()

        return Response({"message": f"User's role changed to {new_role_name}."}, status=status.HTTP_200_OK)

    def has_permission_to_change_role(self, user, workspace, target_membership, new_role_name):
        """
        Checks if the user can change the role
            - Owner can assign any roles
            - Admin can only assign `user`, `client`, but not `admin`
        """
        if workspace.owner == user:
            return True

        user_membership = WorkspaceMember.objects.filter(user=user, workspace=workspace, role__name="admin").first()
        if user_membership:
            return not (new_role_name == "admin" or (target_membership.role and target_membership.role.name == "admin"))
        return False


class WorkspaceDetailAPIView(APIView):
    """
    Retrieve or update a specific workspace.

    This view provides two operations:
        - GET: Returns detailed information about a workspace.
          Requires the user to be the owner or a member of the workspace.
        - PUT: Updates workspace details.
          Requires the user to be the owner or have the 'can_edit_workspace' permission in their role settings.

    Permissions:
        - permissions.IsAuthenticated: User must be authenticated.
        - HasWorkspacePermission: Custom permission that checks role-based access in the workspace context.

    Attributes:
        required_workspace_permission (str): Dynamically set per request method
            - "can_view_workspace" for GET
            - "can_edit_workspace" for PUT

    Path parameters:
        workspace_id (int): The ID of the workspace to retrieve or update.

    Responses:
        - 200 OK: Successful retrieval or update
        - 400 Bad Request: Invalid input data during update
        - 403 Forbidden: Access denied due to insufficient permissions
        - 404 Not Found: Workspace does not exist
    """

    permission_classes = [permissions.IsAuthenticated, HasWorkspacePermission]

    def get(self, request, workspace_id: int) -> Response:
        self.required_workspace_permission = "can_view_workspace"
        workspace = get_object_or_404(
            Workspace.objects.prefetch_related("member__user", "member__role"),
            id=workspace_id
        )
        serializer = WorkspaceSerializer(workspace)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, workspace_id: int) -> Response:
        self.required_workspace_permission = "can_edit_workspace"
        workspace = get_object_or_404(Workspace, id=workspace_id)
        serializer = WorkspaceSerializer(workspace, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorkspaceOwnerChangeAPIView(APIView):
    """
    API view for changing the owner of a workspace.

    Allows the current owner to assign a new owner to the workspace
    by providing one of the following: `new_owner_id`, `new_owner_email`,
    or `new_member_id`.

    Only one identifier can be used per request. The new owner must already
    be a member of the workspace. Their role will be updated to "admin" 
    if the transfer is successful.

    Permissions:
        - User must be authenticated.
        - User must have the `owner_member` permission (workspace owner).
    """

    permission_classes = [permissions.IsAuthenticated, HasWorkspacePermission]
    # Валидатор вернет True, если пользователь является владельцем проекта.
    # Настройки "owner_member" не существует и будет проигнорирована валидатором.
    required_workspace_permission = "owner_member"

    @staticmethod
    def get_user_and_member(
        user_id: Optional[int] = None,
        email: Optional[str] = None,
        member_id: Optional[int] = None,
        workspace: object = None
    ) -> Tuple[Optional[User], Optional[WorkspaceMember], Optional[str]]:
        """
        Returns a tuple (user, member, error_message) based on the provided input.

        If:
        - member_id is provided: searches for the workspace member directly.
        - email or user_id is provided: first searches for the user, then checks if they are a member of the workspace.

        :param user_id: ID of the user
        :param email: Email of the user
        :param member_id: ID of the WorkspaceMember
        :param workspace: Workspace object
        :return: (User | None, WorkspaceMember | None, error_message | None)
        """

        if member_id:
            member = WorkspaceMember.objects.filter(id=member_id, workspace=workspace).select_related("user").first()
            if not member:
                return None, None, "The specified user was found, but they are not a member of this workspace."
            return member.user, member, None

        if email:
            user = User.objects.filter(email=email).first()
        elif user_id:
            user = User.objects.filter(id=user_id).first()

        if not user:
            return None, None, "User not found."

        member = WorkspaceMember.objects.filter(user=user, workspace=workspace).select_related("user").first()
        if not member:
            return user, None, "The specified user was found, but they are not a member of this workspace."

        return user, member, None

    def post(self, request, workspace_id):
        """
        Handles POST request to transfer workspace ownership.

        Validates that exactly one identifier is provided (user ID, email, or member ID),
        checks that the user exists and is a member of the workspace, and updates the
        workspace's owner field accordingly. Also assigns the "admin" role to the new owner.

        Returns:
            - 200 OK with updated workspace data on success.
            - 400 BAD REQUEST with an error message if validation fails.
        """

        workspace = Workspace.objects.filter(id=workspace_id).select_related("owner").first()
        if not workspace:
            return Response(
                {"error": "Workspace is not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_owner_id = request.data.get("new_owner_id")
        new_owner_email = request.data.get("new_owner_email")
        new_member_id = request.data.get("new_member_id")

        provided = [new_owner_id, new_owner_email, new_member_id]
        if sum(bool(x) for x in provided) != 1:
            return Response(
                {"error": "You must provide exactly one of: new_owner_id, new_owner_email, or new_member_id."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            admin_role = WorkspaceRole.objects.get(name='admin', workspace=workspace)
        except WorkspaceRole.DoesNotExist:
            return Response({"error": "Admin role not found."}, status.HTTP_400_BAD_REQUEST)

        user, member, error = self.get_user_and_member(
            user_id=new_owner_id if new_owner_id else None,
            email=new_owner_email if new_owner_email else None,
            member_id=new_member_id if new_member_id else None, 
            workspace=workspace
        )

        if error:
            return Response({"error": error}, status.HTTP_400_BAD_REQUEST)

        member.role = admin_role
        member.save(update_fields=["role"])

        workspace.owner = user
        workspace.save(update_fields=["owner"])

        serializer = WorkspaceSerializer(workspace)
        return Response(serializer.data, status=status.HTTP_200_OK)
