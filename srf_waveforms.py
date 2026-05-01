import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Partial PVs to search for various waveforms
common_waveforms = [
        ('CAV:FLTAWF', 'fault_waveform'),
        ('FWD:FLTAWF', 'forward_power'),
        ('REV:FLTAWF', 'reverse_power'),
        ('DECAYREFWF', 'decay_reference'),
        ('CAV:FLTTWF', 'fault_time'),
        ('FWD:FLTTWF', 'forward_time'),
        ('REV:FLTTWF', 'reverse_time'),
        #('ACQ_SAMP_PERIOD', 'sampling_period'),
    ]

waveform_data = [key for _, key in common_waveforms]

def grab_waveforms(df):
    """
    Extract forward, reverse, and reference waveforms from the Pandas DataFrame.
    """
    waveform_suffixes = [name for name, key in common_waveforms]
    mask = df['waveform'].str.endswith(tuple(waveform_suffixes), na=False)
    return df[mask] 

def load_fault_file(filename):
    """
    Load all SRF fault waveform data from ONE fault text file.

    Returns:
    df (pd.DataFrame): a data frame containing time and waveform data arrays.
    """
    rows = []
    with open(filename) as f:
        basefile = filename.split('/')[-1]
        for line in f:
            if line.startswith('#'):
                # TODO: handle comment lines
                continue  # skip comment lines
            components = line.strip().split()
            if len(components) < 3:
                # TODO: handle lines with insufficient data
                continue 
            if 'CAL' in line:
                # TODO: handle calibration timestamp lines skip for now
                continue 
            if 'ACQ_FLT_TS' in line:
                continue # TODO: handle acquisition timestamp lines 
            
            name = components[0]
            timestamp = components[1]
            cm_num, cav_num = get_cm_cav_num_from_pv(name)

            try:
                values = [float(x) for x in components[2:]]
            except ValueError:
                print(f"Warning: Skipping line due to conversion error: {line.strip()}")
                continue  # skip lines with non-numeric values
                
            rows.append({
                "file_date": basefile.split('_')[3:5],  # gives only the DATE component
                "waveform": name,
                "cryomodule": cm_num,
                "cavity": cav_num,
                "timestamp": timestamp,
                "values": values,
                "source_file": basefile  # just the filename without path            
            })
    df = pd.DataFrame(rows)
    return df

def trim_single_waveform(waveform, derv_threshold=0.01):
    """
    Trim a single waveform based on the derivative of the waveform.
    When the derivative is near zero, we can assume the waveform has settled.
    """

    gradient = np.gradient(waveform)

    # Find indices where the absolute derivative is below the threshold (default 0.1%)
    low_gradient_indices = np.where(np.abs(gradient) > derv_threshold)[0]
    # Handle case where all values are within the derivative threshold
    if len(low_gradient_indices) == 0:
        return waveform

    # Get the first index where the gradient exceeds the threshold (start)
    start_index = low_gradient_indices[0] + 1 # +1 to get the actual array index

    # Get the last index where the gradient exceeds the threshold (end)
    end_index = low_gradient_indices[-1] + 1 # +1 to include this index in the result
    return start_index, end_index

def trim_waveform_dict(waveforms, derv_threshold=0.01):
    trimmed_waveforms = {}
    start, stop = trim_single_waveform(waveforms['fault_waveform'], derv_threshold)
    print('START:', start, 'STOP:', stop)

    for key in waveform_data:
        if key in waveforms:
            trimmed_waveforms[key] = waveforms[key][start:stop]
        else:
            print(f"Warning: {key} not found in waveforms dictionary, skipping trimming for this key.")
    return trimmed_waveforms

def get_cm_cav_num_from_pv(pv_name):
    """Get cryomodule and cavity number from PV."""
    pv_parts = pv_name.split(':')
    try:
        # Assumes PV format ACCL:L3B:3180
        area    = pv_parts[1]
        cav_num = pv_parts[2][2]
        cm_num  = pv_parts[2][:2]
        return cm_num, cav_num
    except Exception as e:
        print(f"Error parsing PV name: {pv_name}. Exception: {e}")
        return None, None

def convert_pv_name_plot_string(raw_name):
    """Make a cryomodule and cavity name for plots"""
    cm, cav = get_cm_cav_num_from_pv(raw_name)
    if cm and cav:
        formatted_name = f"L3B: cryomodule {cm}, cavity {cav}"
        return formatted_name
    else:
        print(f"Warning: Could not parse PV name: {raw_name}")
        return raw_name

def all_arrays_same_length(dictionary):
    """Check length of all arrays in the dictionary"""
    lengths = (len(arr) for arr in dictionary.values())
    # Convert the lengths to a set to check if all are the same
    return len(set(lengths)) == 1

def read_h5_waveforms(filename):
    """
    Read waveform data from an HDF5 file and return it as a dictionary.

    Parameters:
    filename (str): Path to the HDF5 file containing waveform data.

    Returns:
    dict: A dictionary with waveform data arrays and metadata.
    """
    import h5py
    waveforms = {}
    with h5py.File(filename, 'r') as f:
        for key in f.keys():
            waveforms[key] = f[key][:]
    return waveforms

def validate_quench_current(quench_data):
    """Validate quench by checking if cavity amplitude drops below 0.002 MV."""
    #This is as close to copy paste as possible from Lisa's function:
    #def validate_quench(self, wait_for_update: bool = False):
    """
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
    """

    LOADED_Q_CHANGE_FOR_QUENCH = 0.6

    time_data = quench_data["fault_time"] 
    fault_data = quench_data["fault_waveform"]
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

    fault_data = fault_data[:end_decay]
    time_data = time_data[:end_decay]
    #TODO: See where Leila uploaded this
    saved_loaded_q = self.current_q_loaded_pv_obj.get()

    pre_quench_amp = fault_data[0]

    exponential_term = np.polyfit(
        time_data, np.log(pre_quench_amp / fault_data), 1
    )[0]
    # TODO: see where leila uploaded frequency
    loaded_q = (np.pi * self.frequency) / exponential_term

    thresh_for_quench = LOADED_Q_CHANGE_FOR_QUENCH * saved_loaded_q
    is_real = loaded_q < thresh_for_quench
    print("Validation: ", is_real)

    return is_real


## OLD or delete? 
# list of keys for waveforms in the dictionary
# waveform_data = [common_waveforms[i][1] for i in range(len(common_waveforms))] 
# def load_waveform_data(filename):
#         with open(filename) as f:
#         for line in f:
#             components = line.strip().split()
#             name = components[0]
#             timestamp = components[1]
#             # Check if any of the keys are in this line
#             try:
#                 values = [float(x) for x in components[2:]]
#             except ValueError:
#                 if 'CAL' in line:
#                     # TODO: handle calibration timestamp lines skip for now
#                     continue 
#                 print(f"Warning: Skipping line due to conversion error: {line.strip()}")
#                 continue  # skip lines with non-numeric values
#             waveforms[key] = np.array(values)