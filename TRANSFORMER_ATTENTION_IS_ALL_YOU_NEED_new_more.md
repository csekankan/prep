# Transformers: "Attention Is All You Need" — Complete Beginner-to-Expert Guide

> The 2017 paper that changed everything.
> Every concept explained with intuition FIRST, then math, then code.
> No prior deep learning knowledge assumed — we build from the ground up.

---

## Table of Contents

1. [The Problem Transformers Solved](#1-the-problem-transformers-solved)
2. [The Big Idea in 60 Seconds](#2-the-big-idea-in-60-seconds)
3. [Input Representation: From Words to Numbers](#3-input-representation-from-words-to-numbers)
4. [Positional Encoding: Teaching Order](#4-positional-encoding-teaching-order)
5. [Attention: The Core Innovation](#5-attention-the-core-innovation)
6. [Multi-Head Attention: Seeing Multiple Relationships](#6-multi-head-attention-seeing-multiple-relationships)
7. [The Encoder: Understanding Input](#7-the-encoder-understanding-input)
8. [The Decoder: Generating Output](#8-the-decoder-generating-output)
9. [Cross-Attention: Connecting Encoder and Decoder](#9-cross-attention-connecting-encoder-and-decoder)
10. [Residual Connections & Layer Normalization](#10-residual-connections--layer-normalization)
11. [Feed-Forward Network: The Knowledge Store](#11-feed-forward-network-the-knowledge-store)
12. [Training the Transformer](#12-training-the-transformer)
13. [Inference: How Generation Actually Works](#13-inference-how-generation-actually-works)
14. [Full Architecture Walk-Through (Putting It All Together)](#14-full-architecture-walk-through)
15. [Parameter Count & Computation Cost](#15-parameter-count--computation-cost)
16. [What Came After: BERT, GPT, and Modern LLMs](#16-what-came-after)
17. [Common Confusions & FAQ](#17-common-confusions--faq)
18. [Interview Questions](#18-interview-questions)
19. [Complete PyTorch Implementation](#19-complete-pytorch-implementation)

---

## 1. The Problem Transformers Solved

### Before Transformers: The RNN Bottleneck

Before 2017, the best models for language tasks (translation, summarization, Q&A) used
**Recurrent Neural Networks (RNNs)** and their improved versions **LSTMs** and **GRUs**.

```
How RNNs process "I love cats":

Step 1: Process "I"     →  hidden state h₁
Step 2: Process "love"  →  hidden state h₂ (depends on h₁)
Step 3: Process "cats"  →  hidden state h₃ (depends on h₂)

Each step DEPENDS on the previous step. This is sequential.
```

**Three fatal problems with RNNs:**

```
Problem 1: SLOW (Sequential Processing)
  - Must process word-by-word, one after another
  - Cannot use GPU parallelism (GPUs are good at doing many things AT ONCE)
  - Training on 1 billion sentences? Each sentence is processed sequentially
  - Result: training takes weeks/months

Problem 2: FORGETS (Long-Range Dependencies)
  - "The cat, which was sitting on the mat in the living room of the house 
     that Jack built near the park where children play, WAS very tired."
  - By the time we reach "WAS", the RNN has partially forgotten "cat"
  - The information passes through too many steps and degrades
  - LSTMs helped (gates control what to remember) but didn't solve it fully

Problem 3: INFORMATION BOTTLENECK (for translation)
  - Encoder-decoder RNN compresses ENTIRE input into ONE fixed-size vector
  - "The complete works of Shakespeare" → [0.2, -0.5, 0.8, ...]  (512 numbers!)
  - All information about a 1000-word sentence crammed into 512 numbers
```

### The Attention Mechanism (2014-2015): A Partial Fix

Bahdanau (2014) introduced **attention** for RNNs — at each decoder step, look back at
ALL encoder states and focus on relevant ones. This solved Problem 3 (bottleneck).

```
Without attention:
  Encoder: "I love cats" → [single vector] → Decoder: "J'aime les chats"
  The decoder only sees ONE compressed representation.

With attention:
  Encoder: "I love cats" → [h₁, h₂, h₃] (keep ALL hidden states)
  Decoder step 1: look at h₁,h₂,h₃ → focus on h₁,h₂ → output "J'aime"
  Decoder step 2: look at h₁,h₂,h₃ → focus on h₃ → output "les chats"
  The decoder can SELECTIVELY focus on any part of the input.
```

But attention was added ON TOP of RNNs. The sequential bottleneck (Problem 1) remained.

### The Transformer Insight: Throw Away Recurrence Entirely

The key insight of "Attention Is All You Need" (Vaswani et al., 2017):

> **What if attention is not just an add-on, but the ENTIRE architecture?**
> 
> No RNNs. No convolutions. Just attention + simple feed-forward layers.

This seems crazy — how does the model even know word ORDER without recurrence?
The answer: **positional encodings** (we'll get to these).

**Result:** 10-100x faster training, better performance, and the foundation for GPT,
BERT, Claude, Llama, and every modern AI system.

---

## 2. The Big Idea in 60 Seconds

```
THE TRANSFORMER IN ONE DIAGRAM:

INPUT:  "I love cats"                 OUTPUT: "J'aime les chats"
         │                                         ▲
         ▼                                         │
   ┌─────────────┐                         ┌──────────────┐
   │   ENCODER    │ ───── context ──────▶  │   DECODER     │
   │ (understand) │      (rich repr.)      │  (generate)   │
   └─────────────┘                         └──────────────┘

ENCODER: "Read the entire input simultaneously, figure out what each word
          means in context, and create a rich representation."

DECODER: "Generate the output one word at a time, using the encoder's
          understanding of the input AND everything generated so far."

KEY INNOVATIONS:
  1. Self-attention: every word looks at every other word (in parallel!)
  2. Positional encoding: inject word order without recurrence
  3. Multi-head attention: look at multiple relationship types simultaneously
  4. Residual connections: make deep networks trainable
```

```
THE CORE MATH (don't worry, we'll explain every symbol):

  Attention(Q, K, V) = softmax(Q · Kᵀ / √d_k) · V

  That's it. This single equation is the heart of every modern AI system.
  Every component of the transformer is built around this.
```

---

## 3. Input Representation: From Words to Numbers

Neural networks only understand numbers. So we need to convert text to numbers.
This happens in two steps: **tokenization** and **embedding**.

### Step 1: Tokenization — Splitting Text into Pieces

```
"I love cats" → tokens → ["I", "love", "cats"]

But modern tokenizers split into SUBWORDS (BPE — Byte Pair Encoding):
  "unhappiness" → ["un", "happi", "ness"]
  "transformer" → ["transform", "er"]

Why subwords?
  - Pure words: vocabulary too large (500K+ English words), rare words never seen
  - Pure characters: too fine-grained, sequences too long
  - Subwords: sweet spot — ~32K-50K tokens covers all languages

Each token maps to an integer (its ID in the vocabulary):
  "I" → 40     "love" → 1567    "cats" → 9823
```

### Step 2: Embedding — From Integer IDs to Vectors

```
Token ID "cats" = 9823

We look up ID 9823 in a BIG TABLE (called the embedding matrix):

Embedding matrix E ∈ ℝ^(V × d_model)
  V = vocabulary size (e.g., 32000 tokens)
  d_model = embedding dimension (512 in original paper)

E[9823] = [0.12, -0.45, 0.78, 0.03, ..., -0.21]   ← 512 numbers
           \_________________________________________/
                    This IS the meaning of "cats"
                    (learned during training)

Similar words have SIMILAR vectors:
  E["cat"]  = [0.11, -0.44, 0.79, 0.04, ..., -0.20]  (very close to "cats"!)
  E["dog"]  = [0.15, -0.40, 0.75, 0.08, ..., -0.18]  (close-ish — also a pet)
  E["car"]  = [0.82, 0.31, -0.14, 0.55, ..., 0.63]   (very different — not an animal)
```

### Why d_model = 512?

```
- Too small (d_model = 16): not enough room to distinguish word meanings
- Too large (d_model = 10000): wasteful, slow, overfitting
- 512: good balance for the original paper's translation task

Modern models use larger dimensions:
  BERT-base:   d_model = 768
  GPT-2:       d_model = 1024
  GPT-3:       d_model = 12288
  LLaMA-7B:    d_model = 4096
  LLaMA-70B:   d_model = 8192
```

### Scaling the Embeddings

The paper multiplies embeddings by √d_model:

```
embedded_input = Embedding(token_id) × √d_model

Why? Embeddings are initialized small (close to 0). Positional encodings use sin/cos
(range -1 to 1). Without scaling, positional encodings dominate.
Multiplying by √512 ≈ 22.6 brings embeddings to a comparable scale.
```

```python
import torch
import torch.nn as nn
import math

class TokenEmbedding(nn.Module):
    def __init__(self, vocab_size, d_model):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.d_model = d_model

    def forward(self, token_ids):
        return self.embedding(token_ids) * math.sqrt(self.d_model)
```

---

## 4. Positional Encoding: Teaching Order

### The Problem: Attention Has No Sense of Order

```
Self-attention processes ALL words simultaneously (not sequentially like RNNs).
This means it has NO IDEA about word order.

To attention, these two sentences are IDENTICAL:
  "Dog bites man"  ← news
  "Man bites dog"  ← big news!

Without position info, the model can't tell them apart because
self-attention only cares about WHAT the words are, not WHERE they are.
```

### The Solution: Add Position Information to Embeddings

The idea: CREATE a vector for each position (0, 1, 2, ...) and ADD it to the 
word embedding.

```
Position 0: PE₀ = [sin(0), cos(0), sin(0), cos(0), ...]
Position 1: PE₁ = [sin(1/10000^0), cos(1/10000^0), sin(1/10000^(2/512)), ...]
Position 2: PE₂ = [sin(2/10000^0), cos(2/10000^0), ...]

Final input = word_embedding + positional_encoding

"Dog bites man":
  Position 0: E("Dog")  + PE₀    → [0.5, 0.3, ...]  (Dog at position 0)
  Position 1: E("bites") + PE₁   → [0.2, 0.7, ...]  (bites at position 1)
  Position 2: E("man")  + PE₂    → [0.8, 0.1, ...]  (man at position 2)

"Man bites dog":
  Position 0: E("Man")  + PE₀    → different from "Dog" + PE₀
  Position 1: E("bites") + PE₁   → same as before
  Position 2: E("Dog")  + PE₂    → different from "man" + PE₂

Now the model CAN distinguish the two sentences!
```

### The Sinusoidal Formula

```
PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))    ← even dimensions
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))    ← odd dimensions

Where:
  pos = position in the sequence (0, 1, 2, ...)
  i   = dimension index (0, 1, 2, ..., d_model/2 - 1)
  d_model = embedding dimension (512)
```

### Why Sinusoidal? Three Reasons

```
Reason 1: UNIQUE — every position gets a distinct vector
  Each position has a unique combination of frequencies.
  Like a fingerprint made of waves.

Reason 2: RELATIVE POSITION — the model can learn distance
  For any fixed offset k:
    PE(pos + k) = linear_transformation(PE(pos))
  
  This means: "the relationship between position 3 and 5"
  is the SAME as "the relationship between position 100 and 102"
  Both are "2 apart" — and the model can detect this.

  Proof sketch (fully spelled out — the short version above skips the frequency term):
    For dimension pair i, define the frequency ωᵢ = 1 / 10000^(2i/d_model).
    So the actual pair of formulas at pair-index i is:
        PE(pos, 2i)   = sin(ωᵢ · pos)
        PE(pos, 2i+1) = cos(ωᵢ · pos)
    (This is why "sin(pos + k)" alone, without ωᵢ, is NOT the real formula — pos always
    gets multiplied by a frequency ωᵢ first. Different dimension-pairs i use different ωᵢ,
    which is what produces the "different oscillation speeds per dimension" pattern below.)

    Now examine position (pos + k) at this same pair-index i, using the angle-addition identities:
        sin(a+b) = sin(a)cos(b) + cos(a)sin(b)
        cos(a+b) = cos(a)cos(b) - sin(a)sin(b)
    with a = ωᵢ·pos and b = ωᵢ·k:
        PE(pos+k, 2i)   = sin(ωᵢ·pos)·cos(ωᵢ·k) + cos(ωᵢ·pos)·sin(ωᵢ·k)
        PE(pos+k, 2i+1) = cos(ωᵢ·pos)·cos(ωᵢ·k) - sin(ωᵢ·pos)·sin(ωᵢ·k)

    Substituting PE(pos,2i)=sin(ωᵢ·pos) and PE(pos,2i+1)=cos(ωᵢ·pos), this is EXACTLY:
        [PE(pos+k, 2i)  ]   [ cos(ωᵢ·k)   sin(ωᵢ·k)] [PE(pos, 2i)  ]
        [PE(pos+k, 2i+1)] = [-sin(ωᵢ·k)   cos(ωᵢ·k)] [PE(pos, 2i+1)]

    That 2×2 matrix is a pure ROTATION matrix (rotating by angle ωᵢ·k) — and crucially, it
    depends ONLY on k (the distance between positions), NOT on pos itself. That's the whole
    point: "position 3 relative to position 5" applies the exact same rotation as "position
    100 relative to position 102," because both have k=2. This is what lets the model learn
    "attend to the token 2 positions back" as ONE reusable pattern, instead of having to
    separately learn it for every possible (pos, pos+2) pair in the sequence.

Reason 3: GENERALIZATION — works for any sequence length
  Since sin/cos are defined for all real numbers, the model can (in theory)
  handle sequences longer than anything seen during training.
  (Learned positional embeddings can't do this.)
```

### Visualizing Positional Encodings

```
Dimension 0 (i=0): sin(pos / 10000^0) = sin(pos)
  Changes very fast — alternates rapidly between positions
  Good for distinguishing adjacent positions

Dimension 100 (i=50): sin(pos / 10000^(100/512))
  Changes slowly — like a long wave
  Good for understanding "roughly where in the sentence are we?"

Dimension 510 (i=255): sin(pos / 10000^(510/512)) ≈ sin(pos / 10000)
  Changes extremely slowly — almost constant for short sentences
  Captures very coarse position information

Pattern: low dimensions = fast oscillation (local position)
         high dimensions = slow oscillation (global position)
         Like a binary clock counting with different bit frequencies!
```

```python
class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000, dropout=0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        # dropout is applied AFTER adding positional info — standard regularization,
        # unrelated to the positional-encoding math itself

        pe = torch.zeros(max_len, d_model)
        # pre-allocate the full table of positional vectors up front: one row per possible
        # position (up to max_len=5000), each row d_model numbers wide — e.g. shape (5000, 512)

        position = torch.arange(0, max_len).unsqueeze(1).float()
        # torch.arange(0, max_len) → [0, 1, 2, ..., 4999]  (this is "pos" in the formulas above)
        # .unsqueeze(1) turns it from shape (5000,) into shape (5000, 1) — a COLUMN of positions,
        # so it can be broadcast-multiplied against div_term (a ROW) below to get every
        # (position, frequency) combination in one matrix operation, instead of a slow Python loop

        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        # this computes ωᵢ = 1 / 10000^(2i/d_model) for every i, but via exp(log(...)) instead
        # of computing 10000^(2i/d_model) directly — purely for numerical stability (raising
        # 10000 to a fractional power directly can lose floating-point precision; exp/log avoids
        # that). torch.arange(0, d_model, 2) → [0, 2, 4, ..., 510] gives the "2i" values directly.

        pe[:, 0::2] = torch.sin(position * div_term)
        # `0::2` means "every even column" (0, 2, 4, ...) — fills them with sin(pos · ωᵢ),
        # matching PE(pos, 2i) = sin(ωᵢ·pos) from the formula above. `position * div_term`
        # broadcasts (5000, 1) × (256,) → (5000, 256), computing every position × every
        # frequency in a single vectorized operation.
        pe[:, 1::2] = torch.cos(position * div_term)
        # `1::2` means "every odd column" (1, 3, 5, ...) — fills them with cos(pos · ωᵢ),
        # matching PE(pos, 2i+1) = cos(ωᵢ·pos). Note both even AND odd columns use the SAME
        # div_term (same ωᵢ) at a given pair-index i — sin/cos form a pair at each frequency,
        # exactly as derived in the rotation-matrix proof above.

        pe = pe.unsqueeze(0)  # (1, max_len, d_model)
        # adds a "batch" dimension at the front, so this table can be broadcast-added to a
        # batch of embeddings of shape (batch_size, seq_len, d_model) in `forward` below

        self.register_buffer('pe', pe)
        # `register_buffer` (not a regular self.pe = pe) tells PyTorch: "this tensor is part
        # of the model's state (moves to GPU with .to(device), gets saved/loaded with the
        # model), but it's NOT a learnable parameter — never update it during backpropagation."
        # That matches the theory: sinusoidal positional encodings are a fixed mathematical
        # formula, not something the model learns from data.

    def forward(self, x):
        """x shape: (batch_size, seq_len, d_model)"""
        x = x + self.pe[:, :x.size(1), :]
        # slices the precomputed table down to just the first seq_len positions (a given batch
        # of sentences might be shorter than max_len=5000), then adds it elementwise to the word
        # embeddings — this addition IS the "final input = word_embedding + positional_encoding"
        # step described in the theory section above
        return self.dropout(x)
```

**Sample output** — for `d_model=8` (using a tiny size so the numbers are readable; real models use 512+), the first few rows of the `pe` table look like:

```
pos=0: [ 0.000,  1.000,  0.000,  1.000,  0.000,  1.000,  0.000,  1.000]
       # sin(0)=0, cos(0)=1 for every dimension pair — position 0 is always this fixed pattern

pos=1: [ 0.841,  0.541,  0.100,  0.995,  0.010,  1.000,  0.001,  1.000]
       # dim 0-1 (fastest frequency): sin(1)=0.841, cos(1)=0.541 — already swung a lot
       # dim 6-7 (slowest frequency): sin(1·ω)≈0.001, cos(1·ω)≈1.000 — barely moved at all
       # ← this is the "low dimensions oscillate fast, high dimensions oscillate slowly" pattern

pos=2: [ 0.909, -0.416,  0.199,  0.980,  0.020,  1.000,  0.002,  1.000]
```

Notice every row is a unique fingerprint (reason 1 above), and the *difference* between any two
rows that are `k` positions apart is always the same rotation angle regardless of where they sit
in the sequence (reason 2, proven above).

---

## 5. Attention: The Core Innovation

This is the most important section. Take your time here.

### Intuition: The Library Analogy

```
You walk into a library to research "How do cats purr?"

YOUR QUESTION (Query):   "How do cats purr?"
BOOK TITLES  (Keys):     ["Cat Biology", "Dog Training", "Quantum Physics", "Feline Anatomy"]
BOOK CONTENT (Values):   [content_1, content_2, content_3, content_4]

Step 1: Compare your question to each title (dot product)
  "How do cats purr?" vs "Cat Biology"       → HIGH match (0.9)
  "How do cats purr?" vs "Dog Training"      → LOW match  (0.1)
  "How do cats purr?" vs "Quantum Physics"   → NO match   (0.0)
  "How do cats purr?" vs "Feline Anatomy"    → HIGH match (0.8)

Step 2: Normalize scores to sum to 1 (softmax)
  [0.9, 0.1, 0.0, 0.8] → [0.40, 0.04, 0.01, 0.35]  (simplified)

Step 3: Read books weighted by relevance (weighted sum of values)
  output = 0.40 × content_1 + 0.04 × content_2 + 0.01 × content_3 + 0.35 × content_4
  You mostly read "Cat Biology" and "Feline Anatomy", barely touch the others.
```

### Self-Attention: Every Word is Query, Key, AND Value

```
In self-attention, every word in the sentence plays ALL THREE roles:
  - It ASKS a question (Query): "who is relevant to me?"
  - It ADVERTISES itself (Key): "this is what I'm about"
  - It PROVIDES information (Value): "this is my content"

Sentence: "The cat sat on the mat"

For the word "sat":
  Query: "sat" asks "who did the sitting? where was it?"
  Key:   "sat" advertises "I'm an action verb about sitting"
  Value: "sat" provides its content/meaning vector

Attention computes: for each word, how much should it attend to every other word.
```

### The Q, K, V Projections: Why Not Use Raw Embeddings?

```
If we used raw embeddings directly as Q, K, and V, every word would play
the same role as query, key, and value. That's too limiting.

Instead, we LEARN three separate linear transformations:
  Q = X × W_Q   (what am I looking for?)
  K = X × W_K   (what do I advertise?)
  V = X × W_V   (what do I contain?)

Where:
  X ∈ ℝ^(T × d_model)     — input embeddings (T tokens, each d_model-dimensional)
  W_Q ∈ ℝ^(d_model × d_k)  — learned query projection
  W_K ∈ ℝ^(d_model × d_k)  — learned key projection
  W_V ∈ ℝ^(d_model × d_v)  — learned value projection

In the original paper: d_k = d_v = d_model / h = 512 / 8 = 64

This allows the model to LEARN different "views" of each word:
  - W_Q might learn to extract "what grammatical role am I?"
  - W_K might learn to extract "what grammatical role can I fill?"
  - W_V might learn to extract "what semantic meaning do I carry?"
```

### Scaled Dot-Product Attention: The Full Math

```
Step-by-step for sentence "I love cats" (T=3, d_k=4 for simplicity):

Step 1: Compute Q, K, V matrices
  X = [[x_I], [x_love], [x_cats]]    shape: (3, d_model)
  Q = X × W_Q                         shape: (3, d_k) = (3, 4)
  K = X × W_K                         shape: (3, d_k) = (3, 4)
  V = X × W_V                         shape: (3, d_v) = (3, 4)

Step 2: Compute attention scores (how much each word attends to each other)
  scores = Q × Kᵀ                     shape: (3, 3) — every pair!

  scores = ┌                         ┐
           │ q_I·k_I    q_I·k_love    q_I·k_cats   │
           │ q_love·k_I q_love·k_love q_love·k_cats│
           │ q_cats·k_I q_cats·k_love q_cats·k_cats│
           └                         ┘

  Example values:
  scores = ┌           ┐
           │ 2.1  1.5  0.3 │   ← "I" attends mostly to itself
           │ 1.8  3.2  2.7 │   ← "love" attends to itself and "cats"
           │ 0.5  2.9  3.5 │   ← "cats" attends to itself and "love"
           └           ┘

Step 3: Scale by √d_k (prevents softmax saturation)
  scaled = scores / √4 = scores / 2

  scaled = ┌              ┐
           │ 1.05  0.75  0.15 │
           │ 0.90  1.60  1.35 │
           │ 0.25  1.45  1.75 │
           └              ┘

Step 4: Apply softmax (each ROW sums to 1)
  weights = softmax(scaled, dim=-1)

  weights = ┌              ┐
            │ 0.44  0.33  0.18 │   ← "I" focuses: 44% self, 33% love, 18% cats
            │ 0.20  0.41  0.34 │   ← "love" focuses: 41% self, 34% cats
            │ 0.12  0.40  0.54 │   ← "cats" focuses: 54% self, 40% love
            └              ┘

Step 5: Compute output (weighted sum of values)
  output = weights × V                 shape: (3, d_v)

  output_cats = 0.12 × v_I + 0.40 × v_love + 0.54 × v_cats

  Now "cats" has a CONTEXT-AWARE representation:
    it's mostly itself (54%) but infused with meaning from "love" (40%)
    The model learned that "love cats" is a phrase where these words are related.
```

### Why Scale by √d_k? (Critical Detail)

```
The dot product q·k grows with the dimension d_k:

If q and k are random vectors with unit variance:
  E[q·k] = 0            (mean is 0)
  Var[q·k] = d_k         (variance GROWS with dimension!)

For d_k = 64:
  Dot products have variance 64 → standard deviation 8
  Some scores will be very large (like 16+) or very negative

Problem with large scores:
  softmax([16, 1, -10]) ≈ [0.9999, 0.0001, 0.0000]
  The attention is essentially HARD — picks one word, ignores others
  Gradients of softmax are near-zero in saturated regions → vanishing gradients

After scaling by √64 = 8:
  Scores have variance 1, reasonable range
  softmax works in its "sweet spot" where gradients flow well

Simple version: without scaling, attention becomes too "sharp" (picks one thing),
                with scaling, attention is "soft" (attends to multiple things).
```

### The Complete Formula

```
Attention(Q, K, V) = softmax(Q · Kᵀ / √d_k) · V

Shapes:
  Q ∈ ℝ^(T × d_k)         — T queries, each d_k-dimensional
  K ∈ ℝ^(S × d_k)         — S keys (S = T for self-attention)
  V ∈ ℝ^(S × d_v)         — S values
  Q · Kᵀ ∈ ℝ^(T × S)     — attention score matrix
  softmax(·) ∈ ℝ^(T × S)  — attention weight matrix (rows sum to 1)
  output ∈ ℝ^(T × d_v)    — context-enriched representations
```

```python
import torch
import torch.nn.functional as F

def scaled_dot_product_attention(Q, K, V, mask=None):
    """
    Q: (batch, ..., seq_len, d_k)
    K: (batch, ..., seq_len, d_k)
    V: (batch, ..., seq_len, d_v)
    mask: broadcastable to (batch, ..., seq_len, seq_len)
    """
    d_k = Q.size(-1)
    scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(d_k)

    if mask is not None:
        scores = scores.masked_fill(mask == 0, float('-inf'))

    attention_weights = F.softmax(scores, dim=-1)
    output = torch.matmul(attention_weights, V)
    return output, attention_weights
```

---

## 6. Multi-Head Attention: Seeing Multiple Relationships

### Why One Attention Head Isn't Enough

```
Consider: "The animal didn't cross the street because it was too tired."

What does "it" refer to? The model needs to figure out multiple things:
  1. COREFERENCE: "it" → "animal" (pronoun resolution)
  2. SYNTAX: "it" is the subject of "was tired"
  3. SEMANTICS: "tired" is a property of animate things → supports "animal"

A single attention head produces ONE set of weights — it can only capture
ONE type of relationship at a time. With 8 heads, different heads can
specialize in different relationships:

  Head 1: might learn coreference patterns
  Head 2: might learn syntactic dependencies
  Head 3: might learn semantic similarity
  Head 4: might learn positional proximity
  ...and so on.

This is empirically MUCH better than one big attention head with the same
total parameters.
```

### How Multi-Head Attention Works

```
d_model = 512, h = 8 heads → d_k = d_v = 512/8 = 64 per head

Step 1: Project input into h separate Q, K, V sets
  For head i (i = 1 to 8):
    Q_i = X × W_Q_i    shape: (T, 512) × (512, 64) → (T, 64)
    K_i = X × W_K_i    shape: (T, 512) × (512, 64) → (T, 64)
    V_i = X × W_V_i    shape: (T, 512) × (512, 64) → (T, 64)

Step 2: Run attention independently in each head
    head_i = Attention(Q_i, K_i, V_i)    shape: (T, 64)

Step 3: Concatenate all head outputs
    concat = [head_1 ; head_2 ; ... ; head_8]    shape: (T, 512)

Step 4: Final linear projection
    output = concat × W_O    shape: (T, 512) × (512, 512) → (T, 512)

W_O mixes information from all heads into a unified representation.
```

### Visualization

```
Input X (T, 512)
    │
    ├──→ [W_Q₁, W_K₁, W_V₁] → Attention → head₁ (T, 64)
    ├──→ [W_Q₂, W_K₂, W_V₂] → Attention → head₂ (T, 64)
    ├──→ [W_Q₃, W_K₃, W_V₃] → Attention → head₃ (T, 64)
    ├──→ [W_Q₄, W_K₄, W_V₄] → Attention → head₄ (T, 64)
    ├──→ [W_Q₅, W_K₅, W_V₅] → Attention → head₅ (T, 64)
    ├──→ [W_Q₆, W_K₆, W_V₆] → Attention → head₆ (T, 64)
    ├──→ [W_Q₇, W_K₇, W_V₇] → Attention → head₇ (T, 64)
    └──→ [W_Q₈, W_K₈, W_V₈] → Attention → head₈ (T, 64)
                                      │
                                      ▼
                            Concat → (T, 512)
                                      │
                                      ▼
                              W_O → (T, 512)
                                      │
                                      ▼
                               Output (T, 512)
```

### Compute Comparison

```
Single-head (d_k = 512):
  Attention matrix: (T × T) with d_k = 512 → same total compute
  But: ONE attention pattern per layer

Multi-head (h=8, d_k = 64):
  8 attention matrices: 8 × (T × T) with d_k = 64 → same total compute!
  But: EIGHT attention patterns per layer

Same cost, much richer representation. Pure win.
```

```python
class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads):
        super().__init__()
        assert d_model % num_heads == 0
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads

        self.W_Q = nn.Linear(d_model, d_model)
        self.W_K = nn.Linear(d_model, d_model)
        self.W_V = nn.Linear(d_model, d_model)
        self.W_O = nn.Linear(d_model, d_model)

    def forward(self, query, key, value, mask=None):
        batch_size = query.size(0)

        Q = self.W_Q(query).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        K = self.W_K(key).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        V = self.W_V(value).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)

        attn_output, attn_weights = scaled_dot_product_attention(Q, K, V, mask)

        attn_output = attn_output.transpose(1, 2).contiguous().view(
            batch_size, -1, self.d_model
        )
        return self.W_O(attn_output)
```

---

## 7. The Encoder: Understanding Input

The encoder's job: take the input sequence and produce a **rich, context-aware 
representation** that the decoder can use.

### Encoder Architecture

```
Input Tokens: ["I", "love", "cats"]
       │
       ▼
Token Embedding + Positional Encoding → (batch, T, 512)
       │
       ▼
┌─────────────────────────────────────────┐
│  ENCODER BLOCK (repeated N=6 times)     │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  Multi-Head Self-Attention        │  │
│  │  (each word attends to ALL words) │  │
│  └───────────────────────────────────┘  │
│              │                          │
│         Add & Norm (residual + LN)      │
│              │                          │
│  ┌───────────────────────────────────┐  │
│  │  Feed-Forward Network             │  │
│  │  (applied to each position)       │  │
│  └───────────────────────────────────┘  │
│              │                          │
│         Add & Norm (residual + LN)      │
│              │                          │
└─────────────────────────────────────────┘
       │
       ▼
Encoder Output: (batch, T, 512)
```

### What Self-Attention Does in the Encoder

```
Sentence: "The bank by the river was steep"

Before self-attention (layer 0):
  "bank" embedding = generic meaning (could be financial or geographical)

After self-attention:
  "bank" attends to "river", "steep"
  → representation shifts toward "river bank" meaning
  → the word "bank" is now CONTEXTUALLY disambiguated

This is the power of self-attention:
  Static word embeddings → Context-dependent representations
  "bank" near "money" → financial meaning
  "bank" near "river" → geographical meaning
```

### Bidirectional Attention in the Encoder

```
The encoder uses BIDIRECTIONAL attention:
  Every word can attend to every other word (past AND future).

For "The cat sat on the mat":
  "sat" sees: "The" ✓  "cat" ✓  "sat" ✓  "on" ✓  "the" ✓  "mat" ✓

No masking needed — the encoder's job is to UNDERSTAND, not GENERATE.
It sees the entire input at once.
```

### Stacking Encoder Layers

```
The paper uses N=6 encoder layers stacked on top of each other.

Why stack? Each layer captures increasingly abstract relationships:

Layer 1: Word-level relationships
  "New" attends to "York" → recognizes "New York" as a unit

Layer 2: Phrase-level relationships
  "New York" attends to "City" → recognizes "New York City"

Layer 3-4: Syntactic relationships
  Subject-verb agreement, clause boundaries

Layer 5-6: Semantic relationships
  Overall meaning, sentiment, intent

Each layer refines the representation using the output of the previous layer.
```

---

## 8. The Decoder: Generating Output

The decoder's job: generate the output sequence one token at a time, using both 
the encoder's understanding AND what's been generated so far.

### Decoder Architecture

```
Previously Generated Tokens: ["<start>", "J'aime"]
       │
       ▼
Token Embedding + Positional Encoding → (batch, T_out, 512)
       │
       ▼
┌───────────────────────────────────────────────┐
│  DECODER BLOCK (repeated N=6 times)           │
│                                               │
│  ┌─────────────────────────────────────────┐  │
│  │  MASKED Multi-Head Self-Attention       │  │
│  │  (each word attends only to PAST words) │  │
│  └─────────────────────────────────────────┘  │
│              │                                │
│         Add & Norm                            │
│              │                                │
│  ┌─────────────────────────────────────────┐  │
│  │  Multi-Head CROSS-Attention             │  │
│  │  Q from decoder, K & V from encoder     │  │
│  │  (decoder looks at the input)           │  │
│  └─────────────────────────────────────────┘  │
│              │                                │
│         Add & Norm                            │
│              │                                │
│  ┌─────────────────────────────────────────┐  │
│  │  Feed-Forward Network                   │  │
│  └─────────────────────────────────────────┘  │
│              │                                │
│         Add & Norm                            │
│              │                                │
└───────────────────────────────────────────────┘
       │
       ▼
Linear (512 → vocab_size) + Softmax → next token probabilities
```

### Masked Self-Attention: No Peeking at the Future!

```
The decoder generates tokens LEFT TO RIGHT (autoregressive):
  Step 1: Generate "J'aime"   (sees only <start>)
  Step 2: Generate "les"      (sees <start>, J'aime)
  Step 3: Generate "chats"    (sees <start>, J'aime, les)

During TRAINING, we have the full target sequence.
But we can't let position 2 see position 3 — that's cheating (leaking the answer).

Solution: CAUSAL MASK (upper triangular matrix of -infinity)

Before masking:                After masking:
┌                    ┐         ┌                         ┐
│ s₁₁  s₁₂  s₁₃  s₁₄│         │ s₁₁  -∞    -∞    -∞    │
│ s₂₁  s₂₂  s₂₃  s₂₄│   →     │ s₂₁  s₂₂  -∞    -∞    │
│ s₃₁  s₃₂  s₃₃  s₃₄│         │ s₃₁  s₃₂  s₃₃  -∞    │
│ s₄₁  s₄₂  s₄₃  s₄₄│         │ s₄₁  s₄₂  s₄₃  s₄₄  │
└                    ┘         └                         ┘

After softmax, -∞ becomes 0 (e^(-∞) = 0), so future positions are ignored.

This lets us TRAIN on all positions simultaneously (efficient!)
while simulating autoregressive generation (no future leakage).
```

### Why Masking is Brilliant for Training Efficiency

```
Without masking (naive approach):
  To train on a sentence of 100 words, you'd need 100 separate forward passes:
    Pass 1: input = [word_1]          → predict word_2
    Pass 2: input = [word_1, word_2]  → predict word_3
    ...
    Pass 99: input = [word_1, ..., word_99] → predict word_100

With masking:
  ONE forward pass processes ALL 100 predictions simultaneously!
  Position 1 predicts word_2 (sees only word_1 — mask hides the rest)
  Position 2 predicts word_3 (sees word_1, word_2)
  ...
  Position 99 predicts word_100 (sees everything)

  100x more efficient! This is called "teacher forcing."
```

---

## 9. Cross-Attention: Connecting Encoder and Decoder

### What Cross-Attention Does

```
Cross-attention is HOW the decoder "reads" the encoder's output.

Regular self-attention: Q, K, V all come from the same sequence
Cross-attention:        Q comes from DECODER, K and V come from ENCODER

When the decoder is about to generate "chats":
  Q = decoder's representation of "chats" position
  K = encoder's representations of ["I", "love", "cats"]
  V = encoder's representations of ["I", "love", "cats"]

  The decoder asks: "To generate this word, which parts of the input 
                     should I focus on?"

  Answer: high attention weight on "cats" (the word being translated)
```

### Cross-Attention Step by Step

```
Encoder output: representation of "I love cats" → E_out ∈ ℝ^(3, 512)
Decoder state:  processing position for next output → D ∈ ℝ^(2, 512)
                (already generated "<start> J'aime")

Cross-attention:
  Q = D × W_Q    (decoder asks questions)       shape: (2, 64)
  K = E_out × W_K  (encoder provides keys)      shape: (3, 64)
  V = E_out × W_V  (encoder provides values)    shape: (3, 64)

  scores = Q × Kᵀ / √d_k                        shape: (2, 3)

  For decoder position "J'aime":
    scores vs ["I", "love", "cats"] = [0.45, 0.48, 0.07]
    → "J'aime" is mostly translated from "I love"

  For the NEXT position (predicting "les"):
    scores vs ["I", "love", "cats"] = [0.05, 0.10, 0.85]
    → "les" is mostly related to "cats" (article for the noun)
```

### Three Types of Attention in the Transformer

```
┌─────────────────────────────────────────────────────────────────┐
│ TYPE              │ Q FROM    │ K,V FROM  │ WHERE USED          │
├───────────────────┼───────────┼───────────┼─────────────────────┤
│ Encoder           │ Encoder   │ Encoder   │ Encoder blocks      │
│ self-attention     │ (same)    │ (same)    │ (bidirectional)     │
├───────────────────┼───────────┼───────────┼─────────────────────┤
│ Decoder MASKED    │ Decoder   │ Decoder   │ Decoder blocks      │
│ self-attention     │ (same)    │ (same)    │ (causal mask)       │
├───────────────────┼───────────┼───────────┼─────────────────────┤
│ Cross-attention    │ Decoder   │ Encoder   │ Decoder blocks      │
│                   │           │ output    │ (connects them)     │
└───────────────────┴───────────┴───────────┴─────────────────────┘
```

---

## 10. Residual Connections & Layer Normalization

### Residual Connections (Skip Connections)

```
Without residual:
  output = SublayerFunction(x)    ← if gradients vanish in SublayerFunction,
                                     training dies for deep networks

With residual:
  output = x + SublayerFunction(x)
               ↑
               │ This is the "shortcut" / "skip connection"

Why this works:
  The gradient of "x + f(x)" with respect to x is "1 + f'(x)"
  Even if f'(x) ≈ 0 (vanishing gradient), the gradient is still ≈ 1
  Information and gradients can ALWAYS flow through the shortcut path.

  Think of it as: "at worst, a layer can be a no-op (identity function)
                   at best, it adds useful transformations"

For a 96-layer transformer:
  Without residuals: gradient must survive 96 multiplications → vanishes
  With residuals: gradient has a direct highway through all 96 layers
```

### Layer Normalization

```
LayerNorm normalizes across the FEATURE dimension (not the batch):

Given input x ∈ ℝ^(d_model):
  μ = mean(x)                          ← average of all 512 values
  σ = std(x)                           ← standard deviation
  x_norm = (x - μ) / (σ + ε)          ← normalize (ε ≈ 1e-5 for stability)
  output = γ × x_norm + β             ← scale and shift (learned parameters)

γ ∈ ℝ^(d_model), β ∈ ℝ^(d_model) are learned per-feature scale and bias.

Why LayerNorm?
  1. Stabilizes training: keeps activations in a reasonable range
  2. Speeds up convergence: inputs to each layer have consistent scale
  3. Works for variable batch sizes (unlike BatchNorm)
  4. Independent per sample (unlike BatchNorm which needs batch statistics)
```

### Post-LN vs Pre-LN

```
Post-LN (original paper):
  output = LayerNorm(x + SubLayer(x))
  
  Issue: LayerNorm is AFTER the residual → gradients can still be unstable
  Need careful learning rate warmup to avoid divergence

Pre-LN (GPT-2 and all modern models):
  output = x + SubLayer(LayerNorm(x))
  
  Advantage: much more stable training, no warmup needed
  The input to each sub-layer is always well-normalized

Almost ALL modern transformers use Pre-LN. The original paper used Post-LN.
```

---

## 11. Feed-Forward Network: The Knowledge Store

### Architecture

```
FFN(x) = W₂ · ReLU(W₁ · x + b₁) + b₂

Dimensions:
  W₁ ∈ ℝ^(d_model × d_ff) = ℝ^(512 × 2048)    ← expand 4x
  W₂ ∈ ℝ^(d_ff × d_model) = ℝ^(2048 × 512)    ← compress back
  d_ff = 4 × d_model = 2048

Flow:
  x (512) → expand to 2048 → ReLU → compress to 512

This is applied INDEPENDENTLY to each position (each token separately).
No interaction between tokens here — that's attention's job.
```

### Why 4x Expansion? The Key-Value Memory Interpretation

```
Research from Anthropic and others shows FFN layers act as MEMORY:

W₁ (the "keys"):
  Each ROW of W₁ is a "pattern detector"
  Row j fires (high activation) when the input matches pattern j
  2048 rows = 2048 stored patterns

ReLU (the "gate"):
  Only patterns with positive activation pass through
  Sparse activation: typically only ~10% of neurons fire

W₂ (the "values"):
  Each COLUMN of W₂ is the "information" associated with pattern j
  When pattern j fires, its associated information is retrieved

Example:
  Pattern 127 in W₁ might detect "this token is a European capital"
  The corresponding column 127 in W₂ might encode geographical knowledge
  When input = "Paris", pattern 127 fires → geographical info retrieved

This is why:
  - Bigger FFN = more memories = better model
  - ~70% of transformer parameters are in FFN layers
  - Removing specific FFN neurons removes specific knowledge (proven empirically)
```

### Modern Variants: SwiGLU

```
Modern transformers (LLaMA 2+, Mistral) use SwiGLU instead of ReLU:

FFN_SwiGLU(x) = (Swish(x · W₁) ⊙ (x · W₃)) · W₂

Where:
  Swish(x) = x · sigmoid(x)    ← smooth version of ReLU
  ⊙ = element-wise multiplication (gating)
  W₃ is an additional "gate" projection

This uses ~50% more parameters per layer but performs significantly better.
To keep total params the same, d_ff is reduced from 4x to ~2.7x.
```

```python
class FeedForward(nn.Module):
    def __init__(self, d_model, d_ff, dropout=0.1):
        super().__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        return self.linear2(self.dropout(F.relu(self.linear1(x))))
```

---

## 12. Training the Transformer

### Training Objective: Next Token Prediction (for decoder)

```
Target sentence: "<start> J'aime les chats <end>"

The model predicts the NEXT token at each position:
  Input:   <start>  J'aime  les    chats
  Target:  J'aime   les     chats  <end>

At each position, the model outputs a probability distribution over 
the entire vocabulary (e.g., 32000 words).

Loss = Cross-Entropy between predicted probabilities and true next token
     = -log(P(correct_token))

If the model assigns P("les") = 0.8 at position 3:
  loss = -log(0.8) = 0.22  (low loss, good prediction)

If the model assigns P("les") = 0.01 at position 3:
  loss = -log(0.01) = 4.6  (high loss, bad prediction)
```

### Label Smoothing

```
Standard target: one-hot vector [0, 0, ..., 1, ..., 0, 0]
  All probability on the correct token, zero on everything else.
  This makes the model overconfident.

Label smoothing (ε = 0.1, used in the paper):
  Target: [ε/V, ε/V, ..., (1-ε), ..., ε/V, ε/V]
  Spread ε = 0.1 of the probability mass across all tokens
  Correct token gets 0.9 instead of 1.0

  Why? Prevents overconfidence, improves generalization.
  The model learns "I'm 90% sure it's 'les', but other words aren't impossible."
```

### Learning Rate Schedule: Warmup + Decay

```
The paper uses a specific learning rate schedule:

lr = d_model^(-0.5) × min(step^(-0.5), step × warmup_steps^(-1.5))

In plain English:
  1. WARMUP (first 4000 steps): linearly increase LR from ~0 to peak
     Why? Random initial weights → large gradients → need small LR at start
     
  2. DECAY (after 4000 steps): decrease LR proportional to 1/√step
     Why? As model converges, need smaller updates to fine-tune

Visual:

  LR │        ╱╲
     │       ╱  ╲
     │      ╱    ╲
     │     ╱      ╲
     │    ╱        ╲
     │   ╱          ╲──────────
     │  ╱            slowly decays
     │ ╱
     └──────────────────────────── step
         warmup    decay
```

### Optimizer: Adam

```
The paper uses Adam optimizer:
  β₁ = 0.9    (momentum: running average of gradients)
  β₂ = 0.98   (RMS: running average of squared gradients)
  ε = 10⁻⁹    (numerical stability)

Adam adapts the learning rate PER PARAMETER:
  Parameters with large gradients → effectively smaller LR (don't overshoot)
  Parameters with small gradients → effectively larger LR (move faster)
```

### Dropout (Regularization)

```
The paper applies dropout (p = 0.1) in three places:
  1. After positional encoding is added to embeddings
  2. After each sub-layer (attention, FFN) before the residual addition
  3. After the attention weights (before multiplying with V)

Dropout randomly sets 10% of values to zero during training.
Forces the model to not rely on any single neuron → better generalization.
Disabled during inference.
```

### Batching and Parallelism

```
Training batch:
  ~25,000 source + target tokens per batch
  Sentences of similar length grouped together (to minimize padding waste)

The key advantage over RNNs:
  RNN: for a batch of 100 sentences of length 50:
    50 sequential steps × 100 parallel across batch = 50 steps total
    
  Transformer: same batch:
    1 forward pass handles all positions simultaneously
    All 50 positions computed in parallel for all 100 sentences
    
  This is why transformers train 10-100x faster!
```

---

## 13. Inference: How Generation Actually Works

### Autoregressive Generation

```
Translation: "I love cats" → "J'aime les chats"

Step 0: Encode the input ONCE
  encoder_output = Encoder("I love cats")   → (3, 512) — computed once, reused

Step 1: Start with <start> token
  decoder_input = [<start>]
  output = Decoder([<start>], encoder_output)
  next_token = argmax(output[-1])   → "J'aime"

Step 2: Feed back the generated token
  decoder_input = [<start>, J'aime]
  output = Decoder([<start>, J'aime], encoder_output)
  next_token = argmax(output[-1])   → "les"

Step 3: Continue
  decoder_input = [<start>, J'aime, les]
  output = Decoder([<start>, J'aime, les], encoder_output)
  next_token = argmax(output[-1])   → "chats"

Step 4: Continue
  decoder_input = [<start>, J'aime, les, chats]
  output = Decoder([<start>, J'aime, les, chats], encoder_output)
  next_token = argmax(output[-1])   → <end>

STOP when <end> is generated.
```

### Greedy vs Beam Search

```
GREEDY DECODING (what we showed above):
  Always pick the highest-probability token.
  Fast but can miss better overall sequences.
  
  Example: P("The") = 0.6, P("A") = 0.4
  Greedy picks "The" → but "A beautiful day" might be better overall

BEAM SEARCH (used in the paper):
  Keep top-B candidates (B = beam width, paper uses B=4) at each step.
  
  Step 1: Top 4 first tokens:
    Beam 1: "J'aime"  (log-prob: -0.2)
    Beam 2: "Je"      (log-prob: -0.8)
    Beam 3: "J'adore" (log-prob: -1.1)
    Beam 4: "Les"     (log-prob: -2.0)

  Step 2: For each beam, try all next tokens, keep best 4 overall:
    Beam 1: "J'aime les"     (log-prob: -0.5)
    Beam 2: "J'adore les"    (log-prob: -1.3)
    Beam 3: "J'aime des"     (log-prob: -1.4)
    Beam 4: "Je aime les"    (log-prob: -1.5)

  Continue until all beams produce <end>.
  Return the highest-scoring complete sequence.

  The paper also uses LENGTH PENALTY:
    score = log_prob / length^α    (α = 0.6)
    Without this, shorter sequences are unfairly favored (fewer terms in log-prob).
```

### KV Cache: Making Inference Fast

```
Problem: at step T, the decoder recomputes attention for ALL T positions.
  Step 1: compute attention for 1 token
  Step 2: compute attention for 2 tokens  (token 1 recomputed!)
  Step 3: compute attention for 3 tokens  (tokens 1,2 recomputed!)
  ...
  Step 100: compute attention for 100 tokens (99 tokens recomputed!)
  Total: 1+2+3+...+100 = 5050 attention computations → O(T²)

Solution: KV CACHE
  Store the K and V vectors from all previous steps.
  At step T, only compute Q, K, V for the NEW token.
  Append new K, V to the cache. Use cached K, V for attention.

  Step 1: compute K₁,V₁, store in cache. Attention over [K₁],[V₁]
  Step 2: compute K₂,V₂, append to cache. Attention over [K₁,K₂],[V₁,V₂]
  Step 3: compute K₃,V₃, append to cache. Attention over [K₁,K₂,K₃],[V₁,V₂,V₃]
  ...

  Each step only computes ONE new K,V pair + attention with the growing cache.
  Total: 1+1+1+...+1 (for new K,V) + 1+2+3+...+T (for attention) = O(T²) attention
  BUT: the K,V computation drops from O(T²) to O(T). Major practical speedup.
```

---

## 14. Full Architecture Walk-Through (Putting It All Together)

### The Complete Original Transformer

```
┌─────────────── ENCODER ───────────────┐   ┌────────────── DECODER ──────────────┐
│                                       │   │                                     │
│  Input: "I love cats"                 │   │  Target: "<s> J'aime les chats"     │
│         │                             │   │           │                         │
│         ▼                             │   │           ▼                         │
│  ┌──────────────┐                     │   │  ┌──────────────┐                   │
│  │ Token Embed  │                     │   │  │ Token Embed  │                   │
│  │ + Pos Encode │                     │   │  │ + Pos Encode │                   │
│  └──────┬───────┘                     │   │  └──────┬───────┘                   │
│         │                             │   │         │                           │
│         ▼                             │   │         ▼                           │
│  ┌─────────────────────┐              │   │  ┌─────────────────────┐            │
│  │ Multi-Head          │              │   │  │ MASKED Multi-Head   │            │
│  │ Self-Attention      │              │   │  │ Self-Attention      │            │
│  │ (bidirectional)     │              │   │  │ (causal)            │            │
│  └─────────┬───────────┘              │   │  └─────────┬───────────┘            │
│         Add & Norm                    │   │         Add & Norm                  │
│            │                          │   │            │                        │
│  ┌─────────┴───────────┐              │   │  ┌─────────┴───────────┐            │
│  │ Feed-Forward        │              │   │  │ Cross-Attention     │            │
│  │ Network             │              │   │  │ Q=decoder, K,V=enc  │◄── enc_out │
│  └─────────┬───────────┘              │   │  └─────────┬───────────┘            │
│         Add & Norm                    │   │         Add & Norm                  │
│            │                          │   │            │                        │
│         (× 6 layers)                  │   │  ┌─────────┴───────────┐            │
│            │                          │   │  │ Feed-Forward        │            │
│            ▼                          │   │  │ Network             │            │
│     ENCODER OUTPUT ──────────────────────▶│  └─────────┬───────────┘            │
│     (3, 512)                          │   │         Add & Norm                  │
│                                       │   │            │                        │
└───────────────────────────────────────┘   │         (× 6 layers)               │
                                            │            │                        │
                                            │            ▼                        │
                                            │  ┌──────────────────┐              │
                                            │  │ Linear (512→V)   │              │
                                            │  │ Softmax          │              │
                                            │  └────────┬─────────┘              │
                                            │           │                        │
                                            │           ▼                        │
                                            │  Next token probabilities          │
                                            │  P("les") = 0.82                  │
                                            │  P("des") = 0.05                  │
                                            │  P("un")  = 0.03                  │
                                            │  ...                              │
                                            └─────────────────────────────────────┘
```

### Data Flow Example

```
Let's trace "I love cats" → "J'aime les chats" through the ENTIRE model:

═══════════════ ENCODER ═══════════════

1. Tokenize: "I love cats" → [40, 1567, 9823]

2. Embed + scale: 
   [40, 1567, 9823] → [[0.02, ...], [0.15, ...], [0.08, ...]]  × √512
   Shape: (3, 512)

3. Add positional encoding:
   x = embeddings + PE[0:3]
   Shape: still (3, 512)

4. Encoder Layer 1:
   a. Self-attention: each token attends to all 3 tokens
      "cats" learns it's the OBJECT of "love"
   b. Add & Norm: stabilize
   c. FFN: refine each token's representation independently
   d. Add & Norm: stabilize
   Shape: still (3, 512) — dimensions never change within the encoder!

5. Encoder Layers 2-6: progressively deeper understanding
   By layer 6, each token has a rich, contextual representation.

6. Encoder output: (3, 512) — sent to decoder's cross-attention

═══════════════ DECODER (generating "les") ═══════════════

7. Input to decoder: ["<start>", "J'aime"] (already generated)
   Embed + scale + PE → shape: (2, 512)

8. Decoder Layer 1:
   a. MASKED self-attention: "J'aime" attends to "<start>" and itself
      (mask prevents it from seeing future tokens)
   b. Add & Norm
   c. Cross-attention: Q from decoder (2, 512), K,V from encoder (3, 512)
      "J'aime" attends heavily to "I" and "love" in the encoder
      Position 2 (next word) starts attending to "cats"
   d. Add & Norm
   e. FFN
   f. Add & Norm
   Shape: (2, 512)

9. Decoder Layers 2-6: deeper integration of encoder context

10. Final linear + softmax:
    Take the LAST position's output → (512,)
    Linear: (512,) → (32000,)  — score for each vocabulary token
    Softmax: → probabilities
    P("les") = 0.82  ← highest → output "les"
```

---

## 15. Parameter Count & Computation Cost

### Counting Parameters

```
Original Transformer: d_model=512, d_ff=2048, h=8, N=6, V=37000

EMBEDDING LAYERS:
  Source embedding:   V × d_model = 37000 × 512 = 18.9M
  Target embedding:   V × d_model = 37000 × 512 = 18.9M
  (often shared / tied weights)

PER ENCODER LAYER:
  Multi-head attention:
    W_Q: 512 × 512 = 262K
    W_K: 512 × 512 = 262K
    W_V: 512 × 512 = 262K
    W_O: 512 × 512 = 262K
    Total attention: ~1.05M

  Feed-forward:
    W₁: 512 × 2048 = 1.05M
    b₁: 2048
    W₂: 2048 × 512 = 1.05M
    b₂: 512
    Total FFN: ~2.1M

  Layer norms: 2 × (512 + 512) = 2K
  
  Total per encoder layer: ~3.15M

PER DECODER LAYER:
  Masked self-attention: ~1.05M
  Cross-attention: ~1.05M (separate Q, K, V, O projections)
  Feed-forward: ~2.1M
  Layer norms: 3 × (512 + 512) = 3K
  Total per decoder layer: ~4.2M

FULL MODEL:
  Embeddings:       ~18.9M (shared) or ~37.8M (separate)
  Encoder (6 layers): 6 × 3.15M = 18.9M
  Decoder (6 layers): 6 × 4.2M  = 25.2M
  Final linear:     512 × 37000 = 18.9M (often tied with embedding)
  ──────────────────────────────────
  TOTAL: ~65M parameters (base model)
         ~213M parameters (big model: d_model=1024, d_ff=4096, h=16, N=6)
```

### Compute Cost: The O(T^2) Problem

```
Self-attention computation:
  QKᵀ matrix multiplication: O(T² × d_model)
  Where T = sequence length

For T = 512 (original paper):  manageable
For T = 2048 (GPT-2):          4× more compute
For T = 128K (Claude, GPT-4):  62,500× more compute!

This quadratic scaling is the fundamental limitation of transformers.
(Various solutions exist: Flash Attention, sparse attention, etc.)

FLOPs for forward pass (approximate):
  Attention: 2 × N × T² × d_model
  FFN:       2 × N × T × d_model × d_ff
  For T < d_ff (typical): FFN dominates
  For T > d_ff: attention dominates (the quadratic bottleneck)
```

---

## 16. What Came After: BERT, GPT, and Modern LLMs

### Three Families from One Architecture

```
The original transformer is ENCODER-DECODER (for translation).
Three specialized variants emerged:

┌─────────────────────────────────────────────────────────────────┐
│ VARIANT          │ USES           │ MODELS      │ TASK         │
├──────────────────┼────────────────┼─────────────┼──────────────┤
│ Encoder-only     │ Encoder only   │ BERT,       │ Understand   │
│                  │ (bidirectional)│ RoBERTa     │ text         │
├──────────────────┼────────────────┼─────────────┼──────────────┤
│ Decoder-only     │ Decoder only   │ GPT, Claude,│ Generate     │
│                  │ (causal)       │ LLaMA       │ text         │
├──────────────────┼────────────────┼─────────────┼──────────────┤
│ Encoder-Decoder  │ Both           │ T5, BART,   │ Translate,   │
│                  │ (full arch)    │ Flan-T5     │ summarize    │
└──────────────────┴────────────────┴─────────────┴──────────────┘

WINNER (2024+): DECODER-ONLY dominates
  - GPT-4, Claude, LLaMA, Mistral, Gemini — all decoder-only
  - Simpler architecture, scales better
  - Can do everything (generation, understanding, translation)
  - No cross-attention needed (no encoder to attend to)
```

### BERT (2018): Encoder-Only

```
Key idea: MASKED LANGUAGE MODELING
  Input:  "The [MASK] sat on the [MASK]"
  Output: predict "cat" and "mat"

  Bidirectional: sees both left AND right context
  Great for: classification, NER, sentiment analysis, question answering
  
  NOT good for: generation (can't generate text autoregressively)

Architecture differences from original transformer:
  - Encoder only (no decoder, no cross-attention, no causal mask)
  - Learned positional embeddings (not sinusoidal)
  - [CLS] token for classification, [SEP] for sentence boundaries
  - Segment embeddings (distinguish sentence A from sentence B)
```

### GPT (2018-2024): Decoder-Only

```
Key idea: AUTOREGRESSIVE LANGUAGE MODELING
  Input:  "The cat sat on the"
  Output: predict "mat"

  Unidirectional: only sees LEFT context (causal mask)
  Great for: everything (generation, classification, reasoning, coding)

Architecture differences:
  - Decoder only (no encoder, no cross-attention)
  - Causal mask always applied
  - Pre-LN (Layer Norm before attention/FFN, not after)
  - Learned positional embeddings → RoPE (GPT-4 / modern)
  - Scale: GPT-3 = 175B params, GPT-4 = rumored 1.8T (mixture of experts)
```

### Key Architectural Improvements Since 2017

```
1. Pre-LN (GPT-2, 2019): LayerNorm before sub-layers, not after → stable training
2. RoPE (2021): Rotary position embeddings → better length generalization
3. GQA (2023): Grouped-Query Attention → cheaper KV cache
4. SwiGLU (2022): Better FFN activation → improved performance
5. Flash Attention (2022): Same math, 2-4x faster → enables long sequences
6. RMSNorm (2023): Simplified LayerNorm (no mean subtraction) → faster
7. Mixture of Experts (2022+): Only activate subset of FFN → more params, same compute

Modern transformer (LLaMA-3 style):
  - Pre-RMSNorm (not LayerNorm, not Post-LN)
  - RoPE (not sinusoidal, not learned)
  - GQA (not full MHA)
  - SwiGLU FFN (not ReLU FFN)
  - No bias terms in linear layers
  - Flash Attention for training and inference
```

---

## 17. Common Confusions & FAQ

### Q: Why is it called "self-attention" if there are Q, K, V?

```
"Self" means the Q, K, and V all come from the SAME sequence.
In self-attention on "I love cats":
  Q = projection of ["I", "love", "cats"]
  K = projection of ["I", "love", "cats"]  ← same input!
  V = projection of ["I", "love", "cats"]  ← same input!

Compare with CROSS-attention:
  Q = decoder's representation
  K = encoder's representation   ← different input!
  V = encoder's representation   ← different input!
```

### Q: Don't the Q, K, V projections have the same input, so why three?

```
Yes, for self-attention, Q, K, V start from the same X.
But they're projected through DIFFERENT weight matrices (W_Q, W_K, W_V).

Think of it as: the same person (token) plays three different roles.
  As a QUERY: "What am I looking for?" (W_Q extracts this)
  As a KEY:   "What do I represent?"   (W_K extracts this)
  As a VALUE: "What can I contribute?" (W_V extracts this)

W_Q, W_K, W_V are learned to extract DIFFERENT aspects of the input.
If they were all the same, attention would just be similarity × identity = useless.
```

### Q: What if I remove positional encoding?

```
Without PE, the model treats input as a BAG OF WORDS (no order).
"Dog bites man" and "Man bites dog" produce identical representations.

Experimentally: removing PE degrades translation BLEU by 1-2 points.
Less than you'd expect! Self-attention can partially infer order from
semantic context ("The" usually starts a sentence, verbs follow nouns, etc.)
But it can't handle word-order-dependent tasks reliably.
```

### Q: Why does FFN use 4x expansion?

```
The original paper set d_ff = 4 × d_model without much justification.
Later research showed:
  - Too small: not enough capacity to store "knowledge"
  - Too large: diminishing returns, waste of parameters
  - 4x is a good sweet spot empirically

Modern models tune this ratio:
  LLaMA 2: d_ff = 2.68 × d_model (with SwiGLU, which has 3 weight matrices)
  Total FFN params similar to 4x expansion with 2 weight matrices
```

### Q: Why does attention use softmax? Why not sigmoid or normalization?

```
Softmax has two key properties:
  1. Outputs are positive and sum to 1 → interpretable as probability/weight
  2. Amplifies large differences → creates clear "focus"

  scores = [3.0, 1.0, 0.5]
  softmax = [0.84, 0.11, 0.05]   ← clear winner
  sigmoid = [0.95, 0.73, 0.62]   ← all are "high", no clear focus
  l1-norm = [0.67, 0.22, 0.11]   ← similar to softmax but less peaky

Softmax creates a proper ATTENTION DISTRIBUTION where the model
clearly focuses on certain tokens (like a spotlight, not a floodlight).
```

### Q: What does "attention is all you need" actually mean?

```
It means: you don't need recurrence (RNNs) or convolutions (CNNs) to build
a state-of-the-art sequence model. Attention alone + simple feed-forward layers
is sufficient.

This was SURPRISING in 2017:
  - RNNs were considered essential for sequence modeling
  - Convolutions were considered essential for local patterns
  - Attention was just a helper mechanism added to RNNs

The paper proved: attention mechanisms are sufficient as the PRIMARY 
computational building block. Everything else is optional.
```

### Q: Is the transformer fully parallel?

```
TRAINING: Yes! All positions are computed simultaneously.
  - Unlike RNNs which must process sequentially
  - This is why transformers train 10-100x faster

INFERENCE (generation): NO! Must generate one token at a time.
  - Each new token depends on all previous tokens
  - Position T+1 can't be computed until position T is generated
  - This is the INHERENT sequential bottleneck of autoregressive models
  - Speculative decoding partially addresses this (draft model predicts ahead)
```

---

## 18. Interview Questions

### Foundational

```
Q: Explain the transformer architecture in 2 minutes.
A: The transformer processes sequences using self-attention instead of recurrence.
   Input tokens are embedded, positional info is added, then N stacked blocks
   process them. Each block has multi-head self-attention (every token attends 
   to every other token to build context-aware representations) followed by a 
   feed-forward network (stores learned knowledge). Residual connections and
   layer normalization keep training stable. The encoder builds understanding
   of the input; the decoder generates output autoregressively using masked
   self-attention (no future peeking) and cross-attention (reading the encoder).
   Key innovation: O(1) path length between any two tokens (vs O(T) for RNNs),
   and fully parallel training.

Q: What is the time complexity of self-attention? Why is it a problem?
A: O(T² × d) where T is sequence length. For T=128K, the attention matrix
   has 16 billion entries. This makes long-context models expensive.
   Solutions: Flash Attention (same math, better GPU memory usage),
   sparse attention (attend to subset), or linear attention approximations.

Q: Why use multi-head attention instead of single-head?
A: Same compute cost, but each head can specialize in different relationship
   types (syntax, semantics, coreference). Empirically much better.
   8 heads with d_k=64 beat 1 head with d_k=512.

Q: Explain why positional encoding is necessary.
A: Self-attention is permutation-invariant — it treats input as a set, not
   a sequence. Without position info, "dog bites man" = "man bites dog".
   Positional encoding adds position-dependent signals so the model can
   distinguish word order.
```

### Intermediate

```
Q: What's the difference between Pre-LN and Post-LN?
A: Post-LN (original): LN after residual → gradient magnitudes vary across 
   layers → needs careful warmup. Pre-LN (modern): LN before sub-layer → 
   gradients are well-conditioned → trains more stably without warmup.

Q: Why scale dot products by √d_k?
A: Dot products of d_k-dimensional random vectors have variance d_k.
   Large scores → softmax saturation → near-zero gradients.
   Dividing by √d_k normalizes variance to 1, keeping softmax in its 
   gradient-friendly regime.

Q: How does the causal mask enable parallel training?
A: During training, all target positions are processed simultaneously.
   The mask adds -∞ to attention scores for future positions, so after
   softmax they become 0. Position t only sees tokens 1..t, simulating
   autoregressive generation without actual sequential computation.
   This is called teacher forcing.

Q: What happens if you remove the residual connections?
A: Deep transformers (6+ layers) become untrainable. Gradients must flow
   through the network — residuals provide a "gradient highway" that 
   bypasses each layer. Without them, the gradient signal degrades 
   exponentially with depth (vanishing gradient problem).

Q: What is the KV cache and why is it important for inference?
A: During autoregressive generation, each new token recomputes attention
   over ALL previous tokens. The KV cache stores computed K and V tensors
   from previous steps. New step: compute K,V for new token only, append
   to cache, attend over the full cache. Saves recomputation but uses
   memory proportional to sequence_length × num_layers × d_model.
```

### Advanced

```
Q: Compare encoder-only, decoder-only, and encoder-decoder transformers.
A: Encoder-only (BERT): bidirectional attention, good for understanding/
   classification. Decoder-only (GPT): causal attention, good for generation,
   won the scaling game because generation subsumes understanding.
   Encoder-decoder (T5): best for sequence-to-sequence (translation) but
   more complex, harder to scale. Decoder-only dominates 2024+ because
   it's simpler and scales better.

Q: Why did decoder-only win over encoder-decoder?
A: Three reasons: (1) Simpler — no cross-attention mechanism, fewer components.
   (2) Scaling — single unified model with one objective (next token prediction)
   scales more predictably. (3) Flexibility — can handle understanding tasks by
   framing them as generation (classification = "generate the class label").
   (4) Engineering simplicity — one codebase, one training pipeline, one inference
   engine, easier to optimize.

Q: How does Flash Attention work at a high level?
A: Standard attention materializes the full T×T attention matrix in GPU HBM 
   (slow memory). Flash Attention tiles the computation: loads blocks of Q, K, V
   into fast SRAM, computes partial attention, and accumulates results without
   ever storing the full T×T matrix. Same math, same output — but 2-4x faster
   and O(T) memory instead of O(T²). The trick is using the online softmax
   algorithm to compute softmax incrementally over blocks.

Q: Explain RoPE (Rotary Positional Embedding) and why it replaced sinusoidal.
A: RoPE rotates Q and K vectors by a position-dependent angle before the dot
   product. For positions m and n: q_m · k_n = f(x_m, x_n, m-n). Position
   info is encoded in the RELATIVE angle between Q and K, not as an additive
   signal. Advantages: (1) naturally encodes relative position, (2) decays with
   distance, (3) can extrapolate to longer sequences with techniques like NTK-aware
   interpolation or YaRN.

Q: What is Mixture of Experts (MoE) and how does it relate to transformers?
A: MoE replaces the dense FFN with multiple "expert" FFNs. A router network
   selects top-k experts (usually k=2) for each token. Result: model has many
   more total parameters but only activates a subset per token. Mixtral 8x7B
   has 46.7B total params but only 12.9B active per token. Trains like a 
   13B model, performs like a 40B+ model. This is how GPT-4 is rumored to work.
```

---

## 19. Complete PyTorch Implementation

A minimal but complete implementation of the original Transformer.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads, dropout=0.1):
        super().__init__()
        assert d_model % num_heads == 0
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads

        self.W_Q = nn.Linear(d_model, d_model)
        self.W_K = nn.Linear(d_model, d_model)
        self.W_V = nn.Linear(d_model, d_model)
        self.W_O = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, query, key, value, mask=None):
        batch_size = query.size(0)

        Q = self.W_Q(query).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        K = self.W_K(key).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        V = self.W_V(value).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)

        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)

        if mask is not None:
            scores = scores.masked_fill(mask == 0, float('-inf'))

        attn_weights = self.dropout(F.softmax(scores, dim=-1))
        attn_output = torch.matmul(attn_weights, V)

        attn_output = (
            attn_output.transpose(1, 2)
            .contiguous()
            .view(batch_size, -1, self.d_model)
        )
        return self.W_O(attn_output)


class FeedForward(nn.Module):
    def __init__(self, d_model, d_ff, dropout=0.1):
        super().__init__()
        self.linear1 = nn.Linear(d_model, d_ff)
        self.linear2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        return self.linear2(self.dropout(F.relu(self.linear1(x))))


class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000, dropout=0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class EncoderLayer(nn.Module):
    def __init__(self, d_model, num_heads, d_ff, dropout=0.1):
        super().__init__()
        self.self_attn = MultiHeadAttention(d_model, num_heads, dropout)
        self.ffn = FeedForward(d_model, d_ff, dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, x, src_mask=None):
        attn_output = self.self_attn(x, x, x, src_mask)
        x = self.norm1(x + self.dropout1(attn_output))
        ff_output = self.ffn(x)
        x = self.norm2(x + self.dropout2(ff_output))
        return x


class DecoderLayer(nn.Module):
    def __init__(self, d_model, num_heads, d_ff, dropout=0.1):
        super().__init__()
        self.self_attn = MultiHeadAttention(d_model, num_heads, dropout)
        self.cross_attn = MultiHeadAttention(d_model, num_heads, dropout)
        self.ffn = FeedForward(d_model, d_ff, dropout)
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.norm3 = nn.LayerNorm(d_model)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)
        self.dropout3 = nn.Dropout(dropout)

    def forward(self, x, encoder_output, src_mask=None, tgt_mask=None):
        attn_output = self.self_attn(x, x, x, tgt_mask)
        x = self.norm1(x + self.dropout1(attn_output))

        cross_output = self.cross_attn(x, encoder_output, encoder_output, src_mask)
        x = self.norm2(x + self.dropout2(cross_output))

        ff_output = self.ffn(x)
        x = self.norm3(x + self.dropout3(ff_output))
        return x


class Transformer(nn.Module):
    def __init__(
        self,
        src_vocab_size,
        tgt_vocab_size,
        d_model=512,
        num_heads=8,
        num_layers=6,
        d_ff=2048,
        max_len=5000,
        dropout=0.1,
    ):
        super().__init__()
        self.d_model = d_model

        self.src_embedding = nn.Embedding(src_vocab_size, d_model)
        self.tgt_embedding = nn.Embedding(tgt_vocab_size, d_model)
        self.pos_encoding = PositionalEncoding(d_model, max_len, dropout)

        self.encoder_layers = nn.ModuleList([
            EncoderLayer(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])
        self.decoder_layers = nn.ModuleList([
            DecoderLayer(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])

        self.output_projection = nn.Linear(d_model, tgt_vocab_size)
        self.dropout = nn.Dropout(dropout)

    def encode(self, src, src_mask=None):
        x = self.pos_encoding(self.src_embedding(src) * math.sqrt(self.d_model))
        for layer in self.encoder_layers:
            x = layer(x, src_mask)
        return x

    def decode(self, tgt, encoder_output, src_mask=None, tgt_mask=None):
        x = self.pos_encoding(self.tgt_embedding(tgt) * math.sqrt(self.d_model))
        for layer in self.decoder_layers:
            x = layer(x, encoder_output, src_mask, tgt_mask)
        return x

    def forward(self, src, tgt, src_mask=None, tgt_mask=None):
        encoder_output = self.encode(src, src_mask)
        decoder_output = self.decode(tgt, encoder_output, src_mask, tgt_mask)
        return self.output_projection(decoder_output)

    @staticmethod
    def generate_causal_mask(size):
        """Upper triangular mask: prevents attending to future positions."""
        mask = torch.triu(torch.ones(size, size), diagonal=1).bool()
        return ~mask  # True = attend, False = mask


# --- Usage Example ---
def demo():
    model = Transformer(
        src_vocab_size=32000,
        tgt_vocab_size=32000,
        d_model=512,
        num_heads=8,
        num_layers=6,
        d_ff=2048,
    )

    src = torch.randint(0, 32000, (2, 10))   # batch=2, src_len=10
    tgt = torch.randint(0, 32000, (2, 15))   # batch=2, tgt_len=15

    tgt_mask = Transformer.generate_causal_mask(15).unsqueeze(0).unsqueeze(0)

    logits = model(src, tgt, tgt_mask=tgt_mask)
    print(f"Output shape: {logits.shape}")     # (2, 15, 32000)
    print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}")


if __name__ == "__main__":
    demo()
```

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────────────────────┐
│                    TRANSFORMER CHEAT SHEET                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CORE EQUATION:                                                  │
│    Attention(Q,K,V) = softmax(QKᵀ/√d_k) · V                    │
│                                                                  │
│  HYPERPARAMETERS (original paper):                               │
│    d_model = 512      (embedding / hidden dimension)             │
│    d_ff    = 2048     (FFN inner dimension = 4×d_model)          │
│    h       = 8        (attention heads)                          │
│    d_k     = 64       (per-head dimension = d_model/h)           │
│    N       = 6        (encoder layers = decoder layers)          │
│    dropout = 0.1                                                 │
│    warmup  = 4000 steps                                          │
│                                                                  │
│  ATTENTION TYPES:                                                │
│    Encoder self-attn:  Q,K,V = encoder   (bidirectional)         │
│    Decoder self-attn:  Q,K,V = decoder   (causal mask)           │
│    Cross-attention:    Q = decoder, K,V = encoder                │
│                                                                  │
│  SHAPES (batch=B, src=S, tgt=T, model=D):                       │
│    Encoder input:  (B, S) → embed → (B, S, D)                   │
│    Encoder output: (B, S, D)                                     │
│    Decoder input:  (B, T) → embed → (B, T, D)                   │
│    Decoder output: (B, T, D)                                     │
│    Final logits:   (B, T, V)  where V = vocab size               │
│                                                                  │
│  COMPLEXITY:                                                     │
│    Self-attention: O(T² · d)     ← quadratic in sequence length  │
│    FFN:            O(T · d · d_ff) ← linear in sequence length   │
│                                                                  │
│  EVOLUTION:                                                      │
│    2017: Transformer (this paper)                                │
│    2018: BERT (encoder-only), GPT (decoder-only)                 │
│    2019: GPT-2 (Pre-LN)                                          │
│    2020: GPT-3 (scaling laws)                                    │
│    2022: Flash Attention, SwiGLU, RoPE                           │
│    2023: GQA, Mixtral (MoE)                                      │
│    2024+: Claude, GPT-4o, LLaMA-3, Gemini (decoder-only reigns) │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```
