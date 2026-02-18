from sqlalchemy.orm import Session
from app.core.intent_handler import IntentHandler
from app.core.conversation_context import ConversationContext
from app.services.menu_service import MenuService


class BrowseMenuHandler(IntentHandler):
    """Handle menu browsing and item queries"""
    
    @property
    def intent_name(self) -> str:
        return "browse_menu"
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.menu_service = MenuService(db)
    
    def can_handle(self, context: ConversationContext) -> bool:
        """Can handle browse_menu or item_info intents"""
        return context.intent in ["browse_menu", "item_info", "get_price"]
    
    def handle(self, context: ConversationContext) -> ConversationContext:
        """
        Browse menu or get item information
        Entities: {item: "pizza name"} or empty for full menu
        """
        try:
            item_query = context.entities.get("item")
            category = context.entities.get("category")
            
            if item_query:
                # Get specific item
                item = self.menu_service.get_item_by_name(item_query)
                
                if not item:
                    context.handler_result = {
                        "success": False,
                        "error": f"Item '{item_query}' not found in menu"
                    }
                    return context
                
                # Format item with prices
                item_data = self.menu_service.get_item_with_all_prices(item.id)
                formatted = self.menu_service.format_item_for_display(item)
                
                context.handler_result = {
                    "success": True,
                    "item": item_data,
                    "formatted": formatted
                }
                
                context.response_data = {
                    "item_name": item.name,
                    "category": item.category,
                    "sizes": item_data.get("sizes"),
                    "formatted_display": formatted
                }
                
            elif category:
                # Get category items
                items = self.menu_service.get_all_items_by_category(category)
                
                if not items:
                    context.handler_result = {
                        "success": False,
                        "error": f"No items found in category '{category}'"
                    }
                    return context
                
                # Format items
                items_list = [
                    self.menu_service.format_item_for_display(item)
                    for item in items
                ]
                
                context.handler_result = {
                    "success": True,
                    "category": category,
                    "items": items_list,
                    "count": len(items)
                }
                
                context.response_data = {
                    "category": category,
                    "items": items_list
                }
                
            else:
                # Get all pizzas and additions
                pizzas = self.menu_service.get_all_pizzas()
                additions = self.menu_service.get_all_additions()
                
                items_data = {
                    "pizzas": [self.menu_service.format_item_for_display(p) for p in pizzas],
                    "additions": [self.menu_service.format_item_for_display(a) for a in additions]
                }
                
                context.handler_result = {
                    "success": True,
                    "menu": items_data,
                    "pizza_count": len(pizzas),
                    "addition_count": len(additions)
                }
                
                context.response_data = items_data
            
            return context
            
        except Exception as e:
            context.handler_result = {
                "success": False,
                "error": str(e)
            }
            return context
