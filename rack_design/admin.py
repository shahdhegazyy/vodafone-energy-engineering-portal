from django.contrib import admin
from .models import RackDesign


@admin.register(RackDesign)
class RackDesignAdmin(admin.ModelAdmin):
    list_display = ("site_name", "rack_name", "engineer", "used_rack_u", "total_power_kw", "result_status", "created_at")
    list_filter = ("result_status", "created_at")
    search_fields = ("project_reference", "site_name", "rack_name", "engineer")
