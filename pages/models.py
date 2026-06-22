import ast
import html
import json
import ssl
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import certifi
import streamlit as st  # type: ignore
from nav import render_top_nav

# ─── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="FPL Transfer Lab", layout="wide")

is_guest = st.session_state.get("guest", False)
if "manager_id" not in st.session_state and not is_guest:
    st.warning("No manager ID found. Go back to Dashboard and connect your team.")
    if st.button("Go to Dashboard"):
        st.switch_page("live_dashboard.py")
    st.stop()

# ─── CSS ───────────────────────────────────────────────────────────────────────
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

/* glass panels */
.glass-panel {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 18px;
    padding: 20px 22px;
    box-shadow: 0 14px 34px rgba(0,0,0,0.28);
    color: white;
    margin-bottom: 16px;
}

.glass-panel-strong {
    background: rgba(255,255,255,0.16);
    border: 1px solid rgba(255,255,255,0.24);
    border-radius: 18px;
    padding: 20px 22px;
    box-shadow: 0 14px 34px rgba(0,0,0,0.28);
    color: white;
    margin-bottom: 16px;
}

.panel-title {
    font-size: 18px;
    font-weight: 900;
    margin-bottom: 6px;
}

.panel-sub {
    font-size: 13px;
    opacity: 0.78;
    margin-bottom: 14px;
}

.kicker {
    text-transform: uppercase;
    letter-spacing: 1.4px;
    font-size: 11px;
    font-weight: 700;
    color: rgba(255,255,255,0.7);
    margin-bottom: 4px;
}

/* metric cards */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-top: 12px;
}

.metric-card {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 14px;
    padding: 14px 12px;
    text-align: center;
}

.metric-label {
    font-size: 11px;
    color: rgba(255,255,255,0.68);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.metric-value {
    font-size: 26px;
    font-weight: 900;
    margin-top: 4px;
    color: #00ff87;
}

.metric-note {
    font-size: 11px;
    color: rgba(255,255,255,0.60);
    margin-top: 3px;
}

/* squad grid */
.squad-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 10px;
    margin-top: 12px;
}

.squad-card {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 14px;
    padding: 12px 10px;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.squad-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.3);
}

.squad-card img {
    width: 60px;
    height: 77px;
    object-fit: contain;
    border-radius: 8px;
    margin-bottom: 6px;
}

.squad-card .sq-name {
    font-size: 13px;
    font-weight: 800;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.squad-card .sq-meta {
    font-size: 11px;
    color: rgba(255,255,255,0.65);
    margin-top: 2px;
}

.squad-card .sq-score {
    font-size: 14px;
    font-weight: 900;
    color: #00ff87;
    margin-top: 4px;
}

/* transfer rows */
.transfer-row {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 14px;
}

.transfer-row:hover {
    background: rgba(255,255,255,0.12);
}

.transfer-player {
    display: flex;
    align-items: center;
    gap: 12px;
}

.transfer-player img {
    width: 48px;
    height: 62px;
    object-fit: contain;
    border-radius: 8px;
    flex-shrink: 0;
}

.transfer-player .tp-name {
    font-size: 14px;
    font-weight: 800;
}

.transfer-player .tp-meta {
    font-size: 12px;
    color: rgba(255,255,255,0.65);
    margin-top: 2px;
}

.transfer-player .tp-score {
    font-size: 13px;
    font-weight: 900;
    color: #00ff87;
    margin-top: 3px;
}

.transfer-player .tp-score.out {
    color: #ff4f6d;
}

.transfer-arrow {
    font-size: 28px;
    color: #00ff87;
    animation: pulse-arrow 1.5s ease-in-out infinite;
    text-align: center;
}

@keyframes pulse-arrow {
    0%, 100% { opacity: 0.6; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.15); }
}

/* FDR pills */
.fdr-pills {
    display: flex;
    gap: 4px;
    margin-top: 4px;
    flex-wrap: wrap;
}

.fdr-pill {
    font-size: 10px;
    font-weight: 800;
    padding: 2px 6px;
    border-radius: 6px;
    color: #111;
}

