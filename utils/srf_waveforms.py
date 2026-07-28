import numpy as np
import pandas as pd
import re 
from datetime import datetime

# Partial PVs to search for various waveforms
common_data = [
    ("CAV:FLTAWF", "fault_waveform"),
    ("FWD:FLTAWF", "forward_power"),
    ("REV:FLTAWF", "reverse_power"),
    ("DECAYREFWF", "decay_reference"),
    ("CAV:FLTTWF", "fault_time"),
    ("FWD:FLTTWF", "forward_time"),
    ("REV:FLTTWF", "reverse_time"),
    (":QLOADED", "saved_q_loaded"),
    (":FREQ", "frequency"),
    # ('ACQ_SAMP_PERIOD', 'sampling_period'),
]

from interface.quench_config import LOADED_Q_CHANGE_FOR_QUENCH

waveform_data = [key for _, key in common_data]
by_label = {label: pv for pv, label in common_data}


def all_arrays_same_length(dictionary):
    """Convert the array lengths to a set to check if they are all the same"""
    lengths = (len(arr) for arr in dictionary.values())
    return len(set(lengths)) == 1


def convert_pv_name_plot_string(raw_name):
    """Make a cryomodule and cavity name for plots"""
    # Case 1: h5 file path
    match = re.search(r"CM(\w+)/CAV(\d+)/(\d{8})_(\d{6})", raw_name)
    if match:
        cm, cav, date_str, time_str = match.groups()
        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        formatted_time = f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
        return f"Cryomodule {cm}, Cavity {int(cav)}  |  {formatted_date} {formatted_time}"
    
    # Case 2: PV name 
    cm, cav = get_cm_cav_num_from_pv(raw_name)
    print(f"DEBUG case2 cm={repr(cm)} cav={repr(cav)}") 
    if cm and cav:
        return f"cryomodule {cm}, cavity {cav}" 
         
    print(f"Warning: Could not parse PV name: {raw_name}")
    return raw_name


def get_cm_cav_num_from_pv(pv_name):
    """Get cryomodule and cavity number from PV."""
    pv_parts = pv_name.split(":")
    try:
        # Assumes PV format ACCL:L3B:3180
        cav_num = pv_parts[2][2]
        cm_num = pv_parts[2][:2]
        return cm_num, cav_num
    except Exception as e:
        print(f"Error parsing PV name: {pv_name}. Exception: {e}")
        return None, None


def grab_common_data(df):
    """
    Extract forward, reverse, and reference waveforms from the Pandas DataFrame.
    """
    waveform_suffixes = [name for name, key in common_data]
    mask = df["pvname"].str.endswith(tuple(waveform_suffixes), na=False)
    return df[mask]


def label_to_values(quench_data):
    return {
        label: quench_data.loc[
            quench_data["pvname"].str.endswith(pv_suffix, na=False),
            "values",
        ].iloc[0]
        for pv_suffix, label in common_data
        if quench_data["pvname"].str.endswith(pv_suffix, na=False).any()
    }


def load_fault_file(filename):
    """Load one SRF fault file into a DataFrame."""
    rows = []
    with open(filename) as f:
        basefile = filename.split("/")[-1]
        for line in f:
            if line.startswith("#"):
                # TODO: handle comment lines
                continue  # skip comment lines
            components = line.strip().split()
            if len(components) < 3:
                # TODO: handle lines with insufficient data
                continue
            if "CAL" in line:
                # TODO: handle calibration timestamp lines skip for now
                continue
            if "ACQ_FLT_TS" in line:
                continue  # TODO: handle acquisition timestamp lines

            name = components[0]
            timestamp = components[1]
            cm_num, cav_num = get_cm_cav_num_from_pv(name)

            try:
                values = [float(x) for x in components[2:]]
            except ValueError:
                print(f"Warning: Skipping line due to conversion error: {line.strip()}")
                continue  # skip lines with non-numeric values

            rows.append(
                {
                    "file_date": make_timestamp_string(
                        basefile
                    ),  # gives YEARMONTHDAY_HOURMINUTESECOND
                    "pvname": name,
                    "cryomodule": cm_num,
                    "cavity": cav_num,
                    "data_timestamp": timestamp,
                    "values": values,
                    "source_file": basefile,  # just the filename without path
                }
            )
    df = pd.DataFrame(rows)
    return df


def make_timestamp_string(basefile):
    file_date = basefile.split("_")[3:5]
    return f"{file_date[0]}_{file_date[1]}"


