from sqlalchemy.orm import Session
from app.core.conversation_orchestrator import ConversationOrchestrator
from app.core.intent_router import IntentRouter
from app.nlp.HybridNLPService import HybridNLPService
from app.handlers import (
    AddItemHandler,
    RemoveItemHandler,
    GetCartHandler,
    CheckoutHandler,
    BrowseMenuHandler,
    BatchAddItemHandler,
    ClearCartHandler,
)


class ChatService:
    """
    Main chat service that orchestrates conversation flow
    Uses ConversationOrchestrator to process messages with handlers
    Gracefully handles initialization failures
    """
    
    def __init__(self, db: Session, llm_provider_name: str = None):
        self.db = db
        
        try:
            # Create intent router and register handlers
            self.intent_router = IntentRouter(db)
            self._register_handlers()
            
            # Create orchestrator
            self.orchestrator = ConversationOrchestrator(
                db=db,
                intent_router=self.intent_router,
                nlp_service=HybridNLPService(llm_provider_name),
                llm_provider_name=llm_provider_name
            )
            self.initialized = True
        except Exception as e:
            print(f"⚠️ ChatService initialization error: {e}")
            self.initialized = False
            self.orchestrator = None
    
    def _register_handlers(self):
        """Register all intent handlers"""
        handlers = [
            BatchAddItemHandler(self.db),  # MUST be before AddItemHandler!
            AddItemHandler(self.db),
            RemoveItemHandler(self.db),
            GetCartHandler(self.db),
            CheckoutHandler(self.db),
            BrowseMenuHandler(self.db),
            ClearCartHandler(self.db),
        ]
        self.intent_router.register_handlers(handlers)
    
    def handle_message(self, user_id: int, message: str) -> dict:
        """
        Main entry point - process user message and return response
        
        Args:
            user_id: User ID
            message: User's message
        
        Returns: Response dict with bot's response and metadata
        """
        if not self.initialized:
            return {
                "success": False,
                "error": "Chat service not properly initialized",
                "user_message": message,
                "bot_response": "Sorry, the service is unavailable. Please try again.",
                "intent": None,
                "nlp_source": None,
                "nlp_confidence": None,
                "handler_name": None,
                "handler_executed": False,
                "handler_result": None,
                "current_cart": None,
                "recommendations": None,
                "suggested_actions": None,
                "clarification_needed": False,
                "clarification_question": None,
                "metadata": None,
            }
        
        try:
            # Process through orchestrator
            context = self.orchestrator.process_message(user_id, message)
            
            # Check if clarification was needed
            is_clarification = bool(
                context.handler_result and
                context.handler_result.get("clarification_needed")
            )
            
            # Build response with ALL required fields
            return {
                "success": True,
                "user_message": message,
                "bot_response": context.bot_response or "I processed your request.",
                "intent": context.intent,
                "nlp_source": context.nlp_source,
                "nlp_confidence": getattr(context, 'nlp_confidence', None),
                "handler_name": context.handler_name,
                "handler_executed": context.handler_executed,
                "handler_result": context.handler_result,
                "current_cart": context.current_cart,
                "recommendations": getattr(context, 'recommendations', None),
                "suggested_actions": getattr(context, 'suggested_actions', None),
                # FIX: Properly set clarification fields
                "clarification_needed": is_clarification,
                "clarification_question": context.bot_response if is_clarification else None,
                "metadata": context.to_dict()
            }

        except Exception as e:
            import traceback
            print(f"⚠️ Error handling message: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Error processing message: {str(e)}",
                "user_message": message,
                "bot_response": "Sorry, I encountered an error. Please try again.",
                "intent": None,
                "nlp_source": "error",
                "nlp_confidence": None,
                "handler_name": None,
                "handler_executed": False,
                "handler_result": {"error": str(e)},
                "current_cart": None,
                "recommendations": None,
                "suggested_actions": None,
                "clarification_needed": False,
                "clarification_question": None,
                "metadata": {"error": str(e)},
            }