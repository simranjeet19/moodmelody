"""
LLMOps logger — writes every session to sessions.jsonl.

Each line is a JSON record capturing:
  - timestamp
  - user input
  - emotional state (rasa, intensity, keywords)
  - raag recommended
  - time_of_day appropriateness
  - full recommendation for replay/analysis

This file is the basis for offline pattern analysis:
  "What rasa does this user most frequently present with?"
  "Which raags are recommended most at what time?"
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

from .schemas import RaagRecommendation

_LOG_PATH = Path(__file__).parent.parent / "sessions.jsonl"


def log_session(recommendation: RaagRecommendation) -> None:
    """Append one session record to sessions.jsonl."""
    state = recommendation.emotional_state
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_input": state.raw_input,
        "primary_rasa": state.primary_rasa,
        "secondary_rasa": state.secondary_rasa,
        "intensity": state.intensity,
        "keywords": state.keywords,
        "time_context": state.time_context,
        "raag_recommended": recommendation.raag_name,
        "thaat": recommendation.thaat,
        "is_time_appropriate": recommendation.is_time_appropriate,
        "rasa_match": recommendation.rasa_match,
        "practice_duration_minutes": recommendation.practice_plan.duration_minutes,
        "songs": [s.title for s in recommendation.songs],
        "why": recommendation.why,
    }
    with _LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_sessions() -> list[dict]:
    """Load all past session records from sessions.jsonl. Returns [] if file absent."""
    if not _LOG_PATH.exists():
        return []
    records = []
    with _LOG_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def summarise_patterns() -> dict:
    """
    Return a simple frequency analysis over all logged sessions.
    Useful for the LLMOps dashboard / observability.
    """
    sessions = load_sessions()
    if not sessions:
        return {"total_sessions": 0}

    rasa_counts: dict[str, int] = {}
    raag_counts: dict[str, int] = {}
    intensity_counts: dict[str, int] = {}

    for s in sessions:
        r = s.get("primary_rasa", "unknown")
        rasa_counts[r] = rasa_counts.get(r, 0) + 1

        raag = s.get("raag_recommended", "unknown")
        raag_counts[raag] = raag_counts.get(raag, 0) + 1

        intensity = s.get("intensity", "unknown")
        intensity_counts[intensity] = intensity_counts.get(intensity, 0) + 1

    return {
        "total_sessions": len(sessions),
        "rasa_frequency": dict(sorted(rasa_counts.items(), key=lambda x: -x[1])),
        "raag_frequency": dict(sorted(raag_counts.items(), key=lambda x: -x[1])),
        "intensity_distribution": intensity_counts,
        "time_appropriate_pct": round(
            sum(1 for s in sessions if s.get("is_time_appropriate")) / len(sessions) * 100, 1
        ),
    }
