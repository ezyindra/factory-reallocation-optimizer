import pandas as pd
import pytest

from src.optimization_engine import (
    build_demand_buckets,
    optimize_allocation,
)


@pytest.fixture
def sample_demand():
    return pd.DataFrame([
        {
            "Product ID": "P001",
            "Product Name": "Chocolate Bar",
            "Country/Region": "United States",
            "Region": "Atlantic",
            "Units": 100,
        },
        {
            "Product ID": "P002",
            "Product Name": "Gummy Bears",
            "Country/Region": "Canada",
            "Region": "Pacific",
            "Units": 150,
        },
        {
            "Product ID": "P001",
            "Product Name": "Chocolate Bar",
            "Country/Region": "United States",
            "Region": "Atlantic",
            "Units": 50,
        },
    ])


@pytest.fixture
def sample_config():
    return {
        "factories": [
            {
                "factory_id": "FAC-001",
                "name": "Factory North",
                "capacity_units": 200,
                "enabled": True,
                "supported_products": "all",
            },
            {
                "factory_id": "FAC-002",
                "name": "Factory South",
                "capacity_units": 200,
                "enabled": True,
                "supported_products": "all",
            },
        ]
    }


def test_build_demand_buckets_preserves_total_units(sample_demand):
    demand = build_demand_buckets(sample_demand)

    assert demand["Units"].sum() == sample_demand["Units"].sum()


def test_build_demand_buckets_groups_duplicate_markets(sample_demand):
    demand = build_demand_buckets(sample_demand)

    chocolate = demand[
        demand["Product ID"] == "P001"
    ]

    assert len(chocolate) == 1
    assert chocolate.iloc[0]["Units"] == 150


def test_build_demand_buckets_rejects_missing_columns():
    invalid_data = pd.DataFrame({
        "Product ID": ["P001"],
        "Units": [100],
    })

    with pytest.raises(ValueError, match="Missing demand columns"):
        build_demand_buckets(invalid_data)


def test_build_demand_buckets_rejects_negative_units():
    invalid_data = pd.DataFrame([{
        "Product ID": "P001",
        "Product Name": "Chocolate Bar",
        "Country/Region": "United States",
        "Region": "Atlantic",
        "Units": -10,
    }])

    with pytest.raises(ValueError, match="negative units"):
        build_demand_buckets(invalid_data)


def test_optimizer_allocates_all_demand(sample_config, sample_demand):
    demand = build_demand_buckets(sample_demand)

    allocations, summary, status = optimize_allocation(
        sample_config,
        demand,
    )

    assert allocations["Allocated Units"].sum() == demand["Units"].sum()
    assert status in ("OPTIMAL", "FEASIBLE")
    assert len(summary) == 2


def test_optimizer_respects_factory_capacity(sample_config, sample_demand):
    demand = build_demand_buckets(sample_demand)

    allocations, summary, status = optimize_allocation(
        sample_config,
        demand,
    )

    assert (summary["Spare Capacity"] >= 0).all()
    assert (
        summary["Allocated Units"] <= summary["Capacity"]
    ).all()


def test_optimizer_respects_factory_eligibility(sample_demand):
    config = {
        "factories": [
            {
                "factory_id": "FAC-001",
                "name": "Chocolate Factory",
                "capacity_units": 200,
                "enabled": True,
                "supported_products": ["P001"],
            },
            {
                "factory_id": "FAC-002",
                "name": "Gummy Factory",
                "capacity_units": 200,
                "enabled": True,
                "supported_products": ["P002"],
            },
        ]
    }

    demand = build_demand_buckets(sample_demand)

    allocations, summary, status = optimize_allocation(
        config,
        demand,
    )

    chocolate_factories = allocations[
        allocations["Product ID"] == "P001"
    ]["Factory ID"].unique()

    gummy_factories = allocations[
        allocations["Product ID"] == "P002"
    ]["Factory ID"].unique()

    assert list(chocolate_factories) == ["FAC-001"]
    assert list(gummy_factories) == ["FAC-002"]


def test_optimizer_rejects_insufficient_capacity(
    sample_config,
    sample_demand,
):
    demand = build_demand_buckets(sample_demand)

    config = {
        "factories": [
            {
                **sample_config["factories"][0],
                "capacity_units": 100,
            }
        ]
    }

    with pytest.raises(ValueError, match="Insufficient factory capacity"):
        optimize_allocation(config, demand)


def test_optimizer_rejects_no_enabled_factories(sample_demand):
    config = {
        "factories": [
            {
                "factory_id": "FAC-001",
                "name": "Disabled Factory",
                "capacity_units": 500,
                "enabled": False,
                "supported_products": "all",
            }
        ]
    }

    demand = build_demand_buckets(sample_demand)

    with pytest.raises(ValueError, match="No enabled factories"):
        optimize_allocation(config, demand)


def test_optimizer_rejects_empty_demand(sample_config):
    empty_demand = pd.DataFrame(
        columns=[
            "Product ID",
            "Product Name",
            "Country/Region",
            "Region",
            "Units",
        ]
    )

    with pytest.raises(ValueError, match="Demand dataset is empty"):
        optimize_allocation(sample_config, empty_demand)


def test_optimizer_rejects_unsupported_product(sample_demand):
    config = {
        "factories": [
            {
                "factory_id": "FAC-001",
                "name": "Chocolate Factory",
                "capacity_units": 500,
                "enabled": True,
                "supported_products": ["P001"],
            }
        ]
    }

    demand = build_demand_buckets(sample_demand)

    with pytest.raises(ValueError, match="No eligible factory"):
        optimize_allocation(config, demand)
