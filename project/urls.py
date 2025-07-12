from django.urls import path
from project.views import ProjectCreateAPIView, ProjectListAPIView

urlpatterns = [
    path('create/', ProjectCreateAPIView.as_view(), name='project-create'),
    path('get_list/', ProjectListAPIView.as_view(), name='project-list'),
]