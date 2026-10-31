
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "Nassau Candy Distributor.csv"


def load_dataset() -> pd.DataFrame:
    """Load the original Nassau Candy dataset."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    if df.empty:
        raise ValueError("The dataset is empty.")

    return df


def inspect_dataset(df: pd.DataFrame) -> None:
    """Display a concise overview of the dataset."""

    print("\n" + "=" * 65)
    print("NASSAU CANDY — DATASET INSPECTION")
    print("=" * 65)

    print(f"\nRows: {df.shape[0]:,}")
    print(f"Columns: {df.shape[1]}")

    print("\nCOLUMN OVERVIEW")
    print("-" * 65)

    overview = pd.DataFrame({
        "Column": df.columns,
        "Data Type": df.dtypes.astype(str).values,
        "Missing Values": df.isna().sum().values,
        "Unique Values": df.nunique().values,
    })

    print(overview.to_string(index=False))

    print("\nDUPLICATE ROWS")
    print("-" * 65)
    print(f"Duplicate records: {df.duplicated().sum():,}")

    print("\nNUMERIC SUMMARY")
    print("-" * 65)
    print(df.describe().to_string())

    print("\nPOSSIBLE DATE COLUMNS")
    print("-" * 65)

    date_columns = [
        col for col in df.columns
        if "date" in col.lower()
    ]

    if date_columns:
        for col in date_columns:
            parsed = pd.to_datetime(
    df[col],
    format="%d-%m-%Y",
    errors="coerce"
)
            print(f"\n{col}")
            print(f"  Earliest: {parsed.min()}")
            print(f"  Latest:   {parsed.max()}")
            print(f"  Invalid:  {parsed.isna().sum():,}")
    else:
        print("No columns with 'date' in their names were found.")


if __name__ == "__main__":
    dataset = load_dataset()
    inspect_dataset(dataset)
