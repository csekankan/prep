from bm25_search_lab.bm25 import BM25Index


def test_refund_query() -> None:
    idx = BM25Index()
    idx.add("refund within thirty days")
    idx.add("kubernetes scaling")
    top = idx.search("refund")[0]
    assert top == 0
