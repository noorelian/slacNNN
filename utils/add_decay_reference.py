import h5py
import glob
import numpy as np
from pathlib import Path
from typing import List
from classification.logic import QuenchData, find_quench_time
from numpy.typing import NDArray


def calculate_decay_reference(qd: QuenchData) -> np.ndarray:
    idx_0 = find_quench_time(qd)
    decay_ref = np.zeros_like(qd.fault_time)

    decay_ref[:idx_0] = qd.fault_waveform[:idx_0]

    A = qd.fault_waveform[idx_0]
    f = qd.frequency
    Ql = qd.saved_q_loaded
    t_after_fault = qd.fault_time[idx_0:]

    exponent = -(np.pi * f * t_after_fault) / Ql
    decay_ref[idx_0:] = A * np.exp(exponent)

    return decay_ref


def scan_for_missing_decay(directory_path: str) -> List[str]:
    files_to_fix = []

    search_pattern = f"{directory_path}/**/quench_data_L[0-9].h5"  # File path of data to add decay reference
    h5_files = glob.glob(search_pattern, recursive=True)

    for file_path in h5_files:
        try:
            with h5py.File(file_path, "r") as h5_file:
                needs_fix = False
                for event_id in h5_file.keys():
                    if "decay_reference" not in h5_file[event_id]:  # type: ignore
                        needs_fix = True
                        break

                if needs_fix:
                    files_to_fix.append(file_path)
        except Exception:
            print("Error")

    return files_to_fix


def fix_specific_files(file_list: List[str]) -> None:
    for file_path in file_list:
        try:
            with h5py.File(file_path, "r+") as h5_file:
                for event_id in h5_file.keys():
                    event_group = h5_file[event_id]

                    if "decay_reference" in event_group:  # type: ignore
                        continue

                    fault_time: NDArray[np.float64] = np.array(
                        event_group["fault_time"][:],  # type: ignore
                        dtype=np.float64,  # type: ignore
                    )
                    fault_waveform: NDArray[np.float64] = np.array(
                        event_group["fault_waveform"][:],  # type: ignore
                        dtype=np.float64,  # type: ignore
                    )

                    frequency: float = (
                        float(event_group["frequency"][()])  # type: ignore
                        if "frequency" in event_group  # type: ignore
                        else 1300000000.0
                    )

                    saved_q_loaded: float = (
                        float(event_group["saved_q_loaded"][()])  # type: ignore
                        if "saved_q_loaded" in event_group  # type: ignore
                        else 40000000.0
                    )

                    temp_qd = QuenchData(
                        fault_time=fault_time,
                        fault_waveform=fault_waveform,
                        forward_power=np.array([], dtype=np.float64),
                        forward_time=np.array([], dtype=np.float64),
                        reverse_power=np.array([], dtype=np.float64),
                        reverse_time=np.array([], dtype=np.float64),
                        frequency=frequency,
                        saved_q_loaded=saved_q_loaded,
                    )

                    new_decay_ref = calculate_decay_reference(temp_qd)

                    event_group.create_dataset("decay_reference", data=new_decay_ref)  # type: ignore

                print(f"Fixed: {Path(file_path).name}")

        except Exception as e:
            print(f"Failed to fix {Path(file_path).name}: {e}")


if __name__ == "__main__":
    directory = "./data"

    broken_files = scan_for_missing_decay(directory)

    if broken_files:
        fix_specific_files(broken_files)
    else:
        print("All files have decay_reference")
