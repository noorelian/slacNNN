import os
import h5py
import numpy as np
import streamlit as st
import plotly.graph_objects as go

from constants import SIGNAL_TIME_MAP, FREQUENCY_KEYS, SAVED_Q_LOADED_KEYS

from data import (
    get_scalar,
    suggest_classification,
    find_event_groups,
    write_label,
    parse_event_path,
    list_cryomodules,
    list_cavities,
    list_years,
)

from plotting import build_figure, extract_box_range


st.set_page_config(page_title="Quench Labeler", layout="wide")
st.title("Plot a Waveform/Quench")

# A helper function that is responsible for the status of the file in the dropdown
def checked_status(event_path, event_status):
    """Format an event's dropdown label: name | checked | label."""
    status = event_status[event_path]
    event_name = parse_event_path(event_path)
    if status["checked"]:
        return f"{event_name}   |   Checked: Yes    |   Label: {status['label'].upper()}"
    return f"{event_name}   |   Checked: No |   Label: unlabeled"


# A function to format the event status(checked or unchecked), label(Real or False or Other) and note
def format_event_status(event_path, status):
    """Render an event's status as a markdown table."""
    checked = "Yes" if status["checked"] else "No"
    label = status["label"].upper() if status["label"] else "Unlabeled"
    note = status["note"] if status["note"] else "None"
    when = status["checked_at"] if status["checked_at"] else ""
    flag = "Yes" if status["needs_specialist"] else "No"

    display_name = parse_event_path(event_path).replace("|", "\\|")

    return f"""
    | **Event name**                        | {display_name}                      |
    |---------------------------------------|-------------------------------------|
    | **Checked**                           | {checked}                           |
    | **Label**                             | {label}                             |
    | **Note**                              | {note}                              |
    | **Need a specialist to inspect the cavity** | {flag}                        |
    | **Last updated**                      | {when}                              |
    """

@st.cache_data(show_spinner=False)
def cached_cryomodules(path, mtime):
    with h5py.File(path, "r") as f:
        return list_cryomodules(f)
 
 
@st.cache_data(show_spinner=False)
def cached_cavities(path, mtime, cm):
    with h5py.File(path, "r") as f:
        return list_cavities(f, cm)
 
 
@st.cache_data(show_spinner=False)
def cached_years(path, mtime, cm, cav):
    with h5py.File(path, "r") as f:
        return list_years(f, cm, cav)
 
 
@st.cache_data(show_spinner=False)
def cached_events(path, mtime, cm, cav, year):
    with h5py.File(path, "r") as f:
        events = find_event_groups(f, cm=cm, cav=cav, year=year)
        event_status = {}
        for event in events:
            attrs = f[event].attrs
            event_status[event] = {
                "checked": bool(attrs.get("checked", False)),
                "label": attrs.get("quench_labels", None),
                "note": attrs.get("note", None),
                "checked_at": attrs.get("checked_at", None),
                "needs_specialist": bool(attrs.get("needs_specialist", False)),
            }
    return events, event_status

# ** File Selection **
selected_path = st.text_input("Enter the full HDF5 File Path", value="")    # Getting the HDF5 file path from the user 

# if nothing was entered, it will reask you to enter a path 
if not selected_path:
    st.info("Enter the full path to a HDF5 file above.")
    st.stop()

# if entered something else otherthan a file path, it will give you an error message 
if not os.path.isfile(selected_path):
    st.error(f"File not found: {selected_path}")
    st.stop()

file_mtime = os.path.getmtime(selected_path)

try:
    cm_options = ["All"] + cached_cryomodules(selected_path, file_mtime)
except Exception as e:
    st.error(f"Could not open the file: {e}")
    st.stop()

filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

with filter_col1:
    selected_cm = st.selectbox("Cryomodule", cm_options, key="filter_cm")

cav_options =["All"]

if selected_cm != "All":
    cav_options += cached_cavities(selected_path, file_mtime, selected_cm)

with filter_col2:
    selected_cav = st.selectbox("Cavity", cav_options, key="filter_cav", disabled=(selected_cm == "All"))

year_options = ["All"]
if selected_cm != "All" and selected_cav != "All":
    year_options += cached_years(selected_path, file_mtime, selected_cm, selected_cav)

with filter_col3:
    selected_year = st.selectbox("Year", year_options, key="filter_year", disabled=(selected_cm == "All" or selected_cav == "All"))

with filter_col4:
    label_options = ["All", "REAL", "FALSE", "OTHER", "Unlabeled"]
    selected_option = st.selectbox("Label", label_options, key="filter_label")

cm_filter = selected_cm if selected_cm != "All" else None
cav_filter = selected_cav if selected_cav != "All" else None
year_filter = selected_year if selected_year != "All" else None

if cm_filter is None:
    st.caption("Narrow down by cryomodule, cavity, year and label for a faster and more focused set of events")

try:
    events, event_status = cached_events(selected_path, file_mtime, cm_filter, cav_filter, year_filter)

except Exception as e:
    st.error(f"Could not read events from the h5 file: {e}")
    st.stop()

if not events:
    st.warning("No recognizable quench events found")
    st.stop()

