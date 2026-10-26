# Module 06 — Projection

## Measuring Similarity and Extracting Signal

> **Why Projections Matter in ML:** Cosine similarity in embeddings, least squares regression, Gram-Schmidt in QR decomposition, attention scores in transformers — all of these are projections. If linear algebra is a language, projection is its most-spoken verb.

```
 MODULE 06 ROADMAP
 ═══════════════════════════════════════
 06.01 Geometry from Inner Products
 06.02 Orthogonal Structure
 06.03 Projection & Orthonormalization
 ═══════════════════════════════════════
```

---

## 06.01 — Geometry from Inner Products (6 Lessons)

### Lesson 1: The Dot Product (Inner Product)

💡 **Key Intuition:** The dot product measures *how much two vectors agree in direction*. It combines magnitude and alignment into a single number.

```
a · b = a₁b₁ + a₂b₂ + ... + aₙbₙ

Geometric form:
a · b = |a| · |b| · cos(θ)

Where θ is the angle between a and b.
```

📊 **What the Dot Product Tells You:**
```
a · b > 0          a · b = 0          a · b < 0
  ↗ ↗               ↗                   ↗ ↙
 a  b               a → b↑              a  b
Same general         PERPENDICULAR       Opposite
direction            (orthogonal)        directions
```

```python
import numpy as np

a = np.array([1, 2, 3])
b = np.array([4, 5, 6])

# Dot product — three equivalent ways
dot1 = np.dot(a, b)
dot2 = a @ b
dot3 = sum(a_i * b_i for a_i, b_i in zip(a, b))
print(f"Dot product: {dot1} = {dot2} = {dot3}")  # 32

# Find the angle between vectors
cos_theta = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
theta = np.arccos(cos_theta)
print(f"Angle: {np.degrees(theta):.1f}°")  # 12.9°
```

### Lesson 2: Cosine Similarity — The ML Workhorse

⚡ **ML Connection:** Cosine similarity is the dot product of normalized vectors. It measures directional alignment, ignoring magnitude.

```
cos_sim(a, b) = (a · b) / (|a| · |b|)

Range: -1 (opposite) to 0 (perpendicular) to +1 (same direction)
```

```python
import numpy as np

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Document similarity (TF-IDF vectors)
doc1 = np.array([3, 0, 1, 0, 2])  # word frequencies
doc2 = np.array([2, 0, 1, 0, 3])  # similar topic
doc3 = np.array([0, 4, 0, 3, 0])  # different topic

print(f"doc1 vs doc2: {cosine_similarity(doc1, doc2):.3f}")  # ~0.94 (similar!)
print(f"doc1 vs doc3: {cosine_similarity(doc1, doc3):.3f}")  # ~0.00 (different!)

# Sentence transformer embeddings (simplified)
embed_hello = np.array([0.8, 0.2, 0.1])
embed_hi    = np.array([0.7, 0.3, 0.1])   # semantically similar
embed_car   = np.array([0.1, 0.1, 0.9])   # different meaning

print(f"\n'hello' vs 'hi':  {cosine_similarity(embed_hello, embed_hi):.3f}")
print(f"'hello' vs 'car': {cosine_similarity(embed_hello, embed_car):.3f}")
```

### Lesson 3: Norms — Measuring Size

| Norm | Formula | Name | Use Case |
|------|---------|------|----------|
| L1 | \|x\|₁ = Σ\|xᵢ\| | Manhattan | Sparse models (Lasso) |
| L2 | \|x\|₂ = √(Σxᵢ²) | Euclidean | Default distance, Ridge |
| L∞ | \|x\|∞ = max\|xᵢ\| | Chebyshev | Worst-case bounds |

