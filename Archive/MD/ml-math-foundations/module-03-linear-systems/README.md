# Module 03 — Linear Systems

## The Engine That Powers Every ML Model

> **Why Linear Systems Matter:** Neural networks are stacked linear transformations + nonlinearities. Solving Ax = b is the most fundamental operation in all of machine learning. If you understand linear systems, you understand the skeleton of deep learning.

```
 MODULE 03 ROADMAP
 ═══════════════════════════════════════════════════
 03.01 Lines, Planes & Geometric Constraints
 03.02 Determinants & Singularity
 03.03 Solving Linear Systems by Row Reduction
 03.04 Matrix Invertibility
 03.05 Affine Transformations
 ═══════════════════════════════════════════════════
```

---

## 03.01 — Lines, Planes and Geometric Constraints (9 Lessons)

### Lesson 1: A Linear Equation is a Flat Surface

💡 **Key Intuition:** A linear equation in n variables defines a *flat* (n−1)-dimensional surface in n-dimensional space.

| Variables | Equation Example | What It Looks Like |
|:---------:|:----------------|:-------------------|
| 1 | 2x = 6 | A **point** on a line |
| 2 | 2x + 3y = 6 | A **line** in 2D |
| 3 | 2x + 3y + z = 6 | A **plane** in 3D |
| n | a₁x₁ + a₂x₂ + ... = b | A **hyperplane** in nD |

📊 **Visualizing a Line (2D):**
```
  y
  4│         2x + 3y = 6
  3│        /
  2│       /  ← Every point on this line
  1│      /     satisfies the equation
  0├─────/────────── x
   0  1  2  3  4
```

```python
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Plot a linear equation: 2x + 3y = 6  →  y = (6 - 2x) / 3
x = np.linspace(-1, 5, 100)
y = (6 - 2*x) / 3

plt.figure(figsize=(8, 5))
plt.plot(x, y, 'b-', linewidth=2, label='2x + 3y = 6')
plt.axhline(y=0, color='k', linewidth=0.5)
plt.axvline(x=0, color='k', linewidth=0.5)
plt.grid(True, alpha=0.3)
plt.xlabel('x')
plt.ylabel('y')
plt.title('A Linear Equation = A Line in 2D')
plt.legend()
plt.savefig('line_2d.png', dpi=100)
print("✓ Plot saved")
```

### Lesson 2: Systems of Equations = Intersections

**A system of linear equations:**
```
  2x +  y = 5     ← Line 1
   x + 3y = 7     ← Line 2
```

📊 **The solution is where the lines INTERSECT:**
```
  y
  5│  Line 1
  4│    \
  3│     \    / Line 2
  2│      \ /
  1│   ★ (x=1.6, y=1.8)  ← THE SOLUTION
  0├──────────────── x
```

💡 **Three Possibilities:**
```
 ONE solution        NO solution         INFINITE solutions
 (lines cross)       (parallel lines)    (same line)
                     
    \  /                  |  |              ═══════
     \/                   |  |              ═══════
     /\                   |  |
    /  \                  
```

### Lesson 3: Matrix Form — Ax = b

**The compact way to write linear systems:**

```
System:                    Matrix form:
  2x +  y = 5             ┌      ┐ ┌   ┐   ┌   ┐
   x + 3y = 7             │ 2  1 │ │ x │ = │ 5 │
                           │ 1  3 │ │ y │   │ 7 │
                           └      ┘ └   ┘   └   ┘
                              A    ·  x   =   b
```

```python
import numpy as np

# The system: 2x + y = 5, x + 3y = 7
A = np.array([[2, 1],
              [1, 3]])
b = np.array([5, 7])

# Solve Ax = b
x = np.linalg.solve(A, b)
print(f"Solution: x = {x[0]:.2f}, y = {x[1]:.2f}")
# Solution: x = 1.60, y = 1.80

# Verify: Ax should equal b
print(f"Verification: A @ x = {A @ x}")  # [5. 7.] ✓
```

### Lesson 4: Geometric Interpretation in Higher Dimensions

