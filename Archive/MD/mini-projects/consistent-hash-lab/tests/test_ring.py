from consistent_hash_lab.ring import HashRing


def test_add_node_moves_minority_of_keys() -> None:
    keys = [f"k{i}" for i in range(5000)]
    ring = HashRing(vnodes_per_node=64)
    frac = ring.key_move_fraction(keys, ["a", "b"], ["a", "b", "c"])
    assert frac < 0.4
