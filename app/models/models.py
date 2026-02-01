from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Float, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    
    # Subscription
    plan = Column(String, default="free")  # free, pro, creator
    stripe_customer_id = Column(String, nullable=True)
    subscription_status = Column(String, default="inactive")
    
    # Usage tracking
    analyses_this_month = Column(Integer, default=0)
    total_analyses = Column(Integer, default=0)
    
    # Profile
    youtube_channel = Column(String, nullable=True)
    niche = Column(String, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    analyses = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>"


class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Script data
    script_text = Column(Text, nullable=False)
    script_type = Column(String, default="general")  # tutorial, vlog, review, etc.
    title = Column(String, nullable=True)
    
    # Analysis results
    overall_score = Column(Float, nullable=False)
    virality_prediction = Column(String, nullable=False)  # Low, Medium, High
    
    scores = Column(JSON, nullable=False)  # {hook: 8, retention: 7, ...}
    strengths = Column(JSON, nullable=False)  # List of strings
    weaknesses = Column(JSON, nullable=False)
    improvements = Column(JSON, nullable=False)  # List of improvement objects
    
    viral_patterns_detected = Column(JSON, default=[])
    viral_patterns_missing = Column(JSON, default=[])
    
    # Metadata
    word_count = Column(Integer)
    estimated_duration = Column(String)
    estimated_retention = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="analyses")
    
    def __repr__(self):
        return f"<Analysis {self.id} - Score: {self.overall_score}>"


class Comparison(Base):
    __tablename__ = "comparisons"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Scripts being compared
    analysis_a_id = Column(String, ForeignKey("analyses.id"))
    analysis_b_id = Column(String, ForeignKey("analyses.id"))
    
    # Results
    winner = Column(String)  # "A" or "B"
    confidence = Column(String)  # "high", "medium", "low"
    reason = Column(Text)
    
    score_a = Column(Float)
    score_b = Column(Float)
    
    key_differences = Column(JSON, default=[])
    recommendation = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Comparison {self.id} - Winner: {self.winner}>"


class APIKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    key = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<APIKey {self.name or self.id}>"
