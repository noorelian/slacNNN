import streamlit as st # used for the web interface (to run it locally)
import h5py 
import numpy as np
#import matplotlib.pyplot as plt
import plotly.graph_objects as go 
import os
from datetime import datetime 
import re 
 
st.set_page_config(page_title="Quench Labeler", layout="wide") #configure the streamlit website 
st.title("Plot a Waveform/Quench ")
 

# This is mapping the signals with their matching time signals (for plots) 
SIGNAL_TIME_MAP = {
    "forward_power": "forward_time",
    "reverse_power": "reverse_time",
    "fault_waveform": "fault_time",
    "decay_reference": "forward_time",  
}
# Styles for the plot, used similar colors to leila's plots 
STYLES = {
    'fault_waveform': {'color': 'indigo', 'linestyle': '-', 'linewidth': 3, 'alpha': 0.5},
    'forward_power': {'color': 'green', 'marker': 'o', 'markersize':3, 'markevery':30},
    'reverse_power': {'color': 'orange', 'marker': 'x', 'markersize':3, 'markevery':30},
    'decay_reference': {'color': 'darkcyan', 'linestyle': '--', 'linewidth': 3, 'alpha':0.5},
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
        group.attrs[CHECKED_AT] = datetime.now().strftime("%Y-%m-%d")
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
    if status["checked"]:
        return f"{event_path}, Checked: Yes, Label: {status['label'].upper()}"
    else: 
        return f"{event_path}, Checked: No, Label: unlabeled"

event_path = st.selectbox(f"Select event ({len(events)} found)", events, format_func=checked_status) # Allowing the user to choose the event from the dropdown

def parse_event_path(event_path):
  
    parts = event_path.split("/")  # -> ['CM01', 'CAV1', '20220329_103006']

    cryomodule = parts[0] if len(parts) > 0 else "unknown"
    cavity = parts[1] if len(parts) > 1 else "unknown"
    raw_timestamp = parts[2] if len(parts) > 2 else "unknown"

    # Try to format the timestamp '20220329_103006' -> '2022-03-29 10:30:06'
    try:
        dt = datetime.strptime(raw_timestamp, "%Y%m%d_%H%M%S")
        fault_date = dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        fault_date = raw_timestamp  # fall back to the raw string if parsing fails

    return cryomodule, cavity, fault_date


# A function to format the event status(checked or unchecked), label(Real or False or Other) and note
def format_event_status(event_path, status, cryomodule, cavity, fault_date):
    checked = "Yes" if status["checked"] else "No"
    label = status["label"] if status["label"] else "unlabeled"
    note = status["note"] if status["note"] else "None"
    when = status["checked_at"] if status["checked_at"] else ""
    flag = "Yes" if status["needs_specialist"] else "No"

    table = f"""
    | **Event name**                        | {event_path}                        |
    |---------------------------------------|-------------------------------------|
    | **Checked**                           | {checked}                           |
    | **Label**                             | {label}                             |
    | **Note**                              | {note}                              |
    | **Need a specialist to inspect cavity** | {flag}                            |
    | **Last updated**                      | {when}                              |
    """

    #return f"{event} | Checked: {checked} | Label: {label} | Note: {note} | Need a specilist to inspect the cavity: {flag} | (last updated: {when})"
    return table 


current_status = event_status[event_path]

cryomodule, cavity, fault_date = parse_event_path(event_path)

st.markdown(
    format_event_status(event_path, current_status, cryomodule, cavity, fault_date),
    unsafe_allow_html=True
)

# if the event was checked, show the event name(cm/cav/date and the status)
#if current_status["checked"]:
    #st.markdown(format_event_status(event_path, current_status), unsafe_allow_html=True)

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

#fig, ax = plt.subplots(figsize=(7, 3.5))
LINE_STYLES = {"-": "solid", "--": "dash"}
MARKERS = {"o":"circle", "x": "x"}

def plot_style(signal_name, x, y):
    style = STYLES.get(signal_name, {})
    color = style.get("color")
    dash = LINE_STYLES.get(style.get("linestyle", "-"), "solid")
    width = style.get("linewidth", 2)
    opacity = style.get("alpha", 1.0)  # matplotlib's alpha -> Plotly's opacity
 
    traces = [
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            name=signal_name,
            legendgroup=signal_name,
            opacity=opacity,
            line=dict(color=color, dash=dash, width=width),
        )
    ]
 
    marker_symbol = MARKERS.get(style.get("marker"))
    if marker_symbol:
        markevery = style.get("markevery", 1)
        markersize = style.get("markersize", 6)
        traces.append(
            go.Scatter(
                x=x[::markevery],
                y=y[::markevery],
                mode="markers",
                name=signal_name,
                legendgroup=signal_name,
                showlegend=False,  # avoid a duplicate legend entry for the same signal
                opacity=opacity,
                marker=dict(symbol=marker_symbol, size=markersize, color=color),
            )
        )
 
    return traces
 
 
