from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.menu import MenuItem, MenuSize


class MenuService:
    """Service to query and manage menu items from database"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_item_by_name(self, item_name: str, exact_match: bool = False) -> MenuItem:
        """
        Get menu item by name with all available sizes
        Args:
            item_name: Item name to search
            exact_match: If True, only exact matches; if False, fuzzy matching
        Returns: MenuItem with sizes relationship loaded
        """
        if exact_match:
            item = (
                self.db.query(MenuItem)
                .filter(MenuItem.name.ilike(item_name))
                .first()
            )
        else:
            # ILIKE for case-insensitive search (works with fuzzy matching)
            item = (
                self.db.query(MenuItem)
                .filter(MenuItem.name.ilike(f"%{item_name}%"))
                .first()
            )
        return item
    
    def search_items_fuzzy(self, query: str, category: str = None) -> list:
        """
        Fuzzy search items (case-insensitive substring match)
        Returns items sorted by name similarity
        """
        q = self.db.query(MenuItem).filter(
            MenuItem.name.ilike(f"%{query}%")
        )
        
        if category:
            q = q.filter(MenuItem.category == category)
        
        items = q.all()
        
        # Sort by similarity (shorter difference = better match)
        items_sorted = sorted(
            items,
            key=lambda x: abs(len(x.name) - len(query))
        )
        
        return items_sorted
    
    def get_item_by_id(self, item_id: int) -> MenuItem:
        """Get menu item by ID with all sizes"""
        item = self.db.query(MenuItem).filter(MenuItem.id == item_id).first()
        return item
    
    def get_item_size_price(self, item_id: int, size: str, check_availability: bool = True) -> MenuSize:
        """
        Get specific size and price for an item
        Args:
            item_id: MenuItem ID
            size: Size code (S, M, L, REG)
            check_availability: If True, only return if available
        Returns: MenuSize object with price, or None if not found/unavailable
        """
        q = self.db.query(MenuSize).filter(
            MenuSize.menu_item_id == item_id,
            MenuSize.size == size.upper()
        )
        
        if check_availability:
            q = q.filter(MenuSize.is_available == True)
        
        menu_size = q.first()
        return menu_size
    
    def search_items(self, query: str, category: str = None) -> list:
        """
        Search menu items by name
        Args:
            query: Search term
            category: Optional filter (pizza, addition, drink, etc)
        Returns: List of MenuItems
        """
        q = self.db.query(MenuItem).filter(MenuItem.name.ilike(f"%{query}%"))
        
        if category:
            q = q.filter(MenuItem.category == category)
        
        return q.all()
    
    def get_all_items_by_category(self, category: str, available_only: bool = True) -> list:
        """Get all items in a category"""
        q = self.db.query(MenuItem).filter(MenuItem.category == category)
        
        if available_only:
            q = q.filter(MenuItem.is_available == True)
        
        return q.all()
    
    def get_all_pizzas(self, available_only: bool = True) -> list:
        """Get all pizzas"""
        return self.get_all_items_by_category("pizza", available_only)
    
    def get_all_additions(self, available_only: bool = True) -> list:
        """Get all additions (sides, drinks, etc)"""
        q = self.db.query(MenuItem).filter(MenuItem.category != "pizza")
        
        if available_only:
            q = q.filter(MenuItem.is_available == True)
        
        return q.all()
    
    def get_item_with_all_prices(self, item_id: int) -> dict:
        """
        Get item with all available sizes and prices
        Returns: {item_name, category, sizes: [{size, price}, ...]}
        """
        item = self.get_item_by_id(item_id)
        if not item:
            return None
        
        return {
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "sizes": [
                {
                    "size": size.size,
                    "price": size.price,
                    "menu_size_id": size.id
                }
                for size in item.sizes
            ]
        }
    
    def format_item_for_display(self, item: MenuItem, show_availability: bool = False) -> str:
        """
        Format menu item for display in chat
        Example: "Pizza Name (S: 100 EGP, M: 140 EGP, L: 180 EGP)"
        """
        if not item:
            return None
        
        # Filter only available sizes
        available_sizes = [s for s in item.sizes if s.is_available]
        
        if not available_sizes:
            return f"{item.name} (Currently unavailable)"
        
        sizes_str = ", ".join([f"{s.size}: {s.price} EGP" for s in available_sizes])
        result = f"{item.name} ({sizes_str})"
        
        if show_availability and not item.is_available:
            result += " [OUT OF STOCK]"
        
        return result
    
    def is_item_available(self, item_id: int) -> bool:
        """Check if item is available"""
        item = self.get_item_by_id(item_id)
        return item.is_available if item else False
    
    def is_size_available(self, menu_size_id: int) -> bool:
        """Check if specific size is available"""
        menu_size = self.db.query(MenuSize).filter(MenuSize.id == menu_size_id).first()
        return menu_size.is_available if menu_size else False
    
    def toggle_item_availability(self, item_id: int, available: bool):
        """Toggle item availability"""
        item = self.get_item_by_id(item_id)
        if item:
            item.is_available = available
            self.db.commit()
    
    def toggle_size_availability(self, menu_size_id: int, available: bool):
        """Toggle size availability"""
        menu_size = self.db.query(MenuSize).filter(MenuSize.id == menu_size_id).first()
        if menu_size:
            menu_size.is_available = available
            self.db.commit()
