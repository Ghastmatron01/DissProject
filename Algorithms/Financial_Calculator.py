# File to calculate the net income of the user after base salary has been entered
class SalaryCalculator:


def calculate_net_income(gross_salary, tax_year):
    """
    A function that calculates the income of the user after tax
    :param gross_salary:
    :param tax_year:
    :return:
    """


def calculate_tax(gross_salary):
    brackets_2026 = [
        {"name": "personal_allowance", "upper": 12570, "rate": 0},
        {"name": "basic_rate", "upper": 50270, "rate": 0.2},
        {"name": "higher_rate", "upper": 125140, "rate": 0.4},
        {"name": "additional_rate", "upper": None, "rate": 0.45}
    ]

    return calculate_tax_recursive(gross_salary, brackets_2026)

def calculate_tax_recursive(gross_salary, brackets, index=0, breakdown=None):
    """
    Recursively walks through the tax brackets and caluclates how much salary
    is taxed in each bracket.
    :param gross_salary:
    :return: tax percentage
    """

    # checks if it is first call, if yes, creates a dictionary of values
    if breakdown is None:
        breakdown = {b["name"]: 0 for b in brackets}

    # base case: no salary left or no more brackets

    if gross_salary <= 0 or index >= len(brackets):
        return breakdown

    bracket = brackets[index]
    upper = bracket["upper"]
    rate = bracket["rate"]
    name = bracket["name"]

    # determine how much salary falls into bracket
    if upper is None:
        # last bracket is no limit
        taxable_amount = gross_salary
    else:
        taxable_amount = max(0, min(gross_salary, upper - (brackets[index - 1]["upper"]
        if index > 0
        else 0)))

    # Apply tax

    breakdown[name] += taxable_amount * rate

    # recurse on remaining salary
    return calculate_tax_recursive(gross_salary - taxable_amount, brackets, index=index+1, breakdown=breakdown)


# def get tax brackets from user


def calculate_ni_recursive(salary, brackets, index=0, breakdown=None):
    """
    A function that calculates the national income for the user, Very similar to previous function calculating tax
    :param salary:
    :param brackets:
    :param index:
    :param breakdown:
    :return:
    """

    if breakdown is None:
        breakdown = {b["name"]: 0 for b in brackets}

    if salary <= 0 or index >= len(brackets):
        return breakdown

    bracket = brackets[index]
    upper = bracket["upper"]
    rate = bracket["rate"]
    name = bracket["name"]

    if upper is None:
        taxable_amount = salary
    else:
        lower_bound = brackets[index - 1]["upper"] if index > 0 else 0
        width = upper - lower_bound
        taxable_amount = max(0, min(salary, width))

    breakdown[name] += taxable_amount * rate

    return calculate_ni_recursive(
        salary - taxable_amount,
        brackets,
        index + 1,
        breakdown
    )

