from fastapi import FastAPI
from app.database.connection import db
from app.database.base import Base
from app.models import user, conversation_history
from app.routes.chat import chat_router



def create_app() -> FastAPI:
    app = FastAPI(
        title="Primos Pizza Chatbot API",
        version="1.0.0",
        description="Pizza restaurant chatbot with order management"
    )

    # Create database tables
    # Base.metadata.create_all(bind=db.get_engine())

    # Include routes
    app.include_router(chat_router, prefix="/api", tags=["chat"])

    @app.get("/health")
    def health_check():
        return {"status": "ok", "service": "Primos Chatbot API"}

    return app


app = create_app()
