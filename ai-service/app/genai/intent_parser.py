import json
import re
from typing import Optional, Literal

from pydantic import BaseModel
from app.genai.llm import GroqLLM


class UserIntent(BaseModel):

    query: str

    category: Optional[str] = None
    subcategory: Optional[str] = None

    max_price: Optional[float] = None

    vegetarian: Optional[bool] = None
    vegan: Optional[bool] = None
    gluten_free: Optional[bool] = None

    high_protein: Optional[bool] = None
    low_sugar: Optional[bool] = None

    purpose: Optional[str] = None

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

    def _fast_parse(self, user_message: str) -> Optional[UserIntent]:
        """
        Deterministic parser for simple shopping constraint queries.

        Returns None when the query is too ambiguous/complex and
        should be handled by the LLM.
        """

        text = user_message.lower().strip()

        # Only activate this fast path for clearly simple
        # shopping/search queries.
        if not text:
            return None

        # These are the constraint patterns already supported
        # by ConstraintNormalizer.
        constraint_patterns = [
            r"\bhigh[- ]?protein\b",
            r"\bprotein[- ]?(?:rich|packed|heavy)\b",
            r"\bprotein snacks?\b",
            r"\bprotein foods?\b",
            r"\blow[- ]?sugar\b",
            r"\bvegetarian\b",
            r"\bvegan\b",
            r"\bgluten[- ]?free\b",
            r"\b(?:under|below|less than|within|upto|up to)\s*₹?\s*\d+(?:\.\d+)?\b",
        ]

        has_constraint = any(
            re.search(pattern, text)
            for pattern in constraint_patterns
        )

        if not has_constraint:
            return None

        # Avoid taking over complex conversational queries.
        complex_patterns = [
            r"\bwhy\b",
            r"\bhow\b",
            r"\bwhich one\b",
            r"\brecommend\b",
            r"\bsuggest\b",
            r"\bcompare\b",
            r"\btell me\b",
            r"\bexplain\b",
            r"\bwhat is\b",
            r"\bshow me the best\b",
        ]

        if any(re.search(pattern, text) for pattern in complex_patterns):
            return None

        return UserIntent(
            query=user_message,
            category=None,
            subcategory=None,
            max_price=None,
            vegetarian=None,
            vegan=None,
            gluten_free=None,
            high_protein=None,
            low_sugar=None,
            purpose=None,
            intent="search",
        )

    def parse(
        self,
        user_message: str
    ) -> UserIntent:

        # ---------------------------------------------------------
        # FAST PATH
        # ---------------------------------------------------------
        #
        # Simple constraint-based shopping queries do not require
        # an LLM. ConstraintNormalizer will extract the actual
        # constraints immediately after this method returns.
        #
        # This avoids unnecessary Groq calls and rate limits.
        # ---------------------------------------------------------

        fast_intent = self._fast_parse(user_message)

        if fast_intent is not None:
            return fast_intent

        # ---------------------------------------------------------
        # LLM FALLBACK
        # ---------------------------------------------------------

        schema = UserIntent.model_json_schema()

        schema["additionalProperties"] = False

        schema["required"] = list(
            schema["properties"].keys()
        )

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

        content = (
            response
            .choices[0]
            .message
            .content
        )

        data = json.loads(content)

        intent = UserIntent.model_validate(data)

        if intent.intent is None:
            intent.intent = "unknown"

        if intent.category:
            intent.category = intent.category.strip()

        if intent.subcategory:
            intent.subcategory = intent.subcategory.strip()

        return intent