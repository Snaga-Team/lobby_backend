"""
Constants for the `workspace` application.

This module contains fixed values related to workspaces, such as predefined role names
and other global constants used across the workspace system.

Contents:
    - ROLE_ADMIN, ROLE_USER, ROLE_CLIENT: Default role identifiers.
    - DEFAULT_ROLES: A list of all default role names.
    - Other workspace-related constants can be added here as needed.
"""

ROLE_ADMIN = {"name": "admin", "description": "Administrator of the workspace"}
ROLE_USER = {"name": "user", "description": "Regular user of the workspace"}
ROLE_CLIENT = {"name": "client", "description": "Client with limited access"}

DEFAULT_ROLES = [ROLE_ADMIN, ROLE_USER, ROLE_CLIENT]
