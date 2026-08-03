import h5py
import numpy as np
from numpy.typing import NDArray
from typing import Optional, Iterator, Tuple
from dataclasses import dataclass, fields
from pathlib import Path
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
    frequency: float = 1300000000.0
    saved_q_loaded: float = 40000000.0


# Extracts datasets from a single HDF5 group into a QuenchData dataclass
def extract_quench_data(group: h5py.Group) -> QuenchData:
    data_dict = {}

    for field in fields(QuenchData):
        if field.name in group:
            item = group[field.name]
            if isinstance(item, h5py.Dataset):
                data_dict[field.name] = item[()]
        elif field.name in group.attrs:
            data_dict[field.name] = group.attrs[field.name]

    return QuenchData(**data_dict)


# Traverses HDF5 files to extract and yield quench event datasets
def load_quench_events(
    file_pattern: str = "*.h5",
) -> Iterator[Tuple[str, str, QuenchData]]:
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

                        # Use the shared helper function to do the heavy lifting
                        quench_data = extract_quench_data(event_group)

                        yield (event_id, h5_file.name, quench_data)
