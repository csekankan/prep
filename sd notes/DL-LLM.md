# Deep Learning & LLMs — Staff Engineer Reference

> From first principles to production at scale.
> Covers the math, the architecture decisions, the engineering trade-offs, and the war stories.
> Read top-to-bottom once, then use as a reference.

---

## Table of Contents

1. [Neural Network Fundamentals](#1-neural-network-fundamentals)
2. [Training Mechanics](#2-training-mechanics)
3. [Convolutional Neural Networks](#3-convolutional-neural-networks)
4. [Sequence Models — RNN / LSTM / GRU](#4-sequence-models)
5. [Attention Mechanism](#5-attention-mechanism)
6. [Transformer Architecture](#6-transformer-architecture)
7. [Pre-Training — BERT & Masked LM](#7-pre-training--bert)
8. [Autoregressive LLMs — GPT Family](#8-autoregressive-llms--gpt-family)
9. [Alignment — RLHF, DPO, RLAIF](#9-alignment--rlhf-dpo-rlaif)
10. [Scaling Laws & Compute-Optimal Training](#10-scaling-laws)
11. [Efficient Training — Distributed & Memory](#11-efficient-training)
12. [Parameter-Efficient Fine-Tuning — LoRA & Friends](#12-parameter-efficient-fine-tuning)
13. [Inference Optimization](#13-inference-optimization)
14. [Retrieval-Augmented Generation](#14-retrieval-augmented-generation)
15. [Multimodal Models](#15-multimodal-models)
16. [Evaluation & Benchmarks](#16-evaluation--benchmarks)
17. [Production Architecture](#17-production-architecture)
18. [Math Foundations](#18-math-foundations)
19. [Critical Papers Cheat-Sheet](#19-critical-papers-cheat-sheet)
20. [Glossary](#20-glossary)

---

## 1. Neural Network Fundamentals

### The Universal Approximation Theorem

A feedforward network with **one hidden layer** and a non-linear activation can approximate any continuous function on a compact subset of ℝⁿ to arbitrary precision — given enough neurons. This is existence proof, not a training recipe.

```
Why it matters: justifies using NNs for arbitrary tasks.
Why it's insufficient: doesn't tell you how many neurons, how to train, or how well it generalizes.
```

### Neuron / Perceptron

```
z = w₁x₁ + w₂x₂ + ... + wₙxₙ + b    (linear combination)
a = σ(z)                                (non-linearity applied)
```

- **w** = weights, **b** = bias, **σ** = activation function
- Without non-linearity, stacked linear layers collapse to a single linear layer (matrix multiplication is associative)

### Layer Types

| Layer | Input → Output | Parameters | Use Case |
|-------|---------------|-----------|----------|
| Dense / Linear | (B, in) → (B, out) | W ∈ ℝ^(in×out), b ∈ ℝ^out | General, classifier heads |
| Conv2D | (B, C, H, W) → (B, C', H', W') | F filters of size (C, kH, kW) | Vision, local features |
| Embedding | (B, T) → (B, T, D) | Lookup table ℝ^(V×D) | Tokens → dense vectors |
| LayerNorm | (B, T, D) → (B, T, D) | γ, β ∈ ℝ^D | Stabilise training |
| Attention | (B, T, D) → (B, T, D) | Q/K/V projections | Long-range dependencies |

### Activation Functions — When to Use What

```
Sigmoid  σ(x) = 1/(1+e^-x)           Range (0,1)   → binary output, gates
Tanh     tanh(x) = (e^x-e^-x)/(e^x+e^-x)  Range (-1,1) → RNN hidden state
ReLU     max(0, x)                    Dead neurons, fast, default for MLP
LeakyReLU max(αx, x)  α≈0.01         Fixes dead ReLU
GELU     x·Φ(x)  (Gaussian CDF)      LLMs (GPT, BERT) — smooth ReLU
SiLU/Swish x·σ(x)                    LLaMA, PaLM
GLU variants (SwiGLU, GeGLU)          LLaMA2, Gemma — 2× params but better
Softmax  eˣⁱ / Σeˣʲ                  Attention weights, output probabilities
```

**SwiGLU** (used in LLaMA 2+):
```
SwiGLU(x, W, V, b, c) = Swish(xW + b) ⊙ (xV + c)
```
Uses a gating mechanism — empirically outperforms vanilla FFN at same FLOP budget.

### Initialisation

Poor initialisation → vanishing/exploding gradients before training even begins.

| Method | Formula | Use When |
|--------|---------|----------|
| Xavier / Glorot | W ~ U[-√(6/(fan_in+fan_out)), ...] | Sigmoid / Tanh |
| He / Kaiming | W ~ N(0, 2/fan_in) | ReLU |
| Small constant | W ~ N(0, 0.02) | GPT-style embeddings |
| Zero bias | b = 0 | Always |

**Fan-in / fan-out** = number of input / output neurons to a layer.

---

## 2. Training Mechanics

### Loss Functions

```python
# Binary Cross-Entropy  — binary classification
L = -[y·log(ŷ) + (1-y)·log(1-ŷ)]

# Categorical Cross-Entropy — multi-class
L = -Σ yᵢ·log(ŷᵢ)

# Language Model Loss — next-token prediction
L = -Σₜ log P(xₜ | x<t)    # mean over tokens in batch

# MSE — regression
L = (1/n)·Σ(y - ŷ)²

# Contrastive (InfoNCE) — CLIP, SimCLR
L = -log[ exp(sim(zᵢ,zⱼ)/τ) / Σₖ exp(sim(zᵢ,zₖ)/τ) ]
```

### Backpropagation

Chain rule applied recursively from loss to every parameter.

```
∂L/∂W = ∂L/∂z · ∂z/∂W        (chain rule)
∂L/∂Wₗ = δₗ · aₗ₋₁ᵀ          (gradient for layer l)
δₗ = (Wₗ₊₁ᵀ δₗ₊₁) ⊙ σ'(zₗ)   (backpropagated error signal)
```

Key insight: **gradients flow backwards** through the same graph used for forward pass. Frameworks (PyTorch) build a computational graph on the fly; `.backward()` traverses it in reverse.

### Vanishing / Exploding Gradients

```
Vanishing: |∂L/∂W₁| → 0  (deep sigmoid nets — gradients shrink by factor <1 each layer)
Exploding: |∂L/∂W₁| → ∞  (RNNs — same weight matrix applied T times)
```

**Solutions:**
- Residual connections (add identity shortcut, gradient has a direct path)
- LayerNorm / BatchNorm (normalise activations, stabilise gradient magnitudes)
- Gradient clipping: `g = g·(max_norm / ||g||)` if `||g|| > max_norm`
- Careful initialisation (He, Xavier)

### Optimisers

**SGD:**
```
θ ← θ - η·∇L(θ)
```

**SGD + Momentum:**
```
v ← β·v - η·∇L(θ)
θ ← θ + v
```

**Adam** (most common in practice):
```
m ← β₁·m + (1-β₁)·g          (1st moment — mean of gradients)
v ← β₂·v + (1-β₂)·g²         (2nd moment — variance of gradients)
m̂ = m/(1-β₁ᵗ)                (bias correction)
v̂ = v/(1-β₂ᵗ)
θ ← θ - η·m̂/(√v̂ + ε)

Defaults: β₁=0.9, β₂=0.999, ε=1e-8, η=1e-3
```

**AdamW** (Adam + weight decay, used in all LLMs):
```
θ ← θ·(1 - η·λ) - η·m̂/(√v̂ + ε)    (λ = weight decay coefficient)
```
> Decoupled weight decay avoids applying decay through the adaptive denominator — critical for LLM training stability.

**Lion** (sign-based, memory-efficient):
```
update = sign(β₁·m + (1-β₁)·g)
m ← β₂·m + (1-β₂)·g
θ ← θ - η·update
```

**Learning Rate Schedules:**
```
Warmup + Cosine Decay (standard for LLMs):
  η(t) = η_max · 0.5·(1 + cos(π·t/T))   for t > warmup_steps
  η(t) = η_max · t/warmup_steps           for t ≤ warmup_steps

Linear Warmup + constant (BERT)
Warmup + sqrt decay (T5, early transformers)
```

### Regularisation

| Technique | Mechanism | Use When |
|-----------|----------|----------|
| L2 / Weight Decay | Add λ‖w‖² to loss | Always, λ≈0.01-0.1 |
| L1 | Add λ‖w‖₁ to loss | Sparse weights |
| Dropout | Zero activations with prob p at train time; scale by 1/(1-p) | MLPs, attention (p≈0.1) |
| Label Smoothing | Replace one-hot y with (1-ε)·y + ε/K | Classification tasks |
| Data Augmentation | Random crop, flip, noise | Vision, NLP (back-translation) |
| Early Stopping | Stop at validation loss minimum | All tasks |
| Batch Normalisation | Normalise per-feature within batch | CNNs |
| Layer Normalisation | Normalise per-sample across features | Transformers |

**Dropout in LLMs:** Typically dropped entirely at scale (GPT-3 uses no dropout). Too much dropout hurts capacity at billion-param scale.

### Batch Normalisation vs Layer Normalisation

```
BatchNorm:  normalise across batch dimension (per feature)
            μ, σ computed over (B samples) for each feature
            Problem: batch-size dependent, bad for small batches/RNNs

LayerNorm:  normalise across feature dimension (per sample)
            μ, σ computed over (D features) for each sample
            Independent of batch size → works for any sequence length
```

```python
# LayerNorm
def layer_norm(x, γ, β, ε=1e-5):
    μ = x.mean(dim=-1, keepdim=True)
    σ = x.std(dim=-1, keepdim=True)
    return γ * (x - μ) / (σ + ε) + β
```

**Pre-LN vs Post-LN Transformers:**
```
Original (Post-LN): x → sublayer → + residual → LayerNorm
Modern (Pre-LN):    x → LayerNorm → sublayer → + residual

Pre-LN: more stable training, no warmup needed, used in GPT-2+, LLaMA
Post-LN: original BERT, requires careful LR warmup
```

---

## 3. Convolutional Neural Networks

### The Convolution Operation

```
Output(i,j) = Σₘ Σₙ Input(i+m, j+n) · Filter(m,n)

Output size: H_out = (H_in - K + 2P) / S + 1
             W_out = (W_in - K + 2P) / S + 1

K = kernel size, P = padding, S = stride
```

**Parameters per Conv layer:** `K² × C_in × C_out + C_out`  
**FLOPs per Conv layer:** `2 × K² × C_in × C_out × H_out × W_out`

### Key CNN Concepts

**Receptive Field:** The region of input that affects a given output neuron.
- After k layers of 3×3 convolutions: RF = 2k + 1
- Pooling and strided convolutions grow RF faster

**Pooling:**
```
Max Pool: take max value in each window (downsampling + translation invariance)
Avg Pool: take average (global avg pool at end → classification)
```

**Depthwise Separable Convolution** (MobileNet):
```
Standard Conv: K²·C_in·C_out·H·W FLOPs
Depthwise + Pointwise: K²·C_in·H·W + C_in·C_out·H·W FLOPs
Ratio: 1/C_out + 1/K²  (≈8-9× reduction for 3×3, 256 channels)
```

### Architecture Milestones

```
LeNet-5 (1998)       — 2 conv + 3 FC, 60K params, MNIST
AlexNet (2012)       — 8 layers, ReLU, dropout, GPU training, ImageNet winner
VGG (2014)           — 3×3 conv only, 138M params, simple & deep
GoogLeNet (2014)     — Inception modules (1×1, 3×3, 5×5 in parallel)
ResNet (2015)        — Residual connections: y = F(x) + x; enabled 152 layers
DenseNet (2017)      — Each layer connected to all previous layers
EfficientNet (2019)  — Compound scaling of width/depth/resolution via NAS
ViT (2020)           — Vision Transformer: image patches as tokens
```

### Residual Connection (ResNet)

```
y = F(x, {Wᵢ}) + x          (identity shortcut)
y = F(x, {Wᵢ}) + Wₛx        (projection shortcut, when dims change)
```

Why it works:
1. Gradient has **direct path** through identity, solving vanishing gradient
2. Network can learn **incremental refinements** (easier than learning from scratch)
3. At initialisation, residual block ≈ identity → smooth loss landscape

---

## 4. Sequence Models

### Recurrent Neural Network (RNN)

```
hₜ = tanh(Wₕhₜ₋₁ + Wₓxₜ + b)
yₜ = Wᵧhₜ

Parameters: Wₕ ∈ ℝ^(H×H), Wₓ ∈ ℝ^(H×D), Wᵧ ∈ ℝ^(O×H)
```

**BPTT (Backpropagation Through Time):** Unroll T steps and apply backprop.
- Gradient ∝ (Wₕ)ᵀ repeated T times → vanishing/exploding

### LSTM (Long Short-Term Memory)

```
Forget gate:  fₜ = σ(Wf·[hₜ₋₁, xₜ] + bf)      ← what to forget from cell
Input gate:   iₜ = σ(Wᵢ·[hₜ₋₁, xₜ] + bᵢ)      ← what to write
Cell update:  c̃ₜ = tanh(Wc·[hₜ₋₁, xₜ] + bc)   ← candidate values
Cell state:   cₜ = fₜ⊙cₜ₋₁ + iₜ⊙c̃ₜ            ← updated cell
Output gate:  oₜ = σ(Wo·[hₜ₋₁, xₜ] + bo)       ← what to output
Hidden state: hₜ = oₜ ⊙ tanh(cₜ)
```

The **cell state cₜ** flows through additive updates (no repeated matrix mult) → solves vanishing gradient for long sequences.

### GRU (Gated Recurrent Unit)

```
Reset gate:   rₜ = σ(Wr·[hₜ₋₁, xₜ])
Update gate:  zₜ = σ(Wz·[hₜ₋₁, xₜ])
Candidate:    h̃ₜ = tanh(Wh·[rₜ⊙hₜ₋₁, xₜ])
Hidden:       hₜ = (1-zₜ)⊙hₜ₋₁ + zₜ⊙h̃ₜ
```

**GRU vs LSTM:** GRU has fewer parameters (2 gates vs 3, no separate cell state). Similar performance in practice. Both obsoleted by attention for most tasks.

### Encoder-Decoder with Attention (Bahdanau, 2015)

```
Context vector: cₜ = Σⱼ αₜⱼhⱼ            (weighted sum of encoder states)
Attention weights: αₜⱼ = softmax(eₜⱼ)
Energy: eₜⱼ = vᵀtanh(Wₛsₜ₋₁ + Wₕhⱼ)    (alignment model)
```

This was the **pivotal paper** — attention allows the decoder to look at any encoder position, not just the final hidden state. Direct ancestor of transformer attention.

---

## 5. Attention Mechanism

### Scaled Dot-Product Attention

```
Attention(Q, K, V) = softmax(QKᵀ / √dₖ) · V

Q ∈ ℝ^(T×dₖ)   (Queries — what we're looking for)
K ∈ ℝ^(S×dₖ)   (Keys   — what each position advertises)
V ∈ ℝ^(S×dᵥ)   (Values — what each position contains)
```

**Why √dₖ?** Without scaling, dot products grow with dimension → softmax saturates → gradients vanish. Dividing by √dₖ keeps variance ≈1.

```python
import torch
import torch.nn.functional as F

def scaled_dot_product_attention(Q, K, V, mask=None):
    d_k = Q.shape[-1]
    scores = Q @ K.transpose(-2, -1) / (d_k ** 0.5)  # (B, H, T, S)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, -1e9)
    weights = F.softmax(scores, dim=-1)
    return weights @ V, weights
```

### Multi-Head Attention (MHA)

```
MultiHead(Q,K,V) = Concat(head₁,...,headₕ) · Wᴼ
headᵢ = Attention(QWᵢᴼ, KWᵢᴷ, VWᵢᵛ)

Wᵢᴼ ∈ ℝ^(d_model × dₖ)    dₖ = d_model / h
Wᵢᴷ ∈ ℝ^(d_model × dₖ)
Wᵢᵛ ∈ ℝ^(d_model × dᵥ)    dᵥ = d_model / h
Wᴼ  ∈ ℝ^(h·dᵥ × d_model)
```

**Why multiple heads?** Each head can attend to different positions with different "aspects" (syntax vs semantics vs coreference). Empirically much better than a single head with the same total compute.

### Complexity

```
Time:   O(T² · d_model)    (quadratic in sequence length!)
Space:  O(T² + T·d_model)

This is the core scalability bottleneck for long sequences.
```

### Attention Variants for Long Sequences

| Method | Complexity | Idea |
|--------|----------|------|
| Sparse Attention (BigBird) | O(T√T) | Attend to local + global + random |
| Longformer | O(T) | Sliding window + global tokens |
| Linformer | O(T) | Project K,V to fixed dimension |
| Performer | O(T) | Random feature approximation of softmax |
| Flash Attention | O(T²) time, O(T) memory | Tiling trick — compute block-by-block, never materialise full T×T matrix |
| Flash Attention 2 | O(T²) time, O(T) memory | Better GPU parallelism, fewer non-matmul FLOPs |
| Flash Attention 3 | O(T²) time, O(T) memory | Hopper GPU features (WGMMA, TMA) |

**Flash Attention** is the most important practical optimisation — same math, dramatically less memory bandwidth usage. Used universally in production LLM training and inference.

### KV Cache (Inference)

```
Autoregressive decoding without cache: recompute K, V for all previous tokens each step → O(T²) per token
With KV cache: store K, V for each layer; only compute for new token → O(T) per token (amortised)

Memory cost: 2 × num_layers × num_heads × head_dim × seq_len × dtype_bytes
For LLaMA-7B, seq_len=2048, fp16: ~512MB per request
```

This is why context length is a memory bottleneck at inference time.

---

## 6. Transformer Architecture

### Full Architecture Diagram

```
Input tokens: [x₁, x₂, ..., xₜ]
       │
       ▼
Token Embedding (B, T) → (B, T, D)    D = d_model
       +
Positional Encoding (T, D)
       │
       ▼
┌─────────────────────────────────┐
│  Transformer Block × N          │
│                                 │
│  ┌─ LayerNorm (Pre-LN) ─────┐  │
│  │  Multi-Head Attention     │  │
│  │  Q, K, V projections      │  │
│  │  Scaled dot-product attn  │  │
│  │  Output projection Wᴼ     │  │
│  └───────────────────────────┘  │
│  + Residual                     │
│                                 │
│  ┌─ LayerNorm (Pre-LN) ─────┐  │
│  │  FFN                      │  │
│  │  Linear(D → 4D)           │  │
│  │  GELU / SwiGLU            │  │
│  │  Linear(4D → D)           │  │
│  └───────────────────────────┘  │
│  + Residual                     │
└─────────────────────────────────┘
       │
       ▼
LayerNorm (final)
       │
       ▼
LM Head: Linear(D → V)   V = vocab size
Softmax → logits over vocabulary
```

### Parameter Count

For a transformer with:
- `L` layers, `d_model` = D, `d_ff` = 4D, `V` vocab size, `h` heads

```
Embedding:         V × D
Per layer:
  Attention:       4 × D² (Q, K, V, O projections)
  FFN:             2 × D × 4D = 8D²
  LayerNorm:       4D (2 × LN, each has γ,β of size D)
Total per layer:   ≈ 12D²
Total:             V×D + L×12D² + D×V (unembedding, often tied)

LLaMA-7B:  D=4096, L=32, h=32, V=32000 → ~7B params
GPT-3:     D=12288, L=96, h=96, V=50257 → ~175B params
```

### Positional Encodings

**Sinusoidal (original Transformer):**
```
PE(pos, 2i)   = sin(pos / 10000^(2i/D))
PE(pos, 2i+1) = cos(pos / 10000^(2i/D))

Fixed, not learned. Can extrapolate to unseen lengths (in theory).
```

**Learned Absolute (BERT, GPT-2):**
```
Lookup table: E_pos ∈ ℝ^(max_len × D)
Added to token embeddings.
Cannot extrapolate beyond max_len.
```

**Rotary Position Embedding — RoPE (LLaMA, GPT-NeoX):**
```
Rotate Q and K vectors by angle θ·pos before dot-product
Relative position is encoded in the dot-product naturally: Q_pos · K_pos' = f(pos - pos')
Enables length extrapolation with tricks (YaRN, NTK-aware)
```

**ALiBi (BLOOM, MPT):**
```
Subtract linear bias from attention scores based on distance: score(i,j) -= m·|i-j|
m is head-specific slope: m ∈ {1/2¹, 1/2², ...}
No positional vectors, strong length extrapolation
```

### Grouped Query Attention (GQA)

Standard MHA: each head has its own K, V → expensive KV cache.

```
MHA: h Q-heads, h K-heads, h V-heads
GQA: h Q-heads, g K-heads, g V-heads   (g < h, e.g. g=8, h=32)
MQA: h Q-heads, 1 K-head,  1 V-head   (extreme compression)

LLaMA 2 70B uses GQA (g=8), trades slight accuracy for 4× KV cache reduction
```

### Causal Masking (Decoder)

```
Mask: upper-triangular matrix of -inf added to attention scores
Ensures position t can only attend to positions ≤ t (no future leakage)

[[0,   -∞,  -∞,  -∞],
 [0,    0,  -∞,  -∞],
 [0,    0,   0,  -∞],
 [0,    0,   0,   0]]
```

### FFN as Key-Value Memory

Anthropic / OpenAI research shows FFN layers act as **key-value stores**:
- First linear layer: keys (patterns that activate neurons)
- Non-linearity: gates (which knowledge is relevant)
- Second linear layer: values (information to retrieve)

This explains why FFN = 4× width works well — wider = more "memories".

---

## 7. Pre-Training — BERT

### Masked Language Modelling (MLM)

```
Input:  "The [MASK] sat on the mat"
Output: P("cat" | context)   → cross-entropy loss

15% of tokens masked:
  80% replaced with [MASK]
  10% replaced with random token
  10% kept as-is
→ forces model to use context from both directions (bidirectional)
```

### Next Sentence Prediction (NSP)

```
Input: [CLS] sentence A [SEP] sentence B [SEP]
Label: IsNext / NotNext

Later research (RoBERTa, ALBERT) showed NSP hurts performance — removed.
Replaced with Sentence Order Prediction (SOP) in ALBERT.
```

### BERT Architecture Specifics

```
BERT-base:  L=12, D=768,  h=12, V=30522, params=110M
BERT-large: L=24, D=1024, h=16, V=30522, params=340M

Tokeniser: WordPiece (subword)
Input: [CLS] tok₁ ... tokₙ [SEP]
[CLS] pooled → classification head
```

### BERT Variants

| Model | Key Change | Why Better |
|-------|-----------|-----------|
| RoBERTa | Remove NSP, train longer, dynamic masking | NSP was noisy signal |
| ALBERT | Factorised embeddings, layer sharing | 89% fewer params, similar perf |
| DistilBERT | Knowledge distillation from BERT | 40% smaller, 97% of performance |
| DeBERTa | Disentangled attention (separate content/position) | SOTA on many benchmarks |
| ELECTRA | Replace tokens (RTD) vs masked tokens (MLM) | 4× more efficient |

**ELECTRA — Replaced Token Detection:**
```
Generator (small MLM): fills masked tokens
Discriminator: predicts which tokens were replaced (binary task on ALL tokens)
→ All tokens contribute to loss (vs 15% in BERT)
→ Same compute, much better representations
```

---

## 8. Autoregressive LLMs — GPT Family

### Causal Language Modelling Objective

```
L = -Σₜ log P(xₜ | x₁, ..., xₜ₋₁)    (maximise log probability of each token)

Teacher forcing: use ground-truth prefix at train time
Autoregressive at inference: use model's own predictions
```

### GPT Evolution

```
GPT-1 (2018):    117M params,  BooksCorpus, decoder-only transformer. First to show
                               unsupervised pre-training + fine-tuning works.

GPT-2 (2019):    1.5B params,  WebText 40GB. Zero-shot task performance. Initially
                               withheld due to misuse concerns.

GPT-3 (2020):    175B params,  570GB text. Few-shot prompting emerges. No fine-tuning
                               needed for many tasks.

InstructGPT:     1.3B RLHF    RLHF alignment. Showed RLHF > scale for helpfulness.
(2022)

GPT-4 (2023):    ~1.8T MoE?   Multimodal, 128K context, RLHF + Constitutional AI
                 (unconfirmed)

GPT-4o (2024):   Omni model   Native speech/vision/text in same model
```

### LLaMA Family (Meta)

```
LLaMA 1 (2023): 7B–65B, trained on 1T/1.4T tokens public data (CommonCrawl, Wikipedia, GitHub, Books)
                Pre-LN, RoPE, SwiGLU, No bias in linear layers

LLaMA 2 (2023): 7B–70B, 2T tokens, 2× context (4096), GQA for 70B, RLHF fine-tune (Llama-2-chat)

LLaMA 3 (2024): 8B/70B/405B, 15T tokens, 128K vocab (vs 32K), GQA on all sizes

Key architectural changes from GPT-2:
  - RoPE instead of absolute positional embeddings
  - SwiGLU instead of GELU
  - RMSNorm instead of LayerNorm (faster, no mean subtraction)
  - No bias terms in attention/FFN (regularisation, simpler)
```

**RMSNorm:**
```
RMSNorm(x) = x / RMS(x) · γ       RMS(x) = √(Σxᵢ²/n)
Faster than LayerNorm (no mean subtraction, no β bias term)
Empirically matches LayerNorm quality
```

### Tokenisation

**Byte-Pair Encoding (BPE):**
```
Algorithm:
1. Start with individual characters as vocabulary
2. Find most frequent adjacent pair
3. Merge into new token
4. Repeat until vocab_size reached

GPT-2/3/4: 50K tokens, tiktoken (byte-level BPE)
LLaMA 1/2: 32K tokens, sentencepiece BPE
LLaMA 3:   128K tokens (better coverage of non-English, code)
```

**Why tokenisation matters for staff engineers:**
- Arithmetic is hard: "100+200" may tokenise to ["100", "+", "200"] or ["1","0","0","+","2","0","0"]
- Unicode / multilingual: languages with rare characters get broken into many byte tokens → higher latency, worse performance
- Prompt injection risks around special tokens ([INST], <<SYS>>, <|endoftext|>)

### Mixture of Experts (MoE)

```
Standard FFN: all D×4D params activated for every token
MoE FFN: N expert FFNs, router picks top-k experts per token

FFN_MoE(x) = Σᵢ∈TopK(x) Gᵢ(x) · Eᵢ(x)
Gate: G(x) = Softmax(TopK(x·Wg))     (sparse)

Example: Mixtral 8×7B
  8 experts, top-2 activated per token
  Active params per token: ~13B (like a 13B dense model)
  Total params: ~47B (model is expensive to store but fast to run)
```

**Pros:** More capacity at same compute. **Cons:** Load balancing required, communication cost across GPUs, harder to deploy.

**Load Balancing Loss:**
```
L_aux = α · N · Σᵢ fᵢ · Pᵢ
fᵢ = fraction of tokens routed to expert i
Pᵢ = average gate probability for expert i
Encourages uniform expert utilisation
```

---

## 9. Alignment — RLHF, DPO, RLAIF

### Why Alignment?

Pre-trained LLMs optimise next-token prediction on the web — which contains:
- Instructions on harmful tasks
- Biased text
- Undesirable formats (raw HTML, document headers)

**Alignment** teaches the model to be: Helpful, Harmless, Honest (Anthropic's 3H).

### RLHF Pipeline (InstructGPT)

```
Step 1 — Supervised Fine-Tuning (SFT):
  Fine-tune base LLM on curated (prompt, response) pairs written by contractors
  Loss: standard cross-entropy on response tokens

Step 2 — Reward Model Training:
  Collect: prompt + 2-8 model responses, human ranks them
  Train reward model to predict human preference:
    L_RM = -log σ(r(x, yw) - r(x, yl))    (yw = preferred, yl = rejected)
  Reward model is typically same size as policy, uses [EOS] embedding

Step 3 — PPO Fine-Tuning:
  Use RL (PPO) to maximise reward while staying close to SFT model:
    objective = 𝔼[r(x,y)] - β·KL(π_θ || π_SFT)
    KL penalty prevents reward hacking / gibberish that tricks reward model
```

**PPO (Proximal Policy Optimisation):**
```
L_PPO = 𝔼[min(rₜ·Aₜ, clip(rₜ, 1-ε, 1+ε)·Aₜ)]
rₜ = π_θ(aₜ|sₜ) / π_old(aₜ|sₜ)   (probability ratio)
Aₜ = advantage estimate (how much better than baseline)
Clipping prevents catastrophic policy updates
```

### DPO — Direct Preference Optimisation

RLHF is complex (3 stages, RM training, PPO). DPO collapses it to **one fine-tuning step**:

```
L_DPO = -𝔼[log σ(β·log(π_θ(yw|x)/π_ref(yw|x)) - β·log(π_θ(yl|x)/π_ref(yl|x)))]

Key insight: The optimal RLHF policy has a closed-form relationship to the reference policy.
DPO directly optimises for it without explicitly training a reward model.

β = temperature (controls deviation from reference policy, typically 0.1-0.5)
π_ref = frozen SFT model (reference)
```

**DPO Advantages:** Simpler, stable, no RL instability, no reward model. **Disadvantages:** Less flexible, requires offline preference data, no online exploration.

### RLAIF — RL from AI Feedback

Replace human labellers with a strong LLM (Claude, GPT-4):
```
1. Generate responses
2. AI model ranks/scores them (Constitutional AI style)
3. Train reward model on AI preferences
4. Run PPO or DPO
```

**Constitutional AI (Anthropic):**
```
1. Generate harmful response, then critique it against principles
2. Generate revised response
3. Use AI feedback to train RLHF/RLAIF
```

### ORPO, SimPO, KTO

| Method | Key Idea | Advantage |
|--------|---------|----------|
| ORPO | Penalise rejected responses within the same token-level loss, no reference model | No SFT step needed |
| SimPO | Normalise reward by response length; no reference model | Avoids length bias |
| KTO | Use Kahneman-Tversky prospect theory; works with unpaired preferences | Can use binary feedback |

---

## 10. Scaling Laws

### Chinchilla Scaling Laws (Hoffman et al., 2022)

For a given compute budget C (FLOPs):
```
Optimal model size:    N_opt ∝ C^0.5
Optimal training data: D_opt ∝ C^0.5

N_opt ≈ C / (6·D_opt)     (each token processed ≈ 6·N FLOPs, forward+backward)

Rule of thumb: Train with ~20 tokens per parameter
  7B model  → 140B tokens (LLaMA 1 used 1T — overtrained by Chinchilla standards)
  70B model → 1.4T tokens
```

**Pre-Chinchilla** (GPT-3 era): models were undertrained (too big for compute budget)
**Post-Chinchilla** (LLaMA era): train smaller models on more data — inference is cheaper

### OpenAI Scaling Laws (Kaplan et al., 2020)

```
L(N) = (Nc/N)^αN            (model size power law)
L(D) = (Dc/D)^αD            (data size power law)
L(C) = (Cc/C)^αC            (compute power law)

αN ≈ 0.076, αD ≈ 0.095, αC ≈ 0.050

Key finding: smooth power laws, no phase transitions observed
(later work found emergent abilities appear at scale)
```

### Emergent Abilities

```
Abilities that appear suddenly at scale, not present in smaller models:
- Chain-of-thought reasoning (appears ~100B params)
- Multi-step arithmetic
- In-context learning
- Instruction following

Debate: are they real emergent phenomena or measurement artefacts?
(Wei et al. 2022 showed some disappear with continuous metrics)
```

### Inference Scaling (Test-Time Compute)

```
"Inference scaling" = using more compute at test time (not training time)
- Chain-of-thought: more tokens → better reasoning
- Self-consistency: sample N responses, majority vote
- Tree of Thought: breadth/depth-first search over reasoning paths
- o1/o3: extended "thinking" tokens before final answer

Key insight: trading inference FLOPs for accuracy, decoupled from model size
```

---

## 11. Efficient Training

### Distributed Training Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│                    Parallelism Taxonomy                          │
│                                                                  │
│  Data Parallel (DP)                                              │
│  ├── Each GPU has full model copy                                │
│  ├── Different data shards per GPU                               │
│  └── Gradients all-reduced across GPUs (AllReduce)              │
│                                                                  │
│  Tensor Parallel (TP) — Megatron-LM                             │
│  ├── Split individual weight matrices across GPUs               │
│  ├── Each GPU computes partial result → AllReduce per layer      │
│  └── Used within a node (fast NVLink needed)                    │
│                                                                  │
│  Pipeline Parallel (PP)                                          │
│  ├── Different layers on different GPUs                          │
│  ├── Micro-batches pipeline through stages                       │
│  └── Bubble overhead (GPUs idle at pipeline boundaries)         │
│                                                                  │
│  Sequence Parallel (SP)                                          │
│  └── Split sequence dimension for LayerNorm/Dropout             │
│                                                                  │
│  Expert Parallel (EP) — MoE                                      │
│  └── Different experts on different GPUs                        │
└─────────────────────────────────────────────────────────────────┘

3D Parallelism: DP × TP × PP simultaneously (used for GPT-3, LLaMA)
```

### ZeRO (Zero Redundancy Optimiser)

DeepSpeed ZeRO reduces memory by partitioning model state across data-parallel workers:

```
ZeRO Stage 1: Shard optimiser states    (4× memory reduction)
ZeRO Stage 2: + Shard gradients        (8× memory reduction)
ZeRO Stage 3: + Shard parameters       (64×+ reduction, but more communication)

Each GPU holds 1/N of states, gathers as needed (AllGather)
vs. DDP which replicates all state on each GPU
```

### Mixed Precision Training

```
FP32 (full precision):  32-bit, stable, 4 bytes/param
BF16 (bfloat16):        16-bit, same exponent range as FP32, 2 bytes/param → preferred for LLMs
FP16 (half precision):  16-bit, narrower range (overflow risk), needs loss scaling

Strategy:
  Forward pass:   BF16/FP16 (fast, low memory)
  Backward pass:  BF16/FP16 accumulate gradients
  Optimiser step: FP32 master weights (precision matters for parameter updates)
  
FP8 training: Used in H100s, Hopper architecture, 2× more FLOPS vs BF16
  - Used in Llama 3 training, DeepSeek-V3
  - Requires careful scaling (per-tensor or per-block)
```

### Gradient Checkpointing (Activation Recomputation)

```
Standard: save all activations during forward → O(N·L) memory
Checkpointing: save activations only at checkpoints, recompute intermediate during backward
  → O(√(N·L)) memory, ~30% extra compute

Use when GPU memory is the bottleneck.
In PyTorch: torch.utils.checkpoint.checkpoint(function, *inputs)
```

### Flash Attention (Implementation Detail)

```
Standard attention: materialise full (T×T) attention matrix → O(T²) memory
Flash Attention: tile Q,K,V into blocks; compute softmax incrementally
  - Never materialise full attention matrix
  - O(T) memory (bounded by block size)
  - IO-aware: optimised for GPU memory hierarchy (HBM vs SRAM)
  - 2-4× faster wallclock than standard attention

Algorithm (simplified):
  for Q_block in Q:
    for K_block, V_block in zip(K, V):
      compute local scores
      update running max and normaliser (online softmax trick)
      accumulate output
```

---

## 12. Parameter-Efficient Fine-Tuning

### Why PEFT?

Full fine-tuning a 70B model requires:
- 70B × 4 bytes (BF16) = 140GB for weights alone
- 2-3× more for gradients and optimiser states = ~420GB+

PEFT methods freeze most parameters, only train a small subset.

### LoRA — Low-Rank Adaptation

```
Full fine-tuning: W = W₀ + ΔW    (ΔW has same rank as W₀, expensive)

LoRA: ΔW = B·A    where B ∈ ℝ^(d×r), A ∈ ℝ^(r×k), r << min(d,k)
h = W₀x + ΔWx = W₀x + BAx

At init: A ~ N(0, σ²), B = 0  (ΔW = 0 at start → stable)
Scaling: ΔW = (α/r)·BA       (α is hyperparameter, divide by r for stable training)

Trainable params: (d+k)·r  vs  d·k for full
Typical r=8-64 covers 0.1%-1% of original params

Applied to: attention Q,K,V,O projections (sometimes FFN too)
```

```python
class LoRALinear(nn.Module):
    def __init__(self, in_features, out_features, r=8, alpha=16):
        super().__init__()
        self.weight = nn.Parameter(...)  # frozen
        self.lora_A = nn.Parameter(torch.randn(r, in_features) / r**0.5)
        self.lora_B = nn.Parameter(torch.zeros(out_features, r))
        self.scale = alpha / r
    
    def forward(self, x):
        return F.linear(x, self.weight) + self.scale * F.linear(F.linear(x, self.lora_A), self.lora_B)
```

**QLoRA:** Quantise base model to 4-bit NF4 (Normal Float 4), train LoRA adapters in BF16. Enables fine-tuning 65B model on single 48GB GPU.

### Other PEFT Methods

| Method | Trainable Params | Idea |
|--------|----------------|------|
| LoRA | (d+k)×r per layer | Low-rank ΔW |
| QLoRA | Same + 4-bit base | LoRA on quantised model |
| LoRA+ | Same as LoRA | Separate LR for A and B (B larger) |
| DoRA | Same | Decompose into magnitude + direction |
| Prefix Tuning | P × D × L | Prepend trainable prefix to K, V |
| Prompt Tuning | P × D | Learnable soft prompt tokens only |
| Adapter | ~2×r×D per layer | Small bottleneck FFN after attention |
| IA³ | ~3×D per layer | Learn scaling vectors for K, V, FFN |

### When to Use LoRA vs Full Fine-Tuning

```
LoRA: domain adaptation, task-specific style, small datasets, limited compute
Full FT: when you have ample compute + large task-specific data + need best performance
         when base model architecture needs to change
         when new modalities are added

Rule of thumb: LoRA r=16 with alpha=32 is a safe starting point
Try target_modules=["q_proj","v_proj"] first, add k_proj+o_proj+ffn if needed
```

---

## 13. Inference Optimization

### Quantisation

Reduce numerical precision of weights (and/or activations) to reduce memory + increase speed.

```
FP32 → FP16/BF16:  2× memory reduction, ~same accuracy
FP32 → INT8:        4× memory reduction, <1% accuracy loss with PTQ
FP32 → INT4:        8× memory reduction, ~1-3% accuracy loss

Quantisation types:
  Post-Training Quantisation (PTQ): quantise after training, no retraining
  Quantisation-Aware Training (QAT): simulate quantisation during training

Granularity:
  Per-tensor: single scale factor for whole tensor (lossy)
  Per-channel: scale per output channel (better)
  Per-token / Per-group: finest granularity (best accuracy)
```

**Key algorithms:**
```
GPTQ (2022): One-shot weight quantisation using Hessian information
  - Layer-by-layer INT4 quantisation
  - Minimises L2 error between original and quantised layer output
  
AWQ (2023): Activation-aware Weight Quantisation
  - Identify salient weights via activation magnitudes
  - Scale salient channels before quantisation
  - Faster inference than GPTQ, slightly better accuracy
  
NF4 (QLoRA): Normal Float 4
  - 16 values spaced according to N(0,1) quantiles
  - Better for normally distributed weights than INT4
  
GGUF (llama.cpp): K-quant format for CPU inference
  - Q4_K_M, Q5_K_M etc. — mix of 4-bit and 5-bit per layer
```

### Speculative Decoding

```
Problem: LLM inference is memory-bandwidth-bound, not compute-bound
         (for single request; batch inference is different)
         Generating 1 token requires loading all weights → GPU underutilised

Speculative decoding:
1. Draft model (small, fast): generate k tokens autoregressively
2. Target model (large): verify all k tokens in ONE forward pass (parallel!)
3. Accept tokens up to first disagreement, reject rest
4. Net: process multiple tokens per target model forward pass

Acceptance rate ≈ 70-80% for well-matched draft/target pairs
Speedup: 2-3× wallclock for latency-critical applications

Variants:
  Medusa: multiple prediction heads on same model (no draft model needed)
  EAGLE: draft with speculative tree; auto-regressive draft head
  SpecInfer: tree-structured verification
```

### Continuous Batching

```
Traditional batching: wait for batch to fill, all requests same length → GPU sits idle
Continuous batching (iteration-level scheduling):
  - Process each generation step for ALL active requests simultaneously
  - Add new requests mid-flight as soon as a slot opens
  - Dramatically improves GPU utilisation (from ~20% to ~80%+)

Used in: vLLM, TGI (Text Generation Inference), TensorRT-LLM
```

### PagedAttention (vLLM)

```
Problem: KV cache for different requests have different sizes → fragmentation → wasted memory

PagedAttention: store KV cache in fixed-size pages (like OS virtual memory)
  - Physical pages allocated on demand
  - Non-contiguous pages mapped via block table
  - Enables KV cache sharing between requests (prefix caching)
  - Enables larger batch sizes → higher throughput

Result: 24× throughput vs HuggingFace, near-zero waste
```

### Tensor Parallelism at Inference

```
For single large requests (long context), split model across GPUs:
  TP=4: each GPU holds 1/4 of attention heads and FFN width
  All-Reduce after each layer (fast on NVLink within node)

For high-throughput: batch requests, use DP across GPU instances
  Each GPU instance serves different requests (no cross-GPU communication)
```

### Inference Serving Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Inference Stack                           │
│                                                              │
│  Client → Load Balancer → Router                             │
│                              │                               │
│           ┌──────────────────┼──────────────────┐            │
│           │                  │                  │            │
│        GPU Pod 1          GPU Pod 2          GPU Pod 3       │
│        (TP=4)             (TP=4)             (TP=4)          │
│           │                  │                  │            │
│           └──────────────────┼──────────────────┘            │
│                              │                               │
│                      Continuous Batching                      │
│                      PagedAttention KV Cache                 │
│                      Speculative Decoding                    │
└──────────────────────────────────────────────────────────────┘

Key metrics:
  TTFT: Time to First Token (latency, dominated by prefill)
  TPOT: Time per Output Token (throughput, dominated by decode)
  Throughput: tokens/sec across all requests
```

---

## 14. Retrieval-Augmented Generation

### Why RAG?

```
LLMs have:
  - Knowledge cutoff (stale facts)
  - Hallucinations (confabulation)
  - Fixed context window (can't hold all documents)
  - No private data access

RAG adds:
  - Up-to-date retrieval
  - Grounded generation (cite sources)
  - Privacy-preserving (data stays in retrieval store)
  - Cheaper than fine-tuning for knowledge updates
```

### RAG Architecture

```
OFFLINE (indexing):
  Documents → Chunker → Embedder → Vector Store
                                 (Chroma, Pinecone, Weaviate, pgvector)

ONLINE (query time):
  Query → Embedder → Similarity Search → Top-K Chunks
                                              ↓
                              Prompt: [System] + [Chunks] + [Query]
                                              ↓
                                          LLM → Response
```

### Embedding Models

```
Sentence transformers (SBERT):  bi-encoder, fast retrieval
  - text-embedding-3-large (OpenAI): 3072-dim, best for general use
  - bge-large-en-v1.5 (BAAI): strong open-source
  - e5-mistral-7b: instruction-tuned embedding model

Cross-encoders: Re-rank top-K candidates (slower but more accurate)
  - Input: (query, document) pair → single relevance score
  - Used as second-stage reranker after bi-encoder retrieval

Late interaction (ColBERT):
  - Store per-token embeddings
  - MaxSim: max(query_tok · doc_tok) over all pairs
  - Better recall, more storage
```

### Chunking Strategies

```
Fixed-size chunking:     512 tokens with 50 overlap (simple baseline)
Sentence chunking:       split on sentence boundaries
Semantic chunking:       split where embedding similarity drops
Recursive text splitter: try paragraphs → sentences → words
Document-aware:          respect markdown headers, code blocks
Small-to-big:            store small chunks, retrieve parents for context
```

### Advanced RAG Patterns

```
Hypothetical Document Embedding (HyDE):
  Query → LLM generates hypothetical answer → embed that → retrieve
  Better than embedding the query directly for asymmetric retrieval

Query Decomposition:
  Complex query → LLM decomposes into sub-queries → retrieve per sub-query → merge

Step-Back Prompting:
  Specific query → LLM abstracts to higher-level question → retrieve principles → answer

RAPTOR:
  Recursively cluster and summarise documents → build tree of summaries
  Retrieve at appropriate level of abstraction

Self-RAG:
  LLM decides WHEN to retrieve (retrieve token)
  LLM critiques its own output (grounded? useful?)
  Trained end-to-end with special reflection tokens
```

### Evaluation Metrics

```
Retrieval:
  Recall@K: fraction of relevant docs in top-K
  NDCG@K: normalised discounted cumulative gain (position-weighted)
  MRR: mean reciprocal rank (where is first relevant doc?)

Generation:
  RAGAS framework:
    - Faithfulness: are claims supported by retrieved context?
    - Answer Relevance: does answer address the question?
    - Context Precision: are retrieved chunks relevant?
    - Context Recall: did retrieval capture all needed info?
```

---

## 15. Multimodal Models

### Vision-Language Models

```
Architecture patterns:
1. Dual Encoder (CLIP): separate image/text encoders, aligned in shared space
2. Fusion Encoder (BLIP-2): image features injected into LLM via cross-attention
3. Early Fusion (Flamingo): interleave image tokens with text tokens
4. Projection (LLaVA): linear/MLP projection of vision features into LLM token space
```

**CLIP (2021):**
```
Train: image-text pairs, contrastive loss
  - ViT (Vision Transformer): image → patch embeddings → transformer
  - Text Transformer: text → embeddings
  - InfoNCE loss: maximise sim(image, text) for matched pairs
  - Trained on 400M image-text pairs from internet

Zero-shot: compare image embedding to text embeddings of class names
```

**LLaVA Architecture:**
```
Image → CLIP ViT encoder → MLP projection → [image tokens] + [text tokens] → LLM

LLaVA 1.5: 336px input, CLIP ViT-L/14, 2-layer MLP connector
LLaVA-Next: dynamic high-resolution tiling (4 tiles × 336px + thumbnail)
```

**Gemini / GPT-4V native multimodal:**
```
Image patches processed natively alongside text tokens
No separate vision encoder — unified transformer
Allows any image resolution, better spatial reasoning
```

### Diffusion Models

```
Forward process: gradually add Gaussian noise to image x₀ over T steps
  q(xₜ|xₜ₋₁) = N(xₜ; √(1-βₜ)·xₜ₋₁, βₜ·I)
  Can sample xₜ directly: xₜ = √ᾱₜ·x₀ + √(1-ᾱₜ)·ε    (ᾱₜ = Π(1-βᵢ))

Reverse process: learn to denoise
  p_θ(xₜ₋₁|xₜ) = N(xₜ₋₁; μ_θ(xₜ,t), Σ_θ(xₜ,t))
  Loss: ||ε - ε_θ(xₜ, t)||²    (predict noise, not image directly)

Architecture: UNet with attention (DDPM), or Transformer (DiT)
```

**Key diffusion papers:**
```
DDPM (Ho et al. 2020):   Basic denoising diffusion
DDIM (Song et al. 2021): Deterministic sampling, 10-50× fewer steps
LDM / Stable Diffusion:  Diffusion in latent space (VAE encoder/decoder)
DiT (Peebles 2022):      Transformer backbone instead of UNet
DALL-E 3 (OpenAI 2023):  CLIP + Cascaded diffusion with better text alignment
```

---

## 16. Evaluation & Benchmarks

### Core LLM Benchmarks

| Benchmark | Tests | Notes |
|-----------|-------|-------|
| MMLU | 57-subject multiple choice | Knowledge breadth |
| HellaSwag | Commonsense NLI | Sentence completion |
| TruthfulQA | Truthfulness | Avoids common misconceptions |
| GSM8K | Grade school math | 8-step word problems |
| MATH | Competition math | AMC/AIME level |
| HumanEval | Python code gen | 164 problems, pass@k |
| MBPP | Python code gen | 374 beginner problems |
| BIG-Bench Hard | Reasoning tasks | Hardest BIG-Bench subset |
| MT-Bench | Multi-turn chat | GPT-4 as judge |
| LMSYS Chatbot Arena | Human preference | ELO-rated pairwise |

### Evaluation Pitfalls (Staff Engineer Must-Knows)

```
Benchmark contamination: test data in pre-training corpus → inflated scores
  Detection: canary strings, membership inference attacks
  Mitigation: holdout sets, time-based splits, dynamic benchmarks

Prompt sensitivity: model performance varies dramatically with prompt format
  Example: "Answer: A" vs "The answer is A" can differ by 10+ points

N-shot inconsistency: 0-shot vs 5-shot can reverse relative rankings

LLM-as-judge bias:
  - Positional bias (prefers first/last response)
  - Verbosity bias (longer = better)
  - Self-preference (GPT-4 rates GPT-4 responses higher)
  Mitigation: swap order, calibrate with human ratings, use multiple judges
```

### Production Evaluation

```
Offline evals (before deployment):
  - Automated metrics: ROUGE, BLEU, BERTScore (NLG tasks)
  - Task-specific: exact match, F1 (QA), pass@k (code)
  - Regression test suite against golden examples

Online evals (in production):
  - Implicit signals: thumbs up/down, regenerate, copy-paste
  - Shadow traffic: compare new vs old model on same requests
  - A/B testing: route % of traffic to new model
  - SLI/SLO: latency p50/p99, error rate, token quality

Guardrail evals:
  - Refusal rate (too strict = bad UX, too loose = safety issue)
  - Jailbreak success rate (red-team)
  - Prompt injection success rate
```

---

## 17. Production Architecture

### Model Serving Stack

```
┌──────────────────────────────────────────────────────────────┐
│                  Production LLM System                        │
│                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌─────────────┐  │
│  │   API        │     │   Gateway    │     │  Load       │  │
│  │   Clients    │────▶│   (Auth,     │────▶│  Balancer   │  │
│  │              │     │   Rate Limit)│     │             │  │
│  └──────────────┘     └──────────────┘     └──────┬──────┘  │
│                                                    │         │
│                              ┌─────────────────────▼──────┐  │
│                              │    Request Router           │  │
│                              │  (model selection, routing) │  │
│                              └──────────────┬─────────────┘  │
│                                             │                │
│         ┌───────────────┬──────────────────┴──────────┐      │
│         │               │                             │      │
│   ┌─────▼──────┐ ┌──────▼────────┐ ┌──────────────────▼─┐   │
│   │ Inference   │ │  Inference   │ │    Inference        │   │
│   │ Server 1    │ │  Server 2    │ │    Server N         │   │
│   │ (vLLM/TGI) │ │  (vLLM/TGI) │ │    (vLLM/TGI)       │   │
│   └─────────────┘ └─────────────┘ └────────────────────┘   │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Prompt   │  │ Output   │  │ KV Cache │  │ Monitoring │  │
│  │ Cache    │  │ Cache    │  │ Offload  │  │ + Logging  │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Key Serving Frameworks

| Framework | Strengths | Best For |
|-----------|-----------|---------|
| vLLM | PagedAttention, continuous batching, most models | Production throughput |
| TGI (HuggingFace) | Wide model support, easy deploy | Prototyping, HF models |
| TensorRT-LLM | NVIDIA-optimised, fastest on H100 | Max performance on NVIDIA |
| Ollama | Local deployment, simple | Development/local testing |
| SGLang | Structured generation, RadixAttention | Structured outputs, agents |
| llama.cpp | CPU inference, GGUF | Edge, CPU-only |

### Prompt Caching

```
Prefix caching: if multiple requests share the same system prompt,
reuse KV cache for the shared prefix

Implementation:
  - Hash system prompt prefix
  - Store KV cache blocks for prefix
  - New requests with same prefix skip recomputation

Savings: 50-80% latency reduction for cached prefix
Used in: Anthropic Claude, OpenAI GPT-4, vLLM (RadixAttention in SGLang)

RadixAttention (SGLang): cache any common prefix/suffix, not just system prompts
```

### Cost Optimisation

```
Input tokens vs Output tokens:
  Output tokens are 3-5× more expensive (requires sequential decoding)
  → Minimise output length via prompt engineering
  → Cache common outputs

Batching strategies:
  Dynamic batching: accumulate requests for 50-100ms, process together
  Offline batching: async processing for non-latency-sensitive tasks

Prompt compression:
  LLMLingua: compress prompts by removing low-perplexity tokens (5-20× compression)
  Selective context: identify and remove redundant context

Model routing:
  Route simple queries to cheap model (GPT-3.5, Haiku)
  Route complex queries to expensive model (GPT-4, Opus)
  ML classifier or rule-based routing
```

### Guardrails & Safety

```
Input guardrails (before LLM):
  - Prompt injection detection
  - PII detection (names, SSNs, emails)
  - Topic classification (off-topic, harmful intent)
  - Rate limiting per user/IP

Output guardrails (after LLM):
  - Toxicity classifier (Perspective API, Llama Guard)
  - PII in output detection
  - Hallucination detection (factuality check)
  - Format validation (JSON schema, code execution)

Libraries: Guardrails AI, NVIDIA NeMo Guardrails, LlamaGuard
```

### Observability

```
What to instrument:
  - TTFT, TPOT, total latency per request
  - Token counts (input, output, cached)
  - Model used, version
  - Request ID for tracing
  - Cost per request
  - User feedback signals

LLM-specific tracing:
  - Prompt/response logging (with PII masking)
  - Chain of tool calls (for agents)
  - Retrieval sources used

Tools: LangSmith, Helicone, Langfuse, Weights & Biases, Arize
```

---

## 18. Math Foundations

### Linear Algebra Essentials

```
Matrix multiplication: (A ∈ ℝ^(m×k)) · (B ∈ ℝ^(k×n)) = C ∈ ℝ^(m×n)
  FLOPs: 2mnk  (2 per multiply-add)

Eigendecomposition: A = QΛQᵀ    (A symmetric)
SVD: A = UΣVᵀ                   (U,V orthogonal; Σ diagonal)
  Used in LoRA rank determination, weight analysis

Softmax: σ(x)ᵢ = eˣⁱ / Σⱼ eˣʲ
  Numerically stable: σ(x - max(x))ᵢ (subtract max to prevent overflow)
  Temperature: σ(x/T)  → T→0: argmax, T→∞: uniform

Dot product similarity: sim(a,b) = a·b / (‖a‖·‖b‖) = cos θ
```

### Probability & Information Theory

```
Cross-entropy: H(p,q) = -Σ p(x)·log q(x)
  Loss = H(y, ŷ) = -Σ yᵢ·log ŷᵢ
  
KL Divergence: KL(p||q) = Σ p(x)·log(p(x)/q(x))
  Always ≥ 0; 0 iff p = q
  Not symmetric: KL(p||q) ≠ KL(q||p)
  
Perplexity: PPL = exp(H(p,q)) = exp(-Σ log p(xₜ|x<t)/T)
  Geometric mean of inverse probabilities
  PPL=10 → model is as confused as choosing between 10 equally likely tokens
  
Entropy: H(p) = -Σ p(x)·log p(x)   (uncertainty in distribution)
Mutual Information: I(X;Y) = H(X) - H(X|Y)   (shared information)
```

### Sampling Methods

```
Greedy decoding: argmax P(xₜ|x<t)         (deterministic, often repetitive)
Temperature sampling: sample from P^(1/T)  (T<1: sharper, T>1: more random)
Top-K sampling: restrict to top K tokens, renormalise
Top-P / Nucleus sampling: restrict to minimum set with cumulative prob ≥ p
  Adaptive: uses fewer tokens when distribution is peaked
  
Min-P: filter tokens with P < min_p × P_max (relative threshold)

Beam search: keep B candidates at each step, expand all, keep top B
  Better for translation/summarisation (coherence > diversity)
  Worse for open-ended generation (diversity needed)
  
Contrastive decoding: subtract small model logits from large model logits
  → removes boring/generic tokens the small model is also confident about
```

### Optimisation Theory

```
Convexity: f(λx + (1-λ)y) ≤ λf(x) + (1-λ)f(y)
  Convex → unique global minimum
  Neural nets: non-convex, but loss landscapes are surprisingly benign
  (saddle points, not local minima, are the main issue at scale)

Saddle points: gradient = 0, but not minimum
  First-order methods escape via noise; second-order methods are expensive

Loss landscape at scale:
  - Small models: sharp minima, poor generalisation
  - Large models: flatter minima, better generalisation (lottery ticket hypothesis)
  - Sharpness-Aware Minimisation (SAM): explicitly finds flatter minima
```

---

## 19. Critical Papers Cheat-Sheet

### Must-Read Papers by Category

**Foundational Architecture:**
```
"Attention Is All You Need" (Vaswani et al., 2017)
  → Transformer, multi-head attention, positional encoding

"BERT: Pre-training of Deep Bidirectional Transformers" (Devlin et al., 2018)
  → MLM, NSP, encoder-only pre-training

"Language Models are Unsupervised Multitask Learners" (Radford et al., 2019)
  → GPT-2, zero-shot prompting

"An Image is Worth 16×16 Words: Transformers for Image Recognition at Scale" (Dosovitskiy et al., 2020)
  → ViT, applying transformer to vision
```

**Scaling & Training:**
```
"Scaling Laws for Neural Language Models" (Kaplan et al., 2020)
  → Power law relationship between N, D, C and loss

"Training Compute-Optimal Large Language Models" (Hoffman et al., 2022)
  → Chinchilla, 20 tokens/param optimal ratio

"LLaMA: Open and Efficient Foundation Language Models" (Touvron et al., 2023)
  → Open weights, efficient architecture (RoPE, SwiGLU, RMSNorm)

"GPT-4 Technical Report" (OpenAI, 2023)
  → Scale, RLHF, safety, multimodal
```

**Alignment:**
```
"Learning to Summarise from Human Feedback" (Stiennon et al., 2020)
  → First RLHF application to LLMs

"Training Language Models to Follow Instructions with Human Feedback" (Ouyang et al., 2022)
  → InstructGPT, full RLHF pipeline

"Direct Preference Optimisation" (Rafailov et al., 2023)
  → DPO, one-stage alignment, no RL

"Constitutional AI" (Bai et al., 2022)
  → RLAIF, AI-generated feedback, scalable oversight
```

**Efficient Training & Inference:**
```
"LoRA: Low-Rank Adaptation of Large Language Models" (Hu et al., 2021)
  → LoRA, rank decomposition for PEFT

"QLoRA: Efficient Finetuning of Quantised LLMs" (Dettmers et al., 2023)
  → 4-bit quantisation + LoRA, single GPU fine-tuning

"FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness" (Dao et al., 2022)
  → IO-aware tiling for attention

"Efficient Memory Management for LLM Serving with PagedAttention" (Kwon et al., 2023)
  → vLLM, paged KV cache, continuous batching

"Fast Inference from Transformers via Speculative Decoding" (Leviathan et al., 2023)
  → Draft + verify, 2-3× speedup
```

**RAG & Retrieval:**
```
"Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (Lewis et al., 2020)
  → RAG, DPR retriever + BART generator

"Improving Language Models by Retrieving from Trillions of Tokens" (Borgeaud et al., 2021)
  → RETRO, retrieval for billion-token corpora

"Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection" (Asai et al., 2023)
  → Reflection tokens, adaptive retrieval
```

**Reasoning & Agents:**
```
"Chain-of-Thought Prompting Elicits Reasoning in Large Language Models" (Wei et al., 2022)
  → CoT prompting, step-by-step reasoning

"ReAct: Synergising Reasoning and Acting in Language Models" (Yao et al., 2022)
  → Interleave reasoning and tool calls

"Toolformer: Language Models Can Teach Themselves to Use Tools" (Schick et al., 2023)
  → Self-supervised tool use

"Tree of Thoughts" (Yao et al., 2023)
  → Search over reasoning paths
```

---

## 20. Glossary

| Term | Definition |
|------|-----------|
| **Perplexity** | exp(cross-entropy loss); lower = better language model |
| **FLOP** | Floating-point operation; FLOPs = total ops, FLOP/s = throughput |
| **MFU** | Model FLOP Utilisation = actual FLOP/s / theoretical peak FLOP/s |
| **BF16** | Brain Float 16; 1 sign, 8 exponent, 7 mantissa bits |
| **KV Cache** | Cached Key/Value tensors for autoregressive decoding efficiency |
| **TTFT** | Time to First Token; latency metric |
| **TPOT** | Time Per Output Token; throughput metric |
| **Hallucination** | Model generating false but confident information |
| **Grounding** | Connecting model output to verifiable sources |
| **In-Context Learning** | Learning from examples in the prompt without weight updates |
| **Few-Shot** | Providing K examples in prompt (K=1 one-shot, K=0 zero-shot) |
| **SFT** | Supervised Fine-Tuning on curated (prompt, response) pairs |
| **RLHF** | Reinforcement Learning from Human Feedback |
| **DPO** | Direct Preference Optimisation; RL-free alignment |
| **LoRA** | Low-Rank Adaptation; PEFT via rank-r weight updates |
| **QLoRA** | Quantised LoRA; 4-bit base + BF16 LoRA adapters |
| **PPO** | Proximal Policy Optimisation; RL algorithm used in RLHF |
| **Reward Hacking** | Policy exploits reward model flaws to get high reward |
| **Temperature** | Sampling parameter; lower = deterministic, higher = random |
| **Top-P (Nucleus)** | Sample from smallest token set covering probability mass ≥ P |
| **Beam Search** | Keep top-B hypotheses at each decoding step |
| **Speculative Decoding** | Draft + verify trick for faster inference |
| **Flash Attention** | IO-aware tiled attention; O(T) memory, same result as standard |
| **PagedAttention** | OS-like paging for KV cache; enables high-throughput serving |
| **Continuous Batching** | Iteration-level request scheduling for high GPU utilisation |
| **Tensor Parallelism** | Split weight matrices across GPUs |
| **Pipeline Parallelism** | Different layers on different GPUs |
| **ZeRO** | Shard optimiser state / gradients / params across data-parallel workers |
| **MoE** | Mixture of Experts; sparse activation of expert FFNs per token |
| **GQA** | Grouped Query Attention; share K/V heads across query heads |
| **RoPE** | Rotary Position Embedding; relative position via rotation |
| **RMSNorm** | Root Mean Square Norm; faster LayerNorm without mean subtraction |
| **SwiGLU** | Swish-gated Linear Unit; activation used in LLaMA |
| **BPE** | Byte Pair Encoding; subword tokenisation algorithm |
| **RAG** | Retrieval-Augmented Generation; retrieve docs then generate |
| **Embedding** | Dense vector representation of token / document |
| **CLIP** | Contrastive Language-Image Pre-training; aligned vision-language |
| **ViT** | Vision Transformer; image as patch tokens |
| **Diffusion Model** | Generative model: learn to reverse Gaussian noise |
| **Contrastive Loss** | Train embeddings to attract similar, repel dissimilar pairs |
| **Emergence** | Capabilities appearing only above some scale threshold |
| **Chinchilla** | Compute-optimal training: 20 tokens/param rule |
| **Alignment Tax** | Slight capability reduction from alignment training |
| **Constitutional AI** | Use AI feedback based on principles for alignment |
| **MMLU** | Massive Multitask Language Understanding; 57-subject benchmark |
| **HumanEval** | Code generation benchmark; pass@k metric |
| **MT-Bench** | Multi-turn conversation benchmark; GPT-4 as judge |
| **ELO** | Rating system for model ranking via pairwise comparisons |

---

*Last updated: 2026. This document covers concepts through LLaMA 3, GPT-4o, Gemini 1.5, Claude 3, and DeepSeek-V3.*
