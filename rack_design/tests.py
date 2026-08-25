import json
from django.test import TestCase
from django.urls import reverse
from .models import RackDesign


class RackDesignDatabaseTests(TestCase):
    def test_rack_design_is_recalculated_and_saved(self):
        payload = {
            "project_reference": "PRJ-002", "site_name": "Cairo DC",
            "rack_name": "Rack B01", "engineer": "Engineer", "notes": "Test",
            "rack_capacity_u": 42, "dc_voltage_v": 48, "ac_voltage_v": 220,
            "devices": [{"name": "Server", "u": 3, "power": 1, "psu": 2,
                         "qty": 2, "breaker": 25, "type": "DC"}],
        }
        response = self.client.post(
            reverse("rack_design:save_design"), json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        record = RackDesign.objects.get()
        self.assertEqual(record.used_rack_u, 6)
        self.assertEqual(record.installed_devices, 2)
        self.assertEqual(record.protected_circuits, 4)
        self.assertEqual(record.result_status, "PASS")

    def test_ac_device_breaker_is_forced_to_32_amp(self):
        payload = {
            "site_name": "Cairo DC", "rack_name": "Rack AC01", "engineer": "Engineer",
            "rack_capacity_u": 42, "dc_voltage_v": 48, "ac_voltage_v": 220,
            "devices": [{"name": "AC Server", "u": 2, "power": 10, "psu": 2,
                         "qty": 1, "breaker": 20, "type": "AC"}],
        }
        response = self.client.post(
            reverse("rack_design:save_design"), json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        record = RackDesign.objects.get()
        self.assertEqual(record.devices[0]["breaker"], 32.0)
        self.assertAlmostEqual(record.devices[0]["current_per_psu"], 22.72727, places=4)
        self.assertTrue(record.devices[0]["breaker_pass"])
        self.assertEqual(record.result_status, "PASS")

    def test_ac_device_above_fixed_32_amp_limit_fails(self):
        payload = {
            "site_name": "Cairo DC", "rack_name": "Rack AC02", "engineer": "Engineer",
            "rack_capacity_u": 42, "dc_voltage_v": 48, "ac_voltage_v": 220,
            "devices": [{"name": "Large AC Load", "u": 2, "power": 15, "psu": 2,
                         "qty": 1, "breaker": 100, "type": "AC"}],
        }
        response = self.client.post(
            reverse("rack_design:save_design"), json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        record = RackDesign.objects.get()
        self.assertEqual(record.devices[0]["breaker"], 32.0)
        self.assertFalse(record.devices[0]["breaker_pass"])
        self.assertEqual(record.result_status, "FAIL")
