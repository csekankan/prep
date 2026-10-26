# Transformers, LLMs & KV Cache — From Zero to System Design

A **beginner-friendly, plain-language** reference for someone coming from system design / HLD who needs to understand how LLMs actually work **inside**, before diving into serving, KV cache, and inference engineering.

**Related:** `AI-Native-Architecture-Chat-Study-Notes.md` (Ch 5 Serving), Algoroq Ch 5 PDF.

---

## How to read this doc

| If you want… | Jump to |
|--------------|---------|
| What is an LLM at all? | Part A §1–3 |
| How tokens & embeddings work | Part A §4–5 |
| The transformer architecture (full picture) | Part A §6–12 |
| Self-attention explained step by step | Part A §8 |
| How training vs inference differs | Part A §13 |
| K/V vs weight matrices W_k, W_v | Part B §14–15 |
| KV cache in GPU RAM (serving) | Part C §16–20 |
| Worked 8k RAG example with numbers | Part D §21–28 |
| Quick revision drills | Part E |
| **Runnable Python labs** | [`mini-projects/kv-transformer-lab/`](./mini-projects/kv-transformer-lab/) (attention, KV cache, paging, capacity math) |

---

# Part A — Transformers & LLMs from scratch

---

## 1. What is an LLM?

**Large Language Model** = a very large neural network trained to **predict the next word** (technically next **token**) given everything before it.

```text
Input:   "The capital of France is"
Output:  probability over every word in vocabulary
         → "Paris" gets highest probability
```

That's it. Everything else (chat, code generation, reasoning) is built on top of this one trick: **next-token prediction**, scaled to billions of parameters and trillions of training tokens.

---

## 2. Why "transformer"?

Before transformers (2017), language models used **RNNs** (recurrent neural networks) that read tokens **one by one**, passing a hidden state forward like a conveyor belt.

| | RNN | Transformer |
|---|-----|-------------|
| Reads input | One token at a time (sequential) | **All tokens at once** (parallel) |
| How it connects words | Hidden state chain (long chains → forgets) | **Attention** (any token can look at any other directly) |
| Training speed | Slow (sequential) | **Fast** (parallel on GPU) |
| Long-range memory | Weak (vanishing gradients) | **Strong** (direct attention paths) |

**Key insight:** the transformer replaced the sequential conveyor belt with a **lookup table** mechanism (attention) where every position can directly ask "which other positions matter to me?"

---

## 3. Encoder vs decoder vs decoder-only

The original 2017 "Attention Is All You Need" paper had **two halves**:

```text
Original Transformer (translation):

  Input text ──► [ENCODER] ──► representation ──► [DECODER] ──► output text
  "Bonjour"                                                     "Hello"
```

| Architecture | Used for | Examples |
|-------------|----------|----------|
| **Encoder-only** | Understanding / classification | BERT, sentence embeddings |
| **Encoder-decoder** | Translation, summarization | T5, original transformer |
| **Decoder-only** | Text generation (next token) | **GPT, LLaMA, Claude, Gemini** |

**Modern LLMs** (the ones you call via API) are almost all **decoder-only**. The rest of this doc focuses on that.

---

## 4. Tokens — the actual input

LLMs don't see characters or words. They see **tokens** — pieces of text mapped to integer IDs.

```text
Text:     "unhappiness is common"
Tokens:   ["un", "happiness", " is", " common"]
Token IDs: [348, 17432, 318, 2219]
```

**Tokenizer** (BPE, SentencePiece, etc.) is a fixed mapping shipped with the model. Same text → same tokens every time (deterministic).

| Concept | What it means |
|---------|---------------|
| **Vocabulary** | All tokens the model knows (typically 32k–128k tokens) |
| **Context window** | Max number of tokens the model can process in one call (e.g. 8k, 128k) |
| **Prompt tokens** | Tokens in the input (system message, user question, RAG chunks…) |
| **Completion tokens** | Tokens the model **generates** as output |

**Why this matters for system design:** cost, latency, and KV cache size all scale with **token count**, not character count.

---

## 5. Embeddings — tokens become vectors

The model can't do math on integer IDs. First step: look up each token ID in a **learned table** to get a **vector** (list of numbers).

```text
Token ID 348 ("un")  →  embedding vector [0.12, -0.45, 0.78, …]   (d_model numbers)
```

| Term | Meaning |
|------|---------|
| **d_model** | Dimension of the embedding vector (e.g. 4096 for a 7B model, 8192 for 70B+) |
| **Embedding table** | Matrix of shape (vocab_size × d_model) — one row per token |

After this step, every token position has a **vector of d_model numbers**. This vector is called the **hidden state** `h`. It flows through all the layers.

```text
Token IDs:     [348,    17432,    318,    2219]
                 ↓        ↓        ↓       ↓
Hidden states: [h_0,    h_1,     h_2,    h_3]    each is d_model numbers
```

---

## 6. Positional information — the model needs to know order

Unlike RNNs, a transformer processes all tokens **in parallel**. But "cat sat on mat" ≠ "mat sat on cat" — **order matters**.

Solution: add **position information** to each embedding.

| Method | How it works | Used by |
|--------|-------------|---------|
| **Sinusoidal** | Fixed math formula per position | Original transformer |
| **Learned** | Trained position embeddings | GPT-2 |
| **RoPE** (rotary) | Rotate Q and K vectors by position angle | **LLaMA, most modern LLMs** |

**RoPE** is the most common today. It doesn't add to the embedding directly — instead it **rotates** the Query and Key vectors inside attention so that the dot product naturally encodes relative distance.

You don't need to memorize the formula. Just know: **the model knows which token is position 5 vs position 500** because of positional encoding.

---

## 7. The big picture — one decoder layer

Every LLM is a **stack of identical layers** (e.g. 32 layers for 7B, 80 layers for 70B). Each layer does:

