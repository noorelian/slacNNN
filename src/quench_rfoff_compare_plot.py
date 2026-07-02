import matplotlib.pyplot as plt
from srf_waveforms import *

false_quenchfile = (
    "ACCL_L3B_3180_20221108_212822_QUENCH.txt"  # file with false quench waveform data
)
false_quenchdata = load_fault_file(false_quenchfile)

# real_quenchfile = 'ACCL_L3B_3180_20221009_112338_QUENCH.txt'    # file with real quench waveform data
# real_quenchdata = load_faults(real_quenchfile)
false_wf = grab_waveforms(false_quenchdata)
# real_wf = grab_waveforms(real_quenchdata)
# print(false_wf)

# plot setup
# Define line styles for keys
line_styles = {
    "fault_waveform": {"color": "indigo", "linestyle": "-", "linewidth": 3},
    "forward_power": {"color": "green", "marker": "o"},
    "reverse_power": {"color": "orange", "marker": "x"},
    "decay_reference": {"color": "darkcyan", "linestyle": "--", "linewidth": 3},
}


def plot_all_waveforms(wf):
    plt.figure(figsize=(14, 6))
    for key, data in wf.items():
        # Plot all four waveforms
        style = line_styles.get(key, {})
        plt.plot(data, label=key, **style)
    plt.show()


def plot_quench_waveforms(wf):
    trimmed = trim_waveform_dict(wf, derv_threshold=0.000005)
    # Plot quench waveform and decay reference only
    if "fault_waveform" in trimmed:
        style = line_styles.get("fault_waveform", {})
        plt.plot(
            trimmed["fault_time"],
            trimmed["fault_waveform"],
            label="Cavity quench waveform",
            **style,
        )
    if "decay_reference" in trimmed:
        style = line_styles.get("decay_reference", {})
        plt.plot(
            trimmed["fault_time"],
            trimmed["decay_reference"],
            label="Reference decay waveform",
            **style,
        )
        # Shade under the normal decay waveform in light blue
        # plt.fill_between(trimmed['fault_time'], trimmed['decay_reference'], color='lightblue', alpha=0.5, zorder=0)
    return


def set_plot_labels(wf, timestamp=False):
    cmcav = convert_cavity_pv_name(wf["cavity"])
    if timestamp:
        plt.title(f"{cmcav}\nTimestamp {wf['timestamp']}")
    else:
        plt.title(f"{cmcav}", size=16)
    plt.xlabel("Time (s)", size=14)
    plt.ylabel("Amplitude (MV)", size=14)
    plt.tight_layout()
    plt.legend(fontsize=12)
    plt.xlim(-0.02, 0.06)
    # plt.show()


plt.figure(figsize=(6.5, 4))
plt.tick_params(axis="both", which="major", labelsize=14)
# Call the plotting functions
plot_quench_waveforms(false_wf)
# plot_quench_waveforms(real_wf)
set_plot_labels(false_wf)
plt.savefig("quench_rfoff_compare_plot.png", dpi=300)
