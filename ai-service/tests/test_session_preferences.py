
from app.genai.intent_parser import UserIntent
from app.session_preferences import SessionPreferenceStore


FOOD_CATEGORY = "Snacks & Branded Foods"


def make_intent(**overrides):
    values = {
        "query": "snacks",
        "category": None,
        "subcategory": None,
        "max_price": None,
        "vegetarian": None,
        "vegan": None,
        "gluten_free": None,
        "high_protein": None,
        "low_sugar": None,
        "purpose": None,
        "intent": "search",
    }
    values.update(overrides)
    return UserIntent(**values)


def test_sessions_are_isolated():
    store = SessionPreferenceStore()
    store.update_from_intent(
        "session-a",
        make_intent(max_price=200),
    )

    assert store.get("session-a").max_price == 200
    assert store.get("session-b").max_price is None


def test_false_is_saved_as_an_explicit_preference():
    store = SessionPreferenceStore()
    store.update_from_intent(
        "session-a",
        make_intent(vegetarian=False),
    )

    assert store.get("session-a").vegetarian is False


def test_current_intent_overrides_saved_preference():
    store = SessionPreferenceStore()
    store.update_from_intent(
        "session-a",
        make_intent(max_price=200),
    )

    intent = make_intent(max_price=350)
    store.merge_into_intent("session-a", intent)

    assert intent.max_price == 350


def test_saved_preference_fills_unknown_intent_field():
    store = SessionPreferenceStore()
    store.update_from_intent(
        "session-a",
        make_intent(max_price=200),
    )

    intent = make_intent()
    store.merge_into_intent("session-a", intent)

    assert intent.max_price == 200


def test_missing_slots_exclude_answered_preferences():
    store = SessionPreferenceStore()
    intent = make_intent(
        max_price=250,
        vegetarian=True,
    )

    missing = store.missing_preference_slots(
        "session-a",
        intent,
        FOOD_CATEGORY,
    )

    assert "max_price" not in missing
    assert "vegetarian" not in missing
    assert "vegan" not in missing


def test_non_food_category_does_not_ask_dietary_questions():
    store = SessionPreferenceStore()
    intent = make_intent()

    missing = store.missing_preference_slots(
        "session-a",
        intent,
        "Beauty & Hygiene",
    )

    assert missing == ["max_price"]


def test_unresolved_category_does_not_trigger_questions():
    store = SessionPreferenceStore()

    missing = store.missing_preference_slots(
        "session-a",
        make_intent(),
        None,
    )

    assert missing == []


def test_clear_removes_session_state():
    store = SessionPreferenceStore()
    store.update_from_intent(
        "session-a",
        make_intent(max_price=200),
    )

    store.clear("session-a")

    assert store.get("session-a").max_price is None
