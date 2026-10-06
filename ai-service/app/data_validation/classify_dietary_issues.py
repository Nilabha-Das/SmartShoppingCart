import pandas as pd


REPORT_PATH = "/validation/dietary_validation_report.csv"
OUTPUT_PATH = "/validation/dietary_corrections.csv"


# Products where the product description/name confirms that the
# dietary flags should NOT be automatically changed.
MANUAL_REVIEW_IDS = {
    "P006322",  # Hara Bhara Kebab
}


def classify(row):

    product_id = row["product_id"]
    issues = str(row["issues"])
    confidence = row["confidence"]

    # ---------------------------------------------------------
    # 1. Explicit Non-Veg contradiction
    # ---------------------------------------------------------

    if (
        "Non-Veg product_type but vegetarian=True" in issues
        and product_id not in MANUAL_REVIEW_IDS
    ):
        return {
            "decision": "AUTO_FIX_DIETARY",
            "new_vegetarian": False,
            "new_vegan": False,
            "reason": "Non-Veg product type conflicts with vegetarian/vegan flags."
        }

    # ---------------------------------------------------------
    # 2. Hara Bhara Kebab
    # ---------------------------------------------------------

    if product_id in MANUAL_REVIEW_IDS:
        return {
            "decision": "REVIEW_PRODUCT_TYPE",
            "new_vegetarian": row["vegetarian"],
            "new_vegan": row["vegan"],
            "reason": (
                "Dietary flags are consistent with the product description, "
                "but product_type says Non-Veg."
            )
        }

    # ---------------------------------------------------------
    # 3. Veg product type + vegetarian=False
    # ---------------------------------------------------------

    if "Veg product_type but vegetarian=False" in issues:
        return {
            "decision": "REVIEW_DIETARY_METADATA",
            "new_vegetarian": row["vegetarian"],
            "new_vegan": row["vegan"],
            "reason": (
                "Veg product type conflicts with vegetarian=False. "
                "Requires product-level review."
            )
        }

    # ---------------------------------------------------------
    # 4. Product-name animal keyword
    # ---------------------------------------------------------

    if "Animal-product term in product name" in issues:
        return {
            "decision": "REVIEW_NAME_SIGNAL",
            "new_vegetarian": row["vegetarian"],
            "new_vegan": row["vegan"],
            "reason": (
                "Animal-product term appears in product name, "
                "but this alone is insufficient to modify dietary flags."
            )
        }

    # ---------------------------------------------------------
    # 5. Fallback
    # ---------------------------------------------------------

    return {
        "decision": "REVIEW",
        "new_vegetarian": row["vegetarian"],
        "new_vegan": row["vegan"],
        "reason": "Requires manual review."
    }


def main():

    print("Loading validation report...")

    report = pd.read_csv(REPORT_PATH)

    classified = []

    for _, row in report.iterrows():

        result = classify(row)

        classified.append({
            "product_id": row["product_id"],
            "product_name": row["product_name"],
            "product_type": row["product_type"],
            "old_vegetarian": row["vegetarian"],
            "old_vegan": row["vegan"],
            "confidence": row["confidence"],
            "issues": row["issues"],
            **result
        })

    output = pd.DataFrame(classified)

    output.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(f"Records classified: {len(output)}")
    print()
    print("Decision counts:")
    print(output["decision"].value_counts())
    print()
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()