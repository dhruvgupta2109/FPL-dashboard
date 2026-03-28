import streamlit as st
import json
import urllib.request
import ssl
import certifi

st.set_page_config(page_title="FPL Home", layout="wide")

if "manager_id" not in st.session_state:
    st.warning("No manager ID found. Go back to Dashboard and connect your team.")
    if st.button("Go to Dashboard"):
        st.switch_page("live_dashboard.py")
    st.stop()

# ── Global styles ────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── App background ── */
.stApp {
    background: linear-gradient(135deg, #37003c, #2b1e5b, #00ff87) !important;
    min-height: 100vh;
}
.stMainBlockContainer {
    padding-top: 3.5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: none !important;
}

/* Gap between left (points) column and right (leagues) column */
div[data-testid="stHorizontalBlock"]:first-of-type {
    gap: 24px !important;
    align-items: flex-start !important;
}

/* ── Glassmorphism card ── */
.glass-box {
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    color: white;
    border: 1px solid rgba(255,255,255,0.2);
}

/* ── Points box ── */
.points-box {
    text-align: center;
    border-radius: 22px 22px 0 0;
    padding: 30px 30px 24px 30px;
    box-shadow: 0 20px 45px rgba(0,0,0,0.35);
}

.team-name { font-size: 16px; font-weight: 700; opacity: 0.85; margin-bottom: 4px; }
.gw-label  { font-size: 13px; opacity: 0.7; margin-bottom: 12px; }

.points-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 30px;
}

.big-points { font-size: 64px; font-weight: 800; line-height: 1; color: white; }

.side-points { display: flex; flex-direction: column; align-items: center; }
.side-label  { font-size: 11px; opacity: 0.7; margin-bottom: 4px; }
.side-value  { font-size: 28px; font-weight: 600; color: rgba(255,255,255,0.75); }

/* ── Leagues box ── */
.leagues-box {
    padding: 24px;
    border-radius: 22px;
    box-shadow: 0 20px 45px rgba(0,0,0,0.35);
    margin-top: 0;
}

.leagues-sections { display: flex; gap: 20px; }
.league-section   { flex: 1; min-width: 0; }

.leagues-title {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 12px;
    text-align: center;
    border-bottom: 1px solid rgba(255,255,255,0.2);
    padding-bottom: 10px;
    color: white;
}

.league-row {
    padding: 12px;
    margin-bottom: 8px;
    background: rgba(255,255,255,0.08);
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.15);
    color: white;
}

.league-name  { font-size: 15px; font-weight: 700; margin-bottom: 6px; }

.league-ranks {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 13px;
    flex-wrap: wrap;
}

.rank-label { opacity: 0.7; font-size: 12px; }
.rank-arrow { font-size: 20px; font-weight: 700; margin-left: auto; }

.total-managers {
    font-size: 12px;
    color: rgba(255,255,255,0.6);
    margin-top: 6px;
    font-style: italic;
}

/* ── Nav buttons — attach flush below points-box ── */
div[data-testid="stButton"] > button {
    padding: 14px 0 !important;
    text-align: center !important;
    background: rgba(255,255,255,0.12) !important;
    backdrop-filter: blur(18px) !important;
    color: #00ff87 !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    letter-spacing: 0.4px !important;
    border: none !important;
    border-top: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 0 !important;
    box-shadow: 0 20px 45px rgba(0,0,0,0.35) !important;
    margin: 0 !important;
    transition: background 0.2s ease !important;
    width: 100% !important;
}
div[data-testid="stButton"] > button:hover {
    background: rgba(0,255,135,0.2) !important;
    color: white !important;
}

/* Points button — curves bottom-left only */
div[data-testid="stColumn"]:nth-of-type(1) div[data-testid="stButton"] > button {
    border-radius: 0 0 0 22px !important;
    color: #00ff87 !important;
}

/* Graphs button — curves bottom-right only, same green colour */
div[data-testid="stColumn"]:nth-of-type(2) div[data-testid="stButton"] > button {
    border-radius: 0 0 22px 0 !important;
    color: #00ff87 !important;
    font-size: 15px !important;
    border-left: 1px solid rgba(255,255,255,0.15) !important;
}

