from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException, status, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from database.database import engine, SessionLocal, Base, get_db
from database import models
from backend.schemas import schemas
from backend import auth
from services import training_service
from services import prediction_service
from ollama.explain import generate_explanation
from textblob import TextBlob
import numpy as np
import asyncio
from analytics.fairness import run_fairness_audit
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Dynamic Micro-Loan Pricing API",
    description="RL-powered dynamic loan pricing system inspired by MIFOS X",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def sanitize_nill(obj):
    """Replace None, NaN, empty lists, empty dicts with 'NILL'"""
    if obj is None:
        return "NILL"
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return "NILL"
    if isinstance(obj, dict):
        return {k: sanitize_nill(v) for k, v in obj.items()}
    if isinstance(obj, list):
        if len(obj) == 0:
            return "NILL"
        return [sanitize_nill(i) for i in obj]
    return obj

async def run_daily_fairness_audit():
    """Background task that runs the fairness audit every 24 hours."""
    while True:
        try:
            logger.info("Running daily fairness audit...")
            run_fairness_audit()
        except Exception as e:
            logger.error(f"Error during daily fairness audit: {e}")
        # Sleep for 24 hours
        await asyncio.sleep(24 * 60 * 60)

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified.")
    # Auto-detect and load any trained RL models from disk
    prediction_service.load_all_models()
    # Start the background audit scheduler
    asyncio.create_task(run_daily_fairness_audit())

# ─── Auth API ───────────────────────────────────────────────────────

@app.post("/api/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/users/register", response_model=schemas.UserOut)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/api/users/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# ─── Training Studio API ────────────────────────────────────────────

from utils.hardware import detect_hardware, get_recommended_profile
from services.training_service import TrainingJobManager

@app.get("/api/hardware")
def get_hardware_info():
    hw_info = detect_hardware()
    profile = get_recommended_profile(hw_info)
    return {"hardware": hw_info, "recommended_profile": profile}

@app.get("/api/training/projects", response_model=List[schemas.TrainingProjectOut])
def get_projects(db: Session = Depends(get_db)):
    return db.query(models.TrainingProject).order_by(models.TrainingProject.created_at.desc()).all()

