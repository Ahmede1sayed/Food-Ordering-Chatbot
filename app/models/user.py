from sqlalchemy import Column, Integer, String
from app.database.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    phone = Column(String(20), unique=True)
    address = Column(String(255))
