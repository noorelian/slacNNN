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

# # ----------------------------------------------------------------------- #
# # Find days that *look* like MP (a cavity's busiest quench days) but are
# # not recorded in MPdates.csv. These are candidate missing MP entries.
# # ----------------------------------------------------------------------- #
# PEAK_TOP_N = 2          # consider each cavity's top-N busiest days
# PEAK_MIN_COUNT = 10     # only flag days with more than this many quenches
# peakdf = peak_quench_day_per_cavity(real_events, top_n=PEAK_TOP_N, real_only=True)
# candidates = peak_days_not_in_mp(peakdf, onlympevents)
# candidates = candidates[candidates["count"] > PEAK_MIN_COUNT].reset_index(drop=True)
# # candidates = candidates[~candidates["cm"].isin(["CM34", "CM35"])].reset_index(drop=True)

# print(f"\nCandidate missing MP days "
#       f"(top-{PEAK_TOP_N} per cavity, count > {PEAK_MIN_COUNT}):")
# print(candidates.to_string(index=False))
# candidates.to_csv(os.path.join(HERE, "data", "non_mp_peak_quench_days.csv"),
#                   index=False)

# No MP candidates: 
nomp_real = real_events.groupby(["cm", "cav", "year", "month", "day"], observed=True).filter(lambda g: len(g) < 10)

events2022 = real_events[real_events["year"] == "2022"]
events2025 = real_events[real_events["year"] == "2025"]
# ----------------------------------------------------------------------- #
# Plot toggles. Flip True/False to turn individual plots on or off.
# ----------------------------------------------------------------------- #
PLOTS = {
    "box_real_slice_cm":    False,
    "box_real_all":         False,
    "bar_all_per_cryo":     False,
    "bar_real_vs_false_stk": False,
    "bar_real_vs_false_grp": False,
    "bar_real_per_cryo":     False,
    "bar_false_per_cryo":    False,
    "pie_real_vs_false":     False,
    "bar_per_year":         False,
    "line_all_years":       False,
    "bar_per_cavity":       True,
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
        #nomp_real, classification="real",
        events2022, classification="real",
        log=True, annotate_totals=True, compact_label=True,
        section_dividers=True, font_size=20, figsize=(22, 7),
        title="All real quench distributions per cryomodule (2022)",
        save_path=os.path.join(IMG_DIR, "real_quench_distributions_per_cryo_all_2022.png"),
    )

# All quenches per cryomodule
if PLOTS["bar_all_per_cryo"]:
    bar_quenches_per_cryo(
        nomp_real, section_colors=True,
        title="Number of quenches per cryomodule (2022-2025)",
        save_path=os.path.join(IMG_DIR, "all_quench_counts_per_cryo_nomp.png"),
    )

# Real and false stacked
if PLOTS["bar_real_vs_false_stk"]:
    bar_real_vs_false_stacked(
        events,
        title="Real vs false quenches per cryomodule (2022-2025)",
        save_path=os.path.join(IMG_DIR, "real_vs_false_quenches_stacked.png"),
    )

# Real and false grouped, log scale, subset 5-10
if PLOTS["bar_real_vs_false_grp"]:
    bar_real_vs_false_grouped(
        events, #cm_slice=(7, 12),
        log=True,
        title="Real vs false quenches per cryomodule on log scale (2022-2025)",
        save_path=os.path.join(IMG_DIR, "real_vs_false_quenches_log_scale.png"),
    )

# Real-only bar
if PLOTS["bar_real_per_cryo"]:
    bar_quenches_per_cryo(
        events, classification="real", section_colors=True,
        title="Real quenches per cryomodule (2022-2025)",
        save_path=os.path.join(IMG_DIR, "real_quenches_per_cryo.png"),
    )

# False-only bar
if PLOTS["bar_false_per_cryo"]:
    bar_quenches_per_cryo(
        events, classification="false", section_colors=True,
        title="False quenches per cryomodule (2022-2025)",
        save_path=os.path.join(IMG_DIR, "false_quenches_per_cryo.png"),
    )

# Pie chart
if PLOTS["pie_real_vs_false"]:
    pie_real_vs_false(
        events,
        title="Overall quench classification CM01-CM35 (2022-2025)",
        save_path=os.path.join(IMG_DIR, "real_vs_false_pie.png"),
    )

# Scatter: total / real / false per cryomodule
if PLOTS["scatter_totals"]:
    scatter_total_real_false(
        events, log=True, section_dividers=True,
        font_size=17, figsize=(18, 7),
        title="Total / real / false quenches per cryomodule (2022-2025)",
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
cm34 = events2025[events2025["cm"] == "CM34"]
cm35 = events2025[events2025["cm"] == "CM35"]
cavity_events = cm34
if PLOTS["bar_per_cavity"]:
    years = sorted(cavity_events["year"].unique())
    yr_label = years[0] if len(years) == 1 else f"{years[0]}-{years[-1]}"
    for cm in cavity_events["cm"].unique():
        bar_quenches_per_cavity(
            cavity_events, cm,
            title=f"{cm} ({yr_label})",
            figsize=(7, 6),
            save_path=os.path.join(IMG_DIR, f"quenches_per_cavity_{cm}_{yr_label}.png"),
        )

# Monthly bar for one (cm, cav, year)
if PLOTS["bar_per_month"]:
    cm, cav, year = "CM20", "CAV4", "2022"
    bar_quenches_per_month(
        real_events, cm=cm, cav=cav, year=year,
        save_path=os.path.join(IMG_DIR, f"quenches_per_month_{cm}_{cav}_{year}.png"),
    )



