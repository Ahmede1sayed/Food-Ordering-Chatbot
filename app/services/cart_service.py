from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.cart import Cart, CartItem
from app.models.menu import MenuItem, MenuSize


class CartService:
    """Service to manage shopping cart"""
    
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_cart(self, user_id: int) -> Cart:
        """Get existing cart or create new one for user"""
        cart = self.db.query(Cart).filter(Cart.user_id == user_id).first()
        if not cart:
            cart = Cart(user_id=user_id)
            self.db.add(cart)
            self.db.commit()
            self.db.refresh(cart)
        return cart
    
    def add_item(self, user_id: int, menu_size_id: int, quantity: int = 1):
        """
        Add item to cart by menu_size_id
        Args:
            user_id: User ID
            menu_size_id: MenuSize ID (contains item + size + price)
            quantity: Quantity to add
        Returns: Result dict with message and cart data
        """
        cart = self.get_or_create_cart(user_id)
        
        # Verify menu_size exists
        menu_size = self.db.query(MenuSize).filter(MenuSize.id == menu_size_id).first()
        if not menu_size:
            return {"success": False, "message": "Item not found in menu"}
        
        # Check if item already in cart
        existing_item = (
            self.db.query(CartItem)
            .filter(
                CartItem.cart_id == cart.id,
                CartItem.menu_size_id == menu_size_id
            )
            .first()
        )
        
        if existing_item:
            existing_item.quantity += quantity
        else:
            new_item = CartItem(
                cart_id=cart.id,
                menu_size_id=menu_size_id,
                quantity=quantity
            )
            self.db.add(new_item)
        
        self.db.commit()
        
        item_name = menu_size.menu_item.name
        size = menu_size.size
        price = menu_size.price
        
        actual_quantity = existing_item.quantity if existing_item else quantity

        return {
            "success": True,
            "message": f"Added {item_name} ({size}) x {actual_quantity} to cart",
            "item": {
                "name": item_name,
                "size": size,
                "price": price,
                "quantity": actual_quantity
            }

        }

    def remove_item(self, user_id: int, menu_size_id: int):
        """
        Remove item from cart
        Args:
            user_id: User ID
            menu_size_id: MenuSize ID to remove
        Returns: Result dict
        """
        cart = self.get_or_create_cart(user_id)

        item = (
            self.db.query(CartItem)
            .filter(
                CartItem.cart_id == cart.id,
                CartItem.menu_size_id == menu_size_id
            )
            .first()
        )

        if not item:
            return {"success": False, "message": "Item not found in cart"}

        item_name = item.menu_size.menu_item.name
        self.db.delete(item)
        self.db.commit()

        return {"success": True, "message": f"Removed {item_name} from cart"}

    def clear_cart(self, user_id: int) -> dict:
        """Remove all items from cart"""
        try:
            cart = self.get_or_create_cart(user_id)
            self.db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
            self.db.commit()
            return {"success": True, "message": "Cart cleared"}
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def view_cart(self, user_id: int):
        """
        Get cart contents with total price
        Returns: {items: [...], total_price, item_count}
        """
        cart = self.get_or_create_cart(user_id)

        items = self.db.query(CartItem).filter(CartItem.cart_id == cart.id).all()

        cart_data = []
        total = 0
        
        for item in items:
            item_total = item.quantity * item.menu_size.price
            total += item_total
            
            cart_data.append({
                "menu_size_id": item.menu_size_id,
                "item_name": item.menu_size.menu_item.name,
                "category": item.menu_size.menu_item.category,
                "size": item.menu_size.size,
                "price": item.menu_size.price,
                "quantity": item.quantity,
                "subtotal": item_total
            })

        return {
            "success": True,
            "items": cart_data,
            "total_price": total,
            "item_count": len(items)
        }
    
    def get_cart_summary(self, user_id: int) -> str:
        """Get formatted cart summary for chat display"""
        cart_data = self.view_cart(user_id)
        
        if not cart_data["items"]:
            return "Your cart is empty"
        
        summary = "Current Cart:\n"
        for item in cart_data["items"]:
            summary += f"  • {item['item_name']} ({item['size']}) x{item['quantity']} = {item['subtotal']} EGP\n"
        
        summary += f"\nTotal: {cart_data['total_price']} EGP"
        return summary
    def update_item_quantity(self, user_id: int, menu_size_id: int, new_quantity: int) -> dict:


        try:
            if new_quantity <= 0:
                return self.remove_item(user_id, menu_size_id)
            
            cart = self.get_or_create_cart(user_id)
            
            # Find cart item
            cart_item = (
                self.db.query(CartItem)
                .filter(CartItem.cart_id == cart.id)
                .filter(CartItem.menu_size_id == menu_size_id)
                .first()
            )
            
            if not cart_item:
                return {
                    "success": False,
                    "error": "Item not found in cart"
                }
            
            old_quantity = cart_item.quantity
            cart_item.quantity = new_quantity
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Updated quantity from {old_quantity} to {new_quantity}"
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }