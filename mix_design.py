from dataclasses import dataclass
from itertools import product


@dataclass
class GradeData:
    grade: str
    fck: float
    standard_deviation: float


GRADE_DATA = {
    "M20": GradeData("M20", 20.0, 4.0),
    "M25": GradeData("M25", 25.0, 4.0),
    "M30": GradeData("M30", 30.0, 5.0),
    "M35": GradeData("M35", 35.0, 5.0),
    "M40": GradeData("M40", 40.0, 6.0),
    "M45": GradeData("M45", 45.0, 6.0),
    "M50": GradeData("M50", 50.0, 6.0),
}


EXPOSURE_DATA = {
    "Mild": {
        "max_wc": 0.55,
        "min_cement": 300.0
    },
    "Moderate": {
        "max_wc": 0.50,
        "min_cement": 300.0
    },
    "Severe": {
        "max_wc": 0.45,
        "min_cement": 320.0
    },
    "Very Severe": {
        "max_wc": 0.45,
        "min_cement": 340.0
    },
    "Extreme": {
        "max_wc": 0.40,
        "min_cement": 360.0
    }
}


# ---------------------------------------------------------
# TARGET MEAN STRENGTH
# ---------------------------------------------------------

def calculate_target_mean_strength(grade, standard_deviation=None):

    if grade not in GRADE_DATA:
        raise ValueError("Unsupported concrete grade.")

    data = GRADE_DATA[grade]

    sd = (
        data.standard_deviation
        if standard_deviation is None
        else standard_deviation
    )

    return data.fck + 1.65 * sd


# ---------------------------------------------------------
# WORKABILITY
# ---------------------------------------------------------

def workability_from_slump(slump_mm):

    if slump_mm < 25:
        return "Very Low"

    elif slump_mm < 50:
        return "Low"

    elif slump_mm < 100:
        return "Medium"

    elif slump_mm <= 150:
        return "High"

    else:
        return "Very High"


# ---------------------------------------------------------
# BASIC MIX CALCULATION
# ---------------------------------------------------------

