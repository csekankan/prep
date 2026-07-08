# ML & Deep Learning for GenAI Engineers — Complete Guide

> From logistic regression to GPT — every algorithm, architecture, and concept explained
> with theory, intuition, code, and interview focus. Built for engineers transitioning to AI.

---

## Table of Contents

1. [Classical ML Foundations](#1-classical-ml-foundations)
2. [Neural Network Fundamentals](#2-neural-network-fundamentals)
3. [Training Deep Networks](#3-training-deep-networks)
4. [Convolutional Neural Networks (CNNs)](#4-convolutional-neural-networks-cnns)
5. [Recurrent Neural Networks (RNNs)](#5-recurrent-neural-networks-rnns)
6. [Attention Mechanism](#6-attention-mechanism)
7. [Transformers](#7-transformers)
8. [Pre-Training & Transfer Learning](#8-pre-training--transfer-learning)
9. [Large Language Models (LLMs)](#9-large-language-models-llms)
10. [Fine-Tuning Techniques](#10-fine-tuning-techniques)
11. [Generative Models](#11-generative-models)
12. [Reinforcement Learning from Human Feedback (RLHF)](#12-reinforcement-learning-from-human-feedback-rlhf)
13. [Model Compression & Efficiency](#13-model-compression--efficiency)
14. [Practical ML Engineering](#14-practical-ml-engineering)
15. [Interview Deep Dives](#15-interview-deep-dives)

---

## 1. Classical ML Foundations

#### Why This Matters for GenAI Engineers

You MUST understand classical ML because: (1) interview questions start here, (2) many production systems use classical ML for routing/classification alongside LLMs, (3) the concepts (loss, gradient, regularization) are the same ones used in training GPT.

### 1.1 Linear Regression

**What it does:** Predict a continuous number (price, temperature, score).

```
Model: ŷ = w₁x₁ + w₂x₂ + ... + wₙxₙ + b = Wᵀx + b
Loss:  MSE = (1/n) Σ(yᵢ - ŷᵢ)²
Goal:  Find W, b that minimize MSE

Closed-form solution: W = (XᵀX)⁻¹Xᵀy  (only works for small datasets)
Gradient descent:     W = W - α × ∂MSE/∂W (works for any size)
```

**Industry use:** Predicting LLM token costs, estimating API latency, A/B test analysis.

### 1.2 Logistic Regression (Binary Classification)

**What it does:** Predict probability of class 1 (spam/not spam, fraud/legit).

```
Model: ŷ = sigmoid(Wᵀx + b) = 1 / (1 + e^(-(Wᵀx + b)))
Loss:  Binary Cross-Entropy = -[y·log(ŷ) + (1-y)·log(1-ŷ)]
Decision: if ŷ > 0.5 → class 1, else class 0

Why sigmoid?
  - Maps any real number to (0, 1) — interpretable as probability
  - Smooth, differentiable (gradient exists everywhere)
  - Same function used as gates in LSTMs and attention mechanisms
```

**Industry use:** Spam detection, content moderation (before LLMs), model routing (classify query complexity → route to appropriate model).

### 1.3 Decision Trees & Random Forests

```
Decision Tree: sequence of if/else splits on features
  if income > 50000:
    if age > 30:
      → approve_loan
    else:
      → review
  else:
    → deny

Random Forest: train 100 trees on random subsets → majority vote
  Pro: handles non-linear relationships, feature importance, no scaling needed
  Con: can't extrapolate, large model size

Gradient Boosting (XGBoost, LightGBM): build trees sequentially, each fixing
  the previous tree's errors. BEST for tabular data (still in 2025!).
```

**Industry use:** 
- **Stripe:** Fraud detection still uses gradient-boosted trees (fast, interpretable, handles tabular features well).
- **Uber:** ETA prediction combines boosted trees with deep learning.
- **Model routing:** "Should this query go to GPT-4 or GPT-4o-mini?" → trained classifier.

### 1.4 Support Vector Machines (SVMs)

```
Idea: find the hyperplane that MAXIMALLY separates classes
  Maximize the "margin" (distance between hyperplane and nearest points)

Kernel trick: project to higher dimensions where data IS linearly separable
  Linear kernel: K(x,y) = xᵀy
  RBF kernel: K(x,y) = exp(-γ||x-y||²)  (maps to infinite dimensions!)
  Polynomial: K(x,y) = (xᵀy + c)^d

Why learn this (2025)? Interview questions + understanding the margin concept
helps with contrastive learning (triplet loss = maximizing margin in embedding space).
```

### 1.5 K-Means Clustering

```
Algorithm:
  1. Pick K random centers
  2. Assign each point to nearest center
  3. Recompute centers as mean of assigned points
  4. Repeat until convergence

Objective: minimize Σᵢ ||xᵢ - μ_cluster(xᵢ)||²

Industry use:
  - Grouping user queries by intent (embed queries → cluster embeddings)
  - Identifying topics in document collections
  - Customer segmentation for personalized prompts
```

### 1.6 Evaluation Metrics

```
Classification:
  Accuracy = correct / total  (misleading if imbalanced!)
  Precision = TP / (TP + FP)  "Of predicted positives, how many are correct?"
  Recall = TP / (TP + FN)     "Of actual positives, how many did we find?"
  F1 = 2 × (P × R) / (P + R) (harmonic mean — balances P and R)
  AUC-ROC = area under TPR vs FPR curve (threshold-independent)

When to use what:
  - Spam detection: optimize PRECISION (don't mark good emails as spam)
  - Medical diagnosis: optimize RECALL (don't miss disease cases)
  - Balanced datasets: F1 or accuracy are fine
  - Ranking (search): NDCG, MAP

Regression:
  MSE (mean squared error): penalizes large errors heavily
  MAE (mean absolute error): robust to outliers
  R² (coefficient of determination): % of variance explained (1 = perfect)
```

---

## 2. Neural Network Fundamentals

### 2.1 The Perceptron to Multi-Layer Networks

```
Single neuron (1957):
  output = step_function(Σ wᵢxᵢ + b)
  Can only learn LINEAR boundaries (can't solve XOR!)

Multi-layer network (1986 — backprop):
  Layer 1: h = ReLU(W₁x + b₁)       (hidden representation)
  Layer 2: ŷ = softmax(W₂h + b₂)    (classification output)
  
  With one hidden layer: can approximate ANY continuous function
  (Universal Approximation Theorem — but may need exponentially many neurons)
```

**The evolution to modern architectures:**
```
1957: Perceptron (linear, single layer)
1986: Multi-layer + backpropagation (deep learning begins)
1998: LeNet (first successful CNN for images)
2012: AlexNet (deep CNN + GPU → ImageNet breakthrough)
2014: GAN (generate realistic images)
2015: ResNet (residual connections → 152 layers!)
2017: Transformer (attention → replaces RNNs)
2018: BERT (pre-trained transformer for NLP)
2020: GPT-3 (175B params, few-shot learning emerges)
2022: ChatGPT (RLHF → usable by everyone)
2023: GPT-4 (multimodal, reasoning)
2024: Claude 3.5, Gemini 1.5 (long context, tool use)
```

### 2.2 Activation Functions (Complete Reference)

```
SIGMOID: σ(z) = 1/(1+e⁻ᶻ)
  Range: (0, 1)
  Used for: output layer (binary classification), gates (LSTM)
  Problem: vanishing gradient for |z| > 5
  Derivative: σ(z)(1-σ(z)), max = 0.25 at z=0

TANH: (eᶻ-e⁻ᶻ)/(eᶻ+e⁻ᶻ)
  Range: (-1, 1)
  Used for: RNN hidden states (zero-centered)
  Problem: still vanishes for large |z|

ReLU: max(0, z)
  Range: [0, ∞)
  Used for: DEFAULT hidden layers (since 2012)
  Problem: dead neurons (gradient = 0 for z < 0, permanently)
  Pro: fast to compute, no vanishing gradient for z > 0

Leaky ReLU: max(0.01z, z)
  Fixes dead neuron problem (small gradient when z < 0)

GELU: z × Φ(z) ≈ 0.5z(1 + tanh(√(2/π)(z + 0.044715z³)))
  Used for: ALL transformers (GPT, BERT, Claude, Llama)
  Why: smooth approximation of ReLU, non-zero everywhere, empirically better

SwiGLU: Swish(xW₁) ⊙ (xW₂)  (Swish = x × sigmoid(x))
  Used for: Llama 2/3, Mistral, modern models
  Why: better training dynamics, slightly better performance

SOFTMAX: eᶻⁱ / Σⱼeᶻʲ
  Range: (0, 1), sums to 1
  Used for: output layer (multi-class), attention weights
  Converts logits → probability distribution
```

### 2.3 Weight Initialization

```
Why it matters: bad initialization → gradients explode or vanish → training fails.

Xavier/Glorot (for sigmoid/tanh):
  W ~ N(0, σ²) where σ² = 2 / (fan_in + fan_out)
  Keeps variance stable across layers.

He/Kaiming (for ReLU):
  W ~ N(0, σ²) where σ² = 2 / fan_in
  Accounts for ReLU killing half the neurons (factor of 2).

For transformers: typically N(0, 0.02) with special scaling for residual layers.
GPT-2 uses: scale residual layer outputs by 1/√N where N = number of layers.
```

### 2.4 Universal Approximation Theorem

```
Theorem: A neural network with ONE hidden layer and enough neurons can
approximate any continuous function to arbitrary precision.

But: "enough neurons" might be exponentially many!
Depth helps: deep narrow networks can represent functions that shallow 
wide networks need exponentially many neurons for.

This is why depth matters: GPT-4 has 120 layers, not 1 layer with 1 trillion neurons.
Each layer builds progressively more abstract representations:
  Layer 1: character patterns
  Layer 10: word meanings
  Layer 50: sentence structure
  Layer 100: reasoning patterns
```

---

## 3. Training Deep Networks

### 3.1 Backpropagation (The Algorithm)

```
Forward pass: compute output and loss
  x → h₁ = f₁(W₁x) → h₂ = f₂(W₂h₁) → ... → L = loss(hₙ, y)

Backward pass: compute gradients using chain rule, layer by layer
  ∂L/∂Wₙ → ∂L/∂Wₙ₋₁ → ... → ∂L/∂W₁

Key insight: you compute each gradient ONCE and pass it backward.
  Time complexity = O(forward pass)
  Space complexity = O(activations) — must store all intermediate values!

This storage requirement is why training needs MORE memory than inference.
GPT-3 inference: ~350GB. GPT-3 training: ~1.5TB+ (activations + gradients + optimizer state).
```

### 3.2 Vanishing and Exploding Gradients

```
Vanishing gradient:
  gradient = ∂L/∂W₁ = (∂L/∂hₙ) × (∂hₙ/∂hₙ₋₁) × ... × (∂h₂/∂h₁) × (∂h₁/∂W₁)
  
  If each ∂hᵢ/∂hᵢ₋₁ < 1: product → 0 exponentially (gradient vanishes)
  sigmoid derivative max = 0.25, so: 0.25^50 ≈ 10⁻³⁰ → gradient is ZERO
  Layer 1 never learns!

Exploding gradient:
  If each factor > 1: product → ∞ exponentially
  Weights become NaN → training fails

Solutions:
  - ReLU activation (derivative = 1 for positive values — gradient doesn't shrink)
  - Residual connections: gradient flows DIRECTLY through skip connection
  - LayerNorm: keeps activations in reasonable range
  - Gradient clipping: cap gradient magnitude (if ||g|| > threshold, g = g × threshold/||g||)
  - Proper initialization (He/Xavier)
```

### 3.3 Regularization Techniques

```
Dropout:
  Training: randomly zero out neurons with probability p
  Inference: use all neurons, scale by (1-p)
  Effect: ensemble of sub-networks, prevents co-adaptation
  Note: NOT used in modern LLMs (GPT-3+) — they're already undertrained

Weight decay (L2):
  loss = cross_entropy + λ × Σ wᵢ²
  Penalizes large weights → simpler model → less overfitting
  Used in: AdamW (decoupled weight decay), ALL modern training

Label smoothing:
  Instead of hard targets [0, 0, 1, 0]: use [0.033, 0.033, 0.9, 0.033]
  Prevents overconfident predictions, improves generalization
  Used in: transformer training (original paper uses 0.1 smoothing)

Data augmentation:
  For images: flip, rotate, crop, color jitter
  For text: synonym replacement, back-translation, random deletion
  For LLMs: the training data IS the augmentation (internet-scale variety)
```

### 3.4 Batch Size and Learning Rate Relationship

```
Rule of thumb: if you double batch size, multiply learning rate by √2
  (Linear scaling rule, used in training large models)

Small batch (32-128):
  - More noise in gradients → better generalization (implicit regularization)
  - More parameter updates per epoch → can converge faster
  - Fits in single GPU memory

Large batch (1024-millions):
  - Less noise → smoother convergence but might find sharper minima
  - Fewer updates per epoch → needs higher learning rate to compensate
  - Distributed across many GPUs (data parallelism)

LLM training: batch sizes of 1M-4M tokens
  GPT-3: 3.2M tokens per batch, 300B tokens total, ~300,000 steps
```

---

## 4. Convolutional Neural Networks (CNNs)

#### Why Learn This for GenAI?

CNNs are the backbone of vision models (CLIP, GPT-4V, DALL-E). Understanding convolutions is essential for multi-modal AI.

### 4.1 Convolution Operation

```
Input: image (H × W × C channels)
Kernel/Filter: small matrix (e.g., 3×3×C)
Output: slide kernel over input, compute dot product at each position

Why convolution works for images:
  1. LOCAL patterns: edges, textures are local (don't need full image)
  2. TRANSLATION invariance: a cat in top-left = same features as cat in bottom-right
  3. PARAMETER sharing: same kernel applied everywhere → fewer parameters

Hierarchy of learning:
  Layer 1: edges, colors, textures (3×3 patterns)
  Layer 3: shapes, parts (eyes, wheels, letters)
  Layer 5+: objects, scenes, concepts (faces, cars, text)
```

### 4.2 Key CNN Architectures

```
LeNet (1998): 5 layers, MNIST digits — proved CNNs work
AlexNet (2012): 8 layers, ImageNet — deep learning revolution (GPU + dropout + ReLU)
VGG (2014): 19 layers, small 3×3 filters — "deeper is better"
ResNet (2015): 152 layers — residual connections solve vanishing gradients
EfficientNet (2019): NAS-designed, scales width/depth/resolution together

For GenAI:
  Vision Transformer (ViT): patches of image → treated as "tokens" → transformer
  CLIP: CNN image encoder + transformer text encoder → shared embedding space
  This is how GPT-4V "sees" images — via a vision encoder (ViT/CNN) → embeddings → transformer
```

### 4.3 Transfer Learning with CNNs

```
Pretrained model (e.g., ResNet trained on ImageNet → 1M images, 1000 classes):
  - Lower layers: generic features (edges, textures) — KEEP
  - Upper layers: task-specific features (dog breeds) — REPLACE

Transfer learning:
  1. Load pretrained model
  2. Replace final layer (1000 classes → your classes)
  3. Freeze lower layers (don't update their weights)
  4. Train only upper layers on YOUR data (100-1000 images is enough!)

This is the SAME principle as fine-tuning LLMs:
  - Base model learned general language → KEEP
  - Fine-tune for your specific task with small data → UPDATE top layers (or LoRA)
```

---

## 5. Recurrent Neural Networks (RNNs)

#### Why Learn This for GenAI?

RNNs are the predecessors to transformers. Understanding WHY they failed explains WHY attention was invented. Interview question: "Why did transformers replace RNNs?"

### 5.1 Basic RNN

```
h_t = tanh(W_hh × h_{t-1} + W_xh × x_t + b)
y_t = W_hy × h_t + b_y

For each token in sequence:
  1. Take previous hidden state h_{t-1}
  2. Combine with current input x_t
  3. Produce new hidden state h_t
  4. Optionally produce output y_t

Problems:
  - SEQUENTIAL: must process token 1 before token 2 before token 3...
    → Can't parallelize! Training on long sequences is SLOW.
  - VANISHING GRADIENT: after 20-50 tokens, early inputs are "forgotten"
    → Can't learn long-range dependencies (pronoun to antecedent 100 words away)
  - Fixed-size hidden state: ALL information about the past compressed into one vector
    → Information bottleneck for long sequences
```

### 5.2 LSTM (Long Short-Term Memory)

```
The gates mechanism (solving vanishing gradients):

  Forget gate:  f_t = sigmoid(W_f × [h_{t-1}, x_t])   "What to forget?"
  Input gate:   i_t = sigmoid(W_i × [h_{t-1}, x_t])   "What to add?"
  Cell update:  c̃_t = tanh(W_c × [h_{t-1}, x_t])     "What's the new info?"
  Cell state:   c_t = f_t ⊙ c_{t-1} + i_t ⊙ c̃_t     "Updated memory"
  Output gate:  o_t = sigmoid(W_o × [h_{t-1}, x_t])   "What to output?"
  Hidden state: h_t = o_t ⊙ tanh(c_t)                 "Output"

Why LSTM works:
  - Cell state c_t flows through time with minimal transformation
  - Gradient flows DIRECTLY through c_t (like a highway)
  - Gates learn WHAT to remember and WHAT to forget
  - Can theoretically learn dependencies 100+ tokens away

Still limited:
  - Sequential processing (can't parallelize)
  - In practice struggles beyond ~500 tokens
  - This is why transformers won (parallel + unlimited context theoretically)
```

### 5.3 Why Transformers Replaced RNNs (Interview Must-Know)

```
| Feature | RNN/LSTM | Transformer |
|---------|----------|-------------|
| Parallelization | Sequential (O(n) time) | Fully parallel (O(1) with enough GPUs) |
| Long-range deps | Degrades after 100-500 tokens | Theoretically unlimited (128K+ tokens) |
| Training speed | Slow (can't parallelize across time) | Fast (attention is matrix multiply) |
| Context access | Must flow through all intermediate states | Direct access to any position |
| Memory | Fixed-size hidden state (bottleneck) | Grows with sequence length |
| Hardware fit | Poor GPU utilization | Matrix multiply = perfect for GPUs |

The key insight: attention lets every token look at every other token DIRECTLY.
  RNN token 100 must pass info through 99 intermediate states.
  Transformer token 100 looks directly at token 1 (one matrix multiply).
```

---

## 6. Attention Mechanism

### 6.1 Attention Intuition

```
Problem: in machine translation, the decoder needs different parts of the input
at different steps. "I love cats" → "J'aime les chats"
  - When generating "J'aime", focus on "I love"
  - When generating "chats", focus on "cats"

Attention: learn to FOCUS on relevant parts of the input.

Analogy: you're in a library (values) looking for information (query).
  The books have titles (keys). You check which titles match your question,
  then read those books most carefully (weighted sum of values).
```

### 6.2 Attention Mechanisms Taxonomy

```
Bahdanau attention (2014, additive):
  score(h_decoder, h_encoder) = Vᵀ × tanh(W₁h_d + W₂h_e)
  First attention for NMT. Additive (slower but expressive).

Luong attention (2015, multiplicative):
  score(h_d, h_e) = h_dᵀ × W × h_e
  Faster (matrix multiply), simpler.

Scaled dot-product attention (2017, Transformer):
  score(Q, K) = QKᵀ / √d_k
  Even simpler, highly parallelizable, the one everyone uses.
  This IS the attention in GPT/Claude/all modern models.

Multi-head attention: run H parallel attention heads
  Each head specializes in different relationships.
  
Cross-attention: Q from one sequence, K,V from another
  Used in: encoder-decoder models, image captioning, RAG retrieval augmentation.

Self-attention: Q, K, V all from the same sequence
  Used in: GPT, BERT, Claude (the core mechanism).
```

### 6.3 Attention Complexity and Optimizations

```
Standard attention: O(n²) time and space (n = sequence length)
  For n = 128K tokens: 128K × 128K = 16 BILLION attention entries!
  This is the bottleneck for long-context models.

Optimizations:
  Flash Attention: reorganizes computation for GPU memory hierarchy
    Same result, but 2-4x faster and uses O(n) memory instead of O(n²)
    Used by: ALL modern LLM inference engines

  Sparse attention: only attend to subset of positions
    Local: attend to nearby tokens (±256 window)
    Strided: attend to every k-th token
    Used by: Longformer, BigBird

  Grouped-Query Attention (GQA): share K,V across groups of heads
    Instead of H separate K,V: use H/G shared K,V (G groups)
    Llama 2/3 uses GQA with G=8 (reduces KV cache size 8x)
    
  Multi-Query Attention (MQA): ALL heads share ONE K,V
    Fastest inference, slight quality loss.
    Used by: Falcon, PaLM-2
```

---

## 7. Transformers

### 7.1 Architecture Overview

```
Original Transformer (2017, "Attention Is All You Need"):

ENCODER (understands input):
  Input embedding + positional encoding
  × N encoder blocks:
    - Multi-head self-attention (bidirectional — sees all tokens)
    - Feed-forward network (2 linear layers + GELU)
    - Residual connections + LayerNorm after each sub-layer

DECODER (generates output):
  Output embedding + positional encoding
  × N decoder blocks:
    - MASKED self-attention (causal — only sees past tokens)
    - Cross-attention (attend to encoder output)
    - Feed-forward network
    - Residual connections + LayerNorm

Three model families emerged:
  Encoder-only (BERT): bidirectional, for understanding/classification
  Decoder-only (GPT): autoregressive, for generation
  Encoder-decoder (T5, BART): for seq-to-seq (translation, summarization)
  
Winner (2024+): DECODER-ONLY dominates (GPT, Claude, Llama, Mistral, Gemini)
  Why? Simpler architecture, scales better, generation is the primary task.
```

### 7.2 Key Components Explained

```
RESIDUAL CONNECTIONS: output = layer(x) + x
  Why: gradients flow directly through the "+" (shortcut path)
  Without them: 96-layer network is untrainable (gradients vanish)
  With them: information/gradients bypass layers that aren't useful

LAYER NORMALIZATION: normalize across feature dimension
  LN(x) = γ × (x - μ) / √(σ² + ε) + β
  Where μ, σ are computed across features (not batch)
  
  Pre-norm (modern, GPT-2+): LN → Attention → residual
  Post-norm (original): Attention → residual → LN
  Pre-norm trains more stably (gradients are better conditioned)

FEED-FORWARD NETWORK: two linear layers with non-linearity
  FFN(x) = W₂ × GELU(W₁ × x + b₁) + b₂
  
  Dimensions: d_model → 4×d_model → d_model
  
  Why 4x expansion? This is where "knowledge" is stored.
  The FFN acts as a key-value MEMORY:
    W₁ encodes "if input matches pattern P" (key matching)
    W₂ encodes "then output fact F" (value retrieval)
  
  This is why 70% of model parameters are in FFN layers!
```

### 7.3 Positional Encoding Methods

```
Sinusoidal (original, 2017):
  Fixed mathematical pattern. Works but can't extrapolate.

Learned (BERT, GPT-2):
  Trainable embedding per position. Limited to max training length.

RoPE (Rotary Positional Embedding — dominant in 2024+):
  Rotates Q, K vectors by position-dependent angle.
  Encodes RELATIVE position (not absolute).
  Can extrapolate to longer sequences than trained on.
  Used by: Llama, Mistral, Qwen, most open models.

ALiBi (Attention with Linear Biases):
  Adds linear bias to attention scores based on distance.
  No learned parameters. Natural length extrapolation.
  Used by: BLOOM, MPT.
```

---

## 8. Pre-Training & Transfer Learning

### 8.1 Pre-Training Objectives

```
MASKED LANGUAGE MODEL (BERT):
  Mask 15% of tokens, predict them from context.
  "The [MASK] sat on the [MASK]" → predict "cat", "mat"
  Bidirectional: sees both left and right context.
  Good for: understanding, classification, entity extraction.

CAUSAL LANGUAGE MODEL (GPT):
  Predict the next token, only seeing left context.
  "The cat sat on the" → predict "mat"
  Autoregressive: generates one token at a time.
  Good for: generation, few-shot learning, reasoning.

SPAN CORRUPTION (T5):
  Replace spans with sentinel tokens, predict the spans.
  "The <X> sat on the <Y>" → "<X> cat <Y> mat"
  Encoder-decoder: good for seq-to-seq tasks.

Why pre-training works:
  By predicting text, the model learns:
  - Grammar and syntax (which words follow which)
  - Semantics (word meanings from context)
  - World knowledge (facts mentioned in training data)
  - Reasoning patterns (from examples in training data)
  
  This is "compressed internet" — the model stores patterns from trillions of tokens.
```

### 8.2 Scaling Laws (Chinchilla)

```
Kaplan scaling laws (2020, OpenAI):
  Performance improves predictably with: model size, data size, compute.
  Loss ∝ N^(-0.076) (N = parameters)
  → 10x more parameters = measurably lower loss

Chinchilla scaling (2022, DeepMind):
  For compute-optimal training:
    Tokens ≈ 20 × Parameters
  
  GPT-3: 175B params, 300B tokens (undertrained by Chinchilla!)
  Llama 2: 70B params, 2T tokens (properly trained)
  Llama 3: 70B params, 15T tokens (overtrained for cheaper inference)

  Industry implication: training longer on more data gives you a SMALLER
  model that performs as well as a larger undertrained one.
  Smaller model = cheaper inference = better business economics.
```

### 8.3 Emergent Abilities

```
As models scale, abilities EMERGE that weren't present in smaller models:

  10B params: basic language understanding, simple Q&A
  50B params: few-shot learning works, basic reasoning
  100B+ params: chain-of-thought reasoning, code generation, math
  500B+ params: complex multi-step reasoning, creative writing, planning

Why emergence matters for engineers:
  - You can't predict what a larger model can do from a smaller one
  - This is why GPT-4 "surprised" even OpenAI researchers
  - It's also why you should ALWAYS test with the actual model (not smaller proxy)
```

---

## 9. Large Language Models (LLMs)

### 9.1 LLM Architecture (GPT-style)

```
GPT architecture (all modern LLMs):
  1. Token embedding: vocab → d_model (50K → 4096 for Llama)
  2. Positional encoding (RoPE)
  3. N transformer decoder blocks (32 for 7B, 80 for 70B, 120+ for GPT-4)
  4. Final LayerNorm
  5. Linear projection: d_model → vocab_size (4096 → 50K)
  6. Softmax → probability over next token

Key hyperparameters by model size:
  | Model | Params | d_model | Heads | Layers | Context |
  |-------|--------|---------|-------|--------|---------|
  | GPT-2 | 1.5B | 1600 | 25 | 48 | 1024 |
  | Llama 7B | 7B | 4096 | 32 | 32 | 4096 |
  | Llama 70B | 70B | 8192 | 64 | 80 | 8192 |
  | GPT-4 | ~1.8T* | ~12288 | ~96 | ~120 | 128K |
  (* = mixture of experts, not all active)
```

### 9.2 Tokenization

```
Why not characters? "hello" = 5 tokens. Too many steps for generation.
Why not words? "unforgettable" must be one token. Can't handle new words.
Solution: SUBWORD tokenization (BPE, SentencePiece)

BPE (Byte-Pair Encoding):
  1. Start with individual characters
  2. Find most frequent pair → merge into one token
  3. Repeat until vocabulary size reached (32K-100K)
  
  "unhappiness" → ["un", "happiness"] → ["un", "happ", "iness"]
  
  Pro: handles any word (new words split into known subwords)
  Con: 1 word = 1-4 tokens typically (not intuitive)

Vocabulary sizes:
  GPT-4: ~100K tokens
  Llama: ~32K tokens
  Claude: ~100K tokens

Token ≈ 4 characters ≈ 0.75 words (rough rule of thumb for English)
```

### 9.3 Context Window and KV Cache

```
Context window: maximum input + output tokens
  GPT-4: 128K (≈ 300 pages of text)
  Claude: 200K (≈ 500 pages)
  Gemini: 1M tokens (≈ entire codebases)

KV Cache (Key-Value Cache):
  Problem: generating token N requires attention over all N-1 previous tokens.
           Without caching: regenerate K,V for all previous tokens every step → O(n²) per token!
  
  Solution: cache K,V from previous steps, only compute K,V for new token.
           Generation becomes O(n) per token (just one new row of attention).
  
  Memory cost: KV cache = 2 × layers × heads × d_head × sequence_length × batch × dtype
    For Llama 70B, 4096 context: ~80GB of KV cache per batch!
    This is why inference needs expensive GPUs (memory-bound, not compute-bound).

Grouped-Query Attention (GQA): shares K,V across head groups
  Reduces KV cache by 8x → enables longer contexts at same memory budget.
```

### 9.4 Mixture of Experts (MoE)

```
Idea: not all parameters active for every token.
  Standard model: every token uses ALL 70B parameters.
  MoE model: each token activates SOME experts (e.g., 2 out of 8).

Architecture:
  Replace FFN with: Router → Expert₁, Expert₂, ..., Expert₈
  Router decides: "this token should use Expert 3 and Expert 7"
  Only those 2 experts compute → 8x fewer FLOPs per token!

Mixtral 8x7B:
  - 8 experts, each 7B parameters = 56B total parameters
  - But only 2 experts active per token = ~12B compute per token
  - Performance ≈ Llama 70B but 5x faster inference!

GPT-4: rumored to be MoE with 8 experts × ~220B each = 1.8T total
  Active per token: ~220B (explaining its speed despite massive size)
```

---

## 10. Fine-Tuning Techniques

### 10.1 Full Fine-Tuning

```
Update ALL model parameters on task-specific data.
  
  Pro: maximum performance, model fully adapts
  Con: expensive (needs full model in GPU memory × 3 for AdamW states)
  Memory: 70B model needs ~420GB for full fine-tuning (7B × 2 bytes × 3 copies)
  
  When to use: you have massive compute and lots of data (>100K examples)
```

### 10.2 LoRA (Low-Rank Adaptation)

```
Key insight: weight updates during fine-tuning are LOW RANK.
  Instead of updating W (d×d), add ΔW = A×B where A(d×r), B(r×d), r<<d

For each attention/FFN weight matrix:
  W' = W + (α/r) × A × B    (W frozen, only A and B trained)
  
  r = rank (4, 8, 16 typical). Lower = fewer params, less expressiveness.
  α = scaling factor (typically = r, so effective scale = 1)

Benefits:
  - Parameters: 0.1-1% of full model (train 7M params for a 7B model)
  - Memory: fits on single GPU (A100 80GB can fine-tune 70B with LoRA)
  - Speed: 3-10x faster than full fine-tuning
  - Storage: adapter weights are ~100MB (not 140GB for full model)
  - Merge: final model = original + merged adapters (zero inference overhead)

QLoRA: LoRA + 4-bit quantized base model
  Fine-tune 70B model on a single 48GB GPU!
  NF4 quantization for base weights + LoRA adapters in fp16.
```

### 10.3 Instruction Tuning

```
Goal: teach the model to follow instructions (not just predict next token).

Data format:
  {"instruction": "Summarize this article", 
   "input": "The article text...", 
   "output": "The summary..."}

Key datasets:
  - Stanford Alpaca (52K instructions, generated by GPT-4)
  - OpenOrca (1M+ instructions, diverse tasks)
  - ShareGPT (conversations from ChatGPT users)

Effect: base model (autocomplete) → instruction model (assistant)
  Base: "What is Python?" → "What is Python used for? What is Python 3.12?"
  Instruct: "What is Python?" → "Python is a programming language..."

Industry insight: instruction tuning is CHEAP (50K examples, few hours)
but makes the model dramatically more useful. All production models are instruction-tuned.
```

---

## 11. Generative Models

### 11.1 Autoregressive (GPT)

```
P(text) = P(t₁) × P(t₂|t₁) × P(t₃|t₁,t₂) × ...

Generate one token at a time, each conditioned on all previous.
  Pro: simple, scales well, best for text generation
  Con: slow generation (must run full model per token)
       errors accumulate (wrong token → wrong context → more wrong tokens)
```

### 11.2 GANs (Generative Adversarial Networks)

```
Two networks play a game:
  Generator G: creates fake data (noise → image)
  Discriminator D: classifies real vs fake

Training:
  D tries to maximize: log(D(real)) + log(1-D(G(noise)))  (detect fakes)
  G tries to minimize: log(1-D(G(noise)))  (fool discriminator)

Problems:
  - Mode collapse (generator only produces one type of output)
  - Training instability (hard to balance G and D)
  - Mostly replaced by diffusion models (2022+) for image generation

Still used for: super-resolution, style transfer, data augmentation.
```

### 11.3 Diffusion Models (DALL-E, Stable Diffusion, Midjourney)

```
Forward: gradually add noise to image (T steps)
  x_t = √(ᾱ_t)x₀ + √(1-ᾱ_t)ε     (ε ~ N(0,I))

Reverse: learn to denoise step by step
  Model predicts noise: ε_θ(x_t, t, condition)
  Remove predicted noise: x_{t-1} = denoise(x_t, ε_θ)

Training: L = E[||ε - ε_θ(x_t, t)||²]  (predict added noise)

Conditioning (text-to-image):
  Add text embedding (from CLIP) as input to the denoiser.
  Model learns: "given noisy image + text description → remove noise in a way
                 that makes the image match the text"

Classifier-free guidance:
  score = (1+w)×ε_θ(x_t, text) - w×ε_θ(x_t, ∅)
  w = guidance scale (7-12 typical)
  Higher w = follows text more closely (but less diversity)
```

### 11.4 VAE (Variational Autoencoder)

```
Encoder: x → μ, σ (parameters of latent distribution)
Latent: z = μ + σ × ε    (ε ~ N(0,1), reparameterization trick)
Decoder: z → x̂ (reconstruction)

Loss = ||x - x̂||² + KL(N(μ,σ²) || N(0,1))
     = reconstruction + regularization

Used in: Stable Diffusion (latent diffusion = diffusion in VAE's latent space → 
64x fewer pixels to denoise → much faster!)
```

---

## 12. Reinforcement Learning from Human Feedback (RLHF)

### 12.1 Why RLHF Exists

```
Problem with pre-training + instruction tuning:
  Model can generate text, but may:
  - Be harmful/toxic (learned from internet)
  - Hallucinate confidently
  - Be verbose when concise answer is better
  - Refuse to answer safe questions (over-cautious)
  
RLHF aligns the model with HUMAN PREFERENCES (helpful, harmless, honest).
This is what makes ChatGPT feel different from raw GPT-3.
```

### 12.2 The RLHF Pipeline

```
Step 1: Supervised Fine-Tuning (SFT)
  Train on high-quality demonstrations by humans.
  "Here's what good responses look like."

Step 2: Reward Model Training
  Collect comparison data: "Given prompt, is Response A or B better?"
  Train a model to predict human preferences: R(prompt, response) → score
  
  Data: ~100K comparisons from human raters.

Step 3: RL Optimization (PPO)
  Generate responses with the SFT model.
  Score them with the reward model.
  Update the model to maximize reward (with KL penalty).
  
  Objective: max E[R(response)] - β × KL(π_new || π_SFT)
  
  "Generate responses that humans prefer, without straying too far from SFT model"
```

### 12.3 DPO (Direct Preference Optimization — Replacing PPO)

```
DPO insight: you don't need a separate reward model or RL algorithm.
  Directly optimize the LLM from preference data.

Loss: L = -log(σ(β × (log π(y_w|x)/π_ref(y_w|x) - log π(y_l|x)/π_ref(y_l|x))))

Where:
  y_w = preferred response
  y_l = rejected response
  π = model being trained
  π_ref = reference model (SFT checkpoint)
  β = strength of KL constraint

Why DPO is winning (2024+):
  - Simpler (no reward model, no PPO infrastructure)
  - More stable (no RL training instability)
  - Cheaper (single training pass, not RL loop)
  - Used by: Llama 3, Mistral, many open models
```

---

## 13. Model Compression & Efficiency

### 13.1 Quantization

```
Reduce precision of weights: float32 → float16 → int8 → int4

fp32: 4 bytes per parameter. 70B model = 280GB ← doesn't fit on any single GPU!
fp16: 2 bytes per parameter. 70B model = 140GB ← fits on 2× A100 80GB
int8: 1 byte per parameter.  70B model = 70GB  ← fits on 1× A100
int4: 0.5 bytes per parameter. 70B model = 35GB ← fits on consumer GPU!

Quality vs compression:
  fp16: no quality loss (training precision)
  int8 (GPTQ/AWQ): ~0.5% quality loss, 2x smaller
  int4 (GGUF/AWQ): ~2-5% quality loss, 4x smaller
  
Industry practice: serve int4/int8 for inference (massive cost savings),
train in fp16/bf16 (need full precision for gradient updates).
```

### 13.2 Knowledge Distillation

```
Teacher: large, expensive model (GPT-4)
Student: small, fast model (GPT-4o-mini)

Training: student learns to MIMIC teacher's output distribution
  L = α × KL(teacher_softmax || student_softmax) + (1-α) × cross_entropy(labels, student)
  
  The "soft labels" from the teacher carry MORE information than hard labels.
  Teacher predicts: P("cat")=0.7, P("dog")=0.2, P("animal")=0.1
  Hard label: just "cat"
  Soft label teaches: "cat is most likely, but dog and animal are related"

Industry example:
  GPT-4 generates responses → used to train GPT-4o-mini
  Claude 3 Opus outputs → train Claude Haiku
  This is how companies create fast/cheap models with large model quality.
```

### 13.3 Pruning and Sparsity

```
Structured pruning: remove entire neurons/attention heads/layers
  If a head contributes little → remove it (fewer params, faster)
  
Unstructured pruning: set individual weights to 0 (sparse matrices)
  Magnitude pruning: remove weights with smallest |w|
  
  Observation: 90% of weights can be pruned with minimal quality loss
  (lottery ticket hypothesis: there's a small sub-network that works as well)
  
  But: sparse matrices are hard to accelerate on GPUs (need special hardware/software).
  
Industry: speculative decoding is more impactful than pruning currently.
```

### 13.4 Speculative Decoding

```
Problem: LLM generation is slow because each token requires full model forward pass.

Solution: use a SMALL model to draft K tokens, then verify with LARGE model in parallel.
  
  1. Small model (1B params) drafts 5 tokens quickly
  2. Large model (70B params) verifies all 5 in ONE forward pass
  3. Accept all correct tokens, resample from the first incorrect one
  
  Speed: 2-3x faster generation with ZERO quality loss!
  (Large model's output distribution is preserved exactly)

Used by: vLLM, TGI, Claude (internally), GPT-4 (likely).
```

---

## 14. Practical ML Engineering

### 14.1 Data Quality > Model Size

```
"Garbage in, garbage out" applies 10x for ML.

Data quality hierarchy:
  1. Relevant (about the right topic)
  2. Correct (factually accurate)
  3. Diverse (covers edge cases, not just common cases)
  4. Clean (no duplicates, no contradictions, no formatting issues)
  5. Well-labeled (human annotations are consistent)

Industry examples:
  - Llama 3: trained on 15T tokens but heavily filtered for quality
    (only 5% of internet text passes their quality filter)
  - Phi models (Microsoft): tiny models trained on "textbook-quality" synthetic data
    match models 10x larger trained on noisy internet data
```

### 14.2 ML System Design Patterns

```
Feature Pipeline: Raw data → features → feature store → model
  Batch features: computed offline (daily user aggregates)
  Real-time features: computed on request (current session behavior)

Training Pipeline: Data → preprocess → train → evaluate → register → deploy
  Automated retraining on schedule (daily/weekly)
  A/B testing before full deployment

Inference Pipeline: Request → preprocess → predict → postprocess → response
  Online: real-time prediction (10-100ms)
  Batch: process millions of records overnight
  
Monitoring: track data drift, model drift, performance metrics
  Alert if: prediction distribution shifts, accuracy drops, latency increases
```

### 14.3 Common Failure Modes

```
Data leakage: training data contains information from the future
  "Predict tomorrow's stock price" but training data includes tomorrow's news
  Fix: strict temporal splits, careful feature engineering

Overfitting: memorizes training data, fails on new data
  Signs: training loss goes down, validation loss goes UP
  Fix: more data, regularization, early stopping, simpler model

Underfitting: model too simple to capture patterns
  Signs: both training and validation loss are high
  Fix: more parameters, more training, better features

Distribution shift: real-world data differs from training data
  Example: model trained on English reviews, deployed in multilingual market
  Fix: monitor prediction distributions, retrain on new data regularly

Feedback loops: model predictions influence future training data
  Example: recommendation system only shows popular items → only gets data on popular items
  Fix: exploration (show some random items), counterfactual evaluation
```

---

## 15. Interview Deep Dives

### 15.1 "Explain how GPT generates text" (Complete Answer)

```
1. Input text is tokenized using BPE into subword tokens
2. Tokens are converted to embeddings (lookup table, d=4096)
3. Positional encoding (RoPE) is added to embeddings
4. The sequence passes through N transformer decoder blocks:
   - LayerNorm
   - Multi-head causal self-attention (masked: can't see future)
     - Q, K, V computed for each token
     - Attention scores = QKᵀ/√d, with future positions masked to -∞
     - Softmax → attention weights
     - Weighted sum of V → attention output
   - Residual connection
   - LayerNorm
   - FFN (expand 4x, GELU, project back)
   - Residual connection
5. Final LayerNorm
6. Linear projection to vocabulary size (50K-100K)
7. Divide by temperature, apply top-p filtering
8. Softmax → probability distribution
9. Sample next token from distribution
10. Append to sequence, repeat from step 2
```

### 15.2 "Why is self-attention O(n²) and what are the solutions?"

```
Self-attention: every token attends to every other token.
  Attention matrix: n × n (n = sequence length)
  For n=128K: 16 billion entries → 32GB in fp16 (JUST for attention weights!)

Solutions:
  1. Flash Attention: same math, but chunked for GPU memory hierarchy → 2-4x faster
  2. Sparse attention: only attend to subset (local window + stride) → O(n√n) or O(n·log(n))
  3. Linear attention: approximate softmax(QKᵀ) with kernel tricks → O(n)
  4. Ring attention: distribute across GPUs, each processes a chunk
  5. GQA/MQA: reduce K,V heads → smaller attention matrices

In practice (2025): Flash Attention + GQA handles 128K+ contexts efficiently.
True O(n) attention hasn't matched quality of full attention yet.
```

### 15.3 "What is the difference between BERT and GPT?"

```
BERT (Bidirectional Encoder):
  - Sees ALL tokens (both left and right context)
  - Trained with masked language model (predict [MASK]ed tokens)
  - Good for: understanding, classification, entity extraction
  - Can't generate text (no autoregressive capability)
  - Used for: search ranking, sentiment analysis, NER

GPT (Causal Decoder):
  - Sees only LEFT context (causal mask)
  - Trained with next-token prediction
  - Good for: text generation, reasoning, few-shot learning
  - Can also understand (but less efficient than BERT for classification)
  - Used for: ChatGPT, coding assistants, summarization

Why GPT won: generation is harder than understanding, and GPT can do both
(use it for classification by generating the label). BERT can only understand.
Also: scaling laws favor decoder-only (simpler architecture scales more predictably).
```

### 15.4 "Explain the training process for ChatGPT"

```
Phase 1: Pre-training (months, millions of dollars)
  Data: trillions of tokens from internet, books, code
  Objective: next-token prediction (causal language model)
  Result: base model that can autocomplete text but isn't "helpful"

Phase 2: Supervised Fine-Tuning (SFT) (days)
  Data: ~100K high-quality demonstrations by human contractors
  Format: (instruction, response) pairs showing ideal behavior
  Result: model follows instructions, answers questions

Phase 3: Reward Modeling (days)
  Data: ~300K comparison pairs (human rates which response is better)
  Train: reward model R(prompt, response) → scalar score
  
Phase 4: RLHF / DPO (days-weeks)
  Optimize: model generates responses, scored by reward model
  Objective: maximize reward - β × KL(from SFT model)
  Result: model aligned with human preferences (helpful, harmless, honest)

Phase 5: Safety training and red-teaming
  Find failure modes, add safety guardrails, iterate

Total training cost (GPT-4 scale): estimated $50-100M
```

### 15.5 "What is hallucination and how to reduce it?"

```
Hallucination: model generates text that sounds confident but is factually wrong.

Why it happens:
  1. Training data conflicts (internet has wrong info too)
  2. Model optimizes for "plausible next token" not "true next token"
  3. No mechanism to say "I don't know" (always generates something)
  4. Long context + rare facts → model interpolates (makes stuff up)

Reduction strategies:
  1. RAG (ground generation in retrieved documents)
  2. Self-consistency (generate multiple answers, check agreement)
  3. Citation enforcement (model must cite sources)
  4. Confidence calibration (model outputs confidence score)
  5. Knowledge cutoff awareness (model says "I'm not sure about events after...")
  6. Smaller context (less chance of confusing facts from different documents)
  7. Fine-tuning on factual data (teach model to be precise)
  8. Constitutional AI (model checks its own output for accuracy)
```

### 15.6 Quick-Fire Interview Questions

```
Q: What is the difference between parameters and hyperparameters?
A: Parameters are learned (weights). Hyperparameters are set by you (learning rate, layers).

Q: Why is softmax used in the output layer?
A: Converts raw logits to a valid probability distribution (positive, sums to 1).

Q: What is teacher forcing?
A: During training, feed the CORRECT previous token (not model's prediction).
   Enables parallel training of all positions simultaneously.

Q: What is the difference between epoch, batch, and iteration?
A: Epoch = one pass through entire dataset. Batch = subset processed together.
   Iteration = one batch processed = one gradient update.

Q: Why use mini-batches instead of full dataset?
A: Faster updates, regularization effect (noise helps generalization),
   fits in GPU memory.

Q: What is gradient clipping?
A: Cap gradient magnitude: if ||g|| > threshold, scale it down.
   Prevents exploding gradients (especially in RNNs and early transformer training).

Q: What is catastrophic forgetting?
A: Fine-tuning on new task makes model forget old abilities.
   Solution: LoRA (minimal parameter changes), replay, multi-task training.

Q: What is the lottery ticket hypothesis?
A: Large networks contain sparse sub-networks ("winning tickets") that alone
   can match full network performance. Finding them efficiently is still an open problem.

Q: Why do larger models do few-shot learning?
A: Not fully understood. Theory: large models learn "in-context learning algorithms"
   during pre-training — they learn to learn from examples in the prompt.

Q: What is mixture of experts and why does it help?
A: Route each token to a subset of "expert" sub-networks.
   Total params are huge (more knowledge), but active params per token are small (fast).
   Best of both: high quality + fast inference.
```

---

## Quick Reference: The Full Stack from Data to Deployment

```
DATA → FEATURES → MODEL → TRAINING → EVALUATION → DEPLOYMENT → MONITORING

Classical ML:
  Data → Feature engineering → XGBoost/RF → Train/val split → Accuracy/F1 → API → Drift detection

Deep Learning:
  Data → Preprocessing → Architecture design → GPU training → Loss curves → Serving (TensorRT/ONNX) → A/B testing

LLM/GenAI:
  Corpus → Tokenization → Transformer pre-training → SFT → RLHF → Evaluation (human + auto) → 
  Inference (vLLM/TGI) → RAG/Agents → Monitoring (quality + cost + latency)
```

---

*This guide covers the ML/DL foundations needed for GenAI engineering roles. The field is evolving rapidly — architecture details change, but fundamentals (backprop, attention, scaling laws, RLHF) are stable knowledge that will serve you for years.*
