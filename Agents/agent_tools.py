"""
Agent Tools - Wrapper functions that expose existing algorithm and financial
classes as LangChain tools the LLM can call.

Each tool:
  - Takes simple inputs (str, int, float) so the LLM can pass them directly.
  - Calls the real class method internally via closure over the agent.
  - Returns a human-readable string the LLM can reason about.

The ResidentAgent passes its own state into these functions via closures
(see build_agent_tools below).
"""

from langchain_core.tools import tool

from Environment.Mortgages.MortgageProduct import MortgageProduct


def build_agent_tools(agent):
    """
    Create LangChain tool functions bound to a specific ResidentAgent
    instance. Called inside ResidentAgent.__init__() after all classes
    are initialised.

    :param agent: The ResidentAgent instance the tools will read from and write to.
    :return: List of tool-decorated functions the LangChain agent can call.
    """

    # ----------------------------------------------------------------
    #  FINANCE TOOL
    # ----------------------------------------------------------------

    @tool
    def check_my_finances() -> str:
        """Check your current financial situation - net income, expenses, and available funds."""

        # Recalculate to make sure the numbers are up to date
        state = agent.update_financial_state()
        net_monthly = state["net_salary"] / 12
        expenses = state["total_expenses_monthly"]
        available = agent.monthly_available_funds

        return (f"Gross salary: £{agent.gross_salary:,.0f}/year. "
                f"Net monthly: £{net_monthly:,.0f}. "
                f"Monthly expenses: £{expenses:,.0f}. "
                f"Available after expenses: £{available:,.0f}. "
                f"Current savings: £{agent.financial_state['savings']:,.0f}.")

    # ----------------------------------------------------------------
    #  HOUSING PREFERENCES TOOL
    # ----------------------------------------------------------------

    @tool
    def get_my_housing_preferences() -> str:
        """Find out what kind of property would suit you based on your age, income, and family size."""

        # Generate preferences using the evaluator algorithm
        prefs = agent.housing_preference_evaluator.evaluate_preferences(
            agent.age, agent.gross_salary, family_size=agent.family_size
        )
        # Store them on the agent so other tools can use them
        agent.housing_preferences = prefs

        return (f"Preferred location: {prefs['preferred_location']}. "
                f"Property types: {', '.join(prefs['preferred_property_types'])}. "
                f"Bedrooms: {prefs['min_bedrooms']}-{prefs['max_bedrooms']}. "
                f"Budget: £{prefs['min_price']:,.0f} - £{prefs['max_price']:,.0f}.")

    # ----------------------------------------------------------------
    #  PROPERTY SEARCH TOOL
    # ----------------------------------------------------------------

    @tool
    def search_available_properties(max_price: float, property_type: str = None) -> str:
        """Search the housing market for properties within your budget.

        :param max_price: Maximum price you can afford.
        :param property_type: Optional filter - 'flat', 'terraced', 'semi_detached', 'detached'.
        """
        if agent.housing_market is None:
            return "No housing market connected. Cannot search for properties."

        if not agent.housing_market.houses:
            return "Housing market has no data loaded. Load year data first."

        # Build the property_types filter list for the search method
        type_filter = [property_type] if property_type else None

        # Pull price floor and county filters from preferences if available
        prefs = agent.housing_preferences
        min_price = prefs.get("min_price", None) if prefs else None
        counties = prefs.get("counties", None) if prefs else None

        # Run the search on the housing market
        results = agent.housing_market.search(
            min_price=min_price,
            max_price=max_price,
            property_types=type_filter,
            counties=counties,
        )

        if not results:
            return f"No properties found under £{max_price:,.0f}. Try increasing your budget."

        # Store full results so other tools (score_a_property) can reference them
        agent.last_search_results = results

        # Return the top 5 to the LLM so it does not get overwhelmed
        top = results[:5]
        lines = [f"Found {len(results)} properties (showing top 5):"]
        for i, h in enumerate(top):
            beds = h.get_bedrooms()
            lines.append(
                f"  [{i}] £{h.price:,.0f} - {h.property_type}, {beds} bed, "
                f"{h.district}, {h.county} ({h.postcode})"
            )

        return "\n".join(lines)

    # ----------------------------------------------------------------
    #  MORTGAGE ELIGIBILITY TOOL
    # ----------------------------------------------------------------

    @tool
    def check_mortgage_eligibility(property_price: float, deposit: float, bank_name: str) -> str:
        """Check if you can get a mortgage from a specific bank for a given property price.

        :param property_price: Price of the property.
        :param deposit: How much deposit you have.
        :param bank_name: Which bank to check (nationwide, hsbc, barclays, lloyds).
        """
        # Find the bank in the agent's bank list by matching name
        target_bank = None
        for bank in agent.banks_list:
            if bank.bank_name.lower() == bank_name.lower():
                target_bank = bank
                break

        if target_bank is None:
            return f"Bank '{bank_name}' not found. Available: {[b.bank_name for b in agent.banks_list]}"

        # Collect all unique product IDs across every branch of this bank
        all_product_ids = set()
        for branch in target_bank.get_all_branches():
            all_product_ids.update(branch.available_products)

        if not all_product_ids:
            return f"{bank_name} has no mortgage products available."

        # Check each mortgage product against lending criteria
        results = []
        for product_id in sorted(all_product_ids):
            try:
                product = MortgageProduct(product_id)
            except KeyError:
                continue  # Skip if product ID is not in the products catalogue

            # Run the lending criteria check via the evaluator
            check = agent.financial_affordability_evaluator.check_lending_criteria(
                agent_age=agent.age,
                agent_income=agent.gross_salary,
                deposit=deposit,
                property_price=property_price,
                mortgage_product=product
            )

            # Format the result line for the LLM
            status = "APPROVED" if check["passes"] else "REJECTED"
            result_line = (
                f"{status} | {product.name} ({product.type}) @ {product.rate}% | "
                f"Monthly: £{check['monthly_payment']:,.0f} | "
                f"LTV: {check['ltv']*100:.0f}%"
            )
            if not check["passes"]:
                result_line += f" | Reasons: {'; '.join(check['failed_checks'])}"
            if check["flags"]:
                result_line += f" | Warnings: {'; '.join(check['flags'])}"

            results.append(result_line)

        header = f"--- {target_bank.bank_name} Mortgage Products for £{property_price:,.0f} (deposit £{deposit:,.0f}) ---"
        return header + "\n" + "\n".join(results)

    # ----------------------------------------------------------------
    #  PROPERTY SCORING TOOL
    # ----------------------------------------------------------------

    @tool
    def score_a_property(property_index: int) -> str:
        """Score how well a specific property matches your preferences.

        :param property_index: Index of the property from your last search results.
        """
        if not agent.last_search_results:
            return "No search results available. Run search_available_properties first."

        if property_index < 0 or property_index >= len(agent.last_search_results):
            return f"Invalid index. Must be 0 to {len(agent.last_search_results) - 1}."

        if not agent.housing_preferences:
            return "No preferences set. Run get_my_housing_preferences first."

        # Grab the property and score it against the agent's preferences
        property_obj = agent.last_search_results[property_index]
        score = agent.housing_preference_evaluator.score_property(
            property_obj, agent.housing_preferences
        )
        beds = property_obj.get_bedrooms()
        return (f"Property [{property_index}] scores {score:.1f}/100 - "
                f"£{property_obj.price:,.0f} {property_obj.property_type}, "
                f"{beds} bed in {property_obj.district}")

    # ----------------------------------------------------------------
    #  HAPPINESS TOOL
    # ----------------------------------------------------------------

    @tool
    def check_my_happiness() -> str:
        """Check your current happiness and what is affecting it."""

        # Work out whether the agent owns or rents
        if agent.current_property is not None:
            housing_status = "owned"
        else:
            housing_status = "renting"

        # Financial security: 0-100 based on savings vs 6 months of expenses
        monthly_expenses = max(agent.financial_state["total_expenses_monthly"], 1)
        savings = agent.financial_state["savings"]
        financial_security = min(100, (savings / (monthly_expenses * 6)) * 100)

        # Only pass the last 3 events so old events fade over time
        recent_events = agent.life_events[-3:]

        # Delegate the scoring to the happiness evaluator
        result = agent.happiness_evaluator.calculate_happiness_score(
            housing_status, financial_security, recent_events, agent.age
        )

        return result["breakdown"]

    # ----------------------------------------------------------------
    #  MORTGAGE AFFORDABILITY TOOL
    # ----------------------------------------------------------------

    @tool
    def calculate_mortgage_affordability(monthly_payment: float) -> str:
        """Check how comfortable a specific monthly mortgage payment would be.

        :param monthly_payment: The proposed monthly mortgage payment amount.
        """
        net_monthly = agent.financial_state["net_salary"] / 12
        expenses = agent.financial_state["total_expenses_monthly"]
        savings = agent.financial_state["savings"]

        # Run the affordability scorer
        result = agent.financial_affordability_evaluator.calculate_affordability_score(
            monthly_income=net_monthly,
            monthly_payment=monthly_payment,
            monthly_expenses=expenses,
            current_savings=savings
        )
        return (f"Affordability score: {result['score']}/100 - {result['comfort_label']}. "
                f"£{result['available_monthly']:,.0f}/mo left over. "
                f"Income ratio: {result['income_ratio']:.0%}. "
                f"Emergency fund: {'Yes' if result['has_emergency_fund'] else 'No'}.")

    # ----------------------------------------------------------------
    #  LIFE EVENT TOOL
    # ----------------------------------------------------------------

    @tool
    def apply_life_event(event_type: str) -> str:
        """Record a major life event that affects your finances, family, or happiness.

        Known events that change your real situation:
          job_promotion         - salary increases by 10%
          salary_increase       - salary increases by 5%
          job_loss              - salary drops to 0
          marriage              - family size +1
          birth_child           - family size +1, adds 250/mo expenses
          divorce               - family size -1
          debt_increase         - adds 5,000 debt
          property_repossessed  - lose your home, back to renting

        Events that only affect happiness (no state change):
          bereavement, serious_illness, paid_off_debt

        :param event_type: The event name (e.g. 'job_promotion', 'birth_child').
        """

        result = agent.apply_life_event(event_type)

        # Format the output for the LLM
        lines = [f"Life event: {event_type}"]
        for change in result["changes"]:
            lines.append(f"  - {change}")
        lines.append(f"  Happiness: {result['new_happiness']:.0f}/100 "
                      f"(change: {result['happiness_change']:+.1f})")

        return "\n".join(lines)

    # Return all tools as a list
    return [
        check_my_finances,
        get_my_housing_preferences,
        search_available_properties,
        check_mortgage_eligibility,
        score_a_property,
        check_my_happiness,
        calculate_mortgage_affordability,
        apply_life_event,
    ]
