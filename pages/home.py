import streamlit as st
import json
import urllib.request
import ssl
import certifi

st.set_page_config(page_title="FPL Home", layout="centered")

if "manager_id" not in st.session_state:
    st.warning("No manager ID found. Go back to Dashboard and connect your team.")
    if st.button("Go to Dashboard"):
        st.switch_page("live_dashboard.py")
    st.stop()

with open("css/home.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

gw        = st.session_state.gw
history   = st.session_state.history
entry     = st.session_state.entry
team_name = entry["name"]

@st.cache_data(ttl=60)
def fetch_live_points(gw):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = f"https://fantasy.premierleague.com/api/event/{gw}/live/"
    with urllib.request.urlopen(url, context=ctx) as r:
        data = json.loads(r.read())
    return {e["id"]: e["stats"]["total_points"] for e in data["elements"]}

live_pts = fetch_live_points(gw)
picks = sorted(st.session_state.picks["picks"], key=lambda x: x["position"])
starters = picks[:11]

gw_points = sum(
    live_pts.get(pick["element"], 0) * pick.get("multiplier", 1)
    for pick in starters
)

st.markdown(f"""
<div class="glass-box">
    <div class="team-name">{team_name}</div>
    <div class="gw">Gameweek {gw}</div>
    <div class="points">{gw_points}</div>
</div>
""", unsafe_allow_html=True)

if st.button("Points →", key="nav-btn"):
    st.switch_page("pages/points.py")