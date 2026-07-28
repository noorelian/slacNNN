import h5py
from pathlib import Path
from dataclasses import dataclass, fields
from enum import Enum
from typing import Iterator, Tuple, Optional
import numpy as np
from numpy.typing import NDArray
from utils.config import DATA_DIR


@dataclass
class QuenchData:
    fault_time: NDArray[np.float64]
    fault_waveform: NDArray[np.float64]
    forward_power: NDArray[np.float64]
    forward_time: NDArray[np.float64]
    reverse_power: NDArray[np.float64]
    reverse_time: NDArray[np.float64]
    decay_reference: Optional[NDArray[np.float64]] = None


class QuenchStatus(Enum):
    real = "real"
    false = "false"
    other = "other"
    cavity_off = "cavity_off"


# Traverses HDF5 files to extract and yield quench event datasets
def load_quench_events(file_pattern: str = "*.h5") -> Iterator[Tuple[str, QuenchData]]:
    folder = Path(DATA_DIR)
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
