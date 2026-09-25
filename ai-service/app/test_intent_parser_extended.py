from app.genai.intent_parser import IntentParser

def print_result(query, result):
    print("=" * 90)
    print(f"QUERY: {query}")
    print(f"RESULT: {result}")
    print()


parser = IntentParser()


test_queries = [
    # Basic category
    "I want pasta",
    "show me pasta",
    "I need pasta",
    "give me pasta",

    # Price
    "pasta under 200",
    "pasta under rs. 300",
    "pasta below 500",
    "pasta less than 250",
    "pasta between 200 and 500",

    # Dietary
    "vegetarian pasta",
    "vegan pasta",
    "gluten free pasta",

    # Nutrition
    "high protein pasta",
    "low sugar pasta",
    "high protein vegetarian pasta",
    "vegan high protein pasta",
    "low sugar vegan pasta",

    # Combined filters
    "vegetarian high protein pasta under rs. 300",
    "vegan pasta under rs. 250",
    "gluten free pasta under 400",
    "high protein pasta below 300",

    # Natural language
    "I want healthy pasta",
    "I need something healthy",
    "show me something under 300",
    "I want healthy food under 500",
    "I want pasta for dinner",

    # Other products
    "I want rice",
    "show me milk",
    "I need coffee",
    "give me chips",
    "I want bread",
    "show me shampoo",
]


for query in test_queries:

    try:
        result = parser.parse(query)
        print_result(query, result)

    except Exception as e:

        print("=" * 90)
        print(f"QUERY: {query}")
        print(f"ERROR: {type(e).__name__}: {e}")
        print()