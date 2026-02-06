import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Partial PVs to search for various waveforms
common_waveforms = [
        ('CAV:FLTAWF', 'fault_waveform'),
        ('FWD:FLTAWF', 'forward_power'),
        ('REV:FLTAWF', 'reverse_power'),
        ('DECAYREFWF', 'decay_reference'),
        ('ACQ_SAMP_PERIOD', 'sampling_period'),
    ]


def load_faults(filename):
    """
    Load SRF fault waveform data from a given text file.

    Parameters:
    filename (str): Path to the text file containing waveform data.

    Returns:
    dict: A dictionary containing time and waveform data arrays.
    """
    rows = []
    with open(filename) as f:
        for line in f:
            if line.startswith('#'):
                # TODO: handle comment lines
                continue  # skip comment lines
            components = line.strip().split()
            if len(components) < 3:
                # TODO: handle lines with insufficient data
                continue  # skip lines with less than 3 components
            name = components[0]
            timestamp = components[1]
            try:
                values = [float(x) for x in components[2:]]
                rows.append({"name": name, "timestamp": timestamp, "values": values})
            except ValueError:
                if 'CAL' in line:
                    # TODO: handle calibration timestamp lines skip for now
                    continue 
                print(f"Warning: Skipping line due to conversion error: {line.strip()}")
                continue  # skip lines with non-numeric values

    df = pd.DataFrame(rows)
    return df

def grab_waveforms(df):
    """
    Extract forward, reverse, and reference waveforms from the Pandas DataFrame.
    There are multiple rows with CAV:FLTAWF, so skip rows that are not waveforms.

    Parameters:
    df (pd.DataFrame): DataFrame containing waveform data.

    Returns:
    dict: A dictionary with extracted waveforms and timestamp.
    """

    waveforms = {}

    for name, key in common_waveforms:
        print(name, key)
        # Check if row name matches the waveform names.
        # This should return only one row per waveform type.
        row = df[df['name'].str.endswith(name, na=False)]
        print(row)
        if row.shape[0] == 0:
            print(f"Warning: No data found for waveform {name}")
            continue
        elif 'ACQ_SAMP_PERIOD' in name and row.shape[0] == 1:
            waveforms[key] = row.iloc[0]['values'][0] # Store sampling period as a single value
        # Make sure only one waveform was found
        elif row.shape[0] == 1 and len(row.iloc[0]['values'])>1:
            # Make sure waveform has more than one data points
            # TODO: confirm >1 assumptions are ok
            waveforms[key] = np.array(row.iloc[0]['values'])
        else:
            print(f"Warning: Data did not meet expected format for: {name}, skipping.")
            continue
        
     
    # After loop, grab timestamp and cavity info
    waveforms['cavity'] = df.iloc[0]['name']
    waveforms['timestamp'] = df.iloc[0]['timestamp']
    
    return waveforms #return dictionary of waveforms

def trim_waveform_data(waveform, threshold=None):
    """
    Trim the waveform based on derivative of the waveform.
    When the derivative falls below a certain threshold, we can assume the waveform has decayed to a stable state and trim the remaining data.

    Parameters:
    waveform (np.array): The input waveform data array.

    Returns:
    np.array: The trimmed waveform data array.
    """
    max_value = np.max(waveform)
    min_value = np.min(waveform)
    differences = np.abs(np.diff(waveform))

    if threshold is None:
        # Set a default threshold as 10% of the maximum value
        threshold = 0.1 * np.max(waveform)

    # Find indices where the absolute difference exceeds the threshold
    significant_indices = np.where(np.abs(np.diff(waveform)) > threshold)[0]

    if len(significant_indices) == 0:
        print("Warning: No significant changes found in the waveform.")
        return waveform  # Return original if no significant changes

    # Trim the waveform to include only data up to the last significant change
    last_significant_index = significant_indices[-1] + 1  # +1 to include the last point
    trimmed_waveform = waveform[:last_significant_index]

    return trimmed_waveform


def convert_cavity_pv_name(raw_name):
    """
    Convert pv base cavity name to a more readable format.

    Parameters:
    raw_name (str): Raw cavity name string.

    Returns:
    str: Formatted cavity name for plots, etc.
    """
    pv_parts = raw_name.split(':')
    if len(pv_parts) >= 3:
        # Assumes PV format ACCL:L3B:3180
        if 'ACCL' in pv_parts[0]:
            area    = pv_parts[1]
            cav_num = pv_parts[2][2]
            cm_num  = pv_parts[2][:2]
            formatted_name = f"L3B: cryomodule {cm_num}, cavity {cav_num}"
            return formatted_name
        return 
    return raw_name