from sqlalchemy.orm import Session
from app.models.conversation_history import ConversationHistory
from app.models.user import User
from app.core.conversation_context import Message
from datetime import datetime


class StateManager:
    """
    Manages user state and conversation history
    Loads/saves from database
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_state(self, user_id: int) -> dict:
        """
        Get user data from database
        Returns: User info (name, phone, address, etc)
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return None
        
        return {
            "user_id": user.id,
            "name": getattr(user, "name", None),
            "phone": getattr(user, "phone", None),
            "address": getattr(user, "address", None),
            "created_at": user.created_at if hasattr(user, "created_at") else None
        }
    
    def get_user_cart(self, user_id: int) -> dict:
        """
        Get user's current cart from database
        Returns: {items: [...], total: ...}
        """
        from app.models.cart import Cart
        from app.services.cart_service import CartService
        
        cart_service = CartService(self.db)
        cart_data = cart_service.view_cart(user_id)
        
        return cart_data if cart_data.get("success") else {"items": [], "total_price": 0}
    
    def get_conversation_history(self, user_id: int, limit: int = 20) -> list:
        """
        Get conversation history for user from database
        Args:
            user_id: User ID
            limit: Maximum messages to retrieve
        Returns: List of Message objects
        """
        messages = (
            self.db.query(ConversationHistory)
            .filter(ConversationHistory.user_id == user_id)
            .order_by(ConversationHistory.created_at.desc())
            .limit(limit)
            .all()
        )
        
        # Reverse to get chronological order
        messages.reverse()
        
        # Convert to Message objects
        history = []
        for msg in messages:
            history.append(Message(
                role=msg.role,
                content=msg.content,
                timestamp=msg.created_at
            ))
        
        return history
    
    def add_message_to_history(self, user_id: int, role: str, content: str, 
                               metadata: dict = None):
        """
        Add message to conversation history in database
        Args:
            user_id: User ID
            role: "user" or "bot"
            content: Message content
            metadata: Optional metadata (intent, handler, etc)
        """
        history_record = ConversationHistory(
            user_id=user_id,
            role=role,
            content=content,
            metadata_=metadata
        )
        
        self.db.add(history_record)
        self.db.commit()
    
    def clear_conversation_history(self, user_id: int):
        """Clear all conversation history for user"""
        self.db.query(ConversationHistory).filter(
            ConversationHistory.user_id == user_id
        ).delete()
        self.db.commit()
    
    def update_user_state(self, user_id: int, **kwargs):
        """
        Update user state in database
        Args:
            user_id: User ID
            **kwargs: Fields to update (name, phone, address, etc)
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            # Create new user if doesn't exist
            user = User(id=user_id)
            self.db.add(user)
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        self.db.commit()

