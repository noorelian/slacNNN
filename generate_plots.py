"""
HDF5 Plotter main function
"""

from plotter.plot_data import plot_data
from utils.load_data import load_data

PLOTS: dict[str, bool] = {
    "box_real_slice_cm": True,
    "box_all": True,
    "box_real_all": True,
    "bar_all_per_cryo": True,
    "bar_real_vs_false_stk": True,
    "bar_real_vs_false_grp": True,
    "bar_real_per_cryo": True,
    "bar_false_per_cryo": True,
    "pie_real_vs_false": True,
    "bar_per_year": True,
    "line_all_years": True,
    "bar_per_cavity": True,
    "scatter_totals": True,
    "bar_per_month": True,
    "line_section_time": True,
}


def main():
    config = load_data()
    plot_data(PLOTS, config)


if __name__ == "__main__":
    main()
