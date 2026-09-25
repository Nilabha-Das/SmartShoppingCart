from app.pipeline.shopping_search import ShoppingSearchPipeline

pipeline = ShoppingSearchPipeline()

tests = [
    "I want pasta",
    "I want high protein pasta",
    "I want vegetarian high protein pasta under rs. 300",
]

for query in tests:
    print("\n" + "=" * 80)
    print("Query:", query)

    result = pipeline.search(query)

    print ("STATUS:", result.get("status"))
    print ("INTENT:", result.get("intent"))
    print ("TAXONOMY:", result.get("taxonomy"))
    print ("PRODUCT COUNT:", len(result.get("products", [])))
    print ("RESPONSE:", result.get("response"))