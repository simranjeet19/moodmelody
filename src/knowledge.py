from __future__ import annotations
import json
from pathlib import Path

import chromadb
from fastembed import TextEmbedding

_RAAGS_DIR = Path(__file__).parent.parent / "data" / "raags"
_CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
_COLLECTION_NAME = "raags"
_EMBED_MODEL = "BAAI/bge-small-en-v1.5"

_embedder: TextEmbedding | None = None


def _get_embedder() -> TextEmbedding:
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedding(model_name=_EMBED_MODEL)
    return _embedder


def _raag_to_document(data: dict) -> str:
    """Convert raag JSON to a richly worded text document for semantic embedding."""
    rasa = ", ".join(data.get("rasa", []))
    resonance = "; ".join(data.get("emotional_resonance", []))
    parts = [
        f"Raag: {data['raag']}",
        f"Thaat: {data.get('thaat', '')}",
        f"Time of day: {data.get('time_of_day', '')}",
        f"Vadi: {data.get('vadi', '')}. Samvadi: {data.get('samvadi', '')}",
        f"Rasa: {rasa}",
        f"Emotional resonance: {resonance}",
        f"Therapy note: {data.get('therapy_note', '')}",
        f"Aaroh: {data.get('aaroh', '')}",
        f"Avaroh: {data.get('avaroh', '')}",
        f"Characteristic pakad: {data.get('characteristic_pakad', '')}",
    ]
    notes = data.get("notes_for_vocalist", "")
    if notes:
        parts.append(f"Vocalist notes: {notes}")
    return "\n".join(parts)


def _load_all_raags() -> list[tuple[str, dict]]:
    raags = []
    for path in sorted(_RAAGS_DIR.glob("*.json")):
        with path.open() as f:
            data = json.load(f)
        raags.append((path.stem, data))
    return raags


def build_collection(force: bool = False) -> None:
    """
    Embed all raag JSON files and persist them in ChromaDB.
    Idempotent — skips rebuild unless force=True.
    """
    client = chromadb.PersistentClient(path=str(_CHROMA_DIR))
    existing_names = [c.name for c in client.list_collections()]

    if _COLLECTION_NAME in existing_names:
        if not force:
            return
        client.delete_collection(_COLLECTION_NAME)

    collection = client.create_collection(_COLLECTION_NAME)
    raags = _load_all_raags()
    embedder = _get_embedder()

    ids, documents, metadatas = [], [], []
    for stem, data in raags:
        ids.append(stem)
        documents.append(_raag_to_document(data))
        metadatas.append(
            {
                "raag": data["raag"],
                "thaat": data.get("thaat", ""),
                "time_of_day": data.get("time_of_day", ""),
                "rasa": ", ".join(data.get("rasa", [])),
                "vadi": data.get("vadi", ""),
                "aaroh": data.get("aaroh", ""),
                "avaroh": data.get("avaroh", ""),
            }
        )

    embeddings = list(embedder.embed(documents))
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=[e.tolist() for e in embeddings],
        metadatas=metadatas,
    )
    print(f"Built ChromaDB collection with {len(ids)} raags.")


def search(query: str, n_results: int = 3) -> list[dict]:
    """
    Semantic search over raag documents.
    Returns list of dicts: {id, document, metadata, distance}.
    Lower distance = closer match.
    """
    client = chromadb.PersistentClient(path=str(_CHROMA_DIR))
    collection = client.get_collection(_COLLECTION_NAME)
    embedder = _get_embedder()

    query_vec = list(embedder.embed([query]))[0].tolist()
    results = collection.query(
        query_embeddings=[query_vec],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    return [
        {
            "id": results["ids"][0][i],
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        }
        for i in range(len(results["ids"][0]))
    ]


def get_raag_by_name(name: str) -> dict | None:
    """Load full raag JSON by raag name (case-insensitive). Returns None if not found."""
    for path in _RAAGS_DIR.glob("*.json"):
        with path.open() as f:
            data = json.load(f)
        if data["raag"].lower() == name.lower():
            return data
    return None
