import re
from datetime import datetime
import h5py
import numpy as np

from constants import (
    SIGNAL_TIME_MAP,
    LABELS,
    CHECKED,
    NOTE,
    CHECKED_AT,
    NEEDS_SPECIALIST,
    LOADED_Q_CHANGE_FOR_QUENCH,
)

import os

def list_subfolders(directory):
    """Return sorted list of subfolder names in a directory."""
    return sorted(
        d for d in os.listdir(directory)
        if os.path.isdir(os.path.join(directory, d))
    )


def list_h5_files(directory, extensions=(".h5", ".hdf5")):
    """Return sorted list of HDF5 filenames in a directory."""
    return sorted(
        f for f in os.listdir(directory)
        if f.lower().endswith(extensions)
        and os.path.isfile(os.path.join(directory, f))
    )


def find_all_h5_files(base_dir, extensions=(".h5", ".hdf5")):
    """Recursively find all HDF5 files under base_dir."""
    matches = []
    for dirpath, _, filenames in os.walk(base_dir):
        for fn in filenames:
            if fn.lower().endswith(extensions):
                matches.append(os.path.join(dirpath, fn))
    return sorted(matches)


def is_within_directory(path, base_dir):
    """Security check: ensure path stays inside base_dir."""
    return os.path.realpath(path).startswith(os.path.realpath(base_dir))


def get_scalar(group, keys):
    """
    This function is used for extracting a scalar value from the h5 file 

    """
    for key in keys:
        if key in group:
            try:
                arr = np.asarray(group[key])
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


def suggest_classification(time_data, fault_data, frequency, saved_q_loaded):
    """
    A modified version of lisa's function
    Fits the exponential decay to the fault waveform after the fault
    estimate the loaded Q and compares it to the save loaded Q then gives a suggestion (Real or false )
    A(t) = A0 * e^((-2 * pi * cav_freq * t)/(2 * loaded_Q)) = A0 * e ^ ((-pi * cav_freq * t)/loaded_Q)
    ln(A(t)) = ln(A0) + ln(e ^ ((-pi * cav_freq * t)/loaded_Q)) = ln(A0) - ((pi * cav_freq * t)/loaded_Q)
    polyfit(t, ln(A(t)), 1) = [-((pi * cav_freq)/loaded_Q), ln(A0)]
    polyfit(t, ln(A0/A(t)), 1) = [(pi * f * t)/Ql]
    https://education.molssi.org/python-data-analysis/03-data-fitting/index.html

    """
    other = None

    time_data = np.asarray(time_data, dtype=float)
    fault_data = np.asarray(fault_data, dtype=float)

    time_0 = 0
    # Look for time 0 (quench). These waveforms capture data beforehand
    for time_0, timestamp in enumerate(time_data):
        if timestamp >= 0:
            break

    fault_data = fault_data[time_0:]
    time_data = time_data[time_0:]
    end_decay = len(fault_data) - 1

    # Find where the amplitude decays to "zero"
    for end_decay, amp in enumerate(fault_data):
        if amp < 0.002:
            break

    if end_decay <= 1:
        other = "end_decay_not_found"
        pre_quench_amp = fault_data[0]
    else:
        fault_data = fault_data[:end_decay]
        time_data = time_data[:end_decay]
        pre_quench_amp = fault_data[0]

    try:
        with np.errstate(divide="raise", invalid="raise"):
            log_ratio = np.log(pre_quench_amp / fault_data)
            exponential_term = np.polyfit(time_data, log_ratio, 1)[0]
            loaded_q = (np.pi * frequency) / exponential_term
    except (FloatingPointError, ZeroDivisionError):
        return {"is_real": None, "loaded_q": np.nan, "other_issue": "divide_by_zero_or_invalid_value"}

    thresh_for_quench = LOADED_Q_CHANGE_FOR_QUENCH * saved_q_loaded
    is_real = bool(loaded_q < thresh_for_quench)
    return {"is_real": is_real, "loaded_q": loaded_q, "other_issue": other}

def list_cryomodules(h5_file):
    return sorted(k for k in h5_file.keys() if re.fullmatch(r"CM\d+", k))


def list_cavities(h5_file, cm):
    if cm not in h5_file:
        return []
    return sorted(k for k in h5_file[cm].keys() if re.fullmatch(r"CAV\d+", k))

def list_years(h5_file, cm, cav):
    years = set()
    if cm in h5_file and cav in h5_file[cm]:
        for name in h5_file[cm][cav].keys():
            match = re.match (r"(\d{4})\d{4}_\d{6}", name)
            if match:
                years.add(match.group(1))
    return sorted(years)

def has_signal(group):
    return bool(set(group.keys()) & set(SIGNAL_TIME_MAP.keys()))



def find_event_groups(hdf5_file, cm=None, cav=None, year=None):
    """This function is for finding each event groups/identifiers (decay ref, forward power, fault waveform) for each cm/cav/date, used for plotting """
    events = []
    def collect_from_cavity_group(cav_group, cav_path):
        for name, obj in cav_group.items():
            if not isinstance(obj, h5py.Group):
                continue
            if year and not name.startswith(year):
                continue
            if has_signal(obj):
                events.append(f"{cav_path}/{name}")
 
    if cm and cav:
        if cm in hdf5_file and cav in hdf5_file[cm]:
            collect_from_cavity_group(hdf5_file[cm][cav], f"{cm}/{cav}")
    elif cm:
        if cm in hdf5_file:
            for cav_name in list_cavities(hdf5_file, cm):
                collect_from_cavity_group(hdf5_file[cm][cav_name], f"{cm}/{cav_name}")
    else:

        def visitor(name, obj):
            """ This function is for exploring the h5 file structure"""
            if isinstance(obj, h5py.Group) and has_signal(obj):
                if year and not name.split("/")[-1].startswith(year):
                    return
                #keys = set(obj.keys())
                #if keys & set(SIGNAL_TIME_MAP.keys()):
                events.append(name)

        hdf5_file.visititems(visitor)
    return sorted(events)


def write_label(file_path, event_path, label, srf_note, needs_specialist):
    """ writing the label, note and checked status to the hdf5 file for each event (cm/cav/date) """
    note = srf_note.strip() if srf_note and srf_note.strip() else (
        f"This event has been already checked and the waveform was labeled as {label.upper()}"
    )

    with h5py.File(file_path, "a") as f:
        group = f[event_path]
        group.attrs[LABELS] = label
        group.attrs[CHECKED] = True
        group.attrs[NOTE] = note
        group.attrs[CHECKED_AT] = datetime.now().strftime("%Y-%m-%d")
        group.attrs[NEEDS_SPECIALIST] = bool(needs_specialist)


def parse_event_path(event_path):
    """Turn 'CM/CAV/YYYYMMDD_HHMMSS' into a human readable label"""
    match = re.search(r"CM(\d+)/CAV(\d+)/(\d{8})_(\d{6})", event_path)
    if match:
        cm, cav, date_str, time_str = match.groups()
        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
        return f"Cryomodule {int(cm)}, Cavity {int(cav)}  |  {formatted_date} {formatted_time}"
    else:
        print(f"Warning: Could not parse event path: {event_path}")
        return event_path