⚡ **ML Connection:** In ML, we often solve systems with millions of variables:

```
Neural network with 1M parameters:
  - Forward pass:  y = Wx + b  (matrix multiplication)
  - Training:      Find W such that Wx ≈ y for all training data
  - This is a MASSIVE linear system!
```

### Lessons 5-9: Parametric Solutions and Constraints

When a system has infinite solutions, we express them parametrically:

```python
# System with infinite solutions:
# x + y + z = 3
# x + y - z = 1
# Subtracting: 2z = 2 → z = 1
# Then x + y = 2 → y = 2 - x (x is free)

# Parametric solution: x = t, y = 2-t, z = 1
import numpy as np

# Generate points on the solution line
t = np.linspace(-2, 4, 100)
x = t
y = 2 - t
z = np.ones_like(t)

# Verify all points satisfy both equations
for i in range(0, 100, 25):
    eq1 = x[i] + y[i] + z[i]
    eq2 = x[i] + y[i] - z[i]
    print(f"t={t[i]:.1f}: ({x[i]:.1f}, {y[i]:.1f}, {z[i]:.1f}) → eq1={eq1:.1f}, eq2={eq2:.1f}")
```

---

## 03.02 — Determinants and Singularity (6 Lessons)

### Lesson 1: What Is a Determinant?

💡 **Key Intuition:** The determinant tells you how much a matrix *stretches or squishes* space. It's a single number that reveals everything about whether a system has a unique solution.

```
det(A) > 0  →  Space is stretched (orientation preserved)
det(A) < 0  →  Space is stretched AND flipped
det(A) = 0  →  Space is SQUISHED to a lower dimension (SINGULAR!)
```

### Lesson 2: Computing 2×2 Determinant

```
       ┌       ┐
  A =  │ a  b  │      det(A) = ad - bc
       │ c  d  │
       └       ┘
```

📊 **Visual — The Determinant is the AREA:**
```
Before transformation:        After transformation:
  Unit square                 Parallelogram
  ┌────┐                      ╱    ╱
  │    │  Area = 1            ╱    ╱   Area = |det(A)|
  └────┘                     ╱____╱
```

```python
import numpy as np

# 2×2 determinant
A = np.array([[3, 1],
              [2, 4]])

det_A = np.linalg.det(A)
print(f"det(A) = {det_A:.1f}")  # 10.0

# Manual calculation: ad - bc = 3*4 - 1*2 = 10 ✓

# The determinant is the area scaling factor
# Unit square has area 1, after transformation area = |det(A)| = 10
```

### Lesson 3: Computing 3×3 Determinant (Cofactor Expansion)

```
       ┌           ┐
  A =  │ a  b  c   │
       │ d  e  f   │       det(A) = a(ei - fh) - b(di - fg) + c(dh - eg)
       │ g  h  i   │
       └           ┘
```

```python
A = np.array([[1, 2, 3],
              [4, 5, 6],
              [7, 8, 9]])

det_A = np.linalg.det(A)
print(f"det(A) = {det_A:.6f}")  # ≈ 0 (this matrix is SINGULAR!)

# Manual: 1(45-48) - 2(36-42) + 3(32-35)
# = 1(-3) - 2(-6) + 3(-3) = -3 + 12 - 9 = 0 ✓
```

### Lesson 4: Properties of Determinants

| Property | Formula | Plain English |
|---------|---------|---------------|
| Product rule | det(AB) = det(A)·det(B) | Chained transformations multiply areas |
| Transpose | det(Aᵀ) = det(A) | Flipping across diagonal doesn't change area |
| Inverse | det(A⁻¹) = 1/det(A) | Undoing a stretch = reciprocal stretch |
| Scalar | det(cA) = cⁿ·det(A) | Scaling each dimension by c |
| Row swap | Changes sign | Flips orientation |

### Lesson 5: Singularity — When det(A) = 0

💡 **Key Intuition:** A **singular** matrix squishes space into a lower dimension. It's like projecting 3D onto 2D — you lose information and can't go back.

