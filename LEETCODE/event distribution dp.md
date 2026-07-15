# Element Distribution DP — "Put Each Item Into One of K Buckets"

> The pattern behind Subsequence Pair Count, Tallest Billboard, Profitable Schemes,
> and any problem where you process items one by one and decide **which group each goes to**.

---

## The Pattern in One Sentence

Walk through elements left to right. For each element, decide:
**skip it, put it in group 1, put it in group 2, ..., or put it in group K.**

The DP state tracks whatever summary you need about each group (GCD, sum, length, etc.)
— not the full contents of each group.

---

## How to Recognize It

| You see in the problem...                              | Think...                    |
|--------------------------------------------------------|-----------------------------|
| "Two subsequences" + some property must match          | 2-group distribution        |
| "Split into two subsets" + aggregated constraint       | 2-group distribution        |
| "Partition into groups" + each element in one group    | K-group distribution        |
| "Select disjoint subsequences" + optimize/count        | Multi-group distribution    |
| Each element is independently assigned, not range-split| Distribution, not Partition |

### How It Differs from Partition DP

- **Partition DP (§5):** Split a contiguous array at cut points → groups are contiguous segments
- **Distribution DP (this):** Each element is independently assigned to a group → groups can interleave

```
Partition DP:   [a b c | d e | f g h]    ← groups are contiguous slices
Distribution:   a→G1, b→G2, c→skip, d→G1, e→G2   ← elements freely assigned
```

---

## The Template

### Top-Down (Memoized)

```python
@lru_cache(maxsize=None)
def dp(index, state1, state2):
    """state1, state2 = summary of group1 and group2 so far."""
    if index == n:
        return base_case(state1, state2)

    # Choice 1: skip this element
    res = dp(index + 1, state1, state2)

    # Choice 2: add to group 1
    new_state1 = combine(state1, nums[index])
    res = better(res, dp(index + 1, new_state1, state2))

    # Choice 3: add to group 2
    new_state2 = combine(state2, nums[index])
    res = better(res, dp(index + 1, state1, new_state2))

    return res
```

### Bottom-Up

```python
dp = initial_table()  # dp[state1][state2] = ...
dp[empty][empty] = base_value

for k in range(n):
    dp_new = copy(dp)  # ← CRITICAL: start from a copy, not empty
    for s1 in all_states:
        for s2 in all_states:
            if dp[s1][s2] is not valid:
                continue
            val = dp[s1][s2]
            # skip is already in dp_new (from the copy)

            # add to group 1
            ns1 = combine(s1, nums[k])
            dp_new[ns1][s2] = better(dp_new[ns1][s2], val)

            # add to group 2
            ns2 = combine(s2, nums[k])
            dp_new[s1][ns2] = better(dp_new[s1][ns2], val)

    dp = dp_new
```

---

## When Do You Need a New DP Array? (The Complete Rule)

This is the key question you asked. Here's the universal rule:

### The Fan-Out Rule

> **If processing one element causes a single source state `dp[s]` to write to
> MULTIPLE different destination cells, you need a new array.**

That's it. One source → many destinations = new array needed.

### Why?

When `dp[i][j]` fans out to `dp[g1][j]`, `dp[i][g2]`, and stays at `dp[i][j]`:

```
dp[i][j] ──→ dp[g1][j]     (add to group1)
         ──→ dp[i][g2]     (add to group2)
         ──→ dp[i][j]      (skip)
```

If you update in-place:
1. You write to `dp[g1][j]` (modifying it)
2. Later, when the loop reaches `(g1, j)` as a source, it reads the **already-modified** value
3. This value includes contributions from the current element, so effectively the
   element gets used twice — once at `(i,j)` and again at `(g1,j)`

A new array ensures all reads come from the **previous round** (before this element was processed).

### The Complete Decision Table

