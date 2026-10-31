import pandas as pd
import pytest

from src.allocation_validator import (
    validate_demand_reconciliation,
    validate_factory_capacity,
    validate_factory_assignments,
    run_validation,
)


@pytest.fixture
def sample_config():
    return {
        "factories": [
            {
                "factory_id": "FAC-001",
                "name": "Factory North",
                "capacity_units": 200,
                "enabled": True,
                "supported_products": ["P001"],
            },
            {
                "factory_id": "FAC-002",
                "name": "Factory South",
                "capacity_units": 200,
                "enabled": True,
                "supported_products": ["P002"],
            },
        ]
    }


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
    ])


@pytest.fixture
def valid_allocations():
    return pd.DataFrame([
        {
            "Factory ID": "FAC-001",
            "Product ID": "P001",
            "Product Name": "Chocolate Bar",
            "Country/Region": "United States",
            "Region": "Atlantic",
            "Allocated Units": 100,
        },
        {
            "Factory ID": "FAC-002",
            "Product ID": "P002",
            "Product Name": "Gummy Bears",
            "Country/Region": "Canada",
            "Region": "Pacific",
            "Allocated Units": 150,
        },
    ])


def test_demand_reconciliation_passes(
    sample_demand,
    valid_allocations,
):
    passed, comparison = validate_demand_reconciliation(
        sample_demand,
        valid_allocations,
    )

    assert passed is True
    assert (comparison["Difference"] == 0).all()


def test_demand_reconciliation_detects_shortage(
    sample_demand,
    valid_allocations,
):
    invalid_allocations = valid_allocations.copy()
    invalid_allocations.loc[0, "Allocated Units"] = 80

    passed, comparison = validate_demand_reconciliation(
        sample_demand,
        invalid_allocations,
    )

    assert passed is False
    assert (comparison["Difference"] != 0).any()


def test_demand_reconciliation_detects_unexpected_allocation(
    sample_demand,
    valid_allocations,
):
    invalid_allocations = pd.concat(
        [
            valid_allocations,
            pd.DataFrame([{
                "Factory ID": "FAC-001",
                "Product ID": "P999",
                "Product Name": "Unknown Product",
                "Country/Region": "United States",
                "Region": "Atlantic",
                "Allocated Units": 10,
            }]),
        ],
        ignore_index=True,
    )

    passed, comparison = validate_demand_reconciliation(
        sample_demand,
        invalid_allocations,
    )

    assert passed is False


def test_factory_capacity_passes(
    sample_config,
    valid_allocations,
):
    passed, result = validate_factory_capacity(
        sample_config,
        valid_allocations,
    )

    assert passed is True
    assert result["Within Capacity"].all()


def test_factory_capacity_detects_overallocation(
    sample_config,
    valid_allocations,
):
    invalid_allocations = valid_allocations.copy()
    invalid_allocations.loc[0, "Allocated Units"] = 250

    passed, result = validate_factory_capacity(
        sample_config,
        invalid_allocations,
    )

    assert passed is False
    assert not result["Within Capacity"].all()


def test_disabled_factory_cannot_receive_allocation(
    sample_config,
    valid_allocations,
):
    config = {
        "factories": [
            {
                **sample_config["factories"][0],
                "enabled": False,
            },
            sample_config["factories"][1],
        ]
    }

    passed, result = validate_factory_capacity(
        config,
        valid_allocations,
    )

    assert passed is False


def test_factory_assignment_passes(
    sample_config,
    valid_allocations,
):
    passed, issues = validate_factory_assignments(
        sample_config,
        valid_allocations,
    )

    assert passed is True
    assert issues == []


def test_factory_assignment_detects_unknown_factory(
    sample_config,
    valid_allocations,
):
    invalid_allocations = valid_allocations.copy()
    invalid_allocations.loc[0, "Factory ID"] = "FAC-999"

    passed, issues = validate_factory_assignments(
        sample_config,
        invalid_allocations,
    )

    assert passed is False
    assert any("Unknown factory ID" in issue for issue in issues)


def test_factory_assignment_detects_unsupported_product(
    sample_config,
    valid_allocations,
):
    invalid_allocations = valid_allocations.copy()
    invalid_allocations.loc[0, "Factory ID"] = "FAC-002"

    passed, issues = validate_factory_assignments(
        sample_config,
        invalid_allocations,
    )

    assert passed is False
    assert any("not eligible" in issue for issue in issues)


def test_factory_assignment_detects_disabled_factory(
    sample_config,
    valid_allocations,
):
    config = {
        "factories": [
            {
                **sample_config["factories"][0],
                "enabled": False,
            },
            sample_config["factories"][1],
        ]
    }

    passed, issues = validate_factory_assignments(
        config,
        valid_allocations,
    )

    assert passed is False
    assert any("Disabled factory" in issue for issue in issues)


def test_complete_validation_passes(
    sample_config,
    sample_demand,
    valid_allocations,
):
    passed, report, reconciliation, capacity, issues = run_validation(
        sample_config,
        sample_demand,
        valid_allocations,
    )

    assert passed is True
    assert report["Status"].all()
    assert issues == []


def test_complete_validation_detects_invalid_allocations(
    sample_config,
    sample_demand,
    valid_allocations,
):
    invalid_allocations = valid_allocations.copy()
    invalid_allocations.loc[0, "Allocated Units"] = 250

    passed, report, reconciliation, capacity, issues = run_validation(
        sample_config,
        sample_demand,
        invalid_allocations,
    )

    assert passed is False
    assert not report["Status"].all()