```
INVERTIBLE (det ≠ 0):          SINGULAR (det = 0):
  ┌────┐    →    ╱╱            ┌────┐    →    ────
  │    │         ╱╱            │    │         ────
  └────┘        ╱╱             └────┘         
  2D → 2D (reversible)         2D → 1D (information lost!)
```

⚡ **ML Connection:**
- Singular covariance matrix → features are linearly dependent (redundant)
- Near-singular weight matrices → training instability (vanishing/exploding gradients)
- Regularization adds to diagonal → prevents singularity

```python
# Singular matrix: columns are linearly dependent
A_singular = np.array([[1, 2],
                        [2, 4]])  # col2 = 2 × col1

print(f"det = {np.linalg.det(A_singular):.4f}")  # 0.0000

# Can't solve Ax = b for singular A
try:
    x = np.linalg.solve(A_singular, np.array([3, 6]))
    print(f"Solution: {x}")
except np.linalg.LinAlgError as e:
    print(f"Error: {e}")  # Singular matrix

# Fix: add regularization (ridge regression does this!)
lambda_reg = 0.01
A_regularized = A_singular + lambda_reg * np.eye(2)
print(f"det(regularized) = {np.linalg.det(A_regularized):.4f}")  # Non-zero!
x = np.linalg.solve(A_regularized, np.array([3, 6]))
print(f"Regularized solution: {x}")
```

### Lesson 6: Cramer's Rule

For small systems, you can solve using determinants:

```
For Ax = b with 2 unknowns:
  x₁ = det(A₁)/det(A)    where A₁ = replace col 1 of A with b
  x₂ = det(A₂)/det(A)    where A₂ = replace col 2 of A with b
```

```python
# Cramer's Rule example
A = np.array([[2, 1],
              [1, 3]])
b = np.array([5, 7])

det_A = np.linalg.det(A)

A1 = A.copy()
A1[:, 0] = b  # Replace first column with b
x1 = np.linalg.det(A1) / det_A

A2 = A.copy()
A2[:, 1] = b  # Replace second column with b
x2 = np.linalg.det(A2) / det_A

print(f"Cramer's Rule: x = {x1:.2f}, y = {x2:.2f}")  # x = 1.60, y = 1.80
```

---

## 03.03 — Solving Linear Systems by Row Reduction (12 Lessons)

### Lesson 1: The Augmented Matrix

Combine A and b into one matrix:
```
System:              Augmented matrix:
  2x +  y = 5       ┌          ┐
   x + 3y = 7       │ 2  1 │ 5│
                     │ 1  3 │ 7│
                     └          ┘
```

### Lesson 2: Elementary Row Operations

Three legal moves that don't change the solution:

```
1. SWAP:    Swap two rows                    R₁ ↔ R₂
2. SCALE:   Multiply a row by non-zero c     R₁ → c·R₁
3. ADD:     Add a multiple of one row to     R₂ → R₂ + c·R₁
            another
```

### Lesson 3-6: Gaussian Elimination (Step by Step)

💡 **Goal:** Transform the matrix into **Row Echelon Form** (staircase shape).

```python
import numpy as np

def gaussian_elimination(A, b, verbose=True):
    """
    Solve Ax = b using Gaussian Elimination with back-substitution.
    Shows every step for learning.
    """
    n = len(b)
    # Create augmented matrix
    M = np.hstack([A.astype(float), b.reshape(-1, 1).astype(float)])
    
    if verbose:
        print("Initial augmented matrix:")
        print(M)
        print()
    
    # Forward elimination
    for col in range(n):
        # Find pivot (largest element for numerical stability)
        max_row = col + np.argmax(np.abs(M[col:, col]))
        M[[col, max_row]] = M[[max_row, col]]
        
        if verbose:
            print(f"Step {col+1}: Pivot on column {col+1}")
        
        # Eliminate below
        for row in range(col + 1, n):
            factor = M[row, col] / M[col, col]
            M[row] -= factor * M[col]
            if verbose:
                print(f"  R{row+1} → R{row+1} - ({factor:.2f})·R{col+1}")
        
        if verbose:
            print(M)
            print()
    
    # Back substitution
    x = np.zeros(n)
    for i in range(n - 1, -1, -1):
        x[i] = (M[i, -1] - np.sum(M[i, i+1:n] * x[i+1:n])) / M[i, i]
    
    return x

# Example: solve the system
A = np.array([[2, 1, -1],
              [-3, -1, 2],
              [-2, 1, 2]])
b = np.array([8, -11, -3])

x = gaussian_elimination(A, b)
print(f"\nSolution: x = {x}")
print(f"Verify: A @ x = {A @ x}")  # Should equal b
```

