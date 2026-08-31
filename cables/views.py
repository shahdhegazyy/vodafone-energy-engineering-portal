from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, HttpResponse
from django.shortcuts import redirect, render
from .calculations import calculate_at_temperature, calculate_temperature_scenarios
from .excel_service import (
    create_batch_results_workbook, create_results_workbook, read_batch_workbook,
)
from .forms import BatchCableUploadForm, CableDesignForm, OnSiteRecommendationForm
from .models import CableSelection


def dashboard(request):
    action = request.POST.get("action") if request.method == "POST" else None
    form = CableDesignForm(request.POST if action in {"calculate", "download", "save"} else None)
    batch_form = BatchCableUploadForm(
        request.POST if action == "batch_process" else None,
        request.FILES if action == "batch_process" else None,
    )
    selection = temperature_cases = overall_recommendation = None
    batch_rows = None
    batch_summary = None
    error = None

    if action in {"calculate", "download", "save"} and form.is_valid():
        try:
            temperatures = {
                "below_25": form.cleaned_data["temperature_below_25"],
                "between_25_30": form.cleaned_data["temperature_25_30"],
                "between_30_60": form.cleaned_data["temperature_30_60"],
                "above_60": form.cleaned_data["temperature_above_60"],
            }
            selection, temperature_cases, overall_recommendation = calculate_temperature_scenarios(
                form.cleaned_data["load_current_a"],
                form.cleaned_data["length_m"],
                temperatures, 3.0,
            )
            if request.POST.get("action") == "download":
                output = create_results_workbook(selection, temperature_cases, overall_recommendation)
                response = HttpResponse(
                    output.getvalue(),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                response["Content-Disposition"] = 'attachment; filename="DC_Cable_Selection_Result.xlsx"'
                return response
            if action == "save":
                required_metadata = {
                    "site_name": "Site name", "rack_name": "Rack name", "engineer": "Engineer",
                }
                missing = False
                for field, label in required_metadata.items():
                    if not form.cleaned_data.get(field):
                        form.add_error(field, f"{label} is required when saving a selection.")
                        missing = True
                if not missing:
                    CableSelection.objects.create(
                        project_reference=form.cleaned_data.get("project_reference", ""),
                        site_name=form.cleaned_data["site_name"], rack_name=form.cleaned_data["rack_name"],
                        engineer=form.cleaned_data["engineer"], notes=form.cleaned_data.get("notes", ""),
                        load_current_a=selection["load_current_a"], length_m=selection["length_m"],
                        temperature_below_25=temperatures["below_25"],
                        temperature_25_30=temperatures["between_25_30"],
                        temperature_30_60=temperatures["between_30_60"],
                        temperature_above_60=temperatures["above_60"],
                        required_breaker_a=selection["required_breaker_a"],
                        selected_breaker_a=selection["selected_breaker_a"],
                        recommended_cable_mm2=overall_recommendation["size_mm2"] if overall_recommendation else None,
                        worst_voltage_drop_v=overall_recommendation["voltage_drop"] if overall_recommendation else None,
                        result_status="PASS" if overall_recommendation else "NO MATCH",
                        calculation_details={
                            "temperature_cases": [{
                                "label": case["label"], "temperature_c": case["temperature_c"],
                                "resistivity": case["resistivity"],
                                "recommended_cable_mm2": case["recommendation"]["size_mm2"] if case["recommendation"] else None,
                                "voltage_drop_v": case["recommendation"]["voltage_drop"] if case["recommendation"] else None,
                            } for case in temperature_cases],
                        },
                    )
                    messages.success(request, "Cable selection saved to the database.")
        except ValueError as exc:
            error = str(exc)

    if action == "batch_process" and batch_form.is_valid():
        try:
            batch_rows = read_batch_workbook(batch_form.cleaned_data["workbook"])
            request.session["batch_results"] = batch_rows
            batch_summary = {
                "total": len(batch_rows),
                "pass": sum(row["result_status"] == "PASS" for row in batch_rows),
                "no_match": sum(row["result_status"] == "NO MATCH" for row in batch_rows),
                "errors": sum(row["result_status"] == "ERROR" for row in batch_rows),
            }
        except ValueError as exc:
            error = str(exc)

    return render(request, "cables/dashboard.html", {
        "form": form, "selection": selection, "temperature_cases": temperature_cases,
        "overall_recommendation": overall_recommendation, "batch_form": batch_form,
        "batch_rows": batch_rows, "batch_summary": batch_summary, "error": error,
    })


def download_batch_template(request):
    path = settings.DATA_DIR / "DC_Cable_Batch_Input_Template.xlsx"
    return FileResponse(path.open("rb"), as_attachment=True, filename=path.name)


def download_batch_results(request):
    batch_rows = request.session.get("batch_results")
    if not batch_rows:
        return redirect("cables:dashboard")
    output = create_batch_results_workbook(batch_rows)
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = 'attachment; filename="DC_Cable_Batch_Results.xlsx"'
    return response


def on_site_recommendation(request):
    """Simplified fixed-assumption cable selection for field technicians."""
    form = OnSiteRecommendationForm(request.POST or None)
    selection = results = recommendation = None
    error = None

    if request.method == "POST" and form.is_valid():
        try:
            mode = form.cleaned_data["voltage_drop_mode"]
            voltage_drop_limit = 1.5 if mode == "standard" else 3.0

            selection, results, recommendation = calculate_at_temperature(
                form.cleaned_data["load_current_a"],
                form.cleaned_data["length_m"],
                25.0,
                voltage_drop_limit,
            )

            # Standard method fallback:
            # If no approved cable can maintain 1.5 V, show the largest
            # available approved cable (70 mm²) for engineering review.
            if mode == "standard" and recommendation is None and results:
                recommendation = max(results, key=lambda row: row["size_mm2"]).copy()
                recommendation["fallback_to_largest"] = True
            elif recommendation:
                recommendation["fallback_to_largest"] = False

            if request.POST.get("action") == "save":
                is_fallback = bool(
                    recommendation
                    and recommendation.get("fallback_to_largest", False)
                )

                CableSelection.objects.create(
                    project_reference="ON-SITE",
                    site_name=form.cleaned_data["site_name"],
                    rack_name=form.cleaned_data["rack_name"],
                    engineer=form.cleaned_data["technician"],
                    notes=(
                        "Created using On-Site Recommendation: "
                        f"{'Standard 1.5 V' if mode == 'standard' else 'Optimized 3 V — under testing'}; "
                        "fixed copper conductor at 25°C."
                        + (
                            " No cable maintained the 1.5 V limit; "
                            "70 mm² was returned as the maximum available cable "
                            "for engineering review."
                            if is_fallback
                            else ""
                        )
                    ),
                    load_current_a=selection["load_current_a"],
                    length_m=selection["length_m"],
                    temperature_below_25=25,
                    temperature_25_30=25,
                    temperature_30_60=25,
                    temperature_above_60=25,
                    required_breaker_a=selection["required_breaker_a"],
                    selected_breaker_a=selection["selected_breaker_a"],
                    recommended_cable_mm2=(
                        recommendation["size_mm2"]
                        if recommendation
                        else None
                    ),
                    worst_voltage_drop_v=(
                        recommendation["voltage_drop"]
                        if recommendation
                        else None
                    ),
                    result_status=(
                        "REVIEW REQUIRED"
                        if is_fallback
                        else "PASS"
                        if recommendation
                        else "NO MATCH"
                    ),
                    calculation_details={
                        "mode": "on_site_recommendation",
                        "selection_method": mode,
                        "voltage_drop_limit_v": voltage_drop_limit,
                        "conductor": "copper",
                        "fixed_temperature_c": 25,
                        "resistivity": selection["resistivity"],
                        "fallback_to_largest": is_fallback,
                    },
                )

                messages.success(
                    request,
                    "On-site cable recommendation saved to the database.",
                )

        except ValueError as exc:
            error = str(exc)

    return render(request, "cables/on_site_recommendation.html", {
        "form": form,
        "selection": selection,
        "results": results,
        "recommendation": recommendation,
        "error": error,
        "selected_mode": (
            form.cleaned_data.get("voltage_drop_mode")
            if form.is_bound and form.is_valid()
            else None
        ),
    })
