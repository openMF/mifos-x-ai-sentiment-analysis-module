import streamlit as st
import requests
import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.auth import render_sidebar_auth, get_current_role, api_request, require_role
from chatbot.rag import kb

st.set_page_config(page_title="AI Chat Assistant", page_icon="💬", layout="wide")

render_sidebar_auth()
require_role(["Customer", "Loan Officer", "Risk Analyst", "Administrator"])

def load_css():
    css_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "css", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
load_css()

API_URL = "http://127.0.0.1:8000/api"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Initialize Knowledge Base once
if "kb_indexed" not in st.session_state:
    kb.index_project_files()
    st.session_state.kb_indexed = True

st.sidebar.markdown("### 🏦 **MIFOS X** AI Platform")
role = get_current_role()

# Fetch settings for this role
try:
    set_res = api_request("GET", "settings/{role}")
    settings = set_res.json() if set_res.status_code == 200 else {"ollama_model": "gemma2:2b"}
    ollama_model = settings.get("ollama_model", "gemma2:2b")
except:
    ollama_model = "gemma2:2b"

# Auto-detect available model and provide selection
local_models = [ollama_model]
try:
    tags_res = requests.get("http://localhost:11434/api/tags", timeout=2)
    if tags_res.status_code == 200:
        fetched_models = [m['name'] for m in tags_res.json().get('models', [])]
        if fetched_models:
            local_models = fetched_models
            if ollama_model not in local_models:
                ollama_model = local_models[0]
except:
    pass

st.sidebar.markdown("---")
st.sidebar.markdown("### 🦙 Assistant Model")
selected_model_idx = local_models.index(ollama_model) if ollama_model in local_models else 0
ollama_model = st.sidebar.selectbox("Select Language Model", local_models, index=selected_model_idx)


# ─── LEFT SIDEBAR: HISTORY & SEARCH ────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.markdown("### 🗂️ Conversations")

if st.sidebar.button("➕ New Chat", use_container_width=True):
    try:
        new_conv = api_request("POST", "chat/conversations", json={"title": "New Chat", "user_role": role}).json()
        st.session_state.active_conv_id = new_conv["id"]
        st.rerun()
    except Exception as e:
        st.sidebar.error("Failed to create chat.")

search_term = st.sidebar.text_input("🔍 Search chats...")

try:
    convs = api_request("GET", "chat/conversations?user_role={role}").json()
    if isinstance(convs, list):
        for c in convs:
            if search_term.lower() in c['title'].lower():
                # Streamlit sidebar button for each chat
                btn_label = f"⭐ {c['title']}" if c.get('is_favorite') else c['title']
                if st.sidebar.button(btn_label, key=f"conv_{c['id']}", use_container_width=True):
                    st.session_state.active_conv_id = c['id']
                    st.rerun()
except:
    st.sidebar.warning("Could not load chat history.")

if "active_conv_id" not in st.session_state:
    if 'convs' in locals() and isinstance(convs, list) and len(convs) > 0:
        st.session_state.active_conv_id = convs[0]['id']
    else:
        # Create a default one if none exists
        try:
            new_conv = api_request("POST", "chat/conversations", json={"title": "New Chat", "user_role": role}).json()
            st.session_state.active_conv_id = new_conv["id"]
        except:
            st.session_state.active_conv_id = None

# Fetch messages for active conversation
messages = []
if st.session_state.active_conv_id:
    try:
        msgs = api_request("GET", "chat/messages/{st.session_state.active_conv_id}").json()
        if isinstance(msgs, list):
            messages = msgs
    except:
        pass

# ─── LAYOUT: CENTER AND RIGHT ─────────────────────────────────────
col_center, col_right = st.columns([3, 1])

# Fetch right panel context first so it can be passed to the LLM
latest_app = None
try:
    apps_res = api_request("GET", "applications")
    if apps_res.status_code == 200 and apps_res.json() != "NILL":
        apps_list = apps_res.json()
        if isinstance(apps_list, list) and len(apps_list) > 0:
            latest_app = apps_list[0] # The API sorts by desc
except:
    pass

