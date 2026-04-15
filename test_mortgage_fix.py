"""Quick test to verify the mortgage fix works end-to-end."""

from Environment.Banks import Bank
from Environment.Mortgages.MortgageProduct import MortgageProduct
from Algorithms.ResidentAlgorithms import FinancialAffordabilityEvaluator

evaluator = FinancialAffordabilityEvaluator()

print("=== Test 1: Alice early (£3k deposit after reserve) ===")
salary = 32000
savings = 8000
deposit = max(0, savings - 5000)  # 3000 after reserve

for price in [64000, 60000, 50000]:
    product = MortgageProduct("FTB_2_5.8")  # 5% deposit, 95% LTV
    result = evaluator.check_lending_criteria(
        agent_age=28, agent_income=salary, deposit=deposit,
        property_price=price, mortgage_product=product, existing_debts=0
    )
    pct = deposit / price * 100
    ltv = result["ltv"] * 100
    mp = result["monthly_payment"]
    print(f"  £{price:,}: passes={result['passes']}, deposit={pct:.1f}%, LTV={ltv:.0f}%, monthly=£{mp:.0f}")
    if not result["passes"]:
        print(f"    Failed: {result['failed_checks']}")

print("\n=== Test 2: Alice after saving (£15k deposit after reserve) ===")
deposit2 = max(0, 20000 - 5000)  # 15000

for price in [144000, 100000, 80000, 64000]:
    product = MortgageProduct("FTB_2_5.8")
    result = evaluator.check_lending_criteria(
        agent_age=30, agent_income=salary, deposit=deposit2,
        property_price=price, mortgage_product=product, existing_debts=0
    )
    pct = deposit2 / price * 100
    ltv = result["ltv"] * 100
    mp = result["monthly_payment"]
    print(f"  £{price:,}: passes={result['passes']}, deposit={pct:.1f}%, LTV={ltv:.0f}%, monthly=£{mp:.0f}")
    if not result["passes"]:
        print(f"    Failed: {result['failed_checks']}")

print("\n=== Test 3: _find_best_mortgage simulation ===")
from Financial.Expense_Manager import ExpenseManager
from Financial.Financial_Calculator import SalaryCalculator
from Environment.Housing.Housing import HousingMarket
from Agents.Resident_Agent import ResidentAgent

# Build minimal environment
banks = []
for bn in ["Nationwide", "HSBC", "Barclays", "Lloyds"]:
    try:
        banks.append(Bank(bn))
    except Exception:
        pass

market = HousingMarket()

# Build expense manager
em = ExpenseManager()
em.add_expense("food", "groceries", 250, "monthly")
em.add_expense("utilities", "bills", 200, "monthly")
em.add_expense("transport", "travel", 100, "monthly")

# Create agent with realistic savings
fc = SalaryCalculator(32000)
agent = ResidentAgent(
    agent_id="TEST-001", age=28, name="Alice",
    gross_salary=32000, expense_manager=em,
    financial_calculator=fc, initial_savings=15000,
    housing_market=market, banks_list=banks,
    family_size=1, monthly_rent=850, savings_rate=0.5,
)

# Generate preferences
agent.evaluate_housing_preferences()
max_price = agent.housing_preferences.get("max_price", 0)
min_price = agent.housing_preferences.get("min_price", 0)
print(f"  Preferences: max_price=£{max_price:,.0f}, min_price=£{min_price:,.0f}")
print(f"  Savings: £{agent.financial_state['savings']:,.0f}")
print(f"  Net monthly: £{agent.financial_state['net_salary']/12:,.0f}")
print(f"  Monthly available: £{agent.monthly_available_funds:,.0f}")

# Try to find a mortgage
best = agent._find_best_mortgage(max_price)
if best:
    print(f"\n  SUCCESS! Found mortgage:")
    print(f"    Bank: {best['bank']}")
    print(f"    Product: {best['product_name']}")
    print(f"    Property price: £{best['property_price']:,.0f}")
    print(f"    Deposit: £{best['deposit_paid']:,.0f}")
    print(f"    Loan: £{best['loan_amount']:,.0f}")
    print(f"    Monthly payment: £{best['monthly_payment']:,.0f}")
    print(f"    Comfort: {best['comfort_label']} ({best['affordability_score']}/100)")
else:
    print("\n  FAIL: No mortgage found")

print("\n=== Test 4: Deterministic fallback decision ===")
decision = agent._deterministic_housing_decision()
print(f"  Decision with £15k savings: {decision}")

agent2 = ResidentAgent(
    agent_id="TEST-002", age=24, name="Clara",
    gross_salary=26000, expense_manager=em,
    financial_calculator=SalaryCalculator(26000), initial_savings=2000,
    housing_market=market, banks_list=banks,
    family_size=1, monthly_rent=700, savings_rate=0.5,
)
agent2.evaluate_housing_preferences()
decision2 = agent2._deterministic_housing_decision()
print(f"  Decision with £2k savings: {decision2}")

print("\nAll tests complete!")

