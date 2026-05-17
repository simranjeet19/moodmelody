"""
CLI entry point — Raag Rasa Mirror

Usage:
  python -m src.main                        # interactive loop
  python -m src.main --build                # (re)build ChromaDB index then exit
  python -m src.main --stats                # show LLMOps session statistics
  python -m src.main --eval                 # run eval suite (no LLM)
  python -m src.main "my mood text here"    # single one-shot query
"""
from __future__ import annotations
import os
import sys
from dotenv import load_dotenv

load_dotenv()


def _check_env() -> None:
    if not os.environ.get("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY not set. Add it to your .env file.")
        sys.exit(1)


def _build_index() -> None:
    print("Building ChromaDB knowledge index...")
    from .knowledge import build_collection
    build_collection(force=True)
    print("Done. 20 raags embedded and stored.")


def _print_recommendation(rec) -> None:
    time_badge = "✓ Time appropriate" if rec.is_time_appropriate else "⚠ Not traditional time"

    print("\n" + "━" * 56)
    print(f"  Raag: {rec.raag_name}  ({rec.thaat} thaat)")
    print(f"  {time_badge}  |  Best time: {rec.time_of_day}")
    print(f"  Rasa: {rec.rasa_match}")
    print()
    print(f"  Why this raag for you:")
    # Wrap at 52 chars
    words = rec.why.split()
    line, lines = [], []
    for w in words:
        if sum(len(x) + 1 for x in line) + len(w) > 52:
            lines.append("  " + " ".join(line))
            line = [w]
        else:
            line.append(w)
    if line:
        lines.append("  " + " ".join(line))
    print("\n".join(lines))

    print()
    print(f"  Scale:")
    print(f"    ↑  {rec.aaroh}")
    print(f"    ↓  {rec.avaroh}")

    print()
    print(f"  Practice plan  ({rec.practice_plan.duration_minutes} min)")
    for i, step in enumerate(rec.practice_plan.steps, 1):
        print(f"    {i}. {step}")
    print(f"  Key phrases: {', '.join(rec.practice_plan.key_phrases)}")
    print(f"  Hold in mind: {rec.practice_plan.mood_intention}")

    print()
    print("  Songs to listen to:")
    for song in rec.songs:
        print(f"    ♪  {song.title}")
        print(f"       {song.singer}  ·  {song.film}  ({song.year})")
        if song.note:
            print(f"       {song.note}")
    print("━" * 56 + "\n")


def _run_pipeline(user_text: str) -> None:
    from groq import Groq
    from .knowledge import build_collection
    from .agents import mood_reader, raag_mapper, practice_planner
    from .logger import log_session

    # Ensure index exists (no-op if already built)
    build_collection()

    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    print("\nReading your mood...")
    state = mood_reader.run(user_text, client=client)
    print(f"  → {state.primary_rasa} rasa detected  |  intensity: {state.intensity}")
    print(f"  → {state.summary}")

    print("\nSelecting raag (using RAG + tool calling)...")
    mapping = raag_mapper.run(state, client=client)
    print(f"  → Selected: {mapping['raag_name']}")

    print("\nBuilding your practice plan...")
    recommendation = practice_planner.run(state, mapping, client=client)

    log_session(recommendation)
    _print_recommendation(recommendation)


def _show_stats() -> None:
    from .logger import summarise_patterns
    import json
    patterns = summarise_patterns()
    print("\nSession statistics (from sessions.jsonl):")
    print(json.dumps(patterns, indent=2, ensure_ascii=False))


def _interactive_loop() -> None:
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║        Raag Rasa Mirror  🎵                  ║")
    print("║  Tell me how you feel — get a raag to sing   ║")
    print("╚══════════════════════════════════════════════╝")
    print("  Type your mood or situation in plain language.")
    print("  Commands: 'stats', 'quit' / 'exit'\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in {"quit", "exit", "q"}:
            print("Goodbye.")
            break
        if user_input.lower() == "stats":
            _show_stats()
            continue

        try:
            _run_pipeline(user_input)
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.\n")


def main() -> None:
    _check_env()
    args = sys.argv[1:]

    if "--build" in args:
        _build_index()
    elif "--stats" in args:
        _show_stats()
    elif "--eval" in args:
        from .evals import run_all
        run_all(skip_llm="--no-llm" in args)
    elif args:
        # Single one-shot query passed as CLI argument
        _run_pipeline(" ".join(args))
    else:
        _interactive_loop()


if __name__ == "__main__":
    main()
