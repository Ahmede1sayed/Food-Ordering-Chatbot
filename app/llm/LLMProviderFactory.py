from app.llm.providers.OpenAIProvider import OpenAIProvider
from app.llm.providers.GroqProvider import GroqProvider  # Add this

class LLMProviderFactory:
    @staticmethod
    def get_provider(provider_name: str = None):
        provider_name = provider_name or "groq"
        
        if provider_name == "openai":
            return OpenAIProvider()
        elif provider_name == "groq":  # Add this
            return GroqProvider()
        else:
            return None