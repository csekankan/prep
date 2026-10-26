"""Okapi BM25 — sparse lexical retrieval baseline before vectors."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field


def tokenize(text: str) -> list[str]:
    return [t for t in text.lower().split() if t]


@dataclass
class BM25Index:
    k1: float = 1.5
    b: float = 0.75
    docs: list[list[str]] = field(default_factory=list)
    doc_len: list[int] = field(default_factory=list)
    df: Counter[str] = field(default_factory=Counter)
    avgdl: float = 0.0

    def add(self, text: str) -> None:
        tokens = tokenize(text)
        self.docs.append(tokens)
        self.doc_len.append(len(tokens))
        for t in set(tokens):
            self.df[t] += 1
        self.avgdl = sum(self.doc_len) / len(self.doc_len)

    def score(self, query: str, doc_id: int) -> float:
        q_terms = tokenize(query)
        n = len(self.docs)
        dl = self.doc_len[doc_id]
        doc = self.docs[doc_id]
        tf = Counter(doc)
        s = 0.0
        for term in q_terms:
            if term not in self.df:
                continue
            idf = math.log(1 + (n - self.df[term] + 0.5) / (self.df[term] + 0.5))
            f = tf[term]
            denom = f + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
            s += idf * (f * (self.k1 + 1)) / denom
        return s

    def search(self, query: str, k: int = 5) -> list[int]:
        scores = [(i, self.score(query, i)) for i in range(len(self.docs))]
        scores.sort(key=lambda x: -x[1])
        return [i for i, _ in scores[:k]]
