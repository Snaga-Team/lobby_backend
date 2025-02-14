from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
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
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return Response({"error": "Workspace not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = WorkspaceMembershipSerializer(
            data=request.data, 
            context={"request": request, "workspace": workspace}
        )
        if serializer.is_valid():
            result = serializer.save()
            return Response({"message": "User added to workspace"} if isinstance(result, WorkspaceMembership) else result, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class WorkspaceDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, workspace_id):
        try:
            workspace = Workspace.objects.prefetch_related("memberships__user", "memberships__role").get(id=workspace_id)
        except Workspace.DoesNotExist:
            return Response({"error": "Workspace not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = WorkspaceDetailSerializer(workspace)
        return Response(serializer.data, status=status.HTTP_200_OK)