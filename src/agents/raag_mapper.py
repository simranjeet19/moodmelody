"""
Agent 2: Raag Mapper

Takes an EmotionalState and uses RAG (ChromaDB semantic search) + Groq tool calling
to select the single best-fitting raag. Returns the raag name and reasoning.

Tool calling loop:
  1. LLM receives emotional state and available tools.
  2. LLM calls search_raags_by_emotion to retrieve candidates.
  3. LLM calls get_current_time_context to check prahar.
  4. LLM calls get_raag_details on its top candidate.
  5. LLM makes a final selection with reasoning.
"""
from __future__ import annotations
import json
import os
from typing import Any

from groq import Groq

from ..schemas import EmotionalState
from ..tools import TOOL_DEFINITIONS, dispatch_tool
from ..utils import chat_with_retry

_AVAILABLE_RAAGS = [
    "Bageshwari", "Bhairav", "Bhairavi", "Bhimpalasi", "Bhoopali",
    "Bilawal", "Darbari", "Durga", "Hansdhwani", "Jaunpuri",
    "Kafi", "Kedar", "Khamaj", "Lalit", "Malkaans",
    "Marwa", "Puriya Dhanashri", "Rageshwari", "Todi", "Yaman",
]

_SYSTEM_PROMPT = f"""\
You are a master of Hindustani classical music — a guru who understands both the grammar of raags
and the science of rasa therapy. Your task is to select the single most appropriate raag for
a person given their emotional state.

CRITICAL CONSTRAINT: You may ONLY choose from these 20 raags. Do not suggest any other raag.
Available raags: {', '.join(_AVAILABLE_RAAGS)}

You have access to four tools:
  - search_raags_by_emotion: semantic search over these 20 raags by emotional resonance
  - get_current_time_context: find what prahar (time-of-day watch) it is now
  - get_raag_details: fetch full data for a specific raag
  - get_time_appropriate_raags: get raags valid for a given hour

PROCESS (follow this exactly):
1. Call get_current_time_context first to understand the current prahar.
2. Call search_raags_by_emotion with the emotional keywords from the user's state.
3. If you are uncertain between two candidates, call get_raag_details on each.
4. Select the best raag from the available list — prefer one that fits BOTH the rasa AND the time of day.
   If no time-appropriate raag fits the rasa, choose the rasa fit and flag the time mismatch.
5. Return your final answer as a JSON object with these fields:
   {{
     "raag_name": "<must be one of the 20 raags listed above, exact spelling>",
     "rasa_match": "<which rasa this addresses>",
     "is_time_appropriate": <true|false>,
     "reasoning": "<2–3 sentences explaining why this raag fits this person right now>"
   }}

Be warm and specific in your reasoning — speak to the person's actual situation, not abstract theory.
"""


def _build_user_message(state: EmotionalState) -> str:
    return (
        f"Emotional state:\n"
        f"  Summary: {state.summary}\n"
        f"  Primary rasa: {state.primary_rasa}\n"
        f"  Secondary rasa: {state.secondary_rasa or 'none'}\n"
        f"  Intensity: {state.intensity}\n"
        f"  Keywords: {', '.join(state.keywords)}\n"
        f"  Time context from user: {state.time_context or 'not mentioned'}\n\n"
        f"Original input: \"{state.raw_input}\"\n\n"
        f"Please select the most appropriate raag using your tools."
    )


def run(state: EmotionalState, client: Groq | None = None) -> dict[str, Any]:
    """
    Run the tool-calling loop and return a dict:
      {raag_name, rasa_match, is_time_appropriate, reasoning}
    """
    if client is None:
        client = Groq(api_key=os.environ["GROQ_API_KEY"])

    messages: list[dict] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_message(state)},
    ]

    # Agentic loop — keep going until the LLM stops calling tools
    while True:
        response = chat_with_retry(
            client,
            model="llama-3.1-8b-instant",
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
            temperature=0.4,
            max_tokens=600,
        )

        choice = response.choices[0]
        msg = choice.message
        messages.append(msg.model_dump(exclude_none=True))

        # If no tool calls, this is the final answer
        if not msg.tool_calls:
            break

        # Execute each tool call and feed results back
        for tc in msg.tool_calls:
            result = dispatch_tool(tc.function.name, tc.function.arguments)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                }
            )

    # Parse the final text response as JSON
    final_text = choice.message.content or ""
    try:
        # LLM may wrap the JSON in markdown; strip it
        cleaned = final_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: return raw text under a 'reasoning' key so the pipeline doesn't crash
        return {
            "raag_name": "Yaman",
            "rasa_match": state.primary_rasa,
            "is_time_appropriate": True,
            "reasoning": final_text,
        }
