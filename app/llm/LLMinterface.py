# app/llm/llm_interface.py
from abc import ABC, abstractmethod

class LLMInterface(ABC):

    @abstractmethod
    def extract_intent(self, text: str, lang: str = None):
        """Extract user's intent and entities"""
        pass

    @abstractmethod
    def generate_response(self, text: str, context: str = "", lang: str = None):
        """Generate a response based on user input and context"""
        pass
