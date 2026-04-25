import random
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from Environment.Mortgages.MortgageProduct import MortgageProduct
from Financial.Financial_Calculator import SalaryCalculator
from Financial.Debt_Manager import DebtManager
from Financial.Savings_Manager import SavingsGoalManager
from Algorithms.ResidentAlgorithms import (
    HousingPreferenceEvaluator,
    FinancialAffordabilityEvaluator,
    HappinessEvaluator
)
from Agents.agent_tools import build_agent_tools
from Agents.agent_prompts import RESIDENT_SYSTEM_PROMPT, HOMEOWNER_PROMPT
from Algorithms.Fault_Modelling import FaultModelling
from data.postcode_lookup import PostcodeLookup


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

    # Age-weighted probability tables for random life events each year.
    # Format: {event_name: {age_band: probability}}
    LIFE_EVENT_PROBABILITIES = {
        "salary_increase":  {"young": 0.15, "mid_life": 0.12, "later_life": 0.08},
        "job_promotion":    {"young": 0.08, "mid_life": 0.10, "later_life": 0.05},
        "job_loss":         {"young": 0.03, "mid_life": 0.02, "later_life": 0.04},
        "marriage":         {"young": 0.05, "mid_life": 0.08, "later_life": 0.02},
        "birth_child":      {"young": 0.03, "mid_life": 0.10, "later_life": 0.01},
        "divorce":          {"young": 0.01, "mid_life": 0.03, "later_life": 0.02},
        "debt_increase":    {"young": 0.05, "mid_life": 0.04, "later_life": 0.03},
        "bereavement":      {"young": 0.01, "mid_life": 0.02, "later_life": 0.05},
        "serious_illness":  {"young": 0.01, "mid_life": 0.02, "later_life": 0.04},
    }

    # Annual growth rates used during time_step
    SALARY_GROWTH_RATE = 0.025       # 2.5% average annual salary growth
    EXPENSE_INFLATION_RATE = 0.025   # 2.5% average annual expense inflation
    HOUSE_PRICE_GROWTH_RATE = 0.03   # 3% default annual house price growth (fallback)

    # Regional house price growth rates based on recent UK trends.
    # Source: ONS UK House Price Index regional annual change estimates.
    REGIONAL_HOUSE_PRICE_GROWTH = {
        "GREATER LONDON":          0.020,
        "SOUTH EAST":              0.025,
        "EAST OF ENGLAND":         0.025,
        "SOUTH WEST":              0.030,
        "WEST MIDLANDS":           0.035,
        "EAST MIDLANDS":           0.035,
        "NORTH WEST":              0.040,
        "YORKSHIRE AND THE HUMBER": 0.035,
        "NORTH EAST":              0.030,
        "MERSEYSIDE":              0.040,
        "COUNTY DURHAM":           0.030,
    }

    def __init__(self, agent_id, age, name, gross_salary, expense_manager,
                 financial_calculator=None, initial_savings=0,
                 housing_market=None, banks_list=None, family_size=1,
                 monthly_rent=800, student_loan_plans=None,
                 student_loan_balance=0, student_loan_graduation_year=None, savings_rate=0.5,
                 first_time_buyer=True, living_situation="solo", use_llm=True,
                 target_deposit_pct=0.10):
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
        :param monthly_rent: Monthly rent amount while not a homeowner (default 800).
        :param student_loan_plans: List of student loan plan strings (e.g. ["plan_2"]).
        :param student_loan_balance: Outstanding student loan balance (for tracking).
        :param student_loan_graduation_year: Year the agent graduates. Repayments start
               the April after this year. None means repayments are already active.
        :param savings_rate: Fraction of spare cash (after goal contributions) to save
               each year. 0.0 = save nothing, 1.0 = save everything. Default 0.5 (50%).
        """
        # -- Identity --
        self.agent_id = agent_id
        self.age = age
        self.name = name
        self.family_size = family_size
        self.is_married = family_size > 1  # Assume married if household > 1
        self.first_time_buyer = first_time_buyer

        # -- Financial system --
        self.gross_salary = gross_salary
        self.expense_manager = expense_manager
        # _base_rent is the full market rent for the agent's bedroom need.
        # The actual rent charged depends on living_situation (see effective_monthly_rent).
        self._base_rent = monthly_rent
        self.savings_rate = max(0.0, min(1.0, savings_rate))  # Clamp between 0 and 1
        self.student_loan_plans = student_loan_plans or []
        self.student_loan_balance = student_loan_balance  # Total owed (for info)
        self.student_loan_graduation_year = student_loan_graduation_year
        self.simulation_year = 2025  # Updated by time_step each year

        # -- Living situation --
        # "with_parents" : living at home, paying ~£200/month board
        # "shared"       : renting with a placeholder flatmate, paying 50% of 1-bed rate
        # "solo"         : renting alone at full _base_rent
        # "homeowner"    : mortgage (living_situation is set automatically on purchase)
        self.living_situation = living_situation
        # Track consecutive years in deficit — used to trigger automatic downgrade
        self._deficit_years = 0

        # -- LLM flag --
        # When False, all decisions use the deterministic rule-based fallback.
        # Set to False for bulk/batch runs to avoid Ollama calls entirely.
        self.use_llm = use_llm
        # Minimum deposit fraction the agent is willing to put down.
        # Agents avoid 5% (high-risk, expensive products) — 10% is the floor.
        self.target_deposit_pct = max(0.10, float(target_deposit_pct))

        # Use the provided calculator or create one from the salary
        if financial_calculator is not None:
            self.financial_calculator = financial_calculator
        else:
            self.financial_calculator = SalaryCalculator(
                gross_salary, student_loan_plans=self.student_loan_plans
            )

        # Debt and savings managers
        self.debt_manager = DebtManager()
        self.savings_manager = SavingsGoalManager()

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
        self.decision_history = []  # Stores past AI decisions for memory/context

        # -- Algorithm instances --
        self.housing_preference_evaluator = HousingPreferenceEvaluator()
        self.financial_affordability_evaluator = FinancialAffordabilityEvaluator()
        self.happiness_evaluator = HappinessEvaluator()

        # Run the initial financial calculation so net_salary etc. are populated
        self.update_financial_state()

        # Build the LLM agent with tools and system prompt (skip in non-LLM mode)
        if self.use_llm:
            self._setup_llm_agent()

    # --------------------------------------------------------------------
    #  INTERNAL HELPERS
    # --------------------------------------------------------------------

    def _estimate_council_tax_monthly(self, property_price):
        """
        Estimate monthly council tax based on property price band.
        Uses approximate England Band averages (2024/25).

        :param property_price: Price of the property.
        :return: Estimated monthly council tax.
        """
        # Approximate UK council tax bands by property value
        if property_price <= 40_000:
            annual = 1_200  # Band A
        elif property_price <= 52_000:
            annual = 1_400  # Band B
        elif property_price <= 68_000:
            annual = 1_600  # Band C
        elif property_price <= 88_000:
            annual = 1_800  # Band D
        elif property_price <= 120_000:
            annual = 2_100  # Band E
        elif property_price <= 160_000:
            annual = 2_400  # Band F
        elif property_price <= 320_000:
            annual = 2_800  # Band G
        else:
            annual = 3_400  # Band H
        return round(annual / 12, 2)

    def _apply_homeowner_expenses(self, property_price):
        """
        Add homeowner-specific expenses (council tax, home insurance,
        maintenance) when the agent buys a property.

        :param property_price: Price of the purchased property.
        """
        council_tax = self._estimate_council_tax_monthly(property_price)
        self.expense_manager.add_expense("housing", "council_tax", council_tax, "monthly")
        # Home insurance (~£30/month average)
        self.expense_manager.add_expense("insurance", "home_insurance", 30, "monthly")
        # Maintenance budget (~0.5% of property value per year)
        maintenance = round((property_price * 0.005) / 12, 2)
        self.expense_manager.add_expense("housing", "maintenance", maintenance, "monthly")

    def _remove_homeowner_expenses(self):
        """
        Remove homeowner-specific expenses when the agent sells their
        property and returns to renting.
        """
        for cat, name in [("housing", "council_tax"), ("insurance", "home_insurance"),
                          ("housing", "maintenance")]:
            if name in self.expense_manager.categories.get(cat, {}):
                del self.expense_manager.categories[cat][name]

    def _get_property_growth_rate(self):
        """
        Look up the annual house price growth rate for the agent's current
        property region. Falls back to the class default if the region
        is not in the lookup table.

        :return: Annual growth rate as a float (e.g. 0.035 for 3.5%).
        """
        if self.current_property and hasattr(self.current_property, "county"):
            county = self.current_property.county.upper().strip()
            return self.REGIONAL_HOUSE_PRICE_GROWTH.get(
                county, self.HOUSE_PRICE_GROWTH_RATE
            )
        return self.HOUSE_PRICE_GROWTH_RATE

    def _format_decision_memory(self, max_entries=5):
        """
        Format the last N decisions into a short string for inclusion in
        the LLM system prompt. Gives the AI context about what it has
        done in previous years/quarters.

        :param max_entries: Maximum number of past decisions to include.
        :return: Multi-line string summarising recent decisions, or "None yet".
        """
        if not self.decision_history:
            return "None yet — this is your first decision."
        recent = self.decision_history[-max_entries:]
        lines = []
        for entry in recent:
            year = entry.get("year", "?")
            month = entry.get("month", "")
            decision = entry.get("decision", "?")
            reason_snippet = entry.get("reasoning", "")[:80]
            if month:
                lines.append(f"  {year}/{month}: {decision} — {reason_snippet}")
            else:
                lines.append(f"  {year}: {decision} — {reason_snippet}")
        return "\n".join(lines)

    # ----------------------------------------------------------------
    #  Regional rent estimation
    # ----------------------------------------------------------------

    # Average monthly private rents by region (ONS 2024 estimates).
    REGIONAL_AVERAGE_RENTS = {
        "GREATER LONDON":          1_350,
        "SOUTH EAST":              1_050,
        "EAST OF ENGLAND":           950,
        "SOUTH WEST":                850,
        "WEST MIDLANDS":             750,
        "EAST MIDLANDS":             700,
        "NORTH WEST":                750,
        "YORKSHIRE AND THE HUMBER":  680,
        "NORTH EAST":                600,
        "MERSEYSIDE":                650,
        "COUNTY DURHAM":             550,
    }

    def estimate_regional_rent(self, county=None):
        """
        Estimate monthly rent based on the agent's target region.
        Used to set a realistic starting rent for agents whose preferred
        location is known.

        :param county: County/region string (e.g. "GREATER LONDON").
                       If None, uses housing preferences.
        :return: Estimated monthly rent.
        """
        if county is None:
            # Try to infer from housing preferences
            counties = self.housing_preferences.get("counties", [])
            if counties:
                county = counties[0]
        if county:
            return self.REGIONAL_AVERAGE_RENTS.get(
                county.upper().strip(), self.monthly_rent
            )
        return self.monthly_rent

    def _rebuild_calculator(self):
        """
        Recreate the SalaryCalculator from the current gross_salary,
        preserving student loan plans and any other persistent settings.
        Student loan repayments only activate once the simulation year
        passes the April after the graduation year.
        Call this whenever gross_salary changes instead of constructing
        SalaryCalculator directly.
        """
        # Only pass plans if repayments have started
        active_plans = self._active_student_loan_plans()
        self.financial_calculator = SalaryCalculator(
            self.gross_salary,
            student_loan_plans=active_plans,
        )

    def _active_student_loan_plans(self):
        """
        Return the student loan plans that are currently being repaid.
        Repayments start the April after graduation. If no graduation
        year is set, plans are always active.

        :return: List of active plan strings, or empty list.
        """
        if not self.student_loan_plans:
            return []
        if self.student_loan_graduation_year is None:
            # No graduation year set — assume already repaying
            return self.student_loan_plans
        # Repayments start the year after graduation
        repayment_start_year = self.student_loan_graduation_year + 1
        if self.simulation_year >= repayment_start_year:
            return self.student_loan_plans
        return []

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
        max_price = self.housing_preferences.get("max_price", self.gross_salary * 4.5)
        min_deposit_needed = max_price * 0.05  # 5% deposit (FTB products)
        deposit_readiness = (self.financial_state["savings"] / min_deposit_needed * 100) if min_deposit_needed > 0 else 0

        system_prompt = RESIDENT_SYSTEM_PROMPT.format(
            age=self.age,
            name=self.name,
            gross_salary=self.gross_salary,
            net_monthly=self.financial_state["net_salary"] / 12,
            available_monthly=self.monthly_available_funds,
            savings=self.financial_state["savings"],
            housing_status=self.mortgage_status,
            happiness=self.happiness_score,
            family_size=self.family_size,
            is_married="Yes" if self.is_married else "No",
            total_debt=self.financial_state.get("debt", 0),
            monthly_debt=self.debt_manager.total_monthly_payments(),
            student_loan_info=", ".join(self.student_loan_plans) if self.student_loan_plans else "None",
            savings_rate=self.savings_rate,
            first_time_buyer="Yes" if self.first_time_buyer else "No",
            decision_memory=self._format_decision_memory(),
            max_affordable_price=max_price,
            min_deposit_needed=min_deposit_needed,
            deposit_readiness=deposit_readiness,
        )

        # Wire the LLM, tools, and prompt together into a runnable agent
        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=system_prompt,
        )

    # --------------------------------------------------------------------
    #  LIVING SITUATION
    # --------------------------------------------------------------------

    # Board paid when living with parents (contribution to household costs)
    PARENTS_BOARD = 200

    @property
    def monthly_rent(self):
        """Effective monthly rent based on current living situation."""
        return self.effective_monthly_rent

    @monthly_rent.setter
    def monthly_rent(self, value):
        """Allow external code to update the base rent directly."""
        self._base_rent = value

    @property
    def effective_monthly_rent(self):
        """
        Derive the actual rent charged from living_situation:
          with_parents -> £200/month board
          shared       -> 50% of the standard 1-bed rate (£425 at £850 base)
          solo         -> full _base_rent (bedroom-appropriate)
          homeowner    -> 0 (mortgage payment handled separately)
        """
        if self.active_mortgage is not None or self.living_situation == "homeowner":
            return 0
        if self.living_situation == "with_parents":
            return self.PARENTS_BOARD
        if self.living_situation == "shared":
            # Split the 1-bed rate (first entry in MONTHLY_RENT-style lookup).
            # Use _base_rent capped at the 1-bed rate to avoid penalising agents
            # who originally needed a bigger flat but are now in shared housing.
            one_bed_rate = 850  # matches MONTHLY_RENT[1] in synthetic_agents.py
            return min(self._base_rent, one_bed_rate) * 0.5
        # "solo" or anything else
        return self._base_rent

    def _evaluate_living_situation(self):
        """
        Annually reassess whether the agent can afford their current living
        situation and automatically move them if not.

        Rules:
          - Homeowners are never moved (mortgage locked in).
          - Partners always stay in "solo" (they split rent already).
          - If running a deficit for 2+ consecutive years → downgrade one step:
              solo → shared → with_parents
          - If surplus is comfortable (>£200/month) and situation is not solo
            and age >= 23 → upgrade one step toward solo.

        :return: The transition event string if a move happened, else None.
        """
        # Homeowners don't rent — nothing to evaluate
        if self.active_mortgage is not None or self.living_situation == "homeowner":
            return None

        # Partnered agents already have rent split — keep them at solo
        if self.is_married and self.living_situation != "solo":
            old = self.living_situation
            self.living_situation = "solo"
            return f"moved_to_solo_after_partnering (was {old})"

        current_available = self.monthly_available_funds

        # --- Downgrade path: struggling financially ---
        if current_available < -50:
            self._deficit_years += 1
        else:
            self._deficit_years = max(0, self._deficit_years - 1)

        if self._deficit_years >= 2:
            if self.living_situation == "solo":
                self.living_situation = "shared"
                self._deficit_years = 0
                return "moved_to_shared_housing"
            elif self.living_situation == "shared":
                self.living_situation = "with_parents"
                self._deficit_years = 0
                return "moved_back_to_parents"

        # --- Upgrade path: doing well, ready to move out / live alone ---
        if current_available > 200 and self.living_situation != "solo":
            if self.living_situation == "with_parents" and self.age >= 21:
                self.living_situation = "shared"
                return "moved_out_to_shared_housing"
            elif self.living_situation == "shared" and self.age >= 23:
                # Check they can ACTUALLY afford solo rent before moving
                solo_cost = self._base_rent - self.effective_monthly_rent
                if current_available - solo_cost > 50:
                    self.living_situation = "solo"
                    return "moved_to_solo_renting"

        return None

    # --------------------------------------------------------------------
    #  FINANCIAL MANAGEMENT
    # --------------------------------------------------------------------

    def update_financial_state(self):
        """
        Recalculate net pay, expenses, available funds, Includes rent (for renters), mortgage (for homeowners),
        and debt repayments. Called on init and once per time_step.

        :return: The updated financial_state dict.
        """
        # Get annual net pay after tax and NI
        pay_result = self.financial_calculator.calculate_net_pay()
        net_annual = pay_result["net_pay"]

        # Sum all monthly expenses from the expense manager
        total_monthly_expenses = self.expense_manager.calculate_total_monthly()

        # Add debt repayments to monthly outgoings
        debt_payments = self.debt_manager.total_monthly_payments()
        total_monthly_expenses += debt_payments

        # Work out what is left each month after expenses
        net_monthly = net_annual / 12
        available = net_monthly - total_monthly_expenses

        # Subtract housing cost: mortgage for homeowners, rent for renters
        if self.active_mortgage is not None:
            available -= self.active_mortgage.get("monthly_payment", 0)
        else:
            available -= self.monthly_rent  # Renters pay rent

        # Sync debt total from the debt manager
        self.financial_state["debt"] = sum(
            d["balance"] for d in self.debt_manager.debts.values()
        )

        # Persist the calculated values
        self.financial_state["net_salary"] = net_annual
        self.financial_state["total_expenses_monthly"] = total_monthly_expenses
        self.monthly_available_funds = available

        return self.financial_state

    def accumulate_annual_savings(self):
        """
        Run the annual savings cycle:
          1. Contribute to any active savings goals first
          2. Save savings_rate % of the remaining spare cash
          3. The rest is untracked lifestyle spending (gone)

        Spare cash = monthly_available_funds * 12.
        monthly_available_funds is the amount LEFT each month AFTER
        net pay minus ALL expenses, rent/mortgage, and debt repayments.
        It is NOT net salary - it is the genuinely disposable surplus.

        If the agent is in the red (negative spare cash), savings are
        drained first. If savings hit zero and they are still short,
        the shortfall is added as an overdraft debt at 19.9% APR so
        the agent faces a real financial consequence.

        :return: Dict with goal_contributions, general_saved,
                 lifestyle_spent, total_change, and interest_earned.
        """
        # monthly_available_funds = net_monthly - expenses - rent/mortgage
        # Multiply by 12 to get the annual surplus (or deficit)
        available = self.monthly_available_funds   # monthly spare cash
        annual_spare = available * 12              # annualised

        # -- Deficit path: agent is spending more than they earn --
        if annual_spare <= 0:
            deficit = abs(annual_spare)

            if self.financial_state["savings"] >= deficit:
                # Drain savings to cover the shortfall
                self.financial_state["savings"] -= deficit
            else:
                # Savings are wiped out; the remainder becomes overdraft debt
                remaining_deficit = deficit - self.financial_state["savings"]
                self.financial_state["savings"] = 0

                # Add an overdraft entry to DebtManager so interest accrues
                overdraft_label = "overdraft"
                if overdraft_label in self.debt_manager.debts:
                    # Increase existing overdraft balance
                    self.debt_manager.debts[overdraft_label]["balance"] += remaining_deficit
                else:
                    # Create a new overdraft debt at 19.9% APR
                    self.debt_manager.add_debt(
                        overdraft_label,
                        balance=remaining_deficit,
                        apr=0.199,
                        min_payment=max(25, remaining_deficit * 0.02),
                    )

            return {
                "goal_contributions": 0,
                "general_saved": 0,
                "lifestyle_spent": 0,
                "total_change": -deficit,
                "interest_earned": 0,
            }

        # -- Surplus path: agent has money left over --

        # Step 1: Pay savings goal contributions first (capped at spare cash)
        goal_contributions = 0
        if self.savings_manager.has_goals():
            goal_contributions = self.savings_manager.contribute_annual()
            # Do not let goal contributions exceed what is actually available
            goal_contributions = min(goal_contributions, annual_spare)

        remaining = annual_spare - goal_contributions

        # Step 2: Save savings_rate % of what is left over.
        # savings_rate is the fraction of SPARE CASH (after goals) that goes
        # to savings.  E.g. 0.20 = save 20 pence of every spare pound.
        general_saved = remaining * self.savings_rate

        # Step 3: The rest is lifestyle spending (not tracked)
        lifestyle_spent = remaining - general_saved

        # Apply to the savings balance
        total_saved = goal_contributions + general_saved
        self.financial_state["savings"] += total_saved

        # Apply annual interest on the PRE-EXISTING balance only
        # (interest is earned on money that was there at the start of the year)
        savings_interest_rate = 0.035  # 3.5% easy-access savings rate (2024/25)
        pre_existing_balance = self.financial_state["savings"] - total_saved
        interest = max(0, pre_existing_balance) * savings_interest_rate
        self.financial_state["savings"] += interest

        return {
            "goal_contributions": round(goal_contributions, 2),
            "general_saved": round(general_saved, 2),
            "lifestyle_spent": round(lifestyle_spent, 2),
            "total_change": round(total_saved, 2),
            "interest_earned": round(interest, 2),
        }


    def accumulate_monthly_savings(self):
        """
        Run ONE month of the savings cycle:
          1. Contribute to any active savings goals (1 month's worth)
          2. Save savings_rate % of the remaining spare cash
          3. The rest is untracked lifestyle spending (gone)

        Spare cash = monthly_available_funds (net monthly AFTER all
        expenses, rent/mortgage, and debt repayments).

        If the agent is in the red, savings are drained first. If savings
        reach zero, the remaining shortfall becomes overdraft debt.

        :return: Dict with goal_contributions, general_saved,
                 lifestyle_spent, total_change, and interest_earned.
        """
        available = self.monthly_available_funds  # monthly spare cash

        # -- Deficit path --
        if available <= 0:
            deficit = abs(available)

            if self.financial_state["savings"] >= deficit:
                self.financial_state["savings"] -= deficit
            else:
                remaining_deficit = deficit - self.financial_state["savings"]
                self.financial_state["savings"] = 0

                # Add to overdraft debt
                overdraft_label = "overdraft"
                if overdraft_label in self.debt_manager.debts:
                    self.debt_manager.debts[overdraft_label]["balance"] += remaining_deficit
                else:
                    self.debt_manager.add_debt(
                        overdraft_label,
                        balance=remaining_deficit,
                        apr=0.199,
                        min_payment=max(25, remaining_deficit * 0.02),
                    )

            return {
                "goal_contributions": 0,
                "general_saved": 0,
                "lifestyle_spent": 0,
                "total_change": round(-deficit, 2),
                "interest_earned": 0,
            }

        # -- Surplus path --

        # Step 1: Pay savings goal contributions (1 month, capped at spare cash)
        goal_contributions = 0
        if self.savings_manager.has_goals():
            goal_contributions = self.savings_manager.contribute_monthly()
            goal_contributions = min(goal_contributions, available)

        remaining = available - goal_contributions

        # Step 2: Save savings_rate % of what is left
        general_saved = remaining * self.savings_rate

        # Step 3: The rest is lifestyle spending (gone)
        lifestyle_spent = remaining - general_saved

        # Apply to the savings balance
        total_saved = goal_contributions + general_saved
        self.financial_state["savings"] += total_saved

        # Apply monthly interest on the pre-existing savings balance
        savings_annual_rate = 0.035   # 3.5% easy-access savings rate (2024/25)
        monthly_rate = savings_annual_rate / 12
        pre_existing_balance = self.financial_state["savings"] - total_saved
        interest = max(0, pre_existing_balance) * monthly_rate
        self.financial_state["savings"] += interest

        return {
            "goal_contributions": round(goal_contributions, 2),
            "general_saved": round(general_saved, 2),
            "lifestyle_spent": round(lifestyle_spent, 2),
            "total_change": round(total_saved, 2),
            "interest_earned": round(interest, 2),
        }

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
                    mortgage_product=product,
                    existing_debts=self.debt_manager.total_monthly_payments()
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
            mortgage_product=mortgage_product,
            existing_debts=self.debt_manager.total_monthly_payments()
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

    def _extract_tool_trace(self, messages):
        """
        Walk through the LangChain message list and pull out every tool
        call the LLM made along with the tool's response. This lets us
        show the user exactly what the AI did behind the scenes.

        :param messages: List of BaseMessage objects from agent.invoke().
        :return: List of dicts with 'tool', 'input', and 'output' keys.
        """
        trace = []
        # Messages follow the pattern: AIMessage (with tool_calls) -> ToolMessage (with content)
        for msg in messages:
            # AIMessage with tool_calls attribute
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    trace.append({
                        "tool": tc.get("name", "unknown"),
                        "input": tc.get("args", {}),
                        "output": None,  # Filled in by the next ToolMessage
                    })
            # ToolMessage contains the response from the tool
            if hasattr(msg, "type") and msg.type == "tool" and trace:
                # Attach the output to the most recent trace entry missing one
                for entry in reversed(trace):
                    if entry["output"] is None:
                        entry["output"] = msg.content
                        break
        return trace

    def _parse_llm_decision(self, response_text):
        """
        Extract structured fields from the LLM's free-text response.
        Uses flexible matching to handle markdown, bullets, and varied
        formatting from small LLMs.

        :param response_text: Raw string returned by the LLM.
        :return: Dict with decision, reasoning, timeline, and raw_response.
        """
        decision = ""
        reasoning = ""
        timeline = "12 months"

        # Strip common markdown formatting that small LLMs add
        clean = response_text.replace("**", "").replace("*", "").replace("##", "")

        # Scan each line for known prefixes (case-insensitive, allow leading punctuation)
        for line in clean.split("\n"):
            stripped = line.strip().lstrip("-•● ")
            lower = stripped.lower()
            if lower.startswith("decision:"):
                decision = stripped.split(":", 1)[1].strip()
            elif lower.startswith("reasoning:"):
                reasoning = stripped.split(":", 1)[1].strip()
            elif lower.startswith("timeline:"):
                timeline = stripped.split(":", 1)[1].strip()
            elif lower.startswith("next_action:") or lower.startswith("next action:"):
                timeline = stripped.split(":", 1)[1].strip()

        # ── Flexible keyword scan ──
        # If structured parsing didn't find a decision, scan the full
        # response for the decision keywords so small-LLM formatting
        # variations (e.g. "I'll BUY", "My decision is to BUY") still work.
        valid_decisions = ["BUY", "SAVE_FOR_DEPOSIT", "WAIT", "CONTINUE_SEARCHING"]
        if decision:
            # Normalise whatever the LLM wrote into the canonical keyword
            upper = decision.upper().strip().strip('"').strip("'")
            matched = None
            for vd in valid_decisions:
                if vd in upper:
                    matched = vd
                    break
            decision = matched or decision.upper()
        else:
            # Full-text scan: look for the FIRST valid keyword in the response
            upper_full = clean.upper()
            for vd in valid_decisions:
                if vd in upper_full:
                    decision = vd
                    break

        # -- Deterministic fallback --
        # If the LLM still didn't produce a recognised keyword, use a
        # rule-based heuristic so agents are not stuck on WAIT forever.
        if decision not in valid_decisions:
            decision = self._deterministic_housing_decision()

        # Try to grab reasoning from the response if structured parsing missed it
        if not reasoning:
            # Take the longest line as a rough proxy for the reasoning
            lines = [l.strip() for l in clean.split("\n") if len(l.strip()) > 30]
            if lines:
                reasoning = max(lines, key=len)[:200]

        return {
            "decision": decision,
            "reasoning": reasoning,
            "timeline": timeline,
            "raw_response": response_text
        }

    def _deterministic_housing_decision(self):
        """
        Rule-based fallback when the LLM fails to produce a clear decision.
        Uses the agent's actual financial position to decide what makes sense.

        :return: One of "BUY", "SAVE_FOR_DEPOSIT", "WAIT".
        """
        savings = self.financial_state["savings"]
        max_price = self.housing_preferences.get("max_price", self.gross_salary * 4.5)

        # What is the cheapest property the agent could consider?
        min_price = max(150_000, self.housing_preferences.get("min_price", self.gross_salary * 2.0))

        # Check deposit readiness against the cheapest viable price.
        # Agents avoid 5% deposits (expensive, risky) — use their target (min 10%).
        min_deposit_pct = self.target_deposit_pct  # already clamped to >= 0.10
        deposit_needed = min_price * min_deposit_pct
        has_target_deposit = savings >= deposit_needed

        # Also check the income multiple: loan must be ≤ 4.5× salary
        max_borrowable = self.gross_salary * 4.5
        loan_at_min = min_price - savings
        income_ok = loan_at_min <= max_borrowable if loan_at_min > 0 else True

        # Also need enough left over after deposit + transaction costs (~£4k + SDLT)
        estimated_costs = savings * 0.05 + 4_000  # rough upfront costs
        can_cover_costs = savings > deposit_needed + estimated_costs

        if has_target_deposit and income_ok and can_cover_costs and self.monthly_available_funds > 0:
            return "BUY"
        elif savings > deposit_needed * 0.4:
            return "SAVE_FOR_DEPOSIT"
        else:
            return "SAVE_FOR_DEPOSIT"

    def make_housing_decision(self):
        """
        Ask the LLM (or rule-based fallback) to make a housing decision.

        When use_llm=False the deterministic rule-based logic is used directly,
        making bulk/batch runs near-instant with no Ollama calls.

        :return: Dict with decision, reasoning, timeline, raw_response, tool_trace.
        """
        if not self.use_llm:
            decision_str = self._deterministic_housing_decision()
            return {
                "decision": decision_str,
                "reasoning": "rule-based (LLM disabled)",
                "timeline": "",
                "raw_response": "",
                "tool_trace": [],
            }

        # Rebuild the agent so the system prompt reflects current finances
        self._setup_llm_agent()

        # Send the decision prompt to the LLM
        result = self.agent.invoke({
            "messages": [("user", "Its a new year. Review your situation and make a housing decision.")]
        })

        # Extract the tool trace from the full message history
        all_messages = result.get("messages", [])
        tool_trace = self._extract_tool_trace(all_messages)

        # Pull the text out of the last message
        response_text = all_messages[-1].content if all_messages else ""
        decision = self._parse_llm_decision(response_text)

        # Attach the tool trace and raw messages so the simulation can display them
        decision["tool_trace"] = tool_trace

        # Record this decision in the agent's memory for future context
        self.decision_history.append({
            "year": self.simulation_year,
            "decision": decision["decision"],
            "reasoning": decision["reasoning"],
        })

        return decision

    def _find_best_mortgage(self, max_property_price):
        """
        Search every bank for approved mortgages, trying multiple price
        points from the agent's max budget down to the lowest viable
        price. This ensures the agent can still buy a cheaper property
        when their deposit is too small for the most expensive option.

        :param max_property_price: The highest property price to try.
        :return: Dict with mortgage details if approved, or None.
        """
        savings = self.financial_state["savings"]
        net_monthly = self.financial_state["net_salary"] / 12
        # After buying the agent no longer pays rent, so subtract current rent
        # from expenses when evaluating post-purchase affordability.
        current_rent = self.monthly_rent if self.mortgage_status != "active_mortgage" else 0
        expenses = max(0, self.financial_state["total_expenses_monthly"] - current_rent)

        # Reserve funds for transaction costs (SDLT + solicitor + moving)
        # so the agent doesn't go deeply negative after buying.
        transaction_reserve = 5_000
        deposit = max(0, savings - transaction_reserve)

        min_price = max(150_000, self.housing_preferences.get("min_price", self.gross_salary * 2.0))

        # ------------------------------------------------------------------
        # Build candidate list from real market properties where possible.
        # Agents browse a limited shortlist (PROPERTY_SEARCH_SAMPLE) — they
        # don't have access to every listing in the country at once.
        # ------------------------------------------------------------------
        sampled_houses = []
        if self.housing_market is not None and self.housing_market.houses:
            preferred_types = self.housing_preferences.get("preferred_property_types")
            preferred_counties = self.housing_preferences.get("counties")
            sampled_houses = self.housing_market.sample_properties(
                n=self.PROPERTY_SEARCH_SAMPLE,
                min_price=min_price,
                max_price=max_property_price,
                property_types=preferred_types,
                counties=preferred_counties,
            )
            # If preferred filters yield nothing, widen to any matching price range
            if not sampled_houses:
                sampled_houses = self.housing_market.sample_properties(
                    n=self.PROPERTY_SEARCH_SAMPLE,
                    min_price=min_price,
                    max_price=max_property_price,
                )

        # Extract prices from real houses, or fall back to synthetic price points
        if sampled_houses:
            candidate_prices = sorted(
                {round(h.price, -3) for h in sampled_houses},
                reverse=True
            )
            # Store so the BUY path can assign current_property
            self.last_search_results = sampled_houses
        else:
            # Fallback: generate synthetic price candidates from deposit/income
            # (used when no Land Registry data is loaded)
            self.last_search_results = []
            candidate_set = {round(max_property_price, -3)}
            min_dep_pct = self.target_deposit_pct
            for pct in (min_dep_pct, 0.10, 0.15, 0.20, 0.25):
                if pct >= min_dep_pct and deposit > 0:
                    price_at_pct = deposit / pct
                    if min_price <= price_at_pct <= max_property_price:
                        candidate_set.add(round(price_at_pct, -3))
            candidate_set.add(round(min_price, -3))
            income_max = self.gross_salary * 4.5 + deposit
            if min_price <= income_max <= max_property_price:
                candidate_set.add(round(income_max, -3))
            candidate_prices = sorted(candidate_set, reverse=True)

        best = None
        best_house = None

        for idx, property_price in enumerate(candidate_prices):
            if property_price < min_price or property_price <= 0:
                continue

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
                        mortgage_product=product,
                        existing_debts=self.debt_manager.total_monthly_payments()
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

                    # Skip unaffordable mortgages (score < 20)
                    if affordability["score"] < 20:
                        continue

                    # Prefer the HIGHEST property price that is still
                    # affordable, then break ties by comfort score.
                    candidate_key = (property_price, affordability["score"])
                    best_key = (best["property_price"], best["affordability_score"]) if best else (-1, -1)

                    if candidate_key > best_key:
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
                        # Track the matching house object (if from real data)
                        if sampled_houses and idx < len(sampled_houses):
                            best_house = sampled_houses[idx]

        # Make sure current_property points to the winning house object
        if best is not None and best_house is not None:
            self.last_search_results = [best_house] + [
                h for h in self.last_search_results if h is not best_house
            ]

        return best

    # --------------------------------------------------------------------
    #  TIME PROGRESSION
    # --------------------------------------------------------------------

    # Months on which the AI makes a housing decision (default: quarterly)
    AI_DECISION_MONTHS = [1, 4, 7, 10]

    # How many properties an agent can view per search — realistic browsing limit.
    # UK FTBs typically view ~10-20 properties before buying.
    PROPERTY_SEARCH_SAMPLE = 20

    def monthly_step(self, month, sim_year):
        """
        Advance the simulation by ONE month. Yearly events (age, salary
        growth, inflation, life events) only trigger on month 1. Financial
        updates and savings accumulate every month. The AI decides on the
        months listed in AI_DECISION_MONTHS.

        :param month: Month number (1-12).
        :param sim_year: The calendar year of this step.
        :return: Dict summarising what happened this month.
        """
        MONTH_NAMES = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]
        month_label = MONTH_NAMES[month - 1]

        old_happiness = self.happiness_score
        old_savings = self.financial_state["savings"]
        old_debt = self.financial_state.get("debt", 0)
        triggered_events = []

        # ---- YEARLY EVENTS (month 1 only) ----
        if month == 1:
            # Age the resident once per year
            self.age += 1
            self.simulation_year = sim_year

            # Check if student loan repayments should activate
            if (self.student_loan_plans
                    and self.student_loan_graduation_year is not None
                    and self.simulation_year == self.student_loan_graduation_year + 1):
                self._rebuild_calculator()
                triggered_events.append("student_loan_repayments_started")

            # Apply salary growth (annual, applied once in January)
            if self.gross_salary > 0:
                growth = self.SALARY_GROWTH_RATE + random.uniform(-0.01, 0.01)
                self.gross_salary *= (1 + growth)
                self._rebuild_calculator()
                self.financial_state["gross_salary"] = self.gross_salary

            # Apply expense inflation (annual, applied once in January)
            inflation = self.EXPENSE_INFLATION_RATE
            for cat in self.expense_manager.categories.values():
                for expense_data in cat.values():
                    expense_data["amount"] *= (1 + inflation)

            # Apply rent inflation for renters
            if self.mortgage_status != "active_mortgage":
                self.monthly_rent *= (1 + inflation)

            # Generate random life events (once per year)
            triggered_events += self._generate_life_events()
            for event in triggered_events:
                self.apply_life_event(event)

            # Evaluate living situation once per year — may downgrade or upgrade
            situation_event = self._evaluate_living_situation()
            if situation_event:
                triggered_events.append(situation_event)
                self.life_events.append(situation_event)

            # Regenerate preferences (they shift with age and income)
            self.evaluate_housing_preferences()

            # Apply property value growth for homeowners (once per year)
            if self.active_mortgage:
                growth_rate = self._get_property_growth_rate()
                self.active_mortgage["property_price"] *= (1 + growth_rate)

        # ---- EVERY MONTH ----
        # Accrue debt interest and apply payments
        debt_results = self.debt_manager.accrue_monthly()
        for dname, dinfo in debt_results.items():
            if dinfo["paid_off"]:
                self.life_events.append(f"paid_off_{dname}")

        # Recalculate finances
        self.update_financial_state()

        # Deduct student loan repayments from balance (if active)
        if self._active_student_loan_plans() and self.student_loan_balance > 0:
            monthly_sl = self.financial_calculator.calculate_student_loan()["total"] * 52 / 12
            self.student_loan_balance = max(0, self.student_loan_balance - monthly_sl)
            # Write-off check: Plan 2 = 30 years after graduation
            if (self.student_loan_graduation_year
                    and sim_year - self.student_loan_graduation_year >= 30):
                self.student_loan_balance = 0
                triggered_events.append("student_loan_written_off")

        # Accumulate one month of savings
        savings_result = self.accumulate_monthly_savings()

        # ---- AI DECISION (on configured months) ----
        decision = None
        decision_result = {}

        if month in self.AI_DECISION_MONTHS:
            if self.mortgage_status != "active_mortgage":
                decision_result = self.make_housing_decision()
                decision = decision_result["decision"]

                if decision == "BUY":
                    max_price = self.housing_preferences.get("max_price", 0)
                    best_mortgage = self._find_best_mortgage(max_price)

                    if best_mortgage is not None:
                        if self.last_search_results:
                            self.current_property = self.last_search_results[0]
                        else:
                            self.current_property = f"Property @ £{best_mortgage['property_price']:,.0f}"

                        self.financial_state["savings"] -= best_mortgage["deposit_paid"]
                        # Deduct SDLT from savings
                        from Financial.Financial_Calculator import calculate_sdlt
                        sdlt = calculate_sdlt(best_mortgage["property_price"], first_time_buyer=self.first_time_buyer)
                        self.financial_state["savings"] -= sdlt["total_sdlt"]
                        # Deduct solicitor, survey, and moving costs
                        transaction_costs = 4_000  # ~£3k-5k typical UK purchase costs
                        self.financial_state["savings"] -= transaction_costs

                        self.active_mortgage = best_mortgage
                        self.mortgage_status = "active_mortgage"
                        self.first_time_buyer = False  # No longer a first-time buyer
                        self._apply_homeowner_expenses(best_mortgage["property_price"])
                        self.life_events.append("bought_home")

                        # Initialize fault modelling for the property
                        lookup = PostcodeLookup()
                        lsoa = lookup.get_lsoa(self.current_property.postcode)
                        self.current_property.fault_model = FaultModelling(self.current_property, lsoa)
            else:
                decision_result = self._make_homeowner_decision()
                decision = decision_result["decision"]

                if self.active_mortgage:
                    if decision == "OVERPAY_MORTGAGE":
                        overpay = self.financial_state["savings"] * 0.5
                        if overpay > 0:
                            self.active_mortgage["loan_amount"] = max(
                                0, self.active_mortgage["loan_amount"] - overpay
                            )
                            self.financial_state["savings"] -= overpay
                            if self.active_mortgage["loan_amount"] <= 0:
                                self.active_mortgage["years_remaining"] = 0

                    if decision == "CONSIDER_MOVING":
                        self.current_property = None
                        self.active_mortgage = None
                        self.mortgage_status = "no_mortgage"
                        self._remove_homeowner_expenses()
                        self.life_events.append("property_sold")

        # Tick down mortgage by 1 month (1/12 of a year)
        if self.active_mortgage:
            self.active_mortgage["years_remaining"] -= 1 / 12
            if self.active_mortgage["years_remaining"] <= 0:
                self.active_mortgage = None
                self.life_events.append("paid_off_mortgage")

        # Recalculate happiness
        self.update_happiness()

        # Calculate key affordability metrics for logging
        max_price = self.housing_preferences.get("max_price", self.gross_salary * 4.5)
        deposit_needed = max_price * 0.10  # 10% deposit minimum
        deposit_readiness = (self.financial_state["savings"] / deposit_needed * 100) if deposit_needed > 0 else 0
        affordability_ratio = max_price / self.gross_salary if self.gross_salary > 0 else 0

        # Build the month summary
        return {
            "month": month,
            "month_label": month_label,
            "sim_year": sim_year,
            "decision": decision,
            "age": self.age,
            "gross_salary": round(self.gross_salary, 0),
            "net_monthly": round(self.financial_state["net_salary"] / 12, 0),
            "monthly_expenses": round(self.financial_state.get("total_expenses_monthly", 0), 0),
            "monthly_rent": round(
                self.active_mortgage.get("monthly_payment", 0) if self.active_mortgage
                else self.monthly_rent, 0),
            "savings": round(self.financial_state["savings"], 0),
            "monthly_available": round(self.monthly_available_funds, 0),
            "happiness_before": old_happiness,
            "happiness_after": self.happiness_score,
            "financial_change": round(
                (self.financial_state["savings"] - old_savings)
                - (self.financial_state.get("debt", 0) - old_debt), 0),
            "total_debt": round(self.financial_state.get("debt", 0), 0),
            "housing_status": self.mortgage_status,
            "living_situation": self.living_situation,
            "life_events_this_month": triggered_events if month == 1 else [],
            "major_events": self.life_events[-3:],
            "savings_breakdown": savings_result,
            # -- Affordability metrics --
            "affordability_ratio": round(affordability_ratio, 2),
            "deposit_readiness_pct": round(deposit_readiness, 1),
            # AI transparency fields (only populated on AI decision months)
            "ai_reasoning": decision_result.get("reasoning", ""),
            "ai_timeline": decision_result.get("timeline", ""),
            "ai_raw_response": decision_result.get("raw_response", ""),
            "ai_tool_trace": decision_result.get("tool_trace", []),
        }

    def time_step(self, years_elapsed=1):
        """
        Advance the simulation by a number of years. Applies inflation,
        salary growth, random life events, updates finances, asks the
        LLM to decide, and applies the outcome.

        :param years_elapsed: How many years to advance (default 1).
        :return: Dict summarising what happened this year.
        """
        # Snapshot the starting state for comparison later
        old_happiness = self.happiness_score
        old_savings = self.financial_state["savings"]
        old_debt = self.financial_state.get("debt", 0)
        auto_events = []  # Events generated by the simulation (not the user)

        # Age the resident
        self.age += years_elapsed
        self.simulation_year += years_elapsed

        # -- Check if student loan repayments should activate this year --
        if (self.student_loan_plans
                and self.student_loan_graduation_year is not None
                and self.simulation_year == self.student_loan_graduation_year + 1):
            self._rebuild_calculator()  # Plans will now be active
            auto_events.append("student_loan_repayments_started")

        # -- Apply salary growth (2.5% average, +/- some noise) --
        if self.gross_salary > 0:
            growth = self.SALARY_GROWTH_RATE + random.uniform(-0.01, 0.01)
            self.gross_salary *= (1 + growth)
            self._rebuild_calculator()
            self.financial_state["gross_salary"] = self.gross_salary

        # -- Apply expense inflation to all recurring expenses --
        inflation = self.EXPENSE_INFLATION_RATE
        for cat in self.expense_manager.categories.values():
            for expense_data in cat.values():
                expense_data["amount"] *= (1 + inflation)

        # -- Apply rent inflation for renters --
        if self.mortgage_status != "active_mortgage":
            self.monthly_rent *= (1 + inflation)

        # -- Generate random life events based on age-weighted probabilities --
        triggered_events = auto_events + self._generate_life_events()
        for event in triggered_events:
            self.apply_life_event(event)

        # Recalculate finances for the new year
        self.update_financial_state()

        # Evaluate living situation — may downgrade or upgrade
        situation_event = self._evaluate_living_situation()
        if situation_event:
            triggered_events.append(situation_event)
            self.life_events.append(situation_event)
            # Recalculate after rent change
            self.update_financial_state()

        # Add exactly one year's worth of spare cash to savings
        savings_breakdown = self.accumulate_annual_savings()

        # Regenerate preferences (they shift with age and income)
        self.evaluate_housing_preferences()

        # Track the AI's full decision result for display purposes
        decision_result = {}
        # Track purchase details for FTB logging (populated only on a BUY)
        _purchase_details = {}

        # -- Non-homeowner path: ask the LLM what to do --
        if self.mortgage_status != "active_mortgage":
            decision_result = self.make_housing_decision()
            decision = decision_result["decision"]

            # Track purchase details for logging
            _purchase_details = {}

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

                    # Capture FTB purchase details before deducting savings
                    _purchase_details = {
                        "property_price": best_mortgage["property_price"],
                        "deposit_paid":   best_mortgage["deposit_paid"],
                        "deposit_pct":    round(best_mortgage["deposit_paid"] / best_mortgage["property_price"] * 100, 2),
                        "mortgage_rate":  best_mortgage.get("rate"),
                        "first_time_buyer": self.first_time_buyer,
                    }

                    # Deduct the deposit from savings
                    self.financial_state["savings"] -= best_mortgage["deposit_paid"]

                    # Deduct SDLT from savings
                    from Financial.Financial_Calculator import calculate_sdlt
                    sdlt = calculate_sdlt(best_mortgage["property_price"], first_time_buyer=self.first_time_buyer)
                    self.financial_state["savings"] -= sdlt["total_sdlt"]

                    # Deduct solicitor, survey, and moving costs
                    transaction_costs = 4_000  # ~£3k-5k typical UK purchase costs
                    self.financial_state["savings"] -= transaction_costs

                    # Activate the mortgage
                    self.active_mortgage = best_mortgage
                    self.mortgage_status = "active_mortgage"
                    self.first_time_buyer = False  # No longer a first-time buyer

                    # Apply homeowner-specific expenses
                    self._apply_homeowner_expenses(best_mortgage["property_price"])

                    # Record the life event
                    self.life_events.append("bought_home")
                else:
                    # No mortgage was approved - fall back to saving
                    decision = "SAVE_FOR_DEPOSIT"

        # -- Homeowner path: ask the LLM using the homeowner prompt --
        else:
            decision_result = self._make_homeowner_decision()
            decision = decision_result["decision"]

            if self.active_mortgage:
                # Apply property value growth (regional rate)
                growth_rate = self._get_property_growth_rate()
                self.active_mortgage["property_price"] *= (1 + growth_rate)

                # Assess property faults for homeowners
                if self.mortgage_status == "active_mortgage" and hasattr(self.current_property, 'fault_model'):
                    new_faults = self.current_property.fault_model.assess_annual_faults(self.simulation_year)
                    total_repair_cost = sum(f['repair_cost'] for f in new_faults)
                    if total_repair_cost > 0:
                        self.financial_state["savings"] -= total_repair_cost
                        triggered_events.append(f"property_repairs:£{total_repair_cost:,.0f}")

                if decision == "OVERPAY_MORTGAGE":
                    # Put 50% of available savings towards overpayment
                    overpay = self.financial_state["savings"] * 0.5
                    if overpay > 0:
                        self.active_mortgage["loan_amount"] = max(
                            0, self.active_mortgage["loan_amount"] - overpay
                        )
                        self.financial_state["savings"] -= overpay
                        # Reduce remaining years proportionally
                        if self.active_mortgage["loan_amount"] <= 0:
                            self.active_mortgage["years_remaining"] = 0

                # Tick down the mortgage term
                self.active_mortgage["years_remaining"] -= years_elapsed

                # Check if the mortgage is fully paid off
                if self.active_mortgage["years_remaining"] <= 0:
                    self.active_mortgage = None
                    self.life_events.append("paid_off_debt")

                if decision == "CONSIDER_MOVING":
                    # Reset to trigger buying logic next year
                    self.current_property = None
                    self.active_mortgage = None
                    self.mortgage_status = "no_mortgage"
                    self._remove_homeowner_expenses()
                    self.life_events.append("property_sold")

        # Recalculate happiness after all changes
        self.update_happiness()

        # Calculate key affordability metrics for logging
        max_price = self.housing_preferences.get("max_price", self.gross_salary * 4.5)
        deposit_needed = max_price * 0.10  # 10% deposit minimum
        deposit_readiness = (self.financial_state["savings"] / deposit_needed * 100) if deposit_needed > 0 else 0
        affordability_ratio = max_price / self.gross_salary if self.gross_salary > 0 else 0

        # Build and return the year summary
        return {
            "year_summary": f"{self.name} aged {self.age}, decided to {decision}",
            "decision": decision,
            "age": self.age,
            "gross_salary": round(self.gross_salary, 0),
            "net_monthly": round(self.financial_state["net_salary"] / 12, 0),
            "monthly_expenses": round(self.financial_state.get("total_expenses_monthly", 0), 0),
            "monthly_rent": round(
                self.active_mortgage.get("monthly_payment", 0) if self.active_mortgage
                else self.monthly_rent, 0),
            "savings": round(self.financial_state["savings"], 0),
            "monthly_available": round(self.monthly_available_funds, 0),
            "happiness_before": old_happiness,
            "happiness_after": self.happiness_score,
            "financial_change": round(
                (self.financial_state["savings"] - old_savings)
                - (self.financial_state.get("debt", 0) - old_debt), 0),
            "total_debt": round(self.financial_state.get("debt", 0), 0),
            "housing_status": self.mortgage_status,
            "living_situation": self.living_situation,
            "life_events_this_year": triggered_events,
            "major_events": self.life_events[-3:],
            # -- Affordability metrics --
            "affordability_ratio": round(affordability_ratio, 2),
            "deposit_readiness_pct": round(deposit_readiness, 1),
            # -- Savings breakdown (what drove the change in savings this year) --
            "savings_breakdown": savings_breakdown,
            # -- First-time buyer purchase details (populated only when decision == BUY) --
            "property_price":   _purchase_details.get("property_price"),
            "deposit_paid":     _purchase_details.get("deposit_paid"),
            "deposit_pct":      _purchase_details.get("deposit_pct"),
            "mortgage_rate":    _purchase_details.get("mortgage_rate"),
            "first_time_buyer": _purchase_details.get("first_time_buyer"),
            # -- AI transparency fields --
            "ai_reasoning": decision_result.get("reasoning", ""),
            "ai_timeline": decision_result.get("timeline", ""),
            "ai_raw_response": decision_result.get("raw_response", ""),
            "ai_tool_trace": decision_result.get("tool_trace", []),
        }

    # --------------------------------------------------------------------
    #  LIFE EVENT GENERATION
    # --------------------------------------------------------------------

    def _age_band(self):
        """Map current age to the probability band used by LIFE_EVENT_PROBABILITIES."""
        if self.age < 35:
            return "young"
        elif self.age < 55:
            return "mid_life"
        else:
            return "later_life"

    def _generate_life_events(self):
        """
        Roll the dice on every event in LIFE_EVENT_PROBABILITIES based on
        the agent's current age band, but only if the preconditions for
        that event are met. Returns a list of event names that triggered
        this year.

        Preconditions:
            salary_increase  - must have a job (gross_salary > 0)
            job_promotion    - must have a job
            job_loss         - must have a job
            marriage         - must not already be married
            birth_child      - must be married
            divorce          - must be married
            debt_increase    - must already have at least one debt
            bereavement      - no precondition
            serious_illness  - no precondition
        """
        band = self._age_band()
        has_job = self.gross_salary > 0
        has_debt = len(self.debt_manager.debts) > 0

        # Map each event to a boolean precondition
        preconditions = {
            "salary_increase": has_job,
            "job_promotion":   has_job,
            "job_loss":        has_job,
            "marriage":        not self.is_married,
            "birth_child":     self.is_married,
            "divorce":         self.is_married,
            "debt_increase":   has_debt,
            "bereavement":     True,
            "serious_illness": True,
        }

        triggered = []
        for event_name, probs in self.LIFE_EVENT_PROBABILITIES.items():
            # Skip events whose preconditions are not met
            if not preconditions.get(event_name, True):
                continue
            if random.random() < probs.get(band, 0):
                triggered.append(event_name)
        return triggered

    # --------------------------------------------------------------------
    #  HOMEOWNER DECISION MAKING
    # --------------------------------------------------------------------

    def _make_homeowner_decision(self):
        """
        Use the HOMEOWNER_PROMPT to ask the LLM what a homeowner should do
        (STAY, OVERPAY_MORTGAGE, CONSIDER_MOVING).

        :return: Dict with decision, reasoning, timeline, and raw_response.
        """
        if not self.use_llm:
            # Rule-based homeowner decision
            overpay_threshold = 500
            decision = "STAY"
            if self.active_mortgage and self.monthly_available_funds > overpay_threshold:
                decision = "OVERPAY_MORTGAGE"
            return {
                "decision": decision,
                "reasoning": "rule-based (LLM disabled)",
                "timeline": "",
                "raw_response": "",
                "tool_trace": [],
            }

        self.llm = ChatOllama(model="llama3.2")
        self.tools = build_agent_tools(self)

        # Build equity info
        equity = 0
        equity_pct = 0
        if self.active_mortgage:
            equity = self.active_mortgage["property_price"] - self.active_mortgage["loan_amount"]
            equity_pct = (equity / self.active_mortgage["property_price"]) * 100

        system_prompt = HOMEOWNER_PROMPT.format(
            name=self.name,
            age=self.age,
            property=str(self.current_property),
            property_value=self.active_mortgage["property_price"] if self.active_mortgage else 0,
            monthly_payment=self.active_mortgage.get("monthly_payment", 0) if self.active_mortgage else 0,
            years_remaining=self.active_mortgage.get("years_remaining", 0) if self.active_mortgage else 0,
            equity=equity,
            equity_pct=equity_pct,
            savings=self.financial_state["savings"],
            available_monthly=self.monthly_available_funds,
            happiness=self.happiness_score,
        )

        self.agent = create_react_agent(
            model=self.llm,
            tools=self.tools,
            prompt=system_prompt,
        )

        result = self.agent.invoke({
            "messages": [("user", "Its a new year. Review your homeowner situation and decide what to do.")]
        })

        # Extract the tool trace from the full message history
        all_messages = result.get("messages", [])
        tool_trace = self._extract_tool_trace(all_messages)

        response_text = all_messages[-1].content if all_messages else ""
        parsed = self._parse_llm_decision(response_text)
        parsed["tool_trace"] = tool_trace

        # Record this decision in the agent's memory
        self.decision_history.append({
            "year": self.simulation_year,
            "decision": parsed["decision"],
            "reasoning": parsed["reasoning"],
        })

        return parsed

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
            self._rebuild_calculator()
            self.financial_state["gross_salary"] = self.gross_salary
            changes.append(f"Salary: £{old_salary:,.0f} -> £{self.gross_salary:,.0f}")

        elif event_type == "salary_increase":
            # Default raise is 5% of current salary
            raise_amount = event_data.get("salary_increase", self.gross_salary * 0.05)
            old_salary = self.gross_salary
            self.gross_salary += raise_amount
            self._rebuild_calculator()
            self.financial_state["gross_salary"] = self.gross_salary
            changes.append(f"Salary: £{old_salary:,.0f} -> £{self.gross_salary:,.0f}")

        elif event_type == "job_loss":
            old_salary = self.gross_salary
            self.gross_salary = 0
            self._rebuild_calculator()
            self.financial_state["gross_salary"] = self.gross_salary
            changes.append(f"Salary: £{old_salary:,.0f} -> £0 (job lost)")

        elif event_type == "marriage":
            self.family_size += 1
            self.is_married = True
            changes.append(f"Married! Family size: {self.family_size}")

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
            self.is_married = False
            if self.family_size > 1:
                self.family_size -= 1
            changes.append(f"Divorced. Family size: {self.family_size}")

        elif event_type == "debt_increase":
            amount = event_data.get("amount", 5000)
            apr = event_data.get("apr", 0.19)
            min_pay = event_data.get("min_payment", max(50, amount * 0.02))
            debt_label = event_data.get("name", f"debt_{len(self.debt_manager.debts) + 1}")
            self.debt_manager.add_debt(debt_label, amount, apr, min_pay)
            changes.append(f"Debt increased by £{amount:,.0f} (tracked as '{debt_label}')")

        elif event_type == "new_job":
            old_salary = self.gross_salary
            new_salary = event_data.get("salary", old_salary)
            self.gross_salary = new_salary
            self._rebuild_calculator()
            self.financial_state["gross_salary"] = self.gross_salary
            changes.append(f"New job! Salary: £{old_salary:,.0f} -> £{new_salary:,.0f}")

        elif event_type == "inheritance":
            amount = event_data.get("amount", 10_000)
            self.financial_state["savings"] += amount
            changes.append(f"Received inheritance/windfall of £{amount:,.0f}")

        elif event_type == "debt_paid_off":
            debt_name = event_data.get("name", "")
            if debt_name and debt_name in self.debt_manager.debts:
                old_balance = self.debt_manager.debts[debt_name]["balance"]
                del self.debt_manager.debts[debt_name]
                changes.append(f"Paid off '{debt_name}' (was £{old_balance:,.0f})")
            else:
                changes.append(f"Debt '{debt_name}' not found — no change")

        elif event_type == "property_sold":
            equity = 0
            if self.active_mortgage:
                equity = self.active_mortgage["property_price"] - self.active_mortgage["loan_amount"]
            self.financial_state["savings"] += max(0, equity)
            self.current_property = None
            self.active_mortgage = None
            self.mortgage_status = "no_mortgage"
            self._remove_homeowner_expenses()
            changes.append(f"Property sold — £{equity:,.0f} equity added to savings")

        elif event_type == "property_repossessed":
            self.current_property = None
            self.active_mortgage = None
            self.mortgage_status = "no_mortgage"
            self._remove_homeowner_expenses()
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
                    mortgage_product=product,
                    existing_debts=self.debt_manager.total_monthly_payments()
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

    def generate_ai_narrative(self, year_result):
        """
        Ask the LLM to write a short first-person narrative summarising
        what happened. Works with both annual (time_step) and monthly
        (monthly_step) result dicts.

        :param year_result: The dict returned by time_step() or monthly_step().
        :return: String narrative from the LLM, or a fallback message.
        """
        if not self.use_llm:
            return ""

        # Handle both annual and monthly event keys
        events = (year_result.get("life_events_this_year")
                  or year_result.get("life_events_this_month")
                  or [])
        events_str = ", ".join(events) or "nothing unusual"
        savings_change = year_result.get("financial_change", 0)
        direction = "gained" if savings_change >= 0 else "lost"

        # Adapt the prompt for monthly vs annual
        month_label = year_result.get("month_label")
        if month_label:
            time_context = f"This month ({month_label})"
            period = "month"
        else:
            time_context = "This year"
            period = "year"

        decision = year_result.get("decision")
        decision_text = f" you decided to {decision}." if decision else "."

        narrative_prompt = (
            f"You are {self.name}, age {year_result['age']}. "
            f"Write a 2-3 sentence first-person summary of your {period}. "
            f"{time_context}{decision_text} "
            f"Your salary is £{year_result['gross_salary']:,.0f}, "
            f"you have £{year_result['savings']:,.0f} in savings "
            f"({direction} £{abs(savings_change):,.0f} this {period}). "
            f"Your happiness went from {year_result['happiness_before']:.0f} to "
            f"{year_result['happiness_after']:.0f}. "
            f"Life events: {events_str}. "
            f"Housing: {year_result['housing_status']}. "
            f"Keep it conversational and realistic. Do not repeat the raw numbers, "
            f"just reflect on how the {period} felt."
        )

        try:
            response = self.llm.invoke(narrative_prompt)
            return response.content.strip()
        except Exception:
            return (f"This year I decided to {year_result['decision']}. "
                    f"My savings are at £{year_result['savings']:,.0f}.")

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