.fdr-1, .fdr-2 { background: #00ff87; }
.fdr-3 { background: #ffb500; }
.fdr-4 { background: #ff7b4f; }
.fdr-5 { background: #ff4f6d; color: white; }

/* recommendation cards */
.rec-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 12px;
    margin-top: 12px;
}

.rec-card {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.14);
    border-radius: 14px;
    padding: 14px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.rec-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.3);
}

.rec-card img {
    width: 50px;
    height: 64px;
    object-fit: contain;
    border-radius: 8px;
    float: left;
    margin-right: 12px;
}

.rec-card .rc-name {
    font-size: 14px;
    font-weight: 800;
}

.rec-card .rc-meta {
    font-size: 11px;
    color: rgba(255,255,255,0.65);
    margin-top: 2px;
}

.rec-card .rc-score {
    font-size: 16px;
    font-weight: 900;
    color: #00ff87;
    margin-top: 4px;
}

.rec-card .rc-price {
    font-size: 12px;
    font-weight: 700;
    color: rgba(255,255,255,0.8);
}

/* summary box */
.summary-box {
    background: linear-gradient(135deg, rgba(0,255,135,0.12), rgba(255,255,255,0.08));
    border: 1px solid rgba(0,255,135,0.35);
    border-radius: 18px;
    padding: 20px 22px;
    margin-top: 16px;
}

.summary-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}

.summary-row:last-child {
    border-bottom: none;
}

.summary-label {
    font-size: 13px;
    font-weight: 700;
    color: rgba(255,255,255,0.8);
}

.summary-value {
    font-size: 14px;
    font-weight: 900;
}

.summary-value.green { color: #00ff87; }
.summary-value.red { color: #ff4f6d; }
.summary-value.amber { color: #ffb500; }

/* empty state */
.empty-msg {
    text-align: center;
    padding: 30px;
    font-size: 14px;
    color: rgba(255,255,255,0.6);
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,0.12) !important;
    border: 1px solid rgba(255,255,255,0.20) !important;
    border-radius: 18px !important;
    box-shadow: 0 14px 34px rgba(0,0,0,0.28) !important;
}

div[data-testid="stSelectbox"] label,
div[data-testid="stRadio"] label,
div[data-testid="stSlider"] label,
div[data-testid="stNumberInput"] label {
    color: rgba(255,255,255,0.86) !important;
    font-weight: 800 !important;
}

div[data-baseweb="select"] > div,
div[role="radiogroup"] label {
    background: rgba(255,255,255,0.12) !important;
    border-color: rgba(255,255,255,0.25) !important;
    color: white !important;
}

div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.10) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    border-radius: 12px !important;
    padding: 10px !important;
}

