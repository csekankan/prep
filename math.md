# Mathematics for ML & GenAI — Complete Guide (Simple to Advanced)

> From basic algebra to the math behind transformers and diffusion models.
> Every concept explained intuitively FIRST, then formally. Interview questions included.

---

## Table of Contents

1. [Linear Algebra](#1-linear-algebra)
2. [Calculus for ML](#2-calculus-for-ml)
3. [Probability & Statistics](#3-probability--statistics)
4. [Information Theory](#4-information-theory)
5. [Optimization](#5-optimization)
6. [The Math of Neural Networks](#6-the-math-of-neural-networks)
7. [The Math of Attention & Transformers](#7-the-math-of-attention--transformers)
8. [The Math of Embeddings & Vector Spaces](#8-the-math-of-embeddings--vector-spaces)
9. [The Math of Loss Functions](#9-the-math-of-loss-functions)
10. [The Math of Regularization](#10-the-math-of-regularization)
11. [The Math of Generative Models](#11-the-math-of-generative-models)
12. [Interview Questions](#12-interview-questions)

---

## 1. Linear Algebra

#### Why It Matters for ML/GenAI

Everything in ML is a matrix operation. Images are matrices of pixels. Text is matrices of embeddings. Neural networks are chains of matrix multiplications. GPUs exist because matrix multiplication can be massively parallelized.

### 1.1 Vectors

**Intuition:** A vector is a list of numbers. In ML, it represents a data point in some space.

```
A word embedding is a vector:
  "king"  = [0.2, 0.8, -0.1, 0.5, ...]  (1536 numbers in OpenAI's model)
  "queen" = [0.3, 0.7, -0.1, 0.6, ...]  (close to "king" in this space!)

A feature vector:
  user = [age=25, income=50000, purchases=12]  (3D vector)
```

**Operations:**

```
Vector addition:     [1, 2, 3] + [4, 5, 6] = [5, 7, 9]
Scalar multiply:     3 × [1, 2, 3] = [3, 6, 9]
Dot product:         [1, 2, 3] · [4, 5, 6] = 1×4 + 2×5 + 3×6 = 32
```

**Dot product — the most important operation in ML:**

```
dot(a, b) = Σ(aᵢ × bᵢ) = a₁b₁ + a₂b₂ + ... + aₙbₙ

Why it matters:
  - Measures SIMILARITY between vectors (cosine similarity = normalized dot product)
  - Every neuron computes: dot(weights, inputs) + bias
  - Attention scores = dot(query, key)
  - Embedding retrieval = dot(query_embedding, document_embedding)
```

**Cosine similarity (used EVERYWHERE in GenAI):**

```
cos_sim(a, b) = dot(a, b) / (||a|| × ||b||)

||a|| = √(a₁² + a₂² + ... + aₙ²)   (L2 norm / magnitude)

Result range: [-1, 1]
  1.0  = identical direction (same meaning)
  0.0  = perpendicular (unrelated)
  -1.0 = opposite direction (opposite meaning)

Industry use: This is how RAG retrieval works.
  Query embedding · Document embedding → similarity score → rank results
```

### 1.2 Matrices

**Intuition:** A matrix is a 2D array of numbers. In ML, it represents a transformation (weights) or a batch of data.

```
A weight matrix in a neural network:
  W = [[0.1, 0.3, -0.2],
       [0.4, -0.1, 0.5]]    (2×3 matrix: transforms 3D input → 2D output)

A batch of embeddings:
  X = [[emb_word1],
       [emb_word2],
       [emb_word3]]          (3 words × 1536 dims = 3×1536 matrix)
```

**Matrix multiplication (the heart of neural networks):**

```
If A is (m × n) and B is (n × p), then AB is (m × p)

Each element: (AB)ᵢⱼ = Σₖ Aᵢₖ × Bₖⱼ  (dot product of row i with column j)

Neural network forward pass:
  output = input × W + b
  (1×768) × (768×512) = (1×512)   ← transforms 768-dim to 512-dim

Why GPUs are essential:
  Matrix multiply of (1000 × 768) × (768 × 512) = 393 million multiplications
  GPU does this in parallel across thousands of cores → milliseconds
  CPU does it sequentially → seconds
```

**Transpose:**

```
If A = [[1, 2, 3],
        [4, 5, 6]]     (2×3)

Then Aᵀ = [[1, 4],
            [2, 5],
            [3, 6]]    (3×2)

Used in: attention (Q × Kᵀ), computing gradients, covariance matrices
```

### 1.3 Eigenvalues & Eigenvectors (PCA, Dimensionality Reduction)

**Intuition:** An eigenvector is a direction that doesn't change when you apply the transformation — it only gets scaled (by the eigenvalue).

```
Av = λv

A = transformation matrix
v = eigenvector (direction preserved)
λ = eigenvalue (how much it's scaled)
```

**Why it matters:**
- **PCA (Principal Component Analysis):** Find the eigenvectors of the covariance matrix → these are the "principal directions" of your data. Project data onto top-k eigenvectors → dimensionality reduction.
- **Spectral methods:** Graph neural networks, community detection, recommendation systems.

**Industry use:** Reducing 1536-dim embeddings to 256-dim for faster search (Matryoshka embeddings use a similar idea).

### 1.4 Matrix Decompositions

```
SVD (Singular Value Decomposition):
  A = UΣVᵀ
  
  U = left singular vectors (m × m)
  Σ = diagonal matrix of singular values (m × n)
  Vᵀ = right singular vectors (n × n)

Used for:
  - Low-rank approximation (LoRA fine-tuning decomposes weight updates as low-rank matrices)
  - Recommendation systems (Netflix prize was won with matrix factorization)
  - Compressing large language models (quantization uses SVD concepts)
```

---

## 2. Calculus for ML

#### Why It Matters

Training = finding the weights that minimize the loss function. Calculus tells you HOW to move the weights (gradient = direction of steepest ascent, so you go in the OPPOSITE direction).

### 2.1 Derivatives (Gradients)

**Intuition:** The derivative tells you how fast a function is changing at a point. In ML, it tells you "if I change this weight by a tiny amount, how much does the loss change?"

```
f(x) = x²
f'(x) = 2x

At x = 3: f'(3) = 6
Meaning: increasing x by 0.01 will increase f by approximately 0.06
```

**Partial derivatives (for functions of many variables):**

```
f(w₁, w₂) = w₁² + 3w₁w₂ + w₂²

∂f/∂w₁ = 2w₁ + 3w₂   (how f changes when ONLY w₁ changes)
∂f/∂w₂ = 3w₁ + 2w₂   (how f changes when ONLY w₂ changes)

Gradient: ∇f = [∂f/∂w₁, ∂f/∂w₂] = vector pointing toward steepest increase
```

### 2.2 Chain Rule (Backbone of Backpropagation)

**The chain rule:** If f(g(x)), then df/dx = df/dg × dg/dx

```
Neural network example:
  z = wx + b           (linear transform)
  a = sigmoid(z)       (activation)
  L = (a - y)²         (loss)

To find ∂L/∂w (how weight affects loss):
  ∂L/∂w = ∂L/∂a × ∂a/∂z × ∂z/∂w

  ∂L/∂a = 2(a - y)                    (loss derivative)
  ∂a/∂z = sigmoid(z)(1 - sigmoid(z))  (sigmoid derivative)
  ∂z/∂w = x                           (linear derivative)

This IS backpropagation — applying the chain rule layer by layer, from output back to input.
```

### 2.3 Gradient Descent

**Intuition:** You're blindfolded on a hill and want to reach the bottom. You feel which direction is steepest downhill (gradient), take a step in that direction, repeat.

```
Algorithm:
  Repeat:
    1. Compute gradient: g = ∇L(w)    (direction of steepest INCREASE)
    2. Update weights: w = w - α × g  (move OPPOSITE to gradient)
    3. α = learning rate (step size)

If α too large:  overshoot the minimum, bounce around, diverge
If α too small:  converge too slowly, might get stuck in local minimum
Sweet spot:      typically 0.001 to 0.01 for Adam optimizer
```

**Variants:**

| Method | How It Works | When to Use |
|---|---|---|
| SGD | Random sample, compute gradient | Simple, foundational |
| Momentum | Add fraction of previous gradient (rolling ball) | Faster convergence |
| Adam | Adaptive learning rate per parameter + momentum | Default for everything (2025) |
| AdamW | Adam + weight decay (L2 regularization done right) | LLM training standard |

### 2.4 Jacobian and Hessian (Advanced)

```
Jacobian: matrix of ALL first derivatives (for vector-valued functions)
  J[i][j] = ∂fᵢ/∂xⱼ
  Used in: multi-output networks, normalizing flows, generative models

Hessian: matrix of ALL second derivatives
  H[i][j] = ∂²f/∂xᵢ∂xⱼ
  Used in: Newton's method (second-order optimization), understanding loss landscape curvature
  
  Eigenvalues of Hessian tell you:
    All positive → local minimum (good!)
    All negative → local maximum (bad)
    Mixed → saddle point (very common in high dimensions)
```

---

## 3. Probability & Statistics

#### Why It Matters

ML is fundamentally about uncertainty. Models output PROBABILITIES (not certainties). Understanding probability is essential for: classification, language models (next token probability), Bayesian methods, and evaluation.

### 3.1 Probability Basics

```
P(A) = probability of event A, always between 0 and 1
P(A|B) = probability of A GIVEN that B happened (conditional)
P(A,B) = probability of A AND B happening together (joint)

Bayes' Theorem (interview must-know):
  P(A|B) = P(B|A) × P(A) / P(B)

  In English: "probability of model being correct GIVEN the data"
            = "probability of seeing this data IF model is correct" × "prior belief" / "evidence"

Industry example (spam filtering):
  P(spam | contains "free money") = P("free money" | spam) × P(spam) / P("free money")
```

### 3.2 Distributions

**Normal (Gaussian) distribution:**
```
f(x) = (1/√(2πσ²)) × exp(-(x-μ)²/(2σ²))

μ = mean (center)
σ = standard deviation (spread)

Why it matters:
  - Weight initialization (random normal with small σ)
  - Batch normalization assumes activations are roughly normal
  - Noise in diffusion models is Gaussian
  - Central Limit Theorem: sum of many random things → normal
```

**Bernoulli / Binomial:**
```
Bernoulli: single coin flip (P(heads) = p)
Binomial: n coin flips, count successes

Used for: binary classification, dropout (each neuron "flipped off" with probability p)
```

**Categorical / Multinomial:**
```
Generalization of Bernoulli to K categories.
P(class_i) = pᵢ, where Σpᵢ = 1

This is what softmax outputs! A categorical distribution over vocabulary tokens.
LLM outputs: P(next_token = "hello") = 0.3, P("world") = 0.2, P("the") = 0.15, ...
```

### 3.3 Expectation, Variance, Covariance

```
Expectation (mean): E[X] = Σ xᵢ × P(xᵢ)
  "The average value you'd get if you sampled many times"

Variance: Var(X) = E[(X - E[X])²] = E[X²] - (E[X])²
  "How spread out the values are"

Covariance: Cov(X, Y) = E[(X - E[X])(Y - E[Y])]
  "Do X and Y move together?"
  Positive: when X goes up, Y goes up
  Negative: when X goes up, Y goes down
  Zero: no linear relationship
```

### 3.4 Maximum Likelihood Estimation (MLE)

```
Given data D, find parameters θ that maximize P(D|θ)

In practice: maximize log-likelihood (equivalent, numerically stable)
  θ* = argmax Σ log P(xᵢ | θ)

Why LLMs use this:
  Training a language model = maximize the probability of the training text
  θ* = argmax Σ log P(next_token | previous_tokens, θ)
  
  This is EXACTLY the cross-entropy loss used to train GPT/Claude/etc.
```

### 3.5 Sampling and Temperature

```
LLM outputs logits → softmax → probability distribution
  logits = [2.0, 1.0, 0.5, -1.0]
  softmax(logits) = [0.54, 0.20, 0.12, 0.03]  (probabilities sum to 1)

Temperature controls randomness:
  softmax(logits / T)
  
  T = 0.1: Very peaked → [0.98, 0.01, 0.005, 0.0001] → almost deterministic
  T = 1.0: Normal → [0.54, 0.20, 0.12, 0.03] → natural randomness
  T = 2.0: Flat → [0.35, 0.25, 0.22, 0.18] → very random/creative

Top-p (nucleus sampling):
  Sort tokens by probability, take the top tokens whose cumulative probability ≥ p
  If p = 0.9: keep tokens until their cumulative prob reaches 90%, ignore the rest
  This cuts off the "long tail" of unlikely tokens
```

---

## 4. Information Theory

#### Why It Matters

Cross-entropy loss (THE loss function for LLMs) comes from information theory. Understanding entropy = understanding what the model is optimizing.

### 4.1 Entropy

```
H(X) = -Σ P(x) × log₂(P(x))

Intuition: "How surprised am I on average?"
  - Coin with P(heads) = 0.5: H = 1 bit (maximum uncertainty)
  - Coin with P(heads) = 0.99: H ≈ 0.08 bits (barely any surprise)
  - Certain outcome: H = 0 bits (no surprise at all)

For LLMs: entropy of the next-token distribution measures how "confused" the model is.
  Low entropy → model is confident (one token is very likely)
  High entropy → model is uncertain (many tokens are equally likely)
```

### 4.2 Cross-Entropy (THE Loss Function for LLMs)

```
H(p, q) = -Σ p(x) × log(q(x))

p = true distribution (one-hot: the actual next token)
q = model's predicted distribution (softmax output)

For a single next-token prediction:
  True: token "hello" (p = [0, 0, 1, 0, ...] — one-hot)
  Pred: q = [0.1, 0.2, 0.6, 0.1, ...] — model's probabilities
  
  Cross-entropy = -log(0.6) = 0.51  (only the true token matters!)
  
  If model predicted P("hello") = 0.99:
    Cross-entropy = -log(0.99) = 0.01  (very low loss — model is right!)
  If model predicted P("hello") = 0.01:
    Cross-entropy = -log(0.01) = 4.6   (high loss — model was wrong!)

Training minimizes cross-entropy = maximizes the probability of correct tokens.
This is EXACTLY Maximum Likelihood Estimation!
```

### 4.3 KL Divergence

```
KL(p || q) = Σ p(x) × log(p(x)/q(x)) = H(p,q) - H(p)

"How different is distribution q from distribution p?"
  KL = 0: distributions are identical
  KL > 0: always (not symmetric! KL(p||q) ≠ KL(q||p))

Used in:
  - VAEs (regularize latent space toward normal distribution)
  - RLHF (keep fine-tuned model close to base model: KL penalty)
  - Knowledge distillation (student mimics teacher's distribution)
```

### 4.4 Perplexity (LLM Evaluation Metric)

```
Perplexity = 2^(cross-entropy) = exp(average negative log-likelihood)

Intuition: "On average, how many tokens is the model choosing between?"
  Perplexity = 1: model always predicts correctly (impossible in practice)
  Perplexity = 10: model is choosing between ~10 equally likely tokens
  Perplexity = 100: model is very confused

GPT-4 perplexity on various benchmarks: ~5-10 (very confident)
Random guessing on 50K vocab: perplexity = 50,000

Lower perplexity = better language model (industry standard metric)
```

---

## 5. Optimization

#### Why It Matters

Training a neural network = solving an optimization problem with BILLIONS of parameters. The optimizer determines: how fast you converge, whether you find a good minimum, and whether training is stable.

### 5.1 Gradient Descent Variants

```
Batch GD:    Compute gradient on ALL data → one update
             Pro: stable. Con: very slow for large datasets.

Stochastic GD (SGD): Compute gradient on ONE sample → one update
             Pro: fast updates. Con: very noisy.

Mini-batch GD: Compute gradient on batch of 32-512 samples → one update
             Pro: balance of speed and stability. THIS IS WHAT EVERYONE USES.
```

### 5.2 Adam Optimizer (The Industry Standard)

```
Adam = Adaptive Moment Estimation

Maintains two running averages per parameter:
  m = exponential moving average of gradient (momentum — "which direction?")
  v = exponential moving average of gradient² (scaling — "how big should the step be?")

Update rule:
  m = β₁ × m + (1-β₁) × g           (momentum, β₁ = 0.9 typically)
  v = β₂ × v + (1-β₂) × g²          (second moment, β₂ = 0.999)
  m̂ = m / (1 - β₁ᵗ)                  (bias correction for early steps)
  v̂ = v / (1 - β₂ᵗ)
  w = w - α × m̂ / (√v̂ + ε)           (update: momentum / scale)

Why Adam works so well:
  - Adaptive: each parameter gets its own effective learning rate
  - Momentum: doesn't oscillate like plain SGD
  - Robust: works well across most architectures without much tuning

AdamW (for LLMs):
  Same as Adam but decouples weight decay from gradient update.
  This is what GPT, Claude, Llama are all trained with.
```

### 5.3 Learning Rate Schedules

```
Constant:       α = 0.001 (simple, rarely optimal)
Step decay:     α = α₀ × 0.1 every N epochs
Cosine anneal:  α = α_min + 0.5(α_max - α_min)(1 + cos(πt/T))
Warmup + decay: Start low → ramp up → cosine decay (LLM STANDARD)

LLM training schedule (GPT/Llama style):
  Warmup: 0 → α_max over first 2000 steps (prevents instability)
  Decay:  α_max → α_min over remaining steps (cosine schedule)
  
  Typical: α_max = 3e-4, α_min = 3e-5, warmup_steps = 2000
```

### 5.4 Loss Landscape and Saddle Points

```
In high dimensions (billions of parameters):
  - Local minima are RARE (probability decreases exponentially with dims)
  - Saddle points are EVERYWHERE (some directions go up, others go down)
  - "Sharp" minima generalize poorly; "flat" minima generalize well
  
Why SGD noise helps: the noise from random mini-batches helps escape saddle points
and sharp minima, often converging to flat minima (better generalization).
```

---

## 6. The Math of Neural Networks

### 6.1 Single Neuron (Perceptron)

```
output = activation(Σ(wᵢ × xᵢ) + b)
       = activation(dot(w, x) + b)
       = activation(W·X + b)

This is: linear transformation → non-linear activation
  Linear part: z = w₁x₁ + w₂x₂ + ... + wₙxₙ + b
  Activation: a = σ(z)  (sigmoid, ReLU, etc.)
```

### 6.2 Activation Functions

```
Sigmoid:  σ(z) = 1 / (1 + e⁻ᶻ)
  Output: (0, 1) — interprets as probability
  Derivative: σ(z)(1 - σ(z))
  Problem: vanishing gradients (derivative → 0 for large |z|)
  Use: binary classification output layer, gates in LSTM/GRU

Tanh:  tanh(z) = (eᶻ - e⁻ᶻ) / (eᶻ + e⁻ᶻ)
  Output: (-1, 1) — zero-centered
  Derivative: 1 - tanh²(z)
  Problem: still vanishes for large |z|
  Use: RNNs, normalization layers

ReLU:  f(z) = max(0, z)
  Output: [0, ∞)
  Derivative: 1 if z > 0, else 0
  Problem: "dead neurons" (if z < 0 forever, gradient = 0, never learns)
  Use: DEFAULT for hidden layers in modern networks

GELU:  f(z) = z × Φ(z)  where Φ is the standard normal CDF
  ≈ 0.5z(1 + tanh(√(2/π)(z + 0.044715z³)))
  Smooth approximation of ReLU with non-zero gradient everywhere
  Use: Transformers (GPT, BERT, Claude all use GELU)

SiLU/Swish: f(z) = z × sigmoid(z)
  Similar to GELU but slightly different shape
  Use: Llama, Mistral models

Softmax: softmax(zᵢ) = eᶻⁱ / Σⱼ eᶻʲ
  Output: probability distribution (all positive, sums to 1)
  Use: output layer for classification, attention weights
```

### 6.3 Backpropagation (Full Derivation)

```
For a 2-layer network:
  Layer 1: z₁ = W₁x + b₁,  a₁ = ReLU(z₁)
  Layer 2: z₂ = W₂a₁ + b₂, a₂ = softmax(z₂)
  Loss:    L = CrossEntropy(a₂, y)

Backprop computes (applying chain rule from output to input):

  ∂L/∂z₂ = a₂ - y                       (softmax + cross-entropy simplifies!)
  ∂L/∂W₂ = (∂L/∂z₂) × a₁ᵀ              (gradient for layer 2 weights)
  ∂L/∂b₂ = ∂L/∂z₂                       (gradient for layer 2 bias)
  
  ∂L/∂a₁ = W₂ᵀ × (∂L/∂z₂)             (propagate error backward)
  ∂L/∂z₁ = (∂L/∂a₁) ⊙ ReLU'(z₁)       (⊙ = element-wise multiply)
  ∂L/∂W₁ = (∂L/∂z₁) × xᵀ              (gradient for layer 1 weights)
  ∂L/∂b₁ = ∂L/∂z₁

Key insight: backprop is just the chain rule applied systematically.
Each layer computes its local gradient and passes the error backward.
Time complexity: O(forward_pass) — same cost as prediction!
```

### 6.4 Batch Normalization

```
BatchNorm(x) = γ × (x - μ_batch) / √(σ²_batch + ε) + β

μ_batch = mean across the batch for each feature
σ²_batch = variance across the batch
γ, β = learnable scale and shift parameters
ε = small constant for numerical stability (1e-5)

Why it works:
  - Reduces "internal covariate shift" (each layer's input distribution changes during training)
  - Allows higher learning rates (gradients are better scaled)
  - Acts as regularization (batch statistics add noise)
  
LayerNorm (used in Transformers instead of BatchNorm):
  Same formula but normalize across FEATURES (not across batch)
  LN(x) = γ × (x - μ_features) / √(σ²_features + ε) + β
  
  Why LayerNorm for Transformers: works with variable sequence lengths,
  doesn't depend on batch size, works for inference with batch=1.
```

---

## 7. The Math of Attention & Transformers

### 7.1 Self-Attention (The Core Innovation)

```
Attention(Q, K, V) = softmax(QKᵀ / √dₖ) × V

Step by step:
  Input: X (sequence of token embeddings, shape: seq_len × d_model)
  
  1. Project to Q, K, V:
     Q = X × Wq   (queries: "what am I looking for?")
     K = X × Wk   (keys: "what do I contain?")
     V = X × Wv   (values: "what information do I provide?")
     
     All shape: seq_len × d_k (typically d_k = 64)
  
  2. Compute attention scores:
     scores = Q × Kᵀ         (shape: seq_len × seq_len)
     
     scores[i][j] = dot(query_i, key_j)
     "How much should token i attend to token j?"
  
  3. Scale:
     scores = scores / √d_k
     
     Why? Without scaling, dot products grow with dimension → softmax saturates
     → gradients vanish. √d_k keeps variance ≈ 1 regardless of dimension.
  
  4. Mask (for causal/decoder models):
     scores[i][j] = -∞  if j > i  (can't look at future tokens)
     
     After softmax: attention_weight[i][j] = 0 for future tokens.
     This is how GPT generates left-to-right.
  
  5. Softmax:
     weights = softmax(scores)  (each row sums to 1)
     weights[i][j] = "how much attention does token i pay to token j"
  
  6. Weighted sum of values:
     output = weights × V
     output[i] = Σⱼ weights[i][j] × V[j]
     "Token i's representation = weighted combination of all value vectors"
```

### 7.2 Multi-Head Attention

```
Instead of ONE attention, run H separate attentions in parallel:

MultiHead(Q, K, V) = Concat(head₁, head₂, ..., headₕ) × Wₒ

Where headᵢ = Attention(Q×Wᵢᵠ, K×Wᵢᵏ, V×Wᵢᵛ)

Typical: h = 8 or 12 heads, each with d_k = d_model/h

Why multiple heads?
  - Each head can learn different relationship types:
    Head 1: syntactic relationships ("the" attends to its noun)
    Head 2: semantic relationships (verb attends to subject)
    Head 3: positional patterns (nearby tokens)
    Head 4: long-range dependencies (pronoun to its antecedent)
    
  - One big attention would have to learn ALL patterns simultaneously
  - Multiple small attentions specialize → better overall representation
```

### 7.3 Positional Encoding

```
Problem: Attention is permutation-invariant. "dog bites man" and "man bites dog"
         have the same attention pattern without position information.

Solution: Add positional information to embeddings.

Sinusoidal (original transformer):
  PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
  PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
  
  Why sin/cos? Relative positions can be computed as linear functions of PE.
  PE(pos+k) = linear_transform(PE(pos)) for any k.

RoPE (Rotary Position Embedding — used in Llama, Mistral, GPT-4):
  Rotates query/key vectors by angle proportional to position.
  q'_i = q_i × cos(mθ_i) + q_i* × sin(mθ_i)
  
  Advantage: naturally handles relative positions, scales to longer sequences,
  can be extrapolated beyond training length.
```

### 7.4 Full Transformer Block

```
TransformerBlock(x):
  1. a = LayerNorm(x)                        (normalize)
  2. a = MultiHeadAttention(a, a, a) + x     (attention + residual)
  3. b = LayerNorm(a)                        (normalize again)
  4. output = FFN(b) + a                     (feed-forward + residual)

FFN (Feed-Forward Network):
  FFN(x) = GELU(x × W₁ + b₁) × W₂ + b₂
  
  Typically: d_model → 4×d_model → d_model
  (expand to higher dimension, apply non-linearity, project back)

Residual connections (x + attention(x)):
  - Allow gradients to flow directly through the network
  - Without them, deep networks (96+ layers) can't train
  - The "+x" means: "this layer REFINES the representation, doesn't replace it"
```

---

## 8. The Math of Embeddings & Vector Spaces

### 8.1 Word2Vec (Foundation)

```
Idea: predict surrounding words from center word (Skip-gram)
      or center word from surrounding words (CBOW)

Skip-gram objective:
  maximize Σ log P(context_word | center_word)
  P(w_c | w) = exp(dot(v_w, v'_c)) / Σⱼ exp(dot(v_w, v'_j))

Result: words in similar contexts get similar vectors
  vector("king") - vector("man") + vector("woman") ≈ vector("queen")
  
This works because the vector space captures RELATIONSHIPS as directions.
```

### 8.2 Cosine Similarity vs Euclidean Distance

```
Cosine similarity: cos(θ) = dot(a,b) / (||a|| × ||b||)
  Measures ANGLE between vectors (direction, not magnitude)
  Use for: text similarity, recommendation, RAG retrieval

Euclidean distance: d(a,b) = √(Σ(aᵢ - bᵢ)²)
  Measures DISTANCE in space (affected by magnitude)
  Use for: clustering (k-means), anomaly detection

For normalized vectors (||a|| = ||b|| = 1):
  cosine_similarity = 1 - euclidean_distance²/2
  They give equivalent rankings!
  
Industry practice: Normalize embeddings to unit length → use dot product
(fastest, equivalent to cosine similarity for normalized vectors).
```

### 8.3 Dimensionality Reduction for Visualization

```
t-SNE: Non-linear reduction to 2D/3D for visualization
  Preserves local structure (nearby points stay nearby)
  Does NOT preserve global structure (distances between clusters are meaningless)
  
UMAP: Faster than t-SNE, better global structure
  Preferred for large embedding sets (100K+ points)

PCA: Linear reduction, preserves maximum variance
  Fast, deterministic, but can't capture non-linear relationships
```

---

## 9. The Math of Loss Functions

### 9.1 Cross-Entropy Loss (Classification / LLMs)

```
For binary classification:
  L = -[y×log(ŷ) + (1-y)×log(1-ŷ)]
  
  If y=1: L = -log(ŷ)    → loss high when ŷ near 0 (wrong!)
  If y=0: L = -log(1-ŷ)  → loss high when ŷ near 1 (wrong!)

For multi-class (LLMs):
  L = -Σᵢ yᵢ × log(ŷᵢ) = -log(ŷ_correct_class)
  
  Only the correct token's probability matters!
  Training MAXIMIZES P(correct_token) = MINIMIZES -log(P(correct_token))
```

### 9.2 MSE (Regression)

```
L = (1/n) Σ(yᵢ - ŷᵢ)²

Derivative: ∂L/∂ŷᵢ = 2(ŷᵢ - yᵢ)/n
  Direction: pushes prediction toward true value.
  
Assumes Gaussian noise. If outliers are a problem, use MAE (L1) or Huber loss.
```

### 9.3 Contrastive Loss (Embeddings)

```
Used to train embedding models (sentence-transformers, CLIP, etc.)

Idea: pull similar pairs CLOSER, push dissimilar pairs APART in vector space.

Triplet loss:
  L = max(0, d(anchor, positive) - d(anchor, negative) + margin)
  
  "Positive should be closer to anchor than negative by at least 'margin'"

InfoNCE (used in CLIP, SimCLR):
  L = -log(exp(sim(a, p)/τ) / Σⱼ exp(sim(a, nⱼ)/τ))
  
  "Among all candidates, the positive should have the highest similarity"
  τ = temperature (controls how peaked the distribution is)
```

### 9.4 RLHF Loss (Aligning LLMs)

```
Reward model: trained on human preferences
  "Given two responses, which is better?" → score function R(x, y)

PPO objective (simplified):
  maximize E[R(prompt, response)] - β × KL(π_new || π_reference)
  
  "Generate responses that get high reward, but don't deviate too far 
   from the base model (prevent reward hacking)"
  
  β = KL penalty coefficient (typically 0.01-0.1)
  If β too low: model exploits reward model (outputs nonsense that gets high score)
  If β too high: model barely changes from base (no alignment improvement)
```

---

## 10. The Math of Regularization

### 10.1 Why Regularization Exists

```
Problem: model fits training data perfectly but fails on new data (overfitting).

Solution: add constraints that prevent the model from being "too complex."

Bias-variance tradeoff:
  Total error = Bias² + Variance + Irreducible noise
  
  High bias (underfitting): model too simple, can't capture patterns
  High variance (overfitting): model too complex, memorizes noise
  Regularization reduces VARIANCE at the cost of slightly more BIAS.
```

### 10.2 L1 and L2 Regularization

```
L2 (Ridge / Weight Decay):
  L_total = L_data + λ × Σ wᵢ²
  
  Effect: pushes weights toward 0, but never exactly 0.
  Intuition: penalizes large weights → smoother, simpler model.
  Used in: AdamW (decoupled weight decay), virtually all neural network training.

L1 (Lasso):
  L_total = L_data + λ × Σ |wᵢ|
  
  Effect: pushes some weights to EXACTLY 0 → sparse model.
  Intuition: feature selection — irrelevant features get weight = 0.
  Used in: feature selection, sparse models, not common in deep learning.
```

### 10.3 Dropout

```
During training: randomly set each neuron to 0 with probability p (typically 0.1-0.5)
During inference: use all neurons but scale by (1-p)

Math:
  Training: h = mask ⊙ f(x)    where mask ~ Bernoulli(1-p)
  Inference: h = (1-p) × f(x)  OR scale during training (inverted dropout)

Why it works:
  - Forces redundancy: no neuron can rely on specific other neurons
  - Ensemble effect: trains 2^n different sub-networks implicitly
  - Prevents co-adaptation of neurons

LLM-specific: dropout is often REMOVED in large models (GPT-3+)
  because they're already undertrained (not enough epochs to overfit).
```

---

## 11. The Math of Generative Models

### 11.1 Autoregressive Models (GPT)

```
P(x₁, x₂, ..., xₙ) = P(x₁) × P(x₂|x₁) × P(x₃|x₁,x₂) × ... × P(xₙ|x₁,...,xₙ₋₁)

Chain rule of probability: factorize joint probability into sequence of conditionals.
Each P(xᵢ|x₁,...,xᵢ₋₁) is predicted by the transformer.

This is why LLMs generate ONE token at a time — each token is conditioned on all previous.
Parallel generation is impossible because each token depends on the previous one.
```

### 11.2 Diffusion Models (DALL-E, Stable Diffusion)

```
Forward process: gradually add Gaussian noise to data until it's pure noise
  x_t = √(ᾱ_t) × x₀ + √(1-ᾱ_t) × ε    where ε ~ N(0, I)
  
  At t=0: original image
  At t=T: pure random noise

Reverse process: learn to DENOISE step by step
  x_{t-1} = model_prediction(x_t, t)
  
  The model learns: "given noisy image at step t, predict the noise"
  
Training objective (simplified):
  L = E[||ε - ε_θ(x_t, t)||²]
  "Predicted noise should match actual noise"

Generation:
  1. Start with pure noise x_T ~ N(0, I)
  2. For t = T, T-1, ..., 1:
     x_{t-1} = denoise(x_t, t)
  3. x₀ = final image
```

### 11.3 VAE (Variational Autoencoder)

```
Encoder: maps input x to latent distribution q(z|x) = N(μ, σ²)
Decoder: maps latent z back to reconstruction p(x|z)

Loss = Reconstruction loss + KL divergence
     = E_q[log p(x|z)] - KL(q(z|x) || p(z))
     = "output should match input" + "latent distribution should be close to N(0,1)"

Reparameterization trick (enables backprop through sampling):
  z = μ + σ × ε     where ε ~ N(0, I)
  (Sample noise externally, then transform deterministically → gradients flow!)
```

---

## 12. Interview Questions

### 12.1 Quick-Fire Questions

1. **Why do we divide attention scores by √dₖ?**
   → To prevent softmax saturation. Dot products grow with dimension (variance ≈ dₖ). Dividing by √dₖ keeps variance ≈ 1, ensuring softmax has meaningful gradients.

2. **Why is cross-entropy loss used instead of MSE for classification?**
   → Cross-entropy penalizes confident wrong predictions heavily (-log(0.01) = 4.6). MSE barely cares about confident wrong predictions ((1-0.01)² ≈ 1). Cross-entropy provides stronger gradient signal for correcting mistakes.

3. **What is the vanishing gradient problem and how is it solved?**
   → In deep networks, gradients shrink exponentially as they propagate backward (sigmoid derivative ≤ 0.25 → 0.25^50 ≈ 10⁻³⁰). Solutions: ReLU activation, residual connections, LayerNorm, gradient clipping.

4. **Why do transformers use LayerNorm instead of BatchNorm?**
   → LayerNorm normalizes across features (independent of batch). Works with variable sequence lengths, batch size 1 at inference, and doesn't need running statistics.

5. **What is the difference between L1 and L2 regularization?**
   → L1 produces sparse solutions (some weights exactly 0, feature selection). L2 produces small but non-zero weights (smoother model). Geometrically: L1 constraint is a diamond (corners at axes), L2 is a sphere.

6. **Why do LLMs generate one token at a time?**
   → Autoregressive factorization: P(x₁,...,xₙ) = ∏P(xᵢ|x<ᵢ). Each token's probability depends on ALL previous tokens. Can't parallelize generation (but CAN parallelize training with teacher forcing).

7. **What is temperature in LLM sampling?**
   → Divides logits before softmax: softmax(z/T). T<1 → sharper (more deterministic). T>1 → flatter (more random). T→0 → argmax (greedy). T→∞ → uniform random.

8. **Explain the reparameterization trick.**
   → Instead of z ~ N(μ,σ²) (can't backprop through sampling), write z = μ + σ×ε where ε ~ N(0,1). Now z is a deterministic function of μ,σ → gradients flow through to encoder.

9. **What is the KL divergence penalty in RLHF?**
   → Prevents the fine-tuned model from deviating too far from the base model. Without it, the model "hacks" the reward model by finding adversarial outputs that score high but are nonsensical.

10. **Why do large models need warmup?**
    → Random initial weights create large, unstable gradients. Warmup starts with tiny learning rate (gradients don't explode), then ramps up once the loss landscape is smoother. Without warmup, training often diverges immediately.

### 12.2 Deep Dive Questions

**"Walk me through the forward pass of a transformer for text generation"**

```
Input: "The cat sat"

1. Tokenization: ["The", "cat", "sat"] → [1234, 5678, 9012]
2. Embedding: look up in embedding table → 3 vectors of dim 768
3. Add positional encoding (RoPE or sinusoidal)
4. For each transformer block (e.g., 12 blocks):
   a. LayerNorm
   b. Multi-head self-attention (8 heads, each 96-dim)
      - Compute Q, K, V from current representations
      - Causal mask: each token only sees previous tokens
      - Attention weights → weighted sum of values
   c. Residual connection (add input back)
   d. LayerNorm
   e. FFN (768 → 3072 → 768, GELU activation)
   f. Residual connection
5. Final LayerNorm
6. Project to vocabulary size: (768) × (768 × 50257) → 50257 logits
7. Softmax → probability distribution over all tokens
8. Sample next token (or argmax for greedy)
9. Append token, repeat from step 1 for next token
```

**"Why does LoRA work for fine-tuning?"**

```
Full fine-tuning: update all W (billions of params, expensive)
LoRA: W' = W + ΔW, where ΔW = A × B

Instead of updating a (d×d) weight matrix, decompose the update as:
  A: (d × r)    (r = 8 or 16, very small)
  B: (r × d)
  A × B: (d × d)  but only r×d + r×d = 2rd parameters instead of d²

For d=4096, r=16: 
  Full: 4096² = 16.7M parameters per layer
  LoRA: 2 × 4096 × 16 = 131K parameters per layer (128x fewer!)

Why it works: weight updates during fine-tuning have LOW INTRINSIC RANK.
The model mostly knows what to do — fine-tuning makes small adjustments
that can be captured in a low-rank subspace.
```

---

## Quick Reference Card

```
Activation functions:
  sigmoid(z) = 1/(1+e⁻ᶻ)           → (0,1), for gates/probabilities
  tanh(z)    = (eᶻ-e⁻ᶻ)/(eᶻ+e⁻ᶻ) → (-1,1), for RNNs
  ReLU(z)    = max(0,z)             → [0,∞), DEFAULT hidden layers
  GELU(z)    = z×Φ(z)              → smooth ReLU, for transformers
  softmax(z) = eᶻⁱ/Σeᶻʲ           → probability distribution

Loss functions:
  MSE        = (1/n)Σ(y-ŷ)²        → regression
  BCE        = -[y·log(ŷ)+(1-y)·log(1-ŷ)]  → binary classification
  CE         = -Σyᵢ·log(ŷᵢ)       → multi-class / LLM next-token
  Triplet    = max(0, d(a,p)-d(a,n)+m)  → embedding training

Key formulas:
  Attention  = softmax(QKᵀ/√d) × V
  BatchNorm  = γ(x-μ)/√(σ²+ε) + β
  Adam update= w - α·m̂/(√v̂+ε)
  Perplexity = exp(cross_entropy)
  LoRA       = W + A×B (low-rank decomposition)
```

---

*This guide covers the math foundations needed for ML/GenAI engineering roles at companies like Google, Meta, OpenAI, Anthropic, and top AI startups. Focus on intuition first, formal math second.*