with col_right:
    st.markdown("### 📋 Live Context")
    if latest_app:
        st.info("Using Latest Applicant Context")
        st.markdown(f"**App ID:** {latest_app.get('id')}")
        st.markdown(f"**Income:** ${latest_app.get('income')}")
        st.markdown(f"**Debt:** ${latest_app.get('existing_debt')}")
        st.markdown(f"**Score:** {latest_app.get('credit_score')}")
        
        preds = latest_app.get('prediction', {})
        if preds:
            st.markdown("---")
            st.markdown("#### RL Output")
            st.metric("Recommended Rate", f"{preds.get('recommended_rate')}%")
            st.metric("Risk Score", preds.get('risk_score'))
            st.metric("Ensemble Engine", preds.get('best_model'))
            
        st.markdown("---")
        try:
            dash = api_request("GET", "dashboard").json()
            st.markdown("#### System Health")
            st.markdown(f"Approval Rate: **{dash.get('approval_rate', 0)*100}%**")
            st.markdown(f"Active Models: **PPO, SAC, DQN, DDQN**")
        except:
            pass
    else:
        st.warning("No live applicant context available.")

with col_center:
    st.markdown("<h2 style='color:#1F4E79;'>💬 Copilot Workspace</h2>", unsafe_allow_html=True)
    
    query_mode = st.radio("Query Mode", ["🟢 Live Context", "🌐 General Query"], horizontal=True, help="Select whether to include the live applicant context in the query.")

    # Render messages
    if not messages:
        st.info("Start a conversation below.")
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Quick Actions
    st.markdown("---")
    qa_col1, qa_col2, qa_col3, qa_col4 = st.columns(4)
    quick_prompt = None
    if qa_col1.button("Explain Prediction", use_container_width=True): quick_prompt = "Explain the most recent RL prediction in detail."
    if qa_col2.button("Compare PPO vs SAC", use_container_width=True): quick_prompt = "Compare the PPO and SAC algorithms in our banking environment."
    if qa_col3.button("System Architecture", use_container_width=True): quick_prompt = "Explain the system architecture."
    if qa_col4.button("Risk Analysis", use_container_width=True): quick_prompt = "What factors are driving the current risk score?"

    def generate_response(prompt_text, mode):
        # 1. Retrieve RAG Context
        rag_context = kb.search(prompt_text, n_results=2)
        
        # 2. Build System Prompt based on role
        if role == "Customer":
            sys_msg = "You are a polite AI Banking Assistant. Answer simply but with critical depth and insight. Do not use technical RL jargon. Use simple financial terms."
        elif role == "Loan Officer":
            sys_msg = "You are an AI Assistant for Loan Officers. Explain predictions highlighting risk factors, debt ratio, and ensemble model confidence with critical depth and rigorous analysis."
        else:
            sys_msg = "You are a technical AI Administrator. Answer with critical depth and exhaustive detail about RL algorithms, FastAPI, and system architecture."
            
        # 3. Inject Right-Panel Context
        if mode == "🟢 Live Context" and latest_app:
            sys_msg += f"\n\nCURRENT APPLICANT CONTEXT:\n{json.dumps(latest_app, indent=2)}\n"
            sys_msg += "\nPlease analyze the above Live Context in critical depth in your response.\n"
            
        sys_msg += f"\n\nPROJECT KNOWLEDGE BASE:\n{rag_context}\n" if rag_context else ""
        
        full_prompt = f"{sys_msg}\n\nUser: {prompt_text}\nAssistant:"
        
        payload = {
            "model": ollama_model,
            "prompt": full_prompt,
            "stream": True
        }
        try:
            response = requests.post(OLLAMA_URL, json=payload, stream=True)
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        decoded = json.loads(line.decode('utf-8'))
                        yield decoded.get("response", "")
            else:
                yield "Error communicating with local AI engine."
        except:
            yield f"[FALLBACK] Unable to connect to local AI engine (port 11434). Model selected: {ollama_model}."

    user_input = st.chat_input("Ask the AI Assistant...")
    active_prompt = quick_prompt if quick_prompt else user_input

    if active_prompt:
        st.chat_message("user").markdown(active_prompt)
        
        # Save user message
        if st.session_state.active_conv_id:
            api_request("POST", "chat/messages/{st.session_state.active_conv_id}", json={"role": "user", "content": active_prompt})
            
        with st.chat_message("assistant"):
            full_res = st.write_stream(generate_response(active_prompt, query_mode))
            
        # Save assistant message
        if st.session_state.active_conv_id:
            api_request("POST", "chat/messages/{st.session_state.active_conv_id}", json={"role": "assistant", "content": full_res})
            
        st.rerun()
