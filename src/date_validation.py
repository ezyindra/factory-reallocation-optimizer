
import pandas as pd

from src.data_loader import load_dataset


def main():
    df = load_dataset()

    date_columns = ["Order Date", "Ship Date"]

    for column in date_columns:
        df[column] = pd.to_datetime(
            df[column],
            format="%d-%m-%Y",
            errors="coerce"
        )

        print("\n" + "=" * 55)
        print(f"{column} — VALIDATION")
        print("=" * 55)

        print("Valid dates:", df[column].notna().sum())
        print("Invalid dates:", df[column].isna().sum())
        print("Earliest:", df[column].min())
        print("Latest:", df[column].max())

    lead_time = (df["Ship Date"] - df["Order Date"]).dt.days

    print("\n" + "=" * 55)
    print("ORDER-TO-SHIP DATE DIFFERENCE")
    print("=" * 55)

    print(lead_time.describe().to_string())

    print("\nNegative differences:", (lead_time < 0).sum())
    print("Differences above 30 days:", (lead_time > 30).sum())


if __name__ == "__main__":
    main()
