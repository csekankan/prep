# Module 07 — Low Rank

## Compression Is Intelligence

> **Why Low Rank Matters in ML:** SVD is the Swiss army knife of linear algebra. It powers image compression, recommender systems (Netflix Prize), LoRA fine-tuning, latent semantic analysis, and noise reduction. If you understand SVD, you understand how models find structure in data.

```
 MODULE 07 ROADMAP
 ═══════════════════════════════════════
 07.01 Curvature & Quadratic Objectives
 07.02 Singular Value Decomposition
 ═══════════════════════════════════════
```

---

## 07.01 — Curvature and Quadratic Objectives (6 Lessons)

### Lesson 1: Quadratic Forms

A **quadratic form** is an expression like:

```
f(x) = xᵀAx

For x ∈ ℝ², A symmetric:
f(x₁, x₂) = a₁₁x₁² + 2a₁₂x₁x₂ + a₂₂x₂²
```

💡 **Key Intuition:** Quadratic forms define *bowls, saddles, and valleys* in high-dimensional space. Every loss function near its minimum looks like a quadratic form!

```python
import numpy as np

# Quadratic form: f(x) = xᵀAx
A = np.array([[2, 1],
              [1, 3]])

def quadratic_form(x, A):
    return x @ A @ x

# Evaluate at different points
for x in [np.array([1, 0]), np.array([0, 1]), np.array([1, 1])]:
    print(f"f({x}) = {quadratic_form(x, A)}")
```

### Lesson 2: The Hessian Matrix

The **Hessian** is the matrix of second derivatives — it captures curvature.

```
        ┌                        ┐
        │ ∂²f/∂x₁²   ∂²f/∂x₁∂x₂│
  H =   │                        │
        │ ∂²f/∂x₂∂x₁  ∂²f/∂x₂² │
        └                        ┘
```

