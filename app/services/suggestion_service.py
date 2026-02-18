# app/services/suggestion_service.py
from datetime import datetime
from typing import Optional, Dict, Any


class SuggestionService:
    """
    Service to manage pending suggestions for users
    
    When the chatbot suggests something (e.g., "Would you like to add cola?"),
    it stores the suggestion here so that when the user says "yes", 
    the system knows what to execute.
    
    Storage: User's session data (user_data dict in ConversationContext)
    """
    
    @staticmethod
    def create_add_item_suggestion(item: str, size: str = None, quantity: int = 1) -> Dict[str, Any]:
        """
        Create a suggestion for adding an item
        
        Args:
            item: Item name (e.g., "Cola", "Margherita Pizza")
            size: Size code (e.g., "L", "M", "S", "REG")
            quantity: Number of items
        
        Returns:
            Suggestion dict to store in user_data["pending_suggestion"]
        """
        return {
            "type": "add_item",
            "item": item,
            "size": size,
            "quantity": quantity,
            "created_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def create_clarification_suggestion(intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a suggestion for clarification
        
        Example: User says "add pizza" without size
        System asks "What size? (S/M/L)"
        User says "large"
        """
        return {
            "type": "clarification",
            "intent": intent,
            "entities": entities,
            "created_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def set_pending_suggestion(user_data: Dict[str, Any], suggestion: Dict[str, Any]) -> None:
        """
        Store a pending suggestion in user's session
        
        Args:
            user_data: The user_data dict from ConversationContext
            suggestion: The suggestion dict from create_add_item_suggestion()
        """
        user_data["pending_suggestion"] = suggestion
        print(f"💾 Stored pending suggestion: {suggestion}")
    
    @staticmethod
    def get_pending_suggestion(user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get the pending suggestion for a user
        
        Returns:
            Suggestion dict or None
        """
        return user_data.get("pending_suggestion")
    
    @staticmethod
    def clear_pending_suggestion(user_data: Dict[str, Any]) -> None:
        """Clear the pending suggestion"""
        if "pending_suggestion" in user_data:
            del user_data["pending_suggestion"]
            print(f"🗑️ Cleared pending suggestion")
    
    @staticmethod
    def has_pending_suggestion(user_data: Dict[str, Any]) -> bool:
        """Check if user has a pending suggestion"""
        return bool(user_data.get("pending_suggestion"))
    
    @staticmethod
    def format_suggestion_for_user(suggestion: Dict[str, Any], lang: str = "en") -> str:
        """
        Format a suggestion into a natural question for the user
        
        Args:
            suggestion: Suggestion dict
            lang: Language code
        
        Returns:
            Natural language question
        """
        suggestion_type = suggestion.get("type")
        
        if suggestion_type == "add_item":
            item = suggestion.get("item")
            size = suggestion.get("size")
            quantity = suggestion.get("quantity", 1)
            
            if lang == "ar":
                size_text = f" {size}" if size else ""
                qty_text = f"{quantity} " if quantity > 1 else ""
                return f"هل تريد إضافة {qty_text}{item}{size_text} إلى السلة؟"
            else:
                size_text = f" {size}" if size else ""
                qty_text = f"{quantity} " if quantity > 1 else ""
                return f"Would you like to add {qty_text}{size_text} {item} to your cart?"
        
        return "Would you like to proceed?"


# Example usage in your handlers or orchestrator:

def example_usage_in_handler():
    """
    Example: How to use SuggestionService when LLM suggests something
    """
    from app.services.suggestion_service import SuggestionService
    
    # When LLM or handler wants to suggest something:
    suggestion = SuggestionService.create_add_item_suggestion(
        item="Cola",
        size="REG",
        quantity=2
    )
    
    # Store it in user's session
    # (context.user_data is automatically persisted by StateManager)
    SuggestionService.set_pending_suggestion(context.user_data, suggestion)
    
    # Generate the question
    question = SuggestionService.format_suggestion_for_user(suggestion, lang="en")
    # "Would you like to add 2 REG Cola to your cart?"
    
    context.bot_response = question
    
    # Later, when user says "yes":
    # ConfirmationHandler will read context.user_data["pending_suggestion"]
    # and execute the action
