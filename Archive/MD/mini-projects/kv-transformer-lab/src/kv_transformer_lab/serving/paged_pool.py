"""
PagedAttention-style KV block pool (Part C §19, §28).

Real vLLM uses GPU tensors; we model:
  - fixed-size token blocks
  - per-sequence block tables
  - reference-counted physical blocks for prefix sharing
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PhysicalBlock:
    id: int
    ref_count: int = 0


@dataclass
class BlockPool:
    block_size: int
    blocks: dict[int, PhysicalBlock] = field(default_factory=dict)
    free: list[int] = field(default_factory=list)
    _next_id: int = 0

    def __post_init__(self) -> None:
        if not self.blocks:
            self._grow(16)

    def _grow(self, n: int) -> None:
        for _ in range(n):
            bid = self._next_id
            self._next_id += 1
            self.blocks[bid] = PhysicalBlock(id=bid)
            self.free.append(bid)

    def allocate_block(self) -> int:
        if not self.free:
            self._grow(8)
        bid = self.free.pop()
        self.blocks[bid].ref_count += 1
        return bid

    def release_block(self, block_id: int) -> None:
        blk = self.blocks[block_id]
        blk.ref_count -= 1
        if blk.ref_count == 0:
            self.free.append(block_id)

    def share_block(self, block_id: int) -> int:
        """Prefix cache hit: bump refcount, reuse same physical block."""
        self.blocks[block_id].ref_count += 1
        return block_id


@dataclass
class SequenceHandle:
    """Virtual → physical mapping (block table)."""

    block_ids: list[int] = field(default_factory=list)

    def token_capacity(self, block_size: int) -> int:
        return len(self.block_ids) * block_size


class PagedKVAllocator:
    def __init__(self, block_size: int = 16) -> None:
        self.pool = BlockPool(block_size=block_size)
        self.block_size = block_size

    def allocate_sequence(self, num_tokens: int) -> SequenceHandle:
        blocks_needed = (num_tokens + self.block_size - 1) // self.block_size
        handle = SequenceHandle()
        for _ in range(blocks_needed):
            handle.block_ids.append(self.pool.allocate_block())
        return handle

    def free_sequence(self, handle: SequenceHandle) -> None:
        for bid in handle.block_ids:
            self.pool.release_block(bid)
        handle.block_ids.clear()

    def attach_shared_prefix(
        self,
        shared_prefix_blocks: list[int],
        extra_tokens: int,
    ) -> SequenceHandle:
        """
        Part D §28: second user shares exact token-ID prefix blocks.

        shared_prefix_blocks: physical IDs already populated for user A
        extra_tokens: tokens after the diverging point (new blocks allocated)
        """
        handle = SequenceHandle()
        for bid in shared_prefix_blocks:
            handle.block_ids.append(self.pool.share_block(bid))
        remaining = extra_tokens
        while remaining > 0:
            handle.block_ids.append(self.pool.allocate_block())
            remaining -= self.block_size
        return handle
