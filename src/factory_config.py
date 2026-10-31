
import json
from pathlib import Path

import pandas as pd

from src.data_loader import load_dataset
from src.preprocessing import prepare_dataset


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CONFIG_PATH = PROJECT_ROOT / "config" / "factory_assumptions.json"


def load_factory_config():
    """Load the hypothetical factory network configuration."""

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Factory configuration not found: {CONFIG_PATH}"
        )

    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        config = json.load(file)

    return config


def validate_factory_config(config):
    """Check factory profiles and destination definitions."""

    factories = config.get("factories", [])
    destinations = config.get("destinations", [])

    if not factories:
        raise ValueError("No factory profiles configured.")

    if not destinations:
        raise ValueError("No destinations configured.")

    factory_ids = [
        factory.get("factory_id") for factory in factories
    ]

    if len(factory_ids) != len(set(factory_ids)):
        raise ValueError("Duplicate factory IDs found.")

    for factory in factories:
        if not factory.get("factory_id"):
            raise ValueError("A factory is missing its ID.")

        if not factory.get("name"):
            raise ValueError(
                f"Factory {factory['factory_id']} has no name."
            )

        capacity = factory.get("capacity_units")

        if not isinstance(capacity, int) or isinstance(capacity, bool):
            raise ValueError(
                f"Invalid capacity for {factory['factory_id']}."
            )

        if capacity <= 0:
            raise ValueError(
                f"Capacity must be positive for {factory['factory_id']}."
            )

    destination_keys = [
        (item.get("country"), item.get("region"))
        for item in destinations
    ]

    if len(destination_keys) != len(set(destination_keys)):
        raise ValueError("Duplicate destination combinations found.")

    return True


def calculate_capacity_summary(config, total_demand):
    """Compare available factory capacity with actual unit demand."""

    factories = [
        factory
        for factory in config["factories"]
        if factory.get("enabled", True)
    ]

    total_capacity = sum(
        factory["capacity_units"]
        for factory in factories
    )

    spare_capacity = total_capacity - total_demand

    utilization = (
        total_demand / total_capacity * 100
        if total_capacity > 0
        else 0
    )

    return {
        "active_factories": len(factories),
        "total_demand": int(total_demand),
        "total_capacity": total_capacity,
        "spare_capacity": spare_capacity,
        "utilization_percent": utilization,
        "capacity_sufficient": spare_capacity >= 0,
    }


def main():
    config = load_factory_config()

    validate_factory_config(config)

    original = load_dataset()
    data = prepare_dataset(original)

    total_demand = data["Units"].sum()

    summary = calculate_capacity_summary(
        config,
        total_demand
    )

    print("\n" + "=" * 60)
    print("FACTORY CONFIGURATION VALIDATION")
    print("=" * 60)

    print(f"Scenario: {config['scenario_name']}")
    print(f"Classification: {config['data_classification']}")
    print(f"Configured factories: {len(config['factories'])}")
    print(f"Destination markets: {len(config['destinations'])}")

    print("\nFACTORY PROFILES")
    print("-" * 60)

    for factory in config["factories"]:
        status = (
            "Active" if factory.get("enabled", True)
            else "Disabled"
        )

        print(
            f"{factory['factory_id']} | "
            f"{factory['name']:<18} | "
            f"{factory['capacity_units']:>7,} units | "
            f"{status}"
        )

    print("\nCAPACITY ANALYSIS")
    print("-" * 60)

    print(f"Actual recorded demand: {summary['total_demand']:,}")
    print(f"Available capacity:     {summary['total_capacity']:,}")
    print(f"Spare capacity:         {summary['spare_capacity']:,}")
    print(f"Capacity utilization:   {summary['utilization_percent']:.2f}%")

    print(
        "Capacity status:",
        "SUFFICIENT" if summary["capacity_sufficient"]
        else "INSUFFICIENT"
    )

    if not summary["capacity_sufficient"]:
        raise ValueError(
            "Configured factory capacity is below recorded demand."
        )

    print("\nConfiguration validation completed successfully.")


if __name__ == "__main__":
    main()
