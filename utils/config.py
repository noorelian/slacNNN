import os
import pandas as pd
from dataclasses import dataclass

HERE = os.path.dirname(os.path.abspath(__file__))

H5_GLOB = os.path.join(HERE, "..", "data", "quench_data_L*.h5")
IMG_DIR = os.path.join(HERE, "..", "images")

os.makedirs(IMG_DIR, exist_ok=True)


@dataclass
class DataBundle:
    all_events: pd.DataFrame
    events_no_hl: pd.DataFrame
    real_events: pd.DataFrame
    nomp_nohl_real_all: pd.DataFrame
