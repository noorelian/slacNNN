import matplotlib.pyplot as plt
import numpy as np

from quench_data_summary import load_quench_events  # re-exported

DEFAULT_FONT = 14
DEFAULT_FIGSIZE = (14, 6)

REAL_COLOR = "#4daf4a"
FAKE_COLOR = "#e41a1c"
BAR_COLOR = "#377eb8"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def _filter_class(events, classification):
    """classification: 'real' or 'fake'. Pass the events frame directly
    if no filtering is wanted."""
    if classification == "real":
        return events[events["is_real"].astype(bool)]
    if classification == "fake":
        return events[~events["is_real"].astype(bool)]
    raise ValueError(f"classification must be 'real' or 'fake' (got {classification!r})")


_CLASS_LABEL = {None: "", "real": "Real ", "fake": "Fake "}
_CLASS_COLOR = {None: BAR_COLOR, "real": REAL_COLOR, "fake": FAKE_COLOR}


def _annotate_bars(ax, bars, offset=10, fontsize=8):
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + offset, str(int(h)),
                ha="center", fontsize=fontsize)


def _style(ax, xlabel, ylabel, title, font_size, xticks=None, xticklabels=None, rotation=90):
    ax.set_xlabel(xlabel, fontsize=font_size)
    ax.set_ylabel(ylabel, fontsize=font_size)
    ax.set_title(title, fontsize=font_size)
    if xticks is not None:
        ax.set_xticks(xticks)
    if xticklabels is not None:
        ax.set_xticklabels(xticklabels, rotation=rotation)
    ax.grid(True, alpha=0.5)
    ax.set_axisbelow(True)


def _finish(fig, save_path, show):
    fig.tight_layout()
    if save_path:
        fig.savefig(save_path, bbox_inches="tight", dpi=300)
    if show:
        plt.show()
    else:
        plt.close(fig)


# --------------------------------------------------------------------------- #
# plots
# --------------------------------------------------------------------------- #

def box_plot_quenches_per_cavity(events, classification=None, cryo_slice=None,
                                 ylim=(-10, 400), title=None,
                                 annotate_totals=False,
                                 font_size=DEFAULT_FONT, figsize=(8, 6),
                                 save_path=None, show=False):
    """Box plot of per-cavity quench counts, one box per cryomodule.

    `cryo_slice` is a (start, stop) tuple to plot a subset of cryomodules
    in the order of ``events['cm']`` (e.g. (3, 8)). None = all.
    `classification` is 'real', 'fake', or None for no filtering.
    `ylim` may be None for autoscale.
    `annotate_totals` appends ``(n=<total>)`` to each x-tick label.
    """
    sub = _filter_class(events, classification) if classification else events
    counts = (sub.groupby(["cm", "cav"], observed=True).size()
                 .unstack(fill_value=0))
    cms = counts.index.tolist()  # preserves Categorical order 
    if cryo_slice is not None:
        cms = cms[cryo_slice[0]:cryo_slice[1]]
    data = [counts.loc[cm].values for cm in cms]

    fig, ax = plt.subplots(figsize=figsize)
    ax.boxplot(data)
    if ylim is not None:
        ax.set_ylim(*ylim)

    if annotate_totals:
        labels = [f"{cm}\n(n={int(sum(d))})" for cm, d in zip(cms, data)]
    else:
        labels = cms

    label = _CLASS_LABEL[classification]
    _style(ax, "Cryomodule Number",
           f"Number of {label}Quenches per Cavity",
           title or f"{label}Quench Distributions per Cryomodule",
           font_size, xticks=np.arange(1, len(cms) + 1),
           xticklabels=labels, rotation=45)
    _finish(fig, save_path, show)


def bar_quenches_per_cryo(events, classification=None, title=None,
                          font_size=DEFAULT_FONT, figsize=DEFAULT_FIGSIZE,
                          save_path=None, show=False):
    """Bar chart: total quenches per cryomodule.

    `classification` is 'real', 'fake', or None for no filtering.
    """
    sub = _filter_class(events, classification) if classification else events
    counts = sub.groupby("cm").size().sort_index()
    color = _CLASS_COLOR[classification]
    label = _CLASS_LABEL[classification]

    fig, ax = plt.subplots(figsize=figsize)
    bars = ax.bar(counts.index, counts.values, color=color)
    _annotate_bars(ax, bars, offset=max(counts.values) * 0.01 + 1)
    _style(ax, "Cryomodule Number", f"Number of {label}Quenches",
           title or f"{label}Quenches per Cryomodule",
           font_size, xticks=np.arange(len(counts)),
           xticklabels=counts.index.tolist())
    _finish(fig, save_path, show)


def bar_real_vs_fake_stacked(events, title="Real vs Fake Quenches per Cryomodule",
                             font_size=DEFAULT_FONT, figsize=(20, 8),
                             save_path=None, show=False):
    """Stacked bar: real (bottom) + fake (top) per cryomodule."""
    real = events[events["is_real"].astype(bool)].groupby("cm").size()
    fake = events[~events["is_real"].astype(bool)].groupby("cm").size()
    cms = sorted(set(real.index) | set(fake.index))
    r = real.reindex(cms, fill_value=0).values
    f = fake.reindex(cms, fill_value=0).values

    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(cms, r, label="Real Quenches", color=REAL_COLOR)
    ax.bar(cms, f, bottom=r, label="Fake Quenches", color=FAKE_COLOR)
    _style(ax, "Cryomodule", "Number of Quenches", title,
           font_size, xticks=np.arange(len(cms)), xticklabels=cms)
    ax.legend()
    _finish(fig, save_path, show)


