"""
synthetic_agents.py - Generates realistic stand-in agent data to compute
housing metrics including median first-time buyer age, deposit percentages,
and mortgage rates.

Agents experience:
    - UK income tax and National Insurance deductions
    - Monthly rent costs while saving for a deposit
    - Student loan repayments (Plan 2) for graduates
    - Random life events: relationships, marriage, children, promotion,
      job loss, divorce, bereavement, inheritance, unexpected debt
    - Household income combining when partnered (two salaries)
    - Bedroom requirements growing with family size
    - Property price scaling with bedroom needs
    - Fault repair costs once a homeowner (based on EHS probabilities)
    - Monthly mortgage payments once purchased
"""

import random
import pandas as pd
import os

random.seed(42)

# -----------------------------------------------------------------
# Agent profile definitions
# -----------------------------------------------------------------

# Each profile:
# (name, start_age, start_salary, start_savings, savings_rate,
#  monthly_expenses, background, target_deposit_pct,
#  has_student_loan, start_partnered, start_children)

AGENT_PROFILES = [

    # --- Recent university graduates ---
    ("Emma",      21, 23000, 1500,  0.25, 900,  "graduate",   0.10, True,  False, 0),
    ("Liam",      22, 25000, 2000,  0.20, 950,  "graduate",   0.10, True,  False, 0),
    ("Sophie",    21, 22000, 800,   0.20, 880,  "graduate",   0.10, True,  True,  0),
    ("Noah",      23, 27000, 3000,  0.30, 1000, "graduate",   0.15, True,  False, 0),
    ("Chloe",     22, 24000, 500,   0.15, 920,  "graduate",   0.10, True,  False, 0),
    ("Oliver",    21, 21000, 0,     0.15, 870,  "graduate",   0.10, True,  False, 0),
    ("Isabelle",  23, 26000, 1000,  0.20, 940,  "graduate",   0.15, True,  True,  0),
    ("Harry",     22, 28000, 2500,  0.25, 1000, "graduate",   0.15, True,  False, 0),
    ("Mia",       21, 20000, 200,   0.10, 850,  "graduate",   0.10, True,  False, 0),
    ("Jack",      23, 30000, 4000,  0.30, 1050, "graduate",   0.20, True,  True,  0),

    # --- Apprentices / vocational starters ---
    ("Tyler",     18, 14000, 0,     0.10, 600,  "apprentice", 0.10, False, False, 0),
    ("Jade",      19, 15500, 500,   0.15, 650,  "apprentice", 0.10, False, False, 0),
    ("Ryan",      20, 17000, 1000,  0.20, 700,  "apprentice", 0.10, False, True,  0),
    ("Lauren",    18, 13500, 0,     0.10, 580,  "apprentice", 0.10, False, False, 0),
    ("Connor",    19, 16000, 800,   0.15, 670,  "apprentice", 0.10, False, False, 0),
    ("Amy",       20, 18000, 1200,  0.20, 720,  "apprentice", 0.10, False, False, 0),

    # --- Mid-career starters ---
    ("James",     24, 32000, 5000,  0.30, 1100, "mid_career", 0.15, False, True,  0),
    ("Charlotte", 25, 35000, 8000,  0.35, 1150, "mid_career", 0.20, False, True,  1),
    ("Daniel",    26, 38000, 10000, 0.35, 1200, "mid_career", 0.20, False, False, 0),
    ("Grace",     27, 40000, 12000, 0.30, 1250, "mid_career", 0.20, False, True,  0),
    ("Ben",       28, 42000, 15000, 0.30, 1300, "mid_career", 0.20, False, True,  1),
    ("Ella",      25, 34000, 6000,  0.25, 1100, "mid_career", 0.15, False, False, 0),
    ("Tom",       26, 36000, 9000,  0.30, 1180, "mid_career", 0.20, False, True,  0),
    ("Hannah",    24, 31000, 4500,  0.25, 1080, "mid_career", 0.15, False, False, 0),

    # --- Tech graduates / high earners ---
    ("Marcus",    22, 40000, 3000,  0.35, 1200, "tech_grad",  0.20, True,  False, 0),
    ("Priya",     23, 42000, 5000,  0.35, 1250, "tech_grad",  0.20, True,  False, 0),
    ("Jake",      22, 38000, 2000,  0.30, 1150, "tech_grad",  0.15, True,  True,  0),
    ("Aisha",     24, 45000, 7000,  0.40, 1300, "tech_grad",  0.20, True,  False, 0),
    ("Sam",       23, 43000, 4000,  0.35, 1220, "tech_grad",  0.20, True,  True,  0),

    # --- Struggling / high cost of living ---
    ("Lucy",      22, 22000, 0,     0.08, 1050, "high_cost",  0.10, True,  False, 0),
    ("Dan",       23, 24000, 500,   0.08, 1100, "high_cost",  0.10, False, False, 0),
    ("Katie",     21, 21000, 0,     0.05, 1000, "high_cost",  0.10, True,  False, 0),

    # --- Older / later buyers (35–52) ---
    # Long-term renters who saved slowly
    ("Margaret",  42, 38000, 18000, 0.25, 1300, "older_renter",   0.15, False, False, 0),
    ("Derek",     38, 34000, 12000, 0.20, 1200, "older_renter",   0.10, False, False, 0),
    ("Yvonne",    45, 41000, 22000, 0.30, 1350, "older_renter",   0.20, False, True,  1),
    ("Clive",     50, 44000, 30000, 0.35, 1400, "older_renter",   0.20, False, False, 0),

    # Divorcees re-entering the market
    ("Sandra",    40, 36000, 15000, 0.25, 1250, "divorcee",       0.15, False, False, 1),
    ("Martin",    44, 48000, 20000, 0.30, 1400, "divorcee",       0.20, False, False, 0),
    ("Deborah",   37, 32000, 8000,  0.20, 1180, "divorcee",       0.10, False, False, 2),

    # Mid-life career changers / higher earners who prioritised renting
    ("Richard",   35, 55000, 25000, 0.35, 1500, "late_high_earner", 0.20, False, True,  0),
    ("Natasha",   36, 52000, 20000, 0.30, 1450, "late_high_earner", 0.20, True,  True,  1),
    ("Graham",    48, 60000, 35000, 0.40, 1600, "late_high_earner", 0.25, False, True,  0),

    # Older workers on modest incomes who kept missing the ladder
    ("Pauline",   52, 28000, 10000, 0.15, 1050, "older_modest",   0.10, False, False, 0),
    ("Keith",     46, 30000, 8000,  0.12, 1100, "older_modest",   0.10, False, False, 0),
]

