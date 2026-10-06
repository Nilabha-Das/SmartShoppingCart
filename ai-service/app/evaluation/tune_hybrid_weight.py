import hashlib
import os
import random

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

from app.recommender.collaborative import CollaborativeRecommender
from app.recommender.content_based import ContentBasedRecommender


# ============================================================
# CONFIGURATION
# ============================================================

INNER_TRAIN_PATH = (
    "/validation/evaluation/"
    "hybrid_inner_train_interactions.csv"
)

VALIDATION_PATH = (
    "/validation/evaluation/"
    "hybrid_validation_interactions.csv"
)

OUTPUT_PATH = (
    "/validation/evaluation/"
    "hybrid_weight_tuning_results.csv"
)

NEGATIVE_SAMPLES = 100
RANDOM_SEED = 42

# Collaborative weight.
# Content weight = 1 - collaborative weight.
WEIGHTS = [
    round(x, 1)
    for x in np.arange(0.0, 1.01, 0.1)
]

TOP_KS = [5, 10]


# ============================================================
# DETERMINISTIC TIE BREAKING
# ============================================================

def tie_break_value(customer_id, product_id):
    """
    Deterministic tie-breaking.

    This prevents the positive target from receiving an
    artificial advantage when several candidates have exactly
    the same model score.
    """

    key = f"{customer_id}|{product_id}".encode("utf-8")

    digest = hashlib.md5(key).hexdigest()

    return int(digest, 16)


def rank_candidates(
    candidates,
    scores,
    customer_id
):
    """
    Rank candidates by:

        1. descending model score
        2. deterministic hash tie-breaker

    Returns product IDs in ranked order.
    """

    ranked = sorted(
        candidates,
        key=lambda product_id: (
            -float(scores.get(product_id, 0.0)),
            tie_break_value(customer_id, product_id)
        )
    )

    return ranked


# ============================================================
# METRICS
# ============================================================

def hit_at_k(ranked, target, k):
    return 1.0 if target in ranked[:k] else 0.0


def recall_at_k(ranked, target, k):
    """
    Single-positive evaluation.

    With exactly one relevant item:

        Recall@K = Hit@K
    """

    return hit_at_k(ranked, target, k)


def precision_at_k(ranked, target, k):
    """
    Single-positive evaluation.

    There is only one relevant item.
    """

    return hit_at_k(ranked, target, k) / k


def ndcg_at_k(ranked, target, k):

    top_k = ranked[:k]

    if target not in top_k:
        return 0.0

    rank = top_k.index(target) + 1

    return 1.0 / np.log2(rank + 1)


# ============================================================
# NORMALIZATION
# ============================================================

