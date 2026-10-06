import random
import numpy as np
import pandas as pd

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

from app.recommender.collaborative import CollaborativeRecommender
from app.recommender.content_based import ContentBasedRecommender


TRAIN_PATH = (
    "/validation/evaluation/"
    "new_item_train_interactions.csv"
)

TEST_PATH = (
    "/validation/evaluation/"
    "new_item_test_interactions.csv"
)

NEGATIVE_SAMPLES = 100
RANDOM_SEED = 42


def normalize(values):

    values = np.asarray(values, dtype=float)

    if values.max() == values.min():
        return np.zeros_like(values)

    return MinMaxScaler().fit_transform(
        values.reshape(-1, 1)
    ).ravel()


def main():

    random.seed(RANDOM_SEED)

    train = pd.read_csv(TRAIN_PATH)
    test = pd.read_csv(TEST_PATH)

    train["customer_id"] = (
        train["customer_id"].astype(str)
    )

    train["product_id"] = (
        train["product_id"].astype(str)
    )

    test["customer_id"] = (
        test["customer_id"].astype(str)
    )

    test["product_id"] = (
        test["product_id"].astype(str)
    )

    histories = (
        train.groupby("customer_id")["product_id"]
        .apply(set)
        .to_dict()
    )

    train_products = set(
        train["product_id"]
    )

    eligible = test[
        test["product_id"].isin(train_products)
    ]

    collaborative = CollaborativeRecommender(
        interactions_path=TRAIN_PATH
    )

    content = ContentBasedRecommender()

    for _, row in eligible.iterrows():

        customer_id = row["customer_id"]
        target = row["product_id"]

        history = histories.get(
            customer_id,
            set()
        )

        if target in history:
            continue

        negatives = list(
            train_products
            - history
            - {target}
        )

        negatives = random.sample(
            negatives,
            NEGATIVE_SAMPLES
        )

        candidates = [target] + negatives

        # ---------------------------------------------------------
        # Collaborative
        # ---------------------------------------------------------

        collab_scores = (
            collaborative.score_candidates(
                customer_id,
                candidates
            )
        )

        # ---------------------------------------------------------
        # Content
        # ---------------------------------------------------------

        content_scores = {
            product: 0.0
            for product in candidates
        }

        history_indices = [
            content.product_to_index[p]
            for p in history
            if p in content.product_to_index
        ]

        candidate_products = [
            p for p in candidates
            if p in content.product_to_index
        ]

        candidate_indices = [
            content.product_to_index[p]
            for p in candidate_products
        ]

        if history_indices and candidate_indices:

            similarities = cosine_similarity(
                content.tfidf_matrix[candidate_indices],
                content.tfidf_matrix[history_indices]
            )

            max_scores = similarities.max(
                axis=1
            )

            for product, score in zip(
                candidate_products,
                max_scores
            ):
                content_scores[product] = float(
                    score
                )

        # ---------------------------------------------------------
        # Hybrid
        # ---------------------------------------------------------

        collab_array = np.array([
            collab_scores[p]
            for p in candidates
        ])

        content_array = np.array([
            content_scores[p]
            for p in candidates
        ])

        collab_norm = normalize(
            collab_array
        )

        content_norm = normalize(
            content_array
        )

        hybrid_scores = (
            0.6 * collab_norm
            +
            0.4 * content_norm
        )

        results = []

        for i, product in enumerate(candidates):

            results.append({
                "product_id": product,
                "is_target": product == target,
                "collab": collab_scores[product],
                "collab_norm": collab_norm[i],
                "content": content_scores[product],
                "content_norm": content_norm[i],
                "hybrid": hybrid_scores[i],
            })

        df = pd.DataFrame(results)

        df = df.sort_values(
            "hybrid",
            ascending=False
        ).reset_index(drop=True)

        target_row = df[
            df["is_target"]
        ].iloc[0]

        target_rank = (
            df.index[
                df["is_target"]
            ][0]
            + 1
        )

        print()
        print("=" * 80)
        print(f"CUSTOMER : {customer_id}")
        print(f"TARGET   : {target}")
        print(f"TARGET HYBRID RANK : {target_rank}")
        print("=" * 80)

        print()
        print("TARGET SCORE")
        print(target_row.to_string())

        print()
        print("TOP 10 HYBRID")
        print(
            df.head(10).to_string(
                index=False
            )
        )

        print()
        print("TOP 10 COLLABORATIVE")

        collab_df = df.sort_values(
            "collab",
            ascending=False
        )

        print(
            collab_df.head(10).to_string(
                index=False
            )
        )

        print()
        print("TOP 10 CONTENT")

        content_df = df.sort_values(
            "content",
            ascending=False
        )

        print(
            content_df.head(10).to_string(
                index=False
            )
        )

        break


if __name__ == "__main__":
    main()