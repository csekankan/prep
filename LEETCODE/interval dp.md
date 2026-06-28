# LC 312 — Burst Balloons

## Problem
Given n balloons with values, burst them to maximize coins.
Bursting balloon i gives `nums[left] * nums[i] * nums[right]` coins,
where left and right are the nearest un-burst neighbors.

---

## How to Identify the Pattern

### Trigger words
- "Burst/remove elements" + "neighbors change after removal" → interval DP
- "Order of removal matters" + "optimize total" → think about which to remove LAST

### The key mental shift
Thinking "which balloon to burst FIRST" is natural but leads to chaos —
after bursting, neighbors shift and everything depends on future decisions.

Thinking "which balloon to burst LAST" is the trick — when a balloon is the
last one burst in a range, you KNOW its neighbors (they're the range boundaries).

---

## The Critical Insight: Burst LAST, Not First

When you burst balloon k **last** in range [l, r]:

```
Boundaries:    nums[l-1]  ...  nums[k]  ...  nums[r+1]
                  ↑                              ↑
            still exists                   still exists
            (outside range)                (outside range)

Everything else in [l,r] is already gone.
So k's neighbors ARE l-1 and r+1. Guaranteed.

Coins for this last burst = nums[l-1] * nums[k] * nums[r+1]
```

This means the boundaries are **always l-1 and r+1** — no need to track them separately.

---

## Your Attempt (with analysis)

```python
def maxCoins(self, nums: List[int]) -> int:
    nums = [1] + nums + [1]
    n = len(nums)
    @lru_cache(None)
    def solve(l, r, prev, end):         # ← prev and end are redundant!
        if l > r:
            return 0
        if l == r:
            return nums[prev] * nums[l] * nums[end]
        maxCoin = 0
        itr = l
        while itr <= r:
            coin = nums[prev] * nums[itr] * nums[end]
            coin += solve(l, itr-1, prev, itr)    # prev = l-1 always
            coin += solve(itr+1, r, itr, end)     # end = r+1 always
            itr += 1
            maxCoin = max(maxCoin, coin)
        return maxCoin
    return solve(1, n-2, 0, n-1)
```

### What's right
- The logic is correct — you're choosing which balloon to burst last in [l, r]
- The recursive structure is sound
- It produces correct answers

### What's suboptimal

**1. Redundant parameters in cache**

`prev` is always `l-1`, `end` is always `r+1`. Trace it:
```
solve(1, n-2, 0, n-1)          prev = 1-1 = 0 ✓    end = (n-2)+1 ✓

  solve(l, k-1, prev, k)       prev = l-1 ✓         end = (k-1)+1 = k ✓
  solve(k+1, r, k, end)        prev = (k+1)-1 = k ✓ end = r+1 ✓
```

Every single call: `prev == l-1`, `end == r+1`. Always.

This means you're hashing 4 values instead of 2. The number of unique states is
still O(n²), but the extra parameters:
- Make the code harder to read and reason about
- Add hashing overhead
- Obscure the insight that boundaries are fixed by the range

**2. `while` loop instead of `for`** — minor style issue

**3. Unused variable `res = l`**

---

## Clean Top-Down Solution

```python
from functools import lru_cache
from typing import List

def maxCoins(self, nums: List[int]) -> int:
    nums = [1] + nums + [1]
    n = len(nums)

    @lru_cache(None)
    def dp(l: int, r: int) -> int:
        if l > r:
            return 0
        best = 0
        for k in range(l, r + 1):
            # k is the LAST balloon to burst in [l, r]
            # Its neighbors at that point are l-1 and r+1
            coins = nums[l - 1] * nums[k] * nums[r + 1]
            coins += dp(l, k - 1) + dp(k + 1, r)
            best = max(best, coins)
        return best

    return dp(1, n - 2)
```

2 parameters, same logic, same O(n³) time.

---

## Bottom-Up Solution

```python
def maxCoins(self, nums: List[int]) -> int:
    nums = [1] + nums + [1]
    n = len(nums)
    dp = [[0] * n for _ in range(n)]

    # Fill by increasing range length
    for length in range(1, n - 1):           # range length 1 to n-2
        for l in range(1, n - length):       # left boundary
            r = l + length - 1               # right boundary
            for k in range(l, r + 1):        # last balloon to burst
                coins = nums[l - 1] * nums[k] * nums[r + 1]
                coins += dp[l][k - 1] + dp[k + 1][r]
                dp[l][r] = max(dp[l][r], coins)

    return dp[1][n - 2]
```

### Why fill by increasing length?
`dp[l][r]` depends on `dp[l][k-1]` and `dp[k+1][r]` — both are **smaller ranges**.
So we must fill shorter ranges first. This is the hallmark of interval DP.

### Loop bounds explained
```
nums = [1, 3, 1, 5, 8, 1]    (after padding)
index:  0  1  2  3  4  5

Balloons are indices 1..4 (n-2 = 4)

length=1: [1,1], [2,2], [3,3], [4,4]     ← single balloons
length=2: [1,2], [2,3], [3,4]
length=3: [1,3], [2,4]
length=4: [1,4]                            ← the full range (answer)
```

---

## Dry Run: `[3, 1, 5, 8]`

```
Padded: [1, 3, 1, 5, 8, 1]
Index:   0  1  2  3  4  5

Length 1 (single balloons):
  dp[1][1]: k=1, coins = nums[0]*nums[1]*nums[2] = 1*3*1 = 3.        dp[1][1] = 3
  dp[2][2]: k=2, coins = nums[1]*nums[2]*nums[3] = 3*1*5 = 15.       dp[2][2] = 15
  dp[3][3]: k=3, coins = nums[2]*nums[3]*nums[4] = 1*5*8 = 40.       dp[3][3] = 40
  dp[4][4]: k=4, coins = nums[3]*nums[4]*nums[5] = 5*8*1 = 40.       dp[4][4] = 40

Length 2:
  dp[1][2]: 
    k=1: 1*3*5 + dp[2][2] = 15 + 15 = 30
    k=2: 1*1*5 + dp[1][1] = 5 + 3 = 8
    dp[1][2] = 30

  dp[2][3]:
    k=2: 3*1*8 + dp[3][3] = 24 + 40 = 64
    k=3: 3*5*8 + dp[2][2] = 120 + 15 = 135
    dp[2][3] = 135

  dp[3][4]:
    k=3: 1*5*1 + dp[4][4] = 5 + 40 = 45
    k=4: 1*8*1 + dp[3][3] = 8 + 40 = 48
    dp[3][4] = 48

Length 3:
  dp[1][3]:
    k=1: 1*3*8 + dp[2][3] = 24 + 135 = 159
    k=2: 1*1*8 + dp[1][1] + dp[3][3] = 8 + 3 + 40 = 51
    k=3: 1*5*8 + dp[1][2] = 40 + 30 = 70
    dp[1][3] = 159

  dp[2][4]:
    k=2: 3*1*1 + dp[3][4] = 3 + 48 = 51
    k=3: 3*5*1 + dp[2][2] + dp[4][4] = 15 + 15 + 40 = 70
    k=4: 3*8*1 + dp[2][3] = 24 + 135 = 159
    dp[2][4] = 159

Length 4 (full range):
  dp[1][4]:
    k=1: 1*3*1 + dp[2][4] = 3 + 159 = 162
    k=2: 1*1*1 + dp[1][1] + dp[3][4] = 1 + 3 + 48 = 52
    k=3: 1*5*1 + dp[1][2] + dp[4][4] = 5 + 30 + 40 = 75
    k=4: 1*8*1 + dp[1][3] = 8 + 159 = 167  ← MAX!
    dp[1][4] = 167

Answer: 167 ✓

Optimal order: burst 3 first, then 1, then 5, then 8 last.
```

---

## The Pattern: Interval DP

### When to use
- Elements are removed/merged and **neighbors change** after each operation
- You need to consider **all possible orderings** of operations
- Subproblems are **contiguous ranges** [l, r]

### The trick: think about the LAST operation
"Which element is processed LAST in this range?" fixes the boundaries
and makes subproblems independent (left side and right side don't interact).

### The template
```python
# dp[l][r] = optimal result for range [l, r]
# For each k in [l, r] as the LAST element processed:
#   dp[l][r] = optimize(cost(k, l-1, r+1) + dp[l][k-1] + dp[k+1][r])

# Fill order: increasing range length (small ranges first)
# Answer: dp[1][n-2] (or dp[0][n-1] depending on padding)
```

### Related problems (same interval DP pattern)

| # | Problem | Link | The "last operation" |
|---|---------|------|---------------------|
| 312 | Burst Balloons | [link](https://leetcode.com/problems/burst-balloons/) | Last balloon to burst |
| 1039 | Min Score Triangulation | [link](https://leetcode.com/problems/minimum-score-triangulation-of-polygon/) | Last triangle to form |
| 546 | Remove Boxes | [link](https://leetcode.com/problems/remove-boxes/) | Last box group to remove (harder) |
| 664 | Strange Printer | [link](https://leetcode.com/problems/strange-printer/) | Last character to print |
| 1000 | Min Cost to Merge Stones | [link](https://leetcode.com/problems/minimum-cost-to-merge-stones/) | Last merge operation |
| 87 | Scramble String | [link](https://leetcode.com/problems/scramble-string/) | Where to split |

### Practice order
1. **312 — Burst Balloons** (this problem, the classic)
2. **1039 — Min Score Triangulation** (same structure, geometric intuition)
3. **664 — Strange Printer** (different cost function, same range DP)
4. **1000 — Min Cost to Merge Stones** (adds a constraint on merge size)
5. **546 — Remove Boxes** (hardest — needs an extra dimension)

---

## Your Gap: Not Seeing That Boundaries Are Fixed

The reason you added `prev` and `end` as parameters is that you were thinking:
"When I burst balloon k, its neighbors depend on what else has been burst."

That's true if you burst k FIRST. But if k is the LAST in range [l, r],
its neighbors are guaranteed to be l-1 and r+1 — everything else is gone.

**The mental shift:**
```
Burst FIRST → neighbors are unpredictable → need to track them → 4 params
Burst LAST  → neighbors are the range boundaries → always known → 2 params
```

This "think about the last operation" trick applies to ALL interval DP problems.
Whenever you're tempted to add extra parameters to track state, ask yourself:
"If this is the LAST operation, do I already know the state?"

Usually the answer is yes.

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Your solution (4 params) | O(n³) correct, but extra cache overhead | O(n²) |
| Clean top-down (2 params) | O(n³) | O(n²) |
| Bottom-up | O(n³) | O(n²) |

All are O(n³). The bottom-up version tends to be faster in Python due to
no function call overhead and no hash-based caching.

---

# LC 546 — Remove Boxes (The Hard Interval DP)

## Problem
Given boxes with colors (positive integers), remove contiguous same-colored boxes
to earn k² points (k = number removed in that group). Maximize total points.

```
boxes = [1, 3, 2, 2, 2, 3, 4, 3, 1]

One possible sequence:
  [1, 3, 2, 2, 2, 3, 4, 3, 1]
  Remove [2,2,2] → 3² = 9 points    → [1, 3, 3, 4, 3, 1]
  Remove [3,3,3]  → wait, 3s aren't contiguous yet!
  Remove [4]     → 1² = 1 point     → [1, 3, 3, 3, 1]
  Remove [3,3,3] → 3² = 9 points    → [1, 1]
  Remove [1,1]   → 2² = 4 points    → []
  Total: 9 + 1 + 9 + 4 = 23 ✓ (this is the max)
```

---

## Why This is Harder Than Burst Balloons

In Burst Balloons, `dp(l, r)` is enough — the range boundaries tell you everything.

In Remove Boxes, `dp(l, r)` is NOT enough. Why?

```
Consider boxes = [1, 2, 1]

dp(0, 2) = max points for [1, 2, 1]
  Remove 2 first: 1 point → [1, 1] → remove together: 4 points → total = 5

But what if this subarray has extra 1s AFTER it?
  [1, 2, 1, | 1, 1]   ← two extra 1s attached

Now: remove 2 (1 pt) → [1, 1, 1, 1] → remove all: 16 points → total = 17

The answer for [1, 2, 1] DEPENDS on what's outside the range!
```

This is why you need an **extra parameter** — unlike Burst Balloons where 2 params suffice.

---

## How to Identify This Pattern

### When standard interval DP fails
Ask: "Does the value of dp(l, r) depend on context OUTSIDE [l, r]?"

- **Burst Balloons:** No — boundaries are fixed at l-1 and r+1 → 2 params enough
- **Remove Boxes:** Yes — same-colored boxes outside can merge with inside → need extra param

### Trigger
- "Remove contiguous same-colored groups" + "score depends on group SIZE"
- Merging across gaps (remove stuff in between to create bigger groups)

---

## The Key Insight: What Extra State Do We Need?

`dp(l, r, k)` = max points from `boxes[l..r]` given that `k` extra boxes
of the same color as `boxes[l]` are attached **before** index l.

Why `boxes[l]`? Because those extra boxes will merge with `boxes[l]` when we
eventually remove it.

```
k extra boxes     the subarray
[1, 1, 1]  +  [1, 2, 3, 1, 1]
 ←─ k=3 ──→   l=0          r=4

dp(0, 4, 3) = max points considering these 3 extra 1s
```

---

## The Two Choices

At each state `dp(l, r, k)`, we decide what to do with `boxes[l]`:

### Choice 1: Remove boxes[l] immediately (with the k extras)

Remove `boxes[l]` along with the k extra copies → `(k+1)²` points.
Then solve the rest: `dp(l+1, r, 0)` (no extras for the next box).

```
[1,1,1] + [1, 2, 3, 1, 1]
           ^
Remove this 1 + the 3 extras = 4 ones → 4² = 16 points
Then solve [2, 3, 1, 1] with 0 extras
```

### Choice 2: Merge boxes[l] with a matching box deeper in the range

Find some `boxes[m] == boxes[l]` where l < m ≤ r.
Remove everything between l+1 and m-1 first (clearing the path),
then merge boxes[l] with boxes[m]:

```
[1,1,1] + [1, 2, 3, 1, 1]
           ^        ^
           l   m=3 (also a 1)

Step 1: Solve dp(l+1, m-1, 0) = dp(1, 2, 0) = max points for [2, 3]
Step 2: Now boxes[l] merges with boxes[m]:
        [1,1,1,1] + [1, 1]   ← k increases to k+1 = 4
        Solve dp(m, r, k+1) = dp(3, 4, 4)
```

Total: `dp(l+1, m-1, 0) + dp(m, r, k+1)`

### The recurrence

```
dp(l, r, k) = max(
    (k+1)² + dp(l+1, r, 0),                              # choice 1: remove now
    max over m where boxes[m]==boxes[l] of:
        dp(l+1, m-1, 0) + dp(m, r, k+1)                   # choice 2: merge
)
```

---

## Solution

```python
from functools import lru_cache
from typing import List

def removeBoxes(self, boxes: List[int]) -> int:

    @lru_cache(None)
    def dp(l: int, r: int, k: int) -> int:
        """Max points for boxes[l..r] with k extra boxes of color boxes[l] before l."""
        if l > r:
            return 0

        # Optimization: absorb consecutive same-colored boxes at the start
        # (l and k are local — lru_cache keys on the ORIGINAL args, which is fine)
        while l + 1 <= r and boxes[l + 1] == boxes[l]:
            l += 1
            k += 1

        # Choice 1: remove boxes[l] and the k extras now
        result = (k + 1) ** 2 + dp(l + 1, r, 0)

        # Choice 2: find a matching box deeper, merge
        for m in range(l + 2, r + 1):
            if boxes[m] == boxes[l]:
                result = max(result, dp(l + 1, m - 1, 0) + dp(m, r, k + 1))

        return result

    return dp(0, len(boxes) - 1, 0)
```

### Why the optimization (absorb consecutive)?
If `boxes[l]` and `boxes[l+1]` are the same color, we should always group them
together — there's never a benefit to separating adjacent same-colored boxes.
This reduces the search space significantly.

### Note on lru_cache + while loop
The while loop modifies local `l` and `k`, but `lru_cache` caches based on the
**original** arguments. This is correct: calling `dp(0, 5, 0)` always absorbs the
same way and returns the same result. There's minor cache redundancy (e.g.,
`dp(0,5,0)` and `dp(1,5,1)` may compute the same thing), but no correctness issue.

---

## Dry Run: `[1, 3, 2, 2, 2, 3, 4, 3, 1]`

```
dp(0, 8, 0): boxes[0]=1

  Choice 1: remove 1 now → 1² + dp(1, 8, 0) = 1 + dp(1,8,0)

  Choice 2: find other 1s in range
    m=8: boxes[8]=1 → dp(1, 7, 0) + dp(8, 8, 1)
                       solve [3,2,2,2,3,4,3]   solve [1] with 1 extra
                                                = (1+1)² = 4

  For dp(1, 7, 0): boxes = [3, 2, 2, 2, 3, 4, 3]
    Absorb consecutive 3s: just boxes[1]=3, k stays 0

    Choice 1: remove 3 → 1 + dp(2, 7, 0)
    
    For dp(2, 7, 0): boxes = [2, 2, 2, 3, 4, 3]
      Absorb consecutive 2s: l moves to 4, k becomes 2
      Now: dp(4, 7, 2) with boxes[4]=3
      
      Choice 1: remove 3 + 2 extras = 3² = 9 + dp(5, 7, 0)
        dp(5, 7, 0) = [4, 3] ... small subproblem
      
      Choice 2: m=7 (boxes[7]=3=boxes[4])
        dp(5, 6, 0) + dp(7, 7, 3) = solve [4,3] + (3+1)² = ... + 16

  ... (many branches, the recursion explores all and caches results)

Answer: 23
```

---

## Comparison: Burst Balloons vs Remove Boxes

| Aspect | LC 312 (Burst Balloons) | LC 546 (Remove Boxes) |
|--------|------------------------|----------------------|
| **State** | `dp(l, r)` — 2 params | `dp(l, r, k)` — 3 params |
| **Why?** | Boundaries fixed at l-1, r+1 | Extra same-colored boxes from outside affect score |
| **Key idea** | Which to burst LAST | Remove immediately vs merge with matching box deeper |
| **Cost** | Product of neighbors | k² (group size squared) |
| **Time** | O(n³) | O(n⁴) |
| **Space** | O(n²) | O(n³) |

### When do you need the extra parameter?
> When the optimal strategy for a subrange **depends on context outside the range**
> (boxes waiting to merge, characters to match, etc.)

If the cost only depends on range boundaries → 2 params (Burst Balloons).
If the cost depends on accumulated state from outside → 3+ params (Remove Boxes).

---

## How to Approach Remove Boxes in an Interview

### Step 1: Try standard interval DP
Start with `dp(l, r)` and realize it doesn't work —
"the answer for [1,2,1] changes if there are extra 1s outside."

### Step 2: Ask "what extra info do I need?"
The answer depends on how many same-colored boxes are waiting to merge.
→ Add parameter k = number of extras matching boxes[l].

### Step 3: Write the two choices
1. Remove boxes[l] now → `(k+1)² + dp(l+1, r, 0)`
2. Merge with deeper match → `dp(l+1, m-1, 0) + dp(m, r, k+1)`

### Step 4: Add the optimization
Absorb consecutive same-colored boxes at the start of the range.

### Step 5: Verify complexity
States: O(n³) — (l, r, k) where l,r ∈ [0,n), k ∈ [0,n).
Work per state: O(n) scan for matching m.
Total: O(n⁴). For n ≤ 100, this is 10⁸ — tight but passes.

---

## The Mental Framework: When Standard Interval DP Isn't Enough

```
1. Start with dp(l, r) — does it capture everything?
   ↓ YES → done (Burst Balloons, Triangulation)
   ↓ NO  → what external context matters?

2. Identify the missing info:
   - "How many same-colored items are waiting?" → add k parameter
   - "What was the last action?" → add action parameter
   - "Is this range flipped?" → add boolean parameter

3. Write transitions as choices:
   - "Process the first/last element now" vs "merge it with something deeper"

4. Verify: does the added parameter keep the state space polynomial?
   - k ∈ [0, n] → O(n³) states → O(n⁴) total → acceptable for n ≤ 100
```

---

# LC 664 — Strange Printer

## Problem
A strange printer can print a contiguous sequence of the same character in one turn.
It can overwrite previously printed characters. Given string s, find the minimum
number of turns to print it.

```
s = "aba"
Turn 1: print "aaa"   → [a, a, a]
Turn 2: print "b" at position 1  → [a, b, a]
Answer: 2 turns

s = "aaabbb"
Turn 1: print "aaa"   → [a, a, a, _, _, _]
Turn 2: print "bbb"   → [a, a, a, b, b, b]
Answer: 2 turns
```

---

## Why This Problem Feels Impossible at First

The printer OVERWRITES. So the order of printing matters.
You might print a long range of 'a', then overwrite the middle with 'b', 
then overwrite part of 'b' with 'c'. Thinking about print ORDER is overwhelming.

**The trick: DON'T think about print order. Think about which characters SHARE a turn.**

---

## Building the Intuition Step by Step

### Step 1: Simplest cases

```
"a"     → 1 turn (obvious)
"ab"    → 2 turns (different chars, need separate turns)
"aa"    → 1 turn (same char, one turn covers both)
"aba"   → 2 turns (print 'aaa', overwrite middle with 'b')
```

For "aba": the two 'a's SHARE a turn. The 'b' needs its own turn.
We saved a turn because s[0] == s[2].

### Step 2: The key observation

If `s[l] == s[r]`, then printing `s[l..r]` costs the same as printing `s[l..r-1]`.

Why? When you print `s[l]`, you can extend that print all the way to position r
(since they're the same character). Then everything between gets overwritten by
later turns. The rightmost character comes "for free."

```
s = "aba"

dp("aba") = dp("ab")    because s[0]=='a'==s[2], the last 'a' is free
dp("ab")  = 2            two different characters
Answer: 2 ✓
```

### Step 3: What if s[l] != s[r]?

Then we can't get the last character for free. We need to split the range and
try every possible split point:

```
dp(l, r) = min over k from l to r-1 of { dp(l, k) + dp(k+1, r) }
```

Split into two independent subproblems, print each separately.

### Step 4: But we can do better with matching characters

Even when `s[l] != s[r]`, there might be a character `s[m]` inside the range
where `s[l] == s[m]`. We can merge them:

```
s = "abca"    s[0]='a', s[3]='a'

dp(0, 3) = dp(0, 2)    because s[0]==s[3], last 'a' is free
dp(0, 2) = dp("abc") = 3
Answer: 3

But also consider:
dp(0, 3) = dp(0, 0) + dp(1, 3) = 1 + dp("bca")
dp("bca") = 3
Total = 4 (worse)

So the "free character" insight wins here.
```

---

## The Recurrence

```
dp(l, r) = minimum turns to print s[l..r]

Base case:
  l > r  → 0
  l == r → 1

If s[l] == s[r]:
  dp(l, r) = dp(l, r-1)     ← s[r] comes free with s[l]'s turn

If s[l] != s[r]:
  dp(l, r) = min over k from l to r-1 of { dp(l, k) + dp(k+1, r) }
```

Wait — this isn't quite right. Even when `s[l] == s[r]`, we should ALSO check
all split points, because splitting might give a better answer in some cases.

Actually, the cleaner formulation:

```
dp(l, r) = dp(l, r-1) + 1     ← worst case: print s[r] as a separate turn

Then for each m in [l, r-1] where s[m] == s[r]:
  dp(l, r) = min(dp(l, r), dp(l, m) + dp(m+1, r-1))
  
  Why? s[m] and s[r] are the same character. When we print s[m], we extend
  that print all the way to r. So s[r] is covered by s[m]'s turn.
  Then we just need to print the stuff between m+1 and r-1 separately.
```

---

## Solution

```python
from functools import lru_cache

def strangePrinter(self, s: str) -> int:
    # Remove consecutive duplicates (they're always free)
    cleaned = [s[0]]
    for ch in s[1:]:
        if ch != cleaned[-1]:
            cleaned.append(ch)
    s = cleaned
    n = len(s)

    @lru_cache(None)
    def dp(l: int, r: int) -> int:
        if l > r:
            return 0
        if l == r:
            return 1

        # Default: print s[r] as its own turn
        result = dp(l, r - 1) + 1

        # Try merging s[r] with a matching character earlier
        for m in range(l, r):
            if s[m] == s[r]:
                # s[m]'s turn extends to cover s[r] → s[r] is free
                # Just need to print s[m+1..r-1] separately
                result = min(result, dp(l, m) + dp(m + 1, r - 1))

        return result

    return dp(0, n - 1)
```

### Why remove consecutive duplicates?
"aaa" takes 1 turn, same as "a". Consecutive same characters never need
separate turns. Removing them shrinks the input and speeds things up
without affecting the answer.

---

## Your Attempt (with bugs)

```python
def strangePrinter(self, s: str) -> int:
    a = []                                   # ✓ dedup step is correct
    i = 0
    while i < len(s):
        c = s[i]
        while i < len(s)-1 and s[i] == s[i+1]:
            i += 1
        a.append(c)
        i += 1

    @lru_cache(None)
    def solve(l, r):
        if l > r: return 0
        if l == r: return 1

        samechar = [i for i in range(l, r+1) if a[i] == a[l]]

        res = float('inf')
        cumulativeSum = 1
        prevInd = -1
        for ind in samechar:
            res = min(res, 1 + solve(ind+1, r))          # ← BUG 1
            if prevInd != -1:
                cumulativeSum += solve(prevInd+1, ind-1)  # gaps between matches
            else:
                prevInd = ind
        if len(samechar) > 1:
            res = min(res, cumulativeSum)                 # ← BUG 2
        return res
    return solve(0, len(a)-1)
```

### Bug 1: `1 + solve(ind+1, r)` forgets the gap before ind

When `ind > l`, this line says: "1 turn covers a[l] through a[ind], then solve the rest."
But it **completely ignores** the characters between l+1 and ind-1!

```
"aba" → a = ['a', 'b', 'a'],  samechar = [0, 2]

ind=2: res = min(res, 1 + solve(3, 2))
                    = min(res, 1 + 0)
                    = 1

What this says:  "Print a[0..2] in 1 turn. Done!"
What it forgot:  a[1]='b' needs its own turn!
                 You can't print "aba" in 1 turn.

Correct: solve(1, 1) + solve(2, 2) = 1 + 1 = 2
         (gap 'b' + subproblem from position 2 onward)
```

### Bug 2: `cumulativeSum` is missing the tail

cumulativeSum = 1 + (gaps between consecutive matches)

But it never adds `solve(lastMatch+1, r)` — the part AFTER the last match.

```
"abab" → a = ['a', 'b', 'a', 'b'],  samechar = [0, 2]

Your cumulativeSum:
  1 (a-layer) + solve(1,1)=1 (gap)                  = 2

Missing:
  + solve(3, 3)=1 (the tail!)

Correct: 1 + 1 + 1 = 3
Answer should be 3, you return 2.
```

### Why both bugs together are devastating

Bug 1 poisons `res` BEFORE cumulativeSum is even checked:

```
"aba": samechar = [0, 2]

ind=2: res = min(3, 1 + solve(3,2)) = min(3, 1) = 1  ← Bug 1 sets res=1

cumulativeSum = 1 + solve(1,1) = 2  ← correct!

But: res = min(1, 2) = 1  ← Bug 1 already won, cumulativeSum can't help

Answer: 1 (WRONG, expected 2)
```

### Root cause: two competing strategies that are both broken

Your code has TWO independent mechanisms:
1. **Per-match:** `1 + solve(ind+1, r)` — broken (forgets the gap)
2. **All-at-once:** `cumulativeSum` — broken (forgets the tail)

They fight each other, and whichever gives the smaller (wrong) answer wins.

### What the correct approach looks like

You only need ONE mechanism — try each single merge, let recursion handle the rest:

```python
@lru_cache(None)
def solve(l, r):
    if l > r: return 0
    if l == r: return 1

    res = 1 + solve(l + 1, r)              # base: a[l] is its own turn

    for m in range(l + 1, r + 1):          # try merging a[l] with each match
        if a[m] == a[l]:
            res = min(res, solve(l + 1, m - 1) + solve(m, r))
            #              ^^^^^^^^^^^^^^^^^     ^^^^^^^^^^^
            #              print the gap         a[m] shares a[l]'s turn
            #                                    (no +1, it's counted inside)
    return res
```

No samechar list. No cumulativeSum. No prevInd.
The formula `solve(l+1, m-1) + solve(m, r)` handles everything:
- Gap cost: `solve(l+1, m-1)`
- Rest including a[m]'s turn: `solve(m, r)` (a[m]'s turn = a[l]'s turn, same char)
- Multi-match merging: handled automatically by recursion
  (solve(m, r) will find further matches and merge if beneficial)

---

## Your Gap on This Problem

### Gap: Trying to be too clever with "merge all at once"

You saw multiple matching characters and thought: "I should handle them ALL together
in one cumulativeSum." This is a natural instinct but leads to:
- Complex bookkeeping (prevInd, samechar list, cumulative tracking)
- Easy to miss edge cases (tail, gaps)
- Two competing strategies that conflict

**The interval DP mindset:** Make ONE binary decision (merge with THIS match or not),
and let RECURSION handle the rest. The recursion will naturally explore all combinations
of matches — that's what memoization is for.

```
Your approach:     "Let me manually track all matches and sum gaps"  → complex, buggy
Clean approach:    "Let me try each single match, recursion does the rest" → simple, correct
```

**Rule for interval DP:** Each recursive call should make ONE choice, not try to
handle all choices simultaneously. The recursion tree explores all combinations.
Your job is just to enumerate the IMMEDIATE choices correctly.

---

## Is It OK to Fail This Question?

Yes. Here's why:

1. **Strange Printer is genuinely hard.** The "overwriting" mechanic makes it
   unintuitive. Many experienced engineers can't solve it without seeing the pattern first.

2. **You got the right IDEA** — dedup, find matching characters, merge them.
   The gap was in the transition formula, not the high-level approach.

3. **The pattern transfers.** Now that you understand "try one merge, let recursion
   handle the rest," you'll recognize it in Burst Balloons, Remove Boxes, and
   any future interval DP. One failure → permanent skill.

4. **Interview reality:** LC 664 is rarely asked as-is. If interval DP comes up,
   it's more likely Burst Balloons or a partition DP. This problem is for deepening
   your understanding, not memorizing.

**What to take away:**
- The "paint layers" mental model
- The formula: `dp(l, r-1) + 1` as base, `dp(l, m) + dp(m+1, r-1)` as merge
- The rule: ONE choice per recursive call, not all-at-once

---

## Dry Run: "aaabba"

### After removing consecutive duplicates: "aba"

```
dp(0, 2): s = ['a', 'b', 'a']

  Default: dp(0, 1) + 1

  dp(0, 1): s[0]='a', s[1]='b'
    Default: dp(0, 0) + 1 = 1 + 1 = 2
    Check m=0: s[0]='a' != s[1]='b', skip
    dp(0, 1) = 2

  So default = 2 + 1 = 3

  Check matches for s[2]='a':
    m=0: s[0]='a' == s[2]='a' ✓
      dp(0, 0) + dp(1, 1) = 1 + 1 = 2

  dp(0, 2) = min(3, 2) = 2

Answer: 2 ✓  (print "aaa", overwrite middle with "b")
```

## Dry Run: "abcabc"

### After removing consecutive duplicates: "abcabc" (no change)

```
dp(0, 5): s = ['a','b','c','a','b','c']

  Default: dp(0, 4) + 1

  Matches for s[5]='c':
    m=2: s[2]='c' == s[5]='c'
      dp(0, 2) + dp(3, 4)
      dp(0, 2) = "abc" = 3 turns
      dp(3, 4) = "ab" = 2 turns
      Total = 5

  dp(0, 4) = "abcab"
    Matches for s[4]='b':
      m=1: dp(0, 1) + dp(2, 3) = 2 + dp("ca")
        dp("ca") = 2
        Total = 4
    dp(0, 4) = 4

  Default: 4 + 1 = 5

  Best from matches: 5

  dp(0, 5) = min(5, 5) = 5

  But wait — can we do better?
  Actually: dp(0,2)="abc"=3, and dp(3,5)="abc"=3 → split at 2: 3+3=6 (worse)
  
  Let's check dp(0,3)="abca":
    m=0: s[0]='a'==s[3]='a' → dp(0,0)+dp(1,2) = 1+2 = 3
    dp(0,3) = 3

  dp(0,5) with m=3: s[3]='a'==s[0]? No, checking s[m]==s[r]=s[5]='c'.
    m=2 only match.

  So dp(0,5) = 5? Let's verify: a,b,c,a,b,c
  Turn 1: print "aaaaaa" (all a)
  Turn 2: overwrite positions 1,4 with "b" → a,b,a,a,b,a  (2 turns for b, but they're not contiguous!)
  
  Actually: Turn 1: "aaa___", Turn 2: "bbb" at positions 1-3? No that overwrites a...
  
  Optimal: print a at {0,3}, b at {1,4}, c at {2,5} → 
  Turn 1: aaaccc (no, must be contiguous same char)
  
  Actually each turn is a contiguous range of ONE character.
  So: Turn 1: aaaaaa, Turn 2: bbbbb (pos 1-5), Turn 3: cccc (pos 2-5), 
      Turn 4: aaa (pos 3-5), Turn 5: bb (pos 4-5)... that's worse.
  
  Better: print right-to-left layers:
  T1: cccccc, T2: bbbbb (0-4), T3: aaaa (0-3), T4: bb (1-1)... no.
  
  Simplest: print each unique segment separately = 5 turns. 
  (With the matching optimization we can't do better here.)

Answer: 5
```

---

## Comparison: All Three Interval DP Problems

| | Burst Balloons (312) | Remove Boxes (546) | Strange Printer (664) |
|---|---|---|---|
| **State** | `dp(l, r)` | `dp(l, r, k)` | `dp(l, r)` |
| **Extra param?** | No | Yes (k = extras waiting) | No |
| **Key decision** | Which to burst LAST | Remove now vs merge deeper | Print s[r] alone vs merge with matching char |
| **"Free" element** | N/A | Bigger group → k² bonus | Matching char → s[r] costs 0 extra |
| **Combine** | `+` (independent subproblems) | `+` (independent subproblems) | `+` (independent subproblems) |
| **Time** | O(n³) | O(n⁴) | O(n³) |
| **Difficulty** | Hard | Very Hard | Hard |

### The shared pattern
All three ask: "For the current range, should I process this element independently,
or can I merge it with a matching element deeper in the range to save cost?"

```
Standard interval DP structure:

dp(l, r) = worst_case                          ← process s[r] alone
for m where s[m] matches s[r]:
    dp(l, r) = min/max(dp(l, r),
                       combine(dp(l, m), dp(m+1, r-1)))  ← merge and save
```

---

## How to Build Intuition for Strange Printer

### The mental model: painting layers

Think of the string as layers of paint, printed back-to-front:

```
"aba":
Layer 1 (bottom): aaa     ← print 'a' across everything
Layer 2 (top):     b      ← overwrite middle with 'b'

Result: a b a              ← 2 turns
```

Each turn is one layer of paint (contiguous, single color).
Minimizing turns = minimizing layers.

**When does a character NOT need its own layer?**
When it can piggyback on another character's layer — i.e., when a matching
character earlier in the range already has a layer that extends far enough.

That's exactly what the recurrence captures:
- `s[m] == s[r]` → s[r] piggybacks on s[m]'s layer → no extra turn for s[r]
- `s[m] != s[r]` for all m → s[r] needs its own layer → +1 turn