def calculate_loaded_q(time_data, fault_data, frequency, saved_q_loaded):
    """
     This function is responsible for suggesting whether an event is real or false, this is how it works:
    - Trim the waveform to start at t = 0
    - Trim the tail once the amplitude is < 0.002
    - Fit ln(A0/A(t)) vs. time to a line; the slope gives the decay rate and loaded Q = (pi * frequency)/ slope
    - Suggest Real if the loaded Q is < (LOADED_Q_CHANGE_FOR_QUENCH * saved_q_loaded), otherwise suggest False 
   
    https://education.molssi.org/python-data-analysis/03-data-fitting/index.html

    """
    other = None

    time_data = np.asarray(time_data, dtype=float)
    fault_data = np.asarray(fault_data, dtype=float)
    frequency = float(np.asarray(frequency).flat[0])
    saved_q_loaded = float(np.asarray(saved_q_loaded).flat[0])


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


def validate_quench_lisa(quench_data):
    labeled_values = label_to_values(quench_data)

    if "frequency" not in labeled_values:
        print(f"Missing frequency in: {quench_data['source_file'].iloc[0]}")
        print(quench_data["pvname"].unique())
        labeled_values["frequency"] = np.array([1300000000.0])

    time_data = np.array(labeled_values["fault_time"])
    fault_data = np.array(labeled_values["fault_waveform"])
    frequency = np.array(labeled_values["frequency"])
    saved_q_loaded = float(labeled_values["saved_q_loaded"][0])

    return calculate_loaded_q(time_data, fault_data, frequency, saved_q_loaded)

"""
def validate_quench_lisa(quench_data):
    # This is as close to copy paste as possible from Lisa's function:
    # def validate_quench(self, wait_for_update: bool = False):
    
    Parsing the fault waveforms to calculate the loaded Q to try to determine
    if a quench was real.
    DERIVATION NOTES
    A(t) = A0 * e^((-2 * pi * cav_freq * t)/(2 * loaded_Q)) = A0 * e ^ ((-pi * cav_freq * t)/loaded_Q)
    ln(A(t)) = ln(A0) + ln(e ^ ((-pi * cav_freq * t)/loaded_Q)) = ln(A0) - ((pi * cav_freq * t)/loaded_Q)
    polyfit(t, ln(A(t)), 1) = [-((pi * cav_freq)/loaded_Q), ln(A0)]
    polyfit(t, ln(A0/A(t)), 1) = [(pi * f * t)/Ql]
    https://education.molssi.org/python-data-analysis/03-data-fitting/index.html
    :param wait_for_update: bool
    :return: bool representing whether quench was real
    

    LOADED_Q_CHANGE_FOR_QUENCH = 0.6
    other = None

    labeled_values = label_to_values(quench_data)
    if "frequency" not in labeled_values:
        print(f"Missing frequency in: {quench_data['source_file'].iloc[0]}")
        print(quench_data["pvname"].unique())
        labeled_values["frequency"] = np.array([1300000000.0])

    time_data = np.array(labeled_values["fault_time"])
    fault_data = np.array(labeled_values["fault_waveform"])
    frequency = np.array(labeled_values["frequency"])

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
        print(
            f"Warning: End of decay not found for {quench_data['source_file'].iloc[0]}, using all data points."
        )
        print(
            "Fault data length:",
            len(fault_data),
            "Fault data first/last values:",
            fault_data[0],
            fault_data[-1],
        )
        other = "end_decay_not_found"
        fault_data = fault_data[:]
        pre_quench_amp = fault_data[0]
        time_data = time_data[:]
    else:
        fault_data = fault_data[:end_decay]
        time_data = time_data[:end_decay]
        pre_quench_amp = fault_data[0]

    saved_loaded_q = float(labeled_values["saved_q_loaded"][0])

    try:
        with np.errstate(divide="raise", invalid="raise"):
            log_ratio = np.log(pre_quench_amp / fault_data)
            exponential_term = np.polyfit(time_data, log_ratio, 1)[0]
            loaded_q = (np.pi * frequency) / exponential_term
    except (FloatingPointError, ZeroDivisionError) as e:
        print(
            f"Warning: divide-by-zero / invalid value in "
            f"{quench_data['source_file'].iloc[0]}: {e}"
        )
        return {
            "is_real": False,
            "loaded_q": np.nan,
            "other_issue": "divide_by_zero_or_invalid_value",
        }

    thresh_for_quench = LOADED_Q_CHANGE_FOR_QUENCH * saved_loaded_q
    is_real = loaded_q < thresh_for_quench
    return {"is_real": is_real, "loaded_q": loaded_q, "other_issue": other}
"""
