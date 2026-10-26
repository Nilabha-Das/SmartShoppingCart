from app.nutrition_safety import (
    NUTRITION_DATA_VERIFIED,
    has_unverified_nutrition_constraint,
)


def test_nutrition_data_is_not_marked_verified():
    assert NUTRITION_DATA_VERIFIED is False


def test_high_protein_constraint_requires_verified_data():
    assert has_unverified_nutrition_constraint(high_protein=True)


def test_low_sugar_constraint_requires_verified_data():
    assert has_unverified_nutrition_constraint(low_sugar=True)


def test_minimum_protein_constraint_requires_verified_data():
    assert has_unverified_nutrition_constraint(min_protein=15)


def test_ordinary_search_does_not_require_nutrition_data():
    assert not has_unverified_nutrition_constraint()


def test_false_nutrition_preferences_do_not_block_search():
    assert not has_unverified_nutrition_constraint(
        high_protein=False,
        low_sugar=False,
    )
