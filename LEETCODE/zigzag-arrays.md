# Zigzag Arrays — Counting DP with Prefix/Suffix Sum Optimization

## Problem

Given `n`, `l`, `r`, count arrays of length `n` where:
- Each element is in `[l, r]`
- The array **zigzags**: each element is strictly greater or strictly less than its neighbor

Example: `[1, 4, 2, 5]` zigzags — up, down, up.

---

## How to Identify the Pattern in an Interview

### Trigger words
- "Count arrays" or "number of sequences" → counting DP
- "Each element from a range" → value-based DP state
- "Alternating" / "zigzag" / "up-down" → two-state DP (went up vs went down)
- "Strictly greater/less than neighbor" → transitions depend on value ordering

### The mental checklist
1. What choices do I make? **Pick each element from [l, r]**
2. What constrains the choice? **Must be strictly greater or less than previous, alternating**
3. What do I need to remember? **Last value + direction (went up or went down)**
4. How many ways? → Counting → **sum** transitions, not min/max

### Pattern: Value-Based Counting DP with Prefix/Suffix Sum

> You're counting sequences where each element comes from a range,
> and the transition depends on comparing adjacent values.
> The inner summation over "all valid previous values" becomes a
> prefix or suffix sum.

---

## Your Attempt: Correct but Slow

```python
class Solution:
    def zigZagArrays(self, n: int, l: int, r: int) -> int:
        r = r - l
        l = 0
        MOD = 10**9 + 7
        dp = [[[0, 0] for _ in range((r + 1))] for _ in range(n + 1)]
        for i in range(r + 1):
            dp[0][i][0] = 1
            dp[0][i][1] = 1
        for k in range(1, n + 1):
            for i in range(r + 1):
                dp[k][i][1] = 0
                dp[k][i][0] = 0
                for j in range(i + 1, r + 1):       # ← inner loop: O(R)
                    dp[k][i][0] += dp[k - 1][j][1]
                dp[k][i][0] = dp[k][i][0] % MOD
                for j in range(l, i):                # ← inner loop: O(R)
                    dp[k][i][1] += dp[k - 1][j][0]
                dp[k][i][1] = dp[k][i][1] % MOD
        res = 0
        for i in range(l, r + 1):
            res += dp[n - 1][i][0] + dp[n - 1][i][1]
            res %= MOD
        return res
```

### What's right

- State design is correct: `dp[k][i][state]` = ways to build length `k+1` ending at `i`
- `state 0` = arrived by going down (next must go up)
- `state 1` = arrived by going up (next must go down)
- Base case is correct: single element counts as both states
- Normalization `r = r - l; l = 0` is a nice simplification
- Answer extraction is correct

### What's slow

The two inner `for j` loops make this **O(n × R²)** where R = r - l.

For each `(k, i)` pair, you re-scan all valid `j` values. But consecutive values of `i`
scan **almost the same range**:

```
dp[k][5][0] = dp[k-1][6][1] + dp[k-1][7][1] + dp[k-1][8][1] + dp[k-1][9][1]
dp[k][6][0] =                  dp[k-1][7][1] + dp[k-1][8][1] + dp[k-1][9][1]
dp[k][7][0] =                                   dp[k-1][8][1] + dp[k-1][9][1]
```

You're recomputing overlapping sums. This is the textbook signal for prefix/suffix sums.

---

## The Gap: Recognizing When Inner Loops Are Redundant Summations

### The pattern to spot

Whenever your DP transition looks like:

```python
for i in range(...):
    for j in range(i + 1, ...):    # or range(0, i)
        dp[k][i] += dp[k-1][j]
```

Ask yourself: **"Am I summing a contiguous range of the previous layer?"**

If yes → replace the inner loop with a **precomputed prefix or suffix sum**.

### Why it matters

| Range being summed | Precompute | Lookup |
|---|---|---|
| `dp[k-1][0] + ... + dp[k-1][i-1]` | Prefix sum | `prefix[i]` |
| `dp[k-1][i+1] + ... + dp[k-1][R]` | Suffix sum | `suffix[i+1]` |

Building the prefix/suffix array is O(R). Each lookup is O(1).
Total: O(n × R) instead of O(n × R²).

### How suffix sum works (for dp[k][i][0])

You need: sum of `dp[k-1][j][1]` for all `j > i` (values strictly greater than `i`).

Build a suffix array **right to left**:

```
suffix[R+1] = 0                               (nothing past the end)
suffix[R]   = dp[k-1][R][1]
suffix[R-1] = dp[k-1][R-1][1] + suffix[R]
...
suffix[j]   = dp[k-1][j][1]   + suffix[j+1]
```

