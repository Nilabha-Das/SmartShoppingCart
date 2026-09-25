from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType

class QdrantConnection:

    COLLECTION_NAME = "products"

    def __init__(self):
        self.client = QdrantClient(
            host="qdrant",
            port=6333
        ) 

    def create_collection(self):
        collections = self.client.get_collections()
        existing_collections = [
            collection.name
            for collection in collections.collections
        ]
        if self.COLLECTION_NAME not in existing_collections:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=384,
                    distance=Distance.COSINE
                )
            )
            print(
                f"Created Qdrant collection: "
                f"{self.COLLECTION_NAME}"
            )
        else:
            print(
                f"Qdrant collection already exists: "
                f"{self.COLLECTION_NAME}"
            )


    def create_payload_indexes(self):
        indexes = {
            "price": PayloadSchemaType.FLOAT,
            "protein_g": PayloadSchemaType.FLOAT,
            "sugar_g": PayloadSchemaType.FLOAT,
            "vegetarian": PayloadSchemaType.BOOL,
            "vegan": PayloadSchemaType.BOOL,
            "gluten_free": PayloadSchemaType.BOOL
        }
        for field_name, field_schema in indexes.items():
            self.client.create_payload_index(
                collection_name= self.COLLECTION_NAME,
                field_name=field_name,
                field_schema=field_schema
            )
            print(
                f"Created payload index: {field_name}"
            )
    def get_client(self):
        return self.client