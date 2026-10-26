# 01 — Math Fundamentals for AI Research

> **The mathematical foundations you need for AI research — from functions and derivatives to information theory and SVD.**
>
> 15 lessons · Code in Python/NumPy · FAANG interview-ready

---

## Table of Contents

| # | Topic | Key Idea |
|------|-------|----------|
| 01.01 | [Functions](#0101--functions) | Machines that turn inputs into outputs |
| 01.02 | [Derivatives](#0102--derivatives) | How fast is the output changing? |
| 01.03 | [Vectors](#0103--vectors) | Lists of numbers with direction |
| 01.04 | [Gradients](#0104--gradients) | Which direction to walk downhill |
| 01.05 | [Matrices](#0105--matrices) | Tables of numbers that transform space |
| 01.06 | [Derivation Rules & Examples](#0106--derivation-rules--examples) | The toolkit for computing derivatives |
| 01.07 | [The Chain Rule](#0107--the-chain-rule) | Derivatives of nested functions |
| 01.08 | [Backprop in Python](#0108--backprop-in-python) | How neural nets actually learn |
| 01.09 | [The Jacobian Matrix](#0109--the-jacobian-matrix) | Derivatives for vector-valued functions |
| 01.10 | [Hadamard Product](#0110--hadamard-product-element-wise-operations) | Element-wise multiplication |
| 01.11 | [Entropy & Information Theory](#0111--entropy--information-theory) | Measuring surprise and uncertainty |
| 01.12 | [KL Divergence](#0112--kl-divergence) | How different are two distributions? |
| 01.13 | [Singular Value Decomposition (SVD)](#0113--singular-value-decomposition-svd) | X-ray vision for matrices |
| 01.14 | [Moving Averages (EMA)](#0114--moving-averages-ema) | Smoothing noisy signals |
| 01.15 | [More Math Lessons](#0115--more-math-lessons) | Additional essential topics |

---

## How to Use This Guide

```
💡 Every section follows this pattern:

   1. INTUITION   — Plain-English "why should I care?"
   2. MATH        — The actual formula, step by step
   3. EXAMPLE     — Concrete numbers you can follow
   4. CODE        — Python you can run right now
   5. DIAGRAM     — Visual picture of what's happening
   6. FAANG TIE-IN — Where this shows up in real ML systems
```

---

# 01.01 — Functions

## Intuition

A **function** is a machine. You put something in, it does some work, and gives you something out.

```
     ┌─────────────┐
  x ─▶│  f(x) = 2x  │─▶ y
     └─────────────┘
```

**Every AI model is just a big function.** A neural network takes pixels (input), runs them through millions of tiny functions, and outputs "cat" or "dog."

## The Formal Definition

A function `f: A → B` maps every element in set A to **exactly one** element in set B.

```
f(x) = y

  - x is the INPUT  (also called the argument or independent variable)
  - y is the OUTPUT  (also called the dependent variable)
  - f is the RULE    (the recipe for turning x into y)
```

## Types of Functions You'll See in AI

### 1. Linear Functions — `f(x) = mx + b`

The simplest function. A straight line.

```
f(x) = 3x + 1

  x = 0  →  f(0) = 1
  x = 1  →  f(1) = 4
  x = 2  →  f(2) = 7
  x = 3  →  f(3) = 10
```

```
y
10 │              •
 8 │           •
 6 │        •
 4 │     •
 2 │  •
 0 ┼──────────────── x
   0  1  2  3  4
```

**In AI:** Every neuron computes `y = wx + b` (weight × input + bias). That's a linear function!

### 2. Quadratic Functions — `f(x) = x²`

A curve. This is the shape of most **loss functions**.

```
f(x) = x²

  x = -2  →  f(-2) = 4
  x = -1  →  f(-1) = 1
  x =  0  →  f(0)  = 0   ← minimum!
  x =  1  →  f(1)  = 1
  x =  2  →  f(2)  = 4
```

```
y
4 │ •           •
3 │
2 │
1 │   •       •
0 ┼─────•──────── x
  -2  -1  0  1  2
```

**In AI:** Mean Squared Error loss = `(predicted - actual)²`. Training = finding the bottom of this curve.

### 3. Exponential Function — `f(x) = eˣ`

Euler's number `e ≈ 2.718`. This function grows incredibly fast.

```python
import numpy as np

x = np.array([-2, -1, 0, 1, 2, 5, 10])
y = np.exp(x)
print(y)
# [0.135, 0.368, 1.0, 2.718, 7.389, 148.41, 22026.47]
```

**In AI:** The `softmax` function uses `eˣ` to turn raw scores into probabilities.

### 4. Sigmoid Function — `σ(x) = 1 / (1 + e⁻ˣ)`

Squashes **any number** into the range (0, 1). Perfect for probabilities.

```
         1.0 │          ___________
             │        /
         0.5 │ ─ ─ ─•─ ─ ─ ─ ─ ─
             │     /
         0.0 │____/
             ┼───────────────────── x
            -6  -3   0   3   6
```

```python
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

print(sigmoid(0))    # 0.5   ← right in the middle
print(sigmoid(10))   # 0.99  ← very confident "yes"
print(sigmoid(-10))  # 0.00  ← very confident "no"
```

**In AI:** Used in binary classification ("spam or not spam?"), gates in LSTMs, and logistic regression.

### 5. ReLU — `f(x) = max(0, x)`

The most popular activation function in deep learning. Dead simple.

```
y
 │        /
 │       /
 │      /
 │_____/
 ┼──────────── x
      0
```

```python
def relu(x):
    return np.maximum(0, x)

print(relu(-5))   # 0   ← negative? Kill it.
print(relu(0))    # 0
print(relu(3))    # 3   ← positive? Pass through.
```

**In AI:** Used in almost every hidden layer of modern neural networks. Fast, simple, works great.

### Composition of Functions (Functions Inside Functions)

This is where the **magic** of deep learning lives. Neural networks are **composed functions**:

```
Input → f₁ → f₂ → f₃ → ... → fₙ → Output

f₃(f₂(f₁(x)))    ← "3-layer network"
```

```python
# A tiny 3-layer neural network is just function composition!
def layer1(x): return relu(3*x + 1)
def layer2(x): return relu(-2*x + 5)
def layer3(x): return sigmoid(x - 2)

# Forward pass = compose the functions
x = 1.0
out = layer3(layer2(layer1(x)))
print(f"Input: {x} → Output: {out:.4f}")
# Input: 1.0 → Output: 0.2689
```

### 🏢 FAANG Interview Tie-in

> **Google/Meta interview question:** "What activation function would you use and why?"
>
> Answer: ReLU for hidden layers (fast, avoids vanishing gradients), sigmoid for binary output, softmax for multi-class output. Each is just a function applied element-wise.

---

# 01.02 — Derivatives

## Intuition

A derivative tells you **how fast something is changing**.

Imagine driving a car:
- Your **position** is the function `f(t)` (where you are at time t)
- Your **speed** is the derivative `f'(t)` (how fast position is changing)
- Your **acceleration** is the second derivative `f''(t)` (how fast speed is changing)

```
     "How steep is the hill right HERE?"

          /\
         /  \   ← steep here (big derivative)
        /    \
       /      \_____ ← flat here (derivative ≈ 0)
      /
  ___/  ← medium slope
```

## The Formal Definition

```
            f(x + h) - f(x)
f'(x) = lim ─────────────────
         h→0        h
```

Translation: "Zoom in closer and closer. The slope of the tiny line you see is the derivative."

## Step-by-Step Example

Find the derivative of `f(x) = x²`:

```
f'(x) = lim  (x + h)² - x²
         h→0  ───────────────
                    h

      = lim  x² + 2xh + h² - x²
         h→0  ─────────────────────
                      h

      = lim  2xh + h²
         h→0  ─────────
                  h

      = lim  (2x + h)
         h→0

      = 2x    ✅
```

**So if f(x) = x², then f'(x) = 2x.**

```
At x = 3:  slope = 2(3) = 6    (steep, going up fast)
At x = 0:  slope = 2(0) = 0    (flat, at the bottom)
At x = -2: slope = 2(-2) = -4  (steep, going down)
```

## Why Derivatives Matter in AI

**Training a neural network = finding the minimum of the loss function.**

The derivative tells you which direction to move to reduce the loss:

```
Loss
  │\
  │ \
  │  \     We are HERE (x)
  │   \   ↙
  │    \ •          derivative is NEGATIVE
  │     \/          → move RIGHT to decrease loss
  │      \
  │       •  ← MINIMUM (derivative = 0)
  │      /
  │     /
  ┼────────── parameter value
```

## Code: Numerical vs. Analytical Derivative

```python
import numpy as np

# ── The function ──
def f(x):
    return x ** 2

# ── Method 1: Numerical derivative (approximate) ──
def numerical_derivative(f, x, h=1e-7):
    return (f(x + h) - f(x - h)) / (2 * h)

# ── Method 2: Analytical derivative (exact) ──
def analytical_derivative(x):
    return 2 * x   # We derived this by hand above

# ── Compare ──
x = 3.0
print(f"Numerical:  {numerical_derivative(f, x):.6f}")  # 6.000000
print(f"Analytical: {analytical_derivative(x):.6f}")     # 6.000000
```

## Common Derivatives Cheat Sheet

| Function f(x) | Derivative f'(x) | Example |
|---|---|---|
| `c` (constant) | `0` | f(x) = 5 → f'(x) = 0 |
| `x` | `1` | f(x) = x → f'(x) = 1 |
| `xⁿ` | `nxⁿ⁻¹` | f(x) = x³ → f'(x) = 3x² |
| `eˣ` | `eˣ` | f(x) = eˣ → f'(x) = eˣ |
| `ln(x)` | `1/x` | f(x) = ln(x) → f'(x) = 1/x |
| `sin(x)` | `cos(x)` | f(x) = sin(x) → f'(x) = cos(x) |
| `σ(x)` (sigmoid) | `σ(x)(1-σ(x))` | Beautiful self-referential form |

### 🏢 FAANG Interview Tie-in

> **Amazon ML interview:** "What happens when gradients become very small during training?"
>
> This is the **vanishing gradient problem**. The sigmoid derivative maxes out at 0.25. Stack 100 layers: 0.25¹⁰⁰ ≈ 0. The gradient vanishes. That's why ReLU (derivative = 0 or 1) replaced sigmoid in deep networks.

---

# 01.03 — Vectors

## Intuition

A **vector** is just a list of numbers — but that list has a **direction** and a **magnitude** (length).

```
  Think of it as an ARROW in space:

  y
  4│    ↗ v = [3, 4]
  3│   /
  2│  /    length = √(3² + 4²) = 5
  1│ /
  0┼──────── x
   0 1 2 3
```

**In AI:** A word, an image, a user — EVERYTHING is represented as a vector.

- The word "king" might be `[0.2, -0.5, 0.8, ..., 0.1]` (300 numbers)
- An image might be `[pixel1, pixel2, ..., pixel784]` (784 numbers for 28×28)

## Vector Operations

### 1. Addition

```
a = [1, 2]
b = [3, 1]
a + b = [1+3, 2+1] = [4, 3]
```

```
  y
  3│    b    a+b
  2│  a ─ ─ ─ •
  1│ ↗     ↗
  0┼──────────── x
   0 1 2 3 4
```

### 2. Scalar Multiplication

```
v = [2, 3]
2v = [4, 6]    ← same direction, double length
-v = [-2, -3]  ← opposite direction
```

### 3. Dot Product (CRITICAL for AI)

```
a · b = a₁b₁ + a₂b₂ + ... + aₙbₙ

a = [1, 2, 3]
b = [4, 5, 6]
a · b = 1×4 + 2×5 + 3×6 = 4 + 10 + 18 = 32
```

**The dot product measures SIMILARITY.** Big positive = same direction. Zero = perpendicular. Negative = opposite.

```
        Similar          Perpendicular      Opposite
        a · b > 0        a · b = 0          a · b < 0
          ↗ ↗              → ↑               → ←
```

### 4. Magnitude (Length)

```
‖v‖ = √(v₁² + v₂² + ... + vₙ²)

v = [3, 4]
‖v‖ = √(9 + 16) = √25 = 5
```

### 5. Unit Vector (Normalize)

Direction without magnitude. Length = 1.

```
v̂ = v / ‖v‖

v = [3, 4],  ‖v‖ = 5
v̂ = [3/5, 4/5] = [0.6, 0.8]
```

## Code: Vector Operations

```python
import numpy as np

# Create vectors
a = np.array([1, 2, 3])
b = np.array([4, 5, 6])

# Addition
print(f"a + b = {a + b}")              # [5 7 9]

# Dot product
print(f"a · b = {np.dot(a, b)}")       # 32

# Magnitude
print(f"|a| = {np.linalg.norm(a):.4f}")  # 3.7417

# Unit vector
a_hat = a / np.linalg.norm(a)
print(f"â = {a_hat}")                    # [0.267 0.535 0.802]
print(f"|â| = {np.linalg.norm(a_hat)}")  # 1.0 ✓

# Cosine similarity — THE key similarity measure in AI
cos_sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
print(f"cos(a,b) = {cos_sim:.4f}")       # 0.9746 (very similar!)
```

## Real-World Example: Word Embeddings

```python
# Simplified word vectors (in reality these have 300+ dimensions)
king   = np.array([0.8, 0.6, -0.1, 0.9])
queen  = np.array([0.7, 0.65, 0.8, 0.85])
man    = np.array([0.9, 0.1, -0.5, 0.3])
woman  = np.array([0.8, 0.15, 0.4, 0.25])

# The famous analogy: king - man + woman ≈ queen
result = king - man + woman
print(f"king - man + woman = {result}")

# Check similarity
cos_sim = np.dot(result, queen) / (np.linalg.norm(result) * np.linalg.norm(queen))
print(f"Similarity to 'queen': {cos_sim:.4f}")
```

## Diagram: Vectors in AI Pipeline

```
┌──────────────────────────────────────────────────────────────┐
│                     THE AI VECTOR PIPELINE                    │
│                                                              │
│  Raw Data          Embedding           Vector Space           │
│  ─────────         ─────────           ────────────           │
│                                                              │
│  "cat" ──────▶ [0.2, 0.8, 0.1] ──▶    •  cat               │
│  "dog" ──────▶ [0.3, 0.7, 0.2] ──▶   •   dog               │
│  "car" ──────▶ [0.9, 0.1, 0.8] ──▶          • car           │
│                                                              │
│  cat & dog are CLOSE (similar vectors)                       │
│  car is FAR (different vector)                               │
└──────────────────────────────────────────────────────────────┘
```

### 🏢 FAANG Interview Tie-in

> **Meta/Google interview:** "How does semantic search work?"
>
> Convert queries and documents to vectors (embeddings). Find the nearest vectors using cosine similarity. That's it — the entire business of vector databases (Pinecone, Weaviate, FAISS).

---

# 01.04 — Gradients

## Intuition

A gradient is just a **vector of derivatives**. When you have a function with **multiple inputs**, the gradient tells you which direction to go to increase the function the fastest.

```
Imagine standing on a hilly terrain:

            ☁️
    ⛰️    /  \
   /   \ /    \
  /     X       \___
 /    YOU

The GRADIENT at your feet points UPHILL (steepest ascent).
To go DOWNHILL (minimize loss), go OPPOSITE to the gradient.
```

## The Math

For a function `f(x₁, x₂, ..., xₙ)`, the gradient is:

```
        ┌ ∂f/∂x₁ ┐
        │ ∂f/∂x₂ │
∇f(x) = │   ...   │
        │ ∂f/∂xₙ │
        └         ┘
```

Each `∂f/∂xᵢ` is a **partial derivative** — the derivative with respect to one variable while holding all others constant.

## Step-by-Step Example

```
f(x, y) = x² + 3xy + y²

Partial derivative with respect to x (treat y as constant):
∂f/∂x = 2x + 3y

Partial derivative with respect to y (treat x as constant):
∂f/∂y = 3x + 2y

Gradient:
∇f = [2x + 3y, 3x + 2y]

At point (1, 2):
∇f(1, 2) = [2(1) + 3(2), 3(1) + 2(2)]
         = [8, 7]
```

**This means:** At point (1,2), the function increases fastest in the direction [8, 7].

## Why Gradients = The Heart of AI Training

```
┌────────────────────────────────────────────────────────────────┐
│                    GRADIENT DESCENT                             │
│                                                                │
│  Loss                                                          │
│   │\                                                           │
│   │ \        Step 1: Compute gradient ∇L                       │
│   │  \   •←─ Step 2: Move OPPOSITE to gradient                 │
│   │   \ / ←─ Step 3: Arrive at lower loss                      │
│   │    •                                                       │
│   │     \   •←─ Repeat                                         │
│   │      \ /                                                   │
│   │       •  ← Eventually reach MINIMUM                        │
│   │                                                            │
│   ┼─────────── parameter values                                │
│                                                                │
│  Update rule:  θ_new = θ_old - α × ∇L(θ_old)                  │
│                                    ↑                           │
│                              learning rate                     │
└────────────────────────────────────────────────────────────────┘
```

## Code: Gradient Descent from Scratch

```python
import numpy as np

# ── Loss function: L(w) = (w - 3)²  (minimum at w = 3) ──
def loss(w):
    return (w - 3) ** 2

def gradient(w):
    return 2 * (w - 3)   # derivative of (w-3)²

# ── Gradient Descent ──
w = 10.0              # start far from the answer
learning_rate = 0.1
history = [w]

for step in range(20):
    grad = gradient(w)
    w = w - learning_rate * grad   # THE key update
    history.append(w)
    if step % 5 == 0:
        print(f"Step {step:2d}: w = {w:.4f}, loss = {loss(w):.4f}, grad = {grad:.4f}")

# Step  0: w = 8.6000, loss = 31.3600, grad = 14.0000
# Step  5: w = 3.4587, loss = 0.2104, grad = 1.1470
# Step 10: w = 3.0376, loss = 0.0014, grad = 0.0940
# Step 15: w = 3.0031, loss = 0.0000, grad = 0.0077
# → Converges to w ≈ 3.0 ✓
```

## 2D Gradient Descent (Multiple Parameters)

```python
import numpy as np

# ── Loss: L(x, y) = x² + y²  (minimum at origin) ──
def loss_2d(x, y):
    return x**2 + y**2

def gradient_2d(x, y):
    return np.array([2*x, 2*y])

# Start at (5, 7)
params = np.array([5.0, 7.0])
lr = 0.1

print(f"Start: ({params[0]:.2f}, {params[1]:.2f}), loss = {loss_2d(*params):.2f}")

for step in range(30):
    grad = gradient_2d(*params)
    params = params - lr * grad
    if step % 5 == 0:
        print(f"Step {step:2d}: ({params[0]:.4f}, {params[1]:.4f}), "
              f"loss = {loss_2d(*params):.6f}")

# Step  0: (4.0000, 5.6000), loss = 47.360000
# Step  5: (1.3108, 1.8351), loss = 5.086018
# ...
# Step 25: (0.0019, 0.0027), loss = 0.000011
# → Converges to (0, 0) ✓
```

### 🏢 FAANG Interview Tie-in

> **Google Brain interview:** "Explain gradient descent in terms a product manager would understand."
>
> "Imagine you're blindfolded on a mountain. You feel the slope under your feet (compute gradient). You take a step downhill (update parameters). Repeat until you reach the valley (minimum loss). Learning rate is how big each step is — too big and you overshoot, too small and it takes forever."

---

# 01.05 — Matrices

## Intuition

A **matrix** is a table of numbers. That's it. Rows and columns of numbers.

```
     ┌         ┐
A =  │ 1  2  3 │   ← 2×3 matrix (2 rows, 3 columns)
     │ 4  5  6 │
     └         ┘
```

**In AI:** A matrix is used EVERYWHERE:
- A **dataset** is a matrix (rows = samples, columns = features)
- A **weight layer** in a neural network is a matrix
- An **image** is a matrix (rows × columns of pixel values)
- **Attention scores** in Transformers are a matrix

## Matrix Multiplication

This is THE most important operation in deep learning.

```
A (2×3) × B (3×2) = C (2×2)

     ┌       ┐     ┌     ┐     ┌          ┐
     │ 1 2 3 │  ×  │ 7 8 │  =  │  58  64  │
     │ 4 5 6 │     │ 9 10│     │ 139 154  │
     └       ┘     │11 12│     └          ┘
                    └     ┘

C[0,0] = 1×7 + 2×9 + 3×11 = 7 + 18 + 33 = 58
C[0,1] = 1×8 + 2×10 + 3×12 = 8 + 20 + 36 = 64
C[1,0] = 4×7 + 5×9 + 6×11 = 28 + 45 + 66 = 139
C[1,1] = 4×8 + 5×10 + 6×12 = 32 + 50 + 72 = 154
```

**Rule:** Inner dimensions must match: (m×**n**) × (**n**×p) = (m×p)

## The Neural Network Connection

```
┌───────────────────────────────────────────────────────────────┐
│          A NEURAL NETWORK LAYER IS MATRIX MULTIPLICATION       │
│                                                               │
│   Input (1×3)      Weights (3×2)     Output (1×2)             │
│                                                               │
│   [x₁ x₂ x₃]  ×  ┌ w₁₁ w₁₂ ┐  =  [y₁ y₂]                  │
│                    │ w₂₁ w₂₂ │                                │
│                    │ w₃₁ w₃₂ │                                │
│                    └         ┘                                │
│                                                               │
│   y = xW + b   ← The fundamental equation of neural networks  │
│                                                               │
│   3 inputs → 2 outputs (the matrix "transforms" the shape)    │
└───────────────────────────────────────────────────────────────┘
```

## Key Matrix Operations

```python
import numpy as np

# ── Create matrices ──
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

# ── Multiplication ──
print("A @ B =\n", A @ B)
# [[19 22]
#  [43 50]]

# ── Transpose (flip rows ↔ columns) ──
print("A.T =\n", A.T)
# [[1 3]
#  [2 4]]

# ── Element-wise multiplication (Hadamard) ──
print("A * B =\n", A * B)
# [[ 5 12]
#  [21 32]]

# ── Identity matrix (the "1" of matrices) ──
I = np.eye(2)
print("A @ I =\n", A @ I)
# Same as A! (Just like x × 1 = x)

# ── Inverse (A × A⁻¹ = I) ──
A_inv = np.linalg.inv(A)
print("A @ A_inv =\n", (A @ A_inv).round(2))
# [[1 0]
#  [0 1]]  ← Identity matrix ✓

# ── Determinant ──
print(f"det(A) = {np.linalg.det(A):.1f}")  # -2.0

# ── Eigenvalues & Eigenvectors ──
eigenvalues, eigenvectors = np.linalg.eig(A)
print(f"Eigenvalues: {eigenvalues}")
```

## Matrix as Transformation

A matrix **transforms** space — it can rotate, scale, shear, or reflect vectors.

```
Original Space              After transformation by A
                            
     •  •  •                      •     •
     •  •  •      ──A──▶        •     •
     •  •  •                  •     •       (sheared!)

This is EXACTLY what a neural network layer does:
  it transforms the input space to make patterns separable.
```

## Code: A Complete Neural Network Layer

```python
import numpy as np

# ── Simulate one layer of a neural network ──
np.random.seed(42)

# Input: batch of 4 samples, each with 3 features
X = np.random.randn(4, 3)
print(f"Input shape: {X.shape}")      # (4, 3)

# Weights: transform 3 features into 2 features
W = np.random.randn(3, 2)
b = np.zeros(2)  # bias
print(f"Weight shape: {W.shape}")     # (3, 2)

# Forward pass = Matrix multiplication + bias + activation
Z = X @ W + b             # Linear transformation
A = np.maximum(0, Z)      # ReLU activation
print(f"Output shape: {A.shape}")     # (4, 2)
print(f"Output:\n{A.round(3)}")

# 4 samples with 3 features → 4 samples with 2 features
# The matrix W "projected" 3D space into 2D space
```

### 🏢 FAANG Interview Tie-in

> **NVIDIA interview:** "Why is matrix multiplication so important for GPUs?"
>
> A GPU has thousands of cores that can multiply in parallel. One layer of a neural network is one matrix multiply. A 175B parameter model (GPT-3) does hundreds of matrix multiplies per forward pass, each involving matrices with millions of elements. GPUs turn what would take hours on a CPU into seconds.

---

# 01.06 — Derivation Rules & Examples

## The Toolkit

You need these rules to differentiate ANY function in a neural network.

### Rule 1: Constant Rule

```
d/dx [c] = 0

The derivative of a constant is zero.
"If nothing changes, the rate of change is zero."

Example: d/dx [7] = 0
```

### Rule 2: Power Rule

```
d/dx [xⁿ] = n · xⁿ⁻¹

"Bring the exponent down, subtract 1 from it."

Examples:
  d/dx [x³]   = 3x²
  d/dx [x⁵]   = 5x⁴
  d/dx [x]    = 1        (x = x¹, so 1·x⁰ = 1)
  d/dx [1/x]  = -1/x²   (1/x = x⁻¹, so -1·x⁻² = -1/x²)
  d/dx [√x]   = 1/(2√x) (√x = x^½, so ½·x⁻½)
```

### Rule 3: Sum Rule

```
d/dx [f(x) + g(x)] = f'(x) + g'(x)

"Derivative of a sum = sum of derivatives."

Example: d/dx [x² + 3x] = 2x + 3
```

### Rule 4: Product Rule

```
d/dx [f(x) · g(x)] = f'(x)·g(x) + f(x)·g'(x)

"First's derivative times second, PLUS first times second's derivative."

Example: d/dx [x² · sin(x)]
  = 2x · sin(x) + x² · cos(x)
```

### Rule 5: Quotient Rule

```
d/dx [f(x)/g(x)] = [f'(x)·g(x) - f(x)·g'(x)] / [g(x)]²

Example: d/dx [x²/(x+1)]
  = [2x(x+1) - x²·1] / (x+1)²
  = [2x² + 2x - x²] / (x+1)²
  = [x² + 2x] / (x+1)²
```

### Rule 6: Chain Rule (Preview — full lesson next)

```
d/dx [f(g(x))] = f'(g(x)) · g'(x)

"Outer derivative × Inner derivative."

Example: d/dx [sin(x²)]
  = cos(x²) · 2x
```

## AI-Specific Derivation Examples

### Example 1: MSE Loss Derivative

```
L = (ŷ - y)²    where ŷ = predicted, y = actual

dL/dŷ = 2(ŷ - y)

If ŷ = 5 and y = 3:
  dL/dŷ = 2(5-3) = 4  → "prediction too high, push it down"

If ŷ = 2 and y = 3:
  dL/dŷ = 2(2-3) = -2 → "prediction too low, push it up"
```

### Example 2: Sigmoid Derivative

```
σ(x) = 1 / (1 + e⁻ˣ)

σ'(x) = σ(x) · (1 - σ(x))    ← beautiful!

At x = 0: σ(0) = 0.5
  σ'(0) = 0.5 × (1 - 0.5) = 0.25   ← maximum slope

At x = 5: σ(5) ≈ 0.993
  σ'(5) ≈ 0.993 × 0.007 = 0.007    ← very flat (vanishing gradient!)
```

### Example 3: Softmax + Cross-Entropy Derivative

```
The combined derivative simplifies beautifully:

∂L/∂zᵢ = pᵢ - yᵢ

where pᵢ = softmax output, yᵢ = true label (one-hot)

If true class is 2 and softmax gives [0.1, 0.2, 0.7]:
  gradients = [0.1-0, 0.2-0, 0.7-1] = [0.1, 0.2, -0.3]
  
  "Push class 0 and 1 probabilities DOWN, push class 2 UP."
```

## Code: Verify Derivatives Numerically

```python
import numpy as np

def verify_derivative(f, f_prime, x, name=""):
    """Compare analytical derivative with numerical approximation."""
    h = 1e-7
    numerical = (f(x + h) - f(x - h)) / (2 * h)
    analytical = f_prime(x)
    match = np.allclose(numerical, analytical, rtol=1e-5)
    print(f"{name:20s} | analytical={analytical:8.4f} | numerical={numerical:8.4f} | {'✅' if match else '❌'}")

# Test all our rules
x = 2.0

verify_derivative(lambda x: x**3,       lambda x: 3*x**2,          x, "Power: x³")
verify_derivative(lambda x: np.exp(x),   lambda x: np.exp(x),       x, "Exp: eˣ")
verify_derivative(lambda x: np.log(x),   lambda x: 1/x,             x, "Log: ln(x)")
verify_derivative(lambda x: np.sin(x),   lambda x: np.cos(x),       x, "Sin: sin(x)")

# Sigmoid
sig = lambda x: 1/(1+np.exp(-x))
sig_prime = lambda x: sig(x)*(1-sig(x))
verify_derivative(sig, sig_prime, x, "Sigmoid")

# Output:
# Power: x³            | analytical=  12.0000 | numerical=  12.0000 | ✅
# Exp: eˣ              | analytical=   7.3891 | numerical=   7.3891 | ✅
# Log: ln(x)           | analytical=   0.5000 | numerical=   0.5000 | ✅
# Sin: sin(x)          | analytical=  -0.4161 | numerical=  -0.4161 | ✅
# Sigmoid              | analytical=   0.1050 | numerical=   0.1050 | ✅
```

### 🏢 FAANG Interview Tie-in

> **DeepMind interview:** "Derive the gradient of the cross-entropy loss with respect to the logits."
>
> This tests your ability to combine the chain rule, quotient rule (for softmax), and logarithm derivative. The punchline: `∂L/∂z = p - y` (softmax output minus one-hot label). Elegant, simple, and computationally efficient.

---

# 01.07 — The Chain Rule

## Intuition

The chain rule handles **functions inside functions** (compositions). In AI, this is literally how **backpropagation** works.

Think of a chain of gears:

```
   ┌───┐    ┌───┐    ┌───┐
───│ g  │───│ f  │───│ h  │───
   └───┘    └───┘    └───┘
   
If the first gear turns 2×, and the second turns 3×,
the total effect is 2 × 3 = 6×.

Chain rule: multiply the rates through the chain.
```

## The Math

```
If y = f(g(x)), then:

   dy/dx = f'(g(x)) · g'(x)

Or in Leibniz notation:

   dy/dx = (dy/du) · (du/dx)     where u = g(x)
```

## Step-by-Step Example

Find the derivative of `y = (3x + 2)⁵`

```
Step 1: Identify the outer and inner functions
   Outer: f(u) = u⁵        → f'(u) = 5u⁴
   Inner: g(x) = 3x + 2    → g'(x) = 3

Step 2: Apply the chain rule
   dy/dx = f'(g(x)) · g'(x)
         = 5(3x + 2)⁴ · 3
         = 15(3x + 2)⁴  ✓
```

## Multi-Layer Chain Rule (Why Backprop Works)

In a neural network with 3 layers:

```
Input x → Layer 1 → Layer 2 → Layer 3 → Loss L

  z₁ = W₁x + b₁      (linear)
  a₁ = ReLU(z₁)       (activation)
  z₂ = W₂a₁ + b₂      (linear)
  a₂ = ReLU(z₂)       (activation)
  z₃ = W₃a₂ + b₃      (linear)
  L  = (z₃ - y)²      (loss)
```

To update W₁, we need `∂L/∂W₁`. Chain rule gives us:

```
∂L/∂W₁ = ∂L/∂z₃ · ∂z₃/∂a₂ · ∂a₂/∂z₂ · ∂z₂/∂a₁ · ∂a₁/∂z₁ · ∂z₁/∂W₁

Each factor is easy to compute individually!
The chain rule lets us multiply them together.
```

```
┌───────────────────────────────────────────────────────────────────┐
│               THE CHAIN OF DERIVATIVES (BACKPROP)                  │
│                                                                   │
│  FORWARD PASS (left to right):                                    │
│  x ──▶ z₁ ──▶ a₁ ──▶ z₂ ──▶ a₂ ──▶ z₃ ──▶ L                    │
│                                                                   │
│  BACKWARD PASS (right to left, multiplying derivatives):           │
│  ∂L/∂W₁ ◀── ∂z₁/∂W₁ ◀── ∂a₁/∂z₁ ◀── ∂z₂/∂a₁ ◀── ... ◀── ∂L/∂z₃│
│                                                                   │
│  = (∂L/∂z₃) × (∂z₃/∂a₂) × (∂a₂/∂z₂) × (∂z₂/∂a₁) × ...        │
└───────────────────────────────────────────────────────────────────┘
```

## Code: Chain Rule in Action

```python
import numpy as np

# ── Function: y = sin(x²) ──
# Outer: sin(u),  u = x²
# Chain rule: dy/dx = cos(x²) · 2x

def f(x):
    return np.sin(x**2)

def f_prime_chain(x):
    return np.cos(x**2) * 2*x   # chain rule!

# Verify numerically
x = 1.5
h = 1e-7
numerical = (f(x+h) - f(x-h)) / (2*h)
analytical = f_prime_chain(x)
print(f"Chain rule: {analytical:.6f}")
print(f"Numerical:  {numerical:.6f}")
print(f"Match: {np.isclose(analytical, numerical)}")
# ✅ They match!

# ── Multi-layer chain rule ──
# y = relu(sigmoid(3x + 1))

def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def relu(x):
    return np.maximum(0, x)

def multi_layer(x):
    z1 = 3*x + 1
    a1 = sigmoid(z1)
    a2 = relu(a1)
    return a2

# Derivative by chain rule:
# da2/dx = da2/da1 · da1/dz1 · dz1/dx
# da2/da1 = 1 (if a1 > 0, since relu'(x)=1 for x>0)
# da1/dz1 = sigmoid(z1)(1-sigmoid(z1))
# dz1/dx = 3

def multi_layer_derivative(x):
    z1 = 3*x + 1
    a1 = sigmoid(z1)
    # relu derivative: 1 if input > 0, 0 otherwise
    da2_da1 = 1.0 if a1 > 0 else 0.0
    # sigmoid derivative
    da1_dz1 = a1 * (1 - a1)
    # linear derivative
    dz1_dx = 3.0
    return da2_da1 * da1_dz1 * dz1_dx

x = 0.5
numerical = (multi_layer(x+h) - multi_layer(x-h)) / (2*h)
analytical = multi_layer_derivative(x)
print(f"\nMulti-layer chain rule: {analytical:.6f}")
print(f"Numerical verification: {numerical:.6f}")
```

### 🏢 FAANG Interview Tie-in

> **OpenAI interview:** "Why does the chain rule lead to vanishing gradients in deep networks?"
>
> Each layer multiplies a derivative ≤ 1 (sigmoid: max 0.25). Through 50 layers: 0.25⁵⁰ ≈ 10⁻³⁰. The gradient for early layers effectively becomes zero. Solutions: ReLU (derivative = 1), residual connections (add shortcut paths), normalization.

---

# 01.08 — Backprop in Python

## Intuition

**Backpropagation** = the chain rule applied systematically to compute gradients for every weight in a neural network.

```
FORWARD PASS:  Compute outputs layer by layer (left → right)
BACKWARD PASS: Compute gradients layer by layer (right → left)
UPDATE:        Adjust weights using gradients
```

## A Complete Backprop Implementation

```python
import numpy as np
np.random.seed(42)

# ═══════════════════════════════════════════════════════
#  DATASET: Learn XOR (not linearly separable!)
# ═══════════════════════════════════════════════════════
X = np.array([[0, 0],
              [0, 1],
              [1, 0],
              [1, 1]])

y = np.array([[0],
              [1],
              [1],
              [0]])   # XOR!

# ═══════════════════════════════════════════════════════
#  NETWORK: 2 inputs → 4 hidden → 1 output
# ═══════════════════════════════════════════════════════
def sigmoid(z):
    return 1 / (1 + np.exp(-z))

def sigmoid_derivative(a):
    return a * (1 - a)   # a is already sigmoid(z)

# Initialize weights randomly
W1 = np.random.randn(2, 4) * 0.5    # input→hidden  (2×4)
b1 = np.zeros((1, 4))
W2 = np.random.randn(4, 1) * 0.5    # hidden→output (4×1)
b2 = np.zeros((1, 1))

learning_rate = 1.0
losses = []

# ═══════════════════════════════════════════════════════
#  TRAINING LOOP
# ═══════════════════════════════════════════════════════
for epoch in range(10000):

    # ─── FORWARD PASS ───
    # Layer 1
    z1 = X @ W1 + b1           # (4×2) @ (2×4) = (4×4)
    a1 = sigmoid(z1)           # activation

    # Layer 2 (output)
    z2 = a1 @ W2 + b2          # (4×4) @ (4×1) = (4×1)
    a2 = sigmoid(z2)           # final prediction

    # ─── COMPUTE LOSS ───
    loss = np.mean((y - a2) ** 2)
    losses.append(loss)

    # ─── BACKWARD PASS (Chain Rule!) ───
    # Output layer gradients
    dL_da2 = -(2/4) * (y - a2)                 # ∂L/∂a₂
    da2_dz2 = sigmoid_derivative(a2)            # ∂a₂/∂z₂
    dz2 = dL_da2 * da2_dz2                     # ∂L/∂z₂ (chain rule!)

    dW2 = a1.T @ dz2                           # ∂L/∂W₂
    db2 = np.sum(dz2, axis=0, keepdims=True)   # ∂L/∂b₂

    # Hidden layer gradients
    dL_da1 = dz2 @ W2.T                        # ∂L/∂a₁ (backprop through W2)
    da1_dz1 = sigmoid_derivative(a1)            # ∂a₁/∂z₁
    dz1 = dL_da1 * da1_dz1                     # ∂L/∂z₁ (chain rule!)

    dW1 = X.T @ dz1                            # ∂L/∂W₁
    db1 = np.sum(dz1, axis=0, keepdims=True)   # ∂L/∂b₁

    # ─── UPDATE WEIGHTS ───
    W2 -= learning_rate * dW2
    b2 -= learning_rate * db2
    W1 -= learning_rate * dW1
    b1 -= learning_rate * db1

    if epoch % 2000 == 0:
        print(f"Epoch {epoch:5d} | Loss: {loss:.6f}")

# ═══════════════════════════════════════════════════════
#  TEST
# ═══════════════════════════════════════════════════════
print("\n── Predictions ──")
for i in range(4):
    print(f"Input: {X[i]} → Predicted: {a2[i][0]:.4f} | True: {y[i][0]}")

# Input: [0 0] → Predicted: 0.0263 | True: 0  ✓
# Input: [0 1] → Predicted: 0.9704 | True: 1  ✓
# Input: [1 0] → Predicted: 0.9708 | True: 1  ✓
# Input: [1 1] → Predicted: 0.0361 | True: 0  ✓
```

## Diagram: The Complete Backprop Flow

```
┌───────────────────────────────────────────────────────────────────────┐
│                        BACKPROPAGATION FLOW                           │
│                                                                       │
│     FORWARD (compute outputs)                                         │
│     ═══════════════════════▶                                         │
│                                                                       │
│  ┌──────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌────┐  │
│  │Input │    │ Linear   │    │  Sigmoid  │    │ Linear   │    │Loss│  │
│  │  X   │──▶│ z₁=XW₁+b₁│──▶│ a₁=σ(z₁) │──▶│z₂=a₁W₂+b₂│──▶│ L  │  │
│  └──────┘    └──────────┘    └──────────┘    └──────────┘    └────┘  │
│                                                                       │
│     ◀═══════════════════════                                         │
│     BACKWARD (compute gradients, multiply through chain)              │
│                                                                       │
│     ∂L/∂W₁      ∂L/∂z₁         ∂L/∂a₁        ∂L/∂z₂       ∂L/∂a₂  │
│    = X.T@dz₁  = dL_da1·σ'(z₁) = dz₂@W₂.T  = dL_da2·σ'(z₂) = 2(a₂-y)│
│                                                                       │
│     Each gradient = LOCAL derivative × UPSTREAM gradient              │
│     This is the CHAIN RULE in action!                                 │
└───────────────────────────────────────────────────────────────────────┘
```

### 🏢 FAANG Interview Tie-in

> **Google interview:** "Implement backpropagation for a 2-layer network on a whiteboard."
>
> The key insight: backprop is just the chain rule + caching forward pass values. You need `a₁` (from forward pass) to compute `∂L/∂W₂ = a₁ᵀ · δ₂`. That's why we store intermediate activations — memory for speed.

---

# 01.09 — The Jacobian Matrix

## Intuition

When a function has **multiple inputs AND multiple outputs**, a single derivative isn't enough. You need a **matrix of all partial derivatives** — that's the Jacobian.

```
One input, one output    → derivative (scalar)
Multiple inputs, one out → gradient (vector)
Multiple inputs & outs   → JACOBIAN (matrix)
```

## The Math

For a function **f**: ℝⁿ → ℝᵐ (n inputs, m outputs):

```
          ┌ ∂f₁/∂x₁  ∂f₁/∂x₂  ...  ∂f₁/∂xₙ ┐
          │ ∂f₂/∂x₁  ∂f₂/∂x₂  ...  ∂f₂/∂xₙ │
J(f) =   │    ...       ...    ...     ...    │
          │ ∂fₘ/∂x₁  ∂fₘ/∂x₂  ...  ∂fₘ/∂xₙ │
          └                                    ┘

Row i = gradient of the i-th output
Column j = how the j-th input affects all outputs
```

## Step-by-Step Example

```
f(x₁, x₂) = [x₁² + x₂,  x₁ · x₂]

f₁ = x₁² + x₂
f₂ = x₁ · x₂

Jacobian:
J = ┌ ∂f₁/∂x₁  ∂f₁/∂x₂ ┐   =   ┌ 2x₁   1  ┐
    │ ∂f₂/∂x₁  ∂f₂/∂x₂ │       │  x₂   x₁ │
    └                     ┘       └           ┘

At point (3, 2):
J = ┌ 6  1 ┐
    │ 2  3 │
    └      ┘
```

## Why the Jacobian Matters in AI

### Backprop Through Layers

Each neural network layer is a function **f**: ℝⁿ → ℝᵐ. Backpropagation through that layer requires the **Jacobian-vector product** (JVP):

```
Layer:  a = f(z)      (m outputs from n inputs)
Upstream gradient:  δ  (m-dimensional)

Gradient passed backward = Jᵀ · δ   (n-dimensional)
```

```
┌─────────────────────────────────────────────────────────┐
│  WHY WE NEVER COMPUTE THE FULL JACOBIAN                  │
│                                                         │
│  For a layer with 1000 inputs and 1000 outputs:          │
│    Full Jacobian = 1000 × 1000 = 1,000,000 numbers!     │
│                                                         │
│  But we only need Jᵀ · δ (a vector, not a matrix).      │
│  Modern frameworks compute this efficiently without      │
│  ever forming the full Jacobian.                         │
│                                                         │
│  This is called a "vector-Jacobian product" (VJP).       │
└─────────────────────────────────────────────────────────┘
```

## Code: Computing the Jacobian

```python
import numpy as np

# ── Define a vector-valued function ──
def f(x):
    """f: R² → R² """
    x1, x2 = x
    return np.array([
        x1**2 + x2,     # f₁
        x1 * x2          # f₂
    ])

# ── Analytical Jacobian ──
def jacobian_analytical(x):
    x1, x2 = x
    return np.array([
        [2*x1, 1],    # ∂f₁/∂x₁, ∂f₁/∂x₂
        [x2,   x1]    # ∂f₂/∂x₁, ∂f₂/∂x₂
    ])

# ── Numerical Jacobian ──
def jacobian_numerical(f, x, h=1e-7):
    n = len(x)
    m = len(f(x))
    J = np.zeros((m, n))
    for j in range(n):
        x_plus = x.copy(); x_plus[j] += h
        x_minus = x.copy(); x_minus[j] -= h
        J[:, j] = (f(x_plus) - f(x_minus)) / (2*h)
    return J

# ── Compare ──
x = np.array([3.0, 2.0])
J_analytical = jacobian_analytical(x)
J_numerical = jacobian_numerical(f, x)

print("Analytical Jacobian:")
print(J_analytical)
print("\nNumerical Jacobian:")
print(J_numerical.round(6))
print("\nMatch:", np.allclose(J_analytical, J_numerical))

# Analytical Jacobian:
# [[6. 1.]
#  [2. 3.]]
# Match: True ✅

# ── Jacobian-Vector Product (what backprop actually computes) ──
upstream_gradient = np.array([1.0, -0.5])  # δ from next layer
grad_input = J_analytical.T @ upstream_gradient
print(f"\nJᵀ · δ = {grad_input}")
# This is the gradient passed back to the previous layer
```

### Softmax Jacobian (Key for Transformers)

```python
def softmax(z):
    exp_z = np.exp(z - np.max(z))
    return exp_z / exp_z.sum()

def softmax_jacobian(z):
    """The Jacobian of softmax is: diag(p) - p·pᵀ"""
    p = softmax(z)
    return np.diag(p) - np.outer(p, p)

z = np.array([2.0, 1.0, 0.1])
J = softmax_jacobian(z)
print("Softmax Jacobian:")
print(J.round(4))
# Each row tells how that output changes w.r.t. each input
```

### 🏢 FAANG Interview Tie-in

> **Tesla AI interview:** "What is a Jacobian and how does it relate to backpropagation?"
>
> The Jacobian captures all input-output sensitivities of a layer. Backprop computes **Jᵀ · δ** (vector-Jacobian product) at each layer to propagate gradients backward. Modern autodiff (PyTorch autograd) never builds the full Jacobian — it computes only the VJP, which is O(n) instead of O(n²).

---

# 01.10 — Hadamard Product (Element-wise Operations)

## Intuition

The **Hadamard product** is the simplest matrix operation: multiply corresponding elements.

```
Standard matrix multiply: rows × columns, sum products (complex!)
Hadamard product:         just multiply each element by its partner

┌ 1  2 ┐     ┌ 5  6 ┐     ┌ 1×5  2×6 ┐     ┌  5  12 ┐
│ 3  4 │ ⊙   │ 7  8 │  =  │ 3×7  4×8 │  =  │ 21  32 │
└      ┘     └      ┘     └          ┘     └        ┘
```

Both matrices MUST be the same shape (or broadcastable).

## Where Hadamard Product Appears in AI

### 1. Gating Mechanisms (LSTMs, GRUs)

```
┌───────────────────────────────────────────────────────┐
│  LSTM GATES USE HADAMARD PRODUCT                       │
│                                                       │
│  Forget gate:  fₜ ⊙ Cₜ₋₁                             │
│  "Multiply cell state by forget gate (0s and 1s)."    │
│  0 = forget this information                          │
│  1 = keep this information                            │
│                                                       │
│  Memory: [0.8, 0.2, 0.9, 0.1]  (cell state)          │
│  Gate:   [1.0, 0.0, 1.0, 0.0]  (forget gate output)  │
│  Result: [0.8, 0.0, 0.9, 0.0]  (after gating)        │
│                                                       │
│  The gate "masks" which memories to keep!              │
└───────────────────────────────────────────────────────┘
```

### 2. Attention Masking

```python
# In Transformers, we mask future tokens with Hadamard product
scores = np.array([[1.0, 0.5, 0.3],
                   [0.8, 1.0, 0.6],
                   [0.2, 0.7, 1.0]])

# Causal mask: can only attend to past & present
mask = np.array([[1, 0, 0],
                 [1, 1, 0],
                 [1, 1, 1]])

masked_scores = scores * mask  # Hadamard product!
print(masked_scores)
# [[1.  0.  0. ]    ← token 1 sees only itself
#  [0.8 1.  0. ]    ← token 2 sees tokens 1-2
#  [0.2 0.7 1. ]]   ← token 3 sees all
```

### 3. Dropout (Regularization)

```python
# Dropout randomly zeros out neurons — using Hadamard product!
activations = np.array([0.5, 1.2, -0.3, 0.8, 2.1])

# Random mask (keep probability = 0.8)
np.random.seed(42)
dropout_mask = (np.random.rand(5) > 0.2).astype(float)
print(f"Mask: {dropout_mask}")  # [1. 1. 1. 0. 1.]

result = activations * dropout_mask  # Hadamard!
print(f"After dropout: {result}")     # [0.5 1.2 -0.3 0.  2.1]
# The 4th neuron was "dropped out" (multiplied by 0)
```

### 4. Backprop Through ReLU

```python
# ReLU derivative is 0 or 1 — applied via Hadamard product
z = np.array([-1.0, 2.0, -0.5, 3.0, 0.0])
upstream_grad = np.array([0.5, 1.0, 0.3, 0.8, 0.2])

relu_mask = (z > 0).astype(float)       # [0, 1, 0, 1, 0]
grad_through_relu = upstream_grad * relu_mask   # Hadamard!
print(f"Gradient after ReLU: {grad_through_relu}")
# [0.  1.  0.  0.8 0. ]
# Negative inputs block the gradient (gradient = 0)
```

## Code: Hadamard vs. Matrix Multiplication

```python
import numpy as np

A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

# Hadamard product (element-wise, symbol: ⊙ or *)
hadamard = A * B
print(f"A ⊙ B =\n{hadamard}")
# [[ 5 12]
#  [21 32]]

# Matrix multiplication (completely different!)
matmul = A @ B
print(f"A @ B =\n{matmul}")
# [[19 22]
#  [43 50]]

# Key differences:
# Hadamard: same-shape inputs → same-shape output
# MatMul:   (m×n) @ (n×p) → (m×p), inner dimensions must match
```

### 🏢 FAANG Interview Tie-in

> **Apple ML interview:** "How does the gating mechanism in an LSTM work mathematically?"
>
> The forget gate `fₜ = σ(Wf·[hₜ₋₁, xₜ] + bf)` produces values in (0,1). These are multiplied element-wise (Hadamard) with the cell state: `Cₜ = fₜ ⊙ Cₜ₋₁ + iₜ ⊙ C̃ₜ`. The ⊙ is the mechanism that lets the network learn what to remember and what to forget.

---

# 01.11 — Entropy & Information Theory

## Intuition

**Entropy** measures **uncertainty** or **surprise**.

```
LOW ENTROPY (boring, predictable):
  "Tomorrow the sun will rise."  → Not surprising. You already knew.

HIGH ENTROPY (surprising, uncertain):
  "Tomorrow aliens will land."   → Very surprising! High information.
```

**In AI:** Entropy tells us how uncertain a model's predictions are. A confident model has LOW entropy. A confused model has HIGH entropy.

## Shannon Entropy Formula

```
H(X) = -Σ p(xᵢ) · log₂(p(xᵢ))
         i
```

Translation: "Sum up each outcome's probability times its surprise."

## Step-by-Step Example

### Fair coin (maximum uncertainty):

```
P(heads) = 0.5,  P(tails) = 0.5

H = -(0.5 × log₂(0.5) + 0.5 × log₂(0.5))
  = -(0.5 × (-1) + 0.5 × (-1))
  = -(-0.5 + -0.5)
  = 1.0 bit

Maximum entropy! Total uncertainty.
```

### Biased coin (less uncertainty):

```
P(heads) = 0.9,  P(tails) = 0.1

H = -(0.9 × log₂(0.9) + 0.1 × log₂(0.1))
  = -(0.9 × (-0.152) + 0.1 × (-3.322))
  = -(−0.137 + −0.332)
  = 0.469 bits

Lower entropy! The outcome is more predictable.
```

### Certain outcome (zero uncertainty):

```
P(heads) = 1.0,  P(tails) = 0.0

H = -(1.0 × log₂(1.0))
  = -(1.0 × 0)
  = 0 bits

Zero entropy! No uncertainty at all.
```

## Cross-Entropy (THE Loss Function for Classification)

Cross-entropy measures how well a predicted distribution `q` matches the true distribution `p`:

```
H(p, q) = -Σ p(xᵢ) · log(q(xᵢ))
            i
```

```
True label:     p = [0, 0, 1]         (class 2 is correct)
Good prediction: q = [0.05, 0.05, 0.9]
Bad prediction:  q = [0.4, 0.3, 0.3]

Good: H = -(0·log(0.05) + 0·log(0.05) + 1·log(0.9))
     = -log(0.9) = 0.105   ← LOW loss ✓

Bad:  H = -(0·log(0.4) + 0·log(0.3) + 1·log(0.3))
     = -log(0.3) = 1.204   ← HIGH loss ✗
```

## Code: Entropy and Cross-Entropy

```python
import numpy as np

# ── Shannon Entropy ──
def entropy(probs):
    """H(X) = -Σ p·log₂(p)"""
    probs = np.array(probs)
    probs = probs[probs > 0]  # avoid log(0)
    return -np.sum(probs * np.log2(probs))

print(f"Fair coin:   H = {entropy([0.5, 0.5]):.4f} bits")    # 1.0000
print(f"Biased coin: H = {entropy([0.9, 0.1]):.4f} bits")    # 0.4690
print(f"Certain:     H = {entropy([1.0]):.4f} bits")          # 0.0000
print(f"Fair die:    H = {entropy([1/6]*6):.4f} bits")        # 2.5850

# ── Cross-Entropy Loss (classification) ──
def cross_entropy(y_true, y_pred):
    """H(p, q) = -Σ p·log(q)"""
    y_pred = np.clip(y_pred, 1e-15, 1)  # avoid log(0)
    return -np.sum(y_true * np.log(y_pred))

# True: class 2 (one-hot)
y_true = np.array([0, 0, 1])

# Confident correct prediction
y_pred_good = np.array([0.05, 0.05, 0.90])
print(f"\nGood prediction loss: {cross_entropy(y_true, y_pred_good):.4f}")  # 0.1054

# Uncertain prediction
y_pred_bad = np.array([0.33, 0.33, 0.34])
print(f"Bad prediction loss:  {cross_entropy(y_true, y_pred_bad):.4f}")   # 1.0788

# Wrong prediction
y_pred_wrong = np.array([0.80, 0.10, 0.10])
print(f"Wrong prediction loss: {cross_entropy(y_true, y_pred_wrong):.4f}")  # 2.3026
```

## Diagram: Entropy Visualization

```
Entropy
(bits)
  1.0 │          •
      │        •   •
      │       •     •
  0.5 │     •         •
      │   •             •
      │  •               •
  0.0 │•                   •
      ┼────────────────────── P(heads)
      0   0.25  0.5  0.75  1.0
      
      certain  uncertain  certain
      (tails)  (maximum)  (heads)
```

### 🏢 FAANG Interview Tie-in

> **Google interview:** "Why do we use cross-entropy instead of MSE for classification?"
>
> Cross-entropy loss has stronger gradients when the model is wrong. MSE with sigmoid: gradient ∝ (p-y)·σ'(z), and σ' is small when confident-but-wrong. Cross-entropy: gradient ∝ (p-y), no σ' multiplier. It learns faster from mistakes.

---

# 01.12 — KL Divergence

## Intuition

**KL Divergence** measures how **different** one probability distribution is from another.

```
"How many EXTRA bits do I need if I use distribution Q
 to encode data that actually follows distribution P?"
```

```
P = true distribution (what actually happens)
Q = approximate distribution (what we think happens)

If Q = P:   KL = 0    (perfect match!)
If Q ≠ P:   KL > 0    (always positive)
```

⚠️ **KL divergence is NOT symmetric!** KL(P‖Q) ≠ KL(Q‖P)

## The Math

```
KL(P ‖ Q) = Σ P(x) · log(P(x) / Q(x))
             x

           = Σ P(x) · [log P(x) - log Q(x)]
             x

           = H(P, Q) - H(P)
             ────────   ────
             cross-     entropy
             entropy    of P
```

## Step-by-Step Example

```
P = [0.4, 0.6]    (true distribution)
Q = [0.5, 0.5]    (our model)

KL(P ‖ Q) = 0.4 × log(0.4/0.5) + 0.6 × log(0.6/0.5)
          = 0.4 × log(0.8) + 0.6 × log(1.2)
          = 0.4 × (-0.223) + 0.6 × (0.182)
          = -0.089 + 0.109
          = 0.020 nats

Small KL = distributions are similar!
```

## Where KL Divergence Appears in AI

### 1. Variational Autoencoders (VAEs)

```
┌────────────────────────────────────────────────────────────────┐
│  VAE LOSS = Reconstruction Loss + KL Divergence                │
│                                                                │
│  Input ──▶ ENCODER ──▶ z ~ q(z|x) ──▶ DECODER ──▶ Output      │
│                           │                                    │
│                    KL(q(z|x) ‖ p(z))                           │
│                           │                                    │
│                   "Make the learned distribution                │
│                    close to a standard Normal"                  │
│                                                                │
│  Without KL term: encoder could map each input to a single     │
│  point → no generative ability. KL forces it to spread out.    │
└────────────────────────────────────────────────────────────────┘
```

### 2. Knowledge Distillation

```
Teacher (big model) output:  P = [0.7, 0.2, 0.1]
Student (small model) output: Q = [0.6, 0.3, 0.1]

Train student to MINIMIZE KL(P ‖ Q)
= Make student's distribution match teacher's distribution
```

### 3. RLHF (Reinforcement Learning from Human Feedback)

```
In ChatGPT training:
  KL(π_new ‖ π_old) < ε

"Don't change the model TOO MUCH from the original."
This KL penalty prevents the model from going off the rails.
```

## Code: KL Divergence

```python
import numpy as np

def kl_divergence(p, q):
    """KL(P || Q) — how different Q is from P."""
    p = np.array(p, dtype=float)
    q = np.array(q, dtype=float)
    # Avoid log(0)
    mask = p > 0
    return np.sum(p[mask] * np.log(p[mask] / q[mask]))

# ── Example 1: Similar distributions ──
P = [0.4, 0.6]
Q = [0.5, 0.5]
print(f"KL(P||Q) = {kl_divergence(P, Q):.4f}")  # 0.0204 (small!)

# ── Example 2: Very different distributions ──
P = [0.9, 0.1]
Q = [0.1, 0.9]
print(f"KL(P||Q) = {kl_divergence(P, Q):.4f}")  # 3.5066 (huge!)

# ── Example 3: Asymmetry ──
P = [0.3, 0.7]
Q = [0.6, 0.4]
print(f"KL(P||Q) = {kl_divergence(P, Q):.4f}")  # 0.2231
print(f"KL(Q||P) = {kl_divergence(Q, P):.4f}")  # 0.2513
# They're DIFFERENT! KL is not symmetric.

# ── Example 4: VAE KL for Gaussian ──
def kl_gaussian(mu, log_var):
    """KL(q(z|x) || N(0,1)) for VAE."""
    return -0.5 * np.sum(1 + log_var - mu**2 - np.exp(log_var))

mu = np.array([0.5, -0.3, 0.8])
log_var = np.array([-0.5, -1.0, 0.2])
print(f"\nVAE KL: {kl_gaussian(mu, log_var):.4f}")

# ── Example 5: Knowledge Distillation ──
teacher_probs = np.array([0.7, 0.2, 0.1])
student_probs = np.array([0.6, 0.3, 0.1])
kl = kl_divergence(teacher_probs, student_probs)
print(f"\nDistillation KL loss: {kl:.4f}")
```

## Diagram: KL Divergence Visual

```
Probability
    │
0.9 │ █                                    
0.8 │ █                                    
0.7 │ █                                    
0.6 │ █  ░                                 
0.5 │ █  ░                                 
0.4 │ █  ░                                 
0.3 │ █  ░                                 
0.2 │ █  ░  █                              
0.1 │ █  ░  █  ░                           
    ┼──────────────                        
      P  Q  P  Q                           
     Class A  Class B                       
                                           
  █ = True distribution P                   
  ░ = Model distribution Q                  
  KL(P‖Q) measures the gap between them     
```

### 🏢 FAANG Interview Tie-in

> **OpenAI interview:** "Why do we use KL divergence in RLHF, and why not just optimize the reward?"
>
> Without KL penalty, the model would overfit to the reward model, producing degenerate text that scores high but looks gibberish. The KL term `KL(π_θ ‖ π_ref)` acts as a regularizer: "don't drift too far from the pretrained model." This is the PPO objective: `reward - β·KL`.

---

# 01.13 — Singular Value Decomposition (SVD)

## Intuition

SVD is like **X-ray vision for matrices**. It breaks ANY matrix into three simpler matrices that reveal its structure:

```
A = U · Σ · Vᵀ

Where:
  U  = "What directions in the output space matter?"
  Σ  = "How much each direction matters" (singular values)
  Vᵀ = "What directions in the input space matter?"
```

Think of it like this:

```
Any linear transformation can be decomposed into:
  1. ROTATE (Vᵀ)  →  2. SCALE (Σ)  →  3. ROTATE (U)

┌───────┐      ┌───────┐      ┌───────┐      ┌───────┐
│  ○    │  Vᵀ  │  ○    │  Σ   │  ⬭   │  U   │  ⬭   │
│       │ ───▶ │       │ ───▶ │       │ ───▶ │       │
│  ○    │rotate│  ○    │scale │  ⬭   │rotate│  ⬭   │
└───────┘      └───────┘      └───────┘      └───────┘
 original     aligned w/     stretched      final
              axes           differently    orientation
```

## The Math

For any m×n matrix A:

```
A = U · Σ · Vᵀ

A:  m × n  (original matrix)
U:  m × m  (orthogonal — columns are left singular vectors)
Σ:  m × n  (diagonal — singular values σ₁ ≥ σ₂ ≥ ... ≥ 0)
Vᵀ: n × n  (orthogonal — rows are right singular vectors)
```

## Step-by-Step Example

```python
import numpy as np

A = np.array([[3, 2, 2],
              [2, 3, -2]])

U, S, Vt = np.linalg.svd(A)

print("U (left singular vectors):")
print(U.round(3))
# [[-0.707 -0.707]
#  [-0.707  0.707]]

print(f"\nSingular values: {S.round(3)}")
# [5.    3.]
# First direction captures MORE variance

print("\nVᵀ (right singular vectors):")
print(Vt.round(3))

# Verify: A = U @ diag(S) @ Vt
Sigma = np.zeros_like(A, dtype=float)
Sigma[:2, :2] = np.diag(S)
A_reconstructed = U @ Sigma @ Vt
print(f"\nReconstruction error: {np.max(np.abs(A - A_reconstructed)):.2e}")
# 0.00e+00 ✓ Perfect reconstruction!
```

## Low-Rank Approximation (THE Killer App)

Keep only the top-k singular values to compress the matrix:

```
┌─────────────────────────────────────────────────────────────────┐
│  RANK-k APPROXIMATION                                           │
│                                                                 │
│  Full SVD:     A = σ₁u₁v₁ᵀ + σ₂u₂v₂ᵀ + ... + σₙuₙvₙᵀ         │
│                                                                 │
│  Keep top-2:   A ≈ σ₁u₁v₁ᵀ + σ₂u₂v₂ᵀ                          │
│                                                                 │
│  Singular values:  σ₁=100, σ₂=50, σ₃=2, σ₄=0.5, σ₅=0.01      │
│                    ═══════════════  ──────────────────           │
│                    KEEP (big impact) DROP (noise)               │
│                                                                 │
│  This is how we compress models, reduce dimensions, and         │
│  denoise data!                                                  │
└─────────────────────────────────────────────────────────────────┘
```

```python
import numpy as np

# ── Image compression with SVD ──
np.random.seed(42)

# Simulate a 100x100 grayscale image
image = np.random.randn(100, 100)

U, S, Vt = np.linalg.svd(image, full_matrices=False)

# Reconstruct with different ranks
for k in [5, 10, 20, 50]:
    compressed = U[:, :k] @ np.diag(S[:k]) @ Vt[:k, :]
    error = np.linalg.norm(image - compressed) / np.linalg.norm(image)

    original_size = 100 * 100                        # 10,000 numbers
    compressed_size = k * 100 + k + k * 100          # U_k + S_k + Vt_k
    ratio = compressed_size / original_size * 100

    print(f"Rank {k:2d}: error = {error:.4f}, "
          f"storage = {ratio:.1f}% of original")

# Rank  5: error = 0.9481, storage = 10.1%
# Rank 10: error = 0.8952, storage = 20.1%
# Rank 20: error = 0.7811, storage = 40.1%
# Rank 50: error = 0.4887, storage = 100.1%
```

## SVD in Modern AI

### 1. LoRA (Low-Rank Adaptation) — Fine-tuning LLMs

```
┌────────────────────────────────────────────────────────────────┐
│  LoRA: Instead of updating the full weight matrix W,            │
│  learn a LOW-RANK update ΔW = A · B                            │
│                                                                │
│  Original: W (4096 × 4096) = 16.7M parameters                  │
│  LoRA:     A (4096 × 8) · B (8 × 4096) = 65K parameters       │
│                                                                │
│  Compression: 16.7M → 65K = 256× fewer parameters!             │
│                                                                │
│  Why it works: weight updates are approximately low-rank.       │
│  SVD shows that most singular values are small.                 │
└────────────────────────────────────────────────────────────────┘
```

### 2. PCA (Principal Component Analysis)

```python
# PCA is just SVD of the centered data matrix!
from sklearn.decomposition import PCA

# 1000 samples, 50 features
X = np.random.randn(1000, 50)

# Center the data
X_centered = X - X.mean(axis=0)

# SVD
U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)

# The principal components = rows of Vt
# The explained variance ∝ S²
explained_variance = (S**2) / np.sum(S**2)
cumulative = np.cumsum(explained_variance)

# How many components to keep 95% of information?
k_95 = np.argmax(cumulative >= 0.95) + 1
print(f"Need {k_95} components to explain 95% of variance")
print(f"Reduced from 50 → {k_95} dimensions!")
```

### 3. Recommender Systems

```python
# Netflix-style recommendation using SVD
# Users × Movies rating matrix (with missing values)
ratings = np.array([
    [5, 4, 0, 1, 0],   # User 0 likes action (cols 0,1)
    [4, 5, 1, 0, 0],   # User 1 likes action
    [1, 0, 5, 4, 5],   # User 2 likes drama (cols 2,3,4)
    [0, 1, 4, 5, 4],   # User 3 likes drama
])

# SVD reveals latent factors (e.g., "action" vs "drama")
U, S, Vt = np.linalg.svd(ratings, full_matrices=False)

# Keep top-2 latent factors
k = 2
predicted = U[:, :k] @ np.diag(S[:k]) @ Vt[:k, :]
print("Predicted ratings:")
print(predicted.round(1))
# The zeros (unknown ratings) now have predictions!
```

### 🏢 FAANG Interview Tie-in

> **Netflix/Spotify interview:** "How would you build a recommendation system?"
>
> Matrix factorization via SVD: decompose the user-item matrix into latent factors. Each user becomes a vector, each item becomes a vector. Predict rating = dot product of user and item vectors. This won Nobel-equivalent (Netflix Prize, $1M) and powers billions of recommendations daily.

---

# 01.14 — Moving Averages (EMA)

## Intuition

**Exponential Moving Average (EMA)** is a way to smooth noisy data by giving **more weight to recent values** and less to old ones.

```
Raw signal:      ∿∿∿∿∿∿∿∿∿∿   (noisy, jumpy)
After EMA:       ∽∽∽∽∽∽∽∽∽∽   (smooth, captures trend)
```

```
Weight given to past observations:

Most recent: ████████████  (high weight)
1 step ago:  ████████       (less)
2 steps ago: █████          (even less)
3 steps ago: ███            (fading)
4 steps ago: █              (almost forgotten)
```

## The Formula

```
EMA_t = β · EMA_{t-1} + (1 - β) · x_t

Where:
  β = decay factor (typically 0.9 or 0.99)
  x_t = current observation
  EMA_{t-1} = previous EMA value
```

- **β = 0.9**: Responds fairly quickly to changes (window ≈ 10 steps)
- **β = 0.99**: Very smooth, slow to respond (window ≈ 100 steps)
- **β = 0.999**: Ultra smooth (window ≈ 1000 steps)

## Step-by-Step Example

```
Data: x = [10, 12, 11, 15, 13, 14, 16]
β = 0.8

EMA₀ = 10                              (initialize with first value)
EMA₁ = 0.8 × 10 + 0.2 × 12 = 10.4
EMA₂ = 0.8 × 10.4 + 0.2 × 11 = 10.52
EMA₃ = 0.8 × 10.52 + 0.2 × 15 = 11.42
EMA₄ = 0.8 × 11.42 + 0.2 × 13 = 11.73
EMA₅ = 0.8 × 11.73 + 0.2 × 14 = 12.19
EMA₆ = 0.8 × 12.19 + 0.2 × 16 = 12.95
```

## Where EMA Appears in AI

### 1. Adam Optimizer (First & Second Moment EMA)

```
┌────────────────────────────────────────────────────────────────┐
│  ADAM OPTIMIZER uses TWO EMAs:                                   │
│                                                                │
│  m_t = β₁ · m_{t-1} + (1-β₁) · g_t        ← EMA of gradient  │
│  v_t = β₂ · v_{t-1} + (1-β₂) · g_t²       ← EMA of gradient² │
│                                                                │
│  Default: β₁ = 0.9, β₂ = 0.999                                │
│                                                                │
│  m_t = "which direction to go" (momentum)                      │
│  v_t = "how big should the step be" (adaptive learning rate)   │
│                                                                │
│  Update: θ_t = θ_{t-1} - α · m_t / (√v_t + ε)                │
└────────────────────────────────────────────────────────────────┘
```

### 2. Batch Normalization (Running Stats)

```python
# During training, BN tracks running mean and variance with EMA
running_mean = 0.0
momentum = 0.1  # (1-β)

for batch_mean in [2.0, 2.5, 1.8, 2.2, 2.1]:
    running_mean = (1 - momentum) * running_mean + momentum * batch_mean
    print(f"Batch mean: {batch_mean}, Running mean: {running_mean:.3f}")
```

### 3. EMA Model Weights (Used in DALL-E, Diffusion Models)

```python
# Keep an EMA copy of model weights for better generation quality
ema_decay = 0.999

# After each training step:
# ema_weights = decay * ema_weights + (1 - decay) * model_weights
```

## Code: Complete EMA Implementation

```python
import numpy as np

# ═══════════════════════════════════════════════════════
#  EMA from scratch
# ═══════════════════════════════════════════════════════
class EMA:
    def __init__(self, beta):
        self.beta = beta
        self.value = None
        self.step = 0

    def update(self, x):
        self.step += 1
        if self.value is None:
            self.value = x
        else:
            self.value = self.beta * self.value + (1 - self.beta) * x
        # Bias correction (important for early steps!)
        return self.value / (1 - self.beta ** self.step)

# ── Simulate noisy training loss ──
np.random.seed(42)
true_loss = np.linspace(2.0, 0.1, 100)   # decreasing trend
noise = np.random.randn(100) * 0.3
noisy_loss = true_loss + noise

# Apply EMA with different β values
ema_slow = EMA(beta=0.99)    # very smooth
ema_fast = EMA(beta=0.9)     # responsive

smoothed_slow = [ema_slow.update(x) for x in noisy_loss]
smoothed_fast = [ema_fast.update(x) for x in noisy_loss]

print("Step |  Raw Loss | EMA(0.9) | EMA(0.99)")
print("─────┼───────────┼──────────┼──────────")
for i in [0, 10, 25, 50, 75, 99]:
    print(f"  {i:2d}  | {noisy_loss[i]:8.4f}  | {smoothed_fast[i]:7.4f}  | {smoothed_slow[i]:7.4f}")


# ═══════════════════════════════════════════════════════
#  Adam Optimizer (uses EMA internally)
# ═══════════════════════════════════════════════════════
def adam_optimizer(gradient_fn, x_init, lr=0.001, beta1=0.9, beta2=0.999,
                  eps=1e-8, steps=100):
    """Adam optimizer from scratch — just two EMAs + division."""
    x = x_init
    m = 0  # first moment EMA
    v = 0  # second moment EMA

    for t in range(1, steps + 1):
        g = gradient_fn(x)
        m = beta1 * m + (1 - beta1) * g        # EMA of gradient
        v = beta2 * v + (1 - beta2) * g**2      # EMA of gradient²
        m_hat = m / (1 - beta1**t)               # bias correction
        v_hat = v / (1 - beta2**t)               # bias correction
        x = x - lr * m_hat / (np.sqrt(v_hat) + eps)

        if t % 20 == 0:
            print(f"Step {t:3d}: x = {x:.6f}")
    return x

# Minimize f(x) = (x - 5)²
print("\n── Adam minimizing (x-5)² ──")
result = adam_optimizer(lambda x: 2*(x-5), x_init=0.0, lr=0.1, steps=100)
print(f"Final x = {result:.4f} (should be ≈ 5.0)")
```

## Diagram: EMA Smoothing Effect

```
Loss
2.5 │ •
    │   •  •
2.0 │ •  •   •          raw loss (noisy)
    │       •  •
1.5 │    ╲     •  •
    │     ╲      •
1.0 │      ╲───────•   EMA smoothed (β=0.9)
    │        ╲      •
0.5 │         ╲──────•──•
    │          ╲        •
0.0 │           ╲─────────•
    ┼────────────────────────── step
    0    20    40    60    80  100
```

### 🏢 FAANG Interview Tie-in

> **Google Brain interview:** "Why does Adam use bias correction for the moving averages?"
>
> At step 1, EMA = β×0 + (1-β)×g₁ = (1-β)×g₁. With β=0.999, that's 0.001×g₁ — way too small! Bias correction divides by (1-β^t), fixing this: at t=1, m̂ = m/(1-0.999) = m/0.001 = g₁. This makes early estimates accurate and is critical for training stability.

---

# 01.15 — More Math Lessons

## Essential Topics for Deep Dives

This section covers additional mathematical concepts that appear throughout AI research.

### 1. Taylor Series (Function Approximation)

Any smooth function can be approximated by polynomials:

```
f(x) ≈ f(a) + f'(a)(x-a) + f''(a)(x-a)²/2! + f'''(a)(x-a)³/3! + ...

Example: eˣ around a=0:
eˣ ≈ 1 + x + x²/2 + x³/6 + x⁴/24 + ...
```

```python
import numpy as np

def taylor_exp(x, terms=10):
    """Approximate eˣ using Taylor series."""
    result = 0
    for n in range(terms):
        result += x**n / np.math.factorial(n)
    return result

x = 2.0
print(f"Taylor (5 terms):  {taylor_exp(x, 5):.6f}")
print(f"Taylor (10 terms): {taylor_exp(x, 10):.6f}")
print(f"np.exp(2):         {np.exp(x):.6f}")
# Taylor (5 terms):  7.000000
# Taylor (10 terms): 7.389056
# np.exp(2):         7.389056  ✓
```

**In AI:** Used in approximating activations, understanding optimization landscapes, and Hessian-free optimization.

### 2. Probability & Bayes' Theorem

```
P(A|B) = P(B|A) · P(A) / P(B)

"Update your beliefs when you see new evidence."
```

```python
# Spam filter example
P_spam = 0.3                    # 30% of emails are spam
P_word_given_spam = 0.8         # "FREE" appears in 80% of spam
P_word_given_not_spam = 0.1     # "FREE" appears in 10% of non-spam

# P(word) = P(word|spam)·P(spam) + P(word|¬spam)·P(¬spam)
P_word = P_word_given_spam * P_spam + P_word_given_not_spam * (1 - P_spam)

# P(spam|word) via Bayes
P_spam_given_word = (P_word_given_spam * P_spam) / P_word

print(f"P(spam | sees 'FREE') = {P_spam_given_word:.2%}")
# P(spam | sees 'FREE') = 77.42%
```

### 3. Norms (Measuring Size)

```
L1 Norm: ‖x‖₁ = |x₁| + |x₂| + ... + |xₙ|     (Manhattan distance)
L2 Norm: ‖x‖₂ = √(x₁² + x₂² + ... + xₙ²)      (Euclidean distance)
L∞ Norm: ‖x‖∞ = max(|x₁|, |x₂|, ..., |xₙ|)    (max element)
```

```python
x = np.array([3, -4, 0, 5])

print(f"L1 norm: {np.linalg.norm(x, 1)}")   # 12.0
print(f"L2 norm: {np.linalg.norm(x, 2):.4f}")  # 7.0711
print(f"L∞ norm: {np.linalg.norm(x, np.inf)}")  # 5.0
```

**In AI:**
- **L1 regularization** → sparsity (feature selection, Lasso)
- **L2 regularization** → small weights (weight decay, Ridge)
- **L∞ norm** → adversarial robustness

### 4. Eigenvalues & Eigenvectors

```
A · v = λ · v

"v is a special vector — when multiplied by A, 
 it only gets SCALED (by λ), not rotated."
```

```python
A = np.array([[4, 1],
              [2, 3]])

eigenvalues, eigenvectors = np.linalg.eig(A)
print(f"Eigenvalues: {eigenvalues}")     # [5. 2.]
print(f"Eigenvectors:\n{eigenvectors}")

# Verify: A @ v = λ @ v
for i in range(2):
    v = eigenvectors[:, i]
    lam = eigenvalues[i]
    Av = A @ v
    lam_v = lam * v
    print(f"\nλ={lam:.1f}: A@v = {Av.round(4)}, λ*v = {lam_v.round(4)}, "
          f"Match: {np.allclose(Av, lam_v)}")
```

**In AI:** PCA, spectral clustering, PageRank, stability analysis of training dynamics.

### 5. Log-Sum-Exp Trick (Numerical Stability)

```python
# PROBLEM: softmax overflows with large numbers
z = np.array([1000, 1001, 1002])
# np.exp(z) would be inf!

# SOLUTION: Log-Sum-Exp trick
def stable_softmax(z):
    z_shifted = z - np.max(z)   # subtract max for stability
    exp_z = np.exp(z_shifted)
    return exp_z / exp_z.sum()

print(stable_softmax(z))
# [0.0900, 0.2447, 0.6652]  ← works perfectly!

def log_sum_exp(z):
    """log(Σ exp(zᵢ)) computed stably."""
    c = np.max(z)
    return c + np.log(np.sum(np.exp(z - c)))

print(f"log_sum_exp = {log_sum_exp(z):.4f}")
```

**In AI:** Used in EVERY softmax computation, attention mechanisms, CTC loss, and mixture models.

### 6. Convexity

```
A function is CONVEX if any line between two points 
lies ABOVE the curve:

Convex (good!):         Not convex (tricky!):
                         
  \     /                    /\
   \   /                   /  \    /\
    \_/                   /    \  /  \
     ↑                         \/
  One minimum!           Multiple minima!
```

**In AI:** Convex loss functions (e.g., logistic regression) guarantee finding the global minimum. Neural network losses are non-convex — that's why training is hard and we need tricks like learning rate schedules, momentum, and batch normalization.

---

## Quick Reference: Math → AI Connection Map

```
┌──────────────────────────────────────────────────────────────────────┐
│                    MATH → AI CONNECTION MAP                          │
│                                                                      │
│  CONCEPT              │  WHERE IT SHOWS UP IN AI                     │
│  ─────────────────────│──────────────────────────────────────────     │
│  Functions            │  Activation functions, loss functions         │
│  Derivatives          │  Gradient computation, optimization           │
│  Vectors              │  Embeddings, features, word2vec               │
│  Gradients            │  Gradient descent, backpropagation            │
│  Matrices             │  Weight layers, attention, data batches       │
│  Chain Rule           │  Backpropagation algorithm                    │
│  Jacobian             │  Layer-wise gradient computation              │
│  Hadamard Product     │  Gating (LSTM), dropout, masking              │
│  Entropy              │  Cross-entropy loss, decision trees            │
│  KL Divergence        │  VAE loss, RLHF regularization                │
│  SVD                  │  PCA, LoRA, recommendations, compression      │
│  EMA                  │  Adam optimizer, batch norm, EMA models       │
│  Taylor Series        │  Function approximation, Hessian methods      │
│  Bayes' Theorem       │  Naive Bayes, Bayesian optimization           │
│  Norms                │  Regularization (L1/L2), adversarial attacks  │
│  Eigenvalues          │  PCA, PageRank, spectral methods              │
│  Log-Sum-Exp          │  Softmax stability, attention computation     │
│  Convexity            │  Optimization guarantees, loss design         │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Summary: The 5 Most Important Formulas

```
1. GRADIENT DESCENT:      θ_new = θ_old - α · ∇L(θ)
   
2. CHAIN RULE:            ∂L/∂w = (∂L/∂y)(∂y/∂z)(∂z/∂w)
   
3. SOFTMAX:               p_i = exp(z_i) / Σ exp(z_j)
   
4. CROSS-ENTROPY LOSS:    L = -Σ y_i · log(p_i)
   
5. ADAM UPDATE:            θ -= α · m̂ / (√v̂ + ε)
```

Master these five, and you understand 80% of all AI training.

---

## Practice Problems

### Problem 1: Compute by Hand

```
f(x) = 3x² + 2x + 1

a) Find f'(x)
b) Find f'(2)
c) If this were a loss function, which direction would you move from x=2?
```

<details>
<summary>Solution</summary>

```
a) f'(x) = 6x + 2   (power rule + constant rule)
b) f'(2) = 6(2) + 2 = 14
c) Gradient is positive (14), so move in the NEGATIVE direction
   x_new = 2 - α × 14  (for some learning rate α)
```
</details>

### Problem 2: Implement Cosine Similarity

```python
# Given these embeddings, which two words are most similar?
embeddings = {
    "king":   [0.9, 0.5, -0.2, 0.8],
    "queen":  [0.8, 0.6, 0.7, 0.75],
    "apple":  [-0.1, 0.2, 0.1, -0.5],
    "throne": [0.7, 0.4, -0.1, 0.6]
}

# Your code here: compute cosine similarity between all pairs
```

<details>
<summary>Solution</summary>

```python
import numpy as np
from itertools import combinations

embeddings = {
    "king":   np.array([0.9, 0.5, -0.2, 0.8]),
    "queen":  np.array([0.8, 0.6, 0.7, 0.75]),
    "apple":  np.array([-0.1, 0.2, 0.1, -0.5]),
    "throne": np.array([0.7, 0.4, -0.1, 0.6])
}

for (w1, v1), (w2, v2) in combinations(embeddings.items(), 2):
    cos_sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    print(f"{w1:6s} ↔ {w2:6s}: {cos_sim:.4f}")

# king   ↔ queen : 0.7854
# king   ↔ apple : -0.5321
# king   ↔ throne: 0.9899  ← MOST SIMILAR!
# queen  ↔ apple : -0.0876
# queen  ↔ throne: 0.7322
# apple  ↔ throne: -0.5127
```
</details>

### Problem 3: Backprop a 1-Layer Network

```
Given:
  Input x = 2
  Weight w = 0.5
  Bias b = 1
  True label y = 3

  Forward: z = wx + b = 0.5(2) + 1 = 2
  Loss: L = (z - y)² = (2 - 3)² = 1

Find ∂L/∂w and ∂L/∂b using the chain rule.
Update w and b with learning rate α = 0.1.
```

<details>
<summary>Solution</summary>

```
∂L/∂z = 2(z - y) = 2(2 - 3) = -2
∂z/∂w = x = 2
∂z/∂b = 1

Chain rule:
∂L/∂w = ∂L/∂z × ∂z/∂w = -2 × 2 = -4
∂L/∂b = ∂L/∂z × ∂z/∂b = -2 × 1 = -2

Update:
w_new = 0.5 - 0.1 × (-4) = 0.5 + 0.4 = 0.9
b_new = 1 - 0.1 × (-2) = 1 + 0.2 = 1.2

New prediction: z = 0.9(2) + 1.2 = 3.0 → Loss = 0! ✓
(In this simple case, one step gets us to the answer.)
```
</details>

---

# 🔴 FAANG PRODUCTION DEEP-DIVE — Large-Scale Solutions & Best Practices

> **This section goes beyond textbook math. It covers what actually breaks at billion-parameter scale, how Google/Meta/OpenAI solve it, and the interview questions that separate L4 from L6+ candidates.**

---

## A. Numerical Stability at Scale — "The Silent Killer"

### The Problem Nobody Teaches You

At FAANG scale (billions of parameters, FP16/BF16 precision, thousands of GPUs), **math that works on paper explodes in practice**.

```
┌──────────────────────────────────────────────────────────────────────────┐
│         THE FLOAT16 DANGER ZONE                                          │
│                                                                          │
│  Float32:  range ≈ ±3.4 × 10³⁸,  precision ≈ 7 decimal digits           │
│  Float16:  range ≈ ±65,504,      precision ≈ 3 decimal digits            │
│  BFloat16: range ≈ ±3.4 × 10³⁸,  precision ≈ 3 decimal digits           │
│                                                                          │
│  OVERFLOW:  exp(12) = 162,755  → 💥 INF in FP16                          │
│  UNDERFLOW: exp(-20) = 2×10⁻⁹ → rounds to 0 in FP16                     │
│  CANCELLATION: 1.0001 - 1.0000 = 0.0001 → could be 0 in FP16            │
│                                                                          │
│  These aren't edge cases. They happen in EVERY forward pass              │
│  of a large Transformer.                                                 │
└──────────────────────────────────────────────────────────────────────────┘
```

### Production Solution 1: Stable Softmax (Used in Every Transformer)

```python
import numpy as np

# ── NAIVE SOFTMAX (will crash at scale) ──
def softmax_naive(z):
    return np.exp(z) / np.sum(np.exp(z))

# This EXPLODES in FP16:
z_large = np.array([500, 501, 502], dtype=np.float32)
try:
    print(softmax_naive(z_large))  # [nan, nan, nan] 💥
except:
    print("OVERFLOW!")

# ── PRODUCTION SOFTMAX (Google/Meta/OpenAI all use this) ──
def softmax_stable(z):
    """Subtract max for numerical stability.
    Math: softmax(z) = softmax(z - c) for any constant c.
    Proof: exp(z_i - c) / Σexp(z_j - c) = exp(z_i)/exp(c) / Σexp(z_j)/exp(c)
         = exp(z_i) / Σexp(z_j) ✓
    """
    z_shifted = z - np.max(z)  # now max element = 0, exp(0) = 1
    exp_z = np.exp(z_shifted)
    return exp_z / np.sum(exp_z)

print(softmax_stable(z_large))
# [0.0900, 0.2447, 0.6652] ← Works perfectly!

# ── ONLINE SOFTMAX (FlashAttention v2 — what Google actually uses) ──
def online_softmax(z):
    """Process elements ONE AT A TIME — O(1) memory instead of O(n).
    Used in FlashAttention to avoid materializing the full attention matrix.
    Paper: 'Online normalizer calculation for softmax' (Milakov & Gimelshein, 2018)
    """
    m = -np.inf   # running max
    d = 0.0       # running denominator
    n = len(z)

    # Pass 1: compute max and denominator online
    for i in range(n):
        m_prev = m
        m = max(m, z[i])
        d = d * np.exp(m_prev - m) + np.exp(z[i] - m)

    # Pass 2: compute softmax values
    result = np.exp(z - m) / d
    return result

print(online_softmax(z_large))
# Same result, but STREAMING — no need to store all exp values!
# This is the core trick behind FlashAttention's O(1) SRAM usage.
```

### Production Solution 2: Mixed Precision Training (Google Brain, 2018)

```
┌──────────────────────────────────────────────────────────────────────────┐
│           MIXED PRECISION TRAINING ARCHITECTURE                          │
│           (How GPT-4, Gemini, LLaMA are actually trained)                │
│                                                                          │
│   ┌────────────────────────────────────────────────────────┐             │
│   │  MASTER WEIGHTS (FP32) — stored in CPU/main memory     │             │
│   │  Full precision copy, updated once per step             │             │
│   └────────────────────┬───────────────────────────────────┘             │
│                        │ copy                                            │
│                        ▼                                                 │
│   ┌────────────────────────────────────────────────────────┐             │
│   │  FORWARD PASS (FP16/BF16) — runs on GPU                │             │
│   │  2× faster matmuls, 2× less memory                     │             │
│   └────────────────────┬───────────────────────────────────┘             │
│                        │                                                 │
│                        ▼                                                 │
│   ┌────────────────────────────────────────────────────────┐             │
│   │  LOSS SCALING — multiply loss by 1024 before backward   │             │
│   │  Prevents tiny gradients from underflowing to 0 in FP16 │             │
│   └────────────────────┬───────────────────────────────────┘             │
│                        │                                                 │
│                        ▼                                                 │
│   ┌────────────────────────────────────────────────────────┐             │
│   │  BACKWARD PASS (FP16/BF16)                              │             │
│   │  Gradients computed in low precision                     │             │
│   └────────────────────┬───────────────────────────────────┘             │
│                        │ unscale gradients (÷ 1024)                      │
│                        ▼                                                 │
│   ┌────────────────────────────────────────────────────────┐             │
│   │  OPTIMIZER STEP (FP32) — Adam on master weights         │             │
│   │  m, v accumulators MUST be FP32 or training diverges    │             │
│   └────────────────────────────────────────────────────────┘             │
│                                                                          │
│   WHY BF16 > FP16 for LLMs:                                             │
│   BF16 has same RANGE as FP32 (±3.4×10³⁸) but less precision.           │
│   FP16 has tiny range (±65504) → overflow on large logits.               │
│   Google TPUs use BF16 natively. NVIDIA A100+ supports both.             │
└──────────────────────────────────────────────────────────────────────────┘
```

```python
# ── Simulating Loss Scaling ──
def train_step_mixed_precision(model_fp32, x, y, loss_scale=1024):
    """What PyTorch AMP / DeepSpeed actually does under the hood."""
    # 1. Cast weights to FP16
    model_fp16 = {k: v.astype(np.float16) for k, v in model_fp32.items()}

    # 2. Forward pass in FP16
    z = x.astype(np.float16) @ model_fp16['W'] + model_fp16['b']
    loss_fp16 = np.mean((z - y.astype(np.float16)) ** 2)

    # 3. SCALE the loss before backward pass
    scaled_loss = loss_fp16 * loss_scale

    # 4. Backward pass in FP16 (gradients are bigger → don't underflow)
    grad_scaled = 2 * (z - y.astype(np.float16)) * loss_scale / len(y)

    # 5. UNSCALE gradients back to real values
    grad_real = grad_scaled.astype(np.float32) / loss_scale

    # 6. Check for inf/nan (skip step if found)
    if np.any(np.isinf(grad_real)) or np.any(np.isnan(grad_real)):
        print("⚠️ Inf/NaN detected, skipping step & reducing loss scale")
        return model_fp32, loss_scale / 2

    # 7. Update MASTER weights in FP32
    model_fp32['W'] -= 0.001 * grad_real
    return model_fp32, loss_scale
```

### Production Solution 3: Gradient Clipping (Prevents Exploding Gradients)

```python
import numpy as np

def clip_grad_norm_(gradients, max_norm=1.0):
    """Clip gradients by global norm — used in EVERY large model.
    
    Papers: 
      - 'On the difficulty of training RNNs' (Pascanu et al., 2013)
      - Used in GPT-2/3/4, LLaMA, PaLM, Gemini training
    
    Why global norm (not per-parameter)?
      Per-parameter clipping changes gradient DIRECTION.
      Global norm only changes MAGNITUDE — direction preserved.
    """
    # Compute global norm across ALL parameters
    total_norm = np.sqrt(sum(np.sum(g**2) for g in gradients))

    # Scale factor
    clip_coef = max_norm / (total_norm + 1e-6)
    clip_coef = min(clip_coef, 1.0)  # never scale UP

    # Apply clipping
    clipped = [g * clip_coef for g in gradients]

    print(f"  Global norm: {total_norm:.4f}")
    print(f"  Clip coef:   {clip_coef:.4f}")
    print(f"  {'CLIPPED ✂️' if clip_coef < 1.0 else 'No clipping needed ✅'}")
    return clipped

# Simulate gradients from a 3-layer network
grads = [
    np.random.randn(100, 256) * 5,    # Layer 1: large gradients!
    np.random.randn(256, 256) * 0.1,   # Layer 2: normal
    np.random.randn(256, 10) * 50,     # Layer 3: exploding! 💥
]

print("Before clipping:")
clipped = clip_grad_norm_(grads, max_norm=1.0)
# Global norm: ~800+ → clipped to 1.0
```

---

## B. Large-Scale Gradient Descent — Beyond Textbook SGD

### The Optimization Landscape at Scale

```
┌──────────────────────────────────────────────────────────────────────────┐
│              LOSS LANDSCAPE OF A 70B PARAMETER MODEL                     │
│                                                                          │
│  What textbooks show:          What actually happens:                    │
│                                                                          │
│    ╲    ╱                        ╱╲  ╱╲   ╱╲                            │
│     ╲  ╱                        ╱  ╲╱  ╲_╱  ╲  ╱╲  ╱╲                  │
│      ╲╱  ← one minimum         ╱     saddle   ╲╱  ╲╱  ╲_____           │
│                                ╱      points        local     ╲         │
│  Convex (easy!)               ╱    everywhere!       minima    ╲___     │
│                                                                    ╲    │
│                              REAL loss landscape:                       │
│                              - Billions of dimensions                   │
│                              - Saddle points (not local minima!)         │
│                              - Sharp vs flat minima matter               │
│                              - Loss spikes from data/numerical issues    │
│                                                                          │
│  KEY INSIGHT: In high dimensions, local minima are rare.                 │
│  Most "stuck" points are SADDLE POINTS.                                  │
│  SGD naturally escapes saddle points (noise helps!)                      │
│  (Ref: 'Identifying & attacking saddle point problem', Dauphin 2014)     │
└──────────────────────────────────────────────────────────────────────────┘
```

### Production Optimizer: AdamW (What LLMs Actually Use)

```python
import numpy as np

class AdamW:
    """AdamW optimizer — the ACTUAL optimizer used for:
    - GPT-4 (OpenAI)
    - LLaMA 2/3/4 (Meta)
    - Gemini (Google)
    - Claude (Anthropic)
    
    Key difference from Adam:
    Adam:  θ -= lr * (m̂/(√v̂+ε) + λ*θ)     ← L2 reg applied to adaptive grad
    AdamW: θ -= lr * m̂/(√v̂+ε) + lr*λ*θ     ← weight decay DECOUPLED
    
    Why it matters: L2 regularization in Adam is scale-dependent 
    (parameters with large gradients get less regularization).
    AdamW gives UNIFORM regularization regardless of gradient scale.
    
    Paper: 'Decoupled Weight Decay Regularization' (Loshchilov & Hutter, 2019)
    """
    def __init__(self, params, lr=1e-3, betas=(0.9, 0.999), eps=1e-8, 
                 weight_decay=0.01):
        self.lr = lr
        self.beta1, self.beta2 = betas
        self.eps = eps
        self.wd = weight_decay
        self.t = 0
        self.m = [np.zeros_like(p) for p in params]
        self.v = [np.zeros_like(p) for p in params]

    def step(self, params, grads):
        self.t += 1
        updated = []
        for i, (p, g) in enumerate(zip(params, grads)):
            # 1. Momentum (EMA of gradients)
            self.m[i] = self.beta1 * self.m[i] + (1 - self.beta1) * g
            # 2. Velocity (EMA of squared gradients)
            self.v[i] = self.beta2 * self.v[i] + (1 - self.beta2) * g**2
            # 3. Bias correction
            m_hat = self.m[i] / (1 - self.beta1**self.t)
            v_hat = self.v[i] / (1 - self.beta2**self.t)
            # 4. Adam update + DECOUPLED weight decay
            p = p - self.lr * (m_hat / (np.sqrt(v_hat) + self.eps)
                               + self.wd * p)   # ← decoupled!
            updated.append(p)
        return updated


# ── LLaMA 3 actual hyperparameters (from Meta's paper): ──
# lr = 1.5e-4 (with warmup + cosine decay)
# betas = (0.9, 0.95)      ← note: β₂=0.95, not 0.999!
# weight_decay = 0.1
# gradient_clip = 1.0
# warmup_steps = 2000
# batch_size = 4M tokens
```

### Learning Rate Schedules (Critical at Scale)

```python
import numpy as np

def llama_lr_schedule(step, total_steps=100000, warmup_steps=2000,
                      max_lr=1.5e-4, min_lr=1.5e-5):
    """LLaMA-style learning rate schedule.
    
    1. LINEAR WARMUP:  0 → max_lr over warmup_steps
    2. COSINE DECAY:   max_lr → min_lr over remaining steps
    
    Why warmup? At step 0, Adam's m and v are all zeros.
    Large lr + zero statistics = unstable updates.
    Warmup lets statistics "warm up" before taking big steps.
    
    Why cosine? Smooth decay. Better than step-decay because
    there's no sudden loss spike at decay boundaries.
    """
    if step < warmup_steps:
        # Linear warmup
        return max_lr * step / warmup_steps
    else:
        # Cosine decay
        progress = (step - warmup_steps) / (total_steps - warmup_steps)
        return min_lr + 0.5 * (max_lr - min_lr) * (1 + np.cos(np.pi * progress))

# Print schedule at key points
for step in [0, 500, 1000, 2000, 10000, 50000, 90000, 100000]:
    lr = llama_lr_schedule(step)
    phase = "warmup" if step < 2000 else "cosine"
    print(f"  Step {step:6d}: lr = {lr:.2e}  ({phase})")

# Step      0: lr = 0.00e+00  (warmup)
# Step    500: lr = 3.75e-05  (warmup)
# Step   2000: lr = 1.50e-04  (warmup peak)
# Step  10000: lr = 1.48e-04  (cosine — slow start)
# Step  50000: lr = 8.25e-05  (cosine — midpoint)
# Step  90000: lr = 2.10e-05  (cosine — nearing min)
# Step 100000: lr = 1.50e-05  (cosine — min_lr)
```

```
Learning Rate
1.5e-4 │         ╱‾‾‾‾╲
       │        ╱       ╲
       │       ╱         ╲
1.0e-4 │      ╱           ╲
       │     ╱              ╲
       │    ╱                 ╲
0.5e-4 │   ╱                   ╲
       │  ╱                     ╲
1.5e-5 │ ╱                       ╲___________
       ┼─────────────────────────────────────── step
       0   2K       25K      50K     75K   100K
         warmup        cosine decay
```

---

## C. Large-Scale Matrix Operations — How GPUs Actually Do It

### Tiled Matrix Multiplication (How NVIDIA Implements It)

```
┌──────────────────────────────────────────────────────────────────────────┐
│      TILED MATRIX MULTIPLY (What Tensor Cores Actually Do)               │
│                                                                          │
│  PROBLEM: A (4096×4096) @ B (4096×4096) = 68 BILLION multiply-adds      │
│           Full matrices don't fit in GPU SRAM (only ~192KB per SM)        │
│                                                                          │
│  SOLUTION: Tile-based computation                                        │
│                                                                          │
│  Matrix A              Matrix B              Matrix C                    │
│  ┌────┬────┬────┐      ┌────┬────┐           ┌────┬────┐                │
│  │ A₁₁│ A₁₂│ A₁₃│      │ B₁₁│ B₁₂│           │ C₁₁│ C₁₂│                │
│  ├────┼────┼────┤  @   ├────┼────┤     =     ├────┼────┤                │
│  │ A₂₁│ A₂₂│ A₂₃│      │ B₂₁│ B₂₂│           │ C₂₁│ C₂₂│                │
│  ├────┼────┼────┤      ├────┼────┤           ├────┼────┤                │
│  │ A₃₁│ A₃₂│ A₃₃│      │ B₃₁│ B₃₂│           │ C₃₁│ C₃₂│                │
│  └────┴────┴────┘      └────┴────┘           └────┴────┘                │
│                                                                          │
│  C₁₁ = A₁₁@B₁₁ + A₁₂@B₂₁ + A₁₃@B₃₁                                   │
│                                                                          │
│  Each tile (128×128) fits in SRAM. Process tile-by-tile.                 │
│  NVIDIA Tensor Cores: 4×4 FP16 matmul in ONE cycle.                     │
│  A100: 312 TFLOPS FP16 (vs 19.5 TFLOPS FP32 → 16× speedup)             │
│  H100: 989 TFLOPS FP16                                                  │
└──────────────────────────────────────────────────────────────────────────┘
```

### FlashAttention — The Biggest Algorithmic Breakthrough (Tri Dao, 2022)

```python
# ── Standard Attention: O(n²) memory ──
def standard_attention(Q, K, V):
    """This is what you see in papers. DO NOT use at scale."""
    d_k = Q.shape[-1]
    scores = Q @ K.T / np.sqrt(d_k)     # (n × n) matrix — 💥 at n=128K
    weights = softmax_stable(scores)      # (n × n) matrix — still in GPU HBM
    output = weights @ V                  # final result
    return output
    # Memory: O(n²) — for n=128K, that's 128K × 128K × 2 bytes = 32 GB!

# ── FlashAttention: O(n) memory ──
def flash_attention_simplified(Q, K, V, block_size=256):
    """Simplified FlashAttention — real impl is in CUDA/Triton.
    
    KEY IDEA: Never materialize the n×n attention matrix!
    Process blocks, keep running softmax statistics.
    
    Paper: 'FlashAttention: Fast and Memory-Efficient Exact Attention'
    Used in: GPT-4, LLaMA 2/3, Claude, Gemini, Mistral — literally everything
    """
    n, d = Q.shape
    output = np.zeros_like(Q)
    
    for i_start in range(0, n, block_size):
        i_end = min(i_start + block_size, n)
        Q_block = Q[i_start:i_end]
        
        # Running statistics for online softmax
        m_i = np.full(i_end - i_start, -np.inf)  # running max
        l_i = np.zeros(i_end - i_start)           # running sum
        O_i = np.zeros((i_end - i_start, d))      # running output
        
        for j_start in range(0, n, block_size):
            j_end = min(j_start + block_size, n)
            K_block = K[j_start:j_end]
            V_block = V[j_start:j_end]
            
            # Compute attention scores for this block
            S_block = Q_block @ K_block.T / np.sqrt(d)
            
            # Online softmax update
            m_new = np.maximum(m_i, np.max(S_block, axis=1))
            exp_old = np.exp(m_i - m_new)
            exp_new = np.exp(S_block - m_new[:, None])
            l_new = exp_old * l_i + np.sum(exp_new, axis=1)
            
            # Update output
            O_i = (exp_old[:, None] * l_i[:, None] * O_i + 
                   exp_new @ V_block) / l_new[:, None]
            
            m_i = m_new
            l_i = l_new
        
        output[i_start:i_end] = O_i
    
    return output
    # Memory: O(block_size²) ≈ O(1) relative to sequence length!
```

---

## D. Distributed Training Math — Scaling Across 10,000 GPUs

### Data Parallelism vs. Model Parallelism

```
┌──────────────────────────────────────────────────────────────────────────┐
│                DISTRIBUTED TRAINING STRATEGIES                           │
│                                                                          │
│  ╔═══════════════════════════════════════════════════════════╗           │
│  ║  DATA PARALLELISM (most common)                          ║           │
│  ║                                                          ║           │
│  ║  GPU 0: Full Model + Batch 0    ──┐                      ║           │
│  ║  GPU 1: Full Model + Batch 1    ──┤  AllReduce            ║           │
│  ║  GPU 2: Full Model + Batch 2    ──┤  (average grads)      ║           │
│  ║  GPU 3: Full Model + Batch 3    ──┘                      ║           │
│  ║                                                          ║           │
│  ║  Each GPU has FULL model copy.                            ║           │
│  ║  Works when model fits in 1 GPU (~7B params in 80GB)      ║           │
│  ╚═══════════════════════════════════════════════════════════╝           │
│                                                                          │
│  ╔═══════════════════════════════════════════════════════════╗           │
│  ║  TENSOR PARALLELISM (split each layer)                    ║           │
│  ║                                                          ║           │
│  ║  Layer matmul: Y = XW,  where W is (4096 × 16384)        ║           │
│  ║                                                          ║           │
│  ║  GPU 0: Y₀ = X @ W[:, :4096]    ← first 4096 columns     ║           │
│  ║  GPU 1: Y₁ = X @ W[:, 4096:8192]                         ║           │
│  ║  GPU 2: Y₂ = X @ W[:, 8192:12288]                        ║           │
│  ║  GPU 3: Y₃ = X @ W[:, 12288:]                            ║           │
│  ║  Y = concat(Y₀, Y₁, Y₂, Y₃)    ← AllGather               ║           │
│  ║                                                          ║           │
│  ║  Used for layers too large for one GPU.                    ║           │
│  ║  Megatron-LM (NVIDIA) uses this for 530B+ models.         ║           │
│  ╚═══════════════════════════════════════════════════════════╝           │
│                                                                          │
│  ╔═══════════════════════════════════════════════════════════╗           │
│  ║  PIPELINE PARALLELISM (split by layers)                    ║           │
│  ║                                                          ║           │
│  ║  GPU 0: Layers 0-15    ──▶                                ║           │
│  ║  GPU 1: Layers 16-31   ──▶                                ║           │
│  ║  GPU 2: Layers 32-47   ──▶                                ║           │
│  ║  GPU 3: Layers 48-63   ──▶ Output                         ║           │
│  ║                                                          ║           │
│  ║  Problem: "pipeline bubbles" (GPUs idle waiting for data)  ║           │
│  ║  Solution: micro-batching (GPipe, PipeDream)               ║           │
│  ╚═══════════════════════════════════════════════════════════╝           │
│                                                                          │
│  REALITY: LLaMA 70B uses ALL THREE simultaneously:                      │
│  8-way tensor parallel × 8-way pipeline parallel × data parallel         │
│  = 2048 GPUs training in sync                                            │
└──────────────────────────────────────────────────────────────────────────┘
```

### The AllReduce Problem

```python
def ring_allreduce(gradients_per_gpu, num_gpus=8):
    """Ring AllReduce — how gradients are synchronized across GPUs.
    
    Problem: Each GPU has its own gradients. We need the AVERAGE.
    Naive: Send all grads to GPU 0, average, broadcast back.
           → GPU 0 is bottleneck. O(n) bandwidth at root.
    
    Ring AllReduce: Each GPU sends to its neighbor in a ring.
           → O(1) bandwidth per GPU regardless of GPU count!
           → Used in NCCL (NVIDIA Collective Communication Library)
    
    Cost: 2(n-1)/n × data_size × latency_per_hop
    For n=8: only 1.75× a single transfer (not 8×!)
    """
    n = num_gpus
    param_size = len(gradients_per_gpu[0])
    chunk_size = param_size // n

    # Phase 1: Scatter-Reduce (n-1 steps)
    # Each GPU accumulates a different chunk
    buffers = [g.copy() for g in gradients_per_gpu]
    for step in range(n - 1):
        for gpu in range(n):
            send_chunk = (gpu - step) % n
            recv_chunk = (gpu - step - 1) % n
            next_gpu = (gpu + 1) % n
            # GPU sends its chunk to next GPU, which adds it
            # (simplified — real impl is asynchronous)

    # Phase 2: AllGather (n-1 steps)
    # Spread the fully-reduced chunks to all GPUs
    
    # Result: all GPUs have identical averaged gradients
    avg_gradient = np.mean(gradients_per_gpu, axis=0)
    return avg_gradient

# Real numbers:
# LLaMA 70B: ~140 GB of gradients (FP16)
# 8 GPUs in one node: NVLink 900 GB/s → AllReduce ≈ 0.3 seconds
# Cross-node (InfiniBand 400 Gb/s): → AllReduce ≈ 3 seconds
# That's why large-scale training is COMMUNICATION-BOUND, not compute-bound!
```

### Gradient Accumulation (Simulating Large Batch Sizes)

```python
def train_with_gradient_accumulation(model, data_loader, optimizer,
                                     accumulation_steps=8):
    """Simulate batch_size = 8 × micro_batch_size using 1 GPU.
    
    WHY: GPT-3 trained with batch_size = 3.2M tokens.
    One GPU can fit maybe 4K tokens. 
    3.2M / 4K = 800 gradient accumulation steps across GPUs.
    
    MATH: Gradient of sum = sum of gradients (linearity!)
    ∇L(batch) = (1/N) Σᵢ ∇L(sampleᵢ)
              = (1/N) Σⱼ Σₖ ∇L(micro_batchⱼ[k])
    """
    accumulated_grads = None

    for step, (x, y) in enumerate(data_loader):
        # Forward + backward on micro-batch
        loss, grads = compute_loss_and_grads(model, x, y)
        
        # Accumulate gradients
        if accumulated_grads is None:
            accumulated_grads = grads
        else:
            accumulated_grads = [a + g for a, g in zip(accumulated_grads, grads)]

        # Update only every N steps
        if (step + 1) % accumulation_steps == 0:
            # Average the accumulated gradients
            avg_grads = [g / accumulation_steps for g in accumulated_grads]
            optimizer.step(model.params, avg_grads)
            accumulated_grads = None
            print(f"Updated at step {step+1}, effective batch = "
                  f"{accumulation_steps}× micro_batch")
```

---

## E. Production SVD — How LoRA Actually Works at Meta

```python
import numpy as np

class LoRA:
    """LoRA: Low-Rank Adaptation of Large Language Models.
    Paper: Hu et al., 2021 (Microsoft Research)
    
    CORE IDEA based on SVD insight:
    - Full fine-tuning updates W by ΔW (same size as W)
    - LoRA factorizes ΔW = A @ B where A is (d×r) and B is (r×d)
    - r << d, so parameter count drops MASSIVELY
    
    WHY IT WORKS:
    The paper showed that weight updates during fine-tuning have 
    very low "intrinsic dimensionality." Most singular values of 
    ΔW are near zero. Rank r=8 captures 90%+ of the update.
    
    REAL NUMBERS (LLaMA 70B):
    - Full fine-tuning: 70B parameters to update = 140 GB
    - LoRA rank=16: only 160M parameters = 0.3 GB (467× less!)
    - Quality loss: < 1% on most benchmarks
    """
    def __init__(self, in_features, out_features, rank=8, alpha=16):
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank
        
        # A: initialized with Kaiming/Gaussian, B: initialized with zeros
        # → ΔW = A@B starts as ZERO matrix (no initial change!)
        self.A = np.random.randn(in_features, rank) * 0.01
        self.B = np.zeros((rank, out_features))
        
        # Original weight (FROZEN — never updated)
        self.W_frozen = np.random.randn(in_features, out_features) * 0.02

    def forward(self, x):
        # Original path (no grad needed)
        base_output = x @ self.W_frozen
        # LoRA path (only this gets gradients)
        lora_output = (x @ self.A @ self.B) * self.scaling
        return base_output + lora_output

    @property
    def trainable_params(self):
        return self.A.size + self.B.size

    @property
    def frozen_params(self):
        return self.W_frozen.size

# ── Demo ──
layer = LoRA(in_features=4096, out_features=4096, rank=8)
print(f"Frozen parameters:    {layer.frozen_params:>12,}")
print(f"Trainable parameters: {layer.trainable_params:>12,}")
print(f"Compression ratio:    {layer.frozen_params / layer.trainable_params:.0f}×")
print(f"Memory saved:         {(1 - layer.trainable_params/layer.frozen_params)*100:.2f}%")

# Frozen parameters:      16,777,216
# Trainable parameters:        65,536
# Compression ratio:    256×
# Memory saved:         99.61%

# Forward pass
x = np.random.randn(32, 4096)  # batch of 32
output = layer.forward(x)
print(f"\nInput shape:  {x.shape}")
print(f"Output shape: {output.shape}")
```

---

## F. Information Theory in Production — Real Systems

### Cross-Entropy Loss Pitfalls at Scale

```python
import numpy as np

def cross_entropy_production(logits, targets, label_smoothing=0.1,
                              ignore_index=-100):
    """Production cross-entropy with ALL the tricks.
    
    TRICK 1: Label Smoothing (Szegedy et al., 2016 — Google Inception v2)
      Instead of hard labels [0, 0, 1], use [0.033, 0.033, 0.933]
      WHY: Prevents model from becoming overconfident.
      GPT-3 doesn't use it. ViT uses 0.1. It's task-dependent.
    
    TRICK 2: Ignore Index
      For language models, padding tokens should NOT contribute to loss.
      Set target = -100 for padding → skip in loss computation.
    
    TRICK 3: Z-loss (PaLM paper, Google 2022)
      Add penalty on log(Σ exp(z))² to prevent logits from growing.
      Large logits → numerical instability in softmax.
    """
    num_classes = logits.shape[-1]
    
    # Stable log-softmax
    log_probs = logits - np.max(logits, axis=-1, keepdims=True)
    log_probs = log_probs - np.log(np.sum(np.exp(log_probs), axis=-1, keepdims=True))
    
    # Create mask for valid (non-padding) tokens
    valid_mask = targets != ignore_index
    targets_clean = np.where(valid_mask, targets, 0)
    
    # Label smoothing
    if label_smoothing > 0:
        smooth = label_smoothing / num_classes
        confidence = 1.0 - label_smoothing
        # One-hot with smoothing
        one_hot = np.full_like(logits, smooth)
        one_hot[np.arange(len(targets_clean)), targets_clean] = confidence + smooth
        loss = -np.sum(one_hot * log_probs, axis=-1)
    else:
        # Standard cross-entropy
        loss = -log_probs[np.arange(len(targets_clean)), targets_clean]
    
    # Apply mask
    loss = loss * valid_mask
    
    # Z-loss penalty (prevents logit drift)
    z_loss_weight = 1e-4
    log_z = np.log(np.sum(np.exp(logits - np.max(logits, axis=-1, keepdims=True)), 
                          axis=-1))
    z_loss = z_loss_weight * np.mean(log_z ** 2)
    
    total_loss = np.sum(loss) / np.sum(valid_mask) + z_loss
    return total_loss

# Example
logits = np.random.randn(4, 50257)  # batch=4, vocab=50257 (GPT-2 vocab)
targets = np.array([1024, 2048, -100, 512])  # -100 = padding

loss = cross_entropy_production(logits, targets, label_smoothing=0.1)
print(f"Loss: {loss:.4f}")
```

### KL Divergence in RLHF — The PPO Objective

```python
import numpy as np

def ppo_objective(log_probs_new, log_probs_old, advantages, 
                  log_probs_ref, kl_coeff=0.1, clip_range=0.2):
    """PPO-clip objective used in ChatGPT / Claude / Gemini RLHF training.
    
    Paper: 'Training language models to follow instructions with human feedback'
           (Ouyang et al., 2022 — OpenAI InstructGPT paper)
    
    L_PPO = E[ min(rₜ·Aₜ, clip(rₜ, 1-ε, 1+ε)·Aₜ) ] - β·KL(π_θ ‖ π_ref)
    
    rₜ = π_θ(aₜ|sₜ) / π_old(aₜ|sₜ)     (importance ratio)
    Aₜ = advantage estimate (from reward model)
    β  = KL penalty coefficient
    
    The KL term prevents "reward hacking":
    Without it, the model finds degenerate text that scores high
    on the reward model but is gibberish to humans.
    """
    # Importance ratio
    ratio = np.exp(log_probs_new - log_probs_old)

    # Clipped surrogate objective
    obj1 = ratio * advantages
    obj2 = np.clip(ratio, 1 - clip_range, 1 + clip_range) * advantages
    ppo_loss = -np.mean(np.minimum(obj1, obj2))

    # KL penalty (approximate KL using log probs)
    kl = np.mean(log_probs_new - log_probs_ref)
    kl_penalty = kl_coeff * kl

    total_loss = ppo_loss + kl_penalty

    print(f"PPO loss:    {ppo_loss:.4f}")
    print(f"KL penalty:  {kl_penalty:.4f} (β={kl_coeff})")
    print(f"Mean ratio:  {np.mean(ratio):.4f} (should be ≈1.0)")
    print(f"Total loss:  {total_loss:.4f}")
    return total_loss

# Simulate
n = 1000
log_probs_new = np.random.randn(n) * 0.1 - 5
log_probs_old = log_probs_new + np.random.randn(n) * 0.01
log_probs_ref = log_probs_new + np.random.randn(n) * 0.05
advantages = np.random.randn(n)

ppo_objective(log_probs_new, log_probs_old, advantages, log_probs_ref)
```

---

## G. 🔥 FAANG Interview Deep-Dive — 30 Questions Across Levels

### Level: L3/L4 (Junior/Mid — Fundamentals)

**Q1 (Google): "What is the derivative of ReLU? What problem does this cause?"**

```
ReLU(x) = max(0, x)

Derivative:
  ReLU'(x) = 0  if x < 0
              1  if x > 0
              undefined at x = 0 (in practice: 0)

PROBLEM: "Dying ReLU" — if a neuron's output is always negative,
gradient is ALWAYS 0 → neuron never updates → permanently dead.

In a network with 1000 neurons, 10-40% can die during training!

SOLUTIONS:
  1. Leaky ReLU:  f(x) = max(0.01x, x)  — small gradient when x < 0
  2. ELU:         f(x) = x if x>0, α(eˣ-1) if x≤0
  3. GELU:        f(x) = x·Φ(x)  — used in GPT/BERT (smooth approximation)
  4. SwiGLU:      f(x) = Swish(xW)⊙(xV)  — used in LLaMA, PaLM
  5. He initialization: W ~ N(0, 2/n_in) — keeps activations in good range
```

**Q2 (Amazon): "You trained a model and loss is NaN. How do you debug?"**

```
SYSTEMATIC DEBUGGING CHECKLIST:

1. CHECK DATA
   - Are there NaN/Inf in your input data?
   - Are labels out of expected range?
   - python: assert not torch.isnan(x).any()

2. CHECK LEARNING RATE
   - Too high → parameters explode → loss = NaN
   - Try lr /= 10 and see if NaN disappears

3. CHECK LOSS FUNCTION
   - log(0) = -inf → NaN
   - Division by zero in custom loss
   - Fix: torch.clamp(probs, min=1e-7) before log

4. CHECK FOR EXPLODING GRADIENTS
   - Print gradient norms per layer
   - Add gradient clipping: torch.nn.utils.clip_grad_norm_(params, 1.0)

5. CHECK NUMERICAL PRECISION
   - FP16 overflow: logits > 65504 → Inf
   - Fix: use BF16, or add loss scaling

6. CHECK NORMALIZATION
   - BatchNorm with batch_size=1 → variance=0 → division by zero
   - LayerNorm input all identical → variance=0
   
PRODUCTION TIP (Meta): Add `torch.autograd.detect_anomaly()` during 
debugging to pinpoint exactly which operation produced NaN.
```

**Q3 (Meta): "Explain batch normalization mathematically and why it helps."**

```
FORWARD PASS:
  μ_B = (1/m) Σ xᵢ                    (batch mean)
  σ²_B = (1/m) Σ (xᵢ - μ_B)²          (batch variance)
  x̂ᵢ = (xᵢ - μ_B) / √(σ²_B + ε)      (normalize)
  yᵢ = γ · x̂ᵢ + β                      (scale & shift — learnable!)

WHY IT HELPS (three complementary explanations):
  1. ORIGINAL CLAIM (Ioffe & Szegedy, 2015): 
     Reduces "internal covariate shift" — each layer's input 
     distribution changes as previous layers update.
     
  2. MODERN UNDERSTANDING (Santurkar et al., 2018):
     Actually, it smooths the loss landscape. BatchNorm makes 
     the loss surface more Lipschitz → larger learning rates work.
     
  3. IMPLICIT REGULARIZATION:
     Each mini-batch adds noise through μ_B and σ²_B estimates.
     This acts like dropout — prevents overfitting.

WHY LayerNorm REPLACED BatchNorm in Transformers:
  - BatchNorm needs batch statistics → breaks for batch_size=1 at inference
  - BatchNorm breaks for variable-length sequences (padding issue)
  - LayerNorm normalizes across features, not batch → no batch dependency
```

### Level: L5/L6 (Senior — Production Depth)

**Q4 (Google Brain): "Explain the gradient flow in a ResNet and why skip connections solve vanishing gradients."**

```
STANDARD NETWORK:
  x → f₁ → f₂ → ... → fₙ → loss
  
  ∂loss/∂x = ∂fₙ/∂fₙ₋₁ · ∂fₙ₋₁/∂fₙ₋₂ · ... · ∂f₁/∂x
  
  If each |∂fᵢ/∂fᵢ₋₁| < 1: gradient → 0 (vanishing)
  If each |∂fᵢ/∂fᵢ₋₁| > 1: gradient → ∞ (exploding)

RESNET (He et al., 2015):
  y = f(x) + x     ← skip connection!
  
  ∂y/∂x = ∂f(x)/∂x + 1    ← the "+1" is the key!
  
  Even if ∂f(x)/∂x ≈ 0, the gradient is still ≈ 1.
  The gradient has a "highway" to flow back unchanged.
  
  Through 100 layers:
    Standard: ∂L/∂x ≈ 0.9¹⁰⁰ ≈ 0.00003  (vanished!)
    ResNet:   ∂L/∂x ≈ 1.0 + small_corrections  (healthy!)

THIS IS WHY:
  - Pre-ResNet: training 20+ layers was extremely hard
  - Post-ResNet: training 1000+ layers is routine
  - Transformers use skip connections in EVERY layer
```

**Q5 (OpenAI): "You're training a 70B model and see loss spikes. Diagnose."**

```
LOSS SPIKE TAXONOMY (from real training runs):

1. DATA ISSUE (most common)
   - Batch contains corrupted/extreme data
   - Diagnosis: log batch statistics, check for outlier tokens
   - Fix: data filtering, gradient clipping handles most cases
   
2. LEARNING RATE TOO HIGH AT CURRENT STAGE
   - Often happens right after warmup ends
   - Fix: extend warmup, reduce max_lr
   
3. NUMERICAL INSTABILITY
   - Logits grow too large → softmax overflow
   - Fix: Z-loss regularization (penalize large logits)
   - PaLM paper documents this extensively
   
4. NORM GROWTH
   - Embedding norms or attention logits drift upward over training
   - Fix: QK-norm (normalize Q and K before dot product)
   - Used in ViT-22B, PaLM-2

5. INTER-GPU DESYNC
   - Rare but devastating: one GPU gets different gradients
   - Causes: non-deterministic operations, bit-flip in memory
   - Fix: periodic checksum validation across replicas

RECOVERY STRATEGY (used at Meta/Google):
  1. Rewind to checkpoint 100 steps before spike
  2. Skip the bad data batch
  3. Reduce learning rate by 10%
  4. Resume training
  5. If repeated: check hardware (GPU memory errors are real!)
```

**Q6 (NVIDIA): "How do you choose between FP16, BF16, and FP8 for training?"**

```
                    FP32        BF16        FP16        FP8 (E4M3)
Range:              ±3.4e38     ±3.4e38     ±65504      ±448
Precision:          7 digits    3 digits    3 digits    ~1.5 digits
Bytes per param:    4           2           2           1

DECISION FRAMEWORK:

Use FP32 for:
  └─ Optimizer states (Adam m, v)
  └─ Loss computation
  └─ Master weight copy

Use BF16 for:
  └─ LLM training (GPT-4, LLaMA, Claude)
  └─ Same range as FP32 → no overflow risk
  └─ Supported: Google TPU, NVIDIA A100+

Use FP16 for:
  └─ Vision models (less dynamic range needed)
  └─ REQUIRES loss scaling (overflow at >65504)
  └─ Faster on older NVIDIA GPUs (V100)

Use FP8 for:
  └─ Inference only (or very careful training)
  └─ H100 Transformer Engine
  └─ 2× throughput vs FP16
  └─ Requires per-tensor dynamic scaling

RULE OF THUMB: BF16 for training, FP8/INT8 for inference.
```

**Q7 (DeepMind): "Derive the softmax gradient and explain its computational implications."**

```
Softmax: pᵢ = exp(zᵢ) / Σⱼ exp(zⱼ)

Case 1: i = j (diagonal)
  ∂pᵢ/∂zᵢ = pᵢ(1 - pᵢ)

Case 2: i ≠ j (off-diagonal)
  ∂pᵢ/∂zⱼ = -pᵢ · pⱼ

Jacobian: J = diag(p) - ppᵀ

Combined with cross-entropy loss L = -Σ yᵢ log(pᵢ):
  ∂L/∂zᵢ = pᵢ - yᵢ

COMPUTATIONAL IMPLICATION:
  Full Jacobian is O(V²) where V = vocab size (e.g., 128K for LLaMA 3).
  128K × 128K × 4 bytes = 64 GB just for ONE token's Jacobian!
  
  But ∂L/∂z = p - y is O(V). We NEVER compute the full Jacobian.
  This is why the cross-entropy + softmax combination is special:
  the gradient simplifies to a single vector subtraction.
  
  At FAANG scale (V=128K, batch=4M tokens):
  Naive:  4M × 128K × 128K × 4B = impossible
  Smart:  4M × 128K × 4B = 2 TB (still large, but feasible)
```

### Level: Staff/Principal (L6+ — System Design)

**Q8 (Google): "Design the numerical stack for training a 1T parameter model."**

```
ARCHITECTURE:
  
  ┌────────────────────────────────────────────────────────────────┐
  │  1 TRILLION PARAMETER MODEL TRAINING STACK                      │
  │                                                                │
  │  Hardware: 16,384 × H100 GPUs (2048 nodes, 8 GPUs each)        │
  │  Interconnect: 400 Gbps InfiniBand (3-level fat tree)           │
  │  Memory: 80GB HBM3 per GPU → 1.3 PB total GPU memory           │
  │                                                                │
  │  MODEL PARTITION (3D parallelism):                              │
  │  ├── Tensor Parallel: 8-way (within node, NVLink)               │
  │  ├── Pipeline Parallel: 16-way (across nodes)                   │
  │  ├── Data Parallel: 128-way (FSDP/ZeRO-3)                      │
  │  └── 8 × 16 × 128 = 16,384 GPUs ✓                              │
  │                                                                │
  │  MEMORY BUDGET PER GPU (80 GB):                                 │
  │  ├── Model shard (FP16):     ~12 GB  (1T/16384 × 2 bytes × 2)  │
  │  ├── Optimizer states (FP32): ~24 GB  (Adam: 2× params in FP32)│
  │  ├── Activations:            ~30 GB  (with activation ckpt)     │
  │  ├── Gradients:              ~12 GB                             │
  │  └── Communication buffers:   ~2 GB                             │
  │                               ─────                             │
  │                                80 GB ✓                          │
  │                                                                │
  │  NUMERICAL CHOICES:                                             │
  │  ├── Forward/Backward: BF16                                     │
  │  ├── Optimizer: FP32 master weights + FP32 Adam states          │
  │  ├── Gradient AllReduce: BF16 (with gradient compression)       │
  │  ├── Softmax: FP32 for attention scores (numerical safety)      │
  │  ├── LayerNorm: FP32 for mean/variance computation              │
  │  └── Loss: FP32                                                 │
  │                                                                │
  │  CRITICAL TECHNIQUES:                                           │
  │  ├── Activation Checkpointing: Recompute activations in         │
  │  │   backward pass instead of storing (3× compute, 10× memory)  │
  │  ├── ZeRO-3 (DeepSpeed): Shard optimizer + gradients + params   │
  │  │   across all data-parallel ranks                              │
  │  ├── Sequence Parallelism: Distribute LayerNorm/Dropout          │
  │  │   across tensor-parallel ranks                                │
  │  └── Communication-Computation Overlap: Start AllReduce          │
  │      while still computing next layer's forward pass              │
  │                                                                │
  │  FAULT TOLERANCE:                                               │
  │  ├── Checkpoint every 100 steps (async, to distributed storage)  │
  │  ├── Automatic GPU failure detection + replacement               │
  │  ├── Elastic training (continue with fewer GPUs if needed)       │
  │  └── ECC memory checks (bit flips cause silent corruption)       │
  └────────────────────────────────────────────────────────────────┘
```

**Q9 (Meta): "How does FSDP (Fully Sharded Data Parallel) save memory? Explain the math."**

```
PROBLEM: Adam optimizer for 70B model:
  Parameters:     70B × 2 bytes (FP16)  =  140 GB
  Gradients:      70B × 2 bytes (FP16)  =  140 GB
  Adam m (FP32):  70B × 4 bytes         =  280 GB
  Adam v (FP32):  70B × 4 bytes         =  280 GB
  Master (FP32):  70B × 4 bytes         =  280 GB
                                         ─────────
  Total per GPU:                          1,120 GB  💥 (GPU has 80 GB!)

FSDP SOLUTION: Shard everything across N GPUs.
  With N = 64 GPUs:
  Each GPU stores: 1,120 GB / 64 = 17.5 GB ✓ Fits!

HOW IT WORKS:
  1. Each GPU stores only 1/N of params, grads, and optimizer states
  2. Before forward pass of layer L:
     AllGather W_L from all GPUs → full W_L in memory
  3. Compute forward for layer L
  4. Discard full W_L (only keep 1/N shard)
  5. Backward: AllGather again, compute grads, ReduceScatter
  6. Each GPU updates only its 1/N shard of optimizer states

TRADE-OFF:
  Communication: 3× more AllGather/ReduceScatter ops
  But: overlapped with computation → near-zero overhead on fast interconnect
  
  Memory savings:  O(Model/N) per GPU
  Communication:   O(Model) per step (same as DDP!)
```

**Q10 (Anthropic): "What mathematical properties make Transformer training stable at scale?"**

```
STABILITY INGREDIENTS IN MODERN TRANSFORMERS:

1. PRE-NORM (vs Post-Norm)
   Pre:  x + Attention(LayerNorm(x))    ← LLaMA, GPT-3, PaLM
   Post: LayerNorm(x + Attention(x))    ← Original Transformer
   
   Pre-Norm: gradient flows through skip connection FIRST,
   then through a normalized sub-path. More stable.
   
2. RMSNorm (vs LayerNorm)
   LayerNorm: (x - μ) / σ · γ + β    (center + scale)
   RMSNorm:   x / RMS(x) · γ         (scale only, no centering)
   
   RMSNorm is 10-15% faster and equally effective.
   Used in: LLaMA, Gemma, Mistral
   
3. QK-NORM
   score = (Q·Kᵀ) / √d_k
   Problem: Q and K norms grow during training → scores explode
   Fix: Normalize Q and K before dot product
   score = (norm(Q) · norm(Kᵀ)) / √d_k
   
4. ROTARY POSITION EMBEDDING (RoPE)
   Encodes position through rotation matrices.
   Key property: relative position information preserved in dot product.
   Numerically stable because rotation matrices have norm = 1.
   
5. MUON / μP SCALING (Maximal Update Parameterization)
   Scale initialization and learning rate by width:
   - Init: W ~ N(0, 1/√width)
   - LR per layer varies by role
   → Hyperparameters transfer across model sizes!
   Train with 125M params, use same HPs for 70B.
   Paper: 'Tensor Programs V' (Yang et al., 2022)
```

---

## H. Best Practices Checklist — Production Training

```
┌──────────────────────────────────────────────────────────────────────────┐
│          ✅ PRODUCTION TRAINING CHECKLIST                                │
│          (Used at Google, Meta, OpenAI, Anthropic)                        │
│                                                                          │
│  DATA                                                                    │
│  □ Deduplicate training data (MinHash / exact match)                     │
│  □ Filter toxic/low-quality content                                      │
│  □ Validate data loading pipeline (check shapes, dtypes, ranges)         │
│  □ Log data statistics per batch (mean, std, min, max)                   │
│                                                                          │
│  NUMERICAL                                                               │
│  □ Use BF16 for training, FP32 for optimizer states                      │
│  □ Gradient clipping (max_norm = 1.0)                                    │
│  □ Check for NaN/Inf every N steps                                       │
│  □ Use stable softmax (subtract max)                                     │
│  □ Z-loss regularization for large vocab models                          │
│  □ FP32 for LayerNorm/RMSNorm variance computation                      │
│                                                                          │
│  OPTIMIZATION                                                            │
│  □ AdamW with decoupled weight decay                                     │
│  □ Linear warmup (1-5% of total steps)                                   │
│  □ Cosine or WSD learning rate schedule                                  │
│  □ β₂ = 0.95 for LLMs (not default 0.999)                               │
│  □ Weight decay = 0.1                                                    │
│  □ Gradient accumulation for effective large batch                       │
│                                                                          │
│  ARCHITECTURE                                                            │
│  □ Pre-LayerNorm (not Post-LayerNorm)                                    │
│  □ RMSNorm instead of LayerNorm                                          │
│  □ SwiGLU activation in FFN                                              │
│  □ RoPE for position encoding                                            │
│  □ GQA (Grouped Query Attention) for inference efficiency                │
│                                                                          │
│  MONITORING                                                              │
│  □ Log loss, gradient norm, learning rate every step                     │
│  □ Log parameter norms per layer every 100 steps                        │
│  □ Log activation statistics every 100 steps                            │
│  □ Alert on loss spike (> 2× moving average)                             │
│  □ Alert on gradient norm spike                                          │
│  □ Validation eval every 1000 steps                                      │
│                                                                          │
│  FAULT TOLERANCE                                                         │
│  □ Checkpoint every 100-500 steps                                        │
│  □ Keep last 5 checkpoints (for rollback)                                │
│  □ Async checkpointing (don't block training)                            │
│  □ Verify checkpoint loading before long training run                    │
│  □ Watchdog process to restart on hardware failure                       │
│                                                                          │
│  EVALUATION                                                              │
│  □ Eval on diverse benchmarks (not just one metric)                      │
│  □ Track perplexity, downstream task accuracy, calibration               │
│  □ Watch for benchmark overfitting (contamination in train data)         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## I. Key Research Papers Reference

| Paper | Year | Key Math Concept | Impact |
|-------|------|-----------------|--------|
| Backpropagation (Rumelhart et al.) | 1986 | Chain rule for networks | Foundation of all NN training |
| Adam Optimizer (Kingma & Ba) | 2015 | EMA of gradients + adaptive LR | Default optimizer for a decade |
| Batch Normalization (Ioffe & Szegedy) | 2015 | Running statistics normalization | Enabled deeper networks |
| ResNet (He et al.) | 2015 | Skip connections (f(x) + x) | 1000+ layer networks possible |
| Attention Is All You Need (Vaswani) | 2017 | Scaled dot-product attention | Started the Transformer era |
| Mixed Precision Training (Micikevicius) | 2018 | FP16/FP32 hybrid arithmetic | 2× speedup for free |
| AdamW (Loshchilov & Hutter) | 2019 | Decoupled weight decay | Standard for LLM training |
| LoRA (Hu et al.) | 2021 | Low-rank matrix factorization | 100-1000× cheaper fine-tuning |
| FlashAttention (Dao et al.) | 2022 | Online softmax + tiling | O(n) memory attention |
| PaLM (Chowdhery et al.) | 2022 | Z-loss, training at 540B scale | Production training recipes |
| μP (Yang et al.) | 2022 | Width-dependent scaling rules | Hyperparameter transfer |
| QLoRA (Dettmers et al.) | 2023 | 4-bit quantization + LoRA | Fine-tune 65B on 1 GPU |
| GQA (Ainslie et al.) | 2023 | Grouped query attention | 8× KV-cache reduction |
| DeepSeek V3 (DeepSeek AI) | 2024 | MoE + multi-head latent attention | 671B params, 37B active |

---

## What's Next?

Continue to **[02 — Core AI Intuitions](./02-core-ai-intuitions.md)** to build deep intuition for dot products, softmax, broadcasting, and norms — the operations that power everything from search engines to ChatGPT.

---

> **📚 This guide is part of the AI Research Curriculum.**
> Designed for engineers preparing for FAANG AI/ML roles or transitioning into AI research.
