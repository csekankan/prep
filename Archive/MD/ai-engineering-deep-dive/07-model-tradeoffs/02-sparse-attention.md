# 07.02 — Sparse Attention

> **One sentence:** Sparse attention reduces the O(n²) cost of full attention by only computing attention between a subset of token pairs — enabling much longer context windows.

---

## Why Sparse?

```
Full attention for 128K tokens:
  128,000 × 128,000 = 16.4 BILLION attention scores per head
  Memory: ~32 GB just for the attention matrix (float16)

Sparse attention (1% density):
  ~164 MILLION attention scores per head
  Memory: ~0.32 GB — 100x reduction!
```

---

## Common Sparse Attention Patterns

```
FULL ATTENTION (dense):        SLIDING WINDOW:             DILATED:
┌────────────────┐             ┌────────────────┐          ┌────────────────┐
│ ████████████ │             │ ██░░░░░░░░░░ │          │ █░█░█░░░░░░░ │
│ ████████████ │             │ ███░░░░░░░░░ │          │ ░█░█░█░░░░░░ │
│ ████████████ │             │ ░███░░░░░░░░ │          │ █░█░█░█░░░░░ │
│ ████████████ │             │ ░░███░░░░░░░ │          │ ░░░█░█░█░░░░ │
│ ████████████ │             │ ░░░███░░░░░░ │          │ ░░░░█░█░█░░░ │
│ ████████████ │             │ ░░░░███░░░░░ │          │ ░░░░░█░█░█░░ │
│ ████████████ │             │ ░░░░░███░░░░ │          │ ░░░░░░█░█░█░ │
│ ████████████ │             │ ░░░░░░███░░░ │          │ ░░░░░░░█░█░█ │
│ ████████████ │             │ ░░░░░░░███░░ │          │ █░░░░░░░█░█░ │
│ ████████████ │             │ ░░░░░░░░███░ │          │ ░█░░░░░░░█░█ │
│ ████████████ │             │ ░░░░░░░░░███ │          │ █░█░░░░░░░█░ │
│ ████████████ │             │ ░░░░░░░░░░██ │          │ ░█░█░░░░░░░█ │
└────────────────┘             └────────────────┘          └────────────────┘
O(n²)                          O(n × w)                     O(n × w)

GLOBAL + LOCAL (BigBird):      STRIDED (Longformer):
┌────────────────┐             ┌────────────────┐
│ ████████████ │             │ ██░░░█░░░░░░ │  ← Global tokens
│ ████░░░░░░░░ │             │ ███░░░█░░░░░ │
│ █░███░░░░░░░ │             │ ░███░░░█░░░░ │
│ █░░███░░░░░░ │             │ ░░███░░░█░░░ │
│ █░░░███░░░░░ │             │ █░░███░░░█░░ │  ← Strided
│ █░░░░███░░░░ │             │ ░█░░███░░░█░ │
│ █░░░░░███░░░ │             │ ░░█░░███░░░█ │
│ █░░░░░░███░░ │             │ ░░░█░░███░░░ │
│ █░░░░░░░███░ │             │ ░░░░█░░███░░ │
│ █░░░░░░░░███ │             │ ░░░░░█░░███░ │
│ █░░░░░░░░░██ │             │ ░░░░░░█░░███ │
│ ████████████ │             │ ████████████ │  ← Global tokens
└────────────────┘             └────────────────┘
O(n × (w + g))                 O(n × (w + n/s))
```

---

## Sliding Window Attention (Mistral)

```python
import torch
import torch.nn.functional as F

def sliding_window_attention(Q, K, V, window_size=4096):
    """
    Each token only attends to the last `window_size` tokens.
    Used by Mistral, Gemma, and others.
    
    Complexity: O(n × w) instead of O(n²)
    """
    batch, heads, seq_len, d_k = Q.shape
    
    # Create sliding window mask
    mask = torch.zeros(seq_len, seq_len, dtype=torch.bool)
    for i in range(seq_len):
        start = max(0, i - window_size + 1)
        mask[i, start:i+1] = True  # Attend to window + causal
    
    # Compute attention with mask
    scores = Q @ K.transpose(-2, -1) / (d_k ** 0.5)
    scores = scores.masked_fill(~mask, float('-inf'))
    weights = F.softmax(scores, dim=-1)
    output = weights @ V
    
    return output

# Mistral 7B uses window_size=4096
# But can handle 32K+ tokens because information flows through layers:
# Layer 1: each token sees 4K tokens
# Layer 2: each token indirectly sees 8K tokens (4K of which saw 4K)
# ...
# Layer 32: each token effectively sees 128K tokens!
```

```
Information flow with sliding window across layers:

Layer 1:  Token 10 sees tokens 6-10
Layer 2:  Token 10's representation includes info from tokens 2-10
Layer 3:  Token 10's representation includes info from tokens 0-10
...
After enough layers, every token has "seen" the entire sequence
through indirect information flow!
```

---

## Key Takeaways

1. **Full attention is O(n²)** — prohibitive for long sequences
2. **Sliding window** is the most popular sparse pattern — used by Mistral, Gemma
3. **Information flows across layers** — each layer extends the effective context
4. **Global tokens** (BigBird, Longformer) add long-range connections
5. **Sparse attention trades quality for efficiency** — works well in practice

---

## 💼 FAANG Interview Questions

1. *"How does Mistral handle 32K context with a 4K sliding window?"*
2. *"Compare sliding window attention vs. full attention. When would each fail?"*
3. *"Design an attention pattern for a document QA system with 100K+ token documents."*
