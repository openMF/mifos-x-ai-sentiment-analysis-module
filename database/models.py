from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from database.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="Customer")

class LoanApplication(Base):
    __tablename__ = "loan_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    age = Column(Integer)
    gender = Column(String)
    employment = Column(String)
    income = Column(Float)
    credit_score = Column(Float)
    loan_amount = Column(Float)
    loan_purpose = Column(String)
    existing_debt = Column(Float)
    loan_tenure = Column(Integer)
    repayment_history = Column(Float)
    region = Column(String)
    collateral = Column(String, default="None")
    existing_loans = Column(Integer, default=0)
    education = Column(String, default="High School")
    interview_notes = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class RLPrediction(Base):
    __tablename__ = "rl_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id"))
    ppo_prediction = Column(String)
    dqn_prediction = Column(String)
    ddqn_prediction = Column(String)
    sac_prediction = Column(String)
    best_model = Column(String)
    recommended_interest_rate = Column(Float)
    risk_score = Column(Float)
    confidence = Column(Float)
    behavioral_score = Column(Float, nullable=True)

class TrainingHistory(Base):
    __tablename__ = "training_history"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String)
    episode = Column(Integer)
    reward = Column(Float)
    loss = Column(Float)
    learning_rate = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class LoanDecision(Base):
    __tablename__ = "loan_decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("loan_applications.id"))
    officer_name = Column(String)
    remarks = Column(String)
    approved = Column(Boolean)
    rejected = Column(Boolean)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_value = Column(Float)
    total_profit = Column(Float)
    average_risk = Column(Float)
    default_rate = Column(Float)
    approval_rate = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class ChatConversation(Base):
    __tablename__ = "chat_conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="New Chat")
    user_role = Column(String)  # The UI role that created it (e.g. Loan Officer)
    is_favorite = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id"))
    role = Column(String) # 'user' or 'assistant'
    content = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_role = Column(String, unique=True, index=True) # e.g. "Administrator"
    ollama_model = Column(String, default="gemma2:2b")
    theme = Column(String, default="light")

class TrainingProject(Base):
    __tablename__ = "training_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CustomDataset(Base):
    __tablename__ = "custom_datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("training_projects.id"))
    filename = Column(String)
    filepath = Column(String)
    schema_mapping = Column(String) # JSON string of column mappings
    row_count = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TrainingExperiment(Base):
    __tablename__ = "training_experiments"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("training_projects.id"))
    dataset_id = Column(Integer, ForeignKey("custom_datasets.id"))
    algorithm = Column(String)
    profile_name = Column(String)
    hyperparameters = Column(String) # JSON string
    status = Column(String, default="Pending") # Pending, Running, Completed, Failed, Paused
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    best_reward = Column(Float, nullable=True)

class Checkpoint(Base):
    __tablename__ = "checkpoints"
    
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("training_experiments.id"))
    episode = Column(Integer)
    filepath = Column(String)
    reward = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class ABTestCampaign(Base):
    __tablename__ = "ab_test_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_name = Column(String, index=True)
    model_a = Column(String)
    model_b = Column(String)
    split_a = Column(Integer)
    is_active = Column(Boolean, default=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class FairnessAuditLog(Base):
    __tablename__ = "fairness_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, index=True)
    feature = Column(String)           # e.g. "gender", "region"
    group_a = Column(String)           # privileged group
    group_b = Column(String)           # unprivileged group
    disparate_impact = Column(Float, nullable=True)
    equal_opportunity_diff = Column(Float, nullable=True)
    flagged = Column(Boolean, default=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
