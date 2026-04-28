# Comprehensive Test Plan - 60 Tests Across Entire Project

## Overview
This document outlines 60 tests across the entire Dissertation project, organised by module and test type.

**Test Distribution:**
- Unit Tests: 20
- Boundary/Edge Case Tests: 15
- Integration Tests: 12
- Data Validation Tests: 8
- Performance/Stress Tests: 3
- End-to-End Tests: 2
**Total: 60 tests**

---

## 1. FINANCIAL MODULE (12 tests)

### Unit Tests (4)
| ID | Component | Test | Purpose |
|---|---|---|---|
| FIN-UT-01 | DebtManager | `test_add_debt_basic` | Verify debt can be added with correct properties |
| FIN-UT-02 | ExpenseManager | `test_add_expense_basic` | Verify expense can be added to category |
| FIN-UT-03 | SalaryCalculator | `test_calculate_net_pay_basic` | Verify net pay calculation works |
| FIN-UT-04 | SavingsGoalManager | `test_add_goal_basic` | Verify savings goal can be created |

### Boundary/Edge Case Tests (4)
| ID | Component | Test | Purpose |
|---|---|---|---|
| FIN-BC-01 | DebtManager | `test_zero_debt_balance` | Handle zero balance debt |
| FIN-BC-02 | ExpenseManager | `test_negative_expense_rejected` | Reject negative expenses |
| FIN-BC-03 | SalaryCalculator | `test_zero_salary` | Handle £0 salary edge case |
| FIN-BC-04 | SDLT | `test_zero_property_price` | SDLT for £0 property |

### Integration Tests (2)
| ID | Components | Test | Purpose |
|---|---|---|---|
| FIN-INT-01 | Debt + Salary | `test_debt_plus_salary_deductions` | Debt and salary deductions work together |
| FIN-INT-02 | Expense + Savings | `test_expenses_reduce_savings_capacity` | Expenses impact savings goals |

### Data Validation Tests (2)
| ID | Component | Test | Purpose |
|---|---|---|---|
| FIN-DV-01 | ExpenseManager | `test_invalid_category_rejected` | Invalid expense categories rejected |
| FIN-DV-02 | SalaryCalculator | `test_invalid_ni_category` | Invalid NI category rejected |

---

## 2. ENVIRONMENT MODULE - HOUSING (12 tests)

### Unit Tests (4)
| ID | Component | Test | Purpose |
|---|---|---|---|
| HOUS-UT-01 | Housing | `test_create_housing_object` | Housing object creation |
| HOUS-UT-02 | Housing | `test_calculate_property_value` | Property value calculation |
| HOUS-UT-03 | fuzzy_utils | `test_fuzzy_match_location` | Fuzzy location matching |
| HOUS-UT-04 | vocab | `test_load_counties` | Load county vocabulary |

### Boundary/Edge Case Tests (4)
| ID | Component | Test | Purpose |
|---|---|---|---|
| HOUS-BC-01 | Housing | `test_negative_property_price` | Reject negative property price |
| HOUS-BC-02 | Housing | `test_max_property_price` | Handle very high property price (£10M+) |
| HOUS-BC-03 | fuzzy_utils | `test_zero_similarity_match` | Handle no match scenario |
| HOUS-BC-04 | Housing | `test_missing_location_data` | Handle missing location data |

### Integration Tests (2)
| ID | Components | Test | Purpose |
|---|---|---|---|
| HOUS-INT-01 | Housing + vocab | `test_housing_with_vocabulary` | Housing works with location vocab |
| HOUS-INT-02 | Housing + fuzzy | `test_housing_location_fuzzy_match` | Fuzzy matching for housing locations |

### Data Validation Tests (2)
| ID | Component | Test | Purpose |
|---|---|---|---|
| HOUS-DV-01 | Housing | `test_invalid_property_type` | Invalid property type rejected |
| HOUS-DV-02 | Housing | `test_invalid_bedrooms` | Invalid bedroom count rejected |

---

## 3. ENVIRONMENT MODULE - MORTGAGES (10 tests)

