import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from mix_design import (
    calculate_mix,
    calculate_cost,
    generate_candidate_mixes,
    GRADE_DATA,
    EXPOSURE_DATA
)


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="Concrete Mix Optimization Tool",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ Sustainable Concrete Mix Optimization Tool")

st.markdown(
    """
### Python-Based Concrete Mix Optimization and Cost Analysis

This tool calculates a conventional/reference concrete mix and
generates user-defined candidate mixes for optimization based on
cost, cementitious content, water-cement ratio and SCM content.
"""
)

st.warning(
    "Academic project prototype: final concrete proportions must be "
    "verified using IS 10262:2019, IS 456, actual material properties "
    "and laboratory trial mixes."
)


# ============================================================
# SIDEBAR - PROJECT INPUTS
# ============================================================

st.sidebar.header("Project Inputs")


grade = st.sidebar.selectbox(
    "Concrete Grade",
    list(GRADE_DATA.keys()),
    index=list(GRADE_DATA.keys()).index("M25")
)


slump = st.sidebar.number_input(
    "Slump / Workability (mm)",
    min_value=25,
    max_value=200,
    value=100,
    step=5
)


exposure = st.sidebar.selectbox(
    "Exposure Condition",
    list(EXPOSURE_DATA.keys()),
    index=1
)


# ============================================================
# MATERIAL PROPERTIES
# ============================================================

st.sidebar.subheader("Material Properties")


sg_cement = st.sidebar.number_input(
    "Cement Specific Gravity",
    min_value=2.50,
    max_value=3.50,
    value=3.15,
    step=0.01
)


sg_fine = st.sidebar.number_input(
    "Fine Aggregate Specific Gravity",
    min_value=2.20,
    max_value=3.00,
    value=2.65,
    step=0.01
)


sg_coarse = st.sidebar.number_input(
    "Coarse Aggregate Specific Gravity",
    min_value=2.20,
    max_value=3.20,
    value=2.70,
    step=0.01
)


# ============================================================
# AGGREGATE CONDITIONS
# ============================================================

st.sidebar.subheader("Aggregate Conditions")


fa_moisture = st.sidebar.number_input(
    "Fine Aggregate Moisture (%)",
    min_value=0.0,
    max_value=10.0,
    value=2.0,
    step=0.1
)


ca_moisture = st.sidebar.number_input(
    "Coarse Aggregate Moisture (%)",
    min_value=0.0,
    max_value=10.0,
    value=1.0,
    step=0.1
)


fa_absorption = st.sidebar.number_input(
    "Fine Aggregate Absorption (%)",
    min_value=0.0,
    max_value=10.0,
    value=1.0,
    step=0.1
)


ca_absorption = st.sidebar.number_input(
    "Coarse Aggregate Absorption (%)",
    min_value=0.0,
    max_value=10.0,
    value=0.5,
    step=0.1
)


# ============================================================
# CONVENTIONAL MIX
# ============================================================

st.sidebar.subheader("Conventional / Reference Mix")


water_content = st.sidebar.number_input(
    "Water Content (kg/m³)",
    min_value=100.0,
    max_value=250.0,
    value=186.0,
    step=1.0
)


selected_wc = st.sidebar.number_input(
    "Selected W/C Ratio",
    min_value=0.25,
    max_value=0.70,
    value=0.45,
    step=0.01
)


coarse_fraction = st.sidebar.number_input(
    "Coarse Aggregate Fraction",
    min_value=0.40,
    max_value=0.75,
    value=0.62,
    step=0.01
)


entrapped_air = st.sidebar.number_input(
    "Entrapped Air Fraction",
    min_value=0.0,
    max_value=0.10,
    value=0.01,
    step=0.005
)


# ============================================================
# SCM
# ============================================================

st.sidebar.subheader("Supplementary Cementitious Material")


scm_replacement = st.sidebar.slider(
    "SCM Replacement (%)",
    min_value=0,
    max_value=50,
    value=0,
    step=5
)


# ============================================================
# MATERIAL COST
# ============================================================

st.sidebar.subheader("Material Cost")


# IMPORTANT:
# Minimum changed from 1.0 to 0.01 because default is ₹0.45/kg.

cement_rate = st.sidebar.number_input(
    "Cement Rate (₹/kg)",
    min_value=0.01,
    max_value=100.0,
    value=0.45,
    step=0.05
)


scm_rate = st.sidebar.number_input(
    "SCM Rate (₹/kg)",
    min_value=0.01,
    max_value=100.0,
    value=0.20,
    step=0.05
)


