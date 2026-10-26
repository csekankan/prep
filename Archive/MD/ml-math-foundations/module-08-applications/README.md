# Module 08 — Applications

## Where Math Meets the Machine

> **Why This Module Matters:** This is where everything comes together. Residual minimization, linear regression, and PCA are the three pillars that connect all the linear algebra you've learned to actual ML algorithms. These aren't just theory — they're production code at every FAANG company.

```
 MODULE 08 ROADMAP
 ═══════════════════════════════════════
 08.01 Residual Minimization
 08.02 Linear Regression
 08.03 Principal Component Analysis
 ═══════════════════════════════════════
```

---

## 08.01 — Residual Minimization (2 Lessons)

### Lesson 1: The Residual — Measuring How Wrong You Are

💡 **Key Intuition:** A **residual** is the difference between what you predicted and what actually happened. Making residuals small is literally the goal of all supervised learning.

```
Residual = Actual Value − Predicted Value
    rᵢ = yᵢ − ŷᵢ

      y (actual)
      │
      │  • (actual)
      │  │
  rᵢ │  │ ← residual (the error)
      │  │
      │  ★ (predicted = ŷ)
      │──────────── x
```

```python
import numpy as np

# Simple prediction
y_actual = np.array([3, 5, 7, 9, 11])
y_predicted = np.array([2.8, 5.1, 6.5, 9.3, 10.8])

residuals = y_actual - y_predicted
print(f"Residuals: {residuals}")
print(f"Mean residual: {residuals.mean():.3f}")
print(f"Sum of squared residuals: {np.sum(residuals**2):.3f}")
```

### Lesson 2: Why Minimize SQUARED Residuals?

We minimize Σrᵢ² (sum of squared residuals) instead of Σ|rᵢ| because:

| Property | Sum of Squares (L2) | Sum of Absolutes (L1) |
|---------|:---:|:---:|
| Differentiable everywhere? | ✅ Yes | ❌ No (kink at 0) |
| Penalizes large errors more? | ✅ Yes (quadratic) | ❌ Linear |
| Has closed-form solution? | ✅ Yes | ❌ No |
| Sensitive to outliers? | ❌ Very | ✅ Less |

```python
import numpy as np

residuals = np.array([-0.2, 0.1, -0.5, 0.3, -0.2])

# L2 loss (Mean Squared Error)
mse = np.mean(residuals**2)
print(f"MSE: {mse:.4f}")

# L1 loss (Mean Absolute Error)  
mae = np.mean(np.abs(residuals))
print(f"MAE: {mae:.4f}")

# Huber loss (best of both worlds — used in practice!)
def huber_loss(r, delta=1.0):
    return np.where(np.abs(r) <= delta,
                    0.5 * r**2,
                    delta * (np.abs(r) - 0.5 * delta))

huber = np.mean(huber_loss(residuals))
print(f"Huber: {huber:.4f}")
```

**The Geometry:**
```
     Loss                Loss               Loss
      │ ╱╲               │  │               │╲   ╱
      │╱  ╲              │  │               │ ╲╱
      ╱    ╲             │  │               │  ╱╲ 
     ╱      ╲            │╱ │╲              │╱    ╲
────┼────────── r    ────┼──────── r    ────┼──────── r
     L2 (squared)         L1 (absolute)      Huber (hybrid)
  Smooth, penalizes      Robust but          Smooth AND robust
  outliers heavily       not smooth
```

---

## 08.02 — Linear Regression (3 Lessons)

### Lesson 1: The Normal Equation — Derivation from Scratch

⚡ **ML Connection:** Every linear model (linear regression, logistic regression, SVMs with linear kernel) boils down to this equation. Understanding it means understanding the mathematical core of classical ML.

💡 **The Problem:** Find weights w that minimize ||Xw − y||²

