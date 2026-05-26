import json
import ssl
import urllib.request
from datetime import datetime
from pathlib import Path

import certifi
import plotly.graph_objects as go
import streamlit as st  # type: ignore

try:
    from streamlit_plotly_events import plotly_events
except Exception:
    plotly_events = None

from nav import render_top_nav


st.set_page_config(page_title="FPL Graphs", layout="wide")

st.markdown(
    """
<style>
.stApp {
    background: linear-gradient(135deg, #37003c, #2b1e5b, #00cc6a) !important;
    min-height: 100vh;
}
.stMainBlockContainer {
    padding-top: 2rem !important;
    max-width: none !important;
    width: 100% !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

h1, h2, h3, p, span, li, label {
    color: white !important;
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
    color: white !important;
}
</style>
""",
    unsafe_allow_html=True,
)

render_top_nav()

ROOT_DIR = Path(__file__).resolve().parents[1]
LOCAL_BOOTSTRAP_PATH = ROOT_DIR / "data" / "raw" / "bootstrap_static.json"
LOCAL_FIXTURES_PATH = ROOT_DIR / "data" / "raw" / "fixtures.json"
BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
FIXTURES_URL = "https://fantasy.premierleague.com/api/fixtures/"
SUMMARY_URL = "https://fantasy.premierleague.com/api/element-summary/{element_id}/"


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


def safe_div(numerator, denominator):
    if not denominator:
        return 0.0
    return numerator / denominator


def parse_dt(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def fetch_json(url):
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, context=ctx, timeout=10) as response:
        return json.loads(response.read())


def load_local_json(path, fallback):
    if not path.exists():
        return fallback
    try:
        with path.open() as f:
            return json.load(f)
    except Exception:
        return fallback


@st.cache_data(ttl=900, show_spinner=False)
def fetch_bootstrap_static():
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


@st.cache_data(ttl=120, show_spinner=False)
def fetch_live_event(gw):
    try:
        return fetch_json(f"https://fantasy.premierleague.com/api/event/{gw}/live/")
    except Exception:
        return {"elements": []}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_entry_event_entry_history(entry_id, event_id):
    try:
        return fetch_json(
            f"https://fantasy.premierleague.com/api/entry/{entry_id}/event/{event_id}/picks/"
        ).get("entry_history", {})
    except Exception:
        return {}


@st.cache_data(ttl=900, show_spinner=False)
def fetch_player_summary(element_id):
    try:
        return fetch_json(SUMMARY_URL.format(element_id=element_id))
    except Exception:
        return {"fixtures": [], "history": [], "history_past": []}


def current_gw_from_events(events):
    current = next((e.get("id") for e in events if e.get("is_current")), None)
    if current:
        return current
    return max((e.get("id") or 1 for e in events), default=1)


def build_maps(bootstrap):
    positions = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
    teams = {}
    for team in bootstrap.get("teams", []):
        teams[team.get("id")] = {
            "id": team.get("id"),
            "name": team.get("name", "Unknown"),
            "short": team.get("short_name", "UNK"),
            "form": to_float(team.get("form")),
            "points": to_int(team.get("points")),
            "strength_attack_home": to_int(team.get("strength_attack_home")),
            "strength_attack_away": to_int(team.get("strength_attack_away")),
            "strength_defence_home": to_int(team.get("strength_defence_home")),
            "strength_defence_away": to_int(team.get("strength_defence_away")),
            "strength_overall_home": to_int(team.get("strength_overall_home")),
            "strength_overall_away": to_int(team.get("strength_overall_away")),
        }

    players = []
    player_by_id = {}
    for player in bootstrap.get("elements", []):
        pid = player.get("id")
        team = teams.get(player.get("team"), {})
        price = to_float(player.get("now_cost")) / 10
        minutes = to_float(player.get("minutes"))
        total_points = to_float(player.get("total_points"))
        row = {
            "id": pid,
            "name": player.get("web_name")
            or f"{player.get('first_name', '')} {player.get('second_name', '')}".strip(),
            "team_id": team.get("id"),
            "team_short": team.get("short", "UNK"),
            "team_name": team.get("name", "Unknown"),
            "position_id": player.get("element_type"),
            "position": positions.get(player.get("element_type"), "UNK"),
            "price": price,
            "total_points": total_points,
            "minutes": minutes,
            "starts": to_float(player.get("starts")),
            "form": to_float(player.get("form")),
            "xg": to_float(player.get("expected_goals")),
            "xa": to_float(player.get("expected_assists")),
            "xgi": to_float(player.get("expected_goal_involvements")),
            "xgi_per_90": to_float(player.get("expected_goal_involvements_per_90")),
            "points_per_90": safe_div(total_points, minutes) * 90 if minutes else 0,
            "value": safe_div(total_points, price) if price else 0,
            "ict": to_float(player.get("ict_index")),
            "threat": to_float(player.get("threat")),
            "creativity": to_float(player.get("creativity")),
            "ownership": to_float(player.get("selected_by_percent")),
        }
        if pid is not None:
            players.append(row)
            player_by_id[pid] = row

    return players, player_by_id, teams, positions


