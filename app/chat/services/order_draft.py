class OrderDraft:
    def __init__(self):
        self.items = []
        self.address = None
        self.phone = None
    
    def add_item(self, item_name, size=None):
        self.items.append({"item": item_name, "size": size})
    
    def remove_item(self, item_name):
        self.items = [i for i in self.items if i["item"] != item_name]
    
    def summary(self):
        return {"items": self.items, "address": self.address, "phone": self.phone}
