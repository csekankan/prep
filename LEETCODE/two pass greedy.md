# Two-Pass Greedy Pattern — Comprehensive Revision Guide

## Your Gaps (Be Honest With Yourself)

### Gap 1: Python `for` loop doesn't support skipping
```python
# BROKEN — i resets every iteration
for i in range(len(nums)):
    i = end + 1  # ← IGNORED by Python

# FIX — use while when you need to control the index
while i < len(nums):
    i = end + 1  # ← works
```
**Rule:** If you need to skip ahead, always use `while`.

---

### Gap 2: Too many tangled pointers
Your attempts used `st`, `mid`, `end` all moving simultaneously.
This made it impossible to reason about what each pointer represented.

```python
# YOUR CODE — confusing, which pointer is where?
while mid < len(nums) and nums[st] < nums[mid]:
    mid += 1
    st += 1     # both moving — hard to track

# CLEAN — each pointer has ONE job
left = peak - 1   # only moves left
right = peak + 1   # only moves right
```
**Rule:** Each pointer should have ONE clear job and move in ONE direction.

---

### Gap 3: Wrong two-pass state tracking
You tried storing start indices in `sm[]` but mixed up what to store:

```python
# ATTEMPT 1 — stores l (some moving index), not the uphill count
sm[i] = l  # ← what is l? hard to reason about

# ATTEMPT 2 — stores sm[i-1] (chained start), closer but logic still broken
sm[i] = sm[i-1]

# CLEAN — store exactly what you need: the COUNT of uphill/downhill steps
up[i] = up[i-1] + 1    # how many steps going UP ending at i
down[i] = down[i-1] + 1 # how many steps going DOWN starting at i
```
**Rule:** In two-pass, each array should store ONE simple thing — usually a count or a max.

---

### Gap 4: Off-by-one in skip logic
```python
i = end - 1  # ← goes BACK, re-scans elements → O(n²)
i = end      # ← correct, no re-scan → O(n)
```
**Rule:** After processing a range, skip TO the end, not before it.

---

### Gap 5: Not identifying the peak first
Your approach: scan uphill → find where it stops → scan downhill.
Problem: you don't know where the peak is until you finish scanning, and by then your pointers are tangled.

Better approach: **find the peak first, THEN expand**.

---

### Gap 6: Computing DERIVED values instead of the DIRECT thing
In LC 1671, you computed **removals** per-position instead of **LIS/LDS lengths**.
This forced two different formulas (extend vs replace branch) and caused off-by-one bugs.

```python
# YOUR CODE — different formula per branch, easy to mess up
if not tracker or tracker[-1] < nums[i]:
    left[i] = i + 1 - len(tracker)    # formula A
else:
    left[i] = i - ind                  # formula B (happens to match A, but fragile)

# CLEAN — one formula, always correct
pos = bisect_left(tails, nums[i])
lis[i] = pos + 1                       # always this, no branching
```
**Rule:** Store the THING you care about (length). Derive removals ONCE at the end (`n - best`).

---

### Gap 7: `range(len(nums) - 1)` instead of `range(len(nums))`
Off-by-one in loop bounds — the last element never gets processed.
This is a recurring mistake. Always double-check: **does every index get visited?**

---

## The Two-Pass Pattern

### When to use it
> **When constraints or information flows in BOTH directions.**

Ask yourself: "Does knowing what's on the left AND right matter?" If yes → two-pass.

### The template
```python
# Pass 1: left → right (what can I know from the left?)
left_info = [0] * n
for i in range(1, n):
    if some_condition(i, i-1):
        left_info[i] = left_info[i-1] + 1  # or some update

# Pass 2: right → left (what can I know from the right?)
right_info = [0] * n
for i in range(n-2, -1, -1):
    if some_condition(i, i+1):
        right_info[i] = right_info[i+1] + 1  # or some update

# Combine: merge both directions
result = 0
for i in range(n):
    result = max(result, combine(left_info[i], right_info[i]))
```

---

## Problem 1: LC 845 — Longest Mountain in Array

### Problem
Find the longest subarray that goes strictly up then strictly down (min length 3).

### How to identify this in an interview
- You see "subarray" + "increasing then decreasing" → mountain shape
- You think: "For each position, I need to know how far the uphill goes AND how far the downhill goes"
- That's TWO pieces of directional info → two-pass

