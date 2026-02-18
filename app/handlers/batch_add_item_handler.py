"""
Batch Add Item Handler
Handles adding multiple items in a single command
"""

from sqlalchemy.orm import Session
from app.core.intent_handler import IntentHandler
from app.core.conversation_context import ConversationContext
from app.services.cart_service import CartService
from app.services.item_validation_service import ItemValidationService
from typing import List, Dict, Any


class BatchAddItemHandler(IntentHandler):
    """Handle adding multiple items at once"""
    
    @property
    def intent_name(self) -> str:
        return "batch_add_item"
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.cart_service = CartService(db)
        self.validation_service = ItemValidationService(db)
    
    def can_handle(self, context: ConversationContext) -> bool:
        """Can handle if we have multiple items parsed"""
        return hasattr(context, 'batch_items') and len(context.batch_items) > 1
    
    def handle(self, context: ConversationContext) -> ConversationContext:
        """Add multiple items to cart"""
        
        batch_items = getattr(context, 'batch_items', [])
        
        if not batch_items:
            context.handler_result = {
                "success": False,
                "error": "No items to add"
            }
            return context
        
        results = []
        success_count = 0
        failed_items = []
        
        for item_data in batch_items:
            item_name = item_data.get("item", "").strip()
            size = item_data.get("size")
            quantity = item_data.get("quantity", 1)
            
            # Validate item
            success, validated_data, error_msg = self.validation_service.validate_full_item(
                item_name, size
            )
            
            if not success:
                failed_items.append({
                    "item": item_name,
                    "error": error_msg
                })
                continue
            
            # Add to cart
            try:
                result = self.cart_service.add_item(
                    user_id=context.user_id,
                    menu_size_id=validated_data["menu_size_id"],
                    quantity=quantity
                )
                
                if result.get("success"):
                    success_count += 1
                    results.append({
                        "item": validated_data["item_name"],
                        "size": validated_data["size"],
                        "quantity": quantity,
                        "success": True
                    })
                else:
                    failed_items.append({
                        "item": item_name,
                        "error": result.get("error", "Unknown error")
                    })
            except Exception as e:
                failed_items.append({
                    "item": item_name,
                    "error": str(e)
                })
        
        # Build result message
        if success_count > 0:
            # Build success message
            added_items = []
            for result in results:
                if result["success"]:
                    size_text = f" ({result['size']})" if result.get('size') else ""
                    qty_text = f" x{result['quantity']}" if result['quantity'] > 1 else ""
                    added_items.append(f"{result['item']}{size_text}{qty_text}")
            
            message = f"Added {success_count} items to cart: " + ", ".join(added_items)
            
            if failed_items:
                failed_names = [f"{item['item']} ({item['error']})" for item in failed_items]
                message += f"\n\nCouldn't add: " + ", ".join(failed_names)
            
            context.handler_result = {
                "success": True,
                "message": message,
                "added_count": success_count,
                "failed_count": len(failed_items),
                "results": results
            }
        else:
            # All failed
            error_details = "\n".join([f"  • {item['item']}: {item['error']}" for item in failed_items])
            context.handler_result = {
                "success": False,
                "error": f"Couldn't add any items:\n{error_details}"
            }
        
        # Update cart
        cart_data = self.cart_service.view_cart(context.user_id)
        context.current_cart = cart_data
        
        return context
