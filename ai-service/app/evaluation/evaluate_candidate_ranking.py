import random
import hashlib

import numpy as np
import pandas as pd

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

from app.recommender.collaborative import CollaborativeRecommender
from app.recommender.content_based import ContentBasedRecommender


# ================================================================
# CONFIGURATION
# ================================================================

TRAIN_PATH = (
    "/validation/evaluation/"
    "new_item_train_interactions.csv"
)

TEST_PATH = (
    "/validation/evaluation/"
    "new_item_test_interactions.csv"
)

NEGATIVE_SAMPLES = 100

TOP_KS = [5, 10]

RANDOM_SEED = 42


# ================================================================
# REPRODUCIBLE TIE BREAKING
# ================================================================

def tie_break_value(
    customer_id,
    product_id
):
    """
    Generate a deterministic pseudo-random value for
    breaking score ties.

    This is important because many candidate products
    can have exactly the same score, especially zero.

    The positive target must NOT receive an advantage
    simply because it appeared first in the candidate list.
    """

    value = (
        f"{RANDOM_SEED}|"
        f"{customer_id}|"
        f"{product_id}"
    )

    digest = hashlib.md5(
        value.encode("utf-8")
    ).hexdigest()

    return int(digest, 16)


# ================================================================
# RANKING FUNCTION
# ================================================================

def rank_candidates(
    candidates,
    scores,
    customer_id
):
    """
    Rank candidates by model score.

    Primary key:
        model score

    Secondary key:
        deterministic tie breaker

    This ensures that products with equal scores are
    ranked fairly and reproducibly.
    """

    return sorted(
        candidates,
        key=lambda product_id: (
            float(
                scores.get(
                    product_id,
                    0.0
                )
            ),
            tie_break_value(
                customer_id,
                product_id
            )
        ),
        reverse=True
    )


# ================================================================
# MIN-MAX NORMALIZATION
# ================================================================

def minmax_normalize(values):
    """
    Normalize scores to [0, 1].

    If all scores are identical, return zeros.

    This prevents MinMaxScaler from creating an
    artificial difference where none exists.
    """

    values = np.asarray(
        values,
        dtype=float
    )

    if len(values) == 0:
        return values

    minimum = np.min(values)
    maximum = np.max(values)

    if maximum == minimum:
        return np.zeros_like(values)

    return (
        MinMaxScaler()
        .fit_transform(
            values.reshape(-1, 1)
        )
        .ravel()
    )


# ================================================================
# NDCG
# ================================================================

def ndcg_for_single_positive(
    rank,
    k
):
    """
    Calculate NDCG for a single positive item.

    If the positive item is ranked at position r:

        NDCG = 1 / log2(r + 1)

    when r <= k.

    Otherwise NDCG = 0.
    """

    if rank is None:
        return 0.0

    if rank > k:
        return 0.0

    return 1.0 / np.log2(
        rank + 1
    )


# ================================================================
# MAIN EVALUATION
# ================================================================

