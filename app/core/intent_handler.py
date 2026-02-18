from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from app.core.enhanced_conversation_context import ConversationContext


class IntentHandler(ABC):
    """
    Base class for all intent handlers
    Each handler processes a specific intent (add_item, checkout, etc)
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    @property
    @abstractmethod
    def intent_name(self) -> str:
        """Return the intent this handler processes"""
        pass
    
    @abstractmethod
    def can_handle(self, context: ConversationContext) -> bool:
        """
        Check if this handler can process the given context
        Args:
            context: ConversationContext with parsed intent
        Returns: True if handler can process, False otherwise
        """
        pass
    
    @abstractmethod
    def handle(self, context: ConversationContext) -> ConversationContext:
        """
        Execute handler logic and update context with results
        Args:
            context: ConversationContext to process
        Returns: Updated ConversationContext with results
        """
        pass
