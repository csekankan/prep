# Module 09 — Calculus

## The Language of Change That Trains Every Model

> **Why Calculus Matters in ML:** Backpropagation IS calculus. Gradient descent IS calculus. Every time a neural network learns, it's computing derivatives and following gradients. This module is the mathematical core of deep learning.

```
 MODULE 09 ROADMAP
 ═══════════════════════════════════════════════════
 09.01 Geometry of Multivariable Surfaces
 09.02 Local Change in Many Variables
 09.03 Gradients & Vector-Valued Maps
 09.04 Jacobians & Local Approximation
 09.05 Matrix Calculus
 09.06 From Partitions to Volume
 09.07 Integration over Two Variables
 09.08 Constrained & Unconstrained Optimization
 ═══════════════════════════════════════════════════
```

---

## 09.01 — Geometry of Multivariable Surfaces (7 Lessons)

### Lesson 1: Functions of Multiple Variables

💡 **Key Intuition:** A function f(x, y) maps a point on the floor to a height. The result is a surface — and a loss function is exactly such a surface!

```
f(x, y) = x² + y²    ← a bowl (paraboloid)

      z
      │     ╱╲
      │    ╱  ╲
      │   ╱    ╲
      │  ╱   ★  ╲    ★ = minimum at (0,0)
      │ ╱________╲
      └──────────── x
     ╱
    y
```

```python
import numpy as np

# Loss surface visualization data
def loss_function(w1, w2):
    """A simple loss surface: f(w1, w2) = w1² + 2*w2²"""
    return w1**2 + 2*w2**2

# Create a grid of points
w1 = np.linspace(-3, 3, 50)
w2 = np.linspace(-3, 3, 50)
W1, W2 = np.meshgrid(w1, w2)
L = loss_function(W1, W2)

print(f"Loss at (0, 0): {loss_function(0, 0)}")     # 0 (minimum)
print(f"Loss at (1, 1): {loss_function(1, 1)}")     # 3
print(f"Loss at (2, 2): {loss_function(2, 2)}")     # 12
```

### Lesson 2: Level Curves (Contour Lines)

**Level curves** connect points of equal function value, like elevation lines on a map.

```
Contour plot of f(x,y) = x² + y²:

  y
  │    ╱────╲
  │   ╱ ╱──╲ ╲    Each ring = constant f value
  │  ╱ ╱ ·  ╲ ╲   · = minimum
  │  ╲ ╲    ╱ ╱
  │   ╲ ╲──╱ ╱
  │    ╲────╱
  └──────────── x

Circular contours → equal curvature in all directions
Elongated contours → different curvatures (ill-conditioned!)
```

### Lessons 3-7: Surfaces, Cross Sections, and Topology

⚡ **ML Connection — Loss Landscape Topology:**

```python
# Different loss landscape shapes and what they mean
import numpy as np

# Bowl (convex) — easy to optimize
def convex_loss(w1, w2):
    return w1**2 + w2**2

# Saddle point — tricky for gradient descent
def saddle_loss(w1, w2):
    return w1**2 - w2**2

# Multiple minima — non-convex (like real neural networks!)
def multi_minima_loss(w1, w2):
    return np.sin(w1) * np.cos(w2) + 0.1 * (w1**2 + w2**2)

# Ravine (ill-conditioned) — GD oscillates
def ravine_loss(w1, w2):
    return w1**2 + 100 * w2**2

for name, f in [("Bowl", convex_loss), ("Saddle", saddle_loss), 
                ("Multi-min", multi_minima_loss), ("Ravine", ravine_loss)]:
    print(f"{name}: f(0,0)={f(0,0):.2f}, f(1,1)={f(1,1):.2f}")
```

---

## 09.02 — Local Change in Many Variables (13 Lessons)

### Lesson 1: Partial Derivatives

A **partial derivative** measures how f changes when you wiggle ONE variable, keeping others fixed.

