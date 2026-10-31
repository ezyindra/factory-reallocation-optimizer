
import os
import copy

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import load_dataset
from src.preprocessing import prepare_dataset
from src.factory_config import (
    load_factory_config,
    validate_factory_config,
)
from src.optimization_engine import (
    build_demand_buckets,
    optimize_allocation,
)
from src.recommendation_engine import generate_recommendations


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Factory Allocation | Nassau Candy",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM STYLING
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #0b1120;
        color: #e5e7eb;
    }

    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #263244;
    }

    [data-testid="stMetric"] {
        background-color: #151f30;
        border: 1px solid #263449;
        padding: 18px;
        border-radius: 12px;
    }

    [data-testid="stMetricLabel"] {
        color: #9ca3af;
    }

    [data-testid="stMetricValue"] {
        color: #f9fafb;
    }

    .main-title {
        font-size: 30px;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 4px;
    }

    .subtitle {
        color: #94a3b8;
        font-size: 14px;
        margin-bottom: 24px;
    }

    .notice {
        background: #172554;
        border-left: 3px solid #60a5fa;
        padding: 12px 15px;
        border-radius: 6px;
        color: #dbeafe;
        font-size: 13px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FILE PATHS
# ============================================================

PROCESSED = "data/processed"


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_csv(filename):

    path = os.path.join(PROCESSED, filename)

    if not os.path.exists(path):
        return pd.DataFrame()

    return pd.read_csv(path)


@st.cache_data
def load_scenario_inputs():

    config = load_factory_config()
    validate_factory_config(config)

    raw_data = load_dataset()
    data = prepare_dataset(raw_data)

    demand = build_demand_buckets(data)
    total_demand = int(data["Units"].sum())

    return config, demand, total_demand


# Existing project outputs.
factory_summary = load_csv(
    "optimized_factory_summary.csv"
)

allocations = load_csv(
    "factory_allocations.csv"
)

scenario_results = load_csv(
    "scenario_optimization_comparison.csv"
)

recommendations = load_csv(
    "factory_recommendations.csv"
)

validation_report = load_csv(
    "validation_report.csv"
)

validation_capacity = load_csv(
    "validation_factory_capacity.csv"
)

demand_reconciliation = load_csv(
    "validation_demand_reconciliation.csv"
)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.markdown("## 🏭 Factory Optimizer")

st.sidebar.caption(
    "Nassau Candy | Decision Support System"
)

st.sidebar.divider()

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Overview",
        "Factory Analysis",
        "Allocation Explorer",
        "Scenario Analysis",
        "Recommendations",
        "Validation",
    ],
)

st.sidebar.divider()

st.sidebar.caption("PROJECT STATUS")
st.sidebar.success("Optimization pipeline connected")

st.sidebar.caption(
    "Factory profiles are illustrative simulation assumptions."
)


# ============================================================
# DATA VALIDATION
# ============================================================

if factory_summary.empty or allocations.empty:

    st.error(
        "Required optimization files are missing. "
        "Run the optimization engine before launching "
        "the dashboard."
    )

    st.code(
        "python -m src.optimization_engine",
        language="powershell",
    )

    st.stop()


required_summary_columns = [
    "Factory ID",
    "Factory Name",
    "Capacity",
    "Allocated Units",
    "Spare Capacity",
    "Utilization (%)",
]

required_allocation_columns = [
    "Factory ID",
    "Product ID",
    "Product Name",
    "Country/Region",
    "Region",
    "Allocated Units",
]

missing_summary = [
    column
    for column in required_summary_columns
    if column not in factory_summary.columns
]

missing_allocations = [
    column
    for column in required_allocation_columns
    if column not in allocations.columns
]

if missing_summary or missing_allocations:

    st.error(
        f"Missing dashboard columns. "
        f"Summary: {missing_summary}. "
        f"Allocations: {missing_allocations}."
    )

    st.stop()


# Load actual demand independently.
try:
    _, _, total_demand = load_scenario_inputs()

except Exception as error:
    st.error(f"Could not load source demand data: {error}")
    st.stop()


