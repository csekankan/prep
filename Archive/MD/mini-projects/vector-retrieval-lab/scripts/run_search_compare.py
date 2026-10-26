#!/usr/bin/env python3
import time

import numpy as np
from rich.console import Console

from vector_retrieval_lab.brute_force import top_k_brute
from vector_retrieval_lab.embeddings import text_to_vector
from vector_retrieval_lab.ivf_index import IVFIndex

console = Console()

CORPUS = [
    "refund policy within 30 days",
    "how to reset your password",
    "kubernetes pod oom killed troubleshooting",
    "stripe idempotency keys for payments",
    "vector database approximate nearest neighbor",
    "kv cache memory per token fp16",
    "rate limiting token bucket algorithm",
    "consistent hashing for shard placement",
] * 50  # 400 docs


def main() -> None:
    dim = 64
    matrix = np.stack([text_to_vector(t, dim) for t in CORPUS])
    query = text_to_vector("payment retry without double charge")

    t0 = time.perf_counter()
    exact = top_k_brute(query, matrix, k=5)
    t_exact = time.perf_counter() - t0

    ivf = IVFIndex(nlist=16, nprobe=3)
    ivf.train(matrix)
    t0 = time.perf_counter()
    approx = ivf.search(query, matrix, k=5)
    t_ivf = time.perf_counter() - t0

    overlap = len(set(exact) & set(approx))
    console.print(f"Brute top-5 ({t_exact*1000:.2f} ms): {exact[:3]}…")
    console.print(f"IVF top-5  ({t_ivf*1000:.2f} ms): {approx[:3]}…")
    console.print(f"Recall@5 overlap: {overlap}/5")


if __name__ == "__main__":
    main()
