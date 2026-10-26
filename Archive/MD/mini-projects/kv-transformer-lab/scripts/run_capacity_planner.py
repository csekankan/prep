#!/usr/bin/env python3
"""Part D §22–27 — 8k RAG KV ledger on an 80GB GPU."""

from rich.console import Console

from kv_transformer_lab.serving.kv_sizing import (
    DOC_70B_FP16,
    DOC_80GB_GPU,
    DOC_8K_RAG,
    format_ledger,
    max_concurrent_sequences,
)

console = Console()


def main() -> None:
    console.print(format_ledger(DOC_8K_RAG, DOC_80GB_GPU))
    prefill_gib = DOC_8K_RAG.kv_gib_prefill()
    n = max_concurrent_sequences(DOC_80GB_GPU.effective_kv_pool_gib(), prefill_gib)
    console.print(f"\nSanity: floor(10 GiB / {prefill_gib:.2f} GiB) ≈ {n} concurrent 8k prompts")
    console.print(f"Formula bytes/token (override): {DOC_70B_FP16.kv_bytes_per_token():,}")


if __name__ == "__main__":
    main()
