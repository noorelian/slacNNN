import os

from quench_data_summary import load_quench_events
from quench_plots import (
    box_plot_quenches_per_cavity,
    bar_quenches_per_cryo,
    bar_real_vs_fake_stacked,
    bar_real_vs_fake_grouped,
    pie_real_vs_fake,
    bar_quenches_per_year,
    line_quenches_all_years,
    bar_quenches_per_cavity,
)

HERE = os.path.dirname(os.path.abspath(__file__))
H5_GLOB = os.path.join(HERE, "quench_data_L*.h5")

events = load_quench_events(H5_GLOB)
print(f"Loaded {len(events)} quench events from {H5_GLOB}")
print(events.groupby("cm").size())

"""
Questions answered with these plots:
    (1) Which cryomodule quenched the most?
    (2) How many real quenches per cryomodule?
    (3) How many fake quenches per cryomodule?
    (4) How many quenches per year?
    (5) Which cavity quenched the most?
"""

# Box plot: real quenches per cavity, cryomodules 4-8
box_plot_quenches_per_cavity(
    events, classification="real", cryo_slice=(3, 8),
    save_path=os.path.join(HERE, "real_quench_distributions_per_cryo_4-8.png"),
)

# All quenches per cryomodule
bar_quenches_per_cryo(
    events,
    title="Number of Quenches Per Cryomodule (2022-2025)",
    save_path=os.path.join(HERE, "all_quench_counts_per_cryo.png"),
)

# Real and fake stacked
bar_real_vs_fake_stacked(
    events,
    title="Real vs Fake Quenches per Cryomodule (2022-2025)",
    save_path=os.path.join(HERE, "real_vs_fake_quenches_stacked.png"),
)

# Real and fake grouped, log scale, subset 5-10
bar_real_vs_fake_grouped(
    events, cryo_slice=(5, 10), log=True,
    title="Real vs Fake Quenches per Cryomodule on Log Scale (2022-2025)",
    save_path=os.path.join(HERE, "real_vs_fake_quenches_log_scale.png"),
)

# Real-only bar
bar_quenches_per_cryo(
    events, classification="real",
    title="Real Quenches per Cryomodule (2022-2025)",
    save_path=os.path.join(HERE, "real_quenches_per_cryo.png"),
)

# Fake-only bar
bar_quenches_per_cryo(
    events, classification="fake",
    title="Fake Quenches per Cryomodule (2022-2025)",
    save_path=os.path.join(HERE, "fake_quenches_per_cryo.png"),
)

# Pie chart
pie_real_vs_fake(
    events,
    title="Overall Quench Classification CM01-CM35 (2022-2025)",
    save_path=os.path.join(HERE, "real_vs_fake_pie.png"),
)

# One bar chart per year
for year in sorted(events["year"].unique()):
    bar_quenches_per_year(
        events, year,
        save_path=os.path.join(HERE, f"quenches_{year}_by_cryo.png"),
    )

# All-years line plot
line_quenches_all_years(
    events, ylim=(0, 4000),
    save_path=os.path.join(HERE, "quenches_per_cryo_all_years.png"),
)

# Per-cavity bar for each cryomodule
for cm in sorted(events["cm"].unique()):
    bar_quenches_per_cavity(
        events, cm,
        title=f"Number of Quenches per Cavity in {cm} (2022-2025)",
        save_path=os.path.join(HERE, f"quenches_per_cavity_{cm}.png"),
    )



# plot for all quenches per cryomodule
# fig1, ax1 = plt.subplots(figsize=(12,6))
# bars = ax1.bar(cryo_names, quench_counts_per_cryo.values(), color='#377eb8')
# for bar in bars:
#     height = bar.get_height()
#     ax1.text(bar.get_x() + bar.get_width()/2, height + 30, str(height), ha='center', fontsize=8)
# ax1.set_xlabel('Cryomodule Number', fontsize=14)
# ax1.set_ylabel('Total Number of Quenches', fontsize=14)
# ax1.set_title('Number of Quenches Per Cryomodule (2022-2025)', fontsize=14)
# ax1.set_xticks(np.arange(len(cryo_names)))
# ax1.set_xticklabels(cryo_names, rotation=90)
# plt.tight_layout()
# ax1.grid(True, alpha=0.5)
# ax1.set_axisbelow(True)
# #plt.savefig('all_quench_counts_per_cryo.pdf', bbox_inches='tight', dpi=300)
# plt.show()



