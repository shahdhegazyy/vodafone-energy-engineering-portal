COPPER_RESISTIVITY_OHM_MM2_PER_M = 0.01724
COPPER_TEMPERATURE_COEFFICIENT_PER_C = 0.00393
SAFETY_MARGIN = 0.25
APPROVED_BREAKERS_A = (15, 30, 40, 63, 80, 100)

# Cable areas transcribed from the approved reference sheet.
APPROVED_AREAS_BY_BREAKER = {
    15: (6, 10, 16, 25, 35, 50, 70),
    30: (6, 10, 16, 25, 35, 50, 70),
    40: (6, 10, 16, 25, 35, 50, 70),
    63: (10, 16, 25, 35, 50, 70),
    80: (10, 16, 25, 35, 50, 70),
    100: (10, 16, 25, 35, 50, 70),
}

TEMPERATURE_CASES = (
    ("below_25", "Below 25°C"),
    ("between_25_30", "25°C to below 30°C"),
    ("between_30_60", "30°C to 60°C"),
    ("above_60", "Above 60°C"),
)


def select_breaker(load_current_a):
    """Apply 25% margin and return the next approved breaker rating."""
    required_rating = load_current_a * (1 + SAFETY_MARGIN)
    selected = next((rating for rating in APPROVED_BREAKERS_A if rating >= required_rating), None)
    if selected is None:
        raise ValueError("The load is above the approved Phase 1 range (maximum load current is 80 A).")
    return required_rating, selected


def calculate_phase1(load_current_a, length_m, voltage_drop_limit_v=3.0):
    required_breaker_a, selected_breaker_a = select_breaker(load_current_a)
    results = []
    for area_mm2 in APPROVED_AREAS_BY_BREAKER[selected_breaker_a]:
        voltage_drop_v = (
            2 * COPPER_RESISTIVITY_OHM_MM2_PER_M * length_m * load_current_a / area_mm2
        )
        maximum_length_m = (
            voltage_drop_limit_v * area_mm2
            / (2 * COPPER_RESISTIVITY_OHM_MM2_PER_M * load_current_a)
        )
        passes = voltage_drop_v <= voltage_drop_limit_v
        results.append({
            "size_mm2": area_mm2,
            "voltage_drop": voltage_drop_v,
            "maximum_length": maximum_length_m,
            "voltage_pass": passes,
            "overall_pass": passes,
        })

    recommendation = next((row for row in results if row["overall_pass"]), None)
    selection = {
        "load_current_a": load_current_a,
        "length_m": length_m,
        "safety_margin_percent": SAFETY_MARGIN * 100,
        "required_breaker_a": required_breaker_a,
        "selected_breaker_a": selected_breaker_a,
        "voltage_drop_limit_v": voltage_drop_limit_v,
        "resistivity": COPPER_RESISTIVITY_OHM_MM2_PER_M,
    }
    return selection, results, recommendation


def temperature_corrected_resistivity(temperature_c):
    """Return copper resistivity at the supplied conductor temperature."""
    return COPPER_RESISTIVITY_OHM_MM2_PER_M * (
        1 + COPPER_TEMPERATURE_COEFFICIENT_PER_C * (temperature_c - 20)
    )


