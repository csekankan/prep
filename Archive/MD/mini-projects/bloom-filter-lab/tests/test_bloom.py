from bloom_filter_lab.filter import BloomFilter


def test_member_always_found() -> None:
    bf = BloomFilter(size=10_000)
    bf.add("user:42")
    assert "user:42" in bf


def test_absent_usually_not_found() -> None:
    bf = BloomFilter(size=10_000, num_hashes=5)
    for i in range(1000):
        bf.add(f"x{i}")
    assert "definitely-not-inserted" not in bf
