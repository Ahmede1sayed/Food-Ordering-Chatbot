# app/handlers/confirmation_handler.py
from sqlalchemy.orm import Session
from app.core.intent_handler import IntentHandler
from app.core.enhanced_conversation_context import ConversationContext
from app.services.cart_service import CartService
from app.services.menu_service import MenuService
from datetime import datetime, timedelta


class ConfirmationHandler(IntentHandler):
    """
    Handle confirmation/rejection of pending suggestions
    
    Flow:
    1. Check if user has a pending suggestion in session
    2. If yes → Execute the suggested action
    3. If no → Politely inform there's nothing to confirm
    """
    
    @property
    def intent_name(self) -> str:
        return "confirmation"
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.cart_service = CartService(db)
        self.menu_service = MenuService(db)
    
    def can_handle(self, context: ConversationContext) -> bool:
        """Can handle if intent is confirmation"""
        return context.intent == "confirmation"
    
    def handle(self, context: ConversationContext) -> ConversationContext:
        """
        Execute pending suggestion if one exists
        """
        try:
            # Check if there's a pending suggestion
            pending = context.user_data.get("pending_suggestion")
            
            if not pending:
                # No pending suggestion
                context.handler_result = {
                    "success": False,
                    "message": "I'm not sure what you're confirming. Could you please be more specific?"
                }
                return context
            
            # Check if suggestion has expired (older than 5 minutes)
            created_at = pending.get("created_at")
            if created_at:
                created_time = datetime.fromisoformat(created_at)
                if datetime.now() - created_time > timedelta(minutes=5):
                    # Expired
                    context.handler_result = {
                        "success": False,
                        "message": "That suggestion has expired. What would you like to order?"
                    }
                    # Clear expired suggestion
                    context.user_data["pending_suggestion"] = None
                    return context
            
            # Execute the pending suggestion based on type
            suggestion_type = pending.get("type")
            
            if suggestion_type == "add_item":
                return self._handle_add_item_confirmation(context, pending)
            else:
                context.handler_result = {
                    "success": False,
                    "message": "I couldn't process that confirmation."
                }
                return context
            
        except Exception as e:
            print(f"⚠️ Error in ConfirmationHandler: {e}")
            import traceback
            traceback.print_exc()
            context.handler_result = {
                "success": False,
                "error": str(e)
            }
            return context
    
    def _handle_add_item_confirmation(self, context: ConversationContext, pending: dict) -> ConversationContext:
        """Handle confirmation for adding an item"""
        try:
            item_name = pending.get("item")
            size = pending.get("size")
            quantity = pending.get("quantity", 1)
            
            print(f"🔍 Confirming add: {quantity}x {size} {item_name}")
            
            # Find the menu item
            menu_items = self.menu_service.search_items(item_name)
            
            if not menu_items:
                context.handler_result = {
                    "success": False,
                    "message": f"Sorry, I couldn't find '{item_name}' in our menu anymore."
                }
                return context
            
            # Find matching size
            menu_item = menu_items[0]
            menu_size_id = None
            
            for size_option in menu_item.get("sizes", []):
                if size and size_option["size"] == size:
                    menu_size_id = size_option["menu_size_id"]
                    break
                elif not size and size_option["size"] == "REG":
                    menu_size_id = size_option["menu_size_id"]
                    break
            
            if not menu_size_id and menu_item.get("sizes"):
                # Use first available size
                menu_size_id = menu_item["sizes"][0]["menu_size_id"]
                size = menu_item["sizes"][0]["size"]
            
            if not menu_size_id:
                context.handler_result = {
                    "success": False,
                    "message": f"Sorry, I couldn't find the right size for {item_name}."
                }
                return context
            
            # Add to cart
            result = self.cart_service.add_item(
                user_id=context.user_id,
                menu_size_id=menu_size_id,
                quantity=quantity
            )
            
            if result.get("success"):
                # Clear pending suggestion
                context.user_data["pending_suggestion"] = None
                
                # Update cart in context
                cart_data = self.cart_service.view_cart(context.user_id)
                context.current_cart = cart_data
                
                context.handler_result = {
                    "success": True,
                    "message": f"✅ Added {quantity}x {size} {item_name} to your cart!",
                    "item_added": {
                        "name": item_name,
                        "size": size,
                        "quantity": quantity
                    }
                }
            else:
                context.handler_result = {
                    "success": False,
                    "message": result.get("message", "Failed to add item to cart")
                }
            
            return context
            
        except Exception as e:
            print(f"⚠️ Error adding confirmed item: {e}")
            context.handler_result = {
                "success": False,
                "error": str(e)
            }
            return context


class RejectionHandler(IntentHandler):
    """
    Handle rejection of pending suggestions
    User said "no" to a suggestion
    """
    
    @property
    def intent_name(self) -> str:
        return "rejection"
    
    def can_handle(self, context: ConversationContext) -> bool:
        return context.intent == "rejection"
    
    def handle(self, context: ConversationContext) -> ConversationContext:
        """Clear pending suggestion and ask what they want instead"""
        try:
            # Clear any pending suggestion
            had_pending = bool(context.user_data.get("pending_suggestion"))
            context.user_data["pending_suggestion"] = None
            
            if had_pending:
                context.handler_result = {
                    "success": True,
                    "message": "No problem! What would you like to order instead?"
                }
            else:
                context.handler_result = {
                    "success": True,
                    "message": "Okay! How can I help you?"
                }
            
            return context
            
        except Exception as e:
            print(f"⚠️ Error in RejectionHandler: {e}")
            context.handler_result = {
                "success": False,
                "error": str(e)
            }
            return context
