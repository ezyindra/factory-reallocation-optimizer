
import pandas as pd

from src.data_loader import load_dataset
from src.preprocessing import (
    prepare_dataset,
    create_product_region_demand,
)


def analyze_product_demand(data):
    """Rank products by actual sales volume and profitability."""

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
                "Order Count": ("Order ID", "nunique"),
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


def analyze_regional_demand(data):
    """Measure demand and profitability across regions."""

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
                "Customer Count": ("Customer ID", "nunique"),
                "Order Count": ("Order ID", "nunique"),
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


def analyze_product_region_demand(data):
    """Create a product-by-region unit demand matrix."""

    return pd.pivot_table(
        data,
        index="Product Name",
        columns="Region",
        values="Units",
        aggfunc="sum",
        fill_value=0,
    )


def main():
    original = load_dataset()
    data = prepare_dataset(original)

    products = analyze_product_demand(data)
    regions = analyze_regional_demand(data)
    product_regions = analyze_product_region_demand(data)

    print("\n" + "=" * 60)
    print("PRODUCT DEMAND ANALYSIS")
    print("=" * 60)

    print(products.to_string(index=False))

    print("\n" + "=" * 60)
    print("REGIONAL DEMAND ANALYSIS")
    print("=" * 60)

    print(regions.to_string(index=False))

    print("\n" + "=" * 60)
    print("PRODUCT-REGION DEMAND MATRIX")
    print("=" * 60)

    print(product_regions.to_string())

    products.to_csv(
        "data/processed/product_demand.csv",
        index=False
    )

    regions.to_csv(
        "data/processed/regional_demand.csv",
        index=False
    )

    product_regions.to_csv(
        "data/processed/product_region_matrix.csv"
    )

    print("\nAnalysis files saved successfully.")


if __name__ == "__main__":
    main()
