import numpy as np
from .data_loader import QuenchData, QuenchStatus


def find_quench_time(quench_event_data: QuenchData) -> int:
    return int(np.searchsorted(quench_event_data.fault_time, 0.0))


def pre_quench_amplitude(quench_event_data: QuenchData, time_0: int) -> bool:
    pre_quench_window = quench_event_data.fault_waveform[0:time_0]
    is_avg_sufficient = np.mean(pre_quench_window) >= 0.1

    pre_quench_fwd_power = quench_event_data.forward_power[0:time_0]
    is_fwd_power_on = np.mean(pre_quench_fwd_power) > 0.01

    return bool(is_avg_sufficient and is_fwd_power_on)


def is_post_quench_higher(quench_event_data: QuenchData, time_0: int) -> bool:
    pre_quench_mean = np.mean(quench_event_data.fault_waveform[:time_0])
    post_quench_mean = np.mean(quench_event_data.fault_waveform[time_0:])

    return bool(post_quench_mean > pre_quench_mean)


def verify_tau_decay(quench_event_data: QuenchData, time_0: int) -> bool:
    decay_waveform = quench_event_data.fault_waveform[time_0:]
    decay_time = quench_event_data.fault_time[time_0:]

    a0 = decay_waveform[0]
    target_1 = a0 / np.e

    idx_1 = np.searchsorted(-decay_waveform, -target_1)

    if idx_1 >= len(decay_waveform):
        return False

    t1 = decay_time[idx_1] - decay_time[0]

    freq = getattr(quench_event_data, "frequency", 1300000000.0)
    q_loaded = getattr(quench_event_data, "saved_q_loaded", 4e7)

    expected_tau = q_loaded / (np.pi * freq)
    threshold = 0.60 * expected_tau

    return bool(t1 < threshold)


def classify(event_data: QuenchData) -> QuenchStatus:
    time_0 = find_quench_time(event_data)

    if verify_tau_decay(event_data, time_0):
        return QuenchStatus.real

    if not pre_quench_amplitude(event_data, time_0):
        return QuenchStatus.cavity_off

    if is_post_quench_higher(event_data, time_0):
        return QuenchStatus.other

    return QuenchStatus.false