/* Remove gap between nav button columns so they sit flush */
div[data-testid="stHorizontalBlock"]:not(:first-of-type) {
    gap: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Remove Streamlit's default padding around columns */
div[data-testid="stColumn"] {
    padding: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Data ─────────────────────────────────────────────────────────────────────
gw         = st.session_state.gw
entry      = st.session_state.entry
team_name  = entry["name"]
manager_id = st.session_state.manager_id

@st.cache_data(ttl=60)
def fetch_live_points(gw):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = f"https://fantasy.premierleague.com/api/event/{gw}/live/"
    with urllib.request.urlopen(url, context=ctx) as r:
        data = json.loads(r.read())
    return {e["id"]: e["stats"]["total_points"] for e in data["elements"]}

@st.cache_data(ttl=60)
def fetch_gw_stats(gw):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    with urllib.request.urlopen(url, context=ctx) as r:
        bootstrap = json.loads(r.read())
    for event in bootstrap.get("events", []):
        if event["id"] == gw:
            return round(event.get("average_entry_score") or 0), (event.get("highest_score") or 0)
    return 0, 0

@st.cache_data(ttl=300)
def fetch_leagues(manager_id):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/"
    with urllib.request.urlopen(url, context=ctx) as r:
        data = json.loads(r.read())
    all_leagues    = data.get("leagues", {}).get("classic", [])
    mini_leagues   = []
    public_leagues = []
    for l in all_leagues:
        ld = {k: l.get(k) for k in ("name","id","entry_rank","entry_last_rank","league_type","admin_entry","start_event","scoring")}
        (mini_leagues if l.get("league_type") == "x" else public_leagues).append(ld)
    return mini_leagues, public_leagues

def get_league_size(league_id):
    if not league_id:
        return None
    try:
        ctx = ssl.create_default_context(cafile=certifi.where())
        req = urllib.request.Request(
            f"https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            data = json.loads(r.read())
        li   = data.get("league", {})
        size = li.get("size") or li.get("max_entries") or len(data.get("standings", {}).get("results", []))
        return size if size and size > 0 else None
    except Exception:
        return None

def fmt(rank):
    return f"{rank:,}" if rank is not None else "N/A"

def rank_style(rank):
    if rank == 1: return "#FFD700", "900", "20px"
    if rank == 2: return "#C0C0C0", "900", "20px"
    if rank == 3: return "#CD7F32", "900", "20px"
    return None, "700", "16px"

live_pts = fetch_live_points(gw)
avg_points, highest_points = fetch_gw_stats(gw)
picks    = sorted(st.session_state.picks["picks"], key=lambda x: x["position"])
starters = picks[:11]
gw_points = sum(live_pts.get(p["element"], 0) * p.get("multiplier", 1) for p in starters)

mini_leagues, public_leagues = fetch_leagues(manager_id)

def build_league_html(leagues, show_total=False, max_count=5):
    html = ""
    for league in leagues[:max_count]:
        name   = league.get("name", "Unknown")
        lid    = league.get("id")
        cur    = league.get("entry_rank")
        prev   = league.get("entry_last_rank")

        total_line = ""
        if show_total and lid:
            size = get_league_size(lid)
            total_line = f'<div class="total-managers">Total managers: {fmt(size)}</div>'

        if cur and prev:
            if cur < prev:   arrow, ac, default_cc = "↑", "#00ff87", "#00ff87"
            elif cur > prev: arrow, ac, default_cc = "↓", "#f64646", "#f64646"
            else:            arrow, ac, default_cc = "—", "#999",    "#999"
        else:
            arrow, ac, default_cc = "—", "#999", "#999"

        cc, cw, cs = rank_style(cur);   cc = cc or default_cc
        pc, pw, ps = rank_style(prev);  pc = pc or "#999"

        html += (
            f'<div class="league-row">'
            f'<div class="league-name">{name}</div>'
            f'<div class="league-ranks">'
            f'<span class="rank-label">Current:</span>'
            f'<span style="color:{cc};font-weight:{cw};font-size:{cs};font-family:sans-serif;">{fmt(cur)}</span>'
            f'<span class="rank-label">Previous:</span>'
            f'<span style="color:{pc};font-weight:{pw};font-size:{ps};font-family:sans-serif;">{fmt(prev)}</span>'
            f'<span class="rank-arrow" style="color:{ac};">{arrow}</span>'
            f'</div>{total_line}</div>'
        )
    return html

mini_html   = build_league_html(mini_leagues,   show_total=True)
public_html = build_league_html(public_leagues, show_total=False)

# ── Layout: two columns — left (fixed 400px), right (leagues) ────────────────
left_col, right_col = st.columns([1, 2])

with left_col:
    # Points glassbox
    st.markdown(f"""
    <div class="glass-box points-box">
        <div class="team-name">{team_name}</div>
        <div class="gw-label">Gameweek {gw}</div>
        <div class="points-row">
            <div class="side-points">
                <div class="side-label">Average</div>
                <div class="side-value">{avg_points}</div>
            </div>
            <div class="big-points">{gw_points}</div>
            <div class="side-points">
                <div class="side-label">Highest</div>
                <div class="side-value">{highest_points}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Two nav buttons flush below — use nested columns so they sit side by side
    btn1, btn2 = st.columns(2)
    with btn1:
        if st.button("Points →", key="nav_points", use_container_width=True):
            st.switch_page("pages/points.py")
    with btn2:
        if st.button("Graphs →", key="nav_graphs", use_container_width=True):
            st.switch_page("pages/graphs.py")

with right_col:
    st.markdown(f"""
    <div class="glass-box leagues-box">
        <div class="leagues-sections">
            <div class="league-section">
                <div class="leagues-title">Mini Leagues</div>
                {mini_html}
            </div>
            <div class="league-section">
                <div class="leagues-title">Public Leagues</div>
                {public_html}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)