Now `dp[k][i][0] = suffix[i+1]` — one lookup, no loop.

### How prefix sum works (for dp[k][i][1])

You need: sum of `dp[k-1][j][0]` for all `j < i` (values strictly less than `i`).

Build a prefix array **left to right**:

```
prefix[0] = 0                                  (nothing before 0)
prefix[1] = dp[k-1][0][0]
prefix[2] = dp[k-1][0][0] + dp[k-1][1][0]
...
prefix[j+1] = prefix[j] + dp[k-1][j][0]
```

Now `dp[k][i][1] = prefix[i]` — one lookup, no loop.

---

## Concrete Trace: R = 4, Building Layer k from Layer k-1

Suppose `dp[k-1][·][1]` = `[3, 1, 4, 2, 5]` (values at indices 0..4):

### Building suffix (for state 0 — "went down, need values above me")

```
suffix[5] = 0
suffix[4] = 5                       (just index 4)
suffix[3] = 2 + 5 = 7               (indices 3,4)
suffix[2] = 4 + 7 = 11              (indices 2,3,4)
suffix[1] = 1 + 11 = 12             (indices 1,2,3,4)
suffix[0] = 3 + 12 = 15             (indices 0,1,2,3,4)
```

Reading off values:
```
dp[k][0][0] = suffix[1] = 12    (sum of values at j=1,2,3,4)
dp[k][1][0] = suffix[2] = 11    (sum of values at j=2,3,4)
dp[k][2][0] = suffix[3] = 7     (sum of values at j=3,4)
dp[k][3][0] = suffix[4] = 5     (sum of values at j=4)
dp[k][4][0] = suffix[5] = 0     (no values above 4)
```

### Verify dp[k][2][0] against brute force

Brute force: `dp[k-1][3][1] + dp[k-1][4][1]` = `2 + 5` = `7` ✓
Suffix lookup: `suffix[3]` = `7` ✓

---

## Evolution of the Solution

### Version 1: Your original (correct, O(n × R²))

3D array, inner loops for summation.

### Version 2: Add prefix/suffix sums (O(n × R))

```python
class Solution:
    def zigZagArrays(self, n: int, l: int, r: int) -> int:
        MOD = 10**9 + 7
        R = r - l
        dp = [[[0, 0] for _ in range(R + 1)] for _ in range(n + 1)]

        for i in range(R + 1):
            dp[0][i][0] = 1
            dp[0][i][1] = 1

        for k in range(1, n + 1):
            suffix = [0] * (R + 2)
            for j in range(R, -1, -1):
                suffix[j] = (suffix[j + 1] + dp[k - 1][j][1]) % MOD

            prefix = [0] * (R + 2)
            for j in range(R + 1):
                prefix[j + 1] = (prefix[j] + dp[k - 1][j][0]) % MOD

            for i in range(R + 1):
                dp[k][i][0] = suffix[i + 1]
                dp[k][i][1] = prefix[i]

        res = 0
        for i in range(R + 1):
            res = (res + dp[n - 1][i][0] + dp[n - 1][i][1]) % MOD
        return res
```

### Version 3: Drop the k dimension (O(n × R) time, O(R) space)

Only the previous layer matters. Rename states to `down[i]` and `up[i]` for clarity.

```python
class Solution:
    def zigZagArrays(self, n: int, l: int, r: int) -> int:
        MOD = 10**9 + 7
        R = r - l

        # down[i] = ways ending at value i, last move was down (next must go up)
        # up[i]   = ways ending at value i, last move was up   (next must go down)
        down = [1] * (R + 1)
        up = [1] * (R + 1)

        for _ in range(1, n):
            new_down = [0] * (R + 1)
            new_up = [0] * (R + 1)

            # suffix sum of up[] — new_down[i] = sum of up[j] for j > i
            s = 0
            for i in range(R, -1, -1):
                new_down[i] = s
                s = (s + up[i]) % MOD

            # prefix sum of down[] — new_up[i] = sum of down[j] for j < i
            s = 0
            for i in range(R + 1):
                new_up[i] = s
                s = (s + down[i]) % MOD

            down, up = new_down, new_up

        return sum(down[i] + up[i] for i in range(R + 1)) % MOD
```

---

## Why the Running Accumulator Works (No Extra Array Needed)

In Version 3, instead of building a separate suffix/prefix array, we use a single
variable `s` as a running accumulator:

**Suffix sum with accumulator (for `new_down`):**
```python
s = 0
for i in range(R, -1, -1):
    new_down[i] = s         # s = sum of up[j] for all j > i (built so far)
    s = (s + up[i]) % MOD   # now include up[i] for future iterations
```

