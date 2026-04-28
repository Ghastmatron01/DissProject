import matplotlib.pyplot as plt
import numpy as np

# The precise data from our comparative analysis
categories = ['Rule-Based\nHeuristic', 'LLM Agents\n(ReAct)', 'Real-World\nUK Benchmark']
ftb_ages = [32.0, 41.0, 33.0]
deposits = [15.0, 11.0, 20.0]

# Set up the figure with 2 subplots side-by-side
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

# Beautiful academic colors (Blue, Orange, Green)
colors = ['#4C72B0', '#DD8452', '#55A868']
x_pos = np.arange(len(categories))

# --- PLOT 1: FTB AGE ---
bars1 = ax1.bar(x_pos, ftb_ages, color=colors, edgecolor='black', width=0.6)
ax1.set_title('Median First-Time Buyer Age', fontsize=14, pad=15)
ax1.set_ylabel('Age (Years)', fontsize=12)
ax1.set_xticks(x_pos)
ax1.set_xticklabels(categories, fontsize=11)
ax1.set_ylim(0, 50)
ax1.grid(axis='y', linestyle='--', alpha=0.7)

# Add the numbers on top of the bars
for bar in bars1:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2, yval + 1, f'{yval}',
             ha='center', va='bottom', fontweight='bold', fontsize=12)

# --- PLOT 2: DEPOSIT PERCENTAGE ---
bars2 = ax2.bar(x_pos, deposits, color=colors, edgecolor='black', width=0.6)
ax2.set_title('Average Deposit at Purchase', fontsize=14, pad=15)
ax2.set_ylabel('Deposit Percentage (%)', fontsize=12)
ax2.set_xticks(x_pos)
ax2.set_xticklabels(categories, fontsize=11)
ax2.set_ylim(0, 25)
ax2.grid(axis='y', linestyle='--', alpha=0.7)

# Add the numbers on top of the bars
for bar in bars2:
    yval = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2, yval + 0.5, f'{yval}%',
             ha='center', va='bottom', fontweight='bold', fontsize=12)

# Polish and Save
plt.tight_layout()
plt.savefig('comparative_results.png', dpi=300, bbox_inches='tight')
print("Graph successfully saved as 'comparative_results.png'!")