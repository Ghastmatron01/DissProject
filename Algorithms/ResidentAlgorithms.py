from pathlib import Path
from Algorithms.Data_Extraction import DataExtractor


class HousingPreferenceEvaluator:
    """
    Generates housing preferences based on an agent's life stage,
    and allows specific values to be overridden by user input.

    Flow:
        1. evaluate_preferences()  - generates base preferences from life situation
        2. override_preferences()  - user adjusts specific fields (optional)
        3. score_property()        - scores a property against the final preferences
    """

    def __init__(self):
        """
        Load the income percentile data once when the class is created.
        Stored as self.income_percentiles so every method can use it
        without hitting the file on disk again.
        """
        extractor = DataExtractor()
        data_path = Path(__file__).parent.parent / "data" / "Table_3.1a_2223.xlsx"
        self.income_percentiles = extractor.load_income_after_tax_percentiles(
            str(data_path), tax_year="2022 to 2023"
        )

    def evaluate_preferences(self, agent_age, agent_income, family_size):
        """
        Generate base housing preferences from the agent's life circumstances.
        These are algorithm-driven defaults - no user input needed here.

        :param agent_age: Age of the agent (e.g. 25).
        :param agent_income: Annual gross income (e.g. 40000.0).
        :param family_size: Number of people in household (e.g. 1).
        :return: Dict with preferred_location, preferred_property_types,
                 min/max_bedrooms, min/max_price, and weights.
        """
        # Find which percentile bracket the agent's income falls into
        income_bracket = self.income_percentile(agent_income)

        # Determine age band from the agent's age
        if 18 <= agent_age <= 29:
            age_band = "young"
        elif 30 <= agent_age <= 45:
            age_band = "mid_life"
        else:
            age_band = "later_life"

        # Pick base preferences from the age + income matrix
        if age_band == "young" and income_bracket == "low":
            location = "city"
            property_types = ["flat", "terraced"]
            min_bed, max_bed = 1, 2

        elif age_band == "young" and income_bracket == "mid":
            location = "city"
            property_types = ["terraced", "semi_detached"]
            min_bed, max_bed = 2, 3

        elif age_band == "young" and income_bracket == "high":
            location = "suburban"
            property_types = ["semi_detached", "detached"]
            min_bed, max_bed = 2, 3

        elif age_band == "mid_life" and income_bracket == "low":
            location = "suburban"
            property_types = ["terraced", "semi_detached"]
            min_bed, max_bed = 2, 3

        elif age_band == "mid_life" and income_bracket == "mid":
            location = "suburban"
            property_types = ["semi_detached", "detached"]
            min_bed, max_bed = 3, 4

        elif age_band == "mid_life" and income_bracket == "high":
            location = "countryside"
            property_types = ["detached"]
            min_bed, max_bed = 4, 5

        elif age_band == "later_life" and income_bracket == "low":
            location = "suburban"
            property_types = ["terraced", "flat"]
            min_bed, max_bed = 2, 3

        elif age_band == "later_life" and income_bracket == "mid":
            location = "suburban"
            property_types = ["semi_detached", "detached"]
            min_bed, max_bed = 3, 4

        else:  # later_life + high
            location = "countryside"
            property_types = ["detached"]
            min_bed, max_bed = 3, 5

        # Family size adjustment - more people need more bedrooms
        if family_size > 2:
            min_bed = min(min_bed + 1, 5)
            max_bed = min(max_bed + 1, 6)

        # Price range derived from income multiplier
        max_price = agent_income * 4.5
        min_price = agent_income * 2.0  # ignore properties that are too cheap

        return {
            "preferred_location": location,
            "preferred_property_types": property_types,
            "min_bedrooms": min_bed,
            "max_bedrooms": max_bed,
            "min_price": min_price,
            "max_price": max_price,
            "weights": {
                "price": 0.4,
                "location": 0.3,
                "property_type": 0.2,
                "size": 0.1
            }
        }

    def income_percentile(self, income):
        """
        Determine the income bracket by comparing the agent's income
        against national percentile thresholds.

        :param income: The income of the user after tax.
        :return: "low", "mid", or "high".
        """
        # Iterate in sorted order (1 to 99) so the first match is the correct bracket
        for percentile in sorted(self.income_percentiles.keys()):
            if income <= self.income_percentiles[percentile]:
                # Found the first percentile whose threshold is >= the agent's income
                if percentile <= 25:
                    return "low"
                elif percentile <= 75:
                    return "mid"
                else:
                    return "high"

        # Fallback: income is above the 99th percentile value
        return "high"

    def override_preferences(self, base_preferences, user_overrides):
        """
        Merge user-supplied overrides into the algorithm-generated preferences.
        Any key in user_overrides replaces the matching key in base_preferences.
        Keys not provided in user_overrides are left unchanged.

        :param base_preferences: Dict output from evaluate_preferences().
        :param user_overrides: Dict of preference keys to replace.
        :return: Merged preferences dict ready for score_property().
        """
        merged = base_preferences.copy()
        merged.update(user_overrides)
        return merged

    def score_property(self, property_obj, preferences):
        """
        Score how well a specific property matches the final preferences.
        Called after evaluate_preferences() and optionally override_preferences().

        :param property_obj: House object (has .price, .property_type, .county, .district).
        :param preferences: Final preferences dict (from evaluate or override).
        :return: Float (0-100) representing how well the property fits.
        """
        # -- Price score --
        if preferences["min_price"] <= property_obj.price <= preferences["max_price"]:
            price_score = 100
        elif property_obj.price < preferences["min_price"]:
            # Below budget floor - scale down based on how far below
            price_score = max(0, 100 - (preferences["min_price"] - property_obj.price) / preferences["min_price"] * 100)
        else:
            # Above budget ceiling - scale down based on how far above
            price_score = max(0, 100 - (property_obj.price - preferences["max_price"]) / preferences["max_price"] * 100)

        # -- Location score --
        location_type = self.map_location_to_type(property_obj.county, property_obj.district)
        if location_type == preferences["preferred_location"]:
            location_score = 100
        elif self.is_partial_location_match(location_type, preferences["preferred_location"]):
            location_score = 50
        else:
            location_score = 0

        # -- Property type score --
        if property_obj.property_type in preferences["preferred_property_types"]:
            type_score = 100
        else:
            type_score = 0

        # -- Size score (bedrooms) --
        bedrooms = property_obj.get_bedrooms()
        if preferences["min_bedrooms"] <= bedrooms <= preferences["max_bedrooms"]:
            size_score = 100
        elif bedrooms < preferences["min_bedrooms"]:
            size_score = max(0, 100 - (preferences["min_bedrooms"] - bedrooms) * 25)
        else:
            size_score = max(0, 100 - (bedrooms - preferences["max_bedrooms"]) * 25)

        # -- Final weighted score --
        weights = preferences.get("weights", {"price": 0.4, "location": 0.3, "property_type": 0.2, "size": 0.1})
        final_score = (price_score * weights.get("price", 0.4) +
                       location_score * weights.get("location", 0.3) +
                       type_score * weights.get("property_type", 0.2) +
                       size_score * weights.get("size", 0.1))

        return final_score

    def map_location_to_type(self, county, district):
        """
        Map a county or district name to a broad location type using
        simple keyword lists.

        :param county: County name from the property record.
        :param district: District name from the property record.
        :return: "city", "suburban", "countryside", or "unknown".
        """
        city_areas = ["Greater London", "Manchester", "Birmingham", "Leeds"]
        suburban_areas = ["Surrey", "Kent", "Essex", "Hertfordshire"]
        countryside_areas = ["Cornwall", "Devon", "Lake District", "Yorkshire Dales"]

        if county in city_areas or district in city_areas:
            return "city"
        elif county in suburban_areas or district in suburban_areas:
            return "suburban"
        elif county in countryside_areas or district in countryside_areas:
            return "countryside"
        else:
            return "unknown"

    def is_partial_location_match(self, location_type, preferred):
        """
        Check whether two location types are close enough to count
        as a partial match (worth half marks in scoring).

        :param location_type: The location type of the property (e.g. "city").
        :param preferred: The user's preferred location type (e.g. "suburban").
        :return: True if it counts as a partial match, False otherwise.
        """
        # Adjacent location types count as partial matches
        if preferred == "city" and location_type == "suburban":
            return True
        if preferred == "suburban" and location_type in ["city", "countryside"]:
            return True
        if preferred == "countryside" and location_type == "suburban":
            return True
        return False


