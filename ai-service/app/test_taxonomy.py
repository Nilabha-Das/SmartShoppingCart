from app.rag.taxonomy_resolver import TaxonomyResolver

resolver = TaxonomyResolver()

tests = [
    "I want pasta",
    "I want high protein pasta",
    "I want vegetarian high protein pasta under rs. 300",
]

for query in tests:
    print("\n" + "=" * 70)
    print("Query:", query)

    result = resolver.resolve(
        user_query=query
    )

    print ("STATUS:", result["status"])
    print ("CATEGORY:", result["category"])
    print ("SUBCATEGORY:", result["subcategory"])
    print ("MATCHED_BY:", result["matched_by"])
    print ("CANDIDATES:", result["candidates"])