from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import generics, permissions
from workspace.models import Workspace, WorkspaceMember, WorkspaceRole
from workspace.serializers import (
    WorkspaceSerializer, WorkspaceMemberSerializer, 
    WorkspaceDetailSerializer, WorkspaceWithRolesSerializer, RoleSerializer
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
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, id=workspace_id)

        if workspace.owner != request.user:
            return Response(
                {"error": "Only the current owner can change the workspace owner."},
                status=status.HTTP_403_FORBIDDEN
            )

        new_owner_id = request.data.get("new_owner_id")
        new_owner_email = request.data.get("new_owner_email")
        new_member_id = request.data.get("new_member_id")

        if not any([new_owner_id, new_owner_email, new_member_id]):
            return Response(
                {"error": "One of new_owner_id, new_owner_email, or new_member_id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_owner = None
        if new_member_id:
            membership = WorkspaceMember.objects.filter(
                id=new_member_id, workspace=workspace
            ).select_related("user").first()
            if membership:
                new_owner = membership.user
        elif new_owner_id:
            new_owner = User.objects.filter(id=new_owner_id).first()
        elif new_owner_email:
            new_owner = User.objects.filter(email=new_owner_email).first()

        if not new_owner:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not new_member_id:
            new_owner_membership = WorkspaceMember.objects.filter(
                user=new_owner, workspace=workspace
            ).first()
            if not new_owner_membership:
                return Response(
                    {"error": "The new owner must be a member of the workspace."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        current_owner = workspace.owner
        current_owner_membership = WorkspaceMember.objects.filter(
            user=current_owner, workspace=workspace
        ).first()

        if not current_owner_membership:
            admin_role = WorkspaceRole.objects.filter(name="admin").first()
            if not admin_role:
                return Response(
                    {"error": "Admin role not found in the system."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            WorkspaceMember.objects.create(
                user=current_owner,
                workspace=workspace,
                role=admin_role,
                is_active=True
            )


        workspace.owner = new_owner
        workspace.save()

        serializer = WorkspaceDetailSerializer(workspace)
        return Response(serializer.data, status=status.HTTP_200_OK)