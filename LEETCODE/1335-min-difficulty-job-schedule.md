# LC 1335 — Minimum Difficulty of a Job Schedule

## Problem
Schedule n jobs over d days. Jobs are sequential (must do j before j+1).
At least one job per day. Day difficulty = max job difficulty that day.
Minimize total difficulty (sum of daily maxes).

---

## How to Identify the Pattern in an Interview

### Trigger words
- "Split an array into k groups" → interval DP / partition DP
- "At least one per group" → partition with constraints
- "Min sum of (some aggregate per group)" → classic partition DP

### The mental checklist
1. Can I reorder? **No** — jobs are sequential → this is a **partition** problem, not selection
2. What's the cost of a partition? **max of the segment** → need to track running max
3. How many partitions? **d** → one dimension of DP

### Pattern: Partition DP
> Given a sequential array, split it into exactly k contiguous groups,
> minimize/maximize some function of each group.

Other problems with THIS EXACT pattern:
- LC 410 — Split Array Largest Sum (min the max-sum partition)
- LC 1043 — Partition Array for Max Sum (max the sum with capped width)
- LC 813 — Largest Sum of Averages (max sum of averages of k groups)

---

## Intuition

Think of it as placing **d-1 dividers** in a row of n jobs:

```
Jobs:     [7, 1, 7, 1, 7, 1]     d = 3 days

Option A:  [7 | 1 | 7, 1, 7, 1]  → 7 + 1 + 7 = 15  ✓ optimal
Option B:  [7, 1 | 7, 1 | 7, 1]  → 7 + 7 + 7 = 21
Option C:  [7, 1, 7 | 1 | 7, 1]  → 7 + 1 + 7 = 15  ✓ optimal
```

At each position, you decide: "Should this job be the last job of today,
or should I continue today and push the divider further right?"

This is a classic **"where do I place the cut?"** DP.

### The DP state
- `dp(i, day)` = min difficulty to schedule jobs `i..n-1` over `day` remaining days
- OR equivalently: `dp[j][d]` = min difficulty to schedule jobs `0..j` using `d` days

### The transition
Try every possible "last day" boundary. If the last day covers jobs k..j:
- Cost of last day = max(nums[k..j])
- Cost of first d-1 days = dp[k-1][d-1]
- Total = max(nums[k..j]) + dp[k-1][d-1]

Pick the k that minimizes this.

---

## Your Attempt 1: Top-Down (Memoized) — CORRECT ✓

```python
class Solution:
    def minDifficulty(self, nums: List[int], d: int) -> int:
        if len(nums) < d:
            return -1
        @lru_cache(None)
        def solve(start, d):
            if d == 1:
                return max(nums[start:len(nums)])
            maxVal = nums[start]
            result = float('inf')
            for i in range(start, len(nums) - d + 1):
                maxVal = max(maxVal, nums[i])
                result = min(result, maxVal + solve(i + 1, d - 1))
            return result
        return solve(0, d)
```

**This is correct!** The logic is sound:
- Base case: 1 day left → must do all remaining jobs → cost = max of remaining
- Recursive: try each split point i, first day covers `start..i`, rest is `solve(i+1, d-1)`
- `len(nums) - d + 1` ensures enough jobs left for remaining days

**Minor performance note:** `max(nums[start:])` creates a list slice each time.
You could precompute suffix maxes, but it doesn't affect correctness.

---

## Your Attempt 2: Bottom-Up DP — TWO BUGS

```python
class Solution:
    def minDifficulty(self, nums: List[int], d: int) -> int:
        if len(nums) < d:
            return -1
        dp = [[0] * (d + 1) for _ in range(len(nums) + 1)]
        n = len(nums)
        maxVal = 0
        for i in range(n):
            maxVal = max(nums[i], maxVal)
            dp[i][1] = maxVal                       # ✓ correct base case

        res = float('inf')
        for i in range(2, d + 1):
            for j in range(i - 1, len(nums)):
                maxVal = nums[j]
                dp[j][i] = float('inf')
                for k in range(j, i - 2, -1):
                    maxVal = max(maxVal, nums[k])
                    dp[j][i] = min(dp[j][i], maxVal + dp[k][i - 1])  # ← BUG 1
                if i == d:
                    res = min(res, dp[j][i])         # ← BUG 2
        return res
```

