import time
import math
import hashlib

import numpy as np
import pandas as pd

from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity

from app.recommender.collaborative import CollaborativeRecommender
from app.recommender.content_based import ContentBasedRecommender
from app.recommender.personalized_reranker import PersonalizedReranker


# ============================================================
# CONFIG
# ============================================================

TRAIN_PATH = (
    "/validation/evaluation/"
    "hybrid_inner_train_interactions.csv"
)

VALIDATION_PATH = (
    "/validation/evaluation/"
    "hybrid_validation_interactions.csv"
)

RESULTS_PATH = (
    "/validation/evaluation/"
    "personalized_recommendation_results.csv"
)

CUSTOMER_RESULTS_PATH = (
    "/validation/evaluation/"
    "personalized_customer_results.csv"
)

RECOMMENDATION_LISTS_PATH = (
    "/validation/evaluation/"
    "personalized_recommendation_lists.csv"
)

TOP_N = 10
CF_CANDIDATES = 50

# Evaluation-only hybrid candidate generation.
CF_WEIGHT = 0.1
CONTENT_WEIGHT = 0.9

CONTENT_NEIGHBORS = CF_CANDIDATES

PROGRESS_EVERY = 50


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def print_progress(
    prefix,
    current,
    total,
    start_time,
):

    elapsed = time.time() - start_time

    if current > 0:
        eta = (
            elapsed / current
        ) * (
            total - current
        )
    else:
        eta = 0

    percent = (
        current / total
    ) * 100

    print(
        f"\r{prefix}: "
        f"{current:,}/{total:,} "
        f"({percent:6.2f}%) | "
        f"Elapsed: {elapsed / 60:5.1f} min | "
        f"ETA: {eta / 60:5.1f} min",
        end="",
        flush=True,
    )

    if current == total:
        print()


def minmax_scores(values):

    values = np.asarray(
        values,
        dtype=float,
    )

    if len(values) == 0:
        return values

    minimum = values.min()
    maximum = values.max()

    if maximum - minimum <= 1e-12:
        return np.zeros_like(values)

    return (
        values - minimum
    ) / (
        maximum - minimum
    )


def dcg_at_k(
    relevance,
    k,
):

    relevance = np.asarray(
        relevance[:k],
        dtype=float,
    )

    if len(relevance) == 0:
        return 0.0

    discounts = np.log2(
        np.arange(
            2,
            len(relevance) + 2,
        )
    )

    return float(
        np.sum(
            relevance / discounts
        )
    )


def ndcg_at_k(
    recommendations,
    target,
    k,
):

    relevance = [
        1 if product_id == target else 0
        for product_id
        in recommendations[:k]
    ]

    actual = dcg_at_k(
        relevance,
        k,
    )

    # One relevant item.
    ideal = 1.0

    return actual / ideal


def hash_tiebreak(
    product_id,
):

    return hashlib.md5(
        str(product_id)
        .encode("utf-8")
    ).hexdigest()


# ============================================================
# BUILD CONTENT NEIGHBOR INDEX
# ============================================================

def build_content_neighbor_index(
    content_model,
    product_ids,
):

    print("\n" + "=" * 70)
    print("BUILDING CONTENT NEIGHBOR INDEX")
    print("=" * 70)

    start_time = time.time()

    tfidf_matrix = (
        content_model.tfidf_matrix
    )

    product_to_index = (
        content_model.product_to_index
    )

    valid_product_ids = [
        pid
        for pid in product_ids
        if pid in product_to_index
    ]

    unique_product_ids = list(
        dict.fromkeys(
            valid_product_ids
        )
    )

    print(
        "Products requiring content "
        f"neighbors: {len(unique_product_ids):,}"
    )

    print(
        "TF-IDF matrix shape: "
        f"{tfidf_matrix.shape}"
    )

    print(
        f"Finding top-{CONTENT_NEIGHBORS} "
        "content neighbors for each product..."
    )

    nn = NearestNeighbors(
        n_neighbors=CONTENT_NEIGHBORS + 1,
        metric="cosine",
        algorithm="brute",
        n_jobs=-1,
    )

    nn.fit(tfidf_matrix)

    neighbor_index = {}

    batch_size = 512
    total = len(
        unique_product_ids
    )

    for start in range(
        0,
        total,
        batch_size,
    ):

        end = min(
            start + batch_size,
            total,
        )

        batch_ids = (
            unique_product_ids[
                start:end
            ]
        )

        batch_indices = [
            product_to_index[pid]
            for pid in batch_ids
        ]

        distances, indices = (
            nn.kneighbors(
                tfidf_matrix[
                    batch_indices
                ],
                n_neighbors=(
                    CONTENT_NEIGHBORS + 1
                ),
            )
        )

        for row_number, source_product_id in enumerate(
            batch_ids
        ):

            source_index = (
                product_to_index[
                    source_product_id
                ]
            )

            neighbours = []

            for distance, neighbour_index in zip(
                distances[row_number],
                indices[row_number],
            ):

                if (
                    neighbour_index
                    == source_index
                ):
                    continue

                neighbour_product_id = str(
                    content_model
                    .content_products
                    .iloc[
                        neighbour_index
                    ]["product_id"]
                )

                similarity = float(
                    1.0 - distance
                )

                neighbours.append(
                    (
                        neighbour_product_id,
                        similarity,
                    )
                )

                if len(neighbours) >= (
                    CONTENT_NEIGHBORS
                ):
                    break

            neighbor_index[
                source_product_id
            ] = neighbours

        print_progress(
            "Content index",
            end,
            total,
            start_time,
        )

    print(
        "\nContent neighbor index "
        f"completed in "
        f"{(time.time() - start_time) / 60:.2f} minutes."
    )

    return neighbor_index


