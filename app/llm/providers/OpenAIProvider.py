# app/llm/providers/openai_provider.py
import os
from openai import OpenAI
from app.llm.LLMinterface import LLMInterface
from app.llm.templates.locales.TemplateParser import TemplateParser
from dotenv import load_dotenv
import json

load_dotenv()

class OpenAIProvider(LLMInterface):
    def __init__(self, default_lang: str = None):
        self.api_key = os.getenv("OPENAI_API_KEY")
        try:
            # Only initialize client if API key exists
            if self.api_key:
                self.client = OpenAI(api_key=self.api_key)
            else:
                self.client = None
                print("⚠️ Warning: OPENAI_API_KEY not set. LLM features disabled.")
        except Exception as e:
            self.client = None
            print(f"⚠️ Warning: Failed to initialize OpenAI client: {e}")
        
        self.default_lang = default_lang or os.getenv("LLM_DEFAULT_LANG", "en")
        self.parser = TemplateParser(language=self.default_lang, default_language=self.default_lang)
        self.model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", 0.1))

    def extract_intent(self, text: str, lang: str = None):
        if not self.client:
            return {"intent": "unknown", "confidence": 0}
        
        lang = lang or self.default_lang
        prompt = self.parser.get_prompt("parse_prompt", {"query": text})
        return self._call_openai(prompt)

    def generate_response(self, text: str, context: str = "", lang: str = None):
        if not self.client:
            return f"I understand you said: '{text}'. Please use one of our menu commands."
        
        lang = lang or self.default_lang
        prompt = self.parser.get_prompt("response_prompt", {"query": text, "context": context})
        return self._call_openai(prompt)

    def _call_openai(self, prompt: str):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                messages=[{"role": "system", "content": prompt}]
            )
            result = response.choices[0].message.content
            try:
                return json.loads(result)  # structured JSON if the LLM returns JSON
            except json.JSONDecodeError:
                return {"text": result}   # fallback to raw text
        except Exception as e:
            print(f"⚠️ OpenAI API Error: {e}")
            return {"text": "I encountered an issue processing your request."}
