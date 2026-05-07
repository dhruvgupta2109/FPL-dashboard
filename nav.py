import streamlit as st

NAV_ITEMS = [
    ("Home", "pages/home.py"),
    ("Teams", "pages/teams.py"),
    ("Players", "pages/players.py"),
    ("Points", "pages/points.py"),
    ("Fixtures", "pages/fixtures.py"),
    ("Graphs", "pages/graphs.py"),
    ("Leagues", "pages/leagues.py"),
    ("Models", "pages/models.py"),
]


THEMES = {
    False: {
        "page_bg": "linear-gradient(135deg, #37003c, #2b1e5b, #00cc6a)",
        "nav_bg": "rgba(14, 10, 28, 0.55)",
        "panel_bg": "rgba(255,255,255,0.12)",
        "panel_bg_strong": "rgba(255,255,255,0.15)",
        "panel_border": "rgba(255,255,255,0.20)",
        "soft_bg": "rgba(255,255,255,0.10)",
        "button_bg": "rgba(255,255,255,0.12)",
        "button_hover": "rgba(255,255,255,0.22)",
        "text": "#ffffff",
        "text_muted": "rgba(255,255,255,0.78)",
        "shadow": "0 14px 34px rgba(0,0,0,0.28)",
    },
    True: {
        "page_bg": (
            "radial-gradient(circle at 16% 12%, rgba(0,255,135,0.15), transparent 28%), "
            "radial-gradient(circle at 84% 10%, rgba(116,245,192,0.10), transparent 24%), "
            "linear-gradient(135deg, #120018 0%, #17102e 48%, #04170f 100%)"
        ),
        "nav_bg": "rgba(7, 5, 16, 0.78)",
        "panel_bg": "rgba(8, 7, 18, 0.58)",
        "panel_bg_strong": "rgba(11, 8, 24, 0.72)",
        "panel_border": "rgba(116,245,192,0.20)",
        "soft_bg": "rgba(255,255,255,0.07)",
        "button_bg": "rgba(255,255,255,0.09)",
        "button_hover": "rgba(0,255,135,0.16)",
        "text": "#f8fff9",
        "text_muted": "rgba(248,255,249,0.76)",
        "shadow": "0 18px 42px rgba(0,0,0,0.44)",
    },
}


def theme_is_dark():
    return bool(st.session_state.get("dark_mode", False))


def render_theme_styles():
    theme = THEMES[theme_is_dark()]
    st.markdown(
        f"""
<style>
.stApp {{
    --fpl-page-bg: {theme["page_bg"]};
    --fpl-nav-bg: {theme["nav_bg"]};
    --fpl-panel-bg: {theme["panel_bg"]};
    --fpl-panel-bg-strong: {theme["panel_bg_strong"]};
    --fpl-panel-border: {theme["panel_border"]};
    --fpl-soft-bg: {theme["soft_bg"]};
    --fpl-button-bg: {theme["button_bg"]};
    --fpl-button-hover: {theme["button_hover"]};
    --fpl-text: {theme["text"]};
    --fpl-text-muted: {theme["text_muted"]};
    --fpl-shadow: {theme["shadow"]};
    background: var(--fpl-page-bg) !important;
    min-height: 100vh;
}}

.stMainBlockContainer {{
    max-width: none !important;
}}

h1, h2, h3, p, div, span, li, label {{
    color: var(--fpl-text) !important;
}}

.glass-box,
.glass-panel,
.points-box,
.leagues-box,
.matches-box,
.matches-header-box,
.matches-body-box,
.match-hero,
.player-chip,
.metric-card,
.data-row,
.mini-chart,
.profile-panel,
.mini-player-card,
.center-box,
.comp-head,
.comp-label,
.comp-cell,
div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stExpander"] {{
    background: var(--fpl-panel-bg) !important;
    border-color: var(--fpl-panel-border) !important;
    box-shadow: var(--fpl-shadow) !important;
}}

div[data-testid="stMetric"] {{
    background: var(--fpl-soft-bg) !important;
    border: 1px solid var(--fpl-panel-border) !important;
    border-radius: 12px !important;
    padding: 10px !important;
}}

div[data-testid="stButton"] > button,
div[data-baseweb="select"] > div,
div[role="radiogroup"] label {{
    background: var(--fpl-button-bg) !important;
    border-color: var(--fpl-panel-border) !important;
    color: var(--fpl-text) !important;
}}

div[data-testid="stButton"] > button:hover {{
    background: var(--fpl-button-hover) !important;
    color: var(--fpl-text) !important;
}}

.panel-sub,
.team-meta,
.metric-note,
.fixture-meta,
.fixture-date,
.chip-meta,
.empty-note,
.empty-stat,
.page-caption,
.profile-meta,
.profile-news,
.mini-player-meta,
.mini-stat-row {{
    color: var(--fpl-text-muted) !important;
}}

div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPageLink"]) {{
    background: var(--fpl-nav-bg) !important;
    border-color: var(--fpl-panel-border) !important;
}}

div[data-testid="stToggle"] {{
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    min-height: 36px !important;
}}

div[data-testid="stToggle"] label {{
    gap: 6px !important;
    margin: 0 !important;
    font-size: 12px !important;
    font-weight: 800 !important;
    color: var(--fpl-text) !important;
}}
</style>
""",
        unsafe_allow_html=True,
    )


def render_top_nav():
    st.markdown(
        """
<style>
/* Top nav row */
div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPageLink"]) {
    margin: 0 0 14px 0 !important;
    padding: 8px 10px !important;
    gap: 10px !important;
    border-radius: 18px !important;
    background: rgba(14, 10, 28, 0.55) !important;
    border: 1px solid rgba(255,255,255,0.18) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
}

div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPageLink"]) > div[data-testid="stColumn"] {
    padding: 0 !important;
}

div[data-testid="stPageLink"] > a {
    display: block !important;
    text-align: center !important;
    padding: 8px 12px !important;
    border-radius: 999px !important;
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.16) !important;
    color: rgba(255,255,255,0.85) !important;
    font-size: 12.5px !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px !important;
    text-decoration: none !important;
    transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease !important;
}

div[data-testid="stPageLink"] > a:hover {
    background: rgba(255,255,255,0.16) !important;
    color: #ffffff !important;
    border-color: rgba(255,255,255,0.4) !important;
}

div[data-testid="stPageLink"] > a[aria-current="page"] {
    color: #0b1a13 !important;
    background: linear-gradient(135deg, #00ff87, #74f5c0) !important;
    border-color: rgba(0,255,135,0.65) !important;
}

@media (max-width: 768px) {
    div[data-testid="stHorizontalBlock"]:has(div[data-testid="stPageLink"]) {
        padding: 8px 8px !important;
        gap: 6px !important;
        border-radius: 14px !important;
    }

    div[data-testid="stPageLink"] > a {
        font-size: 11.5px !important;
        padding: 7px 9px !important;
    }
}
</style>
""",
        unsafe_allow_html=True,
    )

    render_theme_styles()

    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = False

    nav_cols = st.columns([1] * len(NAV_ITEMS) + [0.85], gap="small")
    for col, (label, path) in zip(nav_cols[:-1], NAV_ITEMS):
        with col:
            st.page_link(path, label=label)

    with nav_cols[-1]:
        st.toggle("Dark", key="dark_mode")
