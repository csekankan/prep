"""Exact k-NN — O(N) comparisons per query (baseline from vector-search MD)."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def top_k_brute(
    query: NDArray[np.float64],
    matrix: NDArray[np.float64],
    k: int,
) -> list[int]:
    """matrix: (N, D) — return indices of k highest cosine similarities."""
    # Normalize rows for cosine via dot product
    q = query / (np.linalg.norm(query) + 1e-9)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9
    normed = matrix / norms
    scores = normed @ q
    if k >= len(scores):
        return list(np.argsort(-scores))
    idx = np.argpartition(-scores, k)[:k]
    return list(idx[np.argsort(-scores[idx])])
