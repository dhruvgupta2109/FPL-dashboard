import streamlit as st
from nav import render_top_nav

st.set_page_config(page_title="FPL Teams", layout="wide")

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

st.markdown("### Teams")

left, right = st.columns(2, gap="large")

with left:
    st.markdown(
        """
<div class="glass-panel">
    <div class="kicker">TEAM SNAPSHOT</div>
    <div class="panel-title">Form, xG, and fixture difficulty</div>
    <div class="panel-sub">Planned: rolling 5-match form, xG trend lines, and easy/hard run indicators.</div>
</div>
""",
        unsafe_allow_html=True,
    )

with right:
    st.markdown(
        """
<div class="glass-panel">
    <div class="kicker">TEAM COMPARISON</div>
    <div class="panel-title">Head-to-head stats and strengths</div>
    <div class="panel-sub">Planned: compare two teams on chance creation, clean sheet odds, and set-piece threat.</div>
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
    <div class="kicker">PREDICTION INPUTS</div>
    <div class="panel-title">Feature set preview</div>
    <div class="panel-sub">Planned: opponent strength, days of rest, home/away split, and recent minutes.</div>
</div>
""",
        unsafe_allow_html=True,
    )

with wide_right:
    st.markdown(
        """
<div class="glass-panel">
    <div class="kicker">MODEL READY</div>
    <div class="panel-title">Team forecast sandbox</div>
    <div class="panel-sub">Hook up your ML model here to project goals, clean sheets, and match difficulty.</div>
</div>
""",
        unsafe_allow_html=True,
    )