### Intuition
Imagine standing at each index and asking two questions:
1. "How many steps was I climbing UP to get here?" → need to look LEFT
2. "How many steps can I go DOWN from here?" → need to look RIGHT

You can't answer both in one pass. But each question alone is a simple left-to-right
or right-to-left scan. So do them separately and combine.

### Algorithm
1. **Left pass:** Build `up[i]` = consecutive increasing steps ending at i
2. **Right pass:** Build `down[i]` = consecutive decreasing steps starting at i
3. **Combine:** Any index with `up[i] > 0 AND down[i] > 0` is a valid peak.
   Mountain length = `up[i] + down[i] + 1`

**Time:** O(n) — two passes. **Space:** O(n) — two arrays.

### Solution
```python
def longestMountain(self, nums: List[int]) -> int:
    n = len(nums)
    if n < 3:
        return 0

    up = [0] * n
    for i in range(1, n):
        if nums[i] > nums[i - 1]:
            up[i] = up[i - 1] + 1

    down = [0] * n
    for i in range(n - 2, -1, -1):
        if nums[i] > nums[i + 1]:
            down[i] = down[i + 1] + 1

    result = 0
    for i in range(1, n - 1):
        if up[i] > 0 and down[i] > 0:
            result = max(result, up[i] + down[i] + 1)

    return result
```

### Dry run: `[2, 1, 4, 7, 3, 2, 5]`
```
Index:    0  1  2  3  4  5  6
Value:    2  1  4  7  3  2  5

up[]:     0  0  1  2  0  0  1
          ·  ↓  ↑  ↑  ↓  ↓  ↑

down[]:   1  0  0  2  1  0  0
          ↓  ·  ·  ↓  ↓  ·  ·

Peak check (up>0 AND down>0):
  i=3: up=2, down=2 → length = 2+2+1 = 5  ✓
  (subarray: [1, 4, 7, 3, 2])

Answer: 5
```

### Alternative: One-pass with peak detection
```python
def longestMountain(self, arr: List[int]) -> int:
    n = len(arr)
    result = 0
    i = 1

    while i < n - 1:
        if arr[i] > arr[i-1] and arr[i] > arr[i+1]:  # peak!
            left = i - 1
            right = i + 1
            while left > 0 and arr[left-1] < arr[left]:
                left -= 1
            while right < n-1 and arr[right] > arr[right+1]:
                right += 1
            result = max(result, right - left + 1)
            i = right  # skip to end of mountain
        else:
            i += 1

    return result
```

---

## Problem 2: LC 1840 — Maximum Building Height

### Problem
Buildings 1..n, building 1 height = 0, adjacent differ by ≤ 1, some buildings have max height restrictions. Find max possible height.

### How to identify this in an interview
- "Adjacent differ by at most 1" → constraints propagate linearly (like a slope)
- Restrictions cap heights at specific positions → these limits spread outward in BOTH directions
- A restriction on the LEFT limits what you can reach. A restriction on the RIGHT also limits you.
  You need BOTH → two-pass

### Intuition
Think of it physically: each restriction is a "ceiling" at a position. From that ceiling,
the max possible height spreads out at slope ±1 in both directions.

If two restrictions are close, they squeeze each other down. To find the true max at each
restriction, you need to know the tightest constraint from the LEFT and from the RIGHT.

Between two resolved restrictions, the best you can do is rise from both sides at slope +1
until they meet — that's a simple geometry formula.

