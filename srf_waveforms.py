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
waveform_data = ['fault_waveform', 'forward_power', 'reverse_power', 'decay_reference']

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
        # Check if row name matches the waveform names.
        # This should return only one row per waveform type.
        row = df[df['name'].str.endswith(name, na=False)]
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

def make_time_axis(wf):
    """
    Create a time axis based on the sampling period 
    and number of data points in the waveforms.
    Check that all waveforms have the same length before creating the time axis.

    Parameters: wf (dict): A dictionary of waveform data and sampling period.
    Returns: np.array: An array representing the time axis for the waveforms.
    """
    if 'sampling_period' not in wf:
        print("Error: Sampling period not found in waveforms dictionary.")
        return None
    
    points = {}
    sampling_period = wf['sampling_period']
    for key in waveform_data:
        print(key, wf[key])
        points[key] = wf[key]
    
    # Check all keys have the same length
    check = all_arrays_same_length(points)
    if not check:
        print("Error: Not all waveform arrays have the same length.")
        return None

    num_points_value = len(next(iter(points.values())))  # Get the length of the first array
    time_axis = (np.arange(num_points_value)-num_points_value//2) * sampling_period
    return time_axis

def trim_waveform_data(waveform, derv_threshold=0.01):
    """
    Trim the waveform based on the derivative of the waveform.
    When the derivative is near zero, we can assume the waveform has settled.

    Parameters:
    waveform (np.array): The input waveform data array.

    Returns:
    np.array: The trimmed waveform data array.
    """
    # Calculate the gradient (derivative)
    gradient = np.gradient(waveform)

    # Find indices where the absolute gradient is below the threshold (default 0.1%)
    low_gradient_indices = np.where(np.abs(gradient) > derv_threshold)[0]
    print("LOW", low_gradient_indices)

    # Handle case where all values are within the gradient threshold
    if len(low_gradient_indices) == 0:
        return waveform

    # Get the first index where the gradient exceeds the threshold (start)
    start_index = low_gradient_indices[0] + 1  # +1 to get the actual array index

    # Get the last index where the gradient exceeds the threshold (end)
    end_index = low_gradient_indices[-1] + 1    # +1 to include this index in the result
    return start_index, end_index

def trim_waveform_dict(waveforms, derv_threshold=0.01):
    trimmed_waveforms = {}
    # grab the time axis for the waveforms
    time_axis   = make_time_axis(waveforms)
    start, stop = trim_waveform_data(waveforms['fault_waveform'], derv_threshold)
    print('START:', start, 'STOP:', stop)
    # Time key is not in the waveform dict, add it here after trimming
    trimmed_waveforms['time_axis'] = time_axis[start:stop]

    for key in waveform_data:
        if key in waveforms:
            trimmed_waveforms[key] = waveforms[key][start:stop]
        else:
            print(f"Warning: {key} not found in waveforms dictionary, skipping trimming for this key.")
    return trimmed_waveforms

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

def all_arrays_same_length(dictionary):
    # Extract the lengths of all arrays using a generator expression
    lengths = (len(arr) for arr in dictionary.values())
    # Convert the lengths to a set to check if all are the same
    return len(set(lengths)) == 1