# Class to help the user payoff their debts, grievances, and alimony
class DebtManager:
    """
    Handles the User defined debts
    """
    def __init__(self):
        self.debts = {}

    def add_debt(self, name, balance, apr, min_payment, monthly_payment=None):
        """
        Add a debt to the system.
        monthly_payment defaults to min_payment if not provided.
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
        self.debts[name]["monthly_payment"] = new_payment


    def monthly_interest_rate(self, apr):
        return apr / 12


    def model_payoff(self, name):
        """
        Simulates the debt month-by-month until paid off.
        Returns:
            - months to payoff
            - total interest paid
            - optional: amortisation schedule (list of dicts with month, interest, payment, remaining balance)
        """
        debt = self.debts[name]
        balance = debt["balance"]
        monthly_rate = self.monthly_interest_rate(debt["apr"])
        payment = debt["monthly_payment"]

        months = 0
        total_interest = 0

        # Optional: store amortisation schedule
        schedule = []

        while balance > 0:
            interest = balance * monthly_rate
            total_interest += interest
            balance += interest

            # Prevent infinite loop if payment is too small
            if payment <= interest:
                raise ValueError(
                    f"Payment for {name} is too low to cover interest. Increase payment."
                )

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
    return sum(d["monthly_payment"] for d in self.debts.values())


def full_summary(self):
    summary = {}
    for name in self.debts:
        summary[name] = self.model_payoff(name)
    return summary
