# File to calculate the net income of the user after base salary has been entered
class SalaryCalculator:
    """
    A unified calculator for UK salary deductions:
    - Income Tax
    - Employee National Insurance
    - Employer National Insurance
    - Student Loan Repayments

    The class uses a shared bracket-based calculation engine to avoid
    repeating logic across tax, NI, and other deduction systems.
    """

    def __init__(self, gross_salary, ni_category="A", student_loan_plans=None,
                 pension_mode="auto_enrolement",
                 employee_pension_rate=0.05,
                 employer_pension_rate=0.03,
                 pension_contribution_gross=0,
                 use_qualifying_earnings=True,
                 number_of_children = 0,
                 receive_child_benefit = True,
                 gift_aid=0,
                 salary_sacrifice=0):
        """
        Initialise the calculator with the user's salary and deduction settings.

        :param gross_salary: Annual gross salary (before deductions)
        :param ni_category: National Insurance category letter (A, B, C, etc.)
        :param student_loan_plans: List of student loan plans (e.g. ["plan_2", "pgl"])
        """
        self.gross_salary = gross_salary
        self.weekly_salary = gross_salary / 52  # NI and student loans use weekly thresholds
        self.ni_category = ni_category
        self.student_loan_plans = student_loan_plans or []

        # Load all bracket systems (you will plug your dictionaries in here)
        self.tax_brackets = TAX_BRACKETS_2026 = [
        {"name": "personal_allowance", "upper": 12570, "rate": 0},
        {"name": "basic_rate", "upper": 50270, "rate": 0.2},
        {"name": "higher_rate", "upper": 125140, "rate": 0.4},
        {"name": "additional_rate", "upper": None, "rate": 0.45}
    ]
        self.employee_ni_brackets = NI_CATEGORIES = {
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
        self.employer_ni_brackets = EMPLOYER_NI_CATEGORIES = {
    "A": [
        {"name": "lel_to_st", "upper": 481, "rate": 0.15},
        {"name": "st_to_ust", "upper": 967, "rate": 0.15},
        {"name": "above_ust", "upper": None, "rate": 0.15}
    ],
    "B": [
        {"name": "lel_to_st", "upper": 481, "rate": 0.15},
        {"name": "st_to_ust", "upper": 967, "rate": 0.15},
        {"name": "above_ust", "upper": None, "rate": 0.15}
    ],
    "C": [
        {"name": "lel_to_st", "upper": 481, "rate": 0.15},
        {"name": "st_to_ust", "upper": 967, "rate": 0.15},
        {"name": "above_ust", "upper": None, "rate": 0.15}
    ],
    "D": [
        {"name": "lel_to_st", "upper": 481, "rate": 0.00},
        {"name": "st_to_ust", "upper": 967, "rate": 0.15},
        {"name": "above_ust", "upper": None, "rate": 0.15}
    ],
    "E": [
        {"name": "lel_to_st", "upper": 481, "rate": 0.00},
        {"name": "st_to_ust", "upper": 967, "rate": 0.15},
        {"name": "above_ust", "upper": None, "rate": 0.15}
    ],
    "F": [
        {"name": "lel_to_st", "upper": 481, "rate": 0.00},
        {"name": "st_to_ust", "upper": 967, "rate": 0.15},
        {"name": "above_ust", "upper": None, "rate": 0.15}
    ],
    "H": [
        {"name": "lel_to_st", "upper": 481, "rate": 0.00},
        {"name": "st_to_ust", "upper": 967, "rate": 0.00},
        {"name": "above_ust", "upper": None, "rate": 0.15}
    ],
    "I": [
        {"name": "lel_to_st", "upper": 481, "rate": 0.00},
        {"name": "st_to_ust", "upper": 967, "rate": 0.15},
        {"name": "above_ust", "upper": None, "rate": 0.15}
    ],
    "J": [
        {"name": "lel_to_st", "upper": 481, "rate": 0.15},
        {"name": "st_to_ust", "upper": 967, "rate": 0.15},
        {"name": "above_ust", "upper": None, "rate": 0.15}
    ],
    "K": [
        {"name": "lel_to_st", "upper": 481, "rate": 0.00},
        {"name": "st_to_ust", "upper": 967, "rate": 0.15},
        {"name": "above_ust", "upper": None, "rate": 0.15}
    ],
    "L": [
        {"name": "lel_to_st", "upper": 481, "rate": 0.00},
        {"name": "st_to_ust", "upper": 967, "rate": 0.15},
        {"name": "above_ust", "upper": None, "rate": 0.15}
    ],
    "M": [
        {"name": "lel_to_st", "upper": 481, "rate": 0.00},
        {"name": "st_to_ust", "upper": 967, "rate": 0.00},
        {"name": "above_ust", "upper": None, "rate": 0.15}
    ],
    "N": [
        {"name": "lel_to_st", "upper": 481, "rate": 0.00},
        {"name": "st_to_ust", "upper": 967, "rate": 0.15},
        {"name": "above_ust", "upper": None, "rate": 0.15}
    ],
    "S": [
        {"name": "lel_to_st", "upper": 481, "rate": 0.00},
        {"name": "st_to_ust", "upper": 967, "rate": 0.15},
        {"name": "above_ust", "upper": None, "rate": 0.15}
    ],
    "V": [
        {"name": "lel_to_st", "upper": 481, "rate": 0.00},
        {"name": "st_to_ust", "upper": 967, "rate": 0.00},
        {"name": "above_ust", "upper": None, "rate": 0.15}
    ],
    "Z": [
        {"name": "lel_to_st", "upper": 481, "rate": 0.00},
        {"name": "st_to_ust", "upper": 967, "rate": 0.00},
        {"name": "above_ust", "upper": None, "rate": 0.15}
    ]
}
        self.student_loan_data =   STUDENT_LOAN_PLANS = {
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

        # Pension settings
        self.employee_pension_rate = employee_pension_rate
        self.employer_pension_rate = employer_pension_rate
        self.use_qualifying_earnings = use_qualifying_earnings

        # Child Benefit Settings
        self.number_of_children = number_of_children
        self.receive_child_benefit = receive_child_benefit
        self.pension_contributions_gross = pension_contribution_gross

        # ANI Deductions
        self.gift_aid = gift_aid
        self.salary_sacrifice = salary_sacrifice

    # ----------------------------------------------------------------------
    #  SHARED BRACKET CALCULATION ENGINE
    # ----------------------------------------------------------------------
    def _calculate_bracketed(self, income, brackets):
        """
        Generic bracket-based deduction calculator.
        This method is used for:
        - Income Tax
        - Employee NI
        - Employer NI

        :param income: The income to apply the brackets to (annual or weekly)
        :param brackets: A list of bracket dictionaries with:
                         { "name": str, "upper": int or None, "rate": float }
        :return: A breakdown dict of how much was charged in each bracket.
        """
        breakdown = {b["name"]: 0 for b in brackets}
        remaining = income

        for i, b in enumerate(brackets):
            upper = b["upper"]
            rate = b["rate"]

            # Determine the lower bound of this bracket
            lower = brackets[i - 1]["upper"] if i > 0 else 0

            # If this is the last bracket (upper=None), everything remaining is taxable
            if upper is None:
                taxable = remaining
            else:
                # Width of this bracket
                width = upper - lower
                # Amount of income that fits into this bracket
                taxable = max(0, min(remaining, width))

            # Apply the rate to the taxable portion
            breakdown[b["name"]] += taxable * rate

            # Reduce remaining income
            remaining -= taxable

            # Stop early if no income left
            if remaining <= 0:
                break

        return breakdown

    # ----------------------------------------------------------------------
    #  TAX CALCULATION
    # ----------------------------------------------------------------------
    def calculate_tax(self):
        """
        Calculate income tax using the shared bracket engine.
        Uses annual salary and tax brackets.
        """
        allowance = self.calculate_personal_allowance()

        # Clone the brackets so we don’t mutate the original
        brackets = [b.copy() for b in self.tax_brackets]

        # Update the personal allowance bracket
        brackets[0]["upper"] = allowance

        return self._calculate_bracketed(self.gross_salary, brackets)

    # ----------------------------------------------------------------------
    #  EMPLOYEE NATIONAL INSURANCE
    # ----------------------------------------------------------------------
    def calculate_employee_ni(self):
        """
        Calculate employee NI contributions.
        Uses weekly salary and NI category brackets.
        """
        brackets = self.employee_ni_brackets[self.ni_category]
        return self._calculate_bracketed(self.weekly_salary, brackets)

    # ----------------------------------------------------------------------
    #  EMPLOYER NATIONAL INSURANCE
    # ----------------------------------------------------------------------
    def calculate_employer_ni(self):
        """
        Calculate employer NI contributions.
        Uses weekly salary and NI category brackets.
        """
        brackets = self.employer_ni_brackets[self.ni_category]
        return self._calculate_bracketed(self.weekly_salary, brackets)

    # ----------------------------------------------------------------------
    #  STUDENT LOAN REPAYMENTS
    # ----------------------------------------------------------------------
    def calculate_student_loan(self):
        """
        Calculate student loan repayments for all applicable plans.
        Student loans do NOT use brackets — they use a threshold + rate.
        """
        breakdown = {}
        total = 0

        for plan in self.student_loan_plans:
            data = self.student_loan_data[plan]
            threshold = data["threshold"]
            rate = data["rate"]

            # Only repay on income above the threshold
            if self.weekly_salary > threshold:
                repay = (self.weekly_salary - threshold) * rate
            else:
                repay = 0

            breakdown[plan] = repay
            total += repay

        return {"total": total, "breakdown": breakdown}

    # ----------------------------------------------------------------------
    # PENSION CALCULATIONS
    # ----------------------------------------------------------------------
    def _get_qualifying_earnings(self):
        lower = 6240
        upper = 50270
        # check if the user is contributing to a pension
        if not self.use_qualifying_earnings:
            return self.gross_salary

        return max(0, min(self.gross_salary, upper) - lower)

    # calculate how much the employee pays
    def calculate_employee_pension(self):
        qualifying = self._get_qualifying_earnings()
        return qualifying * self.employee_pension_rate

    # calculate how much the employer pays
    def calculate_employer_pension(self):
        qualifying = self._get_qualifying_earnings()
        return qualifying * self.employer_pension_rate

    # ----------------------------------------------------------------------
    #  CHILD BENEFITS
    # ----------------------------------------------------------------------

    def _calculate_child_benefit_amount(self):
        if not self.receive_child_benefit or self.number_of_children == 0:
            return 0

        first_child = 26.05 * 52
        additional = 17.25 * 52

        if self.number_of_children == 1:
            return first_child
        else:
            return first_child + (self.number_of_children - 1) * additional

    def calculate_child_benefit_charge(self):
        """
        Calculates the High Income Child Benefit Charge (HICBC)
        using Adjusted Net Income (ANI).
        """
        benefit = self._calculate_child_benefit_amount()

        if benefit == 0:
            return {"charge": 0, "percentage": 0}

        # Use ANI instead of gross salary
        adjusted_income = self.calculate_adjusted_net_income()

        if adjusted_income <= 60000:
            return {"charge": 0, "percentage": 0}

        excess = adjusted_income - 60000

        # 1% charge per £200 over threshold
        percentage = min(100, (excess // 200))

        charge = benefit * (percentage / 100)

        return {
            "charge": charge,
            "percentage": percentage
        }

    # ----------------------------------------------------------------------
    #  ANI CALCULATIONS
    # ----------------------------------------------------------------------
    def calculate_adjusted_net_income(self):
        """
        Adjusted Net Income (ANI) is used for:
        - Child Benefit Tax
        - Personal Allowance tapering
        - Marriage Allowance eligibility

        ANI = taxable income - allowable deductions
        """
        taxable_income = self.gross_salary - self.salary_sacrifice

        deductions = (
                self.pension_contributions_gross +
                self.gift_aid
        )

        return taxable_income - deductions

    # ----------------------------------------------------------------------
    #  PERSONAL ALLOWANCE TAPERING
    # ----------------------------------------------------------------------

    def calculate_personal_allowance(self):
        """
        Personal Allowance reduces by £1 for every £2 of ANI above £100,000.
        It reaches zero at £125,140.
        """
        base_allowance = 12570
        ani = self.calculate_adjusted_net_income()

        if ani <= 100000:
            return base_allowance

        reduction = (ani - 100000) / 2
        allowance = max(0, base_allowance - reduction)

        return allowance


    # ----------------------------------------------------------------------
    #  FULL BREAKDOWN
    # ----------------------------------------------------------------------
    def calculate_total_employee_deductions(self):
        """
        Sums all deductions that reduce the employee's take-home pay.
        Employer NI and employer pension are excluded.
        """
        tax = sum(self.calculate_tax().values())
        employee_ni = sum(self.calculate_employee_ni().values())
        student_loan = self.calculate_student_loan()["total"]
        employee_pension = self.calculate_employee_pension()
        child_benefit_charge = self.calculate_child_benefit_charge()["charge"]

        # Salary sacrifice reduces gross salary BEFORE tax/NI,
        # so it must also be counted as a deduction.
        salary_sacrifice = self.salary_sacrifice

        return {
            "tax": tax,
            "employee_ni": employee_ni,
            "student_loan": student_loan,
            "employee_pension": employee_pension,
            "child_benefit_charge": child_benefit_charge,
            "salary_sacrifice": salary_sacrifice,
            "total": (
                    tax +
                    employee_ni +
                    student_loan +
                    employee_pension +
                    child_benefit_charge +
                    salary_sacrifice
            )
        }

    def calculate_net_pay(self):
        """
        Calculates the employee's take-home pay after all deductions.
        """
        deductions = self.calculate_total_employee_deductions()
        net = self.gross_salary - deductions["total"]

        return {
            "net_pay": net,
            "deductions": deductions
        }

    def calculate_all(self):
        """
        Calculate all deductions and return a full structured breakdown.
        """
        return {
            "adjusted_net_income": self.calculate_adjusted_net_income(),
            "tax": self.calculate_tax(),
            "employee_ni": self.calculate_employee_ni(),
            "employer_ni": self.calculate_employer_ni(),
            "student_loan": self.calculate_student_loan(),
            "employee_pension": self.calculate_employee_pension(),
            "employer_pension": self.calculate_employer_pension(),
            "child_benefit_charge": self.calculate_child_benefit_charge(),
            "net_pay": self.calculate_net_pay()
        }