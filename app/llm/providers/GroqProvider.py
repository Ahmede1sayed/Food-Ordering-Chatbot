# app/llm/providers/GroqProvider.py
# FIXED VERSION - Uses your existing prompts + fixes JSON parsing bug
import os
import json
import re
from groq import Groq
from app.llm.LLMinterface import LLMInterface
from dotenv import load_dotenv

load_dotenv()

class GroqProvider(LLMInterface):
    """Free LLM provider using Groq (14,400 requests/day free)"""
    
    def __init__(self, default_lang: str = None):
        self.api_key = os.getenv("GROQ_API_KEY")
        try:
            if self.api_key:
                self.client = Groq(api_key=self.api_key)
                print("✅ Groq LLM initialized successfully")
            else:
                self.client = None
                print("⚠️ Warning: GROQ_API_KEY not set. LLM features disabled.")
        except Exception as e:
            self.client = None
            print(f"⚠️ Warning: Failed to initialize Groq client: {e}")
        
        self.default_lang = default_lang or os.getenv("LLM_DEFAULT_LANG", "en")
        self.model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", 0.1))
        
        # Load your existing prompts
        self._load_prompts()

    def _load_prompts(self):
        """Load prompts from your existing prompt.py file"""
        try:
            # Import your existing prompt templates
            if self.default_lang == "ar":
                from app.llm.templates.locales.ar.prompt import parse_prompt, response_prompt
            else:
                from app.llm.templates.locales.en.prompt import parse_prompt, response_prompt
            
            self.parse_prompt = parse_prompt
            self.response_prompt = response_prompt
            print(f"✅ Loaded prompts for language: {self.default_lang}")
        except Exception as e:
            print(f"⚠️ Warning: Could not load prompt templates: {e}")
            # Fallback to inline prompts
            from string import Template
            self.parse_prompt = Template(
                "You are a pizza ordering assistant. "
                "Extract the intent and entities from: $query\n"
                "Respond in JSON only."
            )
            self.response_prompt = Template(
                "You are a pizza ordering assistant. "
                "Generate a polite, concise response."
            )

    def extract_intent(self, text: str, lang: str = None):
        """Extract intent from text - FIXED to handle malformed JSON from LLM"""
        if not self.client:
            return {"intent": "unknown", "confidence": 0}
        
        # Use your existing parse_prompt template
        prompt = self.parse_prompt.substitute(query=text)
        
        # Enforce JSON-only response
        prompt += "\n\nIMPORTANT: Respond with ONLY valid JSON. No explanations or extra text."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
            result = response.choices[0].message.content.strip()
            
            # FIX: Robust JSON extraction to handle extra text from LLM
            return self._extract_json_safe(result)
            
        except Exception as e:
            print(f"⚠️ Groq intent extraction error: {e}")
            return {"intent": "unknown", "confidence": 0, "entities": {}}

    def _extract_json_safe(self, text: str) -> dict:
        """
        CRITICAL FIX: Robust JSON extraction
        
        Handles these cases:
        ✅ {"intent": "greeting"}
        ✅ {"intent": "greeting"}\n\nSure, I can help!
        ✅ ```json\n{"intent": "greeting"}\n```
        ✅ Sure! {"intent": "greeting"}
        
        This fixes the "Extra data: line 3 column 1" error
        """
        # Strategy 1: Try direct parse (clean JSON)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Remove markdown code blocks
        cleaned = re.sub(r'```(?:json)?\s*|\s*```', '', text)
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Extract JSON object from mixed content
        # This handles: {"intent": "greeting"}\n\nExtra text here
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                print(f"⚠️ Groq returned extra text, extracted JSON successfully")
                return parsed
            except json.JSONDecodeError:
                pass
        
        # Strategy 4: Try first line only
        first_line = text.split('\n')[0].strip()
        try:
            return json.loads(first_line)
        except json.JSONDecodeError:
            pass
        
        # Last resort: return unknown intent
        print(f"⚠️ Could not parse JSON from Groq response:")
        print(f"   Raw response: {text[:200]}...")
        return {"intent": "unknown", "confidence": 0, "entities": {}}

    def generate_response(self, text: str, context: str = "", lang: str = None):
        """Generate natural response - UNCHANGED, uses your existing prompt"""
        if not self.client:
            return None  # Let orchestrator use handler result
        
        try:
            # Use your existing response_prompt template
            system_prompt = self.response_prompt.template
            if context:
                system_prompt += "\n\nContext:\n" + context
            
            user_prompt = f"User said: {text}"
            
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=150
            )
            
            result = response.choices[0].message.content.strip()
            print(f"✅ Groq response: {result[:100]}...")
            return result
            
        except Exception as e:
            print(f"⚠️ Groq API Error: {e}")
            print(f"   Model: {self.model}")
            print(f"   API Key present: {bool(self.api_key)}")
            return None