def bar_real_vs_fake_grouped(events, cryo_slice=None, log=False,
                             title=None, font_size=DEFAULT_FONT,
                             figsize=(15, 7), save_path=None, show=False):
    """Side-by-side bars of real and fake quenches per cryomodule."""
    real = events[events["is_real"].astype(bool)].groupby("cm").size()
    fake = events[~events["is_real"].astype(bool)].groupby("cm").size()
    cms = sorted(set(real.index) | set(fake.index))
    if cryo_slice is not None:
        cms = cms[cryo_slice[0]:cryo_slice[1]]
    r = real.reindex(cms, fill_value=0).values
    f = fake.reindex(cms, fill_value=0).values

    x = np.arange(len(cms))
    w = 0.4
    fig, ax = plt.subplots(figsize=figsize)
    ax.bar(x - w / 2, r, width=w, label="Real Quenches", color="indigo")
    ax.bar(x + w / 2, f, width=w, label="Fake Quenches", color="darkcyan")
    if log:
        ax.set_yscale("log")
    suffix = " (Log Scale)" if log else ""
    _style(ax, "Cryomodule", "Number of Quenches",
           title or f"Real vs Fake Quenches per Cryomodule{suffix}",
           font_size, xticks=x, xticklabels=cms)
    ax.legend()
    _finish(fig, save_path, show)


def pie_real_vs_fake(events, title="Overall Quench Classification",
                     font_size=DEFAULT_FONT, figsize=(6, 6),
                     save_path=None, show=False):
    """Pie chart of real vs fake quenches across the whole input."""
    real = int(events["is_real"].astype(bool).sum())
    fake = int((~events["is_real"].astype(bool)).sum())
    fig, ax = plt.subplots(figsize=figsize)
    ax.pie([real, fake], labels=["Real Quenches", "Fake Quenches"],
           colors=[REAL_COLOR, FAKE_COLOR],
           autopct="%1.1f%%", startangle=90,
           textprops={"fontsize": font_size})
    ax.set_title(title, fontsize=font_size)
    ax.axis("equal")
    _finish(fig, save_path, show)


def bar_quenches_per_year(events, year, title=None, font_size=DEFAULT_FONT,
                          figsize=DEFAULT_FIGSIZE, save_path=None, show=False):
    """Bar chart of quench counts per cryomodule for a single year."""
    sub = events[events["year"] == str(year)]
    counts = sub.groupby("cm").size().sort_index()
    fig, ax = plt.subplots(figsize=figsize)
    bars = ax.bar(counts.index, counts.values, color=BAR_COLOR)
    _annotate_bars(ax, bars, offset=max(counts.values) * 0.01 + 1)
    _style(ax, "Cryomodule Number", "Number of Quenches",
           title or f"Number of Quenches in {year} by Cryomodule",
           font_size, xticks=np.arange(len(counts)),
           xticklabels=counts.index.tolist())
    _finish(fig, save_path, show)


def line_quenches_all_years(events, title="Number of Quenches per Cryomodule (All Years)",
                            font_size=DEFAULT_FONT, figsize=DEFAULT_FIGSIZE,
                            ylim=None, save_path=None, show=False):
    """One line per year showing quench counts vs cryomodule."""
    pivot = (events.groupby(["cm", "year"]).size()
                   .unstack(fill_value=0).sort_index())
    cms = pivot.index.tolist()
    years = sorted(pivot.columns)
    colors = ["#377eb8", "#ff7f00", "#4daf4a", "#f781bf", "#984ea3",
              "#a65628", "#999999"]

    fig, ax = plt.subplots(figsize=figsize)
    for i, yr in enumerate(years):
        ax.plot(cms, pivot[yr].values, label=str(yr),
                color=colors[i % len(colors)],
                marker="o", markersize=6, linewidth=2, alpha=0.8)
    if ylim is not None:
        ax.set_ylim(*ylim)
    _style(ax, "Cryomodule Number", "Number of Quenches", title,
           font_size, xticks=np.arange(len(cms)), xticklabels=cms)
    ax.legend(title="Year")
    _finish(fig, save_path, show)


def bar_quenches_per_cavity(events, cm, title=None, font_size=DEFAULT_FONT,
                            figsize=DEFAULT_FIGSIZE, save_path=None, show=False):
    """Bar chart of quench counts per cavity for a single cryomodule."""
    sub = events[events["cm"] == cm]
    counts = sub.groupby("cav").size().sort_index()
    fig, ax = plt.subplots(figsize=figsize)
    bars = ax.bar(counts.index, counts.values, color=BAR_COLOR)
    _annotate_bars(ax, bars, offset=max(counts.values) * 0.01 + 1)
    _style(ax, "Cavity Number", "Number of Quenches",
           title or f"Number of Quenches per Cavity in {cm}",
           font_size, xticks=np.arange(len(counts)),
           xticklabels=counts.index.tolist())
    _finish(fig, save_path, show)
