import pandas as pd


TRAIN_PATH = (
    "/validation/evaluation/new_item_train_interactions.csv"
)

TEST_PATH = (
    "/validation/evaluation/new_item_test_interactions.csv"
)

CONTENT_PATH = (
    "/app/models/content_based/content_products.csv"
)


print("=" * 70)
print("TEST TARGET DIAGNOSTICS")
print("=" * 70)


# ------------------------------------------------------------
# Load
# ------------------------------------------------------------

train = pd.read_csv(TRAIN_PATH)
test = pd.read_csv(TEST_PATH)
content = pd.read_csv(CONTENT_PATH)


print(f"\nTrain interactions: {len(train)}")
print(f"Test interactions:  {len(test)}")
print(f"Content products:   {len(content)}")


# ------------------------------------------------------------
# Product sets
# ------------------------------------------------------------

train_products = set(
    train["product_id"]
)

test_products = set(
    test["product_id"]
)

content_products = set(
    content["product_id"]
)


# ------------------------------------------------------------
# Test products available to CF
# ------------------------------------------------------------

cf_eligible = (
    test["product_id"]
    .isin(train_products)
)

content_eligible = (
    test["product_id"]
    .isin(content_products)
)


print("\n" + "=" * 70)
print("TARGET AVAILABILITY")
print("=" * 70)


print(
    f"\nTest targets total: "
    f"{len(test)}"
)

print(
    f"Targets seen somewhere in training: "
    f"{cf_eligible.sum()}"
)

print(
    f"Targets NOT seen in training: "
    f"{(~cf_eligible).sum()}"
)

print(
    f"Targets present in content catalog: "
    f"{content_eligible.sum()}"
)

print(
    f"Targets missing from content catalog: "
    f"{(~content_eligible).sum()}"
)


# ------------------------------------------------------------
# Both
# ------------------------------------------------------------

both = (
    cf_eligible
    & content_eligible
)

print(
    f"\nTargets available to BOTH CF and Content: "
    f"{both.sum()}"
)


# ------------------------------------------------------------
# Per-customer diagnostics
# ------------------------------------------------------------

test["cf_available"] = cf_eligible
test["content_available"] = content_eligible
test["both_available"] = both


print("\n" + "=" * 70)
print("CUSTOMER-LEVEL AVAILABILITY")
print("=" * 70)


print(
    f"\nCustomers: "
    f"{test['customer_id'].nunique()}"
)

print(
    f"Customers with CF-available target: "
    f"{test.groupby('customer_id')['cf_available'].max().sum()}"
)

print(
    f"Customers with Content-available target: "
    f"{test.groupby('customer_id')['content_available'].max().sum()}"
)

print(
    f"Customers with target available to both: "
    f"{test.groupby('customer_id')['both_available'].max().sum()}"
)


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

output_path = (
    "/validation/evaluation/"
    "test_target_diagnostics.csv"
)

test.to_csv(
    output_path,
    index=False
)

print("\nSaved:")
print(output_path)

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)