div[data-testid="stMetric"] label,
div[data-testid="stMetric"] div {
    color: white !important;
}
</style>
""",
    unsafe_allow_html=True,
)

render_top_nav()


# ─── Utilities ─────────────────────────────────────────────────────────────────
def esc(v):
    return html.escape(str(v)) if v is not None else ""


def to_float(v, fallback=0.0):
    if v in (None, ""):
        return fallback
    try:
        return float(v)
    except (TypeError, ValueError):
        return fallback


def to_int(v, fallback=0):
    if v in (None, ""):
        return fallback
    try:
        return int(v)
    except (TypeError, ValueError):
        return fallback


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def parse_dt(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        return None


ROOT_DIR = Path(__file__).resolve().parents[1]
LOCAL_BOOTSTRAP = ROOT_DIR / "data" / "raw" / "bootstrap_static.json"
LOCAL_FIXTURES = ROOT_DIR / "data" / "raw" / "fixtures.json"
POINTS_PAGE = ROOT_DIR / "pages" / "points.py"
BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
FIXTURES_URL = "https://fantasy.premierleague.com/api/fixtures/"
POS_MAP = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}
POS_FULL = {1: "Goalkeepers", 2: "Defenders", 3: "Midfielders", 4: "Forwards"}


@st.cache_data(show_spinner=False)
def load_fallback_jersey():
    try:
        tree = ast.parse(POINTS_PAGE.read_text())
    except Exception:
        return ""

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "FALLBACK_JERSEY" for t in node.targets):
            continue
        try:
            return ast.literal_eval(node.value)
        except Exception:
            return ""
    return ""


def fetch_json(url):
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(url, context=ctx, timeout=10) as r:
        return json.loads(r.read())


def load_local(path, fallback):
    if not path.exists():
        return fallback
    try:
        with path.open() as f:
            return json.load(f)
    except Exception:
        return fallback


@st.cache_data(ttl=900, show_spinner=False)
def fetch_bootstrap():
    try:
        return fetch_json(BOOTSTRAP_URL)
    except Exception:
        return load_local(LOCAL_BOOTSTRAP, {})


@st.cache_data(ttl=900, show_spinner=False)
def fetch_fixtures():
    try:
        return fetch_json(FIXTURES_URL)
    except Exception:
        return load_local(LOCAL_FIXTURES, [])


@st.cache_data(ttl=120, show_spinner=False)
def fetch_entry(manager_id):
    return fetch_json(f"https://fantasy.premierleague.com/api/entry/{manager_id}/")


@st.cache_data(ttl=120, show_spinner=False)
def fetch_picks(manager_id, gw):
    return fetch_json(
        f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{gw}/picks/"
    )


@st.cache_data(ttl=300, show_spinner=False)
def fetch_history(manager_id):
    return fetch_json(
        f"https://fantasy.premierleague.com/api/entry/{manager_id}/history/"
    )


def current_event(events):
    for e in events:
        if e.get("is_current"):
            return to_int(e["id"], 1)
    for e in events:
        if e.get("is_next"):
            return max(1, to_int(e["id"], 1) - 1)
    return max((to_int(e.get("id"), 0) for e in events), default=1)


def photo_url(player):
    photo = player.get("photo")
    if not photo:
        return ""
    return f"https://resources.premierleague.com/premierleague/photos/players/110x140/p{photo.replace('.jpg', '.png')}"


def logo_url(code):
    if not code:
        return ""
    return f"https://resources.premierleague.com/premierleague/badges/50/t{code}.png"


# ─── Next fixtures for a team ─────────────────────────────────────────────────
def next_fixtures_for_team(team_id, all_fixtures, team_map, count=3):
    upcoming = []
    for fx in all_fixtures:
        if fx.get("finished"):
            continue
        h, a = fx.get("team_h"), fx.get("team_a")
        if team_id not in (h, a):
            continue
        is_home = h == team_id
        opp_id = a if is_home else h
        opp = team_map.get(opp_id, {})
        diff_key = "team_h_difficulty" if is_home else "team_a_difficulty"
        fdr = to_int(fx.get(diff_key), 3)
        upcoming.append(
            {
                "event": to_int(fx.get("event")),
                "opp_short": opp.get("short_name", "?"),
                "venue": "H" if is_home else "A",
                "fdr": fdr,
            }
        )
    upcoming.sort(key=lambda x: x["event"])
    return upcoming[:count]


# ─── Scoring model ─────────────────────────────────────────────────────────────
def compute_score(player, fixtures_next3):
    """
    Weighted composite score for transfer targeting.
    Higher = better pick.
    """
    form = to_float(player.get("form"))
    xgi90 = to_float(player.get("expected_goal_involvements_per_90"))
    minutes = to_float(player.get("minutes"))
    pts = to_float(player.get("total_points"))
    pts90 = (pts / minutes * 90) if minutes > 0 else 0
    own = to_float(player.get("selected_by_percent"))

    # Fixture ease: avg of (6 - fdr) for next fixtures, normalised 0–1
    if fixtures_next3:
        raw_ease = sum(6 - fx["fdr"] for fx in fixtures_next3) / len(fixtures_next3)
        fixture_ease = clamp(raw_ease / 5, 0, 1)
    else:
        fixture_ease = 0.5

    # Ownership factor (higher ownership = slight bonus for differential safety)
    own_factor = clamp(own / 100, 0, 1)

    score = (
        0.30 * form
        + 0.25 * xgi90 * 20  # scale xgi90 to similar range as form
        + 0.20 * pts90
        + 0.15 * fixture_ease * 10  # scale to ~0-10
        + 0.10 * own_factor * 5  # scale to ~0-5
    )
    return round(score, 2)


# ─── Load data ─────────────────────────────────────────────────────────────────
bootstrap = fetch_bootstrap()
all_fixtures = fetch_fixtures()
events = bootstrap.get("events", [])
teams_raw = bootstrap.get("teams", [])
elements = bootstrap.get("elements", [])
element_types = bootstrap.get("element_types", [])

if not teams_raw or not elements:
    st.error("Could not load FPL data. Please try again later.")
    st.stop()

team_map = {t["id"]: t for t in teams_raw}
et_map = {et["id"]: et for et in element_types}
gw = st.session_state.get("gw") or current_event(events)

# All active players
all_players = [p for p in elements if not p.get("removed") and p.get("status") == "a"]
player_by_id = {p["id"]: p for p in elements}

# Precompute next-3 fixtures per team
team_fixtures = {}
for tid in team_map:
    team_fixtures[tid] = next_fixtures_for_team(tid, all_fixtures, team_map, count=3)

# Precompute scores for all players
player_scores = {}
for p in all_players:
    tid = p.get("team")
    fxs = team_fixtures.get(tid, [])
    player_scores[p["id"]] = compute_score(p, fxs)

# ─── Manager data ─────────────────────────────────────────────────────────────
if is_guest:
    st.markdown("### ⚽ Transfer Lab")
    st.info("Connect your team on the Dashboard to use the Transfer Lab. Guest mode shows a demo view.")
    st.stop()

manager_id = st.session_state.manager_id

try:
    entry_data = fetch_entry(manager_id)
    picks_data = fetch_picks(manager_id, gw)
    history_data = fetch_history(manager_id)
except Exception as exc:
    st.error(f"Could not fetch manager data: {exc}")
    st.stop()

# Extract squad
squad_picks = picks_data.get("picks", [])
entry_history = picks_data.get("entry_history", {})
bank = to_float(entry_history.get("bank")) / 10  # bank is in tenths
squad_value = to_float(entry_history.get("value")) / 10
event_transfers = to_int(entry_history.get("event_transfers"))

# Determine free transfers
# FPL doesn't directly expose remaining free transfers via the API,
# so we derive it from the history data
history_current = history_data.get("current", [])
chips_used = history_data.get("chips", [])

# Check active chips
active_chip = None
for chip in chips_used:
    if chip.get("event") == gw:
        active_chip = chip.get("name")

# Estimate free transfers: start at 1, accumulate unused ones (max 5 since 24/25)
free_transfers = 1
for hw in sorted(history_current, key=lambda x: to_int(x.get("event"))):
    ev = to_int(hw.get("event"))
    if ev >= gw:
        break
    used = to_int(hw.get("event_transfers"))
    # If wildcard or free hit was active, transfers don't deduct from saved transfers
    wc_or_fh = any(
        c.get("event") == ev and c.get("name") in ("wildcard", "freehit")
        for c in chips_used
    )
    if wc_or_fh:
        free_transfers = min(5, free_transfers + 1)
    else:
        free_transfers = min(5, max(1, free_transfers - used + 1))

# If transfers already made this GW, subtract them
remaining_transfers = max(0, free_transfers - event_transfers)

# Squad player details
squad_ids = set()
squad_players = []
for pick in squad_picks:
    pid = pick["element"]
    squad_ids.add(pid)
    p = player_by_id.get(pid, {})
    tid = p.get("team")
    fxs = team_fixtures.get(tid, [])
    score = compute_score(p, fxs)
    squad_players.append(
        {
            "pick": pick,
            "player": p,
            "score": score,
            "fixtures": fxs,
            "selling_price": to_float(pick.get("selling_price", p.get("now_cost", 0))) / 10,
        }
    )

team_name = entry_data.get("player_first_name", "") + " " + entry_data.get("player_last_name", "")
fpl_team_name = entry_data.get("name", "My Team")


# ─── RENDER ────────────────────────────────────────────────────────────────────

# Header
st.markdown(
    f"""
