from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from datetime import datetime


# ============= AUTH SCHEMAS =============
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    username: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    username: Optional[str]
    plan: str
    analyses_this_month: int
    total_analyses: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= ANALYSIS SCHEMAS =============
class AnalyzeScriptRequest(BaseModel):
    script: str = Field(..., min_length=50, max_length=50000)
    script_type: str = Field(default="general")
    title: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "script": "Did you know that 95% of YouTubers quit before hitting 1000 subscribers? I was almost one of them...",
                "script_type": "tutorial",
                "title": "How I Grew From 0 to 100K Subscribers"
            }
        }


class ImprovementObject(BaseModel):
    section: str
    issue: str
    suggestion: str


class AnalysisResponse(BaseModel):
    id: str
    overall_score: float
    virality_prediction: str
    
    scores: Dict[str, float]
    strengths: List[str]
    weaknesses: List[str]
    improvements: List[ImprovementObject]
    
    viral_patterns_detected: List[str]
    viral_patterns_missing: List[str]
    
    word_count: int
    estimated_duration: str
    estimated_retention: Optional[str]
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class ScriptCompareRequest(BaseModel):
    script_a: str = Field(..., min_length=50)
    script_b: str = Field(..., min_length=50)
    title: Optional[str] = None


class ComparisonResponse(BaseModel):
    winner: str
    confidence: str
    reason: str
    score_a: float
    score_b: float
    key_differences: List[str]
    recommendation: str


class ImproveScriptRequest(BaseModel):
    script: str = Field(..., min_length=50)
    focus_area: str = Field(default="all")  # hook, retention, structure, all


class ImprovementResponse(BaseModel):
    improved_script: str
    changes_made: List[str]
    improvement_score: float
    explanation: str


# ============= HISTORY SCHEMAS =============
class AnalysisListItem(BaseModel):
    id: str
    title: Optional[str]
    overall_score: float
    virality_prediction: str
    word_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisHistory(BaseModel):
    total: int
    analyses: List[AnalysisListItem]


# ============= STATS SCHEMAS =============
class UserStats(BaseModel):
    total_analyses: int
    average_score: float
    best_score: float
    analyses_this_month: int
    plan_limit: int
    remaining_analyses: int
