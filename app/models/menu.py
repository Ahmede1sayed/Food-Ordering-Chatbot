from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean ,text
from sqlalchemy.orm import relationship
from app.database.base import Base


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    category = Column(String(50), nullable=False)  # pizza, drink, side



    is_available = Column(Boolean,nullable=False,server_default=text("1"))  # Availability status
    description = Column(String(500), nullable=True)  # Optional description

    sizes = relationship("MenuSize", back_populates="menu_item", cascade="all, delete-orphan")


class MenuSize(Base):
    __tablename__ = "menu_sizes"

    id = Column(Integer, primary_key=True, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)

    size = Column(String(5))  # S, M, L, REG
    price = Column(Float, nullable=False)
    is_available = Column(Boolean,nullable=False,server_default=text("1"))  # Availability status

    menu_item = relationship("MenuItem", back_populates="sizes")
