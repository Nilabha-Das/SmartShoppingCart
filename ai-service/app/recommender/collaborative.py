import pandas as pd
import numpy as np

from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity


INTERACTIONS_PATH = (
    "/app/data/phase2/customer_product_interactions.csv"
)


class CollaborativeRecommender:

    def __init__(self):

        print("COLLAB: loading interactions...", flush=True)

        # ---------------------------------------------------------
        # 1. Load interaction data
        # ---------------------------------------------------------

        self.interactions = pd.read_csv(
            INTERACTIONS_PATH
        )

        print(
            f"COLLAB: interactions loaded: "
            f"{self.interactions.shape}",
            flush=True
        )

        # ---------------------------------------------------------
        # 2. Create customer and product mappings
        # ---------------------------------------------------------

        self.customers = sorted(
            self.interactions["customer_id"]
            .unique()
            .tolist()
        )

        self.products = sorted(
            self.interactions["product_id"]
            .unique()
            .tolist()
        )

        self.customer_to_index = {
            customer_id: index
            for index, customer_id
            in enumerate(self.customers)
        }

        self.product_to_index = {
            product_id: index
            for index, product_id
            in enumerate(self.products)
        }

        print(
            f"COLLAB: customers = {len(self.customers)}",
            flush=True
        )

        print(
            f"COLLAB: products = {len(self.products)}",
            flush=True
        )

        # ---------------------------------------------------------
        # 3. Build sparse customer-product matrix
        #
        # IMPORTANT:
        # Do NOT use pandas pivot_table here.
        #
        # The dense matrix would be approximately:
        #
        # 3000 x 27555 = 82M cells
        #
        # ---------------------------------------------------------

        rows = (
            self.interactions["customer_id"]
            .map(self.customer_to_index)
            .to_numpy()
        )

        cols = (
            self.interactions["product_id"]
            .map(self.product_to_index)
            .to_numpy()
        )

        values = (
            self.interactions["total_quantity"]
            .astype(float)
            .to_numpy()
        )

        self.interaction_matrix = csr_matrix(
            (
                values,
                (rows, cols)
            ),
            shape=(
                len(self.customers),
                len(self.products)
            )
        )

        print(
            "COLLAB: sparse interaction matrix created",
            flush=True
        )

        print(
            f"COLLAB: matrix shape = "
            f"{self.interaction_matrix.shape}",
            flush=True
        )

        print(
            f"COLLAB: non-zero values = "
            f"{self.interaction_matrix.nnz}",
            flush=True
        )

        # ---------------------------------------------------------
        # 4. Convert to implicit/binary feedback
        # ---------------------------------------------------------

        binary_matrix = self.interaction_matrix.copy()

        binary_matrix.data = np.ones_like(
            binary_matrix.data
        )

        print(
            "COLLAB: calculating customer similarity...",
            flush=True
        )

        # ---------------------------------------------------------
        # 5. Customer-to-customer similarity
        # ---------------------------------------------------------

        self.customer_similarity = cosine_similarity(
            binary_matrix,
            dense_output=True
        )

        print(
            "COLLAB: customer similarity calculated",
            flush=True
        )

        print(
            "COLLAB ENGINE OK",
            flush=True
        )

    # =============================================================
    # RECOMMEND
    # =============================================================

    def recommend(
        self,
        customer_id,
        n_similar=20,
        n_candidates=10
    ):

        # ---------------------------------------------------------
        # Customer doesn't exist
        # ---------------------------------------------------------

        if customer_id not in self.customer_to_index:
            return pd.DataFrame(
                columns=[
                    "product_id",
                    "collaborative_score"
                ]
            )

        customer_index = (
            self.customer_to_index[customer_id]
        )

        similarity_scores = (
            self.customer_similarity[
                customer_index
            ]
        )

        similar_indices = np.argsort(
            similarity_scores
        )[::-1]

        candidates = {}

        processed_similar = 0

        # ---------------------------------------------------------
        # Products already purchased
        # ---------------------------------------------------------

        customer_row = (
            self.interaction_matrix.getrow(
                customer_index
            )
        )

        purchased_indices = set(
            customer_row.indices
        )

        # ---------------------------------------------------------
        # Find products from similar customers
        # ---------------------------------------------------------

        for i in similar_indices:

            similar_customer_index = int(i)

            # Skip the customer themselves
            if (
                similar_customer_index
                == customer_index
            ):
                continue

            similarity = float(
                similarity_scores[i]
            )

            # Ignore zero similarity
            if similarity <= 0:
                continue

            similar_row = (
                self.interaction_matrix.getrow(
                    similar_customer_index
                )
            )

            for product_index, quantity in zip(
                similar_row.indices,
                similar_row.data
            ):

                # Don't recommend something the
                # customer already purchased
                if product_index in purchased_indices:
                    continue

                product_id = (
                    self.products[product_index]
                )

                score = (
                    similarity
                    * float(quantity)
                )

                candidates[product_id] = (
                    candidates.get(
                        product_id,
                        0.0
                    )
                    + score
                )

            processed_similar += 1

            if (
                processed_similar
                >= n_similar
            ):
                break

        # ---------------------------------------------------------
        # No candidates
        # ---------------------------------------------------------

        if not candidates:
            return pd.DataFrame(
                columns=[
                    "product_id",
                    "collaborative_score"
                ]
            )

        # ---------------------------------------------------------
        # Create recommendation DataFrame
        # ---------------------------------------------------------

        recommendations = pd.DataFrame(
            list(candidates.items()),
            columns=[
                "product_id",
                "collaborative_score"
            ]
        )

        recommendations = (
            recommendations
            .sort_values(
                "collaborative_score",
                ascending=False
            )
            .head(n_candidates)
            .reset_index(drop=True)
        )

        return recommendations