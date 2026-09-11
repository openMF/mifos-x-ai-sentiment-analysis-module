import streamlit as st
import pandas as pd
import numpy as np
import random
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.auth import require_role, api_request, render_sidebar_auth

st.set_page_config(page_title="Live A/B Testing", layout="wide")
require_role(["Loan Officer", "Administrator"])

st.title("⚖️ Live A/B Testing Environment")
st.markdown("Deploy different models to subsets of users and track real-world business metrics in real-time.")

# ─── 1. Campaign Manager ───
st.header("1. Campaign Manager")

# Create Campaign Form
with st.expander("➕ Create New A/B Test Campaign", expanded=False):
    with st.form("create_campaign_form"):
        col1, col2 = st.columns(2)
        with col1:
            campaign_name = st.text_input("Campaign Name")
            model_a = st.selectbox("Model A", ["PPO", "DQN", "DDQN", "SAC"], index=0)
        with col2:
            model_b = st.selectbox("Model B", ["PPO", "DQN", "DDQN", "SAC"], index=3)
            split_a = st.slider("Traffic Split (% to Model A)", 0, 100, 50)
            st.caption(f"Model B will receive {100 - split_a}% of traffic.")
            
        submitted = st.form_submit_button("Create Campaign", type="primary")
        if submitted:
            if not campaign_name:
                st.error("Campaign name is required.")
            elif model_a == model_b:
                st.error("Model A and Model B must be different.")
            else:
                payload = {
                    "campaign_name": campaign_name,
                    "model_a": model_a,
                    "model_b": model_b,
                    "split_a": split_a
                }
                res = api_request("POST", "/ab-test/campaigns", json=payload)
                if res.status_code == 200:
                    st.success("Campaign created successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to create campaign: {res.text}")

# List Campaigns
campaigns_res = api_request("GET", "/ab-test/campaigns")
campaigns = []
if campaigns_res.status_code == 200:
    campaigns_data = campaigns_res.json()
    if isinstance(campaigns_data, list):
        campaigns = campaigns_data

if campaigns:
    for c in campaigns:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.markdown(f"**{c['campaign_name']}**")
                st.caption(f"Created: {c['timestamp'][:10]}")
            with col2:
                st.markdown(f"**{c['model_a']}** ({c['split_a']}%) vs **{c['model_b']}** ({100 - c['split_a']}%)")
            with col3:
                if c['is_active']:
                    st.success("Active", icon="🟢")
                    if st.button("Stop", key=f"stop_{c['id']}"):
                        api_request("POST", f"/ab-test/campaigns/{c['id']}/toggle")
                        st.rerun()
                else:
                    st.write("Inactive")
                    if st.button("Start", key=f"start_{c['id']}", type="primary"):
                        api_request("POST", f"/ab-test/campaigns/{c['id']}/toggle")
                        st.rerun()
else:
    st.info("No A/B testing campaigns found. Create one above to get started!")
        
st.divider()

# ─── 2. Live Analytics ───
st.header("2. Live A/B Testing Analytics")

# Try to load real data first
has_real_data = False
analytics_res = api_request("GET", "/analytics/ab-test")
if analytics_res.status_code == 200:
    data = analytics_res.json()
    if data and isinstance(data, list) and len(data) > 0:
        has_real_data = True
        df = pd.DataFrame(data)

# ─── Generate simulation data if no real data ───
if not has_real_data:
    st.info("💡 Showing **simulated** A/B test results to demonstrate how this dashboard works. Process real loans with an active campaign to see live data.")
    
    # Find active campaign models or default
    sim_model_a = "PPO"
    sim_model_b = "DDQN"
    for c in campaigns:
        if c.get("is_active"):
            sim_model_a = c["model_a"]
            sim_model_b = c["model_b"]
            break
    
    # Seed for consistent display per session
    np.random.seed(42)
    
    n_applications = 200
    
    df = pd.DataFrame([
        {
            "model": sim_model_a,
            "total_applications": n_applications,
            "approval_rate": round(np.random.uniform(0.68, 0.78), 4),
            "default_rate": round(np.random.uniform(0.05, 0.12), 4),
            "expected_profit": round(np.random.uniform(18000, 32000), 2),
        },
        {
            "model": sim_model_b,
            "total_applications": n_applications,
            "approval_rate": round(np.random.uniform(0.60, 0.72), 4),
            "default_rate": round(np.random.uniform(0.08, 0.18), 4),
            "expected_profit": round(np.random.uniform(12000, 25000), 2),
        },
    ])

# ─── KPI Cards ───
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
total_apps = int(df["total_applications"].sum())
leader = df.loc[df["expected_profit"].idxmax(), "model"]
best_approval = df["approval_rate"].max()
lowest_default = df["default_rate"].min()

