
import pandas as pd

from src.data_loader import load_dataset
from src.preprocessing import prepare_dataset
from src.factory_config import load_factory_config, validate_factory_config
from src.optimization_engine import build_demand_buckets


def validate_demand_reconciliation(demand, allocations):
    """Check that each product-market demand bucket is fully allocated."""

    keys = [
        "Product ID",
        "Product Name",
        "Country/Region",
        "Region",
    ]

    expected = (
        demand.groupby(keys, as_index=False)["Units"]
        .sum()
        .rename(columns={"Units": "Expected Units"})
    )

    actual = (
        allocations.groupby(keys, as_index=False)["Allocated Units"]
        .sum()
        .rename(columns={"Allocated Units": "Allocated Units"})
    )

    comparison = expected.merge(
        actual,
        on=keys,
        how="outer",
    )

    comparison[["Expected Units", "Allocated Units"]] = (
        comparison[["Expected Units", "Allocated Units"]]
        .fillna(0)
    )

    comparison["Difference"] = (
        comparison["Expected Units"]
        - comparison["Allocated Units"]
    )

    passed = bool((comparison["Difference"] == 0).all())

    return passed, comparison


def validate_factory_capacity(config, allocations):
    """Check that no factory exceeds its configured capacity."""

    factory_rows = []

    for factory in config["factories"]:
        factory_id = factory["factory_id"]
        capacity = int(factory["capacity_units"])

        allocated = int(
            allocations.loc[
                allocations["Factory ID"] == factory_id,
                "Allocated Units",
            ].sum()
        )

        factory_rows.append({
            "Factory ID": factory_id,
            "Factory Name": factory["name"],
            "Enabled": factory.get("enabled", False),
            "Capacity": capacity,
            "Allocated Units": allocated,
            "Spare Capacity": capacity - allocated,
            "Within Capacity": allocated <= capacity,
        })

    result = pd.DataFrame(factory_rows)

    passed = bool(
        (
            result["Within Capacity"]
            & (
                result["Allocated Units"].eq(0)
                | result["Enabled"]
            )
        ).all()
    )

    return passed, result


def validate_factory_assignments(config, allocations):
    """Check that allocations use only enabled and eligible factories."""

    factory_lookup = {
        factory["factory_id"]: factory
        for factory in config["factories"]
    }

    issues = []

    for _, row in allocations.iterrows():

        factory_id = row["Factory ID"]
        product_id = str(row["Product ID"])
        product_name = str(row["Product Name"])

        factory = factory_lookup.get(factory_id)

        if factory is None:
            issues.append(
                f"Unknown factory ID: {factory_id}"
            )
            continue

        if not factory.get("enabled", False):
            issues.append(
                f"Disabled factory received allocation: {factory_id}"
            )

        supported = factory.get(
            "supported_products", "all"
        )

        product_supported = (
            supported == "all"
            or (
                isinstance(supported, list)
                and (
                    product_id in supported
                    or product_name in supported
                )
            )
        )

        if not product_supported:
            issues.append(
                f"{factory_id} is not eligible for {product_name}"
            )

    return len(issues) == 0, issues


def run_validation(config, demand, allocations):

    checks = []

    reconciliation_passed, reconciliation = (
        validate_demand_reconciliation(
            demand,
            allocations,
        )
    )

    checks.append({
        "Validation": "Product-market demand reconciliation",
        "Status": reconciliation_passed,
    })

    capacity_passed, capacity_summary = (
        validate_factory_capacity(
            config,
            allocations,
        )
    )

    checks.append({
        "Validation": "Factory capacity constraints",
        "Status": capacity_passed,
    })

    assignments_passed, assignment_issues = (
        validate_factory_assignments(
            config,
            allocations,
        )
    )

    checks.append({
        "Validation": "Factory eligibility and status",
        "Status": assignments_passed,
    })

    validation_report = pd.DataFrame(checks)

    all_passed = bool(validation_report["Status"].all())

    return (
        all_passed,
        validation_report,
        reconciliation,
        capacity_summary,
        assignment_issues,
    )


def main():

    config = load_factory_config()
    validate_factory_config(config)

    raw_data = load_dataset()
    data = prepare_dataset(raw_data)

    demand = build_demand_buckets(data)

    allocations = pd.read_csv(
        "data/processed/factory_allocations.csv"
    )

    all_passed, report, reconciliation, capacity, issues = (
        run_validation(
            config,
            demand,
            allocations,
        )
    )

    print("\n" + "=" * 65)
    print("INDEPENDENT ALLOCATION VALIDATION")
    print("=" * 65)

    print("\nVALIDATION RESULTS")
    print(report.to_string(index=False))

    print("\nFACTORY CAPACITY CHECK")
    print(capacity.to_string(index=False))

    if issues:
        print("\nASSIGNMENT ISSUES")
        for issue in issues:
            print(f"- {issue}")

    mismatches = reconciliation[
        reconciliation["Difference"] != 0
    ]

    if not mismatches.empty:
        print("\nDEMAND RECONCILIATION ISSUES")
        print(mismatches.to_string(index=False))

    print("\n" + "-" * 65)

    if all_passed:
        print("RESULT: ALL VALIDATIONS PASSED")
    else:
        print("RESULT: VALIDATION FAILED")

    print("-" * 65)

    report.to_csv(
        "data/processed/validation_report.csv",
        index=False,
    )

    capacity.to_csv(
        "data/processed/validation_factory_capacity.csv",
        index=False,
    )

    reconciliation.to_csv(
        "data/processed/validation_demand_reconciliation.csv",
        index=False,
    )

    if not all_passed:
        raise SystemExit("Allocation validation failed.")

    print("\nValidation reports saved successfully.")


if __name__ == "__main__":
    main()
