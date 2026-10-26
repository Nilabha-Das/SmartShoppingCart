
import re

from sentence_transformers import SentenceTransformer

from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
    Range,
)

from app.rag.qdrant_client import QdrantConnection


MODEL_NAME = "all-MiniLM-L6-v2"


class ProductRetriever:

    def __init__(self, top_k=5, candidate_k=20):
        self.top_k = top_k
        self.candidate_k = max(candidate_k, top_k)

        self.model = SentenceTransformer(MODEL_NAME)

        qdrant = QdrantConnection()
        self.client = qdrant.get_client()
        self.collection_name = QdrantConnection.COLLECTION_NAME

    @staticmethod
    def _tokenize(text):
        """Convert text into normalized searchable tokens."""

        if not text:
            return set()

        return set(
            re.findall(r"[a-z0-9]+", str(text).lower())
        )

    @classmethod
    def _calculate_relevance(cls, query, product):
        """
        Calculate a heuristic relevance score using:
        - Original vector similarity
        - Product-name keyword overlap
        - Category and subcategory keyword overlap

        This is a ranking heuristic, not a calibrated probability.
        """

        query_tokens = cls._tokenize(query)

        if not query_tokens:
            return product.get("score", 0.0)

        name_tokens = cls._tokenize(
            product.get("product_name", "")
        )

        category_tokens = cls._tokenize(
            product.get("category", "")
        )

        subcategory_tokens = cls._tokenize(
            product.get("subcategory", "")
        )

        name_match = (
            len(query_tokens & name_tokens)
            / len(query_tokens)
        )

        category_match = (
            len(query_tokens & category_tokens)
            / len(query_tokens)
        )

        subcategory_match = (
            len(query_tokens & subcategory_tokens)
            / len(query_tokens)
        )

        vector_score = float(product.get("score") or 0.0)

        # Weighted combination.
        relevance_score = (
            0.60 * vector_score
            + 0.25 * name_match
            + 0.10 * subcategory_match
            + 0.05 * category_match
        )

        return relevance_score

    def retrieve(
        self,
        query,
        category=None,
        subcategory=None,
        max_price=None,
        vegetarian=None,
        vegan=None,
        gluten_free=None,
        high_protein=None,
        min_protein=None,
        low_sugar=None,
        top_k=None,
    ):

        # --------------------------------------------------
        # 1. Convert the user's query into an embedding
        # --------------------------------------------------

        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True,
        )

        # --------------------------------------------------
        # 2. Build Qdrant filters
        # --------------------------------------------------

        filters = []

        if category is not None:
            filters.append(
                FieldCondition(
                    key="category",
                    match=MatchValue(value=category),
                )
            )

        if subcategory is not None:
            filters.append(
                FieldCondition(
                    key="subcategory",
                    match=MatchValue(value=subcategory),
                )
            )

        if max_price is not None:
            filters.append(
                FieldCondition(
                    key="price",
                    range=Range(lte=max_price),
                )
            )

        if vegetarian is not None:
            filters.append(
                FieldCondition(
                    key="vegetarian",
                    match=MatchValue(value=vegetarian),
                )
            )

        if vegan is not None:
            filters.append(
                FieldCondition(
                    key="vegan",
                    match=MatchValue(value=vegan),
                )
            )

        if gluten_free is not None:
            filters.append(
                FieldCondition(
                    key="gluten_free",
                    match=MatchValue(value=gluten_free),
                )
            )

        # High protein
        if high_protein is True:
            filters.append(
                FieldCondition(
                    key="protein_g",
                    range=Range(gte=10.0),
                )
            )

        # Custom minimum protein
        if min_protein is not None:
            filters.append(
                FieldCondition(
                    key="protein_g",
                    range=Range(gte=float(min_protein)),
                )
            )

        # Low sugar
        if low_sugar is True:
            filters.append(
                FieldCondition(
                    key="sugar_g",
                    range=Range(lte=5.0),
                )
            )

        # --------------------------------------------------
        # 3. Create final Qdrant filter
        # --------------------------------------------------

        query_filter = (
            Filter(must=filters)
            if filters
            else None
        )

        # --------------------------------------------------
        # 4. Retrieve more candidates for reranking
        # --------------------------------------------------

        requested_top_k = (
            top_k if top_k is not None else self.top_k
        )

        candidate_limit = max(
            self.candidate_k,
            requested_top_k,
        )

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding.tolist(),
            query_filter=query_filter,
            limit=candidate_limit,
            with_payload=True,
        ).points

        # --------------------------------------------------
        # 5. Convert Qdrant results into product dictionaries
        # --------------------------------------------------

        retrieved_products = []

        for result in results:
            payload = result.payload or {}

            retrieved_products.append(
                {
                    "product_id": payload.get("product_id"),
                    "product_name": payload.get("product_name"),
                    "brand": payload.get("brand"),
                    "category": payload.get("category"),
                    "subcategory": payload.get("subcategory"),
                    "price": payload.get("price"),
                    "rating": payload.get("rating"),

                    # Retained for internal compatibility.
                    # Their presence does not establish verification.
                    "vegetarian": payload.get("vegetarian"),
                    "vegan": payload.get("vegan"),
                    "gluten_free": payload.get("gluten_free"),

                    # Other catalog attributes.
                    "contains_milk": payload.get("contains_milk"),
                    "contains_nuts": payload.get("contains_nuts"),
                    "contains_soy": payload.get("contains_soy"),

                    # Original vector similarity.
                    "score": result.score,
                }
            )

        # --------------------------------------------------
        # 6. Hybrid relevance reranking
        # --------------------------------------------------

        for product in retrieved_products:
            product["relevance_score"] = (
                self._calculate_relevance(query, product)
            )

        retrieved_products.sort(
            key=lambda product: product["relevance_score"],
            reverse=True,
        )

        # --------------------------------------------------
        # 7. Return only the requested number of products
        # --------------------------------------------------

        return retrieved_products[:requested_top_k]
