#!/usr/bin/env python3
"""Part C §19 + Part D §28 — block pool and prefix sharing."""

from rich.console import Console

from kv_transformer_lab.serving.paged_pool import PagedKVAllocator

console = Console()


def main() -> None:
    alloc = PagedKVAllocator(block_size=16)
    user_a = alloc.allocate_sequence(8192)
    console.print(f"User A: {len(user_a.block_ids)} blocks for 8192 tokens (block_size=16)")
    shared = user_a.block_ids[:32]  # same system+RAG prefix blocks
    user_b = alloc.attach_shared_prefix(shared, extra_tokens=400)
    console.print(f"User B: reuses {len(shared)} prefix blocks, total {len(user_b.block_ids)} blocks")
    console.print(f"Physical block 0 refcount: {alloc.pool.blocks[shared[0]].ref_count}")


if __name__ == "__main__":
    main()
