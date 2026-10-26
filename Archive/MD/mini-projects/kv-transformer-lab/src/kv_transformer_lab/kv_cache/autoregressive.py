"""
Autoregressive decode: naive recompute vs KV cache (Part A §13.1).

We count abstract "layer forward passes" instead of FLOPs so the O(T²) vs O(T)
story is obvious without a GPU.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from kv_transformer_lab.decoder.decoder_layer import DecoderLayerOutput, DecoderLayerWeights, decoder_layer_forward
from kv_transformer_lab.kv_cache.cache import LayerKVCache


@dataclass
class WorkCounter:
    """Instrumentation for teaching — not a real profiler."""

    layer_forwards: int = 0
    tokens_processed: int = 0

    def bump_layer(self, n_tokens: int) -> None:
        self.layer_forwards += 1
        self.tokens_processed += n_tokens


def naive_decode_step(
    h_prefix: NDArray[np.float64],
    h_new_token: NDArray[np.float64],
    weights: DecoderLayerWeights,
    num_heads: int,
    counter: WorkCounter,
) -> DecoderLayerOutput:
    """
    Without KV cache: re-run the layer on the *entire* sequence every new token.

    h_prefix: (t, d_model) — all tokens so far excluding the new one
    h_new_token: (1, d_model)
    """
    h_full = np.concatenate([h_prefix, h_new_token], axis=0)
    counter.bump_layer(h_full.shape[0])
    return decoder_layer_forward(h_full, weights, num_heads)


def cached_decode_step(
    h_new_token: NDArray[np.float64],
    weights: DecoderLayerWeights,
    num_heads: int,
    cache: LayerKVCache,
    counter: WorkCounter,
) -> DecoderLayerOutput:
    """
    With KV cache: forward only the *new* token's hidden state, attend using cached K,V.

    Real engines fuse attention kernels; we simulate by:
      1) running decoder_layer on length-1 h (cheap)
      2) appending new K,V to cache
    """
    counter.bump_layer(1)
    out = decoder_layer_forward(h_new_token, weights, num_heads)
    cache.append(out.k, out.v)
    return out


def simulate_generation(
    embeddings: NDArray[np.float64],
    weights: DecoderLayerWeights,
    num_heads: int,
    *,
    use_kv_cache: bool,
) -> WorkCounter:
    """
    Generate token-by-token over a sequence of precomputed embeddings.

    embeddings: (total_len, d_model) — stand-in for "prompt + completions"
    We treat position 0 as prefill (all tokens at once) then decode 1..T-1.
    """
    counter = WorkCounter()
    d_model = embeddings.shape[1]
    assert d_model == weights.w_q.shape[0]

    # Prefill: process full prompt in one shot (Part C §16 step 2)
    prompt_len = max(2, embeddings.shape[0] // 2)
    h_prompt = embeddings[:prompt_len]
    counter.bump_layer(h_prompt.shape[0])
    prefill_out = decoder_layer_forward(h_prompt, weights, num_heads)

    cache = LayerKVCache()
    cache.append(prefill_out.k, prefill_out.v)

    for t in range(prompt_len, embeddings.shape[0]):
        h_t = embeddings[t : t + 1]
        if use_kv_cache:
            cached_decode_step(h_t, weights, num_heads, cache, counter)
        else:
            h_prefix = embeddings[:t]
            naive_decode_step(h_prefix, h_t, weights, num_heads, counter)

    return counter


def multi_layer_kv_bytes(
    num_layers: int,
    seq_len: int,
    num_kv_heads: int,
    head_dim: int,
    bytes_per_element: int = 2,
) -> int:
    """
    Part C §17 formula:
      KV_bytes ≈ 2 × layers × kv_heads × head_dim × bytes × seq_len
    """
    per_token = 2 * num_layers * num_kv_heads * head_dim * bytes_per_element
    return per_token * seq_len
