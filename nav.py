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

    nav_cols = st.columns(len(NAV_ITEMS), gap="small")
    for col, (label, path) in zip(nav_cols, NAV_ITEMS):
        with col:
            st.page_link(path, label=label)