```text
┌─────────────────────────────────────────────────────┐
│                   ONE DECODER LAYER                  │
│                                                      │
│   Input: h (hidden state for each position)          │
│                                                      │
│   ┌──────────────────────────────────────────────┐   │
│   │  1. Layer Norm                                │   │
│   │  2. Masked Self-Attention  ← the magic part   │   │
│   │  3. Residual connection (add input back)      │   │
│   │  4. Layer Norm                                │   │
│   │  5. Feed-Forward Network (FFN)                │   │
│   │  6. Residual connection (add input back)      │   │
│   └──────────────────────────────────────────────┘   │
│                                                      │
│   Output: updated h for each position                │
└─────────────────────────────────────────────────────┘
```

Repeat this **N times** (N = number of layers). Each layer refines the hidden state, building up richer understanding.

Let's look at each piece:

---

## 8. Self-attention — the core mechanism (step by step)

This is the **most important** part of a transformer. If you get this, you get the model.

### 8.1 The question attention answers

At each position, attention asks: **"Which other positions in the sequence should I pay attention to, and what information should I pull from them?"**

Example: in "The **cat** sat on the **mat** because **it** was soft"
- When processing "it", attention figures out "it" refers to "mat" (not "cat") by giving "mat" a high attention weight.

### 8.2 Three vectors: Query, Key, Value

For **each** token position, the layer creates three vectors from the hidden state:

```text
h_t = hidden state at position t

Q_t = h_t × W_q    ← "What am I looking for?" (Query)
K_t = h_t × W_k    ← "What do I have to offer as a label?" (Key)
V_t = h_t × W_v    ← "What actual content do I carry?" (Value)
```

**Analogy — library search:**

| Vector | Library analogy |
|--------|----------------|
| **Query** | Your search question: "books about cooking" |
| **Key** | Label on each book's spine: "Italian Recipes", "Python Programming", "Baking 101" |
| **Value** | The actual contents of the book |

You compare your **Query** against every book's **Key** (spine label).
High match → you read more of that book's **Value** (contents).

### 8.3 Computing attention scores

```text
score(t, j) = dot_product(Q_t, K_j) / sqrt(d_head)

     Q_t = [0.2, 0.8, 0.1, 0.0]   ← current position's query
     K_5 = [0.1, 0.9, 0.0, 0.2]   ← position 5's key

     dot product = 0.02 + 0.72 + 0 + 0 = 0.74  ← high! position 5 is relevant
     K_3 = [0.9, 0.0, 0.1, 0.8]
     dot product = 0.18 + 0 + 0.01 + 0 = 0.19   ← low, less relevant
```

**sqrt(d_head)** is just a scaling factor to keep numbers stable (not magic).

### 8.4 Softmax → attention weights

```text
raw scores:    [0.19, 0.45, 0.74, 0.12, …]
                 ↓ softmax
weights:       [0.08, 0.15, 0.35, 0.05, …]   ← sums to 1.0
```

Softmax turns scores into **probabilities**: position 5 gets 35% of attention, position 3 gets 8%, etc.

### 8.5 Weighted sum of Values → output

```text
attention_output_t = 0.08 × V_3 + 0.15 × V_4 + 0.35 × V_5 + 0.05 × V_6 + …
```

The output is a **mix** of all positions' values, weighted by how relevant each position was.

### 8.6 Causal mask — "no peeking at the future"

