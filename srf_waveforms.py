import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Partial PVs to search for various waveforms
common_waveforms = [
        ('CAV:FLTAWF', 'fault_waveform'),
        ('FWD:FLTAWF', 'forward_power'),
        ('REV:FLTAWF', 'reverse_power'),
        ('DECAYREFWF', 'decay_reference')
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
                    continue  # skip calibration timestamp lines for now
                print(f"Warning: Skipping line due to conversion error: {line.strip()}")
                continue  # skip lines with non-numeric values

    df = pd.DataFrame(rows)
    
    return df

def grab_waveforms(df):
    """
    Extract forward, reverse, and reference waveforms from the DataFrame.
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
        
        # TODO: confirm >1 assumptions are ok
        if row.shape[0] == 0:
            print(f"Warning: No data found for waveform {name}")
            continue
        # Make sure only one waveform was found
        elif row.shape[0] == 1:
            # Make sure waveform has more than one data points
            if len(row.iloc[0]['values'])>1:
                waveforms[key] = np.array(row.iloc[0]['values'])
    return waveforms #return dictionary of waveforms