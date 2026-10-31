
import pandas as pd

from src.data_loader import load_dataset


def audit_date_column(df, column):
    print("\n" + "=" * 65)
    print(f"DATE AUDIT: {column}")
    print("=" * 65)

    raw = df[column].astype("string").str.strip()

    print("\nOriginal date examples:")
    print(raw.drop_duplicates().head(15).to_string(index=False))

    # Compare two possible parsing preferences.
    parsed_default = pd.to_datetime(
        raw, format="mixed", errors="coerce", dayfirst=False
    )

    parsed_dayfirst = pd.to_datetime(
        raw, format="mixed", errors="coerce", dayfirst=True
    )

    print("\nPARSING COMPARISON")
    print("-" * 65)

    print(
        f"Day-first FALSE: "
        f"{parsed_default.notna().sum():,} valid, "
        f"{parsed_default.isna().sum():,} invalid"
    )

    print(
        f"Day-first TRUE:  "
        f"{parsed_dayfirst.notna().sum():,} valid, "
        f"{parsed_dayfirst.isna().sum():,} invalid"
    )

    print("\nExamples where interpretations differ:")
    different = (
        parsed_default.notna()
        & parsed_dayfirst.notna()
        & (parsed_default != parsed_dayfirst)
    )

    comparison = pd.DataFrame({
        "Original": raw[different],
        "Day-first FALSE": parsed_default[different],
        "Day-first TRUE": parsed_dayfirst[different],
    })

    print(comparison.head(15).to_string(index=False))

    print("\nExamples still invalid with both methods:")
    invalid = parsed_default.isna() & parsed_dayfirst.isna()

    print(raw[invalid].drop_duplicates().head(15).to_string(index=False))


if __name__ == "__main__":
    dataset = load_dataset()

    audit_date_column(dataset, "Order Date")
    audit_date_column(dataset, "Ship Date")