def calculate_mix(
    grade,
    slump_mm,
    exposure,
    selected_wc,
    water_content,
    specific_gravity_cement=3.15,
    specific_gravity_fine=2.65,
    specific_gravity_coarse=2.70,
    coarse_fraction=0.62,
    entrapped_air=0.01,
    scm_replacement=0.0,
    fa_moisture=0.0,
    ca_moisture=0.0,
    fa_absorption=0.0,
    ca_absorption=0.0,
    standard_deviation=None,
    minimum_cement_override=None,
    maximum_wc_override=None
):

    if grade not in GRADE_DATA:
        raise ValueError("Unsupported concrete grade.")

    if exposure not in EXPOSURE_DATA:
        raise ValueError("Unsupported exposure condition.")

    if water_content <= 0:
        raise ValueError("Water content must be greater than zero.")

    if not 0 < selected_wc <= 1:
        raise ValueError("W/C ratio must be between 0 and 1.")

    if not 0 < coarse_fraction < 1:
        raise ValueError(
            "Coarse aggregate fraction must be between 0 and 1."
        )

    if not 0 <= scm_replacement < 100:
        raise ValueError(
            "SCM replacement must be between 0 and 100%."
        )

    exposure_data = EXPOSURE_DATA[exposure]

    maximum_wc = (
        exposure_data["max_wc"]
        if maximum_wc_override is None
        else maximum_wc_override
    )

    minimum_cement = (
        exposure_data["min_cement"]
        if minimum_cement_override is None
        else minimum_cement_override
    )

    # -----------------------------------------------------
    # STRENGTH
    # -----------------------------------------------------

    target_mean = calculate_target_mean_strength(
        grade,
        standard_deviation
    )

    # -----------------------------------------------------
    # WORKABILITY
    # -----------------------------------------------------

    workability = workability_from_slump(slump_mm)

    # -----------------------------------------------------
    # WATER-CEMENT RATIO
    # -----------------------------------------------------

    adopted_wc = min(
        selected_wc,
        maximum_wc
    )

    # -----------------------------------------------------
    # TOTAL CEMENTITIOUS MATERIAL
    # -----------------------------------------------------

    calculated_cementitious = (
        water_content / adopted_wc
    )

    total_cementitious = max(
        calculated_cementitious,
        minimum_cement
    )

    actual_wc = (
        water_content / total_cementitious
    )

    # -----------------------------------------------------
    # SCM
    # -----------------------------------------------------

    scm_mass = (
        total_cementitious
        * scm_replacement
        / 100
    )

    cement_mass = (
        total_cementitious
        - scm_mass
    )

    # -----------------------------------------------------
    # ABSOLUTE VOLUME METHOD
    # -----------------------------------------------------

    cement_volume = (
        cement_mass
        / (specific_gravity_cement * 1000)
    )

    # Preliminary SCM specific gravity.
    # Replace with actual material test value later.
    scm_specific_gravity = 2.30

    scm_volume = (
        scm_mass
        / (scm_specific_gravity * 1000)
    )

    water_volume = (
        water_content / 1000
    )

    aggregate_volume = (
        1
        - cement_volume
        - scm_volume
        - water_volume
        - entrapped_air
    )

    if aggregate_volume <= 0:
        raise ValueError(
            "Aggregate volume is not positive. Check inputs."
        )

    # -----------------------------------------------------
    # AGGREGATE SPLIT
    # -----------------------------------------------------

    coarse_volume = (
        aggregate_volume
        * coarse_fraction
    )

    fine_volume = (
        aggregate_volume
        - coarse_volume
    )

    coarse_ssd = (
        coarse_volume
        * specific_gravity_coarse
        * 1000
    )

    fine_ssd = (
        fine_volume
        * specific_gravity_fine
        * 1000
    )

    # -----------------------------------------------------
    # MOISTURE CORRECTION
    # -----------------------------------------------------

    fine_batch = (
        fine_ssd
        * (1 + fa_absorption / 100)
        / (1 + fa_moisture / 100)
    )

    coarse_batch = (
        coarse_ssd
        * (1 + ca_absorption / 100)
        / (1 + ca_moisture / 100)
    )

    # Free water contribution from aggregates
    fine_free_water = (
        fine_batch
        * (fa_moisture - fa_absorption)
        / 100
    )

    coarse_free_water = (
        coarse_batch
        * (ca_moisture - ca_absorption)
        / 100
    )

    corrected_water = (
        water_content
        - fine_free_water
        - coarse_free_water
    )

    return {

        "Grade": grade,

        "Characteristic Strength (MPa)":
            GRADE_DATA[grade].fck,

        "Standard Deviation (MPa)":
            standard_deviation
            if standard_deviation is not None
            else GRADE_DATA[grade].standard_deviation,

        "Target Mean Strength (MPa)":
            round(target_mean, 2),

        "Slump (mm)":
            slump_mm,

        "Workability":
            workability,

        "Exposure":
            exposure,

        "Maximum W/C Ratio":
            round(maximum_wc, 3),

        "Adopted W/C Ratio":
            round(adopted_wc, 3),

        "Water Content (kg/m³)":
            round(water_content, 2),

        "Cement Content (kg/m³)":
            round(cement_mass, 2),

        "SCM Content (kg/m³)":
            round(scm_mass, 2),

        "Total Cementitious (kg/m³)":
            round(total_cementitious, 2),

        "Fine Aggregate SSD (kg/m³)":
            round(fine_ssd, 2),

        "Coarse Aggregate SSD (kg/m³)":
            round(coarse_ssd, 2),

        "Fine Aggregate Batch (kg/m³)":
            round(fine_batch, 2),

        "Coarse Aggregate Batch (kg/m³)":
            round(coarse_batch, 2),

        "Fine Aggregate Volume (m³)":
            round(fine_volume, 4),

        "Coarse Aggregate Volume (m³)":
            round(coarse_volume, 4),

        "Corrected Water (kg/m³)":
            round(corrected_water, 2),

        "Entrapped Air":
            entrapped_air,

        "Actual W/C Ratio":
            round(actual_wc, 3)
    }


