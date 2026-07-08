import streamlit as st # used for the web interface (to run it locally)
import h5py 
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime 
 
st.set_page_config(page_title="Quench Labeler", layout="wide") #configure the streamlit website 
st.title("Plot a Waveform/Quench ")
 

# This is mapping the signals with their matching time signals (for plots) 
SIGNAL_TIME_MAP = {
    "decay_reference": "forward_time",   # used forward time for decay reference because it is the only one that is always present, not sure, ask nicole about this 
    "fault_waveform": "fault_time",
    "forward_power": "forward_time",
    "reverse_power": "reverse_time",
}
# colors for the plot, used similar colors to leila's plots 
COLORS = {
    "decay_reference": "tab:blue",
    "fault_waveform": "tab:orange",
    "forward_power": "tab:green",
    "reverse_power": "tab:red",
}

# the attributes used for lableing the events 
LABELS = "quench_labels" # REAL, FALSE OR OTHER 
CHECKED = "checked" # checked or unchecked(True or false)
NOTE = "note"  # note BY CHECKER 
CHECKED_AT = "checked_at" # TIME WHEN CHECKED
NEEDS_SPECIALIST = "needs_specialist" # someone should go and chcek the cavity 
 
 
def find_event_groups(hddf5_file):
    """This function is for finding each event groups/identifiers (decay ref, forward power, fault waveform) for each cm/cav/date, used for plotting """
    events = []
 
    def visitor(name, obj):
        """ This function is for exploring the h5 file structure"""
        if isinstance(obj, h5py.Group):
            keys = set(obj.keys())
            if keys & set(SIGNAL_TIME_MAP.keys()):
                events.append(name)
 
    hddf5_file.visititems(visitor)
    return sorted(events)

def write_label(file_path, event_path, label, SRF_note, needs_specialist):
    """ writing the label, note and checked status to the hdf5 file for each event (cm/cav/date) """
    note = SRF_note.strip() if SRF_note and SRF_note.strip() else f"This event has been already checked and the waveform was labeled as {label.upper()}"

    # open in append mode 
    with h5py.File(file_path, "a") as f:
        group = f[event_path]
        group.attrs[LABELS] = label
        group.attrs[CHECKED] = True
        group.attrs[NOTE] = note
        group.attrs[CHECKED_AT] = datetime.now().isoformat()
        group.attrs[NEEDS_SPECIALIST] = bool (needs_specialist)
 
 
selected_path = st.text_input("Enter the full HDF5 File Path", value="")    # Getting the HDF5 file path from the user 
 

# if nothing was entered, it will reask you to enter a path 
if not selected_path:
    st.info("Enter the full path to a HDF5 file above.")
    st.stop()
 
# if entered something else otherthan a file path, it will give you an error message 
if not os.path.isfile(selected_path):
    st.error(f"File not found: {selected_path}")
    st.stop()

# exception for opening the file, if the file type is incorrect, it will give you an error message 
try:
     with h5py.File(selected_path, "r") as f:
         events = find_event_groups(f)
         event_status = {}
         for event in events:
             attrs = f[event].attrs
             event_status[event] = {
                "checked": bool(attrs.get(CHECKED, False)),
                "label": attrs.get(LABELS, None),
                "note": attrs.get(NOTE, None),
                "checked_at": attrs.get(CHECKED_AT, None),
                "needs_specialist": bool(attrs.get(NEEDS_SPECIALIST, False))
             }

except Exception as e:
    st.error(f"Could not open file as HDF5: {e}") # throw an exception if the file is not a valid HDF5 file and stop 
    st.stop()
 
# if no events were found, it will give you a warning message then close the file and stop 
if not events:
    st.warning("No recognizable quench events found in this file.")
    f.close()
    st.stop()

# A function that is responsible for the status of the file in the dropdown
def checked_status(event_path):
    """ This is how the files will be formatted in the dropdown, (event path , checked: Yes or No,  label: real, false, other or unlabled) """
    status = event_status[event_path]
    flag = "SPECIALIST" if status["needs_specialist"] else ""
    if status["checked"]:
        return f"{event_path}, Checked: Yes, Label: {status['label']}{flag}"
    else: 
        return f"{event_path}, Checked: No, Label: unlabeled {flag}"