⚡ **ML Connection:** The Hessian of the loss function tells you about:
- Curvature of the loss landscape
- How to set learning rates (Newton's method)
- Whether you're at a minimum, maximum, or saddle point

```python
# The Hessian determines the shape of the loss surface
# Eigenvalues of H tell you the curvature in each direction

H_bowl = np.array([[2, 0], [0, 3]])     # Both λ > 0 → minimum!
H_saddle = np.array([[2, 0], [0, -1]])   # Mixed signs → saddle!
H_valley = np.array([[10, 0], [0, 0.1]]) # Big ratio → narrow valley

for name, H in [("Bowl", H_bowl), ("Saddle", H_saddle), ("Valley", H_valley)]:
    eigenvalues = np.linalg.eigvalsh(H)
    condition = max(abs(eigenvalues)) / min(abs(eigenvalues))
    print(f"{name}: eigenvalues = {eigenvalues}, condition = {condition:.1f}")
```

### Lesson 3: Condition Number and Learning Rate

📊 **Why Condition Number Kills Gradient Descent:**

```
Well-conditioned (κ ≈ 1):         Ill-conditioned (κ >> 1):
Circular contours                  Elongated contours

    ╱──╲                              ════════════════
   │ ★  │     ← Easy to reach         ══════★═══════
    ╲──╱        minimum                ════════════════
                                       
 Few steps needed                  Many steps needed!
                                   GD oscillates across the valley
```

```python
import numpy as np

# Ill-conditioned system: gradient descent struggles
np.random.seed(42)

# Well-conditioned: eigenvalues [1, 1.5]
A_good = np.array([[1.25, 0.25], [0.25, 1.25]])

# Ill-conditioned: eigenvalues [0.01, 100]
A_bad = np.array([[50.005, 49.995], [49.995, 50.005]])

def gradient_descent_quadratic(A, x0, lr=0.01, steps=100):
    """Minimize f(x) = xᵀAx using gradient descent. Gradient = 2Ax."""
    x = x0.copy()
    trajectory = [x.copy()]
    for _ in range(steps):
        grad = 2 * A @ x
        x = x - lr * grad
        trajectory.append(x.copy())
    return np.array(trajectory)

x0 = np.array([5.0, 5.0])

traj_good = gradient_descent_quadratic(A_good, x0, lr=0.3, steps=20)
traj_bad = gradient_descent_quadratic(A_bad, x0, lr=0.005, steps=200)

print(f"Well-conditioned: κ = {np.linalg.cond(A_good):.1f}")
print(f"  Final point: {traj_good[-1]}, Distance to origin: {np.linalg.norm(traj_good[-1]):.6f}")
print(f"\nIll-conditioned: κ = {np.linalg.cond(A_bad):.0f}")
print(f"  Final point: {traj_bad[-1]}, Distance to origin: {np.linalg.norm(traj_bad[-1]):.6f}")
```

### Lessons 4-6: Positive Definite Quadratics and Optimization

**Newton's Method uses the Hessian:**

```
x_{n+1} = x_n - H⁻¹ ∇f(x_n)

Gradient descent:  x_{n+1} = x_n - α ∇f(x_n)     ← fixed step size
Newton's method:   x_{n+1} = x_n - H⁻¹ ∇f(x_n)   ← adaptive step using curvature
```

💡 **Key Insight:** Newton's method adjusts the step size based on curvature, so it handles ill-conditioned problems much better. But computing H⁻¹ is expensive (O(n³)), which is why we use approximations like Adam, L-BFGS, etc.

---

## 07.02 — Singular Value Decomposition (6 Lessons)

### Lesson 1: What Is SVD?

💡 **Key Intuition:** ANY matrix can be decomposed into three simple operations: **rotate → stretch → rotate**

```
A = UΣVᵀ

Where:
  U  = m×m orthogonal matrix (left rotation)
  Σ  = m×n diagonal matrix (stretching factors = singular values)
  Vᵀ = n×n orthogonal matrix (right rotation)
```

📊 **The SVD Story:**
```
  Step 1: Rotate (Vᵀ)     Step 2: Stretch (Σ)     Step 3: Rotate (U)
  
  ┌────┐    Vᵀ    ┌────┐    Σ     ╱────╲    U     ╱╲
  │    │  ──────▶  │    │  ──────▶ │    │  ──────▶ ╲╱
  └────┘           └────┘          ╲────╱           
  
  Align to          Same           Stretch along    Rotate to
  principal         position       principal axes   output space
  directions                       
```

**Eigendecomposition vs SVD:**

| | Eigendecomposition | SVD |
|---|---|---|
| Works for | Square matrices only | ANY matrix (m×n) |
| Formula | A = PDP⁻¹ | A = UΣVᵀ |
| Diagonal | Eigenvalues (can be negative/complex) | Singular values (always ≥ 0, real) |
| Basis matrices | May not be orthogonal | U, V always orthogonal |

### Lesson 2: Computing SVD

```python
import numpy as np

A = np.array([[3, 2, 2],
              [2, 3, -2]])

U, sigma, Vt = np.linalg.svd(A, full_matrices=True)

print(f"U (left vectors):\n{np.round(U, 4)}")
print(f"\nSingular values: {np.round(sigma, 4)}")
print(f"\nVᵀ (right vectors):\n{np.round(Vt, 4)}")

# Reconstruct A from SVD
Sigma = np.zeros_like(A, dtype=float)
np.fill_diagonal(Sigma, sigma)
A_reconstructed = U @ Sigma @ Vt
print(f"\nReconstructed A:\n{np.round(A_reconstructed, 10)}")
print(f"Match? {np.allclose(A, A_reconstructed)}")  # True!
```

### Lesson 3: Singular Values — What They Mean

Singular values σ₁ ≥ σ₂ ≥ ... ≥ σᵣ > 0 tell you:

```
σ₁ = how much A stretches in the MOST stretched direction
σ₂ = how much A stretches in the next direction
...
σᵣ = smallest stretch (r = rank of A)

LARGE σ → important direction (signal)
SMALL σ → unimportant direction (noise)
```

### Lesson 4: Low-Rank Approximation (The Killer App) ⭐

**Eckart-Young Theorem:** The best rank-k approximation of A is:

```
A ≈ Aₖ = U[:,:k] × Σ[:k,:k] × Vᵀ[:k,:]

(Keep only the k largest singular values and their vectors)
```

📊 **Image Compression Example:**
```
Original image (rank 1000):          Rank-50 approximation:
███████████████████████              ███████████████████████
█ Very detailed image █              █ Slightly blurry but █
█ 1000 × 1000 pixels █              █ 95% of the info!    █
███████████████████████              ███████████████████████
Storage: 1,000,000 numbers           Storage: 100,000 numbers (10×)
```

```python
import numpy as np

def low_rank_approx(A, k):
    """Best rank-k approximation of matrix A."""
    U, sigma, Vt = np.linalg.svd(A, full_matrices=False)
    return U[:, :k] @ np.diag(sigma[:k]) @ Vt[:k, :]

# Simulate an image (or any data matrix)
np.random.seed(42)
m, n = 100, 80

# Create a matrix with fast-decaying singular values (typical of real data)
U_true = np.linalg.qr(np.random.randn(m, m))[0]
V_true = np.linalg.qr(np.random.randn(n, n))[0]
sigma_true = np.exp(-0.3 * np.arange(min(m, n)))  # exponential decay
Sigma = np.zeros((m, n))
np.fill_diagonal(Sigma, sigma_true)
A = U_true @ Sigma @ V_true.T

print("Low-rank approximation quality:")
print(f"{'Rank k':>8} {'Storage':>10} {'Error':>10} {'% Energy':>10}")
print("-" * 42)

total_energy = np.sum(sigma_true ** 2)
for k in [1, 5, 10, 20, 50]:
    A_k = low_rank_approx(A, k)
    error = np.linalg.norm(A - A_k) / np.linalg.norm(A)
    storage_original = m * n
    storage_compressed = k * (m + n + 1)
    energy_captured = np.sum(sigma_true[:k]**2) / total_energy * 100
    
    print(f"{k:>8} {storage_compressed:>10} {error:>10.4f} {energy_captured:>9.1f}%")
```

### Lesson 5: SVD in Recommender Systems ⭐

⚡ **ML Connection — The Netflix Prize:**

```python
import numpy as np

def matrix_factorization_svd(ratings, k=2):
    """
    Recommender system using SVD.
    The Netflix $1M prize was essentially this idea!
    
    ratings: user × item matrix (0 = unknown)
    k: number of latent factors
    """
    # Fill unknown ratings with row means
    filled = ratings.copy().astype(float)
    for i in range(filled.shape[0]):
        mask = filled[i] != 0
        if mask.any():
            filled[i][~mask] = filled[i][mask].mean()
    
    # SVD decomposition
    U, sigma, Vt = np.linalg.svd(filled, full_matrices=False)
    
    # Keep top k factors
    U_k = U[:, :k]
    S_k = np.diag(sigma[:k])
    Vt_k = Vt[:k, :]
    
    # Reconstruct (predicted ratings)
    predicted = U_k @ S_k @ Vt_k
    return predicted

# User-Item rating matrix (5 users, 6 movies)
# 0 = not yet rated
ratings = np.array([
    [5, 4, 0, 0, 1, 0],  # User 0: likes action (movies 0,1)
    [4, 5, 1, 0, 0, 1],  # User 1: likes action
    [0, 1, 5, 4, 0, 5],  # User 2: likes drama (movies 2,3,5)
    [1, 0, 4, 5, 0, 4],  # User 3: likes drama
    [0, 0, 0, 0, 5, 0],  # User 4: only rated movie 4
])

predicted = matrix_factorization_svd(ratings, k=2)
print("Original ratings (0 = unknown):")
print(ratings)
print("\nPredicted ratings:")
print(np.round(predicted, 1))

# Recommend for User 4 (only rated movie 4)
user4_predictions = predicted[4]
unrated = np.where(ratings[4] == 0)[0]
print(f"\nRecommendations for User 4:")
for movie in unrated:
    print(f"  Movie {movie}: predicted rating = {user4_predictions[movie]:.1f}")
```

### Lesson 6: SVD and LoRA (Modern LLM Fine-Tuning)

```python
import numpy as np

# LoRA: Low-Rank Adaptation of Large Language Models
# Instead of fine-tuning the full weight matrix W (huge!),
# learn a low-rank update: W' = W + BA

d_model = 768    # Hidden dimension (like in BERT/GPT)
rank = 8         # LoRA rank (much smaller!)

# Original frozen weight matrix
W = np.random.randn(d_model, d_model) * 0.02

# LoRA matrices (tiny!)
B = np.random.randn(d_model, rank) * 0.02   # Down-projection
A = np.zeros((rank, d_model))                # Up-projection (init to 0)

# During fine-tuning, only B and A are updated
# Forward pass: y = (W + BA)x = Wx + BAx
x = np.random.randn(d_model)
y_original = W @ x
y_lora = W @ x + B @ (A @ x)  # BA adds a low-rank correction

print("LoRA Parameter Savings:")
print(f"  Full W:     {d_model * d_model:>10,} parameters")
print(f"  LoRA B + A: {d_model * rank + rank * d_model:>10,} parameters")
print(f"  Ratio:      {(d_model * rank * 2) / (d_model * d_model) * 100:.1f}%")

# SVD of the LoRA update BA
BA = B @ A
U, sigma, Vt = np.linalg.svd(BA, full_matrices=False)
print(f"\n  Rank of BA: {np.sum(sigma > 1e-10)} (at most {rank})")
```

---

## 🔥 FAANG Deep Dive — Low Rank

### Interview Problem 1: Google — "Image Compression with SVD"

```python
def compress_image_svd(image, k):
    """
    Compress a grayscale image using rank-k SVD approximation.
    
    Compression ratio: (m*n) / (k*(m+n+1))
    """
    U, sigma, Vt = np.linalg.svd(image, full_matrices=False)
    compressed = U[:, :k] @ np.diag(sigma[:k]) @ Vt[:k, :]
    
    m, n = image.shape
    original_size = m * n
    compressed_size = k * (m + n + 1)
    ratio = original_size / compressed_size
    
    return compressed, ratio

# Create a test image (gradient + pattern)
m, n = 200, 300
x, y = np.meshgrid(np.linspace(0, 1, n), np.linspace(0, 1, m))
image = np.sin(5 * x) * np.cos(3 * y) + 0.1 * np.random.randn(m, n)

for k in [1, 5, 10, 20, 50]:
    compressed, ratio = compress_image_svd(image, k)
    error = np.linalg.norm(image - compressed) / np.linalg.norm(image)
    print(f"Rank {k:>3}: compression {ratio:.1f}x, error {error:.4f}")
```

### Interview Problem 2: Amazon — "Find Latent Topics (LSA)"

```python
def latent_semantic_analysis(term_document_matrix, n_topics=2):
    """
    Find latent topics in documents using SVD.
    This is the precursor to modern topic models!
    """
    U, sigma, Vt = np.linalg.svd(term_document_matrix, full_matrices=False)
    
    # Topics are captured in the first n_topics singular vectors
    topic_term = Vt[:n_topics, :]        # How terms relate to topics
    doc_topic = U[:, :n_topics] @ np.diag(sigma[:n_topics])  # How docs relate to topics
    
    return doc_topic, topic_term, sigma

# Term-document matrix: 6 terms × 5 documents
# Rows = terms: [car, engine, horse, stable, algorithm, data]
# Cols = documents
tdm = np.array([
    [3, 0, 0, 2, 0],   # "car" in docs about vehicles
    [2, 0, 0, 3, 0],   # "engine"
    [0, 3, 0, 0, 0],   # "horse"
    [0, 2, 0, 0, 0],   # "stable"
    [0, 0, 4, 0, 3],   # "algorithm"
    [0, 0, 3, 0, 4],   # "data"
])

doc_topic, topic_term, sigma = latent_semantic_analysis(tdm, n_topics=3)
print("Singular values (topic importance):")
print(f"  {np.round(sigma[:5], 2)}")
print("\nDocument-Topic matrix (which topic each doc belongs to):")
print(np.round(doc_topic, 2))
```

---

## ✅ Module 07 Checkpoint

- [ ] Explain quadratic forms and their connection to loss surfaces
- [ ] Compute and interpret the Hessian matrix
- [ ] Explain why condition number affects gradient descent convergence
- [ ] Decompose any matrix using SVD: A = UΣVᵀ
- [ ] Perform low-rank approximation for compression
- [ ] Build a basic recommender system with SVD
- [ ] Explain how LoRA uses low-rank structure

**Next →** [Module 08: Applications](../module-08-applications/README.md)
