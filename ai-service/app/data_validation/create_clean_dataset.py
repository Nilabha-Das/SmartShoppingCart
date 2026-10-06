import pandas as pd


INPUT_PATH = "/app/data/phase1/master_products.csv"
CORRECTIONS_PATH = "/validation/dietary_corrections.csv"
OUTPUT_PATH = "/validation/master_products_clean.csv"


def main():

    print("Loading original dataset...")

    df = pd.read_csv(INPUT_PATH)

    print(f"Original products: {len(df)}")

    corrections = pd.read_csv(CORRECTIONS_PATH)

    auto_fixes = corrections[
        corrections["decision"] == "AUTO_FIX_DIETARY"
    ]

    print(f"Automatic corrections: {len(auto_fixes)}")

    # Apply ONLY approved automatic dietary corrections
    for _, correction in auto_fixes.iterrows():

        product_id = correction["product_id"]

        mask = df["product_id"] == product_id

        df.loc[mask, "vegetarian"] = correction["new_vegetarian"]
        df.loc[mask, "vegan"] = correction["new_vegan"]

    df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print(f"Clean dataset saved to: {OUTPUT_PATH}")
    print(f"Clean products: {len(df)}")


if __name__ == "__main__":
    main()