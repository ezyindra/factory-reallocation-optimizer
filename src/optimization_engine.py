
import os

import pandas as pd
from ortools.sat.python import cp_model

from src.data_loader import load_dataset
from src.preprocessing import prepare_dataset
from src.factory_config import (
    load_factory_config,
    validate_factory_config,
)


def build_demand_buckets(data):
    """Aggregate demand by product and destination market."""

    required = [
        "Product ID",
        "Product Name",
        "Country/Region",
        "Region",
        "Units",
    ]

    missing = [
        column for column in required
        if column not in data.columns
    ]

    if missing:
        raise ValueError(f"Missing demand columns: {missing}")

    demand = (
        data.groupby(
            [
                "Product ID",
                "Product Name",
                "Country/Region",
                "Region",
            ],
            as_index=False,
        )["Units"]
        .sum()
    )

    demand["Units"] = demand["Units"].astype(int)

    if (demand["Units"] < 0).any():
        raise ValueError("Demand cannot contain negative units.")

    return demand.reset_index(drop=True)


def optimize_allocation(config, demand):
    """Allocate demand while minimizing maximum factory utilization."""

    factories = [
        factory
        for factory in config["factories"]
        if factory.get("enabled") is True
    ]

    if not factories:
        raise ValueError("No enabled factories are available.")

    if demand.empty:
        raise ValueError("Demand dataset is empty.")

    # Validate factory capacities.
    for factory in factories:
        capacity = factory.get("capacity_units")

        if (
            not isinstance(capacity, int)
            or isinstance(capacity, bool)
            or capacity <= 0
        ):
            raise ValueError(
                f"Invalid capacity for {factory['factory_id']}."
            )

    total_demand = int(demand["Units"].sum())
    total_capacity = sum(
        factory["capacity_units"]
        for factory in factories
    )

    if total_demand > total_capacity:
        raise ValueError(
            f"Insufficient factory capacity. "
            f"Demand: {total_demand:,}, "
            f"Capacity: {total_capacity:,}, "
            f"Shortage: {total_demand - total_capacity:,} units."
        )

    model = cp_model.CpModel()

    assignments = {}
    factory_loads = {}

    utilization_limit = model.new_int_var(
        0,
        10000,
        "maximum_utilization",
    )

    # Create allocation variables.
    for factory in factories:

        factory_id = factory["factory_id"]
        factory_loads[factory_id] = []

        supported_products = factory.get(
            "supported_products", "all"
        )

        for index, bucket in demand.iterrows():

            product_id = str(bucket["Product ID"])
            product_name = str(bucket["Product Name"])
            required_units = int(bucket["Units"])

            product_supported = (
                supported_products == "all"
                or (
                    isinstance(supported_products, list)
                    and (
                        product_id in supported_products
                        or product_name in supported_products
                    )
                )
            )

            if not product_supported:
                continue

            variable = model.new_int_var(
                0,
                required_units,
                f"allocation_{factory_id}_{index}",
            )

            assignments[(factory_id, index)] = variable
            factory_loads[factory_id].append(variable)

    # Ensure every demand bucket is fully allocated.
    for index, bucket in demand.iterrows():

        eligible_variables = [
            variable
            for (factory_id, bucket_index), variable
            in assignments.items()
            if bucket_index == index
        ]

        if not eligible_variables:
            raise ValueError(
                f"No eligible factory can produce "
                f"{bucket['Product Name']}."
            )

        model.add(
            sum(eligible_variables) == int(bucket["Units"])
        )

    # Apply factory capacity and utilization constraints.
    for factory in factories:

        factory_id = factory["factory_id"]
        capacity = factory["capacity_units"]

        load = sum(factory_loads[factory_id])

        model.add(load <= capacity)

        # Keep utilization comparisons in integer arithmetic.
        model.add(
            load * 10000 <= utilization_limit * capacity
        )

    # Minimize the maximum factory utilization.
    model.minimize(utilization_limit)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30

    status = solver.solve(model)

    if status not in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE,
    ):
        raise RuntimeError(
            "The optimizer could not find a feasible allocation."
        )

    # Collect product and destination allocations.
    allocation_rows = []

    for (factory_id, index), variable in assignments.items():

        allocated_units = solver.value(variable)

        if allocated_units == 0:
            continue

        bucket = demand.iloc[index]

        allocation_rows.append({
            "Factory ID": factory_id,
            "Product ID": bucket["Product ID"],
            "Product Name": bucket["Product Name"],
            "Country/Region": bucket["Country/Region"],
            "Region": bucket["Region"],
            "Allocated Units": allocated_units,
        })

    allocations = pd.DataFrame(
        allocation_rows,
        columns=[
            "Factory ID",
            "Product ID",
            "Product Name",
            "Country/Region",
            "Region",
            "Allocated Units",
        ],
    )

    # Calculate factory utilization.
    factory_summary = []

    for factory in factories:

        factory_id = factory["factory_id"]
        capacity = factory["capacity_units"]

        factory_allocations = allocations[
            allocations["Factory ID"] == factory_id
        ]

        allocated = int(
            factory_allocations["Allocated Units"].sum()
        )

        factory_summary.append({
            "Factory ID": factory_id,
            "Factory Name": factory["name"],
            "Capacity": capacity,
            "Allocated Units": allocated,
            "Spare Capacity": capacity - allocated,
            "Utilization (%)": round(
                allocated / capacity * 100,
                2,
            ),
        })

    summary = pd.DataFrame(factory_summary)

    # Final reconciliation check.
    allocated_total = int(
        allocations["Allocated Units"].sum()
    )

    if allocated_total != total_demand:
        raise RuntimeError(
            f"Demand mismatch: expected {total_demand}, "
            f"allocated {allocated_total}."
        )

    if (summary["Spare Capacity"] < 0).any():
        raise RuntimeError(
            "A factory has exceeded its available capacity."
        )

    return allocations, summary, solver.status_name(status)


