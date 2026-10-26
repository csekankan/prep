"""
Per-layer K/V cache (Part B §14–15, Part C §18).

In production (vLLM, TensorRT-LLM, etc.) tensors are GPU-resident and paged.
Here we use NumPy arrays and explicit append operations so you can *see* growth.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray


@dataclass
class LayerKVCache:
    """
    Stores K and V for one transformer layer.

    Shapes grow along sequence dimension:
      k, v: (seq_len, d_model) after each append
    """

    k: NDArray[np.float64] | None = None
    v: NDArray[np.float64] | None = None

    def append(self, k_new: NDArray[np.float64], v_new: NDArray[np.float64]) -> None:
        """Append one or more positions (usually 1 during decode)."""
        if k_new.shape != v_new.shape:
            raise ValueError("K and V must have the same shape")
        if self.k is None:
            self.k = k_new
            self.v = v_new
            return
        self.k = np.concatenate([self.k, k_new], axis=0)
        self.v = np.concatenate([self.v, v_new], axis=0)

    @property
    def seq_len(self) -> int:
        return 0 if self.k is None else int(self.k.shape[0])


@dataclass
class KVCache:
    """One cache entry per layer (typical serving layout)."""

    layers: list[LayerKVCache] = field(default_factory=list)

    @classmethod
    def empty(cls, num_layers: int) -> KVCache:
        return cls(layers=[LayerKVCache() for _ in range(num_layers)])

    def nbytes(self) -> int:
        """Rough RAM footprint (both K and V, all layers)."""
        total = 0
        for layer in self.layers:
            if layer.k is not None:
                total += layer.k.nbytes + layer.v.nbytes  # type: ignore[union-attr]
        return total
