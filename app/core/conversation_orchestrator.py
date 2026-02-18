# app/core/conversation_orchestrator.py
from sqlalchemy.orm import Session
from app.core.conversation_context import ConversationContext
from app.core.intent_router import IntentRouter
from app.nlp.HybridNLPService import HybridNLPService
from app.llm.LLMProviderFactory import LLMProviderFactory
from app.chat.services.state_manager import StateManager
from app.services.pricing_service import PricingService
from app.services.clarification_service import ClarificationService
from app.services.recommendation_engine import RecommendationEngine
from app.services.multi_item_parser import MultiItemParser
import json


class ConversationOrchestrator:
    """
    Main orchestration engine that coordinates the entire conversation flow
    
    Flow:
    1. Extract intent using HybridNLPService (regex → fallback to LLM)
    2. Load user state (cart, history) from StateManager
    3. Check for clarification needs
    4. Route to appropriate intent handler
    5. Execute handler (interacts with DB through services)
    6. Generate response using LLM with recommendations
    7. Save conversation history
    8. Return response
    """
    
    def __init__(self, db: Session, intent_router: IntentRouter, 
                 nlp_service: HybridNLPService = None,
                 llm_provider_name: str = None):
        self.db = db
        self.intent_router = intent_router
        self.nlp_service = nlp_service or HybridNLPService(llm_provider_name)
        self.state_manager = StateManager(db)
        self.pricing_service = PricingService(db)
        self.llm_provider = LLMProviderFactory.get_provider(llm_provider_name)
        # NEW: Clarification and Recommendation services
        self.clarification_service = ClarificationService(db)
        self.rec_engine = RecommendationEngine(db)
        self.multi_item_parser = MultiItemParser()

    
    def process_message(self, user_id: int, message: str) -> ConversationContext:
        """
        Main entry point - process user message and return response
        
        Args:
            user_id: User ID
            message: User's message text
        
        Returns: ConversationContext with bot response
        """
        
        # Step 1: Create context
        context = self._create_context(user_id, message)
        
        # Step 2: Extract intent (HybridNLP: regex → fallback to LLM)
        context = self._extract_intent(context)
        
        # Step 3: Load user state from DB
        context = self._load_user_state(context)
        
        # Step 4: Route to handler and execute (with clarification support)
        context = self._execute_handler(context)
        
        # Step 5: Generate bot response (with recommendations)
        context = self._generate_response(context)
        
        # Step 6: Save conversation history
        self._save_conversation(context)
        
        return context
    
    def _create_context(self, user_id: int, message: str) -> ConversationContext:
        """Create initial conversation context"""
        context = ConversationContext(
            user_id=user_id,
            user_message=message
        )
        return context
    
    def _extract_intent(self, context: ConversationContext) -> ConversationContext:
        """
        Extract intent using HybridNLPService
        Now handles multi-item commands from RegexNLPService
        """
        nlp_result = self.nlp_service.parse(context.user_message)
        
        context.intent = nlp_result.get("intent")
        context.entities = nlp_result.get("entities", {})
        context.detected_language = nlp_result.get("lang", "en")
        context.nlp_source = nlp_result.get("source", "llm")
        context.nlp_confidence = nlp_result.get("confidence", 1.0)
        
        # NEW: Handle multi-item batch from RegexNLPService
        if nlp_result.get("batch_items"):
            context.batch_items = nlp_result["batch_items"]
            print(f"✅ Multi-item detected: {context.batch_items}")
        
        return context

    
    def _load_user_state(self, context: ConversationContext) -> ConversationContext:
        """Load user state from StateManager (user data, cart, history)"""
        
        # Get conversation history
        history = self.state_manager.get_conversation_history(context.user_id)
        context.conversation_history = history
        
        # Get user data
        user_data = self.state_manager.get_user_state(context.user_id)
        context.user_data = user_data or {}
        
        # Get current cart
        cart_data = self.state_manager.get_user_cart(context.user_id)
        context.current_cart = cart_data or {"items": [], "total": 0}
        
        return context
    
    def _execute_handler(self, context: ConversationContext) -> ConversationContext:
        
        if context.intent:
            
            # NEW: Skip clarification if we have batch_items!
            has_batch = hasattr(context, 'batch_items') and context.batch_items
            
            if not has_batch:  # Only check clarification for single items
                needs_clarification, missing_fields = self.clarification_service.needs_clarification(
                    context.intent,
                    context.entities
                )
                
                if needs_clarification:
                    question = self.clarification_service.generate_clarification_question(
                        intent=context.intent,
                        entities=context.entities,
                        missing_fields=missing_fields,
                        lang=context.detected_language,
                        context={"current_cart": context.current_cart}
                    )
                    context.bot_response = question
                    context.handler_executed = False
                    context.handler_result = {
                        "clarification_needed": True,
                        "missing_fields": missing_fields
                    }
                    return context
        
        # Route to handler
        context = self.intent_router.execute(context)
        
        # FORCE REFRESH CART after remove/add operations to prevent stale data
        if context.intent in ["add_item", "remove_item"] and context.handler_executed:
            cart_data = self.state_manager.get_user_cart(context.user_id)
            context.current_cart = cart_data or {"items": [], "total": 0}
            print(f"✅ Cart refreshed after {context.intent}: {len(cart_data.get('items', []))} items")
        
        if not context.handler_executed:
            context.handler_result = {
                "error": f"No handler for intent: {context.intent}",
                "fallback_to_llm": True
            }
        
        return context
    
    def _generate_response(self, context: ConversationContext) -> ConversationContext:
        """
        Generate bot response using LLM
        NEW: Adds personalized recommendations after successful operations
        LLM has access to conversation history and handler results for context
        Falls back to handler result if LLM unavailable
        
        CRITICAL FIX: For checkout, NEVER use LLM to prevent hallucination of order details
        """
        
        # FIX #1: For checkout, ALWAYS use structured response from actual data
        # This prevents LLM from hallucinating quantities, prices, or items
        if context.intent == "checkout" and context.handler_result.get("success"):
            items_summary = []
            for item in context.handler_result.get("items", []):
                items_summary.append(
                    f"• {item['quantity']}x {item['size']} {item['name']} - ₹{item['subtotal']}"
                )
            
            order_summary = "\n".join(items_summary)
            context.bot_response = f"""✅ Order placed successfully!

{order_summary}

💰 Total: ₹{context.handler_result['total_price']}
📦 Order ID: #{context.handler_result['order_id']}

Your delicious pizza will be ready in 30-40 minutes. Thank you for your order! 🍕"""
            
            return context
        
        # Existing clarification check
        if context.handler_result and context.handler_result.get("clarification_needed"):
            # bot_response is already set to the clarification question
            # Just return without calling LLM
            return context
    
        # If LLM provider is not available, use handler result or generic response
        if not self.llm_provider:
            if context.handler_executed and context.handler_result.get("success"):
                context.bot_response = context.handler_result.get("message", "Request processed successfully")
                
                # Add recommendations for successful add_item
                if context.intent == "add_item":
                    recommendations = self.rec_engine.get_recommendations(
                        user_id=context.user_id,
                        context={"current_cart": context.current_cart},
                        max_items=2
                    )
                    if recommendations:
                        rec_text = self.rec_engine.format_recommendations_text(
                            recommendations, 
                            context.detected_language
                        )
                        # Fix: Check if bot_response exists before appending
                        if context.bot_response:
                            context.bot_response += f"\n\n{rec_text}"
                        else:
                            context.bot_response = rec_text
                
                return context
            else:
                context.bot_response = "I understand your message, but I need more specific menu commands. Try: 'add [item] [size]', 'show cart', or 'checkout'"
                return context
        
        # Build context for LLM
        history_text = context.get_history_text()
        
        handler_summary = ""
        if context.handler_executed:
            handler_summary = f"Handler executed: {context.handler_name}\nResults: {context.handler_result}"
        else:
            handler_summary = f"No specific handler for intent: {context.intent}"
        
        # FIX #2: Provide EXACT handler data to LLM to prevent hallucination
        llm_context = f"""Conversation History:
{history_text}

User's current message: {context.user_message}

Handler Information:
{handler_summary}

CRITICAL - ACTUAL DATA (do not modify or guess):
Handler Result: {json.dumps(context.handler_result, indent=2)}

Current cart: {context.current_cart}

Instructions:
1. For orders/checkout: Use EXACT quantities, prices, and items from handler_result
2. Never guess or change numerical values
3. Be natural but accurate
4. Keep it concise (1-2 sentences)

Please provide a natural, friendly response based ONLY on the actual data above."""
        
        try:
            # Generate response
            response = self.llm_provider.generate_response(
                text=context.user_message,
                context=llm_context,
                lang=context.detected_language
            )
            
            # Only use LLM response if valid
            if response and isinstance(response, str):
                context.bot_response = response
            else:
                # Fallback to handler message
                context.bot_response = context.handler_result.get("message", "Request processed")
            
            # NEW: Add recommendations after successful add_item operations
            if context.intent == "add_item" and context.handler_result.get("success"):
                recommendations = self.rec_engine.get_recommendations(
                    user_id=context.user_id,
                    context={"current_cart": context.current_cart},
                    max_items=2
                )
                
                if recommendations:
                    rec_text = self.rec_engine.format_recommendations_text(
                        recommendations, 
                        context.detected_language
                    )
                    if context.bot_response:
                        context.bot_response += f"\n\n{rec_text}"
                    else:
                        context.bot_response = rec_text
            
        except Exception as e:
            print(f"⚠️ Error generating LLM response: {e}")
            if context.handler_executed and context.handler_result.get("success"):
                context.bot_response = context.handler_result.get("message", "Request processed")
            else:
                context.bot_response = "I processed your request. Please let me know if you need anything else."
        
        return context
    
    def _save_conversation(self, context: ConversationContext):
        """Save conversation history to database"""
        
        # Save user message
        self.state_manager.add_message_to_history(
            user_id=context.user_id,
            role="user",
            content=context.user_message,
            metadata={
                "intent": context.intent,
                "nlp_source": context.nlp_source
            }
        )
        
        # Save bot response
        self.state_manager.add_message_to_history(
            user_id=context.user_id,
            role="bot",
            content=context.bot_response,
            metadata={
                "handler": context.handler_name,
                "handler_executed": context.handler_executed
            }
        )