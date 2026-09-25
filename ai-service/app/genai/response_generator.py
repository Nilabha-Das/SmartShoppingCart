from app.genai.llm import GroqLLM


class ResponseGenerator:
    def __init__(self):
        self.llm = GroqLLM()

    def generate(self, user_message, intent, products):
        if not products:
            return (
                "I couldn't find any products matching your request. "
                "Try changing your category, budget, or other requirements."
            )

        product_data = []

        for product in products:
            product_data.append({
                "product_id": product.get("product_id"),
                "product_name": product.get("product_name"),
                "brand": product.get("brand"),
                "category": product.get("category"),
                "subcategory": product.get("subcategory"),
                "price": product.get("price"),
                "rating": product.get("rating"),
                "protein_g": product.get("protein_g"),
                "sugar_g": product.get("sugar_g"),
                "document": product.get("document")
            })

        prompt = f"""
You are a grounded shopping assistant.

USER REQUEST:
{user_message}

PARSED INTENT:
{intent if isinstance(intent, dict) else intent.model_dump()}

RETRIEVED PRODUCTS:
{product_data}

Your task is ONLY to present the retrieved products clearly.

STRICT RULES:

1. Use ONLY the products provided in RETRIEVED PRODUCTS.
2. Do NOT invent products.
3. Do NOT remove products because you personally think another product
   is better.
4. Do NOT select only one product when multiple products are provided.
5. Present ALL retrieved products unless there is a technical reason
   that makes a product impossible to display.
6. Do NOT change prices, nutrition values, ratings, or attributes.
7. Do NOT infer attributes from the product name.
8. If the stored data says something different from the product name,
   report the stored data.
9. Do NOT claim that a product is vegetarian, vegan, gluten-free,
   high-protein, etc. unless that information is explicitly present
   in the supplied product data.
10. Keep the answer concise and useful.
11. If the user specifies a constraint such as price, vegetarian,
    vegan, gluten-free, high-protein, or low-sugar, mention that
    constraint in the introduction.
12. When nutrition information is available, show protein and sugar
    when relevant to the user's request.
13. Do not rank, score, or declare a "best" product.
14. Do not recommend one product over another.
15. The retrieval system has already applied the user's hard filters.
    Do not reinterpret or change those filters.

FORMAT:

Start with one short sentence describing what was found.

Then display ALL retrieved products in a Markdown table.

Use these columns when the information is available:

Product | Brand | Price | Protein/100g | Sugar/100g | Rating

After the table, add at most one short factual sentence.

Do not add unnecessary explanations.
"""

        response = self.llm.generate(prompt)

        return response

    def generate_clarification(
        self,
        user_message,
        intent,
        taxonomy
    ):
        prompt = f"""
You are a shopping assistant helping a customer clarify an ambiguous
product request.

User request:
{user_message}

Parsed intent:
{intent if isinstance(intent, dict) else intent.model_dump()}

Detected taxonomy:
{taxonomy}

Ask ONE short clarification question that helps the customer specify
what they want.

Do not recommend a product.
Do not invent categories.
Use only the taxonomy information supplied above.
"""

        return self.llm.generate(prompt)