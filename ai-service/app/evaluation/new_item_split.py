import os
import pandas as pd


# ============================================================
# PATHS
# ============================================================

INPUT_PATH = (
    "/app/data/phase2/customer_product_interactions.csv"
)

OUTPUT_DIR = "/validation/evaluation"

TRAIN_PATH = os.path.join(
    OUTPUT_DIR,
    "new_item_train_interactions.csv"
)

TEST_PATH = os.path.join(
    OUTPUT_DIR,
    "new_item_test_interactions.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("TEMPORAL NEW-ITEM SPLIT")
print("=" * 70)

print("\nLoading interaction data...")

df = pd.read_csv(INPUT_PATH)

print(f"Total interactions: {len(df)}")
print(f"Customers: {df['customer_id'].nunique()}")
print(f"Products: {df['product_id'].nunique()}")


# ============================================================
# DATE
# ============================================================

df["last_purchase_date"] = pd.to_datetime(
    df["last_purchase_date"],
    format="mixed"
)


# ============================================================
# SORT CHRONOLOGICALLY
# ============================================================

df = df.sort_values(
    [
        "customer_id",
        "last_purchase_date"
    ]
).reset_index(drop=True)


# ============================================================
# FIND LATEST NEW-TO-CUSTOMER PRODUCT
# ============================================================

test_indices = []

print("\nFinding latest new-to-customer interaction...")

for customer_id, customer_df in df.groupby(
    "customer_id",
    sort=False
):

    seen_products = set()
    latest_new_index = None

    for index, row in customer_df.iterrows():

        product_id = row["product_id"]

        # Product has never been purchased by this customer
        if product_id not in seen_products:
            latest_new_index = index

        seen_products.add(product_id)

    if latest_new_index is not None:
        test_indices.append(latest_new_index)


# ============================================================
# CREATE SPLIT
# ============================================================

test_df = df.loc[test_indices].copy()

# IMPORTANT:
# For every test interaction, only interactions BEFORE
# that test interaction are allowed into training.

train_indices = []

test_index_set = set(test_indices)

for customer_id, customer_df in df.groupby(
    "customer_id",
    sort=False
):

    customer_test = test_df[
        test_df["customer_id"] == customer_id
    ]

    if customer_test.empty:
        continue

    test_index = customer_test.index[0]

    for index in customer_df.index:

        if index < test_index:
            train_indices.append(index)


train_df = df.loc[train_indices].copy()


# ============================================================
# SAFETY CHECK
# ============================================================

print("\nRunning leakage checks...")

violations = 0

for row in test_df.itertuples(index=False):

    customer_id = row.customer_id
    product_id = row.product_id

    customer_train_products = set(
        train_df.loc[
            train_df["customer_id"] == customer_id,
            "product_id"
        ]
    )

    if product_id in customer_train_products:
        violations += 1


print(f"Leakage violations: {violations}")


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("NEW-ITEM TEMPORAL SPLIT")
print("=" * 70)

print(f"Train interactions: {len(train_df)}")
print(f"Test interactions:  {len(test_df)}")

print(
    f"Train customers:    "
    f"{train_df['customer_id'].nunique()}"
)

print(
    f"Test customers:     "
    f"{test_df['customer_id'].nunique()}"
)

print(
    f"Train products:     "
    f"{train_df['product_id'].nunique()}"
)

print(
    f"Test products:      "
    f"{test_df['product_id'].nunique()}"
)

print("\nDate range")

print(
    f"Train: "
    f"{train_df['last_purchase_date'].min().date()}"
    f" -> "
    f"{train_df['last_purchase_date'].max().date()}"
)

print(
    f"Test:  "
    f"{test_df['last_purchase_date'].min().date()}"
    f" -> "
    f"{test_df['last_purchase_date'].max().date()}"
)


# ============================================================
# SAVE
# ============================================================

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

print("\nFiles saved")
print("-" * 70)
print(TRAIN_PATH)
print(TEST_PATH)

print("\nNew-item split completed successfully.")