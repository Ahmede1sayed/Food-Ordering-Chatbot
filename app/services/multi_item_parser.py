"""
Multi-Item Parser
Handles commands like "add 1 fries 2 cola" or "add large pizza and fries"
"""

import re
from typing import List, Dict, Any, Tuple


class MultiItemParser:
    """
    Parses multi-item commands and splits them into individual items
    
    Examples:
    - "add 1 fries 2 cola" → [{"item": "fries", "quantity": 1}, {"item": "cola", "quantity": 2}]
    - "add large pizza and fries" → [{"item": "pizza", "size": "L"}, {"item": "fries"}]
    - "add 2 large margherita and 3 cola" → [{"item": "margherita", "size": "L", "quantity": 2}, {"item": "cola", "quantity": 3}]
    - "add one fries and 2 cola" → [{"item": "fries", "quantity": 1}, {"item": "cola", "quantity": 2}]
    """

    WORD_TO_NUM = {
        "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8",
        "nine": "9", "ten": "10"
    }

    def __init__(self):
        # Size patterns
        self.size_patterns = {
            "S": r"\b(small|s)\b",
            "M": r"\b(medium|m)\b",
            "L": r"\b(large|l|big)\b",
            "REG": r"\b(regular|reg)\b"
        }
        
        # Common separators
        self.separators = ["and", "with", ",", "&"]

    def _normalize_word_numbers(self, text: str) -> str:
        """Convert word numbers to digits: 'one fries' → '1 fries'"""
        for word, digit in self.WORD_TO_NUM.items():
            text = re.sub(rf'\b{word}\b', digit, text)
        return text

    def parse(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse text into multiple items
        
        Returns:
            List of items with quantity, size, and name
        """
        text = text.lower().strip()
        
        # Remove common starting phrases
        text = re.sub(r"^(add|order|i want|get me|give me)\s+", "", text)

        # Normalize word numbers to digits before any parsing
        text = self._normalize_word_numbers(text)
        
        # Try different parsing strategies
        items = []
        
        # Strategy 1: Number + item pattern (1 fries 2 cola)
        items = self._parse_numbered_items(text)
        if items:
            return items
        
        # Strategy 2: Separated items (pizza and cola, pizza, fries)
        items = self._parse_separated_items(text)
        if items:
            return items
        
        # Strategy 3: Single item (fallback)
        return [{"item": text, "quantity": 1, "size": None}]
    
    def _parse_numbered_items(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse pattern: "1 fries 2 cola" or "2 large pizza 3 fries"
        
        Pattern: [number] [size?] [item_name]
        """
        items = []
        
        # Pattern: number + optional size + item
        # Example: "1 fries" or "2 large pizza" or "3 cola"
        pattern = r'(\d+)\s*(small|medium|large|s|m|l|big|reg|regular)?\s*([a-z\s]+?)(?=\d+\s|$|and|,)'
        
        matches = re.findall(pattern, text)
        
        for match in matches:
            quantity_str, size_str, item_name = match
            
            quantity = int(quantity_str) if quantity_str else 1
            size = self._normalize_size(size_str) if size_str else None
            item_name = item_name.strip()
            
            if item_name:
                items.append({
                    "item": item_name,
                    "quantity": quantity,
                    "size": size
                })
        
        return items
    
    def _parse_separated_items(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse pattern: "large pizza and fries" or "pizza, cola, fries"
        """
        items = []
        
        # Split by common separators
        parts = re.split(r'\s+and\s+|\s*,\s*|\s*&\s+', text)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Extract quantity (if present)
            quantity_match = re.match(r'^(\d+)\s+(.+)$', part)
            if quantity_match:
                quantity = int(quantity_match.group(1))
                rest = quantity_match.group(2)
            else:
                quantity = 1
                rest = part
            
            # Extract size
            size = None
            for size_code, pattern in self.size_patterns.items():
                if re.search(pattern, rest, re.IGNORECASE):
                    size = size_code
                    # Remove size from text
                    rest = re.sub(pattern, "", rest, flags=re.IGNORECASE).strip()
                    break
            
            # Clean item name
            item_name = rest.strip()
            
            if item_name:
                items.append({
                    "item": item_name,
                    "quantity": quantity,
                    "size": size
                })
        
        return items
    
    def _normalize_size(self, size_str: str) -> str:
        """Normalize size string to code"""
        if not size_str:
            return None
        
        size_str = size_str.lower().strip()
        
        if size_str in ["small", "s"]:
            return "S"
        elif size_str in ["medium", "m"]:
            return "M"
        elif size_str in ["large", "l", "big"]:
            return "L"
        elif size_str in ["regular", "reg"]:
            return "REG"
        
        return None
    
    def is_multi_item(self, text: str) -> bool:
        """
        Check if text contains multiple items
        """
        text = text.lower()
        text = self._normalize_word_numbers(text)  # normalize before checking

        # Check for number patterns (1 fries 2 cola)
        number_count = len(re.findall(r'\d+', text))
        if number_count >= 2:
            return True
        
        # Check for separators (and, with, comma)
        for separator in self.separators:
            if separator in text:
                return True
        
        return False


# Test cases
if __name__ == "__main__":
    parser = MultiItemParser()
    
    test_cases = [
        "1 fries 2 cola",
        "2 large pizza 3 fries",
        "large pizza and fries",
        "pizza, cola, fries",
        "2 large margherita and 3 cola",
        "1 small hot dog pizza 2 fries 3 cola",
        "one fries and 2 cola",        # word number fix
        "two large pizza and one cola", # word number fix
    ]
    
    print("🧪 Multi-Item Parser Tests\n")
    for test in test_cases:
        items = parser.parse(test)
        print(f"Input: '{test}'")
        print(f"Output: {items}")
        print("-" * 60)