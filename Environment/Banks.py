"""
Bank class - loads branch data and manages branches through BranchManager.
When created, it automatically populates itself with branches from branch_data.py
"""
from BankBranches.BranchManager import BranchManager
from BankBranches.Branch import Branch
from BankBranches.branch_data import BANK_BRANCHES

class Bank:
    def __init__(self, bank_name):
        self.bank_name = bank_name
        self.branch_manager = BranchManager(bank_name)
        self._load_branches()  # Automatically load data on creation

    def _load_branches(self):
        """Load branches from branch_data.py and populate the BranchManager"""
        bank_key = self.bank_name.lower()

        # Get branches for this bank from branch_data
        if bank_key not in BANK_BRANCHES:
            raise ValueError(f"Bank {self.bank_name} not found in branch_data")

        branches_data = BANK_BRANCHES[bank_key]

        # Create Branch objects and add them to the manager
        for branch_data in branches_data:
            branch = Branch(
                branch_id=branch_data["branch_id"],
                bank_name=self.bank_name,
                branch_name=branch_data["address"],  # Use address and bank name as name
                location=self._extract_city(branch_data["postcode"]),
                address=branch_data["address"],
                available_products=branch_data["available_products"]
            )
            self.branch_manager.add_branch(branch)

    def _extract_city(self, postcode):
        """
        Extract city from postcode (M1 = Manchester, W1 = London, etc.)
        In time will create a python data file with all postcode prefixes with city names
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
        """Add a branch"""
        self.branch_manager.add_branch(branch)

    def get_branch(self, branch_id):
        """Get a specific branch"""
        return self.branch_manager.get_branch(branch_id)

    def get_branches_by_location(self, location):
        """Find branches in a location"""
        return self.branch_manager.get_branches_by_location(location)

    def get_all_branches(self):
        """Get all branches"""
        return self.branch_manager.get_all_branches()

    def __str__(self):
        return f"{self.bank_name} - {self.branch_manager.get_branch_count()} branches"
