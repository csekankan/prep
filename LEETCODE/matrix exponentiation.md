# Matrix Exponentiation for DP — The Complete Guide

## When to Use

You have a DP where:
1. The **same linear transition** is applied at every step
2. The number of steps **n is huge** (up to 10^9)
3. The state space per step is **small** (≤ ~200)

Matrix exponentiation turns O(n × S) into O(S^3 × log n), where S = state size.

| n | S | Brute force DP | Matrix expo | Winner |
|---|---|---|---|---|
| 10^9 | 5 | 5 × 10^9 (TLE) | 125 × 30 = 3750 | Matrix expo |
| 10^9 | 75 | 75 × 10^9 (TLE) | 421875 × 30 ≈ 12.6M | Matrix expo |
| 10^9 | 200 | 200 × 10^9 (TLE) | 8M × 30 = 240M | Matrix expo (tight) |
| 100 | 1000 | 100K | 10^9 × 7 (TLE) | Brute force DP |

**Rule of thumb:** Use matrix expo when **n is large and S is small**. Use regular DP
when S is large but n is manageable.

---

## Recognition Signals

| You see in the problem... | Think matrix exponentiation |
|---|---|
| `n <= 10^9` but state space ≤ ~200 | Can't iterate n steps, but matrix is small |
| "Count sequences of length n" + small alphabet | Each step is same transition matrix |
| Fibonacci-like recurrence with big n | Classic 2×2 matrix |
| "Count paths of length n in a graph" | Adjacency matrix raised to nth power |
| Same DP transition at every step (no step-dependent data) | Linear recurrence → matrix power |
| "Number of ways to reach state X after n steps" | Transition matrix to the nth power |

### The Key Question

> "Is my DP transition the **same** at every step, and does it only use
> **linear combinations** (addition and multiplication by constants) of
> the previous state?"

If yes → you can write it as `new_state = M × old_state` → matrix expo works.

If no (e.g., the transition depends on `nums[i]` which changes each step) → matrix expo
doesn't apply. You need regular DP.

---

## The Core Idea

### Step 1: See That Your DP Is a Linear Recurrence

Take Fibonacci:
```
F(n) = F(n-1) + F(n-2)
```

This is a linear combination of previous states. Write it as matrix multiplication:

```
| F(n)   |   | 1  1 |   | F(n-1) |
| F(n-1) | = | 1  0 | × | F(n-2) |
```

Applying this n-1 times:

```
| F(n)   |   | 1  1 |^(n-1)   | F(1) |
| F(n-1) | = | 1  0 |       × | F(0) |
```

### Step 2: Compute M^n Efficiently

Naive: multiply M × M × M × ... (n times) → O(S^3 × n) — no improvement.

**Repeated squaring:** compute M^1, M^2, M^4, M^8, ... and multiply the ones you need.

```
M^13 = M^8 × M^4 × M^1    (because 13 = 1101 in binary)
```

Only ~log₂(n) multiplications needed. Each multiplication is O(S^3).

**Total: O(S^3 × log n)**

### Step 3: Extract the Answer

Multiply the initial state vector by M^(n-1):

```
final_state = initial_vector × M^(n-1)
answer = sum(final_state)    or    final_state[target_index]
```

---

## The Template

```python
MOD = 10**9 + 7

def mat_mult(A, B):
    """Multiply two matrices mod MOD."""
    rows, mid, cols = len(A), len(B), len(B[0])
    C = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        for k in range(mid):
            if A[i][k] == 0:
                continue
            for j in range(cols):
                C[i][j] = (C[i][j] + A[i][k] * B[k][j]) % MOD
    return C

def mat_pow(M, power):
    """Compute M^power using repeated squaring."""
    size = len(M)
    result = [[int(i == j) for j in range(size)] for i in range(size)]  # identity
    while power:
        if power & 1:
            result = mat_mult(result, M)
        M = mat_mult(M, M)
        power >>= 1
    return result
```

Usage:
```python
# 1. Build transition matrix M (size S × S)
# 2. Build initial state vector V (size 1 × S)
# 3. Compute M^(n-1)
# 4. Multiply V × M^(n-1) → final state
# 5. Extract answer from final state
```

---

## Example 1: Fibonacci (The Simplest Case)

**Problem:** Compute F(n) where F(0) = 0, F(1) = 1, n up to 10^18.

**State:** `[F(k), F(k-1)]` — size 2.

