import h5py
import numpy as np
from numpy.typing import NDArray
from typing import Optional, Iterator, Tuple, Dict
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

    if "frequency" not in data_dict:
        if "FREQ" in group.attrs:
            data_dict["frequency"] = float(group.attrs["FREQ"])  # type: ignore

    if "saved_q_loaded" not in data_dict:
        if "QLOADED" in group.attrs:
            data_dict["saved_q_loaded"] = float(group.attrs["QLOADED"])  # type: ignore

    return QuenchData(**data_dict)


# Loads and formats waveform data from an HDF5 file for easy plotting
def load_event_waveform_data(
    file_path: str, event_path: str
) -> Tuple[Dict[str, Tuple[NDArray, NDArray]], float, float]:
    with h5py.File(file_path, "r") as f:
        group = f[event_path]
        quench_data = extract_quench_data(group)  # type: ignore

    signal_data = {}
    signal_time_map = {
        "forward_power": "forward_time",
        "reverse_power": "reverse_time",
        "fault_waveform": "fault_time",
        "decay_reference": "forward_time",
    }

    for signal_name, time_name in signal_time_map.items():
        y_data = getattr(quench_data, signal_name, None)
        if y_data is None:
            continue

        y = np.array(y_data)
        x_data = getattr(quench_data, time_name, None)
        x = None

        if x_data is not None:
            t = np.array(x_data)
            if t.shape[0] == y.shape[0]:
                x = t

        if x is None:
            x = np.arange(y.shape[0])

        signal_data[signal_name] = (x, y)

    return (
        signal_data,
        getattr(quench_data, "frequency", 1.3e9),
        getattr(quench_data, "saved_q_loaded", 4e7),
    )


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
                        quench_data = extract_quench_data(event_group)
                        yield (event_id, h5_file.name, quench_data)
