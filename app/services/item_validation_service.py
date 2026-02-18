from sqlalchemy.orm import Session
from app.services.menu_service import MenuService
from app.models.menu import MenuItem, MenuSize
from typing import Tuple, Dict, Any


class ItemValidationService:
    """
    Service to validate menu items before adding to cart
    Checks: existence, availability, size validation, name matching
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.menu_service = MenuService(db)
    
    def validate_and_get_item(self, item_name: str) -> Tuple[bool, MenuItem, str]:
        """
        Validate item exists with fuzzy matching
        
        Args:
            item_name: Item name query
        
        Returns: (success, item, message)
            success: True if item found and available
            item: MenuItem object if found, None otherwise
            message: Error/info message for user
        """
        if not item_name or not item_name.strip():
            return False, None, "Item name cannot be empty"
        
        # Search with fuzzy matching
        item = self.menu_service.get_item_by_name(item_name, exact_match=False)
        
        if not item:
            # Try to find similar items
            similar = self.menu_service.search_items_fuzzy(item_name)
            if similar:
                suggestions = ", ".join([s.name for s in similar[:3]])
                return False, None, f"'{item_name}' not found. Did you mean: {suggestions}?"
            else:
                return False, None, f"'{item_name}' not found in menu"
        
        # Check if item is available
        if not item.is_available:
            return False, None, f"{item.name} is currently out of stock"
        
        return True, item, f"Item '{item.name}' found"
    
    def validate_size(self, item: MenuItem, size: str) -> Tuple[bool, MenuSize, str]:
        """
        Validate size exists for item and is available
        
        Args:
            item: MenuItem object
            size: Size code (S, M, L, REG)
        
        Returns: (success, menu_size, message)
        """
        if not size or not size.strip():
            # Return first available size as default
            available = [s for s in item.sizes if s.is_available]
            if available:
                return True, available[0], f"Using default size: {available[0].size}"
            else:
                return False, None, f"{item.name} has no available sizes"
        
        menu_size = self.menu_service.get_item_size_price(item.id, size, check_availability=True)
        
        if not menu_size:
            # Check if size exists but unavailable
            all_sizes = self.menu_service.get_item_size_price(item.id, size, check_availability=False)
            if all_sizes:
                return False, None, f"{size} size for {item.name} is currently unavailable"
            else:
                available_sizes = [s.size for s in item.sizes]
                return False, None, f"Size {size} not available. Try: {', '.join(available_sizes)}"
        
        return True, menu_size, f"Size {menu_size.size} available"
    
    def validate_full_item(self, item_name: str, size: str = None) -> Tuple[bool, Dict[str, Any], str]:
        """
        Full validation: item exists, size exists, both available
        
        Args:
            item_name: Item name
            size: Optional size code
        
        Returns: (success, item_data, message)
            item_data: {item: MenuItem, menu_size: MenuSize, item_name, size, price}
        """
        # Validate item
        success, item, msg = self.validate_and_get_item(item_name)
        if not success:
            return False, {}, msg
        
        # Validate size
        success, menu_size, msg = self.validate_size(item, size or "")
        if not success:
            return False, {}, msg
        
        # All validations passed
        item_data = {
            "item": item,
            "item_id": item.id,
            "menu_size": menu_size,
            "menu_size_id": menu_size.id,
            "item_name": item.name,
            "size": menu_size.size,
            "price": menu_size.price,
            "category": item.category
        }
        
        return True, item_data, f"{item.name} ({menu_size.size}) is available"
    
    def get_available_sizes(self, item_id: int) -> list:
        """Get all available sizes for an item"""
        item = self.menu_service.get_item_by_id(item_id)
        if not item:
            return []
        return [s for s in item.sizes if s.is_available]
    
    def get_available_sizes_str(self, item_id: int) -> str:
        """Get available sizes as formatted string"""
        sizes = self.get_available_sizes(item_id)
        if not sizes:
            return "No sizes available"
        return ", ".join([f"{s.size} ({s.price} EGP)" for s in sizes])