---

### Bug 1: Off-by-one — job k is double-counted

Your DP definition: `dp[j][d]` = min difficulty of jobs `0..j` in `d` days.

Your transition says: last day = `nums[k..j]`, previous days = `dp[k][d-1]`.

But `dp[k][d-1]` covers jobs `0..k` — that INCLUDES job k!
So job k appears in BOTH the last day AND the previous days.

**Trace with `[7,1,7,1,7,1]`, d=3:**
```
dp[5][3]: k=5
  Last day = nums[5..5] = [1], cost = 1
  Previous days = dp[5][2] = 8     ← covers jobs 0..5, includes job 5!
  Candidate = 1 + 8 = 9            ← WRONG (job 5 counted twice)

Should be:
  Last day = nums[5..5] = [1], cost = 1
  Previous days = dp[4][2] = 14    ← covers jobs 0..4, correct!
  Candidate = 1 + 14 = 15          ← CORRECT
```

**Fix:** `dp[k][i-1]` → `dp[k-1][i-1]`

---

### Bug 2: Wrong answer extraction — not using all jobs

Your code: `res = min(res, dp[j][i])` for ALL valid j when i == d.

This means you might return `dp[3][3]` = cost of scheduling jobs 0..3 in 3 days,
ignoring jobs 4 and 5 entirely!

The answer MUST be `dp[n-1][d]` — schedule ALL jobs.

**In the trace:**
```
dp[3][3] = 9   (only jobs 0..3 in 3 days — ignores jobs 4,5!)
dp[5][3] = 9   (wrong due to Bug 1, should be 15)

Your code: min(dp[2][3], dp[3][3], dp[4][3], dp[5][3]) = min(21, 9, 15, 9) = 9
Correct:   dp[5][3] = 15 (after fixing Bug 1)
```

**Fix:** Return `dp[n-1][d]` instead of min over all j.

---

### Root cause analysis: what went wrong mentally

| Mistake | What happened | The rule to remember |
|---------|--------------|---------------------|
| Bug 1 | Transition uses `dp[k]` but last day starts at k | If last day = `[k..j]`, previous = `[0..k-1]` = `dp[k-1]` |
| Bug 2 | Took min over all j as if any subset works | We must use ALL jobs → answer is always `dp[n-1][d]` |

**The deeper pattern:** When converting top-down to bottom-up, your top-down had:
```python
result = min(result, maxVal + solve(i + 1, d - 1))
# "first day = start..i, remaining = solve(i+1, ...)"
```

In bottom-up you flipped it to "last day = k..j, previous = dp[k]". But you forgot
to adjust the index — `dp[k]` includes job k, so it should be `dp[k-1]`.

**Rule:** When flipping top-down to bottom-up, draw the partition on paper:
```
jobs:  [0 ... k-1 | k ... j]
        ↑ prev     ↑ last day
        dp[k-1]    max(nums[k..j])
```

---

## Clean Bottom-Up Solution

```python
def minDifficulty(self, jobDifficulty: List[int], d: int) -> int:
    n = len(jobDifficulty)
    if n < d:
        return -1

    # dp[j][day] = min difficulty of scheduling jobs 0..j using `day` days
    dp = [[float('inf')] * (d + 1) for _ in range(n)]

    # Base case: 1 day — must do all jobs 0..j, cost = max(jobs[0..j])
    running_max = 0
    for j in range(n):
        running_max = max(running_max, jobDifficulty[j])
        dp[j][1] = running_max

    # Fill: for each day count, for each ending position
    for day in range(2, d + 1):
        for j in range(day - 1, n):
            # Try each split: last day = jobs[k..j], first day-1 days = jobs[0..k-1]
            cur_max = 0
            for k in range(j, day - 2, -1):
                cur_max = max(cur_max, jobDifficulty[k])
                dp[j][day] = min(dp[j][day], cur_max + dp[k - 1][day - 1])

    return dp[n - 1][d]
```

