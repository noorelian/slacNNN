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
H5_GLOB = os.path.join(HERE, "data", "quench_data_L*.h5")
IMG_DIR = os.path.join(HERE, "images")
os.makedirs(IMG_DIR, exist_ok=True)

events = load_quench_events(H5_GLOB)
print(f"Loaded {len(events)} quench events from {H5_GLOB}")

# Physical cryomodule order: L0 (CM01), L1 (CM02-CM03), HL (CMH1-CMH2),
# L2 (CM04-CM15), L3 (CM16-CM35). Set as a Categorical so every
# groupby/sort_index in the plots respects this layout.
import pandas as pd
CM_ORDER = ["CM01", "CM02", "CM03", "CMH1", "CMH2"] + [f"CM{n:02d}" for n in range(4, 36)]
present = [cm for cm in CM_ORDER if cm in set(events["cm"])]
events["cm"] = pd.Categorical(events["cm"], categories=present, ordered=True)

print(events.groupby("cm", observed=True).size())

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
    events, classification="real", cryo_slice=(5, 10),
    save_path=os.path.join(IMG_DIR, "real_quench_distributions_per_cryo_4-8.png"),
)

# Box plot: real quenches per cavity, all cryomodules, totals annotated
box_plot_quenches_per_cavity(
    events, classification="real",
    ylim=None, annotate_totals=True, figsize=(22, 7),
    title="Real Quench Distributions per Cryomodule (2022-2026)",
    save_path=os.path.join(IMG_DIR, "real_quench_distributions_per_cryo_all.png"),
)

# All quenches per cryomodule
bar_quenches_per_cryo(
    events,
    title="Number of Quenches Per Cryomodule (2022-2026)",
    save_path=os.path.join(IMG_DIR, "all_quench_counts_per_cryo.png"),
)

# Real and fake stacked
bar_real_vs_fake_stacked(
    events,
    title="Real vs Fake Quenches per Cryomodule (2022-2026)",
    save_path=os.path.join(IMG_DIR, "real_vs_fake_quenches_stacked.png"),
)

# Real and fake grouped, log scale, subset 5-10
bar_real_vs_fake_grouped(
    events, cryo_slice=(7, 12), log=True,
    title="Real vs Fake Quenches per Cryomodule on Log Scale (2022-2026)",
    save_path=os.path.join(IMG_DIR, "real_vs_fake_quenches_log_scale.png"),
)

# Real-only bar
bar_quenches_per_cryo(
    events, classification="real",
    title="Real Quenches per Cryomodule (2022-2026)",
    save_path=os.path.join(IMG_DIR, "real_quenches_per_cryo.png"),
)

# Fake-only bar
bar_quenches_per_cryo(
    events, classification="fake",
    title="Fake Quenches per Cryomodule (2022-2026)",
    save_path=os.path.join(IMG_DIR, "fake_quenches_per_cryo.png"),
)

# Pie chart
pie_real_vs_fake(
    events,
    title="Overall Quench Classification CM01-CM35 (2022-2026)",
    save_path=os.path.join(IMG_DIR, "real_vs_fake_pie.png"),
)

# One bar chart per year
# for year in sorted(events["year"].unique()):
#     bar_quenches_per_year(
#         events, year,
#         save_path=os.path.join(IMG_DIR, f"quenches_{year}_by_cryo.png"),
#     )

# All-years line plot
line_quenches_all_years(
    events, ylim=(0, 4000),
    save_path=os.path.join(IMG_DIR, "quenches_per_cryo_all_years.png"),
)

# Per-cavity bar for each cryomodule
for cm in sorted(events["cm"].unique()):
    bar_quenches_per_cavity(
        events, cm,
        title=f"Number of Quenches per Cavity in {cm} (2022-2026)",
        save_path=os.path.join(IMG_DIR, f"quenches_per_cavity_{cm}.png"),
    )



