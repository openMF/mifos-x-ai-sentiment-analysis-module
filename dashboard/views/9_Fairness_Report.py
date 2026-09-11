import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.auth import render_sidebar_auth, require_role, api_request

st.set_page_config(page_title="Fairness Report", layout="wide")

require_role(["Risk Analyst", "Compliance Officer", "Administrator"])

def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "css", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()

st.markdown("<h2 style='color:#1F4E79;'>⚖️ Regulatory Fairness & Bias Audit</h2>", unsafe_allow_html=True)
st.markdown("Automated auditing to ensure RL models comply with the 4/5ths (80%) rule for Disparate Impact.")

@st.cache_data(ttl=60)
def fetch_fairness_data():
    try:
        response = api_request("GET", "analytics/fairness-audit")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to connect to backend: {e}")
        return None

data = fetch_fairness_data()

if not data or data.get("total_applications", 0) < 10:
    st.warning("Insufficient application data to run a meaningful fairness audit. Showing simulated data for Scenario A (Regional Bias).")
    
    # ─── Simulated Scenario A Data ───────────────────────────
    data = {
        "summary": {
            "gender_female": {"disparate_impact": 0.95, "equal_opportunity_diff": -0.02, "privileged_group": "Male", "unprivileged_group": "Female", "feature": "gender"},
            "region_rural": {"disparate_impact": 0.72, "equal_opportunity_diff": -0.15, "privileged_group": "Urban", "unprivileged_group": "Rural", "feature": "region"},
        },
        "by_model": [
            {"model": "PPO", "feature": "gender", "privileged_group": "Male", "unprivileged_group": "Female", "disparate_impact": 0.94, "equal_opportunity_diff": -0.03, "flagged": False},
            {"model": "PPO", "feature": "region", "privileged_group": "Urban", "unprivileged_group": "Rural", "disparate_impact": 0.72, "equal_opportunity_diff": -0.15, "flagged": True},
            {"model": "DQN", "feature": "region", "privileged_group": "Urban", "unprivileged_group": "Rural", "disparate_impact": 0.88, "equal_opportunity_diff": -0.05, "flagged": False}
        ],
        "flagged_models": [
            {
                "model": "PPO",
                "flagged": True,
                "reason": "Disparate Impact (0.72) below threshold (0.8) for region: Rural",
                "details": {"feature": "region", "disparate_impact": 0.72}
            }
        ],
        "group_rates": {
            "region_rural": {
                "privileged": {"group": "Urban", "favorable_rate": 0.65, "avg_interest_rate": 8.5},
                "unprivileged": {"group": "Rural", "favorable_rate": 0.46, "avg_interest_rate": 13.5}
            }
        }
    }


# ─── Alert Banner ──────────────────────────────────────────
if data.get("flagged_models"):
    st.error("🚨 **FAIRNESS ALERT: Regulatory Threshold Violated**")
    for flag in data["flagged_models"]:
        st.markdown(f"**Model `{flag['model']}` is flagged for retraining.**\n> {flag['reason']}")

st.markdown("---")

# ─── KPI Cards ─────────────────────────────────────────────
summary = data.get("summary", {})
if summary:
    cols = st.columns(len(summary))
    for idx, (key, metrics) in enumerate(summary.items()):
        with cols[idx]:
            di = metrics['disparate_impact']
            eod = metrics['equal_opportunity_diff']
            feature = metrics['feature'].title()
            unpriv = metrics['unprivileged_group']
            
            color = "normal"
            if not pd.isna(di) and di < 0.8:
                color = "inverse"
                
            st.metric(
                label=f"{feature} ({unpriv}) - Disparate Impact",
                value=f"{di:.2f}" if not pd.isna(di) else "N/A",
                delta="Below 0.8 Threshold!" if not pd.isna(di) and di < 0.8 else "Passes 80% Rule",
                delta_color=color
            )
            st.caption(f"Equal Opportunity Diff: {eod:.2f}" if not pd.isna(eod) else "EOD: N/A")

st.markdown("---")

# ─── Visualizations & Tables ───────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Favorable Outcome Rates by Group")
    group_rates = data.get("group_rates", {})
    if group_rates:
        # Prepare data for plotting
        plot_data = []
        for key, rates in group_rates.items():
            priv = rates['privileged']
            unpriv = rates['unprivileged']
            feature = key.split('_')[0].title()
            
            plot_data.append({"Feature": feature, "Group": priv['group'], "Favorable Rate": priv['favorable_rate']})
            plot_data.append({"Feature": feature, "Group": unpriv['group'], "Favorable Rate": unpriv['favorable_rate']})
            
        df_plot = pd.DataFrame(plot_data)
        fig = px.bar(
            df_plot, 
            x="Feature", 
            y="Favorable Rate", 
            color="Group", 
            barmode="group",
            color_discrete_sequence=["#1F4E79", "#5B9BD5", "#A5A5A5", "#ED7D31"]
        )
        fig.update_layout(yaxis_title="Probability of Favorable Outcome")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### Model Breakdown")
    by_model = data.get("by_model", [])
    if by_model:
        df_model = pd.DataFrame(by_model)
        # Highlight flagged rows
        def highlight_flags(s):
            return ['background-color: #ffcccc' if s['flagged'] else '' for v in s]
            
        st.dataframe(
            df_model[['model', 'feature', 'unprivileged_group', 'disparate_impact', 'flagged']]
            .style.apply(highlight_flags, axis=1),
            use_container_width=True,
            hide_index=True
        )

st.markdown("---")
st.markdown("### Audit History")
try:
    history_resp = api_request("GET", "analytics/fairness-audit/history")
    if history_resp.status_code == 200:
        hist_data = history_resp.json()
        if hist_data and hist_data != "NILL":
            df_hist = pd.DataFrame(hist_data)
            st.dataframe(
                df_hist[['timestamp', 'model_name', 'feature', 'group_b', 'disparate_impact', 'flagged']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No historical audit logs found.")
except Exception:
    st.info("History API endpoint not ready or empty.")
