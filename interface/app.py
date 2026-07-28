import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import h5py
import numpy as np

import streamlit as st
import plotly.graph_objects as go
import streamlit as st

from h5_reader import (
    get_scalar,
    #suggest_classification,
    write_label,
    #parse_event_path,
    find_event_groups,
)

from utils.quench_data_summary import list_cryomodules, list_cavities, list_years
from plotting import build_figure, extract_box_range
from quench_config import SIGNAL_TIME_MAP, LABEL_OPTIONS, LABEL_BUTTONS, LABEL_DISPLAY_TO_STORED, FREQUENCY_KEYS, SAVED_Q_LOADED_KEYS
# from utils.srf_waveforms import calculate_loaded_q, validate_quench_lisa
from utils.srf_waveforms import convert_pv_name_plot_string
from classification.logic import classify, QuenchStatus, QuenchData



def to_string(value):
    """ Decode byte attributes to string."""
    return value.decode() if isinstance(value, bytes) else value 


def normalize_label(label):
    """Normalize any label to a canonical form so case, spaces, and
    underscores never matter. 'NOT SURE', 'not_sure', 'Not Sure' all match."""
    label = to_string(label)

    if not label:
        return ""          
    return str(label).strip().lower().replace(" ", "_")

def display_label(status, unlabeled="Unlabeled"):
    """Uppercased, human readable label, or unlabeled if nothing is set."""
    label =normalize_label(status["label"])
    return label.upper() if label else unlabeled 


# A helper function that is responsible for the status of the file in the dropdown
def checked_status(event_path, event_status):
    """Format an event's dropdown label: name | checked | label."""
    status = event_status[event_path]
    event_name = convert_pv_name_plot_string(event_path)
    if status["checked"]:
        label = normalize_label(status["label"])
        label = label.upper() if label else "UNLABELED"
        return f"{event_name}   |   Checked: Yes    |   Label: {label}"
    return f"{event_name}   |   Checked: No |   Label: unlabeled"


def build_summary_table(display_name, checked, label, note, flag, when):
    """Build a markdown table for each event."""
    return f"""
    | **Event name**                        | {display_name}                      |
    |---------------------------------------|-------------------------------------|
    | **Checked**                           | {checked}                           |
    | **Label**                             | {label}                             |
    | **Note**                              | {note}                              |
    | **Need a specialist to inspect the cavity** | {flag}                        |
    | **Last updated**                      | {when}                              |
    """

# A function to format the event status(checked or unchecked), label(Real or False or Other) and note
def format_event_status(event_path, status):
    """Render an event's status as a markdown table."""
    checked = "Yes" if status["checked"] else "No"
    label = normalize_label(status["label"])
    label = label.upper() if label else "Unlabeled"

    note = status["note"] 
    if isinstance(note, bytes):
        note = note.decode()
    note = note if note else "None"
    when = status["checked_at"] if status["checked_at"] else ""
    if isinstance(when, bytes):
        when = when.decode()

    flag = "Yes" if status["needs_specialist"] else "No"

    display_name = convert_pv_name_plot_string(event_path).replace("|", "\\|")

    return build_summary_table(display_name, checked, label, note, flag, when)

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
def get_file_path():
    """Ask for the h5 file path and validate it."""
    selected_path = st.text_input("Enter the full HDF5 File Path", value="")    # Getting the HDF5 file path from the user 

    # if nothing was entered, it will reask you to enter a path 
    if not selected_path:
        st.info("Enter the full path to a HDF5 file above.")
        st.stop()

    # if entered something else otherthan a file path, it will give you an error message 
    if not os.path.isfile(selected_path):
        st.error(f"File not found: {selected_path}")
        st.stop()
    return selected_path


def render_filters(selected_path, file_mtime):
    """Render the CM/CAV/year/label filters."""
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
        selected_option = st.selectbox("Label", LABEL_OPTIONS, key="filter_label")

    cm_filter = selected_cm if selected_cm != "All" else None
    cav_filter = selected_cav if selected_cav != "All" else None
    year_filter = selected_year if selected_year != "All" else None

    if cm_filter is None:
        st.caption("Narrow down by cryomodule, cavity, year and label for a faster and more focused set of events")
    
    return cm_filter, cav_filter, year_filter, selected_option


