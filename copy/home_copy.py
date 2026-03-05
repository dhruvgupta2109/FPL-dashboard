import streamlit as st # type: ignore
import streamlit.components.v1 as components # type: ignore
import json
import urllib.request
import ssl
import certifi
from datetime import datetime, timezone

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
    background: linear-gradient(135deg, #37003c, #2b1e5b, #00cc6a) !important;
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
    margin-top: 20px;
    font-size: 1.25rem; /* base font size up */
}

.team-name { font-size: 18px; font-weight: 800; opacity: 0.92; margin-bottom: 4px; }
.gw-label  { font-size: 15px; opacity: 0.8;   margin-bottom: 12px; }

.points-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 30px;
}

.big-points { font-size: 70px; font-weight: 900; line-height: 1; color: white; }

.side-points { display: flex; flex-direction: column; align-items: center; }
.side-label  { font-size: 14px; opacity: 0.8; margin-bottom: 2px; }
.side-value  { font-size: 30px; font-weight: 700; color: rgba(255,255,255,0.85); }

/* ── Leagues box ── */
.leagues-box {
    padding: 24px;
    border-radius: 22px;
    box-shadow: 0 20px 45px rgba(0,0,0,0.35);
    margin-top: 20px;
}

/* ── Countdown and matches (left column) ── */
.matches-box {
    padding: 18px 16px;
    border-radius: 22px;
    box-shadow: 0 20px 45px rgba(0,0,0,0.35);
    margin-top: 14px;
}

/* Fixtures burger layout */
.matches-header-box {
    padding: 14px 16px 10px 16px;
    border-radius: 22px 22px 0 0;
    box-shadow: 0 20px 45px rgba(0,0,0,0.35);
    margin-top: 14px;
    margin-bottom: 0;
    border-bottom: 1px solid rgba(255,255,255,0.18);
}

.matches-body-box {
    padding: 10px 16px 14px 16px;
    border-radius: 0 0 22px 22px;
    box-shadow: 0 20px 45px rgba(0,0,0,0.35);
    margin-top: 0;
}

.matches-section-title {
    font-size: 15px;
    font-weight: 700;
    opacity: 0.92;
    margin: 0;
    color: #ffffff;
    text-align: center;
}

.st-key-see_fixtures {
    margin-top: 15.5px !important;
    margin-bottom: 0 !important;
    border-radius: 0 !important;
}

.st-key-see_fixtures button {
    width: 100% !important;
    min-width: 0 !important;
    padding: 10px 14px !important;
    border-radius: 0 !important;
    border: 1px solid rgba(0,255,135,0.55) !important;
    background: linear-gradient(135deg, rgba(0,255,135,0.22), rgba(255,255,255,0.12)) !important;
    color: #00ff87 !important;
    font-size: 14px !important;
    font-weight: 800 !important;
    box-shadow: 0 6px 16px rgba(0,0,0,0.25) !important;
    margin: 0 !important;
}

.st-key-see_fixtures button:hover {
    background: linear-gradient(135deg, rgba(0,255,135,0.3), rgba(255,255,255,0.18)) !important;
    color: #ffffff !important;
}

.st-key-see_leagues {
    margin-top: 15.5px !important;
    margin-bottom: 0 !important;
    border-radius: 0 !important;
}

.st-key-see_leagues button {
    width: 100% !important;
    min-width: 0 !important;
    padding: 10px 14px !important;
    border-radius: 0 !important;
    border: 1px solid rgba(0,255,135,0.55) !important;
    background: linear-gradient(135deg, rgba(0,255,135,0.22), rgba(255,255,255,0.12)) !important;
    color: #00ff87 !important;
    font-size: 14px !important;
    font-weight: 800 !important;
    box-shadow: 0 6px 16px rgba(0,0,0,0.25) !important;
    margin: 0 !important;
}

