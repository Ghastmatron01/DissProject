import tabulate
from Environment.Mortgages.mortgage_products import MORTGAGE_PRODUCTS


class MortgageProduct:
    """
    Represents a single mortgage product loaded from the MORTGAGE_PRODUCTS
    data file. Holds rates, fees, and deposit requirements for one product.
    """

    def __init__(self, product_id):
        """
        Load a mortgage product's details from the data file by its ID.

        :param product_id: Key in MORTGAGE_PRODUCTS (e.g. "FIXED_2_5.2").
        """
        data = MORTGAGE_PRODUCTS[product_id]  # Look up the product once

        self.product_id = product_id
        self.name = data["name"]
        self.bank = data["bank"]
        self.rate = data["rate"]
        self.term = data["term"]
        self.min_deposit = data["min_deposit"]
        self.min_deposit_percent = data["min_deposit"]
        self.max_ltv = data["max_ltv"]
        self.arrangement_fee = data["arrangement_fee"]
        self.valuation_fee = data["valuation_fee"]
        self.early_repay_charge = data["early_repay_charge"]
        self.type = data["type"]

    def get_details(self):
        """
        Format all product details into a readable table.

        :return: Formatted string table of the product's key fields.
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
        Convert the annual interest rate to a monthly decimal rate.

        :return: Monthly interest rate (e.g. 0.004375 for 5.25% annual).
        """
        return self.rate / 12 / 100

    def can_borrow(self, property_price, deposit):
        """
        Check whether a borrower's deposit meets this product's requirements.

        :param property_price: Total property price.
        :param deposit: Deposit amount available.
        :return: Tuple of (can_borrow, max_loan, required_deposit).
        """
        # Minimum deposit required for this product
        required_deposit = property_price * self.min_deposit_percent

        # Maximum loan this product allows based on LTV limit
        max_loan = property_price * self.max_ltv

        # Actual loan amount if the full deposit is used
        actual_loan = property_price - deposit

        # Both conditions must be met: enough deposit AND loan within LTV
        can_borrow = (deposit >= required_deposit) and (actual_loan <= max_loan)

        return can_borrow, max_loan, required_deposit

    def is_fixed(self):
        """
        Check if this product is fixed-rate (as opposed to variable).

        :return: True if fixed, False if variable.
        """
        return self.type.lower() == "fixed"

    def __repr__(self):
        """Return a readable summary for debugging and printing."""
        return f"{self.bank} - {self.name} @ {self.rate}%"
