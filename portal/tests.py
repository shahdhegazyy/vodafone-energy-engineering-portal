from django.test import SimpleTestCase, TestCase
from django.urls import reverse


class PortalRouteTests(SimpleTestCase):
    def test_home_page_links_to_both_tools(self):
        response = self.client.get(reverse("portal:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("cables:dashboard"))
        self.assertContains(response, reverse("rack_design:dashboard"))
        self.assertContains(response, reverse("cables:on_site_recommendation"))
        self.assertContains(response, "How to use cable design")
        self.assertContains(response, "How to use rack design")
        self.assertContains(response, "How to use on-site recommendation")

    def test_dc_cable_dashboard_is_available(self):
        response = self.client.get(reverse("cables:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DC cable sizing across conductor temperatures")

    def test_rack_dashboard_is_available(self):
        response = self.client.get(reverse("rack_design:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AC / DC Rack")
        self.assertContains(response, "Device Database")


class HistoryPageTests(TestCase):
    def test_history_page_is_available(self):
        response = self.client.get(reverse("portal:history"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Saved designs")
