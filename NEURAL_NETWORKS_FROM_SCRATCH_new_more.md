# Neural Networks & Deep Learning From Scratch — Core-Level Implementation Guide (Beginner → Research Engineer)

> Build a real autograd engine, a real MLP, a real Transformer decoder (GPT-style), and a real fine-tuning
> pipeline (full fine-tune + LoRA) — using **only Python + NumPy**, core-level, the way you'd implement a
> paper if the paper's official code didn't exist. Then (Sections 20-21) see the exact same architectures
> and fine-tuning techniques written idiomatically in **PyTorch** and **TensorFlow/Keras**, so you can map
> every from-scratch line to its framework equivalent. Section 22 covers everything ELSE a real research-paper
> implementation needs beyond the model code itself: reproducibility, LR schedules, checkpointing, and more.
> **New here?** Read [Section 0](#0-beginner-primer--read-this-first) first.

---

## Table of Contents

0. [Beginner Primer — Read This First](#0-beginner-primer--read-this-first)
1. [Why Build From Scratch (No PyTorch/TensorFlow)](#1-why-build-from-scratch-no-pytorchtensorflow)
2. [Autograd Engine From Scratch — The Core of Every Framework](#2-autograd-engine-from-scratch--the-core-of-every-framework)
3. [Building Blocks: Linear, Activations, Losses](#3-building-blocks-linear-activations-losses)
4. [Backpropagation Derived From First Principles](#4-backpropagation-derived-from-first-principles)
5. [Building & Training a Multi-Layer Perceptron From Scratch](#5-building--training-a-multi-layer-perceptron-from-scratch)
6. [Optimizers From Scratch (SGD, Momentum, Adam)](#6-optimizers-from-scratch-sgd-momentum-adam)
7. [Gradient Checking — Proving Your Backward Pass Is Correct](#7-gradient-checking--proving-your-backward-pass-is-correct)
8. [Convolution From Scratch (im2col Forward/Backward)](#8-convolution-from-scratch-im2col-forwardbackward)
9. [RNN & LSTM Cells From Scratch](#9-rnn--lstm-cells-from-scratch)
10. [Self-Attention From Scratch: Math + Backward Derivation](#10-self-attention-from-scratch-math--backward-derivation)
11. [Building a GPT-Style Decoder-Only Transformer From Scratch](#11-building-a-gpt-style-decoder-only-transformer-from-scratch)
12. [Training a Tiny GPT From Scratch (Character-Level LM)](#12-training-a-tiny-gpt-from-scratch-character-level-lm)
13. [Fine-Tuning — Core Concepts From First Principles](#13-fine-tuning--core-concepts-from-first-principles)
14. [Full Fine-Tuning From Scratch](#14-full-fine-tuning-from-scratch)
15. [Parameter-Efficient Fine-Tuning: LoRA From Scratch](#15-parameter-efficient-fine-tuning-lora-from-scratch)
16. [Decoder Fine-Tuning: Loss Masking, Packing, Teacher Forcing](#16-decoder-fine-tuning-loss-masking-packing-teacher-forcing)
17. [End-to-End Project: Pretrain → Fine-Tune a Tiny Decoder LM](#17-end-to-end-project-pretrain--fine-tune-a-tiny-decoder-lm)
18. [What Frameworks (PyTorch/TF) Actually Automate For You](#18-what-frameworks-pytorchtf-actually-automate-for-you)
19. [Interview Questions & Common Pitfalls](#19-interview-questions--common-pitfalls)
20. [The Same GPT + Fine-Tuning in PyTorch](#20-the-same-gpt--fine-tuning-in-pytorch)
21. [The Same GPT + Fine-Tuning in TensorFlow/Keras](#21-the-same-gpt--fine-tuning-in-tensorflowkeras)
22. [Beyond the Code: What Real Research-Paper Implementations Need](#22-beyond-the-code-what-real-research-paper-implementations-need)

---

## 0. Beginner Primer — Read This First

### What does "core level, like implementing a research paper" mean?

```
When a paper like "Attention Is All You Need" or a fine-tuning paper like "LoRA: Low-Rank
Adaptation" is published, the authors don't get PyTorch's autograd for free at the MATH level —
PyTorch is just a tool that happens to implement the chain rule efficiently. To truly understand
an architecture, you should be able to answer:

  1. What is the exact forward-pass formula (shapes, matrix multiplies, non-linearities)?
  2. What is the exact backward-pass formula (the derivative of the loss w.r.t. every weight)?
  3. How do you turn those formulas into working code that trains and converges?

This document does all three, using nothing but NumPy arrays and Python control flow. By the
end you will have written your own miniature "PyTorch" (an autograd engine), your own GPT
(a decoder-only Transformer), and your own fine-tuning pipeline (full fine-tune + LoRA) —
entirely from first principles.
```

### Why NumPy only, and not "no libraries at all"?

```
NumPy gives you fast array storage and vectorized math (matrix multiply, elementwise ops) —
the equivalent of "arithmetic" for this exercise. It does NOT give you:
  - Automatic differentiation (computing gradients automatically)      → you build this (Section 2)
  - Layers (nn.Linear, nn.LayerNorm, nn.MultiheadAttention)             → you build these (Sections 3, 10, 11)
  - Optimizers (torch.optim.Adam)                                      → you build these (Section 6)
  - Training loops, LoRA, fine-tuning utilities                        → you build these (Sections 13-16)

That is exactly the boundary we want: NumPy = "a calculator that's fast at matrix math."
Everything that makes it "deep learning" — the learning part — you implement yourself.
```

### The one idea that everything below builds on: the chain rule

```
Forward pass:  x → f1 → f2 → f3 → loss                 (compute a number: how wrong are we?)
Backward pass: loss → ∂loss/∂f3 → ∂loss/∂f2 → ∂loss/∂f1 → ∂loss/∂x   (chain rule, applied
               layer by layer, right to left)

∂loss/∂(any weight w inside f2) tells you: "if I nudge w up by a tiny amount, does the loss
go up or down, and by how much?" Gradient descent then does:
               w = w - learning_rate * ∂loss/∂w
repeated thousands of times. Every single thing in this document — MLPs, CNNs, RNNs,
Transformers, GPT, fine-tuning, LoRA — is this ONE idea, applied to progressively more
complicated forward-pass formulas.
```

### How to read this document

Each section states the **theory/math first** (as you'd see in a paper), then gives a **from-scratch
NumPy implementation** you can run. Sections build on each other in order — the autograd engine from
Section 2 is reused everywhere after it. If you already have a working autograd engine, skip to
whichever architecture/fine-tuning section you need.

---

## 1. Why Build From Scratch (No PyTorch/TensorFlow)

**Beginner recap:** Frameworks like PyTorch exist so you *don't* have to do this in production. But
if you only ever call `nn.Linear` and `.backward()`, several things stay permanently mysterious:
why does a bad weight init blow up training, why does LoRA only need 2 small matrices, why does
GPT mask attention the way it does. Implementing it once from scratch removes that mystery for good.

### What you gain from doing this once

```
1. Debugging superpowers — when a real PyTorch model's loss goes to NaN, you'll know EXACTLY
   which of ~5 usual suspects to check (bad init, no grad clipping, exploding softmax, wrong
   masking, learning rate) because you've hit all 5 yourself while building this.

2. Reading papers becomes tractable — a paper's "Section 3: Method" is just forward-pass math.
   If you've implemented forward+backward for attention once, a new paper's new attention
   variant is a 20-line diff you can reason about, not a black box.

3. You understand WHY fine-tuning techniques work — LoRA is not magic once you've implemented
   the base Linear layer's backward pass and can see exactly which gradients get replaced by
   a low-rank version.

4. Interview differentiation — "explain backprop through attention" or "why does LoRA freeze
   the base weights" are common staff/research-track interview questions where "I called
   .backward()" is not an acceptable answer.
```

### Scope and honesty about limitations

```
This implementation prioritizes CLARITY over speed. It will not train billion-parameter models —
it trains tiny models (thousands to low-millions of parameters) on tiny datasets, on CPU, in
seconds to minutes. The architecture and math are IDENTICAL to production systems (GPT-2/GPT-3
use literally the same equations you'll write below) — only the scale and the engineering
(GPU kernels, mixed precision, distributed training) differ. Once you understand this, reading
production code (e.g. nanoGPT, Hugging Face `transformers`) becomes far easier because you
recognize every operation.
```

---

## 2. Autograd Engine From Scratch — The Core of Every Framework

**Beginner recap:** An "autograd engine" is the thing that watches every math operation you do
(`a + b`, `a @ b`, `relu(a)`) and remembers how to compute the derivative of each one, so that
later it can automatically apply the chain rule backward through the whole computation, no matter
how deep. This is the ONE piece of infrastructure that everything else in this document sits on top
of — build it once, correctly, and every later section (MLP, CNN, RNN, Transformer, GPT, LoRA)
becomes "just define the forward pass" because backward comes for free.

### 2.1 The Core Idea: A Computation Graph

```
Every operation creates a new Tensor that remembers:
  - its data (the actual numbers, a NumPy array)
  - its "parents" (which Tensors it was computed FROM)
  - a local "_backward" function: given the gradient of the LOSS w.r.t. THIS tensor's output,
    compute the gradient of the loss w.r.t. each of its parents (this is just the chain rule
    applied to ONE operation, e.g. d(a*b)/da = b).

To get gradients for the whole graph, you:
  1. Topologically sort all tensors reachable from the loss (children before parents in the
     forward direction → so parents come AFTER children when we reverse it for backward).
  2. Set the loss tensor's own gradient to 1 (d(loss)/d(loss) = 1).
  3. Walk the sorted list in REVERSE, calling each tensor's `_backward()`, which ACCUMULATES
     (+=, never =) gradient into its parents. Accumulation matters because a tensor can be
     used in more than one place (e.g. residual connections reuse `x` twice).
```

### 2.2 The `Tensor` Class

```python
"""
tensor.py — a minimal reverse-mode autodiff engine (NumPy-array valued, PyTorch-style API).
This is the ENTIRE "framework" this document uses. No torch, no tensorflow, only numpy.
"""
import numpy as np


class Tensor:
    def __init__(self, data, requires_grad=False, _children=(), _op=""):
        self.data = np.asarray(data, dtype=np.float64)
        self.requires_grad = requires_grad
        self.grad = np.zeros_like(self.data) if requires_grad else None
        self._backward = lambda: None
        self._prev = set(_children)
        self._op = _op

    # ---- utilities ------------------------------------------------------
    @property
    def shape(self):
        return self.data.shape

    def __repr__(self):
        return f"Tensor(shape={self.shape}, op={self._op or 'leaf'})"

    def zero_grad(self):
        if self.requires_grad:
            self.grad = np.zeros_like(self.data)

    def _ensure_grad(self):
        if self.grad is None:
            self.grad = np.zeros_like(self.data)

    @staticmethod
    def _unbroadcast(grad, shape):
        """Undo NumPy broadcasting: sum gradient back down to the original (pre-broadcast) shape."""
        while grad.ndim > len(shape):
            grad = grad.sum(axis=0)
        for axis, dim in enumerate(shape):
            if dim == 1 and grad.shape[axis] != 1:
                grad = grad.sum(axis=axis, keepdims=True)
        return grad

    def _wrap(self, other):
        return other if isinstance(other, Tensor) else Tensor(other)

    # ---- elementwise ops --------------------------------------------------
    def __add__(self, other):
        other = self._wrap(other)
        out = Tensor(self.data + other.data, self.requires_grad or other.requires_grad,
                     (self, other), "+")

        def _backward():
            if self.requires_grad:
                self._ensure_grad()
                self.grad += Tensor._unbroadcast(out.grad, self.data.shape)
            if other.requires_grad:
                other._ensure_grad()
                other.grad += Tensor._unbroadcast(out.grad, other.data.shape)
        out._backward = _backward
        return out

    def __mul__(self, other):
        other = self._wrap(other)
        out = Tensor(self.data * other.data, self.requires_grad or other.requires_grad,
                     (self, other), "*")

        def _backward():
            if self.requires_grad:
                self._ensure_grad()
                self.grad += Tensor._unbroadcast(out.grad * other.data, self.data.shape)
            if other.requires_grad:
                other._ensure_grad()
                other.grad += Tensor._unbroadcast(out.grad * self.data, other.data.shape)
        out._backward = _backward
        return out

    def __pow__(self, power):
        out = Tensor(self.data ** power, self.requires_grad, (self,), f"**{power}")

        def _backward():
            if self.requires_grad:
                self._ensure_grad()
                self.grad += (power * self.data ** (power - 1)) * out.grad
        out._backward = _backward
        return out

    def __neg__(self):
        return self * -1.0

    def __sub__(self, other):
        return self + (self._wrap(other) * -1.0)

    def __truediv__(self, other):
        return self * self._wrap(other) ** -1.0

    def __radd__(self, other):
        return self + other

    def __rmul__(self, other):
        return self * other

    def __rsub__(self, other):
        return self._wrap(other) - self

    # ---- matrix / reduction ops --------------------------------------------
    def matmul(self, other):
        other = self._wrap(other)
        out = Tensor(self.data @ other.data, self.requires_grad or other.requires_grad,
                     (self, other), "@")

        def _backward():
            if self.requires_grad:
                self._ensure_grad()
                grad = out.grad @ np.swapaxes(other.data, -1, -2)
                self.grad += Tensor._unbroadcast(grad, self.data.shape)
            if other.requires_grad:
                other._ensure_grad()
                grad = np.swapaxes(self.data, -1, -2) @ out.grad
                other.grad += Tensor._unbroadcast(grad, other.data.shape)
        out._backward = _backward
        return out

    __matmul__ = matmul

    def sum(self, axis=None, keepdims=False):
        out = Tensor(self.data.sum(axis=axis, keepdims=keepdims), self.requires_grad, (self,), "sum")

        def _backward():
            if self.requires_grad:
                self._ensure_grad()
                grad = out.grad
                if not keepdims and axis is not None:
                    grad = np.expand_dims(grad, axis)
                self.grad += np.broadcast_to(grad, self.data.shape)
        out._backward = _backward
        return out

    def mean(self, axis=None, keepdims=False):
        n = self.data.size if axis is None else self.data.shape[axis]
        return self.sum(axis=axis, keepdims=keepdims) * (1.0 / n)

    def transpose(self, *axes):
        axes = axes if axes else None
        out = Tensor(self.data.transpose(axes), self.requires_grad, (self,), "T")

        def _backward():
            if self.requires_grad:
                self._ensure_grad()
                inv = np.argsort(axes) if axes else None
                self.grad += out.grad.transpose(inv) if inv is not None else out.grad.T
        out._backward = _backward
        return out

    def reshape(self, *shape):
        out = Tensor(self.data.reshape(*shape), self.requires_grad, (self,), "reshape")

        def _backward():
            if self.requires_grad:
                self._ensure_grad()
                self.grad += out.grad.reshape(self.data.shape)
        out._backward = _backward
        return out

    def __getitem__(self, idx):
        out = Tensor(self.data[idx], self.requires_grad, (self,), "getitem")

        def _backward():
            if self.requires_grad:
                self._ensure_grad()
                np.add.at(self.grad, idx, out.grad)
        out._backward = _backward
        return out

    # ---- nonlinearities -----------------------------------------------------
    def relu(self):
        out = Tensor(np.maximum(0, self.data), self.requires_grad, (self,), "relu")

        def _backward():
            if self.requires_grad:
                self._ensure_grad()
                self.grad += (self.data > 0) * out.grad
        out._backward = _backward
        return out

    def exp(self):
        out = Tensor(np.exp(self.data), self.requires_grad, (self,), "exp")

        def _backward():
            if self.requires_grad:
                self._ensure_grad()
                self.grad += out.data * out.grad
        out._backward = _backward
        return out

    def log(self):
        out = Tensor(np.log(self.data + 1e-12), self.requires_grad, (self,), "log")

        def _backward():
            if self.requires_grad:
                self._ensure_grad()
                self.grad += out.grad / (self.data + 1e-12)
        out._backward = _backward
        return out

    def tanh(self):
        t = np.tanh(self.data)
        out = Tensor(t, self.requires_grad, (self,), "tanh")

        def _backward():
            if self.requires_grad:
                self._ensure_grad()
                self.grad += (1 - t * t) * out.grad
        out._backward = _backward
        return out

    def sigmoid(self):
        s = 1.0 / (1.0 + np.exp(-self.data))
        out = Tensor(s, self.requires_grad, (self,), "sigmoid")

        def _backward():
            if self.requires_grad:
                self._ensure_grad()
                self.grad += s * (1 - s) * out.grad
        out._backward = _backward
        return out

    def softmax(self, axis=-1):
        # Numerically-stable softmax: subtract the max before exponentiating.
        shifted = self.data - np.max(self.data, axis=axis, keepdims=True)
        exp = np.exp(shifted)
        probs = exp / np.sum(exp, axis=axis, keepdims=True)
        out = Tensor(probs, self.requires_grad, (self,), "softmax")

        def _backward():
            if self.requires_grad:
                self._ensure_grad()
                # d(softmax)/dx, applied via the Jacobian-vector product trick:
                # grad_x = probs * (grad_out - sum(grad_out * probs, axis, keepdims=True))
                dot = np.sum(out.grad * probs, axis=axis, keepdims=True)
                self.grad += probs * (out.grad - dot)
        out._backward = _backward
        return out

    # ---- the actual backward pass ------------------------------------------
    def backward(self):
        topo, visited = [], set()

        def build(node):
            if node not in visited:
                visited.add(node)
                for parent in node._prev:
                    build(parent)
                topo.append(node)
        build(self)

        self._ensure_grad()
        self.grad = np.ones_like(self.data)
        for node in reversed(topo):
            node._backward()
```

**What this gives you:** write `y = (x @ w).relu().sum()`, call `y.backward()`, and `x.grad` /
`w.grad` are populated correctly — with *zero* manually-written backward math for that expression.
Every architecture below (MLP, attention, GPT) is built by composing these primitives; you never
write a `d/dx` formula for the *model*, only (once) for each primitive operation above.

---

## 3. Building Blocks: Linear, Activations, Losses

**Beginner recap:** A "layer" in a framework is just a small Python object that holds some learnable
weight `Tensor`s and defines a `forward(x)` method using the primitives from Section 2. Because those
primitives already know how to backprop themselves, the layer gets backprop for free.

### 3.1 Parameter Initialization

```python
def he_init(fan_in, fan_out):
    """He/Kaiming init — good default for ReLU networks. Keeps activation variance ~constant
    across layers, which is the difference between a network that trains and one whose
    activations explode/vanish within the first few layers."""
    std = np.sqrt(2.0 / fan_in)
    return Tensor(np.random.randn(fan_in, fan_out) * std, requires_grad=True)


def xavier_init(fan_in, fan_out):
    """Xavier/Glorot init — good default for tanh/sigmoid networks."""
    limit = np.sqrt(6.0 / (fan_in + fan_out))
    return Tensor(np.random.uniform(-limit, limit, (fan_in, fan_out)), requires_grad=True)
```

**Why init matters (paper-level detail):** with `n` layers and a naive `std=1` init, activation
variance multiplies by roughly `fan_in` at every layer → after 10 layers your activations are
either `1e20` (explode → NaN) or `1e-20` (vanish → dead gradients). He/Xavier init is *derived*
by solving "what scale keeps `Var(output) ≈ Var(input))` for a given activation function.

### 3.2 The `Linear` Layer

```python
class Linear:
    """y = x @ W + b — the single most-used building block in all of deep learning."""

    def __init__(self, in_features, out_features, bias=True):
        self.W = he_init(in_features, out_features)
        self.b = Tensor(np.zeros(out_features), requires_grad=True) if bias else None

    def __call__(self, x):
        out = x @ self.W
        if self.b is not None:
            out = out + self.b
        return out

    def parameters(self):
        return [self.W] + ([self.b] if self.b is not None else [])
```

### 3.3 Loss Functions

```python
def mse_loss(pred, target):
    """Mean Squared Error — for regression."""
    target = pred._wrap(target)
    diff = pred - target
    return (diff * diff).mean()


def cross_entropy_loss(logits, targets):
    """
    Softmax + Negative Log-Likelihood, fused for numerical stability — for classification /
    next-token prediction (the loss EVERY language model, including GPT, is trained with).

    logits:  Tensor of shape (batch, num_classes) — raw, un-normalized scores
    targets: integer NumPy array of shape (batch,) — the correct class index per example
    """
    batch = logits.shape[0]
    # log-sum-exp trick, computed manually (not via .softmax()) so we can fuse log+softmax
    # into one numerically stable expression, exactly like PyTorch's F.cross_entropy does.
    shifted = logits.data - np.max(logits.data, axis=-1, keepdims=True)
    log_probs = shifted - np.log(np.sum(np.exp(shifted), axis=-1, keepdims=True))
    nll = -log_probs[np.arange(batch), targets]
    loss_value = nll.mean()

    out = Tensor(loss_value, logits.requires_grad, (logits,), "cross_entropy")

    def _backward():
        if logits.requires_grad:
            logits._ensure_grad()
            probs = np.exp(log_probs)                 # softmax probabilities
            grad = probs.copy()
            grad[np.arange(batch), targets] -= 1.0     # d(CE)/d(logits) = softmax(logits) - one_hot(target)
            grad /= batch
            logits.grad += grad * out.grad
    out._backward = _backward
    return out
```

**Paper-level derivation of `softmax + NLL` gradient:** for a single example with logits `z`,
target class `t`, `L = -log(softmax(z)_t)`. The derivative works out to the remarkably clean
`∂L/∂z_i = softmax(z)_i - 1[i == t]` — i.e. "probability you predicted, minus 1 for the correct
class, 0 elsewhere." This is why the fused implementation above is preferred over composing
`.softmax().log()` manually — it's both more numerically stable AND matches this clean closed form.

---

## 4. Backpropagation Derived From First Principles

**Beginner recap:** This section derives, by hand, the backward pass for a single `Linear → ReLU`
layer — the exact math the autograd engine in Section 2 is automating. Do this derivation once on
paper and every later "backward" in this document (attention, LoRA, etc.) is the same technique
applied to a different forward formula.

### 4.1 Setup

```
Forward:   z = xW + b            (x: 1×n,  W: n×m,  b: 1×m,  z: 1×m)
           a = relu(z)
           L = loss(a)           (some scalar loss further downstream)

We are GIVEN (from the layer above, via the chain rule already applied there):
           δ = ∂L/∂a             (shape 1×m — "how much does the loss change per unit of a")

We WANT:
           ∂L/∂W   (to update W)
           ∂L/∂b   (to update b)
           ∂L/∂x   (to keep propagating backward into earlier layers)
```

### 4.2 Step 1 — Through the ReLU

```
a_i = relu(z_i) = max(0, z_i)
∂a_i/∂z_i = 1 if z_i > 0 else 0

By the chain rule:  ∂L/∂z_i = ∂L/∂a_i · ∂a_i/∂z_i = δ_i · 1[z_i > 0]

So:  dz = δ * (z > 0)     (elementwise multiply — exactly what Tensor.relu()'s _backward does)
```

### 4.3 Step 2 — Through the Linear layer

```
z_j = Σ_i x_i W_ij + b_j

∂z_j/∂W_ij = x_i        →  ∂L/∂W_ij = dz_j · x_i         →  dW = xᵀ @ dz   (outer product)
∂z_j/∂b_j  = 1           →  ∂L/∂b_j  = dz_j                →  db = dz
∂z_j/∂x_i  = W_ij        →  ∂L/∂x_i  = Σ_j dz_j · W_ij     →  dx = dz @ Wᵀ
```

### 4.4 The Result, as Code (what `Linear.backward` would look like if written by hand)

```python
def linear_relu_forward(x, W, b):
    z = x @ W + b
    a = np.maximum(0, z)
    cache = (x, W, z)
    return a, cache


def linear_relu_backward(d_out, cache):
    """d_out = dL/da, coming from the next layer. Returns dL/dx, dL/dW, dL/db."""
    x, W, z = cache
    dz = d_out * (z > 0)          # step 1: through ReLU
    dW = x.T @ dz                 # step 2: through Linear
    db = dz.sum(axis=0)
    dx = dz @ W.T
    return dx, dW, db
```

Compare this by-hand version to what `Tensor.relu()` and `Linear.__call__` do inside the autograd
engine — they are *identical formulas*, just applied automatically instead of by hand. This is the
entire trick behind every autodiff framework that has ever existed.

### 4.5 Why This Generalizes: The Chain Rule Never Changes, Only the Local Derivative Does

```
For ANY operation y = f(x), backprop needs exactly one thing: the LOCAL derivative ∂y/∂x
(a Jacobian, or Jacobian-vector product for efficiency). Then:

           ∂L/∂x = ∂L/∂y · ∂y/∂x           (chain rule, always this shape)

Section 10 will do EXACTLY this derivation for softmax(QKᵀ/√d)V (attention) — same technique,
more terms. There is no "new kind of math" required to understand Transformer backprop beyond
what you just did for Linear+ReLU.
```

---

## 5. Building & Training a Multi-Layer Perceptron From Scratch

**Beginner recap:** An MLP ("multi-layer perceptron") is just `Linear → activation → Linear →
activation → ... → Linear`, stacked. We use the `Tensor`/`Linear` primitives from Sections 2-3, so
the *only* new code is "stack layers, loop over data, call `.backward()`, update weights."

### 5.1 The Model

```python
class MLP:
    def __init__(self, layer_sizes):
        self.layers = [Linear(layer_sizes[i], layer_sizes[i + 1])
                       for i in range(len(layer_sizes) - 1)]

    def __call__(self, x):
        for i, layer in enumerate(self.layers):
            x = layer(x)
            if i < len(self.layers) - 1:      # no activation on the final (output) layer
                x = x.relu()
        return x

    def parameters(self):
        return [p for layer in self.layers for p in layer.parameters()]
```

### 5.2 Training Loop on XOR (the "hello world" of proving backprop actually works)

XOR is famously **not linearly separable** — a single-layer perceptron provably cannot solve it
(this is the exact 1969 Minsky/Papert result that stalled neural network research for a decade).
An MLP with a hidden layer can, which makes it the perfect from-scratch sanity check.

```python
import numpy as np

X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=np.float64)
Y = np.array([[0], [1], [1], [0]], dtype=np.float64)   # XOR truth table

model = MLP([2, 8, 1])
lr = 0.1

for epoch in range(2000):
    x = Tensor(X)
    y_true = Tensor(Y)

    y_pred = model(x).sigmoid()
    loss = ((y_pred - y_true) ** 2).mean()          # MSE on probabilities

    for p in model.parameters():
        p.zero_grad()
    loss.backward()

    for p in model.parameters():
        p.data -= lr * p.grad                        # plain gradient descent (Section 6 improves this)

    if epoch % 400 == 0:
        print(f"epoch {epoch:4d}  loss {loss.data:.4f}")

print("predictions:", model(Tensor(X)).sigmoid().data.round(2).flatten())
# → converges to ~[0, 1, 1, 0], matching the XOR table
```

**What to notice:** nothing here mentions gradients explicitly except `loss.backward()` and
`p.grad` — every derivative (through sigmoid, MSE, both Linear layers) is produced automatically
by the engine from Section 2. This is the payoff of building the autograd engine first.

---

## 6. Optimizers From Scratch (SGD, Momentum, Adam)

**Beginner recap:** "Optimizer" = the rule for turning `p.grad` into a weight update. Plain SGD
(`p -= lr * p.grad`) works but is slow and sensitive to learning rate; Adam (used to train
essentially every modern LLM) adapts the step size per-parameter using running averages of the
gradient and its square.

### 6.1 SGD with Momentum

```python
class SGD:
    """v = momentum * v - lr * grad ; p += v
    Momentum smooths out noisy gradients by remembering a running direction, like a ball
    rolling downhill picking up speed instead of a random walk."""

    def __init__(self, parameters, lr=0.01, momentum=0.9):
        self.params = list(parameters)
        self.lr = lr
        self.momentum = momentum
        self.velocity = [np.zeros_like(p.data) for p in self.params]

    def step(self):
        for p, v in zip(self.params, self.velocity):
            v[:] = self.momentum * v - self.lr * p.grad
            p.data += v

    def zero_grad(self):
        for p in self.params:
            p.zero_grad()
```

### 6.2 Adam — Derived Term by Term

```
Adam maintains, per parameter, two running averages of the gradient:

  m_t = β1 · m_{t-1} + (1-β1) · g_t          (first moment  ≈ mean of recent gradients)
  v_t = β2 · v_{t-1} + (1-β2) · g_t²          (second moment ≈ variance of recent gradients)

Both start at 0, which biases them toward 0 early in training, so Adam BIAS-CORRECTS:

  m̂_t = m_t / (1 - β1^t)
  v̂_t = v_t / (1 - β2^t)

Then updates:

  p ← p - lr · m̂_t / (√v̂_t + ε)

Intuition: divide the step by √(recent gradient variance) → parameters with noisy/large
gradients get SMALLER effective steps, parameters with small/consistent gradients get
RELATIVELY larger steps. This is why Adam needs much less learning-rate tuning than plain SGD,
and it's the default optimizer for training/fine-tuning virtually every Transformer.
```

```python
class Adam:
    def __init__(self, parameters, lr=1e-3, betas=(0.9, 0.999), eps=1e-8):
        self.params = list(parameters)
        self.lr, self.b1, self.b2, self.eps = lr, betas[0], betas[1], eps
        self.m = [np.zeros_like(p.data) for p in self.params]
        self.v = [np.zeros_like(p.data) for p in self.params]
        self.t = 0

    def step(self):
        self.t += 1
        for p, m, v in zip(self.params, self.m, self.v):
            g = p.grad
            m[:] = self.b1 * m + (1 - self.b1) * g
            v[:] = self.b2 * v + (1 - self.b2) * (g * g)
            m_hat = m / (1 - self.b1 ** self.t)
            v_hat = v / (1 - self.b2 ** self.t)
            p.data -= self.lr * m_hat / (np.sqrt(v_hat) + self.eps)

    def zero_grad(self):
        for p in self.params:
            p.zero_grad()
```

### 6.3 Gradient Clipping (essential once you get to RNNs/Transformers)

```python
def clip_grad_norm(parameters, max_norm=1.0):
    """Rescale ALL gradients together so their combined L2 norm <= max_norm.
    Prevents a single exploding gradient (common in RNNs, and early in Transformer training)
    from wrecking every parameter's update in one step."""
    total_norm = np.sqrt(sum(np.sum(p.grad ** 2) for p in parameters if p.grad is not None))
    if total_norm > max_norm:
        scale = max_norm / (total_norm + 1e-6)
        for p in parameters:
            if p.grad is not None:
                p.grad *= scale
    return total_norm
```

---

## 7. Gradient Checking — Proving Your Backward Pass Is Correct

**Beginner recap:** When you hand-derive a backward pass (as you will for attention, LoRA, etc.),
how do you know it's actually right, and not just "runs without crashing"? Numerical gradient
checking: approximate the derivative directly from the DEFINITION of a derivative, and compare.
This is standard practice when implementing a paper's method with no reference code.

### 7.1 The Technique

```
Definition of a derivative:   f'(x) ≈ [f(x + ε) - f(x - ε)] / (2ε)     for tiny ε (e.g. 1e-5)

For a parameter p with analytic gradient g = ∂L/∂p (from your backward pass):
  1. Nudge p UP by ε, recompute the full forward loss  → L_plus
  2. Nudge p DOWN by ε, recompute the full forward loss → L_minus
  3. numerical_grad ≈ (L_plus - L_minus) / (2ε)
  4. Compare: relative_error = |g - numerical_grad| / (|g| + |numerical_grad| + 1e-8)

If relative_error < 1e-5 (roughly), your backward pass is correct. If it's ~1.0, something
in your backward math is wrong — this pinpoints WHICH tensor's gradient is broken, layer by layer.
```

### 7.2 Implementation

```python
def gradient_check(model_fn, params, eps=1e-5, tol=1e-5):
    """
    model_fn: a zero-arg function that runs forward + backward and returns the scalar loss
              Tensor (params must already have `.grad` populated by the time it's called once
              for the analytic check).
    params:   list of Tensors to check.
    """
    # 1. Analytic gradients (one forward+backward pass)
    for p in params:
        p.zero_grad()
    loss = model_fn()
    loss.backward()
    analytic = [p.grad.copy() for p in params]

    # 2. Numerical gradients (2 forward passes PER SCALAR — slow, only for small test models!)
    all_ok = True
    for p, g_analytic in zip(params, analytic):
        g_numeric = np.zeros_like(p.data)
        it = np.nditer(p.data, flags=["multi_index"])
        for _ in it:
            idx = it.multi_index
            orig = p.data[idx]

            p.data[idx] = orig + eps
            loss_plus = model_fn().data

            p.data[idx] = orig - eps
            loss_minus = model_fn().data

            p.data[idx] = orig  # restore
            g_numeric[idx] = (loss_plus - loss_minus) / (2 * eps)

        rel_error = np.abs(g_analytic - g_numeric) / (np.abs(g_analytic) + np.abs(g_numeric) + 1e-8)
        max_err = rel_error.max()
        status = "OK" if max_err < tol else "MISMATCH"
        print(f"  param shape={p.data.shape}  max_rel_error={max_err:.2e}  [{status}]")
        all_ok &= max_err < tol
    return all_ok


# Example: verify the MLP + cross-entropy backward pass end to end
model = MLP([4, 6, 3])
x_fixed = Tensor(np.random.randn(5, 4))
y_fixed = np.random.randint(0, 3, size=5)

def forward():
    return cross_entropy_loss(model(x_fixed), y_fixed)

gradient_check(forward, model.parameters())
```

**Practice used in real research code:** exactly this technique (often called a "grad check")
is how you validate a from-scratch implementation of a new paper's layer BEFORE trusting it enough
to spend hours training a real model with it. Silent backward-pass bugs are one of the most
time-wasting classes of bugs in deep learning because training can still "look like it's working"
(loss goes down) while converging to a worse-than-correct optimum.

---

## 8. Convolution From Scratch (im2col Forward/Backward)

**Beginner recap:** A convolution slides a small learnable filter over an image, computing a
dot-product at every position — this is how CNNs detect edges/textures/shapes regardless of
WHERE in the image they appear (translation invariance). Naive nested-loop convolution is
extremely slow in Python; the standard trick (used inside real frameworks too) is **im2col**:
reshape the sliding-window patches into a big matrix so the whole convolution becomes one matmul.

### 8.1 The im2col Trick

```
A convolution with kernel size k×k, over an input of shape (C_in, H, W), producing C_out output
channels, is mathematically identical to:
  1. Extract every k×k×C_in patch the kernel would slide over → stack them as ROWS of a matrix
     `cols` of shape (num_patches, k*k*C_in)
  2. Flatten the kernel weights to shape (k*k*C_in, C_out)
  3. output = cols @ weights_flat        → shape (num_patches, C_out), reshape to (C_out, H', W')

This turns convolution into "the same matmul primitive we already have autograd for" — no new
backward math needed if we implement im2col/col2im as plain NumPy index operations and let matmul
autograd (Section 2) handle the rest.
```

### 8.2 Implementation

```python
def im2col(x, kh, kw, stride=1, pad=0):
    """x: (N, C, H, W) numpy array → cols: (N, out_h*out_w, C*kh*kw)"""
    N, C, H, W = x.shape
    x_padded = np.pad(x, ((0, 0), (0, 0), (pad, pad), (pad, pad)))
    out_h = (H + 2 * pad - kh) // stride + 1
    out_w = (W + 2 * pad - kw) // stride + 1

    cols = np.zeros((N, out_h * out_w, C * kh * kw))
    idx = 0
    for i in range(out_h):
        for j in range(out_w):
            patch = x_padded[:, :, i * stride:i * stride + kh, j * stride:j * stride + kw]
            cols[:, idx, :] = patch.reshape(N, -1)
            idx += 1
    return cols, out_h, out_w


class Conv2D:
    """A convolution layer built on top of the Tensor autograd engine — forward is expressed
    purely as reshape + matmul, so backward is 100% free (Section 2 already handles it)."""

    def __init__(self, in_channels, out_channels, kernel_size, stride=1, padding=0):
        self.kh = self.kw = kernel_size
        self.stride, self.pad = stride, padding
        self.C_in, self.C_out = in_channels, out_channels
        fan_in = in_channels * kernel_size * kernel_size
        self.W = he_init(fan_in, out_channels)               # flattened kernel weights
        self.b = Tensor(np.zeros(out_channels), requires_grad=True)

    def __call__(self, x_tensor):
        N, C, H, W = x_tensor.shape
        cols, out_h, out_w = im2col(x_tensor.data, self.kh, self.kw, self.stride, self.pad)
        cols_t = Tensor(cols, requires_grad=x_tensor.requires_grad)

        # Manually wire cols_t's backward to scatter gradient back into x_tensor via col2im,
        # since im2col itself isn't (yet) a primitive of the engine — this is the ONE place
        # in this layer where we write backward math by hand (everything else reuses matmul).
        def _backward():
            if x_tensor.requires_grad:
                x_tensor._ensure_grad()
                x_tensor.grad += col2im(cols_t.grad, x_tensor.data.shape,
                                         self.kh, self.kw, self.stride, self.pad)
        cols_t._backward = _backward
        cols_t._prev = {x_tensor}
        cols_t.requires_grad = True

        out = cols_t.matmul(self.W) + self.b               # (N, out_h*out_w, C_out) via broadcasting
        out = out.transpose(0, 2, 1).reshape(N, self.C_out, out_h, out_w)
        return out

    def parameters(self):
        return [self.W, self.b]


def col2im(d_cols, x_shape, kh, kw, stride, pad):
    """Inverse of im2col: scatter-add gradient patches back to their original pixel locations."""
    N, C, H, W = x_shape
    H_p, W_p = H + 2 * pad, W + 2 * pad
    out_h = (H_p - kh) // stride + 1
    out_w = (W_p - kw) // stride + 1
    dx_padded = np.zeros((N, C, H_p, W_p))

    idx = 0
    for i in range(out_h):
        for j in range(out_w):
            patch_grad = d_cols[:, idx, :].reshape(N, C, kh, kw)
            dx_padded[:, :, i * stride:i * stride + kh, j * stride:j * stride + kw] += patch_grad
            idx += 1
    return dx_padded[:, :, pad:pad + H, pad:pad + W] if pad else dx_padded
```

**Key lesson for reading real framework internals:** even inside cuDNN/PyTorch, convolution is
frequently lowered to matmul-like operations (im2col, Winograd, FFT-based methods) for exactly this
reason — matmul is the most heavily hardware-optimized primitive that exists (GPUs are literally
matmul machines), so every architecture eventually gets expressed in terms of it where possible.

---

## 9. RNN & LSTM Cells From Scratch

**Beginner recap:** Before Transformers, sequences (text, time series) were processed by RNNs:
a small network applied at every timestep that carries a "hidden state" forward as memory. Worth
building once because (a) it clarifies exactly what problem attention solves, and (b) it's the
simplest possible from-scratch example of backprop THROUGH TIME (a recurrent computation graph).

### 9.1 Vanilla RNN Cell

```
h_t = tanh(x_t @ Wx + h_{t-1} @ Wh + b)

This is applied at every timestep, REUSING the same Wx, Wh, b — this weight sharing across time
is why RNNs generalize to sequences of any length. Because h_t depends on h_{t-1}, which depends
on h_{t-2}, ..., the computation graph is a CHAIN across all T timesteps — backprop through it is
called "Backpropagation Through Time" (BPTT), and it's just the SAME chain rule, applied T times
in a row instead of once.
```

```python
class RNNCell:
    def __init__(self, input_size, hidden_size):
        self.Wx = xavier_init(input_size, hidden_size)
        self.Wh = xavier_init(hidden_size, hidden_size)
        self.b = Tensor(np.zeros(hidden_size), requires_grad=True)

    def __call__(self, x_t, h_prev):
        return (x_t @ self.Wx + h_prev @ self.Wh + self.b).tanh()

    def parameters(self):
        return [self.Wx, self.Wh, self.b]


def run_rnn(cell, x_seq, h0):
    """x_seq: list of Tensors, each (batch, input_size). Returns list of hidden states.
    Because we reuse the SAME Tensor objects (cell.Wx etc.) at every step, and the autograd
    graph records every use as a separate node, calling .backward() at the end automatically
    ACCUMULATES gradients from every timestep into cell.Wx.grad — that's BPTT, for free."""
    h = h0
    hidden_states = []
    for x_t in x_seq:
        h = cell(x_t, h)
        hidden_states.append(h)
    return hidden_states
```

**Why RNNs vanish/explode (paper-level explanation):** `∂h_T/∂h_0` is a PRODUCT of T Jacobians
(one per timestep, roughly `~diag(1-tanh²) @ Wh` each). If the dominant eigenvalue of `Wh` is
`< 1`, the product shrinks toward 0 exponentially in T (vanishing gradients — can't learn
long-range dependencies). If `> 1`, it grows exponentially (exploding gradients — NaN losses).
This single fact is WHY LSTMs were invented, and later, why Transformers (Section 10) replaced
RNNs almost entirely for long sequences — self-attention has an O(1)-hop path between any two
timesteps, not a T-hop chain.

### 9.2 LSTM Cell — Gates Solve the Vanishing Gradient Problem

```
LSTM adds a separate "cell state" c_t that information can flow through almost UNCHANGED
(via an additive update, not a repeated matmul+tanh), controlled by three learned gates:

  f_t = σ(x_t Wxf + h_{t-1} Whf + bf)      forget gate  — what to erase from memory
  i_t = σ(x_t Wxi + h_{t-1} Whi + bi)      input gate   — what new info to write
  g_t = tanh(x_t Wxg + h_{t-1} Whg + bg)   candidate    — the new info itself
  o_t = σ(x_t Wxo + h_{t-1} Who + bo)      output gate  — what to expose as the hidden state

  c_t = f_t * c_{t-1} + i_t * g_t          ← ADDITIVE update: gradient can flow through this
                                              sum with NO repeated matrix multiply, avoiding
                                              the vanishing-gradient product-of-Jacobians problem
  h_t = o_t * tanh(c_t)
```

```python
class LSTMCell:
    def __init__(self, input_size, hidden_size):
        self.hidden_size = hidden_size
        z = input_size + hidden_size
        # Combine [x_t, h_{t-1}] into one matmul per gate for compactness.
        self.Wf = xavier_init(z, hidden_size); self.bf = Tensor(np.ones(hidden_size), requires_grad=True)
        self.Wi = xavier_init(z, hidden_size); self.bi = Tensor(np.zeros(hidden_size), requires_grad=True)
        self.Wg = xavier_init(z, hidden_size); self.bg = Tensor(np.zeros(hidden_size), requires_grad=True)
        self.Wo = xavier_init(z, hidden_size); self.bo = Tensor(np.zeros(hidden_size), requires_grad=True)
        # bf initialized to 1.0: a well-known trick (Jozefowicz et al. 2015) so the forget gate
        # starts near "remember everything," which trains much more reliably than starting near 0.

    def __call__(self, x_t, state):
        h_prev, c_prev = state
        z = concat_last_dim(x_t, h_prev)          # (batch, input_size + hidden_size)

        f = (z @ self.Wf + self.bf).sigmoid()
        i = (z @ self.Wi + self.bi).sigmoid()
        g = (z @ self.Wg + self.bg).tanh()
        o = (z @ self.Wo + self.bo).sigmoid()

        c_t = f * c_prev + i * g
        h_t = o * c_t.tanh()
        return h_t, c_t

    def parameters(self):
        return [self.Wf, self.bf, self.Wi, self.bi, self.Wg, self.bg, self.Wo, self.bo]


def concat_last_dim(a, b):
    """Concatenate two Tensors along the last axis, with correct backward (split the
    incoming gradient back into the two original slices)."""
    out_data = np.concatenate([a.data, b.data], axis=-1)
    out = Tensor(out_data, a.requires_grad or b.requires_grad, (a, b), "concat")
    split = a.data.shape[-1]

    def _backward():
        if a.requires_grad:
            a._ensure_grad()
            a.grad += out.grad[..., :split]
        if b.requires_grad:
            b._ensure_grad()
            b.grad += out.grad[..., split:]
    out._backward = _backward
    return out
```

---

## 10. Self-Attention From Scratch: Math + Backward Derivation

**Beginner recap:** Self-attention lets every position in a sequence directly look at every other
position and decide "how relevant is that position to me right now" — no T-step recurrent chain
(Section 9) required. This is THE mechanism that makes Transformers (and therefore GPT, BERT,
every modern LLM) work. Because we already have a general-purpose autograd engine (Section 2),
we technically don't NEED to hand-derive the backward pass — but doing it once, on paper, is
exactly what you'd do to understand (or reproduce) the "Attention Is All You Need" paper, so we do
it here for completeness before writing the from-scratch code.

### 10.1 The Forward-Pass Formula

```
Given input X (seq_len × d_model), project it into three roles using learned weight matrices:

  Q = X Wq      (queries — "what am I looking for?")
  K = X Wk      (keys    — "what do I contain, for others to match against?")
  V = X Wv      (values  — "what do I actually offer, once matched?")

  scores = Q Kᵀ / √d_k              (seq_len × seq_len — similarity between every pair of tokens)
  scores = scores + mask            (causal mask: -inf above the diagonal, for decoder-only models)
  A      = softmax(scores, axis=-1) (attention WEIGHTS — rows sum to 1)
  output = A V                      (weighted average of values, weighted by relevance)
```

### 10.2 Backward Derivation (by hand, the way you'd derive it for a paper with no reference code)

```
We are given δ = ∂L/∂output (seq_len × d_v), and need ∂L/∂Q, ∂L/∂K, ∂L/∂V.

Step 1 — through "output = A @ V" (a plain matmul, same rule as Section 4):
    ∂L/∂A = δ @ Vᵀ
    ∂L/∂V = Aᵀ @ δ

Step 2 — through "A = softmax(scores)" (this is the tricky one — softmax mixes all elements
of a row together, so the Jacobian is NOT diagonal). For row i, using dA_i = ∂L/∂A_i:
    ∂L/∂scores_i = A_i * (dA_i - Σ_j(dA_i_j * A_i_j))
This is exactly the Jacobian-vector-product formula already implemented in Tensor.softmax()
in Section 2 — softmax's backward is subtle enough that hand-deriving it once (as we did back
in Section 2's docstring) is the standard way every framework's built-in softmax is validated.

Step 3 — through "scores = QKᵀ/√d_k" (matmul + scalar):
    ∂L/∂Q = (∂L/∂scores) @ K / √d_k
    ∂L/∂K = (∂L/∂scores)ᵀ @ Q / √d_k

Step 4 — through the input projections Q = XWq, K = XWk, V = XWv (plain Linear backward,
Section 4), each contributes to ∂L/∂X — SUM all three contributions since X was reused 3 times:
    ∂L/∂X = (∂L/∂Q) Wqᵀ + (∂L/∂K) Wkᵀ + (∂L/∂V) Wvᵀ
    ∂L/∂Wq = Xᵀ (∂L/∂Q),   ∂L/∂Wk = Xᵀ (∂L/∂K),   ∂L/∂Wv = Xᵀ (∂L/∂V)
```

**Why this matters even though the autograd engine derives it for you automatically:** this exact
derivation (steps 1-4) is what you'd need to write a custom fused/optimized attention kernel (e.g.
FlashAttention-style), or to debug NaN gradients in attention (usually traced to step 2 — softmax
gradients blowing up when `scores` isn't properly scaled by `√d_k`, which is precisely why that
scaling term exists in the first place — without it, large dot products push softmax into a
saturated regime with near-zero or exploding gradients).

### 10.3 From-Scratch Implementation (built on the Section 2 engine — backward is automatic)

```python
def causal_mask(seq_len):
    """Upper-triangular -inf mask so position i cannot attend to position j > i — this is what
    makes a Transformer a DECODER (autoregressive: can only see the past, never the future)."""
    mask = np.triu(np.ones((seq_len, seq_len)), k=1) * -1e9
    return Tensor(mask)


class SelfAttentionHead:
    def __init__(self, d_model, d_head):
        self.d_head = d_head
        self.Wq = xavier_init(d_model, d_head)
        self.Wk = xavier_init(d_model, d_head)
        self.Wv = xavier_init(d_model, d_head)
        # Optional LoRA adapters (Section 15.4 sets these post-hoc on a pretrained head).
        # Left as None here so the plain pretraining path (Section 12) is completely unaffected.
        self.Wq_lora = None
        self.Wv_lora = None

    def __call__(self, x, mask=None):
        # x: (batch, seq_len, d_model)
        # If a LoRA adapter has been attached (Section 15.4), route through it instead of the
        # raw frozen projection — this is the ONE line that actually makes LoRA "take effect"
        # at inference/training time; attaching the adapter object alone changes nothing unless
        # the forward pass is wired to use it, exactly like `requires_grad=False` alone doesn't
        # stop a stale optimizer parameter list from stepping a tensor (Section 19 pitfall #5).
        Q = self.Wq_lora(x) if self.Wq_lora is not None else x @ self.Wq
        K = x @ self.Wk
        V = self.Wv_lora(x) if self.Wv_lora is not None else x @ self.Wv

        scores = Q.matmul(K.transpose(0, 2, 1)) * (1.0 / np.sqrt(self.d_head))  # (batch, seq, seq)
        if mask is not None:
            scores = scores + mask
        attn = scores.softmax(axis=-1)
        return attn.matmul(V)                                                  # (batch, seq, d_head)

    def parameters(self):
        return [self.Wq, self.Wk, self.Wv]


class MultiHeadAttention:
    """Run several attention heads in parallel with SMALLER d_head each, then concatenate.
    Why multiple heads instead of one big head? Each head can specialize in a different kind
    of relationship (e.g. one head tracks syntax/adjacent words, another tracks long-range
    coreference) — empirically this outperforms one large single-head attention of equal
    total compute, and is one of the key architectural choices from the original paper."""

    def __init__(self, d_model, num_heads):
        assert d_model % num_heads == 0
        self.d_head = d_model // num_heads
        self.heads = [SelfAttentionHead(d_model, self.d_head) for _ in range(num_heads)]
        self.Wo = xavier_init(d_model, d_model)          # output projection mixes heads together

    def __call__(self, x, mask=None):
        head_outputs = [head(x, mask) for head in self.heads]     # list of (batch, seq, d_head)
        concat = head_outputs[0]
        for h in head_outputs[1:]:
            concat = concat_last_dim(concat, h)                    # (batch, seq, d_model)
        return concat @ self.Wo

    def parameters(self):
        params = [self.Wo]
        for head in self.heads:
            params += head.parameters()
        return params
```

---

## 11. Building a GPT-Style Decoder-Only Transformer From Scratch

**Beginner recap:** GPT (and every modern chat LLM) is a **decoder-only** Transformer: it's just
`MultiHeadAttention` (Section 10, with the causal mask so it can't see the future) plus a small
per-position MLP, stacked N times, with residual connections and normalization holding it
together, followed by one final projection back to vocabulary-sized logits. There is no encoder,
no cross-attention — the entire model reused for both "understanding" and "generating" is the
same stack of causal self-attention blocks.

### 11.1 LayerNorm From Scratch

```python
class LayerNorm:
    """Normalize each token's feature vector to mean 0 / variance 1, then apply a learned
    scale (gamma) and shift (beta). Stabilizes training by keeping activation scale consistent
    across layers — without it, deep Transformer stacks are very difficult to train."""

    def __init__(self, dim, eps=1e-5):
        self.eps = eps
        self.gamma = Tensor(np.ones(dim), requires_grad=True)
        self.beta = Tensor(np.zeros(dim), requires_grad=True)

    def __call__(self, x):
        mean = x.mean(axis=-1, keepdims=True)
        # Var(x) = E[(x-mean)^2] — expressed with primitives we already have, so backward is free
        diff = x - mean
        var = (diff * diff).mean(axis=-1, keepdims=True)
        std_inv = (var + self.eps) ** -0.5
        normalized = diff * std_inv
        return normalized * self.gamma + self.beta

    def parameters(self):
        return [self.gamma, self.beta]
```

### 11.2 The Feed-Forward (Position-Wise MLP) Block

```python
class FeedForward:
    """Applied independently to each token/position (hence 'position-wise'). Standard GPT
    design expands the dimension 4x in the hidden layer — thought of as a per-token
    key-value memory lookup: the first Linear 'queries' a large bank of learned patterns via
    ReLU/GELU activation, the second Linear combines the results back down to d_model."""

    def __init__(self, d_model, d_ff=None):
        d_ff = d_ff or 4 * d_model
        self.fc1 = Linear(d_model, d_ff)
        self.fc2 = Linear(d_ff, d_model)

    def __call__(self, x):
        return self.fc2(self.fc1(x).relu())

    def parameters(self):
        return self.fc1.parameters() + self.fc2.parameters()
```

### 11.3 The Decoder Block: Attention + FFN + Residuals + Pre-LayerNorm

```python
class DecoderBlock:
    """
    Pre-LN residual design (the modern default, used by GPT-2 onward — more stable to train
    than the original 2017 paper's Post-LN design because gradients have a clean, unimpeded
    residual path all the way from the output back to the input embeddings):

        x = x + MultiHeadAttention(LayerNorm(x))     # attention sub-layer, residual around it
        x = x + FeedForward(LayerNorm(x))             # FFN sub-layer, residual around it
    """

    def __init__(self, d_model, num_heads):
        self.ln1 = LayerNorm(d_model)
        self.attn = MultiHeadAttention(d_model, num_heads)
        self.ln2 = LayerNorm(d_model)
        self.ffn = FeedForward(d_model)

    def __call__(self, x, mask):
        x = x + self.attn(self.ln1(x), mask)
        x = x + self.ffn(self.ln2(x))
        return x

    def parameters(self):
        return (self.ln1.parameters() + self.attn.parameters()
                + self.ln2.parameters() + self.ffn.parameters())
```

### 11.4 Token + Positional Embeddings

```python
class Embedding:
    """A lookup table: row i of the weight matrix IS the vector for token id i. Backward
    (via Tensor.__getitem__ from Section 2, which uses np.add.at) correctly accumulates
    gradient into a row every time that token appears anywhere in the batch."""

    def __init__(self, vocab_size, d_model):
        self.weight = Tensor(np.random.randn(vocab_size, d_model) * 0.02, requires_grad=True)

    def __call__(self, token_ids):
        return self.weight[token_ids]         # fancy indexing → (batch, seq_len, d_model)

    def parameters(self):
        return [self.weight]
```

### 11.5 The Full GPT Model

```python
class GPT:
    def __init__(self, vocab_size, d_model=64, num_heads=4, num_layers=4, max_seq_len=128):
        self.token_emb = Embedding(vocab_size, d_model)
        self.pos_emb = Embedding(max_seq_len, d_model)
        self.blocks = [DecoderBlock(d_model, num_heads) for _ in range(num_layers)]
        self.ln_f = LayerNorm(d_model)
        self.head = Linear(d_model, vocab_size, bias=False)
        self.max_seq_len = max_seq_len

    def __call__(self, token_ids):
        # token_ids: (batch, seq_len) integer numpy array
        batch, seq_len = token_ids.shape
        positions = np.tile(np.arange(seq_len), (batch, 1))

        x = self.token_emb(token_ids) + self.pos_emb(positions)
        mask = causal_mask(seq_len)
        for block in self.blocks:
            x = block(x, mask)
        x = self.ln_f(x)
        logits = self.head(x)                 # (batch, seq_len, vocab_size)
        return logits

    def parameters(self):
        params = self.token_emb.parameters() + self.pos_emb.parameters()
        for block in self.blocks:
            params += block.parameters()
        params += self.ln_f.parameters() + self.head.parameters()
        return params
```

**Parameter count sanity check (paper-level bookkeeping):** for `d_model=64, num_heads=4,
num_layers=4, vocab_size=65` (a tiny char-level model), parameters ≈
`vocab*d_model*2 (tied-ish embeddings) + num_layers*(4*d_model² (attention Q/K/V/O) + 8*d_model²
(FFN, 4x expansion in+out))` — roughly 200K parameters. GPT-2-small scales the *exact same
formula* up to `d_model=768, num_heads=12, num_layers=12, vocab_size=50257` → ~124M parameters.
Nothing architecturally changes between your from-scratch toy and real GPT-2 — only the sizes.

---

## 12. Training a Tiny GPT From Scratch (Character-Level LM)

**Beginner recap:** "Pretraining" a language model means: take a big pile of text, and repeatedly
ask the model "given these tokens so far, predict the next one" — that's it. No labels needed
beyond the text itself (this is why it's called *self-supervised*). We'll do this at the
character level on a small text so it trains on CPU in seconds, but the training LOOP is
identical to what pretrains GPT-3/GPT-4-scale models.

### 12.1 Data Prep: Text → Integer Tokens

```python
text = "hello world, this is a tiny character level language model. " * 50

chars = sorted(set(text))
stoi = {ch: i for i, ch in enumerate(chars)}
itos = {i: ch for ch, i in stoi.items()}
vocab_size = len(chars)

data = np.array([stoi[c] for c in text])


def get_batch(data, batch_size, seq_len):
    """Sample random (input, target) windows. target is input SHIFTED by one position —
    this shift IS the 'next token prediction' objective in code form."""
    start_idxs = np.random.randint(0, len(data) - seq_len - 1, size=batch_size)
    x = np.stack([data[i:i + seq_len] for i in start_idxs])
    y = np.stack([data[i + 1:i + seq_len + 1] for i in start_idxs])
    return x, y
```

### 12.2 The Training Loop

```python
model = GPT(vocab_size=vocab_size, d_model=64, num_heads=4, num_layers=4, max_seq_len=32)
optimizer = Adam(model.parameters(), lr=3e-3)

batch_size, seq_len = 16, 32

for step in range(500):
    xb, yb = get_batch(data, batch_size, seq_len)
    logits = model(xb)                                    # (batch, seq_len, vocab_size)

    # Flatten (batch, seq_len, vocab) → (batch*seq_len, vocab) so cross_entropy_loss (which
    # expects one target class per ROW) can be reused as-is — this reshape is exactly what
    # real frameworks' loss functions do internally for sequence models too.
    logits_flat = logits.reshape(batch_size * seq_len, vocab_size)
    targets_flat = yb.reshape(-1)
    loss = cross_entropy_loss(logits_flat, targets_flat)

    optimizer.zero_grad()
    loss.backward()
    clip_grad_norm(model.parameters(), max_norm=1.0)
    optimizer.step()

    if step % 50 == 0:
        print(f"step {step:4d}  loss {loss.data:.4f}")
```

### 12.3 Generation (Autoregressive Sampling)

```python
def generate(model, prompt_ids, max_new_tokens, temperature=1.0):
    """The SAME loop that runs behind every '...' typing effect you've seen from a chat LLM:
    predict next-token distribution → sample one token → append it → repeat, feeding the
    model's own output back in as input each time (hence 'autoregressive')."""
    ids = list(prompt_ids)
    for _ in range(max_new_tokens):
        context = np.array([ids[-model.max_seq_len:]])          # (1, seq_len)
        logits = model(context)                                  # (1, seq_len, vocab)
        last_logits = logits.data[0, -1] / temperature
        probs = np.exp(last_logits - last_logits.max())
        probs /= probs.sum()
        next_id = np.random.choice(len(probs), p=probs)
        ids.append(int(next_id))
    return ids


prompt = [stoi[c] for c in "hello"]
generated_ids = generate(model, prompt, max_new_tokens=40, temperature=0.8)
print("".join(itos[i] for i in generated_ids))
```

**What "pretraining" produced:** a model that has learned, purely from next-character statistics,
things like "after `'hel'` the next char is very likely `'l'`", "spaces follow words", etc. This
is the identical mechanism (scaled up ~a billion times in parameters and data) that gives large
LLMs their fluency — there is no separate "understanding module"; fluent, coherent generation
*emerges* from getting extremely good at next-token prediction over huge amounts of data.

---

## 13. Fine-Tuning — Core Concepts From First Principles

**Beginner recap:** "Fine-tuning" is not a different algorithm from "training" — it's the
*exact same* forward pass + backward pass + optimizer step loop from Sections 5/12, with two
things changed: (1) you **start from already-learned weights** instead of random init, and
(2) you train on a smaller, more specific dataset, usually for far fewer steps and with a
smaller learning rate. Everything you built in Sections 2-12 is reused as-is.

### 13.1 Why Fine-Tuning Works At All (the geometric intuition)

```
Pretraining (Section 12) walks the model's ~millions of weights to a point in weight-space that
is good at "predict the next token, in general, across a huge diverse corpus." That point already
encodes an enormous amount of structure: grammar, facts, reasoning patterns, formatting.

Fine-tuning does NOT relearn any of that from scratch. It takes a few more, SMALL gradient steps
FROM that point, guided by a narrower dataset — nudging the weights toward "predict the next
token well, specifically for THIS task/style/format," while (ideally) not destroying the general
knowledge already encoded nearby in weight-space. This is why fine-tuning needs orders of
magnitude less data and compute than pretraining: you're doing local fine-adjustment, not global
search.
```

### 13.2 The Central Risk: Catastrophic Forgetting

```
If the fine-tuning learning rate is too high, or you train too many steps/epochs, the weights
can move far enough from the pretrained point that the model "forgets" general capabilities it
had before fine-tuning (catastrophic forgetting) — e.g. a model fine-tuned hard on customer
support transcripts might get worse at basic arithmetic or general knowledge Q&A, purely because
its weights moved to a region of weight-space that's great for one narrow distribution but has
drifted away from the broader capabilities.

Mitigations you'll see in every fine-tuning paper/framework:
  - Small learning rate (often 10-100x smaller than pretraining LR)
  - Few epochs (often 1-3 passes over the fine-tuning set, not hundreds)
  - Parameter-efficient fine-tuning (Section 15) — freeze almost everything, so most of the
    pretrained "knowledge manifold" is PHYSICALLY unable to move
  - Mixing in some general-purpose data alongside the task-specific data
```

### 13.3 Three Levels of "How Much Do You Change the Model?"

```
1. FULL FINE-TUNING (Section 14)
   Every single weight is updated by gradient descent. Most expressive, most prone to
   forgetting, most expensive (needs full optimizer state — e.g. Adam needs 2x extra memory
   per parameter for its running averages — for EVERY parameter).

2. PARAMETER-EFFICIENT FINE-TUNING / PEFT, e.g. LoRA (Section 15)
   Freeze ~100% of the original weights. Add a small number of NEW trainable parameters
   (often <1% of the model's total) that modify the frozen weights' effective behavior.
   Cheap, fast, low forgetting risk, and — critically — the ORIGINAL weights are never
   touched, so you can literally keep multiple LoRA "skins" for one frozen base model.

3. PROMPT-BASED ADAPTATION (no weight updates at all)
   In-context learning / few-shot prompting changes the model's OUTPUT without changing
   ANY weights — not covered further here since it's not "training" in the gradient-descent
   sense, but worth knowing it exists as the "0th" rung on this ladder.
```

### 13.4 Decoder-Only Fine-Tuning, Specifically

```
Because GPT-style models (Section 11) are decoder-only, EVERY fine-tuning technique for them —
instruction tuning, chat fine-tuning, domain adaptation, LoRA — reduces to the SAME underlying
objective as pretraining: next-token cross-entropy loss, with causal masking. What changes
between "pretraining" and "instruction fine-tuning" a decoder is:

  1. WHAT data you feed it (Section 16.1): (prompt, response) pairs instead of raw text
  2. WHICH tokens you compute loss on (Section 16.2): usually only the RESPONSE tokens
     (loss masking) — you don't want to "reward" the model for reproducing the prompt itself
  3. HOW MANY parameters you actually update (full fine-tune vs LoRA vs freezing early layers)

The forward pass, the model class (GPT from Section 11), and the optimizer (Adam from Section 6)
are all reused UNCHANGED. This is the key insight that makes fine-tuning tractable to understand:
it's 90% the same code as pretraining.
```

---

## 14. Full Fine-Tuning From Scratch

**Beginner recap:** The simplest possible fine-tuning: load pretrained weights, keep every
parameter trainable, run the same training loop from Section 12 on new data with a smaller
learning rate. Demonstrated here by pretraining on one corpus, then full-fine-tuning the SAME
model on a different, narrower corpus.

### 14.1 Saving / Loading Pretrained Weights (your own tiny "checkpoint" format)

```python
import pickle

def save_checkpoint(model, path):
    """Real frameworks call this a '.pt' or '.safetensors' file; ours is just a pickled list
    of numpy arrays, in the same order model.parameters() returns them."""
    weights = [p.data.copy() for p in model.parameters()]
    with open(path, "wb") as f:
        pickle.dump(weights, f)


def load_checkpoint(model, path):
    with open(path, "rb") as f:
        weights = pickle.load(f)
    for p, w in zip(model.parameters(), weights):
        p.data[:] = w
```

### 14.2 Full Fine-Tuning Loop

```python
def full_finetune(model, finetune_data, steps=200, lr=5e-5, batch_size=8, seq_len=32):
    """Identical training loop to Section 12 — the ONLY differences from pretraining are:
    (1) model starts from pretrained weights (already loaded before this is called),
    (2) lr is much smaller (5e-5 vs 3e-3 used for pretraining from random init),
    (3) far fewer steps, since we're fine-adjusting, not learning from scratch."""
    optimizer = Adam(model.parameters(), lr=lr)

    for step in range(steps):
        xb, yb = get_batch(finetune_data, batch_size, seq_len)
        logits = model(xb)
        logits_flat = logits.reshape(batch_size * seq_len, logits.shape[-1])
        loss = cross_entropy_loss(logits_flat, yb.reshape(-1))

        optimizer.zero_grad()
        loss.backward()
        clip_grad_norm(model.parameters(), max_norm=1.0)
        optimizer.step()

        if step % 50 == 0:
            print(f"[full fine-tune] step {step:4d}  loss {loss.data:.4f}")
    return model


# --- demo: pretrain on generic text, then fully fine-tune on a narrow domain ---
# (using the `model`/`data` from Section 12 as the "pretrained" starting point)
save_checkpoint(model, "pretrained.pkl")

domain_text = "the quarterly revenue report shows strong growth in q3 2026. " * 50
domain_data = np.array([stoi.get(c, 0) for c in domain_text if c in stoi])

finetuned_model = GPT(vocab_size=vocab_size, d_model=64, num_heads=4, num_layers=4, max_seq_len=32)
load_checkpoint(finetuned_model, "pretrained.pkl")
full_finetune(finetuned_model, domain_data, steps=200, lr=5e-5)
```

**Cost accounting (why full fine-tuning is expensive at real scale):** Adam's optimizer state
(`m`, `v` from Section 6.2) doubles the memory needed for EVERY trainable parameter, on top of
the weights themselves and their gradients — roughly **4x the raw parameter memory** (weights +
grad + m + v) for full fine-tuning with Adam. For a 7B-parameter model in float32 that's ~112GB,
which is why full fine-tuning of large models needs multiple high-memory GPUs, and why
parameter-efficient methods (Section 15) exist.

---

## 15. Parameter-Efficient Fine-Tuning: LoRA From Scratch

**Beginner recap:** LoRA ("Low-Rank Adaptation," Hu et al. 2021) freezes a pretrained weight
matrix entirely and instead learns a small, *additive* correction to it, expressed as the
product of two much smaller matrices. This means you only ever compute gradients for those two
tiny matrices — the giant pretrained matrix is mathematically untouched (its `.grad` is simply
never computed), which is why LoRA fine-tuning uses a small fraction of full fine-tuning's memory.

### 15.1 The Core Idea, Precisely

```
A pretrained Linear layer computes:      h = x W          (W is d_in × d_out, FROZEN)

LoRA claims: the WEIGHT UPDATE needed to adapt W to a new task, ΔW, tends to have low
"intrinsic rank" — i.e. ΔW can be well-approximated as the product of two skinny matrices:

      ΔW ≈ B A          where  A is d_in × r,  B is r × d_out,  and r << min(d_in, d_out)

So the fine-tuned layer becomes:

      h = x W + x (B A) * (α / r)         (W is frozen; only A, B are trained)
        = x W + (x A) B * (α / r)          (compute right-to-left: cheaper, avoids ever
                                             materializing the full d_in × d_out matrix BA)

α (a fixed scaling constant, often set so α/r ≈ 1-2) controls how much the LoRA update
contributes relative to the frozen base output — a hyperparameter you tune once per task.

Trainable parameter count comparison, for a 1024×1024 weight matrix with rank r=8:
  Full fine-tune:  1024 * 1024        = 1,048,576 trainable parameters
  LoRA (r=8):      1024*8 + 8*1024    =    16,384 trainable parameters   (~64x fewer!)
```

### 15.2 Why Low Rank Is a Reasonable Assumption (paper-level intuition)

```
Empirically (this is the paper's central experimental finding, not something derivable from
first principles alone), the actual weight change needed to specialize a pretrained model to a
new but related task lives in a much lower-dimensional subspace than the full weight matrix.
Intuition: pretraining already learned the "hard," general-purpose structure; adapting to a
narrower downstream task is more like "rotating/scaling a few existing directions" than
"learning an entirely new function," which is exactly what a low-rank update can express.
This is also WHY LoRA tends to forget less than full fine-tuning (Section 13.2): the frozen W
physically cannot move, so whatever pretrained knowledge it encodes remains fully intact.
```

### 15.3 From-Scratch `LoRALinear` Layer

```python
class LoRALinear:
    """
    Wraps a FROZEN base Linear layer (base.W, base.b are never updated — they're excluded
    from the optimizer's parameter list) and adds a trainable low-rank correction.
    """

    def __init__(self, base_linear, rank=4, alpha=8):
        self.base = base_linear
        self.base.W.requires_grad = False        # freeze the pretrained weight...
        if self.base.b is not None:
            self.base.b.requires_grad = False     # ...and its bias
        d_in, d_out = base_linear.W.shape

        self.rank = rank
        self.scale = alpha / rank

        # A initialized small-random, B initialized to EXACTLY ZERO — this is a deliberate
        # design choice from the paper: at step 0, B @ A == 0, so the LoRA-augmented model
        # is IDENTICAL to the frozen pretrained model (training starts from a known-good point,
        # not from a random perturbation of it).
        self.A = Tensor(np.random.randn(d_in, rank) * 0.01, requires_grad=True)
        self.B = Tensor(np.zeros((rank, d_out)), requires_grad=True)

    def __call__(self, x):
        base_out = self.base(x)                            # frozen path — no grad flows into base.W
        lora_out = (x @ self.A) @ self.B * self.scale       # trainable low-rank path
        return base_out + lora_out

    def parameters(self):
        """Only A and B are returned — this list is what gets passed to the optimizer, so
        the frozen base weights literally never receive an update, by construction."""
        return [self.A, self.B]

    def merge(self):
        """Optional: fold the LoRA correction into the base weight for zero-overhead inference
        once fine-tuning is done — ΔW = B A * scale, W_new = W_old + ΔW. After merging, the
        model is a plain GPT again, with no runtime cost from the LoRA path."""
        self.base.W.data += (self.A.data @ self.B.data) * self.scale
```

### 15.4 Injecting LoRA Into the GPT Model

```python
def apply_lora_to_gpt(model, rank=4, alpha=8):
    """Standard practice (matching the LoRA paper's own experiments): apply LoRA only to the
    attention Q and V projections — empirically the highest-value/cheapest place to adapt,
    leaving K, O, and the FFN untouched and frozen for maximum parameter efficiency."""
    lora_params = []
    for block in model.blocks:
        for head in block.attn.heads:
            head.Wq_lora = LoRALinearFromWeight(head.Wq, rank, alpha)
            head.Wv_lora = LoRALinearFromWeight(head.Wv, rank, alpha)
            lora_params += head.Wq_lora.parameters() + head.Wv_lora.parameters()
    return lora_params


class LoRALinearFromWeight:
    """Same idea as LoRALinear, but wraps a raw weight Tensor (as used inside
    SelfAttentionHead, which stores Wq/Wk/Wv as bare Tensors rather than Linear objects)."""

    def __init__(self, weight_tensor, rank=4, alpha=8):
        self.W = weight_tensor
        self.W.requires_grad = False
        d_in, d_out = self.W.shape
        self.scale = alpha / rank
        self.A = Tensor(np.random.randn(d_in, rank) * 0.01, requires_grad=True)
        self.B = Tensor(np.zeros((rank, d_out)), requires_grad=True)

    def __call__(self, x):
        return x @ self.W + (x @ self.A) @ self.B * self.scale

    def parameters(self):
        return [self.A, self.B]
```

### 15.5 Validating LoRA's Backward Pass With Gradient Checking

Before trusting any from-scratch implementation of a paper's method, run it through Section 7's
gradient checker — this catches subtle bugs like "forgot to freeze the base weight" or
"scaled A/B incorrectly" immediately, rather than after an hour of confusing training runs.

```python
base = Linear(6, 4)
lora = LoRALinear(base, rank=2, alpha=4)
x_fixed = Tensor(np.random.randn(3, 6))
y_fixed = np.random.randint(0, 4, size=3)

def forward():
    return cross_entropy_loss(lora(x_fixed), y_fixed)

print("Checking LoRA A, B gradients (base.W should NOT even be in this list):")
gradient_check(forward, lora.parameters())          # only [A, B] — base.W is correctly excluded
```

### 15.6 LoRA Fine-Tuning Loop (compare directly against Section 14's full fine-tune)

```python
lora_model = GPT(vocab_size=vocab_size, d_model=64, num_heads=4, num_layers=4, max_seq_len=32)
load_checkpoint(lora_model, "pretrained.pkl")

lora_params = apply_lora_to_gpt(lora_model, rank=4, alpha=8)
optimizer = Adam(lora_params, lr=1e-3)              # LoRA typically uses a HIGHER lr than full
                                                      # fine-tuning (Section 14 used 5e-5) because
                                                      # A/B start near-zero and need to move more,
                                                      # while the (much larger) frozen base can't move at all

total_params = sum(p.data.size for p in lora_model.parameters())
trainable_params = sum(p.data.size for p in lora_params)
print(f"Full model params: {total_params:,}  |  LoRA-trainable params: {trainable_params:,} "
      f"({100 * trainable_params / total_params:.2f}%)")

for step in range(200):
    xb, yb = get_batch(domain_data, batch_size=8, seq_len=32)
    logits = lora_model(xb)
    loss = cross_entropy_loss(logits.reshape(-1, vocab_size), yb.reshape(-1))

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if step % 50 == 0:
        print(f"[LoRA fine-tune] step {step:4d}  loss {loss.data:.4f}")
```

---

## 16. Decoder Fine-Tuning: Loss Masking, Packing, Teacher Forcing

**Beginner recap:** Section 12 pretrained on raw, unstructured text with loss on every token.
Real-world decoder fine-tuning (instruction tuning, chat fine-tuning) uses **structured**
`(prompt, response)` pairs and typically computes loss **only on the response tokens** — this
section builds that from scratch on top of everything above.

### 16.1 Formatting Instruction Data for a Decoder-Only Model

```
Since a decoder-only model only ever does "predict next token," an instruction example is
turned into ONE long token sequence with a clear delimiter between prompt and response:

  "### Instruction:\nSummarize this text.\n### Input:\n<article>\n### Response:\n<summary><EOS>"

The model is trained with the USUAL next-token objective over this ENTIRE sequence — there is
no architectural difference from pretraining. What differs is which positions' loss gets
INCLUDED in the average (Section 16.2), and that every example is now one coherent
(instruction → answer) unit rather than an arbitrary window of running text.
```

### 16.2 Loss Masking — The Key Implementation Detail

```
Without masking, the model would be "rewarded" for correctly predicting the PROMPT tokens too
— but the prompt is given, fixed, user-supplied text; there's nothing useful to learn by
getting good at predicting it, and doing so can even encourage the model to reproduce prompts
verbatim rather than USE them. So: zero out the loss (and hence the gradient contribution) for
every position that is part of the prompt, keeping it only for response-token positions.
```

```python
def cross_entropy_loss_masked(logits, targets, loss_mask):
    """
    Same math as cross_entropy_loss (Section 3.3), but the mean is taken only over positions
    where loss_mask == 1 (response tokens), not over every position in the batch.

    logits:     Tensor (N, vocab_size), N = batch*seq_len flattened
    targets:    int array (N,)
    loss_mask:  float/bool array (N,), 1.0 for response tokens, 0.0 for prompt/padding tokens
    """
    shifted = logits.data - np.max(logits.data, axis=-1, keepdims=True)
    log_probs = shifted - np.log(np.sum(np.exp(shifted), axis=-1, keepdims=True))
    nll = -log_probs[np.arange(len(targets)), targets]

    masked_nll = nll * loss_mask
    denom = max(loss_mask.sum(), 1.0)             # avoid divide-by-zero if a batch has no response tokens
    loss_value = masked_nll.sum() / denom

    out = Tensor(loss_value, logits.requires_grad, (logits,), "masked_cross_entropy")

    def _backward():
        if logits.requires_grad:
            logits._ensure_grad()
            probs = np.exp(log_probs)
            grad = probs.copy()
            grad[np.arange(len(targets)), targets] -= 1.0
            grad *= loss_mask[:, None] / denom      # zero-out prompt-token gradients entirely
            logits.grad += grad * out.grad
    out._backward = _backward
    return out
```

### 16.3 Building `(input_ids, target_ids, loss_mask)` Triples From Instruction Data

```python
def build_instruction_example(prompt_text, response_text, stoi, eos_id):
    """Teacher forcing: at training time, the model is fed the GROUND-TRUTH response tokens
    as input (shifted by one), not its own (possibly wrong) generated tokens — this is what
    lets training be done in a single parallel forward pass instead of token-by-token
    generation, and it's called 'teacher forcing' because the correct answer 'teaches' the
    model what should have come next at every position, regardless of what the model itself
    would have predicted."""
    prompt_ids = [stoi[c] for c in prompt_text]
    response_ids = [stoi[c] for c in response_text] + [eos_id]

    full_sequence = prompt_ids + response_ids
    input_ids = full_sequence[:-1]
    target_ids = full_sequence[1:]

    # Loss mask aligned with target_ids: True only where the TARGET is a response token.
    # len(prompt_ids) prompt-input positions predict [rest-of-prompt + first response token];
    # we mask everything up to (but not including) the first response token as target.
    loss_mask = np.zeros(len(target_ids))
    loss_mask[len(prompt_ids) - 1:] = 1.0
    return np.array(input_ids), np.array(target_ids), loss_mask
```

### 16.4 Packing — Efficiently Batching Variable-Length Examples

```python
def pack_examples(examples, seq_len, pad_id=0):
    """Real fine-tuning datasets have examples of wildly different lengths. 'Packing'
    concatenates multiple short examples back-to-back into one fixed-length sequence (instead
    of wastefully padding every example up to the longest one), separated by EOS, with the
    loss mask correctly zeroed across example boundaries so the model never learns to treat
    unrelated packed examples as one continuous story."""
    input_ids, target_ids, loss_masks = [], [], []
    for ex_input, ex_target, ex_mask in examples:
        input_ids.extend(ex_input)
        target_ids.extend(ex_target)
        loss_masks.extend(ex_mask)

    input_ids = input_ids[:seq_len] + [pad_id] * max(0, seq_len - len(input_ids))
    target_ids = target_ids[:seq_len] + [pad_id] * max(0, seq_len - len(target_ids))
    loss_masks = loss_masks[:seq_len] + [0.0] * max(0, seq_len - len(loss_masks))
    return np.array(input_ids), np.array(target_ids), np.array(loss_masks)
```

### 16.5 Full Instruction Fine-Tuning Loop (LoRA + Loss Masking Combined)

```python
instructions = [
    # Kept short, and restricted to characters that appear in the Section 12 pretraining
    # corpus (this toy tokenizer has no <UNK> token), so (prompt + response) fits within
    # max_seq_len=32 (must match the pretrained checkpoint's positional embedding size).
    # Real datasets would use pack_examples (16.4) or a larger max_seq_len instead of this.
    ("hello there. ", "hello again."),
    ("this is nice. ", "so is that."),
    # ... realistically hundreds/thousands of examples
]
eos_id = vocab_size  # reserve one extra id for EOS in a real setup; simplified here

# max_seq_len MUST match the checkpoint's positional embedding table shape (Section 12 pretrained
# with max_seq_len=32) — this is a common real-world gotcha: architecture hyperparameters like
# max_seq_len, d_model, num_heads/layers are part of the checkpoint's shape contract, not just
# the training config, and must match exactly when loading a state dict into a fresh model.
sft_model = GPT(vocab_size=vocab_size, d_model=64, num_heads=4, num_layers=4, max_seq_len=32)
load_checkpoint(sft_model, "pretrained.pkl")
lora_params = apply_lora_to_gpt(sft_model, rank=4, alpha=8)
optimizer = Adam(lora_params, lr=1e-3)

for epoch in range(20):
    for prompt_text, response_text in instructions:
        input_ids, target_ids, loss_mask = build_instruction_example(
            prompt_text, response_text, stoi, eos_id=0)   # eos_id simplified for this toy vocab

        logits = sft_model(input_ids[None, :])                       # (1, seq_len, vocab)
        loss = cross_entropy_loss_masked(
            logits.reshape(-1, vocab_size), target_ids, loss_mask)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    if epoch % 5 == 0:
        print(f"[SFT] epoch {epoch:2d}  loss {loss.data:.4f}")
```

**This is, in miniature, exactly what "instruction fine-tuning" / "SFT" (Supervised
Fine-Tuning) means for real decoder-only LLMs (GPT, Llama, etc.):** same architecture, same
cross-entropy objective, same teacher forcing, with (a) structured prompt/response data, (b) a
loss mask over prompt tokens, and (c) usually a parameter-efficient method like LoRA layered on
top so the base model's general capabilities are preserved.

---

## 17. End-to-End Project: Pretrain → Fine-Tune a Tiny Decoder LM

**Beginner recap:** This section stitches every previous section into one runnable pipeline —
the same three-stage shape (pretrain → supervised fine-tune → use) that real LLM providers follow,
just at a scale that runs on your laptop's CPU in well under a minute.

```python
"""
end_to_end.py — pretrain, LoRA-fine-tune, and generate, using ONLY the classes/functions
defined in Sections 2-16 of this document. Run top to bottom.
"""
import numpy as np

np.random.seed(0)

# ---- Stage 0: data --------------------------------------------------------
raw_text = "hello world, this is a tiny character level language model. " * 80
chars = sorted(set(raw_text))
stoi = {ch: i for i, ch in enumerate(chars)}
itos = {i: ch for ch, i in stoi.items()}
vocab_size = len(chars)
pretrain_data = np.array([stoi[c] for c in raw_text])

# ---- Stage 1: pretrain (Section 12) ---------------------------------------
model = GPT(vocab_size, d_model=64, num_heads=4, num_layers=4, max_seq_len=32)
opt = Adam(model.parameters(), lr=3e-3)
for step in range(400):
    xb, yb = get_batch(pretrain_data, batch_size=16, seq_len=32)
    logits = model(xb)
    loss = cross_entropy_loss(logits.reshape(-1, vocab_size), yb.reshape(-1))
    opt.zero_grad(); loss.backward(); clip_grad_norm(model.parameters()); opt.step()
print(f"pretrain final loss: {loss.data:.4f}")
save_checkpoint(model, "pretrained.pkl")

# ---- Stage 2: LoRA fine-tune on a narrow instruction-style task (Sections 15-16) --
sft_model = GPT(vocab_size, d_model=64, num_heads=4, num_layers=4, max_seq_len=32)
load_checkpoint(sft_model, "pretrained.pkl")
lora_params = apply_lora_to_gpt(sft_model, rank=4, alpha=8)
opt_ft = Adam(lora_params, lr=1e-3)

instructions = [("hello there. ", "hello again."), ("this is nice. ", "so is that.")]
for epoch in range(100):
    for p_text, r_text in instructions:
        inp, tgt, mask = build_instruction_example(p_text, r_text, stoi, eos_id=0)
        logits = sft_model(inp[None, :])
        loss = cross_entropy_loss_masked(logits.reshape(-1, vocab_size), tgt, mask)
        opt_ft.zero_grad(); loss.backward(); opt_ft.step()
print(f"fine-tune final loss: {loss.data:.4f}")

# ---- Stage 3: generate from both models, compare ---------------------------
prompt_ids = [stoi[c] for c in "hello"]
print("pretrained :", "".join(itos[i] for i in generate(model, prompt_ids, 20, temperature=0.7)))
print("fine-tuned :", "".join(itos[i] for i in generate(sft_model, prompt_ids, 20, temperature=0.7)))
```

**What you should observe:** the pretrained model's continuation is diffuse (reflects the whole
generic corpus), while the fine-tuned model, having only had its Q/V LoRA adapters nudged toward
the small instruction set, is measurably more likely to complete `"hello"` the way its fine-tuning
examples did — with a small fraction of the parameters updated and no change at all to `model`
(the frozen pretrained checkpoint remains reusable for other tasks/adapters).

---

## 18. What Frameworks (PyTorch/TF) Actually Automate For You

**Beginner recap:** Now that you've built the pieces by hand, here's a direct map from what you
wrote to what a framework call actually does underneath — useful both for reading production
code fluently and for knowing what to check when a framework's behavior surprises you.

```
YOUR FROM-SCRATCH CODE                              PYTORCH EQUIVALENT
────────────────────────────────────────────────────────────────────────────────
Tensor class + _backward closures (Sec 2)      →    torch.Tensor with requires_grad=True,
                                                     autograd.Function, .backward()
Linear class (Sec 3)                            →    torch.nn.Linear
he_init / xavier_init (Sec 3)                   →    torch.nn.init.kaiming_normal_ / xavier_normal_
cross_entropy_loss (Sec 3)                      →    torch.nn.functional.cross_entropy
SGD / Adam classes (Sec 6)                      →    torch.optim.SGD / torch.optim.Adam
clip_grad_norm (Sec 6)                          →    torch.nn.utils.clip_grad_norm_
gradient_check (Sec 7)                          →    torch.autograd.gradcheck
im2col-based Conv2D (Sec 8)                     →    torch.nn.Conv2d (uses cuDNN kernels,
                                                     same underlying math)
RNNCell / LSTMCell (Sec 9)                      →    torch.nn.RNNCell / torch.nn.LSTMCell
SelfAttentionHead / MultiHeadAttention (Sec 10) →    torch.nn.MultiheadAttention (or the
                                                     hand-rolled attention inside every HF
                                                     transformers model)
causal_mask (Sec 10)                            →    is_causal=True flag / additive mask arg
LayerNorm class (Sec 11)                        →    torch.nn.LayerNorm
DecoderBlock / GPT (Sec 11)                     →    a HuggingFace GPT2Block / GPT2LMHeadModel
save_checkpoint / load_checkpoint (Sec 14)      →    torch.save(model.state_dict(), ...) /
                                                     model.load_state_dict(...)
LoRALinear (Sec 15)                             →    peft.LoraConfig + get_peft_model(...)
                                                     (Hugging Face's `peft` library)
cross_entropy_loss_masked (Sec 16)              →    labels with -100 at masked positions,
                                                     passed to a HF model's built-in loss
                                                     (-100 is PyTorch's convention for "ignore
                                                     this position in the loss")
```

**The honest, important truth:** what frameworks add on top of the MATH you've now implemented
is almost entirely **engineering**, not new algorithms: GPU kernels (fused/optimized matmuls),
automatic mixed precision, distributed training across many machines, memory-efficient
attention (FlashAttention avoids ever materializing the full seq×seq score matrix), and a huge
ecosystem of pretrained checkpoints. The forward-pass formulas and backward-pass chain rule are
exactly what you wrote above, at any scale.

---

## 19. Interview Questions & Common Pitfalls

### Conceptual

1. **"Walk me through backprop for a single Linear+ReLU layer, with shapes."** → Section 4;
   be ready to write `dx = dz @ W.T`, `dW = x.T @ dz`, `db = dz.sum(axis=0)` from memory.
2. **"Why does attention scale by √d_k?"** → Section 10.2; without it, large dot products push
   softmax into a saturated regime, causing vanishing gradients through the softmax Jacobian.
3. **"Derive the gradient of softmax + cross-entropy."** → Section 3.3; the clean closed form
   `softmax(z) - one_hot(target)` is a strong signal of real understanding, not memorization.
4. **"Why does LoRA initialize B to zero?"** → Section 15.3; guarantees the fine-tuned model is
   IDENTICAL to the pretrained model at step 0 (no random perturbation of a working model).
5. **"What's the difference between full fine-tuning and LoRA, in terms of what gets a gradient?"**
   → Full: every parameter has `requires_grad=True` and a full Adam state. LoRA: the base weight's
   `requires_grad=False` (never appears in the optimizer's parameter list at all); only the small
   A/B matrices are trainable — Section 15.3/15.4.
6. **"Why do we mask the loss on prompt tokens during instruction fine-tuning?"** → Section 16.2;
   the prompt is given/fixed input, not something worth "rewarding" the model for predicting.
7. **"What is catastrophic forgetting, and how does LoRA reduce the risk of it?"** → Section
   13.2/15.2; frozen base weights physically cannot move, bounding how far the model can drift.
8. **"Why is GPT decoder-only rather than encoder-decoder like the original Transformer?"** →
   A decoder-only model with causal masking can do both understanding (via context in the causal
   window) and generation with ONE architecture and ONE training objective (next-token
   prediction), simplifying both pretraining and the same architecture's later fine-tuning.

### Common From-Scratch Implementation Pitfalls

```
1. Forgetting to zero gradients between steps → gradients silently ACCUMULATE across
   iterations (this is actually valid for micro-batch gradient accumulation, but a bug
   otherwise) — always model.zero_grad() (or per-parameter) before each .backward().

2. Not using the log-sum-exp trick in softmax/cross-entropy → np.exp() of a large logit
   overflows to `inf`, and `inf/inf = nan` silently poisons the entire training run.

3. Broadcasting bugs in a hand-rolled autograd engine → e.g. adding a (batch, dim) tensor to
   a (dim,) bias without unbroadcasting the gradient back down on the way out (Section 2.2's
   `_unbroadcast` static method exists specifically to prevent this class of bug).

4. Missing causal mask (or applying it to the wrong axis) in a decoder → the model can "see
   the future" during TRAINING (looks great — near-zero loss, since it can just copy the
   next token from its own input) but is unusable at inference time, where future tokens
   don't exist yet. This is one of the most common and most confusing from-scratch bugs.

5. Forgetting to exclude frozen (LoRA base) weights from the optimizer's parameter list →
   even with requires_grad=False set correctly, an optimizer given the WRONG parameter list
   would still try to step them if their .grad happened to be non-None from a stale computation.

6. Learning rate mismatched to the fine-tuning method → using a full-fine-tuning-scale LR
   (e.g. 5e-5) for freshly-initialized, near-zero LoRA A/B matrices means they barely move at
   all in the fine-tuning budget — LoRA typically wants a noticeably HIGHER learning rate
   than full fine-tuning (Section 15.6) precisely because it initializes near-zero.
```

---

## 20. The Same GPT + Fine-Tuning in PyTorch

**Beginner recap:** Everything below is the SAME architecture and SAME fine-tuning techniques
from Sections 11-16, rewritten idiomatically in PyTorch. Read it side by side with Sections 11-16
— every `nn.Module` here corresponds to a from-scratch class you already built, and every
`.backward()` call is doing exactly the topological-sort-and-reverse-walk from Section 2.6,
just implemented in optimized C++/CUDA instead of Python.

### 20.1 The Decoder-Only Model

```python
import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class CausalSelfAttention(nn.Module):
    """Equivalent to Section 10.3's SelfAttentionHead + MultiHeadAttention, fused into one
    module that computes all heads via a single bigger matmul (the standard, faster way to
    implement multi-head attention — mathematically identical to running heads separately
    and concatenating, just reshaped for one big batched matmul instead of a Python loop)."""

    def __init__(self, d_model, num_heads):
        super().__init__()
        assert d_model % num_heads == 0
        self.num_heads = num_heads
        self.d_head = d_model // num_heads
        self.qkv = nn.Linear(d_model, 3 * d_model)     # fused Q,K,V projection
        self.proj = nn.Linear(d_model, d_model)         # equivalent to Section 10.3's Wo

    def forward(self, x):
        B, T, C = x.shape
        qkv = self.qkv(x)                                        # (B, T, 3C)
        q, k, v = qkv.split(C, dim=-1)
        q = q.view(B, T, self.num_heads, self.d_head).transpose(1, 2)   # (B, heads, T, d_head)
        k = k.view(B, T, self.num_heads, self.d_head).transpose(1, 2)
        v = v.view(B, T, self.num_heads, self.d_head).transpose(1, 2)

        # F.scaled_dot_product_attention fuses exactly the math from Section 10.1
        # (QK^T/sqrt(d_k) -> causal mask -> softmax -> @V) into one optimized (often
        # FlashAttention-backed) kernel — same formula, no separate mask tensor needed.
        out = F.scaled_dot_product_attention(q, k, v, is_causal=True)   # (B, heads, T, d_head)
        out = out.transpose(1, 2).contiguous().view(B, T, C)
        return self.proj(out)


class FeedForward(nn.Module):
    """Same 4x-expansion position-wise MLP as Section 11.2."""

    def __init__(self, d_model, d_ff=None):
        super().__init__()
        d_ff = d_ff or 4 * d_model
        self.net = nn.Sequential(nn.Linear(d_model, d_ff), nn.GELU(), nn.Linear(d_ff, d_model))

    def forward(self, x):
        return self.net(x)


class DecoderBlock(nn.Module):
    """Same Pre-LN residual layout as Section 11.3."""

    def __init__(self, d_model, num_heads):
        super().__init__()
        self.ln1 = nn.LayerNorm(d_model)
        self.attn = CausalSelfAttention(d_model, num_heads)
        self.ln2 = nn.LayerNorm(d_model)
        self.ffn = FeedForward(d_model)

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.ffn(self.ln2(x))
        return x


class GPT(nn.Module):
    """Directly comparable to Section 11.5's from-scratch GPT class."""

    def __init__(self, vocab_size, d_model=64, num_heads=4, num_layers=4, max_seq_len=128):
        super().__init__()
        self.token_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb = nn.Embedding(max_seq_len, d_model)
        self.blocks = nn.ModuleList([DecoderBlock(d_model, num_heads) for _ in range(num_layers)])
        self.ln_f = nn.LayerNorm(d_model)
        self.head = nn.Linear(d_model, vocab_size, bias=False)
        self.max_seq_len = max_seq_len
        self.apply(self._init_weights)               # explicit init, same intent as Section 3.1

    def _init_weights(self, module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, token_ids):
        B, T = token_ids.shape
        positions = torch.arange(T, device=token_ids.device).unsqueeze(0).expand(B, T)
        x = self.token_emb(token_ids) + self.pos_emb(positions)
        for block in self.blocks:
            x = block(x)
        x = self.ln_f(x)
        return self.head(x)                            # (B, T, vocab_size)
```

### 20.2 Pretraining Loop

```python
def get_batch_torch(data, batch_size, seq_len, device="cpu"):
    ix = torch.randint(0, len(data) - seq_len - 1, (batch_size,))
    x = torch.stack([data[i:i + seq_len] for i in ix]).to(device)
    y = torch.stack([data[i + 1:i + seq_len + 1] for i in ix]).to(device)
    return x, y


model = GPT(vocab_size=vocab_size, d_model=64, num_heads=4, num_layers=4, max_seq_len=32)
optimizer = torch.optim.AdamW(model.parameters(), lr=3e-3)
data_t = torch.tensor(pretrain_data, dtype=torch.long)

for step in range(500):
    xb, yb = get_batch_torch(data_t, batch_size=16, seq_len=32)
    logits = model(xb)                                             # (B, T, vocab)
    loss = F.cross_entropy(logits.view(-1, vocab_size), yb.view(-1))

    optimizer.zero_grad(set_to_none=True)
    loss.backward()                                                 # autograd engine from Section 2,
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)          # but written in C++/CUDA
    optimizer.step()

    if step % 50 == 0:
        print(f"step {step:4d}  loss {loss.item():.4f}")

torch.save(model.state_dict(), "pretrained_torch.pt")
```

### 20.3 Full Fine-Tuning in PyTorch

```python
finetune_model = GPT(vocab_size=vocab_size, d_model=64, num_heads=4, num_layers=4, max_seq_len=32)
finetune_model.load_state_dict(torch.load("pretrained_torch.pt"))

# Every parameter is trainable by default (requires_grad=True) — this IS full fine-tuning;
# the only difference from pretraining is the starting weights and a smaller learning rate.
ft_optimizer = torch.optim.AdamW(finetune_model.parameters(), lr=5e-5)
domain_data_t = torch.tensor(domain_data, dtype=torch.long)

for step in range(200):
    xb, yb = get_batch_torch(domain_data_t, batch_size=8, seq_len=32)
    logits = finetune_model(xb)
    loss = F.cross_entropy(logits.view(-1, vocab_size), yb.view(-1))
    ft_optimizer.zero_grad(set_to_none=True)
    loss.backward()
    ft_optimizer.step()
```

### 20.4 LoRA in PyTorch — Hand-Rolled (Same Idea as Section 15.3)

```python
class LoRALinear(nn.Module):
    """Drop-in replacement for nn.Linear that wraps a frozen pretrained layer, exactly
    mirroring Section 15.3 — the only difference is `requires_grad_(False)` and autograd
    exclusion are handled by PyTorch's built-in machinery instead of a hand-rolled flag."""

    def __init__(self, base_linear: nn.Linear, rank=4, alpha=8):
        super().__init__()
        self.base = base_linear
        self.base.weight.requires_grad_(False)          # freeze the pretrained weight
        if self.base.bias is not None:
            self.base.bias.requires_grad_(False)

        d_out, d_in = base_linear.weight.shape            # nn.Linear stores W as (out, in)
        self.scale = alpha / rank
        self.A = nn.Parameter(torch.randn(d_in, rank) * 0.01)
        self.B = nn.Parameter(torch.zeros(rank, d_out))    # zero-init B, same reasoning as 15.3

    def forward(self, x):
        return self.base(x) + (x @ self.A) @ self.B * self.scale


def apply_lora(model: GPT, rank=4, alpha=8):
    """Replace the fused qkv projection's query/value slices — in practice with a fused qkv
    Linear it's simplest to wrap the WHOLE qkv projection; production LoRA implementations
    (e.g. Hugging Face `peft`) instead target named sub-modules directly by string pattern."""
    lora_params = []
    for block in model.blocks:
        wrapped = LoRALinear(block.attn.qkv, rank=rank, alpha=alpha)
        block.attn.qkv = wrapped
        lora_params += [wrapped.A, wrapped.B]
    return lora_params


lora_model = GPT(vocab_size=vocab_size, d_model=64, num_heads=4, num_layers=4, max_seq_len=32)
lora_model.load_state_dict(torch.load("pretrained_torch.pt"))
lora_params = apply_lora(lora_model, rank=4, alpha=8)

total = sum(p.numel() for p in lora_model.parameters())
trainable = sum(p.numel() for p in lora_params)
print(f"trainable: {trainable:,} / {total:,} ({100*trainable/total:.2f}%)")

lora_optimizer = torch.optim.AdamW(lora_params, lr=1e-3)   # ONLY A, B ever get an update
for step in range(200):
    xb, yb = get_batch_torch(domain_data_t, batch_size=8, seq_len=32)
    logits = lora_model(xb)
    loss = F.cross_entropy(logits.view(-1, vocab_size), yb.view(-1))
    lora_optimizer.zero_grad(set_to_none=True)
    loss.backward()
    lora_optimizer.step()
```

**Production shortcut:** in real projects you'd use Hugging Face's `peft` library instead of
hand-rolling `LoRALinear`:

```python
from peft import LoraConfig, get_peft_model

config = LoraConfig(r=8, lora_alpha=16, target_modules=["q_proj", "v_proj"], lora_dropout=0.05)
peft_model = get_peft_model(base_model, config)      # freezes base, injects LoRA adapters
peft_model.print_trainable_parameters()               # confirms the <1% trainable ratio
```

`peft` does exactly what Section 15/20.4 does by hand: freeze the named target modules, wrap
them with a `Linear + low-rank A/B` module, and expose only `A`/`B` to the optimizer.

### 20.5 Decoder / Instruction Fine-Tuning With Loss Masking in PyTorch

```python
def build_instruction_batch(examples, tokenizer_encode, max_len, pad_id=0, ignore_index=-100):
    """PyTorch's convention (used throughout Hugging Face `transformers`) is to set the TARGET
    label to -100 at every position that should be excluded from the loss — F.cross_entropy's
    `ignore_index` argument then handles the masking internally, replacing the hand-written
    masked-mean from Section 16.2 with a single kwarg."""
    all_input_ids, all_labels = [], []
    for prompt, response in examples:
        prompt_ids = tokenizer_encode(prompt)
        response_ids = tokenizer_encode(response) + [pad_id]      # +EOS in a real tokenizer

        input_ids = (prompt_ids + response_ids)[:-1]
        labels = [ignore_index] * (len(prompt_ids) - 1) + response_ids
        labels = labels[:len(input_ids)]

        pad_len = max_len - len(input_ids)
        input_ids = input_ids + [pad_id] * pad_len
        labels = labels + [ignore_index] * pad_len                # padding also excluded from loss

        all_input_ids.append(input_ids[:max_len])
        all_labels.append(labels[:max_len])
    return torch.tensor(all_input_ids), torch.tensor(all_labels)


sft_optimizer = torch.optim.AdamW(lora_params, lr=1e-3)
for epoch in range(20):
    input_ids, labels = build_instruction_batch(
        [("hello there. ", "hello again."), ("this is nice. ", "so is that.")],
        tokenizer_encode=lambda s: [stoi[c] for c in s], max_len=32)

    logits = lora_model(input_ids)
    # ignore_index=-100 makes this line do EXACTLY what Section 16.2's cross_entropy_loss_masked
    # does by hand: sum the loss only over non-masked positions, divide by the count of those.
    loss = F.cross_entropy(logits.view(-1, vocab_size), labels.view(-1), ignore_index=-100)

    sft_optimizer.zero_grad(set_to_none=True)
    loss.backward()
    sft_optimizer.step()
```

---

## 21. The Same GPT + Fine-Tuning in TensorFlow/Keras

**Beginner recap:** Same architecture again, this time in TensorFlow 2.x using `tf.keras` and
`tf.GradientTape` — TensorFlow's equivalent of the Section 2 autograd engine: it also records a
computation graph ("tape") as ops run, then walks it backward to produce gradients on demand.

### 21.1 The Decoder-Only Model

```python
import tensorflow as tf
from tensorflow.keras import layers


class CausalSelfAttention(layers.Layer):
    """Same fused-qkv design as Section 20.1's PyTorch version."""

    def __init__(self, d_model, num_heads, **kwargs):
        super().__init__(**kwargs)
        assert d_model % num_heads == 0
        self.num_heads = num_heads
        self.d_head = d_model // num_heads
        self.qkv = layers.Dense(3 * d_model)
        self.proj = layers.Dense(d_model)

    def call(self, x):
        B = tf.shape(x)[0]
        T = tf.shape(x)[1]
        qkv = self.qkv(x)
        q, k, v = tf.split(qkv, 3, axis=-1)

        def reshape_heads(t):
            t = tf.reshape(t, (B, T, self.num_heads, self.d_head))
            return tf.transpose(t, [0, 2, 1, 3])          # (B, heads, T, d_head)

        q, k, v = reshape_heads(q), reshape_heads(k), reshape_heads(v)

        scores = tf.matmul(q, k, transpose_b=True) / tf.math.sqrt(tf.cast(self.d_head, tf.float32))
        causal_mask = tf.linalg.band_part(tf.ones((T, T)), -1, 0)     # lower-triangular = allowed
        scores = tf.where(causal_mask[None, None] == 0, tf.fill(tf.shape(scores), -1e9), scores)
        attn = tf.nn.softmax(scores, axis=-1)                           # same formula as Sec 10.1
        out = tf.matmul(attn, v)                                        # (B, heads, T, d_head)

        out = tf.transpose(out, [0, 2, 1, 3])
        out = tf.reshape(out, (B, T, self.num_heads * self.d_head))
        return self.proj(out)


class FeedForward(layers.Layer):
    def __init__(self, d_model, d_ff=None, **kwargs):
        super().__init__(**kwargs)
        d_ff = d_ff or 4 * d_model
        self.fc1 = layers.Dense(d_ff, activation="gelu")
        self.fc2 = layers.Dense(d_model)

    def call(self, x):
        return self.fc2(self.fc1(x))


class DecoderBlock(layers.Layer):
    def __init__(self, d_model, num_heads, **kwargs):
        super().__init__(**kwargs)
        self.ln1 = layers.LayerNormalization()
        self.attn = CausalSelfAttention(d_model, num_heads)
        self.ln2 = layers.LayerNormalization()
        self.ffn = FeedForward(d_model)

    def call(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.ffn(self.ln2(x))
        return x


class GPT(tf.keras.Model):
    def __init__(self, vocab_size, d_model=64, num_heads=4, num_layers=4, max_seq_len=128, **kwargs):
        super().__init__(**kwargs)
        self.token_emb = layers.Embedding(vocab_size, d_model)
        self.pos_emb = layers.Embedding(max_seq_len, d_model)
        self.blocks = [DecoderBlock(d_model, num_heads) for _ in range(num_layers)]
        self.ln_f = layers.LayerNormalization()
        self.head = layers.Dense(vocab_size, use_bias=False)
        self.max_seq_len = max_seq_len

    def call(self, token_ids):
        T = tf.shape(token_ids)[1]
        positions = tf.range(T)[None, :]
        x = self.token_emb(token_ids) + self.pos_emb(positions)
        for block in self.blocks:
            x = block(x)
        x = self.ln_f(x)
        return self.head(x)                                # (B, T, vocab_size)
```

### 21.2 Pretraining Loop With `tf.GradientTape` (the explicit, "from-scratch-style" way)

```python
model = GPT(vocab_size=vocab_size, d_model=64, num_heads=4, num_layers=4, max_seq_len=32)
optimizer = tf.keras.optimizers.AdamW(learning_rate=3e-3)
loss_fn = tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)


def get_batch_tf(data, batch_size, seq_len):
    ix = tf.random.uniform((batch_size,), 0, len(data) - seq_len - 1, dtype=tf.int32)
    x = tf.stack([data[i:i + seq_len] for i in ix])
    y = tf.stack([data[i + 1:i + seq_len + 1] for i in ix])
    return x, y


data_tf = tf.constant(pretrain_data, dtype=tf.int32)

for step in range(500):
    xb, yb = get_batch_tf(data_tf, batch_size=16, seq_len=32)

    with tf.GradientTape() as tape:                          # records the computation graph —
        logits = model(xb)                                    # this IS Section 2's Tensor graph,
        loss = loss_fn(yb, logits)                             # just built by TensorFlow's own engine

    grads = tape.gradient(loss, model.trainable_variables)     # the "backward pass" call
    grads, _ = tf.clip_by_global_norm(grads, 1.0)
    optimizer.apply_gradients(zip(grads, model.trainable_variables))

    if step % 50 == 0:
        print(f"step {step:4d}  loss {loss.numpy():.4f}")

model.save_weights("pretrained_tf.weights.h5")
```

### 21.3 Full Fine-Tuning in TensorFlow

```python
finetune_model = GPT(vocab_size=vocab_size, d_model=64, num_heads=4, num_layers=4, max_seq_len=32)
finetune_model(tf.zeros((1, 32), dtype=tf.int32))            # build the model (creates variables)
finetune_model.load_weights("pretrained_tf.weights.h5")

ft_optimizer = tf.keras.optimizers.AdamW(learning_rate=5e-5)  # small LR — same reasoning as Sec 14.2
domain_data_tf = tf.constant(domain_data, dtype=tf.int32)

for step in range(200):
    xb, yb = get_batch_tf(domain_data_tf, batch_size=8, seq_len=32)
    with tf.GradientTape() as tape:
        logits = finetune_model(xb)
        loss = loss_fn(yb, logits)
    grads = tape.gradient(loss, finetune_model.trainable_variables)
    ft_optimizer.apply_gradients(zip(grads, finetune_model.trainable_variables))
```

### 21.4 LoRA as a Custom Keras Layer

```python
class LoRADense(layers.Layer):
    """Same idea as Sections 15.3/20.4: wrap a frozen Dense layer, add a trainable low-rank
    correction. In Keras, `trainable=False` on a layer/weight is what excludes it from
    `trainable_variables`, which is the list `tape.gradient` and the optimizer actually use —
    the direct equivalent of `requires_grad=False` in PyTorch or our own flag in Section 15.3."""

    def __init__(self, base_dense: layers.Dense, rank=4, alpha=8, **kwargs):
        super().__init__(**kwargs)
        self.base = base_dense
        self.base.trainable = False                        # freeze pretrained weight + bias
        self.rank, self.alpha = rank, alpha

    def build(self, input_shape):
        d_in = input_shape[-1]
        d_out = self.base.units
        self.scale = self.alpha / self.rank
        self.A = self.add_weight(shape=(d_in, self.rank), initializer="random_normal", trainable=True)
        self.B = self.add_weight(shape=(self.rank, d_out), initializer="zeros", trainable=True)

    def call(self, x):
        return self.base(x) + tf.matmul(tf.matmul(x, self.A), self.B) * self.scale


def apply_lora_tf(model, rank=4, alpha=8):
    lora_layers = []
    for block in model.blocks:
        wrapped = LoRADense(block.attn.qkv, rank=rank, alpha=alpha)
        block.attn.qkv = wrapped
        lora_layers.append(wrapped)
    return lora_layers


lora_model = GPT(vocab_size=vocab_size, d_model=64, num_heads=4, num_layers=4, max_seq_len=32)
lora_model(tf.zeros((1, 32), dtype=tf.int32))
lora_model.load_weights("pretrained_tf.weights.h5")
lora_layers_list = apply_lora_tf(lora_model, rank=4, alpha=8)

lora_optimizer = tf.keras.optimizers.AdamW(learning_rate=1e-3)
lora_vars = [v for layer in lora_layers_list for v in [layer.A, layer.B]]

for step in range(200):
    xb, yb = get_batch_tf(domain_data_tf, batch_size=8, seq_len=32)
    with tf.GradientTape() as tape:
        logits = lora_model(xb)
        loss = loss_fn(yb, logits)
    grads = tape.gradient(loss, lora_vars)          # only A, B ever get gradients computed
    lora_optimizer.apply_gradients(zip(grads, lora_vars))
```

### 21.5 Decoder / Instruction Fine-Tuning With Loss Masking in TensorFlow

```python
def masked_loss(labels, logits, loss_mask):
    """TensorFlow/Keras convention: pass an explicit `sample_weight`-style mask multiplied
    into a per-token loss, then reduce — the direct equivalent of Section 16.2's masked mean,
    and of PyTorch's `ignore_index=-100` from Section 20.5."""
    per_token_loss = tf.keras.losses.sparse_categorical_crossentropy(labels, logits, from_logits=True)
    per_token_loss *= loss_mask
    return tf.reduce_sum(per_token_loss) / tf.maximum(tf.reduce_sum(loss_mask), 1.0)


for epoch in range(20):
    for prompt_text, response_text in [("hello there. ", "hello again."), ("this is nice. ", "so is that.")]:
        input_ids, target_ids, loss_mask = build_instruction_example(prompt_text, response_text, stoi, eos_id=0)
        xb = tf.constant(input_ids[None, :], dtype=tf.int32)

        with tf.GradientTape() as tape:
            logits = lora_model(xb)[0]                       # (seq_len, vocab)
            loss = masked_loss(target_ids, logits, tf.constant(loss_mask, dtype=tf.float32))

        grads = tape.gradient(loss, lora_vars)
        lora_optimizer.apply_gradients(zip(grads, lora_vars))
```

### 21.6 Quick-Reference: NumPy-From-Scratch ↔ PyTorch ↔ TensorFlow

```
CONCEPT                    FROM SCRATCH (Sec 2-16)         PYTORCH (Sec 20)              TENSORFLOW (Sec 21)
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
Autograd graph              Tensor._prev / _backward()      autograd graph (dynamic)      tf.GradientTape
Backward pass                node.backward()                 loss.backward()               tape.gradient(...)
Freeze a weight              requires_grad = False            .requires_grad_(False)        layer.trainable = False
Cross-entropy + mask         cross_entropy_loss_masked        ignore_index=-100             per-token loss * mask
Optimizer                    Adam class (Sec 6)               torch.optim.AdamW             tf.keras.optimizers.AdamW
Gradient clipping            clip_grad_norm (Sec 6.3)         clip_grad_norm_               clip_by_global_norm
Save/load weights            pickle (Sec 14.1)                state_dict / torch.save        model.save_weights
LoRA                         LoRALinear (Sec 15.3)            LoRALinear(nn.Module)          LoRADense(layers.Layer)
```

---

## 22. Beyond the Code: What Real Research-Paper Implementations Need

**Beginner recap:** A correct forward/backward pass (Sections 2-21) is necessary but NOT
sufficient to reproduce a paper's reported results. Papers' "Experiments" sections rely on a
whole layer of engineering discipline around the model code — this section covers the pieces
that most commonly cause "I implemented the architecture but can't match the paper's numbers."

### 22.1 Reproducibility: Seed Everything

```python
import random
import numpy as np
import torch

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True   # trade some speed for exact reproducibility
    torch.backends.cudnn.benchmark = False
    # TensorFlow equivalent: tf.random.set_seed(seed)
```

```
Why this matters: neural network training is stochastic (weight init, data shuffling, dropout).
Two runs with different seeds can differ by several points on a benchmark purely from noise —
which is why serious papers report results AVERAGED over multiple seeds (often 3-5), with a
standard deviation or confidence interval, not a single run's number. If you can't reproduce a
paper's exact number with one run, that alone doesn't mean your implementation is wrong.
```

### 22.2 Config Management — Never Hardcode Hyperparameters Inline

```python
from dataclasses import dataclass

@dataclass
class GPTConfig:
    vocab_size: int
    d_model: int = 768
    num_heads: int = 12
    num_layers: int = 12
    max_seq_len: int = 1024
    dropout: float = 0.1

@dataclass
class TrainConfig:
    lr: float = 3e-4
    weight_decay: float = 0.1
    warmup_steps: int = 2000
    max_steps: int = 100_000
    batch_size: int = 64
    grad_clip: float = 1.0
    seed: int = 42

# Real projects load these from YAML/JSON (or a tool like Hydra) so every experiment run is
# fully reproducible from a single saved config file, not scattered magic numbers in code.
```

### 22.3 Learning Rate Schedules — Warmup + Decay (Essential for Transformers)

```
Almost every Transformer paper (the original 2017 paper, GPT, BERT, ...) uses a NON-constant
learning rate: a short linear WARMUP phase, then decay. Skipping warmup is one of the most
common reasons a from-scratch Transformer training run diverges (loss -> NaN) in the first
few hundred steps — large random-init gradients combined with a full-strength learning rate is
exactly the exploding-gradient scenario from Section 9.1's RNN discussion, applied to depth
instead of time.

  warmup:  lr(t) = base_lr * (t / warmup_steps)                         for t < warmup_steps
  decay:   lr(t) = base_lr * cosine_decay(t - warmup_steps, ...)         for t >= warmup_steps
```

```python
import math

def lr_schedule(step, base_lr, warmup_steps, max_steps, min_lr_ratio=0.1):
    if step < warmup_steps:
        return base_lr * step / warmup_steps
    progress = (step - warmup_steps) / max(1, max_steps - warmup_steps)
    cosine = 0.5 * (1 + math.cos(math.pi * min(progress, 1.0)))
    return base_lr * (min_lr_ratio + (1 - min_lr_ratio) * cosine)

# Applied manually each step (works identically whether the optimizer is your Section 6 Adam,
# torch.optim.AdamW, or tf.keras.optimizers.AdamW):
for step in range(max_steps):
    current_lr = lr_schedule(step, base_lr=3e-4, warmup_steps=2000, max_steps=max_steps)
    for param_group in optimizer.param_groups:      # PyTorch convention
        param_group["lr"] = current_lr
    # ... forward, backward, optimizer.step() as before
```

### 22.4 Mixed Precision & Gradient Accumulation

```
Mixed precision: run most of the forward/backward pass in float16/bfloat16 (2x less memory,
faster on modern GPUs) while keeping a float32 "master copy" of weights for the actual update —
avoids the precision loss that would otherwise make small gradient updates vanish in float16.
  PyTorch:    torch.cuda.amp.autocast() + torch.cuda.amp.GradScaler()
  TensorFlow: tf.keras.mixed_precision.set_global_policy("mixed_float16")

Gradient accumulation: simulate a larger batch size than fits in memory by running several
forward/backward passes WITHOUT calling optimizer.step(), summing gradients, then stepping once:

  optimizer.zero_grad()
  for micro_step in range(accumulation_steps):
      loss = compute_loss(get_micro_batch()) / accumulation_steps   # scale down before backward
      loss.backward()                                                # accumulates into .grad
  optimizer.step()                                                   # one update, effective
                                                                      # batch = micro_batch * accumulation_steps

This is exactly why Section 2's Tensor.backward() ACCUMULATES gradient (+=) rather than
overwriting it — gradient accumulation across micro-batches (and across multiple uses of the
same tensor in one graph, like residual connections) relies on that one design choice.
```

### 22.5 Checkpointing Correctly (Model AND Optimizer State)

```python
def save_full_checkpoint(model, optimizer, step, path):
    """Saving ONLY model weights (Section 14.1) is enough to resume for INFERENCE or a fresh
    fine-tune, but NOT enough to exactly resume interrupted TRAINING — Adam's running averages
    (m, v from Section 6.2) are themselves part of the optimization trajectory; restarting them
    at zero after a crash measurably changes the rest of training versus an uninterrupted run."""
    torch.save({
        "step": step,
        "model_state": model.state_dict(),
        "optimizer_state": optimizer.state_dict(),
    }, path)


def load_full_checkpoint(model, optimizer, path):
    ckpt = torch.load(path)
    model.load_state_dict(ckpt["model_state"])
    optimizer.load_state_dict(ckpt["optimizer_state"])
    return ckpt["step"]
```

### 22.6 Evaluation Protocol — Matching the Paper's Methodology, Not Just the Model

```
Common ways implementations diverge from a paper's REPORTED numbers, even with an identical
model architecture:
  1. Different train/val/test split (or split seed) than the paper used.
  2. Evaluating on a single seed instead of averaging over the paper's N seeds.
  3. Different tokenizer / vocabulary / preprocessing (e.g. whitespace handling, casing,
     BPE merges count) — token-level perplexity is NOT comparable across tokenizers.
  4. Different definition of the metric itself (e.g. "accuracy" computed per-token vs
     per-sequence for a generation task give very different numbers).
  5. Missing an implementation detail mentioned only in an appendix/footnote (weight decay
     applied to some but not all parameter groups is a classic one — LayerNorm/bias
     parameters are conventionally EXCLUDED from weight decay; forgetting this measurably
     changes results).
  6. Different effective batch size due to different gradient-accumulation/hardware setup,
     which interacts with the learning rate (Section 6's Adam batch-size/LR relationship).

A rigorous from-scratch reproduction explicitly documents each of these choices rather than
leaving them as implicit defaults, precisely so a reviewer (or future you) can tell whether a
numeric mismatch is a bug or an intentional methodology difference.
```

### 22.7 A Practical "Implementing a Paper" Checklist

```
[ ] Read the WHOLE paper first (including appendices) before writing any code — architecture
    diagrams often hide details (bias terms, normalization placement, activation choice) that
    only appear in an equation or a sentence buried in Section 4.2.
[ ] Write down the forward-pass shapes for every tensor, layer by layer, BEFORE coding — if you
    can't state "input is (B, T, d_model), after this Linear it's (B, T, d_ff)," you don't yet
    understand the architecture well enough to implement it correctly.
[ ] Implement the smallest possible version first (few layers, tiny hidden size, tiny dataset)
    and confirm it can literally MEMORIZE a handful of examples (overfit a tiny batch to ~0
    loss) before scaling up — this is the fastest way to catch backward-pass/masking bugs
    (Section 19's pitfall list), because a broken gradient path usually can't even memorize.
[ ] Gradient-check (Section 7) any new/custom layer before trusting it in a real training run.
[ ] Match the paper's optimizer, learning rate schedule (Section 22.3), weight decay policy,
    warmup, and batch size as closely as possible — these matter as much as the architecture.
[ ] Log EVERYTHING (loss curves, gradient norms, learning rate over time) — a training run that
    "looks fine" from the final loss number can still be diverging/plateauing early, which log
    curves reveal immediately and a single final number hides.
[ ] Compare against a reference implementation's INTERMEDIATE outputs (not just final metrics)
    where possible — e.g. feed the same input through both implementations and diff the
    attention weights or hidden states after layer 1, to localize a discrepancy fast.
[ ] Report results averaged over multiple seeds (Section 22.1) with variance, not a single run.
```

---

## Learning Path

1. **Week 1**: Sections 1-4 (Autograd engine, building blocks, backprop derivation) — build
   and gradient-check the `Tensor` class until every primitive passes Section 7's checker.
2. **Week 2**: Sections 5-7 (MLP training, optimizers, gradient checking) — train XOR to
   convergence with SGD, then again with Adam; compare convergence speed.
3. **Week 3**: Sections 8-9 (CNN via im2col, RNN/LSTM) — implement and gradient-check both.
4. **Week 4**: Section 10 (attention math + backward derivation) — derive the backward pass on
   paper BEFORE looking at the provided code, then compare.
5. **Week 5**: Sections 11-12 (GPT architecture, pretraining loop) — train the tiny char-level
   GPT until generated text is locally coherent.
6. **Week 6**: Sections 13-16 (fine-tuning theory, full fine-tune, LoRA, decoder/instruction
   fine-tuning with loss masking) — reproduce Section 17's end-to-end pipeline yourself.
7. **Week 7**: Sections 18-19 — map every from-scratch piece to its PyTorch/HF equivalent, then
   read a small chunk of real `nanoGPT` or Hugging Face `transformers`/`peft` source code and
   confirm you can identify every operation.
8. **Week 8**: Sections 20-21 — reimplement the same GPT + full fine-tune + LoRA + masked
   instruction fine-tuning in both PyTorch and TensorFlow; use Section 21.6's table to check
   you can name the equivalent call for every from-scratch concept in either framework.
9. **Week 9**: Section 22 — take a small recent paper with public code, and BEFORE looking at
   its repo, write down your own config, LR schedule, and evaluation protocol; then diff your
   choices against the real implementation to see what you missed.

---

*This guide prioritizes correctness of the underlying math and clarity of implementation over
performance — it will not scale to production-size models as written. The goal is that after
working through it, reading (or writing) a real paper's "Method" section, or the source of a
real framework (PyTorch, TensorFlow, or otherwise), is no longer a black box.*
