import numpy as np
import pandas as pd


class PersonalizedReranker:
    """
    Customer-preference based personalization layer.

    Uses historical purchases to learn:
        - category preference
        - subcategory preference
        - brand preference
        - product-type preference
        - frequency-weighted attribute preference
        - recency-weighted attribute preference

    It does NOT replace CF, content-based filtering,
    or the production hybrid recommender.

    It reranks an existing candidate pool.
    """

    def __init__(
        self,
        products_path="/validation/master_products_clean.csv",
        interactions_path=None,
    ):
        self.products_path = products_path
        self.interactions_path = interactions_path

        print(
            "PERSONALIZED RERANKER: "
            "loading product metadata..."
        )

        self.products = pd.read_csv(
            products_path
        )

        self.products["product_id"] = (
            self.products["product_id"]
            .astype(str)
        )

        self.product_lookup = (
            self.products
            .drop_duplicates("product_id")
            .set_index("product_id")
        )

        self.reference_columns = [
            "category",
            "subcategory",
            "brand",
            "product_type",
        ]

        print(
            "PERSONALIZED RERANKER: "
            f"products loaded = "
            f"{len(self.products):,}"
        )

    # =========================================================
    # CUSTOMER PROFILE
    # =========================================================

    def build_customer_profile(
        self,
        history,
        interactions_df=None,
    ):
        """
        Build a customer preference profile from purchase history.

        The profile contains:
            1. basic attribute preferences
            2. frequency-weighted attribute preferences
            3. recency-weighted attribute preferences
        """

        history_ids = self._extract_product_ids(
            history
        )

        history_ids = list(
            dict.fromkeys(history_ids)
        )

        # Keep only products available in metadata.
        history_ids = [
            pid
            for pid in history_ids
            if pid in self.product_lookup.index
        ]

        if not history_ids:
            return {
                "category": {},
                "subcategory": {},
                "brand": {},
                "product_type": {},
                "frequency_attributes": {
                    "category": {},
                    "subcategory": {},
                    "brand": {},
                    "product_type": {},
                },
                "recency_attributes": {
                    "category": {},
                    "subcategory": {},
                    "brand": {},
                    "product_type": {},
                },
            }

        history_products = (
            self.product_lookup.loc[
                history_ids
            ].copy()
        )

        # =====================================================
        # BASIC ATTRIBUTE PREFERENCE
        # =====================================================

        profile = {}

        for column in self.reference_columns:

            if column not in history_products.columns:
                profile[column] = {}
                continue

            values = (
                history_products[column]
                .fillna("UNKNOWN")
                .astype(str)
                .str.strip()
            )

            counts = values.value_counts()

            if len(counts) == 0:
                profile[column] = {}
                continue

            total = counts.sum()

            profile[column] = {
                str(key): float(
                    value / total
                )
                for key, value
                in counts.items()
            }

        # =====================================================
        # FREQUENCY-WEIGHTED ATTRIBUTE PROFILE
        # =====================================================

        frequency_attributes = {
            column: {}
            for column in self.reference_columns
        }

        if (
            interactions_df is not None
            and not interactions_df.empty
        ):

            interactions = interactions_df.copy()

            interactions["product_id"] = (
                interactions["product_id"]
                .astype(str)
            )

            # Only this customer's history.
            interactions = interactions[
                interactions["product_id"].isin(
                    history_ids
                )
            ]

            if not interactions.empty:

                if "total_quantity" in interactions.columns:

                    quantity_by_product = (
                        interactions
                        .groupby("product_id")[
                            "total_quantity"
                        ]
                        .sum()
                    )

                    total_quantity = float(
                        quantity_by_product.sum()
                    )

                    if total_quantity > 0:

                        for product_id, quantity in (
                            quantity_by_product.items()
                        ):

                            if product_id not in self.product_lookup.index:
                                continue

                            product = (
                                self.product_lookup.loc[
                                    product_id
                                ]
                            )

                            weight = float(
                                quantity
                                / total_quantity
                            )

                            for column in self.reference_columns:

                                if column not in product.index:
                                    continue

                                value = str(
                                    product[column]
                                )

                                if pd.isna(
                                    product[column]
                                ):
                                    value = "UNKNOWN"

                                frequency_attributes[
                                    column
                                ][value] = (
                                    frequency_attributes[
                                        column
                                    ].get(
                                        value,
                                        0.0,
                                    )
                                    + weight
                                )

        # Normalize frequency attributes.
        for column in self.reference_columns:

            values = frequency_attributes[
                column
            ]

            total = sum(
                values.values()
            )

            if total > 0:

                frequency_attributes[
                    column
                ] = {
                    key: float(
                        value / total
                    )
                    for key, value
                    in values.items()
                }

        # =====================================================
        # RECENCY-WEIGHTED ATTRIBUTE PROFILE
        # =====================================================

        recency_attributes = {
            column: {}
            for column in self.reference_columns
        }

        if (
            interactions_df is not None
            and not interactions_df.empty
        ):

            interactions = interactions_df.copy()

            interactions["product_id"] = (
                interactions["product_id"]
                .astype(str)
            )

            interactions = interactions[
                interactions["product_id"].isin(
                    history_ids
                )
            ]

            if (
                not interactions.empty
                and "days_since_last_purchase"
                in interactions.columns
            ):

                recency_by_product = (
                    interactions
                    .groupby("product_id")[
                        "days_since_last_purchase"
                    ]
                    .min()
                )

                if len(recency_by_product) > 0:

                    max_days = float(
                        recency_by_product.max()
                    )

                    for product_id, days in (
                        recency_by_product.items()
                    ):

                        if product_id not in self.product_lookup.index:
                            continue

                        # More recent purchase =
                        # larger weight.
                        if max_days > 0:

                            weight = (
                                1.0
                                - (
                                    float(days)
                                    / max_days
                                )
                            )

                        else:
                            weight = 1.0

                        weight = max(
                            0.0,
                            min(
                                1.0,
                                weight,
                            ),
                        )

                        product = (
                            self.product_lookup.loc[
                                product_id
                            ]
                        )

                        for column in self.reference_columns:

                            if column not in product.index:
                                continue

                            value = product[column]

                            if pd.isna(value):
                                value = "UNKNOWN"

                            value = str(value)

                            recency_attributes[
                                column
                            ][value] = (
                                recency_attributes[
                                    column
                                ].get(
                                    value,
                                    0.0,
                                )
                                + weight
                            )

                    # Normalize.
                    for column in self.reference_columns:

                        values = recency_attributes[
                            column
                        ]

                        total = sum(
                            values.values()
                        )

                        if total > 0:

                            recency_attributes[
                                column
                            ] = {
                                key: float(
                                    value / total
                                )
                                for key, value
                                in values.items()
                            }

        profile[
            "frequency_attributes"
        ] = frequency_attributes

        profile[
            "recency_attributes"
        ] = recency_attributes

        return profile

    # =========================================================
    # PREFERENCE SCORE
    # =========================================================

    def preference_score(
        self,
        product_id,
        profile,
    ):
        """
        Calculate how strongly a candidate matches
        the customer's historical preferences.

        Score components:

            40% basic historical preference
            35% frequency-weighted preference
            25% recency-weighted preference
        """

        product_id = str(
            product_id
        )

        if (
            product_id
            not in self.product_lookup.index
        ):
            return 0.0

        product = (
            self.product_lookup.loc[
                product_id
            ]
        )

        base_scores = []
        frequency_scores = []
        recency_scores = []

        for column in self.reference_columns:

            if column not in product.index:
                continue

            value = product[column]

            if pd.isna(value):
                value = "UNKNOWN"

            value = str(value)

            # ---------------------------------------------
            # Basic preference
            # ---------------------------------------------

            basic_profile = profile.get(
                column,
                {},
            )

            base_scores.append(
                float(
                    basic_profile.get(
                        value,
                        0.0,
                    )
                )
            )

            # ---------------------------------------------
            # Frequency preference
            # ---------------------------------------------

            frequency_profile = (
                profile
                .get(
                    "frequency_attributes",
                    {},
                )
                .get(
                    column,
                    {},
                )
            )

            frequency_scores.append(
                float(
                    frequency_profile.get(
                        value,
                        0.0,
                    )
                )
            )

            # ---------------------------------------------
            # Recency preference
            # ---------------------------------------------

            recency_profile = (
                profile
                .get(
                    "recency_attributes",
                    {},
                )
                .get(
                    column,
                    {},
                )
            )

            recency_scores.append(
                float(
                    recency_profile.get(
                        value,
                        0.0,
                    )
                )
            )

        if base_scores:
            base_score = float(
                np.mean(base_scores)
            )
        else:
            base_score = 0.0

        if frequency_scores:
            frequency_score = float(
                np.mean(frequency_scores)
            )
        else:
            frequency_score = 0.0

        if recency_scores:
            recency_score = float(
                np.mean(recency_scores)
            )
        else:
            recency_score = 0.0

        final_preference = (
            0.40 * base_score
            + 0.35 * frequency_score
            + 0.25 * recency_score
        )

        return float(
            np.clip(
                final_preference,
                0.0,
                1.0,
            )
        )

    # =========================================================
    # RERANK
    # =========================================================

    def rerank(
        self,
        candidates,
        customer_profile,
        top_n=10,
        cf_weight=0.40,
        content_weight=0.25,
        preference_weight=0.30,
        popularity_weight=0.05,
        popularity_scores=None,
    ):
        """
        Rerank an existing candidate pool.

        Final score:

            0.40 CF
          + 0.25 Content
          + 0.30 Customer Preference
          + 0.05 Popularity

        Customer preference itself combines:

            40% historical attribute preference
            35% frequency preference
            25% recency preference
        """

        if not candidates:
            return []

        rows = []

        for candidate in candidates:

            product_id = str(
                candidate.get(
                    "product_id"
                )
            )

            if (
                product_id
                not in self.product_lookup.index
            ):
                continue

            cf_score = float(
                candidate.get(
                    "cf_score",
                    candidate.get(
                        "collaborative_score",
                        candidate.get(
                            "score",
                            0.0,
                        ),
                    ),
                )
            )

            content_score = float(
                candidate.get(
                    "content_score",
                    0.0,
                )
            )

            rows.append(
                {
                    "product_id": product_id,
                    "cf_score": cf_score,
                    "content_score": content_score,
                }
            )

        if not rows:
            return []

        df = pd.DataFrame(
            rows
        )

        # =====================================================
        # NORMALIZE CF
        # =====================================================

        df["cf_normalized"] = (
            self._minmax(
                df["cf_score"].values
            )
        )

        # =====================================================
        # NORMALIZE CONTENT
        # =====================================================

        df["content_normalized"] = (
            self._minmax(
                df["content_score"].values
            )
        )

        # =====================================================
        # CUSTOMER PREFERENCE
        # =====================================================

        df["preference_score"] = [
            self.preference_score(
                product_id,
                customer_profile,
            )
            for product_id
            in df["product_id"]
        ]

        # =====================================================
        # GLOBAL POPULARITY
        # =====================================================

        if popularity_scores is not None:

            df["popularity_score"] = [
                float(
                    popularity_scores.get(
                        product_id,
                        0.0,
                    )
                )
                for product_id
                in df["product_id"]
            ]

            df["popularity_score"] = (
                self._minmax(
                    df[
                        "popularity_score"
                    ].values
                )
            )

        else:

            # No popularity data supplied.
            # Keep this neutral instead of accidentally
            # using customer frequency as popularity.
            df["popularity_score"] = 0.0

        # =====================================================
        # FINAL PERSONALIZED SCORE
        # =====================================================

        df["personalized_score"] = (
            cf_weight
            * df["cf_normalized"]

            + content_weight
            * df["content_normalized"]

            + preference_weight
            * df["preference_score"]

            + popularity_weight
            * df["popularity_score"]
        )

        # =====================================================
        # FINAL RANKING
        # =====================================================

        df = df.sort_values(
            by=[
                "personalized_score",
                "preference_score",
                "content_normalized",
                "cf_normalized",
            ],
            ascending=False,
        )

        return (
            df
            .head(top_n)
            .to_dict(
                orient="records"
            )
        )

    # =========================================================
    # MIN-MAX
    # =========================================================

    @staticmethod
    def _minmax(values):

        values = np.asarray(
            values,
            dtype=float,
        )

        if len(values) == 0:
            return values

        minimum = values.min()
        maximum = values.max()

        if (
            maximum - minimum
            <= 1e-12
        ):
            return np.zeros_like(
                values
            )

        return (
            values - minimum
        ) / (
            maximum - minimum
        )

    # =========================================================
    # HISTORY EXTRACTION
    # =========================================================

    @staticmethod
    def _extract_product_ids(
        history
    ):

        if history is None:
            return []

        # DataFrame
        if isinstance(
            history,
            pd.DataFrame,
        ):

            if (
                "product_id"
                in history.columns
            ):

                return (
                    history[
                        "product_id"
                    ]
                    .astype(str)
                    .tolist()
                )

            return []

        # List / tuple
        if isinstance(
            history,
            (list, tuple),
        ):

            product_ids = []

            for item in history:

                if isinstance(
                    item,
                    dict,
                ):

                    if (
                        "product_id"
                        in item
                    ):

                        product_ids.append(
                            str(
                                item[
                                    "product_id"
                                ]
                            )
                        )

                else:

                    product_ids.append(
                        str(item)
                    )

            return product_ids

        return []