"""
Enhanced Conversation Context with Multi-Turn Dialogue Support
Improvements:
- Dialogue state tracking
- Clarification questions
- Context memory
- Session management
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DialogueState(Enum):
    """States for multi-turn dialogues"""
    IDLE = "idle"
    AWAITING_SIZE = "awaiting_size"
    AWAITING_QUANTITY = "awaiting_quantity"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    AWAITING_ADDRESS = "awaiting_address"
    AWAITING_PAYMENT = "awaiting_payment"
    CLARIFYING_ITEM = "clarifying_item"


@dataclass
class Message:
    """Enhanced message with metadata"""
    role: str  # "user", "bot", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    intent: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PendingAction:
    """Tracks incomplete actions requiring clarification"""
    action_type: str  # "add_item", "remove_item", etc
    missing_info: List[str]  # ["size", "quantity"]
    partial_data: Dict[str, Any]  # {"item": "margherita pizza"}
    created_at: datetime = field(default_factory=datetime.utcnow)
    attempts: int = 0


@dataclass
class ConversationContext:
    """
    Enhanced context object for multi-turn conversations
    Contains all information needed for processing user message
    """
    # ===== User & Session Info =====
    user_id: int
    user_message: str

    session_id: Optional[str] = None
    
    # ===== Current Message =====
    detected_language: str = "en"
    
    # ===== NLP Results =====
    intent: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)
    nlp_source: str = "none"  # "regex", "llm", "clarification"
    nlp_confidence: float = 1.0
    
    # ===== Conversation History =====
    conversation_history: List[Message] = field(default_factory=list)
    
    # ===== User State =====
    user_data: Dict[str, Any] = field(default_factory=dict)
    current_cart: Dict[str, Any] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)  # NEW: User preferences
    
    # ===== Multi-Turn Dialogue State =====
    dialogue_state: DialogueState = DialogueState.IDLE
    pending_action: Optional[PendingAction] = None
    clarification_needed: bool = False
    clarification_question: Optional[str] = None
    
    # ===== Context Memory =====
    last_mentioned_item: Optional[str] = None
    last_mentioned_size: Optional[str] = None
    last_order_id: Optional[int] = None
    context_variables: Dict[str, Any] = field(default_factory=dict)  # Flexible context storage
    
    # ===== Handler Results =====
    handler_executed: bool = False
    handler_name: Optional[str] = None
    handler_result: Dict[str, Any] = field(default_factory=dict)
    
    # ===== Bot Response =====
    bot_response: Optional[str] = None
    response_data: Dict[str, Any] = field(default_factory=dict)
    suggested_actions: List[str] = field(default_factory=list)  # NEW: Action suggestions
    
    # ===== Recommendations =====
    recommendations: List[Dict[str, Any]] = field(default_factory=list)  # NEW
    
    # ===== Metadata =====
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # ===== Methods =====
    
    def add_to_history(self, role: str, content: str, **kwargs):
        """Add message to conversation history with metadata"""
        msg = Message(
            role=role,
            content=content,
            intent=kwargs.get('intent', self.intent),
            entities=kwargs.get('entities', self.entities),
            metadata=kwargs.get('metadata', {})
        )
        self.conversation_history.append(msg)
    
    def get_history_text(self, max_messages: int = 10) -> str:
        """Get formatted history for LLM context"""
        if not self.conversation_history:
            return ""
        
        history = ""
        for msg in self.conversation_history[-max_messages:]:
            history += f"{msg.role}: {msg.content}\n"
        
        return history
    
    def get_history_with_intents(self, max_messages: int = 10) -> str:
        """Get history with intent information for better context"""
        if not self.conversation_history:
            return ""
        
        history = ""
        for msg in self.conversation_history[-max_messages:]:
            intent_info = f" [{msg.intent}]" if msg.intent else ""
            history += f"{msg.role}{intent_info}: {msg.content}\n"
        
        return history
    
    def set_pending_action(self, action_type: str, missing_info: List[str], 
                          partial_data: Dict[str, Any]):
        """Set a pending action that needs clarification"""
        self.pending_action = PendingAction(
            action_type=action_type,
            missing_info=missing_info,
            partial_data=partial_data
        )
        self.clarification_needed = True
    
    def resolve_pending_action(self, new_data: Dict[str, Any]) -> bool:
        """
        Resolve pending action with new data
        Returns True if all required info is now present
        """
        if not self.pending_action:
            return False
        
        # Merge new data
        self.pending_action.partial_data.update(new_data)
        
        # Check if all missing info is now present
        still_missing = [
            info for info in self.pending_action.missing_info 
            if info not in self.pending_action.partial_data or 
               self.pending_action.partial_data[info] is None
        ]
        
        if not still_missing:
            # All info present, resolve
            self.entities = self.pending_action.partial_data
            self.intent = self.pending_action.action_type
            self.pending_action = None
            self.clarification_needed = False
            self.dialogue_state = DialogueState.IDLE
            return True
        else:
            # Still missing info
            self.pending_action.missing_info = still_missing
            self.pending_action.attempts += 1
            return False
    
    def update_context_memory(self):
        """Update context memory with current entities"""
        if 'item' in self.entities and self.entities['item']:
            self.last_mentioned_item = self.entities['item']
        
        if 'size' in self.entities and self.entities['size']:
            self.last_mentioned_size = self.entities['size']
        
        if 'order_id' in self.handler_result:
            self.last_order_id = self.handler_result['order_id']
    
    def get_context_for_clarification(self) -> Dict[str, Any]:
        """Get relevant context for generating clarification questions"""
        return {
            "last_mentioned_item": self.last_mentioned_item,
            "last_mentioned_size": self.last_mentioned_size,
            "current_cart": self.current_cart,
            "pending_action": self.pending_action,
            "dialogue_state": self.dialogue_state.value
        }
    
    def to_dict(self) -> dict:
        """Convert to dict for JSON serialization"""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "intent": self.intent,
            "entities": self.entities,
            "nlp_source": self.nlp_source,
            "nlp_confidence": self.nlp_confidence,
            "dialogue_state": self.dialogue_state.value,
            "clarification_needed": self.clarification_needed,
            "handler_name": self.handler_name,
            "handler_result": self.handler_result,
            "bot_response": self.bot_response,
            "response_data": self.response_data,
            "recommendations": self.recommendations,
            "suggested_actions": self.suggested_actions,
            "context_variables": self.context_variables
        }