In a **decoder** (text generation), position 5 must **not** see positions 6, 7, 8… (those haven't been generated yet).

```text
Position 5 can attend to: [0, 1, 2, 3, 4, 5]  ✓
Position 5 cannot see:    [6, 7, 8, …]          ✗ masked to -∞ before softmax
```

This is the **causal mask** (or "autoregressive mask"). It's what makes the model generate left-to-right.

### 8.7 Full attention in one diagram

```text
For token at position t:

   h_t ──► W_q ──► Q_t ──────────────┐
                                      │ dot product with every K
   h_0 ──► W_k ──► K_0 ──┐           │    (only positions ≤ t)
   h_1 ──► W_k ──► K_1 ──┤           │
   h_2 ──► W_k ──► K_2 ──┤ scores ◄──┘
   …                      │    │
   h_t ──► W_k ──► K_t ──┘    ↓
                           softmax → weights
   h_0 ──► W_v ──► V_0 ──┐    │
   h_1 ──► W_v ──► V_1 ──┤    ↓
   h_2 ──► W_v ──► V_2 ──┤ weighted sum → attention output
   …                      │
   h_t ──► W_v ──► V_t ──┘
```

### 8.8 Prefill vs decode — when is Q computed for all positions?

During **prefill** (processing the prompt), Q is computed for **ALL** positions in parallel — not just one.

```text
PREFILL (process entire prompt in parallel):
  "The capital of France is"  →  tokens [0, 1, 2, 3, 4]

  h_0 × W_q → Q_0     ┐
  h_1 × W_q → Q_1     │
  h_2 × W_q → Q_2     ├── ALL Q's computed at once (one big matrix multiply)
  h_3 × W_q → Q_3     │
  h_4 × W_q → Q_4     ┘

  Similarly ALL K's and ALL V's computed at once.


DECODE (generate one new token at a time):
  New token "Paris" at position 5

  h_5 × W_q → Q_5     ← ONLY one Q (current token asks a question)
  h_5 × W_k → K_5     ← appended to cache
  h_5 × W_v → V_5     ← appended to cache
```

During prefill, every position asks its question against every **earlier** position (causal mask enforced):

```text
                    K_0  K_1  K_2  K_3  K_4
                   ┌────┬────┬────┬────┬────┐
  Q_0 ×            │ ✅ │ ✗  │ ✗  │ ✗  │ ✗  │   ← can only see itself
  Q_1 ×            │ ✅ │ ✅ │ ✗  │ ✗  │ ✗  │
  Q_2 ×            │ ✅ │ ✅ │ ✅ │ ✗  │ ✗  │
  Q_3 ×            │ ✅ │ ✅ │ ✅ │ ✅ │ ✗  │
  Q_4 ×            │ ✅ │ ✅ │ ✅ │ ✅ │ ✅ │
                   └────┴────┴────┴────┴────┘
                   ✗ = masked to -∞ before softmax (triangular attention matrix)
```

This is one big matrix multiply on the GPU — highly parallel, **compute-bound**.

| | **Prefill** | **Decode** |
|---|---|---|
| **Q computed for** | All positions (0 to T) | Only position T (new token) |
| **K, V computed for** | All positions (0 to T) | Only position T |
| **K, V from past** | None (first pass) | Read from KV cache |
| **Attention shape** | All Q's × all K's (matrix × matrix) | One Q × all K's (vector × matrix) |
| **GPU bottleneck** | **Compute-bound** (huge matmul) | **Memory-bound** (reading KV cache) |

After prefill, all Q's are **discarded** — just like during decode. They did their job. Only K and V survive in the cache for future decode steps.

```text
After prefill completes:
  Kept:      K_0…K_4, V_0…V_4  ← cached, needed by every future decode token
  Discarded: Q_0…Q_4           ← never needed again
```

---

## 9. Multi-head attention — look at things from many angles

One head might focus on syntax ("subject-verb agreement"). Another might focus on meaning ("it → mat"). Running **multiple heads in parallel** lets the model capture different relationships.

```text
d_model = 4096, num_heads = 32  →  d_head = 4096/32 = 128 per head

Head 1: Q,K,V each 128 dims → output 128 dims
Head 2: Q,K,V each 128 dims → output 128 dims
…
Head 32: Q,K,V each 128 dims → output 128 dims

Concatenate all 32 outputs → 4096 dims → multiply by W_o → final attention output
```

| Term | Meaning |
|------|---------|
| **num_heads** | How many parallel attention "views" (e.g. 32, 64) |
| **d_head** | Dimension per head = d_model / num_heads |
| **W_o** | Output projection that combines all heads back to d_model |

### 9.1 GQA — Grouped-Query Attention (modern trick)

**Problem:** with many heads, each has its own K and V → the **KV cache** (§16+) becomes enormous.

**GQA fix:** multiple query heads **share** one K/V head.

```text
Standard MHA (old):    32 Q heads, 32 K heads, 32 V heads
GQA (e.g. LLaMA 70B): 64 Q heads,  8 K heads,  8 V heads
                                     ↑ 8× less KV to cache!
```

Quality barely drops; KV cache shrinks dramatically.

---

## 10. Feed-Forward Network (FFN) — the other half of each layer

After attention mixes information **across positions**, FFN processes each position **independently**:

```text
FFN(x) = activation(x × W_up) × (x × W_gate) × W_down

Dimensions (example):
  x:     4096  →  W_up:  4096 × 14336  →  activation  →  W_down: 14336 × 4096
```

| What it does | Analogy |
|-------------|---------|
| Attention | "Read from other positions" — **communication** between tokens |
| FFN | "Think about what I just read" — **processing** within each token |

The FFN is where most of the model's **parameters** live (the big matrices). It's also where the model stores **factual knowledge** (this is an active research area).

Modern variants use **SwiGLU** (gated activation) — but for system design you just need to know: FFN = big matmul, per position, lots of parameters.

---

## 11. Residual connections & layer norm — stability plumbing

### 11.1 Residual connections (skip connections)

```text
output = LayerNorm(x + Attention(x))       ← add input back to attention output
output = LayerNorm(output + FFN(output))   ← add input back to FFN output
```

**Why?** In deep networks (80 layers), gradients can vanish. Adding the input back gives the gradient a "highway" to flow through. Without residuals, very deep transformers would not train.

### 11.1a The math behind the gradient highway

**Without residual** — gradient must flow *through* the layer:

```text
y = f(x)

∂y/∂x = ∂f/∂x          ← can be tiny (e.g. 0.01)

Stack 80 layers:
∂Loss/∂x₀ = ∂f₈₀/∂x₇₉ × ∂f₇₉/∂x₇₈ × … × ∂f₁/∂x₀
           = 0.01 × 0.01 × 0.01 × … (80 times)
           = 0.01⁸⁰ ≈ 10⁻¹⁶⁰  ← dead zero. Layer 1 stops learning.
```

**With residual** — derivative of a sum is sum of derivatives:

```text
y = x + f(x)

∂y/∂x = ∂(x)/∂x + ∂f(x)/∂x
       =    1     + ∂f(x)/∂x
             ↑
        ALWAYS 1 — this is the bypass
```

That `+ 1` is the key. Stack 80 layers:

```text
∂Loss/∂x₀ = (1 + ∂f₈₀/∂x₇₉) × (1 + ∂f₇₉/∂x₇₈) × … × (1 + ∂f₁/∂x₀)
```

Expand this product — there's always a path through all the 1's:

```text
= 1×1×1×…×1  +  (cross terms with ∂f's)
= 1           +  (other stuff)
  ↑
  Gradient highway — pure 1, never vanishes regardless of depth
```

### 11.1b Visual: two paths for gradient flow

```text
GRADIENT FLOWS BACKWARDS (right to left):

Highway path:    x₀ ◄── 1 ◄── 1 ◄── 1 ◄── 1 ◄── Loss    → arrives as 1.0 ✅
Through-f path:  x₀ ◄─0.01◄─0.01◄─0.01◄─0.01◄── Loss    → arrives as ≈0  ❌

Both paths ADD together. Even when the through-f path dies, the highway delivers.
```

Water pipe analogy:

```text
WITHOUT RESIDUAL:
  ┌──────┐   ┌──────┐   ┌──────┐
  │Narrow │───│Narrow │───│Narrow │── water barely trickles after 80 narrow pipes
  │ pipe  │   │ pipe  │   │ pipe  │
  └──────┘   └──────┘   └──────┘

WITH RESIDUAL:
  ════════════════════════════════════  BIG OPEN PIPE (the +x highway, gradient=1)
  ┌──────┐   ┌──────┐   ┌──────┐
  │Narrow │   │Narrow │   │Narrow │     water flows freely through the big pipe
  │ pipe  │   │ pipe  │   │ pipe  │     AND a little extra through the narrow ones
  └──────┘   └──────┘   └──────┘
```

### 11.1c What each layer actually learns with residuals

Instead of learning the **full transformation**, each layer only learns **what to change** (the delta):

```text
Without residual:  Layer must learn f(x)         ← learn everything from scratch
With residual:     Layer must learn f(x) - x     ← just learn "what to adjust"
```

If a layer has nothing useful to contribute, it can output near-zero → input passes through unchanged → **it can't make things worse**.

| | With Residuals | Without Residuals |
|---|---|---|
| Training depth | 80+ layers work fine | ~10 layers before training collapses |
| Gradient to early layers | Clean signal (≥1.0) | Vanishes exponentially |
| Layer failure mode | Outputs zero → no harm | Outputs noise → corrupts everything |

### 11.2 Layer Norm

Normalizes the hidden state so numbers don't explode or shrink. Two flavors:

| Type | Where norm happens | Used by |
|------|-------------------|---------|
| **Post-Norm** | After attention/FFN | Original transformer |
| **Pre-Norm (RMSNorm)** | **Before** attention/FFN | **LLaMA, most modern LLMs** |

**What RMSNorm does:** rescales the vector so its average magnitude is ~1.0. Without this, values accumulate and grow across layers (attention outputs + FFN outputs pile up), eventually causing numerical overflow or instability.

```text
RMSNorm(x) = x / sqrt(mean(x²) + ε) × γ

  x = [3.2, -1.5, 0.8, 4.1]
  RMS = sqrt((10.24+2.25+0.64+16.81)/4) ≈ 2.74
  normalized = [1.17, -0.55, 0.29, 1.50]   ← stable magnitudes
  × γ (learnable scale)
```

For system design: this adds a tiny compute cost per layer but is crucial for training stability. You won't think about it at serving time.

---

## 12. The full stack — putting it all together

```text
Input text
    ↓
[Tokenizer] → token IDs: [348, 17432, 318, 2219]
    ↓
[Embedding table] → vectors: [h_0, h_1, h_2, h_3]  (each d_model dims)
    ↓
[+ Positional encoding (RoPE applied inside attention)]
    ↓
┌─────────── Layer 1 ───────────┐
│  RMSNorm → Self-Attention → + │
│  RMSNorm → FFN            → + │
└───────────────────────────────┘
    ↓
┌─────────── Layer 2 ───────────┐
│  (same structure)              │
└───────────────────────────────┘
    ↓
    …  (repeat N times: 32 for 7B, 80 for 70B)
    ↓
┌─────────── Layer N ───────────┐
│  (same structure)              │
└───────────────────────────────┘
    ↓
[Final RMSNorm]
    ↓
[LM Head: linear projection d_model → vocab_size]
    ↓
[Logits: one score per token in vocabulary]
    ↓
[Softmax + sampling (temperature)] → chosen next token ID
    ↓
[Detokenize] → text: "Paris"
```

### 12.1 Model size cheat sheet

| Model size | Layers | d_model | Heads (Q/KV) | Params | Typical GPU |
|-----------|--------|---------|--------------|--------|-------------|
| 7B | 32 | 4096 | 32/32 (MHA) | ~7 billion | 1× A100 40G |
| 13B | 40 | 5120 | 40/40 | ~13 billion | 1× A100 80G |
| 70B | 80 | 8192 | 64/8 (GQA) | ~70 billion | 2–4× A100 80G |
| 405B | 126 | 16384 | 128/8 (GQA) | ~405 billion | 8+ H100 |

**More layers + wider d_model = more parameters = smarter model = more GPU RAM needed.**

---

## 12a. Complete architecture — every box explained

Here is the **full decoder-only transformer** from input to output, with every component labeled and explained:

```text
╔══════════════════════════════════════════════════════════════════════════╗
║                    COMPLETE DECODER-ONLY TRANSFORMER                    ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                         ║
║  INPUT: "The capital of France is"                                      ║
║                                                                         ║
║  ┌─────────────────────────────────────────┐                            ║
║  │  ① TOKENIZER                            │                            ║
║  │  Splits text into sub-word pieces        │                            ║
║  │  "The" "capital" "of" "France" "is"      │                            ║
║  │  → token IDs: [464, 3139, 315, 6822, 374]│                           ║
║  └─────────────────┬───────────────────────┘                            ║
║                    ↓                                                     ║
║  ┌─────────────────────────────────────────┐                            ║
║  │  ② TOKEN EMBEDDING TABLE                │                            ║
║  │  Lookup table: token ID → vector         │                            ║
║  │  Shape: (vocab_size × d_model)           │                            ║
║  │  Each ID → d_model numbers (e.g. 4096)   │                            ║
║  │  [464] → [0.12, -0.45, 0.78, …]         │                            ║
║  └─────────────────┬───────────────────────┘                            ║
║                    ↓                                                     ║
║          h = [h_0, h_1, h_2, h_3, h_4]   (5 vectors, each 4096 dims)   ║
║                    ↓                                                     ║
║  ╔═══════════════════════════════════════════════════════════════╗       ║
║  ║              DECODER LAYER 1 of N (all identical)            ║       ║
║  ║                                                              ║       ║
║  ║  ┌──────────────────────────────────────────────────────┐    ║       ║
║  ║  │  ③ RMSNorm (Pre-Norm)                                │    ║       ║
║  ║  │  Normalizes h so values don't explode/shrink          │    ║       ║
║  ║  │  h_norm = h / sqrt(mean(h²) + ε) × γ                 │    ║       ║
║  ║  └───────────────────┬──────────────────────────────────┘    ║       ║
║  ║                      ↓                                       ║       ║
║  ║  ┌──────────────────────────────────────────────────────┐    ║       ║
║  ║  │  ④ MASKED MULTI-HEAD SELF-ATTENTION                  │    ║       ║
║  ║  │                                                      │    ║       ║
║  ║  │  For each head (e.g. 32 heads):                      │    ║       ║
║  ║  │    Q = h_norm × W_q   "What am I looking for?"       │    ║       ║
║  ║  │    K = h_norm × W_k   "What label do I have?"        │    ║       ║
║  ║  │    V = h_norm × W_v   "What content do I carry?"     │    ║       ║
║  ║  │                                                      │    ║       ║
║  ║  │    ④a. RoPE: Rotate Q and K by position angle        │    ║       ║
║  ║  │        (encodes word order without adding vectors)    │    ║       ║
║  ║  │                                                      │    ║       ║
║  ║  │    ④b. Scores = (Q × Kᵀ) / √d_head                  │    ║       ║
║  ║  │        Each Q asks "how relevant is each K to me?"   │    ║       ║
║  ║  │                                                      │    ║       ║
║  ║  │    ④c. Causal Mask: set future positions to -∞       │    ║       ║
║  ║  │        Token 3 CANNOT see tokens 4,5,6…              │    ║       ║
║  ║  │                                                      │    ║       ║
║  ║  │    ④d. Softmax → attention weights (sum to 1.0)      │    ║       ║
║  ║  │                                                      │    ║       ║
║  ║  │    ④e. Output = weights × V  (weighted mix of values)│    ║       ║
║  ║  │                                                      │    ║       ║
║  ║  │  Concatenate all heads → W_o projection → attn_out   │    ║       ║
║  ║  │  (32 heads × 128 dims = 4096 → W_o → 4096)          │    ║       ║
║  ║  └───────────────────┬──────────────────────────────────┘    ║       ║
║  ║                      ↓                                       ║       ║
║  ║  ┌──────────────────────────────────────────────────────┐    ║       ║
║  ║  │  ⑤ RESIDUAL CONNECTION #1                            │    ║       ║
║  ║  │  h = h + attn_out                                    │    ║       ║
║  ║  │  Adds original input back → gradient highway         │    ║       ║
║  ║  │  (derivative has a +1 term that never vanishes)      │    ║       ║
║  ║  └───────────────────┬──────────────────────────────────┘    ║       ║
║  ║                      ↓                                       ║       ║
║  ║  ┌──────────────────────────────────────────────────────┐    ║       ║
║  ║  │  ⑥ RMSNorm (Pre-Norm again)                          │    ║       ║
║  ║  │  Normalize before FFN to keep values stable           │    ║       ║
║  ║  └───────────────────┬──────────────────────────────────┘    ║       ║
║  ║                      ↓                                       ║       ║
║  ║  ┌──────────────────────────────────────────────────────┐    ║       ║
║  ║  │  ⑦ FEED-FORWARD NETWORK (SwiGLU)                     │    ║       ║
║  ║  │                                                      │    ║       ║
║  ║  │  Processes each position INDEPENDENTLY                │    ║       ║
║  ║  │  (attention mixed info ACROSS positions,              │    ║       ║
║  ║  │   FFN now thinks WITHIN each position)                │    ║       ║
║  ║  │                                                      │    ║       ║
║  ║  │  gate   = h_norm × W_gate                             │    ║       ║
║  ║  │  up     = h_norm × W_up                               │    ║       ║
║  ║  │  ffn_out = (SiLU(gate) ⊙ up) × W_down               │    ║       ║
║  ║  │                                                      │    ║       ║
║  ║  │  Dims: 4096 → 14336 → 4096 (expand then compress)   │    ║       ║
║  ║  │  This is where most parameters live (~65% of model)  │    ║       ║
║  ║  │  This is where factual knowledge is stored            │    ║       ║
║  ║  └───────────────────┬──────────────────────────────────┘    ║       ║
║  ║                      ↓                                       ║       ║
║  ║  ┌──────────────────────────────────────────────────────┐    ║       ║
║  ║  │  ⑧ RESIDUAL CONNECTION #2                            │    ║       ║
║  ║  │  h = h + ffn_out                                     │    ║       ║
║  ║  │  Same highway trick as ⑤                              │    ║       ║
║  ║  └───────────────────┬──────────────────────────────────┘    ║       ║
║  ║                      ↓                                       ║       ║
║  ║              Output h (refined hidden state)                 ║       ║
║  ╚══════════════════════╤═══════════════════════════════════╝       ║
║                         ↓                                           ║
║                  (repeat for Layers 2, 3, … N)                      ║
║                         ↓                                           ║
║  ┌─────────────────────────────────────────┐                        ║
║  │  ⑨ FINAL RMSNorm                        │                        ║
║  │  One last normalization after all layers  │                        ║
║  └─────────────────┬───────────────────────┘                        ║
║                    ↓                                                 ║
║  ┌─────────────────────────────────────────┐                        ║
║  │  ⑩ LM HEAD (Linear Projection)          │                        ║
║  │  Maps d_model → vocab_size               │                        ║
║  │  h × W_lm_head → logits                  │                        ║
║  │  4096 dims → 128,000 scores              │                        ║
║  │  One score per token in vocabulary        │                        ║
║  └─────────────────┬───────────────────────┘                        ║
║                    ↓                                                 ║
║  ┌─────────────────────────────────────────┐                        ║
║  │  ⑪ SOFTMAX + SAMPLING                   │                        ║
║  │  Logits → probabilities → pick a token   │                        ║
║  │                                          │                        ║
║  │  Temperature: controls randomness         │                        ║
║  │    T=0: always pick highest prob (greedy) │                        ║
║  │    T=1: sample from distribution          │                        ║
║  │    T>1: more random/creative              │                        ║
║  │                                          │                        ║
║  │  Top-k: only consider top k tokens        │                        ║
║  │  Top-p: only consider tokens summing to p │                        ║
║  └─────────────────┬───────────────────────┘                        ║
║                    ↓                                                 ║
║  ┌─────────────────────────────────────────┐                        ║
║  │  ⑫ DETOKENIZER                          │                        ║
║  │  Token ID → text piece                   │                        ║
║  │  [3681] → "Paris"                         │                        ║
║  └─────────────────────────────────────────┘                        ║
║                                                                      ║
║  OUTPUT: "Paris"                                                     ║
║  (feed back as input → repeat for next token)                        ║
╚══════════════════════════════════════════════════════════════════════╝
```

### 12a.1 What each box does — summary table

| # | Component | What it does | Analogy |
|---|-----------|-------------|---------|
| ① | **Tokenizer** | Splits text into sub-word pieces → integer IDs | Cutting a sentence into Scrabble tiles |
| ② | **Embedding Table** | Looks up each ID → dense vector of d_model numbers | Dictionary: word → meaning (as numbers) |
| ③ | **RMSNorm** | Rescales vectors to stable magnitude ~1.0 | Adjusting volume before passing to next stage |
| ④ | **Masked Multi-Head Attention** | Each token asks "which past tokens matter to me?" and pulls relevant info | Library search: Q=question, K=book labels, V=book contents |
| ④a | **RoPE** | Rotates Q,K vectors by position angle so dot product encodes distance | Stamping a page number on each book |
| ④b | **Score = Q·K/√d** | Measures relevance between positions | Rating each book's match to your question |
| ④c | **Causal Mask** | Prevents seeing future tokens (set to -∞) | Covering books you haven't reached yet |
| ④d | **Softmax** | Turns raw scores into probabilities that sum to 1.0 | Normalizing your ratings to percentages |
| ④e | **Weighted Sum of V** | Mix values based on attention weights | Reading 35% of Book A, 60% of Book B, 5% of Book C |
| ⑤ | **Residual #1** | `h = h + attn_out` — gradient highway (∂y/∂x = **1** + ∂f/∂x) | Big open pipe alongside narrow pipe — gradient always flows |
| ⑥ | **RMSNorm** | Normalize again before FFN | Volume adjustment before next stage |
| ⑦ | **FFN (SwiGLU)** | Per-position processing: expand → activate → compress. Stores factual knowledge | "Thinking about what I just read" — independent per token |
| ⑧ | **Residual #2** | `h = h + ffn_out` — same highway trick | Same open pipe for FFN path |
| ⑨ | **Final RMSNorm** | Last normalization after all layers complete | Final volume check |
| ⑩ | **LM Head** | Linear projection: d_model → vocab_size scores | "Which of my 128k words best follows?" |
| ⑪ | **Softmax + Sampling** | Pick next token based on temperature, top-k, top-p | Rolling weighted dice — temperature controls how fair the dice are |
| ⑫ | **Detokenizer** | Token ID → text string | Reverse dictionary lookup |

### 12a.2 Two halves of each layer — the key insight

```text
ATTENTION (④):                          FFN (⑦):
  Communication between positions        Processing within each position
  "Token 5, look at tokens 0-4"          "Token 5, think about what you learned"
  Mixes information ACROSS the sequence  Transforms information INDEPENDENTLY
  Like a group discussion                Like personal reflection after discussion
```

### 12a.3 Data flow with shapes (7B model example)

```text
Input tokens:       [5 tokens]
                        ↓
Embedding:          5 × 4096          (each token → 4096-dim vector)
                        ↓
── Per Layer (×32 layers) ──────────────────────────────
  RMSNorm:          5 × 4096          (normalize, same shape)
  Q,K,V:            5 × 32 × 128     (32 heads, 128 dims each)
  Attention:        5 × 32 × 128     (per head output)
  Concat + W_o:     5 × 4096          (merge heads back)
  + Residual:       5 × 4096          (add input back)
  RMSNorm:          5 × 4096
  FFN up/gate:      5 × 14336         (expand 3.5×)
  FFN down:         5 × 4096          (compress back)
  + Residual:       5 × 4096          (add input back)
────────────────────────────────────────────────────────
                        ↓
Final RMSNorm:      5 × 4096
LM Head:            5 × 128,000       (score for every vocab token)
Take last position: 1 × 128,000       (only last token predicts next)
Softmax + sample:   → token ID 3681   ("Paris")
```

---

## 13. Training vs inference — two completely different workloads

| | Training | Inference (serving) |
|---|---------|---------------------|
| **Goal** | Learn weights from data | Use learned weights to generate text |
| **Direction** | Forward + **backward** (gradients) | **Forward only** |
| **Batch** | Huge (millions of tokens) | Small (one or few requests) |
| **Compute** | Days/weeks on thousands of GPUs | Milliseconds–seconds per request |
| **What changes** | Weights are **updated** every step | Weights are **frozen** (read-only) |
| **KV cache** | Not used (full sequences known) | **Critical** — avoids recomputing prompt |
| **Cost** | $millions once | $per-token ongoing |

**You as a system designer deal with inference.** Training is someone else's job (or a managed service). But understanding the architecture helps you reason about **why** inference has the constraints it does.

---

### 13.1 Autoregressive generation (how your API call works)

The model generates **one token at a time**. Each new token feeds back as input:

```text
Step 1: "The capital of France is" → model → "Paris"
Step 2: "The capital of France is Paris" → model → ","
Step 3: "The capital of France is Paris," → model → " known"
…
```

**Without KV cache:** every step re-processes the **entire** growing sequence from scratch.  
**With KV cache:** only process the **new** token; reuse stored K,V from all prior positions.

This is **why KV cache exists** — it turns O(T²) per-step work into O(T) per step.

---

# Part B — K, V, and weight matrices (bridge to serving)

---

## 14. K and V vs W_k and W_v — the critical distinction

| | **W_q, W_k, W_v, W_o** | **Q, K, V** |
|---|------------------------|-------------|
| **What** | **Weight matrices** — learned parameters | **Activation vectors** — computed at runtime |
| **When created** | During **training** | During **inference**, per token, per layer |
| **Changes per request?** | **No** — same for every user | **Yes** — different for every sequence |
| **Size depends on** | Model architecture (fixed) | **Context length** (grows with more tokens) |
| **In KV cache?** | **No** — part of model weights in GPU RAM | K and V: **yes**; Q: **no** (only need current Q) |

### 14.1 The computation

```text
At layer ℓ, for token at position t:

   h_t = hidden state (from previous layer)

   Q_t = h_t × W_q     ← "What am I looking for?"     (used once, not cached)
   K_t = h_t × W_k     ← "My label for matching"       (CACHED)
   V_t = h_t × W_v     ← "My content if matched"       (CACHED)
```

**W_k** is the **same matrix** for every token — it's part of the model.  
**K_t** is **different** for every token — it's the result of multiplying that token's hidden state through W_k.

### 14.2 Why cache K and V but not Q?

During **decode**, you generate token at position T:
- You need **Q_T** (current token's query) — computed fresh.
- You need **K_0, K_1, …, K_T** and **V_0, V_1, …, V_T** — all past positions' keys and values.

If you didn't cache past K and V, you'd have to:
1. Recompute h_0 through h_{T-1} (run all layers for all past tokens)
2. Then compute K and V from those

→ That's **re-running the entire prompt** on every decode step → **useless**.

**Q for past positions** isn't needed — attention only uses the **current** position's query against **all** keys.

### 14.3 Diagram

```text
           MODEL WEIGHTS (shared, constant, loaded once)
   ┌───────────────────────────────────────────────────┐
   │   W_q    W_k    W_v    W_o    +  FFN weights …   │
   │   (part of the ~70B parameters)                    │
   └───────────────────────────────────────────────────┘
                          ▲
      h_t ────────────────┴───► Q_t, K_t, V_t  (per token, per layer)

   KV CACHE (per request, grows with context, in GPU HBM):
   ┌─────────────────────────────────────────────────┐
   │  K_0,V_0 │ K_1,V_1 │ K_2,V_2 │ … │ K_T,V_T   │
   └─────────────────────────────────────────────────┘
```

---

## 15. Where everything lives in GPU memory

```text
GPU HBM (e.g. 80 GB)
├── Model Weights ─────────── ~70 GB (FP8) or ~140 GB (FP16)
│   ├── Embedding table
│   ├── W_q, W_k, W_v, W_o  (all layers)
│   ├── FFN weights          (all layers)
│   ├── Layer norms
│   └── LM head
│
├── KV Cache Pool ─────────── ~10 GB (what's left)
│   ├── Sequence A: K,V for positions 0–8191  (~2.6 GB)
│   ├── Sequence B: K,V for positions 0–3000  (~0.96 GB)
│   └── Sequence C: K,V for positions 0–500   (~0.16 GB)
│
└── Scratch / activations ─── small (reused per step)
```

**Weights:** fixed, loaded once, shared by all users.  
**KV cache:** per-request, grows with context, **this is the capacity bottleneck**.

---

# Part C — KV in GPU RAM (inference serving)

---

## 16. The 5-step serving pipeline

```text
Step 1  QUEUE       → request waits for free KV blocks
Step 2  PREFILL     → process entire prompt, compute K,V for all positions
Step 3  KV IN HBM   → store K,V in GPU memory  ← THIS STEP
Step 4  DECODE      → generate one token per step, read all past K,V, append new K,V
Step 5  STREAM      → send tokens to client via SSE
```

Without step 3, every decode step would re-run attention over the **entire** prompt → unusably slow.

---

## 17. How much KV per token?

Formula (all layers, both K and V):

```text
KV_bytes_per_token ≈ 2 × num_layers × num_kv_heads × head_dim × bytes_per_element
```

**Illustrative 70B-class GQA, FP16 KV:** ~**320 KB per token**.

| Context (tokens) | KV for ONE sequence (FP16) |
|------------------|---------------------------|
| 2,048 | ~0.64 GB |
| 8,192 | ~2.6 GB |
| 32,768 | ~10 GB |
| 128,000 | ~40 GB ← may exceed GPU RAM |

---

## 18. What happens on each decode step

```text
Already cached: K_0…K_{T-1}, V_0…V_{T-1}  (prompt + prior output)

New token at position T:
  1. Compute h_T (embedding + pass through layers so far)
  2. At each layer:
     a. Compute Q_T, K_T, V_T from h_T
     b. APPEND K_T, V_T to cache
     c. Attention: Q_T looks at K_0…K_T, V_0…V_T (cache + new)
     d. FFN on result
  3. After all layers: logits → sample → token T emitted
  4. Repeat for token T+1
```

**Cost driver at long context:** reading **all past K,V** each step (grows with T).

---

## 19. PagedAttention — efficient KV storage

**Naive approach:** reserve KV for `max_context` per slot → huge waste when answers are short.

**PagedAttention (vLLM-style):** KV stored in fixed **blocks** (e.g. 16 tokens per block). Each sequence has a **block table** (like virtual memory pages).

```text
Block pool:  [0][1][2][3][4][5][6][7][8][9][10][11][12]…

Request A: blocks [3, 7, 12, 12-partial]     ← 4 blocks for ~60 tokens
Request B: blocks [3, 8, ...]                 ← block 3 shared (same prefix!)
Request C: blocks [1, 4, 5, 6, 9, 10, 11]    ← 7 blocks for ~110 tokens

Free pool: [0, 2, …]
```

Benefits:
- Less fragmentation → **more** concurrent sequences on same budget
- **Prefix caching:** identical leading token blocks **reuse** physical KV → faster TTFT + less duplicate RAM
- Match rule: **exact token ID prefix** — not semantic similarity

---

## 20. KV held longer than you think

```text
t=0     prefill done     → KV allocated (~2.6 GB for 8k)
t=5     last token sent  → KV STILL held
t=5–60  user reading UI  → KV STILL held (SSE connection open)
t=60    connection closed → KV freed → blocks back to pool
```

Capacity planning on **decode duration only** can be **~6× too optimistic** if streams stay open.

**Mitigations:** close server-side stream when generation ends; idle timeout on open connections.

---

## 21. Don't confuse these four "caches"

| Mechanism | Where | What's stored | Match rule |
|-----------|-------|---------------|------------|
| **GPU KV cache** | GPU HBM, per live request | Float tensors (K,V per layer per token) | Exact token prefix |
| **Provider "cached input tokens"** | Provider billing/infra | Same idea, but from **billing** perspective | Exact prefix (product-specific) |
| **Response cache (Redis)** | App layer (your code) | Text responses | Hash or semantic key (your policy) |
| **Vector DB index** | Separate service | Embeddings of document chunks | ANN similarity + filters |

And **conversation DB** (Postgres/Mongo) stores **text messages** — the GPU builds KV from scratch each prefill (unless prefix blocks hit).

---

# Part D — Worked example: one 8k RAG request

---

## 22. Assumptions

| Setting | Value |
|---------|--------|
| Model | ~70B GQA, **FP16 KV** |
| KV per token | **~320 KB** (illustrative) |
| Block size | **16 tokens** per block |
| Prompt size | **8,192 tokens** (at context cap) |
| Completion | **150 tokens** (example) |

---

## 23. What's inside those 8,192 tokens

```text
[A] System prompt + tools + safety        ~   800 tokens
[B] Retrieved RAG chunks (8 × 400 tok)    ~ 3,200 tokens
[C] User question + metadata              ~   200 tokens
[D] Conversation summary + last turns     ~ 1,500 tokens
[E] Remaining / trim slack                ~ 2,492 tokens
                                          ─────────────
                                            8,192 total
```

KV cost depends on **token count only** — 3,200 RAG tokens cost exactly the same as 3,200 chat tokens.

---

## 24. KV size after prefill

```text
KV = 8,192 tokens × 320 KB/token
   = 2,621,440 KB
   ≈ 2.56 GB  (round to ~2.6 GB)
```

---

## 25. Block count

```text
full_blocks  = floor(8192 / 16) = 512 blocks
remainder    = 8192 % 16 = 0
total        = 512 blocks
```

Each block = **16 × 320 KB = 5.12 MB** of KV.  
Check: `512 × 5.12 MB ≈ 2.62 GB` ✓

---

## 26. Decode adds a little more

150 new output tokens:

```text
extra KV ≈ 150 × 320 KB ≈ 48 MB
blocks:  150/16 → 9 full blocks + 1 partial (6 tokens)
```

Total while streaming ≈ **2.65 GB** until client disconnects.

---

## 27. Concurrency on one 80 GB GPU

After **FP8 weights** (~70 GB), roughly ~**10 GB** left for all sequences' KV.

| Scenario | Concurrent 8k RAG chats |
|----------|--------------------------|
| FP16 KV (~2.6 GB each) | floor(10 / 2.6) ≈ **3** |
| KV FP8 (~1.3 GB each) | floor(10 / 1.3) ≈ **7** |
| Trim prompt to **4k** (FP16 KV) | floor(10 / 1.3) ≈ **7** |

Request #4 arrives, only 2 GB free → **queue** or **429**, even if GPU utilization looks low — **KV pool full**, not "compute busy."

---

## 28. Prefix sharing: second user, same RAG template

User 2 has same system prompt [A] and same chunk set [B] (byte-identical), different question [C]:

```text
Shared prefix ~4,000 tokens → 250 blocks may REUSE physical KV
New tail ~4,192 tokens → prefill only 262 new blocks
```

Effects:
- **TTFT:** prefill ~half the tokens → ~**2× faster** first token
- **KV pool:** less duplicate RAM → **fit more** users on same GPU
- Requires: same GPU, exact token IDs match, prefix cache enabled

---

# Part E — Levers, quick reference, drills

---

## 29. Levers that change KV pressure

| Lever | Effect on KV |
|-------|--------------|
| **Shorter context** (RAG 4k vs stuff 128k) | **Huge** — linear reduction |
| **KV FP8** (half precision for cache) | ~2× more tokens/chats |
| **Weight FP8** (frees HBM for KV pool) | More room for KV |
| **GQA** (fewer KV heads) | ~4–8× less KV vs old MHA |
| **Close streams promptly** | Frees blocks sooner |
| Lower `max_tokens` | Slightly less decode growth |

---

## 30. One-page ledger (paste in design reviews)

| Item | Value |
|------|--------|
| Prompt tokens | 8,192 |
| KV after prefill | **~2.6 GB** |
| Paged blocks (16 tok) | **512** |
| +150 output tokens | **+~48 MB** |
| Hold KV until | **Stream closes** (not last token) |
| Main capacity lever | **Shorter context** > smaller max_tokens |

---

## 31. Revision drills

1. What does a transformer **layer** contain? → **Self-attention + FFN + residuals + norms**

2. Q, K, V are created from what? → From the **hidden state h_t** multiplied by **weight matrices W_q, W_k, W_v**

3. W_k is per-token or shared? → **Shared** (weights). K_5 is per-token or shared? → **Per sequence, position 5**

4. Why is the KV cache needed? → Without it, decode would **re-run the full prompt** every token (quadratic cost)

5. Why is Q not cached? → At step T, you only need **Q_T** (current position); past Q values aren't used

6. 8k → 4k context, same model: prefill KV ≈ ? → **~1.3 GB** (half tokens)

7. 8193 tokens, block size 16: how many blocks? → **513** (512 full + 1 partial with 1 token)

8. Why doesn't lowering `max_tokens` save much at prefill? → Prefill KV is from **prompt length**; max_tokens caps **decode growth**

9. What does GQA save? → **KV cache size** (fewer K/V heads shared among Q heads)

10. Name three things that are NOT the GPU KV cache → **Vector DB index**, **conversation DB rows**, **Redis response cache**

---

## 32. Glossary

| Term | Plain definition |
|------|------------------|
| **Transformer** | Neural network architecture using self-attention instead of recurrence |
| **Decoder-only** | Transformer that generates text left-to-right (GPT, LLaMA) |
| **d_model** | Width of hidden state vector (e.g. 4096, 8192) |
| **d_head** | Width per attention head = d_model / num_heads |
| **MHA** | Multi-head attention: each head has own K,V |
| **GQA** | Grouped-query attention: Q heads share K,V heads |
| **RoPE** | Rotary position encoding (how model knows word order) |
| **FFN** | Feed-forward network (per-position processing in each layer) |
| **RMSNorm** | Root-mean-square normalization (stability layer) |
| **Residual** | Skip connection — add input back to output |
| **Logits** | Raw scores over vocabulary before softmax |
| **Temperature** | Controls randomness: low = deterministic, high = creative |
| **HBM** | High-bandwidth memory on the GPU |
| **Prefill** | First pass over prompt; fills KV cache |
| **Decode** | Autoregressive steps; appends one K,V row per token |
| **TTFT** | Time to first token (dominated by prefill) |
| **TPS** | Tokens per second (decode throughput) |
| **PagedAttention** | Block-structured KV allocation (like virtual memory) |
| **KV cache** | Stored K,V tensors in HBM so decode doesn't re-prefill |

---

*Created from AI-Native Architecture study thread. Numbers are illustrative — always verify with your model card and inference engine (vLLM, TensorRT-LLM, etc.).*