# -----------------------------------------------------------------
# Constants
# -----------------------------------------------------------------

SALARY_GROWTH_MEAN    = 0.025
SALARY_GROWTH_STD     = 0.005
EXPENSE_INFLATION     = 0.03
SIM_START_YEAR        = 2025
SIM_MAX_YEARS         = 35
PARTNER_SALARY_RATIO  = 0.85
MONTHLY_RENT          = {1: 850, 2: 1100, 3: 1350, 4: 1600}
CHILD_MONTHLY_COST    = 600
STUDENT_LOAN_THRESHOLD= 27295
STUDENT_LOAN_RATE     = 0.09

# Annual house price inflation (UK long-run average ~5%)
HOUSE_PRICE_INFLATION = 0.05

# Pension auto-enrolment: employee contributes 5% of earnings above £10,000
PENSION_THRESHOLD     = 10000
PENSION_RATE          = 0.05

# Purchase transaction costs added on top of deposit
SURVEY_LEGAL_COSTS    = 2500   # conveyancing + survey (flat rate approximation)

LIFE_EVENT_PROBS = {
    "get_partner":     0.12,
    "marriage":        0.10,
    "have_child":      0.12,
    "job_promotion":   0.08,
    "job_loss":        0.03,
    "divorce":         0.02,
    "bereavement":     0.02,
    "inheritance":     0.015,
    "unexpected_debt": 0.04,
}

FAULT_PROBS = {
    "damp":             0.0075,
    "excess_cold":      0.0060,
    "disrepair":        0.0065,
    "electrical_fault": 0.0030,
    "boiler_failure":   0.0060,
    "roof_leak":        0.0020,
    "plumbing_issue":   0.0040,
}

FAULT_COSTS = {
    "damp":             (1500, 6000),
    "excess_cold":      (2000, 8000),
    "disrepair":        (1000, 5000),
    "electrical_fault": (500,  3000),
    "boiler_failure":   (2000, 4000),
    "roof_leak":        (1000, 15000),
    "plumbing_issue":   (300,  2000),
}

