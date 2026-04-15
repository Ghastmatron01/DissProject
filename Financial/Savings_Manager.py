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

    def remove_goal(self, name):
        """
        Remove a savings goal. Any money already saved towards it stays
        in the agent's general savings.

        :param name: Name of the goal to remove.
        :return: The amount that was saved towards this goal before removal.
        """
        if name not in self.goals:
            return 0
        saved = self.goals[name]["saved"]
        del self.goals[name]
        return saved

    def contribute(self, name, amount):
        """
        Add a contribution to an existing goal.

        :param name: Name of the goal to contribute to.
        :param amount: Amount to add to the saved total.
        """
        self.goals[name]["saved"] += amount

    def contribute_annual(self):
        """
        Apply 12 months of contributions to every active goal. If a goal
        reaches its target it is capped at the target amount.

        :return: Total amount contributed across all goals this year.
        """
        total_contributed = 0
        for name, goal in self.goals.items():
            remaining_to_target = max(0, goal["target"] - goal["saved"])
            # Contribute up to 12 months, but don't overshoot the target
            annual_amount = min(goal["monthly"] * 12, remaining_to_target)
            goal["saved"] += annual_amount
            total_contributed += annual_amount
        return total_contributed

    def contribute_monthly(self):
        """
        Apply 1 month of contributions to every active goal. If a goal
        reaches its target it is capped at the target amount.

        :return: Total amount contributed across all goals this month.
        """
        total_contributed = 0
        for name, goal in self.goals.items():
            remaining_to_target = max(0, goal["target"] - goal["saved"])
            # Contribute 1 month, but don't overshoot the target
            monthly_amount = min(goal["monthly"], remaining_to_target)
            goal["saved"] += monthly_amount
            total_contributed += monthly_amount
        return total_contributed

    def monthly_total(self):
        """
        Calculate the total monthly contributions across all active goals.
        (goals that haven't reached their target yet).

        :return: Sum of monthly contributions for incomplete goals.
        """
        total = 0
        for goal in self.goals.values():
            if goal["saved"] < goal["target"]:
                total += goal["monthly"]
        return total

    def has_goals(self):
        """
        Check if there are any active goals.

        :return: True if there is at least one goal.
        """
        return len(self.goals) > 0

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

    def get_all_summaries(self):
        """
        Get summaries for every savings goal.

        :return: List of summary dicts, one per goal.
        """
        return [self.get_summary(name) for name in self.goals]
