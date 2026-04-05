class MortgageCalculator:
    """
    Calculates mortgage payments, affordability, and generates amortisation schedules.
    """

    def __init__(self, mortgage_product, property_price, deposit_amount, term_years=None):
        """
        Initialize calculator with mortgage details.

        :param mortgage_product: MortgageProduct object (has rate, min_deposit, max_ltv)
        :param property_price: Total property price
        :param deposit_amount: Deposit paid upfront
        :param term_years: Loan term (defaults to product term if not specified)
        """
        self.product = mortgage_product
        self.property_price = property_price
        self.deposit_amount = deposit_amount
        self.principal = property_price - deposit_amount  # Amount to borrow
        self.term_years = term_years or mortgage_product.term


    def calculate_monthly_payment(self):
        """
        Calculate monthly mortgage payment using standard formula:
        M = P × [r(1+r)^n] / [(1+r)^n - 1]

        Where:
        - P = Principal (loan amount)
        - r = Monthly interest rate (annual rate / 12 / 100)
        - n = Number of monthly payments (years × 12)

        :return: Monthly payment amount
        """
        # Convert annual rate to monthly decimal
        annual_rate = self.product.rate
        r = annual_rate / 12 / 100  # Convert to monthly decimal

        # Calculate number of months
        n = self.term_years * 12

        # Handle edge case: 0% interest
        if r == 0:
            return self.principal / n

        # Apply formula
        numerator = r * (1 + r) ** n
        denominator = (1 + r) ** n - 1

        monthly_payment = self.principal * (numerator / denominator)
        return monthly_payment


    def calculate_total_cost(self):
        """
        Calculate total cost (principal + interest).

        :return: Total amount paid back to bank
        """
        monthly_payment = self.calculate_monthly_payment()
        total_months = self.term_years * 12
        return monthly_payment * total_months


    def calculate_total_interest(self):
        """
        Calculate total interest paid over life of mortgage.

        :return: Total interest
        """
        return self.calculate_total_cost() - self.principal


    def check_lending_criteria(self, annual_gross_income, existing_monthly_debts=0):
        """
        Check if borrower meets bank's lending criteria.

        Criteria checked:
        - Deposit meets minimum requirement
        - LTV (Loan-to-Value) within limits
        - Income multiple (can borrow 4.5× annual salary)
        - Affordability (mortgage ≤ 50% of net income)

        :param annual_gross_income: Annual gross salary (before tax)
        :param existing_monthly_debts: Current monthly debt payments (credit cards, etc.)
        :return: (approved: bool, reason: str, affordable_monthly: float)
        """
        reasons = []

        # Deposit Check
        min_deposit_percent = self.product.min_deposit_percent
        actual_deposit_percent = self.deposit_amount / self.property_price

        if actual_deposit_percent < min_deposit_percent: # tells the user if they dont have enough deposit
            reasons.append(
                f"Insufficient deposit: {actual_deposit_percent*100:.1f}% "
                f"(minimum required: {min_deposit_percent*100:.0f}%)"
            )

        # LTV Check
        max_ltv = self.product.max_ltv
        actual_ltv = self.principal / self.property_price

        if actual_ltv > max_ltv:
            reasons.append(
                f"LTV too high: {actual_ltv*100:.1f}% (maximum allowed: {max_ltv*100:.0f}%)"
            )

        # Income Multiple Check
        # Standard UK lending: Can borrow up to 4.5× annual salary
        income_multiple_limit = 4.5
        max_borrow_by_income = annual_gross_income * income_multiple_limit

        if self.principal > max_borrow_by_income:
            reasons.append(
                f"Loan amount too high for income: Borrowing £{self.principal:,.0f} "
                f"(maximum allowed for £{annual_gross_income:,.0f} salary: £{max_borrow_by_income:,.0f})"
            )

        # Affordability Check
        # Estimate net monthly income, parameter from financial class
        net_monthly_income = (annual_gross_income / 12)

        # Calculate proposed mortgage payment
        monthly_mortgage = self.calculate_monthly_payment()

        # Total monthly debt obligations
        total_monthly_debt = monthly_mortgage + existing_monthly_debts

        # Standard rule: Total debt shouldn't exceed 50% of net income
        affordability_ratio = total_monthly_debt / net_monthly_income

        if affordability_ratio > 0.50:
            reasons.append(
                f"Affordability concern: Monthly payments (£{total_monthly_debt:.2f}) "
                f"exceed 50% of net income (50% = £{net_monthly_income*0.50:.2f})"
            )

        # Final decision
        if reasons:
            return False, " | ".join(reasons), 0
        else:
            # Calculate how much disposable income remains
            available_after_debt = net_monthly_income - total_monthly_debt
            return True, "Approved", available_after_debt


    def calculate_affordability(self, net_monthly_income, existing_debts, monthly_expenses, mortgage_payment):
        """
        Calculate disposable income after all payments.

        :param net_monthly_income: Monthly income after tax/NI
        :param existing_debts: Existing debt payments (credit cards, etc.)
        :param monthly_expenses: Regular monthly expenses (bills, food, etc.)
        :param mortgage_payment: Proposed mortgage payment
        :return: Disposable income remaining
        """
        total_outgoings = existing_debts + monthly_expenses + mortgage_payment
        return net_monthly_income - total_outgoings


    def generate_amortisation_schedule(self):
        """
        Generate month-by-month breakdown of mortgage payments.

        Shows how much of each payment goes to interest vs principal.

        :return: List of dictionaries with monthly breakdown
        """
        schedule = []

        balance = self.principal
        monthly_rate = self.product.rate / 12 / 100
        monthly_payment = self.calculate_monthly_payment()

        for month in range(1, (self.term_years * 12) + 1):
            # Calculate interest for this month
            interest = balance * monthly_rate

            # Principal is payment minus interest
            principal_paid = monthly_payment - interest

            # Reduce balance
            balance -= principal_paid
            balance = max(0, balance)  # Ensure no negative balance

            schedule.append({
                "month": month,
                "payment": monthly_payment,
                "principal": principal_paid,
                "interest": interest,
                "remaining_balance": balance
            })

        return schedule


    def total_cost_summary(self):
        """
        Return comprehensive cost summary.

        :return: Dictionary with all financial details
        """
        monthly_payment = self.calculate_monthly_payment()

        return {
            "property_price": self.property_price,
            "deposit": self.deposit_amount,
            "deposit_percent": (self.deposit_amount / self.property_price) * 100,
            "loan_amount": self.principal,
            "interest_rate": self.product.rate,
            "term_years": self.term_years,
            "term_months": self.term_years * 12,
            "monthly_payment": monthly_payment,
            "arrangement_fee": self.product.arrangement_fee,
            "total_interest": self.calculate_total_interest(),
            "total_repaid": self.calculate_total_cost(),
            "total_cost_to_buyer": (
                self.deposit_amount +
                self.calculate_total_cost() +
                self.product.arrangement_fee
            )
        }