```
∂f/∂x = lim[h→0] (f(x+h, y) − f(x, y)) / h     ← change in x direction
∂f/∂y = lim[h→0] (f(x, y+h) − f(x, y)) / h     ← change in y direction
```

**Example:** f(x, y) = x²y + 3xy²

```
∂f/∂x = 2xy + 3y²      ← treat y as constant, differentiate with respect to x
∂f/∂y = x² + 6xy        ← treat x as constant, differentiate with respect to y
```

```python
import numpy as np

def f(x, y):
    return x**2 * y + 3 * x * y**2

# Numerical partial derivatives
def partial_x(f, x, y, h=1e-7):
    return (f(x + h, y) - f(x - h, y)) / (2 * h)

def partial_y(f, x, y, h=1e-7):
    return (f(x, y + h) - f(x, y - h)) / (2 * h)

# Analytical: ∂f/∂x = 2xy + 3y², ∂f/∂y = x² + 6xy
x, y = 2.0, 3.0

print(f"∂f/∂x at ({x},{y}):")
print(f"  Numerical: {partial_x(f, x, y):.6f}")
print(f"  Analytical: {2*x*y + 3*y**2:.6f}")

print(f"∂f/∂y at ({x},{y}):")
print(f"  Numerical: {partial_y(f, x, y):.6f}")
print(f"  Analytical: {x**2 + 6*x*y:.6f}")
```

### Lesson 2: The Chain Rule — The Heart of Backpropagation ⭐

💡 **THE most important calculus rule in all of ML:**

```
If z = f(g(x)), then:
  dz/dx = (dz/dg) × (dg/dx)

Multi-variable chain rule:
  If z = f(u, v), u = g(x, y), v = h(x, y):
  ∂z/∂x = (∂z/∂u)(∂u/∂x) + (∂z/∂v)(∂v/∂x)
```

📊 **Backpropagation IS the Chain Rule:**
```
Input → [Layer 1] → [Layer 2] → [Layer 3] → Loss
  x        W₁          W₂          W₃        L

Forward: L = f₃(f₂(f₁(x)))

Backward (chain rule!):
  ∂L/∂W₃ = ∂L/∂f₃ × ∂f₃/∂W₃
  ∂L/∂W₂ = ∂L/∂f₃ × ∂f₃/∂f₂ × ∂f₂/∂W₂
  ∂L/∂W₁ = ∂L/∂f₃ × ∂f₃/∂f₂ × ∂f₂/∂f₁ × ∂f₁/∂W₁
```

```python
import numpy as np

# Manual backpropagation for a tiny network
def forward_and_backward(x, w1, w2, y_true):
    """
    Network: input → linear → relu → linear → MSE loss
    """
    # Forward pass
    z1 = w1 * x                    # linear layer 1
    a1 = max(0, z1)                # ReLU activation
    z2 = w2 * a1                   # linear layer 2
    loss = (z2 - y_true) ** 2      # MSE loss
    
    # Backward pass (chain rule!)
    dL_dz2 = 2 * (z2 - y_true)           # ∂Loss/∂z2
    dL_dw2 = dL_dz2 * a1                 # ∂Loss/∂w2 = ∂Loss/∂z2 × ∂z2/∂w2
    dL_da1 = dL_dz2 * w2                 # ∂Loss/∂a1 = ∂Loss/∂z2 × ∂z2/∂a1
    dL_dz1 = dL_da1 * (1 if z1 > 0 else 0)  # ∂Loss/∂z1 (ReLU derivative)
    dL_dw1 = dL_dz1 * x                  # ∂Loss/∂w1
    
    return loss, dL_dw1, dL_dw2

# Train for a few steps
x, y_true = 2.0, 4.0
w1, w2 = 0.5, 0.5
lr = 0.01

for step in range(20):
    loss, grad_w1, grad_w2 = forward_and_backward(x, w1, w2, y_true)
    w1 -= lr * grad_w1
    w2 -= lr * grad_w2
    if step % 5 == 0:
        print(f"Step {step:>2}: loss={loss:.4f}, w1={w1:.4f}, w2={w2:.4f}")
```

