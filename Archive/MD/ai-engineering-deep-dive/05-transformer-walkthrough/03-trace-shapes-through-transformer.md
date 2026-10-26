# 05.03 — Trace the Shapes Through a Transformer

> **One sentence:** Following tensor shapes through each transformer component is the best way to build intuition about what each layer does and how data flows from input tokens to output probabilities.

---

## Model Configuration

```python
# Let's trace shapes through a small GPT-style model
config = {
    "vocab_size": 50000,     # V: vocabulary size
    "d_model": 768,          # D: hidden dimension
    "num_heads": 12,         # H: attention heads
    "d_k": 64,               # D/H: dimension per head
    "d_ff": 3072,            # 4D: feed-forward dimension
    "num_layers": 12,        # L: transformer layers
    "max_seq_len": 1024,     # S_max: maximum sequence length
    "batch_size": 2,         # B: batch size
    "seq_len": 10,           # S: actual sequence length
}
B, S, D, H, d_k, d_ff, V = 2, 10, 768, 12, 64, 3072, 50000
```

---

## Complete Shape Trace

```
STEP                           SHAPE                    COMPUTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Input token IDs               (B, S)                   [2, 10]
                               ↓
Token Embedding lookup         (B, S, D)               [2, 10, 768]
  embed_matrix: (V, D) = (50000, 768)
  token_ids[i] → embed_matrix[token_ids[i]]
                               ↓
+ Position Embedding           (B, S, D)               [2, 10, 768]
  pos_matrix: (S_max, D) = (1024, 768)
  pos_ids = [0, 1, 2, ..., 9]
                               ↓
━━━ TRANSFORMER LAYER (×12) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                               
Layer Norm                     (B, S, D)               [2, 10, 768]
                               ↓
─── Multi-Head Attention ──────────────────────────────────────────
                               
Q = x @ W_Q                   (B, S, D)               [2, 10, 768]
  W_Q: (D, D) = (768, 768)
                               ↓
Reshape Q for heads            (B, S, H, d_k)          [2, 10, 12, 64]
                               ↓
Transpose                      (B, H, S, d_k)          [2, 12, 10, 64]
                               
K: same shapes as Q            (B, H, S, d_k)          [2, 12, 10, 64]
V: same shapes as Q            (B, H, S, d_k)          [2, 12, 10, 64]
                               ↓
Attention scores               
  Q @ K^T                     (B, H, S, S)            [2, 12, 10, 10]
  / sqrt(d_k)                 (B, H, S, S)            [2, 12, 10, 10]
                               ↓
Causal mask                    (S, S)                  [10, 10]
  Applied: masked_fill(-inf)   (B, H, S, S)            [2, 12, 10, 10]
                               ↓
Softmax                        (B, H, S, S)            [2, 12, 10, 10]
                               ↓
Attention @ V                  (B, H, S, d_k)          [2, 12, 10, 64]
                               ↓
Transpose                      (B, S, H, d_k)          [2, 10, 12, 64]
                               ↓
Reshape (concat heads)         (B, S, D)               [2, 10, 768]
                               ↓
W_O projection                 (B, S, D)               [2, 10, 768]
  W_O: (D, D) = (768, 768)
                               
─── End Multi-Head Attention ──────────────────────────────────────
                               ↓
+ Residual (add input)         (B, S, D)               [2, 10, 768]
                               ↓
Layer Norm                     (B, S, D)               [2, 10, 768]
                               ↓
─── Feed-Forward Network ──────────────────────────────────────────
                               
Linear1: x @ W1 + b1          (B, S, d_ff)            [2, 10, 3072]
  W1: (D, d_ff) = (768, 3072)
                               ↓
GELU activation                (B, S, d_ff)            [2, 10, 3072]
                               ↓
Linear2: x @ W2 + b2          (B, S, D)               [2, 10, 768]
  W2: (d_ff, D) = (3072, 768)
                               
─── End Feed-Forward ──────────────────────────────────────────────
                               ↓
+ Residual (add input)         (B, S, D)               [2, 10, 768]
                               
━━━ END TRANSFORMER LAYER ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                               ↓
(Repeat for all 12 layers)     (B, S, D)               [2, 10, 768]
                               ↓
Final Layer Norm               (B, S, D)               [2, 10, 768]
                               ↓
Output projection              (B, S, V)               [2, 10, 50000]
  W_out: (D, V) = (768, 50000)
                               ↓
Softmax (per position)         (B, S, V)               [2, 10, 50000]
                               ↓
Take last position             (B, V)                  [2, 50000]
  → Probability distribution over vocabulary
  → Pick next token
```

