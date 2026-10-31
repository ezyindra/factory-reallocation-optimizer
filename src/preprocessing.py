
import pandas as pd

from src.data_loader import load_dataset


DATE_COLUMNS = ["Order Date", "Ship Date"]

NUMERIC_COLUMNS = [
    "Sales",
    "Units",
    "Gross Profit",
    "Cost",
]


def prepare_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and prepare the original transaction data."""

    data = df.copy()

    # Parse dates using the confirmed source format.
    for column in DATE_COLUMNS:
        data[column] = pd.to_datetime(
            data[column],
            format="%d-%m-%Y",
            errors="coerce"
        )

    # Convert financial and quantity fields.
    for column in NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(
            data[column],
            errors="coerce"
        )

    # Remove accidental whitespace from text fields.
    text_columns = data.select_dtypes(
        include=["object", "string"]
    ).columns

    for column in text_columns:
        data[column] = data[column].str.strip()

    # Reject records with invalid essential fields.
    required_columns = [
        "Order ID",
        "Order Date",
        "Ship Date",
        "Product ID",
        "Product Name",
        "Country/Region",
        "Region",
        "Sales",
        "Units",
        "Gross Profit",
        "Cost",
    ]

    invalid_rows = data[required_columns].isna().any(axis=1)

    if invalid_rows.any():
        raise ValueError(
            f"Found {invalid_rows.sum()} records "
            "with missing or invalid essential values."
        )

    if (data["Units"] <= 0).any():
        raise ValueError("Units must be greater than zero.")

    # Add calendar features from the order date.
    data["Order Year"] = data["Order Date"].dt.year
    data["Order Month"] = data["Order Date"].dt.month
    data["Order Quarter"] = data["Order Date"].dt.quarter

    # Calculate the recorded date difference for auditing.
    data["Recorded Date Difference"] = (
        data["Ship Date"] - data["Order Date"]
    ).dt.days

    # Preserve the anomaly instead of silently correcting it.
    data["Date Difference Flag"] = (
        data["Recorded Date Difference"] > 30
    )

    return data



def create_product_region_demand(
    data: pd.DataFrame
) -> pd.DataFrame:
    """Aggregate actual demand by product and destination."""

    demand = (
        data.groupby(
            [
                "Product ID",
                "Product Name",
                "Country/Region",
                "Region",
            ],
            as_index=False
        )
        .agg(
            **{
                "Total Units": ("Units", "sum"),
                "Total Sales": ("Sales", "sum"),
                "Total Cost": ("Cost", "sum"),
                "Total Gross Profit": ("Gross Profit", "sum"),
                "Order Count": ("Order ID", "nunique"),
                "Customer Count": ("Customer ID", "nunique"),
            }
        )
    )

    demand["Gross Margin"] = (
        demand["Total Gross Profit"]
        / demand["Total Sales"].replace(0, pd.NA)
        * 100
    )

    return demand



def main():
    original = load_dataset()

    print("Preparing Nassau Candy dataset...")

    prepared = prepare_dataset(original)

    demand = create_product_region_demand(prepared)

    # Save processed outputs without modifying the original CSV.
    processed_path = (
        "data/processed/nassau_candy_clean.csv"
    )

    demand_path = (
        "data/processed/product_region_demand.csv"
    )

    prepared.to_csv(processed_path, index=False)
    demand.to_csv(demand_path, index=False)

    print("\nPREPROCESSING SUMMARY")
    print("-" * 50)

    print(f"Original records: {len(original):,}")
    print(f"Processed records: {len(prepared):,}")
    print(f"Product-region combinations: {len(demand):,}")

    print(
        "Flagged date differences:",
        f"{prepared['Date Difference Flag'].sum():,}"
    )

    print("\nProduct-region demand preview:")
    print(demand.head(10).to_string(index=False))

    print("\nSaved files:")
    print(processed_path)
    print(demand_path)


if __name__ == "__main__":
    main()