```python
import numpy as np

x = np.array([3, -4, 0, 5])

print(f"L1 norm (Manhattan): {np.linalg.norm(x, 1)}")    # 12
print(f"L2 norm (Euclidean): {np.linalg.norm(x, 2):.3f}")# 7.071
print(f"L∞ norm (Max):       {np.linalg.norm(x, np.inf)}")# 5

# Regularization in ML uses these norms!
# L1 (Lasso): encourages sparsity (some weights become exactly 0)
# L2 (Ridge): encourages small weights (no weight dominates)

weights = np.array([0.5, -0.3, 0.0, 0.8, 0.0, -0.1])
l1_penalty = 0.01 * np.linalg.norm(weights, 1)   # = 0.017
l2_penalty = 0.01 * np.linalg.norm(weights, 2)**2 # = 0.0099
print(f"L1 penalty: {l1_penalty:.4f}")
print(f"L2 penalty: {l2_penalty:.4f}")
```

### Lessons 4-6: Inner Product Spaces and the Cauchy-Schwarz Inequality

**Cauchy-Schwarz Inequality (Most Important Inequality in Math):**

```
|a · b| ≤ |a| · |b|

Equality holds ⟺ a and b are parallel (a = cb for some scalar c)
```

💡 **Why it matters:** It guarantees cosine similarity always stays in [-1, 1].

```python
# Cauchy-Schwarz: always true!
for _ in range(5):
    a = np.random.randn(100)
    b = np.random.randn(100)
    lhs = abs(np.dot(a, b))
    rhs = np.linalg.norm(a) * np.linalg.norm(b)
    print(f"|a·b| = {lhs:.3f} ≤ |a|·|b| = {rhs:.3f}  →  {lhs <= rhs + 1e-10}")
```

---

## 06.02 — Orthogonal Structure (6 Lessons)

### Lesson 1: Orthogonality

Two vectors are **orthogonal** (perpendicular) if their dot product is zero:

```
a ⊥ b  ⟺  a · b = 0
```

⚡ **ML Connection:** Orthogonal features carry completely independent information — the ideal case!

```python
# Check orthogonality
a = np.array([1, 0, 0])
b = np.array([0, 1, 0])
c = np.array([1, 1, 0])

print(f"a·b = {np.dot(a, b)} → Orthogonal? {np.dot(a, b) == 0}")  # Yes
print(f"a·c = {np.dot(a, c)} → Orthogonal? {np.dot(a, c) == 0}")  # No
```

### Lesson 2: Orthogonal Matrices

A matrix Q is **orthogonal** if Qᵀ = Q⁻¹ (transpose equals inverse).

```
Properties:
  QᵀQ = QQᵀ = I      ← columns (and rows) are orthonormal
  |Qx| = |x|          ← preserves lengths
  (Qx)·(Qy) = x·y    ← preserves angles
  det(Q) = ±1         ← preserves volume (no stretching!)
```

💡 **Key Intuition:** Orthogonal matrices are pure rotations (and reflections). They reshape data without distorting it.

```python
# Rotation matrix is orthogonal
theta = np.pi / 4  # 45 degrees
Q = np.array([[np.cos(theta), -np.sin(theta)],
              [np.sin(theta),  np.cos(theta)]])

print(f"Q @ Q.T = I? {np.allclose(Q @ Q.T, np.eye(2))}")  # True
print(f"det(Q) = {np.linalg.det(Q):.3f}")                   # 1.000

# Rotation preserves length
v = np.array([3, 4])  # length = 5
v_rotated = Q @ v
print(f"|v| = {np.linalg.norm(v):.3f}")
print(f"|Qv| = {np.linalg.norm(v_rotated):.3f}")  # Also 5!
```

### Lessons 3-6: Orthogonal Complements and Decomposition

**Orthogonal Complement:** W⊥ is the set of all vectors perpendicular to every vector in W.

```
ℝⁿ = W ⊕ W⊥     ← any vector can be uniquely split into 
                     a W-part and a W⊥-part
```

📊 **Visual:**
```
                ↑ W⊥ (perpendicular part)
                │  
        ★ v    │
       ╱  │    │
      ╱   │    │
     ╱    │    │
────┼─────┼────────→ W (subspace)
    ↑     ↑
   proj   the "shadow"
          of v onto W
```