FAULT_AGE_MULT = {
    "new": 0.3, "recent": 0.7, "mid": 1.0, "old": 1.5, "very_old": 2.0
}

PROPERTY_TYPES = ["flat", "terraced", "semi_detached", "detached"]
PROPERTY_TYPE_FAULT_MULT = {
    "flat": 0.8, "terraced": 1.2, "semi_detached": 1.0, "detached": 1.1
}
PROPERTY_TYPE_AGE_EST = {
    "flat": 25, "terraced": 60, "semi_detached": 50, "detached": 30
}


# -----------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------

def calculate_net_monthly(gross_annual: float) -> float:
    """
    Estimates monthly net pay using simplified UK 2024/25 income tax
    and National Insurance bands.

    :param gross_annual: gross annual salary in pounds
    :return: estimated monthly net pay in pounds
    """
    personal_allowance = 12570
    basic_rate_limit   = 50270
    higher_rate_limit  = 125140
    taxable = max(0, gross_annual - personal_allowance)
    if gross_annual <= basic_rate_limit:
        tax = taxable * 0.20
    elif gross_annual <= higher_rate_limit:
        tax = (basic_rate_limit - personal_allowance) * 0.20
        tax += (gross_annual - basic_rate_limit) * 0.40
    else:
        tax = (basic_rate_limit - personal_allowance) * 0.20
        tax += (higher_rate_limit - basic_rate_limit) * 0.40
        tax += (gross_annual - higher_rate_limit) * 0.45
    if gross_annual <= 12570:
        ni = 0
    elif gross_annual <= 50270:
        ni = (gross_annual - 12570) * 0.08
    else:
        ni = (50270 - 12570) * 0.08
        ni += (gross_annual - 50270) * 0.02
    return round((gross_annual - tax - ni) / 12, 2)


def calculate_student_loan_monthly(gross_annual: float) -> float:
    """
    Calculates monthly student loan repayment under UK Plan 2.

    :param gross_annual: gross annual salary in pounds
    :return: monthly repayment in pounds
    """
    if gross_annual <= STUDENT_LOAN_THRESHOLD:
        return 0.0
    return round(((gross_annual - STUDENT_LOAN_THRESHOLD) * STUDENT_LOAN_RATE) / 12, 2)


def calculate_pension_monthly(gross_annual: float) -> float:
    """
    Calculates monthly auto-enrolment pension contribution (employee side).
    5% of earnings above £10,000 threshold, matching the real simulation.

    :param gross_annual: gross annual salary in pounds
    :return: monthly pension deduction in pounds
    """
    if gross_annual <= PENSION_THRESHOLD:
        return 0.0
    return round(((gross_annual - PENSION_THRESHOLD) * PENSION_RATE) / 12, 2)


def calculate_sdlt(property_price: float, first_time_buyer: bool = True) -> float:
    """
    Calculates Stamp Duty Land Tax (SDLT) on a UK property purchase.

    First-time buyer relief: 0% up to £425,000, 5% on £425,001 to £625,000,
    standard rates above £625,000. Matches the real simulation's SDLT logic.

    :param property_price: purchase price of the property in pounds
    :param first_time_buyer: whether the agent qualifies for FTB relief
    :return: SDLT amount in pounds
    """
    if first_time_buyer and property_price <= 425000:
        return 0.0
    elif first_time_buyer and property_price <= 625000:
        return (property_price - 425000) * 0.05

    # Standard rates (non-FTB or above £625k)
    sdlt = 0.0
    bands = [(250000, 0.0), (925000, 0.05), (1500000, 0.10), (float("inf"), 0.12)]
    prev = 0
    for limit, rate in bands:
        if property_price <= prev:
            break
        taxable = min(property_price, limit) - prev
        sdlt += taxable * rate
        prev = limit
    return round(sdlt, 2)


def get_mortgage_rate(deposit_pct: float) -> float:
    """
    Returns approximate UK fixed-rate mortgage interest rate by LTV band.

    :param deposit_pct: deposit as fraction of property price (e.g. 0.10)
    :return: annual interest rate as decimal
    """
    ltv = 1 - deposit_pct
    if ltv <= 0.60:   return 0.038
    elif ltv <= 0.75: return 0.040
    elif ltv <= 0.80: return 0.042
    elif ltv <= 0.85: return 0.045
    elif ltv <= 0.90: return 0.048
    elif ltv <= 0.95: return 0.055
    else:             return 0.060