**Transition matrix:**
```
M = | 1  1 |      because  F(k)   = 1×F(k-1) + 1×F(k-2)
    | 1  0 |               F(k-1) = 1×F(k-1) + 0×F(k-2)
```

**Code:**
```python
def fib(n):
    if n <= 1:
        return n
    M = [[1, 1], [1, 0]]
    result = mat_pow(M, n - 1)
    return result[0][0]  # result × [F(1), F(0)] = result × [1, 0]
```

**Complexity:** O(2^3 × log n) = O(8 × 60) for n up to 10^18. Instant.

---

## Example 2: Count Vowel Permutation (LC 1220)

**Problem:** Count strings of length n where transitions follow vowel rules.
Each vowel can only be followed by certain other vowels. n up to 2 × 10^4.

**State:** `[count_a, count_e, count_i, count_o, count_u]` — size 5.

**Transition rules:**
```
a → e
e → a, i
i → a, e, o, u
o → i, u
u → a
```

**Transition matrix** (M[i][j] = 1 if vowel j can follow vowel i):
```
     a  e  i  o  u
a  [ 0  1  0  0  0 ]    a can only be followed by e
e  [ 1  0  1  0  0 ]    e can be followed by a or i
i  [ 1  1  0  1  1 ]    i can be followed by a, e, o, u
o  [ 0  0  1  0  1 ]    o can be followed by i or u
u  [ 1  0  0  0  0 ]    u can only be followed by a
```

**Code:**
```python
def countVowelPermutation(n):
    M = [
        [0, 1, 0, 0, 0],
        [1, 0, 1, 0, 0],
        [1, 1, 0, 1, 1],
        [0, 0, 1, 0, 1],
        [1, 0, 0, 0, 0],
    ]
    Mpow = mat_pow(M, n - 1)
    # Initial: one string of length 1 starting with each vowel
    init = [[1, 1, 1, 1, 1]]
    result = mat_mult(init, Mpow)
    return sum(result[0]) % MOD
```

**Note:** For n ≤ 2×10^4, brute force DP is fine (5 × 20000 = 100K ops). But if n were
10^9, only matrix expo would work. The pattern is the same either way.

---

## Example 3: Knight Dialer (LC 935)

**Problem:** Count phone numbers of length n that a knight can dial. n up to 5000.

**State:** 10 digits (0-9), each with a count. Size 10.

**Transition:** knight moves on phone pad. From digit i, which digits j can you jump to?

```
0 → [4, 6]
1 → [6, 8]
2 → [7, 9]
3 → [4, 8]
4 → [0, 3, 9]
5 → []
6 → [0, 1, 7]
7 → [2, 6]
8 → [1, 3]
9 → [2, 4]
```

**Build M:** `M[i][j] = 1` if a knight on j can jump to i.

**Code:**
```python
def knightDialer(n):
    jumps = {
        0: [4, 6], 1: [6, 8], 2: [7, 9], 3: [4, 8], 4: [0, 3, 9],
        5: [],     6: [0, 1, 7], 7: [2, 6], 8: [1, 3], 9: [2, 4],
    }
    M = [[0] * 10 for _ in range(10)]
    for frm, tos in jumps.items():
        for to in tos:
            M[to][frm] = 1  # column frm contributes to row to

    Mpow = mat_pow(M, n - 1)
    init = [[1] * 10]
    result = mat_mult(init, Mpow)
    return sum(result[0]) % MOD
```

---

## Example 4: Zigzag Arrays II (LC 3700)

**Problem:** Count zigzag arrays of length n, elements in [l, r].
- n up to **10^9** (huge!)
- r - l up to **74** (small!)

**From your Part I solution:**
```python
down_new[i] = sum(up_old[j] for j > i)    # suffix sum
up_new[i]   = sum(down_old[j] for j < i)  # prefix sum
```

This is a linear transition — each new value is a sum of old values.
Two states (up/down) with R+1 values each → naively 2(R+1) state size.

**The symmetry trick:** If you define `down'[i] = down[R - i]`, the two transitions
become the same matrix. So you only need one (R+1) × (R+1) matrix:

```python
R = r - l
M[i][j] = 1  if  i + j < R
```

**Why this works:**
- `down[i]` = sum of `up[j]` for `j > i` = sum of `up[j]` for `j` in `[i+1, R]`
- Reversed: `down'[i] = down[R-i]` = sum of `up[j]` for `j > R-i`
  = sum of `up[j]` for `j` in `[R-i+1, R]`
