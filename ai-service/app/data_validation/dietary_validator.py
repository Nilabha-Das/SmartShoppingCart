import pandas as pd
import re


class DietaryValidator:

    ANIMAL_PRODUCT_TERMS = [
        "chicken",
        "murgh",
        "pork",
        "beef",
        "mutton",
        "fish",
        "prawn",
        "prawns",
        "shrimp",
        "crab",
        "lobster",
        "salami",
        "bacon",
        "ham",
        "seafood",
    ]

    @staticmethod
    def validate(df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate dietary metadata.

        IMPORTANT:
        This function only detects inconsistencies.
        It does not modify the input dataframe.
        """

        results = []

        for _, row in df.iterrows():

            product_id = row.get("product_id")
            product_name = str(row.get("product_name", ""))
            product_type = str(row.get("product_type", ""))

            vegetarian = row.get("vegetarian")
            vegan = row.get("vegan")

            pt = product_type.strip().lower()
            name = product_name.strip().lower()

            issues = []
            confidence = "NONE"

            # --------------------------------------------------
            # Structured product-type checks
            # --------------------------------------------------

            is_non_veg = bool(
                re.search(r"\bnon[- ]?veg\b", pt)
            )

            is_veg = (
                bool(re.search(r"\bveg\b", pt))
                and not is_non_veg
            )

            # --------------------------------------------------
            # RULE 1
            # Non-Veg product marked vegetarian
            # --------------------------------------------------

            if is_non_veg and vegetarian is True:

                issues.append(
                    "Non-Veg product_type but vegetarian=True"
                )

                confidence = "HIGH"

            # --------------------------------------------------
            # RULE 2
            # Non-Veg product marked vegan
            # --------------------------------------------------

            if is_non_veg and vegan is True:

                issues.append(
                    "Non-Veg product_type but vegan=True"
                )

                confidence = "HIGH"

            # --------------------------------------------------
            # RULE 3
            # Veg product marked non-vegetarian
            # --------------------------------------------------

            if is_veg and vegetarian is False:

                issues.append(
                    "Veg product_type but vegetarian=False"
                )

                confidence = "MEDIUM"

            # --------------------------------------------------
            # RULE 4
            # Strong product-name contradiction
            #
            # We inspect PRODUCT NAME only.
            # We deliberately do NOT inspect description.
            # --------------------------------------------------

            matched_animal_terms = []

            for term in DietaryValidator.ANIMAL_PRODUCT_TERMS:

                if re.search(
                    rf"\b{re.escape(term)}\b",
                    name
                ):
                    matched_animal_terms.append(term)

            if matched_animal_terms and vegetarian is True:

                issues.append(
                    "Animal-product term in product name: "
                    + ", ".join(matched_animal_terms)
                )

                confidence = "HIGH"

            # --------------------------------------------------
            # Store problematic products
            # --------------------------------------------------

            if issues:

                results.append({
                    "product_id": product_id,
                    "product_name": product_name,
                    "product_type": product_type,
                    "vegetarian": vegetarian,
                    "vegan": vegan,
                    "confidence": confidence,
                    "issues": " | ".join(issues)
                })

        return pd.DataFrame(results)