def calculate_monthly_mortgage(loan: float, annual_rate: float, term_years: int = 25) -> float:
    """
    Calculates monthly mortgage repayment using amortisation formula.

    :param loan: loan amount in pounds
    :param annual_rate: annual interest rate as decimal
    :param term_years: mortgage term in years
    :return: monthly payment in pounds
    """
    r = annual_rate / 12
    n = term_years * 12
    if r == 0:
        return round(loan / n, 2)
    return round(loan * (r * (1 + r) ** n) / ((1 + r) ** n - 1), 2)


def get_bedrooms_needed(is_partnered: bool, children: int) -> int:
    """
    Returns minimum bedrooms needed based on household composition.

    :param is_partnered: whether agent has a partner living with them
    :param children: number of children
    :return: number of bedrooms needed
    """
    if not is_partnered and children == 0:
        return 1
    elif children == 0:
        return 2
    elif children == 1:
        return 3
    else:
        return min(4, 2 + children)


def get_price_multiplier(bedrooms: int) -> float:
    """
    Returns property price as a salary multiplier based on bedroom count.

    :param bedrooms: number of bedrooms needed
    :return: salary multiplier
    """
    return {1: 3.5, 2: 4.0, 3: 4.5, 4: 5.5}.get(bedrooms, 4.5)


def roll_fault_costs(property_type: str, property_age: int) -> tuple:
    """
    Rolls for property faults this year using EHS-derived probabilities
    adjusted by property age and type.

    :param property_type: type of property (flat, terraced, etc.)
    :param property_age: estimated age of property in years
    :return: tuple of (total_repair_cost, list_of_fault_names)
    """
    if property_age < 10:    age_mult = FAULT_AGE_MULT["new"]
    elif property_age < 30:  age_mult = FAULT_AGE_MULT["recent"]
    elif property_age < 60:  age_mult = FAULT_AGE_MULT["mid"]
    elif property_age < 100: age_mult = FAULT_AGE_MULT["old"]
    else:                    age_mult = FAULT_AGE_MULT["very_old"]

    type_mult  = PROPERTY_TYPE_FAULT_MULT.get(property_type, 1.0)
    total_cost = 0.0
    faults     = []

    for fault, base_prob in FAULT_PROBS.items():
        if random.random() < min(base_prob * age_mult * type_mult, 1.0):
            cost = random.randint(*FAULT_COSTS[fault])
            total_cost += cost
            faults.append(fault)

    return round(total_cost, 0), faults


# -----------------------------------------------------------------
# Main agent simulation
# -----------------------------------------------------------------

