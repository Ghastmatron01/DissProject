"""
Bank class - loads branch data and manages branches through BranchManager.
When created, it automatically populates itself with branches from branch_data.py.
"""
from BankBranches.BranchManager import BranchManager
from BankBranches.Branch import Branch
from BankBranches.branch_data import BANK_BRANCHES


class Bank:
    """
    Represents a bank with multiple branches. Automatically loads
    branch data on creation and provides methods to query branches
    and their products.
    """

    def __init__(self, bank_name):
        """
        Initialise the bank and load all its branches from branch_data.

        :param bank_name: Name of the bank (must match a key in BANK_BRANCHES).
        """
        self.bank_name = bank_name
        self.branch_manager = BranchManager(bank_name)
        self._load_branches()  # Automatically load data on creation

    def _load_branches(self):
        """
        Load branches from branch_data.py and populate the BranchManager.
        """
        bank_key = self.bank_name.lower()

        # Check that the bank exists in the data
        if bank_key not in BANK_BRANCHES:
            raise ValueError(f"Bank {self.bank_name} not found in branch_data")

        branches_data = BANK_BRANCHES[bank_key]

        # Create Branch objects and add them to the manager
        for branch_data in branches_data:
            branch = Branch(
                branch_id=branch_data["branch_id"],
                bank_name=self.bank_name,
                branch_name=branch_data["address"],
                location=self._extract_city(branch_data["postcode"]),
                address=branch_data["address"],
                available_products=branch_data["available_products"]
            )
            self.branch_manager.add_branch(branch)

    def _extract_city(self, postcode):
        """
        Extract a city name from a postcode prefix. Uses a simple
        lookup map for common UK postcode areas.

        :param postcode: Full postcode string (e.g. "M1 1AL").
        :return: City name string, or "Unknown" if not recognised.
        """
        postcode_prefix = postcode.split()[0]

        city_map = {
            "M": "Manchester",
            "W": "London",
            "EC": "London",
            "B": "Birmingham",
            "E": "London"
        }

        for prefix, city in city_map.items():
            if postcode_prefix.startswith(prefix):
                return city

        return "Unknown"

    def add_branch(self, branch):
        """
        Add a branch to this bank.

        :param branch: Branch object to add.
        """
        self.branch_manager.add_branch(branch)

    def get_branch(self, branch_id):
        """
        Get a specific branch by its ID.

        :param branch_id: The branch's unique identifier.
        :return: Branch object, or None if not found.
        """
        return self.branch_manager.get_branch(branch_id)

    def get_branches_by_location(self, location):
        """
        Find all branches in a given location.

        :param location: Location string to search for (e.g. "Manchester").
        :return: List of matching Branch objects.
        """
        return self.branch_manager.get_branches_by_location(location)

    def get_all_branches(self):
        """
        Get all branches belonging to this bank.

        :return: List of all Branch objects.
        """
        return self.branch_manager.get_all_branches()

    def get_products_by_branch(self, branch_id):
        """
        Get the products offered by a specific branch.

        :param branch_id: The branch's unique identifier.
        :return: List of product IDs available at that branch.
        """
        branch = self.get_branch(branch_id)
        if not branch:
            raise ValueError(f"Branch {branch_id} not found")
        return Branch.get_product(branch, branch_id)

    def get_branch_id_by_name(self, branch_name):
        """
        Look up a branch ID by its name.

        :param branch_name: The branch name to search for.
        :return: Branch ID string, or None if not found.
        """
        return self.branch_manager.get_branch_id_by_name(branch_name)

    def __str__(self):
        """Return a readable summary of the bank and its branch count."""
        return f"{self.bank_name} - {self.branch_manager.get_branch_count()} branches"