fig = go.Figure()
for signal_name, (x, y) in signal_data.items():
    for trace in plot_style(signal_name, x, y):
        fig.add_trace(trace)
 
fig.update_layout(
    title=event_path,
    xaxis_title="Time (s)",
    yaxis_title="Amplitude",
    template="plotly_white",
    width=700,
    height=400,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    dragmode="select",
)
 
 
def extract_box_range(box_item):
    if "x0" in box_item and "x1" in box_item:
        return sorted([box_item["x0"], box_item["x1"]]), sorted([box_item["y0"], box_item["y1"]])
    if "range" in box_item:
        r = box_item["range"]
        return sorted(r["x"]), sorted(r["y"])
    if "x" in box_item and "y" in box_item:
        return sorted(box_item["x"]), sorted(box_item["y"])
    return None, None
 
 
st.caption("Drag a box on the plot to preview a zoomed-in view in the magnifier panel on the right.")
 
col_main, col_zoom = st.columns([2, 1])
 
with col_main:
    select_event = st.plotly_chart(
        fig,
        use_container_width=False,
        on_select="rerun",
        selection_mode=("box",),
        key=f"main_chart_{event_path}",
    )
 
with col_zoom:
    st.caption("🔍 Magnifier preview")
 
    box_list = select_event.selection.get("box", []) if select_event else []
    x_range, y_range = (None, None)
    if box_list:
        x_range, y_range = extract_box_range(box_list[0])
 
    if x_range and y_range:
        zoom_fig = go.Figure(fig)  # independent copy - editing this never touches the main plot
        zoom_fig.update_layout(
            xaxis=dict(range=x_range, title=None),
            yaxis=dict(range=y_range, title=None),
            margin=dict(l=10, r=10, t=10, b=10),
            width=260,
            height=300,
            showlegend=False,
            title=None,
            dragmode=False,
        )
        st.plotly_chart(
            zoom_fig,
            use_container_width=False,
            config={"staticPlot": True},  # preview only, not independently interactive
            key=f"zoom_chart_{event_path}",
        )
    else:
        st.info("No selection yet. Drag a box on the plot to preview it here.")




# plot every attribute with the correspoding time 
#for signal_name, (x, y) in signal_data.items():
   # ax.plot(x, y, label=signal_name, **STYLES.get(signal_name,{}))


#ax.set_title(event_path) # Titlke of the plot 
#ax.set_xlabel("Time (s)") # x-axis
#ax.set_ylabel("Amplitude") # y-axis 
#ax.legend() #legend for the plot 
#ax.grid(alpha=0.3) #grid on
#st.pyplot(fig, use_container_width=False)  #dispaly in the streamlit app 



# Labeling the waveform 
st.subheader("Label this waveform")
existing_note = current_status["note"] if current_status["note"] else ""
SRF_note = st.text_area(
    "Add a note (optional), If you decide to leave it blank, a generated note will be used.", 
    value="", 
    key=f"note_{event_path}") #textbox to insert a note 

# A checkbox for whether there is a need for a specialist to check the cvaity in person 
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
    # Throw an exception if anything wrong happens 
    except Exception as e:
        st.error(f"Could not write label to file: {e}") 

 