### Why this works
- `k` ranges from j down to `day - 1` (need at least day-1 jobs for previous days)
- `dp[k-1][day-1]` = cost of jobs 0..k-1 in day-1 days (no double-counting)
- `cur_max` tracks max(jobs[k..j]) as we expand the last day leftward
- Answer: `dp[n-1][d]` — all n jobs scheduled in d days

---

## Clean Top-Down Solution (your style, slightly optimized)

```python
from functools import lru_cache
from typing import List

def minDifficulty(self, jobDifficulty: List[int], d: int) -> int:
    n = len(jobDifficulty)
    if n < d:
        return -1

    # Precompute suffix max to avoid slicing
    suffix_max = [0] * n
    suffix_max[n - 1] = jobDifficulty[n - 1]
    for i in range(n - 2, -1, -1):
        suffix_max[i] = max(jobDifficulty[i], suffix_max[i + 1])

    @lru_cache(None)
    def dp(start: int, days_left: int) -> int:
        if days_left == 1:
            return suffix_max[start]

        cur_max = 0
        result = float('inf')
        for end in range(start, n - days_left + 1):
            cur_max = max(cur_max, jobDifficulty[end])
            result = min(result, cur_max + dp(end + 1, days_left - 1))
        return result

    return dp(0, d)
```

Improvement: precomputed `suffix_max` avoids creating a new list slice on every base case call.

---

## Dry Run: `[6, 5, 4, 3, 2, 1]`, d = 2

### Top-down trace
```
dp(0, 2):
  end=0: max([6])=6, dp(1,1)=max([5,4,3,2,1])=5 → 6+5=11
  end=1: max([6,5])=6, dp(2,1)=max([4,3,2,1])=4 → 6+4=10
  end=2: max([6,5,4])=6, dp(3,1)=max([3,2,1])=3 → 6+3=9
  end=3: max([6,5,4,3])=6, dp(4,1)=max([2,1])=2 → 6+2=8
  end=4: max([6,5,4,3,2])=6, dp(5,1)=max([1])=1 → 6+1=7  ← min!

Answer: 7
Split: Day 1 = [6,5,4,3,2] (max=6), Day 2 = [1] (max=1), total = 7
```

### Bottom-up trace
```
Jobs:     6  5  4  3  2  1
Index:    0  1  2  3  4  5

dp[j][1] (base):
  dp[0][1] = 6    (max of [6])
  dp[1][1] = 6    (max of [6,5])
  dp[2][1] = 6    (max of [6,5,4])
  dp[3][1] = 6    (max of [6,5,4,3])
  dp[4][1] = 6    (max of [6,5,4,3,2])
  dp[5][1] = 6    (max of [6,5,4,3,2,1])

dp[j][2] (day=2):
  j=1: k=1, max([5])=5+dp[0][1]=6 → 11.  dp[1][2]=11
  j=2: k=2, max([4])=4+dp[1][1]=6 → 10.  k=1, max([5,4])=5+dp[0][1]=6 → 11.  dp[2][2]=10
  j=3: k=3, max([3])=3+dp[2][1]=6 → 9.   ...  dp[3][2]=9
  j=4: k=4, max([2])=2+dp[3][1]=6 → 8.   ...  dp[4][2]=8
  j=5: k=5, max([1])=1+dp[4][1]=6 → 7.   ...  dp[5][2]=7

Answer: dp[5][2] = 7  ✓
```

---

## Dry Run: `[7, 1, 7, 1, 7, 1]`, d = 3

