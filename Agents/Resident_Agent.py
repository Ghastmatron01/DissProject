from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from Environment.Mortgages.MortgageProduct import MortgageProduct
from Financial.Financial_Calculator import SalaryCalculator
from Algorithms.ResidentAlgorithms import (
    HousingPreferenceEvaluator,
    FinancialAffordabilityEvaluator,
    HappinessEvaluator
)
from Agents.agent_tools import build_agent_tools
from Agents.agent_prompts import RESIDENT_SYSTEM_PROMPT, DECISION_SUMMARY_PROMPT


class ResidentAgent:
    """
    AI-powered resident agent that uses an LLM (Ollama) as its decision-making
    brain, while calling algorithm classes as tools for calculations.

    Architecture:
        LLM (Ollama llama3.2)           - the "brain", reasons about what to do
        Tools (agent_tools.py)           - the "advisors", call algorithm classes
        Algorithms (ResidentAlgorithms.py) - the "maths", scoring and evaluation
        Financial classes                - the "accountant", tax, expenses, mortgage calcs

    The LLM never does maths. It asks the tools, reads the answers, then decides.
    """

    def __init__(self, agent_id, age, name, gross_salary, expense_manager,
                 financial_calculator=None, initial_savings=0,
                 housing_market=None, banks_list=None, family_size=1):
        """
        Set up the resident agent with identity, finances, environment
        references, algorithm instances, and the LLM agent.

        :param agent_id: Unique identifier for this agent.
        :param age: Current age of the resident.
        :param name: Resident's name.
        :param gross_salary: Annual gross salary before tax.
        :param expense_manager: ExpenseManager instance with expenses already set up.
        :param financial_calculator: SalaryCalculator instance. If None, one is created.
        :param initial_savings: Starting savings balance.
        :param housing_market: HousingMarket instance for property searches.
        :param banks_list: List of Bank objects the agent can apply to.
        :param family_size: Number of people in the household.
        """
        # -- Identity --
        self.agent_id = agent_id
        self.age = age
        self.name = name
        self.family_size = family_size

        # -- Financial system --
        self.gross_salary = gross_salary
        self.expense_manager = expense_manager

        # Use the provided calculator or create one from the salary
        if financial_calculator is not None:
            self.financial_calculator = financial_calculator
        else:
            self.financial_calculator = SalaryCalculator(gross_salary)

        # Central dict that tracks all financial values
        self.financial_state = {
            "gross_salary": gross_salary,
            "net_salary": 0,
            "total_expenses_monthly": 0,
            "savings": initial_savings,
            "debt": 0,
        }
        self.monthly_available_funds = 0

        # -- Environment references --
        self.housing_market = housing_market   # HousingMarket instance
        self.banks_list = banks_list or []     # List of Bank objects
        self.last_search_results = []          # Stores the most recent property search

        # -- Housing and mortgage status --
        self.mortgage_status = "no_mortgage"
        self.current_property = None
        self.active_mortgage = None            # Dict of mortgage details when bought
        self.housing_preferences = {}

        # -- Life and satisfaction --
        self.happiness_score = 70
        self.life_events = []

        # -- Algorithm instances --
        self.housing_preference_evaluator = HousingPreferenceEvaluator()
        self.financial_affordability_evaluator = FinancialAffordabilityEvaluator()
        self.happiness_evaluator = HappinessEvaluator()

        # Run the initial financial calculation so net_salary etc. are populated
        self.update_financial_state()

        # Build the LLM agent with tools and system prompt
        self._setup_llm_agent()

    # --------------------------------------------------------------------
    #  LLM AGENT SETUP
    # --------------------------------------------------------------------

    def _setup_llm_agent(self):
        """
        Create the LangChain agent backed by Ollama, bind the tools, and
        inject the current agent state into the system prompt.
        """
        # Initialise the LLM
        self.llm = ChatOllama(model="llama3.2")

        # Build the tool functions that are bound to this agent instance
        self.tools = build_agent_tools(self)

        # Format the system prompt with the agent's current state
        system_prompt = RESIDENT_SYSTEM_PROMPT.format(
            age=self.age,
            name=self.name,
            gross_salary=self.gross_salary,
            net_monthly=self.financial_state["net_salary"] / 12,
            available_monthly=self.monthly_available_funds,
            savings=self.financial_state["savings"],
            housing_status=self.mortgage_status,
            happiness=self.happiness_score,
        )

        # Wire the LLM, tools, and prompt together into a runnable agent
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt,
            name="resident_agent",
        )

    # --------------------------------------------------------------------
    #  FINANCIAL MANAGEMENT
    # --------------------------------------------------------------------

    def update_financial_state(self):
        """
        Recalculate net pay, expenses, available funds, and accumulate
        savings. Called on init and once per time_step.

        :return: The updated financial_state dict.
        """
        # Get annual net pay after tax and NI
        pay_result = self.financial_calculator.calculate_net_pay()
        net_annual = pay_result["net_pay"]

        # Sum all monthly expenses from the expense manager
        total_monthly_expenses = self.expense_manager.calculate_total_monthly()

        # Work out what is left each month after expenses
        net_monthly = net_annual / 12
        available = net_monthly - total_monthly_expenses

        # Subtract the mortgage payment if one is active
        if self.active_mortgage is not None:
            available -= self.active_mortgage.get("monthly_payment", 0)

        # Persist the calculated values
        self.financial_state["net_salary"] = net_annual
        self.financial_state["total_expenses_monthly"] = total_monthly_expenses
        self.monthly_available_funds = available

        # Accumulate a full year of spare cash into savings
        if available > 0:
            annual_savings = available * 12
            self.financial_state["savings"] += annual_savings

        return self.financial_state

    def get_monthly_financial_summary(self):
        """
        Build a snapshot of the agent's monthly finances for display.

        :return: Dict with gross_monthly, net_monthly, total_expenses,
                 available_after_expenses, savings_balance, debt_balance.
        """
        net_annual = self.financial_state["net_salary"]
        return {
            "gross_monthly": round(self.gross_salary / 12, 2),
            "net_monthly": round(net_annual / 12, 2),
            "total_expenses": round(self.financial_state["total_expenses_monthly"], 2),
            "available_after_expenses": round(self.monthly_available_funds, 2),
            "savings_balance": round(self.financial_state["savings"], 2),
            "debt_balance": round(self.financial_state["debt"], 2),
        }

    # --------------------------------------------------------------------
    #  HOUSING PREFERENCES
    # --------------------------------------------------------------------

    def evaluate_housing_preferences(self, user_overrides=None):
        """
        Generate algorithm-based housing preferences and optionally merge
        in user-supplied overrides.

        :param user_overrides: Dict of preference keys to override, or None.
        :return: The final housing preferences dict.
        """
        # Generate defaults from age, income, and family size
        self.housing_preferences = self.housing_preference_evaluator.evaluate_preferences(
            self.age, self.gross_salary, self.family_size
        )

        # Merge any user-supplied values on top of the defaults
        if user_overrides is not None:
            self.housing_preferences = self.housing_preference_evaluator.override_preferences(
                self.housing_preferences, user_overrides
            )

        return self.housing_preferences

    # --------------------------------------------------------------------
    #  MORTGAGE SEARCHING
    # --------------------------------------------------------------------

    def search_for_mortgages(self, max_property_price):
        """
        Loop through every bank's products and return the ones the agent
        qualifies for, sorted by cheapest monthly payment first.

        :param max_property_price: The maximum property price to check against.
        :return: List of dicts (bank, product, lending_result), sorted by monthly payment.
        """
        viable_mortgages = []

        for bank in self.banks_list:
            # Gather all unique product IDs across every branch of this bank
            product_ids = set()
            for branch in bank.get_all_branches():
                product_ids.update(branch.available_products)

            # Check each product against lending criteria
            for product_id in sorted(product_ids):
                try:
                    product = MortgageProduct(product_id)
                except KeyError:
                    continue  # Skip unknown product IDs

                deposit = self.financial_state["savings"]

                # Run the affordability evaluator's lending check
                lending_result = self.financial_affordability_evaluator.check_lending_criteria(
                    agent_age=self.age,
                    agent_income=self.gross_salary,
                    deposit=deposit,
                    property_price=max_property_price,
                    mortgage_product=product
                )

                # Only keep products the agent is approved for
                if lending_result["passes"]:
                    viable_mortgages.append({
                        "bank": bank.bank_name,
                        "product": product,
                        "lending_result": lending_result
                    })

        # Sort cheapest monthly payment first
        return sorted(viable_mortgages, key=lambda x: x["lending_result"]["monthly_payment"])

    def assess_mortgage_suitability(self, mortgage_product, house_price, deposit_amount):
        """
        Run both lending criteria and affordability scoring for a single
        mortgage-property combination.

        :param mortgage_product: MortgageProduct object to evaluate.
        :param house_price: Price of the property.
        :param deposit_amount: Deposit the agent would put down.
        :return: Dict with "lending" and "affordability" sub-dicts.
        """
        # Check if the bank would approve this mortgage
        lending = self.financial_affordability_evaluator.check_lending_criteria(
            agent_age=self.age,
            agent_income=self.gross_salary,
            deposit=deposit_amount,
            property_price=house_price,
            mortgage_product=mortgage_product
        )

        net_monthly = self.financial_state["net_salary"] / 12
        expenses = self.financial_state["total_expenses_monthly"]

        # Score how comfortable the repayments would be
        affordability = self.financial_affordability_evaluator.calculate_affordability_score(
            monthly_income=net_monthly,
            monthly_payment=lending["monthly_payment"],
            monthly_expenses=expenses,
            current_savings=deposit_amount
        )

        return {
            "lending": lending,
            "affordability": affordability,
        }

    # --------------------------------------------------------------------
    #  AI DECISION MAKING
    # --------------------------------------------------------------------

    def _parse_llm_decision(self, response_text):
        """
        Extract structured fields from the LLM's free-text response.

        :param response_text: Raw string returned by the LLM.
        :return: Dict with decision, reasoning, timeline, and raw_response.
        """
        decision = "WAIT"       # Safe fallback if parsing fails
        reasoning = ""
        timeline = "12 months"

        # Scan each line for known prefixes
        for line in response_text.split("\n"):
            line = line.strip()
            if line.startswith("DECISION:"):
                decision = line.replace("DECISION:", "").strip()
            elif line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
            elif line.startswith("TIMELINE:"):
                timeline = line.replace("TIMELINE:", "").strip()
            elif line.startswith("NEXT_ACTION:"):
                timeline = line.replace("NEXT_ACTION:", "").strip()

        return {
            "decision": decision,
            "reasoning": reasoning,
            "timeline": timeline,
            "raw_response": response_text
        }

    def make_housing_decision(self):
        """
        Refresh the LLM agent with the latest state, ask it to make a
        housing decision, and parse the response.

        :return: Dict with decision, reasoning, timeline, and raw_response.
        """
        # Rebuild the agent so the system prompt reflects current finances
        self._setup_llm_agent()

        # Send the decision prompt to the LLM
        result = self.agent.invoke({
            "messages": [("user", "Its a new year. Review your situation and make a housing decision.")]
        })

        # Pull the text out of the last message
        response_text = result["messages"][-1].content
        decision = self._parse_llm_decision(response_text)

        return decision

    def _find_best_mortgage(self, property_price):
        """
        Search every bank for approved mortgages at the given price and
        return the one with the highest affordability comfort score.

        :param property_price: The property price to evaluate against.
        :return: Dict with mortgage details if approved, or None.
        """
        deposit = self.financial_state["savings"]
        net_monthly = self.financial_state["net_salary"] / 12
        expenses = self.financial_state["total_expenses_monthly"]

        best = None
        best_score = -1

        for bank in self.banks_list:
            # Gather unique product IDs from all branches
            product_ids = set()
            for branch in bank.get_all_branches():
                product_ids.update(branch.available_products)

            for product_id in sorted(product_ids):
                try:
                    product = MortgageProduct(product_id)
                except KeyError:
                    continue  # Skip unknown product IDs

                # Check if the agent passes lending criteria
                lending = self.financial_affordability_evaluator.check_lending_criteria(
                    agent_age=self.age,
                    agent_income=self.gross_salary,
                    deposit=deposit,
                    property_price=property_price,
                    mortgage_product=product
                )

                if not lending["passes"]:
                    continue  # Skip rejected products

                # Score how comfortable this mortgage would be
                affordability = self.financial_affordability_evaluator.calculate_affordability_score(
                    monthly_income=net_monthly,
                    monthly_payment=lending["monthly_payment"],
                    monthly_expenses=expenses,
                    current_savings=deposit
                )

                # Keep the product with the highest comfort score
                if affordability["score"] > best_score:
                    best_score = affordability["score"]
                    best = {
                        "monthly_payment": lending["monthly_payment"],
                        "product_name": product.name,
                        "bank": bank.bank_name,
                        "rate": product.rate,
                        "loan_amount": lending["loan_amount"],
                        "deposit_paid": deposit,
                        "term_years": 25,
                        "years_remaining": 25,
                        "property_price": property_price,
                        "affordability_score": affordability["score"],
                        "comfort_label": affordability["comfort_label"],
                    }

        return best

    # --------------------------------------------------------------------
    #  TIME PROGRESSION
    # --------------------------------------------------------------------

    def time_step(self, years_elapsed=1):
        """
        Advance the simulation by a number of years. Updates finances,
        preferences, asks the LLM to decide, and applies the outcome.

        :param years_elapsed: How many years to advance (default 1).
        :return: Dict summarising what happened this year.
        """
        # Snapshot the starting state for comparison later
        old_happiness = self.happiness_score
        old_savings = self.financial_state["savings"]

        # Age the resident
        self.age += years_elapsed

        # Recalculate finances for the new year
        self.update_financial_state()

        # Regenerate preferences (they shift with age and income)
        self.evaluate_housing_preferences()

        # -- Non-homeowner path: ask the LLM what to do --
        if self.mortgage_status != "active_mortgage":
            decision_result = self.make_housing_decision()
            decision = decision_result["decision"]

            if decision == "BUY":
                # Try to find an approved mortgage within budget
                max_price = self.housing_preferences.get("max_price", 0)
                best_mortgage = self._find_best_mortgage(max_price)

                if best_mortgage is not None:
                    # Assign the property (use search results if available)
                    if self.last_search_results:
                        self.current_property = self.last_search_results[0]
                    else:
                        self.current_property = f"Property @ £{best_mortgage['property_price']:,.0f}"

                    # Deduct the deposit from savings
                    self.financial_state["savings"] -= best_mortgage["deposit_paid"]

                    # Activate the mortgage
                    self.active_mortgage = best_mortgage
                    self.mortgage_status = "active_mortgage"

                    # Record the life event
                    self.life_events.append("bought_home")
                else:
                    # No mortgage was approved - fall back to saving
                    decision = "SAVE_FOR_DEPOSIT"

        # -- Homeowner path: tick down the mortgage --
        else:
            decision = "STAY"
            if self.active_mortgage:
                self.active_mortgage["years_remaining"] -= years_elapsed
                # Check if the mortgage is fully paid off
                if self.active_mortgage["years_remaining"] <= 0:
                    self.active_mortgage = None
                    self.life_events.append("paid_off_debt")

        # Recalculate happiness after all changes
        self.update_happiness()

        # Build and return the year summary
        return {
            "year_summary": f"{self.name} aged {self.age}, decided to {decision}",
            "age": self.age,
            "happiness_before": old_happiness,
            "happiness_after": self.happiness_score,
            "financial_change": self.financial_state["savings"] - old_savings,
            "housing_status": self.mortgage_status,
            "major_events": self.life_events[-years_elapsed:]
        }

    # --------------------------------------------------------------------
    #  HAPPINESS
    # --------------------------------------------------------------------

    def update_happiness(self):
        """
        Recalculate the agent's happiness score from housing status,
        financial security, recent life events, and age.

        :return: Dict with old_score, new_score, change, and breakdown.
        """
        old_score = self.happiness_score

        # Map current property ownership to a status string
        if self.current_property:
            housing_status = "owned"
        else:
            housing_status = "renting"

        # Financial security: 0-100 based on savings covering 6 months of expenses
        monthly_expenses = max(self.financial_state["total_expenses_monthly"], 1)
        savings = self.financial_state["savings"]
        financial_security = min(100, (savings / (monthly_expenses * 6)) * 100)

        # Only pass the last 3 events so old events fade over time
        recent_events = self.life_events[-3:]

        # Delegate the actual scoring to the evaluator
        result = self.happiness_evaluator.calculate_happiness_score(
            housing_status, financial_security, recent_events, self.age
        )

        # Persist the new score
        self.happiness_score = result["score"]

        return {
            "old_score": old_score,
            "new_score": result["score"],
            "change": result["score"] - old_score,
            "breakdown": result["breakdown"]
        }

    def apply_life_event(self, event_type, event_data=None):
        """
        Process a major life event. Known events update real financial or
        family state. Unknown events are estimated by the LLM. All events
        are recorded and fed into the happiness evaluator.

        :param event_type: Name of the event (e.g. "job_promotion", "birth_child").
        :param event_data: Optional dict with extra details like {"salary_increase": 5000}.
        :return: Dict with event, changes list, happiness_change, and new_happiness.
        """
        event_data = event_data or {}
        changes = []

        # Always record the event so the happiness evaluator can see it
        self.life_events.append(event_type)

        # -- Events that change real state --

        if event_type == "job_promotion":
            # Default raise is 10% of current salary
            raise_amount = event_data.get("salary_increase", self.gross_salary * 0.10)
            old_salary = self.gross_salary
            self.gross_salary += raise_amount
            # Rebuild the calculator with the new salary
            self.financial_calculator = SalaryCalculator(self.gross_salary)
            self.financial_state["gross_salary"] = self.gross_salary
            changes.append(f"Salary: £{old_salary:,.0f} -> £{self.gross_salary:,.0f}")

        elif event_type == "salary_increase":
            # Default raise is 5% of current salary
            raise_amount = event_data.get("salary_increase", self.gross_salary * 0.05)
            old_salary = self.gross_salary
            self.gross_salary += raise_amount
            self.financial_calculator = SalaryCalculator(self.gross_salary)
            self.financial_state["gross_salary"] = self.gross_salary
            changes.append(f"Salary: £{old_salary:,.0f} -> £{self.gross_salary:,.0f}")

        elif event_type == "job_loss":
            old_salary = self.gross_salary
            self.gross_salary = 0
            self.financial_calculator = SalaryCalculator(self.gross_salary)
            self.financial_state["gross_salary"] = self.gross_salary
            changes.append(f"Salary: £{old_salary:,.0f} -> £0 (job lost)")

        elif event_type == "marriage":
            self.family_size += 1
            changes.append(f"Family size: {self.family_size}")

        elif event_type == "birth_child":
            self.family_size += 1
            # Children cost roughly £250/month in extra expenses
            child_cost = event_data.get("monthly_cost", 250)
            self.expense_manager.add_expense("misc", f"child_{self.family_size}", child_cost, "monthly")
            changes.append(f"Family size: {self.family_size}, +£{child_cost}/mo expenses")

        elif event_type == "bought_home":
            # Usually handled by time_step, but can be triggered manually
            property_info = event_data.get("property", "Home")
            self.current_property = property_info
            self.mortgage_status = "active_mortgage"
            changes.append(f"Now owns: {property_info}")

        elif event_type == "divorce":
            if self.family_size > 1:
                self.family_size -= 1
            changes.append(f"Family size: {self.family_size}")

        elif event_type == "debt_increase":
            amount = event_data.get("amount", 5000)
            self.financial_state["debt"] += amount
            changes.append(f"Debt increased by £{amount:,.0f}")

        elif event_type == "property_repossessed":
            self.current_property = None
            self.active_mortgage = None
            self.mortgage_status = "no_mortgage"
            changes.append("Property repossessed - back to renting")

        else:
            # Unknown event - ask the LLM to estimate its happiness impact
            estimated_score = self.happiness_evaluator.estimate_unknown_event(
                event_type, self.llm
            )
            changes.append(
                f"Event '{event_type}' - LLM estimated impact: {estimated_score:+d}"
            )

        # Recalculate finances and happiness after the changes
        self.update_financial_state()
        happiness_result = self.update_happiness()

        return {
            "event": event_type,
            "changes": changes,
            "happiness_change": happiness_result["change"],
            "new_happiness": happiness_result["new_score"],
        }

    # --------------------------------------------------------------------
    #  UTILITY METHODS
    # --------------------------------------------------------------------

    def evaluate_user_property(self):
        """
        Let the user input a property they found online, then score it
        against preferences and check mortgage eligibility at every bank.
        Prints a full report to the console.

        :return: Dict with house, preference_score, mortgage_results,
                 and approved_count. Returns None if cancelled.
        """
        if self.housing_market is None:
            print("No housing market connected. Set agent.housing_market first.")
            return None

        # Prompt the user to enter house details
        house = self.housing_market.user_uploading_house()
        if house is None:
            print("Property entry cancelled.")
            return None

        # Make sure preferences exist before scoring
        if not self.housing_preferences:
            self.evaluate_housing_preferences()

        # Score how well this property matches the agent's preferences
        preference_score = self.housing_preference_evaluator.score_property(
            house, self.housing_preferences
        )
        print(f"\n Preference Match: {preference_score:.1f}/100")

        # Grab the financial snapshot for mortgage checks
        deposit = self.financial_state["savings"]
        net_monthly = self.financial_state["net_salary"] / 12
        expenses = self.financial_state["total_expenses_monthly"]

        print(f"\n Your deposit (current savings): £{deposit:,.0f}")
        print(f"   Net monthly income: £{net_monthly:,.0f}")
        print(f"   Monthly expenses: £{expenses:,.0f}\n")

        # Check every mortgage product at every bank
        mortgage_results = []
        for bank in self.banks_list:
            # Collect unique product IDs from all branches of this bank
            product_ids = set()
            for branch in bank.get_all_branches():
                product_ids.update(branch.available_products)

            for product_id in sorted(product_ids):
                try:
                    product = MortgageProduct(product_id)
                except KeyError:
                    continue  # Skip unknown product IDs

                # Run the lending criteria check
                lending = self.financial_affordability_evaluator.check_lending_criteria(
                    agent_age=self.age,
                    agent_income=self.gross_salary,
                    deposit=deposit,
                    property_price=house.price,
                    mortgage_product=product
                )

                # Score how comfortable the repayments would be
                affordability = self.financial_affordability_evaluator.calculate_affordability_score(
                    monthly_income=net_monthly,
                    monthly_payment=lending["monthly_payment"],
                    monthly_expenses=expenses,
                    current_savings=deposit
                )

                mortgage_results.append({
                    "bank": bank.bank_name,
                    "product": product,
                    "lending": lending,
                    "affordability": affordability,
                })

                # Print the result for this product
                status = "PASS" if lending["passes"] else "FAIL"
                print(f"  {status} {bank.bank_name} - {product.name} @ {product.rate}%")
                print(f"     Monthly: £{lending['monthly_payment']:,.0f} | "
                      f"LTV: {lending['ltv']*100:.0f}% | "
                      f"Comfort: {affordability['comfort_label']} ({affordability['score']}/100)")
                if not lending["passes"]:
                    print(f"     Rejected: {'; '.join(lending['failed_checks'])}")
                if lending["flags"]:
                    print(f"     Warnings: {'; '.join(lending['flags'])}")

        # Print summary
        approved = [m for m in mortgage_results if m["lending"]["passes"]]
        print(f"\n{'-'*50}")
        print(f"  Property: £{house.price:,.0f} {house.property_type} in {house.district}")
        print(f"  Preference score: {preference_score:.1f}/100")
        print(f"  Mortgages checked: {len(mortgage_results)}")
        print(f"  Approved: {len(approved)}")
        if approved:
            # Pick the mortgage with the best comfort score
            best = max(approved, key=lambda m: m["affordability"]["score"])
            print(f"  Best option: {best['bank']} - {best['product'].name} @ {best['product'].rate}%")
            print(f"    Monthly payment: £{best['lending']['monthly_payment']:,.0f}")
            print(f"    Comfort: {best['affordability']['comfort_label']}")
        else:
            print("  No mortgages approved. Consider saving more for a deposit.")
        print(f"{'-'*50}")

        return {
            "house": house,
            "preference_score": preference_score,
            "mortgage_results": mortgage_results,
            "approved_count": len(approved),
        }

    def get_status_summary(self):
        """
        Build a human-readable dict of the agent's full current state.

        :return: Dict with name, age, financial summary, housing info,
                 happiness score, and life events list.
        """
        summary = self.get_monthly_financial_summary()
        return {
            "name": self.name,
            "age": self.age,
            "financial": summary,
            "housing": {
                "status": self.mortgage_status,
                "property": str(self.current_property) if self.current_property else "None",
                "preferences": self.housing_preferences,
            },
            "happiness": self.happiness_score,
            "life_events": self.life_events,
        }

    def __repr__(self):
        """Return a short string representation of the agent."""
        return (f"ResidentAgent(id={self.agent_id}, name={self.name}, "
                f"age={self.age}, happiness={self.happiness_score:.1f})")
