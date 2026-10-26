
import re
from typing import Any, Optional

from app.session_preferences import SessionPreferenceStore


class PreferenceQuestionManager:
    """Selects and processes one missing shopping preference at a time."""

    QUESTION_PRIORITY = [
        "max_price",
        "vegetarian",
        "vegan",
        "gluten_free",
        "high_protein",
        "low_sugar",
    ]

    QUESTIONS = {
        "max_price": (
            "What is your approximate budget for these products?"
        ),
        "vegetarian": (
            "Do you prefer vegetarian products?"
        ),
        "vegan": (
            "Do you prefer vegan products?"
        ),
        "gluten_free": (
            "Do you need gluten-free products?"
        ),
        "high_protein": (
            "Are you looking for high-protein products?"
        ),
        "low_sugar": (
            "Would you prefer low-sugar products?"
        ),
    }

    # Context cues prioritize relevant questions when the user's
    # request explicitly mentions a related need or goal.
    CONTEXT_CUES = {
        "max_price": (
            r"\b(budget|cheap|cheapest|affordable|"
            r"under\s+\d+|below\s+\d+|less than\s+\d+|"
            r"within\s+\d+|up to\s+\d+|price limit|save money)\b"
        ),
        "vegetarian": (
            r"\b(vegetarian|vegetarian food|veg food|meat-free)\b"
        ),
        "vegan": (
            r"\b(vegan|plant-based)\b"
        ),
        "gluten_free": (
            r"\b(gluten-free|gluten free|celiac|coeliac)\b"
        ),
        "high_protein": (
            r"\b(high-protein|high protein|protein-rich|"
            r"protein rich|protein snacks?|protein foods?|"
            r"gym|workout|muscle gain)\b"
        ),
        "low_sugar": (
            r"\b(low-sugar|low sugar|less sugar|"
            r"sugar-free|sugar free|diabetic|diabetes)\b"
        ),
    }

    def __init__(
        self,
        preference_store: SessionPreferenceStore,
    ):
        self.preference_store = preference_store

    
    def select_question(
        self,
        session_id: str,
        intent: Any,
        category: Optional[str],
    ) -> Optional[dict]:
        """
        Select one missing preference.

        Prefer explicit requirements over weaker contextual cues.
        If multiple cues are present, use a deterministic priority
        rather than assuming the first word expresses the main goal.
        """
        missing = set(
            self.preference_store.missing_preference_slots(
                session_id, intent, category
            )
        )

        if not missing:
            return None

        context = " ".join(
            str(value or "")
            for value in (
                getattr(intent, "query", ""),
                getattr(intent, "purpose", ""),
            )
        ).lower()

        # Explicit requirements should take precedence over indirect
        # context such as "gym" or "workout".
        explicit_cues = {
            "max_price": (
                r"\b(budget|affordable|cheap|cheapest|"
                r"under\s+\d+|below\s+\d+|less than\s+\d+|"
                r"within\s+\d+|up to\s+\d+|price limit)\b"
            ),
            "vegetarian": (
                r"\b(vegetarian|veg food|meat-free)\b"
            ),
            "vegan": (
                r"\b(vegan|plant-based)\b"
            ),
            "gluten_free": (
                r"\b(gluten-free|gluten free|celiac|coeliac)\b"
            ),
            "high_protein": (
                r"\b(high-protein|high protein|protein-rich|"
                r"protein rich|protein snacks?|protein foods?)\b"
            ),
            "low_sugar": (
                r"\b(low-sugar|low sugar|less sugar|"
                r"sugar-free|sugar free)\b"
            ),
        }

        # Indirect context is weaker than an explicit preference.
        indirect_cues = {
            "high_protein": (
                r"\b(gym|workout|muscle gain)\b"
            ),
            "low_sugar": (
                r"\b(diabetic|diabetes)\b"
            ),
        }

        for cue_map in (explicit_cues, indirect_cues):
            matches = [
                field
                for field, pattern in cue_map.items()
                if field in missing
                and re.search(pattern, context)
            ]

            if matches:
                selected_field = next(
                    (
                        field
                        for field in self.QUESTION_PRIORITY
                        if field in matches
                    ),
                    None,
                )

                if selected_field:
                    return {
                        "status": "needs_preference",
                        "preference": selected_field,
                        "question": self.QUESTIONS[selected_field],
                    }

        # Preserve the original fallback for generic requests.
        selected_field = next(
            (
                field
                for field in self.QUESTION_PRIORITY
                if field in missing
            ),
            None,
        )

        if selected_field is None:
            return None

        return {
            "status": "needs_preference",
            "preference": selected_field,
            "question": self.QUESTIONS[selected_field],
        }

    @staticmethod
    def _parse_boolean(answer: str) -> Optional[bool]:
        """Parse common explicit yes/no responses."""
        value = answer.strip().lower()

        true_answers = {
            "yes",
            "y",
            "true",
            "sure",
            "please do",
            "i do",
            "i prefer that",
            "definitely",
        }

        false_answers = {
            "no",
            "n",
            "false",
            "no preference",
            "not necessary",
            "not needed",
            "either is fine",
        }

        if value in true_answers:
            return True

        if value in false_answers:
            return False

        return None

    @staticmethod
    def _parse_budget(answer: str) -> Optional[float]:
        """
        Parse positive budget amounts such as:
        200, ₹200, Rs. 200, Rs 200, or 200.50.
        """
        value = answer.strip().lower().replace(",", "")

        match = re.search(
            r"(?:₹|rs\.?\s*)?(\d+(?:\.\d{1,2})?)",
            value,
        )

        if not match:
            return None

        amount = float(match.group(1))

        if amount <= 0 or amount > 1_000_000:
            return None

        return amount

    def process_answer(
        self,
        session_id: str,
        preference: str,
        answer: str,
    ) -> dict:
        """Validate and save one answer to the session."""
        if preference not in SessionPreferenceStore.PREFERENCE_FIELDS:
            return {
                "status": "invalid_preference",
                "message": "Unknown preference field.",
            }

        if not answer or not answer.strip():
            return {
                "status": "invalid_answer",
                "preference": preference,
                "message": "Please provide an answer.",
            }

        if preference == "max_price":
            value = self._parse_budget(answer)

            if value is None:
                return {
                    "status": "invalid_answer",
                    "preference": preference,
                    "message": (
                        "Please provide a positive budget, "
                        "such as ₹200."
                    ),
                }
        else:
            value = self._parse_boolean(answer)

            if value is None:
                return {
                    "status": "invalid_answer",
                    "preference": preference,
                    "message": (
                        "Please answer yes or no, or clarify "
                        "your preference."
                    ),
                }

        self.preference_store.update_preference(
            session_id=session_id,
            field=preference,
            value=value,
        )

        return {
            "status": "answer_saved",
            "preference": preference,
            "value": value,
        }