# --------------------------------------------------------------------
# --------------------------------------------------------------------


class FinancialAffordabilityEvaluator:
    """
    Evaluates whether an agent can afford a specific mortgage on a
    specific property.

    This class bridges the agent's financial data and the MortgageCalculator.
    It:
      1. Uses MortgageCalculator.check_lending_criteria() to check bank approval rules.
      2. Adds UK-standard age checks (must be 18-70, must finish before 75).
      3. Scores how comfortable the mortgage is beyond just pass/fail.
    """

    def __init__(self):
        """Initialise the evaluator. No state needed - it is a pure evaluator."""
        pass

    def check_lending_criteria(self, agent_age, agent_income, deposit,
                               property_price, mortgage_product, mortgage_term=25):
        """
        Check whether the agent meets a bank's lending criteria for a
        specific mortgage product. Combines MortgageCalculator's built-in
        checks with age-based checks.

        :param agent_age: Agent's current age.
        :param agent_income: Annual gross income (before tax).
        :param deposit: Deposit amount the agent has saved.
        :param property_price: Price of the property.
        :param mortgage_product: MortgageProduct object from Environment.Mortgages.
        :param mortgage_term: Repayment term in years (default 25).
        :return: Dict with passes, ltv, loan_amount, monthly_payment,
                 age_at_end, failed_checks, and flags.
        """
        from Environment.Mortgages.MortgageCalculator import MortgageCalculator

        failed_checks = []
        flags = []

        # -- Age checks (not covered by MortgageCalculator) --
        age_at_end = agent_age + mortgage_term

        if agent_age < 18:
            failed_checks.append("Agent must be at least 18 years old")
        if agent_age >= 70:
            failed_checks.append("Agent must be under 70 to apply for a new mortgage")
        if age_at_end > 75:
            failed_checks.append(
                f"Mortgage would end at age {age_at_end} - banks require completion before 75"
            )

        # -- MortgageCalculator checks (deposit, LTV, income rules) --
        calculator = MortgageCalculator(
            mortgage_product=mortgage_product,
            property_price=property_price,
            deposit_amount=deposit,
            term_years=mortgage_term
        )

        approved, reason, available_after = calculator.check_lending_criteria(
            annual_gross_income=agent_income,
            existing_monthly_debts=0   # Existing debts not tracked yet - defaulting to 0
        )

        if not approved:
            # MortgageCalculator returns reasons joined with " | "
            for r in reason.split(" | "):
                if r.strip():
                    failed_checks.append(r.strip())

        # Calculate key ratios for the return dict
        loan_amount = property_price - deposit
        ltv = loan_amount / property_price if property_price > 0 else 0
        monthly_payment = calculator.calculate_monthly_payment()

        # -- Soft flags (warnings, not failures) --
        if ltv > 0.90:
            flags.append(f"High LTV: {ltv*100:.1f}% - expect higher interest rates")
        if age_at_end > 70:
            flags.append(f"Mortgage finishes at age {age_at_end} - lenders may scrutinise closely")

        return {
            "passes":          len(failed_checks) == 0,
            "ltv":             round(ltv, 4),
            "loan_amount":     loan_amount,
            "monthly_payment": round(monthly_payment, 2),
            "age_at_end":      age_at_end,
            "failed_checks":   failed_checks,
            "flags":           flags
        }

    def calculate_affordability_score(self, monthly_income, monthly_payment,
                                      monthly_expenses, current_savings):
        """
        Score how comfortable a mortgage is beyond just pass/fail.
        Useful for comparing two mortgages that both technically pass -
        which one leaves the agent in a healthier financial position?

        :param monthly_income: Net monthly income (after tax).
        :param monthly_payment: Proposed mortgage monthly payment.
        :param monthly_expenses: Other regular outgoings (bills, food, transport).
        :param current_savings: Current savings balance.
        :return: Dict with score (0-100), available_monthly, income_ratio,
                 has_emergency_fund, and comfort_label.
        """
        # Cash remaining after mortgage + all other expenses
        available_monthly = monthly_income - monthly_payment - monthly_expenses

        # Fraction of net income consumed by mortgage + expenses
        total_outgoings = monthly_payment + monthly_expenses
        income_ratio = total_outgoings / monthly_income if monthly_income > 0 else 1.0

        # Emergency fund check: does the agent have 6 months of expenses saved
        emergency_fund_target = monthly_expenses * 6
        has_emergency_fund = current_savings >= emergency_fund_target

        # -- Score from income ratio --
        # < 50% outgoings = comfortable   (80-100)
        # 50-65% outgoings = acceptable   (50-79)
        # 65-80% outgoings = tight        (20-49)
        # > 80% outgoings = unaffordable  (0-19)
        if income_ratio <= 0.50:
            base_score = 100 - (income_ratio / 0.50) * 20
        elif income_ratio <= 0.65:
            base_score = 79 - ((income_ratio - 0.50) / 0.15) * 29
        elif income_ratio <= 0.80:
            base_score = 49 - ((income_ratio - 0.65) / 0.15) * 29
        else:
            base_score = max(0, 19 - ((income_ratio - 0.80) / 0.20) * 19)

        # Emergency fund bonus/penalty
        if has_emergency_fund:
            base_score = min(100, base_score + 5)   # Small comfort bonus
        else:
            base_score = max(0, base_score - 10)    # Penalty for no safety net

        # Assign a human-readable comfort label
        if base_score >= 70:
            label = "Comfortable"
        elif base_score >= 45:
            label = "Acceptable"
        elif base_score >= 20:
            label = "Tight"
        else:
            label = "Unaffordable"

        return {
            "score":              round(base_score, 1),
            "available_monthly":  round(available_monthly, 2),
            "income_ratio":       round(income_ratio, 4),
            "has_emergency_fund": has_emergency_fund,
            "comfort_label":      label
        }