.st-key-see_leagues button:hover {
    background: linear-gradient(135deg, rgba(0,255,135,0.3), rgba(255,255,255,0.18)) !important;
    color: #ffffff !important;
}

.section-title {
    font-size: 15px;
    font-weight: 700;
    opacity: 0.92;
    margin-bottom: 12px;
    text-align: center;
    border-bottom: 1px solid rgba(255,255,255,0.2);
    padding-bottom: 8px;
}

.match-row {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 8px;
    padding: 10px;
    margin-bottom: 8px;
    border-radius: 12px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
}

.match-head {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    padding: 0 10px;
}

.match-head-side {
    font-size: 11px;
    font-weight: 700;
    opacity: 0.75;
}

.match-head-side.right {
    text-align: right;
}

.team-cell {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
}

.team-cell.right {
    justify-content: flex-end;
}

.team-logo {
    width: 20px;
    height: 20px;
    object-fit: contain;
    flex-shrink: 0;
}

.team-name-small {
    font-size: 15px;
    font-weight: 700;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.score-cell {
    text-align: center;
    min-width: 90px;
}

.score-main {
    font-size: 15px;
    font-weight: 800;
    color: #ffffff;
}

.score-sub {
    font-size: 11px;
    opacity: 0.75;
    margin-top: 2px;
}

.leagues-sections { display: flex; gap: 20px; }
.league-section   { flex: 1; min-width: 0; }

.leagues-header-box {
    padding: 14px 16px 10px 16px;
    border-radius: 22px 22px 0 0;
    box-shadow: 0 20px 45px rgba(0,0,0,0.35);
    margin-top: 20px;
    margin-bottom: 0;
    border-bottom: 1px solid rgba(255,255,255,0.18);
}

.leagues-body-box {
    padding: 10px 16px 14px 16px;
    border-radius: 0 0 22px 22px;
    box-shadow: 0 20px 45px rgba(0,0,0,0.35);
    margin-top: 0;
}

.leagues-headings {
    display: flex;
    gap: 20px;
}

.leagues-title {
    font-size: 18px;
    font-weight: 700;
    margin: 0;
    text-align: center;
    padding-bottom: 0;
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
    font-style: normal;
}

.trends-wrap {
    margin-top: 56px;
}

.trend-box {
    padding: 14px 14px 12px 14px;
    border-radius: 16px;
    min-height: 340px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.28);
}

/* Restore gap for the 3-card trends row in the right column */
div[data-testid="stColumn"]:nth-of-type(2)
  > div[data-testid="stVerticalBlock"]
  > div[data-testid="stHorizontalBlock"] {
        gap: 32px !important;
}

.trend-title {
    margin: 0 0 8px 0;
    text-align: center;
    font-size: 15px;
    font-weight: 800;
    color: #ffffff;
}

.trend-subtitle {
    margin: 0 0 10px 0;
    text-align: center;
    font-size: 11px;
    opacity: 0.78;
}

.trend-list {
    margin: 0;
    padding: 0;
    list-style: none;
}

.trend-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    padding: 8px 24px;
    margin-bottom: 7px;
    border-radius: 10px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.14);
}

.trend-player {
    flex: 1;
    font-size: 15px;
    font-weight: 700;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.trend-value {
    font-size: 12px;
    font-weight: 800;
    color: #00ff87;
    flex-shrink: 0;
}

.trend-empty {
    text-align: center;
    font-size: 12px;
    opacity: 0.75;
    padding: 18px 8px;
}

/* Zero gap and padding on column layout rows */
div[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}
div[data-testid="stColumn"] {
    padding: 0 !important;
    min-width: 0 !important;
}
div[data-testid="stColumn"] > div {
    padding: 0 !important;
    gap: 0 !important;
}
/* Restore gap on the outermost layout row only */
div[data-testid="stMain"] > div > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]:first-of-type {
    gap: 24px !important;
}

