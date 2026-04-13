# Branch.py
# Class should handle specific data of just one branch object

class Branch:
    """
    Represents a single bank branch with its location, address,
    and available mortgage products.
    """

    def __init__(self, branch_id, bank_name, branch_name, location, address, available_products):
        """
        Initialise a branch with its details.

        :param branch_id: Unique identifier for this branch.
        :param bank_name: Name of the parent bank.
        :param branch_name: Display name for the branch.
        :param location: City or area the branch is located in.
        :param address: Street address of the branch.
        :param available_products: List of mortgage product IDs offered here.
        """
        self.branch_id = branch_id
        self.bank_name = bank_name
        self.branch_name = branch_name
        self.location = location
        self.address = address
        self.available_products = available_products # list of product ID's

    def get_product(self, product_id):
        """
        Check if this branch offers a specific product.

        :param product_id: The product ID to check for.
        :return: True if the product is available, False otherwise.
        """
        return product_id in self.available_products

    def add_product(self, product_id):
        """
        Add a product to this branch's available products.

        :param product_id: The product ID to add.
        """
        if product_id not in self.available_products:
            self.available_products.append(product_id)

    def remove_product(self, product_id):
        """
        Remove a product from this branch's available products.

        :param product_id: The product ID to remove.
        """
        if product_id in self.available_products:
            self.available_products.remove(product_id)

    def __str__(self):
        """Return a readable summary of the branch."""
        return f"{self.branch_name} ({self.location}) - Branch ID: {self.branch_id}"