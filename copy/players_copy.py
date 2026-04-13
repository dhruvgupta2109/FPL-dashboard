import streamlit as st # type: ignore
from nav import render_top_nav

st.set_page_config(page_title="FPL Players", layout="wide")

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

.glass-panel {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 14px 34px rgba(0,0,0,0.28);
    color: white;
}

.panel-title {
    font-size: 16px;
    font-weight: 800;
    margin-bottom: 8px;
}

.panel-sub {
    font-size: 13px;
    opacity: 0.8;
}

.kicker {
    text-transform: uppercase;
    letter-spacing: 1.2px;
    font-size: 11px;
    font-weight: 700;
    color: rgba(255,255,255,0.7);
}
</style>
""",
    unsafe_allow_html=True,
)

render_top_nav()

st.markdown("### Players")

left, right = st.columns(2, gap="large")

with left:
    st.markdown(
        """
<div class="glass-panel">
    <div class="kicker">PLAYER RADAR</div>
    <div class="panel-title">Form, minutes, and xGI</div>
    <div class="panel-sub">Planned: rolling xGI, shots on target, and points per 90 overview.</div>
</div>
""",
        unsafe_allow_html=True,
    )

with right:
    st.markdown(
        """
<div class="glass-panel">
    <div class="kicker">VALUE PICKS</div>
    <div class="panel-title">Price-to-output comparison</div>
    <div class="panel-sub">Planned: value tiers by position, ownership, and fixture-adjusted form.</div>
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown(" ")

wide_left, wide_right = st.columns(2, gap="large")

with wide_left:
    st.markdown(
        """
<div class="glass-panel">
    <div class="kicker">PLAYER COMPARISON</div>
    <div class="panel-title">Head-to-head stat cards</div>
    <div class="panel-sub">Planned: compare two players on xG, xA, threat, and minutes trends.</div>
</div>
""",
        unsafe_allow_html=True,
    )

with wide_right:
    st.markdown(
        """
<div class="glass-panel">
    <div class="kicker">MODEL INPUTS</div>
    <div class="panel-title">Feature set for ML scoring</div>
    <div class="panel-sub">Planned: expected points model inputs for next 3-5 gameweeks.</div>
</div>
""",
        unsafe_allow_html=True,
    )
