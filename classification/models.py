from enum import Enum
from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray
from typing import Optional


@dataclass
class QuenchData:
    fault_time: NDArray[np.float64]
    fault_waveform: NDArray[np.float64]
    forward_power: NDArray[np.float64]
    forward_time: NDArray[np.float64]
    reverse_power: NDArray[np.float64]
    reverse_time: NDArray[np.float64]
    decay_reference: Optional[NDArray[np.float64]] = None


class QuenchStatus(Enum):
    real = "real"
    false = "false"
    other = "other"
    cavity_off = "cavity_off"
