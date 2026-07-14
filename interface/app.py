import streamlit as st # used for the web interface (to run it locally)
import numpy as np
import os

from interface.data import load_status, load_signals, write_label
from interface.classification import suggest_classification
from interface.text_format import parse_event_path, checked_status, format_event_status
from interface.plotting import build_figure, zoomed_figure, extract_box_range

st.set_page_config(page_title="Quench Labeler", layout="wide") #configure the streamlit website 
st.title("Plot a Waveform/Quench ")

def get_file_path():
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

def select_event(events, event_status):
    index = 0
    if st.session_state.get("selected_event") in events:
        index = events.index(st.session_state["selected_event"])
    
    event = st.selectbox(
        f"Select event ({len(events)} found)", 
        events, index=index, 
        format_func=checked_status, 
        key="event_selectbox"
    ) # Allowing the user to choose the event from the dropdown

    st.session_state["selected_event"] = event
    return event

def magnifier_preview(fig, event_path):
    st.caption("Drag a box on the plot to preview a zoomed-in view on the right side of the screen")
 
    col_main, col_zoom = st.columns([2, 1])
 
    with col_main:
        selection = st.plotly_chart(
            fig,
            use_container_width=False,
            on_select="rerun",
            selection_mode=("box",),
            key=f"main_chart_{event_path}",
    )
 
    with col_zoom:
        st.caption("🔍 Magnifier preview")
 
        boxes = select_event.selection.get("box", []) if select_event else []
        x_range, y_range = extract_box_range(boxes[0]) if boxes else (None, None)
 
        if x_range and y_range:
            st.plotly_chart(
                zoomed_figure(fig, x_range, y_range),
                use_container_width=False,
                config={"staticPlot": True},  
                key=f"zoom_chart_{event_path}",
        )
        else:
            st.info("No selection yet. Drag a box on the plot to preview it here")

def classifiction_suggestion(suggestion):
    if suggestion is not None: 
         st.info("Data is unavailable") # if the classification wasn't computed 
         return
    if suggestion["other_issue"] and suggestion["is_real"] is None: #if failed, print a warning message 
        st.warning(f"Could not provide a suggested classification ({suggestion['other_issue']})")
        return

 
    suggested_label = "REAL" if suggestion["is_real"] else "FALSE" # We are still not considering the other option (it is either real or false) - Talk to Nicole about this 
    q_text = f"{suggestion['loaded_q']:.3e}" if np.isfinite(suggestion["loaded_q"]) else "N/A" #Format the loaded Q 
    st.info(f"The system suggests that the given waveform is **{suggested_label}** and the estimated loaded Q = {q_text}") # Suggestion message 


def labeling(selected_path, event_path, current_status):

    # Labeling the waveform 
    st.subheader("Label this waveform")

    SRF_note = st.text_area(
        "Add a note (optional), If you decide to leave it blank, a generated note will be used.", 
        value="", 
        key=f"note_{event_path}") #textbox to insert a note 

    # A checkbox for whether there is a need for a specialist to check the cvaity in person 
    needs_specialist = st.checkbox(
        "Needs specialist to inpect the cavity in person", value =current_status["needs_specialist"], key=f"specilist_{event_path}"
    )

    # 3 colums fo the 3 options (real, false , other)
    cols = st.columns(3)

 
    clicked_option = None # a variable that records which button was chosen 

    for col, opt in zip(cols, ["real", "false", "other"]):
        with col:
            if st.button(opt.upper(), use_container_width=True):
                clicked_option = opt
    # if any option/button was clicked, update the label and the status of the event 
    if clicked_option:
        try:
            write_label(selected_path, event_path, clicked_option, SRF_note, needs_specialist) # write the label and notes to the hdf5 file 
            st.rerun()      # Keep the update in the records 
    # Throw an exception if anything wrong happens 
        except Exception as e:
            st.error(f"Could not write label to file: {e}")

def main():
    selected_path = get_file_path()
    try:
        events, statuses = load_status(selected_path)
    except Exception as e:
        st.error(f"Could not open file as HDF5: {e}")
        st.stop()

    if not events:
        st.warning("No recognizable quench events found in this file.")
        st.stop()

    event_path = select_event(events, statuses)
    status = statuses[event_path]

    st.markdown(format_event_status(event_path, status), unsafe_allow_html=True)
    if status["needs_specialist"]:
        st.warning("A specialist needs to inspect the cavity")

    signal_data, frequency, saved_q = load_signals(selected_path, event_path)

    suggestion = None
    if "fault_waveform" in signal_data and frequency is not None and saved_q is not None:
        x, y = signal_data["fault_waveform"]
        try:
            suggestion = suggest_classification(x, y, frequency, saved_q)
        except Exception as e:
            suggestion = {"is_real": None, "loaded_q": np.nan, "other_issue": f"error: {e}"}

    fig = build_figure(signal_data, parse_event_path(event_path))
    magnifier_preview(fig, event_path)

    classifiction_suggestion(suggestion)
    labeling(selected_path, event_path, status)


if __name__ == "__main__":
    main()

 



