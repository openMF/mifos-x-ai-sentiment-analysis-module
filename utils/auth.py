import streamlit as st
import requests

ROLES = ["Customer", "Loan Officer", "Risk Analyst", "Administrator"]
API_URL = "http://127.0.0.1:8000/api"

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
