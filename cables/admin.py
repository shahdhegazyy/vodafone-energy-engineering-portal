from django.contrib import admin
from .models import CableSelection


@admin.register(CableSelection)
class CableSelectionAdmin(admin.ModelAdmin):
    list_display = ("site_name", "rack_name", "engineer", "recommended_cable_mm2", "selected_breaker_a", "result_status", "created_at")
    list_filter = ("result_status", "created_at")
    search_fields = ("project_reference", "site_name", "rack_name", "engineer")
