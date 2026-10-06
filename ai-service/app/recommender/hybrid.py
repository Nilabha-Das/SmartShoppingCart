import pandas as pd
from sklearn.preprocessing import MinMaxScaler


class HybridRecommender:

    def __init__(
        self,
        collaborative_recommender,
        content_recommender,
        collaborative_weight=0.6,
        content_weight=0.4,
    ):
        self.collaborative = collaborative_recommender
        self.content = content_recommender

        self.collaborative_weight = collaborative_weight
        self.content_weight = content_weight

    def _extract_product_ids(self, history):

        if history is None:
            return []

        # DataFrame
        if isinstance(history, pd.DataFrame):
            if "product_id" in history.columns:
                return (
                    history["product_id"]
                    .astype(str)
                    .tolist()
                )

        # List / tuple
        if isinstance(history, (list, tuple)):

            product_ids = []

            for item in history:

                if isinstance(item, dict):
                    if "product_id" in item:
                        product_ids.append(
                            str(item["product_id"])
                        )

                else:
                    product_ids.append(str(item))

            return product_ids

        return []

    def recommend(
        self,
        customer_id,
        n=10,
        n_similar=20,
        n_candidates=50,
    ):

        # ----------------------------------------------------
        # COLLABORATIVE CANDIDATES
        # ----------------------------------------------------

        collaborative_candidates = (
            self.collaborative.recommend(
                customer_id=customer_id,
                n_similar=n_similar,
                n_candidates=n_candidates,
            )
        )

        if collaborative_candidates is None:
            collaborative_candidates = []

        # Convert old DataFrame interface if necessary.
        if isinstance(
            collaborative_candidates,
            pd.DataFrame
        ):
            collaborative_candidates = (
                collaborative_candidates
                .to_dict("records")
            )

        # ----------------------------------------------------
        # CUSTOMER HISTORY
        # ----------------------------------------------------

        history = self.collaborative.get_customer_history(
            customer_id
        )

        purchased_products = set(
            self._extract_product_ids(history)
        )

        # ----------------------------------------------------
        # CONTENT SCORES
        # ----------------------------------------------------

        content_scores = {}

        for candidate in collaborative_candidates:

            product_id = str(
                candidate["product_id"]
            )

            if product_id in purchased_products:
                continue

            max_content_score = 0.0

            for purchased_product in purchased_products:

                similar = (
                    self.content
                    .recommend_similar_products(
                        purchased_product,
                        n=20
                    )
                )

                if similar is None:
                    continue

                if isinstance(similar, pd.DataFrame):

                    if similar.empty:
                        continue

                    matches = similar[
                        similar["product_id"]
                        .astype(str)
                        == product_id
                    ]

                    if not matches.empty:

                        score = float(
                            matches.iloc[0][
                                "content_score"
                            ]
                        )

                        max_content_score = max(
                            max_content_score,
                            score
                        )

                elif isinstance(similar, list):

                    for item in similar:

                        if not isinstance(item, dict):
                            continue

                        if str(
                            item.get("product_id")
                        ) == product_id:

                            score = float(
                                item.get(
                                    "content_score",
                                    0.0
                                )
                            )

                            max_content_score = max(
                                max_content_score,
                                score
                            )

            content_scores[product_id] = (
                max_content_score
            )

        # ----------------------------------------------------
        # BUILD SCORE TABLE
        # ----------------------------------------------------

        rows = []

        for candidate in collaborative_candidates:

            product_id = str(
                candidate["product_id"]
            )

            if product_id in purchased_products:
                continue

            collaborative_score = float(
                candidate.get("score", 0.0)
            )

            content_score = float(
                content_scores.get(
                    product_id,
                    0.0
                )
            )

            rows.append(
                {
                    "product_id": product_id,
                    "collaborative_score":
                        collaborative_score,
                    "content_score":
                        content_score,
                }
            )

        if not rows:
            return []

        df = pd.DataFrame(rows)

        # ----------------------------------------------------
        # NORMALIZE COLLABORATIVE SCORE
        # ----------------------------------------------------

        scaler = MinMaxScaler()

        if df["collaborative_score"].nunique() <= 1:

            df["collaborative_normalized"] = 0.0

        else:

            df[
                "collaborative_normalized"
            ] = scaler.fit_transform(
                df[["collaborative_score"]]
            )

        # ----------------------------------------------------
        # NORMALIZE CONTENT SCORE
        # ----------------------------------------------------

        if df["content_score"].nunique() <= 1:

            df["content_normalized"] = 0.0

        else:

            df[
                "content_normalized"
            ] = scaler.fit_transform(
                df[["content_score"]]
            )

        # ----------------------------------------------------
        # HYBRID SCORE
        # ----------------------------------------------------

        df["hybrid_score"] = (
            self.collaborative_weight
            * df["collaborative_normalized"]
            +
            self.content_weight
            * df["content_normalized"]
        )

        # ----------------------------------------------------
        # FINAL RANKING
        # ----------------------------------------------------

        df = df.sort_values(
            "hybrid_score",
            ascending=False
        )

        return df.head(n).to_dict(
            "records"
        )