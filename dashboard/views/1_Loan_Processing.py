import streamlit as st
import requests
import time
import os
import sys
import plotly.graph_objects as go

# Ensure the parent directory is in the python path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.auth import render_sidebar_auth, get_current_role, api_request, require_role

st.set_page_config(page_title="Loan Processing", layout="wide")

require_role(["Customer", "Loan Officer", "Risk Analyst", "Administrator"])

def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "css", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()

API_URL = "http://127.0.0.1:8000/api"

st.sidebar.markdown("### 🏦 **MIFOS X** AI Platform")
role = get_current_role()

if role not in ["Customer", "Loan Officer", "Administrator"]:
    st.error("Access Denied. You do not have permission to submit loan applications.")
    st.stop()

st.markdown("<h2 style='color:#1F4E79;'> Loan Origination & Processing</h2>", unsafe_allow_html=True)

if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None
if "current_payload" not in st.session_state:
    st.session_state.current_payload = None

# ─── Form Inputs ──────────────────────────────────────────
with st.form("loan_application_form"):
    st.markdown("### 👤 Applicant Profile")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        age = st.number_input("Age", min_value=18, max_value=100, value=30)
        gender = st.selectbox("Gender", ["Male", "Female"])
        education = st.selectbox("Education Level", ["High School", "Bachelor's", "Master's", "PhD"])
    with col2:
        employment = st.selectbox("Employment Status", ["Salaried", "Self-Employed", "Unemployed"])
        income = st.number_input("Monthly Income ($)", min_value=0, value=5000, step=500)
        region = st.selectbox("Region", ["Urban", "Semiurban", "Rural"])
    with col3:
        credit_score = st.number_input("Credit Score (0.0 - 1.0)", min_value=0.0, max_value=1.0, value=0.7, step=0.05)
        existing_debt = st.number_input("Existing Debt ($)", min_value=0, value=1000, step=100)
        existing_loans = st.number_input("Active Loans Count", min_value=0, value=1)
    with col4:
        loan_amount = st.number_input("Requested Loan Amount ($)", min_value=100, value=10000, step=500)
        loan_tenure = st.number_input("Loan Tenure (Months)", min_value=1, max_value=360, value=24)
        loan_purpose = st.selectbox("Loan Purpose", ["Personal", "Business", "Education", "Home"])
        collateral = st.selectbox("Collateral Offered", ["None", "Vehicle", "Property", "Gold"])
        repayment_history = st.number_input("Repayment History (0.0 - 1.0)", min_value=0.0, max_value=1.0, value=0.8, step=0.05)

    st.markdown("### 💬 Alternative Data")
    interview_notes = st.text_area("Loan Officer Interview Notes (Optional)", help="Sentiment analysis will be run on these notes to calculate a Behavioral Reliability Score.")

    submitted = st.form_submit_button("🚀 Submit to AI Engine")

def fetch_prediction(payload):
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.markdown("####  Validating Applicant Data...")
    progress_bar.progress(20)
    time.sleep(0.5)
    status_text.markdown("####  Running Feature Engineering & Sentiment Analysis...")
    progress_bar.progress(40)
    time.sleep(0.5)
    status_text.markdown("####  RL Ensemble Inference (PPO, DQN, DDQN, SAC)...")
    progress_bar.progress(70)
    
    try:
        response = api_request("POST", "predict", json=payload)
        status_text.markdown("#### 🦙 Generating AI Explanations...")
        progress_bar.progress(90)
        time.sleep(0.5)
        
        if response.status_code == 200:
            progress_bar.progress(100)
            status_text.empty()
            progress_bar.empty()
            return response.json()
        elif response.status_code == 401:
            status_text.error("🔒 Your login session has expired. Please click 'Logout' in the sidebar and log back in.")
            return None
        else:
            status_text.error(f"API Error: {response.text}")
            return None
    except Exception as e:
        status_text.error(f"Could not connect to the Backend API. Make sure it is running. Error: {e}")
        return None

if submitted:
    st.markdown("---")
    payload = {
        "age": age, "gender": gender, "employment": employment, "income": income,
        "credit_score": credit_score, "loan_amount": loan_amount, "existing_debt": existing_debt,
        "loan_tenure": loan_tenure, "repayment_history": repayment_history, "loan_purpose": loan_purpose,
        "region": region, "collateral": collateral, "existing_loans": existing_loans, "education": education,
        "interview_notes": interview_notes if interview_notes else None
    }
    st.session_state.current_payload = payload
    result = fetch_prediction(payload)
    if result:
        st.session_state.prediction_result = result
        st.session_state.success_message = "✅ Application successfully processed by the AI Engine."

if st.session_state.get("success_message"):
    st.success(st.session_state.success_message)
    # Clear it so it doesn't stay forever unless we just set it
    st.session_state.success_message = None