| Situation | In-place OK? | Technique | Example |
|-----------|-------------|-----------|---------|
| 1 source → 1 destination, ordered | Yes | Iterate in the safe direction | 0/1 Knapsack (reverse) |
| 1 source → 1 destination, any order OK | Yes | Forward or reverse both work | Unbounded Knapsack |
| 1 source → 2+ destinations | **No** | **New array** | This pattern, LCS, Stock with cooldown |
| All destinations are "later" in iteration | Yes | Forward iteration | Fibonacci, staircase |
| Destinations can be "earlier" in iteration | **No** | **New array** or reverse trick | Varies |

### Worked Examples

#### Example 1: 0/1 Knapsack — In-Place OK

```python
for item in items:
    for w in range(W, weight - 1, -1):    # REVERSE order
        dp[w] = max(dp[w], dp[w - weight] + value)
```

Each `dp[w]` reads from ONE source (`dp[w - weight]`) that's at a **lower** index.
Reverse iteration guarantees the source hasn't been touched yet. **Fan-out = 1, ordered → in-place OK.**

#### Example 2: Stock Buy/Sell with Cooldown — New Variables Needed

```python
for price in prices:
    new_hold = max(hold, cool - price)    # from 2 sources
    new_cash = max(cash, hold + price)    # from 2 sources
    new_cool = cash                       # from 1 source
    hold, cash, cool = new_hold, new_cash, new_cool
```

`cash` state fans out to both `new_hold` (via cool) and `new_cool`.
If you update `cash` first, `cool = cash` would use the new value. **Fan-out > 1 → new variables.**

#### Example 3: LCS — Previous Row Needed

```python
for i in range(1, m + 1):
    dp_new = [0] * (n + 1)
    for j in range(1, n + 1):
        if s1[i-1] == s2[j-1]:
            dp_new[j] = dp_prev[j-1] + 1     # diagonal from previous row
        else:
            dp_new[j] = max(dp_prev[j], dp_new[j-1])
    dp_prev = dp_new
```

`dp_prev[j]` fans out to `dp_new[j]` (not-match case) AND `dp_new[j+1]` (diagonal for next j).
**Fan-out > 1 → need separate row.**

#### Example 4: Subsequence Pair Count — New 2D Array Needed

```python
for num in nums:
    dp_new = copy(dp)
    for g1 in range(maxVal):
        for g2 in range(maxVal):
            if dp[g1][g2] == 0: continue
            val = dp[g1][g2]
            # add to seq1: writes to dp_new[gcd(g1,num)][g2]
            # add to seq2: writes to dp_new[g1][gcd(g2,num)]
            ...
    dp = dp_new
```

State `dp[g1][g2]` fans out to 3 cells (skip + seq1 + seq2). **Fan-out = 3 → new array.**

### The Checklist (Use Before Writing Bottom-Up)

Ask yourself these questions:

```
1. For ONE element, does ONE source state write to MULTIPLE destinations?
   → Yes: NEED new array
   → No: Go to question 2

2. Do destinations ever overlap with sources that haven't been read yet?
   → Yes: NEED new array (or careful iteration order)
   → No: In-place is safe

3. Does iteration order matter?
   → Destination index < source index: iterate in REVERSE
   → Destination index > source index: iterate FORWARD
   → Destination can be anywhere: NEED new array
```

### Visual Summary

```
                     ┌─ 1 destination, ordered ──→ In-place (reverse/forward)
Source state ────────┤
                     └─ 2+ destinations ─────────→ New array / new variables
```

---

## Subsequence Pair Count — Full Walkthrough

### Problem
Given array `nums`, count ordered pairs of non-empty subsequences `(seq1, seq2)`
with `gcd(seq1) == gcd(seq2)`. Subsequences can share indices (they're drawn
independently from `nums`).

### Why This Is Distribution DP
Each element has 3 choices: **skip, add to seq1, add to seq2.**
State = `(gcd of seq1 so far, gcd of seq2 so far)`.

### Top-Down

