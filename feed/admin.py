from django.contrib import admin, messages

from .models import DailyPoll, PollOption, TenantArticle, TenantPortal
from .services import sync_portal_articles


@admin.register(TenantPortal)
class TenantPortalAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "domain", "source_type", "is_active", "last_synced_at")
    list_filter = ("source_type", "is_active")
    search_fields = ("name", "slug", "domain")
    actions = ["sync_selected_portals"]

    @admin.action(description="Sync latest articles from selected tenant portals")
    def sync_selected_portals(self, request, queryset):
        total_created = 0
        for portal in queryset:
            try:
                res = sync_portal_articles(portal)
                total_created += res["created"]
            except Exception as exc:
                self.message_user(
                    request,
                    f"Failed syncing {portal.name}: {exc}",
                    level=messages.ERROR,
                )
        self.message_user(
            request,
            f"Sync finished. Added {total_created} new tenant articles.",
            level=messages.SUCCESS,
        )


@admin.register(TenantArticle)
class TenantArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "portal", "topic", "is_breaking", "is_active", "published_at")
    list_filter = ("portal", "topic", "is_breaking", "is_active")
    search_fields = ("title", "summary", "portal__name")
    list_editable = ("is_breaking", "is_active")


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 2


@admin.register(DailyPoll)
class DailyPollAdmin(admin.ModelAdmin):
    list_display = ("question", "is_active", "created_at")
    list_filter = ("is_active",)
    inlines = [PollOptionInline]