Walk through with `up = [3, 1, 4, 2, 5]` (R = 4):
```
i=4: new_down[4] = 0,  s = 0 + 5 = 5
i=3: new_down[3] = 5,  s = 5 + 2 = 7
i=2: new_down[2] = 7,  s = 7 + 4 = 11
i=1: new_down[1] = 11, s = 11 + 1 = 12
i=0: new_down[0] = 12, s = 12 + 3 = 15
```

Key: we assign `new_down[i] = s` **before** adding `up[i]` to `s`. This ensures
we only count values strictly greater than `i` (not `i` itself).

**Prefix sum with accumulator (for `new_up`):**
```python
s = 0
for i in range(R + 1):
    new_up[i] = s           # s = sum of down[j] for all j < i
    s = (s + down[i]) % MOD # now include down[i] for future iterations
```

Same idea, left to right. Assign before adding ensures strictly less than.

---

## Your Gaps on This Problem

### Gap 1: Not seeing the inner loop as a summation to optimize

Your transitions were:
```python
for j in range(i + 1, r + 1):
    dp[k][i][0] += dp[k - 1][j][1]
```

This is a **contiguous range sum** of the previous layer. Whenever you write
`for j in range(a, b): dp[...] += dp_prev[j]`, you should immediately think:
"Can I precompute this sum?"

**Rule:** If your DP transition sums over a sliding or contiguous range of a
previous layer, replace it with prefix/suffix sums.

### Gap 2: Not reducing dimensions

Your 3D array `dp[k][i][state]` stores all layers, but only `dp[k-1]` is ever read.
This wastes O(n × R) space.

**Rule:** After writing the recurrence, check: "Which previous layers do I actually
read?" If only the immediately previous one → drop that dimension, keep two arrays.

### Gap 3: Not simplifying the accumulator

Building a separate `suffix[]` array and then reading `suffix[i+1]` works but adds
an extra pass. A running accumulator (`s`) does the same work inline.

**Rule:** When building prefix/suffix sums that you use in the same loop direction,
fold them into a running variable. Assign before updating to enforce strict inequality.

### Progression

```
Your solution               →  Identify summation  →  Prefix/suffix  →  Drop dimension  →  Inline accumulator
O(n × R²), 3D array            "this is a range sum"   O(n × R), 3D      O(n × R), 2×1D     O(n × R), clean
```

This same progression applies to MANY counting DP problems.

---

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Your original (inner loops) | O(n × R²) | O(n × R) |
| With prefix/suffix sums | O(n × R) | O(n × R) |
| Space-optimized (final) | O(n × R) | O(R) |

Where R = r - l.

---

## The General Pattern: "Counting DP with Range Transitions"

### Template

Whenever your DP transition sums over **all values in a range** from the previous layer:

```python
# SLOW: O(n × R²)
for i in range(R + 1):
    dp_new[i] = sum(dp_old[j] for j in some_range_depending_on_i)

# FAST: O(n × R)
# Precompute prefix or suffix sum of dp_old, then look up in O(1)
build prefix/suffix of dp_old
for i in range(R + 1):
    dp_new[i] = prefix_or_suffix_lookup(i)
```

### When to use prefix vs suffix

| Transition sums over... | Use |
|---|---|
| `j < i` (all values below current) | **Prefix sum**, built left to right |
| `j > i` (all values above current) | **Suffix sum**, built right to left |
| `j in [i-k, i+k]` (a window around i) | **Prefix sum + subtraction** (`prefix[i+k+1] - prefix[i-k]`) |
| `j in [a, b]` (fixed range, same for all i) | Just compute once, not per-i |

---

## Practice Problems (Same Pattern: Counting DP + Prefix/Suffix Sum)

### Tier 1: Direct Applications