def simulate_agent(profile: tuple) -> list:
    """
    Simulates a single agent's financial life year by year until they buy
    a property or the maximum years are reached.

    Includes rent, student loans, life events, fault costs, and mortgages.

    :param profile: tuple of agent attributes from AGENT_PROFILES
    :return: list of yearly result dictionaries
    """
    (name, start_age, start_salary, start_savings, savings_rate,
     monthly_expenses, background, target_deposit_pct,
     has_student_loan, start_partnered, start_children) = profile

    salary       = float(start_salary)
    savings      = float(start_savings)
    expenses     = float(monthly_expenses)
    age          = start_age
    is_partnered = start_partnered
    is_married   = False
    children     = start_children
    loan_balance = 35000.0 if has_student_loan else 0.0
    debt         = 0.0
    rows         = []
    bought       = False
    is_ftb       = True   # first-time buyer flag for SDLT relief

    # Base property market price index - grows with house price inflation each year
    # Starts at 1.0 and compounds annually, making the target harder to reach
    house_price_index = 1.0

    # Set on purchase
    property_type      = None
    property_age       = None
    monthly_mortgage   = None
    mortgage_rate_used = None
    mortgage_balance   = None

    for year_offset in range(SIM_MAX_YEARS):
        sim_year        = SIM_START_YEAR + year_offset
        life_events_log = []

        # -- House price market grows each year (makes deposit target harder) ---
        house_price_index *= (1 + HOUSE_PRICE_INFLATION)

        # -- Salary growth ----------------------------------------
        growth = random.gauss(SALARY_GROWTH_MEAN, SALARY_GROWTH_STD)
        salary = salary * (1 + growth)

        # -- Student loan repayment -------------------------------
        student_loan_monthly = 0.0
        if loan_balance > 0:
            student_loan_monthly = calculate_student_loan_monthly(salary)
            loan_balance = max(0, loan_balance * 1.05 - student_loan_monthly * 12)

        # -- Expense inflation ------------------------------------
        expenses = expenses * (1 + EXPENSE_INFLATION)

        # -- Partner income ---------------------------------------
        partner_net_monthly = 0.0
        partner_pension_monthly = 0.0
        if is_partnered:
            partner_salary = salary * PARTNER_SALARY_RATIO
            partner_net_monthly = calculate_net_monthly(partner_salary)
            partner_pension_monthly = calculate_pension_monthly(partner_salary)

        # -- Life events ------------------------------------------
        if not bought:
            if (not is_partnered and age <= 35
                    and random.random() < LIFE_EVENT_PROBS["get_partner"]):
                is_partnered = True
                partner_salary = salary * PARTNER_SALARY_RATIO
                partner_net_monthly = calculate_net_monthly(partner_salary)
                partner_pension_monthly = calculate_pension_monthly(partner_salary)
                life_events_log.append("new_relationship")

            if (is_partnered and not is_married
                    and random.random() < LIFE_EVENT_PROBS["marriage"]):
                is_married = True
                savings = max(0, savings - random.randint(5000, 20000))
                life_events_log.append("marriage")

            if (is_partnered and age <= 40
                    and random.random() < LIFE_EVENT_PROBS["have_child"]):
                children += 1
                life_events_log.append(f"child_born(total:{children})")

        if (is_married and random.random() < LIFE_EVENT_PROBS["divorce"]):
            is_married   = False
            is_partnered = False
            partner_net_monthly = 0.0
            savings = max(0, savings - random.randint(3000, 15000))
            life_events_log.append("divorce")

        if random.random() < LIFE_EVENT_PROBS["job_promotion"]:
            raise_pct = random.uniform(0.15, 0.25)
            salary *= (1 + raise_pct)
            life_events_log.append(f"promotion(+{raise_pct:.0%})")

        if random.random() < LIFE_EVENT_PROBS["job_loss"]:
            lost = calculate_net_monthly(salary) * 6 * 0.40
            savings = max(0, savings - lost)
            life_events_log.append("job_loss")

        if random.random() < LIFE_EVENT_PROBS["bereavement"]:
            savings = max(0, savings - random.randint(2000, 8000))
            life_events_log.append("bereavement")

        if random.random() < LIFE_EVENT_PROBS["inheritance"]:
            windfall = random.randint(5000, 40000)
            savings += windfall
            life_events_log.append(f"inheritance(+£{windfall:,})")

        if random.random() < LIFE_EVENT_PROBS["unexpected_debt"]:
            new_debt = random.randint(500, 5000)
            debt += new_debt
            life_events_log.append(f"unexpected_debt(+£{new_debt:,})")

        # -- Net income -------------------------------------------
        net_monthly    = calculate_net_monthly(salary)
        pension_monthly= calculate_pension_monthly(salary)
        # Pension deducted from take-home before spending (auto-enrolment)
        net_after_pension = net_monthly - pension_monthly
        partner_after_pension = partner_net_monthly - partner_pension_monthly
        household_net  = net_after_pension + partner_after_pension

        # -- Rent (pre-purchase only) -----------------------------
        rent_monthly = 0.0
        if not bought:
            bedrooms_renting = get_bedrooms_needed(is_partnered, children)
            rent_monthly = MONTHLY_RENT.get(bedrooms_renting, 1100)

        # -- Child costs ------------------------------------------
        child_costs = children * CHILD_MONTHLY_COST

        # -- Debt repayment and interest --------------------------
        debt_repayment_monthly = 0.0
        if debt > 0:
            debt_repayment_monthly = debt * 0.03
            debt = max(0, debt - debt_repayment_monthly * 12)
            debt *= 1.18

        # -- Fault costs (homeowners) -----------------------------
        fault_cost_annual = 0.0
        faults_this_year  = []
        if bought and property_type and property_age is not None:
            fault_cost_annual, faults_this_year = roll_fault_costs(property_type, property_age)
            savings = max(0, savings - fault_cost_annual)
            property_age += 1

        # -- Mortgage payment (homeowners) ------------------------
        if bought and monthly_mortgage and mortgage_balance and mortgage_rate_used:
            interest_paid  = mortgage_balance * mortgage_rate_used
            principal_paid = max(0, monthly_mortgage * 12 - interest_paid)
            mortgage_balance = max(0, mortgage_balance - principal_paid)

        # -- Monthly available cash -------------------------------
        mortgage_monthly_payment = monthly_mortgage if bought else 0.0
        total_outgoings = (
            expenses
            + rent_monthly
            + child_costs
            + student_loan_monthly
            + debt_repayment_monthly
            + (mortgage_monthly_payment or 0)
        )
        monthly_available = household_net - total_outgoings

        # -- Save proportion of spare cash ------------------------
        # household_net already includes both agent and partner income,
        # so monthly_available correctly reflects the combined household surplus.
        # Saving a proportion of this surplus covers both incomes - no separate
        # partner savings needed to avoid double-counting.
        if monthly_available > 0:
            savings += monthly_available * savings_rate * 12
        else:
            savings = max(0, savings + monthly_available * 12)

        # -- Property target based on family needs ----------------
        bedrooms_needed  = get_bedrooms_needed(is_partnered, children)
        price_multiplier = get_price_multiplier(bedrooms_needed)
        household_salary = salary + (salary * PARTNER_SALARY_RATIO if is_partnered else 0)
        # Base price from income multiplier, then apply inflation only to the
        # gap between what salary affords and the true market price.
        # This reflects that real wages grow slower than house prices,
        # so the required deposit grows over time (inflation applied at 40% weight
        # to avoid making purchasing entirely impossible over 35 years).
        base_price     = household_salary * price_multiplier
        property_price = base_price * (1 + (house_price_index - 1) * 0.4)

        # -- Deposit readiness ------------------------------------
        target_deposit_amt = property_price * target_deposit_pct
        deposit_readiness  = (savings / target_deposit_amt * 100) if target_deposit_amt > 0 else 0
        actual_deposit_pct = (savings / property_price) if property_price > 0 else 0
        current_rate       = get_mortgage_rate(actual_deposit_pct)

        # -- Housing decision -------------------------------------
        if not bought:
            if deposit_readiness >= 100:
                # Calculate SDLT and transaction costs on top of deposit
                sdlt_cost     = calculate_sdlt(property_price, first_time_buyer=is_ftb)
                purchase_costs= sdlt_cost + SURVEY_LEGAL_COSTS
                # Deduct all purchase costs from savings
                savings = max(0, savings - purchase_costs)
                decision           = "BUY"
                bought             = True
                is_ftb             = False   # no longer a first-time buyer
                property_type      = random.choice(PROPERTY_TYPES)
                property_age       = PROPERTY_TYPE_AGE_EST[property_type]
                deposit_paid       = savings
                loan_amount        = property_price - deposit_paid
                mortgage_rate_used = current_rate
                monthly_mortgage   = calculate_monthly_mortgage(loan_amount, mortgage_rate_used)
                mortgage_balance   = loan_amount
            elif deposit_readiness >= 50:
                decision = "SAVE_FOR_DEPOSIT"
            else:
                decision = "WAIT"
        else:
            decision = "HOMEOWNER"

        rows.append({
            "sim_year":             sim_year,
            "agent":                name,
            "background":           background,
            "age":                  age,
            "decision":             decision,
            "gross_salary":         round(salary, 0),
            "net_monthly":          net_monthly,
            "pension_monthly":      round(pension_monthly, 2),
            "net_after_pension":    round(net_after_pension, 2),
            "partner_net_monthly":  round(partner_net_monthly, 2),
            "household_net":        round(household_net, 2),
            "savings":              round(savings, 0),
            "debt":                 round(debt, 0),
            "monthly_available":    round(monthly_available, 2),
            "total_outgoings":      round(total_outgoings, 2),
            "expenses":             round(expenses, 2),
            "rent_monthly":         round(rent_monthly, 2),
            "child_costs_monthly":  round(child_costs, 2),
            "student_loan_monthly": round(student_loan_monthly, 2),
            "student_loan_balance": round(loan_balance, 0),
            "debt_repayment":       round(debt_repayment_monthly, 2),
            "is_partnered":         is_partnered,
            "is_married":           is_married,
            "children":             children,
            "bedrooms_needed":      bedrooms_needed,
            "house_price_index":    round(house_price_index, 4),
            "property_price_est":   round(property_price, 0),
            "target_deposit_pct":   f"{int(target_deposit_pct * 100)}%",
            "target_deposit_amt":   round(target_deposit_amt, 0),
            "deposit_readiness":    round(deposit_readiness, 1),
            "actual_deposit_pct":   round(actual_deposit_pct * 100, 1),
            "mortgage_rate_pct":    round(current_rate * 100, 2),
            "monthly_mortgage":     round(monthly_mortgage, 2) if monthly_mortgage else 0.0,
            "mortgage_balance":     round(mortgage_balance, 0) if mortgage_balance else 0,
            "property_type":        property_type or "",
            "fault_cost_annual":    fault_cost_annual,
            "faults":               ", ".join(faults_this_year),
            "life_events":          ", ".join(life_events_log),
            "housing_status":       "homeowner" if bought else "no_mortgage",
        })

        age += 1
        if bought:
            break

    return rows


