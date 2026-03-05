import streamlit as st  # type: ignore
import json
import urllib.request
import ssl
import certifi
from datetime import datetime

st.set_page_config(page_title="FPL Fixtures", layout="wide")

if "manager_id" not in st.session_state:
    st.warning("No manager ID found. Go back to Dashboard and connect your team.")
    if st.button("Go to Dashboard"):
        st.switch_page("live_dashboard.py")
    st.stop()

if "gw" not in st.session_state:
    st.warning("No gameweek found. Go back to Home.")
    if st.button("Go to Home"):
        st.switch_page("pages/home.py")
    st.stop()

st.markdown(
    """
<style>
.stApp {
    background: linear-gradient(135deg, #37003c, #2b1e5b, #00ff87) !important;
    min-height: 100vh;
}
.stMainBlockContainer {
    max-width: none !important;
    padding-top: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

h1, h2, h3, p, div, span, li {
    color: white;
}

div[data-testid="stButton"] > button {
    background: rgba(255,255,255,0.12) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    border-radius: 12px !important;
    padding: 10px 18px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
}

div[data-testid="stButton"] > button:hover {
    background: rgba(255,255,255,0.22) !important;
}

.match-hero {
    border-radius: 18px 18px 0 0;
    border: 1px solid rgba(255,255,255,0.18);
    border-bottom: 0;
    background: rgba(255,255,255,0.10);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    box-shadow: 0 12px 28px rgba(0,0,0,0.30);
    padding: 14px 16px;
    margin-bottom: 0;
}

.match-grid {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 12px;
}

.side-wrap {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
}

.side-wrap.right {
    justify-content: flex-end;
}

.team-logo {
    width: 40px;
    height: 40px;
    object-fit: contain;
    flex-shrink: 0;
}

.team-name {
    font-size: 18px;
    font-weight: 700;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.score-wrap {
    text-align: center;
    min-width: 120px;
}

.score-main {
    font-size: 38px;
    line-height: 1;
    font-weight: 900;
    color: #00ff87;
}

.score-sub {
    font-size: 12px;
    margin-top: 6px;
    opacity: 0.85;
}

.section-title {
    font-size: 14px;
    font-weight: 700;
    margin-top: 8px;
    margin-bottom: 6px;
    color: #00ff87;
}

.empty-stat {
    font-size: 12px;
    opacity: 0.75;
    margin-bottom: 6px;
}

div[data-testid="stExpander"] {
    border-radius: 0 0 18px 18px !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
    border-top: 0 !important;
    background: rgba(255,255,255,0.10) !important;
    backdrop-filter: blur(18px) !important;
    -webkit-backdrop-filter: blur(18px) !important;
    margin-top: 0 !important;
    margin-bottom: 12px;
    overflow: hidden;
}

div[data-testid="stExpander"] details summary p {
    font-size: 16px !important;
    font-weight: 700 !important;
}

.page-caption {
    opacity: 0.8;
    margin-top: -4px;
    margin-bottom: 10px;
}

.split-row-title {
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 6px;
    color: #00ff87;
}

.player-chip {
    border: 1px solid rgba(255,255,255,0.15);
    background: rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 8px 10px;
    margin-bottom: 8px;
    min-height: 68px;
}

.chip-name {
    font-size: 13px;
    font-weight: 700;
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.chip-meta {
    font-size: 11px;
    opacity: 0.75;
    margin-top: 2px;
}

.chip-val {
    font-size: 18px;
    font-weight: 900;
    margin-top: 2px;
    color: #00ff87;
}
</style>
""",
    unsafe_allow_html=True,
)


