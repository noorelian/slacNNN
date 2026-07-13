import h5py  # type: ignore

import numpy as np
from dataclasses import dataclass, fields
from typing import Optional
from numpy.typing import NDArray


@dataclass
class QuenchEvent:
    fault_time: NDArray[np.float64]
    fault_waveform: NDArray[np.float64]
    forward_power: NDArray[np.float64]
    forward_time: NDArray[np.float64]
    reverse_power: NDArray[np.float64]
    reverse_time: NDArray[np.float64]

    # Optional array, also strictly typed
    decay_reference: Optional[NDArray[np.float64]] = None


def pre_quench_amplitude(quench_event_data: QuenchEvent):
    pass


def area():
    pass


def exponential_decay_fit():
    pass


def power_spike_detection():
    pass


def load_quench_event(file_path: str, event_path: str) -> QuenchEvent:
    with h5py.File(file_path, "r") as f:
        event_group = f[event_path]
        if not isinstance(event_group, h5py.Group):
            raise TypeError(
                f"Expected an h5py.Group at {event_path}, got {type(event_group)}"
            )
        data_dict = {}

        for field in fields(QuenchEvent):
            if field.name in event_group:
                item = event_group[field.name]
                if isinstance(item, h5py.Dataset):
                    data_dict[field.name] = item[:]

        return QuenchEvent(**data_dict)


def main():
    file_path = "/Users/norah.ao/Documents/SLACPython/data/quench_data_L0.h5"
    event_path = "CM01/CAV1/20220329_103006"

    quench_event_data: QuenchEvent = load_quench_event(file_path, event_path)

    pre_quench_amplitude(quench_event_data)


if __name__ == "__main__":
    main()
