import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Concrete Mix Optimization",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ Concrete Mix Optimization & Analysis System")

st.write(
    "A Python-based web prototype for exploring concrete mix alternatives "
    "based on user-defined design requirements."
)

st.info(
    "DEMO VERSION: The strength relationship used here is illustrative. "
    "Final engineering calculations will be based on the applicable mix-design procedure."
)

# ---------------- SIDEBAR ----------------

st.sidebar.header("Design Inputs")

grade = st.sidebar.selectbox(
    "Concrete Grade",
    ["M25", "M30", "M35", "M40"]
)

target_strength = st.sidebar.number_input(
    "Target Strength (MPa)",
    min_value=20.0,
    max_value=60.0,
    value=38.0,
    step=1.0
)

target_slump = st.sidebar.number_input(
    "Target Slump (mm)",
    min_value=50,
    max_value=200,
    value=100,
    step=10
)

current_wc = st.sidebar.number_input(
    "Current W/C Ratio",
    min_value=0.25,
    max_value=0.70,
    value=0.50,
    step=0.01
)

st.sidebar.header("User-Defined Optimization")

min_wc = st.sidebar.number_input(
    "Minimum W/C Ratio",
    min_value=0.25,
    max_value=0.70,
    value=0.35,
    step=0.01
)

max_wc = st.sidebar.number_input(
    "Maximum W/C Ratio",
    min_value=0.25,
    max_value=0.70,
    value=0.55,
    step=0.01
)

min_cement = st.sidebar.number_input(
    "Minimum Cement (kg/m³)",
    min_value=200,
    max_value=500,
    value=280,
    step=10
)

max_cement = st.sidebar.number_input(
    "Maximum Cement (kg/m³)",
    min_value=200,
    max_value=600,
    value=420,
    step=10
)

objective = st.sidebar.selectbox(
    "Optimization Objective",
    [
        "Minimum Cost",
        "Minimum Cement",
        "Balanced Cost + Cement"
    ]
)

st.sidebar.header("Material Cost")

cement_cost = st.sidebar.number_input(
    "Cement Cost (₹/kg)",
    min_value=1.0,
    max_value=100.0,
    value=7.0,
    step=0.5
)

aggregate_cost = st.sidebar.number_input(
    "Aggregate Cost (₹/kg)",
    min_value=0.1,
    max_value=20.0,
    value=1.5,
    step=0.1
)

# ---------------- OPTIMIZATION ----------------