# -----------------------------------------------------------------
# Run all agents
# -----------------------------------------------------------------

def run_synthetic_simulation() -> pd.DataFrame:
    """
    Runs all synthetic agent profiles and returns combined results.

    :return: DataFrame of all agent yearly results
    """
    all_rows = []
    for profile in AGENT_PROFILES:
        all_rows.extend(simulate_agent(profile))
    return pd.DataFrame(all_rows)


# -----------------------------------------------------------------
# Metrics
# -----------------------------------------------------------------

def compute_median_ftb_age(df: pd.DataFrame) -> dict:
    """
    Computes median first-time buyer age from the synthetic dataset.

    :param df: simulation DataFrame
    :return: dictionary of FTB age statistics
    """
    buy_rows = df[df["decision"] == "BUY"].copy()
    if buy_rows.empty:
        return {"median_ftb_age": None, "note": "No BUY decisions found"}
    per_agent = dict(zip(buy_rows["agent"], buy_rows["age"]))
    ages = list(per_agent.values())
    return {
        "per_agent_ftb_age": per_agent,
        "median_ftb_age":    round(pd.Series(ages).median(), 1),
        "mean_ftb_age":      round(pd.Series(ages).mean(), 1),
        "min_ftb_age":       min(ages),
        "max_ftb_age":       max(ages),
        "total_buyers":      len(ages),
        "never_bought":      len(AGENT_PROFILES) - len(ages),
    }


