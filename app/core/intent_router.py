from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.enhanced_conversation_context import ConversationContext
from app.core.intent_handler import IntentHandler
from app.handlers import (
    AddItemHandler,
    RemoveItemHandler,
    GetCartHandler,
    CheckoutHandler,
    BrowseMenuHandler,
    BatchAddItemHandler,
    ClearCartHandler,
    ConfirmationHandler,
    RejectionHandler,
)


class IntentRouter:
    """
    Routes parsed intents to appropriate handlers
    Uses can_handle() to match handlers - supports batch items!
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.handlers = [
            # BatchAddItemHandler MUST come BEFORE AddItemHandler!
            BatchAddItemHandler(db),
            AddItemHandler(db),
            RemoveItemHandler(db),
            GetCartHandler(db),
            CheckoutHandler(db),
            BrowseMenuHandler(db),
            ClearCartHandler(db),
            ConfirmationHandler(db),
            RejectionHandler(db),
        ]
    
    def register_handler(self, handler: IntentHandler):
        """Register a handler for an intent"""
        self.handlers.append(handler)
    
    def register_handlers(self, handlers: List[IntentHandler]):
        """Register multiple handlers at once"""
        self.handlers.extend(handlers)
    
    def route(self, context: ConversationContext) -> Optional[IntentHandler]:
        """
        Find appropriate handler using can_handle()
        This allows BatchAddItemHandler to intercept before AddItemHandler
        """
        if not context.intent:
            return None
        
        # Use can_handle() so BatchAddItemHandler gets priority
        # when batch_items exist on context
        for handler in self.handlers:
            if handler.can_handle(context):
                return handler
        
        return None
    
    def execute(self, context: ConversationContext) -> ConversationContext:
        """
        Route to handler and execute it
        """
        handler = self.route(context)
        
        if handler:
            context = handler.handle(context)
            context.handler_name = handler.intent_name
            context.handler_executed = True
        else:
            context.handler_result = {
                "error": f"No handler found for intent: {context.intent}"
            }
        
        return context