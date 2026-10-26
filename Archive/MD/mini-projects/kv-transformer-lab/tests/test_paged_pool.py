from kv_transformer_lab.serving.paged_pool import PagedKVAllocator


def test_prefix_share_increments_refcount() -> None:
    alloc = PagedKVAllocator(block_size=16)
    a = alloc.allocate_sequence(32)
    bid = a.block_ids[0]
    assert alloc.pool.blocks[bid].ref_count == 1
    b = alloc.attach_shared_prefix([bid], extra_tokens=16)
    assert alloc.pool.blocks[bid].ref_count == 2
    alloc.free_sequence(a)
    assert alloc.pool.blocks[bid].ref_count == 1
    alloc.free_sequence(b)
    assert alloc.pool.blocks[bid].ref_count == 0