---

## Code to Verify

```python
import torch
import torch.nn as nn

B, S, D, H, d_k, d_ff, V = 2, 10, 768, 12, 64, 3072, 50000

# Input
token_ids = torch.randint(0, V, (B, S))
print(f"token_ids:      {token_ids.shape}")  # [2, 10]

# Embedding
tok_emb = nn.Embedding(V, D)
pos_emb = nn.Embedding(1024, D)
x = tok_emb(token_ids) + pos_emb(torch.arange(S))
print(f"after embedding: {x.shape}")  # [2, 10, 768]

# QKV projection
W_Q = nn.Linear(D, D)
Q = W_Q(x)
print(f"Q (projected):   {Q.shape}")  # [2, 10, 768]

# Reshape for multi-head
Q = Q.view(B, S, H, d_k).transpose(1, 2)
print(f"Q (multi-head):  {Q.shape}")  # [2, 12, 10, 64]

# Attention scores
K = torch.randn(B, H, S, d_k)
scores = Q @ K.transpose(-2, -1) / (d_k ** 0.5)
print(f"attn scores:     {scores.shape}")  # [2, 12, 10, 10]

# Causal mask
mask = torch.tril(torch.ones(S, S))
scores = scores.masked_fill(mask == 0, float('-inf'))
weights = torch.softmax(scores, dim=-1)
print(f"attn weights:    {weights.shape}")  # [2, 12, 10, 10]

# Context
V_proj = torch.randn(B, H, S, d_k)
context = weights @ V_proj
print(f"context:         {context.shape}")  # [2, 12, 10, 64]

# Concat heads
context = context.transpose(1, 2).contiguous().view(B, S, D)
print(f"concat heads:    {context.shape}")  # [2, 10, 768]

# FFN
ffn1 = nn.Linear(D, d_ff)
ffn2 = nn.Linear(d_ff, D)
ff_out = ffn2(torch.gelu(ffn1(context)))
print(f"FFN output:      {ff_out.shape}")  # [2, 10, 768]

# Output projection
out_proj = nn.Linear(D, V)
logits = out_proj(ff_out)
print(f"logits:          {logits.shape}")  # [2, 10, 50000]

# Next token probabilities (last position only)
next_token_probs = torch.softmax(logits[:, -1, :], dim=-1)
print(f"next token prob: {next_token_probs.shape}")  # [2, 50000]
```

---

## Shape Summary Table

| Component | Input Shape | Output Shape | Weight Shape |
|-----------|------------|-------------|-------------|
| Token Embedding | (B, S) | (B, S, D) | (V, D) |
| Position Embedding | (S,) | (S, D) | (S_max, D) |
| LayerNorm | (B, S, D) | (B, S, D) | (D,) × 2 |
| Q/K/V Projection | (B, S, D) | (B, S, D) | (D, D) |
| Multi-Head Reshape | (B, S, D) | (B, H, S, d_k) | — |
| Attention Scores | (B, H, S, d_k) × 2 | (B, H, S, S) | — |
| Attention Output | (B, H, S, S) × (B, H, S, d_k) | (B, H, S, d_k) | — |
| Concat Heads | (B, H, S, d_k) | (B, S, D) | — |
| Output Projection | (B, S, D) | (B, S, D) | (D, D) |
| FFN Linear1 | (B, S, D) | (B, S, 4D) | (D, 4D) |
| FFN Linear2 | (B, S, 4D) | (B, S, D) | (4D, D) |
| Final Projection | (B, S, D) | (B, S, V) | (D, V) |

---

## Key Takeaways

1. **Shape is preserved** through the transformer: (B, S, D) in → (B, S, D) out per layer
2. **Attention creates an (S, S) matrix** — this is the O(n²) bottleneck
3. **Multi-head splits D into H pieces** of d_k each — total compute is the same
4. **FFN expands then contracts**: D → 4D → D
5. **Final output is (B, S, V)** — probability distribution over vocabulary at every position

---

## 💼 FAANG Interview Questions

1. *"Trace the tensor shapes for a 70B model with seq_len=4096. What's the memory bottleneck?"*
2. *"Why does the attention matrix have shape (seq_len, seq_len)? Why is this a problem?"*
3. *"If I double the number of attention heads but keep d_model the same, what changes?"*
