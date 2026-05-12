import os

from quench_data_summary import load_quench_events, mp_events
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
# L2 (CM04-CM15), L3 (CM16-CM35). Every plot respects this layout.

import pandas as pd
CM_ORDER = ["CM01", "CM02", "CM03", "CMH1", "CMH2"] + [f"CM{n:02d}" for n in range(4, 36)]
present = [cm for cm in CM_ORDER if cm in set(events["cm"])]
events["cm"] = pd.Categorical(events["cm"], categories=present, ordered=True)
#print(events.groupby("cm", observed=True).size())

nompevents   = mp_events(events, keep=False)
onlympevents = mp_events(events, keep=True)
print(f"\nMP events: {len(onlympevents)}, non-MP events: {len(nompevents)}")

# ----------------------------------------------------------------------- #
# Plot toggles. Flip True/False to turn individual plots on or off.
# ----------------------------------------------------------------------- #
PLOTS = {
    "box_real_4_8":         False,
    "box_real_all":         False,
    "bar_all_per_cryo":     False,
    "bar_real_vs_fake_stk": False,
    "bar_real_vs_fake_grp": False,
    "bar_real_per_cryo":    False,
    "bar_fake_per_cryo":    False,
    "pie_real_vs_fake":     False,
    "bar_per_year":         False,
    "line_all_years":       False,
    "bar_per_cavity":       False,
}

# # Box plot: real quenches per cavity, cryomodules 4-8
if PLOTS["box_real_4_8"]:
    box_plot_quenches_per_cavity(
        events, classification="real", cryo_slice=(5, 10),
        save_path=os.path.join(IMG_DIR, "real_quench_distributions_per_cryo_4-8.png"),
    )

if PLOTS["box_real_all"]:
    box_plot_quenches_per_cavity(
        events, classification="real",
        log=True, annotate_totals=True, compact_label=True,
        section_dividers=True, font_size=20, figsize=(22, 7),
        title="All Quench Distributions per Cryomodule (2022-2026)",
        save_path=os.path.join(IMG_DIR, "real_quench_distributions_per_cryo_all.png"),
    )

# # All quenches per cryomodule
if PLOTS["bar_all_per_cryo"]:
    bar_quenches_per_cryo(
        events, section_colors=True,
        title="Number of Quenches Per Cryomodule (2022-2026)",
        save_path=os.path.join(IMG_DIR, "all_quench_counts_per_cryo.png"),
    )

# # Real and fake stacked
if PLOTS["bar_real_vs_fake_stk"]:
    bar_real_vs_fake_stacked(
        events,
        title="Real vs Fake Quenches per Cryomodule (2022-2026)",
        save_path=os.path.join(IMG_DIR, "real_vs_fake_quenches_stacked.png"),
    )

# # Real and fake grouped, log scale, subset 5-10
if PLOTS["bar_real_vs_fake_grp"]:
    bar_real_vs_fake_grouped(
        events, #cryo_slice=(7, 12),
        log=True,
        title="Real vs False Quenches per Cryomodule on Log Scale (2022-2026)",
        save_path=os.path.join(IMG_DIR, "real_vs_false_quenches_log_scale.png"),
    )

# # Real-only bar
if PLOTS["bar_real_per_cryo"]:
    bar_quenches_per_cryo(
        events, classification="real", section_colors=True,
        title="Real Quenches per Cryomodule (2022-2026)",
        save_path=os.path.join(IMG_DIR, "real_quenches_per_cryo.png"),
    )

# # Fake-only bar
if PLOTS["bar_fake_per_cryo"]:
    bar_quenches_per_cryo(
        events, classification="fake", section_colors=True,
        title="Fake Quenches per Cryomodule (2022-2026)",
        save_path=os.path.join(IMG_DIR, "fake_quenches_per_cryo.png"),
    )

# # Pie chart
if PLOTS["pie_real_vs_fake"]:
    pie_real_vs_fake(
        events,
        title="Overall Quench Classification CM01-CM35 (2022-2026)",
        save_path=os.path.join(IMG_DIR, "real_vs_fake_pie.png"),
    )

# One bar chart per year
if PLOTS["bar_per_year"]:
    for year in sorted(events["year"].unique()):
        bar_quenches_per_year(
            events, year,
            save_path=os.path.join(IMG_DIR, f"quenches_{year}_by_cryo.png"),
        )

# # All-years line plot
if PLOTS["line_all_years"]:
    line_quenches_all_years(
        events, log=True,
        font_size=17, figsize=(22, 7),
        save_path=os.path.join(IMG_DIR, "quenches_per_cryo_all_years.png"),
    )

# # Per-cavity bar for each cryomodule
if PLOTS["bar_per_cavity"]:
    for cm in sorted(events["cm"].unique()):
        bar_quenches_per_cavity(
            events, cm,
            title=f"Number of Quenches per Cavity in {cm} (2022-2026)",
            save_path=os.path.join(IMG_DIR, f"quenches_per_cavity_{cm}.png"),
        )



