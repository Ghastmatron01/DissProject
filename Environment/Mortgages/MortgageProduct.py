import tabulate
from Environment.Mortgages.mortgage_products import MORTGAGE_PRODUCTS


class MortgageProduct:
    """
    Class that represents a mortgage product and the rates of that product
    """
    def __init__ (self, product_id):
        self.product_id = product_id
        self.name = MORTGAGE_PRODUCTS[product_id]["name"]
        self.bank = MORTGAGE_PRODUCTS[product_id]["bank"]
        self.rate = MORTGAGE_PRODUCTS[product_id]["rate"]
        self.term = MORTGAGE_PRODUCTS[product_id]["term"]
        self.min_deposit = MORTGAGE_PRODUCTS[product_id]["min_deposit"]
        self.min_deposit_percent = MORTGAGE_PRODUCTS[product_id]["min_deposit"]
        self.max_ltv = MORTGAGE_PRODUCTS[product_id]["max_ltv"]
        self.arrangement_fee = MORTGAGE_PRODUCTS[product_id]["arrangement_fee"]
        self.valuation_fee = MORTGAGE_PRODUCTS[product_id]["valuation_fee"]
        self.early_repay_charge = MORTGAGE_PRODUCTS[product_id]["early_repay_charge"]
        self.type = MORTGAGE_PRODUCTS[product_id]["type"]

    def get_details(self):
        """
        What are the details of the product
        :return: The details of the product in a nice table using tabulate
        """
        details = [
            ["Product ID", self.product_id],
            ["Name", self.name],
            ["Bank", self.bank],
            ["Rate (%)", self.rate],
            ["Term (years)", self.term if self.term is not None else "Variable"],
            ["Min Deposit (%)", self.min_deposit_percent * 100],
            ["Max LTV (%)", self.max_ltv * 100],
            ["Arrangement Fee (£)", self.arrangement_fee],
            ["Valuation Fee (£)", self.valuation_fee],
            ["Early Repayment Charge (£)", self.early_repay_charge]
        ]
        return tabulate.tabulate(details, tablefmt="grid")

    def monthly_rate(self):
        """
        Get the monthly interest rate as a decimal
        :return: Monthly interest rate (e.g., 0.004375 for 5.25% annual)
        """
        return self.rate / 12 / 100

    def can_borrow(self, property_price, deposit):
        """
        Can the user borrow this amount based on the property price and deposit?

        :param property_price: Total property price
        :param deposit: Deposit amount available
        :return: (can_borrow: bool, max_loan: float, required_deposit: float)
        """
        # Required deposit for this product
        required_deposit = property_price * self.min_deposit_percent

        # Maximum can borrow based on this product's LTV limit
        max_loan = property_price * self.max_ltv

        # Actual loan if deposit is used
        actual_loan = property_price - deposit

        # Can borrow if both conditions met:
        # 1. Deposit >= required AND
        # 2. Loan <= max LTV
        can_borrow = (deposit >= required_deposit) and (actual_loan <= max_loan)

        return can_borrow, max_loan, required_deposit

    def is_fixed(self):
        """
        Check if the product is fixed-rate (vs variable).

        :return: True if fixed, False if variable
        """
        return self.type.lower() == "fixed"


    def __repr__(self):
        """String representation for debugging/printing."""
        return f"{self.bank} - {self.name} @ {self.rate}%"













