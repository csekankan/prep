"""
One decoder layer (Part A §7): Pre-norm → Attention → residual → Pre-norm → FFN → residual.

We return K and V tensors because serving systems *cache those activations* per layer
(see Part B §14)—not the weight matrices W_k, W_v.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from kv_transformer_lab.attention.causal_self_attention import multi_head_attention, project_hidden
from kv_transformer_lab.decoder.rms_norm import rms_norm
from kv_transformer_lab.decoder.swiglu_ffn import swiglu_ffn


@dataclass
class DecoderLayerWeights:
    """All learnable parameters for a single layer (inference: read-only)."""

    gamma_attn: NDArray[np.float64]
    gamma_ffn: NDArray[np.float64]
    w_q: NDArray[np.float64]
    w_k: NDArray[np.float64]
    w_v: NDArray[np.float64]
    w_o: NDArray[np.float64]
    w_gate: NDArray[np.float64]
    w_up: NDArray[np.float64]
    w_down: NDArray[np.float64]


@dataclass
class DecoderLayerOutput:
    h: NDArray[np.float64]
    k: NDArray[np.float64]
    v: NDArray[np.float64]
    attn_weights: list[NDArray[np.float64]]


def decoder_layer_forward(
    h: NDArray[np.float64],
    weights: DecoderLayerWeights,
    num_heads: int,
) -> DecoderLayerOutput:
    """
    Forward one decoder block.

    h: (seq_len, d_model)
    """
    # --- Attention sub-block (communication across positions) ---
    h_norm = rms_norm(h, weights.gamma_attn)
    attn_out, attn_weights = multi_head_attention(
        h_norm,
        weights.w_q,
        weights.w_k,
        weights.w_v,
        weights.w_o,
        num_heads=num_heads,
        causal=True,
    )
    # K,V activations from normalized h — these are what KV cache stores (Part B §14).
    _, k, v = project_hidden(h_norm, weights.w_q, weights.w_k, weights.w_v)

    h = h + attn_out  # residual highway (Part A §11)

    # --- FFN sub-block (thinking within each position) ---
    h_norm2 = rms_norm(h, weights.gamma_ffn)
    ffn_out = swiglu_ffn(h_norm2, weights.w_gate, weights.w_up, weights.w_down)
    h = h + ffn_out

    return DecoderLayerOutput(h=h, k=k, v=v, attn_weights=attn_weights)


def init_decoder_layer_weights(d_model: int, d_ff: int, seed: int = 0) -> DecoderLayerWeights:
    rng = np.random.default_rng(seed)
    s = 0.02
    return DecoderLayerWeights(
        gamma_attn=np.ones(d_model),
        gamma_ffn=np.ones(d_model),
        w_q=rng.normal(0, s, (d_model, d_model)),
        w_k=rng.normal(0, s, (d_model, d_model)),
        w_v=rng.normal(0, s, (d_model, d_model)),
        w_o=rng.normal(0, s, (d_model, d_model)),
        w_gate=rng.normal(0, s, (d_model, d_ff)),
        w_up=rng.normal(0, s, (d_model, d_ff)),
        w_down=rng.normal(0, s, (d_ff, d_model)),
    )