def apply_plotly_layout(fig, height=380, title=None):
    title_spec = None
    if title:
        title_spec = dict(text=title, x=0.5, xanchor="center", y=0.98, yanchor="top")

    fig.update_layout(
        height=height,
        title=title_spec,
        margin=dict(l=70, r=24, t=74 if title else 18, b=56),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        legend=dict(orientation="h", yanchor="bottom", y=1.12, xanchor="right", x=1),
    )
    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.12)",
        automargin=True,
        ticklabelstandoff=10,
    )
    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.12)",
        automargin=True,
        ticklabelstandoff=10,
    )
    return fig


def render_plotly(fig, key, height=380):
    fig.update_layout(height=height)
    if plotly_events:
        return plotly_events(
            fig,
            click_event=True,
            select_event=False,
            hover_event=False,
            override_height=height,
            key=key,
        )
    st.plotly_chart(fig, use_container_width=True)
    return []


def update_selected_player(clicks):
    if not clicks:
        return
    custom = clicks[0].get("customdata")
    if isinstance(custom, list):
        candidate = custom[0] if custom else None
    else:
        candidate = custom
    if candidate is None:
        return
    try:
        st.session_state.selected_player_id = int(candidate)
    except (TypeError, ValueError):
        return


def update_selected_team(clicks):
    if not clicks:
        return
    custom = clicks[0].get("customdata")
    if isinstance(custom, list):
        candidate = custom[0] if custom else None
    else:
        candidate = custom
    if candidate is None:
        return
    try:
        st.session_state.team_filter = int(candidate)
    except (TypeError, ValueError):
        return


def build_fixture_difficulty_matrix(fixtures, team_ids, gw_start, gw_end):
    gws = list(range(gw_start, gw_end + 1))
    bucket = {team_id: {gw: [] for gw in gws} for team_id in team_ids}

    for fixture in fixtures:
        gw = fixture.get("event")
        if gw not in gws:
            continue
        team_h = fixture.get("team_h")
        team_a = fixture.get("team_a")
        if team_h in bucket:
            bucket[team_h][gw].append(to_int(fixture.get("team_h_difficulty"), 3))
        if team_a in bucket:
            bucket[team_a][gw].append(to_int(fixture.get("team_a_difficulty"), 3))

    matrix = []
    for team_id in team_ids:
        row = []
        for gw in gws:
            values = bucket[team_id][gw]
            row.append(round(sum(values) / len(values), 2) if values else None)
        matrix.append(row)
    return gws, matrix


is_guest = st.session_state.get("guest", False)
if "selected_player_id" not in st.session_state:
    st.session_state.selected_player_id = 0
if "team_filter" not in st.session_state:
    st.session_state.team_filter = 0
if "position_filter" not in st.session_state:
    st.session_state.position_filter = 0

