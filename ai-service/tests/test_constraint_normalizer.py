from app.genai.constraint_normalizer import ConstraintNormalizer
from app.genai.intent_parser import UserIntent


def make_intent():
    return UserIntent(
        query="",
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


def test_high_protein():
    intent = make_intent()

    result = ConstraintNormalizer.normalize(
        intent,
        "high protein snacks"
    )

    assert result.high_protein is True


def test_protein_snacks():
    intent = make_intent()

    result = ConstraintNormalizer.normalize(
        intent,
        "protein snacks"
    )

    assert result.high_protein is True


def test_vegetarian():
    intent = make_intent()

    result = ConstraintNormalizer.normalize(
        intent,
        "vegetarian snacks"
    )

    assert result.vegetarian is True


def test_vegan():
    intent = make_intent()

    result = ConstraintNormalizer.normalize(
        intent,
        "vegan snacks"
    )

    assert result.vegan is True


def test_gluten_free():
    intent = make_intent()

    result = ConstraintNormalizer.normalize(
        intent,
        "gluten free snacks"
    )

    assert result.gluten_free is True


def test_low_sugar():
    intent = make_intent()

    result = ConstraintNormalizer.normalize(
        intent,
        "low sugar snacks"
    )

    assert result.low_sugar is True


def test_max_price_under():
    intent = make_intent()

    result = ConstraintNormalizer.normalize(
        intent,
        "snacks under 300"
    )

    assert result.max_price == 300.0


def test_combined_constraints():
    intent = make_intent()

    result = ConstraintNormalizer.normalize(
        intent,
        "vegetarian high protein snacks under 300"
    )

    assert result.vegetarian is True
    assert result.high_protein is True
    assert result.max_price == 300.0