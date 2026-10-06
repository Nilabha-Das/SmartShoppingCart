import os
import pandas as pd


INPUT_PATH = "/app/data/phase2/customer_product_interactions.csv"

OUTPUT_DIR = "/validation/evaluation"

TRAIN_PATH = os.path.join(
    OUTPUT_DIR,
    "train_interactions.csv"
)

TEST_PATH = os.path.join(
    OUTPUT_DIR,
    "test_interactions.csv"
)


def create_temporal_split():

    print("Loading interaction data...")

    df = pd.read_csv(INPUT_PATH)

    print(f"Total interactions: {len(df)}")
    print(f"Customers: {df['customer_id'].nunique()}")
    print(f"Products: {df['product_id'].nunique()}")

    # Parse DD-MM-YYYY explicitly
    df["last_purchase_date"] = pd.to_datetime(
        df["last_purchase_date"],
        format="%d-%m-%Y"
    )

    # Sort chronologically
    df = df.sort_values(
        ["customer_id", "last_purchase_date"]
    ).reset_index(drop=True)

    train_parts = []
    test_parts = []

    # Hold out the latest interaction for every customer
    for customer_id, customer_df in df.groupby(
        "customer_id",
        sort=False
    ):

        customer_df = customer_df.sort_values(
            "last_purchase_date"
        )

        if len(customer_df) < 2:
            continue

        train_parts.append(
            customer_df.iloc[:-1]
        )

        test_parts.append(
            customer_df.iloc[-1:]
        )

    train_df = pd.concat(
        train_parts,
        ignore_index=True
    )

    test_df = pd.concat(
        test_parts,
        ignore_index=True
    )

    # ---------------------------------------------------------
    # Save evaluation datasets
    # ---------------------------------------------------------

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    train_df.to_csv(
        TRAIN_PATH,
        index=False
    )

    test_df.to_csv(
        TEST_PATH,
        index=False
    )

    # ---------------------------------------------------------
    # Report
    # ---------------------------------------------------------

    print()
    print("TEMPORAL SPLIT")
    print("-------------------------")

    print(
        f"Train interactions: {len(train_df)}"
    )

    print(
        f"Test interactions:  {len(test_df)}"
    )

    print(
        f"Train customers:    "
        f"{train_df['customer_id'].nunique()}"
    )

    print(
        f"Test customers:     "
        f"{test_df['customer_id'].nunique()}"
    )

    print()
    print("Date range")
    print("-------------------------")

    print(
        f"Train: "
        f"{train_df['last_purchase_date'].min().date()} "
        f"-> "
        f"{train_df['last_purchase_date'].max().date()}"
    )

    print(
        f"Test:  "
        f"{test_df['last_purchase_date'].min().date()} "
        f"-> "
        f"{test_df['last_purchase_date'].max().date()}"
    )

    print()
    print("Files saved")
    print("-------------------------")

    print(TRAIN_PATH)
    print(TEST_PATH)


if __name__ == "__main__":
    create_temporal_split()