- The combined matrix entry `M[i][j] = 1 if i + j < R` encodes both transitions

**Full solution:**
```python
def zigZagArrays(n, l, r):
    MOD = 10**9 + 7
    R = r - l

    M = [[int(i + j < R) for j in range(R + 1)] for i in range(R + 1)]
    Mpow = mat_pow(M, n - 1)

    init = [[1] * (R + 1)]
    result = mat_mult(init, Mpow)
    return sum(result[0]) % MOD * 2 % MOD  # ×2 for both starting directions
```

**Complexity:** O(R^3 × log n) = O(75^3 × 30) ≈ 12.6 million. Handles n = 10^9 easily.

---

## Example 5: Count Paths of Length n in a Graph

**Problem:** Given a graph with k nodes, count paths of exactly length n.

**Key fact:** If A is the adjacency matrix, then `A^n[i][j]` = number of paths of
length n from node i to node j.

**Why:** A^1[i][j] = 1 if there's an edge (path of length 1). A^2[i][j] = sum over k
of A[i][k] × A[k][j] = number of 2-step paths through any intermediate node k. By
induction, A^n counts n-step paths.

**Code:**
```python
def count_paths(adj_matrix, n, start, end):
    Apow = mat_pow(adj_matrix, n)
    return Apow[start][end]
```

This is the underlying reason matrix expo works for ALL sequence counting problems —
you're counting paths of length n in the state transition graph.

---

## How to Build the Transition Matrix from Your DP

### Step 1: Identify the state vector

List all DP values that the recurrence reads from the previous step.

```
Example: dp[i] depends on dp[i-1] and dp[i-2]
State vector: [dp[k], dp[k-1]]  — size 2
```

### Step 2: Write each new state as a linear combination of old states

```
dp[k]   = 1 × dp[k-1] + 1 × dp[k-2]
dp[k-1] = 1 × dp[k-1] + 0 × dp[k-2]
```

### Step 3: Read off the matrix

Each equation becomes a row of M:

```
M = | 1  1 |    ← coefficients for dp[k]
    | 1  0 |    ← coefficients for dp[k-1]
```

### Step 4: Verify with a small case

Compute M^2 by hand and check it gives the right values for step 2.

### Common Gotcha: Non-Linear Transitions

If your DP has `dp[i] = max(dp[i-1], dp[i-2])` — that's NOT linear. Can't use
matrix expo. The operations must be **addition and scalar multiplication only**.

