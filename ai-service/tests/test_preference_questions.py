
from app.genai.intent_parser import UserIntent
from app.session_preferences import SessionPreferenceStore
from app.preference_questions import PreferenceQuestionManager


def make_intent(**overrides):
    values = {
        "query": "healthy snacks",
        "category": "Snacks & Branded Foods",
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


def setup_manager():
    store = SessionPreferenceStore()
    manager = PreferenceQuestionManager(store)
    return store, manager


def test_selects_first_missing_preference():
    store, manager = setup_manager()
    question = manager.select_question(
        "s1", make_intent(), "Snacks & Branded Foods"
    )
    assert question["preference"] == "max_price"


def test_returns_none_when_no_preferences_missing():
    store, manager = setup_manager()
    intent = make_intent(
        max_price=200,
        vegetarian=True,
        vegan=False,
        gluten_free=False,
        high_protein=False,
        low_sugar=False,
    )
    assert manager.select_question(
        "s1", intent, "Snacks & Branded Foods"
    ) is None


def test_saves_budget_answer():
    store, manager = setup_manager()
    result = manager.process_answer("s1", "max_price", "₹250")
    assert result["status"] == "answer_saved"
    assert store.get("s1").max_price == 250.0


def test_saves_false_as_explicit_answer():
    store, manager = setup_manager()
    result = manager.process_answer("s1", "high_protein", "no")
    assert result["status"] == "answer_saved"
    assert store.get("s1").high_protein is False


def test_rejects_invalid_budget():
    store, manager = setup_manager()
    result = manager.process_answer("s1", "max_price", "cheap")
    assert result["status"] == "invalid_answer"


def test_rejects_invalid_boolean_answer():
    store, manager = setup_manager()
    result = manager.process_answer("s1", "vegan", "sometimes")
    assert result["status"] == "invalid_answer"


def test_preserves_other_preferences():
    store, manager = setup_manager()
    manager.process_answer("s1", "max_price", "300")
    manager.process_answer("s1", "vegan", "yes")

    state = store.get("s1")
    assert state.max_price == 300.0
    assert state.vegan is True


def test_rejects_unknown_preference():
    store, manager = setup_manager()
    result = manager.process_answer("s1", "unknown_field", "yes")
    assert result["status"] == "invalid_preference"


def test_rejects_blank_answer():
    store, manager = setup_manager()
    result = manager.process_answer("s1", "vegan", " ")
    assert result["status"] == "invalid_answer"
