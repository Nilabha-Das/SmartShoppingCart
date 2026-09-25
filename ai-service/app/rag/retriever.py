from sentence_transformers import SentenceTransformer

from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
    Range
)

from app.rag.qdrant_client import QdrantConnection


MODEL_NAME = "all-MiniLM-L6-v2"


class ProductRetriever:

    def __init__(self, top_k=5):
        self.top_k = top_k

        self.model = SentenceTransformer(MODEL_NAME)

        qdrant = QdrantConnection()
        self.client = qdrant.get_client()
        self.collection_name = QdrantConnection.COLLECTION_NAME

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
        top_k=None
    ):

        # --------------------------------------------------
        # 1. Convert the user's query into an embedding
        # --------------------------------------------------

        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True
        )

        # --------------------------------------------------
        # 2. Build Qdrant filters
        # --------------------------------------------------

        filters = []

        # Category filter
        if category is not None:
            filters.append(
                FieldCondition(
                    key="category",
                    match=MatchValue(value=category)
                )
            )

        # Subcategory filter
        if subcategory is not None:
            filters.append(
                FieldCondition(
                    key="subcategory",
                    match=MatchValue(value=subcategory)
                )
            )

        # Maximum price
        if max_price is not None:
            filters.append(
                FieldCondition(
                    key="price",
                    range=Range(lte=max_price)
                )
            )

        # Vegetarian
        if vegetarian is not None:
            filters.append(
                FieldCondition(
                    key="vegetarian",
                    match=MatchValue(value=vegetarian)
                )
            )

        # Vegan
        if vegan is not None:
            filters.append(
                FieldCondition(
                    key="vegan",
                    match=MatchValue(value=vegan)
                )
            )

        # Gluten free
        if gluten_free is not None:
            filters.append(
                FieldCondition(
                    key="gluten_free",
                    match=MatchValue(value=gluten_free)
                )
            )

        # --------------------------------------------------
        # High protein
        # Default approved threshold:
        # protein >= 10 g per 100 g
        # --------------------------------------------------

        if high_protein is True:
            filters.append(
                FieldCondition(
                    key="protein_g",
                    range=Range(gte=10.0)
                )
            )

        # --------------------------------------------------
        # Custom minimum protein
        # Example:
        # min_protein=15
        # means protein >= 15 g
        # --------------------------------------------------

        if min_protein is not None:
            filters.append(
                FieldCondition(
                    key="protein_g",
                    range=Range(gte=float(min_protein))
                )
            )

        # --------------------------------------------------
        # Low sugar
        # Approved threshold:
        # sugar <= 5 g per 100 g
        # --------------------------------------------------

        if low_sugar is True:
            filters.append(
                FieldCondition(
                    key="sugar_g",
                    range=Range(lte=5.0)
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
        # 4. Search Qdrant
        # --------------------------------------------------

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding.tolist(),
            query_filter=query_filter,
            limit=top_k if top_k is not None else self.top_k,
            with_payload=True
        ).points

        # --------------------------------------------------
        # 5. Convert Qdrant results into dictionaries
        # --------------------------------------------------

        retrieved_products = []

        for result in results:

            retrieved_products.append(
                {
                    "product_id": result.payload.get("product_id"),
                    "product_name": result.payload.get("product_name"),
                    "brand": result.payload.get("brand"),
                    "category": result.payload.get("category"),
                    "subcategory": result.payload.get("subcategory"),
                    "price": result.payload.get("price"),
                    "rating": result.payload.get("rating"),
                    "protein_g": result.payload.get("protein_g"),
                    "sugar_g": result.payload.get("sugar_g"),
                    "score": result.score,
                    "document": result.payload.get("document")
                }
            )

        return retrieved_products