
SIGNAL_TIME_MAP = {
    "forward_power": "forward_time",
    "reverse_power": "reverse_time",
    "fault_waveform": "fault_time",
    "decay_reference": "forward_time",  
}
# Styles for the plot
STYLES = {
   'fault_waveform':  {'color': 'indigo', 'linestyle': '-',  'linewidth': 3, 'alpha': 1.0,
                        'marker': None},                      
    'forward_power':   {'color': 'green', 'linestyle': '-',  'linewidth': 2, 'alpha': 1.0,
                        'marker': 'o', 'markersize': 6, 'markevery': 50},  
    'reverse_power':   {'color': 'orange', 'linestyle': '-', 'linewidth': 2, 'alpha': 1.0,
                        'marker': 'x', 'markersize': 6, 'markevery': 50},  
    'decay_reference': {'color': 'darkcyan', 'linestyle': ':',  'linewidth': 3, 'alpha': 1.0,
                        'marker': None},                       
   # 'fault_waveform': {'color': 'indigo', 'linestyle': '-', 'linewidth': 3, 'alpha': 0.5},
   # 'forward_power': {'color': 'green', 'marker': 'o', 'markersize':3, 'markevery':30},
    #'reverse_power': {'color': 'orange', 'marker': 'x', 'markersize':3, 'markevery':30},
    #'decay_reference': {'color': 'darkcyan', 'linestyle': '--', 'linewidth': 3, 'alpha':0.5},
}

#fig, ax = plt.subplots(figsize=(7, 3.5))
LINE_STYLES = {"-": "solid", "--": "dash", ":": "dot", "-.": "dashdot"}
MARKERS = {"o": "circle", "x": "x", "s": "square", "^": "triangle-up", "d": "diamond"}

# the attributes used for lableing the events 
LABELS = "quench_labels" # REAL, FALSE OR OTHER 
CHECKED = "checked" # checked or unchecked(True or false)
NOTE = "note"  # note BY CHECKER 
CHECKED_AT = "checked_at" # TIME WHEN CHECKED
NEEDS_SPECIALIST = "needs_specialist" # someone should go and chcek the cavity 

# used for classification suggestion
FREQUENCY_KEYS = ["frequency", "FREQ"] #used for searching for the cavity frequency 
SAVED_Q_LOADED_KEYS = ["saved_q_loaded", "QLOADED"] # used for searching for the saved loaded Q 
LOADED_Q_CHANGE_FOR_QUENCH = 0.6 #if Q < 0.6, it is a real quench 
