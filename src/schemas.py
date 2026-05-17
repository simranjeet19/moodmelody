from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class EmotionalState(BaseModel):
    """Output of Agent 1 (Mood Reader)."""

    raw_input: str = Field(description="Original user input, unmodified")
    primary_rasa: str = Field(
        description=(
            "Dominant rasa from the nava rasa framework: "
            "Karuna, Shringar, Veera, Raudra, Hasya, Bhayanaka, Bibhatsa, Adbhut, or Shanta"
        )
    )
    secondary_rasa: str | None = Field(
        default=None,
        description="Secondary rasa if a blend is present",
    )
    intensity: Literal["low", "medium", "high"] = Field(
        description="Emotional intensity — low means subtle/background, high means acute"
    )
    keywords: list[str] = Field(
        description="3–6 specific emotional keywords extracted from the input (e.g. 'abandoned', 'morning sadness')"
    )
    time_context: str | None = Field(
        default=None,
        description="Time of day extracted from input if mentioned (e.g. 'morning', 'late night'). None if absent.",
    )
    summary: str = Field(
        description="One concise sentence summarising the emotional situation in warm, human language"
    )


class Song(BaseModel):
    """A Bollywood or classical song reference."""

    title: str
    film: str
    year: int
    singer: str
    note: str


class PracticePlan(BaseModel):
    """Riyaaz plan for the recommended raag."""

    duration_minutes: int = Field(description="Total suggested practice time in minutes")
    steps: list[str] = Field(
        description="Ordered practice steps — each a single clear instruction"
    )
    key_phrases: list[str] = Field(
        description="2–3 characteristic pakad phrases to focus on, written as sargam (e.g. 'Pa Ma Re Sa')"
    )
    mood_intention: str = Field(
        description="One sentence on how to hold the raag emotionally during practice"
    )


class RaagRecommendation(BaseModel):
    """Final output of the full 3-agent pipeline."""

    raag_name: str
    thaat: str
    time_of_day: str
    is_time_appropriate: bool = Field(
        description="True if current time of day matches the raag's prescribed prahar"
    )
    rasa_match: str = Field(
        description="The specific rasa this recommendation addresses"
    )
    why: str = Field(
        description=(
            "2–3 sentence explanation of why this raag suits the user's emotional state, "
            "written in warm, accessible language — not academic"
        )
    )
    aaroh: str
    avaroh: str
    songs: list[Song] = Field(
        description="2–3 songs to listen to that carry the raag's rasa"
    )
    practice_plan: PracticePlan
    emotional_state: EmotionalState = Field(
        description="The EmotionalState parsed by Agent 1 — preserved for logging"
    )
