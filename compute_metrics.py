"""
compute_metrics.py - Computes key statistical metrics from simulation results.

Metrics computed:
    1.  R-squared          - how well salary growth fits a linear trend model
    2.  Homeownership rate - % of agents who own per year + overall average
    3.  Median FTB age     - median age at first purchase (UK benchmark: 33)
    4.  Deposit %          - actual deposit % at purchase (UK benchmark: 20%)
    5.  Median years to purchase - how long agents save before buying
    6.  Mortgage rate distribution - rates paid at purchase
    7.  Living situation breakdown - % in each living situation per year
    8.  Salary vs FTB age correlation - Pearson R between income and purchase age
    9.  Affordability ratio trajectory - house price / salary over time
    10. Debts and their values
"""

import os
import glob
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

# -----------------------------------------------------------------
# UK benchmark values (2024/25 sources)
# -----------------------------------------------------------------
UK_MEDIAN_FTB_AGE     = 33.0   # ONS / Halifax 2024
UK_AVG_DEPOSIT_PCT    = 20.0   # Halifax FTB report 2024
UK_AVG_MORTGAGE_RATE  = 4.5    # Bank of England 2024/25 average
UK_HOMEOWNERSHIP_RATE = 65.0   # ONS 2024 (all ages)
UK_MEDIAN_YEARS_SAVE  = 10.0   # Halifax: avg 10 years to save a deposit

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


