from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LoanApplicationBase(BaseModel):
    age: int
    gender: str
    employment: str
    income: float
    credit_score: float
    loan_amount: float
    loan_purpose: str
    existing_debt: float
    loan_tenure: int
    repayment_history: float
    region: str
    collateral: str = "None"
    existing_loans: int = 0
    education: str = "High School"
    interview_notes: Optional[str] = None

class LoanApplicationCreate(LoanApplicationBase):
    pass

class ChatMessageCreate(BaseModel):
    role: str
    content: str

class ChatConversationCreate(BaseModel):
    title: str
    user_role: str

class UserSettingsUpdate(BaseModel):
    user_role: str
    ollama_model: str
    theme: str

class LoanApplicationOut(LoanApplicationBase):
    id: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class RLPredictionOut(BaseModel):
    application_id: int
    best_model: str
    recommended_interest_rate: float
    risk_score: float
    confidence: float
    behavioral_score: Optional[float] = None
    
    class Config:
        from_attributes = True

class LoanDecisionCreate(BaseModel):
    application_id: int
    officer_name: str
    remarks: str
    approved: bool
    rejected: bool

class TrainingHistoryOut(BaseModel):
    model_name: str
    episode: int
    reward: float
    loss: float
    timestamp: datetime
    
    class Config:
        from_attributes = True

class TrainingProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CustomDatasetCreate(BaseModel):
    project_id: int
    filename: str
    filepath: str
    schema_mapping: str
    row_count: int

class TrainingExperimentCreate(BaseModel):
    project_id: int
    dataset_id: int
    algorithm: str
    profile_name: str
    hyperparameters: str

class TrainingExperimentUpdate(BaseModel):
    status: Optional[str] = None
    best_reward: Optional[float] = None
    end_time: Optional[datetime] = None

class TrainingProjectOut(TrainingProjectCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class CustomDatasetOut(CustomDatasetCreate):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class TrainingExperimentOut(TrainingExperimentCreate):
    id: int
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    best_reward: Optional[float] = None
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "Customer"

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class ABTestCampaignCreate(BaseModel):
    campaign_name: str
    model_a: str
    model_b: str
    split_a: int

class ABTestCampaignOut(ABTestCampaignCreate):
    id: int
    is_active: bool
    timestamp: datetime
    class Config:
        from_attributes = True

class FairnessAuditLogOut(BaseModel):
    id: int
    model_name: str
    feature: str
    group_a: str
    group_b: str
    disparate_impact: Optional[float] = None
    equal_opportunity_diff: Optional[float] = None
    flagged: bool
    timestamp: datetime
    class Config:
        from_attributes = True