### Unit Tests (3)
| ID | Component | Test | Purpose |
|---|---|---|---|
| MORT-UT-01 | MortgageProduct | `test_create_mortgage_product` | Create mortgage product |
| MORT-UT-02 | MortgageCalculator | `test_calculate_monthly_payment` | Calculate monthly mortgage payment |
| MORT-UT-03 | MortgageProduct | `test_can_borrow_check` | Check lending criteria |

### Boundary/Edge Case Tests (3)
| ID | Component | Test | Purpose |
|---|---|---|---|
| MORT-BC-01 | MortgageCalculator | `test_zero_loan_amount` | Handle £0 loan |
| MORT-BC-02 | MortgageCalculator | `test_zero_interest_rate` | Handle 0% interest rate |
| MORT-BC-03 | MortgageProduct | `test_max_loan_amount` | Very high loan amount (£1M+) |

### Integration Tests (2)
| ID | Components | Test | Purpose |
|---|---|---|---|
| MORT-INT-01 | Mortgage + Housing | `test_mortgage_for_property` | Get mortgage for specific property |
| MORT-INT-02 | Mortgage + Salary | `test_affordability_check` | Check affordability with salary |

### Data Validation Tests (2)
| ID | Component | Test | Purpose |
|---|---|---|---|
| MORT-DV-01 | MortgageProduct | `test_invalid_product_data` | Invalid product data rejected |
| MORT-DV-02 | MortgageCalculator | `test_negative_interest_rate` | Negative rates rejected |

---

## 4. ENVIRONMENT MODULE - BANKS (8 tests)

### Unit Tests (3)
| ID | Component | Test | Purpose |
|---|---|---|---|
| BANK-UT-01 | Banks | `test_create_bank` | Create bank object |
| BANK-UT-02 | BankBranches | `test_create_branch` | Create bank branch |
| BANK-UT-03 | BranchManager | `test_get_branch_details` | Get branch information |

### Boundary/Edge Case Tests (2)
| ID | Component | Test | Purpose |
|---|---|---|---|
| BANK-BC-01 | Banks | `test_empty_branch_list` | Handle bank with no branches |
| BANK-BC-02 | BranchManager | `test_invalid_branch_id` | Invalid branch ID handling |

### Integration Tests (2)
| ID | Components | Test | Purpose |
|---|---|---|---|
| BANK-INT-01 | Bank + Mortgages | `test_bank_mortgage_products` | Get mortgages from bank |
| BANK-INT-02 | Bank + Branch | `test_branch_location_data` | Branch location information |

### Data Validation Tests (1)
| ID | Component | Test | Purpose |
|---|---|---|---|
| BANK-DV-01 | Banks | `test_invalid_bank_data` | Invalid bank data rejected |

---

## 5. ALGORITHMS MODULE (8 tests)

### Unit Tests (3)
| ID | Component | Test | Purpose |
|---|---|---|---|
| ALG-UT-01 | ResidentAlgorithms | `test_calculate_happiness` | Happiness calculation |
| ALG-UT-02 | ResidentAlgorithms | `test_evaluate_preferences` | Preference evaluation |
| ALG-UT-03 | Data_Extraction | `test_extract_property_data` | Extract property data |

### Boundary/Edge Case Tests (2)
| ID | Component | Test | Purpose |
|---|---|---|---|
| ALG-BC-01 | ResidentAlgorithms | `test_happiness_bounds` | Happiness stays 0-100 range |
| ALG-BC-02 | Fault_Modelling | `test_invalid_fault_type` | Invalid fault type rejected |

### Integration Tests (2)
| ID | Components | Test | Purpose |
|---|---|---|---|
| ALG-INT-01 | ResidentAlgorithms + Housing | `test_algorithm_with_housing_data` | Algorithms work with housing |
| ALG-INT-02 | Data_Extraction + Housing | `test_extract_from_housing_module` | Data extraction from housing |

### Data Validation Tests (1)
| ID | Component | Test | Purpose |
|---|---|---|---|
| ALG-DV-01 | Data_Extraction | `test_corrupted_data_handling` | Handle corrupted data gracefully |

---

## 6. AGENTS MODULE (6 tests)

