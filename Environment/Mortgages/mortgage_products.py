MORTGAGE_PRODUCTS = {
    # ----- NATIONWIDE -----
    "FIXED_2_5.2": {
        "product_id": "FIXED_2_5.2",
        "name": "2-Year Fixed",
        "bank": "Nationwide",
        "type": "fixed",
        "rate": 5.2,
        "term": 2,
        "min_deposit": 0.15,
        "max_ltv": 0.85,
        "arrangement_fee": 995,
        "valuation_fee": 0,
        "early_repay_charge": 0
    },
    "FIXED_5_5.5": {
        "product_id": "FIXED_5_5.5",
        "name": "5-Year Fixed",
        "bank": "Nationwide",
        "type": "fixed",
        "rate": 5.5,
        "term": 5,
        "min_deposit": 0.15,
        "max_ltv": 0.85,
        "arrangement_fee": 995,
        "valuation_fee": 0,
        "early_repay_charge": 0
    },
    "VAR_6.1": {
        "product_id": "VAR_6.1",
        "name": "Standard Variable Rate",
        "bank": "Nationwide",
        "type": "variable",
        "rate": 6.1,
        "term": None,
        "min_deposit": 0.20,
        "max_ltv": 0.80,
        "arrangement_fee": 500,
        "valuation_fee": 150,
        "early_repay_charge": 0
    },

    # ----- HSBC -----
    "FIXED_2_5.4": {
        "product_id": "FIXED_2_5.4",
        "name": "2-Year Fixed",
        "bank": "HSBC",
        "type": "fixed",
        "rate": 5.4,
        "term": 2,
        "min_deposit": 0.20,
        "max_ltv": 0.80,
        "arrangement_fee": 1495,
        "valuation_fee": 295,
        "early_repay_charge": 0
    },
    "FIXED_5_5.6": {
        "product_id": "FIXED_5_5.6",
        "name": "5-Year Fixed",
        "bank": "HSBC",
        "type": "fixed",
        "rate": 5.6,
        "term": 5,
        "min_deposit": 0.20,
        "max_ltv": 0.80,
        "arrangement_fee": 1495,
        "valuation_fee": 295,
        "early_repay_charge": 0
    },
    "VAR_6.2": {
        "product_id": "VAR_6.2",
        "name": "Standard Variable Rate",
        "bank": "HSBC",
        "type": "variable",
        "rate": 6.2,
        "term": None,
        "min_deposit": 0.25,
        "max_ltv": 0.75,
        "arrangement_fee": 995,
        "valuation_fee": 295,
        "early_repay_charge": 0
    },

    # ----- BARCLAYS -----
    "FIXED_2_5.3": {
        "product_id": "FIXED_2_5.3",
        "name": "2-Year Fixed",
        "bank": "Barclays",
        "type": "fixed",
        "rate": 5.3,
        "term": 2,
        "min_deposit": 0.15,
        "max_ltv": 0.85,
        "arrangement_fee": 595,
        "valuation_fee": 0,
        "early_repay_charge": 0
    },
    "FIXED_5_5.7": {
        "product_id": "FIXED_5_5.7",
        "name": "5-Year Fixed",
        "bank": "Barclays",
        "type": "fixed",
        "rate": 5.7,
        "term": 5,
        "min_deposit": 0.15,
        "max_ltv": 0.85,
        "arrangement_fee": 595,
        "valuation_fee": 0,
        "early_repay_charge": 0
    },
    "VAR_6.0": {
        "product_id": "VAR_6.0",
        "name": "Standard Variable Rate",
        "bank": "Barclays",
        "type": "variable",
        "rate": 6.0,
        "term": None,
        "min_deposit": 0.20,
        "max_ltv": 0.80,
        "arrangement_fee": 495,
        "valuation_fee": 200,
        "early_repay_charge": 0
    },

    # ----- LLOYDS -----
    "FIXED_2_5.25": {
        "product_id": "FIXED_2_5.25",
        "name": "2-Year Fixed",
        "bank": "Lloyds",
        "type": "fixed",
        "rate": 5.25,
        "term": 2,
        "min_deposit": 0.15,
        "max_ltv": 0.85,
        "arrangement_fee": 999,
        "valuation_fee": 0,
        "early_repay_charge": 0
    },
    "FIXED_5_5.55": {
        "product_id": "FIXED_5_5.55",
        "name": "5-Year Fixed",
        "bank": "Lloyds",
        "type": "fixed",
        "rate": 5.55,
        "term": 5,
        "min_deposit": 0.15,
        "max_ltv": 0.85,
        "arrangement_fee": 999,
        "valuation_fee": 0,
        "early_repay_charge": 0
    },
    "VAR_6.05": {
        "product_id": "VAR_6.05",
        "name": "Standard Variable Rate",
        "bank": "Lloyds",
        "type": "variable",
        "rate": 6.05,
        "term": None,
        "min_deposit": 0.20,
        "max_ltv": 0.80,
        "arrangement_fee": 500,
        "valuation_fee": 150,
        "early_repay_charge": 0
    }
}


def get_product(product_id):
    """
    Get a mortgage product by ID.

    :param product_id: Product ID (e.g., "FIXED_2_5.2")
    :return: Product dictionary
    :raises ValueError: If product not found
    """
    if product_id not in MORTGAGE_PRODUCTS:
        raise ValueError(f"Product {product_id} not found")
    return MORTGAGE_PRODUCTS[product_id]


def get_bank_products(bank_name):
    """
    Get all products for a specific bank.

    :param bank_name: Bank name (e.g., "Nationwide")
    :return: Dictionary of products for that bank
    """
    return {pid: p for pid, p in MORTGAGE_PRODUCTS.items()
            if p["bank"].lower() == bank_name.lower()}

