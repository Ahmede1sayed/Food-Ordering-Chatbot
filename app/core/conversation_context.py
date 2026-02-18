from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Message:
    """Single message in conversation"""
    role: str  # "user" or "bot"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConversationContext:
    """
    Context object that travels through the orchestration pipeline
    Contains all information needed for processing user message
    """
    # User & Session info
    user_id: int
    
    # Current message
    user_message: str
    detected_language: str = "en"  # Language detected by NLP
    
    # NLP Results
    intent: Optional[str] = None  # e.g. "add_item", "checkout", "browse_menu"
    entities: Dict[str, Any] = field(default_factory=dict)  # e.g. {item: "pizza", size: "L"}
    nlp_source: str = "none"  # "regex" or "llm"
    nlp_confidence: float = 1.0
    
    # Conversation History
    conversation_history: List[Message] = field(default_factory=list)
    
    # User State (from DB)
    user_data: Dict[str, Any] = field(default_factory=dict)  # name, phone, address, etc
    current_cart: Dict[str, Any] = field(default_factory=dict)  # cart items, total
    
    # Handler Results
    handler_executed: bool = False
    handler_name: Optional[str] = None
    handler_result: Dict[str, Any] = field(default_factory=dict)  # Result from handler
    
    # Bot Response
    bot_response: Optional[str] = None
    response_data: Dict[str, Any] = field(default_factory=dict)  # Extra data for response
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append(Message(role=role, content=content))
    
    def get_history_text(self) -> str:
        """Get formatted history for LLM context"""
        if not self.conversation_history:
            return ""
        
        history = ""
        for msg in self.conversation_history[-10:]:  # Last 10 messages for context
            history += f"{msg.role}: {msg.content}\n"
        
        return history
    
    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization"""
        return {
            "user_id": self.user_id,
            "intent": self.intent,
            "entities": self.entities,
            "nlp_source": self.nlp_source,
            "handler_name": self.handler_name,
            "handler_result": self.handler_result,
            "bot_response": self.bot_response,
            "response_data": self.response_data
        }
