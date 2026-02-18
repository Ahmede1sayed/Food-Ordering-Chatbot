from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    user_id: int
    text: str
    
    class Config:
        example = {
            "user_id": 1,
            "text": "Add large sea ranch pizza"
        }


class ChatResponse(BaseModel):
    success: bool
    user_message: str
    bot_response: str
    intent: Optional[str] = None
    nlp_source: Optional[str] = None
    handler_name: Optional[str] = None
    handler_executed: bool = False
    current_cart: dict
    
    class Config:
        example = {
            "success": True,
            "user_message": "Add large pizza",
            "bot_response": "Added Large Margherita Pizza (140 EGP) to your cart",
            "intent": "add_item",
            "nlp_source": "regex",
            "handler_name": "add_item",
            "handler_executed": True,
            "current_cart": {
                "items": [
                    {
                        "item_name": "Margherita Pizza",
                        "size": "L",
                        "price": 140,
                        "quantity": 1,
                        "subtotal": 140
                    }
                ],
                "total_price": 140,
                "item_count": 1
            }
        }

