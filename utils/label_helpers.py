from utils.srf_waveforms import convert_pv_name_plot_string
from interface.quench_config import LABEL_DISPLAY_TO_STORED


def to_string(value):
    """ Decode byte attributes to string."""
    return value.decode() if isinstance(value, bytes) else value 


def normalize_label(label):
    """Normalize any label to a canonical form so case, spaces, and
    underscores never matter. 'NOT SURE', 'not_sure', 'Not Sure' all match."""
    label = to_string(label)

    if not label:
        return ""          
    return str(label).strip().lower().replace(" ", "_")

def display_label(status, unlabeled="Unlabeled"):
    """Uppercased, human readable label, or unlabeled if nothing is set."""
    label =normalize_label(status["label"])
    return label.upper() if label else unlabeled 


# A helper function that is responsible for the status of the file in the dropdown
def checked_status(event_path, event_status):
    """Format an event's dropdown label: name | checked | label."""
    status = event_status[event_path]
    event_name = convert_pv_name_plot_string(event_path)
    if status["checked"]:
        label = normalize_label(status["label"])
        label = label.upper() if label else "UNLABELED"
        return f"{event_name}   |   Checked: Yes    |   Label: {label}"
    return f"{event_name}   |   Checked: No |   Label: unlabeled"


def build_summary_table(display_name, checked, label, note, flag, when):
    """Build a markdown table for each event."""
    return f"""
    | **Event name**                        | {display_name}                      |
    |---------------------------------------|-------------------------------------|
    | **Checked**                           | {checked}                           |
    | **Label**                             | {label}                             |
    | **Note**                              | {note}                              |
    | **Need a specialist to inspect the cavity** | {flag}                        |
    | **Last updated**                      | {when}                              |
    """

# A function to format the event status(checked or unchecked), label(Real or False or Other) and note
def format_event_status(event_path, status):
    """Render an event's status as a markdown table."""
    checked = "Yes" if status["checked"] else "No"
    label = normalize_label(status["label"])
    label = label.upper() if label else "Unlabeled"

    note = status["note"] 
    if isinstance(note, bytes):
        note = note.decode()
    note = note if note else "None"
    when = status["checked_at"] if status["checked_at"] else ""
    if isinstance(when, bytes):
        when = when.decode()

    flag = "Yes" if status["needs_specialist"] else "No"

    display_name = convert_pv_name_plot_string(event_path).replace("|", "\\|")

    return build_summary_table(display_name, checked, label, note, flag, when)

def event_matches_label(event_path, event_status, target_label):
    """This function is used for the label filter"""
    if target_label == "All":
        return True
    
    status = event_status[event_path]
    label = normalize_label(status["label"])

    if target_label == "Unlabeled":
        return(not status["checked"]) or (not label)
    
    target = LABEL_DISPLAY_TO_STORED.get(target_label.upper(), target_label)
    target = normalize_label(target)
    
    return label == target