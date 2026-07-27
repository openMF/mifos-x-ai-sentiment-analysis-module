import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.auth import render_sidebar_auth, get_current_role, api_request, require_role

st.set_page_config(page_title="Enterprise Analytics", page_icon="📈", layout="wide")

render_sidebar_auth()
require_role(["Administrator", "Loan Officer", "Risk Analyst"])

def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "css", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()

st.sidebar.markdown("### 🏦 **MIFOS X** AI Platform")
role = get_current_role()

if role not in ["Risk Analyst", "Administrator"]:
    st.error("Access Denied. Only Risk Analysts and Administrators can view Analytics.")
    st.stop()

st.markdown("<h2 style='color:#1F4E79;'>📈 Enterprise Portfolio Analytics</h2>", unsafe_allow_html=True)

try:
    with st.spinner("Fetching live portfolio data..."):
        apps_res = api_request("GET", "applications")
        
    if apps_res.status_code == 200 and apps_res.json() != "NILL":
        raw_data = apps_res.json()
        
        if not raw_data:
            st.info("No applications found in the database.")
            st.stop()
            
        # Flatten the nested dictionary
        flat_data = []
        for app in raw_data:
            item = app.copy()
            pred = item.pop("prediction", {})
            dec = item.pop("decision", {})
            
            if not isinstance(pred, dict):
                pred = {}
            if not isinstance(dec, dict):
                dec = {}
            
            item["best_model"] = pred.get("best_model", "Unknown")
            item["recommended_rate"] = pred.get("recommended_rate", None)
            item["risk_score"] = pred.get("risk_score", None)
            
            # Map boolean to string for better legend in Plotly
            approved_status = dec.get("approved")
            if approved_status is True:
                item["Status"] = "Approved"
            elif approved_status is False:
                item["Status"] = "Rejected"
            else:
                item["Status"] = "Pending"
                
            flat_data.append(item)
            
        df = pd.DataFrame(flat_data)
        
        # Clean "NILL" strings from numeric columns
        numeric_cols = ["recommended_rate", "risk_score", "loan_amount", "income"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # --- 1. Top-Level KPIs ---
        total_apps = len(df)
        approved_count = len(df[df["Status"] == "Approved"])
        approval_rate = (approved_count / total_apps * 100) if total_apps > 0 else 0
        avg_rate = df["recommended_rate"].mean()
        avg_risk = df["risk_score"].mean()
        
        st.markdown("### Key Performance Indicators")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Applications", total_apps)
        k2.metric("Overall Approval Rate", f"{approval_rate:.1f}%")
        k3.metric("Avg Recommended Rate", f"{avg_rate:.2f}%" if pd.notnull(avg_rate) else "N/A")
        k4.metric("Avg Portfolio Risk", f"{avg_risk:.2f}" if pd.notnull(avg_risk) else "N/A")
        
        st.divider()
        
        # --- 2. Risk & Portfolio Analytics ---
        st.markdown("### Risk & Portfolio Analysis")
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("**1. Risk Score Distribution**")
            if df["risk_score"].notnull().any():
                fig1 = px.histogram(df, x="risk_score", nbins=15, color_discrete_sequence=['#ef4444'], template="plotly_dark")
                fig1.update_layout(xaxis_title="AI Risk Score (Lower is Better)")
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.info("No risk score data available.")
                
        with c2:
            st.markdown("**2. Risk vs. Loan Amount (By Status)**")
            if df["risk_score"].notnull().any() and df["loan_amount"].notnull().any():
                color_map = {"Approved": "#22c55e", "Rejected": "#ef4444", "Pending": "#94a3b8"}
                fig2 = px.scatter(df, x="loan_amount", y="risk_score", color="Status", color_discrete_map=color_map, template="plotly_dark", size="income", hover_data=["age", "employment"])
                fig2.update_layout(xaxis_title="Requested Loan Amount", yaxis_title="Risk Score")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Insufficient data for Scatter plot.")
                
        # --- 3. Demographic & Business Analytics ---
        st.markdown("### Demographic Insights")
        c3, c4 = st.columns(2)
        
        with c3:
            st.markdown("**3. Application Volume by Region**")
            if "region" in df.columns:
                fig3 = px.pie(df, names="region", hole=0.4, template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("No region data.")
                
        with c4:
            st.markdown("**4. Loan Purposes Breakdown**")
            if "loan_purpose" in df.columns:
                fig4 = px.histogram(df, x="loan_purpose", color="Status", template="plotly_dark", barmode="group", color_discrete_map=color_map)
                fig4.update_layout(xaxis_title="Loan Purpose", yaxis_title="Count")
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("No loan purpose data.")
                
        # --- 4. AI Insights ---
        st.markdown("### Artificial Intelligence Telemetry")
        c5, c6 = st.columns(2)
        
        with c5:
            st.markdown("**5. AI Ensemble Model Preferences**")
            if "best_model" in df.columns:
                # Filter out None/Unknown
                valid_models = df[df["best_model"] != "Unknown"]
                if not valid_models.empty:
                    fig5 = px.pie(valid_models, names="best_model", template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Bold)
                    st.plotly_chart(fig5, use_container_width=True)
                else:
                    st.info("No ensemble model preferences recorded yet.")
                    
        with c6:
            st.markdown("**6. Income Distribution of Applicants**")
            if "income" in df.columns:
                fig6 = px.box(df, x="Status", y="income", color="Status", template="plotly_dark", color_discrete_map=color_map)
                st.plotly_chart(fig6, use_container_width=True)

    else:
        st.info("Not enough data to generate analytics. Please process some applications first.")
except Exception as e:
    st.error(f"Failed to load analytics: {e}")

