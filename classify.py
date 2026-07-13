from enum import Enum
import h5py  # type: ignore

import numpy as np
from dataclasses import dataclass, fields
from typing import Optional
from numpy.typing import NDArray
from pathlib import Path
from typing import Iterator, Tuple
import csv

from utils.config import DATA_DIR


@dataclass
class QuenchEvent:
    fault_time: NDArray[np.float64]
    fault_waveform: NDArray[np.float64]
    forward_power: NDArray[np.float64]
    forward_time: NDArray[np.float64]
    reverse_power: NDArray[np.float64]
    reverse_time: NDArray[np.float64]

    decay_reference: Optional[NDArray[np.float64]] = None


class QuenchStatus(Enum):
    REAL_QUENCH = "REAL_QUENCH"
    FALSE_QUENCH = "FALSE_QUENCH"
    CAVITY_OFF = "CAVITY_OFF"


def pre_quench_amplitude(quench_event_data: QuenchEvent) -> bool:
    pre_quench_window = quench_event_data.fault_waveform[0:500]

    pre_quench_avg = np.mean(pre_quench_window)

    if pre_quench_avg >= 5.0:
        return True
    else:
        return False


def area():
    pass


def exponential_decay_fit():
    pass


def power_spike_detection():
    pass


def load_all_quench_events(data_dir: str) -> Iterator[Tuple[str, QuenchEvent]]:
    folder = Path(data_dir)

    for h5_file in folder.glob("*.h5"):
        # h5_file.stem gets the filename without the ".h5" extension
        # e.g., "quench_data_L0"
        file_prefix = h5_file.stem

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

                        # --- THE NEW UNIQUE ID ---
                        event_id = f"{file_prefix}-{cm_name}-{cav_name}-{timestamp}"

                        data_dict = {}
                        for field in fields(QuenchEvent):
                            if field.name in event_group:
                                item = event_group[field.name]
                                if isinstance(item, h5py.Dataset):
                                    data_dict[field.name] = item[:]

                        yield (event_id, QuenchEvent(**data_dict))


def classify(event_data):
    if not pre_quench_amplitude:
        return QuenchStatus.CAVITY_OFF

    # SWAP FOR YOUR CLASSIFY MAIN function TODO
    if area() and exponential_decay_fit() and power_spike_detection():
        return QuenchStatus.REAL_QUENCH

    return QuenchStatus.FALSE_QUENCH


def run_classification(events_iterator: Iterator[Tuple[str, QuenchEvent]]):
    with open("classification_results.csv", mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["event", "classification"])
        print("Processing events and writing to CSV...")

        for event_id, event_data in events_iterator:
            label = classify(event_data)

            writer.writerow([event_id, label])
            print(f"Logged: {event_id} -> {label}")
            break


def analyze_classification():
    """
    Compare classification result of Algorithm vs labled dataset
    1. Load labes.csv and classification_retult.csv
    2. Compare all labels to the classification
    3. Output result and falsely classified
    """
    pass


def main():
    events_iterator: Iterator[Tuple[str, QuenchEvent]] = load_all_quench_events(
        DATA_DIR
    )
    run_classification(events_iterator)

    analyze_classification()

    print("\nPipeline finished! Results saved to classification_results.csv")


if __name__ == "__main__":
    main()
