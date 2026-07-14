import h5py 
import numpy as np
from datetime import datetime 

from constants import (
    SIGNAL_TIME_MAP,
    FREQUENCY_KEYS,
    SAVED_Q_LOADED_KEYS,
    LABELS,
    CHECKED,
    NOTE,
    CHECKED_AT,
    NEED_SPECIALIST,
)

def get_scalar(group, keys):
    """
    This function is used for extracting a scalar value from the h5 file 
    """
    for key in keys:
        if key in group:
            try:
                arr = np.array(group[keys])
                return float(arr.flat[0]) if arr.shape else float(arr)
            except Exception:
                continue
        if key in group.attrs:
            try:
                val = group.attrs[key]
                if isinstance(val, bytes):
                    val = val.decode()
                return float(val)
            except Exception:
                continue
    return None

def find_event_groups(hddf5_file):
    """This function is for finding each event groups/identifiers (decay ref, forward power, fault waveform) for each cm/cav/date, used for plotting """
    events = []
 
    def visitor(name, obj):
        """ This function is for exploring the h5 file structure"""
        if isinstance(obj, h5py.Group):
            keys = set(obj.keys())
            if keys & set(SIGNAL_TIME_MAP.keys()):
                events.append(name)
 
    hddf5_file.visititems(visitor)
    return sorted(events)

def load_status(selected_path):
    with h5py.File(selected_path, "r") as f:
         events = find_event_groups(f)
         event_status = {}
         for event in events:
             attrs = f[event].attrs
             event_status[event] = {
                "checked": bool(attrs.get(CHECKED, False)),
                "label": attrs.get(LABELS, None),
                "note": attrs.get(NOTE, None),
                "checked_at": attrs.get(CHECKED_AT, None),
                "needs_specialist": bool(attrs.get(NEED_SPECIALIST, False))
             }
    return events, event_status

def load_signals(selected_path, event_path):
    with h5py.File(selected_path, "r") as f:
        group = f[event_path]
        signal_data ={}

        for signal_name, time_name in SIGNAL_TIME_MAP.items():
            if signal_name not in group: # if an event is missing some attributes like the very first ones in 2022, skip the missing attributes 
                continue

            y = np.array(group[signal_name]) # load the signals(attributes) into array 
            x = None 

            if time_name in group:
                t = np.array(group[time_name]) # load time data into array 
                # only assign t to x if its shape matches that of y 
                if t.shape[0] == y.shape[0]:
                    x = t

            if x is None:
                x = np.arange(y.shape[0]) # if no time is available, create an x-axis starts from 0 to the length of y 

        signal_data[signal_name] = (x, y)

        frequency = get_scalar(group, FREQUENCY_KEYS) #read cavity frequency 
        saved_q_loaded = get_scalar(group, SAVED_Q_LOADED_KEYS) #read the saved loaded Q
    return  signal_data, frequency, saved_q_loaded

def write_label(file_path, event_path, label, SRF_note, needs_specialist):
    """ writing the label, note and checked status to the hdf5 file for each event (cm/cav/date) """
    note = SRF_note.strip() if SRF_note and SRF_note.strip() else f"This event has been already checked and the waveform was labeled as {label.upper()}"

    # open in append mode 
    with h5py.File(file_path, "a") as f:
        group = f[event_path]
        group.attrs[LABELS] = label
        group.attrs[CHECKED] = True
        group.attrs[NOTE] = note
        group.attrs[CHECKED_AT] = datetime.now().strftime("%Y-%m-%d")
        group.attrs[NEED_SPECIALIST] = bool (needs_specialist)


