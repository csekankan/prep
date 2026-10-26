# Module 04 — Spaces

## Where Data Lives and How to Navigate It

> **Why Spaces Matter in ML:** Word embeddings live in vector spaces. The "latent space" in autoencoders IS a vector space. Understanding subspaces, bases, and rank tells you about the *true dimensionality* of your data — and that's the key to dimensionality reduction, compression, and understanding what your model has learned.

```
 MODULE 04 ROADMAP
 ═══════════════════════════════════════
 04.01 Vectors, Spans & Dependence
 04.02 Subspaces, Column & Null Spaces
 04.03 Bases as Coordinate Systems
 04.04 Dimension, Rank & Nullity
 ═══════════════════════════════════════
```

---

## 04.01 — Vectors, Spans and Dependence (5 Lessons)

### Lesson 1: What Is a Vector?

💡 **Key Intuition:** A vector is an arrow with a direction and magnitude. In ML, it's just an *ordered list of numbers* — a point in space.

```
             ↑ y
             │     ★ v = [3, 2]
             │    ╱
         2 ──│───╱
             │  ╱
             │ ╱
         ────┼╱──────→ x
             │  3
```

**Three perspectives of a vector:**

| Perspective | Example | Used In |
|------------|---------|---------|
| **Arrow** (geometry) | Direction + magnitude | Physics, intuition |
| **Point** (coordinate) | Position in space | Data points, features |
| **List of numbers** (algebra) | [3, 2, 1, 4] | Code, computation |

```python
import numpy as np

# A vector is just an array of numbers
v = np.array([3, 2])          # 2D vector
w = np.array([1, -1, 4, 0.5]) # 4D vector (can't visualize, but math works!)

# Word embedding: a word IS a vector
# (simplified example — real ones have 300-768 dimensions)
word_king  = np.array([0.9, 0.1, 0.8, 0.2])
word_queen = np.array([0.9, 0.1, 0.2, 0.8])
word_man   = np.array([0.7, 0.3, 0.9, 0.1])
word_woman = np.array([0.7, 0.3, 0.1, 0.9])

# The famous equation: king - man + woman ≈ queen
result = word_king - word_man + word_woman
print(f"king - man + woman = {result}")
print(f"queen              = {word_queen}")
print(f"Close? {np.allclose(result, word_queen)}")  # True!
```

### Lesson 2: Vector Operations

```python
import numpy as np

a = np.array([1, 2, 3])
b = np.array([4, 5, 6])

# Addition: component-wise
print(f"a + b = {a + b}")        # [5, 7, 9]

# Scalar multiplication: stretch/shrink
print(f"3 * a = {3 * a}")        # [3, 6, 9]

# Magnitude (length/norm)
print(f"|a| = {np.linalg.norm(a):.3f}")  # 3.742

# Unit vector (direction only, length = 1)
a_hat = a / np.linalg.norm(a)
print(f"â = {a_hat}")
print(f"|â| = {np.linalg.norm(a_hat):.3f}")  # 1.000
```

### Lesson 3: Linear Combinations

A **linear combination** of vectors v₁, v₂, ..., vₖ is:

```
c₁v₁ + c₂v₂ + ... + cₖvₖ    (where c₁, c₂, ... are scalars)
```

💡 **Key Intuition:** A linear combination lets you "mix" vectors by stretching them and adding them together.

```python
import numpy as np

v1 = np.array([1, 0])  # →
v2 = np.array([0, 1])  # ↑

# Any 2D vector is a linear combination of v1 and v2
target = np.array([3, 7])
c1, c2 = 3, 7
print(f"{c1}·v1 + {c2}·v2 = {c1*v1 + c2*v2}")  # [3, 7] ✓

# In ML: a prediction is a linear combination of features
features = np.array([1500, 3, 2])  # sqft, bedrooms, bathrooms
weights  = np.array([100, 5000, 3000])  # learned weights
prediction = np.dot(features, weights)  # linear combination!
print(f"House price prediction: ${prediction:,}")  # $161,000
```

