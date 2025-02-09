from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from accounts.models import CustomUser


class Workspace(models.Model):
    name = models.CharField(max_length=255, verbose_name="Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date of create")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date of update")
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="workspace_owner", verbose_name="Owner")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            WorkspaceRole.objects.bulk_create([
                WorkspaceRole(name="admin", description="Administrator of the workspace", workspace=self),
                WorkspaceRole(name="user", description="Regular user of the workspace", workspace=self),
                WorkspaceRole(name="client", description="Client with limited access", workspace=self),
            ])

    def __str__(self):
        return self.name
    

class WorkspaceRole(models.Model):
    name = models.CharField(max_length=50, verbose_name="Name of role")
    description = models.TextField(blank=True, null=True, verbose_name="Descriotion of role")
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="roles", verbose_name="Workspace")

    def __str__(self):
        return f"{self.name} ({self.workspace.name})"
    

class WorkspaceMembership(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="workspace_memberships", verbose_name="User")
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="memberships", verbose_name="Workspace")
    role = models.ForeignKey(WorkspaceRole, on_delete=models.SET_NULL, null=True, blank=True, related_name="memberships", verbose_name="Role")
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="Date of joined")

    class Meta:
        unique_together = ('user', 'workspace')  # One user can be added only once to the current workspace.

    def __str__(self):
        return f"{self.user.email} in {self.workspace.name} as {self.role.name if self.role else 'No Role'}"