from Environment.Banks import Bank
from Algorithms.ResidentAlgorithms import (
    HousingPreferenceEvaluator,
    FinancialAffordabilityEvaluator,
    HappinessEvaluator
)

class ResidentAgent:
    """
    Main resident agent that orchestrates all decision-making and life progression.

    This agent:
    - Tracks personal financial state and housing situation
    - Makes decisions about mortgages and property purchases
    - Evaluates preferences and evaluates opportunities
    - Progresses through time (annual/bi-annual updates)
    - Maintains happiness score based on life circumstances
    """

    def __init__(self, agent_id, age, name, gross_salary, expense_manager,
                 financial_calculator=None, initial_savings=0):
        """
        Initialize a resident agent with basic demographics and financial setup.

        Args:
            agent_id (int): Unique identifier for this resident
            age (int): Current age of resident
            name (str): Name of resident
            gross_salary (float): Annual gross salary before deductions
            expense_manager (ExpenseManager): Instance with resident's expenses
            financial_calculator (SalaryCalculator, optional): Salary calculator instance
            initial_savings (float, optional): Starting savings amount

        Implementation notes:
        - If financial_calculator is None, you should create one using the gross_salary
        - Initialize all algorithm evaluators as instance variables
        - Set default housing preferences appropriate for age
        - Calculate initial financial state (net income, monthly available funds)
        """
        self.agent_id = agent_id
        self.age = age
        self.name = name
        self.gross_salary = gross_salary

        # Financial System
        self.financial_calculator = financial_calculator
        self.expense_manager = expense_manager
        self.financial_state = {
            "gross_salary": gross_salary,
            "net_salary": 0,  # Will be calculated
            "total_expenses_monthly": 0,  # Will be calculated
            "savings": initial_savings,
            "debt": 0,
        }
        self.monthly_available_funds = 0  # Will be calculated

        # Housing & Mortgage Status
        self.mortgage_status = "no_mortgage"  # Options: no_mortgage, searching, pending_approval, approved, active_mortgage
        self.current_property = None
        self.housing_preferences = {}  # Will be populated by evaluate_housing_preferences()

        # Life & Satisfaction
        self.happiness_score = 70  # Start at neutral (0-100 scale)
        self.life_events = []  # Track major events (marriage, children, job change, etc.)

        # Algorithm Instances (for decision-making)
        self.housing_preference_evaluator = HousingPreferenceEvaluator()
        self.financial_affordability_evaluator = FinancialAffordabilityEvaluator()
        self.mortgage_product_evaluator = MortgageProductEvaluator()
        self.happiness_evaluator = HappinessEvaluator()

        # Initialize financial state on creation
        self.update_financial_state()

    # ==================== FINANCIAL MANAGEMENT ====================

    def update_financial_state(self):
        """
        Recalculate all financial values based on current situation.
        Called annually or when circumstances change.

        Implementation steps:
        1. Calculate net salary using financial_calculator.calculate_net_pay()
        2. Extract deductions breakdown
        3. Calculate total monthly expenses using expense_manager.calculate_total_monthly()
        4. Calculate monthly_available_funds = (net_salary / 12) - total_monthly_expenses
        5. Update self.financial_state dictionary
        6. Handle mortgage payments if active_mortgage exists

        Return: Dictionary with updated financial state

        Example calculation:
        - Gross annual: £50,000
        - Tax + NI deductions: £8,500
        - Net annual: £41,500
        - Net monthly: £3,458
        - Monthly expenses: £1,200
        - Monthly available: £2,258 (for savings/mortgage)
        """
        pass

    def get_monthly_financial_summary(self):
        """
        Return current monthly financial snapshot for easy reference.

        Should return dict with:
        {
            "gross_monthly": float,
            "net_monthly": float,
            "total_expenses": float,
            "available_after_expenses": float,
            "savings_balance": float,
            "debt_balance": float
        }
        """
        pass

    # ==================== HOUSING PREFERENCES ====================

    def evaluate_housing_preferences(self):
        """
        Determine what kind of house this resident wants based on their life situation.
        Call this to update preferences (preferences evolve with age/income/family).

        Implementation considerations:
        - Age factor: Young (20-30) may prefer city/apartments, older (40+) may prefer suburbs
        - Income factor: Higher income = more expensive properties
        - Family status: Consider if have children, would want more space
        - Location preference: Consider urban vs rural vs green space
        - Property type: Detached, semi, terraced, flat, etc.

        Should return dict like:
        {
            "preferred_location": "countryside",  # From vocab.py LOCATION_TYPES
            "preferred_property_type": ["detached", "semi"],
            "min_bedrooms": 3,
            "max_bedrooms": 5,
            "min_bathrooms": 2,
            "price_range": {
                "min": 250000,
                "max": 500000
            },
            "must_haves": ["garden", "garage"],
            "nice_to_haves": ["pool", "home_office"]
        }

        Update self.housing_preferences with the result.
        Return: The preferences dictionary
        """
        pass

    # ==================== MORTGAGE SEARCHING & EVALUATION ====================

    def search_for_mortgages(self, banks_list, max_property_price):
        """
        Query multiple banks for available mortgage products that resident could qualify for.

        Args:
            banks_list (list): List of Bank objects to query
            max_property_price (float): Maximum property price to consider

        Implementation steps:
        1. Initialize empty list for viable_mortgages
        2. For each bank in banks_list:
            a. Get all branches: bank.get_all_branches()
            b. For each branch, get available products
            c. For each mortgage product:
               - Check if lending criteria met using mortgage_product_evaluator
               - If criteria met, add to viable_mortgages
        3. Sort viable mortgages by suitability score
        4. Return sorted list with top options

        Return: List of mortgage products sorted by suitability

        Example output structure:
        [
            {
                "product": mortgage_product_obj,
                "bank_name": "HSBC",
                "branch": branch_obj,
                "suitability_score": 87,
                "estimated_monthly_payment": 1850,
                "max_borrowable": 400000
            },
            ...
        ]
        """
        pass

    def assess_mortgage_suitability(self, mortgage_product, house_price, deposit_amount):
        """
        Deep-dive evaluation: Can this resident actually afford this specific mortgage for this price?

        Args:
            mortgage_product: MortgageProduct object from bank
            house_price (float): Price of specific property
            deposit_amount (float): Deposit the resident has/will have

        Implementation steps:
        1. Calculate loan_amount = house_price - deposit_amount
        2. Use financial_affordability_evaluator to:
           a. Check lending criteria (LTV, age, income, etc.)
           b. Calculate affordability ratio
           c. Check if emergency fund maintained
           d. Check if deposit savings timeline feasible
        3. Use mortgage_product_evaluator to:
           a. Calculate mortgage suitability score
           b. Compare against other viable products (if available)
        4. Return comprehensive assessment

        Return: Dictionary with decision and reasoning
        {
            "suitable": True/False,
            "affordability_score": float,  # 0-100
            "monthly_payment": float,
            "affordability_ratio": float,  # 0.0-1.0
            "passes_lending_criteria": True/False,
            "failed_criteria": [],  # List of criteria not met
            "warnings": [],  # Non-critical issues
            "recommendation": "Highly Suitable" / "Marginal" / "Not Suitable"
        }
        """
        pass

    # ==================== DECISION MAKING ====================

    def make_housing_decision(self, available_properties, available_mortgage_products):
        """
        Evaluate all property + mortgage combinations and decide whether to purchase.
        This is the core AI decision logic.

        Args:
            available_properties (list): List of Property objects in market
            available_mortgage_products (list): List of viable mortgage products from search_for_mortgages()

        Implementation steps:
        1. Score each property against preferences using housing_preference_evaluator
        2. For top N properties:
            a. For each viable mortgage:
               - Calculate if affordable
               - Score suitability
               - Create property+mortgage combination score
        3. Evaluate all combinations:
            a. Best fit property + mortgage
            b. Apply happiness weighting (happier residents more willing to take risk)
            c. Apply decision criteria (afford deposit? accept the risk?)
        4. Decide:
            a. If excellent match + affordable + meets risk tolerance → BUY
            b. If good matches exist but need more deposit → SAVE_FOR_DEPOSIT
            c. If market not right → WAIT
            d. If nothing suitable → CONTINUE_SEARCHING

        Return: Decision dict
        {
            "decision": "BUY" / "SAVE_FOR_DEPOSIT" / "WAIT" / "CONTINUE_SEARCHING",
            "selected_property": property_obj or None,
            "selected_mortgage": mortgage_product_obj or None,
            "reasoning": str explaining decision,
            "next_action": str describing what resident will do next,
            "timeline": int or None  # Months until next review if waiting
        }

        Implementation note:
        - This method updates self.mortgage_status
        - This method could update self.happiness_score
        - This method might trigger self.current_property update if BUY decision
        """
        pass

    # ==================== TIME PROGRESSION ====================

    def time_step(self, years_elapsed=1):
        """
        Progress resident through time (called annually or bi-annually in simulation).
        This is the main loop for one resident per year.

        Args:
            years_elapsed (int): Number of years to progress (default 1)

        Implementation steps per year:
        1. Age the resident: self.age += years_elapsed
        2. Update financial state: self.update_financial_state()
        3. Update preferences: self.evaluate_housing_preferences()
        4. If actively searching for property or needs update:
            a. Search for mortgages via banks
            b. Get available properties from housing market
            c. Make housing decision
        5. If owns property:
            a. Process mortgage payment
            b. Check property value changes (appreciation)
        6. Apply any life events (random or predetermined)
        7. Update happiness: self.update_happiness()
        8. Return summary of what happened this year

        Return: Dictionary with summary
        {
            "year_summary": str,
            "age": int,
            "happiness_before": float,
            "happiness_after": float,
            "financial_change": float,
            "housing_status": str,
            "major_events": list
        }
        """
        pass

    # ==================== HAPPINESS MANAGEMENT ====================

    def update_happiness(self):
        """
        Recalculate happiness based on current life circumstances.
        Called during time_step().

        Uses HappinessEvaluator to calculate from:
        - Housing satisfaction (in desired property? right location?)
        - Financial security (can afford lifestyle? emergency fund?)
        - Life events (positive/negative events)
        - Age-based factors (different priorities by age)

        Implementation:
        1. Call happiness_evaluator.calculate_happiness_score()
        2. Pass current state information
        3. Update self.happiness_score
        4. Return old and new scores for tracking

        Return: {"old_score": float, "new_score": float, "change": float}
        """
        pass

    def apply_life_event(self, event_type, event_data):
        """
        Handle major life events that affect happiness and preferences.

        Event types might include:
        - "marriage": Preferences change, might want larger property
        - "birth_child": Adds to family size, changes space needs
        - "job_promotion": Increases salary, may enable mortgage approval
        - "job_loss": Decreases salary, may jeopardize mortgage
        - "property_appreciation": Current property gains value
        - "divorce": Life changes, preference changes

        Implementation:
        1. Record event in self.life_events
        2. Update relevant attributes (salary, family_size, etc.)
        3. Recalculate financial_state if needed
        4. Update happiness based on event type
        5. Re-evaluate preferences if major life change

        Return: Summary of impact
        """
        pass

    # ==================== UTILITY METHODS ====================

    def get_status_summary(self):
        """
        Return human-readable summary of resident's current state.
        Useful for debugging and understanding simulation.

        Return:
        {
            "name": str,
            "age": int,
            "financial": {...},
            "housing": {...},
            "happiness": float,
            "next_action": str
        }
        """
        pass

    def __repr__(self):
        """String representation for debugging"""
        return f"ResidentAgent(id={self.agent_id}, name={self.name}, age={self.age}, happiness={self.happiness_score:.1f})"





