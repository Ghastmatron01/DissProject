from pathlib import Path
from Algorithms.Data_Extraction import DataExtractor

class HousingPreferenceEvaluator:
    """
    Generates housing preferences based on an agent's life stage,
    and allows specific values to be overridden by user input.

    Flow:
        1. evaluate_preferences()  → generates base preferences from life situation
        2. override_preferences()  → user adjusts specific fields (optional)
        3. score_property()        → scores a property against the final preferences
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
        These are algorithm-driven defaults — no user input needed here.

        Input:
            - agent_age (int): Age of the agent (e.g., 25)
            - agent_income (float): Annual gross income (e.g., 40000.0)
            - family_size (int): Number of people in household (e.g., 1)

        Output: dict with generated preferences
        {
            "preferred_location": "city" | "suburban" | "countryside",
            "preferred_property_types": ["flat", "terraced"],
            "min_bedrooms": 1,
            "max_bedrooms": 2,
            "min_price": 100000,
            "max_price": 250000,
            "weights": {
                "price": 0.4,
                "location": 0.3,
                "property_type": 0.2,
                "size": 0.1
            }
        }

        Logic to implement:
            Age 18-29 + low income  → city, flat/terraced, 1-2 bed, lower price range
            Age 30-45 + mid income  → suburban, semi/detached, 2-3 bed, mid price range
            Age 46-65 + high income → countryside/suburban, detached, 3-4 bed, higher range
            Family size > 2         → push bedrooms up, prefer detached/semi
            Income multiplier       → max_price ≈ income * 4.5 (rough affordability ceiling)
        """
        # Find which percentile the agent's income falls into.
        # income_percentile() does the lookup using self.income_percentiles.
        income_bracket = self.income_percentile(agent_income)

        # income_bracket is now one of: "low" | "mid" | "high"
        # Use it below alongside agent_age to determine preferences.

        # age band
        if 18 <= agent_age <= 29:
            age_band = "young"
        elif 30 <= agent_age <= 45:
            age_band = "mid_life"
        else:
            age_band = "later_life"

        # pick base preferences from age + income matrix
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

        # family size adjustment - more people = more bedrooms needed
        if family_size > 2:
            min_bed = min(min_bed + 1, 5)
            max_bed = min(max_bed + 1, 6)

        # Step 4: price range from income
        max_price = agent_income * 4.5
        min_price = agent_income * 2.0  # won't bother with anything too cheap

        # return the preferences dict
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
        Works out the percentile of income based on income after tax, then if it falls within a certain range
        that will define what they can afford
        1-25:  low income
        26-75: mid income
        76-99: high income

        :param income: The income of the user after tax
        :return: str — "low", "mid", or "high"
        """
        # Iterate in sorted order (1 → 99) so the first match is the correct bracket.
        # sorted() guarantees we check percentile 1 before 2 before 3 etc.
        for percentile in sorted(self.income_percentiles.keys()):
            if income <= self.income_percentiles[percentile]:
                # Found the first percentile whose threshold is >= the agent's income
                if percentile <= 25:
                    return "low"
                elif percentile <= 75:
                    return "mid"
                else:
                    return "high"

        # Fallback: income is above the 99th percentile value — still "high"
        return "high"

    def override_preferences(self, base_preferences, user_overrides):
        """
        Merge user-supplied overrides into the algorithm-generated preferences.
        Any key in user_overrides will replace the corresponding key in base_preferences.
        Keys not provided in user_overrides are left as the algorithm generated them.

        Input:
            - base_preferences (dict): Output from evaluate_preferences()
            - user_overrides (dict): Any subset of preference keys the user wants to set.

        Example user_overrides:
        {
            "preferred_location": "countryside",       # User wants countryside
            "preferred_property_types": ["detached"],  # User only wants detached
            "max_price": 400000                        # User has specific budget
        }

        Output: dict — merged preferences ready to pass into score_property()

        """
        merged = base_preferences.copy()
        merged.update(user_overrides)
        return merged

    def score_property(self, property_obj, preferences):
        """
        Score how well a specific property matches the final preferences.
        Called after evaluate_preferences() and optionally override_preferences().

        Input:
            - property_obj: House object (has .price, .property_type, .county, .district)
            - preferences (dict): Final preferences dict (from evaluate or override)

        Output: float (0-100) representing how well the property fits

        Scoring breakdown (uses weights from preferences["weights"]):
            - Price score:         Is the price within min_price → max_price?
                                   100 = within range, scales down outside range
            - Location score:      Does the county/district match preferred_location type?
                                   100 = exact match, 50 = partial, 0 = mismatch
            - Property type score: Is the property_type in preferred_property_types?
                                   100 = match, 0 = no match
            - Size score:          Does bedroom count fall within min_bedrooms → max_bedrooms?
                                   100 = within range, partial credit if close
                                   Use property_obj.get_bedrooms() — this returns the real
                                   bedroom count if known, or an estimate from type+price
                                   if the Land Registry data didn't include it.

        Final score:
            score = (price_score   * weights["price"]
                  +  location_score * weights["location"]
                  +  type_score     * weights["property_type"]
                  +  size_score     * weights["size"])

        Example size scoring:
            bedrooms = property_obj.get_bedrooms()
            if preferences["min_bedrooms"] <= bedrooms <= preferences["max_bedrooms"]:
                size_score = 100
            elif bedrooms < preferences["min_bedrooms"]:
                size_score = max(0, 100 - (preferences["min_bedrooms"] - bedrooms) * 25)
            else:
                size_score = max(0, 100 - (bedrooms - preferences["max_bedrooms"]) * 25)
        """
        # Price score
        if preferences["min_price"] <= property_obj.price <= preferences["max_price"]:
            price_score = 100
        elif property_obj.price < preferences["min_price"]:
            price_score = max(0, 100 - (preferences["min_price"] - property_obj.price) / preferences["min_price"] * 100)
        else:
            price_score = max(0, 100 - (property_obj.price - preferences["max_price"]) / preferences["max_price"] * 100)

        # Location score (simplified: county/district → location type)
        location_type = self.map_location_to_type(property_obj.county, property_obj.district)
        if location_type == preferences["preferred_location"]:
            location_score = 100
        elif self.is_partial_location_match(location_type, preferences["preferred_location"]):
            location_score = 50
        else:
            location_score = 0

        # Property type score
        if property_obj.property_type in preferences["preferred_property_types"]:
            type_score = 100
        else:
            type_score = 0

        # Size score
        bedrooms = property_obj.get_bedrooms()
        if preferences["min_bedrooms"] <= bedrooms <= preferences["max_bedrooms"]:
            size_score = 100
        elif bedrooms < preferences["min_bedrooms"]:
            size_score = max(0, 100 - (preferences["min_bedrooms"] - bedrooms) * 25)
        else:
            size_score = max(0, 100 - (bedrooms - preferences["max_bedrooms"]) * 25)

        # Final weighted score
        weights = preferences.get("weights", {"price": 0.4, "location": 0.3, "property_type": 0.2, "size": 0.1})
        final_score = (price_score * weights.get("price", 0.4) +
                       location_score * weights.get("location", 0.3) +
                       type_score * weights.get("property_type", 0.2) +
                       size_score * weights.get("size", 0.1))

        return final_score

    def map_location_to_type(self, county, district):
        """
        Function to make a fuzzy match of county or districts to where the user wants to be
        Will work out if the county is the county or district the user wanted, if not, how close
        to that county or district.
        :param county:
        :param district:
        :return:
        """
        # This is a placeholder implementation. Need more comprehensive mapping
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

    def is_partial_location_match(self, location_type, param):
        """
        Determines if the location type is a partial match to the preferred location.
        For example, if preferred_location is "suburban", then "city" might be a partial match
        because some city areas can feel suburban, but "countryside" would not be.

        This is a simplified example. In a real implementation, you'd want a more nuanced
        mapping based on actual geographic data.

        :param location_type: The location type of the property (e.g., "city", "suburban", "countryside")
        :param param: The user's preferred location type (e.g., "city", "suburban", "countryside")
        :return: True if it's a partial match, False otherwise
        """
        # Define some simple rules for partial matches:
        # Will be adjusted at a later date, ideal would be to compare the green areas to suburben or city in the district
        # to calculate if it is what the user wants.
        if param == "city" and location_type == "suburban":
            return True
        if param == "suburban" and location_type in ["city", "countryside"]:
            return True
        if param == "countryside" and location_type == "suburban":
            return True
        return False

#-----------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------

class FinancialAffordabilityEvaluator:
    """
    Evaluates whether an agent can afford a specific mortgage on a specific property.

    This class acts as the bridge between the agent's financial data and the
    MortgageCalculator. It:
      1. Uses MortgageCalculator.check_lending_criteria() to check bank approval rules
      2. Adds UK-standard age checks (agent must be 18-70, must finish before 75)
      3. Scores how comfortable the mortgage is beyond just pass/fail
    """

    def __init__(self):
        # No state needed — this is a pure evaluator.
        # MortgageProduct and MortgageCalculator are passed in per-call.
        pass

    def check_lending_criteria(self, agent_age, agent_income, deposit,
                               property_price, mortgage_product, mortgage_term=25):
        """
        Check whether the agent meets a bank's lending criteria for a specific product.
        Combines MortgageCalculator's built-in checks with age-based checks.

        Args:
            agent_age (int):            Agent's current age
            agent_income (float):       Annual gross income (before tax)
            deposit (float):            Deposit amount the agent has saved
            property_price (float):     Price of the property
            mortgage_product:           MortgageProduct object from Environment.Mortgages
            mortgage_term (int):        Repayment term in years (default 25)

        Returns:
            dict:
            {
                "passes":        bool   — True if ALL criteria are met
                "ltv":           float  — Actual loan-to-value ratio (e.g. 0.82 = 82%)
                "loan_amount":   float  — Actual loan amount (price - deposit)
                "monthly_payment": float — Calculated monthly repayment
                "age_at_end":    int    — Agent's age when mortgage finishes
                "failed_checks": list  — Human-readable list of reasons for rejection
                "flags":         list  — Warnings that don't block approval but are notable
            }
        """
        from Environment.Mortgages.MortgageCalculator import MortgageCalculator

        failed_checks = []
        flags = []

        # Age checks (not covered by MortgageCalculator)
        age_at_end = agent_age + mortgage_term

        if agent_age < 18:
            failed_checks.append("Agent must be at least 18 years old")
        if agent_age >= 70:
            failed_checks.append("Agent must be under 70 to apply for a new mortgage")
        if age_at_end > 75:
            failed_checks.append(
                f"Mortgage would end at age {age_at_end} — banks require completion before 75"
            )

        # Use MortgageCalculator to check deposit, LTV and income rules
        calculator = MortgageCalculator(
            mortgage_product=mortgage_product,
            property_price=property_price,
            deposit_amount=deposit,
            term_years=mortgage_term
        )

        approved, reason, available_after = calculator.check_lending_criteria(
            annual_gross_income=agent_income,
            existing_monthly_debts=0   # Existing debts not tracked yet — defaulting to 0
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

        # Soft flags (warnings, not failures)
        if ltv > 0.90:
            flags.append(f"High LTV: {ltv*100:.1f}% — expect higher interest rates")
        if age_at_end > 70:
            flags.append(f"Mortgage finishes at age {age_at_end} — lenders may scrutinise closely")

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
        Score how COMFORTABLE this mortgage is beyond just pass/fail lending criteria.
        Useful for comparing two mortgages that both technically pass — which one
        leaves the agent in a healthier financial position?

        Args:
            monthly_income (float):   Net monthly income (after tax)
            monthly_payment (float):  Proposed mortgage monthly payment
            monthly_expenses (float): Other regular outgoings (bills, food, transport)
            current_savings (float):  Current savings balance

        Returns:
            dict:
            {
                "score":              float  — 0 to 100 (higher = more comfortable)
                "available_monthly":  float  — Cash left after mortgage + expenses
                "income_ratio":       float  — Fraction of income consumed (0.0–1.0+)
                "has_emergency_fund": bool   — Has ≥ 6 months of expenses saved
                "comfort_label":      str    — "Comfortable" / "Acceptable" / "Tight" / "Unaffordable"
            }
        """
        # Cash remaining after mortgage + all other expenses
        available_monthly = monthly_income - monthly_payment - monthly_expenses

        # Fraction of net income consumed by mortgage + expenses
        total_outgoings = monthly_payment + monthly_expenses
        income_ratio = total_outgoings / monthly_income if monthly_income > 0 else 1.0

        # Emergency fund check: 6 months of expenses
        emergency_fund_target = monthly_expenses * 6
        has_emergency_fund = current_savings >= emergency_fund_target

        # Score from income ratio
        # < 50% outgoings = comfortable   → 80–100
        # 50–65% outgoings = acceptable   → 50–79
        # 65–80% outgoings = tight        → 20–49
        # > 80% outgoings = unaffordable  → 0–19
        if income_ratio <= 0.50:
            base_score = 100 - (income_ratio / 0.50) * 20      # 80–100
        elif income_ratio <= 0.65:
            base_score = 79 - ((income_ratio - 0.50) / 0.15) * 29  # 50–79
        elif income_ratio <= 0.80:
            base_score = 49 - ((income_ratio - 0.65) / 0.15) * 29  # 20–49
        else:
            base_score = max(0, 19 - ((income_ratio - 0.80) / 0.20) * 19)  # 0–19

        # Emergency fund bonus/penalty
        if has_emergency_fund:
            base_score = min(100, base_score + 5)   # Small comfort bonus
        else:
            base_score = max(0, base_score - 10)    # Penalty for no safety net

        # Label
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

