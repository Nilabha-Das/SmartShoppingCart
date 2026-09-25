from app.genai.intent_parser import IntentParser
from app.rag.taxonomy_resolver import TaxonomyResolver
from app.rag.retriever import ProductRetriever
from app.genai.response_generator import ResponseGenerator

class ShoppingSearchPipeline:

    def __init__(self):
        self.intent_parser = IntentParser()
        self.retriever = ProductRetriever(top_k=5)
        self.response_generator = ResponseGenerator()
        self.taxonomy_resolver = TaxonomyResolver()

    def search(self, user_message: str):

        # Step 1: Understand the user's request
        intent = self.intent_parser.parse(user_message)

        taxonomy = self.taxonomy_resolver.resolve(
            user_query=user_message,
            category = intent.category, 
            subcategory = intent.subcategory
        )

        if taxonomy["status"] == "ambiguous":
            clarification = self.response_generator.generate_clarification(
                user_message=user_message,
                intent=intent.model_dump(),
                taxonomy=taxonomy
            )
            return {
                "status": "ambiguous",
                "intent": intent.model_dump(),
                "taxonomy": taxonomy,
                "products": [],
                "response": clarification

            }

        if taxonomy["status"] == "unknown":
            return {
                "status": "unknown",
                "intent": intent.model_dump(),
                "taxonomy": taxonomy,
                "products": [],
                "response": None
            }

        # Step 2: Retrieve products using the extracted constraints
        products = self.retriever.retrieve(
            query=intent.query,
            category=taxonomy.get("category"),
            subcategory=taxonomy.get("subcategory"),
            max_price=intent.max_price,
            vegetarian=intent.vegetarian,
            vegan=intent.vegan,
            gluten_free=intent.gluten_free,
            high_protein=intent.high_protein,
            low_sugar=intent.low_sugar
        )

        response = self.response_generator.generate(
            user_message=user_message,
            intent=intent.model_dump(),
            products=products
        )

        return {
            "status": "resolved",
            "intent": intent.model_dump(),
            "taxonomy": taxonomy,
            "products": products,
            "response": response
        }