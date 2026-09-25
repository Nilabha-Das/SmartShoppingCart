from app.recommender.content_based import ContentBasedRecommender
from app.recommender.collaborative import CollaborativeRecommender
from app.recommender.hybrid import HybridRecommender


class RecommendationEngine:

    def __init__(self):

        self.content_recommender = (
            ContentBasedRecommender()
        )

        self.collaborative_recommender = (
            CollaborativeRecommender()
        )

        self.hybrid_recommender = HybridRecommender(
            self.content_recommender,
            self.collaborative_recommender
        )

    # ---------------------------------------------------------
    # Content-based recommendation
    # ---------------------------------------------------------

    def content(
        self,
        product_id: str,
        n: int = 10
    ):

        return (
            self.content_recommender
            .recommend_similar_products(
                product_id,
                n=n
            )
        )

    # ---------------------------------------------------------
    # Collaborative recommendation
    # ---------------------------------------------------------

    def collaborative(
        self,
        customer_id: str,
        n: int = 10
    ):

        return (
            self.collaborative_recommender
            .recommend(
                customer_id,
                n_candidates=n
            )
        )

    # ---------------------------------------------------------
    # Hybrid recommendation
    # ---------------------------------------------------------

    def hybrid(
        self,
        customer_id: str,
        n: int = 10
    ):

        return (
            self.hybrid_recommender
            .recommend(
                customer_id,
                n=n
            )
        )