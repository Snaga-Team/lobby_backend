from django.urls import path
from workspace.views import (
    WorkspaceCreateAPIView, WorkspaceListAPIView, 
    AddWorkspaceMemberAPIView, WorkspaceDetailAPIView,
    DeactivateWorkspaceMemberAPIView, ChangeWorkspaceRoleAPIView,
    WorkspaceOwnerChangeAPIView, WorkspaceRoleListAPIView,
    MembersListAPIView
)

urlpatterns = [
    path('create/', WorkspaceCreateAPIView.as_view(), name='workspace-create'),
    path('get_list/', WorkspaceListAPIView.as_view(), name='workspace-list'),
    
    path("<int:workspace_id>/", WorkspaceDetailAPIView.as_view(), name="workspace-detail"),
    path("<int:workspace_id>/add_member/", AddWorkspaceMemberAPIView.as_view(), name="add-members"),
    path("<int:workspace_id>/members_list/", MembersListAPIView.as_view(), name="members_list"),
    path("<int:workspace_id>/deactivate_member/", DeactivateWorkspaceMemberAPIView.as_view(), name="deactivate_workspace-member"),
    path("<int:workspace_id>/change_role_member/", ChangeWorkspaceRoleAPIView.as_view(), name="change_role_member"),
    path("<int:workspace_id>/change_owner/", WorkspaceOwnerChangeAPIView.as_view(), name="change-owner"),
    path("<int:workspace_id>/workspace_roles/", WorkspaceRoleListAPIView.as_view(), name="workspace-roles"),
]