### Lessons 3-13: Higher-Order Derivatives, Taylor Series, and More

**Taylor Series — Approximating Functions Locally:**

```
f(x + h) ≈ f(x) + f'(x)h + (1/2)f''(x)h² + ...

Multi-variable:
f(x + δ) ≈ f(x) + ∇fᵀδ + (1/2)δᵀHδ

Where:
  ∇f = gradient (first derivatives)
  H = Hessian (second derivatives)
```

⚡ **ML Connection:** This is why second-order optimizers (Newton, L-BFGS) exist — they use the Hessian term for better updates.

---

## 09.03 — Gradients and Vector-Valued Maps (7 Lessons)

### Lesson 1: The Gradient Vector

The **gradient** ∇f is a vector of all partial derivatives — it points in the direction of steepest ascent.

```
           ∂f/∂x₁
∇f(x) =   ∂f/∂x₂
           ...
           ∂f/∂xₙ
```

📊 **The Gradient Points Uphill:**
```
Contour plot with gradient arrows:

  ╱────╲
 ╱ ╱──╲ ╲     →→  gradient points AWAY from minimum
╱ ╱ ·  ╲ ╲    ←   negative gradient points TOWARD minimum
 ╲ ╲──╱ ╱          (that's gradient DESCENT!)
  ╲────╱
```

💡 **Key Insight:** Gradient descent goes in the OPPOSITE direction of the gradient: x_new = x_old − α∇f

```python
import numpy as np

def gradient_descent(f, grad_f, x0, lr=0.1, steps=100, tol=1e-8):
    """
    General gradient descent optimizer.
    
    f: loss function
    grad_f: gradient function (returns vector)
    x0: initial point
    lr: learning rate (step size)
    """
    x = x0.copy()
    history = [x.copy()]
    
    for i in range(steps):
        g = grad_f(x)
        x = x - lr * g
        history.append(x.copy())
        
        if np.linalg.norm(g) < tol:
            print(f"Converged in {i+1} steps!")
            break
    
    return x, np.array(history)

# Example: minimize f(x,y) = x² + 4y²
f = lambda x: x[0]**2 + 4*x[1]**2
grad_f = lambda x: np.array([2*x[0], 8*x[1]])

x0 = np.array([4.0, 3.0])
x_min, history = gradient_descent(f, grad_f, x0, lr=0.1, steps=50)

print(f"Starting point: {x0}, loss = {f(x0):.2f}")
print(f"Final point: {np.round(x_min, 6)}, loss = {f(x_min):.6f}")
```

### Lesson 2: Gradient Properties

| Property | Description |
|---------|-------------|
| Direction | Points toward steepest ascent |
| Magnitude | Rate of steepest change |
| Perpendicular to level curves | Always cuts contours at 90° |
| Zero at extrema | ∇f = 0 at min, max, and saddle points |

### Lessons 3-7: Directional Derivatives and Vector Fields

**Directional Derivative:** Rate of change in ANY direction u:

```
D_u f = ∇f · u     (dot product of gradient with direction)
```

This tells you: "If I walk in direction u, how fast does f change?"

```python
# Directional derivative
def directional_derivative(grad_f, x, direction):
    """How fast does f change in the given direction at point x?"""
    g = grad_f(x)
    u = direction / np.linalg.norm(direction)  # Normalize
    return np.dot(g, u)

grad_f = lambda x: np.array([2*x[0], 8*x[1]])
x = np.array([1.0, 1.0])

# Steepest ascent direction = gradient direction
g = grad_f(x)
dd_gradient = directional_derivative(grad_f, x, g)
print(f"Rate in gradient direction: {dd_gradient:.3f}")  # Maximum!

# Random direction
u = np.array([1.0, 0.0])  # Pure x-direction
dd_x = directional_derivative(grad_f, x, u)
print(f"Rate in x-direction: {dd_x:.3f}")
```

