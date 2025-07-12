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
    CreateWorkspaceMemberSerializer, 
    RoleSerializer,
    MemberSerializer
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
    

class MembersListAPIView(generics.ListAPIView):
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated, HasWorkspacePermission]
    required_workspace_permission = "can_view_workspace"

    def get_queryset(self):
        workspace_id = self.kwargs['workspace_id']
        get_object_or_404(Workspace, id=workspace_id)
        return WorkspaceMember.objects.filter(workspace_id=workspace_id).distinct()


class WorkspaceRoleListAPIView(generics.ListAPIView):
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated, HasWorkspacePermission]
    required_workspace_permission = "can_view_workspace"

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
    permission_classes = [permissions.IsAuthenticated, HasWorkspacePermission]
    required_workspace_permission = "can_invite_users"

    def post(self, request, workspace_id):
        # !!! Если пользователь уже был мембером, то деактивировав его мы не сможем его активировать снова. !!!

        workspace = (
            Workspace.objects
            .filter(id=workspace_id)
            .prefetch_related("member__user")
            .first()
        )
        if not workspace:
            return Response(
                {"error": "Workspace is not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_member_email = request.data.get("email")
        if not new_member_email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        new_member_user = User.objects.filter(email=new_member_email).first()
        
        if new_member_user:
            is_already_member = any(
                member.user_id == new_member_user.id for member in workspace.member.all()
            )
            if is_already_member:
                return Response(
                    {"error": "User is already a member of this workspace."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        role_id = request.data.get("role_id")
        role_name = request.data.get("role_name")

        if role_id:
            role = WorkspaceRole.objects.filter(id=role_id, workspace=workspace).first()
            if not role:
                return Response(
                    {"error": f"Role with id {role_id} does not exist in this workspace."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif role_name:
            role = WorkspaceRole.objects.filter(name=role_name, workspace=workspace).first()
            if not role:
                return Response(
                    {"error": f"Role with name '{role_name}' does not exist in this workspace."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"error": "Either 'role_id' or 'role_name' must be provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CreateWorkspaceMemberSerializer(
            data=request.data, 
            context={'workspace': workspace}
        )
        serializer.is_valid(raise_exception=True)
        member = serializer.save(user=new_member_user, role=role)

        response_serializer = MemberSerializer(member)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class BaseToggleWorkspaceMemberAPIView(APIView):
    """
    Abstract base class to toggle a workspace member's active status (activate or deactivate).

    This view handles the shared logic between activation and deactivation:
        - Validates that exactly one of `user_id` or `email` is provided.
        - Looks up the workspace and verifies membership.
        - Checks if the user's current active status matches the target state.
        - Updates the `is_active` field of the WorkspaceMember instance.
        - Returns a standardized success or error response.

    Subclasses must define the following class attributes:
        - is_active_target (bool): True to activate the user, False to deactivate.
        - action_word (str): Text used in messages (e.g., "activated" or "deactivated").

    Required permissions:
        - Authenticated user.
        - User must have `required_workspace_permission` within the workspace.
          (Currently set to `can_invite_users`, but should be replaced with `can_deactivate_users`.)

    HTTP Method:
        PATCH

    Path parameters:
        workspace_id (int): The ID of the workspace.

    Request body:
        {
            "user_id": <int>,   # optional
            "email": "<str>"    # optional
        }

    Conditions:
        - Exactly one of `user_id` or `email` must be provided.
        - User must exist and be a member of the workspace.
        - User must not already be in the desired active state.

    Responses:
        200 OK:
            {
                "message": "User has been <action_word>.",
                "member": { ... }  # Serialized member data
            }

        400 BAD REQUEST:
            - Missing or invalid input.
            - User does not exist or is not a member.
            - User is already in the desired state.

    This class should not be used directly — subclass it and define the required attributes.
    """

    permission_classes = [permissions.IsAuthenticated, HasWorkspacePermission]
    # Перенастроить права, пока разрешаем всем кто имеет право на 
    # создание юзеров, деактиивировать их. 
    # Потом поменять на права "can_deactivate_users"
    required_workspace_permission = "can_invite_users"

    is_active_target: bool = None  # must be set in subclass: True for activate, False for deactivate
    action_word: str = ""          # "activated" or "deactivated"

    def patch(self, request, workspace_id):
        workspace = Workspace.objects.filter(id=workspace_id).select_related("owner").first()
        if not workspace:
            return Response({"error": "Workspace is not found"}, status=status.HTTP_400_BAD_REQUEST)

        user_id = request.data.get("user_id")
        email = request.data.get("email")

        if sum(bool(x) for x in [user_id, email]) != 1:
            return Response(
                {"error": "You must provide exactly one of: user_id or email."},
                status=status.HTTP_400_BAD_REQUEST
            )

        target_user = User.objects.filter(id=user_id).first() if user_id else User.objects.filter(email=email).first()

        if not target_user:
            return Response({"error": "User is not found."}, status=status.HTTP_400_BAD_REQUEST)

        target_member = WorkspaceMember.objects.filter(workspace=workspace, user=target_user).first()

        if not target_member:
            return Response({"error": "User is not member in this workspace."}, status=status.HTTP_400_BAD_REQUEST)

        if target_member.is_active == self.is_active_target:
            return Response(
                {"error": f"User is already {self.action_word}."},
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


class DeactivateWorkspaceMemberAPIView(BaseToggleWorkspaceMemberAPIView):
    """
    API endpoint to deactivate a workspace member.
    """
    is_active_target = False
    action_word = "deactivated"


class ActivateWorkspaceMemberAPIView(BaseToggleWorkspaceMemberAPIView):
    """
    API endpoint to activate a workspace member.
    """
    is_active_target = True
    action_word = "activated"


class ChangeWorkspaceRoleAPIView(APIView):
    """
    API endpoint to change a member's role within a workspace.

    Required permissions:
        - Authenticated user.
        - The user must have the `can_change_roles` permission in the given workspace.

    HTTP Method:
        PATCH

    Path parameters:
        workspace_id (int): The ID of the workspace in which the role change is to be performed.

    Request body (must include either `user_id` or `email`, and the `new_role`):
        {
            "user_id": <int>,          # (optional) ID of the user whose role should be changed
            "email": "<email>",        # (optional) Email of the user
            "new_role": "<str>"        # (required) Name of the new role (e.g., "user", "client", "admin")
        }

    Conditions:
        - Exactly one of `user_id` or `email` must be provided.
        - The specified `new_role` must exist within the current workspace.
        - Only the owner of the workspace can change the role of a member with the `admin` role.

    Responses:
        200 OK:
            {
                "message": "User's role changed to <new_role>.",
                "member": { ... }  # Serialized member data
            }

        400 BAD REQUEST:
            - Invalid input (missing fields, non-existent user/role, etc.)
            - User not found or is not a member of the workspace
            - Attempt to change the role of an inactive (deactivated) member

        403 FORBIDDEN:
            - Attempt to demote a user with the `admin` role by someone who is not the workspace owner

    Example request:
        PATCH /api/workspaces/5/change-role/
        {
            "email": "user@example.com",
            "new_role": "client"
        }
    """

    permission_classes = [permissions.IsAuthenticated, HasWorkspacePermission]
    required_workspace_permission = "can_change_roles"

    def patch(self, request, workspace_id):
        workspace = Workspace.objects.filter(id=workspace_id).select_related("owner").first()
        if not workspace:
            return Response(
                {"error": "Workspace is not found"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_id = request.data.get("user_id")
        email = request.data.get("email")

        provided = [user_id, email]
        if sum(bool(x) for x in provided) != 1:
            return Response(
                {"error": "You must provide exactly one of: user_id or email."},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_role_name = request.data.get("new_role")
        if not isinstance(new_role_name, str) or not new_role_name.strip():
            return Response(
                {"error": "`new_role` is required and must be a string."},
                status=status.HTTP_400_BAD_REQUEST
            )
        new_role_name = new_role_name.strip().lower()
        
        new_role = WorkspaceRole.objects.filter(workspace=workspace, name=new_role_name).first()
        if not new_role:
            return Response(
                {"error": "Role is not found."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user_id:
            target_user = User.objects.filter(id=user_id).first()
        else:
            target_user = User.objects.filter(email=email).first()

        if not target_user:
            return Response(
                {"error": "User is not found."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        target_member = WorkspaceMember.objects.filter(workspace=workspace, user_id=target_user.id).first()
        
        if not target_member:
            return Response(
                {"error": "User is not member in this workspace."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not target_member.is_active:
            return Response(
                {"error": "Cannot change role of a deactivated user."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # только овнер может понижать роль админам
        if target_member.role.name == 'admin' and workspace.owner != request.user:
            return Response(
                {"error": "Cannot change admin role"}, 
                status=status.HTTP_403_FORBIDDEN
            )

        target_member.role = new_role
        target_member.save(update_fields=["role"])

        response_serializer = MemberSerializer(target_member)

        return Response({
            "message": f"User's role changed to {new_role_name}.",
            "member": response_serializer.data
        }, status=status.HTTP_200_OK)


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
        workspace = get_object_or_404(
            Workspace.objects.prefetch_related("member__user", "member__role"),
            id=workspace_id
        )
        serializer = WorkspaceSerializer(workspace)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, workspace_id: int) -> Response:
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
