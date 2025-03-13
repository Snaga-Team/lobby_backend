from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import models
from rest_framework import generics, permissions
from workspace.models import Workspace, WorkspaceMembership
from workspace.serializers import WorkspaceSerializer, WorkspaceMembershipSerializer, WorkspaceDetailSerializer


class WorkspaceCreateAPIView(generics.CreateAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]


class WorkspaceListAPIView(generics.ListAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        owned_workspaces = Workspace.objects.filter(owner=user)
        member_workspaces = Workspace.objects.filter(memberships__user=user)
    
        return owned_workspaces.union(member_workspaces)
    

class AddWorkspaceMembershipAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, id=workspace_id)

        if not self.has_permission_to_add(request.user, workspace, request.data):
            return Response({"error": "You do not have permission to add users."}, status=status.HTTP_403_FORBIDDEN)

        serializer = WorkspaceMembershipSerializer(
            data=request.data, 
            context={"request": request, "workspace": workspace}
        )
        if serializer.is_valid():
            result = serializer.save()
            return Response({"message": "User added to workspace"} if isinstance(result, WorkspaceMembership) else result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def has_permission_to_add(self, user, workspace, request_data):
        """
        Checks whether the user can add participants to `Workspace`
            - The owner can add any users
            - Admin can only add ordinary participants (not other admins)
        """
        if workspace.owner == user:
            return True

        user_membership = WorkspaceMembership.objects.filter(user=user, workspace=workspace, role__name="admin").first()
        if user_membership:
            new_role_name = request_data.get("role", "").lower()
            if new_role_name == "admin":
                return False
            return True
        
        return False


class DeactivateWorkspaceMembershipAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, workspace_id):
        workspace = get_object_or_404(
            Workspace.objects.prefetch_related("memberships__user", "memberships__role")
            .filter(models.Q(owner=request.user) | models.Q(memberships__user=request.user))
            .distinct(),
            id=workspace_id
        )
        
        user_id = request.data.get("user_id")
        email = request.data.get("email")
        if not user_id and not email:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if user_id:
            target_membership = get_object_or_404(WorkspaceMembership, workspace=workspace, user_id=user_id)
        else:
            target_membership = get_object_or_404(WorkspaceMembership, workspace=workspace, user__email=email)

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

        user_membership = WorkspaceMembership.objects.filter(user=user, workspace=workspace).first()
        if user_membership and user_membership.role and user_membership.role.name == "admin":
            # Admin can deactivate only ordinary users (not admins)
            return target_membership.role is None or target_membership.role.name not in ["admin", ]

        return False


class WorkspaceDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, workspace_id):
        try:
            workspace = Workspace.objects.prefetch_related("memberships__user", "memberships__role").get(id=workspace_id)
        except Workspace.DoesNotExist:
            return Response({"error": "Workspace not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if not self.has_permission_to_view(request.user, workspace):
            return Response({"error": "You do not have permission to view this workspace."}, status=status.HTTP_403_FORBIDDEN)

        serializer = WorkspaceDetailSerializer(workspace)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, workspace_id):
        workspace = get_object_or_404(Workspace, id=workspace_id)

        if not self.has_permission_to_edit(request.user, workspace):
            return Response({"error": "You do not have permission to edit this workspace."}, status=status.HTTP_403_FORBIDDEN)

        serializer = WorkspaceDetailSerializer(workspace, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def has_permission_to_edit(self, user, workspace):
        """ Checks if the user is an owner or admin in the workspace """
        if workspace.owner == user:
            return True
        
        membership = WorkspaceMembership.objects.filter(user=user, workspace=workspace, role__name="admin").first()
        if membership:
            return True
        
        return False
    
    def has_permission_to_view(self, user, workspace):
        """ Checks if the user is an owner or participant of the workspace """
        if workspace.owner == user:
            return True

        is_member = WorkspaceMembership.objects.filter(user=user, workspace=workspace).exists()
        return is_member