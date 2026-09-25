import json
from typing import Optional, Literal

from pydantic import BaseModel
from app.genai.llm import GroqLLM


class UserIntent(BaseModel):

    # ---------------------------------------------------------
    # User's actual shopping query
    # ---------------------------------------------------------

    query: str

    # ---------------------------------------------------------
    # Taxonomy fields
    #
    # These are kept in the schema for compatibility, but the
    # taxonomy resolver is the authoritative component for
    # category/subcategory resolution.
    # ---------------------------------------------------------

    category: Optional[str] = None
    subcategory: Optional[str] = None

    # ---------------------------------------------------------
    # Shopping constraints
    # ---------------------------------------------------------

    max_price: Optional[float] = None

    vegetarian: Optional[bool] = None
    vegan: Optional[bool] = None
    gluten_free: Optional[bool] = None

    high_protein: Optional[bool] = None
    low_sugar: Optional[bool] = None

    # ---------------------------------------------------------
    # User's purpose
    # ---------------------------------------------------------

    purpose: Optional[str] = None

    # ---------------------------------------------------------
    # High-level intent
    # ---------------------------------------------------------

    intent: Optional[
        Literal[
            "search",
            "purchase",
            "recommendation",
            "details",
            "nutrition",
            "cart",
            "navigation",
            "unknown"
        ]
    ] = None


class IntentParser:

    def __init__(self):

        self.llm = GroqLLM()

    def parse(
        self,
        user_message: str
    ) -> UserIntent:

        # ---------------------------------------------------------
        # Generate strict JSON schema
        # ---------------------------------------------------------

        schema = UserIntent.model_json_schema()

        schema["additionalProperties"] = False

        schema["required"] = list(
            schema["properties"].keys()
        )

        # ---------------------------------------------------------
        # Call Groq
        # ---------------------------------------------------------

        response = (
            self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are the intent extraction "
                            "system for a smart shopping cart. "

                            "Extract the user's shopping "
                            "intent and explicit constraints. "

                            "The taxonomy resolver is "
                            "responsible for deciding the "
                            "final product category and "
                            "subcategory from the user's "
                            "original message. "

                            "Do NOT invent taxonomy "
                            "categories or subcategories. "

                            "For category and subcategory, "
                            "return null unless the user "
                            "explicitly states a known "
                            "category or subcategory. "

                            "Examples: "

                            "For 'I want high protein pasta', "
                            "do not create a subcategory "
                            "called 'High Protein Pasta'. "

                            "For 'I want vegetarian high "
                            "protein pasta under 300', "
                            "extract vegetarian=true, "
                            "high_protein=true, and "
                            "max_price=300. "

                            "Do not treat dietary or "
                            "nutritional constraints as "
                            "taxonomy subcategories. "

                            "Extract only information "
                            "explicitly stated or strongly "
                            "implied by the user. "

                            "Do not invent price, dietary "
                            "constraints, health constraints, "
                            "category, or subcategory. "

                            "The intent field should normally "
                            "be one of: "
                            "search, purchase, recommendation, "
                            "details, nutrition, cart, "
                            "navigation, unknown. "

                            "If the user's intent cannot be "
                            "classified confidently, use "
                            "'unknown'."
                        )
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "user_intent",
                        "strict": True,
                        "schema": schema
                    }
                }
            )
        )

        # ---------------------------------------------------------
        # Parse JSON response
        # ---------------------------------------------------------

        content = (
            response
            .choices[0]
            .message
            .content
        )

        data = json.loads(content)

        intent = UserIntent.model_validate(
            data
        )

        # ---------------------------------------------------------
        # Ensure intent always has a value
        # ---------------------------------------------------------

        if intent.intent is None:
            intent.intent = "unknown"

        # ---------------------------------------------------------
        # IMPORTANT:
        #
        # TaxonomyResolver is authoritative for taxonomy.
        #
        # The LLM may produce values such as:
        #
        #   category = "pasta"
        #   subcategory = "High Protein Pasta"
        #
        # even when those are not actual taxonomy values.
        #
        # Therefore, for natural-language product concepts,
        # don't allow the LLM's generated taxonomy to override
        # the deterministic taxonomy resolver.
        #
        # The original user_message is still passed separately
        # to TaxonomyResolver by ShoppingSearchPipeline.
        # ---------------------------------------------------------

        if intent.category:
            intent.category = intent.category.strip()

        if intent.subcategory:
            intent.subcategory = intent.subcategory.strip()

        return intent