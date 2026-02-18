"""
Enhanced Pydantic Schemas with Comprehensive Validation
Fixed for Pydantic V2 compatibility
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ===== Enums =====

class IntentType(str, Enum):
    """Supported intent types"""
    WELCOME = "welcome"
    ADD_ITEM = "add_item"
    REMOVE_ITEM = "remove_item"
    VIEW_CART = "view_cart"
    CLEAR_CART = "clear_cart"
    CHECKOUT = "checkout"
    BROWSE_MENU = "browse_menu"
    TRACK_ORDER = "track_order"
    NEW_ORDER = "new_order"
    CONFIRMATION = "confirmation"  # NEW: For "yes"/"ok" responses
    REJECTION = "rejection"        # NEW: For "no" responses
    UNKNOWN = "unknown"


class SizeType(str, Enum):
    """Supported size types"""
    SMALL = "S"
    MEDIUM = "M"
    LARGE = "L"
    REGULAR = "REG"


class LanguageType(str, Enum):
    """Supported languages"""
    ENGLISH = "en"
    ARABIC = "ar"


class OrderStatus(str, Enum):
    """Order status types"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# ===== Request Schemas =====

class ChatRequest(BaseModel):
    """
    Chat message request
    Validates user input before processing
    """
    user_id: int = Field(..., gt=0, description="User ID must be positive integer")
    text: str = Field(..., min_length=1, max_length=500, description="Message text")
    session_id: Optional[str] = Field(None, max_length=100)
    language: Optional[LanguageType] = Field(None, description="Preferred language")
    
    @field_validator('text')
    @classmethod
    def text_not_empty(cls, v):
        """Ensure text is not just whitespace"""
        if not v or not v.strip():
            raise ValueError('Message text cannot be empty')
        return v.strip()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 1,
                "text": "add large margherita pizza",
                "session_id": "abc123",
                "language": "en"
            }
        }
    }


class AddItemRequest(BaseModel):
    """Request to add item to cart"""
    user_id: int = Field(..., gt=0)
    item_name: str = Field(..., min_length=1, max_length=255)
    size: SizeType
    quantity: int = Field(default=1, gt=0, le=10, description="Quantity between 1-10")
    
    @field_validator('item_name')
    @classmethod
    def clean_item_name(cls, v):
        """Clean and validate item name"""
        return v.strip().title()


class RemoveItemRequest(BaseModel):
    """Request to remove item from cart"""
    user_id: int = Field(..., gt=0)
    menu_size_id: int = Field(..., gt=0)


class CheckoutRequest(BaseModel):
    """Request to checkout"""
    user_id: int = Field(..., gt=0)
    delivery_address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        """Basic phone validation"""
        if v:
            # Remove spaces and special chars
            cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
            if len(cleaned) < 10:
                raise ValueError('Phone number too short')
            return cleaned
        return v


class TrackOrderRequest(BaseModel):
    """Request to track order"""
    user_id: int = Field(..., gt=0)
    order_id: int = Field(..., gt=0)


# ===== Response Schemas =====

class ItemInfo(BaseModel):
    """Item information"""
    name: str
    size: str
    price: float = Field(..., ge=0)
    quantity: int = Field(..., gt=0)
    subtotal: float = Field(..., ge=0)


class CartResponse(BaseModel):
    """Cart view response"""
    success: bool
    items: List[ItemInfo]
    total_price: float = Field(..., ge=0)
    item_count: int = Field(..., ge=0)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "items": [
                    {
                        "name": "Margherita Pizza",
                        "size": "L",
                        "price": 140.0,
                        "quantity": 1,
                        "subtotal": 140.0
                    }
                ],
                "total_price": 140.0,
                "item_count": 1
            }
        }
    }


class RecommendationItem(BaseModel):
    """Recommendation item"""
    name: str
    category: str
    sizes: List[Dict[str, Any]]
    recommendation_reason: Optional[str] = None
    badge: Optional[str] = None


