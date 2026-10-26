"""Lock capacity math to KV-Cache doc Part D numbers."""

from kv_transformer_lab.serving.kv_sizing import DOC_8K_RAG, DOC_80GB_GPU, max_concurrent_sequences


def test_8k_prefill_gib() -> None:
    gib = DOC_8K_RAG.kv_gib_prefill()
    # 8192 × 320 KiB/token = exactly 2.5 GiB; doc rounds to ~2.6 GB
    assert 2.48 <= gib <= 2.65


def test_block_count_8192() -> None:
    assert DOC_8K_RAG.blocks_for_prompt() == 512


def test_concurrency_on_10gib_pool() -> None:
    pool = DOC_80GB_GPU.effective_kv_pool_gib()
    assert pool == 10.0
    n = max_concurrent_sequences(pool, DOC_8K_RAG.kv_gib_prefill())
    assert n == 4  # floor(10 / 2.5 GiB); doc uses ~2.6 GB → ~3 slots