/* ── Nav buttons ── */
div[data-testid="stButton"] > button {
    padding: 14px 0 !important;
    background: rgba(255,255,255,0.12) !important;
    color: #00ff87 !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    border: none !important;
    border-top: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 0 !important;
    margin: 0 !important;
    width: 100% !important;
    transition: background 0.2s ease !important;
}
div[data-testid="stButton"] > button:hover {
    background: rgba(0,255,135,0.2) !important;
    color: white !important;
}
/* Points — bottom-left curve only */
div[data-testid="stColumn"]:nth-of-type(1) div[data-testid="stButton"] > button {
    border-radius: 0 0 0 22px !important;
    border-right: 1px solid rgba(255,255,255,0.15) !important;
}
/* Graphs — bottom-right curve only */
div[data-testid="stColumn"]:nth-of-type(2) div[data-testid="stButton"] > button {
    border-radius: 0 0 22px 0 !important;
}

/* Keep Fixtures button fully uncurved (override column corner rules) */
div[data-testid="stColumn"]:nth-of-type(1) .st-key-see_fixtures div[data-testid="stButton"] > button,
div[data-testid="stColumn"]:nth-of-type(2) .st-key-see_fixtures div[data-testid="stButton"] > button,
div[data-testid="stColumn"]:nth-of-type(1) .st-key-see_fixtures div[data-testid="stButton"] > button:hover,
div[data-testid="stColumn"]:nth-of-type(2) .st-key-see_fixtures div[data-testid="stButton"] > button:hover,
div[data-testid="stColumn"]:nth-of-type(1) .st-key-see_fixtures div[data-testid="stButton"] > button:focus,
div[data-testid="stColumn"]:nth-of-type(2) .st-key-see_fixtures div[data-testid="stButton"] > button:focus,
div[data-testid="stColumn"]:nth-of-type(1) .st-key-see_fixtures div[data-testid="stButton"] > button:active,
div[data-testid="stColumn"]:nth-of-type(2) .st-key-see_fixtures div[data-testid="stButton"] > button:active {
    border-radius: 0 !important;
    border-bottom-left-radius: 0 !important;
    border-bottom-right-radius: 0 !important;
    border-right: 1px solid rgba(255,255,255,0.35) !important;
    border-left: 1px solid rgba(255,255,255,0.35) !important;
}

