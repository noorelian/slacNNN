"""Load quench events from quench_data_L*.h5 files into a flat DataFrame.

The H5 files written by ``save_data_h5.py`` are the source of truth.
``load_quench_events`` returns one row per quench event with these columns:

    source_file  cm   cav   date  year  month  day  is_real
"""

import glob
import os

import h5py
import pandas as pd

EVENT_COLS = ["source_file", "cm", "cav", "date", "year", "month", "day", "is_real"]

def _events_from_h5(paths):
    rows = []
    for path in paths:
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


def load_quench_events(source):
    """Return a flat events DataFrame.

    Args: source: 
          - a path to a single ``quench_data_L*.h5`` file
          - a list/tuple of such paths
          - a glob string like ``"quench_data_L*.h5"``
    """
    if isinstance(source, str) and any(c in source for c in "*?["):
        paths = sorted(glob.glob(source))
        if not paths:
            raise FileNotFoundError(f"No files matched glob: {source}")
        return _events_from_h5(paths)
    if isinstance(source, (str, os.PathLike)):
        return _events_from_h5([source])
    return _events_from_h5(list(source))