bootstrap = fetch_bootstrap_static()
if not bootstrap:
    st.error("Could not load bootstrap data. Try again later.")
    st.stop()

players, player_by_id, teams, positions = build_maps(bootstrap)
fixtures = fetch_fixtures_data()

team_ids = [0] + sorted(teams.keys(), key=lambda tid: teams[tid]["name"])
position_ids = [0, 1, 2, 3, 4]

# Sidebar filters
st.sidebar.header("Filters")
if plotly_events is None:
    st.sidebar.info("Install streamlit-plotly-events to enable click drill-down.")

events = bootstrap.get("events", [])
max_gw = max((e.get("id") or 1 for e in events), default=1)
current_gw = current_gw_from_events(events)
if current_gw:
    max_gw = max(max_gw, current_gw)

gw_start_default = max(1, max_gw - 9)
if max_gw == 1:
    gw_range = (1, 1)
else:
    gw_range = st.sidebar.slider(
        "Gameweek range",
        min_value=1,
        max_value=max_gw,
        value=(gw_start_default, max_gw),
    )

gw_start, gw_end = gw_range

if st.session_state.team_filter not in team_ids:
    st.session_state.team_filter = 0
team_filter = st.sidebar.selectbox(
    "Team",
    team_ids,
    format_func=lambda tid: "All teams" if tid == 0 else teams[tid]["name"],
    key="team_filter",
)

position_filter = st.sidebar.selectbox(
    "Position",
    position_ids,
    format_func=lambda pid: "All positions" if pid == 0 else positions.get(pid, "UNK"),
    key="position_filter",
)

filtered_for_select = [
    p
    for p in players
    if (team_filter == 0 or p["team_id"] == team_filter)
    and (position_filter == 0 or p["position_id"] == position_filter)
]
player_options = [0] + [p["id"] for p in filtered_for_select]
if st.session_state.selected_player_id not in player_options:
    st.session_state.selected_player_id = 0

st.sidebar.selectbox(
    "Player",
    player_options,
    format_func=lambda pid: "All players" if pid == 0 else player_by_id[pid]["name"],
    key="selected_player_id",
)

fixture_window = st.sidebar.slider("Fixture window (GWs)", 3, 8, 5)

if st.sidebar.button("Clear selections"):
    st.session_state.selected_player_id = 0
    st.session_state.team_filter = 0
    st.session_state.position_filter = 0

filtered_players = [
    p
    for p in players
    if (team_filter == 0 or p["team_id"] == team_filter)
    and (position_filter == 0 or p["position_id"] == position_filter)
]

st.title("Graphs")

manager_tab, players_tab, teams_tab, live_tab = st.tabs(
    ["Manager", "Players", "Teams", "Live"]
)

