# app/handlers/add_item_handler.py (ENHANCED WITH SUGGESTIONS)
from sqlalchemy.orm import Session
from app.core.intent_handler import IntentHandler
from app.core.conversation_context import ConversationContext
from app.services.item_validation_service import ItemValidationService
from app.services.cart_service import CartService
from app.services.suggestion_service import SuggestionService


class AddItemHandler(IntentHandler):
    """Handle adding items to cart with full validation and suggestion support"""
    
    @property
    def intent_name(self) -> str:
        return "add_item"
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.validation_service = ItemValidationService(db)
        self.cart_service = CartService(db)
    
    def can_handle(self, context: ConversationContext) -> bool:
        """Can handle if intent is add_item and has required entities"""
        if context.intent != "add_item":
            return False
        
        # Need at least item name
        return "item" in context.entities
    
    def handle(self, context: ConversationContext) -> ConversationContext:
        """
        Add item to cart with full validation:
        1. Check item exists in menu
        2. Check item is available  
        3. Check size is valid
        4. Check size is available
        5. If item not found exactly, suggest similar items (NEW!)
        6. Add to cart
        """
        try:
            item_name = context.entities.get("item")
            size = context.entities.get("size", "")
            quantity = context.entities.get("quantity") or 1
            
            print(f"🔍 AddItemHandler: item='{item_name}', size='{size}', qty={quantity}")
            
            # Validate item and size
            success, item_data, validation_msg = self.validation_service.validate_full_item(
                item_name, 
                size
            )
            
            if not success:
                # Check if it's a "not found" error with suggestions
                if "Did you mean:" in validation_msg:
                    # NEW: Create a suggestion instead of just returning error
                    return self._handle_item_not_found_with_suggestions(
                        context, item_name, size, quantity, validation_msg
                    )
                
                # Other validation errors (out of stock, invalid size, etc.)
                context.handler_result = {
                    "success": False,
                    "error": validation_msg,
                    "suggestion": self.validation_service.get_available_sizes_str(
                        item_data.get("item_id")
                    ) if item_data else None
                }
                return context
            
            # Item and size validated, add to cart
            menu_size_id = item_data["menu_size_id"]
            
            result = self.cart_service.add_item(
                user_id=context.user_id,
                menu_size_id=menu_size_id,
                quantity=quantity
            )
            
            context.handler_result = result
            
            # Update cart in context
            cart_data = self.cart_service.view_cart(context.user_id)
            context.current_cart = cart_data
            
            return context
            
        except Exception as e:
            print(f"⚠️ Error in AddItemHandler: {e}")
            import traceback
            traceback.print_exc()
            context.handler_result = {
                "success": False,
                "error": f"Error adding item: {str(e)}"
            }
            return context
    
    def _handle_item_not_found_with_suggestions(
        self, 
        context: ConversationContext, 
        original_item: str,
        size: str,
        quantity: int,
        validation_msg: str
    ) -> ConversationContext:
        """
        NEW: When item not found, suggest similar items and store as pending suggestion
        
        Example:
        User: "add one cola"
        System: "'one cola' not found. Did you mean: Cola? (Say 'yes' to add it)"
        User: "yes"
        System: [ConfirmationHandler executes pending suggestion]
        """
        # Extract the first suggestion from validation message
        # validation_msg = "'one cola' not found. Did you mean: Cola, Pepsi, Sprite?"
        try:
            if "Did you mean:" in validation_msg:
                suggestions_part = validation_msg.split("Did you mean:")[1].split("?")[0].strip()
                first_suggestion = suggestions_part.split(",")[0].strip()
                
                print(f"💡 Suggesting: {first_suggestion}")
                
                # Create a pending suggestion
                suggestion = SuggestionService.create_add_item_suggestion(
                    item=first_suggestion,
                    size=size or "REG",  # Default to REG if no size specified
                    quantity=quantity
                )
                
                # Store in user session
                SuggestionService.set_pending_suggestion(context.user_data, suggestion)
                
                # Format natural question
                lang = context.detected_language or "en"
                
                if lang == "ar":
                    question = f"لم أجد '{original_item}'. هل تقصد {first_suggestion}؟"
                else:
                    size_text = f" {size}" if size else ""
                    qty_text = f"{quantity} " if quantity > 1 else ""
                    question = f"I couldn't find '{original_item}'. Did you mean {qty_text}{size_text} {first_suggestion}? (Say 'yes' to add it)"
                
                context.handler_result = {
                    "success": False,
                    "error": validation_msg,
                    "suggestion_created": True,
                    "message": question
                }
                
                # Set bot response directly
                context.bot_response = question
                
                return context
        except Exception as e:
            print(f"⚠️ Error creating suggestion: {e}")
        
        # Fallback: just return the validation error
        context.handler_result = {
            "success": False,
            "error": validation_msg
        }
        return context