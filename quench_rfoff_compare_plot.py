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
    trimmed = trim_waveform_dict(wf, derv_threshold=0.00015)
    # Plot quench waveform and decay reference only
    if 'fault_waveform' in trimmed:
        style = line_styles.get('fault_waveform', {})
        plt.plot(trimmed['fault_time'], trimmed['fault_waveform'], label='Cavity fault waveform', **style)
    if 'decay_reference' in trimmed:
        style = line_styles.get('decay_reference', {})
        plt.plot(trimmed['fault_time'], trimmed['decay_reference'], label='Normal decay reference', **style)
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


plt.figure(figsize=(6,6))
# Call the plotting functions
plot_quench_waveforms(false_wf)
#plot_quench_waveforms(real_wf)
set_plot_labels(false_wf)