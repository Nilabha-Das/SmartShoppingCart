import pandas as pd
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from app.rag.product_documents import ProductDocumentStore
from app.rag.qdrant_client import QdrantConnection


BATCH_SIZE = 64
UPLOAD_BATCH_SIZE = 256
MODEL_NAME = "all-MiniLM-L6-v2"


def main():

    print("Loading product data...")

    document_store = ProductDocumentStore()
    products = document_store.products

    products = products.copy()

    products["product_name"] = products["product_name"].fillna("")
    products["brand"] = products["brand"].fillna("")
    products["description"] = products["description"].fillna("")
    products["rating"] = products["rating"].fillna(0.0)

    document_store.products = products

    documents = document_store.get_documents()

    print(f"Products loaded: {len(products)}")

    print("Loading embedding model...")

    model = SentenceTransformer(MODEL_NAME)

    qdrant = QdrantConnection()
    client = qdrant.get_client()

    collection_name = QdrantConnection.COLLECTION_NAME

    print(f"Indexing into collection: {collection_name}")

    total_products = len(products)

    for start in range(0, total_products, BATCH_SIZE):

        end = min(start + BATCH_SIZE, total_products)

        batch_documents = documents[start:end]

        print(
            f"Embedding products "
            f"{start + 1}-{end} / {total_products}"
        )

        embeddings = model.encode(
            batch_documents,
            show_progress_bar=False,
            normalize_embeddings=True
        )

        points = []

        for local_index, embedding in enumerate(embeddings):

            product_index = start + local_index
            row = products.iloc[product_index]

            payload = {
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "brand": row["brand"],
                "category": row["category"],
                "subcategory": row["subcategory"],
                "product_type": row["product_type"],
                "price": float(row["price"]),
                "market_price": float(row["market_price"]),
                "rating": float(row["rating"]),
                "description": row["description"],
                "calories_kcal": float(row["calories_kcal"]),
                "protein_g": float(row["protein_g"]),
                "carbohydrates_g": float(row["carbohydrates_g"]),
                "sugar_g": float(row["sugar_g"]),
                "fat_g": float(row["fat_g"]),
                "saturated_fat_g": float(row["saturated_fat_g"]),
                "fiber_g": float(row["fiber_g"]),
                "sodium_mg": float(row["sodium_mg"]),
                "vegetarian": bool(row["vegetarian"]),
                "vegan": bool(row["vegan"]),
                "gluten_free": bool(row["gluten_free"]),
                "contains_milk": bool(row["contains_milk"]),
                "contains_nuts": bool(row["contains_nuts"]),
                "contains_soy": bool(row["contains_soy"]),
                "health_tags": row["health_tags"],
                "document": batch_documents[local_index]
            }

            points.append(
                PointStruct(
                    id=product_index,
                    vector=embedding.tolist(),
                    payload=payload
                )
            )

        for upload_start in range(
            0,
            len(points),
            UPLOAD_BATCH_SIZE
        ):

            upload_end = min(
                upload_start + UPLOAD_BATCH_SIZE,
                len(points)
            )

            client.upsert(
                collection_name=collection_name,
                points=points[upload_start:upload_end]
            )

    print("Product indexing completed successfully.")

    collection_info = client.get_collection(collection_name)

    print(
        f"Points stored: "
        f"{collection_info.points_count}"
    )


if __name__ == "__main__":
    main()