### Lesson 4: Span

The **span** of a set of vectors is ALL possible linear combinations of those vectors.

```
span({v1, v2}) = {c₁v₁ + c₂v₂ : c₁, c₂ ∈ ℝ}
```

📊 **Visual Examples:**
```
span of ONE vector:          span of TWO vectors (not parallel):
A LINE through origin        THE ENTIRE 2D PLANE
                             
     /                           ╱───────╱
    /                           ╱───────╱
───/───                        ╱───────╱
  /                           ╱───────╱
 /                           
```

⚡ **ML Connection:** The span of your feature vectors determines what your model CAN represent. If features don't span the output space, your model has a blind spot!

### Lesson 5: Linear Independence and Dependence

**Linearly Independent:** No vector can be written as a combination of others. Each vector adds a NEW direction.

**Linearly Dependent:** At least one vector is redundant — it can be made from the others.

```
INDEPENDENT:                    DEPENDENT:
v1 = [1, 0]                    v1 = [1, 0]
v2 = [0, 1]                    v2 = [0, 1]
← Can't make v1 from v2        v3 = [2, 3]  = 2·v1 + 3·v2
                                ← v3 is redundant!
```

```python
import numpy as np

# Check linear independence by looking at rank
v1 = np.array([1, 0, 0])
v2 = np.array([0, 1, 0])
v3 = np.array([0, 0, 1])

A = np.column_stack([v1, v2, v3])
print(f"Rank: {np.linalg.matrix_rank(A)}")  # 3 → all 3 are independent

# Now add a dependent vector
v4 = 2*v1 + 3*v2  # = [2, 3, 0]
B = np.column_stack([v1, v2, v3, v4])
print(f"Rank: {np.linalg.matrix_rank(B)}")  # Still 3! v4 adds nothing new

# ML: If features are dependent, some are redundant
# This is why PCA works — it finds the independent directions!
```

---

## 04.02 — Subspaces, Column and Null Spaces (4 Lessons)

### Lesson 1: What Is a Subspace?

A **subspace** is a subset of a vector space that is itself a vector space. It must:

```
✓ Contain the zero vector (the origin)
✓ Be closed under addition (add two vectors in it → still in it)
✓ Be closed under scalar multiplication (scale a vector → still in it)
```

📊 **Subspaces of ℝ³:**
```
                     ℝ³ (all of 3D space)
                    ╱        │         ╲
            Planes through  Lines through  {0}
              origin          origin       (just the origin)
              (2D)            (1D)          (0D)
```

```python
import numpy as np

def is_subspace(vectors, test_points=1000):
    """
    Empirically check if a set of vectors spans a subspace.
    A valid subspace must: contain 0, be closed under + and ×.
    """
    dim = len(vectors[0])
    
    # Check 1: zero vector in the span? (Always yes for a span)
    print("✓ Zero vector: Yes (0 = 0·v₁ + 0·v₂ + ...)")
    
    # Check 2: closed under addition?
    for _ in range(test_points):
        c1 = np.random.randn(len(vectors))
        c2 = np.random.randn(len(vectors))
        v1 = sum(c * v for c, v in zip(c1, vectors))
        v2 = sum(c * v for c, v in zip(c2, vectors))
        v_sum = v1 + v2  # Should also be in the span
        # v_sum = (c1+c2) combination → yes, still in span
    print("✓ Closed under addition: Yes")
    
    # Check 3: closed under scalar multiplication?
    for _ in range(test_points):
        c = np.random.randn(len(vectors))
        alpha = np.random.randn()
        v = sum(ci * vi for ci, vi in zip(c, vectors))
        # alpha * v = alpha * (Σ ci·vi) = Σ (alpha·ci)·vi → still in span
    print("✓ Closed under scalar multiplication: Yes")
    
    return True

# Example: the xy-plane in 3D IS a subspace
v1 = np.array([1, 0, 0])
v2 = np.array([0, 1, 0])
print("Is span({[1,0,0], [0,1,0]}) a subspace?")
is_subspace([v1, v2])

# Counter-example: {(x, y) : x + y = 1} is NOT a subspace
# Because (0,0) is not in it! (0 + 0 ≠ 1)
print("\n{(x,y) : x+y=1} is NOT a subspace:")
print("✗ (0,0) not included → fails zero vector test")
```

