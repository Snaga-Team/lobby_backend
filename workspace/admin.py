from django.contrib import admin
from django.utils.html import format_html
from workspace.models import Workspace, WorkspaceRole, WorkspaceMembership


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'owner', 'avatar_preview', 
        'avatar_background_display', 'avatar_emoji', 
        'created_at', 'updated_at'
    )
    
    search_fields = ('id', 'name', 'owner__email')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at', 'avatar_preview')

    def avatar_preview(self, obj):
        """Displays a thumbnail of the avatar in the admin panel."""
        if obj.avatar_image:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius:50%;" />', 
                obj.avatar_image.url
            )
        return "No Avatar"
    avatar_preview.short_description = "Avatar"

    def avatar_background_display(self, obj):
        """Displays a colored square instead of a HEX code."""
        return format_html(
            '<div style="width:40px; height:20px; background:{}; border:1px solid #000;"></div>', 
            obj.avatar_background
        )
    avatar_background_display.short_description = "Background"

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