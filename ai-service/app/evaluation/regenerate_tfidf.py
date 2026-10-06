import os
import joblib
import pandas as pd

from scipy.sparse import save_npz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn import __version__ as sklearn_version


INPUT_PATH = "/validation/master_products_clean.csv"

OUTPUT_MATRIX = "/validation/tfidf_matrix_final.npz"
OUTPUT_VECTORIZER = "/validation/tfidf_vectorizer_final.pkl"
OUTPUT_PRODUCTS = "/validation/content_products_final.csv"


def main():

    print("=" * 70)
    print("REGENERATING FINAL TF-IDF CONTENT MODEL")
    print("=" * 70)

    print(f"Input: {INPUT_PATH}")
    print(f"Scikit-learn: {sklearn_version}")

    df = pd.read_csv(INPUT_PATH)

    print(f"Products loaded: {len(df):,}")

    required_columns = [
        "product_id",
        "product_name",
        "category",
        "subcategory",
        "brand",
        "product_type",
        "description",
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    # Fill missing textual fields.
    for col in required_columns[1:]:
        df[col] = df[col].fillna("").astype(str)

    # IMPORTANT:
    # Product name is now included.
    df["combined_features"] = (
        df["product_name"] + " "
        + df["category"] + " "
        + df["subcategory"] + " "
        + df["brand"] + " "
        + df["product_type"] + " "
        + df["description"]
    )

    print("\nFeature representation:")
    print(
        "product_name + category + subcategory + "
        "brand + product_type + description"
    )

    print("\nFitting TF-IDF...")

    tfidf = TfidfVectorizer(
        stop_words="english"
    )

    tfidf_matrix = tfidf.fit_transform(
        df["combined_features"]
    )

    print(
        f"TF-IDF matrix: {tfidf_matrix.shape}"
    )

    print(
        f"Vocabulary size: {len(tfidf.vocabulary_):,}"
    )

    print("\nSaving artifacts...")

    save_npz(
        OUTPUT_MATRIX,
        tfidf_matrix
    )

    joblib.dump(
        tfidf,
        OUTPUT_VECTORIZER
    )

    df.to_csv(
        OUTPUT_PRODUCTS,
        index=False
    )

    print("\nDone.")
    print(f"Matrix:     {OUTPUT_MATRIX}")
    print(f"Vectorizer: {OUTPUT_VECTORIZER}")
    print(f"Products:   {OUTPUT_PRODUCTS}")


if __name__ == "__main__":
    main()