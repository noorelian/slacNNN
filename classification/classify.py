from typing import Dict, Union
from .data_loader import QuenchData
from .logic import classify, QuenchStatus


def classify_event(event_data: QuenchData) -> QuenchStatus:
    return classify(event_data)


def run_classification(
    events_dict: Dict[str, QuenchData],
) -> Dict[str, Union[QuenchStatus, str]]:
    classification_results = {}
    for event_id, event_data in events_dict.items():
        classification_results[event_id] = classify_event(event_data)
    return classification_results
