# file to be an Expense manager for the user

class ExpenseManager:
    """
    Handles user-defined expenses. Supports adding, removing, grouping,
    and calculating monthly totals for both recurring and one-off expenses.
    """

    DEFAULT_CATEGORIES = [
        "housing", "utilities", "food", "transport", "subscriptions",
        "insurance", "health", "hobbies", "misc"
    ]

    def __init__(self):
        """
        Initialise with empty expense categories and one-off expenses.
        """
        self.categories = {cat: {} for cat in self.DEFAULT_CATEGORIES}
        self.one_off_expenses = {}

    # --------------------------------------------------------------------
    #  Recurring expenses
    # --------------------------------------------------------------------

    def add_expense(self, category, name, amount, frequency="monthly"):
        """
        Add a recurring expense to a category.

        :param category: One of the DEFAULT_CATEGORIES (e.g. "food").
        :param name: Name of the expense (e.g. "groceries").
        :param amount: The expense amount per frequency period.
        :param frequency: "daily", "weekly", "monthly", or "annual".
        """
        if category not in self.DEFAULT_CATEGORIES:
            raise ValueError(
                f"Invalid Category: {category}. "
                f"Must be one of: {self.DEFAULT_CATEGORIES}"
            )

        if frequency not in ["daily", "weekly", "monthly", "annual"]:
            raise ValueError("Invalid frequency")

        if amount < 0:
            raise ValueError("Amount cannot be negative")

        self.categories[category][name] = {
            "amount": amount,
            "frequency": frequency
        }

    def _convert_to_monthly(self, amount, frequency):
        """
        Convert any frequency to its monthly equivalent.

        :param amount: The expense amount per frequency period.
        :param frequency: "daily", "weekly", "monthly", or "annual".
        :return: The equivalent monthly amount.
        """
        conversion_rates = {
            "daily": amount * 365 / 12,
            "weekly": amount * 52 / 12,
            "monthly": amount,
            "annual": amount / 12
        }

        if frequency not in conversion_rates:
            raise ValueError(f"Invalid frequency: {frequency}")

        return conversion_rates[frequency]

    # --------------------------------------------------------------------
    #  One-off expenses
    # --------------------------------------------------------------------

    def add_one_off(self, name, amount, spread_over_months=12):
        """
        Add a one-off expense spread across a number of months.

        :param name: Name of the expense (e.g. "holiday").
        :param amount: Total cost of the expense.
        :param spread_over_months: Number of months to spread the cost over.
        """
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        if spread_over_months <= 0:
            raise ValueError("Spread must be at least 1 month")

        self.one_off_expenses[name] = {
            "amount": amount,
            "spread_over_months": spread_over_months
        }

    def monthly_one_off_total(self):
        """
        Calculate the total monthly cost of all one-off expenses.

        :return: Total monthly one-off cost.
        """
        total = 0
        for data in self.one_off_expenses.values():
            total += data["amount"] / data["spread_over_months"]
        return total

    # --------------------------------------------------------------------
    #  Totals
    # --------------------------------------------------------------------

    def calculate_total_monthly(self):
        """
        Calculate the total monthly cost of all recurring and one-off expenses.

        :return: Combined monthly total.
        """
        recurring_total = 0
        for cat_expenses in self.categories.values():
            for data in cat_expenses.values():
                recurring_total += self._convert_to_monthly(data["amount"], data["frequency"])

        return recurring_total + self.monthly_one_off_total()

    def total_monthly(self):
        """
        Deprecated: Use calculate_total_monthly instead.

        :return: Combined monthly total.
        """
        return self.calculate_total_monthly()

    def breakdown(self):
        """
        Return the full breakdown of all expenses.

        :return: Dict with "recurring" and "one_off" sub-dicts.
        """
        return {
            "recurring": self.categories,
            "one_off": self.one_off_expenses
        }