#-----------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------


class HappinessEvaluator:
    """
    Calculates an agent's happiness score (0-100) from four independent components:

        1. Housing status  — having a home is fundamental        (±20)
        2. Financial security — savings vs debt comfort          (±15)
        3. Life events     — major positive/negative life events  (±15, capped)
        4. Age factor      — subtle modifier based on life stage  (±5)

    Each component is capped so no single factor completely dominates.
    The final score is always clamped to [0, 100].

    Also provides get_risk_tolerance() which converts happiness into a
    willingness-to-stretch multiplier used in mortgage decision-making.
    """

    # Lookup table of known life events and their happiness impact.
    # Add new events here — no logic changes needed elsewhere.
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
        Calculate overall happiness score (0-100).

        Args:
            housing_status (str):       "owned" | "renting" | "homeless"
            financial_security (float): 0-100 score (high = comfortable savings/low debt)
            life_events (list[str]):    Recent events, e.g. ["marriage", "job_loss"]
                                        Unknown events are silently ignored.
            age (int):                  Agent's current age

        Returns:
            dict:
            {
                "score":            float  — final clamped score (0-100)
                "housing_component":   float
                "financial_component": float
                "events_component":    float
                "age_component":       float
                "breakdown":        str    — readable summary
            }
        """
        # Base
        happiness = 50.0

        # Housing component (±20)
        housing_map = {
            "owned":    +20,
            "renting":  +10,
            "homeless": -20,
        }
        housing_component = housing_map.get(housing_status, 0)
        happiness += housing_component

        # Financial security component (±15)
        # financial_security is 0-100; map it to -15 → +15
        # Score of 50 = neutral (0 change), 100 = +15, 0 = -15
        financial_component = ((financial_security - 50) / 50) * 15
        financial_component = max(-15, min(15, financial_component))
        happiness += financial_component

        # Life events component (capped at ±15 total)
        raw_events_total = sum(
            self.EVENT_IMPACTS.get(event, 0) for event in life_events
        )
        events_component = max(-15, min(15, raw_events_total))
        happiness += events_component

        # Age factor (±5 subtle modifier)
        # Young: feel housing instability more sharply → amplify housing effect slightly
        # Mid-life: balanced
        # Later-life: financial security matters more → weight already captured above
        if 18 <= age <= 29:
            # Youth: more affected by being stuck renting vs owning
            age_component = -3 if housing_status == "renting" else +2
        elif 30 <= age <= 45:
            # Mid-life: family stress if events include children — already in events
            age_component = 0
        else:
            # Later life: financial security amplified slightly
            age_component = +3 if financial_security >= 60 else -3
        age_component = max(-5, min(5, age_component))
        happiness += age_component

        # Clamp to [0, 100]
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
                f"Age {age_component:+} → {final_score:.1f}"
            )
        }

    def get_risk_tolerance(self, happiness_score):
        """
        Convert a happiness score into a risk tolerance multiplier.
        Used to adjust mortgage decision thresholds - happier agents
        are more willing to stretch their budget.

        Args:
            happiness_score (float): 0-100

        Returns:
            float: 0.5 (very conservative) → 1.5 (very confident)

        Formula: smooth linear interpolation across the full range.
            happiness 0   → 0.5  (will only take the safest option)
            happiness 50  → 1.0  (standard behaviour)
            happiness 100 → 1.5  (willing to stretch)
        """
        # Clamp input
        score = max(0.0, min(100.0, happiness_score))
        # Linear: 0.5 + (score / 100) * 1.0
        return round(0.5 + (score / 100.0) * 1.0, 3)





