"""
ScholarGuard Database Models
SQLAlchemy ORM Models for Academic Integrity Platform
"""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, 
    Text, Boolean, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class User(Base):
    """
    User model for teachers
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Submission(Base):
    """
    Submission model for uploaded files
    """
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # File information
    file_name = Column(String(255), nullable=False)
    
    # Analysis results
    similarity_score = Column(Float, nullable=True)
    ai_risk_score = Column(Float, nullable=True)
    ai_confidence = Column(String(50), nullable=True)
    recommendation = Column(Text, nullable=True)
    matched_sources = Column(JSON, nullable=True)  # Store as JSON array
    
    # Extracted text content
    text_content = Column(Text, nullable=True)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="submissions")
    
    def __repr__(self):
        return f"<Submission(id={self.id}, file_name='{self.file_name}', user_id={self.user_id})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "file_name": self.file_name,
            "similarity_score": self.similarity_score,
            "ai_risk_score": self.ai_risk_score,
            "ai_confidence": self.ai_confidence,
            "recommendation": self.recommendation,
            "matched_sources": self.matched_sources,
            "text_content": self.text_content,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None
        }