def minmax_normalize(scores):

    if not scores:
        return {}

    product_ids = list(scores.keys())

    values = np.array(
        [
            float(scores[p])
            for p in product_ids
        ],
        dtype=float
    )

    # All scores equal.
    if np.max(values) == np.min(values):
        normalized = np.zeros_like(values)

    else:
        scaler = MinMaxScaler()

        normalized = scaler.fit_transform(
            values.reshape(-1, 1)
        ).flatten()

    return {
        product_id: float(value)
        for product_id, value in zip(
            product_ids,
            normalized
        )
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("HYBRID WEIGHT TUNING")
    print("=" * 70)

    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    train = pd.read_csv(INNER_TRAIN_PATH)
    validation = pd.read_csv(VALIDATION_PATH)

    train["customer_id"] = (
        train["customer_id"].astype(str)
    )

    train["product_id"] = (
        train["product_id"].astype(str)
    )

    validation["customer_id"] = (
        validation["customer_id"].astype(str)
    )

    validation["product_id"] = (
        validation["product_id"].astype(str)
    )

    print(
        f"Inner train interactions : {len(train)}"
    )

    print(
        f"Validation interactions  : {len(validation)}"
    )

    # --------------------------------------------------------
    # Customer histories
    # --------------------------------------------------------

    histories = (
        train.groupby("customer_id")["product_id"]
        .apply(list)
        .to_dict()
    )

    # --------------------------------------------------------
    # Training product universe
    # --------------------------------------------------------

    train_products = set(
        train["product_id"].unique()
    )

    print(
        f"Training products        : "
        f"{len(train_products)}"
    )

    # --------------------------------------------------------
    # Validation targets
    # --------------------------------------------------------

    validation = validation[
        validation["product_id"].isin(train_products)
    ].copy()

    print(
        f"Warm-start validation    : "
        f"{len(validation)}"
    )

    # --------------------------------------------------------
    # Initialize models
    # --------------------------------------------------------

    collaborative = CollaborativeRecommender(
        interactions_path=INNER_TRAIN_PATH
    )

    content = ContentBasedRecommender()

    print("Models initialized.")

    # --------------------------------------------------------
    # Prepare content matrix
    # --------------------------------------------------------

    content_products = content.content_products

    content_product_ids = (
        content_products["product_id"]
        .astype(str)
        .tolist()
    )

    content_product_to_index = {
        product_id: index
        for index, product_id in enumerate(
            content_product_ids
        )
    }

    tfidf_matrix = content.tfidf_matrix

    # --------------------------------------------------------
    # Popularity
    # --------------------------------------------------------

    popularity_series = (
        train.groupby("product_id")["total_quantity"]
        .sum()
        .sort_values(ascending=False)
    )

    popularity_scores = (
        popularity_series.to_dict()
    )

    # --------------------------------------------------------
    # Storage for each model
    # --------------------------------------------------------

    results = []

    # --------------------------------------------------------
    # Evaluate every hybrid weight
    # --------------------------------------------------------

    for alpha in WEIGHTS:

        beta = round(1.0 - alpha, 1)

        print()
        print("-" * 70)
        print(
            f"Testing CF weight = {alpha:.1f} | "
            f"Content weight = {beta:.1f}"
        )
        print("-" * 70)

        metrics = {
            "hit@5": 0.0,
            "recall@5": 0.0,
            "ndcg@5": 0.0,
            "precision@5": 0.0,
            "hit@10": 0.0,
            "recall@10": 0.0,
            "ndcg@10": 0.0,
            "precision@10": 0.0,
        }

        evaluated = 0

        # ----------------------------------------------------
        # Customer-level evaluation
        # ----------------------------------------------------

        for row_index, row in enumerate(
            validation.itertuples(index=False),
            start=1
        ):

            customer_id = str(row.customer_id)
            target = str(row.product_id)

            history = histories.get(
                customer_id,
                []
            )

            history_set = set(history)

            # Target must not already be in history.
            if target in history_set:
                continue

            # ------------------------------------------------
            # Negative sampling
            # ------------------------------------------------

            eligible_negatives = (
                train_products
                - history_set
                - {target}
            )

            if len(eligible_negatives) < NEGATIVE_SAMPLES:
                continue

            negatives = random.sample(
                list(eligible_negatives),
                NEGATIVE_SAMPLES
            )

            candidates = [
                target
            ] + negatives

            # ------------------------------------------------
            # Collaborative scores
            # ------------------------------------------------

            collaborative_scores = (
                collaborative.score_candidates(
                    customer_id,
                    candidates,
                    n_similar=20
                )
            )

            collaborative_scores = {
                str(product_id): float(score)
                for product_id, score
                in collaborative_scores.items()
            }

            # Make sure every candidate exists.
            collaborative_scores = {
                product_id:
                    collaborative_scores.get(
                        product_id,
                        0.0
                    )
                for product_id in candidates
            }

            # ------------------------------------------------
            # Content scores
            # ------------------------------------------------

            content_scores = {}

            history_indices = [
                content_product_to_index[product_id]
                for product_id in history
                if product_id
                in content_product_to_index
            ]

            if history_indices:

                history_matrix = (
                    tfidf_matrix[history_indices]
                )

                for candidate in candidates:

                    candidate_index = (
                        content_product_to_index.get(
                            candidate
                        )
                    )

                    if candidate_index is None:
                        content_scores[candidate] = 0.0
                        continue

                    candidate_vector = (
                        tfidf_matrix[
                            candidate_index
                        ]
                    )

                    similarities = cosine_similarity(
                        candidate_vector,
                        history_matrix
                    ).flatten()

                    content_scores[candidate] = (
                        float(np.max(similarities))
                        if len(similarities)
                        else 0.0
                    )

            else:

                content_scores = {
                    candidate: 0.0
                    for candidate in candidates
                }

            # ------------------------------------------------
            # Normalize each signal
            # ------------------------------------------------

            cf_normalized = minmax_normalize(
                collaborative_scores
            )

            content_normalized = minmax_normalize(
                content_scores
            )

            # ------------------------------------------------
            # Hybrid score
            # ------------------------------------------------

            hybrid_scores = {}

            for candidate in candidates:

                hybrid_scores[candidate] = (
                    alpha
                    * cf_normalized.get(
                        candidate,
                        0.0
                    )
                    +
                    beta
                    * content_normalized.get(
                        candidate,
                        0.0
                    )
                )

            # ------------------------------------------------
            # Rank
            # ------------------------------------------------

            ranked = rank_candidates(
                candidates,
                hybrid_scores,
                customer_id
            )

            # ------------------------------------------------
            # Metrics
            # ------------------------------------------------

            for k in TOP_KS:

                metrics[f"hit@{k}"] += (
                    hit_at_k(
                        ranked,
                        target,
                        k
                    )
                )

                metrics[f"recall@{k}"] += (
                    recall_at_k(
                        ranked,
                        target,
                        k
                    )
                )

                metrics[f"ndcg@{k}"] += (
                    ndcg_at_k(
                        ranked,
                        target,
                        k
                    )
                )

                metrics[f"precision@{k}"] += (
                    precision_at_k(
                        ranked,
                        target,
                        k
                    )
                )

            evaluated += 1

            if row_index % 500 == 0:

                print(
                    f"Processed validation rows: "
                    f"{row_index}"
                )

        # ----------------------------------------------------
        # Average metrics
        # ----------------------------------------------------

        if evaluated == 0:
            raise RuntimeError(
                "No validation customers were evaluated."
            )

        for metric in metrics:
            metrics[metric] /= evaluated

        result = {
            "cf_weight": alpha,
            "content_weight": beta,
            "customers": evaluated,
            **metrics
        }

        results.append(result)

        print()
        print(
            f"CF weight {alpha:.1f}: "
            f"Hit@5={metrics['hit@5']:.6f}, "
            f"NDCG@5={metrics['ndcg@5']:.6f}, "
            f"Hit@10={metrics['hit@10']:.6f}, "
            f"NDCG@10={metrics['ndcg@10']:.6f}"
        )

    # ========================================================
    # RESULTS
    # ========================================================

    results_df = pd.DataFrame(results)

    results_df = results_df.sort_values(
        [
            "ndcg@5",
            "hit@5",
            "ndcg@10"
        ],
        ascending=False
    ).reset_index(drop=True)

    results_df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    print()
    print("=" * 70)
    print("WEIGHT TUNING RESULTS")
    print("=" * 70)

    print(
        results_df.to_string(
            index=False
        )
    )

    best = results_df.iloc[0]

    print()
    print("=" * 70)
    print("BEST HYBRID WEIGHT")
    print("=" * 70)

    print(
        f"CF weight      : "
        f"{best['cf_weight']:.1f}"
    )

    print(
        f"Content weight : "
        f"{best['content_weight']:.1f}"
    )

    print(
        f"NDCG@5         : "
        f"{best['ndcg@5']:.6f}"
    )

    print(
        f"Hit@5          : "
        f"{best['hit@5']:.6f}"
    )

    print(
        f"NDCG@10        : "
        f"{best['ndcg@10']:.6f}"
    )

    print(
        f"Hit@10         : "
        f"{best['hit@10']:.6f}"
    )

    print()
    print(
        f"Saved: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
    