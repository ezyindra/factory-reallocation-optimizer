
import copy
import os

import pandas as pd

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


def create_scenarios(base_config):
    """Create independent factory network scenarios."""

    scenarios = []

    # Scenario 1: Baseline.
    scenarios.append({
        "name": "Baseline",
        "config": copy.deepcopy(base_config),
    })

    # Scenario 2: Factory North shutdown.
    shutdown_config = copy.deepcopy(base_config)

    for factory in shutdown_config["factories"]:
        if factory["factory_id"] == "FAC-001":
            factory["enabled"] = False

    scenarios.append({
        "name": "Factory North Shutdown",
        "config": shutdown_config,
    })

    # Scenario 3: Factory Central capacity reduction.
    reduction_config = copy.deepcopy(base_config)

    for factory in reduction_config["factories"]:
        if factory["factory_id"] == "FAC-002":
            factory["capacity_units"] = round(
                factory["capacity_units"] * 0.80
            )

    scenarios.append({
        "name": "Central Capacity -20%",
        "config": reduction_config,
    })

    # Scenario 4: Capacity expansion.
    expansion_config = copy.deepcopy(base_config)

    for factory in expansion_config["factories"]:
        factory["capacity_units"] = round(
            factory["capacity_units"] * 1.10
        )

    scenarios.append({
        "name": "All Factories +10%",
        "config": expansion_config,
    })

    return scenarios


def evaluate_scenario(scenario, demand):
    """Run optimization and summarize one scenario."""

    config = scenario["config"]
    scenario_name = scenario["name"]

    enabled_factories = [
        factory
        for factory in config["factories"]
        if factory.get("enabled") is True
    ]

    total_demand = int(demand["Units"].sum())

    total_capacity = sum(
        int(factory["capacity_units"])
        for factory in enabled_factories
    )

    spare_capacity = total_capacity - total_demand

    base_result = {
        "Scenario": scenario_name,
        "Active Factories": len(enabled_factories),
        "Total Demand": total_demand,
        "Available Capacity": total_capacity,
        "Spare Capacity": spare_capacity,
        "Utilization (%)": (
            round(total_demand / total_capacity * 100, 2)
            if total_capacity > 0 else 0
        ),
        "Solver Status": "NOT RUN",
        "Feasible": False,
    }

    # Reject scenarios that cannot satisfy total demand.
    if total_capacity < total_demand:
        base_result["Solver Status"] = "INSUFFICIENT CAPACITY"
        return base_result, None, None

    try:
        allocations, summary, status = optimize_allocation(
            config,
            demand,
        )

        base_result["Solver Status"] = status
        base_result["Feasible"] = True

        # Use actual solver allocations for utilization.
        base_result["Utilization (%)"] = round(
            allocations["Allocated Units"].sum()
            / total_capacity * 100,
            2,
        )

        return base_result, allocations, summary

    except (ValueError, RuntimeError) as error:
        base_result["Solver Status"] = str(error)
        return base_result, None, None


def main():

    print("\nLoading base factory configuration...")

    base_config = load_factory_config()
    validate_factory_config(base_config)

    print("Preparing demand data...")

    raw_data = load_dataset()
    data = prepare_dataset(raw_data)

    demand = build_demand_buckets(data)

    scenarios = create_scenarios(base_config)

    comparison_rows = []
    allocation_details = []

    output_directory = "data/processed/scenarios"
    os.makedirs(output_directory, exist_ok=True)

    print("\n" + "=" * 75)
    print("SCENARIO-BASED FACTORY OPTIMIZATION")
    print("=" * 75)

    for scenario in scenarios:

        print(f"\nEvaluating: {scenario['name']}")

        result, allocations, summary = evaluate_scenario(
            scenario,
            demand,
        )

        comparison_rows.append(result)

        print(f"Solver status: {result['Solver Status']}")
        print(f"Available capacity: {result['Available Capacity']:,}")
        print(f"Feasible: {result['Feasible']}")

        if allocations is not None:

            safe_name = (
                scenario["name"]
                .lower()
                .replace(" ", "_")
                .replace("-", "")
            )

            allocation_path = os.path.join(
                output_directory,
                f"{safe_name}_allocations.csv",
            )

            summary_path = os.path.join(
                output_directory,
                f"{safe_name}_factory_summary.csv",
            )

            allocations.to_csv(
                allocation_path,
                index=False,
            )

            summary.to_csv(
                summary_path,
                index=False,
            )

            allocation_details.append({
                "Scenario": scenario["name"],
                "Factory Summary": summary,
            })

    comparison = pd.DataFrame(comparison_rows)

    comparison_path = (
        "data/processed/scenario_optimization_comparison.csv"
    )

    comparison.to_csv(
        comparison_path,
        index=False,
    )

    print("\n" + "=" * 75)
    print("SCENARIO COMPARISON")
    print("=" * 75)

    print(comparison.to_string(index=False))

    print("\nScenario comparison saved to:")
    print(comparison_path)

    print("\nIndividual scenario results saved to:")
    print(output_directory)


if __name__ == "__main__":
    main()
