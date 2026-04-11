class SavingsGoalManager:
    def __init__(self):
        self.goals = {}  # {"christmas": {"target": 600, "monthly": 50, "saved": 0}}

    def add_goal(self, name, target, monthly_contribution):
        self.goals[name] = {
            "target": target,
            "monthly": monthly_contribution,
            "saved": 0
        }

    def contribute(self, name, amount):
        self.goals[name]["saved"] += amount

    def monthly_total(self):
        return sum(goal["monthly"] for goal in self.goals.values())

    def progress(self, name):
        """
        Get progress towards a specific goal as a percentage (0-1 Scale)
        :param name:
        :return:
        """
        if name not in self.goals:
            raise ValueError(f"Goal {name} does not exist")

        g = self.goals[name]
        if g["target"] <= 0:
            raise ValueError(f"Target must be > 0, got {g['target']}")

        return min(g["saved"] / g["target"], 1.0)

    def get_summary(self, name):
        """
        get a detailed summary for the goal
        :param name:
        :return:
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
            "progress_percentage": self.progress(name)*100,
            "monthly_contribution": g["monthly"]
        }