# ============================================================
# CONTENT RECOMMENDATIONS
# ============================================================

def get_content_recommendations(
    history,
    content_neighbors,
    top_n,
):

    history = set(
        str(x)
        for x in history
    )

    candidate_scores = {}

    for history_product in history:

        neighbours = (
            content_neighbors.get(
                history_product,
                [],
            )
        )

        for product_id, score in neighbours:

            if product_id in history:
                continue

            previous_score = (
                candidate_scores.get(
                    product_id,
                    -np.inf,
                )
            )

            if score > previous_score:
                candidate_scores[
                    product_id
                ] = score

    if not candidate_scores:
        return []

    ranked = sorted(
        candidate_scores.items(),
        key=lambda x: (
            -x[1],
            hash_tiebreak(
                x[0]
            ),
        ),
    )

    return [
        {
            "product_id": product_id,
            "content_score": float(score),
        }
        for product_id, score
        in ranked[:top_n]
    ]


# ============================================================
# HYBRID CANDIDATE GENERATION
# ============================================================

def build_hybrid_recommendations(
    cf_recommendations,
    content_recommendations,
    top_n,
):

    scores = {}

    # --------------------------------------------------------
    # CF candidates
    # --------------------------------------------------------

    for item in cf_recommendations:

        product_id = str(
            item["product_id"]
        )

        if product_id not in scores:

            scores[
                product_id
            ] = {
                "product_id": product_id,
                "cf_score": 0.0,
                "content_score": 0.0,
            }

        scores[
            product_id
        ]["cf_score"] = float(
            item.get(
                "score",
                item.get(
                    "collaborative_score",
                    0.0,
                ),
            )
        )

    # --------------------------------------------------------
    # Content candidates
    # --------------------------------------------------------

    for item in content_recommendations:

        product_id = str(
            item["product_id"]
        )

        if product_id not in scores:

            scores[
                product_id
            ] = {
                "product_id": product_id,
                "cf_score": 0.0,
                "content_score": 0.0,
            }

        scores[
            product_id
        ]["content_score"] = float(
            item.get(
                "content_score",
                0.0,
            )
        )

    if not scores:
        return []

    items = list(
        scores.values()
    )

    cf_values = [
        item["cf_score"]
        for item in items
    ]

    content_values = [
        item["content_score"]
        for item in items
    ]

    cf_normalized = (
        minmax_scores(
            cf_values
        )
    )

    content_normalized = (
        minmax_scores(
            content_values
        )
    )

    for i, item in enumerate(items):

        item[
            "cf_normalized"
        ] = float(
            cf_normalized[i]
        )

        item[
            "content_normalized"
        ] = float(
            content_normalized[i]
        )

        item[
            "hybrid_score"
        ] = (
            CF_WEIGHT
            * item["cf_normalized"]
            +
            CONTENT_WEIGHT
            * item[
                "content_normalized"
            ]
        )

    items.sort(
        key=lambda x: (
            -x["hybrid_score"],
            hash_tiebreak(
                x["product_id"]
            ),
        )
    )

    return items[:top_n]


# ============================================================
# DIVERSITY
# ============================================================

