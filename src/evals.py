"""
Evals — test suite for the Raag Rasa Mirror pipeline.

Tests three things:
  1. Mood → Rasa consistency: does the mood reader assign the correct rasa to known inputs?
  2. Raag → Time-of-day compliance: does the mapper respect prahar rules?
  3. Knowledge base integrity: are all 20 raag files loadable with required fields?

Run with:  python -m src.evals
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Knowledge base integrity tests (no LLM call needed)
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = [
    "raag", "thaat", "time_of_day", "vadi", "samvadi",
    "aaroh", "avaroh", "rasa", "emotional_resonance",
    "therapy_note", "bollywood_references",
]

_RAAGS_DIR = Path(__file__).parent.parent / "data" / "raags"


def test_knowledge_base_integrity() -> list[str]:
    """Check every raag JSON loads and has all required fields. Returns list of failures."""
    failures = []
    files = list(_RAAGS_DIR.glob("*.json"))
    if len(files) == 0:
        failures.append("CRITICAL: No raag JSON files found in data/raags/")
        return failures

    for path in sorted(files):
        try:
            with path.open() as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            failures.append(f"{path.name}: invalid JSON — {e}")
            continue

        for field in _REQUIRED_FIELDS:
            if field not in data:
                failures.append(f"{path.name}: missing field '{field}'")
        if not isinstance(data.get("bollywood_references"), list):
            failures.append(f"{path.name}: bollywood_references must be a list")
        if not isinstance(data.get("rasa"), list):
            failures.append(f"{path.name}: rasa must be a list")

    return failures


# ---------------------------------------------------------------------------
# 2. Mood → Rasa consistency tests
# ---------------------------------------------------------------------------

_MOOD_RASA_CASES = [
    # (user_input, expected_primary_rasa_contains)
    ("I failed my exam and I feel like a failure", "Karuna"),
    ("My husband didn't appreciate the food I made", "Karuna"),
    ("I'm so angry — my colleague took credit for my work", "Raudra"),
    ("I feel peaceful and content after the morning walk", "Shanta"),
    ("I just got promoted! I'm so happy and excited", "Hasya"),
    ("I'm scared about the presentation tomorrow", "Bhayanaka"),
    ("I miss my mother who passed away last year", "Karuna"),
    ("I feel playful and want to dance", "Hasya"),
    ("I feel brave and ready to face the challenge", "Veera"),
]


def test_mood_rasa_consistency(client=None) -> list[str]:
    """
    Run mood reader on known inputs and check rasa assignments.
    Requires GROQ_API_KEY. Returns list of failures (empty = all passed).
    """
    from .agents import mood_reader

    if client is None:
        from groq import Groq
        client = Groq(api_key=os.environ["GROQ_API_KEY"])

    failures = []
    for user_input, expected_rasa in _MOOD_RASA_CASES:
        try:
            state = mood_reader.run(user_input, client=client)
            if expected_rasa.lower() not in state.primary_rasa.lower():
                failures.append(
                    f"RASA MISMATCH | Input: '{user_input[:50]}...' "
                    f"| Expected: {expected_rasa} | Got: {state.primary_rasa}"
                )
        except Exception as e:
            failures.append(f"EXCEPTION on '{user_input[:40]}...': {e}")
    return failures


# ---------------------------------------------------------------------------
# 3. Time-of-day prahar compliance tests
# ---------------------------------------------------------------------------

_TIME_RAAG_RULES: list[tuple[int, list[str], list[str]]] = [
    # (hour, raags_that_SHOULD_be_appropriate, raags_that_should_NOT_be)
    (7, ["Bhairav", "Lalit", "Todi"], ["Yaman", "Darbari"]),
    (10, ["Jaunpuri", "Bhimpalasi"], ["Bhairav", "Malkaans"]),
    (19, ["Yaman", "Bhoopali", "Durga"], ["Bhairav", "Todi"]),
    (22, ["Bageshwari", "Darbari", "Malkaans"], ["Yaman", "Bhairav"]),
]


def test_time_prahar_compliance() -> list[str]:
    """
    Verify get_time_appropriate_raags returns correct raags for each hour.
    No LLM call needed.
    """
    from .tools import get_time_appropriate_raags

    failures = []
    for hour, should_include, should_exclude in _TIME_RAAG_RULES:
        result = get_time_appropriate_raags(hour)
        result_lower = [r.lower() for r in result]

        for raag in should_include:
            if raag.lower() not in result_lower:
                failures.append(
                    f"PRAHAR FAIL: hour={hour:02d}h — {raag} should be in result, got {result}"
                )
        for raag in should_exclude:
            if raag.lower() in result_lower:
                failures.append(
                    f"PRAHAR FAIL: hour={hour:02d}h — {raag} should NOT be in result, got {result}"
                )
    return failures


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all(skip_llm: bool = False) -> None:
    """Run all evals and print a pass/fail summary."""
    total_pass = 0
    total_fail = 0

    def section(name: str, failures: list[str]) -> None:
        nonlocal total_pass, total_fail
        if failures:
            print(f"\n  FAIL  {name} — {len(failures)} failure(s):")
            for f in failures:
                print(f"    • {f}")
            total_fail += len(failures)
        else:
            print(f"\n  PASS  {name}")
            total_pass += 1

    print("=" * 60)
    print("Raag Rasa Mirror — Eval Suite")
    print("=" * 60)

    section("Knowledge base integrity", test_knowledge_base_integrity())
    section("Time/prahar compliance", test_time_prahar_compliance())

    if not skip_llm:
        print("\n  Running LLM-based mood→rasa tests (this uses API credits)...")
        section("Mood → rasa consistency", test_mood_rasa_consistency())
    else:
        print("\n  Skipping LLM tests (--no-llm flag set)")

    print("\n" + "=" * 60)
    print(f"Result: {total_pass} section(s) passed, {total_fail} failure(s) total")
    print("=" * 60)

    if total_fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    skip = "--no-llm" in sys.argv
    run_all(skip_llm=skip)
