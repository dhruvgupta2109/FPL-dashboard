import html
import json
import ssl
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import certifi
import streamlit as st  # type: ignore
from nav import render_top_nav


st.set_page_config(page_title="FPL Players", layout="wide")

is_guest = st.session_state.get("guest", False)
if "manager_id" not in st.session_state and not is_guest:
    st.warning("No manager ID found. Go back to Dashboard and connect your team.")
    if st.button("Go to Dashboard"):
        st.switch_page("live_dashboard.py")
    st.stop()


ROOT_DIR = Path(__file__).resolve().parents[1]
LOCAL_BOOTSTRAP_PATH = ROOT_DIR / "data" / "raw" / "bootstrap_static.json"
LOCAL_FIXTURES_PATH = ROOT_DIR / "data" / "raw" / "fixtures.json"
BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
FIXTURES_URL = "https://fantasy.premierleague.com/api/fixtures/"
SUMMARY_URL = "https://fantasy.premierleague.com/api/element-summary/{element_id}/"


def esc(value):
    if value is None:
        return ""
    return html.escape(str(value))


def to_float(value, fallback=0.0):
    if value in (None, ""):
        return fallback
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def to_int(value, fallback=0):
    if value in (None, ""):
        return fallback
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def parse_dt(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_local_json(path, fallback):
    if not path.exists():
        return fallback
    try:
        with path.open() as f:
            return json.load(f)
    except Exception:
        return fallback


def fetch_json(url):
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, context=ctx, timeout=8) as response:
        return json.loads(response.read())


@st.cache_data(ttl=900, show_spinner=False)
def fetch_bootstrap_data():
    try:
        return fetch_json(BOOTSTRAP_URL)
    except Exception:
        return load_local_json(LOCAL_BOOTSTRAP_PATH, {})


@st.cache_data(ttl=900, show_spinner=False)
def fetch_fixtures_data():
    try:
        return fetch_json(FIXTURES_URL)
    except Exception:
        return load_local_json(LOCAL_FIXTURES_PATH, [])


@st.cache_data(ttl=900, show_spinner=False)
def fetch_player_summary(element_id):
    try:
        return fetch_json(SUMMARY_URL.format(element_id=element_id))
    except Exception:
        return {"fixtures": [], "history": [], "history_past": []}


def current_event_from_events(events):
    for flag in ("is_current", "is_next", "is_previous"):
        event = next((e for e in events if e.get(flag)), None)
        if event:
            return to_int(event.get("id"), 1)
    return 1


def position_short(player, element_type_map):
    element_type = player.get("element_type")
    meta = element_type_map.get(element_type, {})
    return meta.get("singular_name_short") or meta.get("singular_name") or "UNK"


def full_name(player):
    first = player.get("first_name") or ""
    second = player.get("second_name") or ""
    name = f"{first} {second}".strip()
    return name or player.get("web_name") or f"Player {player.get('id')}"


def display_name(player, team_map, element_type_map):
    team = team_map.get(player.get("team"), {})
    pos = position_short(player, element_type_map)
    return f"{player.get('web_name') or full_name(player)} - {team.get('short_name', 'UNK')} - {pos}"


def normalize_player_id(player_id, player_by_id):
    if player_id in (None, 0, "0", "None"):
        return 0
    normalized = to_int(player_id, 0)
    return normalized if normalized in player_by_id else 0


def player_option_label(player_id, player_by_id, team_map, element_type_map, none_label=None):
    normalized = normalize_player_id(player_id, player_by_id)
    if normalized == 0:
        return none_label or str(player_id)
    return display_name(player_by_id[normalized], team_map, element_type_map)


def photo_url(player):
    photo = player.get("photo")
    if not photo:
        return ""
    filename = photo.replace(".jpg", ".png")
    return f"https://resources.premierleague.com/premierleague/photos/players/110x140/p{filename}"