/* Keep Mini Leagues button fully uncurved too */
div[data-testid="stColumn"]:nth-of-type(1) .st-key-see_leagues div[data-testid="stButton"] > button,
div[data-testid="stColumn"]:nth-of-type(2) .st-key-see_leagues div[data-testid="stButton"] > button,
div[data-testid="stColumn"]:nth-of-type(1) .st-key-see_leagues div[data-testid="stButton"] > button:hover,
div[data-testid="stColumn"]:nth-of-type(2) .st-key-see_leagues div[data-testid="stButton"] > button:hover,
div[data-testid="stColumn"]:nth-of-type(1) .st-key-see_leagues div[data-testid="stButton"] > button:focus,
div[data-testid="stColumn"]:nth-of-type(2) .st-key-see_leagues div[data-testid="stButton"] > button:focus,
div[data-testid="stColumn"]:nth-of-type(1) .st-key-see_leagues div[data-testid="stButton"] > button:active,
div[data-testid="stColumn"]:nth-of-type(2) .st-key-see_leagues div[data-testid="stButton"] > button:active {
    border-radius: 0 !important;
    border-bottom-left-radius: 0 !important;
    border-bottom-right-radius: 0 !important;
    border-right: 1px solid rgba(255,255,255,0.35) !important;
    border-left: 1px solid rgba(255,255,255,0.35) !important;
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
def fetch_bootstrap_data():
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    with urllib.request.urlopen(url, context=ctx) as r:
        return json.loads(r.read())

@st.cache_data(ttl=120)
def fetch_fixtures(event_id):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = f"https://fantasy.premierleague.com/api/fixtures/?event={event_id}"
    with urllib.request.urlopen(url, context=ctx) as r:
        return json.loads(r.read())

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

def parse_deadline(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None

def next_deadline_info(events, current_gw):
    if not events:
        return None, None

    next_event = next((e for e in events if e.get("is_next")), None)
    if not next_event:
        next_event = next((e for e in events if (e.get("id") or 0) > current_gw), None)

    if not next_event:
        return None, None

    return next_event.get("id"), parse_deadline(next_event.get("deadline_time"))

def logo_url(team_code):
    if not team_code:
        return ""
    return f"https://resources.premierleague.com/premierleague/badges/50/t{team_code}.png"

def kickoff_label(kickoff_str):
    dt = parse_deadline(kickoff_str)
    if not dt:
        return "Kickoff TBC"
    return dt.strftime("%d %b %H:%M UTC")

def safe_int(value):
    try:
        return int(value)
    except Exception:
        return 0

def safe_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0

def build_top5_trends(bootstrap, gw):
    elements = bootstrap.get("elements", [])
    events = bootstrap.get("events", [])

    player_by_id = {p.get("id"): p for p in elements if p.get("id") is not None}

    subbed_in = sorted(elements, key=lambda p: safe_int(p.get("transfers_in_event")), reverse=True)[:5]
    subbed_out = sorted(elements, key=lambda p: safe_int(p.get("transfers_out_event")), reverse=True)[:5]

    current_event = next((e for e in events if e.get("id") == gw), {})
    most_captained_id = current_event.get("most_captained")

    top_by_ownership = sorted(elements, key=lambda p: safe_float(p.get("selected_by_percent")), reverse=True)
    captained = []
    seen_ids = set()

    if most_captained_id in player_by_id:
        captained.append(player_by_id[most_captained_id])
        seen_ids.add(most_captained_id)

    for player in top_by_ownership:
        pid = player.get("id")
        if pid in seen_ids:
            continue
        captained.append(player)
        seen_ids.add(pid)
        if len(captained) == 5:
            break

    def player_name(player):
        return player.get("web_name") or player.get("second_name") or "Unknown"

    captained_rows = [
        {
            "name": player_name(p),
            "value": f"{safe_float(p.get('selected_by_percent')):.1f}%",
        }
        for p in captained[:5]
    ]

    subbed_in_rows = [
        {
            "name": player_name(p),
            "value": f"{safe_int(p.get('transfers_in_event')):,}",
        }
        for p in subbed_in
    ]

    subbed_out_rows = [
        {
            "name": player_name(p),
            "value": f"{safe_int(p.get('transfers_out_event')):,}",
        }
        for p in subbed_out
    ]

    return captained_rows, subbed_in_rows, subbed_out_rows

def build_trend_box_html(title, subtitle, rows):
    if not rows:
        rows_html = '<div class="trend-empty">No data available.</div>'
    else:
        items = []
        for idx, row in enumerate(rows, start=1):
            items.append(
                f'<li class="trend-row">'
                f'  <span class="trend-player">{idx}. {row["name"]}</span>'
                f'  <span class="trend-value">{row["value"]}</span>'
                f'</li>'
            )
        rows_html = f'<ol class="trend-list">{"".join(items)}</ol>'

    subtitle_html = f'<p class="trend-subtitle">{subtitle}</p>' if subtitle else ""

    return (
        f'<div class="glass-box trend-box">'
        f'  <h4 class="trend-title">{title}</h4>'
        f'  {subtitle_html}'
        f'  {rows_html}'
        f'</div>'
    )

live_pts = fetch_live_points(gw)
avg_points, highest_points = fetch_gw_stats(gw)
picks    = sorted(st.session_state.picks["picks"], key=lambda x: x["position"])
starters = picks[:11]
gw_points = sum(live_pts.get(p["element"], 0) * p.get("multiplier", 1) for p in starters)

mini_leagues, public_leagues = fetch_leagues(manager_id)
bootstrap_data = fetch_bootstrap_data()
events = bootstrap_data.get("events", [])
teams = bootstrap_data.get("teams", [])
next_gw, next_deadline = next_deadline_info(events, gw)

team_map = {
    t.get("id"): {
        "name": t.get("name", "Unknown"),
        "code": t.get("code")
    }
    for t in teams
}

fixtures = fetch_fixtures(gw)
captained_top5, subbed_in_top5, subbed_out_top5 = build_top5_trends(bootstrap_data, gw)

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

matches_html = ""
for fx in fixtures:
    home_id = fx.get("team_h")
    away_id = fx.get("team_a")
    home = team_map.get(home_id, {"name": "Home", "code": None})
    away = team_map.get(away_id, {"name": "Away", "code": None})

    hs = fx.get("team_h_score")
    aas = fx.get("team_a_score")
    finished = fx.get("finished")

    if hs is not None and aas is not None:
        score_text = f"{hs} - {aas}"
    else:
        score_text = "vs"

    sub_text = "FT" if finished else kickoff_label(fx.get("kickoff_time"))

    matches_html += (
        f'<div class="match-row">'
        f'  <div class="team-cell">'
        f'    <img class="team-logo" src="{logo_url(away.get("code"))}" alt="{away.get("name")}">'
        f'    <div class="team-name-small">{away.get("name")}</div>'
        f'  </div>'
        f'  <div class="score-cell">'
        f'    <div class="score-main">{score_text}</div>'
        f'    <div class="score-sub">{sub_text}</div>'
        f'  </div>'
        f'  <div class="team-cell right">'
        f'    <div class="team-name-small">{home.get("name")}</div>'
        f'    <img class="team-logo" src="{logo_url(home.get("code"))}" alt="{home.get("name")}">'
        f'  </div>'
        f'</div>'
    )

if not matches_html:
    matches_html = '<div class="score-sub" style="text-align:center;padding:10px;">No fixtures found for this gameweek.</div>'

# ── Layout: two columns — left (fixed 400px), right (leagues) ────────────────
left_col, right_col = st.columns([1, 2])

with left_col:
    # Glass card — flat bottom so the Streamlit buttons attach flush below
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

    st.markdown("""
    <div style='height: 32px;'></div>
    """, unsafe_allow_html=True)
    btn1, btn2 = st.columns(2)
    # Inject style targeting the button row that was just created
    st.markdown("""
    <style>
    /* Target the inner button row specifically — override Streamlit inline gap */
    div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlock"]
    div[data-testid="stHorizontalBlock"] {
        gap: 0px !important;
        column-gap: 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    with btn1:
        if st.button("Points →", key="nav_points", use_container_width=True):
            st.switch_page("pages/points.py")
    with btn2:
        if st.button("Graphs →", key="nav_graphs", use_container_width=True):
            st.switch_page("pages/graphs.py")

    deadline_iso = next_deadline.isoformat() if next_deadline else ""
    next_gw_label = next_gw if next_gw else (gw + 1)
    components.html(
        f"""
        <div style="
            margin-top: 14px;
            border-radius: 22px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            box-shadow: 0 20px 45px rgba(0,0,0,0.35);
            color: #fff;
            text-align:center;
            padding: 16px 12px 1px 1px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        ">
            <div style="font-size:15px;font-weight:700;opacity:0.92;margin-bottom:10px;">Deadline Countdown (GW {next_gw_label})</div>
            <div id="deadline-countdown" style="font-size:32px;font-weight:800;letter-spacing:1px;color:#00ff87;">--:--:--</div>
            <div id="deadline-format" style="font-size:11px;opacity:0.7;margin-top:4px;">(Days:Hours:Minutes:Seconds)</div>
            <div id="deadline-sub" style="font-size:12px;opacity:0.8;margin-top:6px;">Calculating...</div>
        </div>
        <script>
            const deadlineIso = "{deadline_iso}";
            const target = deadlineIso ? new Date(deadlineIso) : null;
            const valueEl = document.getElementById("deadline-countdown");
            const formatEl = document.getElementById("deadline-format");
            const subEl = document.getElementById("deadline-sub");

            function pad(n) {{ return String(n).padStart(2, "0"); }}

            function tick() {{
                if (!target || isNaN(target.getTime())) {{
                    valueEl.textContent = "N/A";
                    formatEl.textContent = "Days : Hours : Minutes : Seconds";
                    subEl.textContent = "Next deadline unavailable";
                    return;
                }}

                const now = new Date();
                let diff = Math.floor((target - now) / 1000);

                if (diff <= 0) {{
                    valueEl.textContent = "00:00:00";
                    formatEl.textContent = " Hours : Minutes : Seconds ";
                    subEl.textContent = "Deadline passed";
                    return;
                }}

                const days = Math.floor(diff / 86400);
                diff %= 86400;
                const hours = Math.floor(diff / 3600);
                diff %= 3600;
                const mins = Math.floor(diff / 60);
                const secs = diff % 60;

                let display = '';
                if (days > 0) {{
                    display = `${{days}}:${{pad(hours)}}:${{pad(mins)}}:${{pad(secs)}}`;
                    formatEl.textContent = " Days : Hours : Minutes : Seconds ";
                }} else {{
                    display = `${{pad(hours)}}:${{pad(mins)}}:${{pad(secs)}}`;
                    formatEl.textContent = " Hours : Minutes : Seconds ";
                }}
                valueEl.textContent = display;
                // Format deadline as 12-hour time with AM/PM
                const options = {{ month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', hour12: true, timeZone: 'UTC' }};
                const formattedDeadline = target.toLocaleString('en-US', options) + ' UTC';
                subEl.textContent = `Deadline: ${{formattedDeadline}}`;
            }}

            tick();
            setInterval(tick, 1000);
        </script>
        """,
        height=150,
    )

    # Fixtures burger: title (top), button (middle), matches (bottom)
    st.markdown(f"""
    <div class="glass-box matches-header-box">
        <div class="matches-section-title">Fixtures & Results GW{gw}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("See All Stats", key="see_fixtures", use_container_width=True):
        st.switch_page("pages/fixtures.py")

    st.markdown(f"""
    <div class="glass-box matches-body-box">
        <div class="match-head">
            <div class="match-head-side">Away</div>
            <div></div>
            <div class="match-head-side right">Home</div>
        </div>
        {matches_html}
    </div>
    """, unsafe_allow_html=True)

with right_col:
    st.markdown(f"""
    <div class="glass-box leagues-header-box">
        <div class="leagues-headings">
            <div class="league-section">
                <div class="leagues-title">Mini Leagues</div>
            </div>
            <div class="league-section">
                <div class="leagues-title">Public Leagues</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("See All League Details", key="see_leagues", use_container_width=True):
        st.switch_page("pages/leagues.py")

    st.markdown(f"""
    <div class="glass-box leagues-body-box">
        <div class="leagues-sections">
            <div class="league-section">{mini_html}</div>
            <div class="league-section">{public_html}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="trends-wrap"></div>', unsafe_allow_html=True)
    t1, gap1, t2, gap2, t3 = st.columns([1, 0.06, 1, 0.06, 1])

    with t1:
        st.markdown(
            build_trend_box_html(
                f"Most Captained for GW{gw}",
                "",
                captained_top5,
            ),
            unsafe_allow_html=True,
        )

    with t2:
        st.markdown(
            build_trend_box_html(
                f"Most Subbed In for GW{gw}",
                "",
                subbed_in_top5,
            ),
            unsafe_allow_html=True,
        )

    with t3:
        st.markdown(
            build_trend_box_html(
                f"Most Subbed Out for GW{gw}",
                "",
                subbed_out_top5,
            ),
            unsafe_allow_html=True,
        )