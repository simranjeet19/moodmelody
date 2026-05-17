# 🎵 Mood Melody

> **Tell it how you feel. Get a raag to sing.**

Mood Melody is an AI-powered web app rooted in the ancient Indian tradition of **rasa therapy** — the belief that music can hold, heal, and transform emotion. Describe your emotional state in plain language and the app will recommend the most fitting Hindustani classical raag, paired with Bollywood songs and a classical audio sample to listen to right now.

---

## Demo

| Homepage | Result |
|----------|--------|
| Parchment/navy UI with description and input | Ragamala painting + raag card + songs + audio player |

**Sample input:** *"I am feeling really worried about the global economy after watching a podcast"*

**Output:** Raag Bhairav — Bhayanaka rasa (fear/anxiety), high intensity — with Ragamala painting, scale, warm explanation, Bollywood songs, and a classical sample by Kumar Gandharva.

---

## How It Works

The pipeline runs three AI agents in sequence:

```
User text
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Agent 1: Mood Reader                               │
│  Extracts rasa, intensity, keywords via Groq LLM    │
│  → EmotionalState (Pydantic)                        │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Agent 2: Raag Mapper                               │
│  RAG (ChromaDB semantic search) + tool calling      │
│  Checks time of day (prahar), retrieves raag data   │
│  → raag_name, rasa_match, reasoning                 │
└─────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Agent 3: Practice Planner                          │
│  Structured output — songs, aaroh/avaroh, why       │
│  → RaagRecommendation (Pydantic)                    │
└─────────────────────────────────────────────────────┘
    │
    ▼
Streamlit UI — Ragamala painting + raag card + audio player + songs
```

### The Nine Rasas (Nava Rasa)

| Rasa | Emotion |
|------|---------|
| Karuna | Grief, compassion, sorrow |
| Shringar | Love, longing, romance |
| Veera | Courage, strength, determination |
| Raudra | Anger, frustration, outrage |
| Hasya | Joy, playfulness, celebration |
| Bhayanaka | Fear, anxiety, dread |
| Bibhatsa | Disgust, moral nausea |
| Adbhut | Wonder, awe, curiosity |
| Shanta | Peace, stillness, acceptance |

### 20 Raags in the Knowledge Base

Bageshwari · Bhairav · Bhairavi · Bhimpalasi · Bhoopali · Bilawal · Darbari · Durga · Hansdhwani · Jaunpuri · Kafi · Kedar · Khamaj · Lalit · Malkaans · Marwa · Puriya Dhanashri · Rageshwari · Todi · Yaman

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM inference | [Groq](https://groq.com) — `llama-3.1-8b-instant` (free tier) |
| Vector DB | [ChromaDB](https://www.trychroma.com) |
| Embeddings | [fastembed](https://github.com/qdrant/fastembed) |
| Agents & tools | Groq tool calling (function calling) |
| Structured output | Pydantic v2 + JSON mode |
| UI | [Streamlit](https://streamlit.io) |
| Audio samples | [Internet Archive](https://archive.org) (free to stream) |
| Raag paintings | [Wikimedia Commons](https://commons.wikimedia.org) (public domain Ragamala miniatures) |

---

## Project Structure

```
moodmelody/
├── app.py                  # Streamlit UI
├── src/
│   ├── agents/
│   │   ├── mood_reader.py       # Agent 1 — rasa extraction
│   │   ├── raag_mapper.py       # Agent 2 — RAG + tool calling
│   │   └── practice_planner.py  # Agent 3 — structured output
│   ├── schemas.py          # Pydantic models
│   ├── knowledge.py        # ChromaDB RAG layer
│   ├── tools.py            # Tool definitions for Agent 2
│   ├── logger.py           # Session logging
│   ├── evals.py            # Evaluation suite
│   └── utils.py            # Retry wrapper (Groq 429 handling)
├── data/
│   └── raags/              # JSON knowledge base (20 raags)
├── requirements.txt
└── .env.example
```

---

## Getting Started

### 1. Clone and install

```bash
git clone https://github.com/simranjeet19/moodmelody.git
cd moodmelody
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set your Groq API key

Get a free key at [console.groq.com](https://console.groq.com).

```bash
cp .env.example .env
# Edit .env and add your key:
# GROQ_API_KEY=your_groq_api_key_here
```

### 3. Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Features

- **Mood reading** — understands free-form emotional descriptions in any language or style
- **Time-aware** — checks the current prahar (time-of-day watch) and prefers raags appropriate to the hour
- **Ragamala paintings** — each raag card shows a matching traditional miniature painting (16th–19th century)
- **Classical audio samples** — embedded player with real performances by Pt. Bhimsen Joshi, Kumar Gandharva, Pt. Jasraj, Prabha Atre, and others, streamed free from Internet Archive
- **Bollywood song recommendations** — 2–3 film songs drawn from the raag's knowledge base
- **Session stats** — sidebar tracks your most-felt rasas and recommended raags over time
- **Rate-limit resilient** — auto-retry with backoff for Groq free tier (6000 TPM limit)

---

## Built With

- [Groq](https://groq.com) for fast LLM inference
- [LLaMA 3.1 8B Instant](https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct) by Meta
- Ragamala paintings sourced from [Wikimedia Commons](https://commons.wikimedia.org/wiki/Category:Ragamala_paintings) (public domain)
- Classical audio via [Internet Archive](https://archive.org) (Community Audio, freely licensed)
