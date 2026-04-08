# class to handle multiple branches and their interactions

"""
Branch Manager handles the branches of certain bank names and ones that may have
certain products. For example, this class could answer a query of such
"What bank branches have X"
"""
from Environment.BankBranches.Branch import Branch


class BranchManager:
    def __init__(self, bank_name):
        self.bank_name = bank_name
        self.branches = {}

    # --------------CRUD OPERATIONS---------------

    def add_branch(self, branch):  # Takes a Branch object
        """Add a branch to the manager"""
        self.branches[branch.branch_id] = branch  # Store the branch object

    def remove_branch(self, branch_id):
        """Remove a branch from the manager"""
        if branch_id not in self.branches:
            return
        del self.branches[branch_id]

    def get_branch(self, branch_id):
        """Get the branch from the manager"""
        if branch_id not in self.branches:
            return
        return self.branches[branch_id]

    def update_branch(self, branch_id, **kwargs):
        """Update branch properties"""
        if branch_id not in self.branches:
            raise ValueError(f"Branch {branch_id} not found")

        branch = self.branches[branch_id]
        for key, value in kwargs.items():
            if hasattr(branch, key):
                setattr(branch, key, value)

    # --------------SEARCH/FILTER OPERATIONS------------------

    def get_branches_by_location(self, location):
        """Get the branch from the manager"""
        return [b for b in self.branches.values()
                if b.location.lower() == location.lower()]

    def get_branches_with_product(self, product_id):
        """Find all branches offering a specific product"""
        return [b for b in self.branches.values()
                if b.get_product(product_id)]

    def search_branches(self, **criteria):
        """Generic search with multiple criteria"""
        results = list(self.branches.values())

        if 'location' in criteria:
            results = [b for b in results
                       if b.location.lower() == criteria['location'].lower()]

        if 'product_id' in criteria:
            results = [b for b in results
                       if b.get_product(criteria['product_id'])]

        return results

    # ----------------- QUERY OPERATIONS------------------------

    def get_all_branches(self):
        """Return all branches"""
        return list(self.branches.values())

    def get_branch_count(self):
        """Return the number of branches"""
        return len(list(self.branches.values()))

    def branch_exists(self, branch_id):
        """Check if a branch exists"""
        if branch_id not in self.branches:
            print(f"self.branches[{branch_id}] not found")

    # ----------------------- ANALYSIS OPERATIONS----------------

    def get_all_available_products(self):
        """Get all unique products offered across all branches"""
        all_products = set()
        for branch in self.branches.values():
            all_products.update(branch.available_products)
        return list(all_products)

    def get_common_products(self):
        """Get products offered at ALL branches"""
        if not self.branches:
            return []

        common = set(list(self.branches.values())[0].available_products)
        for branch in list(self.branches.values())[1:]:
            common = common.intersection(set(branch.available_products))

        return list(common)

    def __str__(self):
        return f"{self.bank_name} - {self.get_branch_count()} branches"