fine_rate = st.sidebar.number_input(
    "Fine Aggregate Rate (₹/kg)",
    min_value=0.01,
    max_value=50.0,
    value=0.08,
    step=0.01
)


coarse_rate = st.sidebar.number_input(
    "Coarse Aggregate Rate (₹/kg)",
    min_value=0.01,
    max_value=50.0,
    value=0.07,
    step=0.01
)


water_rate = st.sidebar.number_input(
    "Water Rate (₹/kg)",
    min_value=0.001,
    max_value=10.0,
    value=0.02,
    step=0.005
)


# ============================================================
# STRENGTH / DURABILITY
# ============================================================

default_sd = GRADE_DATA[grade].standard_deviation


standard_deviation = st.sidebar.number_input(
    "Standard Deviation, S (MPa)",
    min_value=1.0,
    max_value=10.0,
    value=float(default_sd),
    step=0.1
)


default_max_wc = EXPOSURE_DATA[exposure]["max_wc"]
default_min_cement = EXPOSURE_DATA[exposure]["min_cement"]


st.sidebar.subheader("Durability Limits")


maximum_wc = st.sidebar.number_input(
    "Maximum W/C Ratio",
    min_value=0.25,
    max_value=0.70,
    value=float(default_max_wc),
    step=0.01
)


minimum_cement = st.sidebar.number_input(
    "Minimum Cementitious Content (kg/m³)",
    min_value=200.0,
    max_value=500.0,
    value=float(default_min_cement),
    step=5.0
)


calculate_button = st.sidebar.button(
    "Calculate Conventional Mix",
    type="primary",
    use_container_width=True
)


# ============================================================
# COST DICTIONARY
# ============================================================

rates = {
    "cement": cement_rate,
    "scm": scm_rate,
    "fine": fine_rate,
    "coarse": coarse_rate,
    "water": water_rate
}


# ============================================================
# BASE INPUTS
# ============================================================

base_inputs = {
    "grade": grade,
    "slump": slump,
    "exposure": exposure,
    "sg_cement": sg_cement,
    "sg_fine": sg_fine,
    "sg_coarse": sg_coarse,
    "air": entrapped_air,
    "fa_moisture": fa_moisture,
    "ca_moisture": ca_moisture,
    "fa_absorption": fa_absorption,
    "ca_absorption": ca_absorption,
    "sd": standard_deviation,
    "minimum_cement": minimum_cement,
    "maximum_wc": maximum_wc
}


# ============================================================
# SESSION STATE
# ============================================================

if "conventional_result" not in st.session_state:
    st.session_state.conventional_result = None

if "conventional_cost" not in st.session_state:
    st.session_state.conventional_cost = None

if "optimization_results" not in st.session_state:
    st.session_state.optimization_results = None


# ============================================================
# CONVENTIONAL MIX CALCULATION
# ============================================================

if calculate_button:

    try:

        conventional_result = calculate_mix(
            grade=grade,
            slump_mm=slump,
            exposure=exposure,
            selected_wc=selected_wc,
            water_content=water_content,
            specific_gravity_cement=sg_cement,
            specific_gravity_fine=sg_fine,
            specific_gravity_coarse=sg_coarse,
            coarse_fraction=coarse_fraction,
            entrapped_air=entrapped_air,
            scm_replacement=scm_replacement,
            fa_moisture=fa_moisture,
            ca_moisture=ca_moisture,
            fa_absorption=fa_absorption,
            ca_absorption=ca_absorption,
            standard_deviation=standard_deviation,
            minimum_cement_override=minimum_cement,
            maximum_wc_override=maximum_wc
        )

        conventional_cost = calculate_cost(
            conventional_result,
            rates
        )

        st.session_state.conventional_result = conventional_result
        st.session_state.conventional_cost = conventional_cost

        st.success(
            "Conventional/reference mix calculated successfully."
        )

    except Exception as e:

        st.error(
            f"Calculation error: {e}"
        )


# ============================================================
# DISPLAY CONVENTIONAL MIX
# ============================================================

