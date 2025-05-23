from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from database import Base

class LLMResponse(Base):
    __tablename__ = "llm_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    operation_type = Column(String, index=True)  # e.g., "summarize", "extract", "simplify"
    input_hash = Column(String, index=True)  # Hash of the input text for caching
    response_text = Column(Text)
    
    # Relationship to the Document model
    document = relationship("Document")