def main():

    random.seed(
        RANDOM_SEED
    )

    np.random.seed(
        RANDOM_SEED
    )

    print("=" * 70)
    print(
        "CANDIDATE-BASED RECOMMENDATION EVALUATION"
    )
    print("=" * 70)

    # ------------------------------------------------------------
    # Load train/test
    # ------------------------------------------------------------

    train = pd.read_csv(
        TRAIN_PATH
    )

    test = pd.read_csv(
        TEST_PATH
    )

    # ------------------------------------------------------------
    # Normalize IDs
    # ------------------------------------------------------------

    train["customer_id"] = (
        train["customer_id"]
        .astype(str)
    )

    train["product_id"] = (
        train["product_id"]
        .astype(str)
    )

    test["customer_id"] = (
        test["customer_id"]
        .astype(str)
    )

    test["product_id"] = (
        test["product_id"]
        .astype(str)
    )

    print(
        f"Train interactions : "
        f"{len(train)}"
    )

    print(
        f"Test interactions  : "
        f"{len(test)}"
    )

    # ------------------------------------------------------------
    # Build customer histories
    # ------------------------------------------------------------

    histories = (
        train
        .groupby("customer_id")["product_id"]
        .apply(set)
        .to_dict()
    )

    # ------------------------------------------------------------
    # Products available to collaborative filtering
    # ------------------------------------------------------------

    train_products = set(
        train["product_id"]
    )

    # ------------------------------------------------------------
    # Warm-start test targets
    #
    # Target must have appeared somewhere in training so that
    # Collaborative Filtering can actually score it.
    # ------------------------------------------------------------

    eligible_test = test[
        test["product_id"]
        .isin(train_products)
    ].copy()

    print(
        f"Eligible warm-start targets: "
        f"{len(eligible_test)}"
    )

    # ------------------------------------------------------------
    # Initialize Collaborative model
    #
    # IMPORTANT:
    # Train ONLY on the training split.
    # ------------------------------------------------------------

    collaborative = (
        CollaborativeRecommender(
            interactions_path=TRAIN_PATH
        )
    )

    # ------------------------------------------------------------
    # Initialize Content model
    # ------------------------------------------------------------

    content = (
        ContentBasedRecommender()
    )

    print(
        "Models initialized."
    )

    # ------------------------------------------------------------
    # Popularity baseline
    #
    # Popularity is calculated ONLY from training data.
    # ------------------------------------------------------------

    popularity = (
        train
        .groupby("product_id")[
            "total_quantity"
        ]
        .sum()
        .sort_values(
            ascending=False
        )
        .to_dict()
    )

    # ------------------------------------------------------------
    # Result containers
    # ------------------------------------------------------------

    model_names = [
        "Popularity",
        "Collaborative",
        "Content-Based",
        "Hybrid"
    ]

    model_hits = {
        model: {
            5: [],
            10: []
        }
        for model in model_names
    }

    model_ndcg = {
        model: {
            5: [],
            10: []
        }
        for model in model_names
    }

    # ------------------------------------------------------------
    # Evaluation counters
    # ------------------------------------------------------------

    customers_evaluated = 0

    customers_skipped = 0

    # ------------------------------------------------------------
    # Evaluate each customer
    # ------------------------------------------------------------

    for row_number, (_, row) in enumerate(
        eligible_test.iterrows(),
        start=1
    ):

        customer_id = (
            row["customer_id"]
        )

        target = (
            row["product_id"]
        )

        # --------------------------------------------------------
        # Customer's training history
        # --------------------------------------------------------

        history = histories.get(
            customer_id,
            set()
        )

        # --------------------------------------------------------
        # Safety check
        #
        # The target must NOT be present in this customer's
        # training history.
        # --------------------------------------------------------

        if target in history:
            customers_skipped += 1
            continue

        # --------------------------------------------------------
        # Build negative pool
        #
        # Negatives:
        #   - appeared in training catalog
        #   - not purchased by this customer
        #   - not the target
        # --------------------------------------------------------

        available_negatives = list(
            train_products
            - history
            - {target}
        )

        if len(
            available_negatives
        ) < NEGATIVE_SAMPLES:

            customers_skipped += 1
            continue

        # --------------------------------------------------------
        # Sample negatives
        #
        # Candidate order is irrelevant because ranking uses
        # deterministic tie-breaking.
        # --------------------------------------------------------

        negatives = random.sample(
            available_negatives,
            NEGATIVE_SAMPLES
        )

        candidates = [
            target
        ] + negatives

        # --------------------------------------------------------
        # POPULARITY
        # --------------------------------------------------------

        popularity_scores = {
            product_id: float(
                popularity.get(
                    product_id,
                    0.0
                )
            )
            for product_id in candidates
        }

        # --------------------------------------------------------
        # COLLABORATIVE
        # --------------------------------------------------------

        collab_scores = (
            collaborative.score_candidates(
                customer_id,
                candidates
            )
        )

        # --------------------------------------------------------
        # CONTENT-BASED
        #
        # Score every candidate against the COMPLETE
        # customer training history.
        #
        # Content score:
        #
        # max cosine similarity(candidate, purchased item)
        #
        # across all products in customer's training history.
        # --------------------------------------------------------

        content_scores = {
            product_id: 0.0
            for product_id in candidates
        }

        history_products = list(
            history
        )

        history_indices = [
            content.product_to_index[
                product_id
            ]
            for product_id in history_products
            if product_id
            in content.product_to_index
        ]

        candidate_products = [
            product_id
            for product_id in candidates
            if product_id
            in content.product_to_index
        ]

        candidate_indices = [
            content.product_to_index[
                product_id
            ]
            for product_id in candidate_products
        ]

        if (
            history_indices
            and candidate_indices
        ):

            similarities = (
                cosine_similarity(
                    content.tfidf_matrix[
                        candidate_indices
                    ],
                    content.tfidf_matrix[
                        history_indices
                    ]
                )
            )

            max_scores = (
                similarities.max(
                    axis=1
                )
            )

            for (
                product_id,
                score
            ) in zip(
                candidate_products,
                max_scores
            ):

                content_scores[
                    product_id
                ] = float(score)

        # --------------------------------------------------------
        # HYBRID
        #
        # Current research candidate-level hybrid:
        #
        #   0.6 * normalized CF
        # + 0.4 * normalized Content
        #
        # We keep this separate from the production Hybrid
        # evaluation that we will implement next.
        # --------------------------------------------------------

        collab_array = np.array([
            collab_scores.get(
                product_id,
                0.0
            )
            for product_id
            in candidates
        ])

        content_array = np.array([
            content_scores.get(
                product_id,
                0.0
            )
            for product_id
            in candidates
        ])

        collab_normalized = (
            minmax_normalize(
                collab_array
            )
        )

        content_normalized = (
            minmax_normalize(
                content_array
            )
        )

        hybrid_array = (
            0.6
            * collab_normalized
            +
            0.4
            * content_normalized
        )

        hybrid_scores = dict(
            zip(
                candidates,
                hybrid_array
            )
        )

        # --------------------------------------------------------
        # RANK ALL FOUR MODELS
        #
        # Deterministic tie-breaking is essential.
        # --------------------------------------------------------

        rankings = {

            "Popularity": rank_candidates(
                candidates,
                popularity_scores,
                customer_id
            ),

            "Collaborative": rank_candidates(
                candidates,
                collab_scores,
                customer_id
            ),

            "Content-Based": rank_candidates(
                candidates,
                content_scores,
                customer_id
            ),

            "Hybrid": rank_candidates(
                candidates,
                hybrid_scores,
                customer_id
            )
        }

        # --------------------------------------------------------
        # Calculate metrics
        # --------------------------------------------------------

        for (
            model_name,
            ranking
        ) in rankings.items():

            # Rank is 1-based
            rank = (
                ranking.index(target)
                + 1
            )

            for k in TOP_KS:

                # ------------------------------------------------
                # Hit / Recall
                #
                # There is exactly one positive target per
                # customer, so recall@K = hit@K.
                # ------------------------------------------------

                hit = (
                    1
                    if rank <= k
                    else 0
                )

                model_hits[
                    model_name
                ][k].append(hit)

                # ------------------------------------------------
                # NDCG
                # ------------------------------------------------

                model_ndcg[
                    model_name
                ][k].append(
                    ndcg_for_single_positive(
                        rank,
                        k
                    )
                )

        customers_evaluated += 1

        # --------------------------------------------------------
        # Progress
        # --------------------------------------------------------

        if (
            customers_evaluated % 250
            == 0
        ):

            print(
                f"Evaluated "
                f"{customers_evaluated} "
                f"customers..."
            )

    # ============================================================
    # BUILD FINAL RESULTS
    # ============================================================

    results = []

    for model_name in model_names:

        row = {
            "model": model_name,
            "customers": customers_evaluated
        }

        for k in TOP_KS:

            hits = (
                model_hits[
                    model_name
                ][k]
            )

            ndcgs = (
                model_ndcg[
                    model_name
                ][k]
            )

            # ----------------------------------------------------
            # Hit Rate
            # ----------------------------------------------------

            hit_rate = (
                np.mean(hits)
                if hits
                else 0.0
            )

            # ----------------------------------------------------
            # Recall
            #
            # One positive per customer.
            # ----------------------------------------------------

            recall = hit_rate

            # ----------------------------------------------------
            # NDCG
            # ----------------------------------------------------

            ndcg = (
                np.mean(ndcgs)
                if ndcgs
                else 0.0
            )

            # ----------------------------------------------------
            # Precision
            #
            # One relevant item exists per evaluation case.
            #
            # If target is in Top-K:
            #
            # precision = 1/K
            #
            # Otherwise:
            #
            # precision = 0
            # ----------------------------------------------------

            precision = (
                hit_rate / k
            )

            row[
                f"hit_rate@{k}"
            ] = hit_rate

            row[
                f"recall@{k}"
            ] = recall

            row[
                f"ndcg@{k}"
            ] = ndcg

            row[
                f"precision@{k}"
            ] = precision

        results.append(row)

    # ============================================================
    # DATAFRAME
    # ============================================================

    results_df = pd.DataFrame(
        results
    )

    # ============================================================
    # PRINT RESULTS
    # ============================================================

    print()
    print("=" * 70)
    print(
        "RESULTS"
    )
    print("=" * 70)

    print(
        results_df.to_string(
            index=False
        )
    )

    print()
    print(
        f"Customers evaluated : "
        f"{customers_evaluated}"
    )

    print(
        f"Customers skipped   : "
        f"{customers_skipped}"
    )

    print(
        f"Negative samples/customer : "
        f"{NEGATIVE_SAMPLES}"
    )

    print(
        f"Candidate set/customer : "
        f"{NEGATIVE_SAMPLES + 1}"
    )

    print(
        f"Random seed : "
        f"{RANDOM_SEED}"
    )

    # ============================================================
    # SAVE RESULTS
    # ============================================================

    output_path = (
        "/validation/evaluation/"
        "candidate_ranking_results.csv"
    )

    results_df.to_csv(
        output_path,
        index=False
    )

    print()
    print(
        f"Saved: {output_path}"
    )


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    main()