def load_latest_results(path: str = None) -> pd.DataFrame:
    if path:
        print(f"Loading: {os.path.basename(path)}\n")
        return pd.read_csv(path)
    csv_files = glob.glob(os.path.join(RESULTS_DIR, "simulation_*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No simulation CSV files found in {RESULTS_DIR}")
    latest = max(csv_files, key=os.path.getmtime)
    print(f"Loading: {os.path.basename(latest)}\n")
    return pd.read_csv(latest)


_NUMERIC_COLS = [
    "gross_salary", "savings", "age", "sim_year", "deposit_pct",
    "deposit_paid", "property_price", "mortgage_rate", "ftb_age",
    "monthly_rent", "net_salary", "debt_overview",
]


def _annual_only(df):
    df = df.copy()
    # Coerce known numeric columns so arithmetic / sklearn won't see 'object' dtype
    for col in _NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df[df["month"] == "annual"].copy() if "month" in df.columns else df


def compute_r_squared(df):
    df = _annual_only(df)
    results = {}
    for agent_name, adf in df.groupby("agent"):
        adf = adf[adf["gross_salary"] > 0].sort_values("sim_year")
        if len(adf) < 2:
            results[agent_name] = None
            continue
        X = adf["sim_year"].values.reshape(-1, 1)
        y = adf["gross_salary"].values
        model = LinearRegression().fit(X, y)
        results[agent_name] = round(r2_score(y, model.predict(X)), 4)
    valid = df[df["gross_salary"] > 0]
    X_all = valid["sim_year"].values.reshape(-1, 1)
    y_all = valid["gross_salary"].values
    model_all = LinearRegression().fit(X_all, y_all)
    return {"per_agent": results, "overall": round(r2_score(y_all, model_all.predict(X_all)), 4)}


def compute_homeownership_rate(df):
    df = _annual_only(df).copy()
    df["is_homeowner"] = df["housing_status"].isin(["active_mortgage", "mortgage_paid_off"])
    per_year = df.groupby("sim_year")["is_homeowner"].mean().mul(100).round(1)
    return {
        "per_year_pct": per_year.to_dict(),
        "average_rate_pct": round(per_year.mean(), 2),
        "uk_benchmark_pct": UK_HOMEOWNERSHIP_RATE,
    }


def compute_median_ftb_age(df):
    df = _annual_only(df)
    if "ftb_age" in df.columns:
        ftb = df[df["ftb_age"].notna() & (df["ftb_age"] > 0)].copy()
    else:
        ftb = df[df["decision"] == "BUY"].copy()
        ftb["ftb_age"] = ftb["age"]
    if ftb.empty:
        return {"median_ftb_age": None, "mean_ftb_age": None,
                "per_agent_ftb_age": {}, "distribution": {},
                "uk_benchmark": UK_MEDIAN_FTB_AGE,
                "note": "No purchases found in this simulation run."}
    first_buy = ftb.sort_values("sim_year").groupby("agent").first().reset_index()
    ages = first_buy["ftb_age"].astype(float)
    bins   = [18, 25, 30, 35, 40, 45, 50, 60]
    labels = ["18-24", "25-29", "30-34", "35-39", "40-44", "45-49", "50+"]
    first_buy["age_band"] = pd.cut(ages, bins=bins, labels=labels, right=False)
    distribution = first_buy["age_band"].value_counts().sort_index().to_dict()
    median_age = round(ages.median(), 1)
    return {
        "median_ftb_age": median_age,
        "mean_ftb_age": round(ages.mean(), 1),
        "per_agent_ftb_age": dict(zip(first_buy["agent"], ages.round(0).astype(int))),
        "per_agent_year": dict(zip(first_buy["agent"], first_buy["sim_year"])),
        "distribution": {str(k): int(v) for k, v in distribution.items()},
        "uk_benchmark": UK_MEDIAN_FTB_AGE,
        "delta_vs_uk": round(median_age - UK_MEDIAN_FTB_AGE, 1),
    }


def compute_deposit_pct(df):
    df = _annual_only(df)
    if "deposit_pct" in df.columns:
        buy = df[df["deposit_pct"].notna() & (df["deposit_pct"] > 0)].copy()
        pct_col = "deposit_pct"
    else:
        buy = df[df["decision"] == "BUY"].copy()
        buy["deposit_pct"] = (buy["savings"] / (buy["gross_salary"] * 4.5) * 100).round(1)
        pct_col = "deposit_pct"
    if buy.empty:
        return {"median_deposit_pct": None, "mean_deposit_pct": None,
                "per_agent": {}, "uk_benchmark": UK_AVG_DEPOSIT_PCT, "note": "No purchases found."}
    first_buy = buy.sort_values("sim_year").groupby("agent").first().reset_index()
    pcts = first_buy[pct_col].astype(float)
    per_agent = {}
    for _, row in first_buy.iterrows():
        per_agent[row["agent"]] = {
            "deposit_pct": round(float(row[pct_col]), 1),
            "deposit_paid": round(float(row.get("deposit_paid") or 0), 0),
            "property_price": round(float(row.get("property_price") or 0), 0),
            "mortgage_rate": round(float(row.get("mortgage_rate") or 0), 2),
            "age_at_purchase": int(row.get("ftb_age") or row.get("age") or 0),
        }
    median_pct = round(pcts.median(), 1)
    return {
        "median_deposit_pct": median_pct,
        "mean_deposit_pct": round(pcts.mean(), 1),
        "per_agent": per_agent,
        "uk_benchmark": UK_AVG_DEPOSIT_PCT,
        "delta_vs_uk": round(median_pct - UK_AVG_DEPOSIT_PCT, 1),
    }


def compute_years_to_purchase(df):
    df = _annual_only(df)
    start_year = df.groupby("agent")["sim_year"].min()
    buy_rows = df[df["decision"] == "BUY"]
    if buy_rows.empty:
        return {"median_years": None, "mean_years": None, "per_agent": {},
                "uk_benchmark": UK_MEDIAN_YEARS_SAVE, "note": "No purchases found."}
    first_buy_year = buy_rows.groupby("agent")["sim_year"].min()
    years_taken = (first_buy_year - start_year).dropna()
    years_taken = years_taken[years_taken >= 0]
    never_bought = sorted(set(df["agent"].unique()) - set(first_buy_year.index))
    return {
        "median_years": round(years_taken.median(), 1),
        "mean_years": round(years_taken.mean(), 1),
        "per_agent": {a: int(y) for a, y in years_taken.items()},
        "never_bought": never_bought,
        "failed_to_buy_pct": round(len(never_bought) / df["agent"].nunique() * 100, 1),
        "uk_benchmark": UK_MEDIAN_YEARS_SAVE,
    }


def compute_mortgage_rate_stats(df):
    df = _annual_only(df)
    if "mortgage_rate" not in df.columns:
        return {"note": "mortgage_rate column not present."}
    buy = df[df["mortgage_rate"].notna() & (df["mortgage_rate"] > 0)]
    if buy.empty:
        return {"note": "No mortgage rates recorded.", "uk_benchmark_pct": UK_AVG_MORTGAGE_RATE}
    first_buy = buy.sort_values("sim_year").groupby("agent").first()["mortgage_rate"].astype(float)
    # Rates stored as decimals (0.045) — convert to %
    rates = first_buy * 100 if first_buy.mean() < 1 else first_buy
    return {
        "mean_rate_pct": round(rates.mean(), 2),
        "median_rate_pct": round(rates.median(), 2),
        "min_rate_pct": round(rates.min(), 2),
        "max_rate_pct": round(rates.max(), 2),
        "uk_benchmark_pct": UK_AVG_MORTGAGE_RATE,
        "delta_vs_uk": round(rates.mean() - UK_AVG_MORTGAGE_RATE, 2),
    }


def compute_living_situation_breakdown(df):
    df = _annual_only(df)
    if "living_situation" not in df.columns:
        return {"note": "living_situation column not present."}
    pivot = df.groupby(["sim_year", "living_situation"]).size().unstack(fill_value=0)
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0).mul(100).round(1)
    overall = df["living_situation"].value_counts(normalize=True).mul(100).round(1).to_dict()
    return {"per_year_pct": pivot_pct.to_dict(), "overall_pct": overall}


