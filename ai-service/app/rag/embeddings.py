from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

class ProductEmbeddingModel:
    def __init__(self):
        self.model = SentenceTransformer(MODEL_NAME)

    def encode(self, documents):
        return self.model.encode(
            documents, show_progress_bar=True,normalize_embeddings=True
        )