### Lesson 7: Row Echelon Form (REF) vs Reduced Row Echelon Form (RREF)

```
REF (staircase):              RREF (identity-like):
┌              ┐              ┌              ┐
│ ■  *  *  │ * │              │ 1  0  0  │ * │
│ 0  ■  *  │ * │     →       │ 0  1  0  │ * │
│ 0  0  ■  │ * │              │ 0  0  1  │ * │
└              ┘              └              ┘
■ = pivot (leading 1)         Solution is read directly!
* = any number                x₁ = *, x₂ = *, x₃ = *
```

```python
from sympy import Matrix, pprint

# RREF using SymPy (exact arithmetic)
M = Matrix([
    [2,  1, -1,  8],
    [-3, -1, 2, -11],
    [-2,  1, 2, -3]
])

rref_matrix, pivot_columns = M.rref()
print("RREF:")
pprint(rref_matrix)
# [1, 0, 0 | 2]
# [0, 1, 0 | 3]
# [0, 0, 1 | -1]
# Solution: x=2, y=3, z=-1
```

### Lessons 8-12: Special Cases and Complexity

**Three outcomes of row reduction:**

```
Case 1: UNIQUE solution          Case 2: NO solution          Case 3: INFINITE solutions
┌            ┐                   ┌            ┐               ┌            ┐
│ 1  0  0 │2│                   │ 1  0  2 │3 │               │ 1  0  2 │3 │
│ 0  1  0 │3│                   │ 0  1  1 │4 │               │ 0  1  1 │4 │
│ 0  0  1 │1│                   │ 0  0  0 │5 │  ← 0=5 !!    │ 0  0  0 │0 │  ← free var
└            ┘                   └            ┘               └            ┘
```

⚡ **ML Connection — Computational Cost:**

| Method | Time Complexity | When to Use |
|--------|:-:|---|
| Gaussian Elimination | O(n³) | Small-medium dense systems |
| LU Decomposition | O(n³) once, O(n²) per solve | Multiple systems same A |
| Iterative (CG, GMRES) | O(n·k) per iteration | Huge sparse systems |
| GPU Batched | O(n³/p) parallel | Deep learning (thousands of small systems) |

---

## 03.04 — Matrix Invertibility (5 Lessons)

### Lesson 1: What Is an Inverse?

💡 **Key Intuition:** If matrix A transforms space, then A⁻¹ *undoes* that transformation. It's the "undo button."

```
A · A⁻¹ = I = A⁻¹ · A

Where I = identity matrix:
┌         ┐
│ 1  0  0 │   ← does nothing (like multiplying by 1)
│ 0  1  0 │
│ 0  0  1 │
└         ┘
```

### Lesson 2: When Does the Inverse Exist?

**A⁻¹ exists ⟺ det(A) ≠ 0 ⟺ A is non-singular ⟺ Ax = b has exactly one solution for every b**

```python
import numpy as np

A = np.array([[4, 7],
              [2, 6]])

# Check if invertible
det_A = np.linalg.det(A)
print(f"det(A) = {det_A:.1f}")  # 10.0 → invertible!

# Compute inverse
A_inv = np.linalg.inv(A)
print(f"A⁻¹ = \n{A_inv}")

# Verify: A × A⁻¹ = I
print(f"A @ A⁻¹ = \n{np.round(A @ A_inv, 10)}")  # Identity matrix

# 2×2 formula: A⁻¹ = (1/det) × [[d, -b], [-c, a]]
det = 4*6 - 7*2  # = 10
A_inv_manual = (1/det) * np.array([[6, -7], [-2, 4]])
print(f"Manual A⁻¹ = \n{A_inv_manual}")  # Same!
```