# print("Real Quenches Per Cryomodule (Classified by Validation Method):\n")
# for cryomodule, count in real_quenches_per_cryo.items():   
#     print(f"{cryomodule}: {count} real quenches")

# print("Fake Quenches Per Cryomodule (Classified by Validation Method):\n")
# for cryomodule, count in fake_quenches_per_cryo.items():   
#     print(f"{cryomodule}: {count} fake quenches")

# all_cryomodules = list(real_quenches_per_cryo.keys())
# real_counts = [real_quenches_per_cryo[cm] for cm in all_cryomodules]
# fake_counts = [fake_quenches_per_cryo[cm] for cm in all_cryomodules]
#
# x = np.arange(len(all_cryomodules))
# width = 0.4

# # plotting both real and fake quench data on bar chart
# fig, ax = plt.subplots(figsize=(30, 10))
# real_bars = ax.bar(x, real_counts, label='Real Quenches', color='#4daf4a')
# fake_bars = ax.bar(x, fake_counts, bottom=real_counts, label='Fake Quenches', color='#e41a1c')
# ax.set_xlabel('Cryomodule', fontsize=14)
# ax.set_ylabel('Number of Quenches', fontsize=14)
# ax.set_title('Real vs Fake Quenches per Cryomodule (2022-2025)', fontsize=14)
# ax.set_xticks(x)
# ax.set_xticklabels(all_cryomodules, rotation=90)
# ax.legend()
# ax.grid(True, alpha=0.5)
# ax.set_axisbelow(True)
# plt.tight_layout()
# plt.show()

# plotting both real and fake quench data on bar chart (LOG SCALE)
# fig8, ax8 = plt.subplots(figsize=(30, 10))
# bar_width = 0.4
# x = np.arange(5,10,1) #len(all_cryomodules))
# real_bars = ax8.bar(x - bar_width/2, real_counts[5:10], width=bar_width, label='Real Quenches', color='indigo')
# fake_bars = ax8.bar(x + bar_width/2, fake_counts[5:10], width=bar_width, label='Fake Quenches', color='darkcyan')
# ax8.set_xlabel('Cryomodule', fontsize=14)
# ax8.set_ylabel('Number of Quenches', fontsize=14)
# ax8.set_yscale('log')
# ax8.set_title('Real vs Fake Quenches per Cryomodule on Log Scale (2022-2025)', fontsize=14)
# ax8.set_xticks(x)
# ax8.set_xticklabels(all_cryomodules[5:10], rotation=90)
# ax8.legend()
# ax8.grid(True, alpha=0.5)
# ax8.set_axisbelow(True)
# plt.tight_layout()
# plt.show()
#plt.savefig('real_vs_fake_quenches_log_scale.pdf', bbox_inches='tight', dpi=300)

# # plotting only real quench data
# fig2, ax2 = plt.subplots(figsize=(15, 7))
# real_bars = ax2.bar(x, real_counts, label='Real Quenches', color='#4daf4a')
# for bar in real_bars:
#     height = bar.get_height()
#     ax2.text(bar.get_x() + bar.get_width()/2, height + 30, str(height), ha='center', fontsize=8)
# ax2.set_xlabel('Cryomodule', fontsize=14)
# ax2.set_ylabel('Number of Quenches', fontsize=14)
# ax2.set_title('Real Quenches per Cryomodule (2022-2025)', fontsize=14)
# ax2.set_xticks(x)
# ax2.set_xticklabels(all_cryomodules, rotation=90)
# ax2.legend()
# ax2.grid(True, alpha=0.5)
# ax2.set_axisbelow(True)
# plt.tight_layout()
# plt.show()

# # plotting only fake quench data
# fig3, ax3 = plt.subplots(figsize=(15, 7))
# fake_bars = ax3.bar(x, fake_counts, label='Fake Quenches', color='#e41a1c')
# for bar in fake_bars:
#     height = bar.get_height()
#     ax3.text(bar.get_x() + bar.get_width()/2, height + 30, str(height), ha='center', fontsize=8)
# ax3.set_xlabel('Cryomodule', fontsize=14)
# ax3.set_ylabel('Number of Quenches', fontsize=14)
# ax3.set_title('Fake Quenches per Cryomodule (2022-2025)', fontsize=14)
# ax3.set_xticks(x)
# ax3.set_xticklabels(all_cryomodules, rotation=90)
# ax3.legend()
# ax3.grid(True, alpha=0.5)
# ax3.set_axisbelow(True)
# plt.tight_layout()
# plt.show()

