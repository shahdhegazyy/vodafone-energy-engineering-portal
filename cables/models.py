from django.db import models


class CableSelection(models.Model):
    project_reference = models.CharField(max_length=100, blank=True)
    site_name = models.CharField(max_length=150)
    rack_name = models.CharField(max_length=150)
    engineer = models.CharField(max_length=150)
    notes = models.TextField(blank=True)
    load_current_a = models.FloatField()
    length_m = models.FloatField()
    temperature_below_25 = models.FloatField()
    temperature_25_30 = models.FloatField()
    temperature_30_60 = models.FloatField()
    temperature_above_60 = models.FloatField()
    required_breaker_a = models.FloatField()
    selected_breaker_a = models.FloatField()
    recommended_cable_mm2 = models.FloatField(null=True, blank=True)
    worst_voltage_drop_v = models.FloatField(null=True, blank=True)
    result_status = models.CharField(max_length=20)
    calculation_details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.site_name} / {self.rack_name} — {self.recommended_cable_mm2 or 'No match'} mm²"