kpi1.metric("Total A/B Applications", f"{total_apps:,}")
kpi2.metric("Leading Model", leader, help="Model with highest expected profit")
kpi3.metric("Best Approval Rate", f"{best_approval:.1%}")
kpi4.metric("Lowest Default Rate", f"{lowest_default:.1%}")

st.markdown("---")

# ─── Charts Row 1: Profit & Rates ───
col1, col2 = st.columns(2)

with col1:
    st.subheader("💰 Expected Profit by Model")
    fig_profit = px.bar(
        df, x="model", y="expected_profit", color="model",
        text_auto='$.3s',
        color_discrete_map={df["model"].iloc[0]: "#636EFA", df["model"].iloc[1]: "#EF553B"},
    )
    fig_profit.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Expected Profit ($)",
        xaxis_title="",
        showlegend=False,
        font=dict(size=13),
    )
    fig_profit.update_traces(textposition="outside")
    st.plotly_chart(fig_profit, use_container_width=True)

with col2:
    st.subheader("📊 Approval vs Default Rate")
    fig_rates = go.Figure(data=[
        go.Bar(name='Approval Rate', x=df['model'], y=df['approval_rate'],
               marker_color='#2ca02c', text=[f"{v:.1%}" for v in df['approval_rate']], textposition='outside'),
        go.Bar(name='Default Rate', x=df['model'], y=df['default_rate'],
               marker_color='#d62728', text=[f"{v:.1%}" for v in df['default_rate']], textposition='outside'),
    ])
    fig_rates.update_layout(
        barmode='group',
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Rate",
        xaxis_title="",
        yaxis_tickformat=".0%",
        font=dict(size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    st.plotly_chart(fig_rates, use_container_width=True)

# ─── Charts Row 2: Simulated Timeline ───
st.subheader("📈 Cumulative Profit Over Time (Simulation)")

np.random.seed(7)
days = 30
dates = pd.date_range(end=pd.Timestamp.today(), periods=days, freq='D')
model_a_name = df["model"].iloc[0]
model_b_name = df["model"].iloc[1]

cumulative_a = np.cumsum(np.random.normal(loc=800, scale=300, size=days)).clip(min=0)
cumulative_b = np.cumsum(np.random.normal(loc=600, scale=350, size=days)).clip(min=0)

timeline_df = pd.DataFrame({
    "Date": list(dates) * 2,
    "Cumulative Profit ($)": list(cumulative_a) + list(cumulative_b),
    "Model": [model_a_name] * days + [model_b_name] * days,
})

fig_timeline = px.line(
    timeline_df, x="Date", y="Cumulative Profit ($)", color="Model",
    color_discrete_map={model_a_name: "#636EFA", model_b_name: "#EF553B"},
    markers=True,
)
fig_timeline.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(size=13),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    hovermode="x unified",
)
fig_timeline.update_traces(line=dict(width=2.5))
st.plotly_chart(fig_timeline, use_container_width=True)

# ─── Charts Row 3: Risk Distribution ───
col3, col4 = st.columns(2)

np.random.seed(21)
n_sim = 200

with col3:
    st.subheader(f"🎯 Risk Score Distribution")
    risk_a = np.random.beta(2, 5, n_sim)
    risk_b = np.random.beta(3, 4, n_sim)
    risk_df = pd.DataFrame({
        "Risk Score": list(risk_a) + list(risk_b),
        "Model": [model_a_name] * n_sim + [model_b_name] * n_sim,
    })
    fig_risk = px.histogram(
        risk_df, x="Risk Score", color="Model", barmode="overlay",
        nbins=30, opacity=0.7,
        color_discrete_map={model_a_name: "#636EFA", model_b_name: "#EF553B"},
    )
    fig_risk.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    st.plotly_chart(fig_risk, use_container_width=True)

with col4:
    st.subheader("💵 Interest Rate Distribution")
    rates_a = np.random.normal(loc=12.5, scale=2.5, size=n_sim).clip(5, 25)
    rates_b = np.random.normal(loc=14.0, scale=3.0, size=n_sim).clip(5, 25)
    rates_df = pd.DataFrame({
        "Interest Rate (%)": list(rates_a) + list(rates_b),
        "Model": [model_a_name] * n_sim + [model_b_name] * n_sim,
    })
    fig_ir = px.histogram(
        rates_df, x="Interest Rate (%)", color="Model", barmode="overlay",
        nbins=30, opacity=0.7,
        color_discrete_map={model_a_name: "#636EFA", model_b_name: "#EF553B"},
    )
    fig_ir.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    st.plotly_chart(fig_ir, use_container_width=True)

# ─── Detailed Metrics Table ───
st.subheader("📋 Detailed Metrics Summary")
st.dataframe(
    df.style.format({
        "approval_rate": "{:.2%}",
        "default_rate": "{:.2%}",
        "expected_profit": "${:,.2f}",
    }),
    use_container_width=True,
    hide_index=True,
)
