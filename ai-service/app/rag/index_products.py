
import os
import time
from typing import Any

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from qdrant_client.models import (
    Distance,
    PointIdsList,
    PointStruct,
    VectorParams,
)

from app.rag.product_documents import ProductDocumentStore
from app.rag.qdrant_client import QdrantConnection


# ============================================================
# Configuration
# ============================================================

BATCH_SIZE = 64
UPLOAD_BATCH_SIZE = 64
SCROLL_BATCH_SIZE = 256

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_SIZE = 384

COLLECTION_NAME = "products"
STAGING_COLLECTION_NAME = "products_staging"

DATA_PATH = os.getenv(
    "PRODUCTS_CSV_PATH",
    "/app/data/phase1/master_products.csv",
)

REQUIRED_COLUMNS = [
    "product_id",
    "product_name",
    "brand",
    "category",
    "subcategory",
    "product_type",
    "price",
    "market_price",
    "rating",
    "description",
]


# ============================================================
# Product validation
# ============================================================

def validate_products(products: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and normalize catalog data before indexing.

    Nutrition, dietary, allergen and health-tag columns are
    deliberately excluded from the indexed payload.
    """

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in products.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required product columns: {missing_columns}"
        )

    if products.empty:
        raise ValueError("The product dataset is empty.")

    products = products.copy()

    # Normalize product IDs.
    products["product_id"] = (
        products["product_id"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    if (products["product_id"] == "").any():
        raise ValueError("Some products have missing product IDs.")

    if products["product_id"].duplicated().any():
        duplicates = (
            products.loc[
                products["product_id"].duplicated(keep=False),
                "product_id",
            ]
            .unique()
            .tolist()
        )

        raise ValueError(
            f"Duplicate product IDs found: {duplicates[:10]}"
        )

    # Normalize text fields.
    text_columns = [
        "product_name",
        "brand",
        "category",
        "subcategory",
        "product_type",
        "description",
    ]

    for column in text_columns:
        products[column] = (
            products[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    # Keep missing names identifiable without modifying the CSV.
    missing_names = products["product_name"] == ""

    products.loc[missing_names, "product_name"] = (
        "Unnamed product ("
        + products.loc[missing_names, "product_id"]
        + ")"
    )

    # Validate prices.
    for column in ["price", "market_price"]:
        products[column] = pd.to_numeric(
            products[column],
            errors="coerce",
        )

        invalid = (
            products[column].isna()
            | ~np.isfinite(products[column])
            | (products[column] < 0)
        )

        if invalid.any():
            invalid_ids = products.loc[
                invalid, "product_id"
            ].head(10).tolist()

            raise ValueError(
                f"Invalid values in '{column}'. "
                f"Example product IDs: {invalid_ids}"
            )

    # Ratings may be missing, but present values must be finite.
    products["rating"] = pd.to_numeric(
        products["rating"],
        errors="coerce",
    )

    invalid_ratings = (
        products["rating"].notna()
        & ~np.isfinite(products["rating"])
    )

    if invalid_ratings.any():
        raise ValueError("Non-finite product ratings were found.")

    print(f"Validated {len(products):,} products.")

    return products


# ============================================================
# Document and payload creation
# ============================================================

def create_document_store() -> ProductDocumentStore:
    """Create the catalog document formatter."""

    return ProductDocumentStore()



def create_document(
    document_store: ProductDocumentStore,
    row: pd.Series,
) -> str:
    """Build a searchable document for one product."""
    return document_store.create_product_document(row)

    # Support the ProductDocumentStore interface used by the
    # existing project. If its method has a different name,
    # keep the method name consistent with that implementation.
    if hasattr(document_store, "create_document"):
        return document_store.create_document(row)

    if hasattr(document_store, "build_document"):
        return document_store.build_document(row)

    if hasattr(document_store, "product_to_document"):
        return document_store.product_to_document(row)

    raise AttributeError(
        "ProductDocumentStore must expose create_document(row), "
        "build_document(row), or product_to_document(row)."
    )


def create_payload(
    row: pd.Series,
    document: str,
) -> dict[str, Any]:
    """
    Create a safe catalog-only Qdrant payload.

    Do not add nutrition values, dietary/allergen flags or
    health tags until those fields have been independently
    validated.
    """

    def safe_text(value: Any) -> str:
        if value is None or pd.isna(value):
            return ""
        return str(value).strip()

    def safe_number(value: Any) -> float | None:
        if value is None or pd.isna(value):
            return None

        number = float(value)

        if not np.isfinite(number):
            return None

        return number

    rating = safe_number(row.get("rating"))

    return {
        "product_id": safe_text(row.get("product_id")),
        "product_name": safe_text(row.get("product_name")),
        "brand": safe_text(row.get("brand")),
        "category": safe_text(row.get("category")),
        "subcategory": safe_text(row.get("subcategory")),
        "product_type": safe_text(row.get("product_type")),
        "price": safe_number(row.get("price")),
        "market_price": safe_number(row.get("market_price")),
        "rating": rating,
        "description": safe_text(row.get("description")),
        "document": document,
    }


# ============================================================
# Collection management
# ============================================================

def get_client():
    """Get the project's configured Qdrant client."""

    connection = QdrantConnection()

    if hasattr(connection, "get_client"):
        return connection.get_client()

    if hasattr(connection, "client"):
        return connection.client

    raise AttributeError(
        "QdrantConnection must expose get_client() or client."
    )


def collection_exists(client, collection_name: str) -> bool:
    collections = client.get_collections().collections

    return any(
        collection.name == collection_name
        for collection in collections
    )


def create_collection(client, collection_name: str) -> None:
    """Create a collection if it does not already exist."""

    if collection_exists(client, collection_name):
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )

    print(f"Created collection: {collection_name}")


