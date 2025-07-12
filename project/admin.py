from django.contrib import admin
from project.models import Project, ProjectMember, ProjectBilling, ProjectQuote

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "workspace", "is_active", "is_public", "is_billable", "created_at")
    list_filter = ("workspace", "is_public", "is_billable", "is_active")
    search_fields = ("name", "key", "workspace__name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ("user", "project", "is_active", "created_at", "updated_at")
    list_filter = ("is_active", "project__workspace")
    search_fields = ("user__email", "project__name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ProjectBilling)
class ProjectBillingAdmin(admin.ModelAdmin):
    list_display = ("project", "type", "limit", "created_at")
    list_filter = ("type",)
    search_fields = ("project__name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(ProjectQuote)
class ProjectQuoteAdmin(admin.ModelAdmin):
    list_display = ("project_billing", "quote_type", "amount", "created_at", "updated_at")
    list_filter = ("quote_type", "project_billing__project__workspace")
    search_fields = ("description", "project_billing__project__name")
    readonly_fields = ("created_at", "updated_at")
