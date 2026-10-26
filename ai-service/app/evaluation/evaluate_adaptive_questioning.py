
"""
Simulated evaluation of adaptive preference questioning.

This evaluates policy selection and catalog-level constraint feasibility only.
It is NOT real-user evidence or recommendation-ranking evaluation.

Scenarios include aligned, neutral, and mixed contexts. Synthetic answers are
generated for the preference actually asked. Target-constraint compliance is
reported only when the target preference was captured; otherwise it is NaN.
"""

from datetime import datetime
from pathlib import Path

import pandas as pd

from app.genai.intent_parser import UserIntent
from app.preference_questions import PreferenceQuestionManager
from app.session_preferences import SessionPreferenceStore


PRODUCTS_PATH = Path("/app/data/phase1/master_products.csv")
OUTPUT_DIR = Path("/validation/evaluation")
CATEGORY = "Snacks & Branded Foods"
FIXED_BUDGET_ANSWER = "₹200"


SCENARIOS = [
    # Aligned contexts: a cue points to the intended preference.
    {
        "scenario_id": "aligned_budget",
        "context_type": "aligned",
        "purpose": "I want affordable choices for my snacks",
        "target_preference": "max_price",
        "target_value": 200.0,
    },
    {
        "scenario_id": "aligned_vegetarian",
        "context_type": "aligned",
        "purpose": "I prefer meat-free options for my snacks",
        "target_preference": "vegetarian",
        "target_value": True,
    },
    {
        "scenario_id": "aligned_vegan",
        "context_type": "aligned",
        "purpose": "I prefer plant-based choices for my snacks",
        "target_preference": "vegan",
        "target_value": True,
    },
    {
        "scenario_id": "aligned_gluten_free",
        "context_type": "aligned",
        "purpose": "I need gluten-free choices for my snacks",
        "target_preference": "gluten_free",
        "target_value": True,
    },
    {
        "scenario_id": "aligned_high_protein",
        "context_type": "aligned",
        "purpose": "I want snacks for my gym routine",
        "target_preference": "high_protein",
        "target_value": True,
    },
    {
        "scenario_id": "aligned_low_sugar",
        "context_type": "aligned",
        "purpose": "I want less sugar in my snacks",
        "target_preference": "low_sugar",
        "target_value": True,
    },

    # Neutral contexts: no explicit preference cue.
    {
        "scenario_id": "neutral_budget",
        "context_type": "neutral",
        "purpose": "I am looking for snacks",
        "target_preference": "max_price",
        "target_value": 200.0,
    },
    {
        "scenario_id": "neutral_vegetarian",
        "context_type": "neutral",
        "purpose": "I am looking for snacks",
        "target_preference": "vegetarian",
        "target_value": True,
    },
    {
        "scenario_id": "neutral_vegan",
        "context_type": "neutral",
        "purpose": "I am looking for snacks",
        "target_preference": "vegan",
        "target_value": True,
    },
    {
        "scenario_id": "neutral_gluten_free",
        "context_type": "neutral",
        "purpose": "I am looking for snacks",
        "target_preference": "gluten_free",
        "target_value": True,
    },
    {
        "scenario_id": "neutral_high_protein",
        "context_type": "neutral",
        "purpose": "I am looking for snacks",
        "target_preference": "high_protein",
        "target_value": True,
    },
    {
        "scenario_id": "neutral_low_sugar",
        "context_type": "neutral",
        "purpose": "I am looking for snacks",
        "target_preference": "low_sugar",
        "target_value": True,
    },

    # Mixed contexts: two cues compete for the next question.
    {
        "scenario_id": "mixed_gym_low_sugar_target_protein",
        "context_type": "mixed",
        "purpose": "I want snacks for my gym routine and less sugar",
        "target_preference": "high_protein",
        "target_value": True,
    },
    {
        "scenario_id": "mixed_gym_low_sugar_target_sugar",
        "context_type": "mixed",
        "purpose": "I want snacks for my gym routine and less sugar",
        "target_preference": "low_sugar",
        "target_value": True,
    },
]


METHODS = (
    "no_elicitation",
    "fixed_question",
    "adaptive_question",
)


