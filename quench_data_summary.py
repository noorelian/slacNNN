import glob
import os

import h5py
import pandas as pd

# The H5 files written by ``save_data_h5.py`` are the source of truth.

EVENT_COLS = ["source_file", "cm", "cav", "date", "year", "month", "day", "is_real"]

MP = pd.read_csv(os.path.join(os.path.dirname(__file__), "data", "MPdates.csv"))


def _mp_keys():
    """Return the set of (cm, cav, yyyymmdd) tuples that were MP-processed."""
    cm = "CM" + MP["CM"].astype(int).astype(str).str.zfill(2)
    cav = "CAV" + MP["CAV"].astype(int).astype(str)
    # Dates in MPdates.csv look like "10/10/24"; normalize to "YYYYMMDD".
    date = pd.to_datetime(MP["date"], format="%m/%d/%y").dt.strftime("%Y%m%d")
    return set(zip(cm, cav, date))


def mp_events(events, keep=False):
    """Filter events by MP-processing membership.

    `keep`:
      - False (default): drop rows that match an MP entry.
      - True: keep only rows that match an MP entry.

    Match key is ``(cm, cav, YYYYMMDD)``. Returns a new DataFrame.
    """
    keys = _mp_keys()
    day = events["date"].str[:8]
    in_mp = [k in keys for k in zip(events["cm"], events["cav"], day)]
    mask = in_mp if keep else [not x for x in in_mp]
    return events[mask].reset_index(drop=True)

def _resolve_paths(source):
    """Normalize a source spec to a sorted list of H5 file paths."""
    if isinstance(source, str) and any(c in source for c in "*?["):
        paths = sorted(glob.glob(source))
        if not paths:
            raise FileNotFoundError(f"No files matched glob: {source}")
        return paths
    if isinstance(source, (str, os.PathLike)):
        return [source]
    return list(source)


def load_quench_events(source):
    """Return a flat events DataFrame, one row per quench event with EVENT_COLS.

    Source can be one of the following:
          - a path to a single ``quench_data_L*.h5`` file
          - a list/tuple of such paths
          - a glob string like ``"quench_data_L*.h5"``
    """
    rows = []
    for path in _resolve_paths(source):
        with h5py.File(path, "r") as f:
            for cm in f:                            # "CM01"
                for cav in f[cm]:                   # "CAV1"
                    for ts in f[cm][cav]:           # "YYYYMMDD_HHMMSS"
                        attrs = f[cm][cav][ts].attrs
                        rows.append((
                            f"{path}::{cm}/{cav}/{ts}",
                            cm, cav, ts,
                            ts[:4], ts[4:6], ts[6:8],
                            bool(attrs.get("quench_classification", False)),
                        ))
    return pd.DataFrame(rows, columns=EVENT_COLS)


def load_quench_waveforms(events, source):
    """Return waveforms + attrs for the quenches in `events`.

    Parameters: events : pd.DataFrame or pd.Series
        A row, Series, or sub-DataFrame from ``load_quench_events``. Only
        the ``cm``, ``cav``, ``date`` columns are used.
    source : same value passed to ``load_quench_events`` to build `events`.

    Returns: dict[str, dict]
        Keyed by ``"CM01/CAV1/YYYYMMDD_HHMMSS"``. Each value is
        ``{"datasets": {label: np.ndarray, ...}, "attrs": {name: value, ...}}``.
    """
    if isinstance(events, pd.Series):
        events = events.to_frame().T
    wanted = set(zip(events["cm"], events["cav"], events["date"]))

    out = {}
    for path in _resolve_paths(source):
        with h5py.File(path, "r") as f:
            for cm in f:
                if cm not in {w[0] for w in wanted}:
                    continue
                for cav in f[cm]:
                    if (cm, cav) not in {(w[0], w[1]) for w in wanted}:
                        continue
                    for ts in f[cm][cav]:
                        if (cm, cav, ts) not in wanted:
                            continue
                        g = f[cm][cav][ts]
                        out[f"{cm}/{cav}/{ts}"] = {
                            "datasets": {k: g[k][...] for k in g.keys()},
                            "attrs": {k: g.attrs[k] for k in g.attrs.keys()},
                        }
    return out

