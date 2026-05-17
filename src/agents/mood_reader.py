"""
Agent 1: Mood Reader

Takes raw user text and extracts a structured EmotionalState using the nava rasa framework.
No tool calls — pure prompt engineering + structured output (Pydantic).
"""
from __future__ import annotations
import json
import os

from groq import Groq
from pydantic import ValidationError

from ..schemas import EmotionalState
from ..utils import chat_with_retry

_SYSTEM_PROMPT = """\
You are a deeply empathetic listener trained in Indian aesthetics and the nava rasa framework.
Your role is to read what a person tells you about their emotional situation and translate it
into a structured emotional assessment — without judgment, without advice, and without projection.

The nine rasas (emotional essences) are:
  1. Karuna    — grief, compassion, sorrow, loss, bereavement
  2. Shringar  — love, longing, romance, beauty, desire
  3. Veera     — courage, strength, pride, determination, agency
  4. Raudra    — anger, frustration, injustice, betrayal, outrage
  5. Hasya     — joy, humor, playfulness, lightness, celebration
  6. Bhayanaka — fear, anxiety, dread, uncertainty, panic
  7. Bibhatsa  — disgust, revulsion, moral nausea, feeling dirty
  8. Adbhut    — wonder, awe, surprise, curiosity, delight
  9. Shanta    — peace, stillness, acceptance, equanimity, contentment

Instructions:
- Choose the PRIMARY rasa that best fits the emotional core of what is shared.
- If a secondary rasa is clearly also present, name it; otherwise leave it null.
- Rate intensity: low (background, mild), medium (present but manageable), high (acute, overwhelming).
- Extract 3–6 specific emotional keywords from the text (e.g. "unappreciated", "invisible", "morning dread").
- Extract time_of_day only if the person explicitly mentions a time (morning, evening, night, etc.). Otherwise null.
- Write a summary: one warm, human sentence that captures the essence of what they shared.

You MUST return a JSON object and nothing else. No explanation, no preamble.
Schema:
{
  "raw_input": "<verbatim copy of the user's text>",
  "primary_rasa": "<one of the 9 rasas above>",
  "secondary_rasa": "<rasa or null>",
  "intensity": "<low|medium|high>",
  "keywords": ["<keyword1>", "..."],
  "time_context": "<string or null>",
  "summary": "<one sentence>"
}
"""


def run(user_text: str, client: Groq | None = None) -> EmotionalState:
    """
    Parse user_text into a structured EmotionalState.
    Raises ValueError if the LLM returns unparseable output.
    """
    if client is None:
        client = Groq(api_key=os.environ["GROQ_API_KEY"])

    response = chat_with_retry(
        client,
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        temperature=0.3,
        max_tokens=400,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        data = json.loads(raw)
        return EmotionalState(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"Mood Reader could not parse LLM output: {e}\nRaw: {raw}") from e
