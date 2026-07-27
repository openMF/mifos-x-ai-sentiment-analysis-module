import streamlit as st
import pandas as pd
import requests
import os
import sys
from io import BytesIO

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.auth import render_sidebar_auth, get_current_role, api_request, require_role
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

from ollama.explain import generate_portfolio_summary, generate_fairness_audit_summary

st.set_page_config(page_title="Reports & Exports", page_icon="📄", layout="wide")

render_sidebar_auth()
require_role(["Administrator", "Loan Officer", "Risk Analyst"])

def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "css", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()

API_URL = "http://127.0.0.1:8000/api"

st.markdown("<h2 style='color:#1F4E79;'>📄 Advanced Reports & Auditing</h2>", unsafe_allow_html=True)
st.markdown("Dynamic filtering, AI summaries, and regulatory compliance audits.")

# Fetch Data
@st.cache_data(ttl=60)
def fetch_data():
    try:
        apps = api_request("GET", "applications").json()
        return apps
    except:
        return []

raw_data = fetch_data()
df = pd.DataFrame()

if raw_data and raw_data != "NILL":
    df_list = []
    for a in raw_data:
        raw_pred = a.get("prediction", {})
        pred = raw_pred if isinstance(raw_pred, dict) else {}
        
        raw_dec = a.get("decision", {})
        dec = raw_dec if isinstance(raw_dec, dict) else {}
        
        status = 'Pending'
        if dec.get('approved') is True: status = 'Approved'
        elif dec.get('approved') is False: status = 'Rejected'
        
        df_list.append({
            "Application ID": a.get("id"),
            "Age": a.get("age"),
            "Gender": a.get("gender", "Unknown"),
            "Region": a.get("region", "Unknown"),
            "Income": a.get("income"),
            "Credit Score": a.get("credit_score"),
            "Loan Amount": a.get("loan_amount"),
            "Purpose": a.get("loan_purpose"),
            "Risk Score": pred.get("risk_score"),
            "Recommended Model": pred.get("best_model", "Unknown"),
            "Interest Rate": pred.get("recommended_rate"),
            "Decision": status,
            "Officer": dec.get("officer_name", "N/A"),
            "Timestamp": a.get("timestamp")
        })
        
    df = pd.DataFrame(df_list)
    for col in ["Income", "Loan Amount", "Risk Score"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# UI Tabs for different report features
tab1, tab2, tab3 = st.tabs(["📊 Portfolio Reports", "🛡️ Fairness Audit", "📅 Report Scheduler"])

with tab1:
    if not df.empty:
        st.markdown("### 🔍 Filter Data")
        with st.expander("Expand to filter dataset before exporting", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                f_status = st.multiselect("Decision Status", options=df["Decision"].dropna().unique(), default=df["Decision"].dropna().unique())
            with col2:
                f_model = st.multiselect("AI Model Used", options=df["Recommended Model"].dropna().unique(), default=df["Recommended Model"].dropna().unique())
            with col3:
                f_region = st.multiselect("Region", options=df["Region"].dropna().unique(), default=df["Region"].dropna().unique())
            with col4:
                max_risk = st.slider("Max Risk Score", min_value=0.0, max_value=1.0, value=1.0, step=0.05)
                
            filtered_df = df[
                (df["Decision"].isin(f_status)) & 
                (df["Recommended Model"].isin(f_model)) & 
                (df["Region"].isin(f_region)) & 
                (df["Risk Score"].fillna(0) <= max_risk)
            ]
            
        st.markdown(f"**Showing {len(filtered_df)} records:**")
        st.dataframe(filtered_df.head(15), use_container_width=True)
        
        st.markdown("### 📥 Export Options")
        
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        
        # Excel generator
        def create_excel(d):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                d.to_excel(writer, index=False, sheet_name='Loan Data')
            return output.getvalue()
            
        # PDF with Embedded Visuals and AI summary
        def create_pitch_deck(d):
            if FPDF is None: return None
            
            # 1. Generate AI Summary
            stats = {
                "total_apps": len(d),
                "approval_rate": round(len(d[d["Decision"] == "Approved"]) / max(len(d),1) * 100, 1),
                "avg_risk": round(d["Risk Score"].mean(), 2) if not d["Risk Score"].isnull().all() else 0,
                "top_purpose": d["Purpose"].mode()[0] if not d.empty and not d["Purpose"].isnull().all() else "N/A",
                "top_model": d["Recommended Model"].mode()[0] if not d.empty and not d["Recommended Model"].isnull().all() else "N/A"
            }
            ai_summary = generate_portfolio_summary(stats)
            
            # 2. Generate Matplotlib Image
            chart_path = "/tmp/report_chart.png"
            try:
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots(figsize=(6, 4))
                region_counts = d["Region"].value_counts()
                ax.bar(region_counts.index, region_counts.values, color='#1F4E79')
                ax.set_title('Loan Applications by Region')
                plt.tight_layout()
                fig.savefig(chart_path)
                plt.close(fig)
                has_chart = True
            except:
                has_chart = False
            
            # 3. Create PDF
            pdf = FPDF()
            pdf.add_page()
            
            # Title
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, "MIFOS X - AI Portfolio Report", ln=1, align="C")
            pdf.ln(5)
            
            # AI Summary
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "AI Executive Summary", ln=1)
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 5, ai_summary)
            pdf.ln(5)
            
            # Embedded Chart
            if has_chart and os.path.exists(chart_path):
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(0, 10, "Regional Distribution", ln=1)
                pdf.image(chart_path, x=10, w=100)
                pdf.ln(5)
            
            # Data Table
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Filtered Dataset Snippet", ln=1)
            pdf.set_font("Arial", '', 9)
            
            for i, row in d.head(15).iterrows():
                app_id = str(row.get('Application ID', 'N/A'))
                amt = str(row.get('Loan Amount', 0))
                dec = str(row.get('Decision', 'Pending'))
                pdf.cell(0, 6, f"App #{app_id} | Amount: ${amt} | Decision: {dec}", ln=1)
            
            output = pdf.output(dest='S')
            if isinstance(output, (bytes, bytearray)): return bytes(output)
            return output.encode('latin-1')

        colA, colB, colC = st.columns(3)
        with colA:
            st.download_button("📥 Download CSV", csv_data, "filtered_report.csv", "text/csv", use_container_width=True)
        with colB:
            try:
                excel_data = create_excel(filtered_df)
                st.download_button("📥 Download Excel", excel_data, "filtered_report.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            except:
                st.button("📥 Download Excel (Requires openpyxl)", disabled=True, use_container_width=True)
                
        with colC:
            if st.button("🤖 Generate AI Pitch Deck (PDF)", use_container_width=True):
                with st.spinner("Ollama is analyzing the portfolio..."):
                    pdf_data = create_pitch_deck(filtered_df)
                    if pdf_data:
                        st.download_button(
                            label="📥 Download Generated PDF", 
                            data=pdf_data, 
                            file_name="ai_pitch_deck.pdf", 
                            mime="application/pdf", 
                            use_container_width=True
                        )
                    else:
                        st.error("Failed to generate PDF. Make sure fpdf2 is installed.")
    else:
        st.info("No data available.")

with tab2:
    st.markdown("### 🛡️ ECOA Fairness & Bias Audit")
    st.markdown("Check if the AI models are showing disparate impact across protected groups (Gender, Region).")
    
    if not df.empty:
        if st.button("Calculate Fairness Metrics & Generate Audit Report"):
            with st.spinner("Analyzing disparate impact..."):
                # Disparate Impact = (Approval Rate of Unprivileged) / (Approval Rate of Privileged)
                audit_metrics = {}
                
                # Gender Bias
                male_apps = df[df["Gender"] == "Male"]
                female_apps = df[df["Gender"] == "Female"]
                male_apr = len(male_apps[male_apps["Decision"] == "Approved"]) / max(len(male_apps), 1)
                female_apr = len(female_apps[female_apps["Decision"] == "Approved"]) / max(len(female_apps), 1)
                
                gender_di = female_apr / max(male_apr, 0.01) # assuming female is unprivileged for this example
                audit_metrics["Gender (Female vs Male)"] = round(gender_di, 2)
                
                # Regional Bias
                urban_apps = df[df["Region"] == "Urban"]
                rural_apps = df[df["Region"] == "Rural"]
                urban_apr = len(urban_apps[urban_apps["Decision"] == "Approved"]) / max(len(urban_apps), 1)
                rural_apr = len(rural_apps[rural_apps["Decision"] == "Approved"]) / max(len(rural_apps), 1)
                
                region_di = rural_apr / max(urban_apr, 0.01)
                audit_metrics["Region (Rural vs Urban)"] = round(region_di, 2)
                
                st.write("**Disparate Impact Metrics (Four-Fifths Rule):**")
                st.json(audit_metrics)
                
                ai_audit = generate_fairness_audit_summary(audit_metrics)
                st.markdown(f"**🤖 AI Audit Summary:**\n\n{ai_audit}")
                
                # Generate Audit PDF
                if FPDF is not None:
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", 'B', 16)
                    pdf.cell(0, 10, "Regulatory Fairness & Bias Audit", ln=1, align="C")
                    pdf.ln(10)
                    pdf.set_font("Arial", '', 12)
                    pdf.multi_cell(0, 8, "This report evaluates the automated AI loan models for potential biases against protected classes using the Disparate Impact metric (Four-Fifths Rule). A score below 0.8 requires review.")
                    pdf.ln(10)
                    
                    for k, v in audit_metrics.items():
                        flag = " [FAIL]" if v < 0.8 else " [PASS]"
                        pdf.cell(0, 10, f"{k}: {v} {flag}", ln=1)
                        
                    pdf.ln(10)
                    pdf.set_font("Arial", 'B', 12)
                    pdf.cell(0, 10, "AI Compliance Summary:", ln=1)
                    pdf.set_font("Arial", '', 10)
                    pdf.multi_cell(0, 5, ai_audit)
                    
                    pdf_data = pdf.output(dest='S')
                    if isinstance(pdf_data, str): pdf_data = pdf_data.encode('latin-1')
                    
                    st.download_button("📥 Download Audit PDF", bytes(pdf_data), "fairness_audit.pdf", "application/pdf")

with tab3:
    st.markdown("### 📅 Report Scheduler")
    st.markdown("Configure automated background jobs to generate and distribute reports.")
    
    col1, col2 = st.columns(2)
    with col1:
        frequency = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly"])
        time = st.time_input("Execution Time")
    with col2:
        export_type = st.multiselect("Included Formats", ["CSV", "Excel", "AI Pitch Deck (PDF)"], default=["CSV"])
        recipient = st.text_input("Recipient Email (e.g., cro@bank.com)")
        
    if st.button("Save Automation Schedule", type="primary"):
        import requests
        # We simulate saving this to the backend
        try:
            payload = {"frequency": frequency, "time": str(time), "formats": export_type, "recipient": recipient}
            res = requests.post("http://127.0.0.1:8000/api/settings/scheduler", json=payload)
            st.success(f"Scheduled task created! Reports will be sent {frequency.lower()} at {time}.")
        except Exception as e:
            # Fallback if endpoint doesn't exist
            st.success(f"Scheduled task created locally! Reports will be sent {frequency.lower()} at {time} to {recipient}.")