---

## 09.04 — Jacobians and Local Approximation (6 Lessons)

### Lesson 1: The Jacobian Matrix

When a function maps **vectors to vectors** (f: ℝⁿ → ℝᵐ), the derivative is a matrix — the **Jacobian**.

```
f(x₁, x₂) = [f₁(x₁,x₂), f₂(x₁,x₂), f₃(x₁,x₂)]

          ┌                        ┐
          │ ∂f₁/∂x₁   ∂f₁/∂x₂    │
J(f) =   │ ∂f₂/∂x₁   ∂f₂/∂x₂    │     (3×2 matrix)
          │ ∂f₃/∂x₁   ∂f₃/∂x₂    │
          └                        ┘
```

⚡ **ML Connection:** Each layer of a neural network has a Jacobian. Backpropagation multiplies Jacobians together (chain rule for matrices).

```python
import numpy as np

def compute_jacobian(f, x, h=1e-7):
    """Numerically compute the Jacobian matrix."""
    n = len(x)
    fx = f(x)
    m = len(fx)
    J = np.zeros((m, n))
    
    for j in range(n):
        x_plus = x.copy()
        x_plus[j] += h
        x_minus = x.copy()
        x_minus[j] -= h
        J[:, j] = (f(x_plus) - f(x_minus)) / (2 * h)
    
    return J

# Example: softmax function (used in every classifier!)
def softmax(x):
    e = np.exp(x - x.max())
    return e / e.sum()

x = np.array([1.0, 2.0, 3.0])
J = compute_jacobian(softmax, x)
print(f"Softmax Jacobian (3×3):\n{np.round(J, 4)}")

# The Jacobian of softmax has a beautiful closed form:
# J[i,j] = s[i](δ[i,j] - s[j])  where s = softmax(x)
s = softmax(x)
J_analytical = np.diag(s) - np.outer(s, s)
print(f"\nAnalytical Jacobian:\n{np.round(J_analytical, 4)}")
print(f"Match? {np.allclose(J, J_analytical, atol=1e-5)}")
```

### Lesson 2-6: Linear Approximation and the Chain Rule for Jacobians

```
Jacobian chain rule:
  If h = g ∘ f, then J(h) = J(g) × J(f)

This is EXACTLY how backpropagation works for matrix operations!
```

---

## 09.05 — Matrix Calculus (5 Lessons)

### Lesson 1: Derivatives of Matrix Expressions

The rules you need for ML:

| Expression | Derivative w.r.t. x | Notes |
|-----------|---------------------|-------|
| aᵀx | a | Linear function |
| xᵀAx | (A + Aᵀ)x | Quadratic form |
| \|\|Ax − b\|\|² | 2Aᵀ(Ax − b) | Least squares gradient |
| xᵀx | 2x | Squared norm |
| tr(AB) | Bᵀ | Trace derivative |

```python
import numpy as np

# Verify: gradient of ||Ax - b||² = 2Aᵀ(Ax - b)
np.random.seed(42)
m, n = 5, 3
A = np.random.randn(m, n)
b = np.random.randn(m)
x = np.random.randn(n)

# Numerical gradient
def loss(x):
    return np.sum((A @ x - b)**2)

def numerical_gradient(f, x, h=1e-7):
    grad = np.zeros_like(x)
    for i in range(len(x)):
        x_plus = x.copy(); x_plus[i] += h
        x_minus = x.copy(); x_minus[i] -= h
        grad[i] = (f(x_plus) - f(x_minus)) / (2 * h)
    return grad

grad_numerical = numerical_gradient(loss, x)
grad_analytical = 2 * A.T @ (A @ x - b)

print(f"Numerical gradient:  {np.round(grad_numerical, 6)}")
print(f"Analytical gradient: {np.round(grad_analytical, 6)}")
print(f"Match? {np.allclose(grad_numerical, grad_analytical)}")
```

### Lessons 2-5: Backpropagation Through Matrix Operations