total_capacity = int(
    factory_summary["Capacity"].sum()
)

total_allocated = int(
    factory_summary["Allocated Units"].sum()
)

spare_capacity = (
    total_capacity - total_allocated
)

network_utilization = (
    total_allocated / total_capacity * 100
    if total_capacity > 0 else 0
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">'
    'Factory Allocation Dashboard'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Production allocation, capacity utilization '
    'and scenario intelligence'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# 1. OVERVIEW
# ============================================================

if page == "Overview":

    st.markdown("### Network Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Demand",
        f"{total_demand:,}",
    )

    col2.metric(
        "Production Capacity",
        f"{total_capacity:,}",
    )

    col3.metric(
        "Spare Capacity",
        f"{spare_capacity:,}",
    )

    col4.metric(
        "Network Utilization",
        f"{network_utilization:.2f}%",
    )

    st.divider()

    left, right = st.columns(2)

    with left:

        st.markdown("### Factory Utilization")

        fig = px.bar(
            factory_summary,
            x="Factory Name",
            y="Utilization (%)",
            color="Utilization (%)",
            text="Utilization (%)",
            color_continuous_scale="Blues",
        )

        fig.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside",
        )

        fig.update_layout(
            template="plotly_dark",
            height=370,
            coloraxis_showscale=False,
            margin=dict(
                l=15,
                r=15,
                t=30,
                b=15,
            ),
            yaxis_title="Utilization (%)",
            xaxis_title="",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with right:

        st.markdown("### Production Distribution")

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=factory_summary["Factory Name"],
                    values=factory_summary["Allocated Units"],
                    hole=0.65,
                    textinfo="label+percent",
                )
            ]
        )

        fig.update_layout(
            template="plotly_dark",
            height=370,
            margin=dict(
                l=15,
                r=15,
                t=30,
                b=15,
            ),
            showlegend=False,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    st.markdown("### Factory Performance")

    st.dataframe(
        factory_summary,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown(
        """
        <div class="notice">
        This dashboard uses historical demand and illustrative
        factory capacity assumptions. It is a decision-support
        simulation, not a live operational system.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 2. FACTORY ANALYSIS
# ============================================================

elif page == "Factory Analysis":

    st.markdown("### Factory Performance Analysis")

    selected_factory = st.selectbox(
        "Select Factory",
        factory_summary["Factory Name"].tolist(),
    )

    factory = factory_summary[
        factory_summary["Factory Name"] == selected_factory
    ].iloc[0]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Capacity",
        f"{int(factory['Capacity']):,}",
    )

    col2.metric(
        "Allocated Units",
        f"{int(factory['Allocated Units']):,}",
    )

    col3.metric(
        "Utilization",
        f"{factory['Utilization (%)']:.2f}%",
    )

    factory_allocations = allocations[
        allocations["Factory ID"] == factory["Factory ID"]
    ]

    st.markdown("### Product Allocation")

    product_data = (
        factory_allocations.groupby(
            "Product Name",
            as_index=False,
        )["Allocated Units"]
        .sum()
        .sort_values(
            "Allocated Units",
            ascending=False,
        )
    )

    fig = px.bar(
        product_data,
        x="Product Name",
        y="Allocated Units",
        color="Allocated Units",
        color_continuous_scale="Blues",
    )

    fig.update_layout(
        template="plotly_dark",
        height=450,
        xaxis_tickangle=-35,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.markdown("### Destination Allocation")

    destination_data = (
        factory_allocations.groupby(
            ["Country/Region", "Region"],
            as_index=False,
        )["Allocated Units"]
        .sum()
        .sort_values(
            "Allocated Units",
            ascending=False,
        )
    )

    st.dataframe(
        destination_data,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# 3. ALLOCATION EXPLORER
# ============================================================

elif page == "Allocation Explorer":

    st.markdown("### Product and Destination Allocations")

    factory_options = (
        ["All Factories"]
        + factory_summary["Factory ID"].tolist()
    )

    selected_factory = st.selectbox(
        "Filter by Factory",
        factory_options,
    )

    filtered = allocations.copy()

    if selected_factory != "All Factories":

        filtered = filtered[
            filtered["Factory ID"] == selected_factory
        ]

    product_options = sorted(
        filtered["Product Name"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_products = st.multiselect(
        "Filter Products",
        product_options,
        default=[],
    )

    if selected_products:

        filtered = filtered[
            filtered["Product Name"].isin(selected_products)
        ]

    col1, col2 = st.columns(2)

    col1.metric(
        "Allocation Records",
        f"{len(filtered):,}",
    )

    col2.metric(
        "Filtered Units",
        f"{int(filtered['Allocated Units'].sum()):,}",
    )

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
    )

    csv = filtered.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "Download Allocation CSV",
        data=csv,
        file_name="filtered_factory_allocations.csv",
        mime="text/csv",
    )


# ============================================================
# 4. INTERACTIVE SCENARIO ANALYSIS
# ============================================================

elif page == "Scenario Analysis":

    st.markdown("### Interactive Factory Scenario Simulator")

    st.caption(
        "Change factory conditions and run the OR-Tools "
        "allocation optimizer directly from this page."
    )

    try:
        base_config, demand, scenario_demand = (
            load_scenario_inputs()
        )

    except Exception as error:
        st.error(f"Could not load scenario inputs: {error}")
        st.stop()

    # --------------------------------------------------------
    # Scenario configuration
    # --------------------------------------------------------

    st.markdown("#### 1. Configure your scenario")

    scenario_type = st.selectbox(
        "Scenario type",
        [
            "Baseline",
            "Factory Shutdown",
            "Capacity Reduction",
            "Capacity Expansion",
        ],
        key="interactive_scenario_type",
    )

    scenario_config = copy.deepcopy(base_config)

    factory_options = [
        factory["factory_id"]
        for factory in scenario_config["factories"]
        if factory.get("enabled") is True
    ]

    selected_factory = None

    if scenario_type in [
        "Factory Shutdown",
        "Capacity Reduction",
    ]:

        if not factory_options:
            st.error("No enabled factories are available.")
            st.stop()

        selected_factory = st.selectbox(
            "Select factory",
            factory_options,
            format_func=lambda factory_id: next(
                factory["name"]
                for factory in scenario_config["factories"]
                if factory["factory_id"] == factory_id
            ),
        )

    if scenario_type == "Factory Shutdown":

        st.warning(
            "The selected factory will be disabled "
            "for this simulation."
        )

        for factory in scenario_config["factories"]:

            if factory["factory_id"] == selected_factory:
                factory["enabled"] = False

    elif scenario_type == "Capacity Reduction":

        reduction = st.slider(
            "Capacity reduction (%)",
            min_value=5,
            max_value=90,
            value=20,
            step=5,
        )

        for factory in scenario_config["factories"]:

            if factory["factory_id"] == selected_factory:

                factory["capacity_units"] = round(
                    factory["capacity_units"]
                    * (1 - reduction / 100)
                )

        st.info(
            f"{selected_factory} capacity reduced by "
            f"{reduction}%."
        )

    elif scenario_type == "Capacity Expansion":

        expansion = st.slider(
            "Capacity expansion (%)",
            min_value=5,
            max_value=50,
            value=10,
            step=5,
        )

        for factory in scenario_config["factories"]:

            factory["capacity_units"] = round(
                factory["capacity_units"]
                * (1 + expansion / 100)
            )

        st.info(
            f"All factory capacities increased by "
            f"{expansion}%."
        )

    # --------------------------------------------------------
    # Scenario capacity overview
    # --------------------------------------------------------

    enabled_factories = [
        factory
        for factory in scenario_config["factories"]
        if factory.get("enabled") is True
    ]

    scenario_capacity = sum(
        int(factory["capacity_units"])
        for factory in enabled_factories
    )

    scenario_spare = scenario_capacity - scenario_demand

    scenario_utilization = (
        scenario_demand / scenario_capacity * 100
        if scenario_capacity > 0 else 0
    )

    st.markdown("#### 2. Scenario capacity overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Demand",
        f"{scenario_demand:,}",
    )

    col2.metric(
        "Available Capacity",
        f"{scenario_capacity:,}",
    )

    col3.metric(
        "Spare Capacity",
        f"{scenario_spare:,}",
    )

    col4.metric(
        "Demand / Capacity",
        f"{scenario_utilization:.2f}%",
    )

    if scenario_spare < 0:

        st.error(
            f"Insufficient capacity. The network is short "
            f"by {abs(scenario_spare):,} units."
        )

    else:

        st.success(
            f"The network has sufficient total capacity "
            f"with {scenario_spare:,} units remaining."
        )

    # --------------------------------------------------------
    # Execute optimization
    # --------------------------------------------------------

    st.divider()

    st.markdown("#### 3. Run optimization")

    run_scenario = st.button(
        "Run Optimization",
        type="primary",
        use_container_width=True,
    )

    if run_scenario:

        # Remove previous results before running a new scenario.
        st.session_state.pop("scenario_result", None)

        if scenario_capacity < scenario_demand:

            st.error(
                "Optimization skipped because total factory "
                "capacity is below demand."
            )

        else:

            with st.spinner(
                "Running OR-Tools allocation optimizer..."
            ):

                try:

                    (
                        allocations_result,
                        summary_result,
                        solver_status,
                    ) = optimize_allocation(
                        scenario_config,
                        demand,
                    )

                    allocated_total = int(
                        allocations_result["Allocated Units"].sum()
                    )

                    if allocated_total != scenario_demand:

                        st.error(
                            "Demand reconciliation failed."
                        )

                    else:

                        st.session_state["scenario_result"] = {
                            "allocations": allocations_result,
                            "summary": summary_result,
                            "status": solver_status,
                            "name": scenario_type,
                            "demand": scenario_demand,
                            "capacity": scenario_capacity,
                        }

                        st.success(
                            f"Optimization completed: {solver_status}"
                        )

                except (ValueError, RuntimeError) as error:

                    st.error(
                        f"Optimization could not be completed: {error}"
                    )

    # --------------------------------------------------------
    # Display latest optimization results
    # --------------------------------------------------------

    if "scenario_result" in st.session_state:

        result = st.session_state["scenario_result"]

        allocations_result = result["allocations"]
        summary_result = result["summary"]

        st.divider()

        st.markdown("### 4. Optimization Results")

        st.caption(
            f"Latest scenario: {result['name']} | "
            f"Solver status: {result['status']}"
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Allocated Units",
            f"{int(allocations_result['Allocated Units'].sum()):,}",
        )

        col2.metric(
            "Active Factories",
            str(len(summary_result)),
        )

        col3.metric(
            "Total Spare Capacity",
            f"{int(summary_result['Spare Capacity'].sum()):,}",
        )

        st.markdown("#### Factory Utilization")

        fig = px.bar(
            summary_result,
            x="Factory Name",
            y="Utilization (%)",
            color="Utilization (%)",
            text="Utilization (%)",
            color_continuous_scale="Blues",
        )

        fig.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside",
        )

        fig.update_layout(
            template="plotly_dark",
            height=380,
            coloraxis_showscale=False,
            yaxis_title="Utilization (%)",
            xaxis_title="",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        st.markdown("#### Factory Allocation Summary")

        st.dataframe(
            summary_result,
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("#### Product and Destination Allocations")

        st.dataframe(
            allocations_result,
            use_container_width=True,
            hide_index=True,
        )

        # ----------------------------------------------------
        # Scenario recommendations
        # ----------------------------------------------------

        st.markdown("#### Scenario Recommendations")

        scenario_recommendations = generate_recommendations(
            summary_result,
            result["demand"],
        )

        for _, row in scenario_recommendations.iterrows():

            with st.container(border=True):

                st.markdown(
                    f"**{row['Category']} — {row['Priority']}**"
                )

                st.write(row["Observation"])

                st.write(
                    f"Recommended action: {row['Recommendation']}"
                )

        # ----------------------------------------------------
        # Export scenario allocation
        # ----------------------------------------------------

        st.markdown("#### Export Results")

        csv_data = allocations_result.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "Download Scenario Allocation CSV",
            data=csv_data,
            file_name="interactive_scenario_allocations.csv",
            mime="text/csv",
            use_container_width=True,
        )

    else:

        st.info(
            "Configure a scenario and click Run Optimization "
            "to see the results here."
        )

    # --------------------------------------------------------
    # Existing precomputed scenario comparison
    # --------------------------------------------------------

    st.divider()

    st.markdown("### Previously Generated Scenario Comparison")

    if scenario_results.empty:

        st.info(
            "No precomputed scenario comparison is available."
        )

    else:

        st.dataframe(
            scenario_results,
            use_container_width=True,
            hide_index=True,
        )

        fig = px.bar(
            scenario_results,
            x="Scenario",
            y="Available Capacity",
            color="Feasible",
            text="Available Capacity",
            color_discrete_map={
                True: "#16a34a",
                False: "#dc2626",
            },
        )

        fig.update_layout(
            template="plotly_dark",
            height=400,
            xaxis_tickangle=-20,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        fig = px.bar(
            scenario_results,
            x="Scenario",
            y="Utilization (%)",
            color="Feasible",
            color_discrete_map={
                True: "#3b82f6",
                False: "#dc2626",
            },
        )

        fig.add_hline(
            y=100,
            line_dash="dash",
            line_color="red",
            annotation_text="100% capacity",
        )

        fig.update_layout(
            template="plotly_dark",
            height=400,
            xaxis_tickangle=-20,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


# ============================================================
# 5. RECOMMENDATIONS
# ============================================================

elif page == "Recommendations":

    st.markdown("### Operational Recommendations")

    if recommendations.empty:

        st.warning(
            "Recommendation file not found. "
            "Run the recommendation engine."
        )

    else:

        for _, row in recommendations.iterrows():

            with st.container(border=True):

                priority = row["Priority"]

                st.markdown(
                    f"**{row['Category']}**"
                )

                if priority == "Critical":
                    st.error(f"Priority: {priority}")

                elif priority == "High":
                    st.warning(f"Priority: {priority}")

                elif priority == "Medium":
                    st.info(f"Priority: {priority}")

                else:
                    st.success(f"Priority: {priority}")

                st.write(row["Observation"])

                st.markdown(
                    f"**Recommended action:** "
                    f"{row['Recommendation']}"
                )


# ============================================================
# 6. VALIDATION
# ============================================================

elif page == "Validation":

    st.markdown("### Optimization Validation")

    if validation_report.empty:

        st.warning(
            "Validation report not found. "
            "Run the allocation validator."
        )

    else:

        all_passed = bool(
            validation_report["Status"].all()
        )

        if all_passed:
            st.success(
                "All validation checks passed."
            )

        else:
            st.error(
                "One or more validation checks failed."
            )

        st.dataframe(
            validation_report,
            use_container_width=True,
            hide_index=True,
        )

        if not validation_capacity.empty:

            st.markdown(
                "### Factory Capacity Validation"
            )

            st.dataframe(
                validation_capacity,
                use_container_width=True,
                hide_index=True,
            )

        if not demand_reconciliation.empty:

            st.markdown(
                "### Demand Reconciliation"
            )

            mismatches = demand_reconciliation[
                demand_reconciliation["Difference"] != 0
            ]

            if mismatches.empty:

                st.success(
                    "All product-market demand buckets reconcile."
                )

            else:

                st.error(
                    f"{len(mismatches)} demand buckets "
                    "have mismatches."
                )

                st.dataframe(
                    mismatches,
                    use_container_width=True,
                    hide_index=True,
                )


# ============================================================
# FOOTER
# ============================================================

st.sidebar.divider()

st.sidebar.caption(
    "Factory Reallocation & Shipping Optimization"
)

st.sidebar.caption(
    "Analytical Decision-Support Project"
)