### Lesson 2: Column Space (Range)

The **column space** of matrix A = all possible outputs of the transformation y = Ax.

```
      ┌     ┐                 Column space = span of columns
 A =  │ 1 2 │                            = span({[1,3], [2,4]})
      │ 3 4 │                            = a LINE (since col2 ≠ k·col1... 
      └     ┘                              wait, det = -2 ≠ 0, so it's all ℝ²!)
```

💡 **Key Intuition:** The column space answers: "What outputs can this transformation produce?"

```python
import numpy as np

# The column space of A
A = np.array([[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]])

# Rank tells us the dimension of the column space
print(f"Rank: {np.linalg.matrix_rank(A)}")  # 2

# This means the 3 columns only span a 2D plane in 3D space!
# The third column is redundant: col3 = 2·col2 - col1
print(f"2·col2 - col1 = {2*A[:,1] - A[:,0]}")  # [3, 6, 9] = col3 ✓
```

### Lesson 3: Null Space (Kernel)

The **null space** of A = all vectors x where Ax = 0 (inputs that get "killed").

```
null(A) = {x : Ax = 0}
```

💡 **Key Intuition:** The null space tells you about *information loss*. If Ax = 0 for some nonzero x, then A destroys information in that direction.

```python
from scipy.linalg import null_space

A = np.array([[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]])

ns = null_space(A)
print(f"Null space basis:\n{ns}")
print(f"Null space dimension: {ns.shape[1]}")  # 1

# Verify: A × (null vector) ≈ 0
print(f"A @ null_vector = {A @ ns[:, 0]}")  # ≈ [0, 0, 0]
```

### Lesson 4: The Fundamental Theorem of Linear Algebra

```
 ┌────────────────────────────────────────────────────────┐
 │         FUNDAMENTAL THEOREM (Strang's Version)         │
 │                                                        │
 │  For an m×n matrix A with rank r:                     │
 │                                                        │
 │  DOMAIN (ℝⁿ):                                        │
 │    Row Space ────── dim = r                            │
 │    Null Space ───── dim = n - r                        │
 │    (These are ORTHOGONAL complements in ℝⁿ)           │
 │                                                        │
 │  CODOMAIN (ℝᵐ):                                      │
 │    Column Space ─── dim = r                            │
 │    Left Null Space ─ dim = m - r                       │
 │    (These are ORTHOGONAL complements in ℝᵐ)           │
 │                                                        │
 │  The KEY equation: rank + nullity = n                  │
 └────────────────────────────────────────────────────────┘
```

```
📊 The Four Fundamental Subspaces:

         ℝⁿ (input)                    ℝᵐ (output)
    ┌───────────────┐              ┌───────────────┐
    │               │     A        │               │
    │  Row Space    │────────────▶│ Column Space  │
    │  (dim = r)    │             │  (dim = r)    │
    │───────────────│              │───────────────│
    │  Null Space   │────────────▶│ {0}           │
    │  (dim = n-r)  │  squished!  │               │
    └───────────────┘              └───────────────┘
```

---

## 04.03 — Bases as Coordinate Systems (7 Lessons)

### Lesson 1: What Is a Basis?

A **basis** for a vector space V is a set of vectors that:
1. **Spans** V (can reach every vector)
2. Is **linearly independent** (no redundancy)

💡 **Key Intuition:** A basis is a minimal set of building blocks. Every vector in the space can be uniquely expressed as a linear combination of basis vectors.

