from rest_framework.permissions import BasePermission
from workspace.models import Workspace, WorkspaceMember
from project.models import Project, ProjectMember
from tools.permissions.constants import DEFAULT_ALWAYS_ALLOWED_PERMISSIONS


class HasWorkspacePermission(BasePermission):
    METHOD_PERMISSION_MAP = {
        "GET": "can_view_workspace",
        "PUT": "can_edit_workspace",
    }

    def has_permission(self, request, view):
        workspace_id = view.kwargs.get("workspace_id") or request.data.get("workspace")
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


class HasProjectPermission(BasePermission):
    METHOD_PERMISSION_MAP = {
        "GET": "can_view_project",
        "PUT": "can_edit_project",
    }

    def has_permission(self, request, view):
        project_id = view.kwargs.get("project_id") or request.data.get("project")
        if not project_id:
            return False
        
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return False
        
        if project.owner == request.user:
            return True

        workspace = project.workspace

        try:
            workspace_member = WorkspaceMember.objects.select_related("role").get(
                user=request.user, workspace=workspace, is_active=True
            )
        except WorkspaceMember.DoesNotExist:
            return False

        required_permission = getattr(view, "required_project_permission", None)

        if not required_permission:
            required_permission = self.METHOD_PERMISSION_MAP.get(request.method)

        if not required_permission:
            return False
        
        if required_permission in DEFAULT_ALWAYS_ALLOWED_PERMISSIONS:
            return True
        
        role = workspace_member.role
        role_settings = role.settings if role else {}

        is_project_member = ProjectMember.objects.filter(project=project, user=request.user, is_active=True).exists()

        if required_permission == "can_view_project":
            if is_project_member or (project.is_public and role_settings.get("can_view_public_projects", False)):
                return True

        return role_settings.get(required_permission, False)
    
