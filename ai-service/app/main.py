
from fastapi import FastAPI, HTTPException, Query

from app.recommender.content_based import ContentBasedRecommender
from app.recommender.collaborative import CollaborativeRecommender
from app.recommender.hybrid import HybridRecommender
from app.rag.retriever import ProductRetriever
from app.pipeline.shopping_search import ShoppingSearchPipeline

from app.nutrition_safety import (
    NUTRITION_UNVERIFIED_MESSAGE,
    has_unverified_nutrition_constraint,
)

from app.dietary_safety import (
    DIETARY_UNVERIFIED_MESSAGE,
    has_unverified_dietary_constraint,
)


app = FastAPI(title="Smart Shopping Cart AI Service")


# --------------------------------------------------
# Recommendation components
# --------------------------------------------------

content_recommender = ContentBasedRecommender()
collaborative_recommender = CollaborativeRecommender()

hybrid_recommender = HybridRecommender(
    collaborative_recommender,
    content_recommender,
)


# --------------------------------------------------
# Retrieval and shopping pipeline
# --------------------------------------------------

rag_retriever = ProductRetriever(top_k=5)
shopping_pipeline = ShoppingSearchPipeline()


# --------------------------------------------------
# Basic endpoints
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "service": "Smart Shopping Cart AI Service",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# --------------------------------------------------
# Content-based recommendations
# --------------------------------------------------

@app.get("/recommend/content/{product_id}")
def recommend_content(
    product_id: str,
    n: int = Query(default=10, ge=1, le=100),
):
    recommendations = (
        content_recommender.recommend_similar_products(
            product_id,
            n,
        )
    )

    return {
        "product_id": product_id,
        "recommendations": recommendations.to_dict(
            orient="records"
        ),
    }


# --------------------------------------------------
# Collaborative recommendations
# --------------------------------------------------

@app.get("/recommend/collaborative/{customer_id}")
def recommend_collaborative(
    customer_id: str,
    n: int = Query(default=10, ge=1, le=100),
):
    recommendations = collaborative_recommender.recommend(
        customer_id,
        n_candidates=n,
    )

    return {
        "customer_id": customer_id,
        "recommendations": recommendations or [],
    }


@app.get("/recommend/hybrid/{customer_id}")
def recommend_hybrid(
    customer_id: str,
    n: int = Query(default=10, ge=1, le=100),
):
    recommendations = hybrid_recommender.recommend(
        customer_id,
        n=n,
    )

    return {
        "customer_id": customer_id,
        "recommendations": recommendations or [],
    }

# --------------------------------------------------
# Direct RAG retrieval
# --------------------------------------------------

@app.get("/rag/retrieve")
def retrieve_products(
    query: str = Query(..., min_length=1),
    top_k: int = Query(default=5, ge=1, le=100),
    max_price: float | None = Query(default=None, gt=0),
    vegetarian: bool | None = None,
    min_protein: float | None = Query(default=None, ge=0),
):
    # Block nutrition-based filtering while the nutrition
    # dataset remains unverified.
    if has_unverified_nutrition_constraint(
        min_protein=min_protein,
    ):
        raise HTTPException(
            status_code=503,
            detail=NUTRITION_UNVERIFIED_MESSAGE,
        )

    # Block dietary filtering while dietary data remains
    # unverified.
    if has_unverified_dietary_constraint(
        vegetarian=vegetarian,
    ):
        raise HTTPException(
            status_code=503,
            detail=DIETARY_UNVERIFIED_MESSAGE,
        )

    results = rag_retriever.retrieve(
        query=query,
        max_price=max_price,
        vegetarian=None,
        min_protein=None,
        top_k=top_k,
    )

    # Return only approved catalog information.
    # Do not expose unverified nutrition, dietary,
    # allergen, or health-tag attributes.
    safe_fields = (
        "product_id",
        "product_name",
        "brand",
        "category",
        "subcategory",
        "price",
        "rating",
        "score",
    )

    safe_results = [
        {
            key: product[key]
            for key in safe_fields
            if key in product
        }
        for product in results
    ]

    return {
        "query": query,
        "filters": {
            "max_price": max_price,
            "vegetarian": vegetarian,
            "min_protein": min_protein,
        },
        "results": safe_results,
    }


# --------------------------------------------------
# Shopping search
# --------------------------------------------------

@app.get("/shopping/search")
def shopping_search(
    message: str = Query(..., min_length=1),
    session_id: str = Query(default="default", min_length=1),
    ask_preferences: bool = False,
):
    result = shopping_pipeline.search(
        user_message=message,
        session_id=session_id,
        ask_preferences=ask_preferences,
    )

    if result["status"] in {
        "invalid_session",
        "invalid_message",
    }:
        raise HTTPException(
            status_code=400,
            detail=result,
        )

    return result


# --------------------------------------------------
# Shopping preference answers
# --------------------------------------------------

@app.post("/shopping/preferences/answer")
def answer_shopping_preference(
    session_id: str = Query(..., min_length=1),
    preference: str = Query(..., min_length=1),
    answer: str = Query(...),
):
    result = shopping_pipeline.answer_preference(
        session_id=session_id,
        preference=preference,
        answer=answer,
    )

    if result["status"] in {
        "invalid_session",
        "invalid_preference",
        "invalid_answer",
        "no_pending_question",
        "unexpected_preference",
    }:
        raise HTTPException(
            status_code=400,
            detail=result,
        )

    return result
