from django.contrib import admin

from .models import NewsletterSubscriber


admin.site.site_header = "PLA - Painel Administrativo"
admin.site.site_title = "PLANETA Admin"
admin.site.index_title = "Gestão do Sistema"


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "status", "subscribed_at", "unsubscribed_at")
    list_filter = ("status", "subscribed_at")
    search_fields = ("email", "name")
    readonly_fields = ("subscribed_at",)
    ordering = ("-subscribed_at",)

    fieldsets = (
        ("Subscritor", {"fields": ("email", "name")}),
        ("Estado", {"fields": ("status", "unsubscribed_at")}),
        ("Datas", {"fields": ("subscribed_at",)}),
    )
