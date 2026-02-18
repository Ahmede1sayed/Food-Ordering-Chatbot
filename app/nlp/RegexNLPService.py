import re

class RegexNLPService:

    def __init__(self):
        self.patterns = {
            "welcome": [
                {"pattern": r"(hi|hello|hey)", "lang": "en"},
                {"pattern": r"(اهلا|مرحبا|هاي)", "lang": "ar"},
            ],
            "track_order": [
                {"pattern": r"(track|status of) my order(?: number (?P<order_id>\d+))?", "lang": "en"},
                {"pattern": r"(عايز اعرف|حالة) طلبي(?: رقم (?P<order_id>\d+))?", "lang": "ar"},
            ],
            "add_item": [
                {"pattern": r"(?:add|order|i want to order|i want|get me|give me)\s+(?:a\s+)?(?P<full_input>[\w\s]+?)(?:\s+(?:please|thanks|thank you))?$", "lang": "en"},
                {"pattern": r"(ضيف|طلب|عايز)\s+(?P<full_input>[\w\s]+?)(?:\s+(?:من فضلك|شكرا))?$", "lang": "ar"},
            ],
            "remove_item": [
                {"pattern": r"(?:remove|delete|cancel)\s+(?P<item>[\d\w\s]+)", "lang": "en"},
                {"pattern": r"(شيل|احذف) (?P<item>[\w\s]+)", "lang": "ar"},
            ],
            "view_cart": [
                {"pattern": r"(show|view|what|see) (?:my )?cart", "lang": "en"},
                {"pattern": r"(what|how much|what's) (?:is )?(?:the |my )?total", "lang": "en"},
                {"pattern": r"(how much|what) (?:do |did )?i (?:order|have|spend)", "lang": "en"},
                {"pattern": r"(what's|show) (?:my )?(?:order|price)", "lang": "en"},
                {"pattern": r"(اعرض|شف) (?:سلة )?الطلب|كام في السلة", "lang": "ar"},
                {"pattern": r"(كام|إيه|ايه) (?:المجموع|السعر)", "lang": "ar"},
            ],
            "clear_cart": [
                {"pattern": r"(clear|empty|reset|cancel) (?:my )?cart", "lang": "en"},
                {"pattern": r"(امسح|فضي|الغي) (?:السلة|الطلب)", "lang": "ar"},
            ],
            "checkout": [
                {"pattern": r"(checkout|confirm|place order|pay|complete)", "lang": "en"},
                {"pattern": r"(ادفع|اكمل|اتمم الطلب|قرر)", "lang": "ar"},
            ],
            "browse_menu": [
                {"pattern": r"(what do you have|show menu|menu|pizza|items)", "lang": "en"},
                {"pattern": r"(في إيه|قائمة|عندك إيه|بيتزا)", "lang": "ar"},
            ],
            "new_order": [
                {"pattern": r"(new order|start order)", "lang": "en"},
                {"pattern": r"(طلب جديد|ابدأ طلب)", "lang": "ar"},
            ],
            "confirmation": [
                {"pattern": r"^(yes|yeah|yep|yup|sure|ok|okay|correct|right|fine|alright|sounds good|that's right)$", "lang": "en"},
                {"pattern": r"^(نعم|ايوة|ماشي|تمام|صح)$", "lang": "ar"},
            ],
            "rejection": [
                {"pattern": r"^(no|nope|nah|not really|incorrect|wrong|cancel that)$", "lang": "en"},
                {"pattern": r"^(لا|مش صح|غلط)$", "lang": "ar"},
            ]
        }
        
        self.size_patterns = {
            "en": {
                "S": r"\b(small|s)\b",
                "M": r"\b(medium|m)\b",
                "L": r"\b(large|l)\b",
                "REG": r"\b(regular|reg)\b"
            },
            "ar": {
                "S": r"\b(صغير|ص)\b",
                "M": r"\b(متوسط|م)\b",
                "L": r"\b(كبير|ك)\b",
                "REG": r"\b(عادي|عاد)\b"
            }
        }
        
        self.filler_words = {
            "en": ["a", "an", "the", "some"],
            "ar": []
        }
        
        self.text_numbers = {
            "en": {
                "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
            },
            "ar": {
                "واحد": 1, "اتنين": 2, "تلاتة": 3, "اربعة": 4, "خمسة": 5,
                "ستة": 6, "سبعة": 7, "تمانية": 8, "تسعة": 9, "عشرة": 10
            }
        }

    def detect_lang(self, text):
        if re.search(r"[\u0600-\u06FF]", text):
            return "ar"
        return "en"

    def clean_item_name(self, text: str, lang: str = "en") -> str:
        """Remove filler words: 'a sea ranch pizza' → 'sea ranch pizza'"""
        words = text.strip().lower().split()
        fillers = self.filler_words.get(lang, [])
        while words and words[0] in fillers:
            words.pop(0)
        return " ".join(words).strip()

    def convert_text_number_to_digit(self, text: str, lang: str = "en") -> tuple:
        """
        Convert text numbers to digits: "one cola" → (1, "cola")
        Returns: (quantity, remaining_text)
        """
        words = text.strip().lower().split()
        if not words:
            return None, text
        
        first_word = words[0]
        text_nums = self.text_numbers.get(lang, self.text_numbers["en"])
        
        if first_word in text_nums:
            quantity = text_nums[first_word]
            remaining = " ".join(words[1:])
            return quantity, remaining
        
        return None, text

    def extract_size(self, text: str, lang: str = "en"):
        """Extract size, return (size_code, text_without_size)"""
        text_lower = text.lower().strip()
        patterns = self.size_patterns.get(lang, self.size_patterns["en"])
        
        for size_code, pattern in patterns.items():
            match = re.search(pattern, text_lower)
            if match:
                cleaned_text = re.sub(pattern, "", text_lower, flags=re.IGNORECASE).strip()
                cleaned_text = re.sub(r"\s+", " ", cleaned_text)
                return size_code, cleaned_text
        
        return None, text_lower

    def is_multi_item(self, text: str) -> bool:
        """
        Detect if text contains multiple items
        Examples: "1fries 2cola", "1 fries 2 cola", "fries and cola"
        """
        # Pattern: number immediately followed by or with space before item, appearing 2+ times
        multi_num_pattern = r'\d+\s*[a-z]'
        num_matches = re.findall(multi_num_pattern, text.lower())
        if len(num_matches) >= 2:
            return True
        
        # Check for "and" or comma separators with multiple items
        if re.search(r'\b(and|,)\b', text.lower()):
            parts = re.split(r'\band\b|,', text.lower())
            if len(parts) >= 2 and all(p.strip() for p in parts):
                return True
        
        return False

    def parse_multi_items(self, text: str) -> list:
        """
        Parse multi-item text into list of items

        "1fries 2cola" → [{"item": "fries", "quantity": 1}, {"item": "cola", "quantity": 2}]
        "1 fries 2 cola" → [{"item": "fries", "quantity": 1}, {"item": "cola", "quantity": 2}]
        "fries and cola" → [{"item": "fries", "quantity": 1}, {"item": "cola", "quantity": 1}]
        "one fries and 2 cola" → [{"item": "fries", "quantity": 1}, {"item": "cola", "quantity": 2}]
        """
        items = []
        text = text.lower().strip()
        
        # Strategy 1: number+item pattern (with or without space)
        # Matches: "1fries", "2 cola", "3large pizza"
        pattern = r'(\d+)\s*([a-z]+(?:\s+[a-z]+)*?)(?=\s*\d|$|\s+and\s+|,)'
        matches = re.findall(pattern, text)
        
        if len(matches) >= 2:
            for qty_str, item_name in matches:
                item_name = item_name.strip()
                if item_name:
                    size, clean_name = self.extract_size(item_name)
                    clean_name = self.clean_item_name(clean_name)
                    if clean_name:
                        items.append({
                            "item": clean_name,
                            "quantity": int(qty_str),
                            "size": size
                        })
            return items
        
        # Strategy 2: "and" or comma separated
        parts = re.split(r'\band\b|,', text)
        if len(parts) >= 2:
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                # Try numeric quantity first: "2 cola"
                qty_match = re.match(r'^(\d+)\s*(.+)$', part)
                if qty_match:
                    qty = int(qty_match.group(1))
                    item_text = qty_match.group(2)
                else:
                    # Try word number: "one fries" → qty=1, item_text="fries"
                    text_qty, remaining = self.convert_text_number_to_digit(part, "en")
                    if text_qty:
                        qty = text_qty
                        item_text = remaining
                    else:
                        qty = 1
                        item_text = part
                
                # Extract size
                size, clean_name = self.extract_size(item_text)
                clean_name = self.clean_item_name(clean_name)
                
                if clean_name:
                    items.append({
                        "item": clean_name,
                        "quantity": qty,
                        "size": size
                    })
            return items
        
        return []

    def empty_entities(self):
        return {
            "item": None,
            "size": None,
            "quantity": None,
            "order_id": None,
            "address": None,
            "phone": None
        }

    def parse(self, text):
        text_lower = text.lower()
        detected_lang = self.detect_lang(text_lower)

        for intent_name, patterns in self.patterns.items():
            for p in patterns:
                if p["lang"] != detected_lang:
                    continue

                match = re.search(p["pattern"], text_lower)
                if match:
                    entities = self.empty_entities()

                    for key, value in match.groupdict().items():
                        if value:
                            entities[key] = value

                    # Special handling for add_item
                    if intent_name == "add_item" and entities.get("full_input"):
                        full_input = entities["full_input"].strip()
                        del entities["full_input"]
                        
                        # Check for multi-item: "1fries 2cola" or "1 fries 2 cola"
                        if self.is_multi_item(full_input):
                            batch_items = self.parse_multi_items(full_input)
                            if len(batch_items) >= 2:
                                return {
                                    "intent": "add_item",
                                    "lang": detected_lang,
                                    "entities": entities,
                                    "batch_items": batch_items,
                                    "source": "regex",
                                    "confidence": 1.0
                                }
                        
                        # Convert text numbers to digits: "one cola" → 1, "cola"
                        text_qty, remaining_text = self.convert_text_number_to_digit(full_input, detected_lang)
                        if text_qty:
                            entities["quantity"] = text_qty
                            full_input = remaining_text
                        
                        # Single item: extract quantity (handles "2cola" and "2 cola")
                        if not text_qty:
                            quantity_match = re.match(r'^(\d+)\s*([a-z].+)$', full_input)
                            if quantity_match:
                                entities["quantity"] = int(quantity_match.group(1))
                                full_input = quantity_match.group(2).strip()
                        
                        # Extract size
                        size, cleaned_item = self.extract_size(full_input, detected_lang)
                        
                        # Clean filler words
                        cleaned_item = self.clean_item_name(cleaned_item, detected_lang)
                        
                        entities["item"] = cleaned_item
                        entities["size"] = size

                    return {
                        "intent": intent_name,
                        "lang": detected_lang,
                        "entities": entities,
                        "source": "regex",
                        "confidence": 1.0
                    }

        return None