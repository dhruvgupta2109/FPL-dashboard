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
manager_id = st.session_state.manager_id

# Fetch live points
@st.cache_data(ttl=60)
def fetch_live_points(gw):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = f"https://fantasy.premierleague.com/api/event/{gw}/live/"
    with urllib.request.urlopen(url, context=ctx) as r:
        data = json.loads(r.read())
    return {e["id"]: e["stats"]["total_points"] for e in data["elements"]}

# Fetch leagues data
@st.cache_data(ttl=300)
def fetch_leagues(manager_id):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/"
    with urllib.request.urlopen(url, context=ctx) as r:
        data = json.loads(r.read())
    
    # Get both classic (public) and mini (private) leagues
    classic_leagues = data.get("leagues", {}).get("classic", [])
    
    # Combine and return all leagues
    return classic_leagues

def format_rank(rank):
    """Format rank with commas (e.g., 1234567 -> 1,234,567)"""
    if rank is None:
        return "N/A"
    return f"{rank:,}"

live_pts = fetch_live_points(gw)
picks = sorted(st.session_state.picks["picks"], key=lambda x: x["position"])
starters = picks[:11]

# Calculate total GW points from starting 11 (with captain multiplier)
gw_points = sum(
    live_pts.get(pick["element"], 0) * pick.get("multiplier", 1)
    for pick in starters
)

# Get leagues data
leagues = fetch_leagues(manager_id)

# Build the complete HTML with leagues
league_rows = ""
for league in leagues[:5]:  # Show top 5 leagues
    league_name = league.get("name", "Unknown")
    current_rank = league.get("entry_rank")
    previous_rank = league.get("entry_last_rank")
    
    # Determine arrow
    if current_rank and previous_rank:
        if current_rank < previous_rank:
            arrow = "↑"
            arrow_color = "#00ff87"
        elif current_rank > previous_rank:
            arrow = "↓"
            arrow_color = "#f64646"
        else:
            arrow = "—"
            arrow_color = "#999"
    else:
        arrow = "—"
        arrow_color = "#999"
    
    # Format ranks with commas
    current_display = format_rank(current_rank)
    previous_display = format_rank(previous_rank)
    
    league_rows += f"""<div class="league-row"><div class="league-name">{league_name}</div><div class="league-ranks"><span class="rank-label">Current:</span> <span class="rank-value">{current_display}</span><span class="rank-label">Previous:</span> <span class="rank-value">{previous_display}</span><span class="rank-arrow" style="color: {arrow_color};">{arrow}</span></div></div>"""

st.markdown(f"""<div class="home-container"><div class="glass-box points-box"><div class="team-name">{team_name}</div><div class="gw">Gameweek {gw}</div><div class="points">{gw_points}</div></div><div class="glass-box leagues-box"><div class="leagues-title">My Leagues</div>{league_rows}</div></div>""", unsafe_allow_html=True)

if st.button("Points →", key="nav-btn"):
    st.switch_page("pages/points.py")