```python
from functools import lru_cache
import math

class Solution:
    def subsequencePairCount(self, nums: List[int]) -> int:
        n = len(nums)
        MOD = 10**9 + 7

        @lru_cache(maxsize=None)
        def dp(i, g1, g2):
            if i == n:
                return 1 if g1 == g2 and g1 > 0 else 0

            res = dp(i + 1, g1, g2)                            # skip
            ng1 = math.gcd(g1, nums[i]) if g1 > 0 else nums[i]
            res += dp(i + 1, ng1, g2)                           # seq1
            ng2 = math.gcd(g2, nums[i]) if g2 > 0 else nums[i]
            res += dp(i + 1, g1, ng2)                           # seq2
            return res % MOD

        return dp(0, 0, 0)
```

### Bottom-Up (Why new array is needed)

```python
class Solution:
    def subsequencePairCount(self, nums: List[int]) -> int:
        MOD = 10**9 + 7
        maxVal = max(nums) + 1
        dp = [[0] * maxVal for _ in range(maxVal)]
        dp[0][0] = 1

        for num in nums:
            # MUST be a full copy — each dp[g1][g2] fans out to 3 cells
            dp_new = [row[:] for row in dp]

            for g1 in range(maxVal):
                for g2 in range(maxVal):
                    if dp[g1][g2] == 0:
                        continue
                    val = dp[g1][g2]
                    # skip: already included via the copy

                    # add to seq1
                    ng1 = math.gcd(g1, num) if g1 > 0 else num
                    dp_new[ng1][g2] = (dp_new[ng1][g2] + val) % MOD

                    # add to seq2
                    ng2 = math.gcd(g2, num) if g2 > 0 else num
                    dp_new[g1][ng2] = (dp_new[g1][ng2] + val) % MOD

            dp = dp_new

        res = 0
        for g in range(1, maxVal):
            res = (res + dp[g][g]) % MOD
        return res
```

**Why `dp_new = copy(dp)` and not `dp_new = zeros()`?**

The copy handles the **skip transition** for free. Every state from the previous round
carries forward (the element is skipped). Then we ADD the seq1/seq2 transitions on top.

If you use zeros, you must explicitly add the skip: `dp_new[g1][g2] += dp[g1][g2]`.

### Complexity
- Time: O(n × maxVal²)
- Space: O(maxVal²)
- maxVal ≤ 200 (typical constraint), so maxVal² ≤ 40,000 per element

---

## The "New Array" Patterns You'll See Again and Again

### Pattern A: Copy + Accumulate (most common)

```python
dp_new = copy(dp)    # skip transition is free
for each state:
    dp_new[destination] += dp[source]    # other transitions add on top
dp = dp_new
```

Used in: Subsequence Pair Count, Target Sum, Profitable Schemes

### Pattern B: Fresh + Explicit Skip

```python
dp_new = empty()
for each state:
    dp_new[state] += dp[state]           # explicit skip
    dp_new[destination] += dp[source]    # other transitions
dp = dp_new
```

Used when skip needs special handling (e.g., cost for skipping)

### Pattern C: Rolling Variables (when state space is tiny)

```python
hold, cash, cool = ...
new_hold = f(hold, cash, cool)
new_cash = g(hold, cash, cool)
new_cool = h(hold, cash, cool)
hold, cash, cool = new_hold, new_cash, new_cool
```

Used in: Stock buy/sell, state machine DP with few states

---

## Practice Problems

### Core Distribution DP

