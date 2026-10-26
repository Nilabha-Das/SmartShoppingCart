NUTRITION_DATA_VERIFIED = False

NUTRITION_UNVERIFIED_MESSAGE = (
    "Nutrition-based recommendations are temporarily unavailable "
    "because the product nutrition data has not been verified. "
    "You can still search products by name, category, and price."
)


def has_unverified_nutrition_constraint(
    high_protein=None,
    low_sugar=None,
    min_protein=None,
):
    """Return True when a request relies on unverified nutrition data."""
    return (
        high_protein is True
        or low_sugar is True
        or min_protein is not None
    )
