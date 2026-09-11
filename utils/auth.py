import streamlit as st
import requests

ROLES = ["Customer", "Loan Officer", "Risk Analyst", "Compliance Officer", "Administrator"]
API_URL = "http://localhost:8000/api"

PAGES_DIR = "views"

PAGE_REGISTRY = {
    "1_Loan_Processing": {
        "file": f"{PAGES_DIR}/1_Loan_Processing.py",
        "title": "Loan Processing",
        "icon": None,
        "roles": ["Customer", "Loan Officer", "Risk Analyst", "Administrator"],
    },
    "2_Model_Training": {
        "file": f"{PAGES_DIR}/2_Model_Training.py",
        "title": "Model Training",
        "icon": None,
        "roles": ["Loan Officer", "Risk Analyst", "Administrator"],
    },
    "3_Analytics": {
        "file": f"{PAGES_DIR}/3_Analytics.py",
        "title": "Analytics",
        "icon": None,
        "roles": ["Loan Officer", "Risk Analyst", "Compliance Officer", "Administrator"],
    },
    "4_AB_Testing": {
        "file": f"{PAGES_DIR}/4_AB_Testing.py",
        "title": "A/B Testing",
        "icon": None,
        "roles": ["Loan Officer", "Administrator"],
    },
    "5_Reports": {
        "file": f"{PAGES_DIR}/5_Reports.py",
        "title": "Reports",
        "icon": None,
        "roles": ["Loan Officer", "Risk Analyst", "Compliance Officer", "Administrator"],
    },
    "6_What_If_Simulator": {
        "file": f"{PAGES_DIR}/6_What_If_Simulator.py",
        "title": "What-If Simulator",
        "icon": None,
        "roles": ["Loan Officer", "Risk Analyst", "Administrator"],
    },
    "7_Ollama_Assistant": {
        "file": f"{PAGES_DIR}/7_Ollama_Assistant.py",
        "title": "AI Chat Assistant",
        "icon": None,
        "roles": ["Customer", "Loan Officer", "Risk Analyst", "Compliance Officer", "Administrator"],
    },
    "8_Settings": {
        "file": f"{PAGES_DIR}/8_Settings.py",
        "title": "Settings",
        "icon": None,
        "roles": ["Customer", "Loan Officer", "Risk Analyst", "Compliance Officer", "Administrator"],
    },
    "9_Fairness_Report": {
        "file": f"{PAGES_DIR}/9_Fairness_Report.py",
        "title": "Fairness Report",
        "icon": None,
        "roles": ["Risk Analyst", "Compliance Officer", "Administrator"],
    },
}


def allowed_pages_for_role(role: str) -> list[str]:
    """Return list of page keys (PAGE_REGISTRY keys) visible to the given role."""
    return [key for key, meta in PAGE_REGISTRY.items() if role in meta["roles"]]


def require_role(allowed_roles: list):
    """Decorator or function to check if the current user has access to a page."""
    current_role = st.session_state.get('current_role', "Customer")
    if current_role not in allowed_roles:
        st.error(f"Access Denied. This page requires one of the following roles: {', '.join(allowed_roles)}")
        st.stop()

def render_sidebar_auth():
    """Renders the logged in user info and logout button."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👤 User Session")
    
    if "token" in st.session_state:
        st.sidebar.write(f"**User**: {st.session_state.get('username')}")
        st.sidebar.write(f"**Role**: {st.session_state.get('current_role')}")
        
        if st.sidebar.button("Logout"):
            del st.session_state["token"]
            del st.session_state["username"]
            del st.session_state["current_role"]
            st.rerun()
    else:
        st.sidebar.warning("Not logged in.")
        st.stop()

def get_current_role():
    return st.session_state.get('current_role', "Customer")

def api_request(method, endpoint, **kwargs):
    """Helper to append Authorization header to API requests"""
    headers = kwargs.get("headers", {})
    if "token" in st.session_state:
        headers["Authorization"] = f"Bearer {st.session_state['token']}"
    kwargs["headers"] = headers
    
    url = f"{API_URL}/{endpoint.lstrip('/')}"
    return requests.request(method, url, **kwargs)