class ChatResponse(BaseModel):
    """
    Comprehensive chat response
    Includes all relevant information from processing
    """
    success: bool
    user_message: str
    bot_response: str
    intent: Optional[str] = None  # Accepts any string, no validation
    nlp_source: Optional[str] = None
    nlp_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Handler info
    handler_name: Optional[str] = None
    handler_executed: bool = False
    handler_result: Optional[Dict[str, Any]] = None
    
    # State info
    current_cart: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[RecommendationItem]] = None
    suggested_actions: Optional[List[str]] = None
    
    # Clarification
    clarification_needed: bool = False
    clarification_question: Optional[str] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "use_enum_values": True,
        "json_schema_extra": {
            "example": {
                "success": True,
                "user_message": "add large pepperoni pizza",
                "bot_response": "Added Large Double Pepperoni Pizza to your cart!",
                "intent": "add_item",
                "nlp_source": "regex",
                "nlp_confidence": 1.0,
                "handler_name": "add_item",
                "handler_executed": True,
                "handler_result": {
                    "success": True,
                    "message": "Item added successfully"
                },
                "current_cart": {
                    "items": [],
                    "total_price": 195.0,
                    "item_count": 1
                },
                "clarification_needed": False
            }
        }
    }


class ErrorResponse(BaseModel):
    """Error response"""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ===== Entity Schemas =====

class EntityExtraction(BaseModel):
    """Extracted entities from user message"""
    item: Optional[str] = None
    size: Optional[SizeType] = None
    quantity: Optional[int] = Field(None, gt=0, le=10)
    order_id: Optional[int] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_entity_combination(self):
        """Validate entity combinations make sense"""
        # If size is specified, item should be specified too
        if self.size and not self.item:
            raise ValueError('Size specified without item name')
        return self


class NLPResult(BaseModel):
    """NLP parsing result"""
    intent: Optional[IntentType] = None
    entities: EntityExtraction = Field(default_factory=EntityExtraction)
    language: LanguageType = LanguageType.ENGLISH
    source: str = Field(..., pattern="^(regex|llm|clarification|none)$")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


# ===== Menu Schemas =====

class MenuSizeInfo(BaseModel):
    """Menu size information"""
    id: int
    size: SizeType
    price: float = Field(..., ge=0)
    is_available: bool


class MenuItemInfo(BaseModel):
    """Menu item information"""
    id: int
    name: str
    category: str
    description: Optional[str] = None
    is_available: bool
    sizes: List[MenuSizeInfo]


class MenuResponse(BaseModel):
    """Menu listing response"""
    success: bool
    categories: Dict[str, List[MenuItemInfo]]
    total_items: int = Field(..., ge=0)


# ===== Order Schemas =====

class OrderItemInfo(BaseModel):
    """Order item information"""
    menu_item_name: str
    size: str
    quantity: int = Field(..., gt=0)
    price: float = Field(..., ge=0)
    subtotal: float = Field(..., ge=0)


class OrderInfo(BaseModel):
    """Order information"""
    id: int
    user_id: int
    items: List[OrderItemInfo]
    total_price: float = Field(..., ge=0)
    status: OrderStatus
    created_at: datetime
    
    model_config = {
        "use_enum_values": True
    }


class OrderResponse(BaseModel):
    """Order creation/tracking response"""
    success: bool
    order: Optional[OrderInfo] = None
    message: Optional[str] = None


# ===== User Preference Schemas =====

class UserPreferences(BaseModel):
    """User preferences for personalization"""
    favorite_size: Optional[SizeType] = None
    favorite_items: List[str] = Field(default_factory=list)
    dietary_restrictions: List[str] = Field(default_factory=list)
    language_preference: LanguageType = LanguageType.ENGLISH
    notification_preferences: Dict[str, bool] = Field(default_factory=dict)


# ===== Session Schema =====

class SessionInfo(BaseModel):
    """Session information"""
    session_id: str
    user_id: int
    started_at: datetime
    last_activity: datetime
    context_variables: Dict[str, Any] = Field(default_factory=dict)