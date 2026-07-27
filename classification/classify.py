import h5py
from pathlib import Path
from typing import Iterator, Tuple, Dict, Any

from utils.config import DATA_DIR
from .data_loader import QuenchData, load_quench_events
from .logic import classify


def run_classification(
    events_iterator: Iterator[Tuple[str, QuenchData]],
) -> Dict[str, Any]:
    classification_results = {}
    for event_id, event_data in events_iterator:
        # Removed the "L0" check since file_prefix is no longer in the event_id
        if "CM01" in event_id and "CAV1" in event_id:
            label = classify(event_data)
            classification_results[event_id] = label
    return classification_results


def compare_classification(
    predictions: Dict[str, Any], ground_truth_file: Path, cm_name: str, cav_name: str
) -> None:
    correct = 0
    total = 0

    with h5py.File(ground_truth_file, "r") as f:
        if cm_name not in f or cav_name not in f[cm_name]:  # type: ignore
            return

        cav_group = f[cm_name][cav_name]  # type: ignore

        for timestamp, event_group in cav_group.items():  # type: ignore
            event_id = f"{cm_name}/{cav_name}/{timestamp}"

            if event_id in predictions:
                true_label = event_group.attrs.get("quench_labels")

                if true_label is None:
                    continue

                if isinstance(true_label, bytes):
                    true_label = true_label.decode("utf-8")

                total += 1
                predicted_enum = predictions[event_id]

                predicted_val = (
                    predicted_enum.value
                    if hasattr(predicted_enum, "value")
                    else str(predicted_enum)
                )

                if predicted_val.strip().upper() == str(true_label).strip().upper():
                    correct += 1
                else:
                    print(
                        f"Mismatch on {event_id:32} | Predicted: {predicted_val.lower():5} | Actual: {str(true_label).lower():5}"
                    )

    if total > 0:
        accuracy = (correct / total) * 100
        print(f"\nResults: {correct}/{total} correct ({accuracy:.2f}%)")
    else:
        print("\nWarning: No matching labeled events found.")


def main() -> None:
    events_iterator = load_quench_events()
    prediction_results = run_classification(events_iterator)

    labeled_file_path = Path(DATA_DIR) / "quench_data_L0_noor.h5"
    compare_classification(prediction_results, labeled_file_path, "CM01", "CAV1")


if __name__ == "__main__":
    main()
