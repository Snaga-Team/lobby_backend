from django.urls import path
from project.views import (
    ProjectCreateAPIView, 
    ProjectListAPIView, 
    ProjectDetailAPIView
)

urlpatterns = [
    path('create/', ProjectCreateAPIView.as_view(), name='project-create'),
    path('get_list/', ProjectListAPIView.as_view(), name='project-list'),
    path("<int:project_id>/", ProjectDetailAPIView.as_view(), name="project-detail"),
]