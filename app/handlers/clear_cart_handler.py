from sqlalchemy.orm import Session
from app.core.intent_handler import IntentHandler
from app.core.enhanced_conversation_context import ConversationContext
from app.services.cart_service import CartService


class ClearCartHandler(IntentHandler):
    """Handle clearing the entire cart"""
    
    @property
    def intent_name(self) -> str:
        return "clear_cart"
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.cart_service = CartService(db)
    
    def can_handle(self, context: ConversationContext) -> bool:
        return context.intent == "clear_cart"
    
    def handle(self, context: ConversationContext) -> ConversationContext:
        try:
            result = self.cart_service.clear_cart(context.user_id)
            
            context.handler_result = {
                "success": True,
                "message": "Cart cleared! Ready for a new order 🛒"
            }
            
            # Update cart in context (now empty)
            context.current_cart = {
                "success": True,
                "items": [],
                "total_price": 0,
                "item_count": 0
            }
            
            return context
            
        except Exception as e:
            print(f"⚠️ Error clearing cart: {e}")
            context.handler_result = {
                "success": False,
                "error": f"Error clearing cart: {str(e)}"
            }
            return context
