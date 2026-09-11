import streamlit as st
import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.auth import (
    render_sidebar_auth,
    get_current_role,
    api_request,
    PAGE_REGISTRY,
    allowed_pages_for_role,
)

st.set_page_config(page_title="MIFOS X AI Engine", page_icon="🏦", layout="wide")


def load_css():
    css_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "frontend", "css", "style.css"
    )
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()

API_URL = "http://127.0.0.1:8000/api"

# ─── Sidebar Authentication ──────────────────────────────────────────
st.sidebar.markdown("### **MIFOS X** AI Platform")

if "token" not in st.session_state:
    st.markdown("## 🔐 Login to MIFOS X")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                res = api_request(
                    "POST", "token", data={"username": username, "password": password}
                )
                if res.status_code == 200:
                    data = res.json()
                    st.session_state["token"] = data["access_token"]
                    st.session_state["username"] = username

                    user_res = api_request(
                        "GET",
                        "users/me",
                        headers={"Authorization": f"Bearer {data['access_token']}"},
                    )
                    if user_res.status_code == 200:
                        st.session_state["current_role"] = user_res.json()["role"]
                        st.rerun()
                else:
                    st.error("Invalid credentials")

    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox(
                "Role", ["Customer", "Loan Officer", "Administrator"]
            )
            reg_submitted = st.form_submit_button("Register")
            if reg_submitted:
                res = api_request(
                    "POST",
                    "users/register",
                    json={
                        "username": new_username,
                        "password": new_password,
                        "role": new_role,
                    },
                )
                if res.status_code == 200:
                    st.success("Registration successful! Please login.")
                else:
                    st.error(f"Registration failed: {res.text}")

    st.stop()


# ─── Authenticated: build role-based navigation ──────────────────────
render_sidebar_auth()
role = get_current_role()
st.sidebar.markdown(f"**Welcome, {role}**")

visible_keys = allowed_pages_for_role(role)
visible_pages = []
for key in visible_keys:
    meta = PAGE_REGISTRY[key]
    page_kwargs = {
        "title": meta["title"],
        "default": (key == visible_keys[0]),
    }
    if meta.get("icon"):
        page_kwargs["icon"] = meta["icon"]
    visible_pages.append(st.Page(meta["file"], **page_kwargs))

home_page_kwargs = {
    "title": "Dashboard",
    "default": (not visible_keys),
}
home_page = st.Page("dashboard_home.py", **home_page_kwargs)

navigation = {"Home": [home_page], "Workspace": visible_pages}
pg = st.navigation(navigation)
pg.run()