def badge_url(team):
    code = team.get("code")
    if not code:
        return ""
    return f"https://resources.premierleague.com/premierleague/badges/70/t{code}.png"


def cost(player):
    return to_float(player.get("now_cost")) / 10


def xgi(player):
    return to_float(player.get("expected_goal_involvements"))


def points_per_90(player):
    minutes = to_float(player.get("minutes"))
    if minutes <= 0:
        return 0.0
    return to_float(player.get("total_points")) / minutes * 90


def starts_per_90(player):
    minutes = to_float(player.get("minutes"))
    if minutes <= 0:
        return 0.0
    return to_float(player.get("starts")) / minutes * 90


def value_score(player):
    player_cost = cost(player)
    if player_cost <= 0:
        return 0.0
    return to_float(player.get("total_points")) / player_cost


def status_label(player):
    labels = {
        "a": "Available",
        "d": "Doubtful",
        "i": "Injured",
        "n": "Unavailable",
        "s": "Suspended",
        "u": "Unavailable",
    }
    base = labels.get(player.get("status"), "Unknown")
    chance = player.get("chance_of_playing_next_round")
    if chance is not None and player.get("status") != "a":
        return f"{base} ({chance}%)"
    return base


def latest_history_entry(history):
    if not history:
        return None
    return max(
        history,
        key=lambda row: (
            to_int(row.get("round")),
            parse_dt(row.get("kickoff_time")) or datetime.min.replace(tzinfo=timezone.utc),
        ),
    )


def latest_match_label(entry, team_map):
    if not entry:
        return "No current-season match history yet."

    opponent = team_map.get(entry.get("opponent_team"), {})
    side = "H" if entry.get("was_home") else "A"
    xgi_value = to_float(entry.get("expected_goal_involvements"))
    return (
        f"Latest: GW{to_int(entry.get('round'))} vs {opponent.get('short_name', 'UNK')} "
        f"({side}) - {to_int(entry.get('total_points'))} pts, "
        f"{to_int(entry.get('minutes'))} min, xGI {xgi_value:.2f}"
    )


def recent_history(history, count=5):
    return sorted(
        history,
        key=lambda row: (
            to_int(row.get("round")),
            parse_dt(row.get("kickoff_time")) or datetime.min.replace(tzinfo=timezone.utc),
        ),
    )[-count:]


def rolling_xgi(history, count=5):
    return sum(to_float(row.get("expected_goal_involvements")) for row in recent_history(history, count))


def percentile_rank(players, value_getter, value):
    values = sorted(value_getter(player) for player in players)
    values = [v for v in values if v is not None]
    if not values:
        return 0
    below = sum(1 for v in values if v <= value)
    return round(below / len(values) * 100)


def pct_width(value):
    return max(4, min(100, to_float(value)))


def next_fixtures_for_team(team_id, fixtures, team_map, count=5):
    future = []
    for fixture in fixtures:
        if fixture.get("finished"):
            continue
        if team_id not in (fixture.get("team_h"), fixture.get("team_a")):
            continue

        is_home = fixture.get("team_h") == team_id
        opponent_id = fixture.get("team_a") if is_home else fixture.get("team_h")
        opponent = team_map.get(opponent_id, {})
        difficulty = fixture.get("team_h_difficulty" if is_home else "team_a_difficulty")
        future.append(
            {
                "event": to_int(fixture.get("event")),
                "kickoff": parse_dt(fixture.get("kickoff_time")),
                "opponent": opponent.get("short_name", "UNK"),
                "venue": "H" if is_home else "A",
                "difficulty": to_int(difficulty, 3),
            }
        )

    future.sort(key=lambda fx: (fx["event"], fx["kickoff"] or datetime.max.replace(tzinfo=timezone.utc)))
    return future[:count]


