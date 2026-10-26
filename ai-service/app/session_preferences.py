
from typing import Optional

from pydantic import BaseModel


class SessionPreferenceState(BaseModel):
    """Explicit preferences collected during one shopping session."""

    max_price: Optional[float] = None
    vegetarian: Optional[bool] = None
    vegan: Optional[bool] = None
    gluten_free: Optional[bool] = None
    high_protein: Optional[bool] = None
    low_sugar: Optional[bool] = None


class SessionPreferenceStore:
    """
    In-memory prototype store.

    Preferences are isolated by session_id. This implementation
    is suitable for local development and tests, not production
    persistence or multi-worker deployment.
    """

    PREFERENCE_FIELDS = (
        "max_price",
        "vegetarian",
        "vegan",
        "gluten_free",
        "high_protein",
        "low_sugar",
    )

    FOOD_CATEGORIES = {
        "bakery, cakes & dairy",
        "beverages",
        "eggs, meat & fish",
        "foodgrains, oil & masala",
        "fruits & vegetables",
        "gourmet & world food",
        "snacks & branded foods",
    }

    def __init__(self):
        self._sessions: dict[str, SessionPreferenceState] = {}

    def get(self, session_id: str) -> SessionPreferenceState:
        """Return a copy so callers cannot mutate stored state."""
        state = self._sessions.get(
            session_id,
            SessionPreferenceState(),
        )
        return state.model_copy(deep=True)

    def update_from_intent(
        self,
        session_id: str,
        intent,
    ) -> SessionPreferenceState:
        """
        Save only values explicitly represented by non-None fields.
        False is a valid value and must not be discarded.
        """
        if not session_id or not session_id.strip():
            raise ValueError("session_id must not be empty")

        state = self.get(session_id)

        for field in self.PREFERENCE_FIELDS:
            value = getattr(intent, field, None)
            if value is not None:
                setattr(state, field, value)

        self._sessions[session_id] = state
        return state.model_copy(deep=True)

    def merge_into_intent(self, session_id: str, intent):
        """
        Fill unknown current-turn fields from session state.
        Explicit values in the current intent always win.
        """
        state = self.get(session_id)

        for field in self.PREFERENCE_FIELDS:
            current_value = getattr(intent, field, None)
            saved_value = getattr(state, field)

            if current_value is None and saved_value is not None:
                setattr(intent, field, saved_value)

        return intent

    def missing_preference_slots(
        self,
        session_id: str,
        intent,
        category: Optional[str],
    ) -> list[str]:
        """
        Detect eligible unknown fields after taxonomy resolution.

        This method identifies candidates; it does not decide
        which question to ask. Adaptive selection comes in Step 4.
        """
        if not session_id or not session_id.strip():
            raise ValueError("session_id must not be empty")

        if getattr(intent, "intent", None) not in {
            "search",
            "recommendation",
            "purchase",
        }:
            return []

        # Resolve the product domain before asking preference questions.
        if not category:
            return []

        state = self.get(session_id)

        values = {
            field: (
                getattr(intent, field, None)
                if getattr(intent, field, None) is not None
                else getattr(state, field)
            )
            for field in self.PREFERENCE_FIELDS
        }

        missing = []

        # Budget can be relevant to both food and non-food products.
        if values["max_price"] is None:
            missing.append("max_price")

        is_food = category.strip().lower() in self.FOOD_CATEGORIES

        if is_food:
            # A vegan or vegetarian answer makes a second question
            # about the other field unnecessary at this stage.
            if (
                values["vegetarian"] is None
                and values["vegan"] is None
            ):
                missing.extend(["vegetarian", "vegan"])

            if values["gluten_free"] is None:
                missing.append("gluten_free")

            if values["high_protein"] is None:
                missing.append("high_protein")

            if values["low_sugar"] is None:
                missing.append("low_sugar")

        return missing

    def clear(self, session_id: str) -> None:
        """Remove preferences when a session ends or is reset."""
        self._sessions.pop(session_id, None)

    
    def update_preference(self, session_id: str, field: str, value):
        """Update one validated preference without changing other fields."""
        if not session_id or not session_id.strip():
            raise ValueError("session_id must not be empty")

        if field not in self.PREFERENCE_FIELDS:
            raise ValueError(f"Unknown preference field: {field}")

        state = self.get(session_id)
        setattr(state, field, value)
        self._sessions[session_id] = state
        return state.model_copy(deep=True)
