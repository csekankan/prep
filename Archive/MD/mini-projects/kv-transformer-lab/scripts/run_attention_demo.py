#!/usr/bin/env python3
"""Part A §8 — print causal attention weights for a toy sequence."""

import numpy as np
from rich.console import Console
from rich.table import Table

from kv_transformer_lab.attention.causal_self_attention import init_attention_weights, multi_head_attention

console = Console()


def main() -> None:
    # Tiny "model": 4 tokens, 8-dim embeddings (real LLMs use thousands of dims)
    rng = np.random.default_rng(42)
    seq_len, d_model, heads = 4, 8, 2
    h = rng.normal(0, 0.1, (seq_len, d_model))
    w_q, w_k, w_v, w_o = init_attention_weights(d_model, seed=1)

    _, weights = multi_head_attention(h, w_q, w_k, w_v, w_o, num_heads=heads)

    console.print("[bold]Causal self-attention[/bold] — row t can only attend to columns 0..t\n")
    for head_idx, w in enumerate(weights):
        table = Table(title=f"Head {head_idx} (rows=query position, cols=key position)")
        table.add_column("pos", justify="right")
        for j in range(seq_len):
            table.add_column(str(j), justify="right")
        for i in range(seq_len):
            row = [str(i)] + [f"{w[i, j]:.3f}" for j in range(seq_len)]
            table.add_row(*row)
        console.print(table)


if __name__ == "__main__":
    main()
