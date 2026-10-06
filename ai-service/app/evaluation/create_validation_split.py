import os
import pandas as pd


INPUT_PATH = "/validation/evaluation/new_item_train_interactions.csv"
OUTPUT_DIR = "/validation/evaluation"

INNER_TRAIN_PATH = os.path.join(
    OUTPUT_DIR,
    "hybrid_inner_train_interactions.csv"
)

VALIDATION_PATH = os.path.join(
    OUTPUT_DIR,
    "hybrid_validation_interactions.csv"
)


def main():

    print("=" * 70)
    print("CREATING LEAKAGE-FREE HYBRID VALIDATION SPLIT")
    print("=" * 70)

    df = pd.read_csv(INPUT_PATH)

    print(f"Input interactions : {len(df)}")

    df["customer_id"] = df["customer_id"].astype(str)
    df["product_id"] = df["product_id"].astype(str)

    df["last_purchase_date"] = pd.to_datetime(
        df["last_purchase_date"],
        format="mixed",
        errors="coerce"
    )

    if df["last_purchase_date"].isna().any():
        raise ValueError(
            "Some last_purchase_date values could not be parsed."
        )

    # Preserve deterministic ordering
    df = df.sort_values(
        ["customer_id", "last_purchase_date", "product_id"]
    ).reset_index(drop=True)

    train_rows = []
    validation_rows = []

    for customer_id, group in df.groupby(
        "customer_id",
        sort=False
    ):

        seen_products = set()
        last_new_item_index = None

        for idx, row in group.iterrows():

            product_id = row["product_id"]

            if product_id not in seen_products:
                last_new_item_index = idx

            seen_products.add(product_id)

        # We need at least one previous interaction
        if last_new_item_index is None:
            train_rows.extend(group.to_dict("records"))
            continue

        customer_train = group[
            group.index < last_new_item_index
        ]

        customer_validation = group[
            group.index == last_new_item_index
        ]

        # Must have historical data before validation item
        if len(customer_train) == 0:
            train_rows.extend(group.to_dict("records"))
            continue

        train_rows.extend(
            customer_train.to_dict("records")
        )

        validation_rows.extend(
            customer_validation.to_dict("records")
        )

    inner_train = pd.DataFrame(train_rows)
    validation = pd.DataFrame(validation_rows)

    inner_train = inner_train.sort_values(
        ["customer_id", "last_purchase_date", "product_id"]
    ).reset_index(drop=True)

    validation = validation.sort_values(
        ["customer_id", "last_purchase_date", "product_id"]
    ).reset_index(drop=True)

    inner_train.to_csv(
        INNER_TRAIN_PATH,
        index=False
    )

    validation.to_csv(
        VALIDATION_PATH,
        index=False
    )

    print()
    print("RESULT")
    print("-" * 70)

    print(f"Inner train interactions : {len(inner_train)}")
    print(f"Validation interactions  : {len(validation)}")

    print(
        f"Inner train customers   : "
        f"{inner_train['customer_id'].nunique()}"
    )

    print(
        f"Validation customers    : "
        f"{validation['customer_id'].nunique()}"
    )

    print(
        f"Inner train products    : "
        f"{inner_train['product_id'].nunique()}"
    )

    print(
        f"Validation products     : "
        f"{validation['product_id'].nunique()}"
    )

    # ----------------------------------------------------------
    # Leakage checks
    # ----------------------------------------------------------

    violations = 0

    for customer_id, group in validation.groupby("customer_id"):

        customer_train_products = set(
            inner_train.loc[
                inner_train["customer_id"] == customer_id,
                "product_id"
            ]
        )

        validation_products = set(
            group["product_id"]
        )

        # Validation item should be NEW to that customer
        overlap = (
            customer_train_products
            & validation_products
        )

        if overlap:
            violations += len(overlap)

    print()
    print(
        f"Customer-level leakage violations : {violations}"
    )

    if violations != 0:
        raise RuntimeError(
            "Validation split contains customer-level leakage."
        )

    # ----------------------------------------------------------
    # Warm-start availability
    # ----------------------------------------------------------

    inner_products = set(
        inner_train["product_id"]
    )

    warm_start = validation[
        validation["product_id"].isin(inner_products)
    ]

    cold_start = validation[
        ~validation["product_id"].isin(inner_products)
    ]

    print(
        f"Warm-start validation targets     : "
        f"{len(warm_start)}"
    )

    print(
        f"Cold-start validation targets     : "
        f"{len(cold_start)}"
    )

    print()
    print(f"Saved:")
    print(INNER_TRAIN_PATH)
    print(VALIDATION_PATH)


if __name__ == "__main__":
    main()