if st.session_state.conventional_result is not None:

    result = st.session_state.conventional_result
    cost = st.session_state.conventional_cost

    st.header("1. Conventional / Reference Mix")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Grade",
        result["Grade"]
    )

    col2.metric(
        "Target Mean Strength",
        f'{result["Target Mean Strength (MPa)"]} MPa'
    )

    col3.metric(
        "Actual W/C Ratio",
        result["Actual W/C Ratio"]
    )

    col4.metric(
        "Total Cost",
        f'₹{cost["Total Cost"]:,.2f}/m³'
    )


    st.subheader("Mix Proportions")

    conventional_table = pd.DataFrame({

        "Material": [
            "Water",
            "Cement",
            "SCM",
            "Fine Aggregate",
            "Coarse Aggregate"
        ],

        "Quantity (kg/m³)": [
            result["Corrected Water (kg/m³)"],
            result["Cement Content (kg/m³)"],
            result["SCM Content (kg/m³)"],
            result["Fine Aggregate Batch (kg/m³)"],
            result["Coarse Aggregate Batch (kg/m³)"]
        ]

    })

    st.dataframe(
        conventional_table,
        use_container_width=True,
        hide_index=True
    )


    st.subheader("Engineering Parameters")

    engineering_table = pd.DataFrame({

        "Parameter": [
            "Concrete Grade",
            "Slump",
            "Exposure",
            "Workability",
            "Target Mean Strength",
            "Maximum W/C",
            "Actual W/C",
            "Total Cementitious",
            "Fine Aggregate Volume",
            "Coarse Aggregate Volume"
        ],

        "Value": [
            result["Grade"],
            f'{result["Slump (mm)"]} mm',
            result["Exposure"],
            result["Workability"],
            f'{result["Target Mean Strength (MPa)"]} MPa',
            result["Maximum W/C Ratio"],
            result["Actual W/C Ratio"],
            f'{result["Total Cementitious (kg/m³)"]} kg/m³',
            f'{result["Fine Aggregate Volume (m³)"]} m³',
            f'{result["Coarse Aggregate Volume (m³)"]} m³'
        ]

    })

    st.dataframe(
        engineering_table,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# OPTIMIZATION
# ============================================================

st.header("2. Mix Optimization")

st.write(
    "Define the ranges to be investigated. The program automatically "
    "generates combinations instead of using fixed Mix 1, Mix 2, "
    "Mix 3 and Mix 4."
)


opt_col1, opt_col2, opt_col3, opt_col4 = st.columns(4)


with opt_col1:

    wc_min = st.number_input(
        "W/C Minimum",
        min_value=0.25,
        max_value=0.70,
        value=0.35,
        step=0.01
    )

    wc_max = st.number_input(
        "W/C Maximum",
        min_value=0.25,
        max_value=0.70,
        value=0.55,
        step=0.01
    )

    wc_step = st.number_input(
        "W/C Step",
        min_value=0.01,
        max_value=0.20,
        value=0.02,
        step=0.01
    )


with opt_col2:

    cement_min = st.number_input(
        "Cementitious Minimum (kg/m³)",
        min_value=200.0,
        max_value=500.0,
        value=300.0,
        step=10.0
    )

    cement_max = st.number_input(
        "Cementitious Maximum (kg/m³)",
        min_value=200.0,
        max_value=700.0,
        value=450.0,
        step=10.0
    )

    cement_step = st.number_input(
        "Cementitious Step",
        min_value=5.0,
        max_value=100.0,
        value=25.0,
        step=5.0
    )


with opt_col3:

    scm_min = st.number_input(
        "SCM Minimum (%)",
        min_value=0.0,
        max_value=50.0,
        value=0.0,
        step=5.0
    )

    scm_max = st.number_input(
        "SCM Maximum (%)",
        min_value=0.0,
        max_value=50.0,
        value=30.0,
        step=5.0
    )

    scm_step = st.number_input(
        "SCM Step (%)",
        min_value=1.0,
        max_value=20.0,
        value=5.0,
        step=1.0
    )


with opt_col4:

    coarse_min = st.number_input(
        "Coarse Fraction Minimum",
        min_value=0.40,
        max_value=0.75,
        value=0.55,
        step=0.01
    )

    coarse_max = st.number_input(
        "Coarse Fraction Maximum",
        min_value=0.40,
        max_value=0.75,
        value=0.68,
        step=0.01
    )

    coarse_step = st.number_input(
        "Coarse Fraction Step",
        min_value=0.01,
        max_value=0.10,
        value=0.02,
        step=0.01
    )


optimization_inputs = {

    "wc_min": wc_min,
    "wc_max": wc_max,
    "wc_step": wc_step,

    "cement_min": cement_min,
    "cement_max": cement_max,
    "cement_step": cement_step,

    "scm_min": scm_min,
    "scm_max": scm_max,
    "scm_step": scm_step,

    "coarse_min": coarse_min,
    "coarse_max": coarse_max,
    "coarse_step": coarse_step
}


objective = st.selectbox(
    "Optimization Objective",
    [
        "Minimum Cost",
        "Minimum Cementitious Content",
        "Balanced Cost and Cementitious Content"
    ]
)


run_optimization = st.button(
    "🔎 Generate and Optimize Mixes",
    type="primary"
)


# ============================================================
# RUN OPTIMIZATION
# ============================================================

if run_optimization:

    if wc_min > wc_max:

        st.error(
            "W/C minimum cannot be greater than W/C maximum."
        )

    elif cement_min > cement_max:

        st.error(
            "Cementitious minimum cannot be greater than maximum."
        )

    elif scm_min > scm_max:

        st.error(
            "SCM minimum cannot be greater than maximum."
        )

    elif coarse_min > coarse_max:

        st.error(
            "Coarse fraction minimum cannot be greater than maximum."
        )

    else:

        with st.spinner(
            "Generating candidate mixes and evaluating feasibility..."
        ):

            try:

                candidates = generate_candidate_mixes(
                    base_inputs,
                    optimization_inputs,
                    rates
                )

                df = pd.DataFrame(candidates)

                if df.empty:

                    st.error(
                        "No candidate mixes could be generated. "
                        "Try wider ranges."
                    )

                else:

                    feasible_df = df[
                        df["Feasible"] == True
                    ].copy()


                    if feasible_df.empty:

                        st.warning(
                            "Candidate mixes were generated, but none "
                            "satisfy the current constraints."
                        )

                        st.session_state.optimization_results = df

                    else:

                        min_cost = feasible_df["Total Cost"].min()
                        max_cost = feasible_df["Total Cost"].max()

                        min_cement = feasible_df[
                            "Total Cementitious (kg/m³)"
                        ].min()

                        max_cement = feasible_df[
                            "Total Cementitious (kg/m³)"
                        ].max()


                        if max_cost != min_cost:

                            feasible_df["Cost Score"] = (
                                feasible_df["Total Cost"] - min_cost
                            ) / (
                                max_cost - min_cost
                            )

                        else:

                            feasible_df["Cost Score"] = 0.0


                        if max_cement != min_cement:

                            feasible_df["Cement Score"] = (
                                feasible_df[
                                    "Total Cementitious (kg/m³)"
                                ] - min_cement
                            ) / (
                                max_cement - min_cement
                            )

                        else:

                            feasible_df["Cement Score"] = 0.0


                        feasible_df["Balanced Score"] = (
                            0.5 * feasible_df["Cost Score"]
                            +
                            0.5 * feasible_df["Cement Score"]
                        )


                        feasible_df = feasible_df.sort_values(
                            by="Total Cost"
                        ).reset_index(drop=True)


                        feasible_df["Rank"] = range(
                            1,
                            len(feasible_df) + 1
                        )


                        st.session_state.optimization_results = (
                            feasible_df
                        )


                        st.success(
                            f"Optimization completed. "
                            f"{len(feasible_df)} feasible candidate "
                            f"mixes found."
                        )


            except Exception as e:

                st.error(
                    f"Optimization error: {e}"
                )


# ============================================================
# OPTIMIZATION RESULTS
# ============================================================

if st.session_state.optimization_results is not None:

    df = st.session_state.optimization_results.copy()

    st.header("3. Optimization Results")

    feasible_df = df[
        df["Feasible"] == True
    ].copy()


    if not feasible_df.empty:

        if objective == "Minimum Cost":

            optimum = feasible_df.loc[
                feasible_df["Total Cost"].idxmin()
            ]

        elif objective == "Minimum Cementitious Content":

            optimum = feasible_df.loc[
                feasible_df[
                    "Total Cementitious (kg/m³)"
                ].idxmin()
            ]

        else:

            optimum = feasible_df.loc[
                feasible_df[
                    "Balanced Score"
                ].idxmin()
            ]


        col1, col2, col3, col4, col5 = st.columns(5)


        col1.metric(
            "Best Rank",
            int(optimum.get("Rank", 1))
        )

        col2.metric(
            "Total Cost",
            f'₹{optimum["Total Cost"]:,.2f}/m³'
        )

        col3.metric(
            "Cementitious",
            f'{optimum["Total Cementitious (kg/m³)"]:,.1f} kg/m³'
        )

        col4.metric(
            "W/C Ratio",
            optimum["Actual W/C Ratio"]
        )

        col5.metric(
            "SCM",
            f'{optimum["SCM Content (kg/m³)"]:,.1f} kg/m³'
        )


        # ====================================================
        # COMPARISON
        # ====================================================

        st.subheader(
            "Conventional vs Optimized Mix"
        )


        conventional = st.session_state.conventional_result
        conventional_cost = st.session_state.conventional_cost


        if conventional is not None:

            comparison = pd.DataFrame({

                "Parameter": [
                    "Water (kg/m³)",
                    "Cement (kg/m³)",
                    "SCM (kg/m³)",
                    "Fine Aggregate (kg/m³)",
                    "Coarse Aggregate (kg/m³)",
                    "Total Cementitious (kg/m³)",
                    "W/C Ratio",
                    "Total Cost (₹/m³)"
                ],

                "Conventional": [

                    conventional[
                        "Corrected Water (kg/m³)"
                    ],

                    conventional[
                        "Cement Content (kg/m³)"
                    ],

                    conventional[
                        "SCM Content (kg/m³)"
                    ],

                    conventional[
                        "Fine Aggregate Batch (kg/m³)"
                    ],

                    conventional[
                        "Coarse Aggregate Batch (kg/m³)"
                    ],

                    conventional[
                        "Total Cementitious (kg/m³)"
                    ],

                    conventional[
                        "Actual W/C Ratio"
                    ],

                    conventional_cost[
                        "Total Cost"
                    ]

                ],

                "Optimized": [

                    optimum[
                        "Corrected Water (kg/m³)"
                    ],

                    optimum[
                        "Cement Content (kg/m³)"
                    ],

                    optimum[
                        "SCM Content (kg/m³)"
                    ],

                    optimum[
                        "Fine Aggregate Batch (kg/m³)"
                    ],

                    optimum[
                        "Coarse Aggregate Batch (kg/m³)"
                    ],

                    optimum[
                        "Total Cementitious (kg/m³)"
                    ],

                    optimum[
                        "Actual W/C Ratio"
                    ],

                    optimum[
                        "Total Cost"
                    ]

                ]

            })


            comparison["Change"] = (
                comparison["Optimized"]
                -
                comparison["Conventional"]
            )


            st.dataframe(
                comparison,
                use_container_width=True,
                hide_index=True
            )


            # =================================================
            # SAVINGS
            # =================================================

            cost_saving = (
                conventional_cost["Total Cost"]
                -
                optimum["Total Cost"]
            )


            if conventional_cost["Total Cost"] != 0:

                cost_saving_percent = (
                    cost_saving
                    /
                    conventional_cost["Total Cost"]
                    *
                    100
                )

            else:

                cost_saving_percent = 0


            cement_reduction = (
                conventional[
                    "Total Cementitious (kg/m³)"
                ]
                -
                optimum[
                    "Total Cementitious (kg/m³)"
                ]
            )


            metric1, metric2, metric3 = st.columns(3)


            metric1.metric(
                "Cost Saving",
                f"₹{cost_saving:,.2f}/m³"
            )


            metric2.metric(
                "Cost Reduction",
                f"{cost_saving_percent:.2f}%"
            )


            metric3.metric(
                "Cementitious Reduction",
                f"{cement_reduction:,.2f} kg/m³"
            )


            # =================================================
            # CURVE 1
            # =================================================

            st.subheader(
                "Optimization Curve: Cost vs W/C Ratio"
            )


            curve_df = feasible_df[
                [
                    "Actual W/C Ratio",
                    "Total Cost"
                ]
            ].copy()


            curve_df = (
                curve_df
                .groupby(
                    "Actual W/C Ratio",
                    as_index=False
                )["Total Cost"]
                .min()
                .sort_values(
                    "Actual W/C Ratio"
                )
            )


            if len(curve_df) >= 2:

                fig1 = px.line(
                    curve_df,
                    x="Actual W/C Ratio",
                    y="Total Cost",
                    markers=True,
                    title="Minimum Feasible Cost at Different W/C Ratios"
                )


                fig1.update_layout(
                    xaxis_title="Water-Cement Ratio",
                    yaxis_title="Minimum Cost (₹/m³)"
                )


                st.plotly_chart(
                    fig1,
                    use_container_width=True
                )

            else:

                st.info(
                    "Increase the W/C range or reduce the W/C step "
                    "to generate a meaningful curve."
                )


            # =================================================
            # CURVE 2
            # =================================================

            st.subheader(
                "Optimization Curve: Cost vs Cementitious Content"
            )


            curve_df2 = feasible_df[
                [
                    "Total Cementitious (kg/m³)",
                    "Total Cost"
                ]
            ].copy()


            curve_df2 = (
                curve_df2
                .groupby(
                    "Total Cementitious (kg/m³)",
                    as_index=False
                )["Total Cost"]
                .min()
                .sort_values(
                    "Total Cementitious (kg/m³)"
                )
            )


            if len(curve_df2) >= 2:

                fig2 = px.line(
                    curve_df2,
                    x="Total Cementitious (kg/m³)",
                    y="Total Cost",
                    markers=True,
                    title="Minimum Feasible Cost vs Cementitious Content"
                )


                fig2.update_layout(
                    xaxis_title="Total Cementitious Content (kg/m³)",
                    yaxis_title="Minimum Cost (₹/m³)"
                )


                st.plotly_chart(
                    fig2,
                    use_container_width=True
                )

            else:

                st.info(
                    "Increase the cementitious-content range "
                    "to generate the curve."
                )


            # =================================================
            # CURVE 3
            # =================================================

            st.subheader(
                "Optimization Curve: Cost vs SCM Content"
            )


            curve_df3 = feasible_df[
                [
                    "SCM Content (kg/m³)",
                    "Total Cost"
                ]
            ].copy()


            curve_df3 = (
                curve_df3
                .groupby(
                    "SCM Content (kg/m³)",
                    as_index=False
                )["Total Cost"]
                .min()
                .sort_values(
                    "SCM Content (kg/m³)"
                )
            )


            if len(curve_df3) >= 2:

                fig3 = px.line(
                    curve_df3,
                    x="SCM Content (kg/m³)",
                    y="Total Cost",
                    markers=True,
                    title="Minimum Feasible Cost vs SCM Content"
                )


                fig3.update_layout(
                    xaxis_title="SCM Content (kg/m³)",
                    yaxis_title="Minimum Cost (₹/m³)"
                )


                st.plotly_chart(
                    fig3,
                    use_container_width=True
                )

            else:

                st.info(
                    "Increase the SCM range to generate the curve."
                )


            # =================================================
            # TOP MIXES
            # =================================================

            st.subheader(
                "Top Feasible Mixes"
            )


            display_columns = [
                "Rank",
                "Actual W/C Ratio",
                "Total Cementitious (kg/m³)",
                "SCM Content (kg/m³)",
                "Fine Aggregate Batch (kg/m³)",
                "Coarse Aggregate Batch (kg/m³)",
                "Total Cost"
            ]


            top_df = feasible_df[
                display_columns
            ].head(20)


            st.dataframe(
                top_df,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# PDF REPORT FUNCTION
# ============================================================

def create_pdf_report(
    conventional_result,
    conventional_cost,
    optimum,
    comparison,
    objective,
    candidate_count
):

    buffer = BytesIO()


    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm
    )


    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal_style = styles["BodyText"]


    story = []


    story.append(
        Paragraph(
            "Python-Based Concrete Mix Optimization and Cost Analysis",
            title_style
        )
    )


    story.append(
        Spacer(1, 8)
    )


    story.append(
        Paragraph(
            "Sustainable Concrete Mix Optimization Tool",
            heading_style
        )
    )


    story.append(
        Spacer(1, 10)
    )


    story.append(
        Paragraph(
            "This report presents the conventional/reference mix "
            "and the optimized mix obtained from the user-defined "
            "optimization ranges.",
            normal_style
        )
    )


    story.append(
        Spacer(1, 10)
    )


    # ========================================================
    # PROJECT INPUTS
    # ========================================================

    story.append(
        Paragraph(
            "1. Project Inputs",
            heading_style
        )
    )


    input_data = [

        ["Parameter", "Value"],

        [
            "Concrete Grade",
            conventional_result["Grade"]
        ],

        [
            "Slump",
            f'{conventional_result["Slump (mm)"]} mm'
        ],

        [
            "Exposure",
            conventional_result["Exposure"]
        ],

        [
            "Target Mean Strength",
            f'{conventional_result["Target Mean Strength (MPa)"]} MPa'
        ],

        [
            "Maximum W/C Ratio",
            str(conventional_result["Maximum W/C Ratio"])
        ],

        [
            "Actual W/C Ratio",
            str(conventional_result["Actual W/C Ratio"])
        ]

    ]


    input_table = Table(
        input_data,
        colWidths=[
            75 * mm,
            75 * mm
        ]
    )


    input_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            )

        ])
    )


    story.append(
        input_table
    )


    story.append(
        Spacer(1, 12)
    )


    # ========================================================
    # CONVENTIONAL MIX
    # ========================================================

    story.append(
        Paragraph(
            "2. Conventional / Reference Mix",
            heading_style
        )
    )


    conventional_data = [

        ["Material", "Quantity (kg/m³)"],

        [
            "Water",
            str(
                conventional_result[
                    "Corrected Water (kg/m³)"
                ]
            )
        ],

        [
            "Cement",
            str(
                conventional_result[
                    "Cement Content (kg/m³)"
                ]
            )
        ],

        [
            "SCM",
            str(
                conventional_result[
                    "SCM Content (kg/m³)"
                ]
            )
        ],

        [
            "Fine Aggregate",
            str(
                conventional_result[
                    "Fine Aggregate Batch (kg/m³)"
                ]
            )
        ],

        [
            "Coarse Aggregate",
            str(
                conventional_result[
                    "Coarse Aggregate Batch (kg/m³)"
                ]
            )
        ]

    ]


    conventional_table = Table(
        conventional_data,
        colWidths=[
            75 * mm,
            75 * mm
        ]
    )


    conventional_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            )

        ])
    )


    story.append(
        conventional_table
    )


    story.append(
        Spacer(1, 8)
    )


    story.append(
        Paragraph(
            f'Conventional mix cost: '
            f'Rs. {conventional_cost["Total Cost"]:,.2f}/m³',
            normal_style
        )
    )


    story.append(
        Spacer(1, 12)
    )


    # ========================================================
    # OPTIMIZED MIX
    # ========================================================

    story.append(
        Paragraph(
            "3. Optimized Mix",
            heading_style
        )
    )


    optimized_data = [

        ["Parameter", "Value"],

        [
            "Optimization Objective",
            objective
        ],

        [
            "Water",
            f'{optimum["Corrected Water (kg/m³)"]:.2f} kg/m³'
        ],

        [
            "Cement",
            f'{optimum["Cement Content (kg/m³)"]:.2f} kg/m³'
        ],

        [
            "SCM",
            f'{optimum["SCM Content (kg/m³)"]:.2f} kg/m³'
        ],

        [
            "Fine Aggregate",
            f'{optimum["Fine Aggregate Batch (kg/m³)"]:.2f} kg/m³'
        ],

        [
            "Coarse Aggregate",
            f'{optimum["Coarse Aggregate Batch (kg/m³)"]:.2f} kg/m³'
        ],

        [
            "Total Cementitious",
            f'{optimum["Total Cementitious (kg/m³)"]:.2f} kg/m³'
        ],

        [
            "Actual W/C Ratio",
            str(optimum["Actual W/C Ratio"])
        ],

        [
            "Total Cost",
            f'Rs. {optimum["Total Cost"]:,.2f}/m³'
        ]

    ]


    optimized_table = Table(
        optimized_data,
        colWidths=[
            75 * mm,
            75 * mm
        ]
    )


    optimized_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            )

        ])
    )


    story.append(
        optimized_table
    )


    story.append(
        Spacer(1, 12)
    )


    # ========================================================
    # COMPARISON
    # ========================================================

    story.append(
        Paragraph(
            "4. Conventional vs Optimized Comparison",
            heading_style
        )
    )


    comparison_data = [
        [
            "Parameter",
            "Conventional",
            "Optimized",
            "Change"
        ]
    ]


    for _, row in comparison.iterrows():

        comparison_data.append([

            str(row["Parameter"]),

            (
                f'{row["Conventional"]:.2f}'
                if isinstance(
                    row["Conventional"],
                    (int, float)
                )
                else str(row["Conventional"])
            ),

            (
                f'{row["Optimized"]:.2f}'
                if isinstance(
                    row["Optimized"],
                    (int, float)
                )
                else str(row["Optimized"])
            ),

            (
                f'{row["Change"]:.2f}'
                if isinstance(
                    row["Change"],
                    (int, float)
                )
                else str(row["Change"])
            )

        ])


    comparison_table = Table(
        comparison_data,
        colWidths=[
            55 * mm,
            35 * mm,
            35 * mm,
            35 * mm
        ]
    )


    comparison_table.setStyle(
        TableStyle([

            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),

            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8
            )

        ])
    )


    story.append(
        comparison_table
    )


    story.append(
        Spacer(1, 12)
    )


    # ========================================================
    # INTERPRETATION
    # ========================================================

    cost_saving = (
        conventional_cost["Total Cost"]
        -
        optimum["Total Cost"]
    )


    if conventional_cost["Total Cost"] != 0:

        cost_saving_percent = (
            cost_saving
            /
            conventional_cost["Total Cost"]
            *
            100
        )

    else:

        cost_saving_percent = 0


    cement_reduction = (
        conventional_result[
            "Total Cementitious (kg/m³)"
        ]
        -
        optimum[
            "Total Cementitious (kg/m³)"
        ]
    )


    story.append(
        Paragraph(
            "5. Engineering Interpretation",
            heading_style
        )
    )


    interpretation = (

        f"The optimization procedure evaluated "
        f"{candidate_count} feasible candidate mixes. "

        f"The selected optimum was obtained using the objective "
        f"of {objective.lower()}. "

        f"The optimized mix has a calculated material cost of "
        f"Rs. {optimum['Total Cost']:,.2f}/m³ compared with "
        f"Rs. {conventional_cost['Total Cost']:,.2f}/m³ for the "
        f"conventional/reference mix. "

        f"The calculated cost difference is "
        f"Rs. {cost_saving:,.2f}/m³, corresponding to approximately "
        f"{cost_saving_percent:.2f}% change. "

        f"The difference in total cementitious material is "
        f"approximately {cement_reduction:.2f} kg/m³."

    )


    story.append(
        Paragraph(
            interpretation,
            normal_style
        )
    )


    story.append(
        Spacer(1, 10)
    )


    story.append(
        Paragraph(
            "The optimized proportions are computational results "
            "and should be validated through laboratory trial mixes "
            "before being adopted for construction. Final proportioning "
            "should follow applicable provisions of IS 10262:2019 "
            "and IS 456 together with actual material test data.",
            normal_style
        )
    )


    story.append(
        Spacer(1, 15)
    )


    story.append(
        Paragraph(
            "Generated using Python-Based Concrete Mix "
            "Optimization Tool",
            normal_style
        )
    )


    document.build(story)

    buffer.seek(0)

    return buffer