### Lesson 3: The Invertible Matrix Theorem

All of these are equivalent — if ANY one is true, ALL are true:

```
 ┌──────────────────────────────────────────────────────────┐
 │           THE INVERTIBLE MATRIX THEOREM                  │
 │                                                          │
 │  For an n×n matrix A, these are ALL EQUIVALENT:         │
 │                                                          │
 │  1. A is invertible (A⁻¹ exists)                       │
 │  2. det(A) ≠ 0                                          │
 │  3. Ax = b has exactly one solution for every b         │
 │  4. Ax = 0 has only the trivial solution x = 0         │
 │  5. The columns of A are linearly independent           │
 │  6. The rows of A are linearly independent              │
 │  7. rank(A) = n                                         │
 │  8. The column space of A is all of ℝⁿ                 │
 │  9. All eigenvalues of A are nonzero                    │
 │  10. A can be written as a product of elementary        │
 │      matrices                                            │
 └──────────────────────────────────────────────────────────┘
```

### Lessons 4-5: Numerical Stability and Condition Numbers

⚡ **ML Connection:** In practice, we almost never compute A⁻¹ directly. It's numerically unstable and slow. Instead:

```python
# ❌ BAD: Computing inverse explicitly
A = np.random.randn(1000, 1000)
b = np.random.randn(1000)

# Slow and numerically unstable
x_bad = np.linalg.inv(A) @ b

# ✅ GOOD: Use solve (uses LU decomposition internally)
x_good = np.linalg.solve(A, b)

# Even better for least squares: use lstsq
x_lstsq, residuals, rank, sv = np.linalg.lstsq(A, b, rcond=None)

# Check condition number (measure of near-singularity)
cond = np.linalg.cond(A)
print(f"Condition number: {cond:.1f}")
# Large condition → matrix is nearly singular → numerically dangerous
```

---

## 03.05 — Affine Transformations (3 Lessons)

### Lesson 1: Linear vs Affine

```
Linear:  f(x) = Ax          (must pass through origin)
Affine:  f(x) = Ax + b      (can be shifted — the +b part)
```

📊 **The Difference:**
```
LINEAR (through origin):        AFFINE (shifted):
        /                              /
       /                              /
──────0──────                  ──────/──────
     /                              /
    /                              0
```

⚡ **ML Connection:** Every neural network layer is an affine transformation followed by a nonlinearity!

```
Layer output = σ(Wx + b)
                └─────┘
                affine part
              └───────────┘
              nonlinear activation
```

### Lesson 2: Homogeneous Coordinates (The Trick)

We can turn any affine transformation into a linear one by adding an extra dimension:

```
Affine in 2D:                  Linear in 3D (homogeneous):
┌   ┐   ┌      ┐┌   ┐ ┌   ┐    ┌   ┐   ┌         ┐┌   ┐
│ y₁│ = │ a  b ││ x₁│+│ t₁│    │ y₁│   │ a  b  t₁││ x₁│
│ y₂│   │ c  d ││ x₂│ │ t₂│    │ y₂│ = │ c  d  t₂││ x₂│
└   ┘   └      ┘└   ┘ └   ┘    │  1│   │ 0  0   1││  1│
                                └   ┘   └         ┘└   ┘
```

```python
import numpy as np

def affine_transform(x, A, b):
    """Apply affine transformation: y = Ax + b"""
    return A @ x + b

def affine_as_linear(x, A, b):
    """Same transformation using homogeneous coordinates."""
    n = len(b)
    # Build (n+1) × (n+1) matrix
    M = np.zeros((n+1, n+1))
    M[:n, :n] = A
    M[:n, n] = b
    M[n, n] = 1
    
    # Extend x with a 1
    x_homo = np.append(x, 1)
    result = M @ x_homo
    return result[:n]  # Drop the extra 1

# Test
A = np.array([[2, 0], [0, 3]])
b = np.array([1, -1])
x = np.array([1, 2])

print(f"Affine:     {affine_transform(x, A, b)}")    # [3, 5]
print(f"Homogeneous:{affine_as_linear(x, A, b)}")    # [3, 5] — same!
```