```
dp[j][1]: [7, 7, 7, 7, 7, 7]

dp[j][2]:
  j=1: last=[1], prev=dp[0][1]=7 → 1+7=8.  dp[1][2]=8
  j=2: last=[7], prev=dp[1][1]=7 → 14.  last=[1,7], prev=dp[0][1]=7 → 14.  dp[2][2]=14
  j=3: last=[1], prev=dp[2][1]=7 → 8.  ...  dp[3][2]=8
  j=4: last=[7], prev=dp[3][1]=7 → 14.  last=[1,7], prev=dp[2][1]=7 → 14.  dp[4][2]=14
  j=5: last=[1], prev=dp[4][1]=7 → 8.   ...  dp[5][2]=8

dp[j][3]:
  j=2: last=[7], prev=dp[1][2]=8 → 7+8=15.  dp[2][3]=15
  j=3: last=[1], prev=dp[2][2]=14 → 15.  last=[7,1], prev=dp[1][2]=8 → 15.  dp[3][3]=15
  j=4: last=[7], prev=dp[3][2]=8 → 15.   dp[4][3]=15
  j=5: last=[1], prev=dp[4][2]=14 → 15.  last=[7,1], prev=dp[3][2]=8 → 15.  dp[5][3]=15

Answer: dp[5][3] = 15  ✓

Optimal splits (multiple exist):
  [7 | 1 | 7,1,7,1] → 7+1+7 = 15
  [7,1 | 7,1 | 7,1] → 7+7+7 = 21 (worse)
  [7 | 1,7 | 1,7,1] → 7+7+7 = 21 (worse)
```

---

## Your Gaps on This Problem

### Gap 1: Off-by-one when flipping top-down → bottom-up

Your top-down splits as: `[start..i]` then `[i+1..end]`.
Your bottom-up splits as: `[0..k]` then `[k..j]` — job k is in both!

**Rule:** Always draw the partition boundary on paper before writing the transition:
```
[0 ... k-1 | k ... j]
 prev part   last day
 dp[k-1]     max(k..j)
```

### Gap 2: Returning the wrong answer

You took `min over all j` instead of `dp[n-1][d]`. This considers partial schedules
(not all jobs) as valid answers.

**Rule:** In partition DP, the answer is always at the "full array" state:
- Top-down: `dp(0, d)` = start from beginning
- Bottom-up: `dp[n-1][d]` = end at last element

### Gap 3: Not testing the translation

When converting top-down to bottom-up, always verify with a small example:
1. Run your top-down on `[6,5,4,3,2,1], d=2` and note each state value
2. Run your bottom-up on the same input and compare state-by-state
3. If ANY state differs, you have a translation bug

---

## Complexity

| Approach | Time | Space |
|----------|------|-------|
| Top-down (your solution) | O(n² × d) | O(n × d) for cache |
| Bottom-up (clean) | O(n² × d) | O(n × d) for table |
| Bottom-up with monotonic stack optimization | O(n × d) | O(n × d) |

The O(n × d) optimization using a decreasing monotonic stack is an advanced technique
where you avoid the inner k-loop by maintaining a stack of candidates. Not expected
in most interviews — the O(n² × d) solution is sufficient.

---

## Related Problems (Same Partition DP Pattern)

### Practice order: start easy, build to hard

