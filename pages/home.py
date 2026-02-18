import streamlit as st

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
gw_points = history["current"][-1]["points"]
team_name = entry["name"]

st.markdown(f"""
<div class="glass-box">
    <div class="team-name">{team_name}</div>
    <div class="gw">Gameweek {gw}</div>
    <div class="points">{gw_points}</div>
</div>
""", unsafe_allow_html=True)

if st.button("Points →", key="nav-btn"):
    st.switch_page("pages/points.py")