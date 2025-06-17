from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from accounts.models import User

@admin.register(User)
class MainUserAdmin(UserAdmin):
    list_display = (
        'id', 'email', 'first_name', 'last_name', 'avatar_preview', 
        'avatar_background_display', 'avatar_emoji', 'is_staff', 
        'is_active'
    )
    list_filter = ('is_staff', 'is_active')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Avatar Settings', {'fields': (
            'avatar_background', 'avatar_emoji', 
            'avatar_image', 'avatar_preview'
        )}),
        ('Permissions', {'fields': (
            'is_staff', 'is_active', 'is_superuser', 
            'groups', 'user_permissions'
        )}),
        ('Important Dates', {'fields': ('last_login',)}),
    )

    readonly_fields = ('avatar_preview',)

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name', 
                'password1', 'password2', 'is_staff', 
                'is_active'
            ),
        }),
    )

    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

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