# ---------------------------------------------------------
# COST CALCULATION
# ---------------------------------------------------------

def calculate_cost(result, rates):

    cement_cost = (
        result["Cement Content (kg/m³)"]
        * rates["cement"]
    )

    scm_cost = (
        result["SCM Content (kg/m³)"]
        * rates["scm"]
    )

    fine_cost = (
        result["Fine Aggregate Batch (kg/m³)"]
        * rates["fine"]
    )

    coarse_cost = (
        result["Coarse Aggregate Batch (kg/m³)"]
        * rates["coarse"]
    )

    water_cost = (
        result["Water Content (kg/m³)"]
        * rates["water"]
    )

    total_cost = (
        cement_cost
        + scm_cost
        + fine_cost
        + coarse_cost
        + water_cost
    )

    return {
        "Cement Cost": cement_cost,
        "SCM Cost": scm_cost,
        "Fine Aggregate Cost": fine_cost,
        "Coarse Aggregate Cost": coarse_cost,
        "Water Cost": water_cost,
        "Total Cost": total_cost
    }


# ---------------------------------------------------------
# GENERATE OPTIMIZATION CANDIDATES
# ---------------------------------------------------------

def generate_values(start, end, step):

    values = []

    current = start

    while current <= end + 0.00001:

        values.append(round(current, 4))

        current += step

    return values


def generate_candidate_mixes(
    base_inputs,
    optimization_inputs,
    rates
):

    wc_values = generate_values(
        optimization_inputs["wc_min"],
        optimization_inputs["wc_max"],
        optimization_inputs["wc_step"]
    )

    cement_values = generate_values(
        optimization_inputs["cement_min"],
        optimization_inputs["cement_max"],
        optimization_inputs["cement_step"]
    )

    scm_values = generate_values(
        optimization_inputs["scm_min"],
        optimization_inputs["scm_max"],
        optimization_inputs["scm_step"]
    )

    coarse_values = generate_values(
        optimization_inputs["coarse_min"],
        optimization_inputs["coarse_max"],
        optimization_inputs["coarse_step"]
    )

    candidates = []

    for wc, cementitious, scm, coarse_fraction in product(
        wc_values,
        cement_values,
        scm_values,
        coarse_values
    ):

        water = (
            cementitious * wc
        )

        try:

            result = calculate_mix(

                grade=base_inputs["grade"],

                slump_mm=base_inputs["slump"],

                exposure=base_inputs["exposure"],

                selected_wc=wc,

                water_content=water,

                specific_gravity_cement=
                    base_inputs["sg_cement"],

                specific_gravity_fine=
                    base_inputs["sg_fine"],

                specific_gravity_coarse=
                    base_inputs["sg_coarse"],

                coarse_fraction=
                    coarse_fraction,

                entrapped_air=
                    base_inputs["air"],

                scm_replacement=
                    scm,

                fa_moisture=
                    base_inputs["fa_moisture"],

                ca_moisture=
                    base_inputs["ca_moisture"],

                fa_absorption=
                    base_inputs["fa_absorption"],

                ca_absorption=
                    base_inputs["ca_absorption"],

                standard_deviation=
                    base_inputs["sd"],

                minimum_cement_override=
                    base_inputs["minimum_cement"],

                maximum_wc_override=
                    base_inputs["maximum_wc"]
            )

            cost = calculate_cost(
                result,
                rates
            )

            row = {
                **result,
                **cost
            }

            row["Feasible"] = (
                result["Actual W/C Ratio"]
                <= base_inputs["maximum_wc"]
                and
                result["Total Cementitious (kg/m³)"]
                >= base_inputs["minimum_cement"]
            )

            candidates.append(row)

        except ValueError:

            continue

    return candidates