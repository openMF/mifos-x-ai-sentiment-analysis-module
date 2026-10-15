import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.auth import render_sidebar_auth, get_current_role, api_request, require_role

st.set_page_config(page_title="What-If Simulator", layout="wide")

require_role(["Loan Officer", "Risk Analyst", "Administrator"])

def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "css", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()

API_URL = "http://127.0.0.1:8000/api"

st.sidebar.markdown("### 🏦 **MIFOS X** AI Platform")
role = get_current_role()

if role not in ["Risk Analyst", "Administrator", "Loan Officer"]:
    st.error("Access Denied. Simulator is for internal staff only.")
    st.stop()

st.markdown("<h2 style='color:#1F4E79;'>🎛️ AI What-If Simulator</h2>", unsafe_allow_html=True)
st.markdown("Adjust the sliders below to see how the RL Ensemble's prediction changes in real-time.")

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🔧 Applicant Variables")
    age = st.slider("Age", 18, 100, 30)
    income = st.slider("Monthly Income ($)", 0, 20000, 5000, step=500)
    credit_score = st.slider("Credit Score (0.0 - 1.0)", 0.0, 1.0, 0.7, step=0.01)
    loan_amount = st.slider("Loan Amount ($)", 500, 50000, 10000, step=500)
    existing_debt = st.slider("Existing Debt ($)", 0, 20000, 1000, step=500)
    repayment_history = st.slider("Repayment History", 0.0, 1.0, 0.8, step=0.01)
    
    # Static defaults for simulation
    payload = {
        "age": age,
        "gender": "Male",
        "employment": "Salaried",
        "income": income,
        "credit_score": credit_score,
        "loan_amount": loan_amount,
        "existing_debt": existing_debt,
        "loan_tenure": 24,
        "repayment_history": repayment_history,
        "loan_purpose": "Personal",
        "region": "Urban",
        "collateral": "None",
        "existing_loans": 0,
        "education": "Bachelor's"
    }

with col2:
    st.markdown("### 📈 Live RL Inference")
    try:
        response = api_request("POST", "predict", json=payload)
        if response.status_code == 200:
            result = response.json()
            rec = result.get('recommended_pricing', {})
            risk = result.get('risk_analysis', {})
            rl = result.get('rl_predictions', {})
            
            rate = rec.get('recommended_interest_rate')
            decision = f"Approve @ {rate}%" if rate else "Reject"
            color = "#27AE60" if rate else "#E74C3C"
            
            st.markdown(f"""
            <div style="background:white; padding:20px; border-radius:15px; box-shadow:0 4px 15px rgba(0,0,0,0.05); text-align:center; border-top: 4px solid {color}; margin-bottom: 20px;">
                <h4 style="color:#828282; margin:0;">Ensemble Recommendation</h4>
                <h2 style="color:{color}; margin:10px 0;">{decision}</h2>
                <p>Risk Score: <b>{risk.get('risk_score')}</b> | Confidence: <b>{round(risk.get('confidence', 0)*100, 1)}%</b></p>
            </div>
            """, unsafe_allow_html=True)
            
            # Chart comparing the 4 models
            rates = []
            for k, v in rl.items():
                if "Approve" in str(v):
                    # Extract number from string like "Approve @ 12.0%"
                    try:
                        val = float(str(v).split("@")[1].replace("%", "").strip())
                        rates.append({"Model": k, "Rate": val})
                    except:
                        rates.append({"Model": k, "Rate": 0})
                else:
                    rates.append({"Model": k, "Rate": 0})
                    
            df = pd.DataFrame(rates)
            fig = px.bar(df, x="Model", y="Rate", title="Interest Rate by Model", 
                         color="Model", color_discrete_sequence=['#1F4E79', '#2F80ED', '#56CCF2', '#27AE60'])
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.error("API Error")
    except Exception as e:
        st.error(f"Cannot reach backend: {e}")