# # pie chart of real vs fake classified quenches in the whole machine
# labels = ['Real Quenches', 'Fake Quenches']
# sizes = [sum(real_counts), sum(fake_counts)]
# colors = ['#4daf4a', '#e41a1c']
# fig4, ax4 = plt.subplots()
# ax4.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
# ax4.set_title('Overall Quench Classification CM01-CM35 (2022-2025)')
# ax4.axis('equal')   # equal aspect ratio makes the pie chart a circle
# plt.show()

# # plotting number of quenches per year for each cryomodule
# all_years = sorted({year for cryo in quenches_per_year for year in quenches_per_year[cryo]})
# cryo_modules = sorted(quenches_per_year.keys())
# for year in all_years:
#     counts = [quenches_per_year[cryo].get(year, 0) for cryo in cryo_modules]
#     fig5, ax5 = plt.subplots(figsize=(14,6))
#     count_bars = ax5.bar(cryo_modules, counts, color='#377eb8')
#     for bar in count_bars:
#         height = bar.get_height()
#         ax5.text(bar.get_x() + bar.get_width()/2, height + 10, str(height), ha='center', fontsize=8)
#     ax5.set_title(f"Number of Quenches in {year} by Cryomodule (Real and Fake)", fontsize=14)
#     ax5.set_xlabel("Cryomodule Number", fontsize=14)
#     ax5.set_ylabel("Number of Quenches", fontsize=14)
#     ax5.set_xticks(np.arange(len(cryo_modules)))
#     ax5.set_xticklabels(cryo_modules, rotation=90)
#     ax5.grid(True, alpha=0.5)
#     ax5.set_axisbelow(True)
#     plt.tight_layout()
#     plt.show()

# # plotting number of quenches per year for each cryomodule (all years on same scatter plot)
# fig6, ax6 = plt.subplots(figsize=(14,6))
# colors = ['#377eb8', '#ff7f00', '#4daf4a', '#f781bf', '#984ea3']
# for i, year in enumerate(all_years):
#     counts = [quenches_per_year[cryo].get(year, 0) for cryo in cryo_modules]
#     # ax6.scatter(cryo_modules, counts, label=year, color=colors[i], s=60, alpha=0.7)
#     ax6.plot(cryo_modules, counts, label=year, color=colors[i], marker='o', markersize=6, linewidth=2, alpha=0.8)
# ax6.set_title("Number of Quenches per Cryomodule (All Years)", fontsize=14)
# ax6.set_xlabel("Cryomodule Number", fontsize=14)
# ax6.set_ylabel("Number of Quenches", fontsize=14)
# ax6.set_ylim(0, 4000)
# ax6.set_xticks(np.arange(len(cryo_modules)))
# ax6.set_xticklabels(cryo_modules, rotation=90)
# ax6.legend(title="Year")
# ax6.grid(True, alpha=0.5)
# ax6.set_axisbelow(True)
# plt.tight_layout()
# plt.show()

# # plotting the number of quenches per cavity
# for cryo_label, cavity_counts in quenches_per_cavity.items():
#     cavities = list(cavity_counts.keys())
#     counts_per_cavity = list(cavity_counts.values())
#     fig7, ax7 = plt.subplots(figsize=(14, 6))
#     count_bars = ax7.bar(cavities, counts_per_cavity, color='#377eb8')
#     for bar in count_bars:
#         height = bar.get_height()
#         ax7.text(bar.get_x() + bar.get_width()/2, height + 100, str(height), ha='center', fontsize=8)        
#     ax7.set_title(f"Number of Quenches per Cavity in {cryo_label} (2022-2025)", fontsize=14)
#     ax7.set_xlabel("Cavity Number", fontsize=14)
#     ax7.set_ylabel("Number of Quenches", fontsize=14)
#     ax7.set_xticks(np.arange(len(cavities)))
#     ax7.set_xticklabels(cavities, rotation=90)
#     ax7.grid(True, alpha=0.5)
#     ax7.set_axisbelow(True)
#     plt.tight_layout()
#     plt.show()