```python
import numpy as np

# Orthogonal decomposition: split any vector into W-part and W⊥-part
def orthogonal_decomposition(v, W_basis):
    """
    Decompose v = v_W + v_perp
    where v_W is in span(W_basis) and v_perp is perpendicular.
    """
    # First orthonormalize W_basis
    Q, _ = np.linalg.qr(np.column_stack(W_basis))
    k = len(W_basis)
    Q = Q[:, :k]
    
    # Project v onto W: v_W = Q @ Qᵀ @ v
    v_W = Q @ (Q.T @ v)
    v_perp = v - v_W
    
    return v_W, v_perp

# Example: W = xy-plane in ℝ³
w1 = np.array([1.0, 0, 0])
w2 = np.array([0, 1.0, 0])
v = np.array([3.0, 4.0, 5.0])

v_W, v_perp = orthogonal_decomposition(v, [w1, w2])
print(f"v = {v}")
print(f"v_W (in xy-plane) = {v_W}")      # [3, 4, 0]
print(f"v_perp (along z) = {v_perp}")     # [0, 0, 5]
print(f"v_W + v_perp = v? {np.allclose(v_W + v_perp, v)}")  # True!
print(f"v_W ⊥ v_perp? {abs(np.dot(v_W, v_perp)) < 1e-10}") # True!

# ML Example: Residuals in linear regression are the orthogonal complement
# ŷ = Xw  lives in column space of X
# residual = y - ŷ  lives in the orthogonal complement of col(X)
np.random.seed(42)
X = np.random.randn(50, 3)
y = np.random.randn(50)
w = np.linalg.lstsq(X, y, rcond=None)[0]
residual = y - X @ w
print(f"\nResidual ⊥ each column of X?")
for i in range(3):
    dot = np.dot(residual, X[:, i])
    print(f"  residual · X[:,{i}] = {dot:.2e}  (≈ 0 ✓)")
```

---

## 06.03 — Projection and Orthonormalization (6 Lessons)

### Lesson 1: Projection onto a Vector

The **projection** of b onto a is the "shadow" of b in the direction of a:

```
            b
           ╱│
          ╱ │
         ╱  │  ← residual (perpendicular to a)
        ╱   │
───────★────┼──────→ a
       proj_a(b)

Formula:
  proj_a(b) = (a · b / a · a) × a
```

```python
import numpy as np

def project_onto_vector(b, a):
    """Project vector b onto vector a."""
    scalar = np.dot(a, b) / np.dot(a, a)
    projection = scalar * a
    return projection

a = np.array([2, 1])
b = np.array([3, 4])

proj = project_onto_vector(b, a)
residual = b - proj

print(f"b = {b}")
print(f"proj_a(b) = {proj}")
print(f"residual = {residual}")
print(f"residual ⊥ a? {abs(np.dot(residual, a)) < 1e-10}")  # True!
```

### Lesson 2: Projection onto a Subspace

For a matrix A whose columns span the target subspace:

```
Projection matrix:  P = A(AᵀA)⁻¹Aᵀ

Properties:
  P² = P        ← projecting twice = projecting once (idempotent)
  Pᵀ = P        ← symmetric
  rank(P) = rank(A)
```

⚡ **ML Connection — Least Squares IS Projection!**

```python
import numpy as np

# LEAST SQUARES as projection
# We want to solve Ax ≈ b (overdetermined system)
# Solution: project b onto the column space of A

# Example: fit a line y = mx + c to data
x_data = np.array([1, 2, 3, 4, 5])
y_data = np.array([2.1, 3.9, 6.2, 7.8, 10.1])

# Design matrix A
A = np.column_stack([x_data, np.ones_like(x_data)])

# Normal equations: AᵀA x̂ = Aᵀb
# This is literally projecting b onto column space of A!
x_hat = np.linalg.solve(A.T @ A, A.T @ y_data)
print(f"Slope m = {x_hat[0]:.3f}")      # ≈ 2.0
print(f"Intercept c = {x_hat[1]:.3f}")  # ≈ 0.1

# The prediction ŷ = Ax̂ IS the projection of y onto col(A)
y_hat = A @ x_hat
residual = y_data - y_hat
print(f"Residual: {residual}")
print(f"Residual ⊥ col(A)? {np.allclose(A.T @ residual, 0)}")  # True!
```

