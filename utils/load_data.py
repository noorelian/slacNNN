import pandas as pd
from utils.config import H5_GLOB, DataBundle
from utils.quench_data_summary import (
    filter_events,
    load_quench_events,
)


def load_data():

    events = load_quench_events(H5_GLOB)
    # TODO: Add option to select year in this function

    print(f"Loaded {len(events)} quench events from {H5_GLOB}")

    # Physical cryomodule order: L0 (CM01), L1 (CM02-CM03), HL (CMH1-CMH2),
    # L2 (CM04-CM15), L3 (CM16-CM35). Every plot respects this layout.

    CM_ORDER = ["CM01", "CM02", "CM03", "CMH1", "CMH2"] + [
        f"CM{n:02d}" for n in range(4, 36)
    ]
    present = [cm for cm in CM_ORDER if cm in set(events["cm"])]
    events["cm"] = pd.Categorical(events["cm"], categories=present, ordered=True)
    # print(events.groupby("cm", observed=True).size())
    events_no_hl = filter_events(events, exclude_hl=True)
    real_events = filter_events(events, classification="real", exclude_hl=True)
    # nompevents   = mp_events(real_events, keep=False)
    # onlympevents = mp_events(real_events, keep=True)
    # print(f"\nMP events: {len(onlympevents)}, non-MP events: {len(nompevents)}")

    # nomp_real = real_events.groupby(["cm", "cav", "year", "month", "day"], observed=True).filter(lambda g: len(g) < 10)
    # Same idea via the merged MP table (data/all_mp_dates.csv):
    nomp_nohl_real_all = filter_events(
        events, classification="real", exclude_hl=True, exclude_mp=True
    )
    # events2022 = real_events[real_events["year"] == "2022"]

    return DataBundle(
        all_events=events,
        events_no_hl=events_no_hl,
        real_events=real_events,
        nomp_nohl_real_all=nomp_nohl_real_all,
    )