```
Given:
  X = design matrix (m samples × n features)
  y = target values (m × 1)
  w = weights to learn (n × 1)

The loss:
  L(w) = ||Xw − y||² = (Xw − y)ᵀ(Xw − y)

Expand:
  L(w) = wᵀXᵀXw − 2wᵀXᵀy + yᵀy

Take gradient and set to 0:
  ∇L = 2XᵀXw − 2Xᵀy = 0
  XᵀXw = Xᵀy               ← THE NORMAL EQUATION
  w = (XᵀX)⁻¹Xᵀy           ← THE SOLUTION
```

📊 **Geometric View:** We're projecting y onto the column space of X!
```
        y (actual values)
       ╱│
      ╱ │
     ╱  │ ← residual (perpendicular to column space!)
    ╱   │
───★────┼────── Column Space of X
   ŷ = Xw   (the projection)
```

```python
import numpy as np

# Generate synthetic data
np.random.seed(42)
n_samples, n_features = 100, 3

X = np.random.randn(n_samples, n_features)
true_w = np.array([2, -1, 0.5])
y = X @ true_w + 0.1 * np.random.randn(n_samples)  # Add noise

# Method 1: Normal equation (closed form)
w_normal = np.linalg.solve(X.T @ X, X.T @ y)
print(f"Normal equation: w = {np.round(w_normal, 4)}")
print(f"True weights:    w = {true_w}")

# Method 2: numpy lstsq (numerically stable)
w_lstsq, residuals, rank, sv = np.linalg.lstsq(X, y, rcond=None)
print(f"lstsq:           w = {np.round(w_lstsq, 4)}")

# Method 3: SVD-based (most stable for ill-conditioned problems)
U, sigma, Vt = np.linalg.svd(X, full_matrices=False)
w_svd = Vt.T @ np.diag(1/sigma) @ U.T @ y
print(f"SVD-based:       w = {np.round(w_svd, 4)}")

# Verify residuals are perpendicular to column space
residual = y - X @ w_normal
print(f"\nXᵀ·residual ≈ 0? {np.allclose(X.T @ residual, 0, atol=1e-10)}")
```

### Lesson 2: Regularized Regression

⚡ **ML Connection:** Regularization is used in nearly every production ML model. L2 (Ridge) shrinks weights uniformly; L1 (Lasso) drives unimportant weights to exactly zero for automatic feature selection.

When XᵀX is near-singular (features are correlated), we add regularization:

```
Ridge (L2):   w = (XᵀX + λI)⁻¹Xᵀy     ← adds λ to diagonal
Lasso (L1):   min ||Xw − y||² + λ||w||₁  ← no closed form
Elastic Net:  min ||Xw − y||² + λ₁||w||₁ + λ₂||w||₂²
```

💡 **Why Ridge Works:** Adding λI to XᵀX guarantees all eigenvalues are ≥ λ > 0, making the matrix invertible!

```python
import numpy as np

# Ridge regression
def ridge_regression(X, y, lambda_reg=1.0):
    n = X.shape[1]
    I = np.eye(n)
    w = np.linalg.solve(X.T @ X + lambda_reg * I, X.T @ y)
    return w

# Create ill-conditioned problem (correlated features)
np.random.seed(42)
X = np.random.randn(50, 5)
X[:, 4] = X[:, 0] + X[:, 1] + 0.01 * np.random.randn(50)  # Feature 5 ≈ F1 + F2
y = X @ np.array([1, 2, 3, 4, 5]) + np.random.randn(50)

print(f"Condition number of XᵀX: {np.linalg.cond(X.T @ X):.0f}")

for lam in [0, 0.01, 0.1, 1.0, 10.0]:
    w = ridge_regression(X, y, lam)
    y_pred = X @ w
    mse = np.mean((y - y_pred)**2)
    print(f"λ={lam:>5.2f}: w_norm={np.linalg.norm(w):.2f}, MSE={mse:.2f}")
```

### Lesson 3: The Bias-Variance Tradeoff (Through the Lens of Linear Algebra)

📊 **The Fundamental Tradeoff in ALL of ML:**

