import streamlit as st  # type: ignore
import json
import urllib.request
import ssl
import certifi
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
	background: linear-gradient(135deg, #37003c, #2b1e5b, #00ff87) !important;
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

div[data-testid="stDataFrame"] {
	border: 1px solid rgba(255,255,255,0.15);
	border-radius: 10px;
	overflow: hidden;
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

	label = f"{league_name}  |  Your rank: {fmt(current_rank)} ({movement_symbol(current_rank, last_rank)})"

	with st.expander(label, expanded=(index == 1)):
		if load_error:
			st.error(f"Could not load this league's standings. ({load_error})")
			continue

		league_size = league_meta.get("size") or league_meta.get("max_entries") or len(members)
		created_at = parse_datetime(league_meta.get("created"))
		created_label = created_at.strftime("%d %b %Y") if created_at else "N/A"

		your_member = None
		if manager_id_int is not None:
			your_member = next((m for m in members if m.get("entry") == manager_id_int), None)

		season_points = your_member.get("total") if your_member else None
		gw_points = your_member.get("event_total") if your_member else None

		info_col1, info_col2, info_col3, info_col4 = st.columns(4)
		info_col1.metric("Total Members", fmt(league_size))
		info_col2.metric("Your Previous Rank", fmt(last_rank))
		info_col3.metric("Your Rank Movement", movement_text(current_rank, last_rank))
		info_col4.metric("Scoring", scoring_label(league.get("scoring") or league_meta.get("scoring")))

		you_col1, you_col2, you_col3 = st.columns(3)
		you_col1.metric("Your Season Points", fmt(season_points))
		you_col2.metric("Your GW Points", fmt(gw_points))
		you_col3.metric("Created", created_label)

		standings_rows = []
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

		table_height = 420 if len(standings_rows) < 12 else min(900, 70 + len(standings_rows) * 34)
		st.dataframe(
			standings_rows,
			use_container_width=True,
			hide_index=True,
			height=table_height,
		)

		st.caption(
			f"League ID: {league.get('id')} | Start event: {fmt(league.get('start_event') or league_meta.get('start_event'))} | "
			f"Pages loaded: {payload.get('pages_loaded')} | Members shown: {len(standings_rows)}"
		)