with manager_tab:
    st.subheader("Manager performance")
    if is_guest or "manager_id" not in st.session_state:
        st.info("Connect a manager to see personal performance charts.")
    else:
        manager_id = st.session_state.manager_id
        avg_by_event = {
            e.get("id"): (e.get("average_entry_score") or 0)
            for e in events
            if e.get("id") is not None
        }

        gw_labels = list(range(gw_start, gw_end + 1))
        pts_series = []
        rank_series = []
        avg_series = []
        for event_id in gw_labels:
            history = fetch_entry_event_entry_history(manager_id, event_id)
            pts_series.append(to_int(history.get("points", history.get("total_points", 0))))
            rank_series.append(
                to_int(history.get("overall_rank", history.get("rank", 0)), 0)
            )
            avg_series.append(to_int(avg_by_event.get(event_id, 0), 0))

        if pts_series:
            last_points = pts_series[-1]
            last_avg = avg_series[-1]
            last_rank = rank_series[-1]
        else:
            last_points = 0
            last_avg = 0
            last_rank = 0

        m1, m2, m3 = st.columns(3)
        m1.metric("Latest GW points", last_points)
        m2.metric("Latest GW average", last_avg)
        m3.metric("Latest overall rank", f"{last_rank:,}")

        points_fig = go.Figure()
        points_fig.add_trace(
            go.Scatter(
                x=gw_labels,
                y=pts_series,
                mode="lines+markers",
                name="My points",
                line=dict(color="#00ff87", width=3),
            )
        )
        points_fig.add_trace(
            go.Scatter(
                x=gw_labels,
                y=avg_series,
                mode="lines",
                name="GW average",
                line=dict(color="#ffb500", width=2, dash="dash"),
            )
        )
        apply_plotly_layout(points_fig, title="Points vs GW average")
        render_plotly(points_fig, key="mgr_points", height=360)

        rank_fig = go.Figure()
        rank_fig.add_trace(
            go.Scatter(
                x=gw_labels,
                y=rank_series,
                mode="lines+markers",
                name="Overall rank",
                line=dict(color="#00ff87", width=3),
            )
        )
        rank_fig.update_yaxes(autorange="reversed")
        apply_plotly_layout(rank_fig, title="Overall rank trend")
        render_plotly(rank_fig, key="mgr_rank", height=360)

        delta_fig = go.Figure()
        delta_fig.add_trace(
            go.Bar(
                x=gw_labels,
                y=[p - a for p, a in zip(pts_series, avg_series)],
                marker_color="#05f0ff",
            )
        )
        apply_plotly_layout(delta_fig, title="Points delta vs average")
        render_plotly(delta_fig, key="mgr_delta", height=320)

        history = st.session_state.get("history", {}) or {}
        chips = history.get("chips", []) if isinstance(history, dict) else []
        if chips:
            chip_map = {
                "bboost": "Bench Boost",
                "freehit": "Free Hit",
                "3xc": "Triple Captain",
                "wildcard": "Wildcard",
            }
            chip_rows = [
                {"chip": chip_map.get(c.get("name"), c.get("name", "Chip")), "gw": c.get("event")}
                for c in chips
            ]
            chip_fig = go.Figure()
            chip_fig.add_trace(
                go.Scatter(
                    x=[c["gw"] for c in chip_rows],
                    y=[c["chip"] for c in chip_rows],
                    mode="markers+text",
                    text=[c["chip"] for c in chip_rows],
                    textposition="top center",
                    marker=dict(color="#ff4f6d", size=10),
                )
            )
            apply_plotly_layout(chip_fig, title="Chip usage timeline", height=260)
            render_plotly(chip_fig, key="mgr_chips", height=260)
        else:
            st.caption("No chip usage data available.")

