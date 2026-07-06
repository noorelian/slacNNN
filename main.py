"""
HDF5 Plotter main function
"""

from src.hdf5_file_plot import plot_data

PLOTS = {
    "box_real_slice_cm": False,
    "box_all": False,
    "box_real_all": True,
    "bar_all_per_cryo": False,
    "bar_real_vs_false_stk": False,
    "bar_real_vs_false_grp": False,
    "bar_real_per_cryo": False,
    "bar_false_per_cryo": False,
    "pie_real_vs_false": True,
    "bar_per_year": False,
    "line_all_years": False,
    "bar_per_cavity": False,
    "scatter_totals": False,
    "bar_per_month": False,
    "line_section_time": True,
}


def main():
    plot_data(PLOTS)


if __name__ == "__main__":
    main()
