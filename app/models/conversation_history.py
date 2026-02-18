from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.base import Base


class ConversationHistory(Base):
    """Store conversation history for users"""
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    role = Column(String(10), nullable=False)  # "user" or "bot"
    content = Column(Text, nullable=False)  # Message content
    
    # Optional metadata
    metadata_ = Column(JSON, nullable=True)  # {intent, nlp_source, handler, etc}
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    user = relationship("User", backref="conversation_history")
