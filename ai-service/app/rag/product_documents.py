
import os
import pandas as pd


DEFAULT_MASTER_PRODUCTS_PATH = "/app/data/phase1/master_products.csv"


class ProductDocumentStore:
    """
    Builds product documents for semantic search.

    Only catalog information is included in the embedded text.
    Unverified nutrition, dietary, allergen, and health-tag
    fields are deliberately excluded.
    """

    def __init__(self, products_path=None):
        self.products_path = (
            products_path
            or os.getenv(
                "MASTER_PRODUCTS_PATH",
                DEFAULT_MASTER_PRODUCTS_PATH,
            )
        )

        print(f"Loading products from: {self.products_path}")
        self.products = pd.read_csv(self.products_path)

    @staticmethod
    def _text(value):
        """Return clean text, using an empty string for missing values."""
        if pd.isna(value):
            return ""

        return str(value).strip()

    @staticmethod
    def _display_number(value):
        """Return a readable number or an explicit unavailable label."""
        if pd.isna(value):
            return "Not available"

        return str(value)

    def create_product_document(self, row):
        """
        Create an embedding document using catalog fields only.

        Excluded fields:
        - Nutrition values
        - Dietary flags
        - Allergen flags
        - Health tags
        """

        product_id = self._text(row.get("product_id"))
        product_name = self._text(row.get("product_name"))
        brand = self._text(row.get("brand"))
        category = self._text(row.get("category"))
        subcategory = self._text(row.get("subcategory"))
        product_type = self._text(row.get("product_type"))
        description = self._text(row.get("description"))

        price = self._display_number(row.get("price"))
        market_price = self._display_number(
            row.get("market_price")
        )
        rating = self._display_number(row.get("rating"))

        return f"""
Product ID: {product_id}
Product Name: {product_name}
Brand: {brand}
Category: {category}
Subcategory: {subcategory}
Product Type: {product_type}
Price: {price}
Market Price: {market_price}
Rating: {rating}
Description: {description}
""".strip()

    def get_documents(self):
        """Return one catalog-only embedding document per product."""
        return [
            self.create_product_document(row)
            for _, row in self.products.iterrows()
        ]