```python
import numpy as np

class AutogradValue:
    """Simplified autograd — tracks computation graph for backprop."""
    
    def __init__(self, value, grad_fn=None, children=()):
        self.value = np.array(value, dtype=float)
        self.grad = np.zeros_like(self.value)
        self.grad_fn = grad_fn
        self.children = children
    
    def backward(self, grad=None):
        if grad is None:
            grad = np.ones_like(self.value)
        self.grad += grad
        if self.grad_fn:
            self.grad_fn(grad)
    
    def __repr__(self):
        return f"AutogradValue({self.value})"

def matmul_forward(X, W):
    """Matrix multiplication with gradient tracking."""
    result = AutogradValue(X.value @ W.value)
    
    def backward(grad):
        X.backward(grad @ W.value.T)     # ∂L/∂X = ∂L/∂Y × Wᵀ
        W.backward(X.value.T @ grad)     # ∂L/∂W = Xᵀ × ∂L/∂Y
    
    result.grad_fn = backward
    return result

# Demo
X = AutogradValue([[1, 2], [3, 4]])
W = AutogradValue([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])

Y = matmul_forward(X, W)
print(f"Forward: X @ W = {Y.value}")

# Backward
Y.backward(np.ones_like(Y.value))
print(f"∂L/∂X = {X.grad}")
print(f"∂L/∂W = {W.grad}")
```

---

## 09.06 & 09.07 — Integration (13 Lessons)

### Key Concepts: From Sums to Integrals

💡 **Key Intuition:** An integral is a continuous sum. In ML, we use integrals for:
- Expected values: E[X] = ∫ x·f(x)dx
- Normalizing probability distributions: ∫ f(x)dx = 1
- Computing marginal distributions
- Evidence in Bayesian inference

### Lesson 1: Single-Variable Integration

```python
from scipy import integrate
import numpy as np

# 1. Expected value of a normal distribution (should be μ)
def normal_pdf(x, mu=0, sigma=1):
    return (1/(sigma * np.sqrt(2*np.pi))) * np.exp(-0.5*((x-mu)/sigma)**2)

# E[X] = ∫ x·f(x)dx
mu, sigma = 3, 2
E_X, _ = integrate.quad(lambda x: x * normal_pdf(x, mu, sigma), -np.inf, np.inf)
print(f"E[X] = {E_X:.4f} (should be {mu})")

# Var[X] = E[X²] - (E[X])²
E_X2, _ = integrate.quad(lambda x: x**2 * normal_pdf(x, mu, sigma), -np.inf, np.inf)
Var_X = E_X2 - E_X**2
print(f"Var[X] = {Var_X:.4f} (should be {sigma**2})")

# 2. Verify PDF integrates to 1
total, _ = integrate.quad(lambda x: normal_pdf(x, mu, sigma), -np.inf, np.inf)
print(f"∫f(x)dx = {total:.6f} (should be 1)")
```

### Lesson 2: Double Integrals — Integration over Two Variables

When you have a function of TWO variables, you integrate over a 2D region:

```
∫∫_R f(x,y) dA = ∫ₐᵇ ∫_c^d f(x,y) dy dx
```

```python
from scipy import integrate
import numpy as np

# Double integral: ∫∫ x²y dA over [0,2] × [0,3]
result, error = integrate.dblquad(
    lambda y, x: x**2 * y,   # f(y, x) — note: y first!
    0, 2,                      # x limits
    0, 3                       # y limits
)
print(f"∫∫ x²y dA = {result:.4f}")
# Analytical: ∫₀² x² dx × ∫₀³ y dy = (8/3)(9/2) = 12.0
print(f"Analytical: {(8/3) * (9/2):.4f}")

# ML Example: Marginal probability from joint density
# If f(x,y) = 6xy for 0 ≤ x ≤ 1, 0 ≤ y ≤ 1 − x
# Marginal: f_X(x) = ∫₀^(1-x) 6xy dy

def joint_pdf(y, x):
    if 0 <= x <= 1 and 0 <= y <= 1 - x:
        return 6 * x * y
    return 0

# Compute marginal f_X(0.3)
x_val = 0.3
marginal, _ = integrate.quad(lambda y: joint_pdf(y, x_val), 0, 1 - x_val)
print(f"\nf_X({x_val}) = {marginal:.4f}")
# Analytical: f_X(x) = 6x · (1-x)²/2 = 3x(1-x)²
print(f"Analytical:  {3 * x_val * (1 - x_val)**2:.4f}")
```

