from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.chat_schema import ChatRequest
from app.chat.services.chat_service import ChatService
from app.database.connection import db as database
from app.schemas.enhanced_schemas_FIXED import ChatRequest, ChatResponse


# Get database dependency
def get_db():
    session = database.get_session()
    try:
        yield session
    finally:
        session.close()

chat_router = APIRouter()


@chat_router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    # Pydantic automatically validates
    chat_service = ChatService(db)
    return chat_service.handle_message(request.user_id, request.text)