# ============================================================
# PDF DOWNLOAD
# ============================================================

if (
    st.session_state.conventional_result is not None
    and
    st.session_state.optimization_results is not None
):

    feasible_df = (
        st.session_state.optimization_results[
            st.session_state.optimization_results["Feasible"] == True
        ]
        .copy()
    )


    if not feasible_df.empty:

        if objective == "Minimum Cost":

            optimum = feasible_df.loc[
                feasible_df["Total Cost"].idxmin()
            ]

        elif objective == "Minimum Cementitious Content":

            optimum = feasible_df.loc[
                feasible_df[
                    "Total Cementitious (kg/m³)"
                ].idxmin()
            ]

        else:

            optimum = feasible_df.loc[
                feasible_df[
                    "Balanced Score"
                ].idxmin()
            ]


        conventional = (
            st.session_state.conventional_result
        )


        conventional_cost = (
            st.session_state.conventional_cost
        )


        comparison = pd.DataFrame({

            "Parameter": [
                "Water (kg/m³)",
                "Cement (kg/m³)",
                "SCM (kg/m³)",
                "Fine Aggregate (kg/m³)",
                "Coarse Aggregate (kg/m³)",
                "Total Cementitious (kg/m³)",
                "W/C Ratio",
                "Total Cost (₹/m³)"
            ],

            "Conventional": [

                conventional[
                    "Corrected Water (kg/m³)"
                ],

                conventional[
                    "Cement Content (kg/m³)"
                ],

                conventional[
                    "SCM Content (kg/m³)"
                ],

                conventional[
                    "Fine Aggregate Batch (kg/m³)"
                ],

                conventional[
                    "Coarse Aggregate Batch (kg/m³)"
                ],

                conventional[
                    "Total Cementitious (kg/m³)"
                ],

                conventional[
                    "Actual W/C Ratio"
                ],

                conventional_cost[
                    "Total Cost"
                ]

            ],

            "Optimized": [

                optimum[
                    "Corrected Water (kg/m³)"
                ],

                optimum[
                    "Cement Content (kg/m³)"
                ],

                optimum[
                    "SCM Content (kg/m³)"
                ],

                optimum[
                    "Fine Aggregate Batch (kg/m³)"
                ],

                optimum[
                    "Coarse Aggregate Batch (kg/m³)"
                ],

                optimum[
                    "Total Cementitious (kg/m³)"
                ],

                optimum[
                    "Actual W/C Ratio"
                ],

                optimum[
                    "Total Cost"
                ]

            ]

        })


        comparison["Change"] = (
            comparison["Optimized"]
            -
            comparison["Conventional"]
        )


        st.header("4. Project Report")


        st.write(
            "The complete report can be generated directly "
            "from the calculated results."
        )


        pdf_file = create_pdf_report(
            conventional_result=conventional,
            conventional_cost=conventional_cost,
            optimum=optimum,
            comparison=comparison,
            objective=objective,
            candidate_count=len(feasible_df)
        )


        st.download_button(
            label="📄 Generate / Download Complete PDF Report",
            data=pdf_file,
            file_name="Concrete_Mix_Optimization_Report.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Python-Based Concrete Mix Optimization and Cost Analysis | "
    "Academic Project Prototype | Final design to be verified "
    "using standard provisions and laboratory trials."
)