# DP Pattern Identification — The Complete Map

> Read the problem → spot the trigger words → identify the pattern → write the state.
>
> This file covers every major DP pattern, how to recognize it, the state design,
> the transition shape, and when to optimize.

---

## Quick Lookup Table

| You see in the problem... | DP Pattern | Jump to |
|---|---|---|
| "Maximum/minimum subarray" | [Linear DP / Kadane's](#1-linear-dp--kadanes) | §1 |
| "Subsequence" + optimize/count | [Subsequence DP (LIS family)](#2-subsequence-dp-lis-family) | §2 |
| "Two strings" + transform/match | [Two-String DP](#3-two-string-dp-lcs--edit-distance) | §3 |
| "Knapsack" / "subset sum" / capacity | [Knapsack DP](#4-knapsack-dp) | §4 |
| "Split array into k groups" | [Partition DP](#5-partition-dp) | §5 |
| "Remove/merge from range [i..j]" | [Interval DP](#6-interval-dp) | §6 |
| "Grid path" + obstacles/costs | [Grid DP](#7-grid-dp) | §7 |
| "Two agents on same grid" | [Multi-Path DP](#8-multi-path-dp) | §8 |
| "Count sequences from a range" + ordering | [Counting DP + Prefix/Suffix Sum](#9-counting-dp--prefixsuffix-sum) | §9 |
| "Buy/sell stock" / cooldown / fee | [State Machine DP](#10-state-machine-dp) | §10 |
| "Palindrome" + partition/count | [Palindrome DP](#11-palindrome-dp) | §11 |
| "How many numbers in [L,R] with property" | [Digit DP](#12-digit-dp) | §12 |
| "Assign n items, visit all" + small n ≤ 20 | [Bitmask DP](#13-bitmask-dp) | §13 |
| "Tree" + aggregate from children | [Tree DP](#14-tree-dp) | §14 |
| "Game, two players, optimal play" | [Game Theory DP](#15-game-theory-dp) | §15 |
| "Probability" / "expected value" | [Probability DP](#16-probability--expected-value-dp) | §16 |

---

## The Universal DP Checklist (Use Before Writing Code)

1. **What am I choosing at each step?** (pick an element, split here, include/exclude)
2. **What do I need to remember?** → that's your **state**
3. **What's the recurrence?** (how does state `k` depend on state `k-1`)
4. **What's the base case?** (empty, single element, boundary)
5. **What's the answer?** (which state cell holds it)
6. **Can I optimize?** (prefix sums, monotonic stack, space reduction)

---

## §1: Linear DP / Kadane's

### Trigger Words
- "Maximum subarray sum"
- "Longest/shortest contiguous segment with property X"
- "Ending at index i"

### Mental Model
You walk left to right. At each position, decide: **extend the previous answer, or start fresh here.**

### State
`dp[i]` = best answer for a subarray **ending at index i**

### Template
```python
dp[0] = nums[0]
for i in range(1, n):
    dp[i] = max(nums[i], dp[i - 1] + nums[i])  # extend or restart
answer = max(dp)
```

### Optimizations
- Space: only need `dp[i-1]` → single variable
- Kadane's is just this with one variable

### Key Problems

| Problem | Twist |
|---|---|
| [Maximum Subarray](https://leetcode.com/problems/maximum-subarray/) (LC 53) | Pure Kadane's |
| [Maximum Product Subarray](https://leetcode.com/problems/maximum-product-subarray/) (LC 152) | Track both max AND min (negatives flip sign) |
| [Longest Turbulent Subarray](https://leetcode.com/problems/longest-turbulent-subarray/) (LC 978) | Two states: last went up / last went down |
| [Maximum Sum Circular Subarray](https://leetcode.com/problems/maximum-sum-circular-subarray/) (LC 918) | Answer = max(Kadane, totalSum - minSubarray) |
| [House Robber](https://leetcode.com/problems/house-robber/) (LC 198) | `dp[i] = max(dp[i-1], dp[i-2] + nums[i])` — skip or take |

---

## §2: Subsequence DP (LIS Family)

### Trigger Words
- "Longest increasing subsequence"
- "Count subsequences"
- "Subsequence" + "not contiguous" + "order preserved"

### Mental Model
For each element, look back at **all previous elements** and extend the best valid one.

### State
`dp[i]` = best answer for subsequence **ending at element i**

### Template
```python
dp = [1] * n
for i in range(n):
    for j in range(i):
        if nums[j] < nums[i]:  # valid extension condition
            dp[i] = max(dp[i], dp[j] + 1)
answer = max(dp)
```

### Optimizations
- O(n²) → O(n log n) with patience sorting (binary search on tails array)
- When counting: prefix sum / BIT / segment tree over values

### Key Problems

| Problem | Twist |
|---|---|
| [Longest Increasing Subsequence](https://leetcode.com/problems/longest-increasing-subsequence/) (LC 300) | Classic LIS |
| [Number of Longest Increasing Subsequence](https://leetcode.com/problems/number-of-longest-increasing-subsequence/) (LC 673) | Track count alongside length |
| [Longest Arithmetic Subsequence](https://leetcode.com/problems/longest-arithmetic-subsequence/) (LC 1027) | State = `(index, common_difference)` |
| [Russian Doll Envelopes](https://leetcode.com/problems/russian-doll-envelopes/) (LC 354) | Sort + LIS on second dimension |
| [Distinct Subsequences](https://leetcode.com/problems/distinct-subsequences/) (LC 115) | Count subsequences matching target |

---

## §3: Two-String DP (LCS / Edit Distance)

### Trigger Words
- "Two strings" + "transform" / "match" / "common"
- "Minimum operations to convert A to B"
- "Longest common subsequence/substring"
- "Interleaving" / "regex matching" / "wildcard"

### Mental Model
2D grid where `dp[i][j]` = answer for `s1[0..i-1]` and `s2[0..j-1]`.
At each cell, either characters match (diagonal) or they don't (try insert/delete/replace).

### State
`dp[i][j]` = answer considering first `i` chars of string 1 and first `j` chars of string 2

### Template (Edit Distance)
```python
for i in range(1, m + 1):
    for j in range(1, n + 1):
        if s1[i-1] == s2[j-1]:
            dp[i][j] = dp[i-1][j-1]          # match — no cost
        else:
            dp[i][j] = 1 + min(
                dp[i-1][j],      # delete
                dp[i][j-1],      # insert
                dp[i-1][j-1],    # replace
            )
```

### Template (LCS)
```python
for i in range(1, m + 1):
    for j in range(1, n + 1):
        if s1[i-1] == s2[j-1]:
            dp[i][j] = dp[i-1][j-1] + 1
        else:
            dp[i][j] = max(dp[i-1][j], dp[i][j-1])
```

### Optimizations
- Space: only need previous row → O(min(m, n))

### Key Problems

| Problem | Twist |
|---|---|
| [Longest Common Subsequence](https://leetcode.com/problems/longest-common-subsequence/) (LC 1143) | Classic LCS |
| [Edit Distance](https://leetcode.com/problems/edit-distance/) (LC 72) | 3 operations: insert, delete, replace |
| [Interleaving String](https://leetcode.com/problems/interleaving-string/) (LC 97) | Can s3 be formed by interleaving s1 and s2? |
| [Regular Expression Matching](https://leetcode.com/problems/regular-expression-matching/) (LC 10) | `.` and `*` wildcards |
| [Wildcard Matching](https://leetcode.com/problems/wildcard-matching/) (LC 44) | `?` and `*` wildcards |
| [Shortest Common Supersequence](https://leetcode.com/problems/shortest-common-supersequence/) (LC 1092) | LCS + reconstruct |

---

## §4: Knapsack DP

### Trigger Words
- "Capacity" / "weight limit" / "budget"
- "Select subset" + "maximize value" + "don't exceed limit"
- "Can you form exactly sum S?"
- "Partition into two equal subsets"
- "Coin change" / "make amount"

### Mental Model
For each item: **take it or skip it**. Track remaining capacity.

### Three Variants

**0/1 Knapsack** — each item used at most once:
```python
for i in range(n):
    for w in range(W, weight[i] - 1, -1):  # reverse to avoid reuse
        dp[w] = max(dp[w], dp[w - weight[i]] + value[i])
```

**Unbounded Knapsack** — unlimited supply of each item:
```python
for w in range(1, W + 1):
    for i in range(n):
        if weight[i] <= w:
            dp[w] = max(dp[w], dp[w - weight[i]] + value[i])
```

**Bounded / Counting** — count number of ways to reach a target:
```python
dp[0] = 1
for i in range(n):
    for w in range(weight[i], W + 1):
        dp[w] += dp[w - weight[i]]
```

### How to Tell Which Variant

| Clue in problem | Variant |
|---|---|
| "Each item used at most once" | 0/1 Knapsack |
| "Unlimited coins/items" | Unbounded |
| "Partition into two equal subsets" | 0/1 Knapsack with target = sum/2 |
| "Number of ways to make amount" | Counting Knapsack |
| "Minimum coins to make amount" | Unbounded (min version) |

### Key Problems

| Problem | Variant |
|---|---|
| [Partition Equal Subset Sum](https://leetcode.com/problems/partition-equal-subset-sum/) (LC 416) | 0/1, target = sum/2 |
| [Target Sum](https://leetcode.com/problems/target-sum/) (LC 494) | 0/1, counting ways |
| [Coin Change](https://leetcode.com/problems/coin-change/) (LC 322) | Unbounded, minimize count |
| [Coin Change II](https://leetcode.com/problems/coin-change-ii/) (LC 518) | Unbounded, count ways |
| [Ones and Zeroes](https://leetcode.com/problems/ones-and-zeroes/) (LC 474) | 0/1, two-dimensional capacity |
| [Last Stone Weight II](https://leetcode.com/problems/last-stone-weight-ii/) (LC 1049) | 0/1, minimize difference |
| [Profitable Schemes](https://leetcode.com/problems/profitable-schemes/) (LC 879) | 0/1, two constraints + counting |

---

## §5: Partition DP

### Trigger Words
- "Split array into k groups"
- "At least one per group"
- "Minimize/maximize sum of (some aggregate per group)"
- "Exactly k partitions"

### Mental Model
Place **k-1 dividers** in a row of n items. Try each split point.

### State
`dp[j][k]` = optimal cost of items `0..j` split into `k` groups

### Template
```python
# Base: 1 group
for j in range(n):
    dp[j][1] = cost(0, j)

# Fill
for g in range(2, k + 1):
    for j in range(g - 1, n):
        for s in range(j, g - 2, -1):
            dp[j][g] = min(dp[j][g], cost(s, j) + dp[s - 1][g - 1])

answer = dp[n - 1][k]
```

### The Partition Boundary Rule
```
[0 ... s-1 | s ... j]
 dp[s-1][g-1]  cost(s..j)
```
**Never** let `dp[s]` overlap with `cost(s..j)`. If `s` appears in both → double-counting bug.

### Optimizations
- Monotonic stack (when cost = max of segment, like LC 1335)
- Convex hull trick (when cost is quadratic in segment size)

### Key Problems

| Problem | Cost function |
|---|---|
| [Minimum Difficulty of Job Schedule](https://leetcode.com/problems/minimum-difficulty-of-a-job-schedule/) (LC 1335) | max per segment |
| [Split Array Largest Sum](https://leetcode.com/problems/split-array-largest-sum/) (LC 410) | minimize the max sum |
| [Largest Sum of Averages](https://leetcode.com/problems/largest-sum-of-averages/) (LC 813) | maximize sum of averages |
| [Partition Array for Max Sum](https://leetcode.com/problems/partition-array-for-maximum-sum/) (LC 1043) | max × length, bounded width |
| [Palindrome Partitioning III](https://leetcode.com/problems/palindrome-partitioning-iii/) (LC 1278) | edit cost to palindrome |

*(You already have detailed notes on this: see `1335-min-difficulty-job-schedule.md`)*

---

## §6: Interval DP

### Trigger Words
- "Merge" / "burst" / "remove" elements from a **range**
- "Minimum cost to merge all into one"
- "Every possible way to split a range"
- Range shrinks as you make choices (not a fixed partition)

### Mental Model
The answer for range `[i, j]` is built by trying **every split point k** in `[i, j]`,
combining the answers for `[i, k]` and `[k+1, j]` (or `[k, j]`).

### How It Differs from Partition DP
- **Partition DP:** split once into k groups, then each group is independent.
- **Interval DP:** repeatedly shrink the range by removing/merging — subproblems overlap.

### State
`dp[i][j]` = answer for the subarray `nums[i..j]`

### Template
```python
# Base: single element
for i in range(n):
    dp[i][i] = base_cost(i)

# Fill by increasing length
for length in range(2, n + 1):
    for i in range(n - length + 1):
        j = i + length - 1
        dp[i][j] = float('inf')
        for k in range(i, j):
            dp[i][j] = min(dp[i][j], dp[i][k] + dp[k+1][j] + combine_cost(i, j))
```

### Key Problems

| Problem | What you're merging |
|---|---|
| [Burst Balloons](https://leetcode.com/problems/burst-balloons/) (LC 312) | Burst = remove from range, neighbors change |
| [Matrix Chain Multiplication](https://en.wikipedia.org/wiki/Matrix_chain_multiplication) | Multiply matrices, minimize scalar ops |
| [Minimum Cost Tree From Leaf Values](https://leetcode.com/problems/minimum-cost-tree-from-leaf-values/) (LC 1130) | Build tree bottom-up from leaves |
| [Strange Printer](https://leetcode.com/problems/strange-printer/) (LC 664) | Min turns to print a string |
| [Minimum Score Triangulation of Polygon](https://leetcode.com/problems/minimum-score-triangulation-of-polygon/) (LC 1039) | Triangulate polygon |

---

## §7: Grid DP

### Trigger Words
- "Grid" / "matrix" + "path"
- "Move right or down only"
- "Minimum path sum" / "number of unique paths"
- "Obstacles" in a grid

### Mental Model
Fill the grid cell by cell. Each cell depends on the cell above and/or to the left.

### State
`dp[r][c]` = answer for reaching cell `(r, c)` from `(0, 0)`

### Template
```python
dp[0][0] = grid[0][0]
for r in range(m):
    for c in range(n):
        if r > 0: dp[r][c] = min(dp[r][c], dp[r-1][c] + grid[r][c])
        if c > 0: dp[r][c] = min(dp[r][c], dp[r][c-1] + grid[r][c])
```

### Optimizations
- Space: only need previous row → O(n)
- If movements include diagonal: check all 3 predecessors

### Key Problems

| Problem | Twist |
|---|---|
| [Unique Paths](https://leetcode.com/problems/unique-paths/) (LC 62) | Count paths |
| [Unique Paths II](https://leetcode.com/problems/unique-paths-ii/) (LC 63) | Obstacles |
| [Minimum Path Sum](https://leetcode.com/problems/minimum-path-sum/) (LC 64) | Sum costs |
| [Dungeon Game](https://leetcode.com/problems/dungeon-game/) (LC 174) | Fill bottom-right to top-left |
| [Minimum Falling Path Sum](https://leetcode.com/problems/minimum-falling-path-sum/) (LC 931) | Move down + diagonal |
| [Triangle](https://leetcode.com/problems/triangle/) (LC 120) | Triangular grid |

---

## §8: Multi-Path DP

### Trigger Words
- "Go then return on same grid"
- "Two agents collecting resources"
- "Two paths that share/interact"

### Mental Model
Simulate both walkers simultaneously. Synchronize by step count.

### State
`dp(t, r1, r2)` — step `t`, walker 1 at row `r1`, walker 2 at row `r2`.
Columns derived: `c = t - r`.

### Key Insight
"Go and return" = "Two people walking forward simultaneously." A return path is
just a forward path reversed.

### Key Problems

| Problem | Setup |
|---|---|
| [Cherry Pickup](https://leetcode.com/problems/cherry-pickup/) (LC 741) | Go and return on grid |
| [Cherry Pickup II](https://leetcode.com/problems/cherry-pickup-ii/) (LC 1463) | Two robots from top corners |

*(You already have detailed notes on this: see `MULTI_PATH_DP_NOTES.md`)*

---

## §9: Counting DP + Prefix/Suffix Sum

### Trigger Words
- "Count arrays" / "number of sequences"
- "Each element from a range [l, r]"
- "Alternating" / "zigzag" / "up-down"
- "Strictly greater/less than neighbor"
- "How many permutations/arrangements satisfy..."

### Mental Model
Build the sequence position by position. At each position, **sum over all valid
previous values**. That sum is a contiguous range → prefix/suffix sum optimization.

### State
`dp[i][state]` = ways to build a sequence ending at value `i` in given `state`

### The Optimization Pattern
```python
# SLOW — O(n × R²)
for i in range(R + 1):
    for j in range(i + 1, R + 1):    # sum over j > i
        dp_new[i] += dp_old[j]

# FAST — O(n × R) — precompute suffix sum
suffix = build_suffix_sum(dp_old)
for i in range(R + 1):
    dp_new[i] = suffix[i + 1]
```

### Running Accumulator (Cleanest Form)
```python
s = 0
for i in range(R, -1, -1):
    new_down[i] = s           # sum of values at j > i (strict)
    s = (s + up[i]) % MOD     # add current AFTER assigning
```

Assign before adding → strictly greater. Add before assigning → greater or equal.

### Key Problems

| Problem | Transition type |
|---|---|
| Zigzag Arrays (this) | Alternating up/down, prefix + suffix |
| [Count Vowels Permutation](https://leetcode.com/problems/count-vowels-permutation/) (LC 1220) | Fixed transition graph (small alphabet) |
| [Knight Dialer](https://leetcode.com/problems/knight-dialer/) (LC 935) | Fixed transition graph (phone pad) |
| [Count Number of Teams](https://leetcode.com/problems/count-number-of-teams/) (LC 1395) | Two-state asc/desc, count predecessors |
| [Maximum Number of Points with Cost](https://leetcode.com/problems/maximum-number-of-points-with-cost/) (LC 1937) | Left prefix max + right suffix max |
| [Distinct Subsequences II](https://leetcode.com/problems/distinct-subsequences-ii/) (LC 940) | Count distinct subsequences, prefix sum |
| [Odd Even Jump](https://leetcode.com/problems/odd-even-jump/) (LC 975) | Two-state (odd up, even down), sorted map |

*(You already have detailed notes on this: see `zigzag-arrays.md`)*

---

## §10: State Machine DP

### Trigger Words
- "Buy and sell stock"
- "Cooldown" / "transaction fee"
- "At most k transactions"
- Anything where you transition between **named states** (holding, not holding, cooldown)

### Mental Model
Draw a state machine with labeled transitions. Each day, you move between states.
Each state tracks the best profit **if you're in that state after day i**.

### State
Each named state gets its own DP array:
- `hold[i]` = max profit on day i if currently holding stock
- `cash[i]` = max profit on day i if not holding stock
- `cool[i]` = max profit on day i if in cooldown

### Template (with cooldown)
```python
hold = -prices[0]
cash = 0
cool = 0

for i in range(1, n):
    new_hold = max(hold, cool - prices[i])   # buy from cooldown
    new_cash = max(cash, hold + prices[i])    # sell
    new_cool = max(cool, cash)                # enter cooldown from cash
    hold, cash, cool = new_hold, new_cash, new_cool

return max(cash, cool)
```

### How to Draw the Machine

1. List all possible states (holding, not holding, cooldown, used k transactions)
2. Draw arrows for valid transitions (buy, sell, wait)
3. Label each arrow with its cost/gain
4. Each arrow becomes one line in your recurrence

### Key Problems

| Problem | States |
|---|---|
| [Best Time to Buy and Sell Stock](https://leetcode.com/problems/best-time-to-buy-and-sell-stock/) (LC 121) | 1 transaction — just track min |
| [Buy Sell Stock II](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-ii/) (LC 122) | Unlimited — hold/cash |
| [Buy Sell Stock III](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iii/) (LC 123) | At most 2 transactions |
| [Buy Sell Stock IV](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iv/) (LC 188) | At most k transactions |
| [Buy Sell with Cooldown](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown/) (LC 309) | +cooldown state |
| [Buy Sell with Transaction Fee](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-transaction-fee/) (LC 714) | hold/cash + fee on sell |

---

## §11: Palindrome DP

### Trigger Words
- "Palindrome" + "partition" / "count" / "subsequence"
- "Minimum cuts to make all palindromes"
- "Longest palindromic subsequence"

### Mental Model
Expand from center or fill `dp[i][j]` = "is `s[i..j]` a palindrome?"
Then use this as a building block for the outer DP.

### Two Layers

**Layer 1:** Precompute `is_palindrome[i][j]` or `cost[i][j]`
```python
for length in range(2, n + 1):
    for i in range(n - length + 1):
        j = i + length - 1
        is_pal[i][j] = (s[i] == s[j]) and (length <= 3 or is_pal[i+1][j-1])
```

**Layer 2:** Use the precomputed table in a partition/counting DP

### Key Problems

| Problem | Structure |
|---|---|
| [Longest Palindromic Subsequence](https://leetcode.com/problems/longest-palindromic-subsequence/) (LC 516) | Interval DP: `dp[i][j]` = LPS in `s[i..j]` |
| [Longest Palindromic Substring](https://leetcode.com/problems/longest-palindromic-substring/) (LC 5) | Expand from center or DP |
| [Palindrome Partitioning II](https://leetcode.com/problems/palindrome-partitioning-ii/) (LC 132) | Min cuts — precompute + 1D DP |
| [Palindrome Partitioning III](https://leetcode.com/problems/palindrome-partitioning-iii/) (LC 1278) | Partition DP + palindrome cost |
| [Count Different Palindromic Subsequences](https://leetcode.com/problems/count-different-palindromic-subsequences/) (LC 730) | Hard counting variant |

---

## §12: Digit DP

### Trigger Words
- "Count numbers in [L, R] with property X"
- "Digit sum" / "adjacent digits" / "no repeated digit"
- Range is huge (up to 10^18)

### Mental Model
Build the number digit by digit, left to right, tracking:
1. **Tight?** — are we still constrained by the upper bound?
2. **Started?** — have we placed a non-zero digit yet?
3. **Custom state** — whatever the property needs (digit sum, last digit, etc.)

### Template
```python
@lru_cache(None)
def dp(pos, tight, started, state):
    if pos == len(digits):
        return base_case(started, state)

    limit = digits[pos] if tight else 9
    result = 0
    for d in range(0, limit + 1):
        new_tight = tight and (d == limit)
        new_started = started or (d > 0)
        new_state = transition(state, d, new_started)
        result += dp(pos + 1, new_tight, new_started, new_state)
    return result
```

### Key Problems

| Problem | Property tracked |
|---|---|
| [Count Special Integers](https://leetcode.com/problems/count-special-integers/) (LC 2376) | All digits distinct (bitmask of used digits) |
| [Numbers At Most N Given Digit Set](https://leetcode.com/problems/numbers-at-most-n-given-digit-set/) (LC 902) | Digits from a given set |
| [Count Numbers with Unique Digits](https://leetcode.com/problems/count-numbers-with-unique-digits/) (LC 357) | No repeated digits |
| [Non-negative Integers without Consecutive Ones](https://leetcode.com/problems/non-negative-integers-without-consecutive-ones/) (LC 600) | Binary — no consecutive 1s |
| [Numbers With Repeated Digits](https://leetcode.com/problems/numbers-with-repeated-digits/) (LC 1012) | At least one repeated digit |

*(You already have detailed notes: see `DIGIT_DP_NOTES.md`)*

---

## §13: Bitmask DP

### Trigger Words
- "Assign n items to n slots" (n ≤ 20)
- "Visit all nodes" / "traveling salesman"
- "Subset" + small n (≤ 20)
- "Minimum cost to do everything"

### Mental Model
Represent which items are "used" as a bitmask. `mask = 0b10110` means items 1, 2, 4 are used.
Iterate over all 2^n masks, try adding each unused item.

### State
`dp[mask]` = best answer when the set of used items is `mask`

### Template
```python
dp = [float('inf')] * (1 << n)
dp[0] = 0

for mask in range(1 << n):
    k = bin(mask).count('1')  # how many items used so far (= current position)
    for i in range(n):
        if mask & (1 << i):
            continue  # already used
        new_mask = mask | (1 << i)
        dp[new_mask] = min(dp[new_mask], dp[mask] + cost[k][i])
```

### Constraint: n ≤ 20
Bitmask DP is O(2^n × n). For n = 20, that's ~20 million — fine.
For n > 20, you need a different approach.

### Key Problems

| Problem | What the mask tracks |
|---|---|
| [Shortest Path Visiting All Nodes](https://leetcode.com/problems/shortest-path-visiting-all-nodes/) (LC 847) | Visited nodes in graph |
| [Minimum Cost to Connect Two Groups](https://leetcode.com/problems/minimum-cost-to-connect-two-groups-of-points/) (LC 1595) | Which group-2 items are connected |
| [Can I Win](https://leetcode.com/problems/can-i-win/) (LC 464) | Which numbers are taken |
| [Partition to K Equal Sum Subsets](https://leetcode.com/problems/partition-to-k-equal-sum-subsets/) (LC 698) | Which elements are assigned |
| [Find the Shortest Superstring](https://leetcode.com/problems/find-the-shortest-superstring/) (LC 943) | TSP variant — which strings are used |
| [Maximum Students Taking Exam](https://leetcode.com/problems/maximum-students-taking-exam/) (LC 1349) | Row bitmask — seat arrangement |

---

## §14: Tree DP

### Trigger Words
- "Tree" + "maximize/minimize/count"
- "Root the tree" / "subtree"
- "Rob houses on a tree" (not adjacent)
- "Max independent set on tree"

### Mental Model
DFS post-order. Each node computes its answer from its children's answers.
Often two states per node: "take this node" vs "skip this node."

### Template
```python
def dfs(node, parent):
    take = value[node]    # include this node
    skip = 0              # exclude this node

    for child in adj[node]:
        if child == parent:
            continue
        child_take, child_skip = dfs(child, node)
        take += child_skip           # if I take this node, must skip children
        skip += max(child_take, child_skip)  # if I skip, children can be either

    return take, skip

answer = max(dfs(root, -1))
```

### Key Problems

| Problem | Tree DP type |
|---|---|
| [House Robber III](https://leetcode.com/problems/house-robber-iii/) (LC 337) | Take/skip on binary tree |
| [Binary Tree Maximum Path Sum](https://leetcode.com/problems/binary-tree-maximum-path-sum/) (LC 124) | Max path — return single-branch to parent |
| [Diameter of Binary Tree](https://leetcode.com/problems/diameter-of-binary-tree/) (LC 543) | Max depth from each child |
| [Longest Path With Different Adjacent Colors](https://leetcode.com/problems/longest-path-with-different-adjacent-colors/) (LC 2246) | Tree diameter variant |
| [Sum of Distances in Tree](https://leetcode.com/problems/sum-of-distances-in-tree/) (LC 834) | Rerooting technique |
| [Maximum Product of Splitted Binary Tree](https://leetcode.com/problems/maximum-product-of-splitted-binary-tree/) (LC 1339) | Subtree sums |

---

## §15: Game Theory DP

### Trigger Words
- "Two players" + "optimal play"
- "First player wins?"
- "Minimax" / "choose optimally"
- "Alice and Bob take turns"

### Mental Model
The current player maximizes their score; the opponent will do the same on their turn.
Use **relative score** (my score minus opponent's) to avoid tracking both players.

### State
`dp[i][j]` = best **relative** advantage the current player can achieve from `nums[i..j]`

### Template
```python
@lru_cache(None)
def dp(i, j):
    if i > j:
        return 0
    # Current player picks left or right
    pick_left  = nums[i] - dp(i + 1, j)   # take left, opponent plays rest
    pick_right = nums[j] - dp(i, j - 1)   # take right, opponent plays rest
    return max(pick_left, pick_right)

# First player wins if dp(0, n-1) >= 0
```

### Why Minus?
After I pick `nums[i]`, the opponent faces `dp(i+1, j)` — that's THEIR advantage.
My advantage = what I took − their advantage. Hence the minus sign.

### Key Problems

| Problem | Game type |
|---|---|
| [Stone Game](https://leetcode.com/problems/stone-game/) (LC 877) | Pick from ends |
| [Stone Game II](https://leetcode.com/problems/stone-game-ii/) (LC 1140) | Variable M piles |
| [Stone Game III](https://leetcode.com/problems/stone-game-iii/) (LC 1406) | Take 1, 2, or 3 from front |
| [Predict the Winner](https://leetcode.com/problems/predict-the-winner/) (LC 486) | Same as Stone Game |
| [Cat and Mouse](https://leetcode.com/problems/cat-and-mouse/) (LC 913) | Graph game — BFS on game states |

---

## §16: Probability / Expected Value DP

### Trigger Words
- "Probability" / "expected value"
- "Random" + "what is the expected..."
- "Average outcome over all random choices"

### Mental Model
Same as regular DP, but transitions **multiply by probability** and **sum** over outcomes.
Expected value = sum of (probability × value) for each branch.

### Template
```python
@lru_cache(None)
def dp(state):
    if is_terminal(state):
        return terminal_value(state)

    expected = 0
    for outcome in possible_outcomes(state):
        prob = probability(outcome)
        expected += prob * dp(next_state(state, outcome))
    return expected
```

### Key Problems

| Problem | Random element |
|---|---|
| [Knight Probability in Chessboard](https://leetcode.com/problems/knight-probability-in-chessboard/) (LC 688) | Random knight moves |
| [New 21 Game](https://leetcode.com/problems/new-21-game/) (LC 837) | Draw random cards |
| [Soup Servings](https://leetcode.com/problems/soup-servings/) (LC 808) | Random serving choices |
| [Airplane Seat Assignment Probability](https://leetcode.com/problems/airplane-seat-assignment-probability/) (LC 1227) | Random seat picks |

---

## The Decision Flowchart

Use this when you're staring at a problem and don't know which pattern:

```
START: What type of input?
│
├── Single array/string?
│   ├── "Contiguous subarray" → §1 Linear/Kadane's
│   ├── "Subsequence" → §2 Subsequence (LIS)
│   ├── "Split into k groups" → §5 Partition DP
│   ├── "Merge/burst elements from range" → §6 Interval DP
│   ├── "Palindrome" → §11 Palindrome DP
│   └── "Count sequences from a value range" → §9 Counting DP
│
├── Two strings?
│   └── → §3 Two-String DP (LCS / Edit Distance)
│
├── Grid?
│   ├── Single agent → §7 Grid DP
│   └── Two agents / go-and-return → §8 Multi-Path DP
│
├── Tree?
│   └── → §14 Tree DP
│
├── Items with weight/value + capacity?
│   └── → §4 Knapsack DP
│
├── Small n ≤ 20 + "use all" / "assign all"?
│   └── → §13 Bitmask DP
│
├── "Numbers in [L, R] with digit property"?
│   └── → §12 Digit DP
│
├── "Two players, optimal play"?
│   └── → §15 Game Theory DP
│
├── "Buy/sell" or named states with transitions?
│   └── → §10 State Machine DP
│
└── "Probability" / "expected value"?
    └── → §16 Probability DP
```

---

## Cross-Pattern Tricks (Apply to Any Pattern)

### 1. Prefix/Suffix Sum Optimization

**When:** Your transition sums over a contiguous range of the previous layer.
**How:** Precompute the sum in O(n), look up in O(1).
**Saves:** One factor of n from the complexity.
**Shows up in:** §2, §5, §9, §11

### 2. Space Reduction

**When:** Your recurrence only reads the previous 1-2 layers.
**How:** Keep only those layers instead of the full table.
**Saves:** One dimension of space.
**Shows up in:** ALL patterns

### 3. Monotonic Stack/Deque Optimization

**When:** You're computing `min/max of dp[j] + cost(j, i)` where `cost` is monotonic.
**How:** Maintain a stack/deque of candidates, pop dominated ones.
**Saves:** One factor of n from the complexity.
**Shows up in:** §1, §5, §7, §9

### 4. Binary Search on Answer

**When:** "Minimize the maximum" or "maximize the minimum."
**How:** Binary search on the answer, check feasibility with greedy.
**Alternative to:** Partition DP when the cost function is monotonic.
**Shows up in:** §5 (LC 410)

### 5. Convex Hull Trick / Li Chao Tree

**When:** Transition is `dp[j] = min(dp[i] + a[i] * b[j])` — a product of two terms.
**How:** Maintain convex hull of lines, query minimum.
**Saves:** Inner loop in partition DP.
**Shows up in:** §5 (advanced)

---

## Top-Down vs Bottom-Up Decision

| Factor | Top-Down (Memoized) | Bottom-Up (Tabulation) |
|---|---|---|
| Easier to write? | Usually yes — closer to how you think about the problem | Harder — must get loop order and bounds right |
| Handles sparse states? | Yes — only computes reachable states | No — fills entire table |
| Cache overhead? | Hash map / lru_cache has overhead | Array access is faster |
| Optimization-friendly? | Hard to apply monotonic stack / prefix sum | Easy — states are laid out in order |
| Stack overflow risk? | Yes (deep recursion, Python limit ~1000) | No |
| Space optimization? | Hard (random access pattern) | Easy (rolling array) |

**Rule of thumb:**
- Start with top-down (faster to code, easier to debug)
- Convert to bottom-up if you need speed, space optimization, or advanced tricks

---

## Common Traps When Converting Top-Down → Bottom-Up

These are the bugs you keep hitting (based on your 1335 notes):

### Trap 1: Off-by-one at partition boundary
- Top-down: `solve(i+1, k-1)` naturally doesn't overlap
- Bottom-up: `dp[k][d-1]` — make sure `k` doesn't appear in both sides
- **Fix:** Always draw `[0..s-1 | s..j]` on paper

### Trap 2: Wrong answer cell
- Top-down answer = `dp(0, d)` (start from beginning)
- Bottom-up answer = `dp[n-1][d]` (end at last element)
- **Never** take min/max over all ending positions (that's a subset, not the full array)

### Trap 3: Loop direction
- Top-down fills states on demand
- Bottom-up: outer loop = stages (days, groups), inner loop = positions
- Inner loop bounds must ensure enough elements for remaining stages

### Trap 4: Base case mismatch
- Top-down: `if d == 1: return ...` handles the base case naturally
- Bottom-up: must explicitly fill `dp[j][1]` for all valid `j`

**The safety net:** After converting, test both versions on a small input (3-4 elements).
Compare every DP state. If any differs → you have a translation bug.
