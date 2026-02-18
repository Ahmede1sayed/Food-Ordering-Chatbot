from sqlalchemy.orm import Session
from app.core.intent_handler import IntentHandler
from app.core.enhanced_conversation_context import ConversationContext
from app.services.cart_service import CartService


class GetCartHandler(IntentHandler):
    """Handle showing cart contents"""
    
    @property
    def intent_name(self) -> str:
        return "view_cart"
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.cart_service = CartService(db)
    
    def can_handle(self, context: ConversationContext) -> bool:
        """Can always handle view_cart intent"""
        return context.intent == "view_cart"
    
    def handle(self, context: ConversationContext) -> ConversationContext:
        """
        Get and return cart contents
        """
        try:
            cart_data = self.cart_service.view_cart(context.user_id)
            
            if not cart_data.get("success"):
                context.handler_result = {
                    "success": False,
                    "error": "Could not retrieve cart"
                }
                return context
            
            # Format cart for display
            cart_summary = self.cart_service.get_cart_summary(context.user_id)
            
            context.handler_result = {
                "success": True,
                "cart_data": cart_data,
                "summary": cart_summary
            }
            
            # Update context cart
            context.current_cart = cart_data
            context.response_data = {"cart_summary": cart_summary}
            
            return context
            
        except Exception as e:
            context.handler_result = {
                "success": False,
                "error": str(e)
            }
            return context
