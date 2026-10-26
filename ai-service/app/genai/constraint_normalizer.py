
import re


class ConstraintNormalizer:

    @staticmethod
    def normalize(intent, original_query: str):
        """
        Deterministically normalize important shopping constraints
        while preserving the existing UserIntent Pydantic object.
        """

        query = original_query.lower().strip()

        # HIGH PROTEIN
        protein_patterns = [
            r"\bhigh[-\s]?protein\b",
            r"\bprotein[-\s]?(rich|packed|heavy)\b",
            r"\bprotein\s+snacks?\b",
            r"\bprotein\s+foods?\b",
            r"\bhigh\s+protein\s+foods?\b",
        ]

        if any(re.search(pattern, query) for pattern in protein_patterns):
            intent.high_protein = True

        # LOW SUGAR
        low_sugar_patterns = [
            r"\blow[-\s]?sugar\b",
            r"\bless\s+sugar\b",
            r"\blow\s+in\s+sugar\b",
            r"\bsugar[-\s]?free\b",
            r"\bno\s+added\s+sugar\b",
        ]

        if any(re.search(pattern, query) for pattern in low_sugar_patterns):
            intent.low_sugar = True

        # VEGETARIAN
        vegetarian_patterns = [
            r"\bvegetarian\b",
            r"\bveg\b",
            r"\bvegetarian[-\s]?only\b",
        ]

        if any(re.search(pattern, query) for pattern in vegetarian_patterns):
            intent.vegetarian = True

        # VEGAN
        vegan_patterns = [
            r"\bvegan\b",
            r"\bvegan[-\s]?only\b",
        ]

        if any(re.search(pattern, query) for pattern in vegan_patterns):
            intent.vegan = True

        # GLUTEN FREE
        gluten_free_patterns = [
            r"\bgluten[-\s]?free\b",
            r"\bwithout\s+gluten\b",
            r"\bgluten\s+free\s+foods?\b",
        ]

        if any(re.search(pattern, query) for pattern in gluten_free_patterns):
            intent.gluten_free = True

        # MAX PRICE
        price_patterns = [
            r"(?:under|below|less\s+than|within|upto|up\s+to)\s*[₹rs\.]*\s*(\d+(?:\.\d+)?)",
            r"[₹rs\.]+\s*(\d+(?:\.\d+)?)\s*(?:or\s+less)?",
        ]

        for pattern in price_patterns:
            match = re.search(pattern, query)

            if match:
                try:
                    intent.max_price = float(match.group(1))
                    break
                except ValueError:
                    pass

        return intent

    @staticmethod
    def clean_search_query(original_query: str) -> str:
        """
        Remove recognized constraints from the semantic search text.

        The original user message and parsed intent remain unchanged.
        Budget constraints are handled separately through max_price.
        """

        query = original_query.lower().strip()

        # Remove budget phrases.
        price_patterns = [
            r"\b(?:under|below|less than|within|upto|up to)\s*"
            r"(?:₹|rs\.?|rupees?)?\s*\d+(?:\.\d+)?\s*"
            r"(?:rupees?|rs\.?)?\b",

            r"(?:₹|rs\.?|rupees?)\s*\d+(?:\.\d+)?\b",
        ]

        for pattern in price_patterns:
            query = re.sub(
                pattern,
                " ",
                query,
                flags=re.IGNORECASE,
            )

        # Remove nutrition and dietary modifiers.
        constraint_patterns = [
            r"\bhigh[-\s]?protein\b",
            r"\bprotein[-\s]?(?:rich|packed|heavy)\b",
            r"\bprotein\s+foods?\b",
            r"\bprotein\s+snacks?\b",
            r"\blow[-\s]?sugar\b",
            r"\bless\s+sugar\b",
            r"\blow\s+in\s+sugar\b",
            r"\bsugar[-\s]?free\b",
            r"\bno\s+added\s+sugar\b",
            r"\bgluten[-\s]?free\b",
            r"\bwithout\s+gluten\b",
            r"\bvegetarian(?:[-\s]?only)?\b",
            r"\bvegan(?:[-\s]?only)?\b",
        ]

        for pattern in constraint_patterns:
            query = re.sub(
                pattern,
                " ",
                query,
                flags=re.IGNORECASE,
            )

        # Remove common conversational filler.
        filler_patterns = [
            r"\bplease\b",
            r"\bshow me\b",
            r"\bfind me\b",
            r"\bi want\b",
            r"\bi need\b",
            r"\blooking for\b",
            r"\bsearch for\b",
            r"\bget me\b",
        ]

        for pattern in filler_patterns:
            query = re.sub(
                pattern,
                " ",
                query,
                flags=re.IGNORECASE,
            )

        # Normalize whitespace and punctuation.
        query = re.sub(r"[?!,]+", " ", query)
        query = re.sub(r"\s+", " ", query).strip()

        return query
