from io import BytesIO
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from openpyxl import Workbook
from .calculations import (
    calculate_at_temperature, calculate_phase1, calculate_temperature_scenarios,
    select_breaker, temperature_corrected_resistivity,
)
from .excel_service import BATCH_HEADERS, create_batch_results_workbook, read_batch_workbook
from .models import CableSelection


class PhaseOneCalculationTests(SimpleTestCase):
    def test_100m_24a_selects_30a_cb_and_35mm2(self):
        selection, results, recommendation = calculate_phase1(24, 100, 3)
        self.assertEqual(selection["selected_breaker_a"], 30)
        self.assertEqual(recommendation["size_mm2"], 35)
        self.assertAlmostEqual(recommendation["voltage_drop"], 2.364342857, places=6)
        self.assertFalse(next(row for row in results if row["size_mm2"] == 25)["overall_pass"])

    def test_breaker_mapping_matches_reference_table(self):
        expected = {12: 15, 24: 30, 32: 40, 50: 63, 64: 80, 80: 100}
        for load, breaker in expected.items():
            self.assertEqual(select_breaker(load)[1], breaker)

    def test_load_above_approved_range_is_rejected(self):
        with self.assertRaises(ValueError):
            select_breaker(81)

    def test_resistivity_increases_with_conductor_temperature(self):
        self.assertAlmostEqual(temperature_corrected_resistivity(20), 0.01724, places=8)
        self.assertGreater(temperature_corrected_resistivity(70), temperature_corrected_resistivity(20))

    def test_four_cases_and_overall_worst_case_recommendation(self):
        temperatures = {
            "below_25": 20, "between_25_30": 27,
            "between_30_60": 45, "above_60": 70,
        }
        selection, cases, overall = calculate_temperature_scenarios(24, 100, temperatures)
        self.assertEqual(selection["selected_breaker_a"], 30)
        self.assertEqual(len(cases), 4)
        self.assertEqual(len(selection["approved_cable_checks"]), 7)
        self.assertFalse(next(row for row in selection["approved_cable_checks"] if row["size_mm2"] == 25)["overall_pass"])
        self.assertEqual(overall["size_mm2"], 35)
        self.assertEqual(overall["worst_case"]["temperature_c"], 70)
        self.assertLessEqual(overall["voltage_drop"], 3)

    def test_on_site_calculation_uses_copper_at_25_degrees(self):
        selection, results, recommendation = calculate_at_temperature(24, 100, 25)
        self.assertEqual(selection["temperature_c"], 25)
        self.assertAlmostEqual(selection["resistivity"], 0.017578766, places=8)
        self.assertEqual(selection["selected_breaker_a"], 30)
        self.assertEqual(recommendation["size_mm2"], 35)


class BatchCalculationTests(SimpleTestCase):
    def create_batch_file(self, rows):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Batch Inputs"
        sheet.append([])
        sheet.append([])
        sheet.append([])
        sheet.append(BATCH_HEADERS)
        for row in rows:
            sheet.append(row)
        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        return output

    def test_valid_batch_row_produces_recommendation(self):
        source = self.create_batch_file([[
            "PRJ-001", "Cairo DC", "Rack A01", "Engineer", "2026-08-10",
            24, 100, 20, 27, 45, 70, "Test", "Draft",
        ]])
        rows = read_batch_workbook(source)
        self.assertEqual(rows[0]["selected_breaker_a"], 30)
        self.assertEqual(rows[0]["recommended_cable_mm2"], 35)
        self.assertEqual(rows[0]["result_status"], "PASS")

    def test_invalid_row_is_reported_without_stopping_batch(self):
        source = self.create_batch_file([[
            "PRJ-002", "Cairo DC", "Rack A02", "Engineer", "2026-08-10",
            90, -1, 20, 27, 45, 70, "Invalid test", "Draft",
        ]])
        rows = read_batch_workbook(source)
        self.assertEqual(rows[0]["result_status"], "ERROR")
        self.assertIn("no more than 80 A", rows[0]["message"])

    def test_generated_batch_results_is_valid_xlsx(self):
        source = self.create_batch_file([[
            "PRJ-003", "Alex DC", "Rack B01", "Engineer", "2026-08-10",
            12, 50, 20, 27, 45, 70, "Test", "Submitted",
        ]])
        rows = read_batch_workbook(source)
        output = create_batch_results_workbook(rows)
        self.assertTrue(output.getvalue().startswith(b"PK"))


class CableSelectionDatabaseTests(TestCase):
    def test_calculated_selection_can_be_saved(self):
        response = self.client.post(reverse("cables:dashboard"), {
            "action": "save", "project_reference": "PRJ-001",
            "site_name": "Cairo DC", "rack_name": "Rack A01", "engineer": "Engineer",
            "notes": "Database test", "load_current_a": 24, "length_m": 100,
            "temperature_below_25": 20, "temperature_25_30": 27,
            "temperature_30_60": 45, "temperature_above_60": 70,
        })
        self.assertEqual(response.status_code, 200)
        record = CableSelection.objects.get()
        self.assertEqual(record.selected_breaker_a, 30)
        self.assertEqual(record.recommended_cable_mm2, 35)
        self.assertEqual(record.result_status, "PASS")

    def test_on_site_recommendation_can_be_saved(self):
        response = self.client.post(reverse("cables:on_site_recommendation"), {
            "action": "save", "voltage_drop_mode": "optimized",
            "site_name": "Cairo DC", "rack_name": "Rack T01",
            "technician": "Field Tech", "load_current_a": 24, "length_m": 100,
        })
        self.assertEqual(response.status_code, 200)
        record = CableSelection.objects.get()
        self.assertEqual(record.project_reference, "ON-SITE")
        self.assertEqual(record.recommended_cable_mm2, 35)
        self.assertEqual(record.calculation_details["fixed_temperature_c"], 25)
        self.assertEqual(record.calculation_details["voltage_drop_limit_v"], 3)

    def test_standard_on_site_mode_uses_1_5_volt_limit(self):
        response = self.client.post(reverse("cables:on_site_recommendation"), {
            "action": "save", "voltage_drop_mode": "standard",
            "site_name": "Cairo DC", "rack_name": "Rack T02",
            "technician": "Field Tech", "load_current_a": 24, "length_m": 100,
        })
        self.assertEqual(response.status_code, 200)
        record = CableSelection.objects.get()
        self.assertEqual(record.recommended_cable_mm2, 70)
        self.assertEqual(record.calculation_details["voltage_drop_limit_v"], 1.5)
