import re
from typing import Optional, List, Dict, Any

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


MASTER_PRODUCTS_PATH = "/app/data/phase1/master_products.csv"
MODEL_NAME = "all-MiniLM-L6-v2"


class TaxonomyResolver:

    def __init__(self):

        # ---------------------------------------------------------
        # 1. Load embedding model
        # ---------------------------------------------------------

        self.model = SentenceTransformer(MODEL_NAME)

        # ---------------------------------------------------------
        # 2. Load product data
        # ---------------------------------------------------------

        self.products = pd.read_csv(
            MASTER_PRODUCTS_PATH
        )

        # ---------------------------------------------------------
        # 3. Clean taxonomy data
        # ---------------------------------------------------------

        taxonomy = (
            self.products[
                ["category", "subcategory"]
            ]
            .dropna()
            .astype(str)
        )

        taxonomy["category"] = (
            taxonomy["category"]
            .str.strip()
        )

        taxonomy["subcategory"] = (
            taxonomy["subcategory"]
            .str.strip()
        )

        # ---------------------------------------------------------
        # 4. Categories
        # ---------------------------------------------------------

        self.categories = sorted(
            taxonomy["category"]
            .unique()
            .tolist()
        )

        # ---------------------------------------------------------
        # 5. Category -> subcategories
        # ---------------------------------------------------------

        self.category_subcategories = (
            taxonomy
            .groupby("category")["subcategory"]
            .apply(
                lambda x: sorted(
                    x.unique().tolist()
                )
            )
            .to_dict()
        )

        # ---------------------------------------------------------
        # 6. Subcategory -> parent categories
        # ---------------------------------------------------------

        self.subcategory_categories = (
            taxonomy
            .groupby("subcategory")["category"]
            .apply(
                lambda x: sorted(
                    x.unique().tolist()
                )
            )
            .to_dict()
        )

        # ---------------------------------------------------------
        # 7. Normalized lookup dictionaries
        # ---------------------------------------------------------

        self.normalized_categories = {
            self._normalize(category): category
            for category in self.categories
        }

        self.normalized_subcategories = {
            self._normalize(subcategory): subcategory
            for subcategory in self.subcategory_categories
        }

        # ---------------------------------------------------------
        # 8. Product-word aliases
        #
        # These are NOT arbitrary category assignments.
        # They are useful natural-language expressions that
        # appear in product names/types/descriptions.
        # ---------------------------------------------------------

        self.aliases = {

            # Snacks
            "chips": {
                "subcategory": "Snacks & Namkeen",
                "category": "Snacks & Branded Foods"
            },

            "namkeen": {
                "subcategory": "Snacks & Namkeen",
                "category": "Snacks & Branded Foods"
            },

            "snack": {
                "category": "Snacks & Branded Foods"
            },

            "snacks": {
                "category": "Snacks & Branded Foods"
            },

            # Pasta
            "pasta": {
                "subcategory": "Pasta, Soup & Noodles",
                "category": "Gourmet & World Food"
            },

            "spaghetti": {
                "subcategory": "Pasta, Soup & Noodles",
                "category": "Gourmet & World Food"
            },

            "noodles": {
                "subcategory": "Pasta, Soup & Noodles",
                "category": "Gourmet & World Food"
            },

            "soup": {
                "subcategory": "Pasta, Soup & Noodles",
                "category": "Gourmet & World Food"
            },

            # Sauces
            "sauce": {
                "subcategory": "Sauces, Spreads & Dips",
                "category": "Gourmet & World Food"
            },

            "sauces": {
                "subcategory": "Sauces, Spreads & Dips",
                "category": "Gourmet & World Food"
            },

            "dip": {
                "subcategory": "Sauces, Spreads & Dips",
                "category": "Gourmet & World Food"
            },

            "dips": {
                "subcategory": "Sauces, Spreads & Dips",
                "category": "Gourmet & World Food"
            },

            "spread": {
                "subcategory": "Sauces, Spreads & Dips",
                "category": "Gourmet & World Food"
            },

            "spreads": {
                "subcategory": "Sauces, Spreads & Dips",
                "category": "Gourmet & World Food"
            },

            "ketchup": {
                "subcategory": "Sauces, Spreads & Dips",
                "category": "Gourmet & World Food"
            },

            # Bakery
            "bakery": {
                "category": "Bakery, Cakes & Dairy"
            },

            "bread": {
                "subcategory": "Breads & Buns",
                "category": "Bakery, Cakes & Dairy"
            },

            "breads": {
                "subcategory": "Breads & Buns",
                "category": "Bakery, Cakes & Dairy"
            },

            "bun": {
                "subcategory": "Breads & Buns",
                "category": "Bakery, Cakes & Dairy"
            },

            "buns": {
                "subcategory": "Breads & Buns",
                "category": "Bakery, Cakes & Dairy"
            },

            "cake": {
                "subcategory": "Cakes & Pastries",
                "category": "Bakery, Cakes & Dairy"
            },

            "cakes": {
                "subcategory": "Cakes & Pastries",
                "category": "Bakery, Cakes & Dairy"
            },

            "pastry": {
                "subcategory": "Cakes & Pastries",
                "category": "Bakery, Cakes & Dairy"
            },

            "pastries": {
                "subcategory": "Cakes & Pastries",
                "category": "Bakery, Cakes & Dairy"
            },

            # Dairy
            "milk": {
                "subcategory": "Dairy",
                "category": "Bakery, Cakes & Dairy"
            },

            "dairy": {
                "subcategory": "Dairy",
                "category": "Bakery, Cakes & Dairy"
            },

            "cheese": {
                "subcategory": "Dairy & Cheese",
                "category": "Gourmet & World Food"
            },

            # Rice
            "rice": {
                "subcategory": "Rice & Rice Products",
                "category": "Foodgrains, Oil & Masala"
            },

            # Fruits
            "fruit": {
                "subcategory": "Fresh Fruits",
                "category": "Fruits & Vegetables"
            },

            "fruits": {
                "subcategory": "Fresh Fruits",
                "category": "Fruits & Vegetables"
            },

            "vegetable": {
                "subcategory": "Fresh Vegetables",
                "category": "Fruits & Vegetables"
            },

            "vegetables": {
                "subcategory": "Fresh Vegetables",
                "category": "Fruits & Vegetables"
            },

            # Beverages
            "tea": {
                "subcategory": "Tea",
                "category": "Beverages"
            },

            "coffee": {
                "subcategory": "Coffee",
                "category": "Beverages"
            },

            "water": {
                "subcategory": "Water",
                "category": "Beverages"
            },

            "juice": {
                "subcategory": "Fruit Juices & Drinks",
                "category": "Beverages"
            },

            "juices": {
                "subcategory": "Fruit Juices & Drinks",
                "category": "Beverages"
            },

            # Cleaning
            "detergent": {
                "subcategory": "Detergents & Dishwash",
                "category": "Cleaning & Household"
            },

            "detergents": {
                "subcategory": "Detergents & Dishwash",
                "category": "Cleaning & Household"
            },

            "dishwash": {
                "subcategory": "Detergents & Dishwash",
                "category": "Cleaning & Household"
            },

            "cleaner": {
                "subcategory": "All Purpose Cleaners",
                "category": "Cleaning & Household"
            },

            "cleaners": {
                "subcategory": "All Purpose Cleaners",
                "category": "Cleaning & Household"
            },

            # Beauty
            "makeup": {
                "subcategory": "Makeup",
                "category": "Beauty & Hygiene"
            },

            "skincare": {
                "subcategory": "Skin Care",
                "category": "Beauty & Hygiene"
            },

            "skin": {
                "subcategory": "Skin Care",
                "category": "Beauty & Hygiene"
            },

            "hair": {
                "subcategory": "Hair Care",
                "category": "Beauty & Hygiene"
            },

            "shampoo": {
                "subcategory": "Hair Care",
                "category": "Beauty & Hygiene"
            },

            "soap": {
                "subcategory": "Bath & Hand Wash",
                "category": "Beauty & Hygiene"
            },

            "perfume": {
                "subcategory": "Fragrances & Deos",
                "category": "Beauty & Hygiene"
            },

            "fragrance": {
                "subcategory": "Fragrances & Deos",
                "category": "Beauty & Hygiene"
            },
        }

        # ---------------------------------------------------------
        # 9. Cache category embeddings
        #
        # Embeddings are only used as a fallback.
        # ---------------------------------------------------------

        self.category_embeddings = (
            self.model.encode(
                self.categories,
                normalize_embeddings=True
            )
        )

        print(
            f"Categories loaded: {len(self.categories)}"
        )

        print(
            f"Subcategories loaded: "
            f"{len(self.subcategory_categories)}"
        )

    # =============================================================
    # TEXT NORMALIZATION
    # =============================================================

    @staticmethod
    def _normalize(text: Any) -> str:

        if text is None:
            return ""

        text = str(text).lower()

        # Normalize ampersand
        text = text.replace("&", " and ")

        # Normalize punctuation
        text = re.sub(
            r"[^a-z0-9\s]",
            " ",
            text
        )

        # Remove repeated whitespace
        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    @staticmethod
    def _tokens(text: Any) -> List[str]:

        normalized = TaxonomyResolver._normalize(
            text
        )

        return [
            token
            for token in normalized.split()
            if len(token) > 1
        ]

    # =============================================================
    # REMOVE CONVERSATIONAL WORDS
    # =============================================================

    @staticmethod
    def _remove_conversation_words(
        text: str
    ) -> str:

        normalized = TaxonomyResolver._normalize(
            text
        )

        stop_phrases = [
            "i want",
            "i need",
            "i am looking for",
            "i am looking",
            "show me",
            "give me",
            "find me",
            "find",
            "show",
            "please",
            "some",
            "something",
            "looking for",
            "can you show",
            "can you find",
            "could you show",
            "could you find",
            "i would like",
            "i would like some",
            "i would like to buy",
            "i need some",
            "i want some",
            "get me",
            "help me find"
        ]

        for phrase in stop_phrases:
            normalized = normalized.replace(
                phrase,
                " "
            )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized
        )

        return normalized.strip()

    # =============================================================
    # EXACT CATEGORY
    # =============================================================

    def _find_exact_category(
        self,
        text: str
    ) -> Optional[str]:

        normalized = self._normalize(text)

        if normalized in self.normalized_categories:
            return self.normalized_categories[
                normalized
            ]

        return None

    # =============================================================
    # EXACT SUBCATEGORY
    # =============================================================

    def _find_exact_subcategory(
        self,
        text: str
    ) -> Optional[str]:

        normalized = self._normalize(text)

        if normalized in self.normalized_subcategories:
            return self.normalized_subcategories[
                normalized
            ]

        return None

    # =============================================================
    # FIND TAXONOMY PHRASES INSIDE QUERY
    # =============================================================

    def _find_subcategory_phrases(
        self,
        query: str
    ) -> List[Dict[str, Any]]:

        normalized_query = (
            self._remove_conversation_words(query)
        )

        matches = []

        for subcategory in (
            self.subcategory_categories.keys()
        ):

            normalized_subcategory = (
                self._normalize(subcategory)
            )

            # Exact phrase contained in query
            if (
                normalized_subcategory
                in normalized_query
            ):

                matches.append(
                    {
                        "subcategory": subcategory,
                        "parents": (
                            self.subcategory_categories[
                                subcategory
                            ]
                        ),
                        "matched_tokens": (
                            self._tokens(
                                subcategory
                            )
                        ),
                        "match_type": "exact_phrase"
                    }
                )

        return matches

    # =============================================================
    # FIND ALIASES
    # =============================================================

    def _find_alias_matches(
        self,
        query: str
    ) -> List[Dict[str, Any]]:

        normalized_query = (
            self._remove_conversation_words(query)
        )

        query_tokens = set(
            self._tokens(normalized_query)
        )

        matches = []

        for alias, mapping in self.aliases.items():

            if alias in query_tokens:

                match = {
                    "alias": alias,
                    "category": mapping.get(
                        "category"
                    ),
                    "subcategory": mapping.get(
                        "subcategory"
                    ),
                    "match_type": "alias"
                }

                matches.append(match)

        return matches

    # =============================================================
    # CATEGORY FROM ALIAS
    # =============================================================

    def _resolve_alias_category(
        self,
        alias_matches: List[Dict[str, Any]]
    ) -> Optional[str]:

        if not alias_matches:
            return None

        categories = [
            match["category"]
            for match in alias_matches
            if match.get("category")
        ]

        if not categories:
            return None

        # If all aliases agree on one category
        unique_categories = list(
            dict.fromkeys(categories)
        )

        if len(unique_categories) == 1:
            return unique_categories[0]

        return None

    # =============================================================
    # SUBCATEGORY FROM ALIAS
    # =============================================================

    def _resolve_alias_subcategory(
        self,
        alias_matches: List[Dict[str, Any]]
    ) -> Optional[str]:

        if not alias_matches:
            return None

        subcategories = [
            match["subcategory"]
            for match in alias_matches
            if match.get("subcategory")
        ]

        if not subcategories:
            return None

        unique_subcategories = list(
            dict.fromkeys(subcategories)
        )

        if len(unique_subcategories) == 1:
            return unique_subcategories[0]

        return None

    # =============================================================
    # SEMANTIC CATEGORY FALLBACK
    # =============================================================

    def _semantic_category(
        self,
        query: str
    ) -> Optional[str]:

        if not query:
            return None

        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True
        )

        scores = np.dot(
            self.category_embeddings,
            query_embedding
        )

        best_index = int(
            np.argmax(scores)
        )

        best_score = float(
            scores[best_index]
        )

        # Conservative fallback
        if best_score < 0.55:
            return None

        return self.categories[
            best_index
        ]

    # =============================================================
    # SEMANTIC SUBCATEGORY FALLBACK
    # =============================================================

    def _semantic_subcategory(
        self,
        query: str,
        category: Optional[str] = None
    ) -> Optional[str]:

        if not query:
            return None

        if category:

            candidates = (
                self.category_subcategories.get(
                    category,
                    []
                )
            )

        else:

            candidates = list(
                self.subcategory_categories.keys()
            )

        if not candidates:
            return None

        embeddings = self.model.encode(
            candidates,
            normalize_embeddings=True
        )

        query_embedding = self.model.encode(
            query,
            normalize_embeddings=True
        )

        scores = np.dot(
            embeddings,
            query_embedding
        )

        best_index = int(
            np.argmax(scores)
        )

        best_score = float(
            scores[best_index]
        )

        # Conservative fallback
        if best_score < 0.55:
            return None

        return candidates[
            best_index
        ]

    # =============================================================
    # MULTI-CONCEPT DETECTION
    # =============================================================

    def _detect_multiple_concepts(
        self,
        query: str
    ) -> List[Dict[str, Any]]:

        matches = []

        # ---------------------------------------------------------
        # Exact subcategory phrases
        # ---------------------------------------------------------

        phrase_matches = (
            self._find_subcategory_phrases(
                query
            )
        )

        for match in phrase_matches:
            matches.append(
                {
                    "category": (
                        match["parents"][0]
                        if len(match["parents"]) == 1
                        else None
                    ),
                    "subcategory": (
                        match["subcategory"]
                    ),
                    "matched_tokens": (
                        match["matched_tokens"]
                    ),
                    "match_type": "subcategory"
                }
            )

        # ---------------------------------------------------------
        # Alias matches
        # ---------------------------------------------------------

        alias_matches = (
            self._find_alias_matches(query)
        )

        for match in alias_matches:

            item = {
                "category": match.get(
                    "category"
                ),
                "subcategory": match.get(
                    "subcategory"
                ),
                "matched_tokens": [
                    match["alias"]
                ],
                "match_type": "alias"
            }

            # Avoid duplicate taxonomy result
            already_exists = any(
                x["category"] == item["category"]
                and
                x["subcategory"] == item["subcategory"]
                for x in matches
            )

            if not already_exists:
                matches.append(item)

        return matches

    # =============================================================
    # GENERIC PASTA DETECTION
    #
    # Bare "pasta" is intentionally treated as ambiguous because
    # pasta-related products exist under multiple taxonomy branches.
    #
    # Queries with additional constraints such as:
    # "high protein pasta"
    # "vegetarian pasta"
    # "pasta under 300"
    # are NOT treated as bare pasta.
    # =============================================================

    def _is_bare_generic_pasta(
        self,
        query: str
    ) -> bool:

        normalized = self._remove_conversation_words(
            query
        )

        # Words that are conversational/polite and do not
        # change the meaning of a bare pasta request.
        filler_words = {
            "please",
            "some",
            "me",
            "just"
        }

        tokens = [
            token
            for token in self._tokens(normalized)
            if token not in filler_words
        ]

        return tokens == ["pasta"]

    # =============================================================
    # MAIN RESOLVER
    # =============================================================

    def resolve(
        self,
        user_query: str,
        category: Optional[str] = None,
        subcategory: Optional[str] = None
    ) -> Dict[str, Any]:

        original_query = user_query or ""

        # ---------------------------------------------------------
        # STEP 1
        # Explicit category supplied by intent parser
        # ---------------------------------------------------------

        if category:

            exact_category = (
                self._find_exact_category(
                    category
                )
            )

            if exact_category:

                resolved_subcategory = None

                if subcategory:

                    exact_subcategory = (
                        self._find_exact_subcategory(
                            subcategory
                        )
                    )

                    if (
                        exact_subcategory
                        and
                        exact_subcategory
                        in self.category_subcategories.get(
                            exact_category,
                            []
                        )
                    ):
                        resolved_subcategory = (
                            exact_subcategory
                        )

                return {
                    "status": "resolved",
                    "category": exact_category,
                    "subcategory": (
                        resolved_subcategory
                    ),
                    "candidates": [],
                    "matched_by": "explicit_category"
                }

        # ---------------------------------------------------------
        # STEP 2
        # Explicit subcategory supplied
        # ---------------------------------------------------------

        if subcategory:

            exact_subcategory = (
                self._find_exact_subcategory(
                    subcategory
                )
            )

            if exact_subcategory:

                parents = (
                    self.subcategory_categories[
                        exact_subcategory
                    ]
                )

                # One parent
                if len(parents) == 1:

                    return {
                        "status": "resolved",
                        "category": parents[0],
                        "subcategory": (
                            exact_subcategory
                        ),
                        "candidates": [],
                        "matched_by": (
                            "explicit_subcategory"
                        )
                    }

                # Multiple parents
                return {
                    "status": "ambiguous",
                    "category": None,
                    "subcategory": (
                        exact_subcategory
                    ),
                    "candidates": [
                        {
                            "category": parent,
                            "subcategory": (
                                exact_subcategory
                            )
                        }
                        for parent in parents
                    ],
                    "matched_by": (
                        "explicit_subcategory"
                    )
                }

        # ---------------------------------------------------------
        # STEP 3
        # Clean natural-language query
        # ---------------------------------------------------------

        cleaned_query = (
            self._remove_conversation_words(
                original_query
            )
        )

        if not cleaned_query:

            return {
                "status": "unknown",
                "category": None,
                "subcategory": None,
                "candidates": [],
                "matched_by": None
            }

        # ---------------------------------------------------------
        # STEP 3.5
        # Bare generic "pasta" is ambiguous
        #
        # Pasta-related products exist under multiple taxonomy
        # branches, so do not automatically choose one branch.
        # ---------------------------------------------------------

        if self._is_bare_generic_pasta(
            original_query
        ):

            pasta_candidates = []

            # Find every taxonomy branch whose subcategory
            # contains "pasta".
            for category_name, subcategories in (
                self.category_subcategories.items()
            ):

                for subcategory_name in subcategories:

                    if "pasta" in self._normalize(
                        subcategory_name
                    ).split():

                        pasta_candidates.append(
                            {
                                "category": category_name,
                                "subcategory": subcategory_name
                            }
                        )

            # Remove duplicates
            unique_candidates = []

            for candidate in pasta_candidates:

                if candidate not in unique_candidates:
                    unique_candidates.append(candidate)

            return {
                "status": "ambiguous",
                "category": None,
                "subcategory": None,
                "candidates": unique_candidates,
                "matched_by": "generic_pasta"
            }

        # ---------------------------------------------------------
        # STEP 4
        # Exact whole query category
        # ---------------------------------------------------------

        exact_category = (
            self._find_exact_category(
                cleaned_query
            )
        )

        if exact_category:

            return {
                "status": "resolved",
                "category": exact_category,
                "subcategory": None,
                "candidates": [],
                "matched_by": "exact_category"
            }

        # ---------------------------------------------------------
        # STEP 5
        # Exact whole query subcategory
        # ---------------------------------------------------------

        exact_subcategory = (
            self._find_exact_subcategory(
                cleaned_query
            )
        )

        if exact_subcategory:

            parents = (
                self.subcategory_categories[
                    exact_subcategory
                ]
            )

            if len(parents) == 1:

                return {
                    "status": "resolved",
                    "category": parents[0],
                    "subcategory": (
                        exact_subcategory
                    ),
                    "candidates": [],
                    "matched_by": (
                        "exact_subcategory"
                    )
                }

            return {
                "status": "ambiguous",
                "category": None,
                "subcategory": (
                    exact_subcategory
                ),
                "candidates": [
                    {
                        "category": parent,
                        "subcategory": (
                            exact_subcategory
                        )
                    }
                    for parent in parents
                ],
                "matched_by": (
                    "exact_subcategory"
                )
            }

        # ---------------------------------------------------------
        # STEP 6
        # Detect multiple taxonomy concepts
        # ---------------------------------------------------------

        concept_matches = (
            self._detect_multiple_concepts(
                original_query
            )
        )

        # Remove duplicates
        unique_matches = []

        for match in concept_matches:

            exists = any(
                existing["category"]
                == match["category"]
                and
                existing["subcategory"]
                == match["subcategory"]
                for existing in unique_matches
            )

            if not exists:
                unique_matches.append(match)

        concept_matches = unique_matches

        # ---------------------------------------------------------
        # STEP 7
        # If multiple concepts are present
        # ---------------------------------------------------------

        if len(concept_matches) >= 2:

            categories = [
                match["category"]
                for match in concept_matches
                if match["category"]
            ]

            unique_categories = list(
                dict.fromkeys(categories)
            )

            subcategories = [
                match["subcategory"]
                for match in concept_matches
                if match["subcategory"]
            ]

            unique_subcategories = list(
                dict.fromkeys(subcategories)
            )

            # If all concepts point to same category
            if len(unique_categories) == 1:

                # If there is one clear subcategory,
                # return it.
                if len(unique_subcategories) == 1:

                    return {
                        "status": "resolved",
                        "category": (
                            unique_categories[0]
                        ),
                        "subcategory": (
                            unique_subcategories[0]
                        ),
                        "candidates": [],
                        "matched_by": (
                            "multiple_concepts"
                        ),
                        "matches": concept_matches
                    }

                # Multiple subcategories under same
                # category.
                return {
                    "status": "resolved",
                    "category": (
                        unique_categories[0]
                    ),
                    "subcategory": None,
                    "candidates": [],
                    "matched_by": (
                        "multiple_concepts"
                    ),
                    "matches": concept_matches
                }

            # Multiple different categories
            return {
                "status": "multi",
                "category": None,
                "subcategory": None,
                "candidates": concept_matches,
                "matched_by": (
                    "multiple_concepts"
                ),
                "matches": concept_matches
            }

        # ---------------------------------------------------------
        # STEP 8
        # One strong concept
        # ---------------------------------------------------------

        if len(concept_matches) == 1:

            match = concept_matches[0]

            return {
                "status": "resolved",
                "category": match["category"],
                "subcategory": (
                    match["subcategory"]
                ),
                "candidates": [],
                "matched_by": (
                    match["match_type"]
                ),
                "matches": concept_matches
            }

        # ---------------------------------------------------------
        # STEP 9
        # Semantic fallback
        #
        # Only used when deterministic matching failed.
        # ---------------------------------------------------------

        semantic_category = (
            self._semantic_category(
                cleaned_query
            )
        )

        if semantic_category:

            semantic_subcategory = (
                self._semantic_subcategory(
                    cleaned_query,
                    semantic_category
                )
            )

            return {
                "status": "resolved",
                "category": semantic_category,
                "subcategory": (
                    semantic_subcategory
                ),
                "candidates": [],
                "matched_by": (
                    "semantic_fallback"
                )
            }

        # ---------------------------------------------------------
        # STEP 10
        # Nothing confidently matched
        # ---------------------------------------------------------

        return {
            "status": "unknown",
            "category": None,
            "subcategory": None,
            "candidates": [],
            "matched_by": None
        }