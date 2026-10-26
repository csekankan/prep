"""
Inverted File (IVF) index — Strategy 1 from 06-vector-search.md.

Train: k-means → assign each vector to nearest centroid.
Query: probe nprobe closest centroids, search only those buckets.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from vector_retrieval_lab.brute_force import top_k_brute


@dataclass
class IVFIndex:
    nlist: int = 8
    nprobe: int = 2
    centroids: NDArray[np.float64] | None = None
    buckets: list[list[int]] = field(default_factory=list)

    def train(self, matrix: NDArray[np.float64], rng_seed: int = 0) -> None:
        """Lloyd k-means (few iterations — teaching only)."""
        rng = np.random.default_rng(rng_seed)
        n, d = matrix.shape
        # k-means++ style init: random distinct points
        idx = rng.choice(n, size=self.nlist, replace=False)
        centroids = matrix[idx].copy()

        for _ in range(15):
            labels = self._assign(matrix, centroids)
            for c in range(self.nlist):
                members = matrix[labels == c]
                if len(members):
                    centroids[c] = members.mean(axis=0)

        self.centroids = centroids
        labels = self._assign(matrix, centroids)
        self.buckets = [[] for _ in range(self.nlist)]
        for i, lab in enumerate(labels):
            self.buckets[int(lab)].append(i)

    def _assign(self, matrix: NDArray[np.float64], centroids: NDArray[np.float64]) -> NDArray[np.int64]:
        # (N, C) squared distances via expansion
        x2 = (matrix**2).sum(axis=1, keepdims=True)
        c2 = (centroids**2).sum(axis=1)
        dist = x2 + c2 - 2 * matrix @ centroids.T
        return np.argmin(dist, axis=1)

    def search(self, query: NDArray[np.float64], matrix: NDArray[np.float64], k: int) -> list[int]:
        if self.centroids is None:
            raise RuntimeError("call train() first")
        # Which clusters does the query land near?
        q = query.reshape(1, -1)
        dist = ((q - self.centroids) ** 2).sum(axis=1)
        probe_ids = np.argsort(dist)[: self.nprobe]
        candidates: list[int] = []
        for cid in probe_ids:
            candidates.extend(self.buckets[int(cid)])
        if not candidates:
            return top_k_brute(query, matrix, k)
        sub = matrix[candidates]
        local_top = top_k_brute(query, sub, min(k, len(candidates)))
        return [candidates[i] for i in local_top]
