# Branch.py
# Class should handle specific data of just one branch object

class Branch:
    def __init__(self, branch_id, bank_name, branch_name, location, address, available_products):
        self.branch_id = branch_id
        self.bank_name = bank_name
        self.branch_name = branch_name
        self.location = location
        self.address = address
        self.available_products = available_products # list of product ID's

    def get_product(self, product_id):
        """Check if this branch offers a product"""
        return product_id in self.available_products

    def add_product(self, product_id):
        """Add a product to this branch"""
        if product_id not in self.available_products:
            self.available_products.append(product_id)

    def remove_product(self, product_id):
        """Remove a product from this branch"""
        if product_id in self.available_products:
            self.available_products.remove(product_id)

    def __str__(self):
        return f"{self.branch_name} ({self.location}) - Branch ID: {self.branch_id}"