from fastapi import FastAPI
from app.recommender.content_based import ContentBasedRecommender
from app.recommender.collaborative import CollaborativeRecommender
from app.recommender.hybrid import HybridRecommender
from app.rag.retriever import ProductRetriever

app = FastAPI(title="Smart Shopping Cart AI Service")

content_recommender = ContentBasedRecommender();
collaborative_recommender = CollaborativeRecommender();
hybrid_recommender = HybridRecommender(
    content_recommender, collaborative_recommender
);
rag_retriever = ProductRetriever(top_k = 5)

@app.get("/")
def root():
    return {
        "service": "Smart Shopping Cart AI Service",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

@app.get("/recommend/content/{product_id}")
def recommend_content(product_id:str, n: int = 10):
    recommendations = content_recommender.recommend_similar_products(
        product_id, n
    )

    return {
        "product_id": product_id,
        "recommendations":recommendations.to_dict(orient="records")
    }

@app.get("/recommend/collaborative/{customer_id}")
def recommend_collaborative(customer_id:str, n: int = 10):
    recommendations = collaborative_recommender.recommend(
        customer_id, n_candidates=n
    )

    if recommendations.empty:
        return {
            "customer_id":customer_id,
            "recommendations":[]
        }

    return {
        "customer_id": customer_id,
        "recommendations":recommendations.to_dict(orient="records")
    }

@app.get("/recommend/hybrid/{customer_id}")
def recommend_hybrid(customer_id:str, n: int = 10):
    recommendations = hybrid_recommender.recommend(
        customer_id, n=n
    )

    if recommendations.empty:
        return {
            "customer_id":customer_id,
            "recommendations":[]
        }

    return {
        "customer_id": customer_id,
        "recommendations":recommendations.to_dict(orient="records")
    }

@app.get("/rag/retrieve")
def retrieve_products(query: str, top_k: int = 5, max_price: float = None, vegetarian : bool = None, min_protein: float = None):
    
    results = rag_retriever.retrieve(
        query=query,
        max_price=max_price, 
        vegetarian=vegetarian, 
        min_protein=min_protein,
        top_k=top_k
    )
    return {
        "query": query,
        "filters": {
            "max_price": max_price,
            "vegetarian": vegetarian,
            "min_protein": min_protein
        },
        "results": results
    }