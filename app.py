"""
Mood Melody — Streamlit UI

Run with:  streamlit run app.py
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from groq import Groq

st.set_page_config(
    page_title="Mood Melody",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Rasa metadata ─────────────────────────────────────────────────────────────
RASA_COLORS: dict[str, str] = {
    "karuna":    "#4A3F9F",
    "shringar":  "#C0395A",
    "veera":     "#B05A00",
    "raudra":    "#9B1C1C",
    "hasya":     "#1A7A5E",
    "bhayanaka": "#5B2D8E",
    "bibhatsa":  "#2D5A3D",
    "adbhut":    "#005F8A",
    "shanta":    "#4A6741",
}
RASA_EMOJIS: dict[str, str] = {
    "karuna":    "💙",
    "shringar":  "🌹",
    "veera":     "🔥",
    "raudra":    "⚡",
    "hasya":     "✨",
    "bhayanaka": "🌌",
    "bibhatsa":  "🌿",
    "adbhut":    "🌊",
    "shanta":    "🍃",
}

RAAG_IMAGES: dict[str, str] = {
    "Bhairav":        "https://upload.wikimedia.org/wikipedia/commons/0/02/Brooklyn_Museum_-_Bhairava_Raga_Page_from_a_Ragamala_Series.jpg",
    "Lalit":          "https://upload.wikimedia.org/wikipedia/commons/e/e5/Lalit_Ragini_%286124559823%29.jpg",
    "Todi":           "https://upload.wikimedia.org/wikipedia/commons/1/15/The_Musical_Mode_-_Ragini_Todi.jpg",
    "Kafi":           "https://upload.wikimedia.org/wikipedia/commons/d/d2/Kafi_Ragamala_painting.jpg",
    "Marwa":          "https://upload.wikimedia.org/wikipedia/commons/9/98/Maru_Ragini_%286125107700%29.jpg",
    "Malkaans":       "https://upload.wikimedia.org/wikipedia/commons/d/d9/Brooklyn_Museum_-_Malkos_Raga.jpg",
}
DEFAULT_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/7/73/Lalit_Ragini_of_the_Bhairava_Raga_by_Chetan_Das.JPG"

# (url, performer) — all sourced from Internet Archive, free to stream
RAAG_AUDIO: dict[str, tuple[str, str]] = {
    "Bageshwari":       ("https://archive.org/download/ragabageshriinstrumentalmusicflutesitartabla/Raga%20Bageshri%20instrumental%20music%2C%20Flute%2Csitar%2Ctabla.mp3", "Flute, Sitar & Tabla"),
    "Bhairav":          ("https://archive.org/download/RaagBhairavDhani/01%20-%20%20Kumar%20Gandharva%20-%20Raag%20Bhairav.mp3", "Kumar Gandharva"),
    "Bhairavi":         ("https://archive.org/download/c.p.ragabhairavi/C.P._Raga%20Bhairavi.MP3", "Raga Bhairavi"),
    "Bhimpalasi":       ("https://archive.org/download/jamendo-194157/01-1766662-Vibhavaree%20Gargeya-PracticeBhimpalasi7_Kunjana.mp3", "Vibhavaree Gargeya"),
    "Bhoopali":         ("https://archive.org/download/kumar-gandharv-bhoopali/Kumar%20Gandharv-Bhoopali.mp3", "Kumar Gandharva"),
    "Bilawal":          ("https://archive.org/download/Smt.VijayaJadhavRagaAllaiyaBilawal.Kedar...AllIndiaRecordingsMay14th2018/Smt.Vijaya%20Jadhav-Raga%20-Allaiya%20Bilawal%20%26.Kedar...All%20India%20Recordings%20May%2014th%202018.mp3", "Smt. Vijaya Jadhav"),
    "Darbari":          ("https://archive.org/download/darbari-alaap-venice-7th-nov-2019-1/Darbari%20alaap%20Venice%207th%20Nov%202019-1.mp3", "Live in Venice 2019"),
    "Durga":            ("https://archive.org/download/01.-raga-durga/01.%20Raga%20Durga.mp3", "Hariprasad Chaurasia"),
    "Hansdhwani":       ("https://archive.org/download/Sg4182.JATOSENAHINHansdhwani/sg418-2.JA%20TO%20SE%20NAHIN-Hansdhwani.mp3", "Swargoshthi"),
    "Jaunpuri":         ("https://archive.org/download/RaagJaunpuri/Raag%20Jaunpuri.mp3", "Sangya Tandon"),
    "Kafi":             ("https://archive.org/download/bhimsen-joshi-kafi/Bhimsen%20Joshi-Kafi.mp3", "Pt. Bhimsen Joshi"),
    "Kedar":            ("https://archive.org/download/bhimsen-joshi-shudh-kedar/Bhimsen%20Joshi-Shudh%20Kedar.mp3", "Pt. Bhimsen Joshi"),
    "Khamaj":           ("https://archive.org/download/Pt.A.KananThumriKhamaj/Pt.A.Kanan-%20Thumri%20Khamaj.mp3", "Pt. A. Kanan"),
    "Lalit":            ("https://archive.org/download/RaagLalitBibhas/01%20-%20%20Omkar%20Dadarkar%20-%20Raag%20Lalit.mp3", "Omkar Dadarkar"),
    "Malkaans":         ("https://archive.org/download/PanditMallikarjunMansurSampurnaMalkaunsePt.DevendraMurdekarFluteRecitalBhimpalasiAIR/Pandit%20Mallikarjun%20Mansur-Sampurna%20Malkaunse%20%26%20Pt.Devendra%20Murdekar-Flute%20Recital-Bhimpalasi-%20AIR.mp3", "Pt. Mallikarjun Mansur"),
    "Marwa":            ("https://archive.org/download/JasrajMarwa/Jasraj-Marwa.mp3", "Pt. Jasraj"),
    "Puriya Dhanashri": ("https://archive.org/download/JasrajPuriyaDhanasri01/Jasraj-Puriya%20Dhanasri%2001.mp3", "Pt. Jasraj"),
    "Rageshwari":       ("https://archive.org/download/dni.ncaa.SKSS-N420-AC/SKSS-N420-AC_SIDE_A.mp3", "Ustad Bade Ghulam Ali Khan"),
    "Todi":             ("https://archive.org/download/bhimsen-joshi-todi/Bhimsen%20Joshi-Todi.MP3", "Pt. Bhimsen Joshi"),
    "Yaman":            ("https://archive.org/download/RaagYaman/prabha_atre-raag_yaman.mp3", "Prabha Atre"),
}


def _color(rasa: str) -> str:
    for k, v in RASA_COLORS.items():
        if k in rasa.lower():
            return v
    return "#C8963E"

def _emoji(rasa: str) -> str:
    for k, v in RASA_EMOJIS.items():
        if k in rasa.lower():
            return v
    return "🎵"

def _image(raag_name: str) -> str:
    return RAAG_IMAGES.get(raag_name, DEFAULT_IMAGE)


# ── CSS ───────────────────────────────────────────────────────────────────────
def _css() -> None:
    st.markdown(
        """<style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,600;0,700;1,400&family=Nunito:wght@400;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Nunito', sans-serif;
        }

        .stApp {
            background-color: #F5ECD7;
            color: #0F2044;
        }

        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }

        /* ── Textarea fix ── */
        [data-baseweb="textarea"],
        [data-baseweb="base-input"],
        .stTextArea [data-baseweb="base-input"] {
            background-color: #FDF6E8 !important;
            border-radius: 12px !important;
        }
        .stTextArea textarea,
        [data-baseweb="textarea"] textarea,
        [data-baseweb="base-input"] textarea {
            background: #FDF6E8 !important;
            border: 2px solid #C8963E !important;
            border-radius: 12px !important;
            color: #0F2044 !important;
            caret-color: #0F2044 !important;
            -webkit-text-fill-color: #0F2044 !important;
            font-size: 1.05rem !important;
            font-family: 'Nunito', sans-serif !important;
        }
        .stTextArea textarea:focus,
        [data-baseweb="textarea"]:focus-within textarea {
            border-color: #0A1628 !important;
            box-shadow: 0 0 0 3px rgba(10,22,40,0.15) !important;
            outline: none !important;
        }
        .stTextArea textarea::placeholder {
            color: #9B8B6E !important;
            -webkit-text-fill-color: #9B8B6E !important;
        }

        /* ── Button ── */
        .stButton > button {
            background: linear-gradient(135deg, #0A1628 0%, #1C3A6E 100%) !important;
            color: #F5ECD7 !important;
            border: 2px solid #C8963E !important;
            border-radius: 50px !important;
            font-size: 1.1rem !important;
            font-weight: 800 !important;
            padding: 0.65rem 2.5rem !important;
            transition: all 0.3s ease !important;
            letter-spacing: 0.3px !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 30px rgba(10,22,40,0.3) !important;
            background: linear-gradient(135deg, #1C3A6E 0%, #0A1628 100%) !important;
        }

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0A1628 0%, #071020 100%) !important;
            border-right: 2px solid #C8963E !important;
        }
        [data-testid="stSidebar"] * { color: #E8D5A3 !important; }
        [data-testid="stSidebar"] hr { border-color: rgba(200,150,62,0.3) !important; }

        /* ── Metrics ── */
        [data-testid="metric-container"] {
            background: rgba(200,150,62,0.12) !important;
            border: 1px solid rgba(200,150,62,0.3) !important;
            border-radius: 10px !important;
            padding: 0.8rem !important;
        }

        hr { border-color: rgba(10,22,40,0.12) !important; }

        /* ── Spinner text ── */
        .stSpinner > div { color: #0A1628 !important; }
        </style>""",
        unsafe_allow_html=True,
    )


# ── Components ────────────────────────────────────────────────────────────────

def _header() -> None:
    st.markdown(
        '<div style="text-align:center;padding:2rem 1rem 1rem;">'
        '<div style="font-size:2.8rem;font-weight:900;font-family:\'Crimson Pro\',serif;'
        'color:#0A1628;letter-spacing:-0.5px;line-height:1.1;">'
        '🎵 Mood Melody'
        '</div>'
        '<div style="color:#6B5B3E;font-size:1.05rem;margin-top:0.5rem;font-weight:600;'
        'font-style:italic;font-family:\'Crimson Pro\',serif;">'
        'Share what stirs within &mdash; let a raag hold it'
        '</div>'
        '<div style="width:80px;height:3px;background:linear-gradient(90deg,#C8963E,#0A1628);'
        'margin:0.8rem auto 0;border-radius:2px;"></div>'
        '</div>',
        unsafe_allow_html=True,
    )


def _mood_chip(state) -> None:
    c = _color(state.primary_rasa)
    em = _emoji(state.primary_rasa)
    bars = {"low": "▮▯▯", "medium": "▮▮▯", "high": "▮▮▮"}.get(state.intensity, "▮▯▯")

    second_html = ""
    if state.secondary_rasa:
        second_html = (
            '<span style="color:#9B8B6E;margin:0 0.4rem">+</span>'
            '<span style="color:#6B5B3E;font-size:0.95rem">' + state.secondary_rasa + '</span>'
        )

    html = (
        '<div style="background:#FDF6E8;border-left:4px solid ' + c + ';'
        'border-radius:12px;padding:0.9rem 1.3rem;margin:1.2rem 0 0.5rem;'
        'display:flex;align-items:center;gap:1rem;'
        'box-shadow:0 2px 12px rgba(10,22,40,0.08);">'
        '<span style="font-size:1.8rem">' + em + '</span>'
        '<div>'
        '<span style="color:' + c + ';font-weight:800;font-size:1.05rem">' + state.primary_rasa + '</span>'
        + second_html +
        '<span style="margin-left:1rem;color:#9B8B6E;font-size:0.9rem">'
        'Intensity: <strong style="color:' + c + '">' + bars + ' ' + state.intensity + '</strong></span>'
        '<div style="color:#3D2E1A;font-size:0.95rem;margin-top:0.3rem;font-style:italic;">'
        + state.summary +
        '</div>'
        '</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _raag_card(rec) -> None:
    c = _color(rec.rasa_match)
    em = _emoji(rec.rasa_match)
    img_url = _image(rec.raag_name)

    time_badge = (
        '<span style="color:#1A7A5E;font-weight:700;font-size:0.85rem">&#10003; Right time</span>'
        if rec.is_time_appropriate
        else '<span style="color:#B05A00;font-weight:700;font-size:0.85rem">&#9888; Not traditional time</span>'
    )

    html = (
        '<div style="background:#FDF6E8;border:1px solid ' + c + ';border-top:4px solid ' + c + ';'
        'border-radius:16px;padding:0;margin:1rem 0;overflow:hidden;'
        'box-shadow:0 4px 24px rgba(10,22,40,0.12);">'

        '<div style="display:flex;gap:0;min-height:280px;">'

        '<div style="width:35%;min-width:200px;flex-shrink:0;overflow:hidden;">'
        '<img src="' + img_url + '" '
        'style="width:100%;height:100%;object-fit:cover;object-position:center top;display:block;" '
        'onerror="this.style.display=\'none\'" />'
        '</div>'

        '<div style="flex:1;padding:1.8rem 2rem;">'

        '<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:0.5rem;">'
        '<div>'
        '<div style="font-size:2.2rem;font-weight:900;color:' + c + ';'
        'font-family:\'Crimson Pro\',serif;letter-spacing:-0.5px;line-height:1;">'
        + em + ' ' + rec.raag_name.upper() +
        '</div>'
        '<div style="color:#9B8B6E;font-size:0.88rem;margin-top:0.3rem;font-weight:600">'
        + rec.thaat + ' thaat &nbsp;&middot;&nbsp; ' + rec.time_of_day +
        '</div>'
        '</div>'
        '<div style="text-align:right;">'
        '<div style="background:' + c + ';color:#FDF6E8;font-weight:800;'
        'font-size:0.82rem;padding:0.3rem 1rem;border-radius:50px;margin-bottom:0.4rem">'
        + rec.rasa_match +
        '</div>'
        '<div style="font-size:0.82rem">' + time_badge + '</div>'
        '</div></div>'

        '<div style="border-top:1px solid rgba(10,22,40,0.1);margin:1.1rem 0"></div>'

        '<div style="color:#3D2E1A;font-size:1rem;line-height:1.75;'
        'font-style:italic;font-family:\'Crimson Pro\',serif;font-size:1.1rem;">'
        '&ldquo;' + rec.why + '&rdquo;'
        '</div>'

        '<div style="margin-top:1.3rem;background:rgba(10,22,40,0.05);border-radius:10px;'
        'padding:0.8rem 1.1rem;font-family:monospace;">'
        '<div style="color:' + c + ';font-weight:700;font-size:0.75rem;letter-spacing:1.5px;margin-bottom:0.4rem">SCALE</div>'
        '<div style="color:#0F2044;font-size:0.92rem">'
        '<span style="color:' + c + ';font-weight:700">&#8593;</span>&nbsp; ' + rec.aaroh +
        '</div>'
        '<div style="color:#0F2044;font-size:0.92rem;margin-top:0.25rem">'
        '<span style="color:' + c + ';font-weight:700">&#8595;</span>&nbsp; ' + rec.avaroh +
        '</div>'
        '</div>'

        '</div>'
        '</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def _audio_player(rec) -> None:
    audio_info = RAAG_AUDIO.get(rec.raag_name)
    if not audio_info:
        return
    url, performer = audio_info
    c = _color(rec.rasa_match)
    st.markdown(
        '<div style="margin:1.5rem 0 0.4rem;">'
        '<div style="font-size:1.25rem;font-weight:800;color:#0A1628;'
        'font-family:\'Crimson Pro\',serif;">🎼 Classical Sample</div>'
        '<div style="color:#6B5B3E;font-size:0.87rem;margin-top:0.15rem">'
        'Performed by <strong style="color:' + c + '">' + performer + '</strong>'
        ' &nbsp;&middot;&nbsp; <span style="font-style:italic">via Internet Archive (free to stream)</span>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    st.audio(url)


def _songs(rec) -> None:
    accents = ["#C0395A", "#4A3F9F", "#C8963E"]

    st.markdown(
        '<div style="font-size:1.25rem;font-weight:800;color:#0A1628;margin:1.5rem 0 0.8rem;'
        'font-family:\'Crimson Pro\',serif;">'
        '🎵 Songs to Listen To'
        '</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(min(len(rec.songs), 3))
    for i, song in enumerate(rec.songs[:3]):
        ac = accents[i % len(accents)]
        with cols[i]:
            st.markdown(
                '<div style="background:#FDF6E8;'
                'border:1px solid ' + ac + '55;border-top:3px solid ' + ac + ';'
                'border-radius:14px;padding:1.1rem 1rem;'
                'box-shadow:0 2px 12px rgba(10,22,40,0.08);">'
                '<div style="font-size:1rem;font-weight:800;color:#0F2044;line-height:1.3;margin-bottom:0.4rem">'
                + song.title +
                '</div>'
                '<div style="color:' + ac + ';font-size:0.82rem;font-weight:700;margin-bottom:0.5rem">'
                + song.singer +
                '</div>'
                '<div style="display:flex;gap:0.4rem;flex-wrap:wrap;margin-bottom:0.5rem">'
                '<span style="background:' + ac + '22;color:' + ac + ';font-size:0.75rem;font-weight:700;'
                'padding:0.15rem 0.6rem;border-radius:50px">' + str(song.year) + '</span>'
                '<span style="background:rgba(10,22,40,0.06);color:#6B5B3E;'
                'font-size:0.75rem;padding:0.15rem 0.6rem;border-radius:50px">' + song.film + '</span>'
                '</div>'
                '<div style="color:#6B5B3E;font-size:0.82rem;line-height:1.45;font-style:italic">'
                + song.note +
                '</div>'
                '</div>',
                unsafe_allow_html=True,
            )


def _sidebar() -> None:
    with st.sidebar:
        st.markdown(
            '<div style="text-align:center;padding:1rem 0 1.5rem">'
            '<div style="font-size:2rem">🎵</div>'
            '<div style="font-size:1.1rem;font-weight:800;color:#E8D5A3;font-family:\'Crimson Pro\',serif">'
            'Mood Melody</div>'
            '<div style="font-size:0.78rem;color:rgba(232,213,163,0.5);margin-top:0.3rem">'
            'AI &middot; RAG &middot; Multi-Agent</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.markdown("**How it works**")
        st.markdown(
            '<div style="font-size:0.87rem;color:rgba(232,213,163,0.8);line-height:1.8">'
            '1. 🧠 <b>Mood Reader</b> — extracts your rasa<br>'
            '2. 🔍 <b>Raag Mapper</b> — RAG + tool calling<br>'
            '3. 📋 <b>Practice Planner</b> — selects songs<br>'
            '4. 📝 <b>Logger</b> — session patterns</div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")

        try:
            from src.logger import summarise_patterns
            stats = summarise_patterns()
            if stats.get("total_sessions", 0) > 0:
                st.markdown("**Your sessions**")
                st.metric("Total sessions", stats["total_sessions"])
                if stats.get("rasa_frequency"):
                    top = list(stats["rasa_frequency"].items())[0]
                    st.metric("Most felt rasa", top[0], f"{top[1]}x")
                if stats.get("raag_frequency"):
                    top = list(stats["raag_frequency"].items())[0]
                    st.metric("Most recommended", top[0], f"{top[1]}x")
                if "time_appropriate_pct" in stats:
                    st.metric("Sung at right time", f"{stats['time_appropriate_pct']}%")
        except Exception:
            pass

        st.markdown("---")
        st.markdown(
            '<div style="font-size:0.75rem;color:rgba(232,213,163,0.35);text-align:center;line-height:1.6">'
            'Groq &middot; LLaMA 3.1 &middot; ChromaDB<br>'
            'fastembed &middot; 20 raags &middot; 9 rasas<br>'
            '<span style="font-style:italic">Ragamala paintings: Wikimedia Commons</span>'
            '</div>',
            unsafe_allow_html=True,
        )


# ── Pipeline ──────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def _run(user_text: str):
    from src.knowledge import build_collection
    from src.agents import mood_reader, raag_mapper, practice_planner
    from src.logger import log_session

    build_collection()
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    state = mood_reader.run(user_text, client=client)
    mapping = raag_mapper.run(state, client=client)
    rec = practice_planner.run(state, mapping, client=client)
    log_session(rec)
    return rec


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    _css()
    _sidebar()
    _header()

    if not os.environ.get("GROQ_API_KEY"):
        st.error("GROQ_API_KEY not set. Add it to your .env file and restart.")
        st.stop()

    st.markdown(
        '<div style="max-width:680px;margin:1.2rem auto 1.8rem;text-align:center;padding:0 1rem;">'
        '<p style="color:#3D2E1A;font-size:1.02rem;line-height:1.8;margin-bottom:1.2rem;">'
        'Mood Melody is rooted in the ancient Indian tradition of <strong>rasa therapy</strong> — '
        'the belief that music can hold, heal, and transform emotion. '
        'Tell it how you feel, and it will find the Hindustani classical raag '
        'that resonates with your inner state, along with Bollywood songs and classical compositions to listen to right now.'
        '</p>'
        '<div style="display:flex;justify-content:center;gap:0.8rem;flex-wrap:wrap;">'
        '<span style="background:#0A1628;color:#E8D5A3;font-size:0.8rem;font-weight:700;'
        'padding:0.35rem 1rem;border-radius:50px;letter-spacing:0.3px;">🧠 AI Mood Reading</span>'
        '<span style="background:#0A1628;color:#E8D5A3;font-size:0.8rem;font-weight:700;'
        'padding:0.35rem 1rem;border-radius:50px;letter-spacing:0.3px;">🎵 20 Hindustani Raags</span>'
        '<span style="background:#0A1628;color:#E8D5A3;font-size:0.8rem;font-weight:700;'
        'padding:0.35rem 1rem;border-radius:50px;letter-spacing:0.3px;">🎬 Bollywood Songs</span>'
        '<span style="background:#0A1628;color:#E8D5A3;font-size:0.8rem;font-weight:700;'
        'padding:0.35rem 1rem;border-radius:50px;letter-spacing:0.3px;">🕐 Time-aware</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    col_input, _ = st.columns([3, 1])
    with col_input:
        user_text = st.text_area(
            label="mood",
            placeholder=(
                "e.g. I've been carrying a quiet sadness I can't explain...\n"
                "or: I failed my exam and feel like a complete failure.\n"
                "or: Feeling peaceful after a morning walk, wanting to sing."
            ),
            height=130,
            label_visibility="collapsed",
        )

    _, btn_col, _ = st.columns([2, 1.2, 2])
    with btn_col:
        submitted = st.button("Find My Raag →", use_container_width=True)

    if submitted and user_text.strip():
        with st.spinner("Reading your mood · selecting your raag · finding songs..."):
            try:
                rec = _run(user_text.strip())
                st.session_state["rec"] = rec
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.stop()

    rec = st.session_state.get("rec")
    if rec:
        _mood_chip(rec.emotional_state)
        _raag_card(rec)
        _audio_player(rec)
        _songs(rec)
    elif not submitted:
        st.markdown(
            '<div style="text-align:center;margin-top:2rem;color:#9B8B6E;font-size:0.88rem;'
            'font-style:italic;font-family:\'Crimson Pro\',serif;">'
            'Describe your situation — as specific or as simple as you like.<br>'
            '"my boss embarrassed me today" &nbsp;&middot;&nbsp; "can\'t sleep, missing someone"'
            ' &nbsp;&middot;&nbsp; "feeling brave and ready"'
            '</div>',
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
