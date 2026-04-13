class SavingsGoalManager:
    """
    Track savings goals with target amounts, monthly contributions,
    and progress tracking.
    """

    def __init__(self):
        """Initialise with an empty goals dictionary."""
        self.goals = {}

    def add_goal(self, name, target, monthly_contribution):
        """
        Add a new savings goal.

        :param name: Name of the goal (e.g. "holiday").
        :param target: Target amount to save.
        :param monthly_contribution: Amount to save each month towards this goal.
        """
        self.goals[name] = {
            "target": target,
            "monthly": monthly_contribution,
            "saved": 0
        }

    def contribute(self, name, amount):
        """
        Add a contribution to an existing goal.

        :param name: Name of the goal to contribute to.
        :param amount: Amount to add to the saved total.
        """
        self.goals[name]["saved"] += amount

    def monthly_total(self):
        """
        Calculate the total monthly contributions across all goals.

        :return: Sum of all monthly contributions.
        """
        return sum(goal["monthly"] for goal in self.goals.values())

    def progress(self, name):
        """
        Get progress towards a specific goal as a fraction (0.0 to 1.0).

        :param name: Name of the goal.
        :return: Progress as a float between 0.0 and 1.0.
        """
        if name not in self.goals:
            raise ValueError(f"Goal {name} does not exist")

        g = self.goals[name]
        if g["target"] <= 0:
            raise ValueError(f"Target must be > 0, got {g['target']}")

        return min(g["saved"] / g["target"], 1.0)

    def get_summary(self, name):
        """
        Get a detailed summary for a specific savings goal.

        :param name: Name of the goal.
        :return: Dict with name, target, monthly, saved, remaining,
                 progress_percentage, and monthly_contribution.
        """
        if name not in self.goals:
            raise ValueError(f"Goal {name} does not exist")

        g = self.goals[name]
        return {
            "name": name,
            "target": g["target"],
            "monthly": g["monthly"],
            "saved": g["saved"],
            "remaining": max(0, g["target"] - g["saved"]),
            "progress_percentage": self.progress(name) * 100,
            "monthly_contribution": g["monthly"]
        }