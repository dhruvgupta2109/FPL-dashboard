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

# Fetch GW stats (average and highest)
@st.cache_data(ttl=60)
def fetch_gw_stats(gw):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    with urllib.request.urlopen(url, context=ctx) as r:
        bootstrap = json.loads(r.read())
    
    for event in bootstrap.get("events", []):
        if event["id"] == gw:
            avg = event.get("average_entry_score") or 0
            highest = event.get("highest_score") or 0
            return round(avg), highest
    
    return 0, 0

# Fetch leagues data
@st.cache_data(ttl=300)
def fetch_leagues(manager_id):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/"
    with urllib.request.urlopen(url, context=ctx) as r:
        data = json.loads(r.read())
    
    all_leagues = data.get("leagues", {}).get("classic", [])
    
    # Separate mini (private) and public leagues
    # For mini leagues, try to get size from admin_entry or other fields
    mini_leagues = []
    public_leagues = []
    
    for l in all_leagues:
        # Add all available fields to league dict
        league_data = {
            "name": l.get("name"),
            "id": l.get("id"),
            "entry_rank": l.get("entry_rank"),
            "entry_last_rank": l.get("entry_last_rank"),
            "league_type": l.get("league_type"),
            "admin_entry": l.get("admin_entry"),
            "start_event": l.get("start_event"),
            "scoring": l.get("scoring")
        }
        
        if l.get("league_type") == "x":
            mini_leagues.append(league_data)
        else:
            public_leagues.append(league_data)
    
    return mini_leagues, public_leagues

def format_rank(rank):
    """Format rank with commas (e.g., 1234567 -> 1,234,567)"""
    if rank is None:
        return "N/A"
    return f"{rank:,}"

live_pts = fetch_live_points(gw)
avg_points, highest_points = fetch_gw_stats(gw)
picks = sorted(st.session_state.picks["picks"], key=lambda x: x["position"])
starters = picks[:11]

# Calculate total GW points from starting 11 (with captain multiplier)
gw_points = sum(
    live_pts.get(pick["element"], 0) * pick.get("multiplier", 1)
    for pick in starters
)

# Get leagues data
mini_leagues, public_leagues = fetch_leagues(manager_id)

# Helper function to get league size
def get_league_size(league_id):
    if not league_id:
        return None
    try:
        ctx = ssl.create_default_context(cafile=certifi.where())
        url = f"https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            data = json.loads(r.read())
            
            # Try multiple possible locations for the size
            league_info = data.get("league", {})
            size = league_info.get("size") or league_info.get("max_entries") or len(data.get("standings", {}).get("results", []))
            
            return size if size and size > 0 else None
    except Exception as e:
        # Return None if there's any error
        return None

# Helper function to build league rows
def build_league_rows(leagues, max_count=5, show_total=False):
    rows = ""
    for league in leagues[:max_count]:
        league_name = league.get("name", "Unknown")
        league_id = league.get("id")
        current_rank = league.get("entry_rank")
        previous_rank = league.get("entry_last_rank")
        
        # Fetch total managers from league standings API if show_total is True
        total_managers = None
        if show_total and league_id:
            total_managers = get_league_size(league_id)
        
        # Determine arrow and current rank color
        if current_rank and previous_rank:
            if current_rank < previous_rank:
                arrow = "↑"
                arrow_color = "#00ff87"
                current_rank_color = "#00ff87"
            elif current_rank > previous_rank:
                arrow = "↓"
                arrow_color = "#f64646"
                current_rank_color = "#f64646"
            else:
                arrow = "—"
                arrow_color = "#999"
                current_rank_color = "#999"
        else:
            arrow = "—"
            arrow_color = "#999"
            current_rank_color = "#999"
        
        # Override colors for top 3 ranks (gold/silver/bronze)
        current_rank_weight = "700"
        previous_rank_weight = "700"
        previous_rank_color = "#999"
        current_rank_size = "16px"
        previous_rank_size = "16px"
        
        if current_rank == 1:
            current_rank_color = "#FFD700"  # Gold
            current_rank_weight = "900"
            current_rank_size = "20px"
        elif current_rank == 2:
            current_rank_color = "#C0C0C0"  # Silver
            current_rank_weight = "900"
            current_rank_size = "20px"
        elif current_rank == 3:
            current_rank_color = "#CD7F32"  # Bronze
            current_rank_weight = "900"
            current_rank_size = "20px"
        
        if previous_rank == 1:
            previous_rank_color = "#FFD700"  # Gold
            previous_rank_weight = "900"
            previous_rank_size = "20px"
        elif previous_rank == 2:
            previous_rank_color = "#C0C0C0"  # Silver
            previous_rank_weight = "900"
            previous_rank_size = "20px"
        elif previous_rank == 3:
            previous_rank_color = "#CD7F32"  # Bronze
            previous_rank_weight = "900"
            previous_rank_size = "20px"
        
        current_display = format_rank(current_rank)
        previous_display = format_rank(previous_rank)
        total_display = format_rank(total_managers) if total_managers else "N/A"
        
        # Add total managers line if show_total is True (for mini leagues)
        total_line = f"""<div class="total-managers">Total managers: {total_display}</div>""" if show_total else ""
        
        rows += f"""<div class="league-row"><div class="league-name">{league_name}</div><div class="league-ranks"><span class="rank-label">Current:</span> <span class="rank-value" style="color: {current_rank_color}; font-weight: {current_rank_weight}; font-size: {current_rank_size};">{current_display}</span><span class="rank-label">Previous:</span> <span class="rank-value" style="color: {previous_rank_color}; font-weight: {previous_rank_weight}; font-size: {previous_rank_size};">{previous_display}</span><span class="rank-arrow" style="color: {arrow_color};">{arrow}</span></div>{total_line}</div>"""
    return rows

mini_rows = build_league_rows(mini_leagues, show_total=True)
public_rows = build_league_rows(public_leagues, show_total=False)

st.markdown(f"""<div class="home-container"><div class="glass-box points-box"><div class="team-name">{team_name}</div><div class="gw">Gameweek {gw}</div><div class="points-row"><div class="side-points"><div class="side-label">Average</div><div class="side-value">{avg_points}</div></div><div class="points">{gw_points}</div><div class="side-points"><div class="side-label">Highest</div><div class="side-value">{highest_points}</div></div></div></div><div class="glass-box leagues-box"><div class="leagues-sections"><div class="league-section"><div class="leagues-title">Mini Leagues</div>{mini_rows}</div><div class="league-section"><div class="leagues-title">Public Leagues</div>{public_rows}</div></div></div></div>""", unsafe_allow_html=True)

if st.button("Points →", key="nav-btn"):
    st.switch_page("pages/points.py")