import streamlit as st
import pandas as pd
import requests
import json
import os
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.auth import render_sidebar_auth, get_current_role, api_request, require_role

API_URL = "http://127.0.0.1:8000/api"

st.set_page_config(page_title="Model Training Studio", layout="wide")

require_role(["Administrator", "Loan Officer", "Risk Analyst"])

# Custom CSS for Enterprise look
st.markdown("""
<style>
    .metric-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00A67E;
        color: white;
    }
    .metric-title {
        font-size: 14px;
        color: #A0A0A0;
        text-transform: uppercase;
        font-weight: bold;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("🧠 Intelligent Adaptive Training Studio")
st.markdown("Automatically configures Reinforcement Learning models based on your hardware constraints and tracks all experiments.")

# --- Session State ---
if 'hardware_info' not in st.session_state:
    try:
        res = api_request("GET", "hardware")
        if res.status_code == 200:
            st.session_state.hardware_info = res.json()
        else:
            st.session_state.hardware_info = None
    except:
        st.session_state.hardware_info = None

if 'active_experiment_id' not in st.session_state:
    st.session_state.active_experiment_id = None

# ==========================================
# MODEL REGISTRY STATUS
# ==========================================
st.markdown("### 🗄️ Loaded Prediction Models")
try:
    models_res = api_request("GET", "models")
    if models_res.status_code == 200:
        model_status = models_res.json()

        cols = st.columns(4)
        model_names = ["PPO", "DQN", "DDQN", "SAC"]
        status_icons = {"loaded": "🟢", "on_disk": "🟡", "not_trained": "🔴"}
        status_labels = {"loaded": "Loaded & Ready", "on_disk": "Saved (Not Loaded)", "not_trained": "Not Trained"}

        for i, name in enumerate(model_names):
            info = model_status.get(name, {})
            if isinstance(info, str) and info == "NILL":
                s = "not_trained"
                size = "N/A"
            else:
                s = info.get("status", "not_trained")
                size_val = info.get("size_mb")
                size = f"{size_val} MB" if size_val and size_val != "NILL" else "N/A"

            icon = status_icons.get(s, "⚪")
            label = status_labels.get(s, "Unknown")
            border_color = "#27AE60" if s == "loaded" else ("#F2C94C" if s == "on_disk" else "#E74C3C")

            with cols[i]:
                st.markdown(f"""<div style="background:white;padding:15px;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.06);border-top:4px solid {border_color};text-align:center;">
<div style="font-size:1.4rem;font-weight:700;color:#1F4E79;">{icon} {name}</div>
<div style="color:{border_color};font-weight:600;margin-top:6px;">{label}</div>
<div style="color:#828282;font-size:0.8rem;margin-top:2px;">Size: {size}</div>
</div>""", unsafe_allow_html=True)

        st.markdown("")
        if st.button("🔄 Reload All Models into Memory"):
            try:
                res = api_request("POST", "models/reload-all")
                if res.status_code == 200:
                    st.success("All models reloaded from disk!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to reload models.")
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Could not fetch model status.")
except requests.exceptions.ConnectionError:
    st.error("🚨 Backend API is not running.")

st.markdown("---")

# --- Tabs ---
tab_quick, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚀 Quick Train",
    "💻 Hardware Diagnostics", 
    "📂 Data Wizard", 
    "⚙️ Hyperparameters", 
    "📈 Live Dashboard", 
    "🔬 Experiment Lab"
])

# ==========================================
# TAB: Quick Train (built-in dataset)
# ==========================================
with tab_quick:
    st.subheader("Train on Built-in Dataset")
    st.markdown("Quickly train any RL algorithm using the project's default loan dataset. No data upload needed.")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        quick_model = st.selectbox("Select Model Architecture", ["PPO", "DQN", "DDQN", "SAC"], key="quick_model")
    with col2:
        quick_timesteps = st.number_input("Total Timesteps", min_value=1000, max_value=1000000, value=10000, step=1000, key="quick_ts")
    with col3:
        st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)
        if st.button("▶ Start Training Job", key="quick_train_btn"):
            with st.spinner(f"Initiating training for {quick_model}..."):
                try:
                    response = api_request("POST", "train?model_type={quick_model}&total_timesteps={quick_timesteps}")
                    if response.status_code == 200:
                        st.success(f"✅ Training started for **{quick_model}** ({quick_timesteps} timesteps). The model will be automatically loaded for predictions once training completes.")
                        st.info("💡 Refresh this page after training finishes to see the updated model status.")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Failed to start training: {e}")
    
    st.markdown("---")
    st.markdown("### 📊 Training History")
    try:
        hist_res = api_request("GET", "history")
        comp_res = api_request("GET", "model-comparison")

        col_left, col_right = st.columns([3, 2])

        with col_left:
            if hist_res.status_code == 200 and hist_res.json() != "NILL":
                data = hist_res.json()
                if isinstance(data, list) and len(data) > 0:
                    df_hist = pd.DataFrame(data)
                    fig = px.line(df_hist, x="episode", y="reward", color="model_name",
                                  title="Episode vs Reward",
                                  color_discrete_sequence=['#1F4E79', '#2F80ED', '#56CCF2', '#27AE60'],
                                  template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No training history available yet. Train a model to see results here.")
            else:
                st.info("No training history available yet.")

        with col_right:
            st.markdown("### 🏆 Model Comparison")
            if comp_res.status_code == 200 and comp_res.json() != "NILL":
                comp_data = comp_res.json()
                if isinstance(comp_data, list) and len(comp_data) > 0:
                    df_comp = pd.DataFrame(comp_data)
                    fig = px.bar(df_comp, x="model", y=["avg_reward", "max_reward"],
                                 barmode="group", title="Average & Maximum Rewards",
                                 color_discrete_sequence=['#2F80ED', '#27AE60'],
                                 template="plotly_white")
                    st.plotly_chart(fig, use_container_width=True)

                    best_model = df_comp.loc[df_comp['avg_reward'].idxmax()]['model']
                    st.markdown(f"""<div style='text-align:center;padding:15px;background:white;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.06);'>
<h4 style='color:#828282;text-transform:uppercase;font-size:0.9rem;'>🥇 Best Model</h4>
<div style='font-size:2.5rem;font-weight:700;color:#1F4E79;'>{best_model}</div>
</div>""", unsafe_allow_html=True)
                else:
                    st.info("No comparison data available.")
            else:
                st.info("No comparison data available.")
    except Exception as e:
        st.error(f"Could not load charts. ({e})")

# ==========================================
# TAB 1: Hardware Diagnostics
# ==========================================
with tab1:
    if st.session_state.hardware_info:
        hw = st.session_state.hardware_info["hardware"]
        profile = st.session_state.hardware_info["recommended_profile"]
        
        st.subheader("System Architecture")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Operating System</div>
                <div class='metric-value'>{hw['os']} {hw['os_version']}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class='metric-card' style='border-color: #3b82f6;'>
                <div class='metric-title'>Processor</div>
                <div class='metric-value'>{hw['cpu_threads']} Threads</div>
                <div style='font-size:12px;color:#bbb'>{hw['cpu_brand']}</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class='metric-card' style='border-color: #f59e0b;'>
                <div class='metric-title'>Memory (RAM)</div>
                <div class='metric-value'>{hw['ram_total']}</div>
                <div style='font-size:12px;color:#bbb'>{hw['ram_percent']}% Used</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            gpu_name = hw["gpus"][0]["name"] if hw.get("gpus") else "CPU Only"
            st.markdown(f"""
            <div class='metric-card' style='border-color: #ef4444;'>
                <div class='metric-title'>Graphics (GPU)</div>
                <div class='metric-value'>{gpu_name}</div>
                <div style='font-size:12px;color:#bbb'>CUDA: {hw['cuda_available']} | MPS: {hw['mps_available']}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🤖 Recommended Training Profile")
        st.info(f"**{profile['name']}**: {profile['notes']}")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Target Device", profile['device'].upper())
        c2.metric("Batch Size", profile['batch_size'])
        c3.metric("Buffer Size", profile['buffer_size'])
        c4.metric("Parallel Envs", profile['n_envs'])

# ==========================================
# TAB 2: Data Wizard
# ==========================================
with tab2:
    st.subheader("Upload Custom Dataset")
    st.markdown("Map your dataset columns to the required Reinforcement Learning features.")
    
    # 1. Project Selection
    st.markdown("#### 1. Select Workspace")
    try:
        proj_res = api_request("GET", "training/projects").json()
    except:
        proj_res = []
        
    proj_names = {p["name"]: p["id"] for p in proj_res}
    
    c1, c2 = st.columns([3, 1])
    with c1:
        selected_proj = st.selectbox("Training Project", ["Create New..."] + list(proj_names.keys()))
    
    if selected_proj == "Create New...":
        with st.form("new_proj"):
            new_name = st.text_input("Project Name")
            new_desc = st.text_input("Description")
            if st.form_submit_button("Create Project"):
                res = api_request("POST", "training/projects", json={"name": new_name, "description": new_desc})
                if res.status_code == 200:
                    st.success("Project created!")
                    time.sleep(1)
                    st.rerun()

    project_id = proj_names.get(selected_proj, None)
    
    if project_id:
        # 2. File Upload
        uploaded_file = st.file_uploader("Upload Dataset (CSV/Excel)", type=["csv", "xlsx"])
        if uploaded_file:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            
            st.markdown("#### Data Preview")
            st.dataframe(df.head(5))
            
            # Simple visualization preview if numeric cols exist
            numeric_cols = df.select_dtypes(include='number').columns
            if len(numeric_cols) > 0:
                viz_col = "loan_amount" if "loan_amount" in df.columns else numeric_cols[0]
                fig = px.histogram(df, x=viz_col, title=f"Distribution of {viz_col}", template="plotly_white", color_discrete_sequence=['#2F80ED'])
                st.plotly_chart(fig, use_container_width=True)
            
            # 3. Column Mapping
            st.markdown("#### 2. Feature Mapping")
            required_features = [
                "age", "gender", "employment", "income", "credit_score", "loan_amount", 
                "loan_purpose", "existing_debt", "loan_tenure", "repayment_history", "region",
                "collateral", "existing_loans", "education", "decision"
            ]
            
            mapping = {}
            cols = st.columns(3)
            for i, req_feat in enumerate(required_features):
                with cols[i % 3]:
                    # Try to auto-guess
                    guess = next((c for c in df.columns if req_feat.lower() in c.lower()), "Skip/Generate")
                    mapping[req_feat] = st.selectbox(f"Map '{req_feat}'", ["Skip/Generate"] + list(df.columns), index=(["Skip/Generate"] + list(df.columns)).index(guess) if guess in df.columns else 0)
            
            if st.button("Save Dataset & Schema"):
                reverse_mapping = {v: k for k, v in mapping.items() if v != "Skip/Generate"}
                
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/octet-stream")}
                data = {
                    "project_id": project_id,
                    "schema_mapping": json.dumps(reverse_mapping),
                    "row_count": len(df)
                }
                
                with st.spinner("Uploading and processing dataset..."):
                    res = api_request("POST", "training/datasets", files=files, data=data)
                    
                    if res.status_code == 200:
                        st.success("Dataset uploaded and processed successfully!")
                    else:
                        st.error(f"Failed to register dataset: {res.text}")

# ==========================================
# TAB 3: Hyperparameters & Launch
# ==========================================
with tab3:
    st.subheader("Algorithm & Hyperparameters")
    
    if st.session_state.hardware_info:
        profile = st.session_state.hardware_info["recommended_profile"]
        
        c1, c2 = st.columns(2)
        with c1:
            algorithm = st.selectbox("RL Algorithm", ["PPO", "DQN", "DDQN", "SAC"])
            if project_id:
                dsets_res = api_request("GET", f"training/datasets?project_id={project_id}")
                if dsets_res.status_code == 200:
                    dsets = dsets_res.json()
                    dset_opts = {d["filename"]: d["id"] for d in dsets}
                    dataset_id = st.selectbox("Dataset", list(dset_opts.keys()))
                else:
                    st.warning("Failed to load datasets.")
                    dataset_id = None
            else:
                st.warning("Please select a project in the Data Wizard tab first.")
                dataset_id = None
                
        with c2:
            st.markdown(f"**Applied Profile:** `{profile['name']}`")
            learning_rate = st.number_input("Learning Rate", value=float(profile.get("learning_rate", 0.0003)), format="%.5f")
            batch_size = st.number_input("Batch Size", value=int(profile.get("batch_size", 64)))
            buffer_size = st.number_input("Buffer Size (Transitions)", value=int(profile.get("buffer_size", 100000)))
            total_timesteps = st.number_input("Total Timesteps", value=10000, step=1000)
            gamma = st.slider("Gamma (Discount Factor)", min_value=0.8, max_value=0.999, value=0.99)
            
            ent_coef = 0.0
            if algorithm in ["PPO", "SAC"]:
                ent_coef = st.number_input("Entropy Coefficient", value=0.01, format="%.3f")
            
        if st.button("🚀 Launch Training Job", use_container_width=True, type="primary"):
            if dataset_id:
                payload = {
                    "project_id": project_id,
                    "dataset_id": dset_opts[dataset_id],
                    "algorithm": algorithm,
                    "profile_name": profile["name"],
                    "hyperparameters": json.dumps({
                        "learning_rate": learning_rate,
                        "batch_size": batch_size,
                        "buffer_size": buffer_size,
                        "total_timesteps": total_timesteps,
                        "gamma": gamma,
                        "ent_coef": ent_coef
                    })
                }
                res = api_request("POST", "training/experiments", json=payload)
                if res.status_code == 200:
                    st.session_state.active_experiment_id = res.json()["id"]
                    st.success(f"Job launched! View progress in Live Dashboard.")
            else:
                st.error("Cannot launch without dataset.")

# ==========================================
# TAB 4: Live Dashboard
# ==========================================
with tab4:
    st.subheader("Live Training Telemetry")
    
    exp_id = st.session_state.active_experiment_id
    if exp_id:
        try:
            status = api_request("GET", f"training/experiments/{exp_id}/status").json()
            
            st.markdown(f"### Status: **{status['status']}** | Progress: **{status['progress']*100:.1f}%**")
            st.progress(status["progress"])
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Current Episode", status["current_episode"])
            col2.metric("Best Reward", round(max(status["rewards"]) if status["rewards"] else 0, 4))
            col3.metric("Training Speed", f"{status['speed']} steps/s")
            
            if len(status["rewards"]) > 0:
                df_plot = pd.DataFrame({"Reward": status["rewards"], "Loss": status["losses"]})
                # Add Moving Average
                if len(df_plot) > 5:
                    df_plot["Reward_MA"] = df_plot["Reward"].rolling(window=5, min_periods=1).mean()
                else:
                    df_plot["Reward_MA"] = df_plot["Reward"]
                
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Scatter(y=df_plot["Reward"], mode="lines", name="Raw Reward", line=dict(color="rgba(0,166,126,0.3)")), secondary_y=False)
                fig.add_trace(go.Scatter(y=df_plot["Reward_MA"], mode="lines", name="Reward (MA)", line=dict(color="#00A67E", width=2)), secondary_y=False)
                fig.add_trace(go.Scatter(y=df_plot["Loss"], mode="lines", name="Loss", line=dict(color="#ef4444", dash='dash')), secondary_y=True)
                fig.update_layout(title="Learning Curve", template="plotly_dark")
                st.plotly_chart(fig, use_container_width=True)
            
            if status["status"] == "Running":
                if st.button("⏹️ Stop Training"):
                    api_request("POST", f"training/experiments/{exp_id}/cancel")
                    st.rerun()
                time.sleep(2)
                st.rerun()

        except Exception as e:
            st.error(f"Waiting for telemetry... ({e})")
            time.sleep(2)
            st.rerun()
    else:
        st.info("No active training job. Launch one from the Hyperparameters tab.")