def compute_salary_ftb_correlation(df):
    df = _annual_only(df)
    if "ftb_age" in df.columns:
        buy = df[df["ftb_age"].notna() & (df["ftb_age"] > 0)].copy()
    else:
        buy = df[df["decision"] == "BUY"].copy()
        buy["ftb_age"] = buy["age"]
    if buy.empty or len(buy) < 3:
        return {"pearson_r": None, "note": "Insufficient data."}
    first_buy = buy.sort_values("sim_year").groupby("agent").first().reset_index()
    r = first_buy["gross_salary"].corr(first_buy["ftb_age"])
    strength = "strong" if abs(r) >= 0.7 else ("moderate" if abs(r) >= 0.4 else "weak")
    direction = "negative (higher earners buy younger)" if r < 0 else "positive"
    return {"pearson_r": round(r, 3), "strength": strength, "direction": direction, "n": len(first_buy)}


def compute_affordability_ratio(df):
    df = _annual_only(df)
    if "affordability_ratio" not in df.columns:
        return {"note": "affordability_ratio column not present."}
    per_year = df[df["affordability_ratio"] > 0].groupby("sim_year")["affordability_ratio"].mean().round(2)
    trend = "worsening" if len(per_year) >= 2 and per_year.iloc[-1] > per_year.iloc[0] else "improving"
    return {"per_year": per_year.to_dict(), "overall_mean": round(per_year.mean(), 2), "trend": trend}


def compute_all(df: pd.DataFrame) -> dict:
    """Run every metric and return combined results dict."""
    return {
        "r_squared":              compute_r_squared(df),
        "homeownership":          compute_homeownership_rate(df),
        "ftb_age":                compute_median_ftb_age(df),
        "deposit_pct":            compute_deposit_pct(df),
        "years_to_purchase":      compute_years_to_purchase(df),
        "mortgage_rates":         compute_mortgage_rate_stats(df),
        "living_situation":       compute_living_situation_breakdown(df),
        "salary_ftb_correlation": compute_salary_ftb_correlation(df),
        "affordability_ratio":    compute_affordability_ratio(df),
    }


