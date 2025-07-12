from django.db import models

from accounts.models import User
from workspace.constants import ROLE_ADMIN, ROLE_USER, ROLE_CLIENT
from tools.validators import validate_hex_color
from tools.permissions.defaults import DEFAULT_ROLE_PERMISSIONS


class Workspace(models.Model):
    """
    Workspace model representing a collaborative environment within the system.

    This model defines the core attributes of a workspace, which serves as a container
    for users, projects, and associated roles. A workspace has an owner and can have
    multiple members with different roles. On creation, default roles ("admin", "user", "client")
    are automatically generated for the workspace.

    Fields:
        name (str): Name of the workspace.
        description (str): Optional text description of the workspace.
        currency (str): 3-letter currency code of the workspace (example, USD, EUR, UAH).
        avatar_background (str): HEX color code for the background of the avatar. Defaults to white.
        avatar_emoji (str): Emoji used as a visual avatar for the workspace. Defaults to "🚀".
        avatar_image (ImageField): Optional image uploaded to visually represent the workspace.
        created_at (datetime): Timestamp when the workspace was created.
        updated_at (datetime): Timestamp when the workspace was last updated.
        owner (User): Foreign key reference to the user who owns the workspace.
        is_active (bool): Indicates whether the workspace is currently active.

    Methods:
        save(): Overrides the default save behavior to create default roles on initial creation.
    
    Returns:
        str: The name of the workspace as its string representation.
    """

    name = models.CharField(max_length=255, verbose_name="Name")
    description = models.TextField(verbose_name="Description", blank=True, null=True)
    currency = models.CharField(max_length=3, verbose_name="Currency", default='USD', blank=True, null=True)
    avatar_background = models.CharField(
        max_length=7,
        verbose_name="Avatar Background",
        default="#ffffff", 
        validators=[validate_hex_color], 
        null=True,
        blank=True
    )
    avatar_emoji = models.CharField(max_length=3, verbose_name="Avatar Emoji", default="🚀")
    avatar_image = models.ImageField(
        upload_to="workspaces/", 
        verbose_name="Avatar Image",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date of create")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date of update")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="workspace_owner", verbose_name="Owner")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    def save(self, *args, **kwargs) -> None:
        """
        Overrides the default save behavior of the Workspace model.

        When a new workspace instance is created, this method automatically generates
        three default roles: "admin", "user", and "client", each with predefined permission
        settings stored in the `settings` JSON field.

        Uses:
            - ROLE_ADMIN, ROLE_USER, ROLE_CLIENT: dictionaries containing the name and description of each role.
            - DEFAULT_ROLE_PERMISSIONS: a dictionary containing default permission settings for each role.

        Example of a generated role:
            name = "admin"
            description = "Administrator of the workspace"
            settings = {
                "can_create_projects": True,
                "can_edit_projects": True,
                ...
            }

        Args:
            *args, **kwargs: Standard arguments passed to the save() method.
        """

        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            WorkspaceRole.objects.bulk_create([
                WorkspaceRole(
                    name=ROLE_ADMIN.get("name"), 
                    description=ROLE_ADMIN.get("description"), 
                    workspace=self,
                    settings=DEFAULT_ROLE_PERMISSIONS.get(ROLE_ADMIN.get("name"), {})
                ),
                WorkspaceRole(
                    name=ROLE_USER.get("name"), 
                    description=ROLE_USER.get("description"), 
                    workspace=self,
                    settings=DEFAULT_ROLE_PERMISSIONS.get(ROLE_USER.get("name"), {})
                ),
                WorkspaceRole(
                    name=ROLE_CLIENT.get("name"), 
                    description=ROLE_CLIENT.get("description"), 
                    workspace=self,
                    settings=DEFAULT_ROLE_PERMISSIONS.get(ROLE_CLIENT.get("name"), {})
                ),
            ])

    def __str__(self) -> str:
        return self.name


class WorkspaceRole(models.Model):
    """
    WorkspaceRole model represents a user role within a specific workspace.

    This model defines the type of role that a user can have in a workspace,
    such as "admin", "user", or "client". Each role belongs to a single workspace
    and can have a custom name and optional description.

    Fields:
        name (str): The name of the role (e.g., "admin", "user", "client").
        description (str): An optional text description explaining the purpose or permissions of the role.
        workspace (Workspace): A foreign key reference to the workspace to which this role belongs.
        settings (JSON): A JSON object storing permission settings (e.g., {"can_edit": true, "can_invite": false}).

    Returns:
        str: A string representation of the role including its name and associated workspace.
    """

    name = models.CharField(max_length=50, verbose_name="Role name")
    description = models.TextField(verbose_name="Description", blank=True, null=True)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="roles", verbose_name="Workspace")
    settings = models.JSONField(default=dict, blank=True, verbose_name="Role Settings")

    def __str__(self) -> str:
        return f"{self.name} ({self.workspace.name})"


class WorkspaceMember(models.Model):
    """
    WorkspaceMember model represents the association between a user and a workspace.

    This model tracks which users are members of which workspaces, including the role assigned
    to the user within that workspace. A user can be added to a workspace only once.

    Fields:
        user (User): Foreign key reference to the user who is a member of the workspace.
        workspace (Workspace): Foreign key reference to the associated workspace.
        role (WorkspaceRole): Optional foreign key reference to the user's role in the workspace.
        status (str): Status of the member in the workspace (e.g., active, invited, pending).
        hour_rate (float): Hourly rate for the member in the current workspace.
        joined_at (datetime): Timestamp indicating when the user was added to the workspace.
        is_active (bool): Indicates whether the user's membership in the workspace is active.

    Meta:
        unique_together (tuple): Ensures a user can only have one membership per workspace.

    Returns:
        str: A string representation showing the user's email, workspace name, and role.
    """

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INVITED = 'invited', 'Invited'
        PENDING = 'pending', 'Pending'
        SUSPENDED = 'suspended', 'Suspended'

    # Хз как правильно member или members в related_name. В projects будет members
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="workspace_member", verbose_name="User")
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="member", verbose_name="Workspace")
    role = models.ForeignKey(WorkspaceRole, on_delete=models.SET_NULL, related_name="member", verbose_name="Role", null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, verbose_name="Status")
    hour_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Hourly Rate", null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name="Date of joined")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")

    class Meta:
        unique_together = ('user', 'workspace')  # One user can be added only once to the current workspace.
        verbose_name = "Workspace Member"
        verbose_name_plural = "Workspace Members"

    def __str__(self) -> str:
        role_name = self.role.name if self.role else 'No Role'
        return f"{self.user.email} in {self.workspace.name} as {role_name}"