def event_matches_label(event_path, target_label):
    if target_label == "All":
        return True
    
    status = event_status[event_path]
    label = status["label"]

    if isinstance(label, bytes):
        label = label.decode()
    if label:
        label = str(label).strip()

    if target_label == "Unlabeled":
        return(not status["checked"]) or (not label)
    
    return label == target_label

if selected_option != "All":
    events = [e for e in events if event_matches_label(e, selected_option)]

    if not events:
        st.warning("No events found with this label")
        st.stop()


# ** Event selection **

if "selected_event" in st.session_state and st.session_state["selected_event"] in events:
    default_index = events.index(st.session_state["selected_event"])
else:
    default_index = 0

event_path = st.selectbox(
    f"Select event ({len(events)} found)",
    events,
    index=default_index,
    format_func=lambda p: checked_status(p, event_status),
    key="event_selectbox_{st.session_state['data_version']}",
)
st.session_state["selected_event"] = event_path

current_status = event_status[event_path]

st.markdown(format_event_status(event_path, current_status), unsafe_allow_html=True)

if current_status["needs_specialist"]:
    st.warning("A specialist needs to inspect the cavity")


# ** Load waveform data for the selected event **
with h5py.File(selected_path, "r") as f:
    group = f[event_path]
    signal_data = {}

    for signal_name, time_name in SIGNAL_TIME_MAP.items():
        if signal_name not in group:  # if an event is missing some signals like the very first ones in 2022 (they are missing the decay reference), skip the missing items 
            continue

        y = np.array(group[signal_name])    # load the signals into array 
        x = None

        if time_name in group:
            t = np.array(group[time_name])  # load time data into array 
            # only assign t to x if its shape matches that of y 
            if t.shape[0] == y.shape[0]:
                x = t

        if x is None:
            x = np.arange(y.shape[0])   # if no time is available, create an x-axis starts from 0 to the length of y 

        signal_data[signal_name] = (x, y)   # store the loaded signal data 

    frequency = get_scalar(group, FREQUENCY_KEYS)   #read cavity frequency 
    saved_q_loaded = get_scalar(group, SAVED_Q_LOADED_KEYS) #read the saved loaded Q


# ** Classification suggestion **

suggestion = None
if "fault_waveform" in signal_data and frequency is not None and saved_q_loaded is not None:
    x_fault, y_fault = signal_data["fault_waveform"]    # get the fault waveform time and amplitude 
    try:
        suggestion = suggest_classification(x_fault, y_fault, frequency, saved_q_loaded)
    except Exception as e:
        suggestion = {"is_real": None, "loaded_q": np.nan, "other_issue": f"error: {e}"}


# ** Plot + magnifier **

fig = build_figure(signal_data, title=parse_event_path(event_path))

st.caption("Drag a box on the plot to preview a zoomed-in view on the right side of the screen")

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
        zoom_fig = go.Figure(fig)
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
            config={"staticPlot": True},
            key=f"zoom_chart_{event_path}",
        )
    else:
        st.info("No selection yet. Drag a box on the plot to preview it here")


# ** Labeling the waveform **

st.subheader("Label this waveform")

# Printing the classification 
if suggestion is not None:  # if the classification was computed
    if suggestion["other_issue"] is not None and suggestion["is_real"] is None: #if failed, display a warning message 
        st.error(f"Could not provide a suggested classification ({suggestion['other_issue']})")
    else:
        suggested_label = "REAL" if suggestion["is_real"] else "FALSE"
        q_text = f"{suggestion['loaded_q']:.3e}" if np.isfinite(suggestion["loaded_q"]) else "N/A"
        st.info(
            f"The system suggests that the given waveform is **{suggested_label}** "
            f"and the estimated loaded Q = {q_text}"
        )
else:
    st.info("Data is unavailable")  # if classificatin couldn't get computed

existing_note = current_status["note"] if current_status["note"] else ""
SRF_note = st.text_area(
    "Add a note (optional), If you decide to leave it blank, a generated note will be used.",
    value="",
    key=f"note_{event_path}",
)

# A checkbox if there is a need for a specialist to check the cvaity in person 
needs_specialist = st.checkbox(
    "Needs specialist to inpect the cavity in person",
    value=current_status["needs_specialist"],
    key=f"specilist_{event_path}",
)

# 3 colums fo the 3 options (real, false , other)
col1, col2, col3 = st.columns(3)

clicked_option = None

with col1:
    # set clicked_option = real if "REAL" was chosen
    if st.button("REAL", use_container_width=True):
        clicked_option = "real"

with col2:
    # set clicked_option = false if "FALSE" was chosen 
    if st.button("FALSE", use_container_width=True):
        clicked_option = "false"

with col3:
    # set the clicked_option = other if "OTHER" was chosen 
    if st.button("OTHER", use_container_width=True):
        clicked_option = "other"

#with col4:
    # set clicked_option = not_sure if "NOT SURE" was chosen
    #if st.button("NOT SURE", use_container_width=True):
       # clicked_option = "not sure"

# if any option/button was clicked, update the label and the status of the event 
if clicked_option:
    try:
        write_label(selected_path, event_path, clicked_option, SRF_note, needs_specialist)
        st.success(f"Saved: '{event_path}' marked as **{clicked_option.upper()}** and checked.") 
        cached_events.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Could not write label to file: {e}")