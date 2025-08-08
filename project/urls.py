from django.urls import path
from project.views import (
    ProjectCreateAPIView, 
    ProjectListAPIView, 
    ProjectDetailAPIView,
    AddProjectMemberAPIView
)

urlpatterns = [
    path('create/', ProjectCreateAPIView.as_view(), name='project-create'),
    path('get_list/', ProjectListAPIView.as_view(), name='project-list'),
    path("<int:project_id>/", ProjectDetailAPIView.as_view(), name="project-detail"),
    path("<int:project_id>/add_member/", AddProjectMemberAPIView.as_view(), name="add-members"),
]