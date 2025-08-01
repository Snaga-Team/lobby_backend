"""
Default permission settings for workspace roles.

This module defines the default JSON permission structures (`settings`) assigned to
each workspace role upon creation. These settings determine what actions each role
is allowed to perform within a workspace.

Contents:
    - DEFAULT_ROLE_PERMISSIONS: A dictionary mapping role names (e.g., "admin", "user", "client")
      to their corresponding permission settings.

Example:
    DEFAULT_ROLE_PERMISSIONS["admin"] = {
        "can_create_projects": True,
        "can_edit_projects": True,
        ...
    }
"""

DEFAULT_ROLE_PERMISSIONS = {
    "admin": {
        "can_edit_workspace": True,
        "can_delete_workspace": True,

        "can_change_role_in_workspace": True,
        "can_invite_users_to_workspace": True,
        "can_deactivate_users_in_workspace": True,

        "can_create_projects": True,
        "can_edit_projects": True,
        "can_delete_projects": True,
        "can_view_public_projects": True,

        "can_invite_users_to_project": True,
        "can_deactivate_users_in_project": True,

        "can_view_reports": True
    },
    "user": {
        "can_edit_workspace": False,
        "can_delete_workspace": False,

        "can_change_role_in_workspace": False,
        "can_invite_users_to_workspace": False,
        "can_deactivate_users_in_workspace": False,

        "can_create_projects": True,
        "can_edit_projects": False,
        "can_delete_projects": False,
        "can_view_public_projects": True,

        "can_invite_users_to_project": False,
        "can_deactivate_users_in_project": False,

        "can_view_reports": True
    },
    "client": {
        "can_edit_workspace": False,
        "can_delete_workspace": False,

        "can_change_role_in_workspace": False,
        "can_invite_users_to_workspace": False,
        "can_deactivate_users_in_workspace": False,

        "can_create_projects": False,
        "can_edit_projects": False,
        "can_delete_projects": False,
        "can_view_public_projects": False,

        "can_invite_users_to_project": False,
        "can_deactivate_users_in_project": False,

        "can_view_reports": True
    }
}
