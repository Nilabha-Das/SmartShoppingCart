import os
import numpy as np
import pandas as pd

from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity


class CollaborativeRecommender:
    """
    User-based collaborative filtering recommender.

    Uses customer-product interaction data to:
    1. Build a customer-product interaction matrix.
    2. Calculate customer-to-customer cosine similarity.
    3. Generate recommendations from similar customers.
    4. Score a specified candidate set for evaluation.
    """

    def __init__(
        self,
        interactions_path=None,
        similarity_metric="cosine"
    ):
        # ---------------------------------------------------------
        # Configuration
        # ---------------------------------------------------------

        if interactions_path is None:
            interactions_path = (
                "/app/data/phase2/"
                "customer_product_interactions.csv"
            )

        self.interactions_path = interactions_path
        self.similarity_metric = similarity_metric

        # ---------------------------------------------------------
        # Load interactions
        # ---------------------------------------------------------

        print(
            f"COLLAB: loading interactions from "
            f"{self.interactions_path}"
        )

        if not os.path.exists(self.interactions_path):
            raise FileNotFoundError(
                f"Interaction file not found: "
                f"{self.interactions_path}"
            )

        self.interactions = pd.read_csv(
            self.interactions_path
        )

        print(
            f"COLLAB: interactions loaded: "
            f"{self.interactions.shape}"
        )

        # ---------------------------------------------------------
        # Normalize IDs
        # ---------------------------------------------------------

        self.interactions["customer_id"] = (
            self.interactions["customer_id"]
            .astype(str)
        )

        self.interactions["product_id"] = (
            self.interactions["product_id"]
            .astype(str)
        )

        # ---------------------------------------------------------
        # Validate required columns
        # ---------------------------------------------------------

        required_columns = {
            "customer_id",
            "product_id",
            "total_quantity"
        }

        missing_columns = (
            required_columns
            - set(self.interactions.columns)
        )

        if missing_columns:
            raise ValueError(
                "Missing required columns: "
                f"{sorted(missing_columns)}"
            )

        # ---------------------------------------------------------
        # Build ID mappings
        # ---------------------------------------------------------

        self.customer_ids = sorted(
            self.interactions["customer_id"]
            .unique()
            .tolist()
        )

        self.product_ids = sorted(
            self.interactions["product_id"]
            .unique()
            .tolist()
        )

        self.customer_to_index = {
            customer_id: index
            for index, customer_id
            in enumerate(self.customer_ids)
        }

        self.index_to_customer = {
            index: customer_id
            for customer_id, index
            in self.customer_to_index.items()
        }

        self.product_to_index = {
            product_id: index
            for index, product_id
            in enumerate(self.product_ids)
        }

        self.index_to_product = {
            index: product_id
            for product_id, index
            in self.product_to_index.items()
        }

        print(
            f"COLLAB: customers = "
            f"{len(self.customer_ids)}"
        )

        print(
            f"COLLAB: products = "
            f"{len(self.product_ids)}"
        )

        # ---------------------------------------------------------
        # Build customer-product interaction matrix
        # ---------------------------------------------------------
        #
        # Rows    -> customers
        # Columns -> products
        # Values  -> total quantity
        #
        # Multiple interaction records for the same
        # customer-product pair are aggregated.
        # ---------------------------------------------------------

        customer_indices = (
            self.interactions["customer_id"]
            .map(self.customer_to_index)
            .to_numpy()
        )

        product_indices = (
            self.interactions["product_id"]
            .map(self.product_to_index)
            .to_numpy()
        )

        quantities = (
            pd.to_numeric(
                self.interactions["total_quantity"],
                errors="coerce"
            )
            .fillna(0)
            .to_numpy(dtype=float)
        )

        self.interaction_matrix = csr_matrix(
            (
                quantities,
                (
                    customer_indices,
                    product_indices
                )
            ),
            shape=(
                len(self.customer_ids),
                len(self.product_ids)
            )
        )

        # ---------------------------------------------------------
        # Convert interaction matrix to binary matrix
        # ---------------------------------------------------------
        #
        # For customer similarity, we care primarily about
        # whether customers interacted with products.
        #
        # This prevents customers who simply bought larger
        # quantities from dominating similarity.
        # ---------------------------------------------------------

        self.binary_interaction_matrix = (
            self.interaction_matrix.copy()
        )

        self.binary_interaction_matrix.data = np.ones_like(
            self.binary_interaction_matrix.data
        )

        print(
            "COLLAB: sparse interaction matrix created"
        )

        print(
            f"COLLAB: matrix shape = "
            f"{self.interaction_matrix.shape}"
        )

        print(
            f"COLLAB: non-zero values = "
            f"{self.interaction_matrix.nnz}"
        )

        # ---------------------------------------------------------
        # Calculate customer similarity
        # ---------------------------------------------------------

        print(
            "COLLAB: calculating customer similarity..."
        )

        if self.similarity_metric == "cosine":

            self.customer_similarity = (
                cosine_similarity(
                    self.binary_interaction_matrix
                )
            )

        else:
            raise ValueError(
                f"Unsupported similarity metric: "
                f"{self.similarity_metric}"
            )

        print(
            "COLLAB: customer similarity calculated"
        )

    # =============================================================
    # INTERNAL HELPERS
    # =============================================================

    def _get_customer_index(self, customer_id):
        """
        Return internal matrix index for a customer.
        """

        customer_id = str(customer_id)

        return self.customer_to_index.get(
            customer_id
        )

    def _get_customer_purchased_products(
        self,
        customer_id
    ):
        """
        Return the set of products already purchased
        by a customer.
        """

        customer_idx = self._get_customer_index(
            customer_id
        )

        if customer_idx is None:
            return set()

        row = self.interaction_matrix.getrow(
            customer_idx
        )

        return {
            self.index_to_product[product_idx]
            for product_idx in row.indices
        }

    # =============================================================
    # SCORE CANDIDATES
    # =============================================================

    def score_candidates(
        self,
        customer_id,
        candidate_product_ids,
        n_similar=20
    ):
        """
        Score a specific set of candidate products for
        a customer.

        This method is primarily used for evaluation.

        Scoring logic:

            score(product) =
                SUM(
                    similarity(customer, similar_customer)
                    *
                    quantity(similar_customer, product)
                )

        over the top `n_similar` similar customers.

        Unlike recommend(), this method does NOT remove
        candidate products from the scoring set. This is
        important for evaluation because the evaluator
        explicitly controls which products are candidates.

        Parameters
        ----------
        customer_id : str
            Customer being evaluated.

        candidate_product_ids : iterable
            Products that should be scored.

        n_similar : int
            Number of similar customers to use.

        Returns
        -------
        dict
            {
                product_id: score
            }
        """

        customer_id = str(customer_id)

        candidate_product_ids = [
            str(product_id)
            for product_id in candidate_product_ids
        ]

        # ---------------------------------------------------------
        # Initialize scores
        # ---------------------------------------------------------

        scores = {
            product_id: 0.0
            for product_id in candidate_product_ids
        }

        # ---------------------------------------------------------
        # Unknown customer
        # ---------------------------------------------------------

        customer_idx = self._get_customer_index(
            customer_id
        )

        if customer_idx is None:
            return scores

        # ---------------------------------------------------------
        # Candidate products must exist in the training matrix
        # ---------------------------------------------------------

        candidate_set = set(
            candidate_product_ids
        )

        # ---------------------------------------------------------
        # Get similarity scores
        # ---------------------------------------------------------

        similarity_scores = (
            self.customer_similarity[
                customer_idx
            ]
        )

        # Highest similarity first
        similar_indices = np.argsort(
            similarity_scores
        )[::-1]

        # ---------------------------------------------------------
        # Accumulate scores from similar customers
        # ---------------------------------------------------------

        processed_similar_customers = 0

        for similar_idx in similar_indices:

            # Don't compare customer with itself
            if similar_idx == customer_idx:
                continue

            similarity = float(
                similarity_scores[similar_idx]
            )

            # No useful similarity beyond this point
            if similarity <= 0:
                continue

            similar_customer_row = (
                self.interaction_matrix[
                    similar_idx
                ]
            )

            product_indices = (
                similar_customer_row.indices
            )

            quantities = (
                similar_customer_row.data
            )

            for product_idx, quantity in zip(
                product_indices,
                quantities
            ):

                product_id = (
                    self.index_to_product[
                        product_idx
                    ]
                )

                if product_id in candidate_set:

                    scores[product_id] += (
                        similarity
                        * float(quantity)
                    )

            processed_similar_customers += 1

            if (
                processed_similar_customers
                >= n_similar
            ):
                break

        return scores

    # =============================================================
    # RECOMMEND
    # =============================================================

    def recommend(
        self,
        customer_id,
        n_similar=20,
        n_candidates=10
    ):
        """
        Generate collaborative-filtering recommendations.

        Parameters
        ----------
        customer_id : str
            Customer ID.

        n_similar : int
            Number of similar customers considered.

        n_candidates : int
            Number of recommendations returned.

        Returns
        -------
        list
            List of dictionaries containing:

            {
                "product_id": ...,
                "score": ...
            }
        """

        customer_id = str(customer_id)

        # ---------------------------------------------------------
        # Validate customer
        # ---------------------------------------------------------

        customer_idx = self._get_customer_index(
            customer_id
        )

        if customer_idx is None:
            return []

        # ---------------------------------------------------------
        # Products already purchased
        # ---------------------------------------------------------

        purchased_products = (
            self._get_customer_purchased_products(
                customer_id
            )
        )

        # ---------------------------------------------------------
        # Similar customers
        # ---------------------------------------------------------

        similarity_scores = (
            self.customer_similarity[
                customer_idx
            ]
        )

        similar_indices = np.argsort(
            similarity_scores
        )[::-1]

        # ---------------------------------------------------------
        # Candidate score dictionary
        # ---------------------------------------------------------

        candidate_scores = {}

        processed_similar_customers = 0

        # ---------------------------------------------------------
        # Collect products from similar customers
        # ---------------------------------------------------------

        for similar_idx in similar_indices:

            # Skip the current customer
            if similar_idx == customer_idx:
                continue

            similarity = float(
                similarity_scores[similar_idx]
            )

            # Ignore customers with zero similarity
            if similarity <= 0:
                continue

            similar_customer_row = (
                self.interaction_matrix[
                    similar_idx
                ]
            )

            product_indices = (
                similar_customer_row.indices
            )

            quantities = (
                similar_customer_row.data
            )

            for product_idx, quantity in zip(
                product_indices,
                quantities
            ):

                product_id = (
                    self.index_to_product[
                        product_idx
                    ]
                )

                # Never recommend an already purchased product
                if product_id in purchased_products:
                    continue

                if product_id not in candidate_scores:
                    candidate_scores[product_id] = 0.0

                candidate_scores[product_id] += (
                    similarity
                    * float(quantity)
                )

            processed_similar_customers += 1

            if (
                processed_similar_customers
                >= n_similar
            ):
                break

        # ---------------------------------------------------------
        # Sort candidates
        # ---------------------------------------------------------

        ranked_candidates = sorted(
            candidate_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # ---------------------------------------------------------
        # Return top N
        # ---------------------------------------------------------

        recommendations = []

        for product_id, score in ranked_candidates[
            :n_candidates
        ]:

            recommendations.append(
                {
                    "product_id": product_id,
                    "score": float(score)
                }
            )

        return recommendations

    # =============================================================
    # GET CUSTOMER HISTORY
    # =============================================================

    def get_customer_history(
        self,
        customer_id
    ):
        """
        Return products purchased by a customer.
        """

        return list(
            self._get_customer_purchased_products(
                customer_id
            )
        )

    # =============================================================
    # GET SIMILAR CUSTOMERS
    # =============================================================

    def get_similar_customers(
        self,
        customer_id,
        n=10
    ):
        """
        Return the most similar customers.
        """

        customer_id = str(customer_id)

        customer_idx = self._get_customer_index(
            customer_id
        )

        if customer_idx is None:
            return []

        similarity_scores = (
            self.customer_similarity[
                customer_idx
            ]
        )

        ranked_indices = np.argsort(
            similarity_scores
        )[::-1]

        results = []

        for similar_idx in ranked_indices:

            if similar_idx == customer_idx:
                continue

            similarity = float(
                similarity_scores[similar_idx]
            )

            if similarity <= 0:
                continue

            results.append(
                {
                    "customer_id": (
                        self.index_to_customer[
                            similar_idx
                        ]
                    ),
                    "similarity": similarity
                }
            )

            if len(results) >= n:
                break

        return results


# ================================================================
# SIMPLE MANUAL TEST
# ================================================================

if __name__ == "__main__":

    recommender = CollaborativeRecommender()

    test_customer = (
        recommender.customer_ids[0]
    )

    print()
    print("=" * 60)
    print(
        f"Testing collaborative recommendations "
        f"for {test_customer}"
    )
    print("=" * 60)

    recommendations = recommender.recommend(
        customer_id=test_customer,
        n_similar=20,
        n_candidates=10
    )

    for recommendation in recommendations:
        print(recommendation)