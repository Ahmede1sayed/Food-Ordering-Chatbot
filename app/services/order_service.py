from sqlalchemy.orm import Session
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem


class OrderService:
    """Service to manage orders"""
    
    def __init__(self, db: Session):
        self.db = db

    def checkout(self, user_id: int):
        """
        Checkout cart and create order
        Args:
            user_id: User ID
        Returns: Result dict with order info
        """
        cart = self.db.query(Cart).filter(Cart.user_id == user_id).first()

        if not cart or not cart.items:
            return {"success": False, "message": "Cart is empty"}

        total = 0
        order = Order(user_id=user_id, total_price=0)
        self.db.add(order)
        self.db.flush()

        items_data = []
        
        for item in cart.items:
            price = item.menu_size.price
            subtotal = price * item.quantity
            total += subtotal

            order_item = OrderItem(
                order_id=order.id,
                menu_item_name=item.menu_size.menu_item.name,
                size=item.menu_size.size,
                quantity=item.quantity,
                price=price
            )

            items_data.append({
                "name": item.menu_size.menu_item.name,
                "size": item.menu_size.size,
                "quantity": item.quantity,
                "price": price,
                "subtotal": subtotal
            })

            self.db.add(order_item)

        order.total_price = total

        # clear cart
        for item in cart.items:
            self.db.delete(item)

        self.db.commit()

        return {
            "success": True,
            "message": "Order placed successfully",
            "order_id": order.id,
            "total_price": total,
            "items": items_data
        }
    
    def get_order(self, order_id: int) -> dict:
        """Get order details"""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        
        if not order:
            return {"success": False, "message": "Order not found"}
        
        return {
            "success": True,
            "order_id": order.id,
            "user_id": order.user_id,
            "total_price": order.total_price,
            "status": order.status,
            "created_at": order.created_at
        }

    def update_status(self, order_id: int, new_status: str):
        """Update order status"""
        order = self.db.query(Order).filter(Order.id == order_id).first()

        if not order:
            return {"success": False, "message": "Order not found"}

        order.status = new_status
        self.db.commit()

        return {"success": True, "message": "Order status updated"}

    def get_user_orders(self, user_id: int):
        """Get all user's orders"""
        return self.db.query(Order).filter(Order.user_id == user_id).all()
    
    def get_all_orders(self):
        """Get all orders"""
        return self.db.query(Order).all()
