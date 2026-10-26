"""SwiGLU feed-forward (Part A §10, §12a box ⑦)."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def silu(x: NDArray[np.float64]) -> NDArray[np.float64]:
    """SiLU / Swish: x * sigmoid(x)."""
    return x * (1.0 / (1.0 + np.exp(-x)))


def swiglu_ffn(
    h: NDArray[np.float64],
    w_gate: NDArray[np.float64],
    w_up: NDArray[np.float64],
    w_down: NDArray[np.float64],
) -> NDArray[np.float64]:
    """
    Per-position FFN (no cross-token mixing).

    h: (seq_len, d_model)
    w_gate, w_up: (d_model, d_ff)
    w_down: (d_ff, d_model)
    """
    gate = h @ w_gate
    up = h @ w_up
    hidden = silu(gate) * up
    return hidden @ w_down
