# app/handlers/remove_item_handler.py (WITH DEBUG LOGGING)
from sqlalchemy.orm import Session
from app.core.intent_handler import IntentHandler
from app.core.conversation_context import ConversationContext
from app.services.cart_service import CartService
import re


class RemoveItemHandler(IntentHandler):
    """Handle removing items from cart with quantity support"""
    
    @property
    def intent_name(self) -> str:
        return "remove_item"
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.cart_service = CartService(db)
    
    def can_handle(self, context: ConversationContext) -> bool:
        if context.intent != "remove_item":
            return False
        return "item" in context.entities and context.entities["item"]
    
    def handle(self, context: ConversationContext) -> ConversationContext:
        """Remove item from cart with optional quantity"""
        try:
            item_text = context.entities.get("item", "").strip()
            
            print(f"\n🔍 REMOVE HANDLER DEBUG:")
            print(f"   User message: {context.user_message}")
            print(f"   Item text from entities: '{item_text}'")
            
            if not item_text:
                context.handler_result = {
                    "success": False,
                    "error": "Please specify which item to remove"
                }
                return context
            
            # Extract quantity from item text (e.g., "2 pizza" → quantity=2, item="pizza")
            quantity_to_remove = None
            quantity_match = re.match(r'^(\d+)\s+(.+)$', item_text)
            if quantity_match:
                quantity_to_remove = int(quantity_match.group(1))
                item_name = quantity_match.group(2)
                print(f"   Extracted quantity: {quantity_to_remove}")
                print(f"   Extracted item name: '{item_name}'")
            else:
                item_name = item_text
                print(f"   No quantity specified, will remove all")
            
            # Get current cart BEFORE removal
            cart_data = self.cart_service.view_cart(context.user_id)
            print(f"   Cart BEFORE removal: {len(cart_data.get('items', []))} items")
            for cart_item in cart_data.get('items', []):
                print(f"      - {cart_item['quantity']}x {cart_item['item_name']}")
            
            if not cart_data.get("items"):
                context.handler_result = {
                    "success": False,
                    "error": "Your cart is empty"
                }
                return context
            
            # Find item in cart
            item_name_lower = item_name.lower()
            found_item = None
            
            for cart_item in cart_data["items"]:
                cart_item_name = cart_item["item_name"].lower()
                if item_name_lower in cart_item_name or cart_item_name in item_name_lower:
                    found_item = cart_item
                    print(f"   ✅ Found matching item: {cart_item['item_name']}")
                    break
            
            if not found_item:
                available = ", ".join([item["item_name"] for item in cart_data["items"]])
                print(f"   ❌ Item not found in cart")
                context.handler_result = {
                    "success": False,
                    "error": f"'{item_name}' not found in cart. You have: {available}"
                }
                return context
            
            menu_size_id = found_item["menu_size_id"]
            current_quantity = found_item["quantity"]
            print(f"   Current quantity in cart: {current_quantity}")
            print(f"   Menu size ID: {menu_size_id}")
            
            # If quantity specified, reduce by that amount
            if quantity_to_remove:
                print(f"   Attempting to remove {quantity_to_remove} items...")
                if quantity_to_remove >= current_quantity:
                    # Remove completely
                    print(f"   Removing all items (requested >= current)")
                    result = self.cart_service.remove_item(context.user_id, menu_size_id)
                    message = f"Removed all {found_item['item_name']} from cart"
                    result["message"] = message
                else:
                    # Reduce quantity
                    new_quantity = current_quantity - quantity_to_remove
                    print(f"   Reducing quantity to {new_quantity}")
                    result = self.cart_service.update_item_quantity(
                        context.user_id, 
                        menu_size_id, 
                        new_quantity
                    )
                    print(f"   update_item_quantity result: {result}")
                    
                    if not result.get("success"):
                        # Fallback: remove and re-add with new quantity
                        print(f"   Fallback: remove and re-add")
                        self.cart_service.remove_item(context.user_id, menu_size_id)
                        add_result = self.cart_service.add_item(context.user_id, menu_size_id, new_quantity)
                        print(f"   Re-add result: {add_result}")
                        result = {
                            "success": True,
                            "message": f"Removed {quantity_to_remove} {found_item['item_name']}, {new_quantity} remaining"
                        }
            else:
                # Remove completely
                print(f"   Removing all items (no quantity specified)")
                result = self.cart_service.remove_item(context.user_id, menu_size_id)
            
            print(f"   Final handler result: {result}")
            context.handler_result = result
            
            # Update cart - GET FRESH DATA
            cart_data_after = self.cart_service.view_cart(context.user_id)
            print(f"   Cart AFTER removal: {len(cart_data_after.get('items', []))} items")
            for cart_item in cart_data_after.get('items', []):
                print(f"      - {cart_item['quantity']}x {cart_item['item_name']}")
            
            context.current_cart = cart_data_after
            
            print(f"   ✅ Remove handler completed successfully\n")
            return context
            
        except Exception as e:
            print(f"⚠️ Error in RemoveItemHandler: {e}")
            import traceback
            traceback.print_exc()
            context.handler_result = {
                "success": False,
                "error": f"Error removing item: {str(e)}"
            }
            return context