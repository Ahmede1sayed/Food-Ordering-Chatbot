from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.cart import Cart, CartItem
from app.models.menu import MenuSize


class PricingService:
    """Service to calculate prices and totals"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_cart_total(self, cart_id: int) -> float:
        """
        Calculate total price for cart
        Args:
            cart_id: Cart ID
        Returns: Total price
        """
        total = (
            self.db.query(func.sum(CartItem.quantity * MenuSize.price))
            .join(MenuSize, CartItem.menu_size_id == MenuSize.id)
            .filter(CartItem.cart_id == cart_id)
            .scalar()
        )
        return float(total) if total else 0.0
    
    def get_item_price(self, menu_size_id: int) -> float:
        """Get price of a specific menu size"""
        menu_size = self.db.query(MenuSize).filter(MenuSize.id == menu_size_id).first()
        return menu_size.price if menu_size else 0.0
    
    def calculate_subtotal(self, menu_size_id: int, quantity: int) -> float:
        """Calculate subtotal for item"""
        price = self.get_item_price(menu_size_id)
        return price * quantity
    
    def apply_discount(self, total: float, discount_percent: float = 0) -> dict:
        """
        Apply discount to total
        Args:
            total: Original total
            discount_percent: Discount percentage (0-100)
        Returns: {original, discount_amount, final_total}
        """
        discount_amount = (total * discount_percent) / 100
        final_total = total - discount_amount
        
        return {
            "original": total,
            "discount_percent": discount_percent,
            "discount_amount": discount_amount,
            "final_total": final_total
        }
    
    def format_price(self, price: float, currency: str = "EGP") -> str:
        """Format price for display"""
        return f"{price:.2f} {currency}"
