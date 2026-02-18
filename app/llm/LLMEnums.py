from enum import Enum

class LLMProviderType(str, Enum):
    OPENAI = "openai"
    LOCAL = "local"

class Language(str, Enum):
    ENGLISH = "en"
    ARABIC = "ar"

class Intent(Enum):
    WELCOME = "welcome"
    NEW_ORDER = "new_order"
    ADD_ITEM = "add_item"
    REMOVE_ITEM = "remove_item"
    TRACK_ORDER = "track_order"
    LLM_FALLBACK = "llm_fallback"