```
                High Bias          Sweet Spot         High Variance
                (underfitting)                        (overfitting)
                
  Error  │                          
         │  ╲                    ╱
         │   ╲ Test error      ╱
         │    ╲               ╱
         │     ╲   ╱─────╲  ╱
         │      ╲ ╱       ╲╱
         │       ╳    ★ optimal
         │      ╱ ╲
         │     ╱   ╲ Train error
         │────╱─────╲──────────
         └─────────────────────── Model complexity
                (rank / # features)
```

```python
import numpy as np

def bias_variance_demo():
    """Show bias-variance tradeoff with polynomial regression."""
    np.random.seed(42)
    
    # True function: y = sin(x)
    x_true = np.linspace(0, 2*np.pi, 200)
    y_true = np.sin(x_true)
    
    # Training data (noisy observations)
    n_train = 20
    x_train = np.random.uniform(0, 2*np.pi, n_train)
    y_train = np.sin(x_train) + 0.3 * np.random.randn(n_train)
    
    print(f"{'Degree':>7} {'Train MSE':>12} {'Test MSE':>12} {'Status':>15}")
    print("-" * 50)
    
    for degree in [1, 3, 5, 10, 18]:
        # Design matrix (polynomial features)
        X_train = np.column_stack([x_train**d for d in range(degree + 1)])
        X_test = np.column_stack([x_true**d for d in range(degree + 1)])
        
        # Fit
        try:
            w = np.linalg.lstsq(X_train, y_train, rcond=None)[0]
            y_pred_train = X_train @ w
            y_pred_test = X_test @ w
            
            train_mse = np.mean((y_train - y_pred_train)**2)
            test_mse = np.mean((y_true - y_pred_test)**2)
            
            status = "underfit" if test_mse > 0.5 else "overfit" if train_mse < 0.01 and test_mse > 0.5 else "good"
            print(f"{degree:>7} {train_mse:>12.4f} {test_mse:>12.4f} {status:>15}")
        except:
            print(f"{degree:>7} {'FAILED':>12}")

bias_variance_demo()
```

---

## 08.03 — Principal Component Analysis (4 Lessons)

### Lesson 1: The Big Idea

⚡ **ML Connection:** PCA is used everywhere — from preprocessing high-dimensional data before training, to visualizing embeddings, to denoising signals, to compressing images. If data has 1000 features but only 50 matter, PCA finds those 50.

💡 **Key Intuition:** PCA finds the directions of maximum variance in your data. It's like rotating your data so the most important information aligns with the axes, then dropping the least important axes.

```
BEFORE PCA:                         AFTER PCA:
  y                                   PC2
  │    · ·  · ·                       │
  │   · · ·· · ·                      │  ·  ·
  │  · · · · · ·  ← data            │ · · ·  · ← same data, 
  │ · · · · · ·     is tilted        │· · · ·     now axis-aligned!
  │· · · · · ·                        │ ·  ·
  └──────────── x                     └────────── PC1
                                      (maximum variance direction)
```

### Lesson 2: PCA Algorithm — Step by Step

```
Step 1: Center the data (subtract mean)
Step 2: Compute covariance matrix C = (1/n)XᵀX
Step 3: Find eigenvalues and eigenvectors of C
Step 4: Sort eigenvectors by eigenvalue (largest first)
Step 5: Project data onto top-k eigenvectors
```

