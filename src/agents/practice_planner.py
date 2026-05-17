"""
Agent 3: Practice Planner

Takes the selected raag + the user's EmotionalState and generates:
  - A personalised riyaaz (practice) plan (PracticePlan)
  - 2–3 Bollywood/classical song recommendations from the raag's data
  - Assembles the final RaagRecommendation Pydantic object

No tool calls — uses prompt engineering + structured output (Pydantic).
The raag data is injected directly into the prompt via RAG retrieval.
"""
from __future__ import annotations
import json
import os

from groq import Groq
from pydantic import ValidationError

from ..schemas import EmotionalState, PracticePlan, RaagRecommendation, Song
from .. import knowledge
from ..utils import chat_with_retry

_SYSTEM_PROMPT = """\
You are a Hindustani classical vocal guru and music therapist. You are given:
  1. A person's emotional state
  2. The raag selected for them
  3. Full technical data about that raag

Your job is to create a personalised riyaaz (practice) plan and song recommendations,
then return them as a single JSON object.

The plan must be practical, warm, and specific to the person's emotional situation —
not generic. If they are feeling grief, the plan should acknowledge that and work with it.
If they are feeling scattered, the plan should start with centering exercises.

Duration should be proportional to intensity:
  - low intensity → 10–15 minutes
  - medium intensity → 20–30 minutes
  - high intensity → 30–45 minutes (but keep steps gentle)

For songs: choose 2–3 from the bollywood_references provided. Prefer songs with high confidence.
Do NOT invent songs. Use only what is in the raag data provided.

Return ONLY valid JSON matching this schema exactly:
{
  "raag_name": "<string>",
  "thaat": "<string>",
  "time_of_day": "<string from raag data>",
  "is_time_appropriate": <true|false>,
  "rasa_match": "<string>",
  "why": "<2–3 sentence warm explanation for the person>",
  "aaroh": "<string>",
  "avaroh": "<string>",
  "songs": [
    {"title": "...", "film": "...", "year": 0, "singer": "...", "note": "..."}
  ],
  "practice_plan": {
    "duration_minutes": <integer>,
    "steps": ["<step1>", "<step2>", ...],
    "key_phrases": ["<pakad phrase>", ...],
    "mood_intention": "<one sentence>"
  }
}
"""


def _build_user_message(
    state: EmotionalState,
    mapping: dict,
    raag_data: dict,
) -> str:
    songs_preview = json.dumps(raag_data.get("bollywood_references", [])[:5], ensure_ascii=False)
    return (
        f"Person's situation: {state.summary}\n"
        f"Primary rasa: {state.primary_rasa} | Intensity: {state.intensity}\n"
        f"Keywords: {', '.join(state.keywords)}\n\n"
        f"Selected raag: {mapping['raag_name']}\n"
        f"Reasoning: {mapping.get('reasoning', '')}\n"
        f"Time appropriate: {mapping.get('is_time_appropriate', True)}\n\n"
        f"Raag data:\n"
        f"  Thaat: {raag_data.get('thaat', '')}\n"
        f"  Time of day: {raag_data.get('time_of_day', '')}\n"
        f"  Aaroh: {raag_data.get('aaroh', '')}\n"
        f"  Avaroh: {raag_data.get('avaroh', '')}\n"
        f"  Pakad: {raag_data.get('characteristic_pakad', '')}\n"
        f"  Therapy note: {raag_data.get('therapy_note', '')}\n"
        f"  Vocalist notes: {raag_data.get('notes_for_vocalist', '')}\n"
        f"  Songs available:\n{songs_preview}\n\n"
        f"Generate the practice plan and final recommendation JSON now."
    )


def run(
    state: EmotionalState,
    mapping: dict,
    client: Groq | None = None,
) -> RaagRecommendation:
    """
    Generate the final RaagRecommendation.
    mapping must have keys: raag_name, rasa_match, is_time_appropriate, reasoning.
    """
    if client is None:
        client = Groq(api_key=os.environ["GROQ_API_KEY"])

    raag_data = knowledge.get_raag_by_name(mapping["raag_name"])
    if raag_data is None:
        # LLM picked a raag outside our knowledge base — fall back to closest semantic match
        results = knowledge.search(mapping.get("reasoning", mapping["raag_name"]), n_results=1)
        if results:
            raag_data = knowledge.get_raag_by_name(results[0]["metadata"]["raag"])
            mapping = dict(mapping)
            mapping["raag_name"] = results[0]["metadata"]["raag"]
        if raag_data is None:
            raag_data = knowledge.get_raag_by_name("Yaman")  # safe universal fallback
            mapping = dict(mapping)
            mapping["raag_name"] = "Yaman"

    response = chat_with_retry(
        client,
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_message(state, mapping, raag_data)},
        ],
        temperature=0.5,
        max_tokens=800,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or ""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Practice Planner returned invalid JSON: {e}\nRaw: {raw}") from e

    try:
        plan = PracticePlan(**data["practice_plan"])
        songs = [Song(**s) for s in data.get("songs", [])]
        return RaagRecommendation(
            raag_name=data["raag_name"],
            thaat=data["thaat"],
            time_of_day=data["time_of_day"],
            is_time_appropriate=data["is_time_appropriate"],
            rasa_match=data["rasa_match"],
            why=data["why"],
            aaroh=data["aaroh"],
            avaroh=data["avaroh"],
            songs=songs,
            practice_plan=plan,
            emotional_state=state,
        )
    except (KeyError, ValidationError) as e:
        raise ValueError(f"Practice Planner output failed validation: {e}\nData: {data}") from e
