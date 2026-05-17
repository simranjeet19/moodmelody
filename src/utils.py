"""Shared Groq call wrapper with automatic retry on rate-limit (429) errors."""
from __future__ import annotations
import time
import re
from typing import Any


def chat_with_retry(client, max_retries: int = 4, **kwargs) -> Any:
    """
    Drop-in replacement for client.chat.completions.create(**kwargs).
    On a 429 rate-limit error, parses the suggested wait time from the
    error message and sleeps before retrying. Falls back to exponential
    backoff if no wait time is found.
    """
    delay = 2.0
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as e:
            msg = str(e)
            if "429" not in msg and "rate_limit" not in msg.lower():
                raise   # not a rate-limit error — don't swallow it

            if attempt == max_retries - 1:
                raise   # exhausted retries

            # Try to extract the suggested wait time from the error message
            # e.g. "Please try again in 1.54s"
            match = re.search(r"try again in ([\d.]+)s", msg)
            wait = float(match.group(1)) + 0.5 if match else delay
            time.sleep(wait)
            delay *= 2   # exponential backoff for subsequent retries
