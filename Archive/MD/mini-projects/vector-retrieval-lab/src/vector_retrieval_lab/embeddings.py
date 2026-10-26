"""
Toy embeddings without calling an API.

Production RAG uses sentence-transformers / OpenAI embeddings. Here we use a
deterministic hashing trick so the lab runs offline and stays reproducible.
"""

from __future__ import annotations

import hashlib

import numpy as np
from numpy.typing import NDArray


def text_to_vector(text: str, dim: int = 64) -> NDArray[np.float64]:
    """
    Map text → unit vector in R^dim via feature hashing.

    Same text always yields the same vector (like a real embedding model).
    """
    vec = np.zeros(dim, dtype=np.float64)
    tokens = text.lower().split()
    for tok in tokens:
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
        vec[idx] += sign
    norm = np.linalg.norm(vec)
    if norm < 1e-9:
        return vec
    return vec / norm


def cosine_similarity(a: NDArray[np.float64], b: NDArray[np.float64]) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