event_path = st.selectbox(f"Select event ({len(events)} found)", events, format_func=checked_status) # Allowing the user to choose the event from the dropdown

# A function to format the event status(checked or unchecked), label(Real or False or Other) and note
def format_event_status(event, status):
    checked = "Yes" if status["checked"] else "No"
    label = status["label"] if status["label"] else "unlabeled"
    note = status["note"] if status["note"] else "None"
    when = status["checked_at"] if status["checked_at"] else ""
    flag = "A specialist should go and check the cavity" if status["needs_specialist"] else ""
    return f"{event}, Checked: {checked}, Label: {label}, Note: {note} (last updated: {when}{flag})"


current_status = event_status[event_path]

# if the event was checked, show the event name(cm/cav/date and the status)
if current_status["checked"]:
    st.info(format_event_status(event_path, current_status))

if current_status["needs_specialist"]:
    st.warning("A specialist needs to inspect the cavity")

# load the waveform data for the event you chose 
with h5py.File(selected_path, "r") as f:
    group = f[event_path]
    signal_data ={}

    for signal_name, time_name in SIGNAL_TIME_MAP.items():
        if signal_name not in group: # if an event is missing some attributes like the very first ones in 2022, skip the missing attributes 
            continue

        y = np.array(group[signal_name]) # load the signals(attributes) into array 
        x = None 

        if time_name in group:
            t = np.array(group[time_name]) # load time data into array 
            # only assign t to x if its shape matches that of y 
            if t.shape[0] == y.shape[0]:
                x = t

            if x is None:
                x = np.arange(y.shape[0]) # if no time is available, create an x-axis starts from 0 to the length of y 

            signal_data[signal_name] = (x, y) # store the loaded signal data 


 
fig, ax = plt.subplots(figsize=(7, 3.5))

# plot every attribute with the correspoding time 
for signal_name, (x, y) in signal_data.items():
    ax.plot(x, y, label=signal_name, color=COLORS.get(signal_name))

ax.set_title(event_path) # Titlke of the plot 
ax.set_xlabel("Time (s)") # x-axis
ax.set_ylabel("Amplitude") # y-axis 
ax.legend() #legend for the plot 
ax.grid(alpha=0.3) #grid on
st.pyplot(fig, use_container_width=False)  #dispaly in the streamlit app 

# Labeling the waveform 
st.subheader("Label this waveform")
existing_note = current_status["note"] if current_status["note"] else ""
SRF_note = st.text_area(
    "Add a note (optional), If you decide to leave it blank, a generated note will be used.", 
    value="", 
    key=f"note_{event_path}") #textbox to insert a note 

needs_specialist = st.checkbox(
    "Needs specialist to inpect the cavity in person", value =current_status["needs_specialist"], key=f"specilist_{event_path}"
)

# 3 colums fo the 3 options (real, false , other)
col1, col2, col3 = st.columns(3)

 
clicked_option = None # a variable that records which button was chosen 

with col1:
    # set clicked_option = real if "REAL" was chosen
    if st.button("REAL", use_container_width=True):
        clicked_option= "real"

with col2:
    # set clicked_option = false if "FALSE" was chosen 
    if st.button("FALSE", use_container_width=True):
        clicked_option = "false"

    # se the clicked_option = other if "OTHER" was chosen 
with col3:
    if st.button("OTHER", use_container_width=True):
        clicked_option = "other"
 
# if any option/button was clicked, update the label and the status of the event 
if clicked_option:
    try:
        write_label(selected_path, event_path, clicked_option, SRF_note, needs_specialist) # write the label and notes to the hdf5 file 
        st.success(f"Saved: '{event_path}' marked as **{clicked_option.upper()}** and checked.") 
        st.rerun()      # Keep the update in the records 
    # Throw an exception if anything wrong happened 
    except Exception as e:
        st.error(f"Could not write label to file: {e}") 

 