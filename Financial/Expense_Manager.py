# file to be an Expense manager for the user

class expense_manager:
    """
    Handles the user-defined expenses.
    Will allow for the adding, removing, grouping and calculating totals
    """

    DEFAULT_CATEGORIES = [
        "housing",
        "utilities",
        "food",
        "transport",
        "subscriptions",
        "insurance",
        "health",
        "hobbies",
        "misc"
    ]

    def __init__(self):
        """
        # Structure:
        # {
        #   "food": {
        #       "groceries": {"amount": 200, "frequency": "monthly"},
        #       "takeaway": {"amount": 20, "frequency": "weekly"}
        #   }
        # }
        #"christmas": {"amount": 600, "spread_over_months": 12},
        #"new_pc": {"amount": 1200, "spread_over_months": 12},
        #"holiday": {"amount": 1500, "spread_over_months": 6}
        """

        self.categories = {cat: {} for cat in self.DEFAULT_CATEGORIES}
        self.one_off_expenses = {}

    # -------------------------
    # Recurring expenses
    # -------------------------
    def add_expense(self, category, name, amount, frequency="monthly"):
        if category not in self.categories:
            self.categories[category] = {}

        if frequency not in ["daily", "weekly", "monthly", "annual"]:
            raise ValueError("Invalid frequency")

        self.categories[category][name] = {
            "amount": amount,
            "frequency": frequency
        }

    def _convert_to_monthly(self, amount, frequency):
        if frequency == "monthly":
            return amount
        if frequency == "weekly":
            return amount * 52 / 12
        if frequency == "annual":
            return amount / 12
        if frequency == "daily":
            return amount * 365 / 12

    # -------------------------
    # One-off expenses
    # -------------------------
    def add_one_off(self, name, amount, spread_over_months=12):
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        if spread_over_months <= 0:
            raise ValueError("Spread must be at least 1 month")

        self.one_off_expenses[name] = {
            "amount": amount,
            "spread_over_months": spread_over_months
        }

    def monthly_one_off_total(self):
        total = 0
        for data in self.one_off_expenses.values():
            total += data["amount"] / data["spread_over_months"]
        return total

    # -------------------------
    # Totals
    # -------------------------
    def total_monthly(self):
        recurring_total = 0
        for cat_expenses in self.categories.values():
            for data in cat_expenses.values():
                recurring_total += self._convert_to_monthly(data["amount"], data["frequency"])

        return recurring_total + self.monthly_one_off_total()

    def breakdown(self):
        return {
            "recurring": self.categories,
            "one_off": self.one_off_expenses
        }