if st.button("🔍 OPTIMIZE MIX", use_container_width=True):

    # Generate candidate combinations from USER-DEFINED ranges
    wc_values = np.linspace(min_wc, max_wc, 31)
    cement_values = np.linspace(min_cement, max_cement, 15)

    results = []

    for wc in wc_values:
        for cement in cement_values:

            # DEMO ONLY strength relationship
            predicted_strength = (
                60
                - 45 * wc
                + 0.025 * (cement - 280)
            )

            # DEMO aggregate quantity
            aggregate = 1000 + (350 - cement) * 0.35

            # DEMO cost
            cost = (
                cement * cement_cost
                + aggregate * aggregate_cost
            )

            feasible = predicted_strength >= target_strength

            if feasible:
                results.append({
                    "W/C Ratio": round(wc, 3),
                    "Cement (kg/m³)": round(cement, 1),
                    "Aggregate (kg/m³)": round(aggregate, 1),
                    "Predicted Strength (MPa)": round(predicted_strength, 2),
                    "Estimated Cost (₹/m³)": round(cost, 2)
                })

    df = pd.DataFrame(results)

    if len(df) == 0:

        st.error(
            "No feasible mix found for the selected constraints. "
            "Try widening the input ranges."
        )

    else:

        # Select optimum
        if objective == "Minimum Cost":

            optimum = df.loc[df["Estimated Cost (₹/m³)"].idxmin()]

        elif objective == "Minimum Cement":

            optimum = df.loc[df["Cement (kg/m³)"].idxmin()]

        else:

            df["Score"] = (
                df["Estimated Cost (₹/m³)"] /
                df["Estimated Cost (₹/m³)"].min()
                +
                df["Cement (kg/m³)"] /
                df["Cement (kg/m³)"].min()
            )

            optimum = df.loc[df["Score"].idxmin()]

        # ---------------- RESULTS ----------------

        st.success("Optimization completed successfully!")

        st.subheader("🎯 Optimized Mix")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "W/C Ratio",
            optimum["W/C Ratio"]
        )

        col2.metric(
            "Cement",
            f'{optimum["Cement (kg/m³)"]} kg/m³'
        )

        col3.metric(
            "Predicted Strength",
            f'{optimum["Predicted Strength (MPa)"]} MPa'
        )

        col4.metric(
            "Estimated Cost",
            f'₹{optimum["Estimated Cost (₹/m³)"]:.0f}'
        )

        # ---------------- TABLE ----------------

        st.subheader("📊 Feasible Mix Alternatives")

        st.dataframe(
            df.sort_values("Estimated Cost (₹/m³)").head(15),
            use_container_width=True
        )

        # ---------------- CURVE 1 ----------------

        st.subheader("📈 Strength vs W/C Ratio")

        strength_curve = (
            df.groupby("W/C Ratio")["Predicted Strength (MPa)"]
            .max()
            .reset_index()
        )

        fig1 = go.Figure()

        fig1.add_trace(
            go.Scatter(
                x=strength_curve["W/C Ratio"],
                y=strength_curve["Predicted Strength (MPa)"],
                mode="lines+markers",
                name="Strength Curve"
            )
        )

        fig1.add_trace(
            go.Scatter(
                x=[optimum["W/C Ratio"]],
                y=[optimum["Predicted Strength (MPa)"]],
                mode="markers",
                marker=dict(size=14),
                name="Optimum"
            )
        )

        fig1.update_layout(
            xaxis_title="Water/Cement Ratio",
            yaxis_title="Predicted Strength (MPa)",
            hovermode="x unified"
        )

        st.plotly_chart(fig1, use_container_width=True)

        # ---------------- CURVE 2 ----------------

        st.subheader("📉 Cost vs W/C Ratio")

        cost_curve = (
            df.groupby("W/C Ratio")["Estimated Cost (₹/m³)"]
            .min()
            .reset_index()
        )

        fig2 = go.Figure()

        fig2.add_trace(
            go.Scatter(
                x=cost_curve["W/C Ratio"],
                y=cost_curve["Estimated Cost (₹/m³)"],
                mode="lines+markers",
                name="Cost Curve"
            )
        )

        fig2.add_trace(
            go.Scatter(
                x=[optimum["W/C Ratio"]],
                y=[optimum["Estimated Cost (₹/m³)"]],
                mode="markers",
                marker=dict(size=14),
                name="Optimum"
            )
        )

        fig2.update_layout(
            xaxis_title="Water/Cement Ratio",
            yaxis_title="Estimated Cost (₹/m³)",
            hovermode="x unified"
        )

        st.plotly_chart(fig2, use_container_width=True)

        # ---------------- ANALYST ----------------

        st.subheader("🔎 Engineering Analysis")

        current_strength = (
            60
            - 45 * current_wc
            + 0.025 * (optimum["Cement (kg/m³)"] - 280)
        )

        st.write(
            f"**Current W/C ratio:** {current_wc:.2f}"
        )

        st.write(
            f"**Optimized W/C ratio:** {optimum['W/C Ratio']:.3f}"
        )

        st.write(
            f"**Change in W/C ratio:** "
            f"{((current_wc - optimum['W/C Ratio']) / current_wc) * 100:.1f}%"
        )

        st.write(
            "The system generates candidate combinations from the "
            "user-defined ranges rather than selecting from fixed Mix 1, "
            "Mix 2, Mix 3 or Mix 4."
        )

else:

    st.warning(
        "Enter your design requirements in the left panel and click "
        "'OPTIMIZE MIX' to generate the analysis."
    )