| # | Problem | Difficulty | Why it's relevant |
|---|---------|:----------:|-------------------|
| 1 | [Number of Longest Increasing Subsequence](https://leetcode.com/problems/number-of-longest-increasing-subsequence/) (LC 673) | Medium | Count LIS — transition sums over `j < i` with `nums[j] < nums[i]`. Not directly prefix sum (value-indexed), but same "sum over valid predecessors" idea. |
| 2 | [Count Number of Teams](https://leetcode.com/problems/count-number-of-teams/) (LC 1395) | Medium | Count triplets with increasing/decreasing order. Two-state (ascending/descending), sum over valid predecessors. |
| 3 | [Count Vowels Permutation](https://leetcode.com/problems/count-vowels-permutation/) (LC 1220) | Hard | Count sequences where transitions depend on previous character. Fixed small alphabet, so no prefix sum needed — but identical structure to zigzag. |
| 4 | [Knight Dialer](https://leetcode.com/problems/knight-dialer/) (LC 935) | Medium | Count sequences on a phone pad. Fixed transitions (like zigzag but on a graph). Good warmup for transition-based counting DP. |

### Tier 2: Prefix/Suffix Sum Optimization Required

| # | Problem | Difficulty | Why it's relevant |
|---|---------|:----------:|-------------------|
| 5 | [Number of Ways to Stay in the Same Place](https://leetcode.com/problems/number-of-ways-to-stay-in-the-same-place-after-some-steps/) (LC 1269) | Hard | DP on position × steps. Transitions sum over neighbors — but neighbors are bounded, so running sums help. |
| 6 | [Maximum Number of Points with Cost](https://leetcode.com/problems/maximum-number-of-points-with-cost/) (LC 1937) | Medium | Row-by-row DP. Transition is `dp_prev[j] - |j - i|` = max over left prefix and right suffix. **Exact same prefix/suffix trick** as zigzag. |
| 7 | [Number of Ways to Reach a Position After Exactly k Steps](https://leetcode.com/problems/number-of-ways-to-reach-a-position-after-exactly-k-steps/) (LC 2400) | Medium | Position DP where transitions sum over neighbors. Prefix sum speeds it up. |
| 8 | [Count of Range Sum](https://leetcode.com/problems/count-of-range-sum/) (LC 327) | Hard | Count subarrays with sum in [lower, upper]. Prefix sums + merge sort or BIT. The "count things in a range" mindset is the same. |

### Tier 3: Advanced — Same Optimization, Harder Problems

| # | Problem | Difficulty | Why it's relevant |
|---|---------|:----------:|-------------------|
| 9 | [Odd Even Jump](https://leetcode.com/problems/odd-even-jump/) (LC 975) | Hard | Two-state DP (odd jump up, even jump down) — **very similar to zigzag**. Uses sorted order + monotonic stack instead of prefix sum, but same two-state alternation. |
| 10 | [Frog Jump](https://leetcode.com/problems/frog-jump/) (LC 403) | Hard | DP on (position, last_jump). Transitions depend on last state. Different structure but same "state carries constraint" idea. |
| 11 | [Distinct Subsequences II](https://leetcode.com/problems/distinct-subsequences-ii/) (LC 940) | Hard | Count distinct subsequences. DP where transition sums over previous states — prefix sum optimization is key. |

### Suggested Order

```
Knight Dialer (935) → Count Vowels Permutation (1220)
→ Count Number of Teams (1395) → Zigzag Arrays (this problem)
→ Maximum Number of Points with Cost (1937) → Odd Even Jump (975)
→ Number of Longest Increasing Subsequence (673) → Distinct Subsequences II (940)
```

First four build the "two-state counting DP" muscle.
Last four add the "optimize the transition with prefix/suffix sums" skill.

---

## Recognition Cheat Sheet

| You see... | Think... |
|---|---|
| "Count arrays/sequences" | Counting DP (sum, not min/max) |
| "Each element from a range [l, r]" | Value-based DP: state includes the value |
| "Alternating greater/less" | Two states: went-up and went-down |
| Inner loop sums over `j < i` or `j > i` | Prefix/suffix sum optimization |
| Only previous layer is read | Drop a dimension, keep 2 arrays |
| "Strictly greater" (not ≥) | Assign accumulator BEFORE adding current value |

---

## The Accumulator Trick — When Strict vs Non-Strict Matters

This is subtle and worth memorizing.

**Strictly greater (`j > i`):** assign **before** adding current

```python
s = 0
for i in range(R, -1, -1):
    result[i] = s            # s has values for j > i only
    s = (s + old[i]) % MOD   # now add i, so future iterations include it
```

**Greater or equal (`j >= i`):** add current **before** assigning

```python
s = 0
for i in range(R, -1, -1):
    s = (s + old[i]) % MOD   # add i first
    result[i] = s             # s now has values for j >= i
```

Same logic applies to prefix sums going left-to-right for `j < i` vs `j <= i`.

---

## Summary: What to Practice

1. **Write the brute force first** (you did this well — correct logic, clear states)
2. **Spot the range summation** — look for `for j in range(a, b): dp += dp_prev[j]`
3. **Replace with prefix/suffix sum** — one precomputation pass, O(1) lookups
4. **Drop unnecessary dimensions** — check which layers you actually read
5. **Fold into running accumulator** — cleaner code, no extra arrays

Your brute-force DP instinct is solid. The gap is the **optimization step** — going from
"I have a correct O(n × R²)" to "I see the range sum pattern and apply prefix/suffix
sums to get O(n × R)." That's a mechanical skill you can drill with the practice
problems above.
