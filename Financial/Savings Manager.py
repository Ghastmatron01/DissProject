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
        g = self.goals[name]
        return g["saved"] / g["target"]