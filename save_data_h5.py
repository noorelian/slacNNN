import numpy as np
import glob
from datetime import datetime, time
import pandas as pd
import h5py
import os
from srf_waveforms import load_fault_file, grab_common_waveforms, validate_quench_lisa

DATA_DIR = r"/Users/nneveu/Google Drive/My Drive/srf/q/"
#DATA_DIR = r"/mccfs2/u1/lcls/physics/rf_lcls2/fault_data"
LOADED_Q_CHANGE_FOR_QUENCH = 0.6 # fixed value to determine threshold

def _get_cav_num(lx, cm):
    "Get cyromodule and cavity number."
    return f"{lx:cm:02d}"

def _get_lx_dir(lx): 
    """Get accelerating section, L0, L1, L2, or L3 directory."""
    lnum = f"{lx:1d}"
    return os.path.join(DATA_DIR, f"ACCL_L{lnum}B_*")

def _get_quench_filenames(lx):
    """Get sorted quench files for Lx section."""
    lx_dir = _get_lx_dir(lx)
    quench_files = glob.glob(os.path.join(lx_dir, '**', '*QUENCH.txt'), recursive=True)
    return sorted(quench_files)

def save_filenames_to_txt(quench_files, output_txt):
    """Save list of quench filenames to a text file."""
    with open(output_txt, 'w') as f:
        for file in quench_files:
            f.write(f"{os.path.basename(file)}\n")

def load_quench_data(quench_files):
    """Load quench files and return DataFrame of all quench waveforms."""
    quench_data = pd.DataFrame() 
    for filename in quench_files:
        df = load_fault_file(filename)
        waveforms   = grab_common_waveforms(df)
        quench_data = pd.concat([quench_data, waveforms], ignore_index=True)
    return quench_data

# def validation_check(quench_data):
#     """Validate quench using Lisa's method and add classification to DataFrame."""
#     return 

# def _return_all_cm_data(all_data, cm):
#     """Return all data for a given cryomodule."""
#     return all_data[all_data['cryomodule'] == cm]

 
# --- Main execution block ---
for lx in range(3, 4): 
    # For each Lx section
    quench_files = _get_quench_filenames(lx)
    #output_txt = f"quench_files_L{lx}.txt"
    #save_filenames_to_txt(quench_files, output_txt)
    all_data  = load_quench_data(quench_files[:10])

    with h5py.File(f"quench_data_L{lx}.h5", 'w') as h5file:
        for (cm, cav), cav_data in all_data.groupby(["cryomodule", "cavity"], dropna=False):
            
            print(f"Processing CM{cm} CAV{cav}...")
            cm_group     = h5file.require_group(f"CM{cm}")
            cav_group    = cm_group.require_group(f"CAV{cav}")
            quench_files = cav_data['source_file'].unique()
            
            print(f"Data for CM{cm} CAV{cav} has {len(quench_files)} quench events.")
            for filename in quench_files:
                quench_data = cav_data[cav_data['source_file'] == filename]
                timestamp   = quench_data['file_date'].iloc[0]
    
                quench_group = cav_group.create_group(timestamp)
                import pdb; pdb.set_trace()
                quench_group.attrs['quench_classification'] = validate_quench_lisa(quench_data)
                quench_group.attrs['q_loaded'] = cav_data['q_loaded']
#                     #quench_group.attrs['calculated_q_value'] = row['calculated_q_value']
#                     quench_group.create_dataset('time_seconds', data=row['time_seconds'])
#                     quench_group.create_dataset('cavity_amplitude_MV', data=row['cavity_amplitude_MV'])
#                     quench_group.create_dataset('forward_power_W2', data=row['forward_power_W2'])
#                     quench_group.create_dataset('reverse_power_W2', data=row['reverse_power_W2'])
#                     if 'decay_reference_MV' in row:
#                         quench_group.create_dataset('decay_reference_MV', data=row['decay_reference_MV'])
#                     else:
#                         print(f"Warning: decay_reference_MV not found for {timestamp} in CM{cm} cavity{cav}")

    #TODO: save all_data (Lx) to an HDF5 file for easier access in the future.
    #TODO: save data by cryomodule, then by cavity, then by data. 
    #TODO: use pandas indexing to access data by cryomodule and cavity number.

# # --- OLD ---