# ============================================================
# Resumable staging index
# ============================================================

def get_existing_point_ids(
    client,
    collection_name: str,
) -> set[int]:
    """Read existing point IDs from a collection."""

    existing_ids: set[int] = set()
    offset = None

    while True:
        records, offset = client.scroll(
            collection_name=collection_name,
            limit=SCROLL_BATCH_SIZE,
            offset=offset,
            with_payload=False,
            with_vectors=False,
        )

        for record in records:
            try:
                existing_ids.add(int(record.id))
            except (TypeError, ValueError):
                raise RuntimeError(
                    "The staging collection contains a non-integer "
                    f"point ID: {record.id!r}"
                )

        if offset is None:
            break

    return existing_ids


def build_staging_collection(
    client,
    model: SentenceTransformer,
    products: pd.DataFrame,
    documents: list[str],
) -> None:
    """
    Build or resume the staging collection.

    Completed batches are skipped. If an upload fails partway
    through a batch, rerunning this script safely upserts the
    missing or repeated IDs.
    """

    if not collection_exists(client, STAGING_COLLECTION_NAME):
        create_collection(client, STAGING_COLLECTION_NAME)
        existing_ids: set[int] = set()
        print("Created a new staging collection.")
    else:
        print("Resuming existing staging collection...")

        existing_ids = get_existing_point_ids(
            client,
            STAGING_COLLECTION_NAME,
        )

        print(
            f"Existing staged points: {len(existing_ids):,}"
        )

    total_products = len(products)

    try:
        for start in range(0, total_products, BATCH_SIZE):
            end = min(start + BATCH_SIZE, total_products)

            expected_batch_ids = set(range(start, end))

            # Skip batches only when every expected point exists.
            if expected_batch_ids.issubset(existing_ids):
                print(
                    f"Skipping completed batch "
                    f"{start + 1}-{end}/{total_products}"
                )
                continue

            print(
                f"Embedding products "
                f"{start + 1}-{end}/{total_products}"
            )

            batch_documents = documents[start:end]

            embeddings = model.encode(
                batch_documents,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )

            points = []

            for local_index, embedding in enumerate(embeddings):
                product_index = start + local_index

                row = products.iloc[product_index]
                document = batch_documents[local_index]

                points.append(
                    PointStruct(
                        id=product_index,
                        vector=embedding.tolist(),
                        payload=create_payload(row, document),
                    )
                )

            # Smaller uploads reduce the impact of connection drops.
            for upload_start in range(
                0,
                len(points),
                UPLOAD_BATCH_SIZE,
            ):
                upload_end = min(
                    upload_start + UPLOAD_BATCH_SIZE,
                    len(points),
                )

                upload_points = points[upload_start:upload_end]

                # Retry transient connection failures.
                last_error = None

                for attempt in range(1, 4):
                    try:
                        client.upsert(
                            collection_name=STAGING_COLLECTION_NAME,
                            points=upload_points,
                            wait=True,
                        )

                        last_error = None
                        break

                    except Exception as error:
                        last_error = error

                        if attempt < 3:
                            wait_seconds = attempt * 2

                            print(
                                f"Upload failed "
                                f"(attempt {attempt}/3): {error}"
                            )

                            print(
                                f"Retrying in {wait_seconds} seconds..."
                            )

                            time.sleep(wait_seconds)

                if last_error is not None:
                    raise last_error

            existing_ids.update(expected_batch_ids)

        # Confirm the complete staging index before touching
        # the active collection.
        staging_info = client.get_collection(
            STAGING_COLLECTION_NAME
        )

        actual_count = staging_info.points_count

        if actual_count != total_products:
            raise RuntimeError(
                "Staging index is incomplete: "
                f"expected {total_products:,} points, "
                f"got {actual_count:,}. "
                "The active collection has not been refreshed."
            )

        print(
            f"Staging index verified: {actual_count:,} points."
        )

    except Exception:
        print(
            "\nStaging build interrupted. Existing staged points "
            "have been preserved. Fix the underlying problem and "
            "rerun the indexer to resume."
        )
        raise