| # | Problem | Groups | State tracked per group | Difficulty |
|---|---------|--------|------------------------|------------|
| 1 | [Target Sum](https://leetcode.com/problems/target-sum/) (LC 494) | 2 (+ and −) | running sum | Medium |
| 2 | [Partition Equal Subset Sum](https://leetcode.com/problems/partition-equal-subset-sum/) (LC 416) | 2 | running sum | Medium |
| 3 | [Last Stone Weight II](https://leetcode.com/problems/last-stone-weight-ii/) (LC 1049) | 2 | running sum | Medium |
| 4 | [Tallest Billboard](https://leetcode.com/problems/tallest-billboard/) (LC 956) | 2 (left/right) | height difference | Hard |
| 5 | [Profitable Schemes](https://leetcode.com/problems/profitable-schemes/) (LC 879) | 1 group vs skip | (members used, profit) | Hard |
| 6 | [Subsequence Pair Count](https://leetcode.com/problems/find-the-number-of-subsequences-with-equal-gcd/) (LC 3336) | 2 subsequences | GCD of each | Hard |

### Problems That Test "New Array or In-Place?"

| # | Problem | Answer | Why |
|---|---------|--------|-----|
| 7 | [Coin Change](https://leetcode.com/problems/coin-change/) (LC 322) | In-place (forward) | Unbounded: reuse within same item OK |
| 8 | [0/1 Knapsack](https://leetcode.com/problems/partition-equal-subset-sum/) (LC 416) | In-place (reverse) | Fan-out = 1, destination < source |
| 9 | [Coin Change II](https://leetcode.com/problems/coin-change-ii/) (LC 518) | In-place (forward) | Unbounded: want to reuse |
| 10 | [Target Sum](https://leetcode.com/problems/target-sum/) (LC 494) | **New array** | Fan-out = 2: dp[s+num] and dp[s-num] from dp[s] |
| 11 | [Stock with Cooldown](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown/) (LC 309) | **New variables** | hold, cash, cool all feed into each other |
| 12 | [Ones and Zeroes](https://leetcode.com/problems/ones-and-zeroes/) (LC 474) | In-place (reverse) | 2D 0/1 Knapsack, reverse on both dimensions |

### Suggested Practice Order

```
Warmup (in-place OK):
  LC 416 Partition Equal Subset Sum
  LC 322 Coin Change
  LC 518 Coin Change II

See why new array is needed:
  LC 494 Target Sum          ← 2 destinations from each state
  LC 1049 Last Stone Weight II
  LC 309 Stock with Cooldown ← state machine, new variables

Full distribution DP:
  LC 879 Profitable Schemes  ← 2D state + skip/include
  LC 956 Tallest Billboard   ← elegant diff-as-state trick
  LC 3336 Subsequence Pair Count ← the problem that started this
```

---

## Quick Reference: In-Place vs New Array

```
Processing element by element?
│
├── Can each element go to ONLY 1 destination from any state?
│   ├── Destination index < source? → In-place, REVERSE iteration
│   ├── Destination index > source? → In-place, FORWARD iteration
│   └── Destination index = source ± offset? → In-place, pick direction
│
└── Can each element go to 2+ destinations from the same state?
    └── MUST use new array (or new variables if state is small)
```

**When in doubt, use a new array. It's always correct. In-place is an optimization.**

---

## Common Bugs in This Pattern

### Bug 1: Updating in-place when you shouldn't

```python
# WRONG — fans out to 3 destinations, but modifying dp in-place
for g1 in range(maxVal):
    for g2 in range(maxVal):
        dp[gcd(g1,num)][g2] += dp[g1][g2]    # corrupts later reads
        dp[g1][gcd(g2,num)] += dp[g1][g2]    # reads already-modified g1,g2
```

### Bug 2: Starting dp_new from zeros instead of a copy (forgetting skip)

```python
# WRONG — skip transition is lost
dp_new = [[0] * maxVal for _ in range(maxVal)]
for g1 in range(maxVal):
    for g2 in range(maxVal):
        dp_new[gcd(g1,num)][g2] += dp[g1][g2]
        dp_new[g1][gcd(g2,num)] += dp[g1][g2]
        # forgot: dp_new[g1][g2] += dp[g1][g2]  ← skip!
dp = dp_new
```

### Bug 3: Double-counting skip when using copy + explicit skip

```python
# WRONG — skip is counted twice (once from copy, once explicitly)
dp_new = [row[:] for row in dp]    # skip already in here
for g1 in range(maxVal):
    for g2 in range(maxVal):
        dp_new[g1][g2] += dp[g1][g2]    # DOUBLE skip!
        dp_new[gcd(g1,num)][g2] += dp[g1][g2]
```

### Bug 4: Using `deepcopy` when a shallow list copy suffices

```python
# SLOW — deepcopy is 100x slower than list comprehension
import copy
dp_new = copy.deepcopy(dp)

# FAST — row slice creates new list objects
dp_new = [row[:] for row in dp]
```