def compute_ftb_age_by_background(df: pd.DataFrame) -> dict:
    """
    Computes median FTB age by agent background category.

    :param df: simulation DataFrame
    :return: dictionary of {background: median_age}
    """
    buy_rows = df[df["decision"] == "BUY"].copy()
    if buy_rows.empty:
        return {}
    return buy_rows.groupby("background")["age"].median().round(1).to_dict()


def compute_deposit_and_rates(df: pd.DataFrame) -> dict:
    """
    Computes deposit percentages, mortgage rates, and monthly payments
    at point of purchase.

    :param df: simulation DataFrame
    :return: dictionary of deposit and rate statistics
    """
    buy_rows = df[df["decision"] == "BUY"].copy()
    if buy_rows.empty:
        return {"average_deposit_pct": None}
    per_agent = {}
    for _, row in buy_rows.iterrows():
        per_agent[row["agent"]] = {
            "actual_deposit_pct":   row["actual_deposit_pct"],
            "target_deposit_pct":   row["target_deposit_pct"],
            "mortgage_rate_pct":    row["mortgage_rate_pct"],
            "monthly_mortgage":     row["monthly_mortgage"],
            "property_type":        row["property_type"],
            "children_at_purchase": row["children"],
            "bedrooms_needed":      row["bedrooms_needed"],
            "savings":              row["savings"],
            "property_price_est":   row["property_price_est"],
        }
    return {
        "per_agent":               per_agent,
        "average_deposit_pct":     round(buy_rows["actual_deposit_pct"].mean(), 2),
        "median_deposit_pct":      round(buy_rows["actual_deposit_pct"].median(), 2),
        "average_mortgage_rate":   round(buy_rows["mortgage_rate_pct"].mean(), 3),
        "median_mortgage_rate":    round(buy_rows["mortgage_rate_pct"].median(), 3),
        "average_monthly_mortgage":round(buy_rows["monthly_mortgage"].mean(), 2),
    }


def compute_life_event_summary(df: pd.DataFrame) -> dict:
    """
    Counts how many times each life event occurred across all agents.

    :param df: simulation DataFrame
    :return: dictionary of {event_name: count}
    """
    counts = {}
    for events_str in df["life_events"].dropna():
        for event in events_str.split(", "):
            if event:
                key = event.split("(")[0]
                counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


