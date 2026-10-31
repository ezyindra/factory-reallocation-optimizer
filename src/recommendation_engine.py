
import os
import pandas as pd

from src.data_loader import load_dataset
from src.preprocessing import prepare_dataset

from src.factory_config import (
    load_factory_config,
    validate_factory_config,
)


def generate_recommendations(summary, total_demand):
    """Generate recommendations from optimized factory utilization."""

    if summary.empty:
        raise ValueError("Factory summary is empty.")

    required_columns = [
        "Factory ID",
        "Factory Name",
        "Capacity",
        "Allocated Units",
        "Spare Capacity",
        "Utilization (%)",
    ]

    missing = [
        column for column in required_columns
        if column not in summary.columns
    ]

    if missing:
        raise ValueError(
            f"Missing columns in factory summary: {missing}"
        )

    if total_demand < 0:
        raise ValueError("Total demand cannot be negative.")

    recommendations = []

    total_capacity = int(summary["Capacity"].sum())
    total_allocated = int(summary["Allocated Units"].sum())
    total_spare = int(summary["Spare Capacity"].sum())

    network_utilization = (
        total_allocated / total_capacity * 100
        if total_capacity > 0 else 0
    )

    # Overall network capacity.
    if total_allocated != total_demand:
        recommendations.append({
            "Category": "Demand Coverage",
            "Priority": "Critical",
            "Observation": (
                f"Only {total_allocated:,} of "
                f"{total_demand:,} demand units are allocated."
            ),
            "Recommendation": (
                "Review factory eligibility and available capacity "
                "before accepting the allocation plan."
            ),
        })

    elif total_spare == 0:
        recommendations.append({
            "Category": "Network Capacity",
            "Priority": "High",
            "Observation": (
                "The network has no spare production capacity."
            ),
            "Recommendation": (
                "Evaluate additional capacity or alternative "
                "production arrangements."
            ),
        })

    else:
        recommendations.append({
            "Category": "Network Capacity",
            "Priority": "Normal",
            "Observation": (
                f"The network has {total_spare:,} spare units "
                f"with {network_utilization:.2f}% utilization."
            ),
            "Recommendation": (
                "Retain the available capacity as a buffer "
                "for potential demand increases."
            ),
        })

    # Factory-level utilization.
    for _, factory in summary.iterrows():

        utilization = float(factory["Utilization (%)"])
        factory_name = factory["Factory Name"]
        spare = int(factory["Spare Capacity"])

        if utilization >= 95:
            priority = "High"
            observation = (
                f"{factory_name} is operating at "
                f"{utilization:.2f}% utilization."
            )
            recommendation = (
                "Monitor this factory closely and assess "
                "whether additional production capacity is needed."
            )

        elif utilization >= 85:
            priority = "Medium"
            observation = (
                f"{factory_name} has relatively high utilization "
                f"of {utilization:.2f}%."
            )
            recommendation = (
                f"Retain its current allocation and monitor "
                f"the remaining {spare:,} units of capacity."
            )

        elif utilization < 50:
            priority = "Medium"
            observation = (
                f"{factory_name} is operating at only "
                f"{utilization:.2f}% utilization."
            )
            recommendation = (
                "Review whether this factory can accept "
                "additional eligible production demand."
            )

        else:
            priority = "Normal"
            observation = (
                f"{factory_name} is operating at "
                f"{utilization:.2f}% utilization."
            )
            recommendation = (
                f"Continue the current allocation while "
                f"monitoring its {spare:,} units of spare capacity."
            )

        recommendations.append({
            "Category": "Factory Utilization",
            "Priority": priority,
            "Observation": observation,
            "Recommendation": recommendation,
        })

    # Compare the utilization distribution.
    utilization_values = summary["Utilization (%)"]

    utilization_spread = (
        float(utilization_values.max())
        - float(utilization_values.min())
    )

    if utilization_spread <= 2:
        recommendations.append({
            "Category": "Allocation Balance",
            "Priority": "Normal",
            "Observation": (
                f"Factory utilization differs by only "
                f"{utilization_spread:.2f} percentage points."
            ),
            "Recommendation": (
                "The current allocation is well balanced. "
                "Retain this distribution unless operational "
                "conditions change."
            ),
        })

    else:
        recommendations.append({
            "Category": "Allocation Balance",
            "Priority": "Medium",
            "Observation": (
                f"Factory utilization varies by "
                f"{utilization_spread:.2f} percentage points."
            ),
            "Recommendation": (
                "Review whether eligible production can be "
                "redistributed to balance factory utilization."
            ),
        })

    return pd.DataFrame(recommendations)


def main():

    print("\nLoading factory configuration...")

    config = load_factory_config()
    validate_factory_config(config)

    print("Loading optimized factory results...")

    summary_path = (
        "data/processed/optimized_factory_summary.csv"
    )

    if not os.path.exists(summary_path):
        raise FileNotFoundError(
            "Optimized factory summary not found. "
            "Run the optimizer first."
        )

    summary = pd.read_csv(summary_path)

    print("Calculating current demand from source data...")

    raw_data = load_dataset()
    data = prepare_dataset(raw_data)

    total_demand = int(data["Units"].sum())

    recommendations = generate_recommendations(
        summary,
        total_demand,
    )

    print("\n" + "=" * 75)
    print("FACTORY REALLOCATION RECOMMENDATIONS")
    print("=" * 75)

    print("\nNETWORK OVERVIEW")

    total_capacity = int(summary["Capacity"].sum())
    total_allocated = int(summary["Allocated Units"].sum())

    print(f"Total demand      : {total_demand:,} units")
    print(f"Allocated demand  : {total_allocated:,} units")
    print(f"Available capacity: {total_capacity:,} units")
    print(
        f"Spare capacity    : "
        f"{total_capacity - total_allocated:,} units"
    )

    print("\nRECOMMENDATIONS")

    for index, row in recommendations.iterrows():

        print(f"\n{index + 1}. {row['Category']}")
        print(f"   Priority       : {row['Priority']}")
        print(f"   Observation    : {row['Observation']}")
        print(f"   Recommendation : {row['Recommendation']}")

    output_path = (
        "data/processed/factory_recommendations.csv"
    )

    os.makedirs("data/processed", exist_ok=True)

    recommendations.to_csv(
        output_path,
        index=False,
    )

    print("\n" + "=" * 75)
    print(f"Recommendations saved to: {output_path}")
    print("Recommendation generation completed.")
    print("=" * 75)


if __name__ == "__main__":
    main()