```python
import numpy as np

def pca_from_scratch(X, n_components):
    """
    PCA implementation from first principles.
    Connects: covariance → eigendecomposition → projection
    """
    n_samples = X.shape[0]
    
    # Step 1: Center the data
    mean = X.mean(axis=0)
    X_centered = X - mean
    
    # Step 2: Covariance matrix
    C = (X_centered.T @ X_centered) / (n_samples - 1)
    
    # Step 3: Eigendecomposition (C is symmetric → use eigh)
    eigenvalues, eigenvectors = np.linalg.eigh(C)
    
    # Step 4: Sort by eigenvalue (descending)
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]
    
    # Step 5: Project onto top-k components
    W = eigenvectors[:, :n_components]
    X_pca = X_centered @ W
    
    # Explained variance
    explained_var = eigenvalues[:n_components] / eigenvalues.sum()
    
    return X_pca, W, eigenvalues, explained_var

# Generate correlated 3D data
np.random.seed(42)
n = 500
t = np.random.randn(n)
X = np.column_stack([
    2*t + 0.5*np.random.randn(n),     # Strongly correlated with t
    1.5*t + 0.5*np.random.randn(n),   # Also correlated
    0.1*np.random.randn(n)             # Almost pure noise
])

X_pca, W, eigenvalues, explained_var = pca_from_scratch(X, 2)

print("PCA Results:")
print(f"  Eigenvalues: {np.round(eigenvalues, 3)}")
print(f"  Explained variance ratios: {np.round(explained_var, 3)}")
print(f"  Total variance explained by 2 PCs: {explained_var.sum():.1%}")
print(f"  Original shape: {X.shape} → PCA shape: {X_pca.shape}")
```

### Lesson 3: PCA via SVD (How It's Actually Done)

💡 **The SVD Shortcut:** We don't need to compute the covariance matrix! SVD of the centered data directly gives PCA:

```
X = UΣVᵀ

Then:
  Principal components = U × Σ (the scores)
  Principal directions = V (the loadings)
  Eigenvalues of XᵀX = Σ² / (n-1)
```

```python
def pca_via_svd(X, n_components):
    """PCA using SVD — numerically more stable than eigendecomposition."""
    n = X.shape[0]
    X_centered = X - X.mean(axis=0)
    
    U, sigma, Vt = np.linalg.svd(X_centered, full_matrices=False)
    
    # Principal components
    X_pca = U[:, :n_components] * sigma[:n_components]
    
    # Explained variance
    explained_var = (sigma[:n_components]**2) / (sigma**2).sum()
    
    return X_pca, Vt[:n_components].T, explained_var

X_pca_svd, loadings, ev = pca_via_svd(X, 2)
print(f"SVD-based PCA explained variance: {ev}")
```

### Lesson 4: PCA in the Wild

📊 **When to Use PCA:**
```
Features → PCA → Top k PCs → Model
  1000      ↓       50          ↓
         Compute            Train faster,
         variance           less overfitting,
         directions         same accuracy!
```

```python
import numpy as np

# 1. DIMENSIONALITY REDUCTION for visualization
def visualize_high_dim(X, labels, n_components=2):
    """Reduce high-dimensional data to 2D for visualization."""
    X_2d, _, ev = pca_via_svd(X, n_components)
    print(f"Reduced {X.shape[1]}D → 2D")
    print(f"Preserved {ev.sum():.1%} of variance")
    return X_2d

# 2. FEATURE SELECTION (keep components above threshold)
def select_components(X, threshold=0.95):
    """Find minimum components to explain threshold% of variance."""
    X_centered = X - X.mean(axis=0)
    _, sigma, _ = np.linalg.svd(X_centered, full_matrices=False)
    
    cumulative = np.cumsum(sigma**2) / np.sum(sigma**2)
    n_components = np.searchsorted(cumulative, threshold) + 1
    
    print(f"Need {n_components} out of {X.shape[1]} features for {threshold:.0%} variance")
    return n_components

# 3. NOISE REDUCTION (remove small components)
def denoise_pca(X, n_components):
    """Remove noise by keeping only top components."""
    X_centered = X - X.mean(axis=0)
    U, sigma, Vt = np.linalg.svd(X_centered, full_matrices=False)
    
    # Zero out small singular values (noise)
    sigma_denoised = sigma.copy()
    sigma_denoised[n_components:] = 0
    
    X_denoised = U @ np.diag(sigma_denoised) @ Vt + X.mean(axis=0)
    return X_denoised

# Demo
np.random.seed(42)
X_demo = np.random.randn(200, 50)  # 200 samples, 50 features

n_needed = select_components(X_demo, threshold=0.95)
print(f"\nWith 50 random features: need {n_needed} components for 95% variance")
# (For random data, most are needed. For real data, much fewer!)
```

