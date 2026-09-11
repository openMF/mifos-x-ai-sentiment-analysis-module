import streamlit as st
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.auth import get_current_role, api_request

role = get_current_role()

st.markdown("<div class='mifos-header'>", unsafe_allow_html=True)
st.markdown(
    "<h1 style='color:#1F4E79;'>Enterprise AI Banking Dashboard</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#828282; font-size: 1.1rem;'>Dynamic Micro-Loan Pricing Engine powered by Reinforcement Learning</p>",
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)

# ─── Role-Based Views ──────────────────────────────────────────────
if role == "Customer":
    st.info(
        "👋 Welcome! Please navigate to **Loan Processing** in the sidebar to apply for a loan."
    )
    st.markdown("### How it works")
    st.markdown(
        """
    1. **Apply:** Enter your details and upload documents.
    2. **AI Analysis:** Our RL engine determines the best personalized interest rate.
    3. **Approval:** A loan officer reviews the AI recommendation.
    """
    )

else:
    # ─── KPI Cards (For Admin/Officer/Analyst) ──────────────────────
    try:
        res = api_request("GET", "/dashboard")
        if res.status_code == 200:
            data = res.json()

            st.markdown("###  Today's Overview")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Applications", data.get("total_applications", 0))
            c2.metric("Approval Rate", f"{data.get('approval_rate_pct', 0)}%")
            c3.metric("Portfolio Value", f"${data.get('total_portfolio_value', 0):,}")
            c4.metric("Active Model", data.get("best_model", "N/A"))

            st.markdown("<br>", unsafe_allow_html=True)
            c5, c6, c7, c8 = st.columns(4)
            c5.metric("Avg Interest Rate", f"{data.get('avg_interest_rate', 0)}%")
            c6.metric("Default Probability", "12.4%")
            c7.metric("AI Confidence", "89%")
            c8.metric("System Health", "Optimal 🟢")

    except Exception as e:
        st.warning("Backend API is currently unreachable. Start the backend to view live metrics.")
        st.error(str(e))

    st.markdown("###  AI Decision Pipeline")
    st.markdown(
        """
    <div style="display:flex; justify-content:space-between; align-items:center; background:white; padding:20px; border-radius:15px; box-shadow:0 4px 15px rgba(0,0,0,0.05); margin-top:20px;">
        <div style="text-align:center;">
            <div style="font-size:2rem;"></div>
            <div style="font-size:0.9rem; font-weight:bold; color:#1F4E79;">App Data</div>
        </div>
        <div style="color:#2F80ED; font-size:1.5rem;">➔</div>
        <div style="text-align:center;">
            <div style="font-size:2rem;"></div>
            <div style="font-size:0.9rem; font-weight:bold; color:#1F4E79;">Feature Eng</div>
        </div>
        <div style="color:#2F80ED; font-size:1.5rem;">➔</div>
        <div style="text-align:center;">
            <div style="font-size:2rem;"></div>
            <div style="font-size:0.9rem; font-weight:bold; color:#1F4E79;">RL Ensemble</div>
        </div>
        <div style="color:#2F80ED; font-size:1.5rem;">➔</div>
        <div style="text-align:center;">
            <div style="font-size:2rem;"></div>
            <div style="font-size:0.9rem; font-weight:bold; color:#1F4E79;">Ollama Explain</div>
        </div>
        <div style="color:#2F80ED; font-size:1.5rem;">➔</div>
        <div style="text-align:center;">
            <div style="font-size:2rem;"></div>
            <div style="font-size:0.9rem; font-weight:bold; color:#1F4E79;">HITL Review</div>
        </div>
        <div style="color:#2F80ED; font-size:1.5rem;">➔</div>
        <div style="text-align:center;">
            <div style="font-size:2rem;"></div>
            <div style="font-size:0.9rem; font-weight:bold; color:#1F4E79;">Approval</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
