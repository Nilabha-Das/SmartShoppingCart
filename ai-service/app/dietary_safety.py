
DIETARY_UNVERIFIED_MESSAGE = (
    "Dietary-filtered recommendations are temporarily unavailable "
    "because the product dietary data has not been fully verified. "
    "You can still search products by name, category, and price."
)


def has_unverified_dietary_constraint(
    vegetarian=None,
    vegan=None,
    gluten_free=None,
):
    """Return True when a request relies on unverified dietary flags."""
    return any(
        value is True
        for value in (vegetarian, vegan, gluten_free)
    )