### Lesson 3: Gram-Schmidt Orthonormalization ⭐

**Problem:** Given a set of linearly independent vectors, create an orthonormal set that spans the same space.

**Algorithm:**
```
Input: v₁, v₂, ..., vₖ (linearly independent)
Output: u₁, u₂, ..., uₖ (orthonormal)

u₁ = v₁ / |v₁|

For i = 2, 3, ..., k:
  w = vᵢ - Σⱼ₌₁ⁱ⁻¹ (vᵢ · uⱼ) × uⱼ    ← subtract all projections
  uᵢ = w / |w|                           ← normalize
```

📊 **Visual (2D case):**
```
Step 1: Normalize v₁         Step 2: Remove v₁ component from v₂
                                      
   v₁                          v₂    u₂ (perpendicular to u₁!)
   ╱      → u₁                ╱│     ↑
  ╱          →                ╱ │     │
 ╱                           ╱  │     │
─────────────                ────┼─────→ u₁
                              proj
```

```python
import numpy as np

def gram_schmidt(vectors):
    """
    Gram-Schmidt orthonormalization.
    Input: list of vectors (as rows or columns)
    Output: orthonormal basis
    """
    basis = []
    for v in vectors:
        w = v.copy().astype(float)
        # Subtract projections onto all previous basis vectors
        for u in basis:
            w -= np.dot(v, u) * u
        # Normalize
        norm = np.linalg.norm(w)
        if norm > 1e-10:
            basis.append(w / norm)
    return np.array(basis)

# Example
v1 = np.array([1, 1, 0])
v2 = np.array([1, 0, 1])
v3 = np.array([0, 1, 1])

Q = gram_schmidt([v1, v2, v3])
print("Orthonormal basis:")
for i, q in enumerate(Q):
    print(f"  u{i+1} = {np.round(q, 4)}")

# Verify orthonormality
print(f"\nOrthogonality check (Q @ Q.T):")
print(np.round(Q @ Q.T, 10))  # Should be identity
```

### Lesson 4: QR Decomposition

Gram-Schmidt leads directly to QR decomposition:

```
A = QR

Where:
  Q = orthogonal matrix (from Gram-Schmidt on columns of A)
  R = upper triangular matrix (the projection coefficients)
```

```python
import numpy as np

A = np.array([[1, 1, 0],
              [1, 0, 1],
              [0, 1, 1]])

Q, R = np.linalg.qr(A)
print(f"Q (orthogonal):\n{np.round(Q, 4)}")
print(f"R (upper triangular):\n{np.round(R, 4)}")
print(f"Q @ R = A? {np.allclose(Q @ R, A)}")      # True!
print(f"Q orthogonal? {np.allclose(Q.T @ Q, np.eye(3))}")  # True!
```

### Lesson 5: Applications of Projection in ML

```python
import numpy as np

# 1. ATTENTION MECHANISM in Transformers uses projection!
d_model = 4
d_k = 2

# Project queries and keys to lower dimension
W_Q = np.random.randn(d_model, d_k) * 0.1
W_K = np.random.randn(d_model, d_k) * 0.1
W_V = np.random.randn(d_model, d_k) * 0.1

# Input sequence (3 tokens, each d_model dimensional)
X = np.random.randn(3, d_model)

Q = X @ W_Q  # Project to query space
K = X @ W_K  # Project to key space
V = X @ W_V  # Project to value space

# Attention scores = similarity in projected space
scores = Q @ K.T / np.sqrt(d_k)
attention = np.exp(scores) / np.exp(scores).sum(axis=-1, keepdims=True)
output = attention @ V

print(f"Attention weights:\n{np.round(attention, 3)}")
print(f"Output shape: {output.shape}")


# 2. RANDOM PROJECTION for dimensionality reduction
# Johnson-Lindenstrauss lemma: random projections preserve distances!
n_original = 1000
n_reduced = 50
n_samples = 100

X_high = np.random.randn(n_samples, n_original)
R = np.random.randn(n_original, n_reduced) / np.sqrt(n_reduced)

X_low = X_high @ R  # Random projection!

# Compare pairwise distances
from scipy.spatial.distance import pdist
dist_original = pdist(X_high)
dist_projected = pdist(X_low)

relative_error = np.abs(dist_projected - dist_original) / dist_original
print(f"\nRandom Projection (1000D → 50D):")
print(f"Mean relative distance error: {relative_error.mean():.3f}")
print(f"Max relative distance error: {relative_error.max():.3f}")
```