(There is "tropical semiring" matrix expo that works with max/min + addition, but
that's rare and advanced.)

---

## Handling Extra State Dimensions

Sometimes your DP state has multiple dimensions but you can flatten them.

### Example: Tiling a 2×n Board

State: which cells in the current column are filled. For a 2×n board, the column has
2 cells → 4 possible states (00, 01, 10, 11).

Transition matrix is 4×4. Raise to nth power.

### Example: Count Strings with No "abc" Substring

State: how much of the forbidden pattern "abc" you've matched so far.
Possible states: matched 0 chars, 1 char ("a"), 2 chars ("ab"). Size = 3.

At each position, try all 26 characters, compute new match state.
Transition matrix is 3×3 (entries may be > 1, representing multiple characters).

### General Rule

If your DP is `dp[step][state]` and:
- `step` goes up to n (huge)
- `state` has S possible values (small)
- Transition from step k to k+1 is the same for all k

→ Build an S×S transition matrix, raise to n-1.

---

## Optimization: When the Matrix Has Structure

### Lower-Triangular or Upper-Triangular

If most entries are 0, matrix mult is faster in practice (the `if A[i][k] == 0: continue`
optimization in the template helps).

### Symmetric Matrix

Can sometimes exploit symmetry to halve the state size (as in Zigzag Arrays II).

### Companion Matrix (Linear Recurrence)

For a k-th order linear recurrence `a[n] = c1×a[n-1] + c2×a[n-2] + ... + ck×a[n-k]`,
the companion matrix is always:

```
| c1  c2  c3  ...  ck |
| 1   0   0   ...  0  |
| 0   1   0   ...  0  |
| ...                  |
| 0   0   ...  1   0  |
```

First row = coefficients. Below = shifted identity. Size = k.

For Fibonacci: k=2, c1=1, c2=1 → `[[1,1],[1,0]]`.

For Tribonacci: k=3, c1=c2=c3=1 → `[[1,1,1],[1,0,0],[0,1,0]]`.

---

## When Matrix Expo Does NOT Apply

| Situation | Why it fails | What to use instead |
|---|---|---|
| Transition depends on `nums[i]` | Matrix changes each step | Regular DP |
| `min`/`max` in transition (not sum) | Not a linear operation | Regular DP (or tropical semiring — rare) |
| State space is huge (10^5+) | O(S^3) per multiply is too slow | Regular DP, optimize with prefix sums |
| n is small (≤ 10^5) | Regular DP is fast enough | Regular DP (simpler to code) |
| Transition graph changes per step | No single matrix to exponentiate | Segment tree of matrices (advanced) |

### The Edge Case: Different Matrix Per Step but Repeated Blocks

If the transition alternates between two matrices A and B:
```
step 1: A, step 2: B, step 3: A, step 4: B, ...
```
Then two steps = B × A. Exponentiate (B × A) to the (n/2)th power.

More generally: if the transition has period p, group p matrices into one product
and exponentiate that.

---

## Practice Problems

### Tier 1: Direct Matrix Exponentiation

| # | Problem | Matrix Size | Why |
|---|---------|:-----------:|-----|
| - | Fibonacci Number (LC 509) | 2×2 | The simplest possible case |
| - | Tribonacci Number (LC 1137) | 3×3 | 3rd order recurrence |
| 1220 | [Count Vowels Permutation](https://leetcode.com/problems/count-vowels-permutation/) | 5×5 | Fixed transition graph, small alphabet |
| 935 | [Knight Dialer](https://leetcode.com/problems/knight-dialer/) | 10×10 | Phone pad transitions |
| 3700 | [Zigzag Arrays II](https://leetcode.com/problems/number-of-zigzag-arrays-ii/) | 75×75 | Symmetry trick to halve state |

### Tier 2: Need to Derive the Matrix

| # | Problem | Matrix Size | Key Insight |
|---|---------|:-----------:|-------------|
| 790 | [Domino and Tromino Tiling](https://leetcode.com/problems/domino-and-tromino-tiling/) | 4×4 | Column states for 2×n board |
| 552 | [Student Attendance Record II](https://leetcode.com/problems/student-attendance-record-ii/) | 6×6 | State = (absent_count, consecutive_late) |
| 1411 | [Number of Ways to Paint N×3 Grid](https://leetcode.com/problems/number-of-ways-to-paint-n-3-grid/) | 12×12 | Column coloring states |
| 2851 | [String Transformation](https://leetcode.com/problems/string-transformation/) | varies | KMP states + matrix expo |

### Tier 3: Advanced (Matrix Expo + Other Techniques)

| # | Problem | Trick |
|---|---------|-------|
| 1622 | [Fancy Sequence](https://leetcode.com/problems/fancy-sequence/) | Affine transformation matrices |
| 1916 | [Count Ways to Build Rooms in an Ant Colony](https://leetcode.com/problems/count-ways-to-build-rooms-in-an-ant-colony/) | Tree DP + combinatorics |

### Suggested Order

```
Fibonacci (509) → Tribonacci (1137)
→ Knight Dialer (935) → Count Vowels Permutation (1220)
→ Domino Tromino Tiling (790) → Student Attendance Record II (552)
→ Zigzag Arrays II (3700) → Paint N×3 Grid (1411)
→ String Transformation (2851)
```

---

## Quick Reference Cheat Sheet

```
1. Is the transition the SAME at every step?
   No  → regular DP, matrix expo won't help
   Yes → continue

2. Is the transition LINEAR (sums and scalar mults only)?
   No  (has min/max) → regular DP
   Yes → continue

3. Is n large (>10^5) and state space small (<200)?
   No  → regular DP is fine
   Yes → USE MATRIX EXPONENTIATION

4. Build it:
   a) List all state values → that's your vector size S
   b) Write new_state[i] = sum of coeff × old_state[j] → that's row i of M
   c) M^(n-1) via repeated squaring
   d) Multiply initial vector × M^(n-1)
   e) Read off answer

Complexity: O(S^3 × log n)
```

---

## Connection to Other Techniques

| Technique | What it exponentiates | Use case |
|---|---|---|
| Matrix exponentiation | Matrix multiplication | Linear recurrences, counting paths |
| Binary lifting | Parent pointers | LCA on trees |
| Sparse table | Range queries | RMQ (range min/max) |
| Segment tree of matrices | Product of different matrices per range | When transition varies by step, answer range queries |

All four use the same **repeated squaring** / **doubling** principle. The difference is
what operation you're accelerating.