```
Standard basis for ℝ³:
  e₁ = [1, 0, 0]  → points right (x-axis)
  e₂ = [0, 1, 0]  → points up (y-axis)
  e₃ = [0, 0, 1]  → points forward (z-axis)
  
Any vector [a, b, c] = a·e₁ + b·e₂ + c·e₃
```

### Lesson 2: Non-Standard Bases

You can use ANY linearly independent set as a basis!

```python
import numpy as np

# Standard basis
e1 = np.array([1, 0])
e2 = np.array([0, 1])

# Non-standard basis (rotated 45°)
b1 = np.array([1, 1]) / np.sqrt(2)
b2 = np.array([-1, 1]) / np.sqrt(2)

# The vector [3, 4] in standard coordinates
v = np.array([3, 4])
print(f"Standard coords: {v}")

# What are its coordinates in the new basis?
B = np.column_stack([b1, b2])
coords_new = np.linalg.solve(B, v)
print(f"New basis coords: {coords_new}")

# Verify: coords_new[0]*b1 + coords_new[1]*b2 should give v
reconstructed = coords_new[0]*b1 + coords_new[1]*b2
print(f"Reconstructed: {reconstructed}")  # [3, 4] ✓
```

### Lesson 3: Change of Basis

⚡ **ML Connection — This is what PCA does!** PCA changes the basis from the original features to the principal components (eigenvectors of the covariance matrix).

```python
import numpy as np

# Simulating PCA as a change of basis
np.random.seed(42)
# Data with correlated features
X = np.random.randn(100, 2)
X[:, 1] = 0.8 * X[:, 0] + 0.2 * np.random.randn(100)

# Find PCA basis (eigenvectors of covariance)
cov = np.cov(X.T)
eigenvalues, eigenvectors = np.linalg.eigh(cov)

# Sort by decreasing eigenvalue
idx = np.argsort(eigenvalues)[::-1]
eigenvalues = eigenvalues[idx]
eigenvectors = eigenvectors[:, idx]

print("Original basis: standard x, y axes")
print(f"PCA basis (new axes):\n{eigenvectors}")
print(f"Variance along each PC: {eigenvalues}")

# Transform data to PCA coordinates (change of basis!)
X_pca = X @ eigenvectors
print(f"Original shape: {X.shape} → PCA shape: {X_pca.shape}")
```

### Lessons 4-7: Coordinates, Transitions, and Orthonormal Bases

**Orthonormal basis:** Basis vectors are both:
- **Orthogonal** (perpendicular to each other)
- **Normal** (each has length 1)

```
                     ↑ b₂
                     │
              ┌──────│──────┐
              │      │      │     Orthonormal: b₁ ⊥ b₂
              │      │      │                  |b₁| = |b₂| = 1
              └──────│──────┘
         ────────────┼──────────── → b₁
                     │
```

💡 **Why orthonormal is BEST:** Changing coordinates is just a dot product! No matrix inversion needed.

```python
# With orthonormal basis, coordinate transformation is just multiplication
Q = eigenvectors  # PCA eigenvectors are orthonormal

# Transform TO new basis: x_new = Qᵀ · x  (just transpose, no inverse!)
x_original = np.array([2.5, 1.8])
x_new = Q.T @ x_original
print(f"PCA coordinates: {x_new}")

# Transform BACK: x_original = Q · x_new
x_back = Q @ x_new
print(f"Back to original: {x_back}")  # [2.5, 1.8] ✓
```

---

## 04.04 — Dimension, Rank and Nullity (5 Lessons)

### Lesson 1: Dimension

The **dimension** of a vector space = number of vectors in any basis = minimum number of coordinates needed.

```
dim(ℝ²) = 2    ← need 2 numbers for a 2D point
dim(ℝ³) = 3    ← need 3 numbers for a 3D point
dim(ℝⁿ) = n    ← need n numbers for an nD point
dim({0}) = 0    ← the zero space has no basis vectors
```

### Lesson 2: Rank

