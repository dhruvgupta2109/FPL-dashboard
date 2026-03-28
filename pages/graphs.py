import streamlit as st
import streamlit.components.v1 as components
import json
import urllib.request
import ssl
import certifi

st.set_page_config(page_title="FPL Graphs", layout="wide")

if "manager_id" not in st.session_state:
    st.warning("No manager ID found. Go back to Home and connect your team.")
    if st.button("Go to Dashboard"):
        st.switch_page("live_dashboard.py")
    st.stop()

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #37003c, #2b1e5b, #00ff87) !important;
    min-height: 100vh;
}
.stMainBlockContainer {
    padding-top: 2rem !important;
    max-width: none !important;
    width: 100% !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}
div[data-testid="stButton"] > button {
    background: rgba(255,255,255,0.12) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.25) !important;
    border-radius: 12px !important;
    padding: 12px 40px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    width: 100% !important;
}
div[data-testid="stButton"] > button:hover {
    background: rgba(255,255,255,0.22) !important;
    color: white !important;
}
iframe { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

manager_id = st.session_state.manager_id
gw         = st.session_state.gw

# ── Data fetching ────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def fetch_bootstrap_static():
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = "https://fantasy.premierleague.com/api/bootstrap-static/"
    with urllib.request.urlopen(url, context=ctx) as r:
        return json.loads(r.read())

@st.cache_data(ttl=3600)
def fetch_entry_event_entry_history(entry_id, event_id):
    ctx = ssl.create_default_context(cafile=certifi.where())
    url = f"https://fantasy.premierleague.com/api/entry/{entry_id}/event/{event_id}/picks/"
    with urllib.request.urlopen(url, context=ctx) as r:
        data = json.loads(r.read())
    return data.get("entry_history", {}) or {}

bootstrap_static = fetch_bootstrap_static()
avg_by_event = {
    e.get("id"): (e.get("average_entry_score") or 0)
    for e in bootstrap_static.get("events", [])
    if e.get("id") is not None
}

gw_labels   = list(range(1, gw + 1))
pts_series  = []
rank_series = []
for event_id in gw_labels:
    try:
        eh = fetch_entry_event_entry_history(manager_id, event_id)
        pts_series.append(eh.get("points", eh.get("total_points", 0)) or 0)
        rank_series.append(eh.get("overall_rank", eh.get("rank", 0)) or 0)
    except Exception:
        pts_series.append(0)
        rank_series.append(0)

avg_series = [avg_by_event.get(event_id, 0) for event_id in gw_labels]

gw_labels_json   = json.dumps(gw_labels)
pts_series_json  = json.dumps(pts_series)
avg_series_json  = json.dumps(avg_series)
rank_series_json = json.dumps(rank_series)

# Smart tick step so x-axis never crowds
tick_step = max(1, len(gw_labels) // 10)

# ── Render ───────────────────────────────────────────────────────────────────

components.html(f"""<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
    background: transparent;
    font-family: sans-serif;
    padding: 8px 60px 24px 60px;
    display: flex;
    flex-direction: column;
    gap: 20px;
}}

/* ── Glassbox ─────────────────────────────────── */
.glassbox {{
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(24px);
    border-radius: 24px;
    border: 1px solid rgba(255,255,255,0.15);
    padding: 24px 28px 32px 28px;
    display: flex;
    flex-direction: column;
    gap: 12px;
}}

.chart-title {{
    color: white;
    font-size: 17px;
    font-weight: 700;
    letter-spacing: 0.3px;
    text-align: left;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(255,255,255,0.12);
}}

.chart-wrap {{
    width: 100%;
    height: 340px;
    position: relative;
}}

.chart-wrap canvas {{
    width: 100% !important;
    height: 100% !important;
}}
</style>
</head>
<body>

<!-- ── Chart 1: Points & Average ── -->
<div class="glassbox">
    <div class="chart-title">Points &amp; GW Average</div>
    <div class="chart-wrap">
        <canvas id="pointsChart"></canvas>
    </div>
</div>

<!-- ── Chart 2: World Rank ── -->
<div class="glassbox">
    <div class="chart-title">Worldwide Rank</div>
    <div class="chart-wrap">
        <canvas id="rankChart"></canvas>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
const gwLabels = {gw_labels_json};
const pts      = {pts_series_json};
const avgPts   = {avg_series_json};
const ranks    = {rank_series_json};

// Shared x-axis config — horizontal labels, max 10 ticks
const xAxis = {{
    ticks: {{
        color: 'rgba(255,255,255,0.75)',
        maxRotation: 0,
        minRotation: 0,
        autoSkip: true,
        maxTicksLimit: 10,
        callback: function(val, idx) {{
            return gwLabels[idx];
        }}
    }},
    grid: {{ color: 'rgba(255,255,255,0.08)' }},
    afterFit: function(axis) {{ axis.paddingRight = 10; }}
}};

const yAxis = {{
    ticks: {{ color: 'rgba(255,255,255,0.75)' }},
    grid:  {{ color: 'rgba(255,255,255,0.08)' }}
}};

const legendOpts = {{
    labels: {{
        color: 'rgba(255,255,255,0.9)',
        boxWidth: 14,
        font: {{ size: 12 }}
    }}
}};

// ── Points chart ─────────────────────────────────────────────────────────
new Chart(document.getElementById('pointsChart').getContext('2d'), {{
    type: 'line',
    data: {{
        labels: gwLabels,
        datasets: [
            {{
                label: 'My Points',
                data: pts,
                borderColor: '#00ff87',
                backgroundColor: 'rgba(0,255,135,0.12)',
                tension: 0.35,
                fill: true,
                pointRadius: 4,
                pointHoverRadius: 6,
                borderWidth: 2.5
            }},
            {{
                label: 'GW Average',
                data: avgPts,
                borderColor: '#ffb500',
                backgroundColor: 'rgba(255,181,0,0.08)',
                tension: 0.35,
                fill: false,
                pointRadius: 3,
                pointHoverRadius: 5,
                borderWidth: 2,
                borderDash: [5, 3]
            }}
        ]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
            legend: legendOpts,
            tooltip: {{
                backgroundColor: 'rgba(30,10,40,0.9)',
                titleColor: 'rgba(255,255,255,0.9)',
                bodyColor: 'rgba(255,255,255,0.75)',
                borderColor: 'rgba(255,255,255,0.15)',
                borderWidth: 1,
                padding: 10
            }}
        }},
        scales: {{ x: xAxis, y: yAxis }}
    }}
}});

// ── Rank chart ───────────────────────────────────────────────────────────
const rankCtx = document.getElementById('rankChart').getContext('2d');

// Gradient fill: green (top/best rank) → red (bottom/worst rank)
const rankGradient = rankCtx.createLinearGradient(0, 0, 0, 340);
rankGradient.addColorStop(0, 'rgba(0,255,135,0.35)');
rankGradient.addColorStop(1, 'rgba(255,60,60,0.08)');

new Chart(rankCtx, {{
    type: 'line',
    data: {{
        labels: gwLabels,
        datasets: [{{
            label: 'World Rank',
            data: ranks,
            borderColor: '#00ff87',
            backgroundColor: rankGradient,
            tension: 0.35,
            fill: true,
            pointRadius: 4,
            pointHoverRadius: 6,
            borderWidth: 2.5
        }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
            legend: legendOpts,
            tooltip: {{
                backgroundColor: 'rgba(30,10,40,0.9)',
                titleColor: 'rgba(255,255,255,0.9)',
                bodyColor: 'rgba(255,255,255,0.75)',
                borderColor: 'rgba(255,255,255,0.15)',
                borderWidth: 1,
                padding: 10,
                callbacks: {{
                    label: function(ctx) {{
                        const v = ctx.raw;
                        if (!v) return 'Rank: —';
                        return 'Rank: ' + v.toLocaleString();
                    }}
                }}
            }}
        }},
        scales: {{
            x: {{
                ticks: {{
                    color: 'rgba(255,255,255,0.75)',
                    maxRotation: 0,
                    minRotation: 0,
                    autoSkip: true,
                    maxTicksLimit: 10,
                    callback: function(val, idx) {{
                        return gwLabels[idx];
                    }}
                }},
                grid: {{ color: 'rgba(255,255,255,0.08)' }},
                afterFit: function(axis) {{ axis.paddingRight = 10; }}
            }},
            y: {{
                reverse: true,
                min: 1,
                ticks: {{
                    color: 'rgba(255,255,255,0.75)',
                    callback: function(v) {{
                        if (v >= 1000000) return (v/1000000).toFixed(1)+'M';
                        if (v >= 1000)    return (v/1000).toFixed(0)+'K';
                        return v;
                    }}
                }},
                grid: {{ color: 'rgba(255,255,255,0.08)' }}
            }}
        }}
    }}
}});
</script>
</body>
</html>
""", height=860, scrolling=False)

_, col, _ = st.columns([1, 1, 1])
with col:
    if st.button("← Back", use_container_width=True):
        st.switch_page("pages/home.py")