def print_results(metrics: dict):
    sep = "═" * 62
    print(f"\n{sep}")
    print(f"  SIMULATION METRICS REPORT")
    print(sep)

    # 1. R-squared
    r2 = metrics.get("r_squared", {})
    print(f"\n  [1] R² — Salary Growth vs Linear Trend")
    print(f"      Overall R²: {r2.get('overall', 'N/A')}")
    print(f"      (1.0 = smooth growth; lower = life events disrupted salary)")
    for agent, val in sorted((r2.get("per_agent") or {}).items()):
        print(f"      {agent:<16} {val if val is not None else 'insufficient data'}")

    # 2. Homeownership
    ho = metrics.get("homeownership", {})
    avg = ho.get("average_rate_pct")
    bm  = ho.get("uk_benchmark_pct", UK_HOMEOWNERSHIP_RATE)
    delta_str = f"  (UK: {bm}%, Δ {avg - bm:+.1f}%)" if avg is not None else ""
    print(f"\n  [2] Homeownership Rate")
    print(f"      Average: {avg}%{delta_str}")
    for year, rate in sorted((ho.get("per_year_pct") or {}).items()):
        print(f"      {year}:  {rate:.1f}%")

    # 3. FTB age
    ftb = metrics.get("ftb_age", {})
    print(f"\n  [3] First-Time Buyer Age")
    if ftb.get("median_ftb_age") is None:
        print(f"      {ftb.get('note', 'No data.')}")
    else:
        med = ftb["median_ftb_age"]
        bm  = ftb.get("uk_benchmark", UK_MEDIAN_FTB_AGE)
        print(f"      Median: {med} yrs  Mean: {ftb.get('mean_ftb_age')} yrs  "
              f"(UK: {bm}, Δ {ftb.get('delta_vs_uk', 0):+.1f})")
        for band, count in (ftb.get("distribution") or {}).items():
            bar = "█" * min(count, 30)
            print(f"      {band:<8} {bar} {count}")
        print(f"      {'Agent':<16} {'Age':>4}  {'Year':>6}")
        for agent, age in sorted((ftb.get("per_agent_ftb_age") or {}).items()):
            yr = (ftb.get("per_agent_year") or {}).get(agent, "")
            print(f"      {agent:<16} {age:>4}  {str(yr):>6}")

    # 4. Deposit %
    dep = metrics.get("deposit_pct", {})
    print(f"\n  [4] Deposit at Purchase")
    if dep.get("median_deposit_pct") is None:
        print(f"      {dep.get('note', 'No data.')}")
    else:
        med = dep["median_deposit_pct"]
        bm  = dep.get("uk_benchmark", UK_AVG_DEPOSIT_PCT)
        print(f"      Median: {med}%  Mean: {dep.get('mean_deposit_pct')}%  "
              f"(UK: {bm}%, Δ {dep.get('delta_vs_uk', 0):+.1f}%)")
        print(f"      {'Agent':<16} {'Dep%':>6}  {'Price':>12}  {'Paid':>10}  {'Rate':>7}")
        for agent, d in sorted(dep["per_agent"].items()):
            price = f"£{d['property_price']:,.0f}" if d["property_price"] else "N/A"
            paid  = f"£{d['deposit_paid']:,.0f}"   if d["deposit_paid"]   else "N/A"
            rate  = f"{d['mortgage_rate']:.2f}%"   if d["mortgage_rate"]  else "N/A"
            print(f"      {agent:<16} {d['deposit_pct']:>5.1f}%  {price:>12}  {paid:>10}  {rate:>7}")

    # 5. Years to purchase
    ytp = metrics.get("years_to_purchase", {})
    print(f"\n  [5] Years to First Purchase")
    if ytp.get("median_years") is None:
        print(f"      {ytp.get('note', 'No data.')}")
    else:
        bm = ytp.get("uk_benchmark", UK_MEDIAN_YEARS_SAVE)
        print(f"      Median: {ytp['median_years']} yrs  Mean: {ytp['mean_years']} yrs  (UK: {bm} yrs)")
        nb = ytp.get("never_bought", [])
        print(f"      Never bought: {ytp.get('failed_to_buy_pct', 0):.0f}% of agents "
              f"({', '.join(nb[:6])}{'...' if len(nb) > 6 else ''})")
        for agent, yrs in sorted((ytp.get("per_agent") or {}).items()):
            print(f"      {agent:<16} {yrs:>4} yrs")

    # 6. Mortgage rates
    mr = metrics.get("mortgage_rates", {})
    if mr.get("median_rate_pct") is not None:
        print(f"\n  [6] Mortgage Rates at Purchase")
        print(f"      Median: {mr['median_rate_pct']}%  Mean: {mr['mean_rate_pct']}%  "
              f"Range: {mr['min_rate_pct']}%–{mr['max_rate_pct']}%")
        print(f"      UK benchmark: {mr.get('uk_benchmark_pct', UK_AVG_MORTGAGE_RATE)}%  "
              f"Δ mean {mr.get('delta_vs_uk', 0):+.2f}%")

    # 7. Living situation
    ls = metrics.get("living_situation", {})
    if ls.get("overall_pct"):
        print(f"\n  [7] Living Situation (all agent-years)")
        for situation, pct in sorted(ls["overall_pct"].items(), key=lambda x: -x[1]):
            bar = "█" * int(pct / 5)
            print(f"      {situation:<20} {bar:<20} {pct:.1f}%")

    # 8. Correlation
    corr = metrics.get("salary_ftb_correlation", {})
    if corr.get("pearson_r") is not None:
        print(f"\n  [8] Salary vs FTB Age (Pearson R)")
        print(f"      R = {corr['pearson_r']}  ({corr['strength']}, {corr['direction']})  n={corr['n']}")

    # 9. Affordability ratio
    af = metrics.get("affordability_ratio", {})
    if af.get("per_year"):
        print(f"\n  [9] Affordability Ratio (house price / salary)  — {af['trend']}")
        print(f"      Overall mean: {af['overall_mean']}")
        for year, ratio in sorted(af["per_year"].items()):
            print(f"      {year}:  {ratio:.2f}")


if __name__ == "__main__":
    df = load_latest_results()
    metrics = compute_all(df)
    print_results(metrics)
