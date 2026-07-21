from enum import Enum

import numpy as np
from dataclasses import dataclass, fields
from numpy.typing import NDArray
from typing import Iterator, Tuple, Optional, Dict, Any
from pathlib import Path
import h5py


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
    REAL = "REAL"
    FALSE = "FALSE"
    OTHER = "OTHER"


def find_quench_time(quench_event_data: QuenchData) -> int:
    return int(np.searchsorted(quench_event_data.fault_time, 0.0))


def pre_quench_amplitude(quench_event_data: QuenchData, time_0: int) -> bool:
    pre_quench_window = quench_event_data.fault_waveform[0:time_0]
    is_avg_sufficient = np.mean(pre_quench_window) >= 0.1
    are_all_points_above_zero = np.all(pre_quench_window > 0.001)

    pre_quench_fwd_power = quench_event_data.forward_power[0:time_0]
    is_fwd_power_on = np.mean(pre_quench_fwd_power) > 0.1

    return bool(is_avg_sufficient and are_all_points_above_zero and is_fwd_power_on)


def verify_tau_decay(quench_event_data: QuenchData, time_0: int) -> bool:
    decay_waveform = quench_event_data.fault_waveform[time_0:]
    decay_time = quench_event_data.fault_time[time_0:]

    a0 = decay_waveform[0]
    target_1 = a0 / np.e
    target_2 = a0 / (np.e**2)

    idx_1 = np.searchsorted(-decay_waveform, -target_1)
    idx_2 = np.searchsorted(-decay_waveform, -target_2)

    if idx_1 >= len(decay_waveform) or idx_2 >= len(decay_waveform):
        return False

    t1 = decay_time[idx_1] - decay_time[0]
    t2 = decay_time[idx_2] - decay_time[0]

    expected_t2 = 2 * t1
    tolerance = 0.20 * expected_t2

    return bool(abs(t2 - expected_t2) <= tolerance)


def exponential_fit():
    pass


# TODO: Add function for reverse power spikes. - Look into more! Use derivative or something? Spikes to more than 40% we can say something else is going on?
def power_spike_detection():
    pass


"""
def load_all_quench_events(data_dir: str) -> Iterator[Tuple[str, QuenchData]]:
    folder = Path(data_dir)

    for h5_file in folder.glob("*.h5"):
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

                        event_id = f"{file_prefix}-{cm_name}-{cav_name}-{timestamp}"

                        data_dict = {}
                        for field in fields(QuenchData):
                            if field.name in event_group:
                                item = event_group[field.name]
                                if isinstance(item, h5py.Dataset):
                                    data_dict[field.name] = item[:]

                        yield (event_id, QuenchData(**data_dict))
"""


def load_specific_quench_events(data_dir: str) -> Iterator[Tuple[str, QuenchData]]:
    folder = Path(data_dir)

    for h5_file in folder.glob("*L0.h5"):
        file_prefix = h5_file.stem

        with h5py.File(h5_file, "r") as f:
            cm_name = "CM01"
            cav_name = "CAV1"

            if cm_name not in f or cav_name not in f[cm_name]:  # type: ignore
                continue

            cav_group = f[cm_name][cav_name]  # type: ignore

            for timestamp, event_group in cav_group.items():  # type: ignore
                if not isinstance(event_group, h5py.Group):
                    continue

                event_id = f"{file_prefix}-{cm_name}-{cav_name}-{timestamp}"

                data_dict = {}
                for field in fields(QuenchData):
                    if field.name in event_group:
                        item = event_group[field.name]
                        if isinstance(item, h5py.Dataset):
                            data_dict[field.name] = item[:]

                yield (event_id, QuenchData(**data_dict))


def classify(event_data: QuenchData):
    time_0: int = find_quench_time(event_data)

    if not pre_quench_amplitude(event_data, time_0):
        return QuenchStatus.OTHER

    if verify_tau_decay(event_data, time_0):
        return QuenchStatus.REAL

    return QuenchStatus.FALSE


def run_classification(
    events_iterator: Iterator[Tuple[str, "QuenchData"]],
) -> Dict[str, Any]:
    classification_results = {}

    for event_id, event_data in events_iterator:
        label = classify(event_data)
        classification_results[event_id] = label
    return classification_results


def analyze_classification(
    predictions: Dict[str, Any], ground_truth_file: Path
) -> None:
    correct = 0
    total = 0

    with h5py.File(ground_truth_file, "r") as f:
        cm_name = "CM01"
        cav_name = "CAV1"

        if cm_name not in f or cav_name not in f[cm_name]:  # type: ignore
            return

        cav_group = f[cm_name][cav_name]  # type:ignore

        for timestamp, event_group in cav_group.items():  # type: ignore
            event_id = f"quench_data_L0-{cm_name}-{cav_name}-{timestamp}"

            if event_id in predictions:
                total += 1
                predicted_label = predictions[event_id]
                true_label = event_group.attrs.get("label")

                if str(predicted_label) == str(true_label):
                    correct += 1
                else:
                    print(
                        f"Mismatch on {event_id} | Predicted: {predicted_label} | Actual: {true_label}"
                    )

    if total > 0:
        accuracy = (correct / total) * 100
        print(f"\nResults: {correct}/{total} correct ({accuracy:.2f}%)")
    else:
        print("\nWarning.")


def main() -> None:
    events_iterator = load_specific_quench_events("data")
    prediction_results = run_classification(events_iterator)
    labeled_file_path = Path("data") / "quench_data_L0_noor.h5"
    analyze_classification(prediction_results, labeled_file_path)


if __name__ == "__main__":
    main()
