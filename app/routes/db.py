from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.connection import get_db

router = APIRouter()

@router.post("/test")
def test(db: Session = Depends(get_db)):
    return {"message": "DB Connected"}