### Unit Tests (2)
| ID | Component | Test | Purpose |
|---|---|---|---|
| AGENT-UT-01 | Resident_Agent | `test_create_agent` | Create resident agent |
| AGENT-UT-02 | Resident_Agent | `test_agent_properties` | Agent has correct properties |

### Boundary/Edge Case Tests (2)
| ID | Component | Test | Purpose |
|---|---|---|---|
| AGENT-BC-01 | Resident_Agent | `test_zero_salary_agent` | Agent with £0 salary |
| AGENT-BC-02 | Resident_Agent | `test_extremely_high_salary` | Agent with £500k+ salary |

### Integration Tests (1)
| ID | Components | Test | Purpose |
|---|---|---|---|
| AGENT-INT-01 | Agent + Housing + Banks | `test_agent_house_hunting` | Agent searches for houses |

### End-to-End Tests (1)
| ID | Components | Test | Purpose |
|---|---|---|---|
| AGENT-E2E-01 | Full System | `test_agent_complete_lifecycle` | Agent full lifecycle |

---

## 7. CROSS-MODULE TESTS (4 tests)

### Integration Tests (2)
| ID | Components | Test | Purpose |
|---|---|---|---|
| CROSS-INT-01 | All Modules | `test_agent_monthly_step` | Agent monthly update cycle |
| CROSS-INT-02 | All Modules | `test_agent_annual_step` | Agent annual update cycle |

### Performance/Stress Tests (2)
| ID | Components | Test | Purpose |
|---|---|---|---|
| CROSS-PERF-01 | All Modules | `test_multiple_agents_performance` | 100 agents run efficiently |
| CROSS-PERF-02 | All Modules | `test_large_dataset_performance` | Large housing dataset processing |

### End-to-End Tests (0)
| N/A | N/A | N/A | N/A |

---

## Test Execution Plan

### Completed Tests So Far
**All Unit Tests:**
- FIN-UT-01, FIN-UT-02, FIN-UT-03, FIN-UT-04
- HOUS-UT-01, HOUS-UT-02, HOUS-UT-03, HOUS-UT-04
- MORT-UT-01, MORT-UT-02, MORT-UT-03
- BANK-UT-01, BANK-UT-02, BANK-UT-03
- ALG-UT-01, ALG-UT-02, ALG-UT-03
- AGENT-UT-01, AGENT-UT-02

**Boundary Tests:**
- FIN-BC-01, FIN-BC-02
- HOUS-BC-01, HOUS-BC-02
- MORT-BC-01, MORT-BC-02
- BANK-BC-01
- ALG-BC-01
- AGENT-BC-01, AGENT-BC-02

### Incomplete Tests
- Remaining Boundary/Edge Case Tests (14)
- All Integration Tests (12)
- All Data Validation Tests (8)
- Performance/Stress Tests (3)
- End-to-End Tests (3)

---

## Test Data Requirements

### Financial Module
```python
# Salary levels
SALARY_LEVELS = {
    "low": 15000,
    "mid": 40000,
    "high": 100000,
    "very_high": 200000
}

# Debt examples
DEBT_EXAMPLES = {
    "credit_card": {"balance": 2000, "apr": 0.19, "min_payment": 50},
    "personal_loan": {"balance": 5000, "apr": 0.08, "min_payment": 150},
    "student_loan": {"balance": 30000, "apr": 0.05, "min_payment": 0}
}

# Monthly expenses
MONTHLY_EXPENSES = {
    "housing": 1200,
    "utilities": 150,
    "food": 400,
    "transport": 200,
    "insurance": 100
}
```

### Housing Module
```python
# Property examples
PROPERTY_EXAMPLES = {
    "cheap": {"price": 150000, "bedrooms": 2, "location": "rural"},
    "average": {"price": 350000, "bedrooms": 3, "location": "city"},
    "expensive": {"price": 750000, "bedrooms": 4, "location": "london"},
    "luxury": {"price": 2000000, "bedrooms": 5, "location": "london"}
}

# Property types
PROPERTY_TYPES = ["flat", "house", "detached", "bungalow"]

# Locations
LOCATIONS = ["london", "manchester", "birmingham", "bristol", "rural"]
```

