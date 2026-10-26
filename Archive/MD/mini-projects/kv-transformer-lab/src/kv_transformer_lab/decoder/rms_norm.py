"""RMSNorm (Part A §11.2) — pre-norm used in LLaMA-style decoders."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def rms_norm(x: NDArray[np.float64], gamma: NDArray[np.float64], eps: float = 1e-6) -> NDArray[np.float64]:
    """
    RMSNorm(x) = x / sqrt(mean(x²) + ε) * γ

    x: (..., d_model)
    gamma: (d_model,) learnable scale per dimension
    """
    rms = np.sqrt(np.mean(x**2, axis=-1, keepdims=True) + eps)
    return (x / rms) * gamma