# ============================================================
# Refresh active collection
# ============================================================


def refresh_active_collection(client) -> None:
    """
    Copy verified staging points into the active collection.
    Convert Qdrant Record objects to PointStruct objects before
    uploading them.
    """

    create_collection(client, COLLECTION_NAME)

    staging_info = client.get_collection(
        STAGING_COLLECTION_NAME
    )
    expected_count = staging_info.points_count

    print(
        f"Refreshing active collection with "
        f"{expected_count:,} staged points..."
    )

    offset = None
    copied_count = 0

    while True:
        records, offset = client.scroll(
            collection_name=STAGING_COLLECTION_NAME,
            limit=SCROLL_BATCH_SIZE,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )

        if records:
            points = []

            for record in records:
                if record.vector is None:
                    raise RuntimeError(
                        f"Missing vector for point {record.id}"
                    )

                points.append(
                    PointStruct(
                        id=record.id,
                        vector=record.vector,
                        payload=record.payload or {},
                    )
                )

            client.upsert(
                collection_name=COLLECTION_NAME,
                points=points,
                wait=True,
            )

            copied_count += len(points)

            print(
                f"Copied {copied_count:,}/"
                f"{expected_count:,} staged points"
            )

        if offset is None:
            break

    # Remove stale IDs left over from any previous active index.
    staged_ids = get_existing_point_ids(
        client,
        STAGING_COLLECTION_NAME,
    )
    active_ids = get_existing_point_ids(
        client,
        COLLECTION_NAME,
    )

    stale_ids = active_ids - staged_ids

    if stale_ids:
        stale_list = list(stale_ids)

        print(
            f"Removing {len(stale_list):,} stale active points..."
        )

        for start in range(
            0,
            len(stale_list),
            UPLOAD_BATCH_SIZE,
        ):
            batch_ids = stale_list[
                start:start + UPLOAD_BATCH_SIZE
            ]

            client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=PointIdsList(points=batch_ids),
                wait=True,
            )

    # Verify before allowing the caller to delete staging.
    active_info = client.get_collection(COLLECTION_NAME)

    if active_info.points_count != expected_count:
        raise RuntimeError(
            "Active collection refresh is incomplete: "
            f"expected {expected_count:,} points, "
            f"got {active_info.points_count:,}. "
            "The staging collection has been preserved. "
            "Rerun the indexer to retry."
        )

    print(
        f"Active collection verified: "
        f"{active_info.points_count:,} points."
    )


# ============================================================
# Main
# ============================================================

def main() -> None:
    print("=" * 60)
    print("PRODUCT INDEXING")
    print("=" * 60)

    # 1. Load product data.
    print(f"Loading products from: {DATA_PATH}")

    products = pd.read_csv(DATA_PATH)

    print(f"Loaded {len(products):,} product rows.")

    # 2. Validate catalog fields.
    products = validate_products(products)

    # 3. Build searchable documents.
    document_store = create_document_store()

    print("Building searchable product documents...")

    documents = [
        create_document(document_store, row)
        for _, row in products.iterrows()
    ]

    if len(documents) != len(products):
        raise RuntimeError(
            "The number of generated documents does not match "
            "the number of products."
        )

    if any(
        not isinstance(document, str) or not document.strip()
        for document in documents
    ):
        raise ValueError(
            "One or more products have empty searchable documents."
        )

    print(f"Prepared {len(documents):,} documents.")

    # 4. Load embedding model.
    print(f"Loading embedding model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    embedding_dimension = model.get_sentence_embedding_dimension()

    if embedding_dimension != VECTOR_SIZE:
        raise RuntimeError(
            f"Expected {VECTOR_SIZE}-dimensional embeddings, "
            f"got {embedding_dimension}."
        )

    print(
        f"Embedding model loaded. Dimension: "
        f"{embedding_dimension}"
    )

    # 5. Connect to Qdrant.
    client = get_client()

    # 6. Build or resume staging.
    build_staging_collection(
        client=client,
        model=model,
        products=products,
        documents=documents,
    )

    # 7. Refresh active collection only after staging is verified.
    refresh_active_collection(client)

    # 8. Delete staging only after successful active verification.
    client.delete_collection(STAGING_COLLECTION_NAME)

    print("Removed staging collection.")

    print("=" * 60)
    print("PRODUCT INDEXING COMPLETED SUCCESSFULLY")
    print(f"Indexed products: {len(products):,}")
    print(f"Active collection: {COLLECTION_NAME}")
    print("=" * 60)


if __name__ == "__main__":
    main()