| Order | # | Problem | Difficulty | Cost function | Key twist |
|:-----:|---|---------|:----------:|---------------|-----------|
| 1 | 1043 | [Partition Array for Max Sum](https://leetcode.com/problems/partition-array-for-maximum-sum/) | Medium | max × length | Fixed max partition width, no k groups |
| 2 | 813 | [Largest Sum of Averages](https://leetcode.com/problems/largest-sum-of-averages/) | Medium | average per group | MAXIMIZE (not minimize), floats |
| 3 | 1335 | [Min Difficulty of Job Schedule](https://leetcode.com/problems/minimum-difficulty-of-a-job-schedule/) | Hard | max per group | This problem |
| 4 | 410 | [Split Array Largest Sum](https://leetcode.com/problems/split-array-largest-sum/) | Hard | sum per group | Minimize the MAXIMUM partition sum |
| 5 | 1278 | [Palindrome Partitioning III](https://leetcode.com/problems/palindrome-partitioning-iii/) | Hard | edit cost to palindrome | Cost requires its own DP |
| 6 | 2547 | [Min Cost to Split an Array](https://leetcode.com/problems/minimum-cost-to-split-an-array/) | Hard | trimmed length + k | Complex cost formula |

---

### The partition DP template
```python
# dp[j][k] = optimal cost of splitting items 0..j into k groups
# Base: dp[j][1] = cost of one group containing 0..j
# Transition: dp[j][k] = min/max over split point s of:
#     cost(items[s..j]) + dp[s-1][k-1]
# Answer: dp[n-1][k]
```

Every problem above is this template with a different `cost()` function.

---

## Practice Problem Sketches (Top-Down AND Bottom-Up for each)

### P1: LC 1043 — Partition Array for Maximum Sum (Medium)

**Problem:** Split array into groups of at most width `k`. Replace each element with
the group's max. Maximize the total sum.

**Why start here:** No fixed number of groups (simpler), just a width constraint.
Good for learning the bottom-up mechanics without the extra `k` dimension.

**How to spot it:** "Split array into groups" + "max of each group" + optimize total

**Top-down:**
```python
def maxSumAfterPartitioning(self, arr: List[int], k: int) -> int:
    n = len(arr)

    @lru_cache(None)
    def dp(i: int) -> int:
        if i >= n:
            return 0
        cur_max = 0
        best = 0
        for length in range(1, min(k, n - i) + 1):
            cur_max = max(cur_max, arr[i + length - 1])
            best = max(best, cur_max * length + dp(i + length))
        return best

    return dp(0)
```

**Bottom-up (practice converting!):**
```python
def maxSumAfterPartitioning(self, arr: List[int], k: int) -> int:
    n = len(arr)
    dp = [0] * (n + 1)

    for j in range(n - 1, -1, -1):
        cur_max = 0
        for length in range(1, min(k, n - j) + 1):
            cur_max = max(cur_max, arr[j + length - 1])
            dp[j] = max(dp[j], cur_max * length + dp[j + length])

    return dp[0]
```

**Key mapping:** `dp(i)` in recursion → `dp[j]` in bottom-up, fill right-to-left.

---

### P2: LC 813 — Largest Sum of Averages (Medium)

**Problem:** Split array into at most k groups. Maximize sum of averages.

**How to spot it:** "At most k groups" + "average of each" + maximize

**Top-down:**
```python
def largestSumOfAverages(self, nums: List[int], k: int) -> float:
    n = len(nums)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]

    @lru_cache(None)
    def dp(i: int, groups_left: int) -> float:
        if i == n:
            return 0
        if groups_left == 1:
            return (prefix[n] - prefix[i]) / (n - i)
        best = 0.0
        for j in range(i + 1, n - groups_left + 2):
            avg = (prefix[j] - prefix[i]) / (j - i)
            best = max(best, avg + dp(j, groups_left - 1))
        return best

    return dp(0, k)
```

**Bottom-up:**
```python
def largestSumOfAverages(self, nums: List[int], k: int) -> float:
    n = len(nums)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]

    # dp[j][g] = best sum of averages for nums[0..j] split into g groups
    dp = [[0.0] * (k + 1) for _ in range(n)]

    # Base: 1 group
    for j in range(n):
        dp[j][1] = prefix[j + 1] / (j + 1)

    for g in range(2, k + 1):
        for j in range(g - 1, n):
            for s in range(j, g - 2, -1):
                # last group = nums[s..j], previous = dp[s-1][g-1]
                avg = (prefix[j + 1] - prefix[s]) / (j - s + 1)
                dp[j][g] = max(dp[j][g], avg + dp[s - 1][g - 1])

    # "at most k" → take best across all group counts
    return max(dp[n - 1][g] for g in range(1, k + 1))
```

**Key difference from 1335:** "at most k" not "exactly k". Answer = max over all
group counts, not just dp[n-1][k].

---

### P3: LC 410 — Split Array Largest Sum (Hard)

**Problem:** Split array into exactly k groups. Minimize the maximum group sum.

**How to spot it:** "Split into k groups" + "minimize the maximum" (minimax)

**Why it's tricky:** The thing you're optimizing (max of sums) is different from
the per-group cost. You can't just sum up group costs — you need the MAX.

**Top-down:**
```python
def splitArray(self, nums: List[int], k: int) -> int:
    n = len(nums)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]

    @lru_cache(None)
    def dp(i: int, groups_left: int) -> int:
        if groups_left == 1:
            return prefix[n] - prefix[i]
        best = float('inf')
        for j in range(i + 1, n - groups_left + 2):
            group_sum = prefix[j] - prefix[i]
            # This group has sum group_sum. Future groups have their own max.
            # We want to minimize the max of ALL groups.
            worst = max(group_sum, dp(j, groups_left - 1))
            best = min(best, worst)
        return best

    return dp(0, k)
```

**Bottom-up:**
```python
def splitArray(self, nums: List[int], k: int) -> int:
    n = len(nums)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]

    dp = [[float('inf')] * (k + 1) for _ in range(n)]

    for j in range(n):
        dp[j][1] = prefix[j + 1]

    for g in range(2, k + 1):
        for j in range(g - 1, n):
            for s in range(j, g - 2, -1):
                group_sum = prefix[j + 1] - prefix[s]
                dp[j][g] = min(dp[j][g], max(group_sum, dp[s - 1][g - 1]))

    return dp[n - 1][k]
```

**Key difference from 1335:** Combine is `max(last_group, previous)` not `+`.
The `min` is over split points, the `max` is over "which group is the bottleneck."

**Alternative approach:** Binary search on the answer (binary search + greedy check).
This is O(n log S) where S = sum of array. Worth knowing for interviews.

---

### P4: LC 1278 — Palindrome Partitioning III (Hard)

**Problem:** Split string into exactly k groups. Minimize total character changes
needed to make each group a palindrome.

**How to spot it:** "Split into k groups" + "cost per group requires its own computation"

**The twist:** The cost function itself needs a sub-DP (min changes to make substring
a palindrome). So you have TWO DPs: one for cost, one for partition.

**Sketch (practice implementing yourself):**
```python
# Step 1: Precompute cost[i][j] = min changes to make s[i..j] a palindrome
# (Two-pointer from both ends, count mismatches)

# Step 2: Standard partition DP
# dp[j][k] = min changes to split s[0..j] into k palindrome groups
# dp[j][k] = min over s of { cost[s][j] + dp[s-1][k-1] }
```

---

## Top-Down → Bottom-Up Conversion Cheat Sheet

This is your specific weakness. Use this checklist every time:

### Step 1: Define the state clearly
Write it down: "dp[j][k] = ______ for items 0..j using k groups"

### Step 2: Draw the partition
```
[0 ... s-1 | s ... j]
 dp[s-1][k-1]  cost(s..j)
```
**Triple check:** Does dp[s-1] overlap with cost(s..j)? If s is in both → BUG.

### Step 3: Get the loop bounds right
- Outer: `k` from 2 to K (day/group count)
- Middle: `j` from k-1 to n-1 (need at least k items for k groups)
- Inner: `s` from j down to k-1 (need at least k-1 items for previous groups)

### Step 4: Get the answer right
- "Exactly k groups, use ALL items" → `dp[n-1][k]`
- "At most k groups" → `max/min over dp[n-1][1..k]`
- NEVER take min/max over all j — that means using a subset of items

### Step 5: Verify with a tiny example
Run both top-down and bottom-up on a 3-4 element input. Compare every state.
If any state differs, you have a translation bug. Fix it before submitting.
