"""
Tool functions and their Groq JSON schema definitions.

These are called by Agent 2 (Raag Mapper) via Groq tool calling.
Each Python function must exactly match the schema it declares.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

from . import knowledge


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def get_current_time_context() -> dict:
    """
    Return the current time of day and which prahar (watch) it falls into.
    Prahar system: 6–9am morning, 9am–12pm late morning, 12–3pm afternoon,
    3–6pm late afternoon, 6–9pm evening, 9pm–12am late night, 12–3am deep night.
    """
    now = datetime.now()
    hour = now.hour

    if 6 <= hour < 9:
        prahar = "Morning (6am–9am) — Bhairav, Lalit, Todi"
    elif 9 <= hour < 12:
        prahar = "Late morning (9am–12pm) — Jaunpuri, Asavari, Bhimpalasi"
    elif 12 <= hour < 15:
        prahar = "Afternoon (12pm–3pm) — Sarang family, Multani"
    elif 15 <= hour < 18:
        prahar = "Late afternoon (3pm–6pm) — Puriya Dhanashri, Marwa, Kafi, Bageshwari"
    elif 18 <= hour < 21:
        prahar = "Evening (6pm–9pm) — Yaman, Bhupali, Durga, Khamaj, Kedar"
    elif 21 <= hour < 24:
        prahar = "Late night (9pm–12am) — Bageshwari, Darbari, Malkaans, Rageshwari, Hansdhwani"
    else:
        prahar = "Deep night (12am–3am) — Darbari, Malkaans"

    return {
        "current_time": now.strftime("%H:%M"),
        "prahar": prahar,
        "hour": hour,
    }


def search_raags_by_emotion(query: str, n_results: int = 3) -> list[dict]:
    """
    Semantic search over the raag knowledge base using an emotion/mood query.
    Returns the top matching raags with their metadata and relevant text.
    """
    results = knowledge.search(query, n_results=n_results)
    return [
        {
            "raag_name": r["metadata"]["raag"],
            "thaat": r["metadata"]["thaat"],
            "time_of_day": r["metadata"]["time_of_day"],
            "rasa": r["metadata"]["rasa"],
            "vadi": r["metadata"]["vadi"],
            "aaroh": r["metadata"]["aaroh"],
            "avaroh": r["metadata"]["avaroh"],
            "relevance_score": round(1.0 - r["distance"], 4),
            "context_excerpt": r["document"][:400],
        }
        for r in results
    ]


def get_raag_details(raag_name: str) -> dict | None:
    """
    Retrieve the full data for a single raag by name.
    Returns all fields including bollywood_references, therapy_note, and practice hints.
    Returns None if the raag is not found.
    """
    return knowledge.get_raag_by_name(raag_name)


def get_time_appropriate_raags(hour: int) -> list[str]:
    """
    Return raag names that are prescribed for the given hour (0–23).
    Follows the traditional prahar system.
    """
    prahar_map = {
        range(6, 9): ["Bhairav", "Lalit", "Todi", "Ramkali", "Vibhas"],
        range(9, 12): ["Jaunpuri", "Asavari", "Bhimpalasi", "Sarang"],
        range(12, 15): ["Bhimpalasi", "Multani"],
        range(15, 18): ["Puriya Dhanashri", "Marwa", "Kafi", "Bageshwari"],
        range(18, 21): ["Yaman", "Bhoopali", "Durga", "Khamaj", "Kedar"],
        range(21, 24): ["Bageshwari", "Darbari", "Malkaans", "Rageshwari", "Hansdhwani"],
        range(0, 6): ["Darbari", "Malkaans", "Bhairav"],
    }
    for hour_range, raags in prahar_map.items():
        if hour in hour_range:
            return raags
    return []


# ---------------------------------------------------------------------------
# Groq tool schema definitions (function calling)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time_context",
            "description": (
                "Get the current time and the prahar (time-of-day watch) it falls into. "
                "Use this to check which raags are traditionally appropriate right now."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_raags_by_emotion",
            "description": (
                "Semantic search over the raag knowledge base. "
                "Pass a natural language emotion/mood description and get the most relevant raags back. "
                "Use this as the primary retrieval step before picking a final raag."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Emotion or mood description to search with (e.g. 'feeling abandoned and sad at night')",
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of raags to retrieve (default 3, max 5)",
                        "default": 3,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_raag_details",
            "description": (
                "Fetch the full data for a single raag by name — including Bollywood references, "
                "therapy note, aaroh/avaroh, and vocalist tips. "
                "Use this after narrowing down candidates to confirm the best fit."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "raag_name": {
                        "type": "string",
                        "description": "Exact raag name as returned by search_raags_by_emotion (e.g. 'Yaman', 'Bhairavi')",
                    }
                },
                "required": ["raag_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_time_appropriate_raags",
            "description": (
                "Return raag names that are traditionally appropriate for a given hour of the day. "
                "Use this to filter or validate candidates against the prahar system."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "hour": {
                        "type": "integer",
                        "description": "Hour in 24-hour format (0–23)",
                    }
                },
                "required": ["hour"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Dispatcher — called by agents to execute any tool by name
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, callable] = {
    "get_current_time_context": get_current_time_context,
    "search_raags_by_emotion": search_raags_by_emotion,
    "get_raag_details": get_raag_details,
    "get_time_appropriate_raags": get_time_appropriate_raags,
}


def dispatch_tool(name: str, arguments: str | dict) -> str:
    """
    Execute a tool by name with JSON arguments.
    Returns result as a JSON string for the Groq tool message.
    """
    if not arguments:
        kwargs = {}
    elif isinstance(arguments, str):
        parsed = json.loads(arguments)
        kwargs = parsed if isinstance(parsed, dict) else {}
    elif isinstance(arguments, dict):
        kwargs = arguments
    else:
        kwargs = {}

    fn = TOOL_REGISTRY.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {name}"})

    result = fn(**kwargs)
    return json.dumps(result, ensure_ascii=False, default=str)