### Mortgage Module
```python
# Mortgage products
MORTGAGE_PRODUCTS = {
    "fixed_2yr": {"rate": 0.045, "term": 2, "min_deposit": 0.15},
    "fixed_5yr": {"rate": 0.050, "term": 5, "min_deposit": 0.15},
    "variable": {"rate": 0.055, "term": None, "min_deposit": 0.20}
}

# Loan amounts
LOAN_AMOUNTS = [50000, 100000, 250000, 500000, 750000]
```

### Agent Module
```python
# Agent profiles
AGENT_PROFILES = {
    "young_professional": {"age": 28, "salary": 45000, "savings": 15000},
    "family": {"age": 35, "salary": 80000, "savings": 50000, "children": 2},
    "first_time_buyer": {"age": 25, "salary": 30000, "savings": 5000},
    "high_earner": {"age": 45, "salary": 200000, "savings": 300000}
}
```

---

## Performance Benchmarks

### Unit Tests
- Target: < 100ms per test
- Total: < 1 second

### Boundary Tests  
- Target: < 100ms per test
- Total: < 2 seconds

### Integration Tests
- Target: < 200ms per test
- Total: < 3 seconds

### Data Validation Tests
- Target: < 100ms per test
- Total: < 1 second

### Performance/Stress Tests
- Multiple agents (100): < 10 seconds
- Large dataset (100k records): < 5 seconds

### End-to-End Tests
- Target: < 1000ms per test
- Total: < 3 seconds

---

## Pass Criteria

### All Test Types
- Must pass 100%
- No warnings or deprecations
- Memory usage reasonable
- Execution time within benchmarks

### Coverage Requirements
- Financial: 100% coverage
- Housing: 90%+ coverage
- Mortgages: 85%+ coverage
- Banks: 85%+ coverage
- Algorithms: 85%+ coverage
- Agents: 80%+ coverage

### Edge Cases
- Zero values handled
- Negative values rejected appropriately
- Maximum values handled
- Missing data handled gracefully
- Invalid data rejected

---

## Test Execution Commands

### Run All Tests
```bash
python -m pytest tests/test_comprehensive.py -v
```

### Run by Test Type
```bash
# Unit tests only
python -m pytest tests/test_comprehensive.py -k "UT" -v

# Boundary tests only
python -m pytest tests/test_comprehensive.py -k "BC" -v

# Integration tests only
python -m pytest tests/test_comprehensive.py -k "INT" -v

# Performance tests only
python -m pytest tests/test_comprehensive.py -k "PERF" -v

# End-to-end tests only
python -m pytest tests/test_comprehensive.py -k "E2E" -v
```

### Run by Module
```bash
# Financial module tests
python -m pytest tests/test_comprehensive.py -k "FIN" -v

# Housing module tests
python -m pytest tests/test_comprehensive.py -k "HOUS" -v

# Mortgage module tests
python -m pytest tests/test_comprehensive.py -k "MORT" -v

# Bank module tests
python -m pytest tests/test_comprehensive.py -k "BANK" -v

# Algorithm module tests
python -m pytest tests/test_comprehensive.py -k "ALG" -v

# Agent module tests
python -m pytest tests/test_comprehensive.py -k "AGENT" -v
```

---

## Summary

**Total Tests Planned: 60**
- Unit Tests: 20 (all implemented and passing)
- Boundary Tests: 15 (8 implemented, 7 remaining)
- Integration Tests: 12 (pending implementation)
- Data Validation Tests: 8 (pending implementation)
- Performance Tests: 3 (pending implementation)
- End-to-End Tests: 2 (pending implementation)

**Modules Covered: 6**
- Financial
- Environment (Housing, Mortgages, Banks)
- Algorithms
- Agents

**Currently Implemented:** 28 tests  
**Tests Remaining:** 32 tests  

**Target Execution Time:** Less than 15 seconds for full suite  
**Target Coverage:** 85 percent or higher overall

---

**Last Updated:** April 16, 2026  
**Status:** Implementing comprehensive test suite
**Current Progress:** Unit tests complete and passing