if st.session_state.prediction_result:
    result = st.session_state.prediction_result
    rec = result.get('recommended_pricing', {})
    risk = result.get('risk_analysis', {})
    rate = rec.get('recommended_interest_rate')
    best_model = rec.get('best_model')
    conf = risk.get('confidence', 0)
    beh_score = risk.get('behavioral_score')
    
    status_color = "#27AE60" if rate else "#E74C3C"
    decision_text = f"APPROVED @ {rate}%" if rate else "REJECTED"
    
    st.markdown(f"""
    <div style="background:white; padding:30px; border-radius:15px; box-shadow:0 4px 20px rgba(0,0,0,0.08); text-align:center; border-top: 5px solid {status_color};">
        <h3 style="color:#828282; margin:0;">AI Recommendation</h3>
        <h1 style="color:{status_color}; font-size:3.5rem; margin:10px 0;">{decision_text}</h1>
        <p style="font-size:1.1rem; color:#4F4F4F;">Confidence Score: <b>{round(conf*100, 1)}%</b> &nbsp;|&nbsp; Primary Engine: <b>{best_model}</b></p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ─── Feature 1: XAI Explanations ───
    st.markdown("### 🦙 AI-Generated Rationale")
    explanation = result.get("ollama_explanation", {})
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        st.info(f"**Customer-Friendly Explanation:**\n\n{explanation.get('customer_friendly_explanation', 'N/A')}")
    with col_exp2:
        st.warning(f"**Officer Technical Explanation:**\n\n{explanation.get('officer_technical_explanation', 'N/A')}")
        
    st.markdown("---")
    
    # ─── Feature 3 & Breakdown ───
    col_l, col_r = st.columns([1, 1])
    with col_l:
        st.markdown("### 🔍 Risk Analysis")
        r1, r2, r3 = st.columns(3)
        r1.metric("Calculated Risk Score", risk.get('risk_score', 'N/A'))
        r2.metric("Risk Level", risk.get('risk_level', 'N/A'))
        r3.metric("Expected Profit", f"${rec.get('expected_profit', 0)}")
        
        if beh_score is not None and beh_score != "NILL":
            st.metric("Behavioral Score (NLP)", round(float(beh_score), 2), help="0 to 1 based on sentiment of notes.")
        
        st.markdown("### 📊 Ensemble Breakdown")
        rl = result.get('rl_predictions', {})
        st.write(f"**PPO**: {rl.get('PPO')} | **DQN**: {rl.get('DQN')} | **DDQN**: {rl.get('DDQN')} | **SAC**: {rl.get('SAC')}")
        
    with col_r:
        st.markdown("### 🕸️ Peer Benchmarking")
        # Feature 5: Radar Chart
        categories = ['Credit Score', 'Repayment History', 'Income Level (Norm)', 'Debt Ratio (Inv)']
        
        # Normalize applicant values for chart (0 to 1)
        app_credit = st.session_state.current_payload['credit_score']
        app_repayment = st.session_state.current_payload['repayment_history']
        app_income_norm = min(st.session_state.current_payload['income'] / 10000, 1.0)
        app_debt_ratio_inv = max(0, 1.0 - (st.session_state.current_payload['existing_debt'] / max(st.session_state.current_payload['income'], 1)))
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=[0.75, 0.8, 0.5, 0.7],
            theta=categories,
            fill='toself',
            name='Avg Approved Applicant'
        ))
        fig.add_trace(go.Scatterpolar(
            r=[app_credit, app_repayment, app_income_norm, app_debt_ratio_inv],
            theta=categories,
            fill='toself',
            name='Current Applicant'
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), showlegend=True, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    
    # ─── Feature 4: Interactive Negotiation Mode ───
    st.markdown("### 🎚️ Interactive Negotiation Mode")
    st.markdown("Adjust key variables to instantly see how it affects the AI decision.")
    
    # We use a form here so that changing the slider doesn't instantly rerun the whole page
    # and collapse or reset things before they click "Re-Evaluate".
    with st.form("negotiation_form"):
        c_neg1, c_neg2, c_neg3 = st.columns(3)
        new_amt = c_neg1.slider("Modify Loan Amount", 100, 50000, int(st.session_state.current_payload['loan_amount']), 500)
        new_ten = c_neg2.slider("Modify Loan Tenure (Months)", 1, 360, int(st.session_state.current_payload['loan_tenure']), 1)
        new_debt = c_neg3.slider("Modify Existing Debt", 0, 50000, int(st.session_state.current_payload['existing_debt']), 500)
        
        reval_submitted = st.form_submit_button("🔄 Re-Evaluate Application")
        
        if reval_submitted:
            mod_payload = st.session_state.current_payload.copy()
            mod_payload['loan_amount'] = new_amt
            mod_payload['loan_tenure'] = new_ten
            mod_payload['existing_debt'] = new_debt
            st.session_state.current_payload = mod_payload
            new_res = fetch_prediction(mod_payload)
            if new_res:
                st.session_state.prediction_result = new_res
                st.rerun()
                
    st.markdown("---")
    
    # ─── Feature 6: Push to Core System ───
    st.markdown("### 🚀 Finalize Decision")
    with st.form("push_to_core"):
        final_remarks = st.text_input("Officer Remarks (Required for final decision)")
        c_app, c_rej = st.columns(2)
        submit_decision = st.form_submit_button("Submit to Core System")
        
        if submit_decision:
            if not final_remarks:
                st.error("Please provide officer remarks before submitting.")
            else:
                decision_payload = {
                    "application_id": result['application_id'],
                    "officer_name": st.session_state.get("username", "Unknown Officer"),
                    "remarks": final_remarks,
                    "approved": rate is not None,
                    "rejected": rate is None
                }
                res = api_request("POST", "loan-decisions", json=decision_payload)
                if res.status_code == 200:
                    st.session_state.success_message = "🎉 Application finalized and pushed to Core System successfully!"
                    st.session_state.prediction_result = None # Reset
                    st.rerun()
                elif res.status_code == 401:
                    st.error("🔒 Your login session has expired. Please click 'Logout' in the sidebar and log back in.")
                else:
                    st.error(f"Failed to push to core: {res.text}")
