"""
BranchManager - Handles multiple branches for a single bank and provides
search, filter, and analysis operations across them.
"""
from Environment.BankBranches.Branch import Branch


class BranchManager:
    """
    Manages a collection of Branch objects for a single bank.
    Provides CRUD, search/filter, query, and analysis operations.
    """

    def __init__(self, bank_name):
        """
        Initialise the manager for a specific bank.

        :param bank_name: Name of the bank this manager belongs to.
        """
        self.bank_name = bank_name
        self.branches = {}

    # --------------------------------------------------------------------
    #  CRUD OPERATIONS
    # --------------------------------------------------------------------

    def add_branch(self, branch):
        """
        Add a branch to the manager.

        :param branch: Branch object to store.
        """
        self.branches[branch.branch_id] = branch

    def remove_branch(self, branch_id):
        """
        Remove a branch from the manager by its ID.

        :param branch_id: ID of the branch to remove.
        """
        if branch_id not in self.branches:
            return
        del self.branches[branch_id]

    def get_branch(self, branch_id):
        """
        Get a single branch by its ID.

        :param branch_id: ID of the branch to retrieve.
        :return: Branch object, or None if not found.
        """
        if branch_id not in self.branches:
            return None
        return self.branches[branch_id]

    def update_branch(self, branch_id, **kwargs):
        """
        Update one or more properties on an existing branch.

        :param branch_id: ID of the branch to update.
        :param kwargs: Key-value pairs of properties to set.
        """
        if branch_id not in self.branches:
            raise ValueError(f"Branch {branch_id} not found")

        branch = self.branches[branch_id]
        for key, value in kwargs.items():
            if hasattr(branch, key):
                setattr(branch, key, value)

    # --------------------------------------------------------------------
    #  SEARCH / FILTER OPERATIONS
    # --------------------------------------------------------------------

    def get_branches_by_location(self, location):
        """
        Get all branches in a specific location.

        :param location: Location string to match (case-insensitive).
        :return: List of matching Branch objects.
        """
        return [b for b in self.branches.values()
                if b.location.lower() == location.lower()]

    def get_branches_with_product(self, product_id):
        """
        Find all branches offering a specific mortgage product.

        :param product_id: Product ID to search for.
        :return: List of Branch objects that offer this product.
        """
        return [b for b in self.branches.values()
                if b.get_product(product_id)]

    def search_branches(self, **criteria):
        """
        Generic search with multiple optional criteria.

        :param criteria: Keyword arguments such as location or product_id.
        :return: List of Branch objects matching all provided criteria.
        """
        results = list(self.branches.values())

        if 'location' in criteria:
            results = [b for b in results
                       if b.location.lower() == criteria['location'].lower()]

        if 'product_id' in criteria:
            results = [b for b in results
                       if b.get_product(criteria['product_id'])]

        return results

    # --------------------------------------------------------------------
    #  QUERY OPERATIONS
    # --------------------------------------------------------------------

    def get_all_branches(self):
        """
        Return all branches managed by this manager.

        :return: List of all Branch objects.
        """
        return list(self.branches.values())

    def get_branch_count(self):
        """
        Return the number of branches.

        :return: Integer count of branches.
        """
        return len(self.branches)

    def branch_exists(self, branch_id):
        """
        Check if a branch exists in the manager.

        :param branch_id: ID of the branch to check.
        """
        if branch_id not in self.branches:
            print(f"self.branches[{branch_id}] not found")

    # --------------------------------------------------------------------
    #  ANALYSIS OPERATIONS
    # --------------------------------------------------------------------

    def get_all_available_products(self):
        """
        Get all unique product IDs offered across all branches.

        :return: List of unique product ID strings.
        """
        all_products = set()
        for branch in self.branches.values():
            all_products.update(branch.available_products)
        return list(all_products)

    def get_common_products(self):
        """
        Get product IDs offered at every branch (intersection).

        :return: List of product ID strings common to all branches.
        """
        if not self.branches:
            return []

        # Start with the first branch's products and intersect with the rest
        common = set(list(self.branches.values())[0].available_products)
        for branch in list(self.branches.values())[1:]:
            common = common.intersection(set(branch.available_products))

        return list(common)

    def __str__(self):
        """Return a readable summary of the manager."""
        return f"{self.bank_name} - {self.get_branch_count()} branches"

    def get_branch_id_by_name(self, branch_name):
        """
        Look up a branch ID by its name (case-insensitive).

        :param branch_name: The branch name to search for.
        :return: Branch ID string, or None if not found.
        """
        for branch in self.branches.values():
            if branch.branch_name.lower() == branch_name.lower():
                return branch.branch_id
        return None

