# Module 05 — Spectral

## Finding the DNA of a Matrix

> **Why Spectral Theory Matters in ML:** Eigenvalues and eigenvectors are the "DNA" of a transformation. They power PCA, PageRank, spectral clustering, stability analysis, and understanding why neural networks converge (or don't).

```
 MODULE 05 ROADMAP
 ═══════════════════════════════════════
 05.01 Invariant Directions & Spectra
 05.02 Spectral Decomposition
 ═══════════════════════════════════════
```

---

## 05.01 — Invariant Directions and Spectra (6 Lessons)

### Lesson 1: The Big Question

💡 **Key Intuition:** When you multiply a vector by a matrix, it usually changes both direction AND length. But some special vectors only get **stretched** (or shrunk) — they keep pointing the same way. These are **eigenvectors**.

```
Regular vector:              Eigenvector:
                             
  v ──A──→ Av               v ──A──→ λv
  ↗        ↘                 ↗         ↗↗↗
 Different direction!        SAME direction, just scaled by λ!
```

**Formal Definition:**

```
Av = λv

Where:
  A = square matrix (the transformation)
  v = eigenvector (the special direction) — v ≠ 0
  λ = eigenvalue (the scaling factor)
```

### Lesson 2: Finding Eigenvalues

To find eigenvalues, solve:

```
Av = λv
Av - λv = 0
(A - λI)v = 0

For non-trivial solutions: det(A - λI) = 0
This is the "characteristic equation"
```

📊 **Step-by-Step Example:**

```
       ┌     ┐
  A =  │ 4 1 │
       │ 2 3 │
       └     ┘

Step 1: Form A - λI
  ┌           ┐
  │ 4-λ   1   │
  │  2   3-λ  │
  └           ┘

Step 2: Set determinant = 0
  (4-λ)(3-λ) - (1)(2) = 0
  12 - 7λ + λ² - 2 = 0
  λ² - 7λ + 10 = 0
  (λ - 5)(λ - 2) = 0
  
  λ₁ = 5,  λ₂ = 2
```

```python
import numpy as np

A = np.array([[4, 1],
              [2, 3]])

# Find eigenvalues and eigenvectors
eigenvalues, eigenvectors = np.linalg.eig(A)
print(f"Eigenvalues: {eigenvalues}")   # [5. 2.]
print(f"Eigenvectors:\n{eigenvectors}")

# Verify: A @ v = λ * v for each pair
for i in range(len(eigenvalues)):
    lam = eigenvalues[i]
    v = eigenvectors[:, i]
    Av = A @ v
    lam_v = lam * v
    print(f"\nλ={lam:.0f}, v={v}")
    print(f"  A·v  = {Av}")
    print(f"  λ·v  = {lam_v}")
    print(f"  Equal? {np.allclose(Av, lam_v)}")
```

### Lesson 3: Finding Eigenvectors

After finding λ, plug back in to find v:

```
For λ₁ = 5:
  (A - 5I)v = 0
  ┌        ┐┌    ┐   ┌   ┐
  │ -1   1 ││ v₁ │ = │ 0 │
  │  2  -2 ││ v₂ │   │ 0 │
  └        ┘└    ┘   └   ┘
  
  -v₁ + v₂ = 0  →  v₁ = v₂
  Eigenvector: v₁ = [1, 1] (or any scalar multiple)

For λ₂ = 2:
  (A - 2I)v = 0
  ┌       ┐┌    ┐   ┌   ┐
  │ 2   1 ││ v₁ │ = │ 0 │
  │ 2   1 ││ v₂ │   │ 0 │
  └       ┘└    ┘   └   ┘
  
  2v₁ + v₂ = 0  →  v₂ = -2v₁
  Eigenvector: v₂ = [1, -2] (or any scalar multiple)
```

### Lesson 4: Geometric Interpretation

📊 **What Eigenvalues Tell You:**

```
λ > 1:  STRETCHES along eigenvector direction
        ──v──  →  ────v────

λ = 1:  NO CHANGE along this direction
        ──v──  →  ──v──

0 < λ < 1:  COMPRESSES along eigenvector direction
        ──v──  →  ─v─

λ = 0:  COLLAPSES to zero (matrix is singular!)
        ──v──  →  · 

λ < 0:  FLIPS direction AND scales
        ──v──  →  ←──v──
```

### Lesson 5: The Spectrum

The **spectrum** of a matrix is its set of all eigenvalues: σ(A) = {λ₁, λ₂, ..., λₙ}

**Key spectral properties:**

| Property | Formula | Meaning |
|---------|---------|---------|
| Trace | tr(A) = Σλᵢ | Sum of eigenvalues = sum of diagonal |
| Determinant | det(A) = Πλᵢ | Product of eigenvalues |
| Spectral radius | ρ(A) = max\|λᵢ\| | Largest eigenvalue magnitude |

```python
A = np.array([[4, 1],
              [2, 3]])

eigenvalues = np.linalg.eigvals(A)
print(f"Eigenvalues: {eigenvalues}")          # [5, 2]
print(f"Sum (trace): {sum(eigenvalues):.0f} = {np.trace(A)}")  # 7 = 7 ✓
print(f"Product (det): {np.prod(eigenvalues):.0f} = {np.linalg.det(A):.0f}")  # 10 = 10 ✓
```

### Lesson 6: Eigenvalues in ML — The PageRank Algorithm ⭐

⚡ **ML Connection — Google's PageRank is eigenvalue computation!**

```python
import numpy as np

def pagerank(adjacency_matrix, damping=0.85, iterations=100):
    """
    Google's PageRank: find the dominant eigenvector of the 
    modified adjacency matrix.
    """
    n = adjacency_matrix.shape[0]
    
    # Normalize columns (transition probabilities)
    M = adjacency_matrix / adjacency_matrix.sum(axis=0, keepdims=True)
    
    # Add damping (random surfer model)
    M = damping * M + (1 - damping) / n * np.ones((n, n))
    
    # Power iteration: find dominant eigenvector
    r = np.ones(n) / n  # Start uniform
    for _ in range(iterations):
        r = M @ r
        r /= r.sum()
    
    return r

# Simple web graph: 4 pages
#   Page 0 → Pages 1, 2
#   Page 1 → Page 2
#   Page 2 → Page 0
#   Page 3 → Pages 0, 1, 2
adj = np.array([
    [0, 0, 1, 1],  # who links TO page 0
    [1, 0, 0, 1],  # who links TO page 1
    [1, 1, 0, 1],  # who links TO page 2
    [0, 0, 0, 0],  # who links TO page 3 (no one!)
])

ranks = pagerank(adj.astype(float))
for i, r in enumerate(ranks):
    print(f"Page {i}: rank = {r:.4f}")

print(f"\nMost important page: Page {np.argmax(ranks)}")
```

---

## 05.02 — Spectral Decomposition (7 Lessons)

### Lesson 1: Diagonalization

If A has n linearly independent eigenvectors, it can be **diagonalized**:

```
A = PDP⁻¹

Where:
  P = matrix of eigenvectors (columns)
  D = diagonal matrix of eigenvalues
  P⁻¹ = inverse of P

  ┌         ┐   ┌       ┐┌       ┐┌         ┐
  │ 4    1  │ = │ v₁ v₂ ││ λ₁  0 ││         │
  │ 2    3  │   │       ││ 0  λ₂ ││  P⁻¹    │
  └         ┘   └       ┘└       ┘└         ┘
```

💡 **Key Intuition:** Diagonalization says: "This complex transformation is actually just stretching along some special directions." Change to the eigenvector basis, and the matrix becomes diagonal (just scaling).

```python
import numpy as np

A = np.array([[4, 1],
              [2, 3]])

# Eigendecomposition
eigenvalues, P = np.linalg.eig(A)
D = np.diag(eigenvalues)
P_inv = np.linalg.inv(P)

# Verify: A = P @ D @ P⁻¹
A_reconstructed = P @ D @ P_inv
print(f"Original A:\n{A}")
print(f"P @ D @ P⁻¹:\n{np.round(A_reconstructed, 10)}")
print(f"Equal? {np.allclose(A, A_reconstructed)}")  # True!
```

### Lesson 2: Power of Diagonalization — Matrix Powers

One huge benefit: computing Aⁿ becomes trivial!

```
A^n = P · D^n · P⁻¹

And D^n is just:
  ┌         ┐
  │ λ₁ⁿ  0  │     ← just raise each diagonal entry to the nth power!
  │  0  λ₂ⁿ │
  └         ┘
```

```python
# Computing A^100 efficiently
n_power = 100

# Slow way: multiply 100 times
A_slow = np.linalg.matrix_power(A, n_power)

# Fast way via diagonalization
D_power = np.diag(eigenvalues ** n_power)
A_fast = P @ D_power @ P_inv

print(f"A^{n_power} (direct):\n{np.round(A_slow, 2)}")
print(f"A^{n_power} (via diag):\n{np.round(A_fast, 2)}")
print(f"Equal? {np.allclose(A_slow, A_fast)}")
```

### Lesson 3: Symmetric Matrices Are Special

For **symmetric** matrices (A = Aᵀ), everything is nicer:

```
 ┌──────────────────────────────────────────────────┐
 │  SPECTRAL THEOREM FOR SYMMETRIC MATRICES         │
 │                                                    │
 │  If A = Aᵀ, then:                                │
 │  1. ALL eigenvalues are REAL (no complex numbers) │
 │  2. Eigenvectors are ORTHOGONAL                   │
 │  3. A = QΛQᵀ  (Q orthogonal: Q⁻¹ = Qᵀ)         │
 │                                                    │
 │  This is called the SPECTRAL DECOMPOSITION        │
 └──────────────────────────────────────────────────┘
```

⚡ **Why this matters in ML:** Covariance matrices are ALWAYS symmetric! So PCA always works beautifully.

```python
# Symmetric matrix example (covariance matrix)
data = np.random.randn(1000, 3)
C = np.cov(data.T)  # Covariance matrix — guaranteed symmetric

print(f"Symmetric? {np.allclose(C, C.T)}")  # True!

eigenvalues, Q = np.linalg.eigh(C)  # eigh = for symmetric matrices
print(f"Eigenvalues (all real): {eigenvalues}")

# Eigenvectors are orthogonal
print(f"Orthogonal? {np.allclose(Q.T @ Q, np.eye(3))}")  # True!

# Spectral decomposition: C = Q Λ Qᵀ
Lambda = np.diag(eigenvalues)
C_reconstructed = Q @ Lambda @ Q.T
print(f"Reconstruction matches? {np.allclose(C, C_reconstructed)}")  # True!
```

### Lesson 4: Positive Definite Matrices

A symmetric matrix A is **positive definite** if ALL eigenvalues > 0.

```
Positive Definite:    All λ > 0    → Bowl shape (has a minimum!)
Positive Semidefinite: All λ ≥ 0   → Bowl, possibly flat in some directions
Indefinite:           Mixed signs  → Saddle shape
Negative Definite:    All λ < 0    → Upside-down bowl (has a maximum!)
```

📊 **Why PD Matters — Loss Landscapes:**
```
Positive Definite (convex):     Indefinite (saddle):
                                        ╱╲
    ╲    ╱                        ╲    ╱  ╲
     ╲  ╱                          ╲╱    ╱
      ╲╱                           ╱╲  ╱
    minimum!                      ╱  ╲╱
                                 saddle point
  → Gradient descent             → Gradient descent might
    converges to minimum           get stuck!
```

```python
# Check positive definiteness
A_pd = np.array([[2, -1],
                  [-1, 2]])

eigenvalues = np.linalg.eigvalsh(A_pd)
print(f"Eigenvalues: {eigenvalues}")
print(f"Positive definite? {all(eigenvalues > 0)}")  # True

# Cholesky decomposition only works for PD matrices!
try:
    L = np.linalg.cholesky(A_pd)
    print(f"Cholesky L:\n{L}")
    print(f"L @ L.T = A? {np.allclose(L @ L.T, A_pd)}")
except np.linalg.LinAlgError:
    print("Not positive definite!")
```

### Lessons 5-7: Spectral Analysis in Practice

```python
import numpy as np

# FULL EXAMPLE: Spectral analysis of a neural network weight matrix
np.random.seed(42)

# Simulate a weight matrix
W = np.random.randn(10, 10) * 0.1

# Make it represent typical layer (symmetric version for illustration)
W_sym = W @ W.T  # This is always positive semidefinite

eigenvalues, eigenvectors = np.linalg.eigh(W_sym)

# Sort by magnitude
idx = np.argsort(np.abs(eigenvalues))[::-1]
eigenvalues = eigenvalues[idx]

print("Spectral Analysis of Weight Matrix:")
print("=" * 40)
print(f"Largest eigenvalue:  {eigenvalues[0]:.4f}")
print(f"Smallest eigenvalue: {eigenvalues[-1]:.4f}")
print(f"Condition number:    {eigenvalues[0]/eigenvalues[-1]:.1f}")
print(f"Spectral radius:     {max(np.abs(eigenvalues)):.4f}")
print(f"\nAll eigenvalues: {np.round(eigenvalues, 4)}")

# Effective rank (how many eigenvalues really matter)
energy = np.cumsum(eigenvalues ** 2) / np.sum(eigenvalues ** 2)
effective_rank = np.searchsorted(energy, 0.95) + 1
print(f"\nEffective rank (95% energy): {effective_rank} out of {len(eigenvalues)}")
```

---

## 🔥 FAANG Deep Dive — Spectral

### Interview Problem 1: Google — "Power Iteration (PageRank)"

```python
def power_iteration(A, num_iterations=1000, tol=1e-10):
    """
    Find the dominant eigenvalue and eigenvector.
    This is how Google computes PageRank!
    
    Time: O(n² × iterations)
    Space: O(n)
    """
    n = A.shape[0]
    b = np.random.randn(n)
    b = b / np.linalg.norm(b)
    
    for i in range(num_iterations):
        b_new = A @ b
        eigenvalue = np.dot(b_new, b)  # Rayleigh quotient
        b_new = b_new / np.linalg.norm(b_new)
        
        if np.linalg.norm(b_new - b) < tol:
            print(f"Converged in {i+1} iterations")
            break
        b = b_new
    
    return eigenvalue, b

A = np.array([[4, 1],
              [2, 3]])

eigenvalue, eigenvector = power_iteration(A)
print(f"Dominant eigenvalue: {eigenvalue:.4f}")   # ≈ 5.0
print(f"Dominant eigenvector: {eigenvector}")
```

### Interview Problem 2: Meta — "Spectral Clustering"

```python
import numpy as np

def spectral_clustering(data, k=2):
    """
    Cluster data using eigenvalues of the similarity matrix.
    Steps:
    1. Build similarity graph
    2. Compute graph Laplacian
    3. Find k smallest eigenvectors
    4. Cluster in eigenvector space
    """
    n = data.shape[0]
    
    # 1. Similarity matrix (Gaussian kernel)
    from scipy.spatial.distance import cdist
    dists = cdist(data, data, 'sqeuclidean')
    sigma = np.median(dists[dists > 0])
    W = np.exp(-dists / sigma)
    
    # 2. Graph Laplacian: L = D - W
    D = np.diag(W.sum(axis=1))
    L = D - W
    
    # 3. Find k smallest eigenvectors (skip λ₁=0)
    eigenvalues, eigenvectors = np.linalg.eigh(L)
    features = eigenvectors[:, 1:k+1]  # skip first (trivial)
    
    # 4. K-means in eigenvector space (simplified)
    from sklearn.cluster import KMeans
    labels = KMeans(n_clusters=k, random_state=42, n_init=10).fit_predict(features)
    
    return labels, eigenvalues[:k+2]

# Two moons dataset
np.random.seed(42)
t = np.linspace(0, np.pi, 100)
moon1 = np.column_stack([np.cos(t), np.sin(t)])
moon2 = np.column_stack([1 + np.cos(t), -np.sin(t) + 0.5])
data = np.vstack([moon1, moon2]) + 0.05 * np.random.randn(200, 2)

labels, eigenvalues = spectral_clustering(data, k=2)
print(f"Smallest eigenvalues: {eigenvalues}")
print(f"Cluster sizes: {np.bincount(labels)}")
```

---

## ✅ Module 05 Checkpoint

- [ ] Compute eigenvalues by solving det(A - λI) = 0
- [ ] Find eigenvectors by solving (A - λI)v = 0
- [ ] State the Spectral Theorem for symmetric matrices
- [ ] Diagonalize a matrix: A = PDP⁻¹
- [ ] Implement power iteration
- [ ] Explain PageRank using eigenvalues
- [ ] Determine if a matrix is positive definite from its spectrum
- [ ] Understand spectral clustering

**Next →** [Module 06: Projection](../module-06-projection/README.md)
