from django.contrib import admin

from .models import Event, EventMedia


class EventMediaInline(admin.TabularInline):
    model = EventMedia
    extra = 0
    fields = ("media_type", "file", "caption")
    ordering = ("id",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "start_at",
        "city",
        "is_featured",
    )
    list_filter = ("is_featured", "start_at", "city")
    search_fields = ("title", "description", "city", "lineup_text")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "start_at"
    ordering = ("-start_at",)

    fields = (
        "title",
        "slug",
        "poster",
        "description",
        "start_at",
        "end_at",
        "city",
        "lineup_text",
        "ticket_url",
        "is_featured",
        "created_at",
    )
    readonly_fields = ("created_at",)

    inlines = (EventMediaInline,)


@admin.register(EventMedia)
class EventMediaAdmin(admin.ModelAdmin):
    list_display = ("event", "media_type", "caption")
    list_filter = ("media_type", "event")
    search_fields = ("event__title", "caption")
    ordering = ("event", "id")
