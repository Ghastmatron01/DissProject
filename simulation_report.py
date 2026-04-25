"""
simulation_report.py - Runs the synthetic agent simulation and produces
a full statistical report with graphs.

Metrics reported:
    - R-squared of salary growth vs linear trend (per agent and overall)
    - Median first-time buyer age
    - Average deposit as a percentage of property price
    - Model accuracy against UK benchmarks

Graphs produced:
    1. FTB age distribution (histogram)
    2. Deposit % at purchase (bar chart)
    3. Salary growth over time per background group (line chart)
    4. Savings trajectory per agent (line chart)
    5. Homeownership rate over time (line chart)
    6. Life event frequency (bar chart)
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

from synthetic_agents import run_synthetic_simulation, AGENT_PROFILES, SIM_MAX_YEARS

# -----------------------------------------------------------------
# Constants - UK benchmark values for accuracy comparison
# -----------------------------------------------------------------

UK_MEDIAN_FTB_AGE      = 33.0    # ONS 2024
UK_AVG_DEPOSIT_PCT     = 20.0    # Halifax/Nationwide 2024
UK_AVG_MORTGAGE_RATE   = 4.5     # Bank of England 2024/25 average
UK_HOMEOWNERSHIP_RATE  = 65.0    # ONS 2024 (all ages)

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
GRAPHS_DIR  = os.path.join(RESULTS_DIR, "graphs")
os.makedirs(GRAPHS_DIR, exist_ok=True)

# -----------------------------------------------------------------
# Metric functions
# -----------------------------------------------------------------

def compute_r_squared(df: pd.DataFrame) -> dict:
    """
    Computes R-squared for each agent's salary growth against a linear
    trend (year as X, gross salary as Y).

    R2 close to 1.0 means salary follows a smooth upward line, validating
    that the 2.5% annual growth model is consistent.

    :param df: simulation DataFrame
    :return: dictionary with per-agent R2 and overall R2
    """
    results = {}

    for agent_name, agent_df in df.groupby("agent"):
        agent_df = agent_df.sort_values("sim_year")
        if len(agent_df) < 2:
            results[agent_name] = None
            continue
        X = agent_df["sim_year"].values.reshape(-1, 1)
        y = agent_df["gross_salary"].values
        model = LinearRegression().fit(X, y)
        results[agent_name] = round(r2_score(y, model.predict(X)), 4)

    # Overall across all agents
    X_all    = df["sim_year"].values.reshape(-1, 1)
    y_all    = df["gross_salary"].values
    model_all= LinearRegression().fit(X_all, y_all)
    overall  = round(r2_score(y_all, model_all.predict(X_all)), 4)

    return {"per_agent": results, "overall": overall}


def compute_ftb_metrics(df: pd.DataFrame) -> dict:
    """
    Computes first-time buyer age statistics.

    :param df: simulation DataFrame
    :return: dictionary of FTB age statistics
    """
    buy_rows = df[df["decision"] == "BUY"].copy()
    if buy_rows.empty:
        return {"median": None, "mean": None, "ages": []}
    ages = buy_rows["age"].tolist()
    return {
        "median":      round(np.median(ages), 1),
        "mean":        round(np.mean(ages), 1),
        "min":         min(ages),
        "max":         max(ages),
        "ages":        ages,
        "per_agent":   dict(zip(buy_rows["agent"], buy_rows["age"])),
        "total_buyers":len(ages),
        "never_bought":len(AGENT_PROFILES) - len(ages),
    }


def compute_deposit_metrics(df: pd.DataFrame) -> dict:
    """
    Computes deposit percentage and mortgage rate statistics at purchase.

    :param df: simulation DataFrame
    :return: dictionary of deposit statistics
    """
    buy_rows = df[df["decision"] == "BUY"].copy()
    if buy_rows.empty:
        return {}
    return {
        "avg_deposit_pct":    round(buy_rows["actual_deposit_pct"].mean(), 2),
        "median_deposit_pct": round(buy_rows["actual_deposit_pct"].median(), 2),
        "avg_rate":           round(buy_rows["mortgage_rate_pct"].mean(), 3),
        "deposits":           buy_rows["actual_deposit_pct"].tolist(),
        "agents":             buy_rows["agent"].tolist(),
        "rates":              buy_rows["mortgage_rate_pct"].tolist(),
    }


def compute_model_accuracy(ftb: dict, deposit: dict, df: pd.DataFrame) -> dict:
    """
    Compares simulation outputs against real UK benchmark values and
    computes a percentage accuracy score for each metric.

    :param ftb: FTB age metrics
    :param deposit: deposit metrics
    :param df: simulation DataFrame
    :return: dictionary of accuracy scores per metric
    """
    results = {}

    # FTB age accuracy
    if ftb.get("median") is not None:
        diff = abs(ftb["median"] - UK_MEDIAN_FTB_AGE)
        results["ftb_age_accuracy_pct"] = round(max(0, 100 - (diff / UK_MEDIAN_FTB_AGE * 100)), 1)
        results["ftb_age_sim"]          = ftb["median"]
        results["ftb_age_benchmark"]    = UK_MEDIAN_FTB_AGE

    # Deposit accuracy
    if deposit.get("avg_deposit_pct") is not None:
        diff = abs(deposit["avg_deposit_pct"] - UK_AVG_DEPOSIT_PCT)
        results["deposit_accuracy_pct"] = round(max(0, 100 - (diff / UK_AVG_DEPOSIT_PCT * 100)), 1)
        results["deposit_sim"]          = deposit["avg_deposit_pct"]
        results["deposit_benchmark"]    = UK_AVG_DEPOSIT_PCT

    # Mortgage rate accuracy
    if deposit.get("avg_rate") is not None:
        diff = abs(deposit["avg_rate"] - UK_AVG_MORTGAGE_RATE)
        results["rate_accuracy_pct"] = round(max(0, 100 - (diff / UK_AVG_MORTGAGE_RATE * 100)), 1)
        results["rate_sim"]          = deposit["avg_rate"]
        results["rate_benchmark"]    = UK_AVG_MORTGAGE_RATE

    # Homeownership rate accuracy
    buyers_pct = (len(AGENT_PROFILES) - ftb.get("never_bought", 0)) / len(AGENT_PROFILES) * 100
    diff = abs(buyers_pct - UK_HOMEOWNERSHIP_RATE)
    results["homeownership_accuracy_pct"] = round(max(0, 100 - (diff / UK_HOMEOWNERSHIP_RATE * 100)), 1)
    results["homeownership_sim"]          = round(buyers_pct, 1)
    results["homeownership_benchmark"]    = UK_HOMEOWNERSHIP_RATE

    # Overall score = mean of individual accuracies
    acc_scores = [v for k, v in results.items() if k.endswith("_accuracy_pct")]
    results["overall_accuracy_pct"] = round(np.mean(acc_scores), 1)

    return results


# -----------------------------------------------------------------
# Graph functions
# -----------------------------------------------------------------

def plot_ftb_age_distribution(ftb: dict, ax):
    """
    Plots a histogram of first-time buyer ages with the UK benchmark line.

    :param ftb: FTB age metrics dictionary
    :param ax: matplotlib axes object
    """
    ages = ftb.get("ages", [])
    if not ages:
        ax.text(0.5, 0.5, "No buyers", ha="center", va="center")
        return

    ax.hist(ages, bins=range(min(ages), max(ages) + 2), color="#4C72B0",
            edgecolor="white", alpha=0.85, rwidth=0.8)
    ax.axvline(ftb["median"], color="#DD4444", linewidth=2,
               label=f"Simulation median: {ftb['median']}")
    ax.axvline(UK_MEDIAN_FTB_AGE, color="#FF8800", linewidth=2, linestyle="--",
               label=f"UK benchmark: {UK_MEDIAN_FTB_AGE}")
    ax.set_title("First-Time Buyer Age Distribution", fontweight="bold")
    ax.set_xlabel("Age at First Purchase")
    ax.set_ylabel("Number of Agents")
    ax.legend(fontsize=8)
    ax.set_xticks(range(min(ages), max(ages) + 2))


def plot_deposit_percentages(deposit: dict, ax):
    """
    Plots a bar chart of deposit percentage at purchase per agent.

    :param deposit: deposit metrics dictionary
    :param ax: matplotlib axes object
    """
    if not deposit.get("agents"):
        ax.text(0.5, 0.5, "No buyers", ha="center", va="center")
        return

    agents   = deposit["agents"]
    deposits = deposit["deposits"]
    colours  = ["#4C72B0" if d >= 20 else "#DD8800" if d >= 10 else "#DD4444"
                for d in deposits]

    bars = ax.bar(agents, deposits, color=colours, edgecolor="white", alpha=0.85)
    ax.axhline(UK_AVG_DEPOSIT_PCT, color="#FF8800", linewidth=2, linestyle="--",
               label=f"UK benchmark: {UK_AVG_DEPOSIT_PCT}%")
    ax.axhline(deposit["avg_deposit_pct"], color="#4C72B0", linewidth=2,
               label=f"Simulation avg: {deposit['avg_deposit_pct']}%")

    for bar, val in zip(bars, deposits):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{val:.1f}%", ha="center", va="bottom", fontsize=7)

    ax.set_title("Deposit % of Property Price at Purchase", fontweight="bold")
    ax.set_xlabel("Agent")
    ax.set_ylabel("Deposit (%)")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(fontsize=8)


def plot_salary_growth_by_group(df: pd.DataFrame, ax):
    """
    Plots average salary trajectory over time for each background group.

    :param df: simulation DataFrame
    :param ax: matplotlib axes object
    """
    colours = {"graduate": "#4C72B0", "apprentice": "#DD8800",
               "mid_career": "#55A868", "tech_grad": "#C44E52", "high_cost": "#8172B2",
               "older_renter": "#64B5CD", "divorcee": "#E07B54",
               "late_high_earner": "#6ABF69", "older_modest": "#B0A0C8"}

    for background, group_df in df.groupby("background"):
        avg_salary = group_df.groupby("sim_year")["gross_salary"].mean()
        ax.plot(avg_salary.index, avg_salary.values / 1000,
                label=background.replace("_", " ").title(),
                color=colours.get(background, "#999999"),
                linewidth=2, marker="o", markersize=3)

    ax.set_title("Average Salary Growth by Background Group", fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Average Gross Salary (£k)")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)


def plot_savings_trajectories(df: pd.DataFrame, ax):
    """
    Plots savings over time for each agent, coloured by background.

    :param df: simulation DataFrame
    :param ax: matplotlib axes object
    """
    colours = {"graduate": "#4C72B0", "apprentice": "#DD8800",
               "mid_career": "#55A868", "tech_grad": "#C44E52", "high_cost": "#8172B2",
               "older_renter": "#64B5CD", "divorcee": "#E07B54",
               "late_high_earner": "#6ABF69", "older_modest": "#B0A0C8"}
    seen_bg = set()

    for agent, agent_df in df.groupby("agent"):
        agent_df = agent_df.sort_values("sim_year")
        bg       = agent_df["background"].iloc[0]
        colour   = colours.get(bg, "#999999")
        label    = bg.replace("_", " ").title() if bg not in seen_bg else None
        seen_bg.add(bg)
        ax.plot(agent_df["sim_year"], agent_df["savings"] / 1000,
                color=colour, alpha=0.5, linewidth=1, label=label)

        # Mark the purchase point
        buy_row = agent_df[agent_df["decision"] == "BUY"]
        if not buy_row.empty:
            ax.scatter(buy_row["sim_year"], buy_row["savings"] / 1000,
                       color=colour, s=40, zorder=5)

    ax.set_title("Savings Trajectories (dot = purchase)", fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Savings (£k)")
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(axis="y", alpha=0.3)


def plot_homeownership_rate(df: pd.DataFrame, ax):
    """
    Plots the cumulative percentage of agents who have bought by each year.

    :param df: simulation DataFrame
    :param ax: matplotlib axes object
    """
    buy_years = df[df["decision"] == "BUY"].groupby("sim_year").size().cumsum()
    total     = len(AGENT_PROFILES)
    pct       = (buy_years / total * 100).reindex(
        range(df["sim_year"].min(), df["sim_year"].max() + 1), fill_value=None
    ).ffill().fillna(0)

    ax.fill_between(pct.index, pct.values, alpha=0.3, color="#4C72B0")
    ax.plot(pct.index, pct.values, color="#4C72B0", linewidth=2,
            label="Simulation homeownership %")
    ax.axhline(UK_HOMEOWNERSHIP_RATE, color="#FF8800", linewidth=2, linestyle="--",
               label=f"UK benchmark: {UK_HOMEOWNERSHIP_RATE}%")

    ax.set_title("Cumulative Homeownership Rate Over Time", fontweight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Agents Who Have Bought (%)")
    ax.set_ylim(0, 105)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)


def plot_life_events(df: pd.DataFrame, ax):
    """
    Plots a horizontal bar chart of life event frequency.

    :param df: simulation DataFrame
    :param ax: matplotlib axes object
    """
    counts = {}
    for events_str in df["life_events"].dropna():
        for event in events_str.split(", "):
            if event:
                key = event.split("(")[0]
                counts[key] = counts.get(key, 0) + 1

    if not counts:
        return

    events = sorted(counts, key=counts.get)
    values = [counts[e] for e in events]
    colours = ["#C44E52" if "loss" in e or "divorce" in e or "bereavem" in e
               else "#55A868" if "inherit" in e or "promo" in e
               else "#4C72B0" for e in events]

    ax.barh(events, values, color=colours, edgecolor="white", alpha=0.85)
    for i, v in enumerate(values):
        ax.text(v + 0.2, i, str(v), va="center", fontsize=8)

    ax.set_title("Life Event Frequency Across All Agents", fontweight="bold")
    ax.set_xlabel("Count")
    ax.grid(axis="x", alpha=0.3)


def plot_model_accuracy(accuracy: dict, ax):
    """
    Plots a bar chart comparing simulation metrics to UK benchmarks.

    :param accuracy: accuracy metrics dictionary
    :param ax: matplotlib axes object
    """
    labels  = ["FTB Age", "Deposit %", "Mortgage Rate", "Homeownership %"]
    sim_vals= [
        accuracy.get("ftb_age_sim", 0),
        accuracy.get("deposit_sim", 0),
        accuracy.get("rate_sim", 0),
        accuracy.get("homeownership_sim", 0),
    ]
    uk_vals = [
        accuracy.get("ftb_age_benchmark", 0),
        accuracy.get("deposit_benchmark", 0),
        accuracy.get("rate_benchmark", 0),
        accuracy.get("homeownership_benchmark", 0),
    ]
    acc_scores = [
        accuracy.get("ftb_age_accuracy_pct", 0),
        accuracy.get("deposit_accuracy_pct", 0),
        accuracy.get("rate_accuracy_pct", 0),
        accuracy.get("homeownership_accuracy_pct", 0),
    ]

    x     = np.arange(len(labels))
    width = 0.35

    bars1 = ax.bar(x - width / 2, sim_vals, width, label="Simulation",
                   color="#4C72B0", alpha=0.85, edgecolor="white")
    bars2 = ax.bar(x + width / 2, uk_vals, width, label="UK Benchmark",
                   color="#FF8800", alpha=0.85, edgecolor="white")

    # Annotate accuracy % above each pair
    for i, (b1, b2, acc) in enumerate(zip(bars1, bars2, acc_scores)):
        mid_x = (b1.get_x() + b2.get_x() + b2.get_width()) / 2
        top_y = max(b1.get_height(), b2.get_height()) + 0.5
        colour = "#55A868" if acc >= 90 else "#DD8800" if acc >= 75 else "#C44E52"
        ax.text(mid_x, top_y, f"{acc:.0f}%", ha="center", fontsize=9,
                fontweight="bold", color=colour)

    ax.set_title("Simulation vs UK Benchmarks\n(% accuracy shown above each pair)",
                 fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)


# -----------------------------------------------------------------
# Print report to console
# -----------------------------------------------------------------

def print_report(r2, ftb, deposit, accuracy):
    """
    Prints a structured summary report to the console.

    :param r2: R-squared metrics
    :param ftb: FTB age metrics
    :param deposit: deposit metrics
    :param accuracy: model accuracy metrics
    """
    sep = "-" * 60
    print(sep)
    print("  SIMULATION STATISTICAL REPORT")
    print(sep)

    # R-squared
    print(f"\n[1] R-SQUARED - Salary Growth Linear Fit")
    print(f"    Overall R2 : {r2['overall']}")
    interpretation = (
        "Excellent" if r2["overall"] >= 0.95 else
        "Good"      if r2["overall"] >= 0.85 else
        "Moderate"  if r2["overall"] >= 0.70 else "Poor"
    )
    print(f"    Fit quality: {interpretation}")
    print(f"    (R2 = 1.0 means salary follows a perfect linear trend)")
    for agent, val in sorted(r2["per_agent"].items(), key=lambda x: x[1] or 0, reverse=True):
        if val is not None:
            print(f"      {agent:<15}: {val}")

    # FTB age
    print(f"\n[2] MEDIAN FIRST-TIME BUYER AGE")
    if ftb.get("median"):
        print(f"    Simulation median : {ftb['median']} years")
        print(f"    Simulation mean   : {ftb['mean']} years")
        print(f"    UK benchmark      : {UK_MEDIAN_FTB_AGE} years")
        print(f"    Accuracy          : {accuracy.get('ftb_age_accuracy_pct', 'N/A')}%")
        print(f"    Buyers            : {ftb['total_buyers']} / {len(AGENT_PROFILES)}")

    # Deposit
    print(f"\n[3] AVERAGE DEPOSIT AS % OF PROPERTY PRICE")
    if deposit.get("avg_deposit_pct"):
        print(f"    Simulation avg    : {deposit['avg_deposit_pct']}%")
        print(f"    Simulation median : {deposit['median_deposit_pct']}%")
        print(f"    UK benchmark      : {UK_AVG_DEPOSIT_PCT}%")
        print(f"    Accuracy          : {accuracy.get('deposit_accuracy_pct', 'N/A')}%")

    # Model accuracy
    print(f"\n[4] MODEL ACCURACY VS UK BENCHMARKS")
    print(f"    FTB age accuracy          : {accuracy.get('ftb_age_accuracy_pct', 'N/A')}%")
    print(f"    Deposit accuracy          : {accuracy.get('deposit_accuracy_pct', 'N/A')}%")
    print(f"    Mortgage rate accuracy    : {accuracy.get('rate_accuracy_pct', 'N/A')}%")
    print(f"    Homeownership accuracy    : {accuracy.get('homeownership_accuracy_pct', 'N/A')}%")
    print(f"    ---")
    print(f"    Overall model accuracy    : {accuracy.get('overall_accuracy_pct', 'N/A')}%")

    print(f"\n{sep}\n")


# -----------------------------------------------------------------
# Main
# -----------------------------------------------------------------

if __name__ == "__main__":
    print("Running synthetic simulation...")
    df = run_synthetic_simulation()

    # Compute metrics
    r2       = compute_r_squared(df)
    ftb      = compute_ftb_metrics(df)
    deposit  = compute_deposit_metrics(df)
    accuracy = compute_model_accuracy(ftb, deposit, df)

    # Print report
    print_report(r2, ftb, deposit, accuracy)

    # Build 6-panel figure
    fig = plt.figure(figsize=(18, 14))
    fig.suptitle("Synthetic Agent Housing Simulation - Results Report",
                 fontsize=16, fontweight="bold", y=0.98)
    gs  = gridspec.GridSpec(3, 3, figure=fig, hspace=0.5, wspace=0.35)

    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])
    ax4 = fig.add_subplot(gs[1, 0:2])
    ax5 = fig.add_subplot(gs[1, 2])
    ax6 = fig.add_subplot(gs[2, 0:2])
    ax7 = fig.add_subplot(gs[2, 2])

    plot_ftb_age_distribution(ftb, ax1)
    plot_deposit_percentages(deposit, ax2)
    plot_model_accuracy(accuracy, ax3)
    plot_savings_trajectories(df, ax4)
    plot_homeownership_rate(df, ax5)
    plot_salary_growth_by_group(df, ax6)
    plot_life_events(df, ax7)

    # Save and show
    out_path = os.path.join(GRAPHS_DIR, "simulation_report.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Graph saved to: {out_path}")
    plt.show()

