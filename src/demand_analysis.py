
import pandas as pd

from src.data_loader import load_dataset
from src.preprocessing import prepare_dataset


def analyze_product_demand(data: pd.DataFrame) -> pd.DataFrame:
    """Summarize demand and profitability for each product."""

    products = (
        data.groupby(
            ["Product ID", "Product Name"],
            as_index=False
        )
        .agg(
            **{
                "Total Units": ("Units", "sum"),
                "Total Sales": ("Sales", "sum"),
                "Total Profit": ("Gross Profit", "sum"),
                "Total Cost": ("Cost", "sum"),
                "Order Count": ("Order ID", "nunique"),
                "Customer Count": ("Customer ID", "nunique"),
            }
        )
    )

    products["Profit Margin"] = (
        products["Total Profit"]
        / products["Total Sales"].replace(0, pd.NA)
        * 100
    )

    return products.sort_values(
        "Total Units",
        ascending=False
    )


def analyze_regional_demand(data: pd.DataFrame) -> pd.DataFrame:
    """Summarize business performance by country and region."""

    regions = (
        data.groupby(
            ["Country/Region", "Region"],
            as_index=False
        )
        .agg(
            **{
                "Total Units": ("Units", "sum"),
                "Total Sales": ("Sales", "sum"),
                "Total Profit": ("Gross Profit", "sum"),
                "Total Cost": ("Cost", "sum"),
                "Order Count": ("Order ID", "nunique"),
                "Customer Count": ("Customer ID", "nunique"),
            }
        )
    )

    regions["Profit Margin"] = (
        regions["Total Profit"]
        / regions["Total Sales"].replace(0, pd.NA)
        * 100
    )

    return regions.sort_values(
        "Total Sales",
        ascending=False
    )


def create_demand_matrix(data: pd.DataFrame) -> pd.DataFrame:
    """Show unit demand for each product across destination regions."""

    matrix = pd.pivot_table(
        data,
        index="Product Name",
        columns="Region",
        values="Units",
        aggfunc="sum",
        fill_value=0
    )

    return matrix


def validate_aggregations(
    data: pd.DataFrame,
    products: pd.DataFrame,
    regions: pd.DataFrame
) -> None:
    """Check that aggregation preserves the original totals."""

    checks = {
        "Total units": (
            data["Units"].sum(),
            products["Total Units"].sum()
        ),
        "Total sales": (
            data["Sales"].sum(),
            products["Total Sales"].sum()
        ),
        "Total gross profit": (
            data["Gross Profit"].sum(),
            products["Total Profit"].sum()
        ),
        "Regional sales": (
            data["Sales"].sum(),
            regions["Total Sales"].sum()
        ),
    }

    print("\nAGGREGATION VALIDATION")
    print("-" * 55)

    for name, (original, aggregated) in checks.items():
        passed = abs(original - aggregated) < 0.01

        print(
            f"{name:<25} "
            f"{'PASSED' if passed else 'FAILED'} "
            f"({aggregated:,.2f})"
        )

        if not passed:
            raise ValueError(
                f"Aggregation mismatch: {name}"
            )


def main():
    original = load_dataset()
    data = prepare_dataset(original)

    products = analyze_product_demand(data)
    regions = analyze_regional_demand(data)
    matrix = create_demand_matrix(data)

    validate_aggregations(data, products, regions)

    print("\n" + "=" * 65)
    print("PRODUCT DEMAND — TOP 10")
    print("=" * 65)

    print(
        products.head(10).to_string(index=False)
    )

    print("\n" + "=" * 65)
    print("REGIONAL PERFORMANCE")
    print("=" * 65)

    print(
        regions.to_string(index=False)
    )

    print("\n" + "=" * 65)
    print("PRODUCT-REGION DEMAND MATRIX")
    print("=" * 65)

    print(matrix.to_string())

    products.to_csv(
        "data/processed/product_demand.csv",
        index=False
    )

    regions.to_csv(
        "data/processed/regional_demand.csv",
        index=False
    )

    matrix.to_csv(
        "data/processed/product_region_matrix.csv"
    )

    print("\nAnalysis completed.")
    print("Three output files saved in data/processed/")


if __name__ == "__main__":
    main()