def main():

    print("\nLoading factory configuration...")

    config = load_factory_config()
    validate_factory_config(config)

    print("Loading and preparing demand data...")

    raw_data = load_dataset()
    data = prepare_dataset(raw_data)

    demand = build_demand_buckets(data)

    print("Running factory allocation optimizer...")

    allocations, summary, status = optimize_allocation(
        config,
        demand,
    )

    total_demand = int(demand["Units"].sum())
    total_allocated = int(allocations["Allocated Units"].sum())

    output_directory = "data/processed"
    os.makedirs(output_directory, exist_ok=True)

    allocations_path = os.path.join(
        output_directory,
        "factory_allocations.csv",
    )

    summary_path = os.path.join(
        output_directory,
        "optimized_factory_summary.csv",
    )

    allocations.to_csv(
        allocations_path,
        index=False,
    )

    summary.to_csv(
        summary_path,
        index=False,
    )

    print("\n" + "=" * 65)
    print("FACTORY ALLOCATION OPTIMIZATION RESULTS")
    print("=" * 65)

    print(f"\nSolver Status       : {status}")
    print(f"Total Demand        : {total_demand:,} units")
    print(f"Total Allocated     : {total_allocated:,} units")
    print(f"Active Factories    : {len(summary)}")

    print("\nFACTORY UTILIZATION")
    print(summary.to_string(index=False))

    print("\nALLOCATION PREVIEW")
    print(allocations.head(15).to_string(index=False))

    print("\nVALIDATION")
    print(f"Demand reconciliation: {'PASSED' if total_demand == total_allocated else 'FAILED'}")
    print(f"Capacity constraints : {'PASSED' if (summary['Spare Capacity'] >= 0).all() else 'FAILED'}")

    print("\nOUTPUT FILES")
    print(f"- {allocations_path}")
    print(f"- {summary_path}")

    print("\nOptimization completed successfully.")


if __name__ == "__main__":
    main()
