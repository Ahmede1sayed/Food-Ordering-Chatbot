# app/nlp/hybrid_nlp_service.py

from app.nlp.RegexNLPService import RegexNLPService
from app.llm.LLMProviderFactory import LLMProviderFactory


class HybridNLPService:

    def __init__(self, provider_name: str = None):
        self.regex_service = RegexNLPService()
        try:
            self.llm_provider = LLMProviderFactory.get_provider(provider_name)
        except Exception as e:
            print(f"⚠️ HybridNLP initialization error: {e}")
            self.llm_provider = None

    def parse(self, text: str):
        """
        1️⃣ Try Regex first
        2️⃣ If no match → fallback to LLM (if available)
        3️⃣ If no LLM → return generic response
        """

        # -------- REGEX FIRST --------
        regex_result = self.regex_service.parse(text)

        if regex_result:
            print("✅ Handled by REGEX")
            return regex_result

        # -------- LLM FALLBACK --------
        if not self.llm_provider:
            print("⚠️ No LLM provider available, returning unhandled")
            detected_lang = self.regex_service.detect_lang(text)
            return {
                "intent": None,
                "lang": detected_lang,
                "entities": {},
                "source": "none",
                "confidence": 0
            }

        print("⚡ Falling back to LLM")

        detected_lang = self.regex_service.detect_lang(text)

        try:
            llm_result = self.llm_provider.extract_intent(
                text=text,
                lang=detected_lang
            )

            # Standardize response structure
            return {
                "intent": llm_result.get("intent"),
                "lang": detected_lang,
                "entities": llm_result.get("entities", {}),
                "source": "llm",
                "confidence": llm_result.get("confidence", 0.5)
            }
        except Exception as e:
            print(f"⚠️ LLM extraction error: {e}")
            return {
                "intent": None,
                "lang": detected_lang,
                "entities": {},
                "source": "error",
                "confidence": 0
            }
        
