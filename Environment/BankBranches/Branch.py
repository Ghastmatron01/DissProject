class Branch:
    def __init__(self, branch_id, branch_name, location, address, available_products):
        self.branch_id = branch_id
        self.branch_name = branch_name
        self.location = location
        self.address = address
        self.available_products = available_products # list of product ID's