def fixture_pills(fixtures):
    if not fixtures:
        return "<span class='empty-inline'>No upcoming fixtures</span>"

    pills = []
    for fixture in fixtures:
        pills.append(
            f"""
            <span class="fixture-pill fdr-{fixture['difficulty']}">
                GW{fixture['event']} {esc(fixture['opponent'])} ({fixture['venue']})
            </span>
            """
        )
    return "".join(pills)


def metric_card(label, value, note=""):
    return f"""
    <div class="metric-card">
        <div class="metric-label">{esc(label)}</div>
        <div class="metric-value">{esc(value)}</div>
        <div class="metric-note">{esc(note)}</div>
    </div>
    """


def player_card(player, team_map, element_type_map):
    team = team_map.get(player.get("team"), {})
    return f"""
    <div class="mini-player-card">
        <div class="mini-player-head">
            <img class="mini-player-photo" src="{esc(photo_url(player))}" alt="{esc(full_name(player))}">
            <div class="mini-player-text">
                <div class="mini-player-name">{esc(player.get("web_name") or full_name(player))}</div>
                <div class="mini-player-meta">
                    {esc(team.get("short_name", "UNK"))} - {esc(position_short(player, element_type_map))} - £{cost(player):.1f}
                </div>
            </div>
        </div>
        <div class="mini-stat-row">
            <span>{to_int(player.get("total_points"))} pts</span>
            <span>{to_float(player.get("form")):.1f} form</span>
            <span>{to_float(player.get("selected_by_percent")):.1f}% own</span>
        </div>
    </div>
    """


def recent_strip_html(history):
    rows = recent_history(history)
    if not rows:
        return "<div class='empty-note'>No recent gameweek data available.</div>"

    cells = []
    max_points = max([to_int(row.get("total_points")) for row in rows] + [1])
    for row in rows:
        points = to_int(row.get("total_points"))
        minutes = to_int(row.get("minutes"))
        xgi_value = to_float(row.get("expected_goal_involvements"))
        points_width = pct_width(points / max_points * 100)
        minutes_width = pct_width(minutes / 90 * 100)
        cells.append(
            f"""
            <div class="trend-cell">
                <div class="trend-gw">GW{to_int(row.get("round"))}</div>
                <div class="trend-points">{points} pts</div>
                <div class="bar-track"><div class="bar-fill" style="width:{points_width}%"></div></div>
                <div class="bar-track muted"><div class="bar-fill cyan" style="width:{minutes_width}%"></div></div>
                <div class="trend-meta">{minutes} min - xGI {xgi_value:.2f}</div>
            </div>
            """
        )

    return f"<div class='trend-grid'>{''.join(cells)}</div>"