### Algorithm
1. **Add sentinels:** [1, 0] and [n, n-1], then sort by position
2. **Forward pass:** For each restriction, cap by `prev_height + distance`
   (can't rise faster than +1 per step from the left)
3. **Backward pass:** For each restriction, cap by `next_height + distance`
   (can't rise faster than +1 per step from the right)
4. **Find peaks:** Between each consecutive pair (p1,h1) → (p2,h2):
   `peak = (distance + h1 + h2) // 2`
5. Return the maximum peak

**Time:** O(m log m) for sort + O(m) for passes. **Space:** O(m).

### Solution
```python
def maxBuilding(self, n: int, restrictions: List[List[int]]) -> int:
    restrictions.append([1, 0])
    restrictions.sort()
    if not restrictions or restrictions[-1][0] != n:
        restrictions.append([n, n - 1])

    # Forward: cap by what's reachable from left
    for i in range(1, len(restrictions)):
        prev_pos, prev_h = restrictions[i - 1]
        cur_pos, cur_h = restrictions[i]
        restrictions[i][1] = min(cur_h, prev_h + (cur_pos - prev_pos))

    # Backward: cap by what's reachable from right
    for i in range(len(restrictions) - 2, -1, -1):
        next_pos, next_h = restrictions[i + 1]
        cur_pos, cur_h = restrictions[i]
        restrictions[i][1] = min(cur_h, next_h + (next_pos - cur_pos))

    # Peak between each consecutive pair
    result = 0
    for i in range(1, len(restrictions)):
        pos1, h1 = restrictions[i - 1]
        pos2, h2 = restrictions[i]
        peak = (pos2 - pos1 + h1 + h2) // 2
        result = max(result, peak)

    return result
```

### Dry run: `n=10, restrictions=[[5,3],[2,5],[7,4],[10,3]]`
```
After sort + add [1,0]:
Position:   1    2    5    7    10
Max height: 0    5    3    4    3

Forward pass (can I reach this from the left?):
  pos 2: min(5, 0+1) = 1
  pos 5: min(3, 1+3) = 3
  pos 7: min(4, 3+2) = 4
  pos 10: min(3, 4+3) = 3
Result:     0    1    3    4    3

Backward pass (can I reach this from the right?):
  pos 7: min(4, 3+3) = 4
  pos 5: min(3, 4+2) = 3
  pos 2: min(1, 3+3) = 1
  pos 1: min(0, 1+1) = 0
Result:     0    1    3    4    3

Peaks between pairs:
  [1,0]→[2,1]:  (1+0+1)//2 = 1
  [2,1]→[5,3]:  (3+1+3)//2 = 3
  [5,3]→[7,4]:  (2+3+4)//2 = 4
  [7,4]→[10,3]: (3+4+3)//2 = 5  ← max!

Answer: 5
```

### Peak formula derivation (for whiteboard)
```
Between positions p1 (height h1) and p2 (height h2):

From left:   height = h1 + (x - p1)     ← slope +1
From right:  height = h2 + (p2 - x)     ← slope +1

Set equal:   h1 + x - p1 = h2 + p2 - x
             2x = p1 + p2 + h2 - h1

Peak height = (p2 - p1 + h1 + h2) // 2
```

---

## Problem 3: LC 135 — Candy (Must solve)

### Problem
n children in a line with ratings. Give candies so that:
- Each child gets ≥ 1 candy
- Higher-rated child gets more than their neighbor

Minimize total candies.

### How to identify this in an interview
- "More than their neighbor" — which neighbor? LEFT and RIGHT!
- If you only look left, child 5 might need 3 candies. If you only look right, child 5
  might need 4 candies. True answer = max(3, 4) = 4 to satisfy BOTH neighbors.
- Two directions → two-pass

### Intuition
Think of it as two separate rules:
- Rule 1: "If you're better than the person on your LEFT, you get more than them"
- Rule 2: "If you're better than the person on your RIGHT, you get more than them"

Each rule alone is a simple one-directional scan. A child must satisfy BOTH rules,
so they get the MAX of what each rule demands.

### Algorithm
1. **Left pass:** `left[i]` = candies needed considering only left neighbor.
   If `rating[i] > rating[i-1]`: `left[i] = left[i-1] + 1`, else reset to 1.
2. **Right pass:** `right[i]` = candies needed considering only right neighbor.
   If `rating[i] > rating[i+1]`: `right[i] = right[i+1] + 1`, else reset to 1.
3. **Combine:** Each child gets `max(left[i], right[i])`. Sum all.

**Time:** O(n). **Space:** O(n).

### Solution
```python
def candy(self, ratings: List[int]) -> int:
    n = len(ratings)

    left = [1] * n
    for i in range(1, n):
        if ratings[i] > ratings[i - 1]:
            left[i] = left[i - 1] + 1

    right = [1] * n
    for i in range(n - 2, -1, -1):
        if ratings[i] > ratings[i + 1]:
            right[i] = right[i + 1] + 1

    return sum(max(left[i], right[i]) for i in range(n))
```

### Dry run: `[1, 0, 2]`
```
Ratings:  1  0  2

left[]:   1  1  2    (0 is not > 1, so stays 1; 2 > 0, so 1+1=2)
right[]:  2  1  1    (0 is not > 2, so stays 1; 1 > 0, so 1+1=2)

Combine:  max(1,2)=2  max(1,1)=1  max(2,1)=2

Answer: 2 + 1 + 2 = 5
```

---

## Problem 4: LC 42 — Trapping Rain Water (Must solve)

### Problem
Given elevation map, compute how much rain water can be trapped.

### How to identify this in an interview
- Water at any position depends on the tallest wall to its LEFT and the tallest wall
  to its RIGHT. You need info from BOTH sides → two-pass.
- If you try to do it in one pass, you'll realize you don't know the right side's max yet.

### Intuition
Imagine pouring water on the elevation map. At any column i:
- Water can't rise higher than the tallest bar on the LEFT (it would overflow left)
- Water can't rise higher than the tallest bar on the RIGHT (it would overflow right)
- So water level at i = min(max_left, max_right)
- Water trapped at i = water level - bar height = min(max_left, max_right) - height[i]

You need `max_left` (scan from left) and `max_right` (scan from right) → two-pass.

### Algorithm
1. **Left pass:** `left_max[i]` = max height from index 0 to i
2. **Right pass:** `right_max[i]` = max height from index i to n-1
3. **Combine:** `water[i] = min(left_max[i], right_max[i]) - height[i]`. Sum all.

**Time:** O(n). **Space:** O(n) (can be O(1) with two-pointer approach).

### Solution
```python
def trap(self, height: List[int]) -> int:
    n = len(height)

    left_max = [0] * n
    left_max[0] = height[0]
    for i in range(1, n):
        left_max[i] = max(left_max[i - 1], height[i])

    right_max = [0] * n
    right_max[n - 1] = height[n - 1]
    for i in range(n - 2, -1, -1):
        right_max[i] = max(right_max[i + 1], height[i])

    return sum(
        min(left_max[i], right_max[i]) - height[i]
        for i in range(n)
    )
```

### Dry run: `[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]` (LeetCode's example)
```
Index:      0  1  2  3  4  5  6  7  8  9  10 11
Height:     0  1  0  2  1  0  1  3  2  1  2  1
left_max:   0  1  1  2  2  2  2  3  3  3  3  3
right_max:  3  3  3  3  3  3  3  3  2  2  2  1

Water[i] = min(L,R) - h:
            0  0  1  0  1  2  1  0  0  1  0  0

Answer: 0+0+1+0+1+2+1+0+0+1+0+0 = 6  ✓
```

---

## Problem 5: LC 821 — Shortest Distance to a Character (Easy warmup)

### Problem
Given string s and character c, return array of shortest distances to c.

### How to identify this in an interview
- "Shortest distance" → nearest occurrence could be on the LEFT or the RIGHT
- You can't know which is closer without checking both directions → two-pass

### Intuition
For each position, the nearest 'c' is either:
- The last 'c' you saw going left-to-right, OR
- The last 'c' you saw going right-to-left

Do one pass each direction, tracking distance from the last 'c' seen.
Take the minimum of both.

### Algorithm
1. **Left pass:** Walk left→right, track distance from last seen 'c'.
   `result[i] = distance` (infinity if no 'c' seen yet on the left)
2. **Right pass:** Walk right→left, track distance from last seen 'c'.
   `result[i] = min(result[i], distance)` (take closer of left/right)

**Time:** O(n). **Space:** O(n) for output.

### Solution
```python
def shortestToChar(self, s: str, c: str) -> List[int]:
    n = len(s)
    result = [float('inf')] * n

    # Forward: distance from last c on the left
    dist = float('inf')
    for i in range(n):
        if s[i] == c:
            dist = 0
        result[i] = dist
        dist += 1

    # Backward: distance from last c on the right
    dist = float('inf')
    for i in range(n - 1, -1, -1):
        if s[i] == c:
            dist = 0
        result[i] = min(result[i], dist)
        dist += 1

    return result
```

---

## Problem 6: LC 1671 — Min Removals to Make Mountain Array (Hard)

### Problem
Remove minimum elements to make a mountain array (strictly up then down).

### How to identify this in an interview
- "Remove minimum elements" = keep maximum elements = find longest valid subsequence
- "Mountain" = increasing then decreasing. That's TWO directional properties.
- "Longest increasing subsequence ending at i" → left pass (LIS)
- "Longest decreasing subsequence starting at i" → right pass (LDS = LIS from right)
- Two directional subsequences → two-pass with LIS

### Key difference from LC 845
LC 845 uses **contiguous** subarrays (just count consecutive ups/downs).
LC 1671 uses **subsequences** (can skip elements). That's why you need binary-search
LIS (O(n log n)) instead of simple counting.

### Key insight
Two-pass with LIS (Longest Increasing Subsequence):
- `lis[i]` = length of LIS ending at i (left pass)
- `lds[i]` = length of LDS (longest decreasing subsequence) starting at i (right pass)
- Mountain at i has length `lis[i] + lds[i] - 1` (if both > 1)

### Algorithm
1. **Left pass (LIS):** For each index, use patience sorting (bisect_left + tails array)
   to find `lis[i] = pos + 1`
2. **Right pass (LDS):** Same thing, scanning right-to-left.
   This gives the longest increasing subsequence from the right = longest decreasing
   from the left. `lds[i] = pos + 1`
3. **Combine:** For each valid peak (lis[i] > 1 AND lds[i] > 1):
   mountain length = `lis[i] + lds[i] - 1` (peak counted once)
4. **Answer:** `n - best_mountain_length`

**Time:** O(n log n) — binary search per element. **Space:** O(n).

### Intuition: Why LIS + LDS?

A mountain array looks like:
```
         peak
        / \
       /   \
      /     \
    up      down
```

If we pick index i as the peak, we want:
- The LONGEST strictly increasing subsequence ending at i (left side of mountain)
- The LONGEST strictly decreasing subsequence starting at i (right side of mountain)
- Together they form the LONGEST mountain with peak at i
- Everything NOT in this mountain gets removed

So: **removals = n - (longest mountain)**, and longest mountain at peak i = `lis[i] + lds[i] - 1` (subtract 1 because peak is counted in both).

---

### Your attempt (with bugs annotated)

```python
def minimumMountainRemovals(self, nums: List[int]) -> int:
    left = [0 for _ in nums]
    tracker = []
    for i in range(len(nums) - 1):          # ← BUG 1: misses last element
        if not tracker or tracker[-1] < nums[i]:
            tracker.append(nums[i])
            left[i] = i + 1 - len(tracker)   # removals = (i+1) - lis_length ✓
        else:
            ind = bisect.bisect_left(tracker, nums[i])
            tracker[ind] = nums[i]
            left[i] = i - ind                 # removals = i - pos = (i+1) - (pos+1) ✓

    right = [0 for _ in nums]
    tracker = []
    for i in range(len(nums) - 1, -1, -1):
        if not tracker or tracker[-1] < nums[i]:
            tracker.append(nums[i])
            right[i] = len(nums) - i - len(tracker)   # (n-i) - lds_length ✓
        else:
            ind = bisect.bisect_left(tracker, nums[i])
            tracker[ind] = nums[i]
            right[i] = len(nums) - i - ind             # ← BUG 2: off by one!
            # should be: len(nums) - i - (ind + 1)
            # because lds[i] = ind + 1, not ind

    res = len(nums)
    for i in range(1, len(nums) - 1):
        if left[i] == i or right[i] == len(nums) - i: continue  # ← BUG 3
        res = min(res, right[i] + left[i])

    return res
```

### Bug 1: Loop range `range(len(nums) - 1)` skips the last element
```
nums = [2, 1, 1, 5, 6, 2, 3, 1]
                               ^
                               index 7 — never processed!
                               left[7] stays 0 (wrong, should be 7)
```
**Fix:** Use `range(len(nums))`.

### Bug 2: Off-by-one in right pass replace branch

In patience sorting, the position `ind` returned by `bisect_left` gives us:
- `lds[i] = ind + 1` (subsequence length = 0-indexed position + 1)
- Removals should be `(n - i) - lds[i]` = `(n - i) - (ind + 1)` = `n - i - ind - 1`

But your code computes `n - i - ind` (missing the `- 1`).

Trace with `nums = [2, 1, 1, 5, 6, 2, 3, 1]`, right pass at i=5 (value 2):
```
tracker = [1, 3] at this point (built from right)
bisect_left([1, 3], 2) = 1
ind = 1, so lds[5] = ind + 1 = 2

Your code:   right[5] = 8 - 5 - 1 = 2     ← says 2 removals
Correct:     right[5] = 8 - 5 - 1 - 1 = 1  ← only 1 removal needed
                                               (subsequence [2, 1] keeps 2, removes 1)
```

**The extend branch gets it right** (`n - i - len(tracker)` where `len(tracker) = lds[i]`),
**but the replace branch is off by 1** (`n - i - ind` instead of `n - i - ind - 1`).

### Bug 3: Guard condition `right[i] == len(nums) - i` never triggers

This tries to check "no downhill" (lds[i] == 1). But:
- `right[i] = (n - i) - lds[i]`
- `right[i] == n - i` would mean `lds[i] == 0`, which is impossible (minimum is 1)
- So this guard never filters anything!

Should be: `right[i] == len(nums) - i - 1` (which means `lds[i] == 1`).

---

### Root cause: computing REMOVALS instead of LENGTHS

All three bugs come from the same mistake: you tried to compute **removals directly**
instead of storing the **LIS/LDS length** at each position. This forced you to derive
the removal formula in two different branches (extend vs replace), making off-by-one
errors almost inevitable.

**The clean way:** Store the LENGTH, compute removals ONCE at the end.

---

### Clean solution

```python
from bisect import bisect_left

def minimumMountainRemovals(self, nums: List[int]) -> int:
    n = len(nums)

    # Pass 1: LIS length ending at each index
    lis = [1] * n
    tails = []
    for i in range(n):                        # ← range(n), not range(n-1)
        pos = bisect_left(tails, nums[i])
        if pos == len(tails):
            tails.append(nums[i])
        else:
            tails[pos] = nums[i]
        lis[i] = pos + 1                      # ← just store the length!

    # Pass 2: LDS length starting at each index (= LIS from right)
    lds = [1] * n
    tails = []
    for i in range(n - 1, -1, -1):
        pos = bisect_left(tails, nums[i])
        if pos == len(tails):
            tails.append(nums[i])
        else:
            tails[pos] = nums[i]
        lds[i] = pos + 1                      # ← same formula, no branching!

    # Combine: find longest mountain, compute removals ONCE
    best = 0
    for i in range(1, n - 1):
        if lis[i] > 1 and lds[i] > 1:         # ← clean guard: need uphill AND downhill
            best = max(best, lis[i] + lds[i] - 1)

    return n - best
```

### Why this is better

| | Your approach | Clean approach |
|---|---|---|
| **Stores** | Removals (derived differently per branch) | Lengths (one formula: `pos + 1`) |
| **Branches** | `if extend: formula A`, `else: formula B` | No branching — `pos + 1` always |
| **Guard** | `left[i]==i or right[i]==n-i` (wrong) | `lis[i]>1 and lds[i]>1` (obvious) |
| **Final calc** | `left[i] + right[i]` (fragile) | `n - (lis[i] + lds[i] - 1)` (one place) |
| **Bug risk** | Off-by-one in 3 places | Almost impossible to get wrong |

### Dry run: `[2, 1, 1, 5, 6, 2, 3, 1]`
```
Index:   0  1  2  3  4  5  6  7
Value:   2  1  1  5  6  2  3  1

LIS (→):
  tails progression: [2] → [1] → [1] → [1,5] → [1,5,6] → [1,2,6] → [1,2,3] → [1]
  lis[]:              1    1    1    2     3      2      3    1

LDS (←) = LIS from right:
  tails progression: [1] → [1,3] → [1,2] → [1,2,6] → [1,2,5] → [1] → [1] → [1,2]
  lds[]:              2    2      3    3      1      1    1    1

                     wait, let me redo this more carefully...

LDS from right (i = 7 down to 0):
  i=7: val=1, tails=[], append → [1],       lds[7] = 1
  i=6: val=3, tails=[1], 3>1, append → [1,3],  lds[6] = 2
  i=5: val=2, tails=[1,3], bisect(2)=1, → [1,2], lds[5] = 2
  i=4: val=6, tails=[1,2], 6>2, append → [1,2,6], lds[4] = 3
  i=3: val=5, tails=[1,2,6], bisect(5)=2, → [1,2,5], lds[3] = 3
  i=2: val=1, tails=[1,2,5], bisect(1)=0, → [1,2,5], lds[2] = 1
  i=1: val=1, tails=[1,2,5], bisect(1)=0, → [1,2,5], lds[1] = 1
  i=0: val=2, tails=[1,2,5], bisect(2)=1, → [1,2,5], lds[0] = 2

Results:
  Index:  0  1  2  3  4  5  6  7
  lis[]:  1  1  1  2  3  2  3  1
  lds[]:  2  1  1  3  3  2  2  1

Combine (need lis>1 AND lds>1):
  i=3: lis=2, lds=3 → mountain = 2+3-1 = 4  ✓
  i=4: lis=3, lds=3 → mountain = 3+3-1 = 5  ✓ ← best!
  i=5: lis=2, lds=2 → mountain = 2+2-1 = 3  ✓

Answer: 8 - 5 = 3 removals
Mountain: [1, 5, 6, 2, 1] (remove indices 0, 2, 6)
```

### Lesson from this problem

> **Store the THING you care about (length), not a DERIVED THING (removals).**
> Derive at the end. This avoids branch-specific formulas and off-by-one bugs.

This applies everywhere — if you need "how many to remove", first find "how many to keep" and subtract once.

---

## Practice Checklist

| # | Problem | Difficulty | Pattern | Status |
|---|---------|-----------|---------|--------|
| 821 | Shortest Distance to a Character | Easy | Two-pass distance | ☐ |
| 135 | Candy | Medium | Two-pass min allocation | ☐ |
| 42 | Trapping Rain Water | Medium | Two-pass left/right max | ☐ |
| 845 | Longest Mountain in Array | Medium | Two-pass up/down count | ☐ |
| 1840 | Maximum Building Height | Hard | Two-pass + peak formula | ☐ |
| 1671 | Min Removals for Mountain Array | Hard | Two-pass LIS/LDS | ☐ |

### Recommended order: 821 → 135 → 42 → 845 → 1840 → 1671

---

## Cheat Sheet: How to Recognize Two-Pass Problems

### The 4 trigger questions (ask in interview)

1. **"Does position i depend on what's to its LEFT and RIGHT?"** → Two-pass
2. **"Are constraints propagating linearly in both directions?"** → Two-pass
3. **"Do I need to know a running max/min from both ends?"** → Two-pass
4. **"Am I struggling with tangled pointers going both ways?"** → Stop. Use two-pass.

### Keyword triggers in problem statements

| You read... | Think... | Example |
|---|---|---|
| "adjacent differ by at most k" | Constraints propagate linearly → two-pass | LC 1840 |
| "more than their neighbor" | Which neighbor? Both! → two-pass | LC 135 |
| "increasing then decreasing" | Mountain = up info + down info → two-pass | LC 845, 1671 |
| "nearest/closest occurrence" | Could be left or right → two-pass | LC 821 |
| "trapped between walls" | Need tallest wall on BOTH sides → two-pass | LC 42 |
| "minimum removals for shape" | Longest valid subsequence from both sides → two-pass | LC 1671 |

### The mental model

```
Pass 1 →→→→→→→→→  "What does the LEFT tell me about each position?"
Pass 2 ←←←←←←←←←  "What does the RIGHT tell me about each position?"
Combine:            "Now I know BOTH sides — merge and find the answer."
```

### What to store vs how to combine (per problem)

| Problem | Left pass stores | Right pass stores | Combine |
|---|---|---|---|
| 821 (Distance) | dist from left 'c' | dist from right 'c' | **min**(left, right) |
| 135 (Candy) | candies from left rule | candies from right rule | **max**(left, right) |
| 42 (Rain Water) | max height so far | max height from right | **min**(L, R) - height |
| 845 (Mountain) | consecutive ups ending here | consecutive downs starting here | up + down + 1 (if both > 0) |
| 1840 (Buildings) | height capped from left | height capped from right | peak formula between pairs |
| 1671 (Removals) | LIS length ending here | LDS length starting here | lis + lds - 1 (if both > 1) |

### Interview flow for two-pass problems

1. **Recognize:** "I need info from both directions" (use trigger questions above)
2. **State what each pass stores:** Be precise — "left pass stores the count of consecutive
   increasing steps ending at i" (not "some info about the left")
3. **State the combine rule:** "The answer at each position is max/min/sum of the two passes"
4. **Code it:** Two loops + one combine loop. Clean, bug-free, easy to verify.
5. **State complexity:** Almost always O(n) time, O(n) space.

That's it. Every problem above is just this template with different "what to store" and "how to combine".
