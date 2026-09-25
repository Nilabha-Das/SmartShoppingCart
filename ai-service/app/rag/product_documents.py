import pandas as pd

MASTER_PRODUCTS_PATH = "/app/data/phase1/master_products.csv"


class ProductDocumentStore:

    def __init__(self):
        self.products = pd.read_csv(MASTER_PRODUCTS_PATH)

    def create_product_document(self, row):
        return f"""
Product ID: {row['product_id']}
Product Name: {row['product_name']}
Brand: {row['brand']}
Category: {row['category']}
Subcategory: {row['subcategory']}
Product Type: {row['product_type']}

Price: ₹{row['price']}
Market Price: ₹{row['market_price']}
Rating: {row['rating']}

Description: {row['description']}

Nutrition per 100g:
Calories: {row['calories_kcal']} kcal
Protein: {row['protein_g']} g
Carbohydrates: {row['carbohydrates_g']} g
Sugar: {row['sugar_g']} g
Fat: {row['fat_g']} g
Saturated Fat: {row['saturated_fat_g']} g
Fiber: {row['fiber_g']} g
Sodium: {row['sodium_mg']} mg

Attributes:
Vegetarian: {row['vegetarian']}
Vegan: {row['vegan']}
Gluten Free: {row['gluten_free']}
Contains Milk: {row['contains_milk']}
Contains Nuts: {row['contains_nuts']}
Contains Soy: {row['contains_soy']}

Health Tags: {row['health_tags']}
""".strip()

    def get_documents(self):
        return [
            self.create_product_document(row)
            for _, row in self.products.iterrows()
        ]