def normalize_bool_column(series):
    """Normalize Boolean CSV values while preserving missing values."""
    truthy = {"true", "1", "yes", "y"}
    falsy = {"false", "0", "no", "n"}

    normalized = series.astype(str).str.strip().str.lower()

    return normalized.map(
        lambda value: True if value in truthy
        else False if value in falsy
        else pd.NA
    ).astype("boolean")


def load_catalog():
    if not PRODUCTS_PATH.exists():
        raise FileNotFoundError(
            f"Product catalog not found: {PRODUCTS_PATH}"
        )

    products = pd.read_csv(PRODUCTS_PATH)

    required = {
        "product_id",
        "category",
        "price",
        "vegetarian",
        "vegan",
        "gluten_free",
        "protein_g",
        "sugar_g",
    }

    missing = required - set(products.columns)

    if missing:
        raise ValueError(
            f"Product catalog is missing columns: {sorted(missing)}"
        )

    products["price"] = pd.to_numeric(
        products["price"], errors="coerce"
    )
    products["protein_g"] = pd.to_numeric(
        products["protein_g"], errors="coerce"
    )
    products["sugar_g"] = pd.to_numeric(
        products["sugar_g"], errors="coerce"
    )

    for field in ("vegetarian", "vegan", "gluten_free"):
        products[field] = normalize_bool_column(products[field])

    products = products.loc[
        products["category"].eq(CATEGORY)
    ].copy()

    if products.empty:
        raise ValueError(
            f"No products found for category {CATEGORY!r}"
        )

    return products


def build_intent(scenario):
    return UserIntent(
        query="snacks",
        category=CATEGORY,
        purpose=scenario["purpose"],
        intent="search",
        max_price=None,
        vegetarian=None,
        vegan=None,
        gluten_free=None,
        high_protein=None,
        low_sugar=None,
    )


def get_question(method, manager, intent, session_id):
    if method == "no_elicitation":
        return None

    if method == "fixed_question":
        return {
            "status": "needs_preference",
            "preference": "max_price",
            "question": manager.QUESTIONS["max_price"],
        }

    return manager.select_question(
        session_id, intent, CATEGORY
    )


def synthetic_answer(selected, scenario):
    """
    Simulate an answer to the question actually asked.

    If the selected preference is the target, answer with its target value.
    Otherwise, use a deterministic synthetic answer for the non-target slot.
    """
    if selected == scenario["target_preference"]:
        value = scenario["target_value"]

        if selected == "max_price":
            return f"₹{value:g}"

        return "yes" if value else "no"

    if selected == "max_price":
        return FIXED_BUDGET_ANSWER

    return "no"


def apply_known_constraints(products, state):
    """Apply the same fields and thresholds as the current retriever."""
    filtered = products.copy()

    if state.max_price is not None:
        filtered = filtered.loc[
            filtered["price"] <= state.max_price
        ]

    if state.vegetarian is not None:
        filtered = filtered.loc[
            filtered["vegetarian"]
            .eq(state.vegetarian)
            .fillna(False)
        ]

    if state.vegan is not None:
        filtered = filtered.loc[
            filtered["vegan"]
            .eq(state.vegan)
            .fillna(False)
        ]

    if state.gluten_free is not None:
        filtered = filtered.loc[
            filtered["gluten_free"]
            .eq(state.gluten_free)
            .fillna(False)
        ]

    if state.high_protein is True:
        filtered = filtered.loc[
            filtered["protein_g"] >= 10.0
        ]

    if state.low_sugar is True:
        filtered = filtered.loc[
            filtered["sugar_g"] <= 5.0
        ]

    return filtered


def target_satisfaction(products, scenario):
    """Fraction of products satisfying the scenario's target constraint."""
    field = scenario["target_preference"]
    target = scenario["target_value"]

    if products.empty:
        return 0.0

    if field == "max_price":
        satisfied = products["price"] <= float(target)

    elif field in {"vegetarian", "vegan", "gluten_free"}:
        satisfied = products[field].eq(bool(target)).fillna(False)

    elif field == "high_protein":
        satisfied = products["protein_g"] >= 10.0

    elif field == "low_sugar":
        satisfied = products["sugar_g"] <= 5.0

    else:
        raise ValueError(
            f"Unsupported target preference: {field}"
        )

    return float(satisfied.mean())


