import streamlit as st  # type: ignore
import json
import urllib.request
import ssl
import certifi
import html
from datetime import datetime


st.set_page_config(page_title="FPL Mini Leagues", layout="wide")

if "manager_id" not in st.session_state:
	st.warning("No manager ID found. Go back to Dashboard and connect your team.")
	if st.button("Go to Dashboard"):
		st.switch_page("live_dashboard.py")
	st.stop()

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

h1, h2, h3, h4, p, div, span, li {
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

div[data-testid="stMetric"] {
	background: rgba(255,255,255,0.10);
	border: 1px solid rgba(255,255,255,0.18);
	border-radius: 12px;
	padding: 10px 12px;
}

div[data-testid="stExpander"] {
	border-radius: 14px !important;
	border: 1px solid rgba(255,255,255,0.18) !important;
	background: rgba(255,255,255,0.10) !important;
	backdrop-filter: blur(14px) !important;
	-webkit-backdrop-filter: blur(14px) !important;
	margin-bottom: 12px;
	overflow: hidden;
}

div[data-testid="stExpander"] details summary p {
	font-size: 16px !important;
	font-weight: 700 !important;
}

div[data-testid="stExpander"] details,
div[data-testid="stExpander"] details summary,
div[data-testid="stExpander"] details[open] summary {
	background: rgba(255,255,255,0.10) !important;
	color: white !important;
}

div[data-testid="stExpander"] details[open] summary {
	border-bottom: 1px solid rgba(255,255,255,0.16) !important;
}

div[data-testid="stExpander"] details > div {
	background: transparent !important;
}

div[data-testid="stDataFrame"] {
	background: rgba(255,255,255,0.10) !important;
	border: 1px solid rgba(255,255,255,0.22) !important;
	border-radius: 14px;
	backdrop-filter: blur(16px) !important;
	-webkit-backdrop-filter: blur(16px) !important;
	overflow: hidden;
	box-shadow: 0 10px 28px rgba(0,0,0,0.20);
}

div[data-testid="stDataFrame"] > div {
	background: transparent !important;
}

div[data-testid="stDataFrame"] [role="columnheader"] {
	background: rgba(255,255,255,0.14) !important;
	color: white !important;
	font-weight: 700 !important;
}

div[data-testid="stDataFrame"] [role="gridcell"] {
	background: rgba(255,255,255,0.04) !important;
	color: white !important;
}

.league-standings-wrap {
	margin-top: 12px;
	border: 1px solid rgba(255,255,255,0.22);
	border-radius: 14px;
	background: rgba(255,255,255,0.08);
	backdrop-filter: blur(16px);
	-webkit-backdrop-filter: blur(16px);
	overflow: hidden;
	box-shadow: 0 10px 28px rgba(0,0,0,0.20);
}

.league-standings-header,
.league-standings-row {
	display: grid;
	grid-template-columns: 0.8fr 1fr 1fr 2.3fr 2.3fr 1.2fr 1.2fr;
	gap: 10px;
	align-items: center;
	padding: 10px 14px;
	font-size: 13px;
}

.league-standings-header {
	background: rgba(255,255,255,0.14);
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 0.3px;
	font-size: 12px;
	border-bottom: 1px solid rgba(255,255,255,0.20);
}

.league-standings-body {
	max-height: 560px;
	overflow-y: auto;
	padding: 8px;
}

.league-standings-row {
	background: rgba(255,255,255,0.05);
	border: 1px solid rgba(255,255,255,0.14);
	border-radius: 10px;
	margin-bottom: 8px;
}

.league-standings-row:last-child {
	margin-bottom: 0;
}

.league-standings-row.is-you {
	background: rgba(0,255,135,0.14);
	border-color: rgba(0,255,135,0.42);
}

.league-cell.rank,
.league-cell.last-rank,
.league-cell.season-pts,
.league-cell.gw-pts,
.league-cell.move {
	font-weight: 700;
}

.league-cell.move {
	color: rgba(255,255,255,0.85);
}

.league-cell.move.move-up {
	color: #00ff87;
}

.league-cell.move.move-down {
	color: #ff5c7a;
}

.league-cell.move.move-flat {
	color: rgba(255,255,255,0.50);
}

.league-empty {
	padding: 20px;
	text-align: center;
	opacity: 0.85;
}

@media (max-width: 1024px) {
	.league-standings-header,
	.league-standings-row {
		grid-template-columns: 1fr 1fr 1fr;
		gap: 8px;
		font-size: 12px;
	}
}

.page-caption {
	opacity: 0.85;
	margin-top: -4px;
	margin-bottom: 12px;
}
</style>
""",
	unsafe_allow_html=True,
)


def fetch_json(url, timeout=20):
	ctx = ssl.create_default_context(cafile=certifi.where())
	req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
	with urllib.request.urlopen(req, context=ctx, timeout=timeout) as r:
		return json.loads(r.read())


@st.cache_data(ttl=180)
def fetch_entry_data(manager_id):
	return fetch_json(f"https://fantasy.premierleague.com/api/entry/{manager_id}/")


def get_mini_leagues(entry_data):
	classic_leagues = entry_data.get("leagues", {}).get("classic", []) or []
	mini = [league for league in classic_leagues if league.get("league_type") == "x"]
	mini.sort(key=lambda league: (league.get("entry_rank") is None, league.get("entry_rank") or 10**9))
	return mini


@st.cache_data(ttl=180)
def fetch_league_standings_page(league_id, page):
	url = f"https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/?page_standings={page}"
	return fetch_json(url)


@st.cache_data(ttl=180)
def fetch_all_league_members(league_id):
	members = []
	league_meta = {}
	page = 1
	pages_loaded = 0

	while True:
		data = fetch_league_standings_page(league_id, page)
		pages_loaded += 1

		if not league_meta:
			league_meta = data.get("league", {}) or {}

		standings = data.get("standings", {}) or {}
		results = standings.get("results", []) or []
		members.extend(results)

		if not standings.get("has_next"):
			break

		page += 1
		if page > 200:
			break

	members.sort(key=lambda m: (m.get("rank_sort") is None, m.get("rank_sort") or 10**9))
	return league_meta, members, pages_loaded


def fmt(value):
	if value is None:
		return "N/A"
	if isinstance(value, int):
		return f"{value:,}"
	return str(value)


def movement_text(current_rank, last_rank):
	if current_rank is None or last_rank is None:
		return "-"
	delta = last_rank - current_rank
	if delta > 0:
		return f"Up {delta}"
	if delta < 0:
		return f"Down {abs(delta)}"
	return "No change"


def movement_symbol(current_rank, last_rank):
	if current_rank is None or last_rank is None:
		return "-"
	delta = last_rank - current_rank
	if delta > 0:
		return f"↑ {delta}"
	if delta < 0:
		return f"↓ {abs(delta)}"
	return "→ 0"


def movement_class(current_rank, last_rank):
	if current_rank is None or last_rank is None:
		return "move-flat"
	delta = last_rank - current_rank
	if delta > 0:
		return "move-up"
	if delta < 0:
		return "move-down"
	return "move-flat"


def scoring_label(scoring_code):
	mapping = {
		"c": "Classic",
		"h": "Head-to-head",
	}
	return mapping.get(scoring_code, scoring_code or "N/A")


def parse_datetime(value):
	if not value:
		return None
	try:
		return datetime.fromisoformat(value.replace("Z", "+00:00"))
	except Exception:
		return None


manager_id = st.session_state.manager_id
manager_id_int = int(manager_id) if str(manager_id).isdigit() else None
current_gw = st.session_state.get("gw")

st.title("Mini Leagues")


nav_col1, nav_col2, _ = st.columns([1, 1, 5])
with nav_col1:
	if st.button("← Back to Home", use_container_width=True):
		st.switch_page("pages/home.py")
with nav_col2:
	if st.button("Refresh Data", use_container_width=True):
		st.cache_data.clear()
		st.rerun()

try:
	entry_data = fetch_entry_data(manager_id)
except Exception as exc:
	st.error(f"Could not load your leagues right now. ({exc})")
	st.stop()

mini_leagues = get_mini_leagues(entry_data)

if not mini_leagues:
	st.info("No mini leagues found for this team.")
	st.stop()

league_payloads = []
with st.spinner("Loading mini league standings..."):
	for league in mini_leagues:
		league_id = league.get("id")
		if not league_id:
			continue

		try:
			league_meta, members, pages_loaded = fetch_all_league_members(league_id)
			league_payloads.append(
				{
					"league": league,
					"league_meta": league_meta,
					"members": members,
					"pages_loaded": pages_loaded,
				}
			)
		except Exception as exc:
			league_payloads.append(
				{
					"league": league,
					"league_meta": {},
					"members": [],
					"pages_loaded": 0,
					"error": str(exc),
				}
			)

total_members = sum(len(payload.get("members", [])) for payload in league_payloads)
best_rank = min(
	(league.get("entry_rank") for league in mini_leagues if league.get("entry_rank") is not None),
	default=None,
)

summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
summary_col1.metric("Mini Leagues", fmt(len(mini_leagues)))
summary_col2.metric("Total Members Loaded", fmt(total_members))
summary_col3.metric("Best Current Rank", fmt(best_rank))
summary_col4.metric("Current GW", fmt(current_gw))

for index, payload in enumerate(league_payloads, start=1):
	league = payload.get("league", {})
	league_meta = payload.get("league_meta", {})
	members = payload.get("members", [])
	load_error = payload.get("error")

	league_name = league.get("name") or league_meta.get("name") or f"Mini League {index}"
	current_rank = league.get("entry_rank")
	last_rank = league.get("entry_last_rank")

	label = (
		f"{league_name} | rank: {fmt(current_rank)} "
		f"({movement_symbol(current_rank, last_rank)})"
	)

	with st.expander(label, expanded=(index == 1)):
		if load_error:
			st.error(f"Could not load this league's standings. ({load_error})")
			continue

		created_at = parse_datetime(league_meta.get("created"))
		created_label = created_at.strftime("%d %b %Y") if created_at else "N/A"

		your_member = None
		if manager_id_int is not None:
			your_member = next((m for m in members if m.get("entry") == manager_id_int), None)

		season_points = your_member.get("total") if your_member else None

		info_col1, info_col2, info_col3, info_col4 = st.columns(4)
		info_col1.metric("Current Rank", fmt(current_rank))
		info_col2.metric("Season Points", fmt(season_points))
		info_col3.metric("Scoring", scoring_label(league.get("scoring") or league_meta.get("scoring")))
		info_col4.metric("Created", created_label)

		standings_rows = []
		rows_markup = []
		for member in members:
			is_you = manager_id_int is not None and member.get("entry") == manager_id_int
			team_name = member.get("entry_name") or "-"
			manager_name = member.get("player_name") or "-"

			if is_you:
				team_name = f"{team_name} (You)"

			standings_rows.append(
				{
					"Rank": member.get("rank"),
					"Last Rank": member.get("last_rank"),
					"Movement": movement_symbol(member.get("rank"), member.get("last_rank")),
					"Team": team_name,
					"Manager": manager_name,
					"Season Points": member.get("total"),
					"GW Points": member.get("event_total"),
				}
			)

			row_class = "league-standings-row is-you" if is_you else "league-standings-row"
			move_class = movement_class(member.get("rank"), member.get("last_rank"))
			rows_markup.append(
				(
					f'<div class="{row_class}">'
					f'<div class="league-cell rank">{fmt(member.get("rank"))}</div>'
					f'<div class="league-cell last-rank">{fmt(member.get("last_rank"))}</div>'
					f'<div class="league-cell move {move_class}">{movement_symbol(member.get("rank"), member.get("last_rank"))}</div>'
					f'<div class="league-cell team">{html.escape(team_name)}</div>'
					f'<div class="league-cell manager">{html.escape(manager_name)}</div>'
					f'<div class="league-cell season-pts">{fmt(member.get("total"))}</div>'
					f'<div class="league-cell gw-pts">{fmt(member.get("event_total"))}</div>'
					'</div>'
				)
			)

		rows_html = "".join(rows_markup) if rows_markup else "<div class=\"league-empty\">No standings data available.</div>"
		st.markdown(
			(
				'<div class="league-standings-wrap">'
				'<div class="league-standings-header">'
				'<div>Rank</div>'
				'<div>Last</div>'
				'<div>Move</div>'
				'<div>Team</div>'
				'<div>Manager</div>'
				'<div>Season</div>'
				'<div>GW</div>'
				'</div>'
				f'<div class="league-standings-body">{rows_html}</div>'
				'</div>'
			),
			unsafe_allow_html=True,
		)

		st.caption(
			f"League ID: {league.get('id')} | Start event: {fmt(league.get('start_event') or league_meta.get('start_event'))} | "
			f"Pages loaded: {payload.get('pages_loaded')} | Members shown: {len(standings_rows)}"
		)
