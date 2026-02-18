"""
Recommendation Engine
Provides personalized item suggestions, popular items, and combo deals
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models.menu import MenuItem, MenuSize
from app.models.order import Order, OrderItem
from app.models.cart import Cart, CartItem
from datetime import datetime, timedelta
import random


class RecommendationEngine:
    """
    Intelligent recommendation engine for menu items
    Features:
    - Popular items (global)
    - Personalized suggestions (user history)
    - Combo deals
    - Complementary items
    - Time-based recommendations
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_recommendations(
        self, 
        user_id: int,
        context: Dict[str, Any] = None,
        max_items: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get comprehensive recommendations for user
        Combines multiple recommendation strategies
        """
        recommendations = []
        context = context or {}
        
        # 1. Check if cart has items - suggest complements
        current_cart = context.get('current_cart', {})
        if current_cart.get('items'):
            complement_recs = self.get_complementary_items(current_cart, max_items=2)
            recommendations.extend(complement_recs)
        
        # 2. Get personalized based on history
        if len(recommendations) < max_items:
            personal_recs = self.get_personalized_recommendations(
                user_id, 
                max_items=max_items - len(recommendations)
            )
            recommendations.extend(personal_recs)
        
        # 3. Fill with popular items if needed
        if len(recommendations) < max_items:
            popular_recs = self.get_popular_items(
                max_items=max_items - len(recommendations),
                exclude_items=[r['name'] for r in recommendations]
            )
            recommendations.extend(popular_recs)
        
        return recommendations[:max_items]
    
    def get_popular_items(
        self, 
        max_items: int = 5,
        category: Optional[str] = None,
        exclude_items: List[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get most popular items based on order history
        
        Args:
            max_items: Maximum items to return
            category: Filter by category (pizza, addition)
            exclude_items: Item names to exclude
            days: Consider orders from last N days
        
        Returns:
            List of popular items with order count
        """
        exclude_items = exclude_items or []
        
        try:
            # Get date threshold
            date_threshold = datetime.utcnow() - timedelta(days=days)
            
            # Query for most ordered items
            query = (
                self.db.query(
                    OrderItem.menu_item_name,
                    func.count(OrderItem.id).label('order_count'),
                    func.sum(OrderItem.quantity).label('total_quantity')
                )
                .join(Order, Order.id == OrderItem.order_id)
                .filter(Order.created_at >= date_threshold)
                .filter(Order.status != 'cancelled')
            )
            
            # Exclude items
            if exclude_items:
                query = query.filter(~OrderItem.menu_item_name.in_(exclude_items))
            
            # Group and order
            popular = (
                query
                .group_by(OrderItem.menu_item_name)
                .order_by(desc('order_count'))
                .limit(max_items)
                .all()
            )
            
            # Format results with menu details
            results = []
            for item_name, order_count, total_qty in popular:
                menu_item = (
                    self.db.query(MenuItem)
                    .filter(MenuItem.name == item_name)
                    .first()
                )
                
                if menu_item and menu_item.is_available:
                    # Filter by category if specified
                    if category and menu_item.category != category:
                        continue
                    
                    # Get size options
                    sizes = []
                    for size in menu_item.sizes:
                        if size.is_available:
                            sizes.append({
                                "size": size.size,
                                "price": size.price,
                                "id": size.id
                            })
                    
                    results.append({
                        "name": menu_item.name,
                        "category": menu_item.category,
                        "description": menu_item.description,
                        "sizes": sizes,
                        "order_count": order_count,
                        "popularity_score": total_qty,
                        "recommendation_reason": "Popular choice",
                        "badge": "🔥 Popular"
                    })
            
            return results
            
        except Exception as e:
            print(f"Error getting popular items: {e}")
            return self._get_fallback_recommendations(max_items, category)
    
    def get_personalized_recommendations(
        self, 
        user_id: int,
        max_items: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations based on user's order history
        """
        try:
            # Get user's past orders (last 90 days)
            date_threshold = datetime.utcnow() - timedelta(days=90)
            
            user_orders = (
                self.db.query(OrderItem.menu_item_name, func.count(OrderItem.id).label('count'))
                .join(Order, Order.id == OrderItem.order_id)
                .filter(Order.user_id == user_id)
                .filter(Order.created_at >= date_threshold)
                .group_by(OrderItem.menu_item_name)
                .order_by(desc('count'))
                .limit(3)
                .all()
            )
            
            if not user_orders:
                return []
            
            # Get items user ordered before
            ordered_items = [name for name, _ in user_orders]
            
            # Find similar items (same category) that user hasn't ordered recently
            recommendations = []
            
            for item_name, order_count in user_orders:
                menu_item = (
                    self.db.query(MenuItem)
                    .filter(MenuItem.name == item_name)
                    .first()
                )
                
                if not menu_item:
                    continue
                
                # Find similar items in same category
                similar_items = (
                    self.db.query(MenuItem)
                    .filter(MenuItem.category == menu_item.category)
                    .filter(MenuItem.is_available == True)
                    .filter(~MenuItem.name.in_(ordered_items))
                    .limit(2)
                    .all()
                )
                
                for similar in similar_items:
                    if len(recommendations) >= max_items:
                        break
                    
                    sizes = []
                    for size in similar.sizes:
                        if size.is_available:
                            sizes.append({
                                "size": size.size,
                                "price": size.price,
                                "id": size.id
                            })
                    
                    recommendations.append({
                        "name": similar.name,
                        "category": similar.category,
                        "description": similar.description,
                        "sizes": sizes,
                        "recommendation_reason": f"Similar to your favorite {item_name}",
                        "badge": "✨ For You"
                    })
                
                if len(recommendations) >= max_items:
                    break
            
            return recommendations
            
        except Exception as e:
            print(f"Error getting personalized recommendations: {e}")
            return []
    
    def get_complementary_items(
        self, 
        current_cart: Dict[str, Any],
        max_items: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Suggest items that complement what's already in cart
        Example: User has pizza → suggest drinks/sides
        """
        try:
            cart_items = current_cart.get('items', [])
            if not cart_items:
                return []
            
            # Analyze cart contents
            has_pizza = any(item['category'] == 'pizza' for item in cart_items)
            has_drink = any(item['category'] == 'addition' and 'cola' in item['item_name'].lower() or 'juice' in item['item_name'].lower() for item in cart_items)
            has_side = any(item['category'] == 'addition' and 'fries' in item['item_name'].lower() for item in cart_items)
            
            recommendations = []
            
            # If has pizza but no drink
            if has_pizza and not has_drink:
                drinks = (
                    self.db.query(MenuItem)
                    .filter(MenuItem.category == 'addition')
                    .filter(MenuItem.is_available == True)
                    .filter(MenuItem.name.in_(['Cola', 'Mango Juice']))
                    .limit(1)
                    .all()
                )
                
                for drink in drinks:
                    sizes = [{"size": s.size, "price": s.price, "id": s.id} 
                            for s in drink.sizes if s.is_available]
                    
                    recommendations.append({
                        "name": drink.name,
                        "category": drink.category,
                        "description": drink.description,
                        "sizes": sizes,
                        "recommendation_reason": "Perfect with your pizza!",
                        "badge": "🥤 Pair it"
                    })
            
            # If has pizza but no side
            if has_pizza and not has_side and len(recommendations) < max_items:
                sides = (
                    self.db.query(MenuItem)
                    .filter(MenuItem.category == 'addition')
                    .filter(MenuItem.is_available == True)
                    .filter(MenuItem.name == 'Fries')
                    .first()
                )
                
                if sides:
                    sizes = [{"size": s.size, "price": s.price, "id": s.id} 
                            for s in sides.sizes if s.is_available]
                    
                    recommendations.append({
                        "name": sides.name,
                        "category": sides.category,
                        "description": sides.description,
                        "sizes": sizes,
                        "recommendation_reason": "Complete your meal!",
                        "badge": "🍟 Add on"
                    })
            
            return recommendations[:max_items]
            
        except Exception as e:
            print(f"Error getting complementary items: {e}")
            return []
    
    def get_combo_deals(self) -> List[Dict[str, Any]]:
        """
        Get predefined combo deals
        Example: Pizza + Drink + Fries at discounted price
        """
        combos = [
            {
                "name": "Family Combo",
                "items": ["Large Pizza", "2 Cola", "Fries"],
                "description": "Perfect for family dinner",
                "discount_percent": 15,
                "badge": "💰 Best Deal"
            },
            {
                "name": "Solo Meal",
                "items": ["Medium Pizza", "Cola"],
                "description": "Quick meal for one",
                "discount_percent": 10,
                "badge": "🎯 Quick Meal"
            },
            {
                "name": "Party Pack",
                "items": ["3 Large Pizzas", "3 Cola", "2 Fries"],
                "description": "Feed the whole party!",
                "discount_percent": 20,
                "badge": "🎉 Party"
            }
        ]
        
        return combos
    
    def get_time_based_recommendations(self) -> List[Dict[str, Any]]:
        """
        Recommend items based on time of day
        Example: Lighter options for lunch, full meals for dinner
        """
        hour = datetime.now().hour
        
        if 11 <= hour < 15:
            # Lunch time - suggest medium pizzas
            return self._get_items_by_size_preference("M", "Quick lunch option")
        elif 18 <= hour < 23:
            # Dinner time - suggest large pizzas and combos
            return self._get_items_by_size_preference("L", "Perfect for dinner")
        else:
            return []
    
    def _get_items_by_size_preference(
        self, 
        preferred_size: str,
        reason: str,
        max_items: int = 2
    ) -> List[Dict[str, Any]]:
        """Helper to get items with specific size preference"""
        try:
            items = (
                self.db.query(MenuItem)
                .filter(MenuItem.category == 'pizza')
                .filter(MenuItem.is_available == True)
                .limit(max_items)
                .all()
            )
            
            recommendations = []
            for item in items:
                # Find the preferred size
                preferred = next(
                    (s for s in item.sizes if s.size == preferred_size and s.is_available),
                    None
                )
                
                if preferred:
                    recommendations.append({
                        "name": item.name,
                        "category": item.category,
                        "description": item.description,
                        "sizes": [{"size": preferred.size, "price": preferred.price, "id": preferred.id}],
                        "recommendation_reason": reason,
                        "badge": "⏰ Right Time"
                    })
            
            return recommendations
        except:
            return []
    
    def _get_fallback_recommendations(
        self, 
        max_items: int = 3,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fallback recommendations when no order data available
        Returns top-rated items from menu
        """
        try:
            query = self.db.query(MenuItem).filter(MenuItem.is_available == True)
            
            if category:
                query = query.filter(MenuItem.category == category)
            
            items = query.limit(max_items).all()
            
            recommendations = []
            for item in items:
                sizes = []
                for size in item.sizes:
                    if size.is_available:
                        sizes.append({
                            "size": size.size,
                            "price": size.price,
                            "id": size.id
                        })
                
                recommendations.append({
                    "name": item.name,
                    "category": item.category,
                    "description": item.description,
                    "sizes": sizes,
                    "recommendation_reason": "Great choice",
                    "badge": "⭐ Featured"
                })
            
            return recommendations
        except:
            return []
    
    def format_recommendations_text(
        self, 
        recommendations: List[Dict[str, Any]],
        lang: str = "en"
    ) -> str:
        """Format recommendations as text for chat"""
        if not recommendations:
            return ""
        
        if lang == "ar":
            text = "🎯 اقتراحات ليك:\n\n"
            for rec in recommendations:
                text += f"{rec.get('badge', '⭐')} {rec['name']}\n"
                if rec.get('recommendation_reason'):
                    text += f"   {rec['recommendation_reason']}\n"
                
                # Add size info
                if rec.get('sizes'):
                    sizes = rec['sizes']
                    if len(sizes) == 1:
                        text += f"   {sizes[0]['price']} جنيه\n"
                    else:
                        size_text = ", ".join([f"{s['size']}({s['price']} جنيه)" for s in sizes])
                        text += f"   {size_text}\n"
                text += "\n"
        else:
            text = "🎯 Recommendations for you:\n\n"
            for rec in recommendations:
                text += f"{rec.get('badge', '⭐')} {rec['name']}\n"
                if rec.get('recommendation_reason'):
                    text += f"   {rec['recommendation_reason']}\n"
                
                # Add size info
                if rec.get('sizes'):
                    sizes = rec['sizes']
                    if len(sizes) == 1:
                        text += f"   {sizes[0]['price']} EGP\n"
                    else:
                        size_text = ", ".join([f"{s['size']}({s['price']} EGP)" for s in sizes])
                        text += f"   {size_text}\n"
                text += "\n"
        
        return text
