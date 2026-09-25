import os
import joblib
import pandas as pd
from scipy.sparse import load_npz
from sklearn.metrics.pairwise import cosine_similarity


# Paths inside the Docker container
CONTENT_PRODUCTS_PATH = "/app/models/content_based/content_products.csv"
TFIDF_MATRIX_PATH = "/app/models/content_based/tfidf_matrix.npz"
TFIDF_VECTORIZER_PATH = "/app/models/content_based/tfidf_vectorizer.pkl"


class ContentBasedRecommender:

    def __init__(self):
        self.content_products = pd.read_csv(CONTENT_PRODUCTS_PATH)
        self.tfidf_matrix = load_npz(TFIDF_MATRIX_PATH)
        self.tfidf = joblib.load(TFIDF_VECTORIZER_PATH)

        self.product_to_index = pd.Series(
            self.content_products.index,
            index=self.content_products["product_id"]
        ).to_dict()

    def recommend_similar_products(self, product_id, n=10):

        if product_id not in self.product_to_index:
            return pd.DataFrame()

        product_index = self.product_to_index[product_id]

        similarity_scores = cosine_similarity(
            self.tfidf_matrix[product_index],
            self.tfidf_matrix
        ).flatten()

        similar_indices = similarity_scores.argsort()[::-1]

        recommendations = []

        for index in similar_indices:

            recommended_product_id = self.content_products.iloc[index]["product_id"]

            # Don't recommend the same product
            if recommended_product_id == product_id:
                continue

            recommendations.append({
                "product_id": recommended_product_id,
                "product_name": self.content_products.iloc[index]["product_name"],
                "content_score": float(similarity_scores[index])
            })

            if len(recommendations) >= n:
                break

        return pd.DataFrame(recommendations)