### Lesson 3: Common Affine Transformations in ML

```python
import numpy as np

# 1. BATCH NORMALIZATION is an affine transformation!
# y = γ * (x - μ) / σ + β = (γ/σ)x + (β - γμ/σ)
gamma, beta, mu, sigma = 1.5, 0.5, 2.0, 0.8
x = np.array([1.0, 2.0, 3.0, 2.5])

# Explicit batch norm
y = gamma * (x - mu) / sigma + beta
print(f"BatchNorm output: {y}")

# As affine: y = ax + b where a = γ/σ, b = β - γμ/σ
a = gamma / sigma
b_val = beta - gamma * mu / sigma
print(f"As affine (a={a:.2f}, b={b_val:.2f}): {a * x + b_val}")  # Same!

# 2. DATA STANDARDIZATION is an affine transformation
# z = (x - mean) / std = (1/std)x + (-mean/std)
data = np.array([10, 20, 30, 40, 50])
mean, std = data.mean(), data.std()
z_scores = (data - mean) / std
print(f"Standardized: {z_scores}")
```

---

## 🔥 FAANG Deep Dive — Linear Systems

### Interview Problem 1: Google — "Matrix Multiplication"

```python
def matrix_multiply(A, B):
    """
    Multiply two matrices without numpy.
    O(n³) — the fundamental operation in deep learning.
    """
    m, n = len(A), len(A[0])
    n2, p = len(B), len(B[0])
    assert n == n2, "Incompatible dimensions"
    
    C = [[0] * p for _ in range(m)]
    for i in range(m):
        for j in range(p):
            for k in range(n):
                C[i][j] += A[i][k] * B[k][j]
    return C

A = [[1, 2], [3, 4]]
B = [[5, 6], [7, 8]]
print(matrix_multiply(A, B))  # [[19, 22], [43, 50]]
```

### Interview Problem 2: Amazon — "Rotate Image (Matrix)"

```python
def rotate_90(matrix):
    """
    Rotate NxN matrix 90° clockwise.
    This is an affine transformation!
    Trick: Transpose + Reverse each row.
    """
    n = len(matrix)
    # Transpose
    for i in range(n):
        for j in range(i, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    # Reverse each row
    for row in matrix:
        row.reverse()
    return matrix

grid = [[1,2,3], [4,5,6], [7,8,9]]
print(rotate_90(grid))
# [[7,4,1], [8,5,2], [9,6,3]]
```

### Interview Problem 3: Meta — "Spiral Matrix"

```python
def spiral_order(matrix):
    """Return elements in spiral order — tests matrix traversal skills."""
    result = []
    while matrix:
        result += matrix.pop(0)           # Top row →
        if matrix and matrix[0]:
            for row in matrix:
                result.append(row.pop())  # Right column ↓
        if matrix:
            result += matrix.pop()[::-1]  # Bottom row ←
        if matrix and matrix[0]:
            for row in reversed(matrix):
                result.append(row.pop(0)) # Left column ↑
    return result

mat = [[1,2,3],[4,5,6],[7,8,9]]
print(spiral_order(mat))  # [1,2,3,6,9,8,7,4,5]
```

---

## ✅ Module 03 Checkpoint

- [ ] Represent linear systems as Ax = b
- [ ] Compute 2×2 and 3×3 determinants by hand
- [ ] Perform Gaussian elimination and back-substitution
- [ ] Determine if a system has 0, 1, or ∞ solutions
- [ ] State the Invertible Matrix Theorem
- [ ] Explain why we use `np.linalg.solve` instead of computing A⁻¹
- [ ] Recognize neural network layers as affine transformations

**Next →** [Module 04: Spaces](../module-04-spaces/README.md)
