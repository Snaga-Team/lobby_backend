from django.urls import path
from project.views import (
    ProjectCreateAPIView, 
    ProjectListAPIView, 
    ProjectDetailAPIView,
    AddProjectMemberAPIView,
    ActivateProjectMemberAPIView,
    DeactivateProjectMemberAPIView,
    ProjectMembersListAPIView,
)

urlpatterns = [
    path('create/', ProjectCreateAPIView.as_view(), name='project-create'),
    path('get_list/', ProjectListAPIView.as_view(), name='project-list'),
    path("<int:project_id>/", ProjectDetailAPIView.as_view(), name="project-detail"),
    
    path("<int:project_id>/add_member/", AddProjectMemberAPIView.as_view(), name="add-members"),
    path("<int:project_id>/deactivate_member/", DeactivateProjectMemberAPIView.as_view(), name="deactivate-project-member"),
    path("<int:project_id>/activate_member/", ActivateProjectMemberAPIView.as_view(), name="activate-project-member"),
    path("<int:project_id>/list_member/", ProjectMembersListAPIView.as_view(), name="project-list-member"),
]