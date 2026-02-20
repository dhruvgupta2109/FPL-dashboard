import streamlit as st
import json
import urllib.request
import ssl
import certifi

st.set_page_config(page_title="FPL Live Tracker", layout="centered")

def fetch(url):
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, context=ctx) as r:
        return json.loads(r.read())

def load_bootstrap():
    return fetch("https://fantasy.premierleague.com/api/bootstrap-static/")

def get_current_gw(bootstrap):
    for e in bootstrap["events"]:
        if e["is_current"]:
            return e["id"]
    return None

def build_player_map(bootstrap):
    team_codes = {t["id"]: t["code"] for t in bootstrap["teams"]}
    return {
        p["id"]: {
            "name": f"{p['first_name']} {p['second_name']}",
            "web_name": p["web_name"],
            "team_id": p["team"],
            "team_code": team_codes.get(p["team"], 0),
            "position": p["element_type"],
            "price": p["now_cost"] / 10,
            "photo": f"https://resources.premierleague.com/premierleague/photos/players/110x140/p{p['photo'].replace('.jpg','.png')}",
        }
        for p in bootstrap["elements"]
    }

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #37003c, #2b1e5b, #00ff87);
    min-height: 100vh;
}
.center-box {
    background: rgba(255, 255, 255, 0.12);
    backdrop-filter: blur(14px);
    border-radius: 20px;
    padding: 35px;
    max-width: 450px;
    margin: 8vh auto;
    color: white;
    box-shadow: 0 20px 45px rgba(0,0,0,0.35);
}
.center-box h1 { text-align: center; margin-bottom: 10px; }
.center-box p  { text-align: center; opacity: 0.9; }
.stButton > button {
    width: 100%;
    border-radius: 12px;
    background: #00ff87;
    color: black;
    font-weight: 700;
    border: none;
    padding: 12px;
    font-size: 16px;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.stButton > button:hover {
    transform: scale(1.08);
    box-shadow: 0 12px 30px rgba(0, 255, 135, 0.45);
    background: #00ff87;
}
.stButton > button:active { transform: scale(1.03); }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="center-box">
    <h1>FPL Live Tracker</h1>
    <p>Connect your team to see live points, leagues & squad</p>
</div>
""", unsafe_allow_html=True)

manager_id = st.text_input("Manager ID", placeholder="e.g. 1234567")

with st.expander("How do I find my Manager ID?"):
    st.markdown("""
    1. Go to **https://fantasy.premierleague.com**
    2. Click **Points →**
    3. Check the URL: `https://fantasy.premierleague.com/entry/1637221/event/26`
    4. `1637221` is your Manager ID — paste it here
    """)

connect = st.button("Connect Team")

if connect:
    if not manager_id.strip().isdigit():
        st.error("Manager ID must be numeric.")
        st.stop()

    try:
        bootstrap = load_bootstrap()
        gw        = get_current_gw(bootstrap)
        players   = build_player_map(bootstrap)

        entry   = fetch(f"https://fantasy.premierleague.com/api/entry/{manager_id}/")
        history = fetch(f"https://fantasy.premierleague.com/api/entry/{manager_id}/history/")
        picks   = fetch(f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{gw}/picks/")
    except Exception as e:
        st.error(f"Could not connect to this team. ({e})")
        st.stop()

    st.session_state.manager_id = manager_id
    st.session_state.entry      = entry
    st.session_state.history    = history
    st.session_state.picks      = picks
    st.session_state.players    = players
    st.session_state.gw         = gw

    st.switch_page("pages/home.py")