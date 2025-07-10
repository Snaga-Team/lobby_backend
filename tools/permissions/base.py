from rest_framework.permissions import BasePermission
from workspace.models import Workspace, WorkspaceMember
from tools.permissions.constants import DEFAULT_ALWAYS_ALLOWED_PERMISSIONS


class HasWorkspacePermission(BasePermission):
    METHOD_PERMISSION_MAP = {
        "GET": "can_view_workspace",
        "PUT": "can_edit_workspace",
    }

    def has_permission(self, request, view):
        workspace_id = view.kwargs.get("workspace_id")
        if not workspace_id:
            return False
        
        try:
            workspace = Workspace.objects.get(id=workspace_id)
        except Workspace.DoesNotExist:
            return False
        
        if workspace.owner == request.user:
            return True
        
        try:
            member = WorkspaceMember.objects.select_related("role").get(
                user=request.user, workspace=workspace
            )
        except WorkspaceMember.DoesNotExist:
            return False

        required_permission = getattr(view, "required_workspace_permission", None)

        if not required_permission:
            required_permission = self.METHOD_PERMISSION_MAP.get(request.method)

        if not required_permission:
            return False
        
        if required_permission in DEFAULT_ALWAYS_ALLOWED_PERMISSIONS:
            return True

        return member.role.settings.get(required_permission, False)