### Lesson 6: Orthogonal Procrustes Problem

Finding the best rotation between two sets of points (used in embedding alignment):

```python
def orthogonal_procrustes(A, B):
    """
    Find orthogonal matrix R such that ||A @ R - B|| is minimized.
    Used to align word embeddings across languages!
    """
    M = A.T @ B
    U, S, Vt = np.linalg.svd(M)
    R = U @ Vt
    return R

# Example: align two word embedding spaces
np.random.seed(42)
n_words = 100
dim = 50

# English embeddings
X_en = np.random.randn(n_words, dim)

# French embeddings (rotated version + noise)
true_R = np.linalg.qr(np.random.randn(dim, dim))[0]
X_fr = X_en @ true_R + 0.1 * np.random.randn(n_words, dim)

# Find alignment
R_learned = orthogonal_procrustes(X_en, X_fr)
X_aligned = X_en @ R_learned

error = np.linalg.norm(X_aligned - X_fr) / np.linalg.norm(X_fr)
print(f"Alignment error: {error:.4f}")
```

---

## 🔥 FAANG Deep Dive — Projection

### Interview Problem 1: Google — "Closest Point on a Line"

```python
def closest_point_on_line(point, line_start, line_end):
    """
    Find the closest point on a line segment to a given point.
    This is a PROJECTION problem!
    """
    line_vec = line_end - line_start
    point_vec = point - line_start
    
    # Project point onto the line
    t = np.dot(point_vec, line_vec) / np.dot(line_vec, line_vec)
    t = np.clip(t, 0, 1)  # Clamp to line segment
    
    closest = line_start + t * line_vec
    return closest

point = np.array([3.0, 4.0])
line_start = np.array([0.0, 0.0])
line_end = np.array([5.0, 0.0])

closest = closest_point_on_line(point, line_start, line_end)
print(f"Closest point: {closest}")  # [3, 0] — projection onto x-axis
```

### Interview Problem 2: Meta — "K Nearest Neighbors with Cosine Similarity"

```python
def knn_cosine(query, database, k=3):
    """KNN using cosine similarity (projection-based distance)."""
    norms = np.linalg.norm(database, axis=1)
    query_norm = np.linalg.norm(query)
    
    similarities = database @ query / (norms * query_norm)
    top_k = np.argsort(similarities)[-k:][::-1]
    
    return top_k, similarities[top_k]

# Database of document embeddings
np.random.seed(42)
database = np.random.randn(1000, 128)
query = np.random.randn(128)

indices, sims = knn_cosine(query, database, k=5)
print(f"Top 5 neighbors: {indices}")
print(f"Similarities: {np.round(sims, 3)}")
```

---

## ✅ Module 06 Checkpoint

- [ ] Compute dot products and cosine similarity
- [ ] Distinguish L1, L2, and L∞ norms
- [ ] Project a vector onto another vector and onto a subspace
- [ ] Perform Gram-Schmidt orthonormalization
- [ ] Explain QR decomposition
- [ ] Connect least squares to projection onto column space
- [ ] Understand attention mechanism as projection

**Next →** [Module 07: Low Rank](../module-07-low-rank/README.md)
