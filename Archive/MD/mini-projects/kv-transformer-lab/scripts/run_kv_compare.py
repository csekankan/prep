#!/usr/bin/env python3
"""Part A §13.1 — layer-forward work: naive decode vs KV cache."""

import numpy as np
from rich.console import Console

from kv_transformer_lab.decoder.decoder_layer import init_decoder_layer_weights
from kv_transformer_lab.kv_cache.autoregressive import simulate_generation

console = Console()


def main() -> None:
    total_len, d_model, heads = 32, 16, 2
    rng = np.random.default_rng(0)
    embeddings = rng.normal(0, 0.05, (total_len, d_model))
    weights = init_decoder_layer_weights(d_model, d_ff=32, seed=2)

    naive = simulate_generation(embeddings, weights, heads, use_kv_cache=False)
    cached = simulate_generation(embeddings, weights, heads, use_kv_cache=True)

    console.print("[bold]Autoregressive decode work counter[/bold] (1 layer, teaching model)\n")
    console.print(f"Sequence length: {total_len} (half prefill, half decode steps)")
    console.print(f"Naive (recompute full prefix each step): {naive.layer_forwards} layer-forwards, "
                  f"{naive.tokens_processed} token-slots processed")
    console.print(f"KV cache (1 new token per step):       {cached.layer_forwards} layer-forwards, "
                  f"{cached.tokens_processed} token-slots processed")
    console.print("\n[dim]Real engines save the same factor on GPU time — this is why KV cache exists.[/dim]")


if __name__ == "__main__":
    main()