def evaluate():
    products = load_catalog()
    rows = []

    for scenario in SCENARIOS:
        for method in METHODS:
            session_id = (
                f"{method}:{scenario['scenario_id']}"
            )

            store = SessionPreferenceStore()
            manager = PreferenceQuestionManager(store)
            intent = build_intent(scenario)

            question = get_question(
                method, manager, intent, session_id
            )

            asked = question is not None
            selected = (
                question["preference"] if asked else None
            )

            answer_saved = False

            if asked:
                answer = synthetic_answer(selected, scenario)

                answer_result = manager.process_answer(
                    session_id, selected, answer
                )

                answer_saved = (
                    answer_result.get("status") == "answer_saved"
                )

            state = store.get(session_id)

            candidate_products = apply_known_constraints(
                products, state
            )

            matches_target = bool(
                asked
                and selected == scenario["target_preference"]
            )

            target_captured = bool(
                answer_saved and matches_target
            )

            # Only report target compliance when the target
            # preference was actually captured.
            target_compliance = (
                target_satisfaction(candidate_products, scenario)
                if target_captured
                else float("nan")
            )

            rows.append({
                "scenario_id": scenario["scenario_id"],
                "context_type": scenario["context_type"],
                "purpose": scenario["purpose"],
                "method": method,
                "category": CATEGORY,
                "target_preference": scenario["target_preference"],
                "selected_preference": selected or "",
                "question_asked": int(asked),
                "selected_question_matches_latent_target": int(
                    matches_target
                ),
                "answer_saved": int(answer_saved),
                "target_preference_captured": int(
                    target_captured
                ),
                "catalog_products_before_constraints": int(
                    len(products)
                ),
                "catalog_products_after_known_constraints": int(
                    len(candidate_products)
                ),
                "catalog_empty_after_constraints": int(
                    candidate_products.empty
                ),
                "target_compliance_rate_when_captured": (
                    target_compliance
                ),
                "evaluation_type": (
                    "simulated_policy_and_catalog_constraint_check"
                ),
            })

    detail = pd.DataFrame(rows)

    summary = (
        detail.groupby(
            ["context_type", "method"], sort=False
        )
        .agg(
            scenarios=("scenario_id", "count"),
            mean_questions_asked=("question_asked", "mean"),
            target_question_match_rate=(
                "selected_question_matches_latent_target", "mean"
            ),
            answer_saved_rate=("answer_saved", "mean"),
            target_preference_capture_rate=(
                "target_preference_captured", "mean"
            ),
            mean_catalog_products_after_constraints=(
                "catalog_products_after_known_constraints", "mean"
            ),
            empty_catalog_rate=(
                "catalog_empty_after_constraints", "mean"
            ),
            mean_target_compliance_rate_when_captured=(
                "target_compliance_rate_when_captured", "mean"
            ),
        )
        .reset_index()
    )

    summary["evaluation_type"] = (
        "simulated_policy_and_catalog_constraint_check"
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    detail_path = OUTPUT_DIR / (
        f"adaptive_question_scenarios_v2_{stamp}.csv"
    )
    summary_path = OUTPUT_DIR / (
        f"adaptive_question_summary_v2_{stamp}.csv"
    )

    detail.to_csv(detail_path, index=False)
    summary.to_csv(summary_path, index=False)

    print(
        "\nEVALUATION TYPE: SIMULATED; "
        "NOT REAL-USER OR RANKING EVIDENCE"
    )
    print("Scenarios: aligned, neutral, and mixed-context")
    print(f"Category: {CATEGORY}")
    print(f"Catalog products in category: {len(products)}")

    print("\nSummary by context type and method:")
    print(summary.to_string(index=False))

    print(f"\nScenario results: {detail_path}")
    print(f"Summary results:  {summary_path}")
    print(
        "\nHistorical and previous adaptive-evaluation "
        "CSV files were not modified."
    )


if __name__ == "__main__":
    evaluate()