def calculate_diversity(
    recommendation_ids,
    content_model,
):

    recommendation_ids = [
        pid
        for pid in recommendation_ids
        if pid
        in content_model.product_to_index
    ]

    if len(
        recommendation_ids
    ) < 2:
        return 0.0

    indices = [
        content_model.product_to_index[
            pid
        ]
        for pid in recommendation_ids
    ]

    matrix = (
        content_model.tfidf_matrix[
            indices
        ]
    )

    similarity_matrix = (
        cosine_similarity(
            matrix
        )
    )

    upper_triangle = (
        similarity_matrix[
            np.triu_indices(
                len(
                    recommendation_ids
                ),
                k=1,
            )
        ]
    )

    if len(
        upper_triangle
    ) == 0:
        return 0.0

    return float(
        1.0
        - np.mean(
            upper_triangle
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    overall_start = time.time()

    print("\n")
    print("=" * 70)
    print(
        "PERSONALIZED RECOMMENDATION EVALUATION"
    )
    print("=" * 70)

    print(
        f"TOP_N              : {TOP_N}"
    )

    print(
        f"CF candidates      : {CF_CANDIDATES}"
    )

    print(
        f"CF weight          : {CF_WEIGHT}"
    )

    print(
        f"Content weight     : {CONTENT_WEIGHT}"
    )

    print("=" * 70)

    # ========================================================
    # 1. LOAD DATA
    # ========================================================

    print(
        "\n[1/6] Loading evaluation data..."
    )

    train_df = pd.read_csv(
        TRAIN_PATH
    )

    validation_df = pd.read_csv(
        VALIDATION_PATH
    )

    train_df["customer_id"] = (
        train_df["customer_id"]
        .astype(str)
    )

    train_df["product_id"] = (
        train_df["product_id"]
        .astype(str)
    )

    validation_df["customer_id"] = (
        validation_df["customer_id"]
        .astype(str)
    )

    validation_df["product_id"] = (
        validation_df["product_id"]
        .astype(str)
    )

    print(
        f"Train interactions      : "
        f"{len(train_df):,}"
    )

    print(
        f"Validation interactions : "
        f"{len(validation_df):,}"
    )

    # ========================================================
    # WARM START CUSTOMERS
    # ========================================================

    train_customers = set(
        train_df[
            "customer_id"
        ].unique()
    )

    validation_customers = set(
        validation_df[
            "customer_id"
        ].unique()
    )

    warm_customers = sorted(
        train_customers.intersection(
            validation_customers
        )
    )

    validation_targets = (
        validation_df
        .groupby(
            "customer_id"
        )["product_id"]
        .first()
        .to_dict()
    )

    warm_customers = [
        customer_id
        for customer_id
        in warm_customers
        if customer_id
        in validation_targets
    ]

    print(
        f"Warm-start customers    : "
        f"{len(warm_customers):,}"
    )

    # ========================================================
    # 2. CUSTOMER HISTORIES
    # ========================================================

    print(
        "\n[2/6] Building customer histories..."
    )

    customer_histories = (
        train_df
        .groupby(
            "customer_id"
        )["product_id"]
        .apply(
            lambda x:
            list(
                dict.fromkeys(
                    x.astype(str)
                )
            )
        )
        .to_dict()
    )

    # ========================================================
    # 3. LOAD MODELS
    # ========================================================

    print(
        "\n[3/6] Loading recommender models..."
    )

    model_start = time.time()

    collaborative = (
        CollaborativeRecommender(
            interactions_path=TRAIN_PATH
        )
    )

    content = (
        ContentBasedRecommender()
    )

    personalized_reranker = (
        PersonalizedReranker(
            products_path=(
                "/validation/"
                "master_products_clean.csv"
            ),
            interactions_path=TRAIN_PATH,
        )
    )

    print(
        "Models initialized in "
        f"{time.time() - model_start:.2f} seconds."
    )

    # ========================================================
    # CONTENT INDEX
    # ========================================================

    all_history_products = set()

    for history in (
        customer_histories.values()
    ):
        all_history_products.update(
            history
        )

    content_neighbors = (
        build_content_neighbor_index(
            content,
            sorted(
                all_history_products
            ),
        )
    )

    # ========================================================
    # 4. POPULARITY
    # ========================================================

    print(
        "\n[4/6] Preparing popularity statistics..."
    )

    popularity = (
        train_df
        .groupby(
            "product_id"
        )["total_quantity"]
        .sum()
        .sort_values(
            ascending=False
        )
    )

    popularity_scores = (
        popularity.to_dict()
    )

    catalog_size = len(
        content.content_products
    )

    # ========================================================
    # 5. EVALUATION
    # ========================================================

    print(
        "\n[5/6] Running personalized evaluation..."
    )

    print(
        f"Customers to evaluate: "
        f"{len(warm_customers):,}"
    )

    print(
        f"Progress updates every: "
        f"{PROGRESS_EVERY} customers"
    )

    print()

    evaluation_start = time.time()

    model_names = [
        "collaborative",
        "content",
        "hybrid",
        "personalized_hybrid",
    ]

    metrics = {
        model_name: {
            "hit5": [],
            "hit10": [],
            "precision5": [],
            "precision10": [],
            "recall5": [],
            "recall10": [],
            "ndcg5": [],
            "ndcg10": [],
            "diversity": [],
            "novelty": [],
            "preference_alignment": [],
        }
        for model_name
        in model_names
    }

    recommendation_sets = {
        model_name: {}
        for model_name
        in model_names
    }

    recommendation_rows = []
    customer_rows = []

    total = len(
        warm_customers
    )

    # ========================================================
    # CUSTOMER LOOP
    # ========================================================

    for customer_number, customer_id in enumerate(
        warm_customers,
        start=1,
    ):

        history = (
            customer_histories[
                customer_id
            ]
        )

        history_set = set(
            history
        )

        target = str(
            validation_targets[
                customer_id
            ]
        )

        # ====================================================
        # COLLABORATIVE
        # ====================================================

        cf_raw = (
            collaborative.recommend(
                customer_id=customer_id,
                n_similar=20,
                n_candidates=CF_CANDIDATES,
            )
        )

        cf_recommendations = []

        for item in cf_raw:

            product_id = str(
                item["product_id"]
            )

            if product_id in history_set:
                continue

            cf_recommendations.append(
                {
                    "product_id":
                        product_id,
                    "score":
                        float(
                            item.get(
                                "score",
                                0.0,
                            )
                        ),
                }
            )

            if len(
                cf_recommendations
            ) >= CF_CANDIDATES:
                break

        # ====================================================
        # CONTENT
        # ====================================================

        content_recommendations = (
            get_content_recommendations(
                history=history,
                content_neighbors=(
                    content_neighbors
                ),
                top_n=CF_CANDIDATES,
            )
        )

        # ====================================================
        # HYBRID CANDIDATES
        # ====================================================

        hybrid_recommendations = (
            build_hybrid_recommendations(
                cf_recommendations=(
                    cf_recommendations
                ),
                content_recommendations=(
                    content_recommendations
                ),
                top_n=CF_CANDIDATES,
            )
        )

        # ====================================================
        # CUSTOMER PROFILE
        # ====================================================

        customer_profile = (
            personalized_reranker
            .build_customer_profile(
                history=history,
                interactions_df=train_df,
            )
        )

        # ====================================================
        # PERSONALIZED HYBRID
        # ====================================================

        personalized_hybrid_recommendations = (
            personalized_reranker.rerank(
                candidates=(
                    hybrid_recommendations
                ),
                customer_profile=(
                    customer_profile
                ),
                top_n=TOP_N,

                # Final personalized score:
                # 40% CF
                # 25% Content
                # 30% Customer Preference
                # 5% Popularity
                cf_weight=0.40,
                content_weight=0.25,
                preference_weight=0.30,
                popularity_weight=0.05,

                popularity_scores=(
                    popularity_scores
                ),
            )
        )

        # ====================================================
        # FINAL RECOMMENDATION LISTS
        # ====================================================

        recommendation_lists = {

            "collaborative": [
                item["product_id"]
                for item
                in cf_recommendations[
                    :TOP_N
                ]
            ],

            "content": [
                item["product_id"]
                for item
                in content_recommendations[
                    :TOP_N
                ]
            ],

            "hybrid": [
                item["product_id"]
                for item
                in hybrid_recommendations[
                    :TOP_N
                ]
            ],

            "personalized_hybrid": [
                item["product_id"]
                for item
                in personalized_hybrid_recommendations
            ],
        }

        # ====================================================
        # METRICS
        # ====================================================

        customer_metric_row = {
            "customer_id":
                customer_id,

            "target_product_id":
                target,

            "history_length":
                len(history),
        }

        for model_name, recommendations in (
            recommendation_lists.items()
        ):

            recommendation_sets[
                model_name
            ][customer_id] = set(
                recommendations
            )

            hit5 = int(
                target
                in recommendations[:5]
            )

            hit10 = int(
                target
                in recommendations[:10]
            )

            precision5 = (
                hit5 / 5
            )

            precision10 = (
                hit10 / 10
            )

            recall5 = hit5
            recall10 = hit10

            ndcg5 = ndcg_at_k(
                recommendations,
                target,
                5,
            )

            ndcg10 = ndcg_at_k(
                recommendations,
                target,
                10,
            )

            diversity = (
                calculate_diversity(
                    recommendations,
                    content,
                )
            )

            novelty_values = []

            for product_id in (
                recommendations
            ):

                rank = (
                    list(
                        popularity.index
                    ).index(product_id)
                    + 1
                    if product_id
                    in popularity.index
                    else catalog_size
                )

                novelty = math.log2(
                    catalog_size
                    / max(
                        rank,
                        1,
                    )
                )

                novelty_values.append(
                    novelty
                )

            novelty = (
                float(
                    np.mean(
                        novelty_values
                    )
                )
                if novelty_values
                else 0.0
            )

            # =================================================
            # PREFERENCE ALIGNMENT
            # =================================================

            preference_alignment = 0.0

            if (
                model_name
                == "personalized_hybrid"
            ):

                preference_values = [
                    personalized_reranker
                    .preference_score(
                        product_id,
                        customer_profile,
                    )
                    for product_id
                    in recommendations
                ]

                if preference_values:

                    preference_alignment = (
                        float(
                            np.mean(
                                preference_values
                            )
                        )
                    )

            # =================================================
            # STORE METRICS
            # =================================================

            metrics[
                model_name
            ]["hit5"].append(
                hit5
            )

            metrics[
                model_name
            ]["hit10"].append(
                hit10
            )

            metrics[
                model_name
            ]["precision5"].append(
                precision5
            )

            metrics[
                model_name
            ]["precision10"].append(
                precision10
            )

            metrics[
                model_name
            ]["recall5"].append(
                recall5
            )

            metrics[
                model_name
            ]["recall10"].append(
                recall10
            )

            metrics[
                model_name
            ]["ndcg5"].append(
                ndcg5
            )

            metrics[
                model_name
            ]["ndcg10"].append(
                ndcg10
            )

            metrics[
                model_name
            ]["diversity"].append(
                diversity
            )

            metrics[
                model_name
            ]["novelty"].append(
                novelty
            )

            metrics[
                model_name
            ]["preference_alignment"].append(
                preference_alignment
            )

            # =================================================
            # CUSTOMER RESULT
            # =================================================

            customer_metric_row[
                f"{model_name}_hit5"
            ] = hit5

            customer_metric_row[
                f"{model_name}_hit10"
            ] = hit10

            customer_metric_row[
                f"{model_name}_ndcg5"
            ] = ndcg5

            customer_metric_row[
                f"{model_name}_ndcg10"
            ] = ndcg10

            customer_metric_row[
                f"{model_name}_diversity"
            ] = diversity

            customer_metric_row[
                f"{model_name}_novelty"
            ] = novelty

            customer_metric_row[
                f"{model_name}_preference_alignment"
            ] = preference_alignment

            # =================================================
            # RECOMMENDATION LIST
            # =================================================

            for rank, product_id in enumerate(
                recommendations,
                start=1,
            ):

                recommendation_rows.append(
                    {
                        "customer_id":
                            customer_id,

                        "model":
                            model_name,

                        "rank":
                            rank,

                        "product_id":
                            product_id,

                        "is_target":
                            int(
                                product_id
                                == target
                            ),
                    }
                )

        customer_rows.append(
            customer_metric_row
        )

        # ====================================================
        # PROGRESS
        # ====================================================

        if (
            customer_number
            % PROGRESS_EVERY
            == 0
            or customer_number
            == total
        ):

            print_progress(
                "Evaluation",
                customer_number,
                total,
                evaluation_start,
            )

    # ========================================================
    # 6. AGGREGATE RESULTS
    # ========================================================

    print("\n")
    print(
        "[6/6] Aggregating final metrics..."
    )

    result_rows = []

    for model_name in model_names:

        model_metrics = (
            metrics[model_name]
        )

        model_recommendations = (
            recommendation_sets[
                model_name
            ]
        )

        unique_products = set()

        for recommendation_set in (
            model_recommendations.values()
        ):

            unique_products.update(
                recommendation_set
            )

        coverage = (
            len(unique_products)
            / catalog_size
        )

        # ====================================================
        # PERSONALIZATION
        # ====================================================

        customer_ids = list(
            model_recommendations.keys()
        )

        overlaps = []

        if len(customer_ids) >= 2:

            rng = np.random.default_rng(
                42
            )

            pair_count = min(
                500,
                len(customer_ids)
                * (
                    len(customer_ids)
                    - 1
                )
                // 2,
            )

            for _ in range(
                pair_count
            ):

                i, j = rng.choice(
                    len(customer_ids),
                    size=2,
                    replace=False,
                )

                set_a = (
                    model_recommendations[
                        customer_ids[i]
                    ]
                )

                set_b = (
                    model_recommendations[
                        customer_ids[j]
                    ]
                )

                union = (
                    set_a.union(
                        set_b
                    )
                )

                if not union:
                    continue

                intersection = (
                    set_a.intersection(
                        set_b
                    )
                )

                overlaps.append(
                    len(intersection)
                    / len(union)
                )

        personalization = (
            1.0
            - float(
                np.mean(
                    overlaps
                )
            )
            if overlaps
            else 0.0
        )

        # ====================================================
        # RESULT ROW
        # ====================================================

        result_rows.append(
            {
                "model":
                    model_name,

                "customers":
                    len(
                        warm_customers
                    ),

                "hit_rate@5":
                    float(
                        np.mean(
                            model_metrics[
                                "hit5"
                            ]
                        )
                    ),

                "hit_rate@10":
                    float(
                        np.mean(
                            model_metrics[
                                "hit10"
                            ]
                        )
                    ),

                "precision@5":
                    float(
                        np.mean(
                            model_metrics[
                                "precision5"
                            ]
                        )
                    ),

                "precision@10":
                    float(
                        np.mean(
                            model_metrics[
                                "precision10"
                            ]
                        )
                    ),

                "recall@5":
                    float(
                        np.mean(
                            model_metrics[
                                "recall5"
                            ]
                        )
                    ),

                "recall@10":
                    float(
                        np.mean(
                            model_metrics[
                                "recall10"
                            ]
                        )
                    ),

                "ndcg@5":
                    float(
                        np.mean(
                            model_metrics[
                                "ndcg5"
                            ]
                        )
                    ),

                "ndcg@10":
                    float(
                        np.mean(
                            model_metrics[
                                "ndcg10"
                            ]
                        )
                    ),

                "catalog_coverage":
                    coverage,

                "diversity":
                    float(
                        np.mean(
                            model_metrics[
                                "diversity"
                            ]
                        )
                    ),

                "novelty":
                    float(
                        np.mean(
                            model_metrics[
                                "novelty"
                            ]
                        )
                    ),

                "personalization":
                    personalization,

                "preference_alignment":
                    (
                        float(
                            np.mean(
                                model_metrics[
                                    "preference_alignment"
                                ]
                            )
                        )
                        if model_name
                        == "personalized_hybrid"
                        else np.nan
                    ),
            }
        )

    # ========================================================
    # SAVE
    # ========================================================

    results_df = pd.DataFrame(
        result_rows
    )

    customer_results_df = (
        pd.DataFrame(
            customer_rows
        )
    )

    recommendation_lists_df = (
        pd.DataFrame(
            recommendation_rows
        )
    )

    results_df.to_csv(
        RESULTS_PATH,
        index=False,
    )

    customer_results_df.to_csv(
        CUSTOMER_RESULTS_PATH,
        index=False,
    )

    recommendation_lists_df.to_csv(
        RECOMMENDATION_LISTS_PATH,
        index=False,
    )

    # ========================================================
    # FINAL OUTPUT
    # ========================================================

    total_minutes = (
        time.time()
        - overall_start
    ) / 60

    print("\n")
    print("=" * 70)
    print(
        "PERSONALIZED RECOMMENDATION "
        "EVALUATION COMPLETE"
    )
    print("=" * 70)

    print(
        f"Total runtime: "
        f"{total_minutes:.2f} minutes"
    )

    print("\nFINAL RESULTS")
    print("-" * 70)

    print(
        results_df.to_string(
            index=False,
            float_format=lambda x:
            f"{x:.6f}",
        )
    )

    print("\nFILES CREATED")
    print("-" * 70)

    print(RESULTS_PATH)
    print(CUSTOMER_RESULTS_PATH)
    print(RECOMMENDATION_LISTS_PATH)

    print("=" * 70)


if __name__ == "__main__":
    main()