### Lesson 3: Monte Carlo Integration ⭐

⚡ **ML Connection:** When integrals are intractable (common in Bayesian ML), we use random sampling to approximate them.

```python
import numpy as np

def monte_carlo_integrate(f, bounds, n_samples=100000):
    """
    Approximate ∫f(x)dx using random sampling.
    Works in ANY number of dimensions!
    
    bounds: list of (low, high) for each dimension
    """
    dim = len(bounds)
    volume = 1.0
    for low, high in bounds:
        volume *= (high - low)
    
    # Sample random points
    points = np.column_stack([
        np.random.uniform(low, high, n_samples)
        for low, high in bounds
    ])
    
    # Evaluate function at all points
    values = np.array([f(*p) for p in points])
    
    # Integral ≈ volume × average function value
    integral = volume * values.mean()
    std_error = volume * values.std() / np.sqrt(n_samples)
    
    return integral, std_error

# Example 1: Area of a circle (π) using Monte Carlo
def inside_circle(x, y):
    return 1.0 if x**2 + y**2 <= 1 else 0.0

pi_estimate, error = monte_carlo_integrate(inside_circle, [(-1, 1), (-1, 1)])
print(f"π ≈ {pi_estimate:.4f} ± {error:.4f} (true: {np.pi:.4f})")

# Example 2: High-dimensional integral (impossible analytically!)
# ∫∫∫∫∫ exp(-x₁²-x₂²-x₃²-x₄²-x₅²) over [-2,2]⁵
def gaussian_5d(x1, x2, x3, x4, x5):
    return np.exp(-(x1**2 + x2**2 + x3**2 + x4**2 + x5**2))

bounds_5d = [(-2, 2)] * 5
result, error = monte_carlo_integrate(gaussian_5d, bounds_5d, n_samples=500000)
print(f"5D Gaussian integral ≈ {result:.4f} ± {error:.4f}")
print(f"Analytical: π^(5/2) = {np.pi**2.5:.4f}")

# Example 3: Evidence in Bayesian inference (the hard integral)
# P(D) = ∫ P(D|θ)P(θ) dθ — this integral makes Bayes hard!
def unnormalized_posterior(theta):
    prior = np.exp(-theta**2 / 2)           # N(0,1) prior
    likelihood = np.exp(-3 * (theta - 2)**2) # likelihood peaked at 2
    return prior * likelihood

evidence, _ = monte_carlo_integrate(
    lambda t: unnormalized_posterior(t), [(-5, 5)], n_samples=100000
)
print(f"\nBayesian evidence P(D) ≈ {evidence:.6f}")
```

---

## 09.08 — Constrained and Unconstrained Optimization (6 Lessons)

### Lesson 1: Finding Minima (Unconstrained)

**First-order condition:** ∇f(x*) = 0 (gradient is zero at optimum)

