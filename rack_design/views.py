import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from .models import RackDesign

DC_VOLTAGE_V = 48.0
AC_VOLTAGE_V = 220.0


def dashboard(request):
    return render(request, "rack_design/dashboard.html")


@require_POST
def save_design(request):
    try:
        payload = json.loads(request.body)
        site_name = str(payload.get("site_name", "")).strip()
        rack_name = str(payload.get("rack_name", "")).strip()
        engineer = str(payload.get("engineer", "")).strip()
        if not all((site_name, rack_name, engineer)):
            return JsonResponse({"ok": False, "error": "Site name, rack name and engineer are required."}, status=400)

        capacity = int(payload["rack_capacity_u"])
        # System supply voltages are fixed engineering assumptions. Never use
        # client-provided voltage values when recalculating a saved design.
        dc_voltage = DC_VOLTAGE_V
        ac_voltage = AC_VOLTAGE_V
        devices = payload.get("devices", [])
        if capacity <= 0 or not isinstance(devices, list):
            raise ValueError

        used = installed = circuits = 0
        total_power = 0.0
        failure = ""
        clean_devices = []
        for raw in devices:
            device = {
                "name": str(raw.get("name", "Device"))[:150],
                "u": int(raw["u"]), "power": float(raw["power"]),
                "psu": int(raw["psu"]), "qty": int(raw["qty"]),
                "type": "AC" if raw.get("type") == "AC" else "DC",
            }
            # AC equipment is supplied from a PDU with a fixed 32 A allowable rating.
            # Do not trust or use a client-provided breaker value for AC devices.
            device["breaker"] = 32.0 if device["type"] == "AC" else float(raw["breaker"])
            if min(device["u"], device["psu"]) <= 0 or device["qty"] < 0 or device["power"] < 0:
                raise ValueError
            voltage = ac_voltage if device["type"] == "AC" else dc_voltage
            current_per_psu = device["power"] * 1000 / voltage / device["psu"]
            device["current_per_psu"] = current_per_psu
            device["breaker_pass"] = current_per_psu <= device["breaker"]
            clean_devices.append(device)
            for _ in range(device["qty"]):
                if used + device["u"] > capacity:
                    failure = f'{device["name"]} exceeds rack capacity.'
                    break
                if not device["breaker_pass"]:
                    failure = f'{device["name"]} exceeds its {"fixed 32 A PDU" if device["type"] == "AC" else "selected breaker"}.'
                    break
                used += device["u"]
                total_power += device["power"]
                installed += 1
                circuits += device["psu"]
            if failure:
                break

        record = RackDesign.objects.create(
            project_reference=str(payload.get("project_reference", ""))[:100],
            site_name=site_name, rack_name=rack_name, engineer=engineer,
            notes=str(payload.get("notes", "")), rack_capacity_u=capacity,
            used_rack_u=used, dc_voltage_v=dc_voltage, ac_voltage_v=ac_voltage,
            total_power_kw=total_power, installed_devices=installed,
            protected_circuits=circuits, result_status="FAIL" if failure else "PASS",
            result_message=failure or "All requested devices passed.", devices=clean_devices,
        )
        return JsonResponse({
    "ok": True,
    "id": record.pk,
    "message": "Rack design saved to the database.",

    "results": {
        "rack_capacity_u": capacity,
        "used_rack_u": used,
        "remaining_rack_u": capacity - used,
        "total_power_kw": round(total_power, 2),
        "installed_devices": installed,
        "protected_circuits": circuits,
        "status": "FAIL" if failure else "PASS",

        "devices": clean_devices,
    }
})
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "The rack design contains invalid values."}, status=400)