def get_events(selected_path, file_mtime, cm_filter, cav_filter, year_filter):
    """Load events for the chosen filters."""
    try:
        events, event_status = cached_events(selected_path, file_mtime, cm_filter, cav_filter, year_filter)

    except Exception as e:
        st.error(f"Could not read events from the h5 file: {e}")
        st.stop()

    if not events:
        st.warning("No recognizable quench events found")
        st.stop()

    return events, event_status


def event_matches_label(event_path, event_status, target_label):
    """This function is used for the label filter"""
    if target_label == "All":
        return True
    
    status = event_status[event_path]
    label = normalize_label(status["label"])

    if target_label == "Unlabeled":
        return(not status["checked"]) or (not label)
    
    target = LABEL_DISPLAY_TO_STORED.get(target_label.upper(), target_label)
    target = normalize_label(target)
    
    return label == target

def filter_events_by_label(events, event_status, label):
    """This function is used to filter events by label"""
    if label == "All":
        return events
    
    filtered =[e for e in events if event_matches_label(e, event_status, label)]

    if not filtered:
        st.warning("No events found with this label")
        st.stop()
    return filtered 

# ** Event selection **
def select_waveform_event(events, event_status, filter_key):
    """Select events from the dropdown."""
    if ("selected_event" in st.session_state and st.session_state["selected_event"] in events):
        default_index = events.index(st.session_state["selected_event"])
    else:
        default_index = 0

    event_path = st.selectbox(
        f"Select event ({len(events)} found)",
        events,
        index=default_index,
        format_func=lambda p: checked_status(p, event_status),
        key=f"event_selectbox_{filter_key}",
    )
    st.session_state["selected_event"] = event_path
    return event_path

def show_event_status(event_path, current_status):
    """Show the status tabel and a specilist warning if needed."""

    st.markdown(format_event_status(event_path, current_status), unsafe_allow_html=True)

    if current_status["needs_specialist"]:
        st.warning("A specialist needs to inspect the cavity")


# ** Load waveform data for the selected event **
def load_signal_data(group):
    """Load signals data (decay_ref, fault_waveform, forward_power, reverse_power)."""
    signal_data = {}

    for signal_name, time in SIGNAL_TIME_MAP.items():
        if signal_name not in group:  # if an event is missing some signals like the very first ones in 2022 (they are missing the decay reference), skip the missing items 
            continue

        y = np.array(group[signal_name])    # load the signals into array 
        x = None

        if time in group:
            t = np.array(group[time])  # load time data into array 
            # only assign t to x if its shape matches that of y 
            if t.shape[0] == y.shape[0]:
                x = t

        if x is None:
            x = np.arange(y.shape[0])   # if no time is available, create an x-axis starts from 0 to the length of y 

        signal_data[signal_name] = (x, y)   # store the loaded signal data 

    return signal_data


# ** Classification suggestion **
def load_event_data_for_classification(path, event_path):
    """load frequency and saved_Q for computing the classsification suggestion"""
    with h5py.File(path, "r") as f:
        group = f[event_path]
        signal_data = load_signal_data(group)
        frequency = get_scalar(group, FREQUENCY_KEYS)   #read cavity frequency 
        saved_q_loaded = get_scalar(group, SAVED_Q_LOADED_KEYS) #read the saved loaded Q
    return signal_data, frequency, saved_q_loaded


def compute_suggestion(signal_data, frequency, saved_q_loaded):
    """Compute the classification suggestion using the classify system written by Norah"""

    # If there is no fault_waveform, we are unable to classify 
    if "fault_waveform" not in signal_data:
        return None

    x_fault, y_fault = signal_data["fault_waveform"]    # Split the fault_waveform (time, amplitude) tuple into two separate arrays

    # If the forward_power is missing, we can't run the classifier 
    if "forward_power" not in signal_data:
        return None
    x_fwd, y_fwd = signal_data["forward_power"]     # Split the forward_power (time, amplitude) tuple into two separate arrays

    # reverse_power may or may not exist, if missing assign none to the time and amplitude 
    x_rev, y_rev = signal_data.get("reverse_power", (None, None))

    try:
        # Build the QuenchData object 
        # Convert every array into float for safer math calculations 
        quench_event = QuenchData(
            fault_time=np.asarray(x_fault, dtype=float),    
            fault_waveform=np.asarray(y_fault, dtype=float), 
            forward_power=np.asarray(y_fwd, dtype=float),
            forward_time=np.asarray(x_fwd, dtype=float),
            reverse_power=np.asarray(y_rev, dtype=float) if y_rev is not None else np.array([]), # Reverse power amplitude if available, else an empty array
            reverse_time=np.asarray(x_rev, dtype=float) if x_rev is not None else np.array([]), # Reverse time if available, else an empty array
        )
       
        if frequency is not None:
            # Convert frequency into numpy no matter what type of data it came in 
            quench_event.frequency = float(np.asarray(frequency).flat[0])
        if saved_q_loaded is not None:
            # Convert saved_q_loaded into numpy no matter what type of data it came in 
            quench_event.saved_q_loaded = float(np.asarray(saved_q_loaded).flat[0])

        return classify(quench_event)  # Calls classify function which returns a QuenchStatus [real, false, other or cavoty off]
    except Exception as e :
        st.error(f"Classification suggestion has failed: {e}")
        return None