def calculate_at_temperature(load_current_a, length_m, temperature_c=25.0, voltage_drop_limit_v=3.0):
    """Select the smallest approved cable at one fixed conductor temperature."""
    required_breaker_a, selected_breaker_a = select_breaker(load_current_a)
    resistivity = temperature_corrected_resistivity(temperature_c)
    results = []
    for area_mm2 in APPROVED_AREAS_BY_BREAKER[selected_breaker_a]:
        voltage_drop = 2 * resistivity * length_m * load_current_a / area_mm2
        maximum_length = voltage_drop_limit_v * area_mm2 / (2 * resistivity * load_current_a)
        results.append({
            "size_mm2": area_mm2, "voltage_drop": voltage_drop,
            "maximum_length": maximum_length,
            "overall_pass": voltage_drop <= voltage_drop_limit_v,
        })
    recommendation = next((row for row in results if row["overall_pass"]), None)

    exceeds_limit = False
    is_standard_mode = voltage_drop_limit_v == 1.5
    if recommendation is None and is_standard_mode and length_m <= 100:
        # Standard 1.5 V mode only: no approved size meets the voltage-drop
        # limit, but the route is still within the 100 m field ceiling.
        # Fall back to the largest approved cable (70 mm²) for this breaker
        # tier and flag it as exceeding the limit.
        recommendation = max(results, key=lambda row: row["size_mm2"])
        exceeds_limit = True

    selection = {
        "load_current_a": load_current_a, "length_m": length_m,
        "temperature_c": temperature_c, "resistivity": resistivity,
        "voltage_drop_limit_v": voltage_drop_limit_v,
        "safety_margin_percent": SAFETY_MARGIN * 100,
        "required_breaker_a": required_breaker_a,
        "selected_breaker_a": selected_breaker_a,
        "exceeds_limit": exceeds_limit,
    }
    return selection, results, recommendation


def calculate_temperature_scenarios(load_current_a, length_m, temperatures, voltage_drop_limit_v=3.0):
    """Calculate four conductor-temperature cases and an all-cases recommendation."""
    required_breaker_a, selected_breaker_a = select_breaker(load_current_a)
    approved_areas = APPROVED_AREAS_BY_BREAKER[selected_breaker_a]
    cases = []

    for key, label in TEMPERATURE_CASES:
        temperature_c = float(temperatures[key])
        resistivity = temperature_corrected_resistivity(temperature_c)
        rows = []
        for area_mm2 in approved_areas:
            voltage_drop = 2 * resistivity * length_m * load_current_a / area_mm2
            maximum_length = voltage_drop_limit_v * area_mm2 / (2 * resistivity * load_current_a)
            rows.append({
                "size_mm2": area_mm2,
                "voltage_drop": voltage_drop,
                "maximum_length": maximum_length,
                "overall_pass": voltage_drop <= voltage_drop_limit_v,
            })
        recommendation = next((row for row in rows if row["overall_pass"]), None)
        cases.append({
            "key": key, "label": label, "temperature_c": temperature_c,
            "resistivity": resistivity, "results": rows, "recommendation": recommendation,
        })

    approved_cable_checks = []
    overall_recommendation = None
    for area_mm2 in approved_areas:
        case_values = []
        for case in cases:
            row = next(item for item in case["results"] if item["size_mm2"] == area_mm2)
            case_values.append({
                "key": case["key"], "label": case["label"],
                "temperature_c": case["temperature_c"], "resistivity": case["resistivity"],
                "voltage_drop": row["voltage_drop"], "maximum_length": row["maximum_length"],
                "pass": row["overall_pass"],
            })
        worst_case = max(case_values, key=lambda item: item["voltage_drop"])
        check = {
            "size_mm2": area_mm2,
            "case_values": case_values,
            "worst_case": worst_case,
            "overall_pass": all(item["pass"] for item in case_values),
        }
        approved_cable_checks.append(check)
        if check["overall_pass"] and overall_recommendation is None:
            overall_recommendation = {
                "size_mm2": area_mm2, "case_values": case_values,
                "worst_case": worst_case, "voltage_drop": worst_case["voltage_drop"],
                "maximum_length": worst_case["maximum_length"],
            }

    selection = {
        "load_current_a": load_current_a, "length_m": length_m,
        "safety_margin_percent": SAFETY_MARGIN * 100,
        "required_breaker_a": required_breaker_a,
        "selected_breaker_a": selected_breaker_a,
        "voltage_drop_limit_v": voltage_drop_limit_v,
        "base_resistivity": COPPER_RESISTIVITY_OHM_MM2_PER_M,
        "temperature_coefficient": COPPER_TEMPERATURE_COEFFICIENT_PER_C,
        "approved_cable_checks": approved_cable_checks,
    }
    return selection, cases, overall_recommendation
