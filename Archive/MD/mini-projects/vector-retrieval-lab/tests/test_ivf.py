import numpy as np

from vector_retrieval_lab.brute_force import top_k_brute
from vector_retrieval_lab.ivf_index import IVFIndex


def test_ivf_recall_reasonable() -> None:
    rng = np.random.default_rng(1)
    matrix = rng.normal(size=(200, 16))
    matrix /= np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-9
    query = matrix[0]
    exact = top_k_brute(query, matrix, 5)
    ivf = IVFIndex(nlist=8, nprobe=4)
    ivf.train(matrix)
    approx = ivf.search(query, matrix, 5)
    assert len(set(exact) & set(approx)) >= 3