---

## 🔥 FAANG Deep Dive — Applications

### Interview Problem 1: Google — "Implement Linear Regression from Scratch"

```python
class LinearRegression:
    """Full linear regression implementation using only numpy."""
    
    def __init__(self, regularization=0.0):
        self.reg = regularization
        self.weights = None
        self.bias = None
    
    def fit(self, X, y):
        n_samples, n_features = X.shape
        
        # Add bias column
        X_b = np.column_stack([X, np.ones(n_samples)])
        
        # Normal equation with regularization
        I = np.eye(n_features + 1)
        I[-1, -1] = 0  # Don't regularize bias
        
        w = np.linalg.solve(
            X_b.T @ X_b + self.reg * I,
            X_b.T @ y
        )
        
        self.weights = w[:-1]
        self.bias = w[-1]
        return self
    
    def predict(self, X):
        return X @ self.weights + self.bias
    
    def score(self, X, y):
        """R² score."""
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred)**2)
        ss_tot = np.sum((y - y.mean())**2)
        return 1 - ss_res / ss_tot

# Test
np.random.seed(42)
X = np.random.randn(200, 5)
true_w = np.array([3, -2, 0, 1.5, -0.5])
y = X @ true_w + 2.0 + 0.5 * np.random.randn(200)

model = LinearRegression(regularization=0.1)
model.fit(X[:150], y[:150])

print(f"True weights:    {true_w}")
print(f"Learned weights: {np.round(model.weights, 3)}")
print(f"True bias: 2.0, Learned bias: {model.bias:.3f}")
print(f"Train R²: {model.score(X[:150], y[:150]):.4f}")
print(f"Test R²:  {model.score(X[150:], y[150:]):.4f}")
```

### Interview Problem 2: Meta — "Implement PCA from Scratch"

```python
class PCA:
    """Full PCA implementation."""
    
    def __init__(self, n_components):
        self.n_components = n_components
        self.components = None
        self.mean = None
        self.explained_variance_ratio = None
    
    def fit(self, X):
        self.mean = X.mean(axis=0)
        X_centered = X - self.mean
        
        # SVD-based (most stable)
        U, sigma, Vt = np.linalg.svd(X_centered, full_matrices=False)
        
        self.components = Vt[:self.n_components]
        variance = sigma**2 / (X.shape[0] - 1)
        self.explained_variance_ratio = variance[:self.n_components] / variance.sum()
        return self
    
    def transform(self, X):
        return (X - self.mean) @ self.components.T
    
    def inverse_transform(self, X_pca):
        return X_pca @ self.components + self.mean
    
    def fit_transform(self, X):
        self.fit(X)
        return self.transform(X)

# Test with face-like data
np.random.seed(42)
X = np.random.randn(500, 100)  # 500 "images" of 100 pixels

pca = PCA(n_components=10)
X_reduced = pca.fit_transform(X)

print(f"Original shape: {X.shape}")
print(f"Reduced shape:  {X_reduced.shape}")
print(f"Explained variance: {pca.explained_variance_ratio.sum():.1%}")

# Reconstruction error
X_reconstructed = pca.inverse_transform(X_reduced)
error = np.linalg.norm(X - X_reconstructed) / np.linalg.norm(X)
print(f"Reconstruction error: {error:.4f}")
```

---

## ✅ Module 08 Checkpoint

- [ ] Explain why we minimize squared residuals
- [ ] Derive the normal equation from scratch
- [ ] Implement linear regression with regularization
- [ ] Explain the bias-variance tradeoff geometrically
- [ ] Implement PCA using both eigendecomposition and SVD
- [ ] Determine the number of principal components needed
- [ ] Use PCA for dimensionality reduction and denoising

**Next →** [Module 09: Calculus](../module-09-calculus/README.md)