# --------------------------------------------------------------------
# --------------------------------------------------------------------


class HappinessEvaluator:
    """
    Calculates an agent's happiness score (0-100) from four independent
    components:

        1. Housing status     - having a home is fundamental        (+/-20)
        2. Financial security - savings vs debt comfort             (+/-15)
        3. Life events        - major positive/negative life events (+/-15, capped)
        4. Age factor         - subtle modifier based on life stage (+/-5)

    All happiness numbers are estimated for now. A future survey will
    provide real-world calibration data.

    Each component is capped so no single factor completely dominates.
    The final score is always clamped to [0, 100].
    """

    # Lookup table of known life events and their happiness impact.
    # Add new events here - no logic changes needed elsewhere.
    EVENT_IMPACTS = {
        "marriage":              +10,
        "birth_child":           +5,    # joy, but also stress
        "job_promotion":         +8,
        "paid_off_debt":         +8,
        "bought_home":           +12,
        "salary_increase":       +6,
        "job_loss":              -15,
        "divorce":               -10,
        "bereavement":           -12,
        "debt_increase":         -8,
        "property_repossessed":  -20,
        "serious_illness":       -10,
    }

    def calculate_happiness_score(self, housing_status, financial_security,
                                  life_events, age):
        """
        Calculate the overall happiness score from all four components.

        :param housing_status: "owned", "renting", or "homeless".
        :param financial_security: 0-100 score (high = comfortable savings/low debt).
        :param life_events: List of recent event strings (e.g. ["marriage", "job_loss"]).
        :param age: Agent's current age.
        :return: Dict with score, component breakdowns, and a readable summary.
        """
        # Start from a neutral baseline
        happiness = 50.0

        # -- Housing component (+/-20) --
        housing_map = {
            "owned":    +20,
            "renting":  +10,
            "homeless": -20,
        }
        housing_component = housing_map.get(housing_status, 0)
        happiness += housing_component

        # -- Financial security component (+/-15) --
        # Score of 50 = neutral (0 change), 100 = +15, 0 = -15
        financial_component = ((financial_security - 50) / 50) * 15
        financial_component = max(-15, min(15, financial_component))
        happiness += financial_component

        # -- Life events component (capped at +/-15 total) --
        raw_events_total = sum(
            self.EVENT_IMPACTS.get(event, 0) for event in life_events
        )
        events_component = max(-15, min(15, raw_events_total))
        happiness += events_component

        # -- Age factor (+/-5 subtle modifier) --
        if 18 <= age <= 29:
            # Young people feel housing instability more sharply
            age_component = -3 if housing_status == "renting" else +2
        elif 30 <= age <= 45:
            # Mid-life is balanced - family stress is handled via events
            age_component = 0
        else:
            # Later life - financial security matters more
            age_component = +3 if financial_security >= 60 else -3
        age_component = max(-5, min(5, age_component))
        happiness += age_component

        # Clamp the final score to [0, 100]
        final_score = max(0.0, min(100.0, happiness))

        return {
            "score":               round(final_score, 1),
            "housing_component":   housing_component,
            "financial_component": round(financial_component, 1),
            "events_component":    events_component,
            "age_component":       age_component,
            "breakdown": (
                f"Base 50 | Housing {housing_component:+} | "
                f"Financial {financial_component:+.1f} | "
                f"Events {events_component:+} | "
                f"Age {age_component:+} -> {final_score:.1f}"
            )
        }

    def get_risk_tolerance(self, happiness_score):
        """
        Convert a happiness score into a risk tolerance multiplier.
        Happier agents are more willing to stretch their budget.

        :param happiness_score: Happiness score from 0 to 100.
        :return: Float from 0.5 (very conservative) to 1.5 (very confident).
        """
        # Clamp input to valid range
        score = max(0.0, min(100.0, happiness_score))
        # Linear interpolation: 0 -> 0.5, 50 -> 1.0, 100 -> 1.5
        return round(0.5 + (score / 100.0) * 1.0, 3)

    def estimate_unknown_event(self, event_type, llm):
        """
        Ask the LLM to estimate the happiness impact of an unknown event.
        Caches the result in EVENT_IMPACTS so it only needs to be estimated once.

        :param event_type: The unknown event name.
        :param llm: The ChatOllama LLM instance to ask.
        :return: Estimated impact score (-20 to +20).
        """
        # If already estimated before, return the cached value
        if event_type in self.EVENT_IMPACTS:
            return self.EVENT_IMPACTS[event_type]

        # Build a prompt asking the LLM to rate the event
        prompt = (
            f"A person has experienced: '{event_type}'. "
            f"On a scale from -20 (devastating) to +20 (life-changing positive), "
            f"how would this affect their overall happiness? "
            f"For reference: marriage = +10, job_loss = -15, bereavement = -12. "
            f"Reply with ONLY a single integer number, nothing else."
        )

        response = llm.invoke(prompt)

        # Parse the number from the response
        try:
            score = int(response.content.strip())
            # Clamp to valid range
            score = max(-20, min(20, score))
        except ValueError:
            # If the LLM did not return a clean number, default to 0
            score = 0

        # Cache it so we do not ask again for the same event
        self.EVENT_IMPACTS[event_type] = score

        return score

