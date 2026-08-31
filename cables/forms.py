from django import forms

SITE_NAME_CHOICES = [
    ("HQ", "HQ"),
    ("TGM", "TGM"),
    ("MKTM", "MKTM"),
    ("TNT", "TNT"),
    ("MNS", "MNS"),
    ("AST", "AST"),
    ("RMD", "RMD"),
    ("BNS", "BNS"),
    ("BRJ", "BRJ"),
    ("Alex", "Alex"),
]

class CableDesignForm(forms.Form):
    project_reference = forms.CharField(max_length=100, required=False, label="Project Reference")
    site_name = forms.ChoiceField(
        choices=SITE_NAME_CHOICES,
        label="Site Name",
    )
    rack_name = forms.CharField(max_length=150, required=False, label="Rack Name")
    engineer = forms.CharField(max_length=150, required=False, label="Engineer")
    notes = forms.CharField(required=False, label="Notes", widget=forms.TextInput())
    load_current_a = forms.FloatField(
        min_value=0.01, max_value=80, initial=24, label="Load Current (A)",
        help_text="Enter the equipment DC load current. Approved Phase 1 range: up to 80 A.",
    )
    length_m = forms.FloatField(
        min_value=0.01, initial=100, label="One-way Cable Length (m)",
    )
    temperature_below_25 = forms.FloatField(initial=20, label="Conductor Temperature Below 25°C")
    temperature_25_30 = forms.FloatField(initial=27, label="Conductor Temperature 25°C to Below 30°C")
    temperature_30_60 = forms.FloatField(initial=45, label="Conductor Temperature 30°C to 60°C")
    temperature_above_60 = forms.FloatField(initial=70, label="Conductor Temperature Above 60°C")

    def clean(self):
        cleaned = super().clean()
        checks = (
            ("temperature_below_25", lambda value: value < 25, "Enter a temperature below 25°C."),
            ("temperature_25_30", lambda value: 25 <= value < 30, "Enter a temperature from 25°C to below 30°C."),
            ("temperature_30_60", lambda value: 30 <= value <= 60, "Enter a temperature from 30°C to 60°C."),
            ("temperature_above_60", lambda value: value > 60, "Enter a temperature above 60°C."),
        )
        for field, condition, message in checks:
            value = cleaned.get(field)
            if value is not None and not condition(value):
                self.add_error(field, message)
        return cleaned


class BatchCableUploadForm(forms.Form):
    workbook = forms.FileField(
        label="Completed Batch Workbook",
        help_text="Upload the completed .xlsx template. Maximum file size: 5 MB.",
    )

    def clean_workbook(self):
        workbook = self.cleaned_data["workbook"]
        if not workbook.name.lower().endswith(".xlsx"):
            raise forms.ValidationError("Please upload an .xlsx workbook.")
        if workbook.size > 5 * 1024 * 1024:
            raise forms.ValidationError("The workbook must be 5 MB or smaller.")
        return workbook


class OnSiteRecommendationForm(forms.Form):
    voltage_drop_mode = forms.ChoiceField(
        label="Selection Method",
        choices=(
            ("standard", "Standard — fixed 1.5 V limit"),
            ("optimized", "Optimized — fixed 3 V limit (under testing)"),
        ),
        initial="standard", widget=forms.RadioSelect,
    )
    site_name = forms.ChoiceField(
        choices=SITE_NAME_CHOICES,
        label="Site Name",
    )
    rack_name = forms.CharField(max_length=150, label="Rack Name")
    technician = forms.CharField(max_length=150, label="Technician Name")
    load_current_a = forms.FloatField(
        min_value=0.01, max_value=80, label="Load Current (A)",
        help_text="Enter the equipment DC load current (maximum 80 A).",
    )
    length_m = forms.FloatField(
        min_value=0.01, label="One-way Cable Length (m)",
        help_text="Measure the route from the source to the rack.",
    )
