import numpy as np
import glob
import pandas as pd
import h5py
import os
from srf_waveforms import load_fault_file, grab_common_data, validate_quench_lisa, label_to_values

DATA_DIR = r"/Users/nneveu/Google Drive/My Drive/srf/q/"
#DATA_DIR = r"/mccfs2/u1/lcls/physics/rf_lcls2/fault_data"

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
    quench_data = []
    for filename in quench_files:
        df = load_fault_file(filename)
        quench_data.append(grab_common_data(df))
    return pd.concat(quench_data, ignore_index=True)

# def _return_all_cm_data(all_data, cm):
#     """Return all data for a given cryomodule."""
#     return all_data[all_data['cryomodule'] == cm]

 
# --- Main execution block ---
all_data = [] #pd.DataFrame()
for lx in range(4): 
    # For each Lx section
    quench_files = _get_quench_filenames(lx)
    #output_txt = f"quench_files_L{lx}.txt"
    #save_filenames_to_txt(quench_files, output_txt)
    all_data.append(load_quench_data(quench_files))
all_data  = pd.concat(all_data, ignore_index=True)
all_data.to_pickle(f"all_quench_data.pkl")

with h5py.File(f"quench_data_L0-L3.h5", 'w') as h5file:
    for (cm, cav), cav_data in all_data.groupby(["cryomodule", "cavity"], dropna=False):
        
        print(f"Processing CM{cm} CAV{cav}...")
        cm_group     = h5file.require_group(f"CM{int(cm)}")
        cav_group    = cm_group.require_group(f"CAV{int(cav)}")
        quench_files = cav_data['source_file'].unique()
        
        print(f"Data for CM{cm} CAV{cav} has {len(quench_files)} quench events.")
        for filename in quench_files:
            quench_data = cav_data[cav_data['source_file'] == filename]
            timestamp   = quench_data['file_date'].iloc[0]

            labeled_values = label_to_values(quench_data)
            quench_group = cav_group.create_group(timestamp)
            is_real, loaded_q = validate_quench_lisa(quench_data)
            quench_group.attrs['quench_classification'] = is_real #boolean
            quench_group.attrs['calculated_q_loaded']   = loaded_q

            for label, values in labeled_values.items():
                if len(values)>1: # don't save freq and q again
                    quench_group.create_dataset(label, data=values)
                elif label in ['frequency', 'saved_q_loaded']:
                    quench_group.attrs[label] = values[0] 

# # --- OLD ---
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
#         # using try-except statement to catch where fault_data[0] is 'None'
#         # idea: file may be corrupt or waveform may be weird
#         try:
#             saved_loaded_q, calculated_q, classification = validate_quench(cavity_data, time_data, saved_loaded_q=q_data[0], frequency=1300000000.0)
#             quench_group.attrs['quench_classification'] = classification
#             quench_group.attrs['saved_q_value'] = saved_loaded_q
#             quench_group.attrs['calculated_q_value'] = calculated_q
#         except IndexError as e:
#             print(f"Processing {filename} failed with {e}")