The **rank** of a matrix = dimension of its column space = number of linearly independent columns (or rows).

```python
import numpy as np

# Full rank matrix (all columns independent)
A = np.array([[1, 0, 0],
              [0, 1, 0],
              [0, 0, 1]])
print(f"Rank of 3×3 identity: {np.linalg.matrix_rank(A)}")  # 3

# Rank-deficient matrix
B = np.array([[1, 2, 3],
              [2, 4, 6],    # = 2 × row 1
              [1, 2, 3]])   # = row 1
print(f"Rank of B: {np.linalg.matrix_rank(B)}")  # 1 (only 1 independent row!)
```

### Lesson 3: Nullity

**Nullity** = dimension of the null space = number of "free" variables.

💡 **Key Intuition:** Nullity tells you how many dimensions get "crushed to zero" by the transformation. High nullity = lots of information lost.

```python
import numpy as np
from scipy.linalg import null_space

# Example: projection matrix squishes 3D to 2D
P = np.array([[1, 0, 0],
              [0, 1, 0],
              [0, 0, 0]])  # Projects onto xy-plane (kills z)

rank = np.linalg.matrix_rank(P)
ns = null_space(P)
nullity = ns.shape[1]

print(f"Rank: {rank}")        # 2 (xy-plane is 2D)
print(f"Nullity: {nullity}")  # 1 (z-axis is destroyed)
print(f"Null space basis: {ns.T}")  # [0, 0, 1] → the z-direction

# Verify: P kills the null vector
print(f"P @ [0,0,1] = {P @ np.array([0, 0, 1])}")  # [0, 0, 0] ✓

# ML Example: A neural network layer that doesn't use all features
W = np.array([[1, 2, 0],    # 2 outputs from 3 inputs
              [3, 4, 0]])   # Third feature is NEVER used
print(f"\nWeight matrix rank: {np.linalg.matrix_rank(W)}")  # 2
ns_W = null_space(W)
print(f"Null space: {np.round(ns_W.T, 4)}")  # Direction [0, 0, 1] — feature 3 ignored!
```

### Lesson 4: The Rank-Nullity Theorem ⭐

```
rank(A) + nullity(A) = n  (number of columns)
```

💡 **Plain English:** The number of independent directions + the number of "killed" directions = total directions.

```python
import numpy as np
from scipy.linalg import null_space

# 3×4 matrix (3 rows, 4 columns)
A = np.array([[1, 2, 0, 1],
              [0, 1, 1, 0],
              [1, 3, 1, 1]])

rank = np.linalg.matrix_rank(A)
ns = null_space(A)
nullity = ns.shape[1]
n_cols = A.shape[1]

print(f"Rank: {rank}")         # 2
print(f"Nullity: {nullity}")   # 2
print(f"Rank + Nullity = {rank + nullity} = {n_cols} columns ✓")
```

### Lesson 5: Rank in ML — Why It Matters

⚡ **ML Connections:**

```python
import numpy as np

# 1. LOW-RANK APPROXIMATION → Compression
# If a 1000×1000 matrix has rank 10, we only need to store 
# 10 × 1000 + 10 × 1000 = 20,000 numbers instead of 1,000,000!

# 2. Feature matrix rank → number of truly independent features
np.random.seed(42)
n_samples = 100
X = np.random.randn(n_samples, 5)
X[:, 4] = X[:, 0] + X[:, 1]  # Feature 5 = Feature 1 + Feature 2

print(f"Shape: {X.shape}")
print(f"Rank: {np.linalg.matrix_rank(X)}")  # 4, not 5!
# → Only 4 truly independent features

# 3. Embedding matrix rank in transformers
# LoRA (Low-Rank Adaptation) exploits this:
d_model = 768
d_lora = 8  # low rank

# Instead of fine-tuning full 768×768 weight matrix (590K params)
# LoRA uses two small matrices: 768×8 and 8×768 (12K params!)
A_lora = np.random.randn(d_model, d_lora) * 0.01
B_lora = np.random.randn(d_lora, d_model) * 0.01
delta_W = A_lora @ B_lora  # rank-8 update!

print(f"Full matrix params: {d_model * d_model:,}")    # 589,824
print(f"LoRA params: {d_model * d_lora * 2:,}")        # 12,288
print(f"Compression ratio: {d_model * d_model / (d_model * d_lora * 2):.0f}x")  # 48x!
```