# -----------------------------------------------------------------
# Save and print
# -----------------------------------------------------------------

def save_synthetic_csv(df: pd.DataFrame):
    """
    Saves the synthetic simulation results to the results folder.

    :param df: simulation DataFrame
    """
    out_path = os.path.join(os.path.dirname(__file__), "results", "synthetic_agents.csv")
    df.to_csv(out_path, index=False)
    print(f"Saved to: {out_path}\n")


def print_results(ftb, ftb_by_bg, deposit, events):
    """
    Prints all metrics to the console in a readable format.

    :param ftb: FTB age metrics dictionary
    :param ftb_by_bg: FTB age by background dictionary
    :param deposit: deposit and rate metrics dictionary
    :param events: life event counts dictionary
    """
    sep = "-" * 65
    print(sep)
    print("  SYNTHETIC AGENTS - FULL LIFE SIMULATION METRICS REPORT")
    print(f"  {len(AGENT_PROFILES)} agents | up to {SIM_MAX_YEARS} years each")
    print(sep)

    print("\n[1] FIRST-TIME BUYER AGE")
    if ftb["median_ftb_age"] is None:
        print(f"    {ftb.get('note')}")
    else:
        print(f"    Median FTB age     : {ftb['median_ftb_age']} years")
        print(f"    Mean FTB age       : {ftb['mean_ftb_age']} years")
        print(f"    Youngest buyer     : {ftb['min_ftb_age']} years")
        print(f"    Oldest buyer       : {ftb['max_ftb_age']} years")
        print(f"    Total buyers       : {ftb['total_buyers']} / {len(AGENT_PROFILES)}")
        print(f"    Never bought       : {ftb['never_bought']} agents")
        print("\n    Per agent:")
        for agent, a in sorted(ftb["per_agent_ftb_age"].items(), key=lambda x: x[1]):
            print(f"      {agent:<15} age {a}")

    print("\n[2] MEDIAN FTB AGE BY BACKGROUND")
    for bg, med in sorted(ftb_by_bg.items(), key=lambda x: x[1]):
        print(f"    {bg:<15}: {med} years")

    print("\n[3] DEPOSIT AND MORTGAGE RATES AT PURCHASE")
    if deposit.get("average_deposit_pct") is None:
        print("    No purchase data")
    else:
        print(f"    Avg deposit           : {deposit['average_deposit_pct']}%")
        print(f"    Median deposit        : {deposit['median_deposit_pct']}%")
        print(f"    Avg mortgage rate     : {deposit['average_mortgage_rate']}%")
        print(f"    Median mortgage rate  : {deposit['median_mortgage_rate']}%")
        print(f"    Avg monthly payment   : £{deposit['average_monthly_mortgage']:,.2f}")
        print(f"\n    {'Agent':<15} {'Tgt':>5} {'Dep%':>6} {'Rate':>6} "
              f"{'Beds':>5} {'Kids':>5} {'Type':<14} {'Mthly':>8}")
        print(f"    {'-'*15} {'-'*5} {'-'*6} {'-'*6} {'-'*5} "
              f"{'-'*5} {'-'*14} {'-'*8}")
        for agent, d in sorted(deposit["per_agent"].items(),
                               key=lambda x: x[1]["actual_deposit_pct"]):
            print(
                f"    {agent:<15} "
                f"{d['target_deposit_pct']:>5} "
                f"{d['actual_deposit_pct']:>5.1f}% "
                f"{d['mortgage_rate_pct']:>5.2f}% "
                f"{d['bedrooms_needed']:>5} "
                f"{d['children_at_purchase']:>5} "
                f"{d['property_type']:<14} "
                f"£{d['monthly_mortgage']:>6,.0f}"
            )

    print("\n[4] LIFE EVENTS ACROSS ALL AGENTS")
    for event, count in events.items():
        print(f"    {event:<30}: {count}")

    print(f"\n{sep}\n")


# -----------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------

if __name__ == "__main__":
    df     = run_synthetic_simulation()
    save_synthetic_csv(df)
    ftb    = compute_median_ftb_age(df)
    ftb_bg = compute_ftb_age_by_background(df)
    dep    = compute_deposit_and_rates(df)
    evts   = compute_life_event_summary(df)
    print_results(ftb, ftb_bg, dep, evts)
