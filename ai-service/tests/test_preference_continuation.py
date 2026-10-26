
from unittest.mock import MagicMock

from app.pipeline.shopping_search import ShoppingSearchPipeline


def make_pipeline():
    """Create a pipeline with mocked external dependencies."""
    pipeline = ShoppingSearchPipeline()

    pipeline.intent_parser = MagicMock()
    pipeline.taxonomy_resolver = MagicMock()
    pipeline.retriever = MagicMock()
    pipeline.response_generator = MagicMock()

    return pipeline


def configure_pipeline(pipeline):
    """Configure mocks for an ordinary snacks search."""
    intent = MagicMock()
    intent.query = "snacks"
    intent.category = None
    intent.subcategory = None
    intent.max_price = None
    intent.vegetarian = None
    intent.vegan = None
    intent.gluten_free = None
    intent.high_protein = None
    intent.low_sugar = None
    intent.purpose = None
    intent.intent = "search"
    intent.model_dump.return_value = {
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
    intent.model_copy.side_effect = (
        lambda update: MagicMock(
            **{
                **{
                    key: getattr(intent, key)
                    for key in (
                        "query",
                        "category",
                        "subcategory",
                        "max_price",
                        "vegetarian",
                        "vegan",
                        "gluten_free",
                        "high_protein",
                        "low_sugar",
                        "purpose",
                        "intent",
                    )
                },
                **update,
                "model_dump": intent.model_dump,
            }
        )
    )

    pipeline.intent_parser.parse.return_value = intent
    pipeline.taxonomy_resolver.resolve.return_value = {
        "status": "resolved",
        "category": "Snacks & Branded Foods",
        "subcategory": "Snacks & Namkeen",
        "candidates": [],
        "matched_by": "test",
        "matches": [],
    }
    pipeline.retriever.retrieve.return_value = [
        {
            "product_id": "TEST001",
            "product_name": "Test Snacks",
            "brand": "Test Brand",
            "category": "Snacks & Branded Foods",
            "subcategory": "Snacks & Namkeen",
            "price": 100,
            "rating": 4.0,
        }
    ]
    pipeline.response_generator.generate.return_value = (
        "Here are the matching snacks."
    )
    pipeline.response_generator.generate_clarification.return_value = (
        "Could you clarify which type you mean?"
    )

    return pipeline


def test_answer_resumes_original_search():
    pipeline = configure_pipeline(make_pipeline())

    question = pipeline.search(
        user_message="snacks",
        session_id="session-1",
        ask_preferences=True,
    )

    assert question["status"] == "needs_preference"

    result = pipeline.answer_preference(
        session_id="session-1",
        preference=question["preference"],
        answer="300",
    )

    assert result["status"] == "resolved"
    assert result["session_id"] == "session-1"
    assert "preference_answer" in result


def test_invalid_answer_preserves_pending_search():
    pipeline = configure_pipeline(make_pipeline())

    question = pipeline.search(
        user_message="snacks",
        session_id="session-2",
        ask_preferences=True,
    )

    assert question["status"] == "needs_preference"

    result = pipeline.answer_preference(
        session_id="session-2",
        preference=question["preference"],
        answer="cheap",
    )

    assert result["status"] == "invalid_answer"
    assert "session-2" in pipeline.pending_searches


def test_wrong_preference_does_not_consume_pending_search():
    pipeline = configure_pipeline(make_pipeline())

    question = pipeline.search(
        user_message="snacks",
        session_id="session-3",
        ask_preferences=True,
    )

    assert question["status"] == "needs_preference"

    expected_preference = question["preference"]
    wrong_preference = (
        "vegan" if expected_preference != "vegan" else "max_price"
    )

    result = pipeline.answer_preference(
        session_id="session-3",
        preference=wrong_preference,
        answer="yes",
    )

    assert result["status"] == "unexpected_preference"
    assert "session-3" in pipeline.pending_searches


def test_answer_without_pending_question_is_rejected():
    pipeline = configure_pipeline(make_pipeline())

    result = pipeline.answer_preference(
        session_id="session-4",
        preference="max_price",
        answer="300",
    )

    assert result["status"] == "no_pending_question"
