import pandas as pd
from sklearn.preprocessing import MinMaxScaler


class HybridRecommender:

    def __init__(self, content_recommender, collaborative_recommender):
        self.content_recommender = content_recommender
        self.collaborative_recommender = collaborative_recommender

    def recommend(self, customer_id, n=10):

        # Get collaborative candidates
        collaborative_candidates = (
            self.collaborative_recommender.recommend(
                customer_id,
                n_candidates=50
            )
        )

        if collaborative_candidates.empty:
            return pd.DataFrame()

        # Products purchased by the customer
        # Products purchased by the customer

        customer_index = (
            self.collaborative_recommender
            .customer_to_index
            [customer_id]
        )

        customer_row = (
            self.collaborative_recommender
            .interaction_matrix
            .getrow(customer_index)
        )

        purchased_products = [
            self.collaborative_recommender.products[
                product_index
            ]
            for product_index in customer_row.indices
        ]

        # Convert purchased products to TF-IDF indices
        purchased_indices = [
            self.content_recommender.product_to_index[p]
            for p in purchased_products
            if p in self.content_recommender.product_to_index
        ]

        if not purchased_indices:
            collaborative_candidates["content_score"] = 0.0
        else:

            purchased_vectors = (
                self.content_recommender.tfidf_matrix[
                    purchased_indices
                ]
            )

            content_scores = []

            for product_id in collaborative_candidates["product_id"]:

                if product_id not in self.content_recommender.product_to_index:
                    content_scores.append(0.0)
                    continue

                product_index = (
                    self.content_recommender.product_to_index[
                        product_id
                    ]
                )

                product_vector = (
                    self.content_recommender.tfidf_matrix[
                        product_index
                    ]
                )

                similarities = (
                    product_vector @ purchased_vectors.T
                ).toarray().flatten()

                content_scores.append(
                    float(similarities.max())
                )

            collaborative_candidates["content_score"] = (
                content_scores
            )

        # Normalize both recommendation signals
        scaler = MinMaxScaler()

        collaborative_candidates[
            ["collaborative_score", "content_score"]
        ] = scaler.fit_transform(
            collaborative_candidates[
                ["collaborative_score", "content_score"]
            ]
        )

        # Existing hybrid weighting
        collaborative_candidates["hybrid_score"] = (
            0.6 * collaborative_candidates["collaborative_score"]
            + 0.4 * collaborative_candidates["content_score"]
        )

        return (
            collaborative_candidates
            .sort_values(
                "hybrid_score",
                ascending=False
            )
            .head(n)
            .reset_index(drop=True)
        )