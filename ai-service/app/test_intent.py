from app.genai.intent_parser import IntentParser


parser = IntentParser()

tests = [
    "I want pasta",
    "I want high protein pasta",
    "I want vegetarian high protein pasta under rs. 300",
    "I want vegan pasta under rs. 250",
    "I want low sugar pasta",
]

for query in tests:

    print("\n" + "=" * 80)
    print("QUERY:", query)

    result = parser.parse(query)

    print("RESULT:")
    print(result.model_dump())