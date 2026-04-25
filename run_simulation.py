"""
Simulation Orchestrator - creates the world (HousingMarket, Banks, Agents),
runs a year-by-year time loop, logs every decision, and exports a CSV
timeline at the end.

Usage:
    python run_simulation.py
"""

import csv
import random
from datetime import datetime
from pathlib import Path

from Environment.Housing.Housing import HousingMarket
from Environment.Banks import Bank
from Financial.Expense_Manager import ExpenseManager
from Financial.Financial_Calculator import SalaryCalculator
from Agents.Resident_Agent import ResidentAgent
from synthetic_agents import AGENT_PROFILES, MONTHLY_RENT
from compute_metrics import compute_all, print_results as print_metrics


# ----------------------------------------------------------------
#  SIMULATION LOGGER
# ----------------------------------------------------------------

class SimulationLogger:
    """
    Records every year-step as a row and exports to CSV when the
    simulation finishes.
    """

    def __init__(self, output_dir="results"):
        """
        Initialise the logger with an empty timeline.

        :param output_dir: Folder where result CSVs are written.
        """
        self.rows = []
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def log_year(self, sim_year, agent_name, year_result):
        """
        Record one year of one agent's results.

        :param sim_year: The calendar year of the simulation step.
        :param agent_name: Name of the agent.
        :param year_result: Dict returned by ResidentAgent.time_step().
        """
        is_ftb = year_result.get("decision") == "BUY" and year_result.get("first_time_buyer", True)
        sb = year_result.get("savings_breakdown", {})
        self.rows.append({
            "sim_year": sim_year,
            "month": "annual",
            "agent": agent_name,
            "age": year_result.get("age"),
            "decision": year_result.get("decision"),
            "gross_salary": year_result.get("gross_salary"),
            "net_monthly": year_result.get("net_monthly"),
            "monthly_expenses": year_result.get("monthly_expenses"),
            "monthly_rent": year_result.get("monthly_rent"),
            "savings": year_result.get("savings"),
            "monthly_available": year_result.get("monthly_available"),
            "happiness_before": year_result.get("happiness_before"),
            "happiness_after": year_result.get("happiness_after"),
            "financial_change": year_result.get("financial_change"),
            "total_debt": year_result.get("total_debt"),
            "housing_status": year_result.get("housing_status"),
            "living_situation": year_result.get("living_situation"),
            "life_events": "; ".join(year_result.get("life_events_this_year", [])),
            "affordability_ratio": year_result.get("affordability_ratio"),
            "deposit_readiness_pct": year_result.get("deposit_readiness_pct"),
            # Savings breakdown columns - shows exactly where savings came from
            "saved_from_surplus": sb.get("general_saved"),
            "goal_contributions": sb.get("goal_contributions"),
            "interest_earned": sb.get("interest_earned"),
            # First-time buyer tracking columns
            "is_ftb_year": is_ftb,
            "ftb_age": year_result.get("age") if is_ftb else None,
            "property_price": year_result.get("property_price") if is_ftb else None,
            "deposit_paid": year_result.get("deposit_paid") if is_ftb else None,
            "deposit_pct": year_result.get("deposit_pct") if is_ftb else None,
            "mortgage_rate": year_result.get("mortgage_rate") if is_ftb else None,
        })

    def log_month(self, sim_year, month, agent_name, month_result):
        """
        Record one month of one agent's results.

        :param sim_year: The calendar year of the simulation step.
        :param month: Month number (1-12).
        :param agent_name: Name of the agent.
        :param month_result: Dict returned by ResidentAgent.monthly_step().
        """
        is_ftb = month_result.get("decision") == "BUY" and month_result.get("first_time_buyer", True)
        self.rows.append({
            "sim_year": sim_year,
            "month": month_result.get("month_label", month),
            "agent": agent_name,
            "age": month_result.get("age"),
            "decision": month_result.get("decision"),
            "gross_salary": month_result.get("gross_salary"),
            "net_monthly": month_result.get("net_monthly"),
            "monthly_expenses": month_result.get("monthly_expenses"),
            "monthly_rent": month_result.get("monthly_rent"),
            "savings": month_result.get("savings"),
            "monthly_available": month_result.get("monthly_available"),
            "happiness_before": month_result.get("happiness_before"),
            "happiness_after": month_result.get("happiness_after"),
            "financial_change": month_result.get("financial_change"),
            "total_debt": month_result.get("total_debt"),
            "housing_status": month_result.get("housing_status"),
            "living_situation": month_result.get("living_situation"),
            "life_events": "; ".join(month_result.get("life_events_this_month", [])),
            "affordability_ratio": month_result.get("affordability_ratio"),
            "deposit_readiness_pct": month_result.get("deposit_readiness_pct"),
            # Savings breakdown columns
            "saved_from_surplus": month_result.get("savings_breakdown", {}).get("general_saved"),
            "goal_contributions": month_result.get("savings_breakdown", {}).get("goal_contributions"),
            "interest_earned": month_result.get("savings_breakdown", {}).get("interest_earned"),
            # First-time buyer tracking columns
            "is_ftb_year": is_ftb,
            "ftb_age": month_result.get("age") if is_ftb else None,
            "property_price": month_result.get("property_price") if is_ftb else None,
            "deposit_paid": month_result.get("deposit_paid") if is_ftb else None,
            "deposit_pct": month_result.get("deposit_pct") if is_ftb else None,
            "mortgage_rate": month_result.get("mortgage_rate") if is_ftb else None,
        })

    def export_csv(self, filename=None):
        """
        Write the full timeline to a CSV file.

        :param filename: Optional filename. Defaults to a timestamped name.
        :return: Path to the written CSV.
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulation_{timestamp}.csv"

        filepath = self.output_dir / filename
        if not self.rows:
            print("  [Logger] Nothing to export — no rows recorded.")
            return filepath

        fieldnames = list(self.rows[0].keys())
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.rows)

        print(f"  [Logger] Results exported to {filepath}")
        return filepath

    def print_summary(self):
        """Print a compact summary table to the console."""
        if not self.rows:
            print("  [Logger] No data to summarise.")
            return

        # Check if we're in monthly mode
        is_monthly = any(r.get("month") not in (None, "annual") for r in self.rows)

        if is_monthly:
            header = f"{'Year':<6} {'Mon':<5} {'Agent':<14} {'Age':<5} {'Decision':<22} " \
                     f"{'Salary':>10} {'Savings':>10} {'Happy':>6} {'Events'}"
        else:
            header = f"{'Year':<6} {'Agent':<14} {'Age':<5} {'Decision':<22} " \
                     f"{'Salary':>10} {'Savings':>10} {'Happy':>6} {'Events'}"

        print("\n" + "=" * 110)
        print(header)
        print("-" * 110)

        for r in self.rows:
            decision_str = str(r.get('decision') or '-')
            events_str = r.get('life_events', '')

            if is_monthly:
                print(
                    f"{r['sim_year']:<6} {str(r.get('month', '')):<5} {r['agent']:<14} {r['age']:<5} "
                    f"{decision_str:<22} "
                    f"£{r['gross_salary']:>8,.0f} £{r['savings']:>8,.0f} "
                    f"{r['happiness_after']:>5.0f} "
                    f"{events_str}"
                )
            else:
                print(
                    f"{r['sim_year']:<6} {r['agent']:<14} {r['age']:<5} "
                    f"{decision_str:<22} "
                    f"£{r['gross_salary']:>8,.0f} £{r['savings']:>8,.0f} "
                    f"{r['happiness_after']:>5.0f} "
                    f"{events_str}"
                )
        print("=" * 110)


# -------------------------------------------------------------------
#  HELPER: BUILD A DEFAULT EXPENSE MANAGER
# -------------------------------------------------------------------

def build_default_expenses(gross_salary):
    """
    Create an ExpenseManager pre-loaded with realistic UK living costs
    scaled loosely to the agent's salary bracket.

    :param gross_salary: Annual gross salary.
    :return: Populated ExpenseManager instance.
    """
    em = ExpenseManager()

    # Scale discretionary spending a little with income
    scale = min(max(gross_salary / 30_000, 0.7), 1.5)

    em.add_expense("food",           "groceries",       220 * scale, "monthly")
    em.add_expense("food",           "eating_out",       60 * scale, "monthly")
    em.add_expense("utilities",      "gas_electric",     120,        "monthly")
    em.add_expense("utilities",      "water",             35,        "monthly")
    em.add_expense("utilities",      "broadband_phone",   55,        "monthly")
    em.add_expense("transport",      "travel",           100 * scale, "monthly")
    em.add_expense("subscriptions",  "streaming",         20,        "monthly")
    em.add_expense("insurance",      "contents_life",     40,        "monthly")
    em.add_expense("health",         "prescriptions",     10,        "monthly")
    em.add_expense("hobbies",        "leisure",           50 * scale, "monthly")
    em.add_expense("misc",           "clothing_other",    60 * scale, "monthly")

    return em


# --------------------------------------------------------------------------------------
#  INTERACTIVE EXPENSE INPUT
# --------------------------------------------------------------------------

# Suggested expenses per category — shown as prompts so the user
# knows what to enter. Each tuple is (expense_name, hint).
EXPENSE_PROMPTS = {
    "food": [
        ("groceries",   "Weekly grocery shop"),
        ("eating_out",  "Eating out / takeaways"),
    ],
    "utilities": [
        ("gas_electric",    "Gas & electricity"),
        ("water",           "Water bill"),
        ("broadband_phone", "Broadband & phone"),
        ("council_tax",     "Council tax"),
    ],
    "transport": [
        ("commute",     "Commuting (bus/train/fuel)"),
        ("car_costs",   "Car insurance, tax, MOT etc."),
    ],
    "subscriptions": [
        ("streaming",   "Streaming services (Netflix, Spotify, etc.)"),
        ("gym",         "Gym / memberships"),
    ],
    "insurance": [
        ("contents_life", "Contents / life / pet insurance"),
    ],
    "health": [
        ("prescriptions", "Prescriptions / dental / optical"),
    ],
    "hobbies": [
        ("leisure", "Hobbies & social activities"),
    ],
    "misc": [
        ("clothing",    "Clothing"),
        ("personal",    "Haircuts, toiletries, etc."),
        ("other",       "Anything else"),
    ],
}


def _read_amount(prompt_text):
    """
    Ask for a monetary amount. Returns 0 if the user presses Enter
    (skip), returns None if the user types 'done'.

    :param prompt_text: The text shown to the user.
    :return: Float amount, 0 for skip, or None for 'done'.
    """
    raw = input(prompt_text).strip()
    if raw.lower() == "done":
        return None
    if raw == "" or raw == "0":
        return 0
    try:
        return float(raw.replace("£", "").replace(",", ""))
    except ValueError:
        print("    Invalid number — skipping this expense.")
        return 0


def interactive_expense_input():
    """
    Walk the user through every expense category and collect their
    monthly amounts. Returns a populated ExpenseManager.

    The user can:
      - Enter an amount for each suggested expense
      - Press Enter to skip (defaults to £0)
      - Type 'done' at any point to finish early

    :return: ExpenseManager with the user's expenses.
    """
    em = ExpenseManager()
    running_total = 0.0

    print("\n" + "=" * 55)
    print("  MONTHLY EXPENSE SETUP")
    print("=" * 55)
    print("  Enter your monthly costs for each item below.")
    print("  Press Enter to skip, or type 'done' to finish early.\n")

    for category, expenses in EXPENSE_PROMPTS.items():
        print(f"  --- {category.upper()} ---")

        for expense_name, hint in expenses:
            amount = _read_amount(f"    {hint} (£/month): ")

            if amount is None:
                # User typed 'done' — stop collecting
                print(f"\n  Total monthly expenses entered: £{running_total:,.2f}")
                return em

            if amount > 0:
                em.add_expense(category, expense_name, amount, "monthly")
                running_total += amount
                print(f"      Added £{amount:,.2f}/month  (running total: £{running_total:,.2f})")

        print()  # Blank line between categories

    print(f"  Total monthly expenses: £{running_total:,.2f}")
    print("=" * 55)
    return em


# --------------------------------------------------------------------------
#  INTERACTIVE DEBT INPUT
# --------------------------------------------------------------------------

def interactive_debt_input():
    """
    Walk the user through adding their existing debts one by one.
    Each debt has its own name, balance, APR, minimum payment, and
    actual monthly payment.

    The user can:
      - Add as many debts as they like
      - Press Enter (or type 'no') when asked to stop adding
      - Each debt is stored separately so interest rates differ

    :return: List of debt dicts ready to pass to DebtManager.add_debt().
    """
    debts = []

    print("\n" + "=" * 55)
    print("  EXISTING DEBTS")
    print("=" * 55)
    print("  Enter any debts you currently have (credit cards,")
    print("  loans, car finance, student overdraft, etc.).")
    print("  Each debt can have a different interest rate.\n")

    while True:
        add_more = input("  Do you have a debt to add? (yes/no) [no]: ").strip().lower()
        if add_more not in ("yes", "y"):
            break

        # -- Debt name --
        name = input("    Debt name (e.g. 'credit_card', 'car_loan'): ").strip()
        if not name:
            name = f"debt_{len(debts) + 1}"

        # -- Outstanding balance --
        balance = _read_float("    Outstanding balance (£)", default=0)
        if balance <= 0:
            print("    Balance must be positive — skipping this debt.")
            continue

        # -- APR --
        print("    Common APRs:  Credit card ~22%  |  Personal loan ~6%  |  Car finance ~8%")
        apr_pct = _read_float("    Annual interest rate (%)", default=19)
        apr = apr_pct / 100  # Convert percentage to decimal

        # -- Minimum payment --
        default_min = max(25, round(balance * 0.02))
        min_payment = _read_float("    Minimum monthly payment (£)", default=default_min)

        # -- Actual payment --
        monthly_payment = _read_float("    What you actually pay per month (£)", default=min_payment)
        if monthly_payment < min_payment:
            print(f"    Payment raised to minimum (£{min_payment:,.2f}).")
            monthly_payment = min_payment

        debts.append({
            "name": name,
            "balance": balance,
            "apr": apr,
            "min_payment": min_payment,
            "monthly_payment": monthly_payment,
        })

        print(f"    ✓ Added '{name}': £{balance:,.0f} at {apr_pct:.1f}% APR, "
              f"paying £{monthly_payment:,.0f}/month\n")

    # Summary
    if debts:
        total_balance = sum(d["balance"] for d in debts)
        total_monthly = sum(d["monthly_payment"] for d in debts)
        print(f"  Debts added: {len(debts)}")
        print(f"  Total owed:  £{total_balance:,.0f}")
        print(f"  Total repayments: £{total_monthly:,.0f}/month")
    else:
        print("  No debts added.")

    print("=" * 55)
    return debts


# --------------------------------------------------------------------------
#  INTERACTIVE STUDENT LOAN INPUT
# --------------------------------------------------------------------------

# UK maintenance loan brackets (2024/25 rates for reference)
MAINTENANCE_LOAN_BRACKETS = {
    "living_at_home": {
        "label": "Living at home with parents",
        "max_loan": 8_610,
    },
    "living_away_outside_london": {
        "label": "Living away from home, outside London",
        "max_loan": 10_227,
    },
    "living_away_london": {
        "label": "Living away from home, in London",
        "max_loan": 13_348,
    },
}


def interactive_student_loan_input():
    """
    Ask the user about their student loan situation. Covers:
      - Whether they are / were a university student
      - Which repayment plan they are on
      - Their maintenance loan bracket (if currently a student)
      - Their estimated total student loan balance
      - Advice on how to check their balance

    :return: Tuple of (student_loan_plans list, student_loan_balance float).
    """
    print("\n" + "=" * 55)
    print("  STUDENT LOAN")
    print("=" * 55)

    is_student = input("  Are you a university student or graduate with "
                       "a student loan? (yes/no) [no]: ").strip().lower()

    if is_student not in ("yes", "y"):
        print("  No student loan — skipping.")
        print("=" * 55)
        return [], 0, None

    # -- Repayment plan --
    print("\n  Which repayment plan are you on?")
    print("    1 - Plan 1  (started before Sept 2012, or Scottish pre-2024)")
    print("    2 - Plan 2  (started Sept 2012 onwards, England & Wales)")
    print("    4 - Plan 4  (Scottish students from 2024)")
    print("    5 - Plan 5  (started Sept 2023 onwards, England)")
    print("    p - Postgraduate Loan (Master's or Doctoral loan)")
    print("    ? - Not sure\n")

    plan_choice = input("  Enter plan number [2]: ").strip().lower()

    plan_map = {
        "1": "plan_1",
        "2": "plan_2",
        "4": "plan_4",
        "5": "plan_5",
        "p": "pgl",
    }

    plans = []
    if plan_choice == "?":
        print("\n  ℹ  Not sure which plan you're on?")
        print("     Check your plan at: https://www.gov.uk/repaying-your-student-loan")
        print("     Or log in to your Student Loans Company account:")
        print("     https://www.gov.uk/student-finance-register-login\n")
        print("     For now, we'll assume Plan 2 (most common for English students).")
        plans = ["plan_2"]
    elif plan_choice in plan_map:
        plans = [plan_map[plan_choice]]
    else:
        plans = ["plan_2"]  # Default to Plan 2

    # Check for postgraduate loan on top
    if plan_choice != "p":
        has_pgl = input("  Do you also have a Postgraduate Loan? (yes/no) [no]: ").strip().lower()
        if has_pgl in ("yes", "y"):
            plans.append("pgl")

    print(f"  → Plan(s) selected: {', '.join(plans)}")

    # -- Repayment thresholds info --
    print("\n  ℹ  How repayment works:")
    threshold_info = {
        "plan_1": ("£423/week (£22,015/year)", "9%"),
        "plan_2": ("£524/week (£27,295/year)", "9%"),
        "plan_4": ("£532/week (£27,660/year)", "9%"),
        "plan_5": ("£480/week (£25,000/year)", "9%"),
        "pgl":    ("£403/week (£21,000/year)", "6%"),
    }
    for p in plans:
        thresh, rate = threshold_info.get(p, ("unknown", "unknown"))
        print(f"     {p}: repay {rate} of income above {thresh}")
    print("     Repayments are deducted from your salary automatically (like tax).")
    print("     They are NOT the same as regular debt — you only pay when earning above the threshold.")

    # -- Current student: maintenance loan bracket --
    currently_studying = input("\n  Are you currently studying at university? (yes/no) [no]: ").strip().lower()
    yearly_maintenance = 0
    if currently_studying in ("yes", "y"):
        print("\n  What is your living situation?")
        print("    1 - Living at home with parents")
        print("    2 - Living away from home, outside London")
        print("    3 - Living away from home, in London\n")

        bracket_choice = input("  Enter choice [2]: ").strip()
        bracket_map = {"1": "living_at_home", "2": "living_away_outside_london", "3": "living_away_london"}
        bracket_key = bracket_map.get(bracket_choice, "living_away_outside_london")
        bracket = MAINTENANCE_LOAN_BRACKETS[bracket_key]

        print(f"\n  → {bracket['label']}")
        print(f"    Maximum maintenance loan: £{bracket['max_loan']:,}/year")
        print("    The exact amount depends on your household income.")
        print("    Check yours at: https://www.gov.uk/student-finance-calculator\n")

        yearly_maintenance = _read_float(
            "    How much maintenance loan do you receive per year? (£)",
            default=bracket["max_loan"]
        )
        print(f"    → £{yearly_maintenance:,.0f}/year maintenance loan noted.")

    # -- Graduation year --
    print("\n  ℹ  Student loan repayments start the April after you graduate.")
    print("     While you're still studying, no repayments are taken.\n")

    graduation_year = _read_int(
        "  What year do you expect to graduate (or did you graduate)?",
        default=2026
    )
    # Repayments start the April after graduation
    repayment_start_year = graduation_year + 1
    print(f"  → Repayments will begin from April {repayment_start_year}.")

    # -- Total balance --
    print("\n  ℹ  How to check your student loan balance:")
    print("     1. Log in at https://www.gov.uk/student-finance-register-login")
    print("     2. Or call the Student Loans Company: 0300 100 0611")
    print("     3. Your employer's payslip shows yearly repayments made\n")

    balance = _read_float(
        "  What is your estimated total student loan balance? (£)",
        default=0
    )

    if balance == 0 and currently_studying in ("yes", "y"):
        # Rough estimate: tuition (£9,250/yr × years) + maintenance
        years_so_far = _read_int("  How many years of study so far?", default=1)
        tuition_yearly = 9_250
        balance = (tuition_yearly + yearly_maintenance) * years_so_far
        print(f"  → Estimated balance: £{balance:,.0f} "
              f"(£{tuition_yearly:,} tuition + £{yearly_maintenance:,.0f} maintenance × {years_so_far} years)")

    if balance > 0:
        print(f"\n  Student loan balance: £{balance:,.0f}")
        print("  Remember: this is repaid through your salary, NOT as a monthly bill.")
        print("  Any remaining balance is written off after 25-40 years (plan dependent).")

    print("=" * 55)
    return plans, balance, graduation_year


# --------------------------------------------------------------------------
#  INTERACTIVE AGENT SETUP (user enters their own details)
# --------------------------------------------------------------------------

def _read_float(prompt_text, default=None):
    """
    Ask for a numeric value. Returns the default if the user presses Enter.

    :param prompt_text: The text shown to the user.
    :param default: Value to use if user presses Enter.
    :return: Float value.
    """
    suffix = f" [{default}]" if default is not None else ""
    raw = input(f"{prompt_text}{suffix}: ").strip()
    if raw == "" and default is not None:
        return float(default)
    try:
        return float(raw.replace("£", "").replace(",", ""))
    except ValueError:
        print(f"    Invalid number — using default ({default}).")
        return float(default) if default is not None else 0


def _read_int(prompt_text, default=None):
    """
    Ask for an integer value. Returns the default if the user presses Enter.

    :param prompt_text: The text shown to the user.
    :param default: Value to use if user presses Enter.
    :return: Int value.
    """
    suffix = f" [{default}]" if default is not None else ""
    raw = input(f"{prompt_text}{suffix}: ").strip()
    if raw == "" and default is not None:
        return int(default)
    try:
        return int(raw)
    except ValueError:
        print(f"    Invalid number — using default ({default}).")
        return int(default) if default is not None else 0


def interactive_agent_setup(housing_market, banks):
    """
    Walk the user through entering their personal details and monthly
    expenses, then build and return a ResidentAgent configured with
    their real data.

    :param housing_market: HousingMarket instance.
    :param banks: List of Bank objects.
    :return: A fully configured ResidentAgent.
    """
    print("\n" + "=" * 55)
    print("  YOUR DETAILS")
    print("=" * 55)
    print("  Press Enter to accept the default shown in [brackets].\n")

    name = input("  Your name [You]: ").strip() or "You"
    age = _read_int("  Your age", default=30)
    gross_salary = _read_float("  Annual gross salary (£)", default=30_000)
    family_size = _read_int("  Household size (including you)", default=1)
    monthly_rent = _read_float("  Current monthly rent (£)", default=850)
    savings = _read_float("  Current savings (£)", default=5_000)

    # Ask for savings rate
    print("\n  What percentage of your spare cash do you save each month?")
    print("  (After bills, rent, and any savings goals are paid)")
    print("  Example: 50 means you save half and spend half on lifestyle")
    savings_pct = _read_float("  Savings rate (%)", default=50)
    savings_rate = max(0, min(100, savings_pct)) / 100  # Convert to 0.0-1.0

    # Collect student loan info
    student_loan_plans, student_loan_balance, graduation_year = interactive_student_loan_input()

    # If still studying, don't activate repayments yet — pass empty plans to calculator
    # The agent will activate them once the simulation year passes graduation + 1
    active_plans = student_loan_plans if graduation_year and graduation_year < 2025 else []

    # Collect expenses interactively
    em = interactive_expense_input()

    # Collect existing debts interactively
    debts = interactive_debt_input()

    fc = SalaryCalculator(gross_salary, student_loan_plans=active_plans)

    agent = ResidentAgent(
        agent_id="USER-001",
        age=age,
        name=name,
        gross_salary=gross_salary,
        expense_manager=em,
        financial_calculator=fc,
        initial_savings=savings,
        housing_market=housing_market,
        banks_list=banks,
        family_size=family_size,
        monthly_rent=monthly_rent,
        student_loan_plans=student_loan_plans,
        student_loan_balance=student_loan_balance,
        student_loan_graduation_year=graduation_year,
        savings_rate=savings_rate,
    )

    # Load the user's debts into the agent's DebtManager
    for debt in debts:
        agent.debt_manager.add_debt(
            name=debt["name"],
            balance=debt["balance"],
            apr=debt["apr"],
            min_payment=debt["min_payment"],
            monthly_payment=debt["monthly_payment"],
        )

    # Recalculate finances now that debts are loaded
    agent.update_financial_state()

    # Show a confirmation summary
    summary = agent.get_monthly_financial_summary()
    sl_repay = agent.financial_calculator.calculate_student_loan()
    sl_annual = sl_repay["total"] * 52

    print("\n" + "-" * 55)
    print(f"  Agent created: {agent}")
    print(f"    Net monthly income:  £{summary['net_monthly']:,.2f}")
    print(f"    Monthly expenses:    £{summary['total_expenses']:,.2f}")
    print(f"    Debt repayments:     £{agent.debt_manager.total_monthly_payments():,.2f}/month")
    if agent.student_loan_plans:
        print(f"    Student loan plan:   {', '.join(agent.student_loan_plans)}")
        print(f"    SL repayment:        £{sl_annual / 12:,.2f}/month (deducted from salary)")
        if agent.student_loan_balance > 0:
            print(f"    SL balance owed:     £{agent.student_loan_balance:,.0f}")
    print(f"    Available per month: £{summary['available_after_expenses']:,.2f}")
    print(f"    Savings rate:        {agent.savings_rate:.0%} of spare cash")
    print(f"    Starting savings:    £{summary['savings_balance']:,.2f}")
    print(f"    Total debt:          £{summary['debt_balance']:,.2f}")
    print("-" * 55)

    return agent


# --------------------------------------------------------------------------
#  YEARLY USER INTERRUPT
# --------------------------------------------------------------------------

def yearly_user_interrupt(agent, sim_year):
    """
    Pause before the AI runs and ask the human player if any life-changing
    events happened this year. Each event is applied to the agent so the
    LLM sees the updated state when it makes its decision.

    :param agent: The user's ResidentAgent.
    :param sim_year: The current simulation year (for display).
    :return: List of event names that the user reported.
    """
    user_events = []

    # Clear last year's one-off expenses so they don't carry over
    agent.expense_manager.one_off_expenses.clear()

    summary = agent.get_monthly_financial_summary()
    print(f"\n  ╔══════════════════════════════════════════════════╗")
    print(f"  ║  YOUR TURN — Year {sim_year}                          ║")
    print(f"  ╠══════════════════════════════════════════════════╣")
    print(f"  ║  Age: {agent.age:<5}  Married: {'Yes' if agent.is_married else 'No':<4}  "
          f"Family: {agent.family_size:<3}      ║")
    print(f"  ║  Salary:  £{agent.gross_salary:>10,.0f}                       ║")
    print(f"  ║  Savings: £{agent.financial_state['savings']:>10,.0f}                       ║")
    print(f"  ║  Debt:    £{summary['debt_balance']:>10,.0f}                       ║")
    print(f"  ║  Saving:  {agent.savings_rate:>9.0%} of spare cash              ║")
    print(f"  ║  Housing: {agent.mortgage_status:<25}        ║")
    print(f"  ╚══════════════════════════════════════════════════╝")

    # Show active savings goals if any
    if agent.savings_manager.has_goals():
        print("\n  Active savings goals:")
        for gs in agent.savings_manager.get_all_summaries():
            bar_len = int(gs["progress_percentage"] / 5)  # 20 char bar
            bar = "█" * bar_len + "░" * (20 - bar_len)
            print(f"    {gs['name']:<16} {bar} {gs['progress_percentage']:5.1f}%  "
                  f"(£{gs['saved']:,.0f} / £{gs['target']:,.0f}, £{gs['monthly']:,.0f}/mo)")

    print("\n  Did anything change in your life this year?")
    print("    1  - Got a new job / salary changed")
    print("    2  - Got married")
    print("    3  - Had a child")
    print("    4  - Got divorced")
    print("    5  - Took on new debt")
    print("    6  - Paid off a debt")
    print("    7  - Received inheritance / windfall")
    print("    8  - Lost my job")
    print("    9  - Other (describe it — the AI will interpret)")
    print("    10 - One-off payment coming up this year")
    print("    11 - Manage savings goals (add/remove)")
    print("    12 - Change my savings rate")
    print("    done - Nothing happened, continue\n")

    while True:
        choice = input("  Enter event number (or 'done'): ").strip().lower()

        if choice in ("done", "d", ""):
            break

        # -- 1. New job / salary change --
        if choice == "1":
            new_salary = _read_float("    What is your new annual gross salary? (£)", default=agent.gross_salary)
            result = agent.apply_life_event("new_job", {"salary": new_salary})
            for c in result["changes"]:
                print(f"      → {c}")
            user_events.append("new_job")

        # -- 2. Marriage --
        elif choice == "2":
            if agent.is_married:
                print("    You're already married — skipping.")
            else:
                result = agent.apply_life_event("marriage")
                for c in result["changes"]:
                    print(f"      → {c}")
                user_events.append("marriage")

        # -- 3. Birth of a child --
        elif choice == "3":
            cost = _read_float("    Estimated extra monthly cost for the child (£)", default=250)
            result = agent.apply_life_event("birth_child", {"monthly_cost": cost})
            for c in result["changes"]:
                print(f"      → {c}")
            user_events.append("birth_child")

        # -- 4. Divorce --
        elif choice == "4":
            if not agent.is_married:
                print("    You're not married — skipping.")
            else:
                result = agent.apply_life_event("divorce")
                for c in result["changes"]:
                    print(f"      → {c}")
                user_events.append("divorce")

        # -- 5. New debt --
        elif choice == "5":
            name = input("    Debt name (e.g. 'car_loan'): ").strip() or f"debt_{len(agent.debt_manager.debts) + 1}"
            balance = _read_float("    Outstanding balance (£)", default=5000)
            print("    Common APRs:  Credit card ~22%  |  Personal loan ~6%  |  Car finance ~8%")
            apr_pct = _read_float("    Annual interest rate (%)", default=19)
            default_min = max(25, round(balance * 0.02))
            min_pay = _read_float("    Monthly payment (£)", default=default_min)
            result = agent.apply_life_event("debt_increase", {
                "name": name,
                "amount": balance,
                "apr": apr_pct / 100,
                "min_payment": min_pay,
            })
            for c in result["changes"]:
                print(f"      → {c}")
            user_events.append("debt_increase")

        # -- 6. Paid off a debt --
        elif choice == "6":
            if not agent.debt_manager.debts:
                print("    You have no debts to pay off.")
            else:
                print("    Your current debts:")
                for dname, dinfo in agent.debt_manager.debts.items():
                    print(f"      - {dname}: £{dinfo['balance']:,.0f} "
                          f"({dinfo['apr']*100:.1f}% APR, £{dinfo['monthly_payment']:,.0f}/mo)")
                which = input("    Which debt did you pay off? (enter name): ").strip()
                result = agent.apply_life_event("debt_paid_off", {"name": which})
                for c in result["changes"]:
                    print(f"      → {c}")
                user_events.append("debt_paid_off")

        # -- 7. Inheritance / windfall --
        elif choice == "7":
            amount = _read_float("    How much did you receive? (£)", default=10_000)
            result = agent.apply_life_event("inheritance", {"amount": amount})
            for c in result["changes"]:
                print(f"      → {c}")
            user_events.append("inheritance")

        # -- 8. Job loss --
        elif choice == "8":
            if agent.gross_salary <= 0:
                print("    You're already unemployed — skipping.")
            else:
                result = agent.apply_life_event("job_loss")
                for c in result["changes"]:
                    print(f"      → {c}")
                user_events.append("job_loss")

        # -- 9. Other (free text → LLM) --
        elif choice == "9":
            description = input("    Describe what happened: ").strip()
            if description:
                result = agent.apply_life_event(description)
                for c in result["changes"]:
                    print(f"      → {c}")
                user_events.append(description)

        # -- 10. One-off payment this year --
        elif choice == "10":
            print("\n    Add one-off expenses expected this year.")
            print("    Examples: holiday, car repair, wedding, moving costs,")
            print("    medical bill, new appliance, etc.")
            print("    These are deducted from your savings over the year.\n")

            while True:
                oo_name = input("    Expense name (or 'done'): ").strip()
                if oo_name.lower() in ("done", "d", ""):
                    break

                oo_amount = _read_float(f"    How much will '{oo_name}' cost? (£)", default=500)
                if oo_amount <= 0:
                    print("    Amount must be positive - skipping.")
                    continue

                MONTH_NAMES = [
                    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
                ]
                print(f"    When is this due?  (1=Jan, 6=Jun, 12=Dec)")
                oo_month = _read_int("    Month number", default=6)
                oo_month = max(1, min(12, oo_month))

                # Work out how many months of the year are left after the payment
                # to spread the impact. E.g. a January payment spreads over 12 months,
                # a December payment hits all at once (spread=1).
                months_remaining = max(1, 13 - oo_month)

                agent.expense_manager.add_one_off(oo_name, oo_amount, spread_over_months=months_remaining)

                # Also deduct immediately from savings since this is a lump sum
                agent.financial_state["savings"] -= oo_amount

                print(f"      ✓ '{oo_name}': £{oo_amount:,.0f} in {MONTH_NAMES[oo_month - 1]} "
                      f"(spread over {months_remaining} remaining months = "
                      f"£{oo_amount / months_remaining:,.0f}/mo impact)")
                user_events.append(f"one_off:{oo_name}")

            # Show summary of all one-offs added this year
            if agent.expense_manager.one_off_expenses:
                total_oo = sum(d["amount"] for d in agent.expense_manager.one_off_expenses.values())
                monthly_oo = agent.expense_manager.monthly_one_off_total()
                print(f"\n    One-off expenses this year: £{total_oo:,.0f} total")
                print(f"    Monthly impact on budget:   £{monthly_oo:,.0f}/month")

        # -- 11. Manage savings goals --
        elif choice == "11":
            print("\n    Savings Goals Manager")
            print("    ─────────────────────")

            # Show current goals
            if agent.savings_manager.has_goals():
                print("    Current goals:")
                for gs in agent.savings_manager.get_all_summaries():
                    print(f"      - {gs['name']}: £{gs['saved']:,.0f}/£{gs['target']:,.0f} "
                          f"({gs['progress_percentage']:.0f}%) — £{gs['monthly']:,.0f}/mo")
            else:
                print("    No savings goals set.")

            print("\n    What would you like to do?")
            print("      a - Add a new savings goal")
            print("      r - Remove an existing goal")
            print("      d - Done with goals")

            while True:
                goal_action = input("    Action (a/r/d): ").strip().lower()

                if goal_action in ("d", "done", ""):
                    break

                if goal_action == "a":
                    goal_name = input("      Goal name (e.g. 'house_deposit', 'holiday'): ").strip()
                    if not goal_name:
                        goal_name = f"goal_{len(agent.savings_manager.goals) + 1}"
                    goal_target = _read_float("      Target amount (£)", default=10_000)
                    goal_monthly = _read_float("      Monthly contribution (£)", default=200)

                    if goal_monthly <= 0 or goal_target <= 0:
                        print("      Target and contribution must be positive — skipping.")
                        continue

                    agent.savings_manager.add_goal(goal_name, goal_target, goal_monthly)
                    months_to_target = goal_target / goal_monthly
                    print(f"      ✓ Goal '{goal_name}': £{goal_target:,.0f} target, "
                          f"£{goal_monthly:,.0f}/mo ({months_to_target:.0f} months to complete)")
                    user_events.append(f"savings_goal_added:{goal_name}")

                elif goal_action == "r":
                    if not agent.savings_manager.has_goals():
                        print("      No goals to remove.")
                        continue
                    print("      Current goals:", ", ".join(agent.savings_manager.goals.keys()))
                    remove_name = input("      Which goal to remove? ").strip()
                    saved = agent.savings_manager.remove_goal(remove_name)
                    if saved > 0:
                        print(f"      ✓ Removed '{remove_name}' (£{saved:,.0f} saved stays in your balance)")
                    else:
                        print(f"      Goal '{remove_name}' not found.")

            # Show updated monthly impact
            goal_monthly_total = agent.savings_manager.monthly_total()
            if goal_monthly_total > 0:
                print(f"\n    Total goal contributions: £{goal_monthly_total:,.0f}/month")
                print(f"    (This comes out of your spare cash before the savings rate is applied)")

        # -- 12. Change savings rate --
        elif choice == "12":
            print(f"\n    Current savings rate: {agent.savings_rate:.0%}")
            print("    This is the percentage of spare cash (after goals) that you save.")
            print("    The rest is lifestyle spending.")
            new_pct = _read_float("    New savings rate (%)", default=agent.savings_rate * 100)
            old_rate = agent.savings_rate
            agent.savings_rate = max(0, min(100, new_pct)) / 100
            print(f"    ✓ Savings rate: {old_rate:.0%} -> {agent.savings_rate:.0%}")
            user_events.append(f"savings_rate_changed:{agent.savings_rate:.0%}")

        else:
            print("    Invalid choice — try again.")

        print()  # Blank line between events

    if user_events:
        print(f"  Events applied: {', '.join(user_events)}")
    else:
        print("  No changes — the AI will proceed with your current situation.")

    return user_events


# --------------------------------------------------------------------------
#  AI ACTIVITY DISPLAY
# --------------------------------------------------------------------------

def display_ai_activity(agent_name, result):
    """
    Print a formatted summary of what the AI did for this agent this year.
    Shows tool calls, reasoning, and the AI's own narrative.

    :param agent_name: Name of the agent.
    :param result: Dict returned by ResidentAgent.time_step().
    """
    tool_trace = result.get("ai_tool_trace", [])
    reasoning = result.get("ai_reasoning", "")
    narrative = result.get("ai_narrative", "")

    # Only show the AI box if we have something to display
    if not tool_trace and not reasoning and not narrative:
        return

    print(f"\n  ┌─── AI Activity for {agent_name} ───")

    # -- Show which tools the AI called --
    if tool_trace:
        print(f"  │")
        print(f"  │  Tools used by the AI this step:")
        for i, tc in enumerate(tool_trace, 1):
            tool_name = tc.get("tool", "unknown")
            tool_input = tc.get("input", {})
            tool_output = tc.get("output", "")

            # Format the input arguments as a short string
            if tool_input:
                args_str = ", ".join(f"{k}={v}" for k, v in tool_input.items())
            else:
                args_str = "(no args)"

            print(f"  │    {i}. {tool_name}({args_str})")

            # Show a truncated version of the tool output
            if tool_output:
                # Limit to first 120 chars so it stays readable
                preview = tool_output.replace("\n", " | ")
                if len(preview) > 120:
                    preview = preview[:117] + "..."
                print(f"  │       -> {preview}")

    # -- Show the AI's reasoning --
    if reasoning:
        print(f"  │")
        print(f"  │  AI Reasoning:")
        # Word-wrap the reasoning to ~70 chars per line
        words = reasoning.split()
        line = "  │    "
        for word in words:
            if len(line) + len(word) + 1 > 78:
                print(line)
                line = "  │    "
            line += word + " "
        if line.strip("│ "):
            print(line)

    # -- Show the AI narrative (first-person summary) --
    if narrative:
        print(f"  │")
        print(f"  │  AI Narrative:")
        # Word-wrap the narrative
        words = narrative.split()
        line = '  │    "'
        for word in words:
            if len(line) + len(word) + 1 > 78:
                print(line)
                line = "  │     "
            line += word + " "
        if line.strip("│ "):
            print(line.rstrip() + '"')

    print(f"  └{'─' * 50}")


# --------------------------------------------------------------------------
#  HELPER: BUILD AGENTS
# --------------------------------------------------------------------------

def build_agents(housing_market, banks, num_agents=3, seed=42, use_llm=True):
    """
    Create a list of ResidentAgent instances with varied demographics.

    :param housing_market: HousingMarket instance.
    :param banks: List of Bank objects.
    :param num_agents: How many agents to create.
    :param seed: Random seed for reproducibility.
    :return: List of ResidentAgent instances.
    """
    rng = random.Random(seed)

    # Agent templates: (name, age, salary, family_size, rent)
    templates = [
        ("Alice",   28,  32_000, 1,  850),
        ("Bob",     35,  45_000, 2,  1_000),
        ("Clara",   24,  26_000, 1,  700),
        ("David",   42,  55_000, 3,  1_100),
        ("Emma",    31,  38_000, 1,  900),
        ("Frank",   50,  60_000, 4,  1_200),
    ]

    agents = []
    for i in range(min(num_agents, len(templates))):
        name, age, salary, fam, rent = templates[i]

        # Add a little randomness to salary (+/- 5%)
        salary *= rng.uniform(0.95, 1.05)

        em = build_default_expenses(salary)
        fc = SalaryCalculator(salary)

        initial_savings = rng.uniform(0.10, 0.25) * salary  # 10-25% of annual salary

        # Random savings rate between 10% and 25% of spare cash
        # (UK average household savings rate is roughly 10-15%)
        savings_rate = rng.uniform(0.10, 0.25)

        agent = ResidentAgent(
            agent_id=f"AGENT-{i+1:03d}",
            age=age,
            name=name,
            gross_salary=salary,
            expense_manager=em,
            financial_calculator=fc,
            initial_savings=initial_savings,
            housing_market=housing_market,
            banks_list=banks,
            family_size=fam,
            monthly_rent=rent,
            savings_rate=savings_rate,
            use_llm=use_llm,
        )
        agents.append(agent)
        print(f"  Created agent: {agent}")

    return agents


# --------------------------------------------------------------------------
#  BUILD AGENTS FROM SYNTHETIC PROFILES
# --------------------------------------------------------------------------

def build_agents_from_profiles(housing_market, banks, max_agents=None, use_llm=True):
    """
    Convert AGENT_PROFILES tuples from synthetic_agents.py into real
    ResidentAgent instances so the LLM simulation can run them.

    Each tuple format:
        (name, start_age, start_salary, start_savings, savings_rate,
         monthly_expenses, background, target_deposit_pct,
         has_student_loan, start_partnered, start_children)

    :param housing_market: HousingMarket instance.
    :param banks: List of Bank objects.
    :param max_agents: Limit how many profiles to load (None = all).
                       Running all 40+ with the LLM is slow - use a subset
                       for quick tests.
    :return: List of ResidentAgent instances.
    """
    if max_agents is None or max_agents >= len(AGENT_PROFILES):
        profiles = AGENT_PROFILES
    else:
        profiles = random.sample(AGENT_PROFILES, max_agents)
    agents = []

    # Bedroom needs: 1 for single, +1 per child, +1 if partnered
    def _bedrooms(partnered, children):
        beds = 1 + children
        if partnered:
            beds = max(beds, 2)
        return min(beds, 4)  # Cap at 4-bed for rent lookup

    for i, profile in enumerate(profiles):
        (name, start_age, start_salary, start_savings, savings_rate,
         monthly_expenses, background, target_deposit_pct,
         has_student_loan, start_partnered, start_children) = profile

        # Build an ExpenseManager from the single monthly_expenses figure.
        # Split the total across realistic categories so the expense manager
        # works as normal - rent is handled separately by ResidentAgent.
        em = ExpenseManager()
        remaining = float(monthly_expenses)
        # Rough realistic split of living costs (excluding rent)
        em.add_expense("food",          "groceries",       remaining * 0.25, "monthly")
        em.add_expense("food",          "eating_out",      remaining * 0.08, "monthly")
        em.add_expense("utilities",     "gas_electric",    remaining * 0.12, "monthly")
        em.add_expense("utilities",     "water",           remaining * 0.04, "monthly")
        em.add_expense("utilities",     "broadband_phone", remaining * 0.05, "monthly")
        em.add_expense("transport",     "travel",          remaining * 0.12, "monthly")
        em.add_expense("subscriptions", "streaming",       remaining * 0.03, "monthly")
        em.add_expense("insurance",     "contents_life",   remaining * 0.05, "monthly")
        em.add_expense("health",        "health_misc",     remaining * 0.03, "monthly")
        em.add_expense("hobbies",       "leisure",         remaining * 0.10, "monthly")
        em.add_expense("misc",          "clothing_other",  remaining * 0.13, "monthly")

        # Student loan setup - assume already graduated (repayments active)
        loan_plans = ["plan_2"] if has_student_loan else []
        loan_balance = 35_000 if has_student_loan else 0

        # Family size = 1 (self) + 1 if partnered + children
        family_size = 1 + (1 if start_partnered else 0) + start_children

        # Monthly rent based on bedroom needs
        beds = _bedrooms(start_partnered, start_children)
        full_rent = MONTHLY_RENT.get(beds, 1100)
        # Partnered agents share rent 50/50 with their partner.
        # The partner isn't a separate LLM agent but they do contribute
        # to household costs — charging the full rent would make partnered
        # agents worse off than singles, which is the opposite of reality.
        monthly_rent = full_rent // 2 if start_partnered else full_rent

        fc = SalaryCalculator(start_salary, student_loan_plans=loan_plans)

        # -- Determine starting living situation --
        # Estimate net monthly to see if the agent can afford to live alone
        _net = SalaryCalculator(start_salary, student_loan_plans=loan_plans).calculate_net_pay()["net_pay"] / 12
        _solo_available = _net - float(monthly_expenses) - monthly_rent
        _shared_available = _net - float(monthly_expenses) - (min(monthly_rent, 850) * 0.5)

        if start_age <= 19:
            # Very young: still living at home is realistic
            living_situation = "with_parents"
        elif _solo_available < -100:
            # Can't afford solo — try shared first
            if _shared_available < -100:
                living_situation = "with_parents"
            else:
                living_situation = "shared"
        else:
            living_situation = "solo"

        agent = ResidentAgent(
            agent_id=f"SYNTH-{i+1:03d}",
            age=start_age,
            name=name,
            gross_salary=start_salary,
            expense_manager=em,
            financial_calculator=fc,
            initial_savings=start_savings,
            housing_market=housing_market,
            banks_list=banks,
            family_size=family_size,
            monthly_rent=monthly_rent,
            student_loan_plans=loan_plans,
            student_loan_balance=loan_balance,
            student_loan_graduation_year=None,  # Already graduated - repayments active
            savings_rate=savings_rate,
            first_time_buyer=True,
            living_situation=living_situation,
            use_llm=use_llm,
            target_deposit_pct=float(target_deposit_pct),
        )
        agents.append(agent)
        print(f"  Created agent: {name} (age {start_age}, £{start_salary:,}/yr, "
              f"savings £{start_savings:,}, living: {living_situation})")

    return agents


# --------------------------------------------------------------------------
#  MAIN SIMULATION LOOP
# --------------------------------------------------------------------------

def run_simulation(num_agents=3, num_years=10, load_housing_data=True,
                   housing_years=None, seed=42):
    """
    End-to-end simulation runner.

    :param num_agents: Number of agents to simulate.
    :param num_years: Number of yearly time steps.
    :param load_housing_data: Whether to load Land Registry CSVs.
    :param housing_years: Which years of housing data to load (default recent).
    :param seed: Master random seed for reproducibility.
    :return: SimulationLogger with all recorded rows.
    """
    random.seed(seed)
    project_root = Path(__file__).parent

    print("=" * 60)
    print("  HOUSING AFFORDABILITY SIMULATION")
    print("=" * 60)

    # -- Build the housing market --
    print("\n[1/4] Setting up housing market...")
    housing_market = HousingMarket()

    if load_housing_data:
        lr_path = project_root / "Environment" / "Housing" / "HM Land Registery Price Paid"
        if lr_path.exists():
            years_to_load = housing_years or [2022, 2023, 2024]
            print(f"  Loading Land Registry data for years: {years_to_load}")
            housing_market.load_years(years_to_load, str(lr_path))
            print(f"  Loaded {len(housing_market.houses):,} properties")
        else:
            print(f"  Warning: Land Registry folder not found at {lr_path}")
            print("  Simulation will run but agents cannot search for properties.")

    # -- Build the banks --
    print("\n[2/4] Setting up banks...")
    bank_names = ["Nationwide", "HSBC", "Barclays", "Lloyds"]
    banks = []
    for bn in bank_names:
        try:
            bank = Bank(bn)
            banks.append(bank)
            print(f"  {bank}")
        except ValueError as e:
            print(f"  Skipping {bn}: {e}")

    # -- Build the agents --
    print(f"\n[3/4] Setting up agents...")

    # Ask LLM mode first so agents can be created with the right flag
    # (avoids Ollama model loading for each agent when not needed)
    print("  Decision-making mode:")
    print("    1 - LLM (Ollama)   — realistic reasoning, slow (~30s per agent-year)")
    print("    2 - Rule-based     — fast deterministic logic, ideal for bulk stats")
    llm_choice = input("  Choose [1/2]: ").strip()
    use_llm = llm_choice != "2"
    if not use_llm:
        print("  ✓ Rule-based mode — LLM disabled. Bulk run will be near-instant.")
    else:
        print("  ✓ LLM mode — Ollama will be called for each agent decision.")

    print("\n  Agent type:")
    print("    1 - Enter my own details (you become an agent in the simulation)")
    print("    2 - Use default agents only (Alice, Bob, Clara...)")
    print("    3 - Use synthetic agent profiles (40 varied agents)")
    choice = input("  Choose [1/2/3]: ").strip()

    agents = []
    if choice == "1":
        user_agent = interactive_agent_setup(housing_market, banks)
        agents.append(user_agent)
        # Add some default comparison agents alongside the user
        comparison_count = max(0, num_agents - 1)
        if comparison_count > 0:
            print(f"\n  Adding {comparison_count} comparison agent(s)...")
            agents.extend(build_agents(housing_market, banks,
                                       num_agents=comparison_count, seed=seed,
                                       use_llm=use_llm))
    elif choice == "3":
        print(f"\n  Loading synthetic agent profiles from synthetic_agents.py...")
        limit_input = input(f"  How many agents to run? (Enter for all {len(AGENT_PROFILES)}): ").strip()
        max_agents = int(limit_input) if limit_input.isdigit() else None
        agents = build_agents_from_profiles(housing_market, banks, max_agents=max_agents, use_llm=use_llm)
        print(f"\n  Loaded {len(agents)} synthetic agent(s).")
    else:
        agents = build_agents(housing_market, banks, num_agents=num_agents, seed=seed, use_llm=use_llm)

    # -- Choose simulation mode --
    print("\n  Simulation step size:")
    print("    1 - Monthly  (month-by-month, AI decides quarterly)")
    print("    2 - Annual   (one step per year, faster)")
    mode_choice = input("  Choose [1/2]: ").strip()
    monthly_mode = mode_choice == "1"

    if monthly_mode:
        print(f"\n[4/4] Running simulation for {num_years} years (monthly mode)...")
        print("  AI decisions are made quarterly (Jan, Apr, Jul, Oct).")
        print("  User interrupt happens each January.\n")
    else:
        print(f"\n[4/4] Running simulation for {num_years} years (annual mode)...")

    # -- Run the simulation loop --
    logger = SimulationLogger()
    start_year = 2025

    if monthly_mode:
        # ----------------------------------------------------------
        #  MONTHLY SIMULATION LOOP
        # ----------------------------------------------------------
        for year_offset in range(num_years):
            sim_year = start_year + year_offset

            for month in range(1, 13):
                MONTH_NAMES = [
                    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
                ]
                month_label = MONTH_NAMES[month - 1]

                # Print a year header on month 1
                if month == 1:
                    print(f"\n{'='*60}")
                    print(f"  Year {sim_year} (step {year_offset + 1}/{num_years})")
                    print(f"{'='*60}")

                for agent in agents:
                    # User interrupt on month 1 (start of each year)
                    user_year_events = []
                    if month == 1 and agent.agent_id == "USER-001":
                        user_year_events = yearly_user_interrupt(agent, sim_year)

                    try:
                        result = agent.monthly_step(month, sim_year)

                        # Merge user-reported events into month 1 result
                        if month == 1 and agent.agent_id == "USER-001" and user_year_events:
                            result["life_events_this_month"] = (
                                user_year_events + result.get("life_events_this_month", [])
                            )

                        # Generate AI narrative on decision months
                        if result.get("decision") is not None:
                            try:
                                result["ai_narrative"] = agent.generate_ai_narrative(result)
                            except Exception:
                                result["ai_narrative"] = ""

                        # Log every month
                        logger.log_month(sim_year, month, agent.name, result)

                        # Print output — detailed on AI months, compact otherwise
                        decision = result.get("decision")
                        saved_this_month = result["savings_breakdown"]["total_change"]

                        if decision is not None:
                            # AI decision month — show full detail
                            print(f"\n  {month_label} {sim_year} | {agent.name} (age {result['age']})")
                            print(f"    Decision: {decision}")
                            print(f"    Savings: £{result['savings']:,.0f} "
                                  f"({'+' if saved_this_month >= 0 else ''}"
                                  f"£{saved_this_month:,.0f} this month)")
                            print(f"    Happy: {result['happiness_after']:.0f}/100")

                            if result.get("life_events_this_month"):
                                print(f"    Life events: {', '.join(result['life_events_this_month'])}")

                            # Show AI activity on decision months
                            display_ai_activity(agent.name, result)
                        else:
                            # Non-decision month — compact one-liner
                            events_str = ""
                            if result.get("life_events_this_month"):
                                events_str = f" | Events: {', '.join(result['life_events_this_month'])}"
                            print(f"  {month_label} | {agent.name}: "
                                  f"Savings £{result['savings']:,.0f} "
                                  f"({'+' if saved_this_month >= 0 else ''}"
                                  f"£{saved_this_month:,.0f})"
                                  f"{events_str}")

                    except Exception as e:
                        print(f"  ERROR for {agent.name} ({month_label}): {e}")
                        logger.log_month(sim_year, month, agent.name, {
                            "month": month,
                            "month_label": month_label,
                            "sim_year": sim_year,
                            "age": agent.age,
                            "decision": f"ERROR: {e}",
                            "gross_salary": agent.gross_salary,
                            "net_monthly": 0,
                            "savings": agent.financial_state.get("savings", 0),
                            "monthly_available": 0,
                            "happiness_before": agent.happiness_score,
                            "happiness_after": agent.happiness_score,
                            "financial_change": 0,
                            "housing_status": agent.mortgage_status,
                            "life_events_this_month": [],
                            "savings_breakdown": {
                                "goal_contributions": 0, "general_saved": 0,
                                "lifestyle_spent": 0, "total_change": 0
                            },
                        })

    else:
        # ----------------------------------------------------------
        #  ANNUAL SIMULATION LOOP (original)
        # ----------------------------------------------------------
        for year_offset in range(num_years):
            sim_year = start_year + year_offset
            print(f"\n--- Year {sim_year} (step {year_offset + 1}/{num_years}) ---")

            for agent in agents:
                # If this is the user's agent, pause for interactive input first
                user_year_events = []
                if agent.agent_id == "USER-001":
                    user_year_events = yearly_user_interrupt(agent, sim_year)

                try:
                    result = agent.time_step(years_elapsed=1)

                    # Merge any user-reported events into the result so they appear in logs
                    if agent.agent_id == "USER-001" and user_year_events:
                        result["life_events_this_year"] = user_year_events + result.get("life_events_this_year", [])

                    # Ask the AI to write a short narrative about the year
                    try:
                        result["ai_narrative"] = agent.generate_ai_narrative(result)
                    except Exception:
                        result["ai_narrative"] = ""

                    logger.log_year(sim_year, agent.name, result)
                    print(f"  {agent.name} (age {result['age']}): "
                          f"{result['decision']} | "
                          f"Salary £{result['gross_salary']:,.0f} | "
                          f"Savings £{result['savings']:,.0f} | "
                          f"Happy {result['happiness_after']:.0f}")
                    if result.get("life_events_this_year"):
                        print(f"    Life events: {', '.join(result['life_events_this_year'])}")

                    # Display the AI's tool usage, reasoning, and narrative
                    display_ai_activity(agent.name, result)
                except Exception as e:
                    print(f"  ERROR for {agent.name}: {e}")
                    # Log a partial row so we can debug later
                    logger.log_year(sim_year, agent.name, {
                        "age": agent.age,
                        "decision": f"ERROR: {e}",
                        "gross_salary": agent.gross_salary,
                        "net_monthly": 0,
                        "savings": agent.financial_state.get("savings", 0),
                        "monthly_available": 0,
                        "happiness_before": agent.happiness_score,
                        "happiness_after": agent.happiness_score,
                        "financial_change": 0,
                        "housing_status": agent.mortgage_status,
                        "life_events_this_year": [],
                    })

    # -- Export results --
    print("\n" + "=" * 60)
    print("  SIMULATION COMPLETE")
    print("=" * 60)

    logger.print_summary()
    csv_path = logger.export_csv()

    # Print final agent states
    print("\n--- Final Agent States ---")
    for agent in agents:
        status = agent.get_status_summary()
        print(f"\n  {status['name']} (age {status['age']}):")
        print(f"    Housing: {status['housing']['status']}")
        print(f"    Savings: £{status['financial']['savings_balance']:,.0f}")
        print(f"    Debt:    £{status['financial']['debt_balance']:,.0f}")
        print(f"    Happiness: {status['happiness']:.0f}/100")
        if status['life_events']:
            print(f"    Life events: {', '.join(status['life_events'][-5:])}")

    # Print first-time buyer summary table
    ftb_rows = [r for r in logger.rows if r.get("is_ftb_year")]
    if ftb_rows:
        print("\n--- First-Time Buyer Summary ---")
        print(f"  {'Agent':<14} {'Year':<6} {'Age':<5} {'Property Price':>15} "
              f"{'Deposit Paid':>14} {'Deposit %':>10} {'Rate':>6}")
        print("  " + "-" * 72)
        for r in ftb_rows:
            price   = f"£{r['property_price']:,.0f}"   if r.get("property_price")  else "N/A"
            deposit = f"£{r['deposit_paid']:,.0f}"      if r.get("deposit_paid")    else "N/A"
            dpct    = f"{r['deposit_pct']:.1f}%"        if r.get("deposit_pct")     else "N/A"
            rate    = f"{r['mortgage_rate']:.2f}%"      if r.get("mortgage_rate")   else "N/A"
            print(f"  {r['agent']:<14} {r['sim_year']:<6} {r['ftb_age']:<5} "
                  f"{price:>15} {deposit:>14} {dpct:>10} {rate:>6}")
    else:
        print("\n  No first-time purchases recorded in this run.")

    # -- Auto-run metrics report --
    print("\n" + "=" * 60)
    print("  COMPUTING METRICS...")
    print("=" * 60)
    try:
        import pandas as pd
        df = pd.DataFrame(logger.rows)
        metrics = compute_all(df)
        print_metrics(metrics)
    except Exception as e:
        print(f"  [Metrics] Could not compute metrics: {e}")

    return logger


# --------------------------------------------------------------------------
#  ENTRY POINT
# --------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  HOUSING AFFORDABILITY SIMULATION - SETUP")
    print("=" * 60)

    # Ask the user how many years to run
    _years_raw = input("\n  How many years to simulate? (default 10): ").strip()
    _num_years = int(_years_raw) if _years_raw.isdigit() and int(_years_raw) > 0 else 10
    print(f"  Running for {_num_years} year(s).")

    run_simulation(
        num_agents=3,
        num_years=_num_years,
        load_housing_data=True,
        housing_years=[2022, 2023, 2024],
        seed=42,
    )
