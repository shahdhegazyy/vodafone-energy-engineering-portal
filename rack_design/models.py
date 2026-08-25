from django.db import models


class RackDesign(models.Model):
    project_reference = models.CharField(max_length=100, blank=True)
    site_name = models.CharField(max_length=150)
    rack_name = models.CharField(max_length=150)
    engineer = models.CharField(max_length=150)
    notes = models.TextField(blank=True)
    rack_capacity_u = models.PositiveIntegerField()
    used_rack_u = models.PositiveIntegerField()
    dc_voltage_v = models.FloatField()
    ac_voltage_v = models.FloatField()
    total_power_kw = models.FloatField()
    installed_devices = models.PositiveIntegerField()
    protected_circuits = models.PositiveIntegerField()
    result_status = models.CharField(max_length=20)
    result_message = models.TextField(blank=True)
    devices = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.site_name} / {self.rack_name} — {self.used_rack_u}/{self.rack_capacity_u} U"
