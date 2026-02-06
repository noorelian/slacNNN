import matplotlib.pyplot as plt
import numpy as np
from srf_waveforms import *

false_quenchfile = 'ACCL_L3B_3180_20220630_164905_QUENCH.txt'   # file with false quench waveform data
false_quenchdata = load_faults(false_quenchfile)

real_quenchfile = 'ACCL_L3B_3180_20220810_184057_QUENCH.txt'    # file with real quench waveform data
real_quenchdata = load_faults(real_quenchfile)
false_wf = grab_waveforms(false_quenchdata)
real_wf = grab_waveforms(real_quenchdata)
#print(false_wf)

def make_time_axis(wf):
    """Create a time axis based on the sampling period 
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


# plot setup
# Define line styles for keys
line_styles = {
    'fault_waveform': {'color': 'red', 'marker': 's'},
    'forward_power': {'color': 'green', 'marker': 'o'},
    'reverse_power': {'color': 'orange', 'marker': 'x'},
    'decay_reference': {'color': 'blue', 'linestyle': '--'},
}

def plot_all_waveforms(wf):
    plt.figure(figsize=(14,6))
    for key, data in wf.items():
        # Plot all four waveforms
        style = line_styles.get(key, {})
        plt.plot(data, label=key, **style)
    plt.show()

def plot_quench_waveforms(wf):
    # grab the time axis for the waveforms
    time_axis = make_time_axis(wf)
    print("Time axis:", time_axis)
    if time_axis is None:
        print("Error: Time axis could not be created. Check waveform data and sampling period.")
        return
    # Plot quench waveform and decay reference only
    if 'fault_waveform' in wf:
        style = line_styles.get('fault_waveform', {})
        plt.plot(time_axis, wf['fault_waveform'], label='Cavity fault waveform', **style)
    if 'decay_reference' in wf:
        style = line_styles.get('decay_reference', {})
        plt.plot(time_axis, wf['decay_reference'], label='Normal decay reference', **style)
    return 

def set_plot_labels(wf, timestamp=False):   
    cmcav = convert_cavity_pv_name(wf['cavity'])    
    if timestamp:
        plt.title(f"Quench Waveforms: {cmcav}\nTimestamp {wf['timestamp']}")
    else:
        plt.title(f"Quench Waveforms: {cmcav}")
    plt.xlabel('Time (s)')
    plt.ylabel('MV')
    plt.tight_layout()
    plt.legend()
    plt.show()


plt.figure(figsize=(14,6))
# Call the plotting functions
plot_quench_waveforms(false_wf)
#plot_quench_waveforms(real_wf)
set_plot_labels(false_wf)