# ==========================================
# TAB 5: Experiment Lab
# ==========================================
with tab5:
    st.subheader("Experiment Tracking & History")
    if project_id:
        try:
            exps = api_request("GET", f"training/experiments?project_id={project_id}").json()
            if exps:
                df_exps = pd.DataFrame(exps)
                df_exps['hyperparameters'] = df_exps['hyperparameters'].apply(lambda x: str(json.loads(x)))
                
                # Interactive selection
                exp_opts = {f"Experiment #{r['id']} ({r['algorithm']} - Reward: {r['best_reward']})": r['id'] for _, r in df_exps.iterrows()}
                selected_exp_name = st.selectbox("Select Experiment to Deploy", list(exp_opts.keys()))
                selected_exp_id = exp_opts[selected_exp_name]
                
                st.dataframe(df_exps[df_exps['id'] == selected_exp_id][["id", "algorithm", "status", "best_reward", "start_time", "hyperparameters"]])
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🚀 Deploy Model to Production", type="primary", use_container_width=True):
                        with st.spinner("Deploying model and reloading API..."):
                            dep_res = api_request("POST", f"training/experiments/{selected_exp_id}/deploy")
                            if dep_res.status_code == 200:
                                st.success(f"Successfully deployed! API is now serving the new model.")
                            else:
                                st.error(f"Failed to deploy: {dep_res.text}")
                
                with col2:
                    if st.button("🤖 Generate AI Analysis of this Run", use_container_width=True):
                        with st.spinner("Analyzing hyperparameter efficacy with Ollama..."):
                            analysis_res = api_request("GET", f"training/experiments/{selected_exp_id}/analyze")
                            if analysis_res.status_code == 200:
                                st.markdown(f"""
                                <div style="background-color: #2D3748; padding: 15px; border-radius: 8px; border-left: 5px solid #00A67E;">
                                    <strong>🤖 AI Analysis:</strong><br>
                                    {analysis_res.json().get('analysis', '')}
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.error("Failed to generate analysis.")
            else:
                st.write("No experiments recorded yet in this project.")
        except:
            st.write("Failed to fetch experiments.")
            
    st.markdown("### Old Training History (Legacy)")
    try:
        hist_res = api_request("GET", "history")
        if hist_res.status_code == 200 and hist_res.json() != "NILL":
            data = hist_res.json()
            if isinstance(data, list) and len(data) > 0:
                df_old = pd.DataFrame(data)
                fig = px.line(df_old, x="episode", y="reward", color="model_name", title="Legacy Episode vs Reward")
                st.plotly_chart(fig, use_container_width=True)
    except:
        pass