def render_radar(player, peers, history):
    metrics = [
        ("Form", to_float(player.get("form")), lambda p: to_float(p.get("form"))),
        ("Pts/90", points_per_90(player), points_per_90),
        ("xGI/90", to_float(player.get("expected_goal_involvements_per_90")), lambda p: to_float(p.get("expected_goal_involvements_per_90"))),
        ("Minutes", to_float(player.get("minutes")), lambda p: to_float(p.get("minutes"))),
        ("Threat", to_float(player.get("threat")), lambda p: to_float(p.get("threat"))),
        ("Last 5 xGI", rolling_xgi(history), lambda p: xgi(p)),
    ]

    rows = []
    for label, value, getter in metrics:
        rank = percentile_rank(peers, getter, value)
        rows.append(
            f"""
            <div class="radar-row">
                <div class="radar-label">{esc(label)}</div>
                <div class="radar-track">
                    <div class="radar-fill" style="width:{pct_width(rank)}%"></div>
                </div>
                <div class="radar-value">{rank}</div>
            </div>
            """
        )

    st.markdown(
        f"""
        <div class="glass-panel">
            <div class="kicker">PLAYER RADAR</div>
            <div class="panel-title">Position percentile snapshot</div>
            <div class="radar-wrap">{''.join(rows)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def comparison_rows(players):
    return [
        ("Total points", lambda p: to_float(p.get("total_points")), "{:.0f}"),
        ("Form", lambda p: to_float(p.get("form")), "{:.1f}"),
        ("Minutes", lambda p: to_float(p.get("minutes")), "{:.0f}"),
        ("Starts", lambda p: to_float(p.get("starts")), "{:.0f}"),
        ("Pts/90", points_per_90, "{:.2f}"),
        ("xG", lambda p: to_float(p.get("expected_goals")), "{:.2f}"),
        ("xA", lambda p: to_float(p.get("expected_assists")), "{:.2f}"),
        ("xGI", xgi, "{:.2f}"),
        ("xGI/90", lambda p: to_float(p.get("expected_goal_involvements_per_90")), "{:.2f}"),
        ("Threat", lambda p: to_float(p.get("threat")), "{:.1f}"),
        ("Creativity", lambda p: to_float(p.get("creativity")), "{:.1f}"),
        ("ICT index", lambda p: to_float(p.get("ict_index")), "{:.1f}"),
        ("Ownership", lambda p: to_float(p.get("selected_by_percent")), "{:.1f}%"),
        ("Value", value_score, "{:.1f}"),
    ]


def render_comparison_table(players):
    if not players:
        st.info("Select at least one player to compare.")
        return

    grid_style = f"grid-template-columns: minmax(120px, 0.8fr) repeat({len(players)}, minmax(0, 1fr));"
    header_cells = ["<div class='comp-head muted-head'>Metric</div>"]
    for player in players:
        header_cells.append(f"<div class='comp-head'>{esc(player.get('web_name') or full_name(player))}</div>")

    rows_html = [f"<div class='comparison-grid' style='{grid_style}'>{''.join(header_cells)}</div>"]
    for label, getter, formatter in comparison_rows(players):
        values = [getter(player) for player in players]
        max_value = max(values) if values else 0
        row_cells = [f"<div class='comp-label'>{esc(label)}</div>"]
        for value in values:
            width = pct_width(value / max_value * 100) if max_value > 0 else 4
            row_cells.append(
                f"""
                <div class="comp-cell">
                    <span>{esc(formatter.format(value))}</span>
                    <div class="comp-track"><div class="comp-fill" style="width:{width}%"></div></div>
                </div>
                """
            )
        rows_html.append(f"<div class='comparison-grid' style='{grid_style}'>{''.join(row_cells)}</div>")

    st.markdown(f"<div class='comparison-table'>{''.join(rows_html)}</div>", unsafe_allow_html=True)


def render_value_table(players, team_map, element_type_map):
    if not players:
        st.markdown("<div class='empty-note'>No players match those filters.</div>", unsafe_allow_html=True)
        return

    rows = []
    for player in players[:8]:
        team = team_map.get(player.get("team"), {})
        rows.append(
            f"""
            <tr>
                <td>{esc(player.get("web_name") or full_name(player))}</td>
                <td>{esc(team.get("short_name", "UNK"))}</td>
                <td>{esc(position_short(player, element_type_map))}</td>
                <td>£{cost(player):.1f}</td>
                <td>{to_int(player.get("total_points"))}</td>
                <td>{to_float(player.get("form")):.1f}</td>
                <td>{value_score(player):.1f}</td>
            </tr>
            """
        )

    st.markdown(
        f"""
        <table class="small-table">
            <thead>
                <tr>
                    <th>Player</th>
                    <th>Team</th>
                    <th>Pos</th>
                    <th>Price</th>
                    <th>Pts</th>
                    <th>Form</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>{''.join(rows)}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def model_row(player, team_map, element_type_map, fixtures, current_event):
    team = team_map.get(player.get("team"), {})
    future = next_fixtures_for_team(player.get("team"), fixtures, team_map, count=5)
    minutes_denominator = max(1, to_int(current_event, 1)) * 90
    minutes_share = min(100, to_float(player.get("minutes")) / minutes_denominator * 100)
    return f"""
    <tr>
        <td>{esc(player.get("web_name") or full_name(player))}</td>
        <td>{esc(team.get("short_name", "UNK"))}</td>
        <td>{esc(position_short(player, element_type_map))}</td>
        <td>{to_float(player.get("form")):.1f}</td>
        <td>{to_float(player.get("expected_goal_involvements_per_90")):.2f}</td>
        <td>{points_per_90(player):.2f}</td>
        <td>{minutes_share:.0f}%</td>
        <td>{to_float(player.get("selected_by_percent")):.1f}%</td>
        <td><div class="fixture-strip">{fixture_pills(future[:3])}</div></td>
    </tr>
    """


st.markdown(
    """
<style>
.stApp {
    background: linear-gradient(135deg, #37003c, #2b1e5b, #00cc6a) !important;
    min-height: 100vh;
}
.stMainBlockContainer {
    max-width: none !important;
    padding-top: 2rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

h1, h2, h3, p, div, span, li, label {
    color: white;
}

div[data-testid="stSelectbox"] label,
div[data-testid="stSlider"] label,
div[data-testid="stRadio"] label {
    color: rgba(255,255,255,0.86) !important;
    font-size: 12px !important;
    font-weight: 800 !important;
}

div[data-baseweb="select"] > div,
div[role="radiogroup"] label {
    background: rgba(255,255,255,0.12) !important;
    border-color: rgba(255,255,255,0.25) !important;
    color: white !important;
}

.glass-panel {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 14px 34px rgba(0,0,0,0.28);
    color: white;
    min-height: 100%;
}

.panel-title {
    font-size: 16px;
    font-weight: 800;
    margin-bottom: 8px;
}

.panel-sub {
    font-size: 13px;
    color: rgba(255,255,255,0.78);
}

.kicker {
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-size: 11px;
    font-weight: 700;
    color: rgba(255,255,255,0.7);
}

.profile-panel {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 18px;
    padding: 20px;
    box-shadow: 0 14px 34px rgba(0,0,0,0.28);
}

.profile-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.9fr);
    gap: 16px;
    align-items: stretch;
}

.profile-main {
    display: flex;
    gap: 16px;
    align-items: center;
    min-width: 0;
}

.player-photo-wrap {
    width: 116px;
    height: 136px;
    border-radius: 14px;
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.16);
    display: flex;
    align-items: flex-end;
    justify-content: center;
    overflow: hidden;
    flex-shrink: 0;
}

.player-photo {
    width: 105px;
    height: 134px;
    object-fit: contain;
}

.team-badge {
    width: 42px;
    height: 42px;
    object-fit: contain;
    margin-bottom: 8px;
}

.profile-name {
    font-size: clamp(26px, 3vw, 44px);
    line-height: 1.02;
    font-weight: 950;
    margin-top: 4px;
    word-break: break-word;
}

.profile-meta {
    margin-top: 8px;
    font-size: 13px;
    color: rgba(255,255,255,0.78);
    font-weight: 700;
}

.profile-news {
    margin-top: 10px;
    font-size: 13px;
    color: rgba(255,255,255,0.78);
}

.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    margin-top: 16px;
}

.metric-card {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 12px;
    padding: 10px;
    min-height: 82px;
}

.metric-label {
    font-size: 11px;
    color: rgba(255,255,255,0.72);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.metric-value {
    font-size: 24px;
    font-weight: 900;
    margin-top: 4px;
    color: #00ff87;
}

.metric-note {
    font-size: 11px;
    color: rgba(255,255,255,0.70);
    margin-top: 3px;
}

.trend-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 8px;
    margin-top: 12px;
}

.trend-cell {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.13);
    border-radius: 12px;
    padding: 9px;
    min-width: 0;
}

.trend-gw,
.trend-meta {
    font-size: 10.5px;
    color: rgba(255,255,255,0.68);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.trend-points {
    font-size: 18px;
    font-weight: 900;
    margin: 3px 0 5px 0;
    color: #00ff87;
}

.bar-track,
.radar-track,
.comp-track {
    height: 7px;
    border-radius: 999px;
    background: rgba(255,255,255,0.12);
    overflow: hidden;
    margin-top: 5px;
}

.bar-track.muted {
    height: 5px;
}

.bar-fill,
.radar-fill,
.comp-fill {
    height: 100%;
    border-radius: 999px;
    background: #00ff87;
}

.bar-fill.cyan,
.comp-fill {
    background: #05f0ff;
}

.radar-wrap {
    display: grid;
    gap: 10px;
    margin-top: 10px;
}

.radar-row {
    display: grid;
    grid-template-columns: 84px minmax(0, 1fr) 32px;
    gap: 10px;
    align-items: center;
}

.radar-label,
.radar-value {
    font-size: 12px;
    font-weight: 800;
    color: rgba(255,255,255,0.80);
}

.radar-value {
    text-align: right;
    color: #00ff87;
}

.mini-player-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    margin: 12px 0 14px 0;
}

.mini-player-card {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 12px;
    padding: 10px;
    min-width: 0;
}

.mini-player-head {
    display: flex;
    gap: 10px;
    align-items: center;
    min-width: 0;
}

.mini-player-photo {
    width: 44px;
    height: 54px;
    object-fit: contain;
    flex-shrink: 0;
}

.mini-player-text {
    min-width: 0;
}

.mini-player-name {
    font-size: 15px;
    font-weight: 900;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.mini-player-meta,
.mini-stat-row {
    font-size: 11px;
    color: rgba(255,255,255,0.70);
}

.mini-stat-row {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    margin-top: 8px;
}

.comparison-table {
    display: grid;
    gap: 7px;
    margin-top: 12px;
}

.comparison-grid {
    display: grid;
    gap: 7px;
    align-items: stretch;
}

.comp-head,
.comp-label,
.comp-cell {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.13);
    border-radius: 11px;
    padding: 9px 10px;
    min-width: 0;
}

.comp-head {
    font-size: 12px;
    font-weight: 900;
    color: #00ff87;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.muted-head {
    color: rgba(255,255,255,0.72);
    text-align: left;
}

.comp-label {
    font-size: 12px;
    font-weight: 800;
    color: rgba(255,255,255,0.74);
}

.comp-cell span {
    display: block;
    font-size: 13px;
    font-weight: 900;
}

.small-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 12px;
}

.small-table th,
.small-table td {
    padding: 8px 6px;
    border-bottom: 1px solid rgba(255,255,255,0.12);
    font-size: 12px;
    vertical-align: middle;
}

.small-table th {
    text-align: left;
    color: rgba(255,255,255,0.70);
    font-weight: 800;
}

.small-table td:first-child {
    font-weight: 800;
}

.small-table td:nth-child(n+4),
.small-table th:nth-child(n+4) {
    text-align: right;
}

.fixture-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    justify-content: flex-start;
}

.fixture-pill {
    display: inline-flex;
    border-radius: 999px;
    padding: 4px 7px;
    font-size: 10.5px;
    font-weight: 900;
    color: #101014;
    background: rgba(255,255,255,0.75);
}

.fdr-1,
.fdr-2 {
    background: #00ff87;
}

.fdr-3 {
    background: #ffb500;
}

.fdr-4,
.fdr-5 {
    background: #ff4f6d;
    color: white;
}

.empty-note,
.empty-inline {
    font-size: 12px;
    color: rgba(255,255,255,0.70);
}

@media (max-width: 1000px) {
    .profile-grid {
        grid-template-columns: 1fr;
    }

    .metric-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }

    .mini-player-grid,
    .trend-grid {
        grid-template-columns: 1fr;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

render_top_nav()

bootstrap_data = fetch_bootstrap_data()
fixtures = fetch_fixtures_data()
teams = bootstrap_data.get("teams", [])
elements = bootstrap_data.get("elements", [])
element_types = bootstrap_data.get("element_types", [])

if not teams or not elements:
    st.error("No player data was found in the FPL bootstrap data.")
    st.stop()

team_map = {team.get("id"): team for team in teams}
element_type_map = {element_type.get("id"): element_type for element_type in element_types}
current_event = st.session_state.get("gw") or current_event_from_events(bootstrap_data.get("events", []))
players = sorted(
    [player for player in elements if not player.get("removed")],
    key=lambda p: (p.get("web_name") or full_name(p)).lower(),
)
player_by_id = {player.get("id"): player for player in players}
player_ids = [player.get("id") for player in players if player.get("id") is not None]

default_profile = max(players, key=lambda p: to_float(p.get("total_points")))

st.title("Players")

selected_profile_id = st.selectbox(
    "Latest player profile",
    player_ids,
    index=player_ids.index(default_profile.get("id")),
    format_func=lambda player_id: player_option_label(player_id, player_by_id, team_map, element_type_map),
)
profile_id = normalize_player_id(selected_profile_id, player_by_id) or default_profile.get("id")
profile = player_by_id[profile_id]
profile_team = team_map.get(profile.get("team"), {})
summary = fetch_player_summary(profile_id)
history = summary.get("history", []) or []
latest_entry = latest_history_entry(history)
recent_xgi = rolling_xgi(history)
news = profile.get("news") or latest_match_label(latest_entry, team_map)

profile_metrics = [
    metric_card("Form", f"{to_float(profile.get('form')):.1f}", "FPL rolling form"),
    metric_card("Total Points", f"{to_int(profile.get('total_points'))}", "Season"),
    metric_card("Pts/90", f"{points_per_90(profile):.2f}", "Minutes adjusted"),
    metric_card("xGI", f"{xgi(profile):.2f}", "Season total"),
    metric_card("Last 5 xGI", f"{recent_xgi:.2f}", "Recent trend"),
    metric_card("Minutes", f"{to_int(profile.get('minutes'))}", f"{to_int(profile.get('starts'))} starts"),
    metric_card("Ownership", f"{to_float(profile.get('selected_by_percent')):.1f}%", "Selected by"),
    metric_card("Value", f"{value_score(profile):.1f}", "Pts per £m"),
]

st.markdown(
    f"""
    <div class="profile-panel">
        <div class="profile-grid">
            <div>
                <div class="profile-main">
                    <div class="player-photo-wrap">
                        <img class="player-photo" src="{esc(photo_url(profile))}" alt="{esc(full_name(profile))}">
                    </div>
                    <div>
                        <img class="team-badge" src="{esc(badge_url(profile_team))}" alt="{esc(profile_team.get('name', ''))}">
                        <div class="kicker">LATEST PLAYER PROFILE</div>
                        <div class="profile-name">{esc(full_name(profile))}</div>
                        <div class="profile-meta">
                            {esc(profile_team.get('name', 'Unknown'))} - {esc(position_short(profile, element_type_map))}
                            - £{cost(profile):.1f} - {esc(status_label(profile))}
                        </div>
                        <div class="profile-news">{esc(news)}</div>
                    </div>
                </div>
                <div class="metric-grid">{''.join(profile_metrics)}</div>
            </div>
            <div>
                <div class="kicker">RECENT MINUTES & OUTPUT</div>
                <div class="panel-title">Last five gameweeks</div>
                {recent_strip_html(history)}
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(" ")

top_row_left, top_row_right = st.columns([1.1, 0.9], gap="large")

with top_row_left:
    peers = [
        player
        for player in players
        if player.get("element_type") == profile.get("element_type")
        and to_float(player.get("minutes")) >= 450
    ]
    render_radar(profile, peers or players, history)

with top_row_right:
    st.markdown(
        """
        <div class="glass-panel">
            <div class="kicker">VALUE PICKS</div>
            <div class="panel-title">Price-to-output comparison</div>
            <div class="panel-sub">Sorted by season points per £m, with minutes and price filters.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    position_options = ["All"] + [
        element_type.get("singular_name_short") or element_type.get("singular_name")
        for element_type in sorted(element_types, key=lambda e: to_int(e.get("id")))
    ]
    position_filter = st.radio("Position", position_options, horizontal=True)
    max_price = st.slider("Max price", min_value=3.5, max_value=15.0, value=15.0, step=0.1)
    max_minutes = max(3420, max(to_int(player.get("minutes")) for player in players))
    min_minutes = st.slider("Minimum minutes", min_value=0, max_value=max_minutes, value=450, step=90)

    value_players = [
        player
        for player in players
        if cost(player) <= max_price
        and to_float(player.get("minutes")) >= min_minutes
        and (
            position_filter == "All"
            or position_short(player, element_type_map) == position_filter
        )
    ]
    value_players.sort(key=value_score, reverse=True)
    render_value_table(value_players, team_map, element_type_map)

st.markdown(" ")

st.markdown(
    """
    <div class="glass-panel">
        <div class="kicker">PLAYER COMPARISON</div>
        <div class="panel-title">Head-to-head stat cards</div>
        <div class="panel-sub">Choose up to three players for xG, xA, threat, ownership, and minutes-adjusted output.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

top_comparison_pool = sorted(players, key=lambda p: to_float(p.get("total_points")), reverse=True)
comparison_defaults = [profile_id]
for player in top_comparison_pool:
    player_id = player.get("id")
    if player_id not in comparison_defaults:
        comparison_defaults.append(player_id)
    if len(comparison_defaults) == 3:
        break

selector_cols = st.columns(3, gap="large")
select_options = [0] + player_ids
selected_comparison_ids = []
raw_comparison_ids = []
for idx, col in enumerate(selector_cols):
    default_id = comparison_defaults[idx] if idx < len(comparison_defaults) else 0
    with col:
        selected_id = st.selectbox(
            f"Player {idx + 1}",
            select_options,
            index=select_options.index(default_id),
            format_func=lambda player_id: player_option_label(player_id, player_by_id, team_map, element_type_map, none_label="None"),
            key=f"comparison_player_{idx + 1}",
        )
    normalized_selected_id = normalize_player_id(selected_id, player_by_id)
    raw_comparison_ids.append(normalized_selected_id)
    if normalized_selected_id and normalized_selected_id not in selected_comparison_ids:
        selected_comparison_ids.append(normalized_selected_id)

comparison_players = [player_by_id[player_id] for player_id in selected_comparison_ids]
if len(selected_comparison_ids) < len([player_id for player_id in raw_comparison_ids if player_id]):
    st.warning("Duplicate comparison selections are shown once.")

st.markdown(
    f"<div class='mini-player-grid'>{''.join(player_card(player, team_map, element_type_map) for player in comparison_players)}</div>",
    unsafe_allow_html=True,
)
render_comparison_table(comparison_players)

st.markdown(" ")

model_players = []
for player in [profile] + comparison_players:
    if player.get("id") not in [p.get("id") for p in model_players]:
        model_players.append(player)

st.markdown(
    """
    <div class="glass-panel">
        <div class="kicker">MODEL INPUTS</div>
        <div class="panel-title">Feature set for ML scoring</div>
        <div class="panel-sub">Current features for next 3-5 gameweek scoring experiments.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <table class="small-table">
        <thead>
            <tr>
                <th>Player</th>
                <th>Team</th>
                <th>Pos</th>
                <th>Form</th>
                <th>xGI/90</th>
                <th>Pts/90</th>
                <th>Min Share</th>
                <th>Own</th>
                <th>Next</th>
            </tr>
        </thead>
        <tbody>{''.join(model_row(player, team_map, element_type_map, fixtures, current_event) for player in model_players)}</tbody>
    </table>
    """,
    unsafe_allow_html=True,
)