with players_tab:
    st.subheader("Player value and performance")
    if not filtered_players:
        st.info("No players match the selected filters.")
    else:
        pos_colors = {"GKP": "#05f0ff", "DEF": "#00ff87", "MID": "#ffb500", "FWD": "#ff4f6d"}

        def scatter_by_position(x_key, y_key, title, x_label, y_label, chart_key):
            fig = go.Figure()
            for pos_name in ["GKP", "DEF", "MID", "FWD"]:
                group = [p for p in filtered_players if p["position"] == pos_name]
                if not group:
                    continue
                fig.add_trace(
                    go.Scatter(
                        x=[p[x_key] for p in group],
                        y=[p[y_key] for p in group],
                        mode="markers",
                        name=pos_name,
                        marker=dict(color=pos_colors.get(pos_name, "#00ff87"), size=9, opacity=0.8),
                        text=[p["name"] for p in group],
                        customdata=[p["id"] for p in group],
                    )
                )
            fig.update_xaxes(title=x_label)
            fig.update_yaxes(title=y_label)
            apply_plotly_layout(fig, title=title)
            clicks = render_plotly(fig, key=chart_key, height=360)
            update_selected_player(clicks)

        col1, col2 = st.columns(2)
        with col1:
            scatter_by_position(
                "price",
                "total_points",
                "Price vs total points",
                "Price",
                "Total points",
                "players_price_points",
            )
        with col2:
            scatter_by_position(
                "xgi",
                "total_points",
                "xGI vs total points",
                "xGI",
                "Total points",
                "players_xgi_points",
            )

        col3, col4 = st.columns(2)
        with col3:
            scatter_by_position(
                "price",
                "points_per_90",
                "Price vs points per 90",
                "Price",
                "Points per 90",
                "players_pp90",
            )
        with col4:
            top_value = sorted(filtered_players, key=lambda p: p["value"], reverse=True)[:10]
            fig = go.Figure(
                go.Bar(
                    x=[p["name"] for p in top_value],
                    y=[round(p["value"], 2) for p in top_value],
                    marker_color="#00ff87",
                )
            )
            fig.update_xaxes(title="Player")
            fig.update_yaxes(title="Points per 1.0 price")
            apply_plotly_layout(fig, title="Top value players")
            render_plotly(fig, key="players_value", height=360)

        selected_id = st.session_state.selected_player_id
        if selected_id and selected_id in player_by_id:
            row = player_by_id[selected_id]
            st.markdown(
                f"Selected player: {row['name']} ({row['team_short']} - {row['position']})"
            )
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total points", int(row["total_points"]))
            c2.metric("Price", f"{row['price']:.1f}")
            c3.metric("Form", f"{row['form']:.1f}")
            c4.metric("xGI", f"{row['xgi']:.2f}")

            summary = fetch_player_summary(selected_id)
            history = summary.get("history", [])
            if history:
                recent = sorted(history, key=lambda h: to_int(h.get("round")))[-6:]
                gws = [to_int(h.get("round")) for h in recent]
                points = [to_int(h.get("total_points")) for h in recent]
                xgi = [to_float(h.get("expected_goal_involvements")) for h in recent]
                trend = go.Figure()
                trend.add_trace(
                    go.Bar(x=gws, y=points, name="Points", marker_color="#00ff87")
                )
                trend.add_trace(
                    go.Scatter(
                        x=gws,
                        y=xgi,
                        name="xGI",
                        mode="lines+markers",
                        line=dict(color="#ffb500", width=2),
                    )
                )
                trend.update_xaxes(title="GW")
                trend.update_yaxes(title="Points / xGI")
                apply_plotly_layout(trend, title="Recent points vs xGI", height=300)
                st.plotly_chart(trend, use_container_width=True)
        else:
            st.caption("Click a player in a chart to see details.")