# ** Plot + magnifier **
def render_plot(signal_data, event_path):
    """Draw the original plot next to a magnifier preview that is used to show the specific part selected to be zoomed into."""

    fig = build_figure(signal_data, title=convert_pv_name_plot_string(event_path))

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
            render_zoom_figure(fig, x_range, y_range, event_path)
        else:
            st.info("No selection yet. Drag a box on the plot to preview it here")

   

def render_zoom_figure(fig, x_range, y_range, event_path):
    """Draw the zommed-in part next to the original plot."""
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


# Printing the classification 
def render_suggestion(suggestion):
    """Show the classification suggestion based on QuenchStatus."""
    if suggestion is None:
        st.info("Data is unavailable")
        return

    if suggestion == QuenchStatus.cavity_off:
        st.info("The system suggests the **cavity was OFF** during this event.")
    elif suggestion == QuenchStatus.real:
        st.info("The system suggests that the given waveform is **REAL**.")
    elif suggestion == QuenchStatus.false:
        st.info("The system suggests that the given waveform is **FALSE**.")
    else:  
        st.info("The system suggests that the given waveform is **OTHER**.")
    

def render_labeling_options(current_status, event_path):
    """
    Show the note field, specialist checkbox and the labeling buttons.
    Returns the clicked label or set as unlabled, the note and the status of the specialist checkbox.
    """

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

    clicked_option = None
    # 3 colums fo the 3 options (real, false , other)
    columns = st.columns(len(LABEL_BUTTONS))

    for col, (display_text, stored_value) in zip (columns, LABEL_BUTTONS):
        with col:
            if st.button(display_text, use_container_width=True):
                clicked_option = stored_value

    return clicked_option, SRF_note, needs_specialist


def save_label(selected_path, event_path, clicked_option, SRF_note, needs_specialist):
    """Save the label back to the h5 file using write_label function."""
    try:
        write_label(selected_path, event_path, clicked_option, SRF_note, needs_specialist)
        st.success(f"Saved: '{event_path}' marked as **{clicked_option.upper()}** and checked.") 
        cached_events.clear() # clear cache so the new label shows up
        st.rerun()
    except Exception as e:
        st.error(f"Could not write label to file: {e}")


def main():
    st.set_page_config(page_title="Quench Labeler", layout="wide")
    st.title("Quench Labeling Interface")

    # ** File Selection **
    selected_path = get_file_path()
    file_mtime = os.path.getmtime(selected_path)

    # ** Filters **
    cm_filter, cav_filter, year_filter, label_option = render_filters(selected_path, file_mtime)

    # ** Load events for the chosen filters **
    events, event_status = get_events(selected_path, file_mtime, cm_filter, cav_filter, year_filter)

    # ** Apply the label filter **
    events = filter_events_by_label(events, event_status, label_option)

    # ** Event selection + status display **
    filter_key = f"{cm_filter}_{cav_filter}_{year_filter}_{label_option}"
    event_path = select_waveform_event(events, event_status, filter_key)
    current_status = event_status[event_path]
    show_event_status(event_path, current_status)

    # ** Compute Classification Suggestion **
    signal_data, frequency, saved_q_loaded, = load_event_data_for_classification(selected_path, event_path)
    suggestion = compute_suggestion(signal_data, frequency, saved_q_loaded)

    # ** Plot + magnifier **
    render_plot(signal_data, event_path)

    # ** Labeling the waveform **
    st.subheader("Label this waveform")
    render_suggestion(suggestion)

    clicked_option, SRF_note, needs_specialist =render_labeling_options(current_status, event_path)

    if clicked_option:
        save_label(
            selected_path, event_path, clicked_option, SRF_note, needs_specialist 
        )

if __name__ == "__main__":
    main()

