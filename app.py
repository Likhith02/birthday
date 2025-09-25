

import os
import sqlite3
import time
from datetime import datetime
from textwrap import dedent

import streamlit as st


st.set_page_config(page_title="Click to Wish!", page_icon="🎉", layout="centered")

FRIEND_URL  = os.getenv("FRIEND_LINKEDIN_URL", "https://www.linkedin.com/in/vamsi-boyapati-a98107213?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_contact_details%3BpmkgaQhMRcK%2B%2FzgXSUY%2BOQ%3D%3D")
FRIEND_NAME = os.getenv("FRIEND_NAME", "My Friend")
REDIRECT_DELAY = int(os.getenv("REDIRECT_DELAY_SEC", "6"))
DB_PATH = os.getenv("DB_PATH", "data.db")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_has_openai = False
try:
    if OPENAI_API_KEY:
        from openai import OpenAI
        _has_openai = True
except Exception:
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
    conn.commit()
    return conn

def record_click(ip: str = None, ua: str = None):
    """Insert compatible with both old and new schemas (adds columns if missing)."""
    conn = get_conn()
    try:
        conn.execute("ALTER TABLE clicks ADD COLUMN ip TEXT;")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE clicks ADD COLUMN ua TEXT;")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute(
            "INSERT INTO clicks (ts, ip, ua) VALUES (?, ?, ?)",
            (datetime.utcnow().isoformat(), ip, ua),
        )
    except sqlite3.OperationalError:
        conn.execute(
            "INSERT INTO clicks (ts) VALUES (?)",
            (datetime.utcnow().isoformat(),),
        )
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

@st.cache_data(ttl=60)
def generate_ai_wish(friend_name: str, total_clicks: int) -> str:
    if not _has_openai:
        picks = [
            f"Happy Birthday, {friend_name}! Another brave soul clicked. Count: {total_clicks}.🎂",
            f"{friend_name}, +1 click to your LinkedIn charisma. Total: {total_clicks}. #OpenToRoasts",
            f"Alert: A well-wisher appeared! {total_clicks} clicks so far. Stay humble, stay hireable.",
        ]
        return picks[total_clicks % len(picks)]
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = (
            f"Write a short, witty birthday wish that lightly roasts someone named {friend_name}. "
            f"Include a LinkedIn/corporate-buzzword joke. Under 30 words. Clicks: {total_clicks}."
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=60,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return f"Happy Birthday, {friend_name}! Someone clicked again. Count: {total_clicks}. KPI: Cake Per Inhale."


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


st.title("🎉 Click to Wish " + FRIEND_NAME)

with st.container(border=True):
    st.markdown("**Step 1.** You're officially part of the birthday experiment. "
                "Your click increases the global counter and creates joy (and mild chaos). ✨")

if "_counted" not in st.session_state:
    record_click()
    st.session_state["_counted"] = True
    st.toast("Thanks! Your click was counted 🎉", icon="🎉")
    fire_confetti()

count = get_counts()
c1, c2 = st.columns([1,1])
with c1:
    st.metric("Total wishes so far", count)
with c2:
    st.caption("(Refresh-resistant. Real DB. No fake vibes.)")
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


st.divider()
if "redirect_at" not in st.session_state:
    st.session_state["redirect_at"] = time.time() + REDIRECT_DELAY

remaining = int(max(0, round(st.session_state["redirect_at"] - time.time())))
st.info(f"You'll be redirected to **{FRIEND_NAME}**'s LinkedIn profile in {remaining} seconds…")

countdown_html = f"""
    <div style='font-size: 16px;'>Redirecting in <span id="cd">{remaining}</span>s…</div>
    <script>
        let t = {remaining};
        let interval = setInterval(() => {{
            t -= 1;
            if (t <= 0) {{
                clearInterval(interval);
                // open in new tab (allowed in Streamlit's iframe sandbox)
                window.open('{FRIEND_URL}', '_blank');
            }}
            const el = document.getElementById('cd');
            if (el) el.innerText = Math.max(0, t);
        }}, 1000);
    </script>
"""
st.components.v1.html(countdown_html, height=40)

st.markdown(f"[Go now → LinkedIn profile]({FRIEND_URL})")
if st.button("Open LinkedIn now"):
    st.markdown(
        f"<meta http-equiv='refresh' content='0; url={FRIEND_URL}'>",
        unsafe_allow_html=True
    )

st.caption("Built by Likhith • Be kind, keep it fun. No scraping, no spam — just birthday science.")



