
import pandas as pd

from src.factory_config import (
    load_factory_config,
    validate_factory_config,
    calculate_capacity_summary,
)
from src.data_loader import load_dataset
from src.preprocessing import prepare_dataset


def create_baseline(config):
    """Create the original factory capacity scenario."""

    factories = [
        factory.copy()
        for factory in config["factories"]
    ]

    return {
        "scenario_name": "Baseline",
        "factories": factories,
    }


def disable_factory(scenario, factory_id):
    """Create a scenario with one factory disabled."""

    updated = {
        "scenario_name": f"Shutdown - {factory_id}",
        "factories": [
            factory.copy()
            for factory in scenario["factories"]
        ],
    }

    matches = [
        factory
        for factory in updated["factories"]
        if factory["factory_id"] == factory_id
    ]

    if not matches:
        raise ValueError(f"Unknown factory ID: {factory_id}")

    matches[0]["enabled"] = False

    return updated


def reduce_capacity(scenario, factory_id, reduction_percent):
    """Reduce one factory's production capacity."""

    if not 0 <= reduction_percent <= 100:
        raise ValueError("Reduction must be between 0 and 100.")

    updated = {
        "scenario_name": f"Capacity Reduction - {factory_id}",
        "factories": [
            factory.copy()
            for factory in scenario["factories"]
        ],
    }

    matches = [
        factory
        for factory in updated["factories"]
        if factory["factory_id"] == factory_id
    ]

    if not matches:
        raise ValueError(f"Unknown factory ID: {factory_id}")

    original_capacity = matches[0]["capacity_units"]

    new_capacity = round(
        original_capacity * (1 - reduction_percent / 100)
    )

    matches[0]["capacity_units"] = new_capacity

    return updated


def expand_capacity(scenario, increase_percent):
    """Increase the capacity of all factories."""

    if increase_percent < 0:
        raise ValueError("Capacity increase cannot be negative.")

    updated = {
        "scenario_name": f"Capacity Expansion - {increase_percent}%",
        "factories": [
            factory.copy()
            for factory in scenario["factories"]
        ],
    }

    for factory in updated["factories"]:
        factory["capacity_units"] = round(
            factory["capacity_units"]
            * (1 + increase_percent / 100)
        )

    return updated


def evaluate_scenario(scenario, total_demand):
    """Calculate capacity and utilization for a scenario."""

    summary = calculate_capacity_summary(
        {
            "factories": scenario["factories"]
        },
        total_demand,
    )

    return {
        "Scenario": scenario["scenario_name"],
        "Active Factories": summary["active_factories"],
        "Total Demand": summary["total_demand"],
        "Available Capacity": summary["total_capacity"],
        "Spare Capacity": summary["spare_capacity"],
        "Utilization (%)": round(
            summary["utilization_percent"], 2
        ),
        "Feasible": summary["capacity_sufficient"],
    }


def run_simulations(config, total_demand):
    """Run and compare the predefined factory scenarios."""

    baseline = create_baseline(config)

    scenarios = [
        baseline,
        disable_factory(baseline, "FAC-001"),
        reduce_capacity(baseline, "FAC-002", 20),
        expand_capacity(baseline, 10),
    ]

    results = [
        evaluate_scenario(scenario, total_demand)
        for scenario in scenarios
    ]

    return pd.DataFrame(results)


def main():
    config = load_factory_config()
    validate_factory_config(config)

    original = load_dataset()
    data = prepare_dataset(original)

    total_demand = int(data["Units"].sum())

    results = run_simulations(
        config,
        total_demand
    )

    print("\n" + "=" * 75)
    print("FACTORY SCENARIO SIMULATION")
    print("=" * 75)

    print(results.to_string(index=False))

    output_path = "data/processed/scenario_comparison.csv"

    results.to_csv(output_path, index=False)

    print(f"\nScenario results saved to: {output_path}")

    feasible_count = results["Feasible"].sum()

    print(
        f"\nFeasible scenarios: "
        f"{feasible_count}/{len(results)}"
    )


if __name__ == "__main__":
    main()