with teams_tab:
    st.subheader("Team strength and fixtures")
    team_rows = [teams[tid] for tid in teams]
    team_rows.sort(key=lambda t: t["name"])

    scatter = go.Figure()
    for team in team_rows:
        attack_avg = safe_div(
            team["strength_attack_home"] + team["strength_attack_away"], 2
        )
        defence_avg = safe_div(
            team["strength_defence_home"] + team["strength_defence_away"], 2
        )
        scatter.add_trace(
            go.Scatter(
                x=[attack_avg],
                y=[defence_avg],
                mode="markers+text",
                text=[team["short"]],
                textposition="top center",
                marker=dict(color="#05f0ff", size=10),
                customdata=[team["id"]],
                name=team["name"],
                showlegend=False,
            )
        )
    scatter.update_xaxes(title="Attack strength (avg)")
    scatter.update_yaxes(title="Defence strength (avg)")
    apply_plotly_layout(scatter, title="Attack vs defence strength")
    clicks = render_plotly(scatter, key="teams_scatter", height=360)
    update_selected_team(clicks)

    selected_team_id = st.session_state.team_filter
    if selected_team_id and selected_team_id in teams:
        team = teams[selected_team_id]
        st.markdown(f"Selected team: {team['name']}")
        t1, t2, t3 = st.columns(3)
        t1.metric("Form", f"{team['form']:.1f}")
        t2.metric("Points", team["points"])
        t3.metric(
            "Overall strength",
            safe_div(team["strength_overall_home"] + team["strength_overall_away"], 2),
        )

        strength_fig = go.Figure()
        strength_fig.add_trace(
            go.Bar(
                x=["Attack home", "Attack away"],
                y=[team["strength_attack_home"], team["strength_attack_away"]],
                marker_color="#00ff87",
                name="Attack",
            )
        )
        strength_fig.add_trace(
            go.Bar(
                x=["Defence home", "Defence away"],
                y=[team["strength_defence_home"], team["strength_defence_away"]],
                marker_color="#ffb500",
                name="Defence",
            )
        )
        strength_fig.update_yaxes(title="Strength")
        apply_plotly_layout(strength_fig, title="Home vs away strength", height=300)
        st.plotly_chart(strength_fig, use_container_width=True)
    else:
        st.caption("Click a team in the scatter to see details.")

    if current_gw:
        heatmap_start = current_gw
        heatmap_end = min(max_gw, current_gw + fixture_window - 1)
    else:
        heatmap_start = gw_start
        heatmap_end = gw_end

    ordered_team_ids = [t["id"] for t in team_rows]
    if selected_team_id in ordered_team_ids:
        ordered_team_ids = [selected_team_id] + [
            tid for tid in ordered_team_ids if tid != selected_team_id
        ]

    gws, matrix = build_fixture_difficulty_matrix(
        fixtures, ordered_team_ids, heatmap_start, heatmap_end
    )
    heatmap = go.Figure(
        data=go.Heatmap(
            z=matrix,
            x=[f"GW{gw}" for gw in gws],
            y=[teams[tid]["short"] for tid in ordered_team_ids],
            zmin=1,
            zmax=5,
            colorscale=[
                [0.0, "#00ff87"],
                [0.5, "#ffb500"],
                [1.0, "#ff4f6d"],
            ],
            colorbar=dict(title="FDR"),
        )
    )
    apply_plotly_layout(heatmap, title="Upcoming fixture difficulty", height=420)
    st.plotly_chart(heatmap, use_container_width=True)

with live_tab:
    st.subheader("Live gameweek")
    if not current_gw:
        st.info("No current gameweek found.")
    else:
        live_data = fetch_live_event(current_gw)
        live_rows = []
        for element in live_data.get("elements", []):
            pid = element.get("id")
            stats = element.get("stats", {})
            points = to_int(stats.get("total_points"), 0)
            player = player_by_id.get(pid)
            if not player:
                continue
            live_rows.append(
                {
                    "id": pid,
                    "name": player["name"],
                    "position": player["position"],
                    "team_short": player["team_short"],
                    "points": points,
                }
            )

        live_rows.sort(key=lambda r: r["points"], reverse=True)
        top_rows = live_rows[:15]
        top_fig = go.Figure(
            go.Bar(
                x=[r["name"] for r in top_rows],
                y=[r["points"] for r in top_rows],
                marker_color="#00ff87",
            )
        )
        top_fig.update_xaxes(title="Player")
        top_fig.update_yaxes(title="Live points")
        apply_plotly_layout(top_fig, title=f"Top live scorers (GW{current_gw})", height=360)
        st.plotly_chart(top_fig, use_container_width=True)

        pos_totals = {"GKP": 0, "DEF": 0, "MID": 0, "FWD": 0}
        pos_counts = {"GKP": 0, "DEF": 0, "MID": 0, "FWD": 0}
        for row in live_rows:
            pos = row["position"]
            pos_totals[pos] += row["points"]
            pos_counts[pos] += 1

        pos_avg = [
            safe_div(pos_totals[pos], pos_counts[pos]) for pos in ["GKP", "DEF", "MID", "FWD"]
        ]
        pos_fig = go.Figure(
            go.Bar(
                x=["GKP", "DEF", "MID", "FWD"],
                y=pos_avg,
                marker_color="#05f0ff",
            )
        )
        pos_fig.update_yaxes(title="Average live points")
        apply_plotly_layout(pos_fig, title="Average live points by position", height=320)
        st.plotly_chart(pos_fig, use_container_width=True)

st.markdown(" ")
if st.button("Back", use_container_width=True):
    st.switch_page("pages/home.py")