import h5py
from pathlib import Path
from dataclasses import dataclass, fields
from enum import Enum
from typing import Iterator, Tuple, Optional
import numpy as np
from numpy.typing import NDArray
from utils.config import DATA_DIR


"""
def load_all_quench_events() -> Iterator[Tuple[str, QuenchData]]:
    folder = Path(DATA_DIR)
    # Use the argument instead of hardcoding the string here
    for h5_file in folder.glob(file_pattern):
        with h5py.File(h5_file, "r") as f:
            for cm_name, cm_group in f.items():
                if not isinstance(cm_group, h5py.Group):
                    continue

                for cav_name, cav_group in cm_group.items():
                    if not isinstance(cav_group, h5py.Group):
                        continue

                    for timestamp, event_group in cav_group.items():
                        if not isinstance(event_group, h5py.Group):
                            continue

                        event_id = f"{cm_name}/{cav_name}/{timestamp}"

                        data_dict = {}
                        for field in fields(QuenchData):
                            if field.name in event_group:
                                item = event_group[field.name]
                                if isinstance(item, h5py.Dataset):
                                    data_dict[field.name] = item[:]

                        yield (event_id, QuenchData(**data_dict))
"""


def load_specific_quench_events() -> Iterator[Tuple[str, QuenchData]]:
    folder = Path(DATA_DIR)

    for h5_file in folder.glob("*L0.h5"):
        with h5py.File(h5_file, "r") as f:
            cm_name = "CM01"
            cav_name = "CAV1"

            if cm_name not in f or cav_name not in f[cm_name]:  # type: ignore
                continue

            cav_group = f[cm_name][cav_name]  # type: ignore

            for timestamp, event_group in cav_group.items():  # type: ignore
                if not isinstance(event_group, h5py.Group):
                    continue

                event_id = f"{cm_name}/{cav_name}/{timestamp}"

                data_dict = {}
                for field in fields(QuenchData):
                    if field.name in event_group:
                        item = event_group[field.name]
                        if isinstance(item, h5py.Dataset):
                            data_dict[field.name] = item[:]

                yield (event_id, QuenchData(**data_dict))


