# Class to help the user payoff their debts, grievances, and alimony
class DebtManager:
    """
    Handles user-defined debts. Supports adding debts, updating payments,
    modelling payoff timelines, and calculating total monthly obligations.
    """

    def __init__(self):
        """Initialise with an empty debts dictionary."""
        self.debts = {}

    def add_debt(self, name, balance, apr, min_payment, monthly_payment=None):
        """
        Add a debt to the system.

        :param name: Name or label for the debt (e.g. "credit_card").
        :param balance: Outstanding balance.
        :param apr: Annual percentage rate (e.g. 0.19 for 19%).
        :param min_payment: Minimum required monthly payment.
        :param monthly_payment: Actual monthly payment (defaults to min_payment).
        """
        if monthly_payment is None:
            monthly_payment = min_payment

        self.debts[name] = {
            "balance": balance,
            "apr": apr,
            "min_payment": min_payment,
            "monthly_payment": monthly_payment
        }

    def update_payment(self, name, new_payment):
        """
        Update the monthly payment for an existing debt.

        :param name: Name of the debt to update.
        :param new_payment: The new monthly payment amount.
        """
        self.debts[name]["monthly_payment"] = new_payment

    def monthly_interest_rate(self, apr):
        """
        Convert an annual percentage rate to a monthly rate.

        :param apr: Annual percentage rate.
        :return: Monthly interest rate.
        """
        return apr / 12

    def model_payoff(self, name):
        """
        Simulate the debt month-by-month until paid off.

        :param name: Name of the debt to model.
        :return: Dict with months to payoff, total interest paid,
                 and an amortisation schedule.
        """
        debt = self.debts[name]
        balance = debt["balance"]
        monthly_rate = self.monthly_interest_rate(debt["apr"])
        payment = debt["monthly_payment"]

        months = 0
        total_interest = 0
        schedule = []

        while balance > 0:
            # Calculate interest for this month
            interest = balance * monthly_rate
            total_interest += interest
            balance += interest

            # Prevent infinite loop if payment is too small
            if payment <= interest:
                raise ValueError(
                    f"Payment for {name} is too low to cover interest. Increase payment."
                )

            # Apply payment and ensure balance does not go negative
            balance -= payment
            balance = max(balance, 0)

            months += 1

            schedule.append({
                "month": months,
                "interest": interest,
                "payment": payment,
                "remaining_balance": balance
            })

        return {
            "months": months,
            "total_interest": total_interest,
            "schedule": schedule
        }

    def total_monthly_payments(self):
        """
        Calculate the total monthly payments across all debts.

        :return: Sum of all monthly debt payments.
        """
        return sum(d["monthly_payment"] for d in self.debts.values())

    def accrue_monthly(self):
        """
        Apply one month of interest and payments to every debt.
        Debts whose balance reaches zero are marked as paid off.

        :return: Dict mapping debt name to a dict with 'interest',
                 'payment', 'new_balance', and 'paid_off'.
        """
        results = {}
        paid_off = []
        for name, debt in self.debts.items():
            monthly_rate = self.monthly_interest_rate(debt["apr"])
            interest = debt["balance"] * monthly_rate
            debt["balance"] += interest
            debt["balance"] -= debt["monthly_payment"]
            if debt["balance"] <= 0:
                debt["balance"] = 0
                paid_off.append(name)
            results[name] = {
                "interest": round(interest, 2),
                "payment": debt["monthly_payment"],
                "new_balance": round(debt["balance"], 2),
                "paid_off": debt["balance"] <= 0,
            }
        # Remove debts that hit zero
        for name in paid_off:
            del self.debts[name]
        return results

    def accrue_annual(self):
        """
        Apply 12 months of interest and payments to every debt in one go.

        :return: Dict mapping debt name to final results.
        """
        combined = {}
        for _ in range(12):
            monthly = self.accrue_monthly()
            for name, data in monthly.items():
                combined[name] = data
        return combined

    def declare_bankruptcy(self):
        """Wipes all unsecured debt and returns the amount forgiven."""
        wiped_amount = sum(d["balance"] for d in self.debts.values())
        self.debts.clear()
        return wiped_amount

    def full_summary(self):
        """
        Run the payoff model for every debt and return a combined summary.

        :return: Dict mapping each debt name to its payoff model result.
        """
        summary = {}
        for name in self.debts:
            summary[name] = self.model_payoff(name)
        return summary

    def full_debt_list(self):
        """
        return a dictionary of all debts with their current balances and monthly payments.
        :return:
        """
        return {
            name: {
                "balance": debt["balance"],
                "monthly_payment": debt["monthly_payment"]
            }
            for name, debt in self.debts.items()
        }