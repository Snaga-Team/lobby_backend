from django.urls import path
from workspace.views import WorkspaceCreateAPIView, WorkspaceListAPIView, AddWorkspaceMembershipAPIView

urlpatterns = [
    path('create/', WorkspaceCreateAPIView.as_view(), name='workspace-create'),
    path('get_list/', WorkspaceListAPIView.as_view(), name='workspace-list'),
    path("<int:workspace_id>/add_members/", AddWorkspaceMembershipAPIView.as_view(), name="add_members"),
]