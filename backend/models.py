from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, Text
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, default="")
    phone_number = Column(String, default="")
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, 
            "email": self.email, 
            "full_name": self.full_name,
            "phone_number": self.phone_number,
            "role": self.role, 
            "is_active": self.is_active, 
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    file_name = Column(String, default="")
    similarity_score = Column(Float, default=0.0)
    ai_risk_score = Column(Float, default=0.0)
    ai_confidence = Column(String, default="Low")
    recommendation = Column(Text, default="")
    matched_sources = Column(JSON, default=list)
    text_content = Column(Text, default="")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    word_count = Column(Integer, default=0)
    sentence_count = Column(Integer, default=0)
    burstiness_score = Column(Float, default=0.0)
    vocabulary_richness = Column(Float, default=0.0)
    improvement_tips = Column(JSON, default=list)
