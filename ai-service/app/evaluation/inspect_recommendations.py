import pandas as pd

from app.recommender.collaborative import CollaborativeRecommender
from app.recommender.content_based import ContentBasedRecommender
from app.recommender.hybrid import HybridRecommender


TRAIN_PATH = "/validation/evaluation/new_item_train_interactions.csv"
TEST_PATH = "/validation/evaluation/new_item_test_interactions.csv"

NUM_CUSTOMERS = 10
TOP_N = 10


def print_recommendations(title, recommendations):
    print(f"\n{title}")

    if recommendations is None or len(recommendations) == 0:
        print("  No recommendations.")
        return

    for rank, item in enumerate(recommendations[:TOP_N], start=1):

        if isinstance(item, dict):
            product_id = item.get("product_id", "")
            score = item.get(
                "score",
                item.get(
                    "content_score",
                    item.get("hybrid_score", 0.0)
                )
            )

            print(
                f"  {rank:2d}. "
                f"{product_id} "
                f"(score={float(score):.6f})"
            )

        else:
            print(
                f"  {rank:2d}. {item}"
            )


def main():

    print("=" * 70)
    print("RECOMMENDATION INSPECTION")
    print("=" * 70)

    # --------------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------------

    train_df = pd.read_csv(TRAIN_PATH)
    test_df = pd.read_csv(TEST_PATH)

    train_df["customer_id"] = train_df[
        "customer_id"
    ].astype(str)

    train_df["product_id"] = train_df[
        "product_id"
    ].astype(str)

    test_df["customer_id"] = test_df[
        "customer_id"
    ].astype(str)

    test_df["product_id"] = test_df[
        "product_id"
    ].astype(str)

    # --------------------------------------------------------
    # LOAD MODELS
    # --------------------------------------------------------

    print("\nLoading Collaborative...")

    collaborative = CollaborativeRecommender(
        interactions_path=TRAIN_PATH
    )

    print("\nLoading Content...")

    content = ContentBasedRecommender()

    print("\nLoading Hybrid...")

    hybrid = HybridRecommender(
        collaborative_recommender=collaborative,
        content_recommender=content
    )

    # --------------------------------------------------------
    # SELECT CUSTOMERS
    # --------------------------------------------------------

    customers = sorted(
        test_df["customer_id"].unique()
    )[:NUM_CUSTOMERS]

    # --------------------------------------------------------
    # INSPECT
    # --------------------------------------------------------

    for customer_id in customers:

        print("\n")
        print("=" * 70)
        print(f"CUSTOMER: {customer_id}")
        print("=" * 70)

        # ----------------------------------------------------
        # TRAINING HISTORY
        # ----------------------------------------------------

        history = train_df[
            train_df["customer_id"] == customer_id
        ].copy()

        history = history.sort_values(
            "last_purchase_date"
        )

        print("\nTraining history:")

        print(
            history[
                [
                    "product_id",
                    "purchase_count",
                    "total_quantity",
                    "last_purchase_date",
                ]
            ].to_string(index=False)
        )

        # ----------------------------------------------------
        # HELD-OUT TARGET
        # ----------------------------------------------------

        target_rows = test_df[
            test_df["customer_id"] == customer_id
        ]

        if target_rows.empty:
            print("\nNo held-out target.")
            continue

        target = str(
            target_rows.iloc[0]["product_id"]
        )

        print(
            f"\nHELD-OUT TARGET: {target}"
        )

        # ----------------------------------------------------
        # COLLABORATIVE
        # ----------------------------------------------------

        collab_recommendations = (
            collaborative.recommend(
                customer_id=customer_id,
                n_similar=20,
                n_candidates=10,
            )
        )

        print_recommendations(
            "Collaborative Top 10:",
            collab_recommendations
        )

        # ----------------------------------------------------
        # CONTENT
        # ----------------------------------------------------

        content_recommendations = []

        purchased_products = (
            history["product_id"]
            .astype(str)
            .tolist()
        )

        seen_content_products = set()

        for product_id in purchased_products:

            recommendations = (
                content.recommend_similar_products(
                    product_id,
                    n=TOP_N
                )
            )

            if recommendations is None:
                continue

            if isinstance(
                recommendations,
                pd.DataFrame
            ):

                for _, row in recommendations.iterrows():

                    recommended_id = str(
                        row["product_id"]
                    )

                    if recommended_id in purchased_products:
                        continue

                    if recommended_id in seen_content_products:
                        continue

                    seen_content_products.add(
                        recommended_id
                    )

                    content_recommendations.append(
                        {
                            "product_id": recommended_id,
                            "content_score": float(
                                row["content_score"]
                            ),
                        }
                    )

            else:

                for item in recommendations:

                    if isinstance(item, dict):

                        recommended_id = str(
                            item["product_id"]
                        )

                        if recommended_id in purchased_products:
                            continue

                        if recommended_id in seen_content_products:
                            continue

                        seen_content_products.add(
                            recommended_id
                        )

                        content_recommendations.append(
                            item
                        )

        content_recommendations.sort(
            key=lambda x: float(
                x.get("content_score", 0.0)
            ),
            reverse=True
        )

        content_recommendations = (
            content_recommendations[:TOP_N]
        )

        print_recommendations(
            "Content-Based Top 10:",
            content_recommendations
        )

        # ----------------------------------------------------
        # HYBRID
        # ----------------------------------------------------

        try:

            hybrid_recommendations = hybrid.recommend(
                customer_id=customer_id,
                n=TOP_N
            )

        except TypeError:

            # Some versions of HybridRecommender use
            # positional arguments.
            hybrid_recommendations = hybrid.recommend(
                customer_id,
                TOP_N
            )

        print_recommendations(
            "Hybrid Top 10:",
            hybrid_recommendations
        )

        # ----------------------------------------------------
        # TARGET CHECK
        # ----------------------------------------------------

        print("\nTarget presence:")

        models = {
            "Collaborative": collab_recommendations,
            "Content": content_recommendations,
            "Hybrid": hybrid_recommendations,
        }

        for model_name, recommendations in models.items():

            ids = []

            for item in recommendations:

                if isinstance(item, dict):
                    ids.append(
                        str(item["product_id"])
                    )
                else:
                    ids.append(
                        str(item)
                    )

            if target in ids:

                rank = ids.index(target) + 1

                print(
                    f"  {model_name}: "
                    f"FOUND at rank {rank}"
                )

            else:

                print(
                    f"  {model_name}: "
                    f"NOT FOUND"
                )

    print("\n")
    print("=" * 70)
    print("INSPECTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()