<div class="glass-panel-strong">
    <div class="kicker">TRANSFER LAB</div>
    <div class="panel-title">Smart Transfer Assistant — GW{gw + 1}</div>
    <div class="panel-sub">
        Analysing <b>{esc(fpl_team_name)}</b> managed by <b>{esc(team_name)}</b>.
        Our model scores every player on form, expected output, fixture difficulty, and ownership
        to find the best moves for your squad.
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ── Metrics row ────────────────────────────────────────────────────────────────
chip_note = f"<br><span style='color:#ffb500;font-size:10px;'>{active_chip.upper()} active</span>" if active_chip else ""
transfers_color = "#00ff87" if remaining_transfers > 0 else "#ff4f6d"

st.markdown(
    f"""
<div class="metric-grid">
    <div class="metric-card">
        <div class="metric-label">Free Transfers</div>
        <div class="metric-value" style="color:{transfers_color}">{remaining_transfers}</div>
        <div class="metric-note">{event_transfers} used this GW{chip_note}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Bank</div>
        <div class="metric-value">£{bank:.1f}m</div>
        <div class="metric-note">Available to spend</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Squad Value</div>
        <div class="metric-value">£{squad_value:.1f}m</div>
        <div class="metric-note">Total team value</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Total Budget</div>
        <div class="metric-value">£{bank + squad_value:.1f}m</div>
        <div class="metric-note">Value + Bank</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("")

# ── Current Squad ──────────────────────────────────────────────────────────────
def image_tag(src, css_class=""):
    fallback = load_fallback_jersey()
    class_attr = f' class="{css_class}"' if css_class else ""
    if src:
        if fallback:
            # Try the real player photo; swap to jersey on load failure
            fb_js = fallback.replace("\\", "\\\\").replace("'", "\\'")
            return f'<img{class_attr} src="{esc(src)}" onerror="this.onerror=null;this.src=\'{fb_js}\'">'
        else:
            return f'<img{class_attr} src="{esc(src)}">'
    elif fallback:
        return f'<img{class_attr} src="{esc(fallback)}">'
    else:
        return ""


def render_fdr_pills(fixtures):
    pills = '<div class="fdr-pills">'
    for fx in fixtures:
        fdr = clamp(to_int(fx.get("fdr"), 3), 1, 5)
        pills += (
            f'<span class="fdr-pill fdr-{fdr}">'
            f'{esc(fx.get("opp_short", "?"))} {esc(fx.get("venue", ""))}'
            '</span>'
        )
    pills += "</div>"
    return pills


with st.container(border=True):
    st.markdown("#### 📋 Current Squad")
    st.caption("Your 15-man squad scored by our model. Lower scores = potential transfer-out candidates.")

    sorted_squad = sorted(
        squad_players,
        key=lambda x: (x["player"].get("element_type", 5), x["pick"].get("position", 99)),
    )

    squad_html = '<div class="squad-grid">'
    for sp in sorted_squad:
        p = sp["player"]
        pos = POS_MAP.get(p.get("element_type"), "?")
        team = team_map.get(p.get("team"), {})
        cost = to_float(p.get("now_cost")) / 10
        is_bench = sp["pick"].get("position", 99) > 11
        bench_class = " style='opacity:0.65;'" if is_bench else ""
        bench_tag = "<span style='font-size:9px;color:#ffb500;'>BENCH</span>" if is_bench else ""

        squad_html += f"""
<div class="squad-card"{bench_class}>
    {image_tag(photo_url(p))}
    <div class="sq-name">{esc(p.get('web_name', '?'))}</div>
    <div class="sq-meta">{pos} &middot; {esc(team.get('short_name', '?'))} &middot; &pound;{cost:.1f}m</div>
    <div class="sq-score">{sp['score']:.1f}</div>
    {render_fdr_pills(sp['fixtures'])}
    {bench_tag}
</div>"""
    squad_html += "</div>"
    st.markdown(squad_html, unsafe_allow_html=True)


# ── Transfer Recommendations ──────────────────────────────────────────────────
def team_counts_for_squad(players):
    counts = {}
    for sp in players:
        team_id = sp["player"].get("team")
        if team_id:
            counts[team_id] = counts.get(team_id, 0) + 1
    return counts


def find_replacements(out_sp, available_cash, counts, excluded_ids, count=3):
    out_player = out_sp["player"]
    out_position = out_player.get("element_type")
    out_team = out_player.get("team")
    out_price = out_sp["selling_price"]
    max_spend = available_cash + out_price

    counts_after_sale = dict(counts)
    if out_team in counts_after_sale:
        counts_after_sale[out_team] = max(0, counts_after_sale[out_team] - 1)

    candidates = []
    for p in all_players:
        if p["id"] in excluded_ids:
            continue
        if p.get("element_type") != out_position:
            continue
        if to_float(p.get("minutes")) < 90:
            continue

        p_cost = to_float(p.get("now_cost")) / 10
        if p_cost > max_spend:
            continue

        p_team = p.get("team")
        if counts_after_sale.get(p_team, 0) >= 3:
            continue

        candidates.append(
            {
                "player": p,
                "score": player_scores.get(p["id"], 0),
                "cost": p_cost,
                "fixtures": team_fixtures.get(p_team, []),
            }
        )

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:count]


with st.container(border=True):
    st.markdown("#### 🔄 Recommended Transfers")
    st.caption(
        "Suggestions use model score, budget, position, squad ownership, and the three-player club limit."
    )

    max_suggestions = min(3, max(1, len([sp for sp in squad_players if sp["pick"].get("position", 99) <= 11])))
    suggested_default = min(max_suggestions, max(1, remaining_transfers or 1))
    num_transfers = st.slider(
        "Transfer suggestions",
        min_value=1,
        max_value=max_suggestions,
        value=suggested_default,
        step=1,
        key="model_transfer_count",
    )

    starters = [sp for sp in squad_players if sp["pick"].get("position", 99) <= 11]
    transfer_out_candidates = sorted(starters, key=lambda x: x["score"])[:num_transfers]

    counts = team_counts_for_squad(squad_players)
    excluded_ids = set(squad_ids)
    available_cash = bank
    transfer_pairs = []

    for out_sp in transfer_out_candidates:
        options = find_replacements(out_sp, available_cash, counts, excluded_ids)
        if not options:
            continue

        best_in = options[0]
        out_player = out_sp["player"]
        in_player = best_in["player"]
        transfer_pairs.append({"out": out_sp, "best_in": best_in, "in_options": options})

        available_cash -= best_in["cost"] - out_sp["selling_price"]
        excluded_ids.add(in_player["id"])
        out_team = out_player.get("team")
        in_team = in_player.get("team")
        if out_team in counts:
            counts[out_team] = max(0, counts[out_team] - 1)
        if in_team:
            counts[in_team] = counts.get(in_team, 0) + 1

    if not transfer_pairs:
        st.markdown(
            '<div class="empty-msg">No affordable upgrades found for the current settings.</div>',
            unsafe_allow_html=True,
        )
    else:
        for pair in transfer_pairs:
            out_sp = pair["out"]
            out_p = out_sp["player"]
            best_in = pair["best_in"]
            in_p = best_in["player"]
            out_team = team_map.get(out_p.get("team"), {})
            in_team = team_map.get(in_p.get("team"), {})
            out_pos = POS_MAP.get(out_p.get("element_type"), "?")
            in_pos = POS_MAP.get(in_p.get("element_type"), "?")

            st.markdown(
                f"""
<div class="transfer-row">
    <div class="transfer-player">
        {image_tag(photo_url(out_p))}
        <div>
            <div class="tp-name">{esc(out_p.get('web_name', '?'))}</div>
            <div class="tp-meta">{out_pos} &middot; {esc(out_team.get('short_name', '?'))} &middot; &pound;{out_sp['selling_price']:.1f}m</div>
            <div class="tp-score out">Score: {out_sp['score']:.1f}</div>
            {render_fdr_pills(out_sp['fixtures'])}
        </div>
    </div>
    <div class="transfer-arrow">&rarr;</div>
    <div class="transfer-player">
        {image_tag(photo_url(in_p))}
        <div>
            <div class="tp-name">{esc(in_p.get('web_name', '?'))}</div>
            <div class="tp-meta">{in_pos} &middot; {esc(in_team.get('short_name', '?'))} &middot; &pound;{best_in['cost']:.1f}m</div>
            <div class="tp-score">Score: {best_in['score']:.1f}</div>
            {render_fdr_pills(best_in['fixtures'])}
        </div>
    </div>
</div>
""",
                unsafe_allow_html=True,
            )

            alts = pair["in_options"][1:]
            if alts:
                alt_names = ", ".join(
                    f"**{a['player'].get('web_name', '?')}** ({a['score']:.1f}, £{a['cost']:.1f}m)"
                    for a in alts
                )
                st.caption(f"Alternatives: {alt_names}")


# ── Transfer Summary ──────────────────────────────────────────────────────────
if transfer_pairs:
    total_sold = sum(p["out"]["selling_price"] for p in transfer_pairs)
    total_bought = sum(p["best_in"]["cost"] for p in transfer_pairs)
    net_cost = total_bought - total_sold
    new_bank = bank - net_cost
    hit_cost = max(0, len(transfer_pairs) - remaining_transfers) * 4
    score_gain = sum(p["best_in"]["score"] - p["out"]["score"] for p in transfer_pairs)

    net_class = "green" if net_cost <= 0 else "red"
    bank_class = "green" if new_bank >= 0 else "red"
    gain_class = "green" if score_gain > 0 else ("red" if score_gain < 0 else "amber")
    hit_class = "green" if hit_cost == 0 else "red"

    summary_rows = ""
    for pair in transfer_pairs:
        out_n = pair["out"]["player"].get("web_name", "?")
        in_n = pair["best_in"]["player"].get("web_name", "?")
        summary_rows += f"""
<div class="summary-row">
    <span class="summary-label">{esc(out_n)} &rarr; {esc(in_n)}</span>
    <span class="summary-value">&pound;{pair['out']['selling_price']:.1f}m &rarr; &pound;{pair['best_in']['cost']:.1f}m</span>
</div>"""

    st.markdown(
        f"""
<div class="summary-box">
    <div class="kicker" style="margin-bottom:10px;">TRANSFER SUMMARY</div>
    {summary_rows}
    <div class="summary-row">
        <span class="summary-label">Net Cost</span>
        <span class="summary-value {net_class}">{'+' if net_cost > 0 else ''}&pound;{net_cost:.1f}m</span>
    </div>
    <div class="summary-row">
        <span class="summary-label">New Bank Balance</span>
        <span class="summary-value {bank_class}">&pound;{new_bank:.1f}m</span>
    </div>
    <div class="summary-row">
        <span class="summary-label">Points Hit</span>
        <span class="summary-value {hit_class}">{'-' + str(hit_cost) if hit_cost > 0 else 'None (free)'}</span>
    </div>
    <div class="summary-row">
        <span class="summary-label">Score Improvement</span>
        <span class="summary-value {gain_class}">{'+' if score_gain > 0 else ''}{score_gain:.1f}</span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown("")

# ── Top picks by position ─────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown("#### 🏆 Top Picks by Position")
    st.caption("Best available players not in your squad, ranked by our composite model score.")

    position_filter = st.radio(
        "Position",
        ["All", "GKP", "DEF", "MID", "FWD"],
        horizontal=True,
        key="model_pos_filter",
    )
    max_price = st.slider(
        "Max price (£m)",
        min_value=3.5,
        max_value=15.0,
        value=min(15.0, max(3.5, bank + 5.0)),
        step=0.1,
        key="model_max_price",
    )

    pos_id_filter = None
    if position_filter != "All":
        pos_id_filter = {v: k for k, v in POS_MAP.items()}.get(position_filter)

    filtered = []
    for p in all_players:
        if p["id"] in squad_ids:
            continue
        if to_float(p.get("minutes")) < 90:
            continue
        cost_val = to_float(p.get("now_cost")) / 10
        if cost_val > max_price:
            continue
        if pos_id_filter and p.get("element_type") != pos_id_filter:
            continue
        filtered.append(
            {
                "player": p,
                "score": player_scores.get(p["id"], 0),
                "cost": cost_val,
                "fixtures": team_fixtures.get(p.get("team"), []),
            }
        )

    filtered.sort(key=lambda x: x["score"], reverse=True)
    top_picks = filtered[:12]

    if not top_picks:
        st.markdown(
            '<div class="empty-msg">No players match your filters.</div>',
            unsafe_allow_html=True,
        )
    else:
        rec_html = '<div class="rec-grid">'
        for tp in top_picks:
            p = tp["player"]
            pos = POS_MAP.get(p.get("element_type"), "?")
            team = team_map.get(p.get("team"), {})
            form_val = to_float(p.get("form"))
            xgi_val = to_float(p.get("expected_goal_involvements_per_90"))
            rec_html += f"""
<div class="rec-card">
    {image_tag(photo_url(p))}
    <div class="rc-name">{esc(p.get('web_name', '?'))}</div>
    <div class="rc-meta">{pos} &middot; {esc(team.get('short_name', '?'))}</div>
    <div class="rc-score">{tp['score']:.1f}</div>
    <div class="rc-price">&pound;{tp['cost']:.1f}m &middot; Form {form_val:.1f} &middot; xGI/90 {xgi_val:.2f}</div>
    {render_fdr_pills(tp['fixtures'])}
</div>"""
        rec_html += "</div>"
        st.markdown(rec_html, unsafe_allow_html=True)