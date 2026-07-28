import numpy as np
from .data_loader import QuenchData, QuenchStatus


# Locates the array index corresponding to the onset of the quench event at time zero
def find_quench_time(quench_event_data: QuenchData) -> int:
    return int(np.searchsorted(quench_event_data.fault_time, 0.0))


# Verifies that the overall average of the entire fault waveform is greater than 0.1
def is_overall_average_sufficient(quench_event_data: QuenchData) -> bool:
    return bool(np.mean(quench_event_data.fault_waveform) > 0.1)


# Evaluates the pre-quench window to confirm the cavity is actively driven
def pre_quench_amplitude(quench_event_data: QuenchData, time_0: int) -> bool:
    pre_quench_window = quench_event_data.fault_waveform[0:time_0]
    avg_waveform = np.mean(pre_quench_window)

    pre_quench_fwd_power = quench_event_data.forward_power[0:time_0]
    avg_fwd_power = np.mean(pre_quench_fwd_power)

    total_avg = (avg_waveform + avg_fwd_power) / 2.0

    return bool((avg_waveform >= 0.1) and (avg_fwd_power > 0.01) and (total_avg > 0.2))


# Extracts empirical and theoretical decay times to avoid repeating math
def calculate_decay_metrics(
    quench_event_data: QuenchData, time_0: int
) -> tuple[float, float]:
    decay_waveform = quench_event_data.fault_waveform[time_0:]
    decay_time = quench_event_data.fault_time[time_0:]

    if len(decay_waveform) == 0:
        return -1.0, 1.0

    a0 = decay_waveform[0]
    target_1 = a0 / np.e

    idx_1 = np.searchsorted(-decay_waveform, -target_1)

    if idx_1 >= len(decay_waveform):
        return -1.0, 1.0

    t1 = decay_time[idx_1] - decay_time[0]

    freq = getattr(quench_event_data, "frequency", 1300000000.0)
    q_loaded = getattr(quench_event_data, "saved_q_loaded", 4e7)
    expected_tau = q_loaded / (np.pi * freq)

    return float(t1), float(expected_tau)


# Determines the operational status of the quench event
def classify(event_data: QuenchData) -> QuenchStatus:
    if not is_overall_average_sufficient(event_data):
        return QuenchStatus.cavity_off

    time_0 = find_quench_time(event_data)

    if not pre_quench_amplitude(event_data, time_0):
        return QuenchStatus.cavity_off

    t1, expected_tau = calculate_decay_metrics(event_data, time_0)

    if t1 < 0:
        return QuenchStatus.other

    if t1 < 0.60 * expected_tau:
        return QuenchStatus.real

    if t1 >= 0.60 * expected_tau:
        return QuenchStatus.false

    return QuenchStatus.other