# # defining a function to imcrement the quench count
# def increment_quench_count(group):
#     # if 'quench_count' already exists then we increment it
#     # if it doesn't exist yet then we set the value to one
#     if "quench_count" in group.attrs:   
#         group.attrs["quench_count"] += 1
#     else:
#         group.attrs["quench_count"] = 1



# # saving waveform and metadata to an HDF5 file
# output_filename = f"quench_data_CM{CM_num}.h5"

# # this block of code is for saving waveform data and metadata to an HDF45 File
# with h5py.File(output_filename, 'w') as h5file: 
#     for i, (filename, parts, timestamp_raw, timestamp_obj, file) in enumerate(quench_files):
#         # print("\nProcessing file: " + file)
        
#         # getting PV and timestamp information from the file
#         pv_base = parts[0] + ":" + parts[1] + ":" + parts[2]
#         timestamp = timestamp_obj.strftime("%Y-%m-%d_%H:%M:%S.").replace('.','')
#         timestamp = timestamp.split('_', 1)[-1] # gives only the HOUR:MINUTE:SECOND

#         # formatting date components
#         year = str(timestamp_obj.year)
#         month = f"{timestamp_obj.month:02d}"
#         day = f"{timestamp_obj.day:02d}"

#         # GROUP HIERARCHY : CM# (HDF5 file) > CAV# > YEAR > MONTH > DAY > TIMESTAMP
#         cavity = cavity_num.get(parts[2])               
#         cavity_group = h5file.require_group(cavity)     # '.require_group()' only creates a group if it doesn't already exist
#         increment_quench_count(cavity_group)            # if the group already exists then this line returns a reference to the existing group

#         year_group = cavity_group.require_group(year) 
#         increment_quench_count(year_group)              # incrementing the number of quenches at each level (cavity, year, month, etc)

#         month_group = year_group.require_group(month)
#         increment_quench_count(month_group)

#         day_group = month_group.require_group(day)
#         increment_quench_count(day_group)

#         quench_group = day_group.create_group(timestamp)

#         # constructing PV label strings
#         cavity_faultname = pv_base + ':CAV:FLTAWF'
#         forward_pow = pv_base + ':FWD:FLTAWF'
#         reverse_pow = pv_base + ':REV:FLTAWF'
#         decay_ref = pv_base + ':DECAYREFWF'  
#         time_range = pv_base + ':CAV:FLTTWF'
#         q_value = pv_base + ":QLOADED"          
#         freq_value = pv_base + ":FREQ" 

#         # extracting all data for quench waveform using defined function
#         cavity_data, cavity_time = extracting_data(file, cavity_faultname)
#         forward_data, forward_time = extracting_data(file, forward_pow)
#         reverse_data, reverse_time = extracting_data(file, reverse_pow)
#         decay_data, decay_time = extracting_data(file, decay_ref)
#         time_data, time_timestamp = extracting_data(file, time_range)
#         q_data, q_time = extracting_data(file, q_value)

#         # using try-except statement to catch where fault_data[0] is 'None'
#         # idea: file may be corrupt or waveform may be weird
#         try:
#             saved_loaded_q, calculated_q, classification = validate_quench(cavity_data, time_data, saved_loaded_q=q_data[0], frequency=1300000000.0)
#             quench_group.attrs['quench_classification'] = classification
#             quench_group.attrs['saved_q_value'] = saved_loaded_q
#             quench_group.attrs['calculated_q_value'] = calculated_q
#         except IndexError as e:
#             print(f"Processing {filename} failed with {e}")

#         # making them all the same length in case the length varies
#         forward_data = forward_data[:len(cavity_data)]

#         # saving waveform data into the group
#         quench_group.create_dataset('time_seconds', data=time_data)
#         quench_group.create_dataset('cavity_amplitude_MV', data=cavity_data)
#         quench_group.create_dataset('forward_power_W2', data=forward_data)
#         quench_group.create_dataset('reverse_power_W2', data=reverse_data)
        
#         if decay_data is not None:
#             quench_group.create_dataset('decay_reference_MV', data=decay_data)
#         else:
#             print(f"Warning: decay_data is None for {filename}")

#         # saving metadata for each quench as attributes
#         quench_group.attrs['filename'] = f"{filename}"
#         quench_group.attrs['timestamp'] = cavity_time
#         quench_group.attrs['faultname'] = cavity_faultname
#         quench_group.attrs['cavity_number'] = parts[2][2]
#         quench_group.attrs['cryomodule'] = parts[2][:2] 

# print(f"Data from {len(quench_files)} files successfully saved to {output_filename}.")
