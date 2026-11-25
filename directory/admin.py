from django.contrib import admin

from .models import Newspaper


@admin.register(Newspaper)
class NewspaperAdmin(admin.ModelAdmin):
    list_display = ("name", "bangla_name", "category", "sort_order", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "bangla_name", "slug", "url")
    list_editable = ("sort_order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