---

## 🔥 FAANG Deep Dive — Spaces

### Interview Problem 1: Google — "Rank of a Matrix"

```python
def matrix_rank_manual(A, tol=1e-10):
    """
    Compute rank using row reduction (no numpy.linalg).
    Count non-zero rows after reduction.
    """
    M = [row[:] for row in A]  # copy
    m, n = len(M), len(M[0])
    rank = 0
    
    for col in range(n):
        # Find pivot
        pivot_row = None
        for row in range(rank, m):
            if abs(M[row][col]) > tol:
                pivot_row = row
                break
        
        if pivot_row is None:
            continue
        
        # Swap with current rank row
        M[rank], M[pivot_row] = M[pivot_row], M[rank]
        
        # Eliminate below
        for row in range(rank + 1, m):
            factor = M[row][col] / M[rank][col]
            for j in range(col, n):
                M[row][j] -= factor * M[rank][j]
        
        rank += 1
    
    return rank

A = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
print(f"Rank: {matrix_rank_manual(A)}")  # 2
```

### Interview Problem 2: Meta — "Check Linear Independence"

```python
def are_independent(vectors):
    """Check if a set of vectors is linearly independent."""
    import numpy as np
    A = np.column_stack(vectors)
    return np.linalg.matrix_rank(A) == len(vectors)

v1 = [1, 0, 0]
v2 = [0, 1, 0]
v3 = [1, 1, 0]  # = v1 + v2 → DEPENDENT

print(are_independent([v1, v2]))      # True
print(are_independent([v1, v2, v3]))  # False
```

### Interview Problem 3: Amazon — "Word Embedding Analogy"

```python
import numpy as np

def find_analogy(word_vectors, a, b, c, top_k=3):
    """
    a is to b as c is to ?
    Find d such that: d ≈ b - a + c
    This is vector arithmetic in the embedding SPACE.
    """
    target = word_vectors[b] - word_vectors[a] + word_vectors[c]
    
    best = []
    for word, vec in word_vectors.items():
        if word in [a, b, c]:
            continue
        similarity = np.dot(target, vec) / (np.linalg.norm(target) * np.linalg.norm(vec))
        best.append((similarity, word))
    
    best.sort(reverse=True)
    return best[:top_k]

# Simplified word vectors (real ones are 300-dim)
word_vectors = {
    "king":   np.array([0.9, 0.8, 0.1, 0.2]),
    "queen":  np.array([0.9, 0.8, 0.9, 0.2]),
    "man":    np.array([0.1, 0.8, 0.1, 0.2]),
    "woman":  np.array([0.1, 0.8, 0.9, 0.2]),
    "prince": np.array([0.7, 0.6, 0.1, 0.2]),
    "princess": np.array([0.7, 0.6, 0.9, 0.2]),
}

results = find_analogy(word_vectors, "king", "queen", "man")
print("king:queen :: man:?")
for sim, word in results:
    print(f"  {word}: similarity = {sim:.3f}")
```

---

## ✅ Module 04 Checkpoint

- [ ] Define and compute linear combinations and spans
- [ ] Test for linear independence (check rank)
- [ ] Identify the four fundamental subspaces of a matrix
- [ ] State and apply the Rank-Nullity Theorem
- [ ] Perform change of basis (especially for PCA)
- [ ] Explain why LoRA works (low-rank approximation)
- [ ] Solve FAANG problems involving vectors and spaces

**Next →** [Module 05: Spectral](../module-05-spectral/README.md)
