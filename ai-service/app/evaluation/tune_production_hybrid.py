import hashlib
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

TRAIN_PATH = (
    "/validation/evaluation/"
    "hybrid_inner_train_interactions.csv"
)

VALIDATION_PATH = (
    "/validation/evaluation/"
    "hybrid_validation_interactions.csv"
)

OUTPUT_PATH = (
    "/validation/evaluation/"
    "production_hybrid_weight_tuning_results.csv"
)

NEGATIVE_SAMPLES = 100
CF_CANDIDATES = 50
RANDOM_SEED = 42

# CF weight values to test.
#
# Content weight = 1 - CF weight
#
# Examples:
#   0.0 -> 100% content
#   0.5 -> 50% CF + 50% content
#   1.0 -> 100% CF
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
    Generate a deterministic tie-breaking value.

    This prevents candidates with identical scores from being
    ordered according to their original list position.

    The held-out target therefore does not receive an artificial
    advantage simply because it was appended to the candidate list.
    """

    key = (
        f"{customer_id}|{product_id}"
        .encode("utf-8")
    )

    digest = hashlib.md5(key).hexdigest()

    return int(digest, 16)


def rank_candidates(
    candidates,
    scores,
    customer_id
):
    """
    Rank candidates by:

    1. Descending model score
    2. Deterministic hash-based tie breaker
    """

    return sorted(
        candidates,
        key=lambda product_id: (
            -float(
                scores.get(
                    product_id,
                    0.0
                )
            ),
            tie_break_value(
                customer_id,
                product_id
            )
        )
    )


# ============================================================
# METRICS
# ============================================================

def hit_at_k(
    ranked,
    target,
    k
):
    """
    Hit@K for a single-positive evaluation.
    """

    return (
        1.0
        if target in ranked[:k]
        else 0.0
    )


def recall_at_k(
    ranked,
    target,
    k
):
    """
    With exactly one relevant item:

        Recall@K = Hit@K
    """

    return hit_at_k(
        ranked,
        target,
        k
    )


def precision_at_k(
    ranked,
    target,
    k
):
    """
    With one relevant item:

        Precision@K = Hit@K / K
    """

    return (
        hit_at_k(
            ranked,
            target,
            k
        )
        / k
    )


def ndcg_at_k(
    ranked,
    target,
    k
):
    """
    NDCG@K for a single relevant item.

    If target is ranked at position r:

        DCG = 1 / log2(r + 1)
    """

    top_k = ranked[:k]

    if target not in top_k:
        return 0.0

    rank = (
        top_k.index(target)
        + 1
    )

    return (
        1.0
        / np.log2(rank + 1)
    )


# ============================================================
# MIN-MAX NORMALIZATION
# ============================================================

def minmax_normalize(scores):
    """
    Min-max normalize a dictionary of scores.

    If all scores are identical, every normalized score
    becomes zero.
    """

    if not scores:
        return {}

    product_ids = list(
        scores.keys()
    )

    values = np.array(
        [
            float(
                scores[product_id]
            )
            for product_id in product_ids
        ],
        dtype=float
    )

    if np.max(values) == np.min(values):

        normalized = np.zeros_like(
            values
        )

    else:

        scaler = MinMaxScaler()

        normalized = (
            scaler
            .fit_transform(
                values.reshape(-1, 1)
            )
            .flatten()
        )

    return {
        product_id: float(value)
        for product_id, value
        in zip(
            product_ids,
            normalized
        )
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("PRODUCTION-FAITHFUL HYBRID WEIGHT TUNING")
    print("=" * 70)

    random.seed(
        RANDOM_SEED
    )

    np.random.seed(
        RANDOM_SEED
    )

    # ========================================================
    # LOAD DATA
    # ========================================================

    train = pd.read_csv(
        TRAIN_PATH
    )

    validation = pd.read_csv(
        VALIDATION_PATH
    )

    train["customer_id"] = (
        train["customer_id"]
        .astype(str)
    )

    train["product_id"] = (
        train["product_id"]
        .astype(str)
    )

    validation["customer_id"] = (
        validation["customer_id"]
        .astype(str)
    )

    validation["product_id"] = (
        validation["product_id"]
        .astype(str)
    )

    print(
        f"Inner train interactions : "
        f"{len(train)}"
    )

    print(
        f"Validation interactions  : "
        f"{len(validation)}"
    )

    # ========================================================
    # CUSTOMER HISTORIES
    # ========================================================

    histories = (
        train
        .groupby("customer_id")["product_id"]
        .apply(list)
        .to_dict()
    )

    # ========================================================
    # TRAINING PRODUCT UNIVERSE
    # ========================================================

    train_products = set(
        train["product_id"]
        .unique()
    )

    # Keep only warm-start validation targets.
    #
    # A target not present in the training product universe
    # cannot be generated by collaborative filtering.
    validation = validation[
        validation["product_id"]
        .isin(train_products)
    ].copy()

    print(
        f"Warm-start validation    : "
        f"{len(validation)}"
    )

    # ========================================================
    # INITIALIZE MODELS
    # ========================================================

    collaborative = (
        CollaborativeRecommender(
            interactions_path=TRAIN_PATH
        )
    )

    content = (
        ContentBasedRecommender()
    )

    print(
        "Models initialized."
    )

    # ========================================================
    # CONTENT ARTIFACT
    # ========================================================

    content_products = (
        content.content_products
    )

    content_product_ids = (
        content_products["product_id"]
        .astype(str)
        .tolist()
    )

    content_product_to_index = {
        product_id: index
        for index, product_id
        in enumerate(
            content_product_ids
        )
    }

    tfidf_matrix = (
        content.tfidf_matrix
    )

    # ========================================================
    # RESULTS STORAGE
    # ========================================================

    all_results = []

    # ========================================================
    # TEST EVERY HYBRID WEIGHT
    # ========================================================

    for alpha in WEIGHTS:

        beta = round(
            1.0 - alpha,
            1
        )

        print()
        print("-" * 70)
        print(
            "Testing production hybrid:"
        )
        print(
            f"CF weight      = {alpha:.1f}"
        )
        print(
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

        # Number of validation targets that were actually
        # produced by the CF candidate-generation stage.
        target_in_cf_candidates = 0

        # ====================================================
        # CUSTOMER-LEVEL EVALUATION
        # ====================================================

        for row_index, row in enumerate(
            validation.itertuples(
                index=False
            ),
            start=1
        ):

            customer_id = str(
                row.customer_id
            )

            target = str(
                row.product_id
            )

            # ------------------------------------------------
            # Customer history
            # ------------------------------------------------

            history = histories.get(
                customer_id,
                []
            )

            history_set = set(
                history
            )

            # The validation item must be new to the customer.
            if target in history_set:
                continue

            # =================================================
            # PRODUCTION CF CANDIDATE GENERATION
            # =================================================

            cf_recommendations = (
                collaborative.recommend(
                    customer_id,
                    n_similar=20,
                    n_candidates=CF_CANDIDATES
                )
            )

            # recommend() returns a list of dictionaries.
            #
            # Example:
            #
            # [
            #     {
            #         "product_id": "P015536",
            #         "score": 0.19535
            #     },
            #     ...
            # ]

            if not cf_recommendations:
                continue

            # ------------------------------------------------
            # Extract CF product IDs
            # ------------------------------------------------

            cf_candidates = []

            for recommendation in (
                cf_recommendations
            ):

                product_id = str(
                    recommendation[
                        "product_id"
                    ]
                )

                if product_id not in cf_candidates:

                    cf_candidates.append(
                        product_id
                    )

            if not cf_candidates:
                continue

            # ------------------------------------------------
            # Check whether CF generated target
            # ------------------------------------------------

            if target in cf_candidates:

                target_in_cf_candidates += 1

            # =================================================
            # PRODUCTION-STYLE CANDIDATE POOL
            # =================================================

            candidates = (
                cf_candidates.copy()
            )

            # ------------------------------------------------
            # Evaluation-only target insertion
            # ------------------------------------------------
            #
            # In the actual production system, if CF does not
            # generate the target, the hybrid cannot rank it.
            #
            # We append the target ONLY for evaluation so that
            # we can distinguish:
            #
            # 1. Candidate-generation failure
            # 2. Ranking failure
            #
            # We separately report how often CF generated the
            # target.
            # ------------------------------------------------

            if target not in candidates:

                candidates.append(
                    target
                )

            # =================================================
            # CONTENT SCORES
            # =================================================

            history_indices = [
                content_product_to_index[
                    product_id
                ]
                for product_id in history
                if product_id
                in content_product_to_index
            ]

            content_scores = {}

            if history_indices:

                history_matrix = (
                    tfidf_matrix[
                        history_indices
                    ]
                )

                for candidate in candidates:

                    candidate_index = (
                        content_product_to_index.get(
                            candidate
                        )
                    )

                    # Product unavailable in content artifact.
                    if candidate_index is None:

                        content_scores[
                            candidate
                        ] = 0.0

                        continue

                    candidate_vector = (
                        tfidf_matrix[
                            candidate_index
                        ]
                    )

                    similarities = (
                        cosine_similarity(
                            candidate_vector,
                            history_matrix
                        )
                        .flatten()
                    )

                    if len(similarities):

                        content_scores[
                            candidate
                        ] = float(
                            np.max(
                                similarities
                            )
                        )

                    else:

                        content_scores[
                            candidate
                        ] = 0.0

            else:

                content_scores = {
                    candidate: 0.0
                    for candidate
                    in candidates
                }

            # =================================================
            # CF SCORES
            # =================================================

            # CollaborativeRecommender.recommend()
            # returns a LIST of dictionaries.
            #
            # Therefore we construct:
            #
            # {
            #     product_id: collaborative_score
            # }

            cf_score_map = {}

            for recommendation in (
                cf_recommendations
            ):

                product_id = str(
                    recommendation[
                        "product_id"
                    ]
                )

                score = float(
                    recommendation[
                        "score"
                    ]
                )

                cf_score_map[
                    product_id
                ] = score

            # Every evaluation candidate gets a score.
            #
            # The held-out target gets 0 if CF did not
            # generate it.

            cf_scores = {
                candidate:
                    cf_score_map.get(
                        candidate,
                        0.0
                    )
                for candidate in candidates
            }

            # =================================================
            # NORMALIZE SIGNALS
            # =================================================

            cf_normalized = (
                minmax_normalize(
                    cf_scores
                )
            )

            content_normalized = (
                minmax_normalize(
                    content_scores
                )
            )

            # =================================================
            # HYBRID SCORE
            # =================================================

            hybrid_scores = {}

            for candidate in candidates:

                hybrid_scores[
                    candidate
                ] = (
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

            # =================================================
            # RANK
            # =================================================

            ranked = rank_candidates(
                candidates,
                hybrid_scores,
                customer_id
            )

            # =================================================
            # METRICS
            # =================================================

            for k in TOP_KS:

                metrics[
                    f"hit@{k}"
                ] += hit_at_k(
                    ranked,
                    target,
                    k
                )

                metrics[
                    f"recall@{k}"
                ] += recall_at_k(
                    ranked,
                    target,
                    k
                )

                metrics[
                    f"ndcg@{k}"
                ] += ndcg_at_k(
                    ranked,
                    target,
                    k
                )

                metrics[
                    f"precision@{k}"
                ] += precision_at_k(
                    ranked,
                    target,
                    k
                )

            evaluated += 1

            if row_index % 500 == 0:

                print(
                    f"Processed validation rows: "
                    f"{row_index}"
                )

        # ====================================================
        # SAFETY CHECK
        # ====================================================

        if evaluated == 0:

            raise RuntimeError(
                "No validation customers were evaluated."
            )

        # ====================================================
        # AVERAGE METRICS
        # ====================================================

        for metric in metrics:

            metrics[metric] /= (
                evaluated
            )

        target_in_cf_rate = (
            target_in_cf_candidates
            / evaluated
        )

        # ====================================================
        # STORE RESULT
        # ====================================================

        result = {
            "cf_weight": alpha,
            "content_weight": beta,
            "customers": evaluated,
            "target_in_cf_candidates_rate":
                target_in_cf_rate,
            **metrics
        }

        all_results.append(
            result
        )

        # ====================================================
        # PRINT CURRENT RESULT
        # ====================================================

        print()

        print(
            f"CF weight {alpha:.1f}: "
            f"Hit@5="
            f"{metrics['hit@5']:.6f}, "
            f"NDCG@5="
            f"{metrics['ndcg@5']:.6f}, "
            f"Hit@10="
            f"{metrics['hit@10']:.6f}, "
            f"NDCG@10="
            f"{metrics['ndcg@10']:.6f}"
        )

        print(
            "Target generated by CF: "
            f"{target_in_cf_rate:.4%}"
        )

    # ========================================================
    # BUILD RESULTS DATAFRAME
    # ========================================================

    results_df = pd.DataFrame(
        all_results
    )

    # Sort primarily by NDCG@5.
    #
    # Tie-breaking:
    #   1. NDCG@5
    #   2. Hit@5
    #   3. NDCG@10
    #
    # This matches the validation objective we selected.
    results_df = (
        results_df
        .sort_values(
            [
                "ndcg@5",
                "hit@5",
                "ndcg@10"
            ],
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # SAVE RESULTS
    # ========================================================

    results_df.to_csv(
        OUTPUT_PATH,
        index=False
    )

    # ========================================================
    # PRINT FULL RESULTS
    # ========================================================

    print()
    print("=" * 70)
    print(
        "PRODUCTION HYBRID WEIGHT TUNING RESULTS"
    )
    print("=" * 70)

    print(
        results_df.to_string(
            index=False
        )
    )

    # ========================================================
    # BEST WEIGHT
    # ========================================================

    best = results_df.iloc[0]

    print()
    print("=" * 70)
    print(
        "BEST PRODUCTION HYBRID WEIGHT"
    )
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

    print(
        "Target in CF candidates : "
        f"{best['target_in_cf_candidates_rate']:.4%}"
    )

    print()
    print(
        f"Saved: {OUTPUT_PATH}"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()