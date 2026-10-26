"""
Masked multi-head self-attention (Part A §8–9).

This is the *math* inside every decoder layer—not a full model. We use tiny
dimensions so you can print every matrix and sanity-check shapes.

Library analogy from the doc:
  - Query  = your search question
  - Key    = spine label on each book
  - Value  = book contents you blend after matching
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def softmax(x: NDArray[np.float64], axis: int = -1) -> NDArray[np.float64]:
    """Numerically stable softmax (subtract max before exp)."""
    shifted = x - np.max(x, axis=axis, keepdims=True)
    exp = np.exp(shifted)
    return exp / np.sum(exp, axis=axis, keepdims=True)


def causal_mask(seq_len: int) -> NDArray[np.float64]:
    """
    Upper triangle = -inf so position t cannot attend to t+1, t+2, …

    Shape: (seq_len, seq_len)
    """
    mask = np.triu(np.ones((seq_len, seq_len), dtype=np.float64), k=1)
    return np.where(mask > 0, -np.inf, 0.0)


def scaled_dot_product_attention(
    q: NDArray[np.float64],
    k: NDArray[np.float64],
    v: NDArray[np.float64],
    *,
    mask: NDArray[np.float64] | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """
    Single attention head.

    Args:
        q, k, v: (seq_len, d_head)
        mask: optional (seq_len, seq_len) added to scores before softmax

    Returns:
        output: (seq_len, d_head)
        weights: (seq_len, seq_len) — rows sum to 1
    """
    d_head = q.shape[-1]
    # Scores[t, s] = how much position t wants to read position s
    scores = (q @ k.T) / np.sqrt(d_head)
    if mask is not None:
        scores = scores + mask
    weights = softmax(scores, axis=-1)
    output = weights @ v
    return output, weights


def project_hidden(
    h: NDArray[np.float64],
    w_q: NDArray[np.float64],
    w_k: NDArray[np.float64],
    w_v: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """
    h @ W_* — these W matrices are *model weights* (fixed at inference).

    h: (seq_len, d_model)
    W_*: (d_model, d_model) for simplicity (real models often use d_model → n_heads*d_head)
    """
    q = h @ w_q
    k = h @ w_k
    v = h @ w_v
    return q, k, v


def multi_head_attention(
    h: NDArray[np.float64],
    w_q: NDArray[np.float64],
    w_k: NDArray[np.float64],
    w_v: NDArray[np.float64],
    w_o: NDArray[np.float64],
    num_heads: int,
    causal: bool = True,
) -> tuple[NDArray[np.float64], list[NDArray[np.float64]]]:
    """
    Full multi-head block: split → attend per head → concat → output projection.

    Returns:
        attn_out: (seq_len, d_model)
        per_head_weights: list of (seq_len, seq_len) for visualization
    """
    seq_len, d_model = h.shape
    if d_model % num_heads != 0:
        raise ValueError("d_model must be divisible by num_heads")
    d_head = d_model // num_heads

    q, k, v = project_hidden(h, w_q, w_k, w_v)
    mask = causal_mask(seq_len) if causal else None

    head_outputs: list[NDArray[np.float64]] = []
    head_weights: list[NDArray[np.float64]] = []

    for head in range(num_heads):
        sl = slice(head * d_head, (head + 1) * d_head)
        out, w = scaled_dot_product_attention(q[:, sl], k[:, sl], v[:, sl], mask=mask)
        head_outputs.append(out)
        head_weights.append(w)

    # Concatenate heads along feature dimension, then mix with W_o
    concat = np.concatenate(head_outputs, axis=-1)
    attn_out = concat @ w_o
    return attn_out, head_weights


def init_attention_weights(
    d_model: int, seed: int = 0
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Small random weights for demos (not trained)."""
    rng = np.random.default_rng(seed)
    scale = 0.02
    w_q = rng.normal(0, scale, (d_model, d_model))
    w_k = rng.normal(0, scale, (d_model, d_model))
    w_v = rng.normal(0, scale, (d_model, d_model))
    w_o = rng.normal(0, scale, (d_model, d_model))
    return w_q, w_k, w_v, w_o
