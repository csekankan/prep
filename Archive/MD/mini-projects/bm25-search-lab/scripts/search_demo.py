#!/usr/bin/env python3
from bm25_search_lab.bm25 import BM25Index

idx = BM25Index()
for doc in [
    "kubernetes pod oom killed increase memory limits",
    "refund policy within 30 days receipt required",
    "password reset email link expires",
]:
    idx.add(doc)
hits = idx.search("refund receipt")
print("top doc:", idx.docs[hits[0]])
