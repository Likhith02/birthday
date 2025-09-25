import os
import sqlite3
import time
from datetime import datetime
from textwrap import dedent
from typing import Optional

import streamlit as st

st.set_page_config(page_title="Click to Wish!", page_icon="🎉", layout="centered")

FRIEND_URL  = os.getenv("FRIEND_LINKEDIN_URL", "https://www.linkedin.com/in/vamsi-boyapati-a98107213/")
FRIEND_NAME = os.getenv("FRIEND_NAME", "My Friend")
REDIRECT_DELAY = int(os.getenv("REDIRECT_DELAY_SEC", "6"))
DB_PATH = os.getenv("DB_PATH", "data.db")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    try:
        OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)  # Streamlit Cloud root secret
    except Exception:
        OPENAI_API_KEY = None

_has_openai = False
try:
    if OPENAI_API_KEY:
        from openai import OpenAI
        _client = OpenAI(api_key=OPENAI_API_KEY)
        _has_openai = True
    else:
        _client = None
except Exception:
    _client = None
    _has_openai = False



@st.cache_resource(show_spinner=False)
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            name TEXT,
            text TEXT
        );
    """)
    # best-effort optional columns (ignore if they already exist)
    for col in ("ip TEXT", "ua TEXT", "src TEXT"):
        try:
            conn.execute(f"ALTER TABLE clicks ADD COLUMN {col};")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    return conn

def record_click(src: Optional[str] = None, ip: Optional[str] = None, ua: Optional[str] = None):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO clicks (ts, ip, ua, src) VALUES (?, ?, ?, ?)",
            (datetime.utcnow().isoformat(), ip, ua, src),
        )
    except sqlite3.OperationalError:
        conn.execute("INSERT INTO clicks (ts) VALUES (?)", (datetime.utcnow().isoformat(),))
    conn.commit()

def get_counts() -> int:
    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM clicks")
    return cur.fetchone()[0]

def add_message(name: str, text: str):
    if not text or not text.strip():
        return
    conn = get_conn()
    conn.execute(
        "INSERT INTO messages (ts, name, text) VALUES (?, ?, ?)",
        (datetime.utcnow().isoformat(), (name or "").strip()[:64] or None, text.strip()[:500]),
    )
    conn.commit()

def fetch_messages(limit: int = 50):
    conn = get_conn()
    cur = conn.execute("SELECT ts, name, text FROM messages ORDER BY id DESC LIMIT ?", (limit,))
    return cur.fetchall()


# ----------------------------
# AI wish (visible errors + fallback)
# ----------------------------
@st.cache_data(ttl=60)
def generate_ai_wish(friend_name: str, total_clicks: int) -> str:
    fallbacks = [
        f"Happy Birthday, {friend_name}! Count: {total_clicks}. May your KPIs be cake-per-slice! 🎂",
        f"{friend_name}, +1 click to your LinkedIn charisma. Total: {total_clicks}. #OpenToRoasts",
        f"Alert: A well-wisher appeared! {total_clicks} clicks so far. Stay humble, stay hireable.",
    ]
    fallback = fallbacks[total_clicks % len(fallbacks)]

    if not _has_openai or not OPENAI_API_KEY:
        return fallback

    try:
        resp = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": (
                    f"Write a short, witty birthday wish that lightly roasts {friend_name}. "
                    "Include one LinkedIn/corporate-buzzword joke. Under 30 words."
                )
            }],
            temperature=0.9,
            max_tokens=60,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text or fallback
    except Exception as e:
        st.warning(f"AI wish error: {type(e).__name__}: {e}")
        return fallback


# ----------------------------
# Confetti
# ----------------------------
def fire_confetti():
    html = dedent("""
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
        <script>
        (function(){
          function shoot(){ confetti({ particleCount: 120, spread: 70, origin: { y: 0.6 } }); }
          shoot(); setTimeout(shoot, 250); setTimeout(shoot, 500);
        })();
        </script>
    """)
    st.components.v1.html(html, height=0)


# ----------------------------
# UI
# ----------------------------
st.title("🎉 Click to Wish " + FRIEND_NAME)

with st.container(border=True):
    st.markdown(
        "**Step 1.** You're officially part of the birthday experiment. "
        "Your click increases the global counter and creates joy (and mild chaos). ✨"
    )

# Query param (?src=linkedin) — works on both new & older Streamlit
src_val = None
try:
    if hasattr(st, "query_params"):  # newer
        qp = st.query_params
    else:
        qp = st.experimental_get_query_params()
    src_val = qp.get("src")
    if isinstance(src_val, list):
        src_val = src_val[0]
except Exception:
    pass

# Count once per session
if "_counted" not in st.session_state:
    record_click(src=src_val)
    st.session_state["_counted"] = True
    st.toast("Thanks! Your click was counted 🎉", icon="🎉")
    fire_confetti()

count = get_counts()

c1, c2 = st.columns([1,1])
with c1:
    st.metric("Total wishes so far", count)
with c2:
    ai_on = bool(OPENAI_API_KEY and _has_openai)
    st.caption("AI wishes: ✅ ON" if ai_on else "AI wishes: ❌ OFF")
    if st.button("🎊 Test confetti"):
        fire_confetti()

with st.spinner("AI is crafting a birthday wish…"):
    wish = generate_ai_wish(FRIEND_NAME, count)
st.success(wish)

with st.expander("Leave your roast/wish (optional)"):
    name = st.text_input("Your name (optional)")
    text = st.text_area("Roast or wish (keep it nice!)",
                        placeholder="e.g., Wishing you infinite endorsements and zero calendar invites.")
    if st.button("Submit to public feed"):
        add_message(name, text)
        st.toast("Submitted! 🎈", icon="🎈")

msgs = fetch_messages()
if msgs:
    st.subheader("Live feed")
    for ts, n, t in msgs:
        who = n or "Anonymous"
        st.markdown(f"**{who}** · _{ts.split('T')[0]}_\n\n{t}")

# ----------------------------
# Stable countdown + iframe-safe redirect + fallbacks
# ----------------------------
st.divider()
if "redirect_at" not in st.session_state:
    st.session_state["redirect_at"] = time.time() + REDIRECT_DELAY

remaining = int(max(0, round(st.session_state["redirect_at"] - time.time())))
st.info(f"You'll be redirected to **{FRIEND_NAME}**'s LinkedIn profile in {remaining} seconds…")
st.write(f"Redirecting in **{remaining}** seconds…")

if remaining <= 0 and not st.session_state.get("_redir_fired"):
    st.session_state["_redir_fired"] = True
    # 1) Try a new tab (works inside Streamlit iframe)
    st.markdown(f"<script>window.open('{FRIEND_URL}', '_blank');</script>", unsafe_allow_html=True)
    # 2) Meta refresh (harmless; sometimes just refreshes iframe)
    st.markdown(f"<meta http-equiv='refresh' content='0; url={FRIEND_URL}'>", unsafe_allow_html=True)

# Manual fallbacks
st.markdown(f"[Go now → LinkedIn profile]({FRIEND_URL})")
if st.button("Open LinkedIn now"):
    st.markdown(f"<meta http-equiv='refresh' content='0; url={FRIEND_URL}'>", unsafe_allow_html=True)

st.caption("Built by Likhith • Be kind, keep it fun. No scraping, no spam — just birthday science.")
