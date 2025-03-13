from django.urls import path
from workspace.views import (
    WorkspaceCreateAPIView, WorkspaceListAPIView, 
    AddWorkspaceMembershipAPIView, WorkspaceDetailAPIView,
    DeactivateWorkspaceMembershipAPIView
)

urlpatterns = [
    path('create/', WorkspaceCreateAPIView.as_view(), name='workspace-create'),
    path('get_list/', WorkspaceListAPIView.as_view(), name='workspace-list'),
    path("<int:workspace_id>/", WorkspaceDetailAPIView.as_view(), name="workspace-detail"),
    path("<int:workspace_id>/add_member/", AddWorkspaceMembershipAPIView.as_view(), name="add_members"),
    path("<int:workspace_id>/deactivate_member/", DeactivateWorkspaceMembershipAPIView.as_view(), name="deactivate_workspace_member"),
]