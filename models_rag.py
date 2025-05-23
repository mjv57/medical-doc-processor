# models_rag.py
from sqlalchemy import Column, Integer, String, Text, Float, JSON
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from sqlalchemy import Column, Integer, String, Text, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship

from database import Base

class UserQuestion(Base):
    __tablename__ = "user_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(JSON)  # Store sources as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())