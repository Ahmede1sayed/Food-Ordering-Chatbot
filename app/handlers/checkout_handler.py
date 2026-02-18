from sqlalchemy.orm import Session
from app.core.intent_handler import IntentHandler
from app.core.enhanced_conversation_context import ConversationContext
from app.services.cart_service import CartService
from app.services.order_service import OrderService


class CheckoutHandler(IntentHandler):
    """Handle checkout and order placement"""
    
    @property
    def intent_name(self) -> str:
        return "checkout"
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.cart_service = CartService(db)
        self.order_service = OrderService(db)
    
    def can_handle(self, context: ConversationContext) -> bool:
        """Can handle checkout if user has items in cart"""
        if context.intent != "checkout":
            return False
        
        # Check if cart has items
        cart_data = context.current_cart
        return len(cart_data.get("items", [])) > 0
    
    def handle(self, context: ConversationContext) -> ConversationContext:
        """
        Checkout: create order from cart
        """
        try:
            # Check if cart is empty
            cart_data = self.cart_service.view_cart(context.user_id)
            
            if not cart_data.get("items"):
                context.handler_result = {
                    "success": False,
                    "error": "Your cart is empty. Cannot checkout."
                }
                return context
            
            # Create order
            order_result = self.order_service.checkout(context.user_id)
            
            if not order_result.get("success"):
                context.handler_result = {
                    "success": False,
                    "error": order_result.get("message", "Checkout failed")
                }
                return context
            
            context.handler_result = order_result
            
            # Update context - cart is now empty after checkout
            context.current_cart = {"items": [], "total_price": 0, "item_count": 0, "success": True}
            
            context.response_data = {
                "order_id": order_result.get("order_id"),
                "total_price": order_result.get("total_price"),
                "items": order_result.get("items")
            }
            
            return context
            
        except Exception as e:
            context.handler_result = {
                "success": False,
                "error": str(e)
            }
            return context
