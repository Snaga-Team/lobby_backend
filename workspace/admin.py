from django.contrib import admin
from workspace.models import Workspace, WorkspaceRole, WorkspaceMembership


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'created_at', 'updated_at')
    search_fields = ('id', 'name', 'owner__email')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(WorkspaceRole)
class WorkspaceRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'workspace')
    search_fields = ('id', 'name', 'workspace__name')
    list_filter = ('workspace',)


@admin.register(WorkspaceMembership)
class WorkspaceMembershipAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'workspace', 'role', 'joined_at')
    search_fields = ('id', 'user__email', 'workspace__name', 'role__name')
    list_filter = ('workspace', 'role')
    readonly_fields = ('joined_at',)