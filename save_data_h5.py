import numpy as np
import glob
from datetime import datetime
import pandas as pd
import h5py
import os
from srf_waveforms import load_faults, waveform_data, grab_waveforms

DATA_DIR = r"/mccfs2/u1/lcls/physics/rf_lcls2/fault_data"
LOADED_Q_CHANGE_FOR_QUENCH = 0.6 # fixed value to determine threshold

def _get_cav_num(cm, lx):
    "Get cyromodule and cavity number."
    return f"{lx:cm:02d}"

def _get_lx_dir(lx): 
    """Get accelerating section, L0, L1, L2, or L3 directory."""
    lnum = f"{lx:1d}"
    return os.path.join(DATA_DIR, f"ACCL_L{lnum}B_*")

def _get_quench_filenames(lx_dir):
    """Get sorted quench files for Lx section."""
    quench_files = glob.glob(os.path.join(lx_dir, '**', '*QUENCH.txt'), recursive=True)
    return sorted(quench_files)

def save_filenames_to_txt(quench_files, output_txt):
    """Save list of quench filenames to a text file."""
    with open(output_txt, 'w') as f:
        for file in quench_files:
            f.write(f"{os.path.basename(file)}\n")

def load_quench_files(quench_files):
    """Load quench files and put waveforms into a list of dictionaries."""
    quench_data = []
    for filename in quench_files:
        df = load_faults(filename)
        waveforms = grab_waveforms(df)
        quench_data.append(waveforms)
    return quench_data

# --- Main execution block ---
for lx in range(0, 4): 
    # For each Lx section. 
    lx_dir = _get_lx_dir(lx)
    quench_files = _get_quench_filenames(lx_dir)
    #output_txt = f"quench_files_L{lx}.txt"
    #save_filenames_to_txt(quench_files, output_txt)
    all_data  = load_quench_files(quench_files)
    waveforms = grab_waveforms(all_data)


# --- OLD ---
def validate_quench(fault_data, time_data, saved_loaded_q, frequency):
    # starts the time closer to when the quench happens to make the fit more accurate
    time_0 = 0
    for time_0, timestamp in enumerate(time_data):
        if timestamp >= 0:
            break
    
    fault_data = fault_data[time_0:]
    time_data = time_data[time_0:]

    # ends the time closer to when the quench is over to eliminate when the amplitude=0
    end_decay = len(fault_data) - 1
    for end_decay, amp in enumerate(fault_data):
        if amp < 0.002:
            break
    
    fault_data = fault_data[:end_decay]
    time_data = time_data[:end_decay]

    pre_quench_amp = fault_data[0]

    exponential_term = np.polyfit(time_data, np.log(pre_quench_amp / fault_data), 1)[0]
    loaded_q = (np.pi * frequency) / exponential_term

    thresh_for_quench = LOADED_Q_CHANGE_FOR_QUENCH * saved_loaded_q

    is_real = loaded_q < thresh_for_quench

    return saved_loaded_q, loaded_q, is_real

# defining a function to imcrement the quench count
def increment_quench_count(group):
    # if 'quench_count' already exists then we increment it
    # if it doesn't exist yet then we set the value to one
    if "quench_count" in group.attrs:   
        group.attrs["quench_count"] += 1
    else:
        group.attrs["quench_count"] = 1



# saving waveform and metadata to an HDF5 file
output_filename = f"quench_data_CM{CM_num}.h5"

# this block of code is for saving waveform data and metadata to an HDF45 File
with h5py.File(output_filename, 'w') as h5file: 
    for i, (filename, parts, timestamp_raw, timestamp_obj, file) in enumerate(quench_files):
        # print("\nProcessing file: " + file)
        
        # getting PV and timestamp information from the file
        pv_base = parts[0] + ":" + parts[1] + ":" + parts[2]
        timestamp = timestamp_obj.strftime("%Y-%m-%d_%H:%M:%S.").replace('.','')
        timestamp = timestamp.split('_', 1)[-1] # gives only the HOUR:MINUTE:SECOND

        # formatting date components
        year = str(timestamp_obj.year)
        month = f"{timestamp_obj.month:02d}"
        day = f"{timestamp_obj.day:02d}"

        # GROUP HIERARCHY : CM# (HDF5 file) > CAV# > YEAR > MONTH > DAY > TIMESTAMP
        cavity = cavity_num.get(parts[2])               
        cavity_group = h5file.require_group(cavity)     # '.require_group()' only creates a group if it doesn't already exist
        increment_quench_count(cavity_group)            # if the group already exists then this line returns a reference to the existing group

        year_group = cavity_group.require_group(year) 
        increment_quench_count(year_group)              # incrementing the number of quenches at each level (cavity, year, month, etc)

        month_group = year_group.require_group(month)
        increment_quench_count(month_group)

        day_group = month_group.require_group(day)
        increment_quench_count(day_group)

        quench_group = day_group.create_group(timestamp)

        # constructing PV label strings
        cavity_faultname = pv_base + ':CAV:FLTAWF'
        forward_pow = pv_base + ':FWD:FLTAWF'
        reverse_pow = pv_base + ':REV:FLTAWF'
        decay_ref = pv_base + ':DECAYREFWF'  
        time_range = pv_base + ':CAV:FLTTWF'
        q_value = pv_base + ":QLOADED"          
        freq_value = pv_base + ":FREQ" 

        # extracting all data for quench waveform using defined function
        cavity_data, cavity_time = extracting_data(file, cavity_faultname)
        forward_data, forward_time = extracting_data(file, forward_pow)
        reverse_data, reverse_time = extracting_data(file, reverse_pow)
        decay_data, decay_time = extracting_data(file, decay_ref)
        time_data, time_timestamp = extracting_data(file, time_range)
        q_data, q_time = extracting_data(file, q_value)

        # using try-except statement to catch where fault_data[0] is 'None'
        # idea: file may be corrupt or waveform may be weird
        try:
            saved_loaded_q, calculated_q, classification = validate_quench(cavity_data, time_data, saved_loaded_q=q_data[0], frequency=1300000000.0)
            quench_group.attrs['quench_classification'] = classification
            quench_group.attrs['saved_q_value'] = saved_loaded_q
            quench_group.attrs['calculated_q_value'] = calculated_q
        except IndexError as e:
            print(f"Processing {filename} failed with {e}")

        # making them all the same length in case the length varies
        forward_data = forward_data[:len(cavity_data)]

        # saving waveform data into the group
        quench_group.create_dataset('time_seconds', data=time_data)
        quench_group.create_dataset('cavity_amplitude_MV', data=cavity_data)
        quench_group.create_dataset('forward_power_W2', data=forward_data)
        quench_group.create_dataset('reverse_power_W2', data=reverse_data)
        
        if decay_data is not None:
            quench_group.create_dataset('decay_reference_MV', data=decay_data)
        else:
            print(f"Warning: decay_data is None for {filename}")

        # saving metadata for each quench as attributes
        quench_group.attrs['filename'] = f"{filename}"
        quench_group.attrs['timestamp'] = cavity_time
        quench_group.attrs['faultname'] = cavity_faultname
        quench_group.attrs['cavity_number'] = parts[2][2]
        quench_group.attrs['cryomodule'] = parts[2][:2] 

print(f"Data from {len(quench_files)} files successfully saved to {output_filename}.")