**Second-order condition:** H(x*) is positive definite (it's a bowl, not a saddle)

### Lesson 2: Gradient Descent Variants

```python
import numpy as np

class Optimizer:
    """All major optimizers in one place."""
    
    @staticmethod
    def sgd(params, grads, lr=0.01):
        return params - lr * grads
    
    @staticmethod
    def momentum(params, grads, velocity, lr=0.01, beta=0.9):
        velocity = beta * velocity + grads
        return params - lr * velocity, velocity
    
    @staticmethod
    def rmsprop(params, grads, cache, lr=0.01, beta=0.999, eps=1e-8):
        cache = beta * cache + (1-beta) * grads**2
        return params - lr * grads / (np.sqrt(cache) + eps), cache
    
    @staticmethod
    def adam(params, grads, m, v, t, lr=0.001, beta1=0.9, beta2=0.999, eps=1e-8):
        m = beta1 * m + (1-beta1) * grads        # First moment
        v = beta2 * v + (1-beta2) * grads**2      # Second moment
        m_hat = m / (1 - beta1**t)                 # Bias correction
        v_hat = v / (1 - beta2**t)
        return params - lr * m_hat / (np.sqrt(v_hat) + eps), m, v

# Compare optimizers on the Rosenbrock function
def rosenbrock(x):
    return (1 - x[0])**2 + 100 * (x[1] - x[0]**2)**2

def rosenbrock_grad(x):
    return np.array([
        -2*(1-x[0]) - 400*x[0]*(x[1]-x[0]**2),
        200*(x[1]-x[0]**2)
    ])

x0 = np.array([-1.0, 1.0])
print(f"Rosenbrock minimum at (1, 1), f = 0")
print(f"Starting at {x0}, f = {rosenbrock(x0):.1f}\n")

# SGD
x = x0.copy()
for i in range(10000):
    x = Optimizer.sgd(x, rosenbrock_grad(x), lr=0.001)
print(f"SGD (10K steps):  x = {np.round(x, 4)}, f = {rosenbrock(x):.6f}")

# Adam
x = x0.copy()
m, v = np.zeros(2), np.zeros(2)
for i in range(10000):
    x, m, v = Optimizer.adam(x, rosenbrock_grad(x), m, v, i+1, lr=0.001)
print(f"Adam (10K steps): x = {np.round(x, 4)}, f = {rosenbrock(x):.6f}")
```

### Lesson 3: Lagrange Multipliers (Constrained Optimization) ⭐

**Problem:** Minimize f(x) subject to g(x) = 0

**Method:** Solve ∇f = λ∇g (gradients are parallel at the optimum)

```python
from scipy.optimize import minimize

# Minimize x² + y² subject to x + y = 1
# (find the point on the line x+y=1 closest to the origin)

result = minimize(
    fun=lambda x: x[0]**2 + x[1]**2,      # objective
    x0=[0, 0],                              # start
    constraints={'type': 'eq', 'fun': lambda x: x[0] + x[1] - 1}  # constraint
)

print(f"Minimum at: ({result.x[0]:.3f}, {result.x[1]:.3f})")  # (0.5, 0.5)
print(f"f(x*) = {result.fun:.3f}")  # 0.5

# This is used in SVMs! Minimize ||w||² subject to yᵢ(w·xᵢ + b) ≥ 1
```

⚡ **ML Connections for Constrained Optimization:**
- **SVMs:** Maximize margin subject to correct classification
- **Normalizing flows:** Volume preservation constraint
- **KKT conditions:** Foundation of SVM dual problem

---

## 🔥 FAANG Deep Dive — Calculus

### Interview Problem 1: Google — "Implement Backpropagation"

```python
import numpy as np

class MiniNeuralNetwork:
    """Complete 2-layer neural network with backprop."""
    
    def __init__(self, input_size, hidden_size, output_size):
        self.W1 = np.random.randn(input_size, hidden_size) * 0.1
        self.b1 = np.zeros(hidden_size)
        self.W2 = np.random.randn(hidden_size, output_size) * 0.1
        self.b2 = np.zeros(output_size)
    
    def relu(self, x):
        return np.maximum(0, x)
    
    def relu_deriv(self, x):
        return (x > 0).astype(float)
    
    def forward(self, X):
        self.z1 = X @ self.W1 + self.b1          # Linear 1
        self.a1 = self.relu(self.z1)               # ReLU
        self.z2 = self.a1 @ self.W2 + self.b2     # Linear 2
        return self.z2                              # Output (raw scores)
    
    def backward(self, X, y, y_pred, lr=0.01):
        m = X.shape[0]
        
        # Output layer gradient
        dz2 = (y_pred - y) / m                                  # ∂L/∂z2
        dW2 = self.a1.T @ dz2                                    # ∂L/∂W2
        db2 = dz2.sum(axis=0)                                    # ∂L/∂b2
        
        # Hidden layer gradient (chain rule!)
        da1 = dz2 @ self.W2.T                                    # ∂L/∂a1
        dz1 = da1 * self.relu_deriv(self.z1)                    # ∂L/∂z1
        dW1 = X.T @ dz1                                          # ∂L/∂W1
        db1 = dz1.sum(axis=0)                                    # ∂L/∂b1
        
        # Update weights
        self.W1 -= lr * dW1
        self.b1 -= lr * db1
        self.W2 -= lr * dW2
        self.b2 -= lr * db2
    
    def train(self, X, y, epochs=1000, lr=0.01):
        for epoch in range(epochs):
            y_pred = self.forward(X)
            loss = np.mean((y_pred - y)**2)
            self.backward(X, y, y_pred, lr)
            
            if epoch % 200 == 0:
                print(f"Epoch {epoch:>4}: loss = {loss:.6f}")

# Test: learn XOR (impossible with single layer!)
X = np.array([[0,0], [0,1], [1,0], [1,1]])
y = np.array([[0], [1], [1], [0]])

nn = MiniNeuralNetwork(2, 8, 1)
nn.train(X, y, epochs=1000, lr=0.5)

print("\nPredictions:")
for i in range(4):
    pred = nn.forward(X[i:i+1])
    print(f"  {X[i]} → {pred[0,0]:.3f} (target: {y[i,0]})")
```

### Interview Problem 2: Amazon — "Implement Adam Optimizer"

```python
class AdamOptimizer:
    """Complete Adam optimizer implementation."""
    
    def __init__(self, lr=0.001, beta1=0.9, beta2=0.999, eps=1e-8):
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.m = {}   # First moment estimates
        self.v = {}   # Second moment estimates
        self.t = 0    # Time step
    
    def step(self, params, grads):
        """Update parameters using Adam."""
        self.t += 1
        updated = {}
        
        for key in params:
            if key not in self.m:
                self.m[key] = np.zeros_like(params[key])
                self.v[key] = np.zeros_like(params[key])
            
            # Update biased moments
            self.m[key] = self.beta1 * self.m[key] + (1-self.beta1) * grads[key]
            self.v[key] = self.beta2 * self.v[key] + (1-self.beta2) * grads[key]**2
            
            # Bias correction
            m_hat = self.m[key] / (1 - self.beta1**self.t)
            v_hat = self.v[key] / (1 - self.beta2**self.t)
            
            # Update
            updated[key] = params[key] - self.lr * m_hat / (np.sqrt(v_hat) + self.eps)
        
        return updated

# Test Adam on a simple problem
optimizer = AdamOptimizer(lr=0.1)
params = {"w": np.array([5.0, -3.0])}

for i in range(100):
    # Gradient of f(w) = w1² + w2² is [2w1, 2w2]
    grads = {"w": 2 * params["w"]}
    params = optimizer.step(params, grads)
    
    if i % 20 == 0:
        loss = np.sum(params["w"]**2)
        print(f"Step {i:>3}: w = {np.round(params['w'], 4)}, loss = {loss:.6f}")
```

---

## ✅ Module 09 Checkpoint

- [ ] Compute partial derivatives by hand and numerically
- [ ] Apply the chain rule (single and multi-variable)
- [ ] Compute and interpret gradients
- [ ] Build a computation graph and backpropagate through it
- [ ] Compute Jacobian matrices
- [ ] Implement gradient descent, momentum, and Adam
- [ ] Solve constrained optimization with Lagrange multipliers
- [ ] Implement a neural network with backpropagation from scratch

**Next →** [Module 10: Probability](../module-10-probability/README.md)
