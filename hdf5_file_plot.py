import os

from quench_data_summary import (
    load_quench_events,
    mp_events,
    peak_days_not_in_mp,
    peak_quench_day_per_cavity,
    print_peak_quench_day_summary,
)
from quench_plots import (
    box_plot_quenches_per_cavity,
    bar_quenches_per_cryo,
    bar_real_vs_false_stacked,
    bar_real_vs_false_grouped,
    pie_real_vs_false,
    scatter_total_real_false,
    bar_quenches_per_year,
    line_quenches_all_years,
    bar_quenches_per_cavity,
    bar_quenches_per_month,
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

real_events  = events[events["is_real"].astype(bool)]
nompevents   = mp_events(real_events, keep=False)
onlympevents = mp_events(real_events, keep=True)
print(f"\nMP events: {len(onlympevents)}, non-MP events: {len(nompevents)}")

#print_peak_quench_day_summary(real_events, top_n=3, real_only=True)
peakdf    = peak_quench_day_per_cavity(real_events, top_n=3, real_only=True)
#cm20_2022 = real_events[(real_events["cm"] == "CM20") & (real_events["year"] == "2022")]
non_mp_peaks = peak_days_not_in_mp(peakdf, onlympevents)
print("\nPeak quench days not in MP:")
print(non_mp_peaks.to_string(index=False))

# ----------------------------------------------------------------------- #
# Plot toggles. Flip True/False to turn individual plots on or off.
# ----------------------------------------------------------------------- #
PLOTS = {
    "box_real_slice_cm":    True,
    "box_real_all":         False,
    "bar_all_per_cryo":     False,
    "bar_real_vs_false_stk": False,
    "bar_real_vs_false_grp": False,
    "bar_real_per_cryo":     False,
    "bar_false_per_cryo":    False,
    "pie_real_vs_false":     False,
    "bar_per_year":         False,
    "line_all_years":       False,
    "bar_per_cavity":       False,
    "scatter_totals":       False,
    "bar_per_month":    False,
}

# Box plot: real quenches per cavity, slice of cryomodules
if PLOTS["box_real_slice_cm"]:
    cm_slice = (35, 37)
    box_plot_quenches_per_cavity(
        events, classification="real", cm_slice=cm_slice,
        save_path=os.path.join(
            IMG_DIR,
            f"real_quench_distributions_per_cryo_{cm_slice[0]}-{cm_slice[1] - 1}.png",
        ),
    )

if PLOTS["box_real_all"]:
    box_plot_quenches_per_cavity(
        events, classification="real",
        log=True, annotate_totals=True, compact_label=True,
        section_dividers=True, font_size=20, figsize=(22, 7),
        title="All real quench distributions per cryomodule (2022-2026)",
        save_path=os.path.join(IMG_DIR, "real_quench_distributions_per_cryo_all.png"),
    )

# All quenches per cryomodule
if PLOTS["bar_all_per_cryo"]:
    bar_quenches_per_cryo(
        events, section_colors=True,
        title="Number of Quenches Per Cryomodule (2022-2026)",
        save_path=os.path.join(IMG_DIR, "all_quench_counts_per_cryo.png"),
    )

# Real and false stacked
if PLOTS["bar_real_vs_false_stk"]:
    bar_real_vs_false_stacked(
        events,
        title="Real vs False Quenches per Cryomodule (2022-2026)",
        save_path=os.path.join(IMG_DIR, "real_vs_false_quenches_stacked.png"),
    )

# Real and false grouped, log scale, subset 5-10
if PLOTS["bar_real_vs_false_grp"]:
    bar_real_vs_false_grouped(
        events, #cm_slice=(7, 12),
        log=True,
        title="Real vs False Quenches per Cryomodule on Log Scale (2022-2026)",
        save_path=os.path.join(IMG_DIR, "real_vs_false_quenches_log_scale.png"),
    )

# Real-only bar
if PLOTS["bar_real_per_cryo"]:
    bar_quenches_per_cryo(
        events, classification="real", section_colors=True,
        title="Real Quenches per Cryomodule (2022-2026)",
        save_path=os.path.join(IMG_DIR, "real_quenches_per_cryo.png"),
    )

# False-only bar
if PLOTS["bar_false_per_cryo"]:
    bar_quenches_per_cryo(
        events, classification="false", section_colors=True,
        title="False Quenches per Cryomodule (2022-2026)",
        save_path=os.path.join(IMG_DIR, "false_quenches_per_cryo.png"),
    )

# Pie chart
if PLOTS["pie_real_vs_false"]:
    pie_real_vs_false(
        events,
        title="Overall Quench Classification CM01-CM35 (2022-2026)",
        save_path=os.path.join(IMG_DIR, "real_vs_false_pie.png"),
    )

# Scatter: total / real / false per cryomodule
if PLOTS["scatter_totals"]:
    scatter_total_real_false(
        events, log=True, section_dividers=True,
        font_size=17, figsize=(18, 7),
        title="Total / Real / False Quenches per Cryomodule (2022-2026)",
        save_path=os.path.join(IMG_DIR, "scatter_total_real_false.png"),
    )

# One bar chart per year
if PLOTS["bar_per_year"]:
    for year in sorted(events["year"].unique()):
        bar_quenches_per_year(
            events, year,
            save_path=os.path.join(IMG_DIR, f"quenches_{year}_by_cryo.png"),
        )

# All-years line plot
if PLOTS["line_all_years"]:
    line_quenches_all_years(
        events, log=True,
        font_size=17, figsize=(22, 7),
        save_path=os.path.join(IMG_DIR, "quenches_per_cryo_all_years.png"),
    )

# Per-cavity bar for each cryomodule
if PLOTS["bar_per_cavity"]:
    #for cm in sorted(events["cm"].unique()):
    years = sorted(cm20_2022["year"].unique())
    yr_label = years[0] if len(years) == 1 else f"{years[0]}-{years[-1]}"
    for cm in cm20_2022["cm"].unique():
        bar_quenches_per_cavity(
            cm20_2022, cm,
            title=f"Number of quenches per cavity in {cm} ({yr_label})",
            save_path=os.path.join(IMG_DIR, f"quenches_per_cavity_{cm}_{yr_label}.png"),
        )

# Monthly bar for one (cm, cav, year)
if PLOTS["bar_per_month"]:
    cm, cav, year = "CM20", "CAV4", "2022"
    bar_quenches_per_month(
        real_events, cm=cm, cav=cav, year=year,
        save_path=os.path.join(IMG_DIR, f"quenches_per_month_{cm}_{cav}_{year}.png"),
    )



