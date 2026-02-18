"""
Clarification Service
Handles incomplete user requests and generates intelligent clarification questions
"""

from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.services.menu_service import MenuService


class ClarificationService:
    """
    Generates and handles clarification questions for incomplete user requests
    Implements multi-turn dialogue for better UX
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.menu_service = MenuService(db)
    
    def needs_clarification(self, intent: str, entities: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check if intent needs clarification
        
        Args:
            intent: Detected intent
            entities: Extracted entities
        
        Returns:
            (needs_clarification: bool, missing_fields: List[str])
        """
        required_fields = self._get_required_fields(intent, entities)
        missing = []
        
        for field in required_fields:
            if field not in entities or entities[field] is None:
                missing.append(field)
        
        return len(missing) > 0, missing
    
    def _get_required_fields(self, intent: str, entities: Dict[str, Any] = None) -> List[str]:
        """Get required fields for each intent"""
        entities = entities or {}
        
        if intent == "add_item":
            # Check if item is an addition (fries, cola, etc.)
            item_name = (entities.get("item") or "").lower()            
            # Additions that only have REG size - don't need size specification
            additions_keywords = ["fries", "cola", "juice", "water", "drink"]
            is_addition = any(keyword in item_name for keyword in additions_keywords)
            
            if is_addition:
                return ["item"]  # Only need item name, not size
            else:
                return ["item", "size"]  # Pizzas need size
        
        requirements = {
            "remove_item": ["item"],
            "track_order": ["order_id"],
            "modify_order": ["order_id", "action"],
        }
        return requirements.get(intent, [])
    
    def generate_clarification_question(
        self, 
        intent: str, 
        entities: Dict[str, Any],
        missing_fields: List[str],
        lang: str = "en",
        context: Dict[str, Any] = None
    ) -> str:
        """
        Generate intelligent clarification question
        
        Args:
            intent: The intent being clarified
            entities: Partial entities
            missing_fields: List of missing required fields
            lang: Language code
            context: Additional context (cart, history, etc)
        
        Returns:
            Clarification question string
        """
        context = context or {}
        
        if intent == "add_item":
            return self._clarify_add_item(entities, missing_fields, lang, context)
        elif intent == "remove_item":
            return self._clarify_remove_item(entities, missing_fields, lang, context)
        elif intent == "track_order":
            return self._clarify_track_order(entities, missing_fields, lang)
        else:
            return self._generic_clarification(missing_fields, lang)
    
    def _clarify_add_item(
        self, 
        entities: Dict[str, Any], 
        missing: List[str],
        lang: str,
        context: Dict[str, Any]
    ) -> str:
        """Generate clarification for add_item intent"""
        
        item_name = entities.get('item')
        size = entities.get('size')
        
        # Missing item completely
        if 'item' in missing:
            if lang == "ar":
                return "عايز تطلب إيه؟ قول اسم البيتزا أو الإضافة."
            return "What would you like to order? Please tell me the item name."
        
        # Have item, missing size
        if 'size' in missing and item_name:
            # Get available sizes for this item
            sizes_info = self._get_available_sizes(item_name)
            
            if not sizes_info:
                if lang == "ar":
                    return f"آسف، مش لاقي '{item_name}' في القائمة. ممكن تتأكد من الاسم؟"
                return f"Sorry, I couldn't find '{item_name}' in our menu. Could you check the name?"
            
            # Format size options
            if lang == "ar":
                size_text = self._format_sizes_arabic(sizes_info)
                return f"أي حجم عايز من {item_name}؟\n{size_text}"
            else:
                size_text = self._format_sizes_english(sizes_info)
                return f"What size would you like for {item_name}?\n{size_text}"
        
        return self._generic_clarification(missing, lang)
    
    def _clarify_remove_item(
        self, 
        entities: Dict[str, Any], 
        missing: List[str],
        lang: str,
        context: Dict[str, Any]
    ) -> str:
        """Generate clarification for remove_item intent"""
        
        # Get current cart
        cart_items = context.get('current_cart', {}).get('items', [])
        
        if not cart_items:
            if lang == "ar":
                return "السلة فاضية، مفيهاش حاجة."
            return "Your cart is empty. There's nothing to remove."
        
        if 'item' in missing:
            # Show cart and ask which to remove
            cart_text = self._format_cart_items(cart_items, lang)
            
            if lang == "ar":
                return f"عايز تشيل إيه؟\nفي السلة دلوقتي:\n{cart_text}"
            return f"What would you like to remove?\nCurrently in your cart:\n{cart_text}"
        
        return self._generic_clarification(missing, lang)
    
    def _clarify_track_order(
        self, 
        entities: Dict[str, Any], 
        missing: List[str],
        lang: str
    ) -> str:
        """Generate clarification for track_order intent"""
        
        if 'order_id' in missing:
            if lang == "ar":
                return "محتاج رقم الطلب عشان اتابعه. رقم الطلب إيه؟"
            return "I need your order number to track it. What's your order number?"
        
        return self._generic_clarification(missing, lang)
    
    def _generic_clarification(self, missing: List[str], lang: str) -> str:
        """Generic clarification message"""
        
        if lang == "ar":
            fields = "، ".join(missing)
            return f"محتاج معلومات إضافية: {fields}"
        
        fields = ", ".join(missing)
        return f"I need more information: {fields}"
    
    def _get_available_sizes(self, item_name: str) -> List[Dict[str, Any]]:
        """Get available sizes and prices for an item using case-insensitive search"""
        try:
            # Use correct method name: get_item_by_name (not find_item_by_name)
            menu_item = self.menu_service.get_item_by_name(item_name, exact_match=False)
            
            if not menu_item:
                # Try word-by-word search as fallback
                words = item_name.lower().split()
                for word in words:
                    if len(word) > 3:  # Skip short words
                        menu_item = self.menu_service.get_item_by_name(word, exact_match=False)
                        if menu_item:
                            break
            
            if not menu_item:
                return []
            
            sizes = []
            for size in menu_item.sizes:
                if size.is_available:
                    sizes.append({
                        "size": size.size,
                        "price": size.price,
                        "id": size.id
                    })
            
            return sizes
        except Exception as e:
            print(f"⚠️ Error getting sizes for '{item_name}': {e}")
            return []
    
    def _format_sizes_english(self, sizes: List[Dict[str, Any]]) -> str:
        """Format sizes for English"""
        lines = []
        size_names = {"S": "Small", "M": "Medium", "L": "Large", "REG": "Regular"}
        
        for s in sizes:
            name = size_names.get(s['size'], s['size'])
            lines.append(f"  • {name} ({s['size']}) - {s['price']} EGP")
        
        return "\n".join(lines)
    
    def _format_sizes_arabic(self, sizes: List[Dict[str, Any]]) -> str:
        """Format sizes for Arabic"""
        lines = []
        size_names = {"S": "صغير", "M": "متوسط", "L": "كبير", "REG": "عادي"}
        
        for s in sizes:
            name = size_names.get(s['size'], s['size'])
            lines.append(f"  • {name} ({s['size']}) - {s['price']} جنيه")
        
        return "\n".join(lines)
    
    def _format_cart_items(self, items: List[Dict[str, Any]], lang: str) -> str:
        """Format cart items for display"""
        lines = []
        
        for item in items:
            name = item.get('item_name', '')
            size = item.get('size', '')
            qty = item.get('quantity', 1)
            
            if lang == "ar":
                lines.append(f"  • {name} ({size}) × {qty}")
            else:
                lines.append(f"  • {name} ({size}) × {qty}")
        
        return "\n".join(lines)
    
    def suggest_alternatives(
        self, 
        item_name: str, 
        lang: str = "en"
    ) -> Optional[str]:
        """
        Suggest similar items if exact match not found
        Uses fuzzy matching
        """
        try:
            all_items = self.menu_service.get_all_items()
            
            # Simple fuzzy matching (you can use libraries like fuzzywuzzy for better results)
            suggestions = []
            item_lower = item_name.lower()
            
            for item in all_items:
                if item_lower in item.name.lower() or item.name.lower() in item_lower:
                    suggestions.append(item.name)
            
            if not suggestions:
                # Try word matching
                words = item_lower.split()
                for item in all_items:
                    item_name_lower = item.name.lower()
                    if any(word in item_name_lower for word in words):
                        suggestions.append(item.name)
            
            if suggestions:
                if lang == "ar":
                    items_text = "، ".join(suggestions[:3])
                    return f"مش لاقي '{item_name}' بالضبط. ممكن تقصد: {items_text}؟"
                else:
                    items_text = ", ".join(suggestions[:3])
                    return f"Couldn't find '{item_name}' exactly. Did you mean: {items_text}?"
            
            return None
            
        except Exception as e:
            print(f"Error suggesting alternatives: {e}")
            return None
    
    def extract_from_context(
        self, 
        current_message: str,
        missing_field: str,
        context: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Try to extract missing field from current message using context
        Example: If user says "large" when size is missing, extract "L"
        """
        message_lower = current_message.lower().strip()
        
        if missing_field == "size":
            # Size extraction patterns
            size_patterns = {
                "S": ["small", "s", "صغير", "ص"],
                "M": ["medium", "m", "متوسط", "م"],
                "L": ["large", "l", "big", "كبير", "ك"],
                "REG": ["regular", "reg", "عادي", "عاد"]
            }
            
            for size_code, patterns in size_patterns.items():
                if any(pattern in message_lower for pattern in patterns):
                    return size_code
        
        elif missing_field == "quantity":
            # Extract numbers
            import re
            numbers = re.findall(r'\d+', message_lower)
            if numbers:
                return int(numbers[0])
        
        elif missing_field == "order_id":
            # Extract order ID
            import re
            numbers = re.findall(r'\d+', message_lower)
            if numbers:
                return int(numbers[0])
        
        return None