@app.post("/api/training/projects", response_model=schemas.TrainingProjectOut)
def create_project(project: schemas.TrainingProjectCreate, db: Session = Depends(get_db)):
    db_project = models.TrainingProject(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/api/training/datasets", response_model=List[schemas.CustomDatasetOut])
def get_datasets(project_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.CustomDataset)
    if project_id:
        query = query.filter(models.CustomDataset.project_id == project_id)
    return query.order_by(models.CustomDataset.created_at.desc()).all()

@app.post("/api/training/datasets", response_model=schemas.CustomDatasetOut)
def create_dataset(
    project_id: int = Form(...),
    schema_mapping: str = Form(...),
    row_count: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not (file.filename.endswith('.csv') or file.filename.endswith('.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV or Excel files are allowed.")
    
    os.makedirs("datasets/custom", exist_ok=True)
    filepath = f"datasets/custom/{file.filename}"
    with open(filepath, "wb") as buffer:
        buffer.write(file.file.read())
        
    db_dataset = models.CustomDataset(
        project_id=project_id,
        filename=file.filename,
        filepath=filepath,
        schema_mapping=schema_mapping,
        row_count=row_count
    )
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    
    # Process dataset synchronously for immediate availability
    from services.dataset_service import load_and_preprocess_dataset
    import json
    load_and_preprocess_dataset(filepath, json.loads(schema_mapping))
    
    return db_dataset

@app.get("/api/training/experiments", response_model=List[schemas.TrainingExperimentOut])
def get_experiments(project_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(models.TrainingExperiment)
    if project_id:
        query = query.filter(models.TrainingExperiment.project_id == project_id)
    return query.order_by(models.TrainingExperiment.start_time.desc()).all()

@app.post("/api/training/experiments", response_model=schemas.TrainingExperimentOut)
def create_experiment(exp: schemas.TrainingExperimentCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_officer)):
    # 1. Create record in DB
    db_exp = models.TrainingExperiment(**exp.model_dump())
    db.add(db_exp)
    db.commit()
    db.refresh(db_exp)
    
    # 2. Start Async Training
    dataset = db.query(models.CustomDataset).filter(models.CustomDataset.id == exp.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    dataset_path = dataset.filepath.replace('.csv', '_processed.csv').replace('.xlsx', '_processed.csv')
    
    TrainingJobManager.start_job(
        experiment_id=db_exp.id,
        model_type=exp.algorithm,
        dataset_path=dataset_path,
        hyperparameters=exp.hyperparameters,
        total_timesteps=1000 # Configurable via hyperparams ideally
    )
    
    return db_exp

@app.get("/api/training/experiments/{exp_id}/status")
def get_experiment_status(exp_id: int):
    status = TrainingJobManager.get_status(exp_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found or not active")
    return status

@app.post("/api/training/experiments/{exp_id}/cancel")
def cancel_experiment(exp_id: int):
    TrainingJobManager.cancel_job(exp_id)
    return {"status": "cancelled"}

@app.post("/api/training/experiments/{exp_id}/deploy")
def deploy_experiment_model(exp_id: int, db: Session = Depends(get_db)):
    exp = db.query(models.TrainingExperiment).filter(models.TrainingExperiment.id == exp_id).first()
    if not exp or exp.status != "Completed":
        raise HTTPException(status_code=400, detail="Experiment not found or not completed.")
    
    import shutil
    source_model = f"models/{exp.algorithm.lower()}_experiment_{exp.id}.zip"
    dest_model = f"models/{exp.algorithm.lower()}_model.zip"
    
    if not os.path.exists(source_model):
        raise HTTPException(status_code=404, detail=f"Saved model {source_model} not found.")
        
    shutil.copy2(source_model, dest_model)
    
    from services.prediction_service import reload_model
    if reload_model(exp.algorithm):
        return {"status": "success", "message": f"{exp.algorithm} deployed to production!"}
    else:
        raise HTTPException(status_code=500, detail="Failed to load model into memory.")

@app.get("/api/training/experiments/{exp_id}/analyze")
def analyze_experiment(exp_id: int, db: Session = Depends(get_db)):
    exp = db.query(models.TrainingExperiment).filter(models.TrainingExperiment.id == exp_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")
    
    import json
    from ollama.explain import analyze_training_run
    
    try:
        hp = json.loads(exp.hyperparameters) if exp.hyperparameters else {}
    except:
        hp = {}
        
    analysis = analyze_training_run(
        algorithm=exp.algorithm,
        hyperparameters=hp,
        best_reward=exp.best_reward or 0.0,
        status=exp.status
    )
    
    return {"analysis": analysis}

# ─── Quick Train (backward-compatible) ────────────────────────────
@app.post("/api/train")
def train_model_quick(
    model_type: str,
    total_timesteps: int = 1000,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Quick-train using the project's built-in dataset. No Data Wizard needed."""
    if model_type not in ["PPO", "DQN", "DDQN", "SAC"]:
        raise HTTPException(status_code=400, detail="Invalid model type. Choose from PPO, DQN, DDQN, SAC.")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, 'datasets', 'processed_loan_dataset.csv')
    
    if not os.path.exists(data_path):
        raise HTTPException(status_code=500, detail=f"Default dataset not found at {data_path}")
    
    from services.training_service import start_training
    background_tasks.add_task(start_training, model_type, total_timesteps, data_path)
    return sanitize_nill({"message": f"Training started for {model_type}", "timesteps": total_timesteps})

# ─── Prediction ───────────────────────────────────────────────────
@app.post("/api/predict")
def predict_loan(application: schemas.LoanApplicationCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    # Save application
    db_app = models.LoanApplication(**application.model_dump())
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    
    # Build state vector for RL models (10 features matching the env)
    state = np.array([
        application.age,
        0 if application.gender == "Male" else 1,
        {"Salaried": 0, "Self-Employed": 1, "Unemployed": 2}.get(application.employment, 0),
        application.income,
        application.repayment_history,
        application.loan_amount,
        {"Personal": 0, "Business": 1, "Education": 2, "Home": 3}.get(application.loan_purpose, 0),
        application.existing_debt,
        application.loan_tenure,
        {"Urban": 0, "Semiurban": 1, "Rural": 2}.get(application.region, 0),
    ], dtype=np.float32)
    
    preds = prediction_service.predict_all_models(state, application.credit_score, application.income)
    
    behavioral_score = None
    if application.interview_notes:
        try:
            polarity = TextBlob(application.interview_notes).sentiment.polarity
            # Map -1 to 1 into 0 to 1 where 1 is good (high polarity)
            behavioral_score = (polarity + 1) / 2
            
            # Slightly adjust risk score based on behavioral score (e.g. up to 10% change)
            # If behavioral score is high (near 1), reduce risk score.
            risk_adjustment = (0.5 - behavioral_score) * 0.1 
            preds['risk_score'] = max(0.0, min(1.0, preds['risk_score'] + risk_adjustment))
        except Exception as e:
            logger.error(f"TextBlob error: {e}")
    
    db_pred = models.RLPrediction(
        application_id=db_app.id,
        ppo_prediction=preds['ppo_prediction'],
        dqn_prediction=preds['dqn_prediction'],
        ddqn_prediction=preds['ddqn_prediction'],
        sac_prediction=preds['sac_prediction'],
        best_model=preds['best_model'],
        recommended_interest_rate=preds['recommended_interest_rate'],
        risk_score=preds['risk_score'],
        confidence=preds['confidence'],
        behavioral_score=behavioral_score
    )
    db.add(db_pred)
    db.commit()
    
    result = {
        "application_id": db_app.id,
        "applicant_info": {
            "age": application.age,
            "gender": application.gender,
            "employment": application.employment,
            "income": application.income,
            "region": application.region,
        },
        "financial_details": {
            "credit_score": application.credit_score,
            "loan_amount": application.loan_amount,
            "existing_debt": application.existing_debt,
            "loan_tenure": application.loan_tenure,
            "repayment_history": application.repayment_history,
            "loan_purpose": application.loan_purpose,
        },
        "rl_predictions": {
            "PPO": preds['ppo_prediction'],
            "DQN": preds['dqn_prediction'],
            "DDQN": preds['ddqn_prediction'],
            "SAC": preds['sac_prediction'],
        },
        "risk_analysis": {
            "risk_score": preds['risk_score'],
            "risk_level": "Low" if preds['risk_score'] < 0.33 else "Medium" if preds['risk_score'] < 0.66 else "High",
            "confidence": preds['confidence'],
            "behavioral_score": behavioral_score,
        },
        "recommended_pricing": {
            "best_model": preds['best_model'],
            "recommended_interest_rate": preds['recommended_interest_rate'],
            "expected_profit": round(preds.get('recommended_interest_rate', 0) * application.loan_amount / 100, 2) if preds.get('recommended_interest_rate') else None,
        }
    }
    
    # ─── Ollama Explainability ───
    # We call Ollama to explain the RL decision. It never overrides the RL decision.
    explanation = generate_explanation(application.model_dump(), result["recommended_pricing"])
    result["ollama_explanation"] = explanation
    
    return sanitize_nill(result)

# ─── Models ───────────────────────────────────────────────────────
@app.get("/api/models")
def get_models():
    """Return the list of model names and their load status."""
    return sanitize_nill(prediction_service.get_model_status())

@app.post("/api/models/reload")
def reload_model(model_type: str, current_user: models.User = Depends(auth.require_admin)):
    """Manually reload a specific model from disk into the prediction cache."""
    if model_type not in ["PPO", "DQN", "DDQN", "SAC"]:
        raise HTTPException(status_code=400, detail="Invalid model type.")
    success = prediction_service.reload_model(model_type)
    return sanitize_nill({"model": model_type, "loaded": success})

@app.post("/api/models/reload-all")
def reload_all_models():
    """Reload all models from disk into the prediction cache."""
    prediction_service.load_all_models()
    return sanitize_nill(prediction_service.get_model_status())

# ─── Training History ─────────────────────────────────────────────
@app.get("/api/history")
def get_training_history(model_name: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.TrainingHistory)
    if model_name:
        query = query.filter(models.TrainingHistory.model_name == model_name)
    results = query.order_by(models.TrainingHistory.timestamp.desc()).limit(500).all()
    return sanitize_nill([{
        "model_name": r.model_name,
        "episode": r.episode,
        "reward": r.reward,
        "loss": r.loss,
        "learning_rate": r.learning_rate,
        "timestamp": str(r.timestamp)
    } for r in results])

# ─── Applications ─────────────────────────────────────────────────
@app.get("/api/applications")
def get_applications(db: Session = Depends(get_db)):
    apps = db.query(models.LoanApplication).order_by(models.LoanApplication.timestamp.desc()).limit(100).all()
    results = []
    for a in apps:
        pred = db.query(models.RLPrediction).filter(models.RLPrediction.application_id == a.id).first()
        decision = db.query(models.LoanDecision).filter(models.LoanDecision.application_id == a.id).first()
        results.append({
            "id": a.id,
            "age": a.age,
            "gender": a.gender,
            "employment": a.employment,
            "income": a.income,
            "credit_score": a.credit_score,
            "loan_amount": a.loan_amount,
            "loan_purpose": a.loan_purpose,
            "existing_debt": a.existing_debt,
            "loan_tenure": a.loan_tenure,
            "repayment_history": a.repayment_history,
            "region": a.region,
            "timestamp": str(a.timestamp),
            "prediction": {
                "best_model": pred.best_model if pred else None,
                "recommended_rate": pred.recommended_interest_rate if pred else None,
                "risk_score": pred.risk_score if pred else None,
                "confidence": pred.confidence if pred else None,
                "ppo": pred.ppo_prediction if pred else None,
                "dqn": pred.dqn_prediction if pred else None,
                "ddqn": pred.ddqn_prediction if pred else None,
                "sac": pred.sac_prediction if pred else None,
            } if pred else None,
            "decision": {
                "officer_name": decision.officer_name if decision else None,
                "approved": decision.approved if decision else None,
                "remarks": decision.remarks if decision else None,
                "timestamp": str(decision.timestamp) if decision else None,
            } if decision else None,
        })
    return sanitize_nill(results)


# ─── AB Testing API ────────────────────────────────────────────

@app.post("/api/ab-test/campaigns", response_model=schemas.ABTestCampaignOut)
def create_ab_campaign(campaign: schemas.ABTestCampaignCreate, db: Session = Depends(get_db)):
    db_campaign = models.ABTestCampaign(**campaign.model_dump())
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

@app.get("/api/ab-test/campaigns", response_model=List[schemas.ABTestCampaignOut])
def get_ab_campaigns(db: Session = Depends(get_db)):
    return db.query(models.ABTestCampaign).order_by(models.ABTestCampaign.timestamp.desc()).all()

@app.post("/api/ab-test/campaigns/{campaign_id}/toggle")
def toggle_campaign(campaign_id: int, db: Session = Depends(get_db)):
    campaign = db.query(models.ABTestCampaign).filter(models.ABTestCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.is_active = not campaign.is_active
    db.commit()
    return {"status": "success", "is_active": campaign.is_active}

# ─── Dashboard Summary ───────────────────────────────────────────
@app.get("/api/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    total_apps = db.query(models.LoanApplication).count()
    total_decisions = db.query(models.LoanDecision).count()
    approvals = db.query(models.LoanDecision).filter(models.LoanDecision.approved == True).count()
    rejections = db.query(models.LoanDecision).filter(models.LoanDecision.rejected == True).count()
    
    avg_risk = db.query(func.avg(models.RLPrediction.risk_score)).scalar()
    avg_rate = db.query(func.avg(models.RLPrediction.recommended_interest_rate)).scalar()
    avg_reward_row = db.query(func.avg(models.TrainingHistory.reward)).scalar()
    
    # Find best model by avg reward
    best_model_row = db.query(
        models.TrainingHistory.model_name,
        func.avg(models.TrainingHistory.reward).label('avg_r')
    ).group_by(models.TrainingHistory.model_name).order_by(func.avg(models.TrainingHistory.reward).desc()).first()
    
    total_loan_value = db.query(func.sum(models.LoanApplication.loan_amount)).scalar()
    
    return sanitize_nill({
        "total_applications": total_apps,
        "total_decisions": total_decisions,
        "approval_rate": round(approvals / total_decisions, 4) if total_decisions > 0 else 0,
        "default_rate": round(rejections / total_decisions, 4) if total_decisions > 0 else 0,
        "average_interest_rate": round(avg_rate, 2) if avg_rate else None,
        "average_risk_score": round(avg_risk, 4) if avg_risk else None,
        "average_reward": round(avg_reward_row, 4) if avg_reward_row else None,
        "best_rl_model": best_model_row[0] if best_model_row else None,
        "portfolio_value": round(total_loan_value, 2) if total_loan_value else 0,
        "approvals": approvals,
        "rejections": rejections,
    })

# ─── Analytics ────────────────────────────────────────────────────
@app.get("/api/analytics")
def get_analytics(db: Session = Depends(get_db)):
    total_apps = db.query(models.LoanApplication).count()
    total_decisions = db.query(models.LoanDecision).count()
    approvals = db.query(models.LoanDecision).filter(models.LoanDecision.approved == True).count()
    
    # Get all predictions for distribution data
    predictions = db.query(models.RLPrediction).all()
    risk_scores = [p.risk_score for p in predictions if p.risk_score is not None]
    rates = [p.recommended_interest_rate for p in predictions if p.recommended_interest_rate is not None]
    
    # Get all applications for distribution data
    apps = db.query(models.LoanApplication).all()
    incomes = [a.income for a in apps if a.income is not None]
    credit_scores = [a.credit_score for a in apps if a.credit_score is not None]
    loan_amounts = [a.loan_amount for a in apps if a.loan_amount is not None]
    ages = [a.age for a in apps if a.age is not None]
    
    return sanitize_nill({
        "total_applications": total_apps,
        "approval_rate": round(approvals / total_decisions, 4) if total_decisions > 0 else 0,
        "risk_scores": risk_scores,
        "interest_rates": rates,
        "incomes": incomes,
        "credit_scores": credit_scores,
        "loan_amounts": loan_amounts,
        "ages": ages,
    })

# ─── Loan Decisions ───────────────────────────────────────────────
@app.post("/api/loan-decisions")
def submit_decision(decision: schemas.LoanDecisionCreate, db: Session = Depends(get_db)):
    db_dec = models.LoanDecision(**decision.model_dump())
    db.add(db_dec)
    db.commit()
    db.refresh(db_dec)
    
    # Update analytics table
    total_decisions = db.query(models.LoanDecision).count()
    approvals = db.query(models.LoanDecision).filter(models.LoanDecision.approved == True).count()
    avg_risk = db.query(func.avg(models.RLPrediction.risk_score)).scalar()
    total_value = db.query(func.sum(models.LoanApplication.loan_amount)).scalar()
    
    analytics = models.Analytics(
        portfolio_value=total_value or 0,
        total_profit=0,
        average_risk=avg_risk or 0,
        default_rate=round((total_decisions - approvals) / total_decisions, 4) if total_decisions > 0 else 0,
        approval_rate=round(approvals / total_decisions, 4) if total_decisions > 0 else 0,
    )
    db.add(analytics)
    db.commit()
    
    return sanitize_nill({"message": "Decision saved successfully", "decision_id": db_dec.id})

@app.get("/api/loan-decisions")
def get_decisions(db: Session = Depends(get_db)):
    decisions = db.query(models.LoanDecision).order_by(models.LoanDecision.timestamp.desc()).all()
    results = []
    for d in decisions:
        app = db.query(models.LoanApplication).filter(models.LoanApplication.id == d.application_id).first()
        pred = db.query(models.RLPrediction).filter(models.RLPrediction.application_id == d.application_id).first()
        results.append({
            "decision_id": d.id,
            "application_id": d.application_id,
            "officer_name": d.officer_name,
            "remarks": d.remarks,
            "approved": d.approved,
            "rejected": d.rejected,
            "timestamp": str(d.timestamp),
            "applicant_income": app.income if app else None,
            "loan_amount": app.loan_amount if app else None,
            "interest_rate": pred.recommended_interest_rate if pred else None,
            "risk_score": pred.risk_score if pred else None,
            "best_model": pred.best_model if pred else None,
        })
    return sanitize_nill(results)

# ─── Model Comparison ─────────────────────────────────────────────
@app.get("/api/model-comparison")
def get_model_comparison(db: Session = Depends(get_db)):
    results = db.query(
        models.TrainingHistory.model_name,
        func.avg(models.TrainingHistory.reward).label("avg_reward"),
        func.count(models.TrainingHistory.id).label("episodes"),
        func.min(models.TrainingHistory.reward).label("min_reward"),
        func.max(models.TrainingHistory.reward).label("max_reward"),
    ).group_by(models.TrainingHistory.model_name).all()
    
    return sanitize_nill([{
        "model": r[0],
        "avg_reward": round(r[1], 4) if r[1] else None,
        "episodes": r[2],
        "min_reward": round(r[3], 4) if r[3] else None,
        "max_reward": round(r[4], 4) if r[4] else None,
    } for r in results])

# ─── Chat & Settings ──────────────────────────────────────────────
@app.get("/api/chat/conversations")
def get_conversations(user_role: str, db: Session = Depends(get_db)):
    convs = db.query(models.ChatConversation).filter(models.ChatConversation.user_role == user_role).order_by(models.ChatConversation.timestamp.desc()).all()
    return [{"id": c.id, "title": c.title, "is_favorite": c.is_favorite, "timestamp": c.timestamp} for c in convs]

@app.post("/api/chat/conversations")
def create_conversation(conv: schemas.ChatConversationCreate, db: Session = Depends(get_db)):
    db_conv = models.ChatConversation(title=conv.title, user_role=conv.user_role)
    db.add(db_conv)
    db.commit()
    db.refresh(db_conv)
    return {"id": db_conv.id, "title": db_conv.title}

@app.delete("/api/chat/conversations/{conv_id}")
def delete_conversation(conv_id: int, db: Session = Depends(get_db)):
    db.query(models.ChatMessage).filter(models.ChatMessage.conversation_id == conv_id).delete()
    db.query(models.ChatConversation).filter(models.ChatConversation.id == conv_id).delete()
    db.commit()
    return {"status": "deleted"}

@app.get("/api/chat/messages/{conv_id}")
def get_messages(conv_id: int, db: Session = Depends(get_db)):
    msgs = db.query(models.ChatMessage).filter(models.ChatMessage.conversation_id == conv_id).order_by(models.ChatMessage.timestamp.asc()).all()
    return [{"role": m.role, "content": m.content, "timestamp": m.timestamp} for m in msgs]

@app.post("/api/chat/messages/{conv_id}")
def create_message(conv_id: int, msg: schemas.ChatMessageCreate, db: Session = Depends(get_db)):
    db_msg = models.ChatMessage(conversation_id=conv_id, role=msg.role, content=msg.content)
    db.add(db_msg)
    db.commit()
    return {"status": "ok"}

@app.get("/api/settings/{user_role}")
def get_settings(user_role: str, db: Session = Depends(get_db)):
    settings = db.query(models.UserSettings).filter(models.UserSettings.user_role == user_role).first()
    if not settings:
        return {"ollama_model": "gemma2:2b", "theme": "light"}
    return {"ollama_model": settings.ollama_model, "theme": settings.theme}

@app.post("/api/settings")
def update_settings(settings: schemas.UserSettingsUpdate, db: Session = Depends(get_db)):
    db_settings = db.query(models.UserSettings).filter(models.UserSettings.user_role == settings.user_role).first()
    if db_settings:
        db_settings.ollama_model = settings.ollama_model
        db_settings.theme = settings.theme
    else:
        db_settings = models.UserSettings(**settings.model_dump())
        db.add(db_settings)
    db.commit()
    return {"status": "ok"}

# ─── Fairness Auditing ──────────────────────────────────────────

@app.get("/api/analytics/fairness-audit")
def get_fairness_audit(db: Session = Depends(get_db)):
    """Runs the fairness audit on demand and returns the results."""
    # We pass the db session so we can run the query synchronously.
    # Note that run_fairness_audit returns dict which FastAPI converts to JSON.
    return run_fairness_audit(db)

@app.get("/api/analytics/fairness-audit/history", response_model=List[schemas.FairnessAuditLogOut])
def get_fairness_audit_history(db: Session = Depends(get_db)):
    """Returns the historical audit logs from the database."""
    return db.query(models.FairnessAuditLog).order_by(models.FairnessAuditLog.timestamp.desc()).all()
