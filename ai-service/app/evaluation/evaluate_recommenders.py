import os
import math
import numpy as np
import pandas as pd

from app.recommender.collaborative import CollaborativeRecommender
from app.recommender.content_based import ContentBasedRecommender
from app.recommender.hybrid import HybridRecommender


# ============================================================
# PATHS
# ============================================================

TRAIN_PATH = "/validation/evaluation/new_item_train_interactions.csv"
TEST_PATH = "/validation/evaluation/new_item_test_interactions.csv"

OUTPUT_DIR = "/validation/evaluation"

RESULTS_PATH = os.path.join(
    OUTPUT_DIR,
    "recommendation_evaluation_results.csv"
)


# ============================================================
# METRICS
# ============================================================

def precision_at_k(recommendations, actual_product, k):
    top_k = recommendations[:k]

    if not top_k:
        return 0.0

    return 1.0 / k if actual_product in top_k else 0.0


def recall_at_k(recommendations, actual_product, k):
    return 1.0 if actual_product in recommendations[:k] else 0.0


def hit_rate_at_k(recommendations, actual_product, k):
    return 1.0 if actual_product in recommendations[:k] else 0.0


def ndcg_at_k(recommendations, actual_product, k):
    top_k = recommendations[:k]

    for rank, product_id in enumerate(top_k, start=1):
        if product_id == actual_product:
            return 1.0 / math.log2(rank + 1)

    return 0.0


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("RECOMMENDATION SYSTEM EVALUATION")
print("=" * 70)

print("\nLoading train data...")
train_df = pd.read_csv(TRAIN_PATH)

print("Loading test data...")
test_df = pd.read_csv(TEST_PATH)

print(f"Train interactions: {len(train_df)}")
print(f"Test interactions:  {len(test_df)}")


# ============================================================
# TRAIN DATA
# ============================================================

# Sort chronologically so the latest training product
# can be used for the content-based baseline.

train_df["last_purchase_date"] = pd.to_datetime(
    train_df["last_purchase_date"],
    format="mixed"
)

test_df["last_purchase_date"] = pd.to_datetime(
    test_df["last_purchase_date"],
    format="mixed"
)

train_df = train_df.sort_values(
    ["customer_id", "last_purchase_date"]
)

test_df = test_df.sort_values(
    ["customer_id", "last_purchase_date"]
)


# ============================================================
# MODELS
# ============================================================

print("\n" + "=" * 70)
print("INITIALIZING MODELS")
print("=" * 70)

print("\n1. Collaborative model")
collaborative = CollaborativeRecommender(
    interactions_path=TRAIN_PATH
)

print("\n2. Content model")
content = ContentBasedRecommender()

print("\n3. Hybrid model")
hybrid = HybridRecommender(
    content_recommender=content,
    collaborative_recommender=collaborative
)


# ============================================================
# POPULARITY MODEL
# ============================================================

print("\n4. Building popularity baseline")

popularity = (
    train_df
    .groupby("product_id")["total_quantity"]
    .sum()
    .sort_values(ascending=False)
)

popular_products = popularity.index.tolist()

print(
    f"Popularity products available: "
    f"{len(popular_products)}"
)


# ============================================================
# TRAINING HISTORY
# ============================================================

customer_history = (
    train_df
    .groupby("customer_id")
    .agg(
        last_product=(
            "product_id",
            "last"
        )
    )
)


# ============================================================
# EVALUATION STORAGE
# ============================================================

records = []

total_customers = len(test_df)

print("\n" + "=" * 70)
print("STARTING EVALUATION")
print("=" * 70)

print(
    f"\nCustomers to evaluate: {total_customers}"
)


# ============================================================
# EVALUATION LOOP
# ============================================================

for counter, row in enumerate(
    test_df.itertuples(index=False),
    start=1
):

    customer_id = row.customer_id
    actual_product = row.product_id

    # --------------------------------------------------------
    # Progress
    # --------------------------------------------------------

    if counter % 100 == 0 or counter == 1:
        print(
            f"Evaluating customer "
            f"{counter}/{total_customers}",
            flush=True
        )

    # ========================================================
    # POPULARITY
    # ========================================================

    purchased_products = set(
        train_df.loc[
            train_df["customer_id"] == customer_id,
            "product_id"
        ]
    )

    popularity_recommendations = [
        product
        for product in popular_products
        if product not in purchased_products
    ][:10]

    # ========================================================
    # COLLABORATIVE
    # ========================================================

    collaborative_df = collaborative.recommend(
        customer_id,
        n_candidates=10
    )

    if collaborative_df.empty:
        collaborative_recommendations = []
    else:
        collaborative_recommendations = (
            collaborative_df["product_id"]
            .tolist()
        )

    # ========================================================
    # CONTENT-BASED
    # ========================================================

    content_recommendations = []

    if customer_id in customer_history.index:

        last_product = customer_history.loc[
            customer_id,
            "last_product"
        ]

        content_df = content.recommend_similar_products(
            last_product,
            n=10
        )

        if not content_df.empty:
            content_recommendations = (
                content_df["product_id"]
                .tolist()
            )

    # ========================================================
    # HYBRID
    # ========================================================

    hybrid_df = hybrid.recommend(
        customer_id,
        n=10
    )

    if hybrid_df.empty:
        hybrid_recommendations = []
    else:
        hybrid_recommendations = (
            hybrid_df["product_id"]
            .tolist()
        )

    # ========================================================
    # STORE METRICS
    # ========================================================

    for model_name, recommendations in [
        (
            "Popularity",
            popularity_recommendations
        ),
        (
            "Content-Based",
            content_recommendations
        ),
        (
            "Collaborative",
            collaborative_recommendations
        ),
        (
            "Hybrid",
            hybrid_recommendations
        )
    ]:

        records.append({
            "customer_id": customer_id,
            "actual_product": actual_product,
            "model": model_name,

            "precision@5": precision_at_k(
                recommendations,
                actual_product,
                5
            ),

            "recall@5": recall_at_k(
                recommendations,
                actual_product,
                5
            ),

            "ndcg@5": ndcg_at_k(
                recommendations,
                actual_product,
                5
            ),

            "hit_rate@5": hit_rate_at_k(
                recommendations,
                actual_product,
                5
            ),

            "precision@10": precision_at_k(
                recommendations,
                actual_product,
                10
            ),

            "recall@10": recall_at_k(
                recommendations,
                actual_product,
                10
            ),

            "ndcg@10": ndcg_at_k(
                recommendations,
                actual_product,
                10
            ),

            "hit_rate@10": hit_rate_at_k(
                recommendations,
                actual_product,
                10
            )
        })


# ============================================================
# CONVERT RESULTS
# ============================================================

results_df = pd.DataFrame(records)


# ============================================================
# AGGREGATE RESULTS
# ============================================================

summary = (
    results_df
    .groupby("model")
    [
        [
            "precision@5",
            "recall@5",
            "ndcg@5",
            "hit_rate@5",
            "precision@10",
            "recall@10",
            "ndcg@10",
            "hit_rate@10"
        ]
    ]
    .mean()
    .reset_index()
)


# ============================================================
# SAVE RESULTS
# ============================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

results_df.to_csv(
    RESULTS_PATH,
    index=False
)

summary_path = os.path.join(
    OUTPUT_DIR,
    "recommendation_evaluation_summary.csv"
)

summary.to_csv(
    summary_path,
    index=False
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 70)
print("EVALUATION COMPLETE")
print("=" * 70)

print("\nRESULTS:")
print(
    summary.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)

print("\nFiles saved:")
print(RESULTS_PATH)
print(summary_path)

print("\n" + "=" * 70)