def calculate_national_insurance(gross_salary, category="A"):
    """
    A function similar to tax, where it calls the recursive function
    :param gross_salary:
    :param category:
    :return:
    """
    NI_CATEGORIES = {
        "A": [
            {"name": "lower_band", "upper": 242, "rate": 0.00},
            {"name": "main_band", "upper": 967, "rate": 0.08},
            {"name": "upper_band", "upper": None, "rate": 0.02}
        ],
        "B": [
            {"name": "lower_band", "upper": 242, "rate": 0.00},
            {"name": "main_band", "upper": 967, "rate": 0.0185},
            {"name": "upper_band", "upper": None, "rate": 0.02}
        ],
        "C": [  # Employees over State Pension age — no employee NI
            {"name": "all_income", "upper": None, "rate": 0.00}
        ],
        "D": [
            {"name": "lower_band", "upper": 242, "rate": 0.00},
            {"name": "main_band", "upper": 967, "rate": 0.02},
            {"name": "upper_band", "upper": None, "rate": 0.02}
        ],
        "E": [
            {"name": "lower_band", "upper": 242, "rate": 0.00},
            {"name": "main_band", "upper": 967, "rate": 0.0185},
            {"name": "upper_band", "upper": None, "rate": 0.02}
        ],
        "F": [
            {"name": "lower_band", "upper": 242, "rate": 0.00},
            {"name": "main_band", "upper": 967, "rate": 0.08},
            {"name": "upper_band", "upper": None, "rate": 0.02}
        ],
        "H": [
            {"name": "lower_band", "upper": 242, "rate": 0.00},
            {"name": "main_band", "upper": 967, "rate": 0.08},
            {"name": "upper_band", "upper": None, "rate": 0.02}
        ],
        "I": [
            {"name": "lower_band", "upper": 242, "rate": 0.00},
            {"name": "main_band", "upper": 967, "rate": 0.0185},
            {"name": "upper_band", "upper": None, "rate": 0.02}
        ],
        "J": [
            {"name": "lower_band", "upper": 242, "rate": 0.00},
            {"name": "main_band", "upper": 967, "rate": 0.02},
            {"name": "upper_band", "upper": None, "rate": 0.02}
        ],
        "K": [  # No employee NI
            {"name": "all_income", "upper": None, "rate": 0.00}
        ],
        "L": [
            {"name": "lower_band", "upper": 242, "rate": 0.00},
            {"name": "main_band", "upper": 967, "rate": 0.02},
            {"name": "upper_band", "upper": None, "rate": 0.02}
        ],
        "M": [
            {"name": "lower_band", "upper": 242, "rate": 0.00},
            {"name": "main_band", "upper": 967, "rate": 0.08},
            {"name": "upper_band", "upper": None, "rate": 0.02}
        ],
        "N": [
            {"name": "lower_band", "upper": 242, "rate": 0.00},
            {"name": "main_band", "upper": 967, "rate": 0.08},
            {"name": "upper_band", "upper": None, "rate": 0.02}
        ],
        "S": [  # Over state pension age
            {"name": "all_income", "upper": None, "rate": 0.00}
        ],
        "V": [
            {"name": "lower_band", "upper": 242, "rate": 0.00},
            {"name": "main_band", "upper": 967, "rate": 0.08},
            {"name": "upper_band", "upper": None, "rate": 0.02}
        ],
        "Z": [
            {"name": "lower_band", "upper": 242, "rate": 0.00},
            {"name": "main_band", "upper": 967, "rate": 0.02},
            {"name": "upper_band", "upper": None, "rate": 0.02}
        ]
    }

    if category not in NI_CATEGORIES:
        raise ValueError(f"Unknown NI category: {category}")

    brackets = NI_CATEGORIES[category]
    return calculate_ni_recursive(gross_salary, brackets)


def calculate_student_loan_for_plan(income, threshold, rate):
    """
    A function to calculate student loan for plan
    :param income:
    :param threshold:
    :param rate:
    :return:
    """
    if income <= threshold:
        return 0
    return (income - threshold) * rate

def calculate_student_loan_repayment(weekly_income, plans):
    """
    weekly_income: income per week (to match NI system)
    plans: list of plan names, e.g. ["plan_2", "pgl"]
    """
    STUDENT_LOAN_PLANS = {
        "plan_1": {
            "threshold": 423,
            "rate": 0.09
        },
        "plan_2": {
            "threshold": 524,
            "rate": 0.09
        },
        "plan_4": {
            "threshold": 532,
            "rate": 0.09
        },
        "plan_5": {
            "threshold": 480,
            "rate": 0.09
        },
        "pgl": {
            "threshold": 403,
            "rate": 0.06
        }
    }
    total = 0
    breakdown = {}

    # Checking if the users plan is in the student loan plan
    if plans is None:
        return total
    else:
        for plan in plans:
            if plan not in STUDENT_LOAN_PLANS:
                raise ValueError(f"Unknown student loan plan: {plan}")

            threshold = STUDENT_LOAN_PLANS[plan]["threshold"]
            rate = STUDENT_LOAN_PLANS[plan]["rate"]

            repayment = calculate_student_loan_for_plan(weekly_income, threshold, rate)
            breakdown[plan] = repayment
            total += repayment

        return {
            "total_repayment": total,
            "breakdown": breakdown
        }



def calculate_monthly_expenses(housing_cost, utilities, food, transport, misc):
    """
    A function that calculates the monthly expenses of the user, we need to find out how much the users current rent is,
    how much utilities they pay, how much it is for them to get to and from work, and misc can be any hobbies or extra
    they pay for anything else
    :param housing_cost: 
    :param utilities: 
    :param food: 
    :param transport: 
    :param misc: 
    :return: 
    """



def calculate_savings(net_income, expenses):
    """
    A function to calculate realistic savings for the user
    :param net_income:
    :param expenses:
    :return:
    """
