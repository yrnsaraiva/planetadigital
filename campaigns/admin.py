from django.contrib import admin
from .models import Campaign


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "status",
        "start_date",
        "end_date",
        "is_featured",
        "created_at",
    )
    list_filter = ("status", "is_featured", "start_date")
    search_fields = ("title", "short_description", "description")
    ordering = ("-start_date", "-created_at")
    date_hierarchy = "start_date"

    prepopulated_fields = {"slug": ("title",)}

    readonly_fields = ("created_at",)

    fieldsets = (
        ("Conteúdo", {
            "fields": (
                "title",
                "slug",
                "cover_image",
                "short_description",
                "description",
            )
        }),
        ("Call-to-action", {
            "fields": (
                "call_to_action",
            ),
            "description": "Use external_link se a doação/inscrição for feita numa plataforma externa."
        }),
        ("Publicação", {
            "fields": (
                "status",
                "start_date",
                "end_date",
                "is_featured",
            )
        }),
        ("Sistema", {
            "fields": ("created_at",),
        }),
    )

    # Ações úteis (opcionais)
    actions = ("make_active", "make_finished")

    @admin.action(description="Marcar como ACTIVE")
    def make_active(self, request, queryset):
        queryset.update(status="active")

    @admin.action(description="Marcar como FINISHED")
    def make_finished(self, request, queryset):
        queryset.update(status="finished")