def parse_deadline(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None


def kickoff_label(kickoff_str):
    dt = parse_deadline(kickoff_str)
    if not dt:
        return "Kickoff TBC"
    return dt.strftime("%d %b %H:%M UTC")


def logo_url(team_code):
    if not team_code:
        return ""
    return f"https://resources.premierleague.com/premierleague/badges/50/t{team_code}.png"


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


gw = st.session_state.gw
bootstrap_data = fetch_bootstrap_data()
fixtures = fetch_fixtures(gw)

teams = bootstrap_data.get("teams", [])
elements = bootstrap_data.get("elements", [])

team_map = {
    t.get("id"): {
        "name": t.get("name", "Unknown"),
        "short": t.get("short_name", "UNK"),
        "code": t.get("code"),
    }
    for t in teams
}

player_map = {
    e.get("id"): {
        "name": e.get("web_name") or e.get("second_name") or f"Player {e.get('id')}",
        "team": e.get("team"),
    }
    for e in elements
}


STAT_GROUPS = [
    ("Goals scored", ("goals_scored",)),
    ("Assists", ("assists",)),
    ("Yellow cards", ("yellow_cards",)),
    ("Red cards", ("red_cards",)),
    ("Saves", ("saves",)),
    ("Defensive contributions", ("defensive_contribution", "defensive_contributions")),
    ("Bonus points", ("bonus",)),
]


def extract_stat_entries(fixture, identifiers):
    stats_list = fixture.get("stats", []) or []
    stats_by_id = {s.get("identifier"): s for s in stats_list}
    rows = []

    for identifier in identifiers:
        stat_obj = stats_by_id.get(identifier)
        if not stat_obj:
            continue

        for side, team_key in (("h", "team_h"), ("a", "team_a")):
            team_id = fixture.get(team_key)
            team_short = team_map.get(team_id, {}).get("short", "UNK")

            for event in stat_obj.get(side, []) or []:
                value = event.get("value") or 0
                player_id = event.get("element")
                if value <= 0:
                    continue

                player_name = player_map.get(player_id, {}).get("name", f"Player {player_id}")
                rows.append((player_name, team_short, value))

    rows.sort(key=lambda r: (-r[2], r[0]))
    return rows


def render_player_stat_grid(rows, per_row=3, center_rows=False):
    if not rows:
        st.markdown("<div class='empty-stat'>None recorded yet for this gameweek</div>", unsafe_allow_html=True)
        return

    if center_rows:
        for player_name, team_short, value in rows:
            cols = st.columns([1, 1.6, 1])
            with cols[1]:
                st.markdown(
                    f"""
                    <div class="player-chip">
                        <div class="chip-name">{player_name}</div>
                        <div class="chip-meta">{team_short}</div>
                        <div class="chip-val">{value}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        return

    for start in range(0, len(rows), per_row):
        row_items = rows[start:start + per_row]
        cols = st.columns(per_row)
        for idx, (player_name, team_short, value) in enumerate(row_items):
            with cols[idx]:
                st.markdown(
                    f"""
                    <div class="player-chip">
                        <div class="chip-name">{player_name}</div>
                        <div class="chip-meta">{team_short}</div>
                        <div class="chip-val">{value}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


sorted_fixtures = sorted(
    fixtures,
    key=lambda f: (
        parse_deadline(f.get("kickoff_time")) is None,
        parse_deadline(f.get("kickoff_time")) or datetime.max,
    ),
)

header_left, header_right = st.columns([1, 1])
with header_left:
    st.markdown(" ")
    st.title(f"Fixtures Stats • GW{gw}")
    st.markdown(" ")
with header_right:
        st.markdown("<div style='margin-top: 2.5rem;'>", unsafe_allow_html=True)
        if st.button("← Back to Home", use_container_width=True):
            st.switch_page("pages/home.py")
        st.markdown("</div>", unsafe_allow_html=True)

if not sorted_fixtures:
    st.info("No fixtures found for this gameweek.")
    st.stop()

for row_start in range(0, len(sorted_fixtures), 2):
    fixture_row = sorted_fixtures[row_start:row_start + 2]
    row_cols = st.columns(2)

    for col_idx, fx in enumerate(fixture_row):
        with row_cols[col_idx]:
            fixture_id = fx.get("id")

            home_id = fx.get("team_h")
            away_id = fx.get("team_a")
            home = team_map.get(home_id, {"name": "Home", "short": "H", "code": None})
            away = team_map.get(away_id, {"name": "Away", "short": "A", "code": None})

            home_score = fx.get("team_h_score")
            away_score = fx.get("team_a_score")

            if home_score is not None and away_score is not None:
                score_text = f"{away_score} - {home_score}"
            else:
                score_text = "vs"

            if fx.get("finished"):
                status_text = "FT"
            elif fx.get("started"):
                status_text = "Live"
            else:
                status_text = kickoff_label(fx.get("kickoff_time"))

            hero_html = f"""
                <div class="match-hero">
                    <div class="match-grid">
                        <div class="side-wrap">
                            <img class="team-logo" src="{logo_url(away.get('code'))}" alt="{away.get('name')}">
                            <div class="team-name">{away.get('name')}</div>
                        </div>
                        <div class="score-wrap">
                            <div class="score-main">{score_text}</div>
                            <div class="score-sub">{status_text}</div>
                        </div>
                        <div class="side-wrap right">
                            <div class="team-name">{home.get('name')}</div>
                            <img class="team-logo" src="{logo_url(home.get('code'))}" alt="{home.get('name')}">
                        </div>
                    </div>
                </div>
            """

            st.markdown(hero_html, unsafe_allow_html=True)

            with st.expander("Show player stats", expanded=False):

                st.caption(f"Fixture ID: {fixture_id}")

                goals_rows = extract_stat_entries(fx, ("goals_scored",))
                assists_rows = extract_stat_entries(fx, ("assists",))
                yellow_rows = extract_stat_entries(fx, ("yellow_cards",))
                red_rows = extract_stat_entries(fx, ("red_cards",))
                saves_rows = extract_stat_entries(fx, ("saves",))
                def_rows = extract_stat_entries(fx, ("defensive_contribution", "defensive_contributions"))
                bonus_rows = extract_stat_entries(fx, ("bonus",))

                ga_left, ga_right = st.columns(2)
                with ga_left:
                    st.markdown("<div class='split-row-title'>Goals</div>", unsafe_allow_html=True)
                    render_player_stat_grid(goals_rows, per_row=2)
                with ga_right:
                    st.markdown("<div class='split-row-title'>Assists</div>", unsafe_allow_html=True)
                    render_player_stat_grid(assists_rows, per_row=2)

                ysr_cols = st.columns(2)
                with ysr_cols[0]:
                    st.markdown("<div class='split-row-title'>Yellow Cards</div>", unsafe_allow_html=True)
                    render_player_stat_grid(yellow_rows, per_row=2)
                with ysr_cols[1]:
                    st.markdown("<div class='split-row-title'>Saves</div>", unsafe_allow_html=True)
                    render_player_stat_grid(saves_rows, per_row=2)

                    st.markdown("<div class='split-row-title'>Red Cards</div>", unsafe_allow_html=True)
                    render_player_stat_grid(red_rows, per_row=2)

                st.markdown("<div class='section-title'>Defensive contributions</div>", unsafe_allow_html=True)
                render_player_stat_grid(def_rows, per_row=3)

                st.markdown("<div class='section-title'>Bonus points</div>", unsafe_allow_html=True)
                render_player_stat_grid(bonus_rows, per_row=3)
