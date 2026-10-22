# Greedy Interval Covering — LC 757 Analysis

---

## Part 1: Problem Recap

**LC 757 – Set Intersection Size At Least Two**

Given intervals, find the minimum set of integers such that every interval contains **at least 2** of the chosen integers.

---

## Part 2: My Flawed Approach — Full Autopsy

### What I Did

```python
class Solution:
    def intersectionSizeTwo(self, intervals: List[List[int]]) -> int:
        intervals.sort(key=lambda x: (x[0], x[1]))
        intervalsNew = [[intervals[0][0], intervals[0][1]]]
        for start, end in intervals:
            if intervalsNew[-1][1] > start:
                intervalsNew[-1][1] = min(intervalsNew[-1][1], end)
                intervalsNew[-1][0] = intervalsNew[-1][1] - 1
            else:
                intervalsNew.append([start, end])

        res = [intervalsNew[0][1] - 1, intervalsNew[0][1]]
        for start, end in intervalsNew:
            if res[-1] >= start and res[-2] >= start:
                continue
            elif res[-1] >= start:
                res += [end]
            else:
                res += [end - 1, end]
        return len(res)
```

### Step-by-step Breakdown of What I Was Trying

1. **Sort by start** → process intervals left to right.
2. **Merge overlapping intervals** into their intersection, keeping only a 2-wide window (`[end-1, end]`).
3. **Greedily place numbers** from the merged list, picking from the right end.

### The Three Flaws

#### Flaw 1: Merging Destroys Information (Fatal)

When I merge `[3,5]` with `[3,7]`, I compute:
```
min(5, 7) = 5 → new end = 5
new start = 5 - 1 = 4
merged = [4, 5]
```

This **erases element 3** from the valid range. But 3 was the leftmost element of `[3,5]` and might be shared with a prior interval like `[1,3]`.

**Counterexample:** `[[1,3], [3,5], [3,7]]`

```
My code:
  Merge [3,5] + [3,7] → [4,5]        ← 3 is lost
  intervalsNew = [[1,3], [4,5]]       ← looks disjoint
  res = [2, 3, 4, 5]                  ← 4 numbers

Correct answer: {2, 3, 5} → 3 numbers
  [1,3] has {2,3} ✓
  [3,5] has {3,5} ✓
  [3,7] has {3,5} ✓
```

**Root cause:** Each original interval independently needs 2 elements. Replacing multiple intervals with one merged interval means I only enforce the "2 elements" requirement **once** instead of once per original interval. The merged interval is a lossy compression.

#### Flaw 2: Sorting by Start Is the Wrong Greedy Order

Sorting by start means I process wide intervals (ending far right) early. These are the **easiest** intervals to satisfy — they accept many numbers. Processing them first wastes greedy leverage.

The correct intuition: process the **hardest to satisfy** intervals first. The interval that ends earliest has the fewest choices, so it should drive the decisions.

#### Flaw 3: `>` vs `>=` Overlap Check

```python
if intervalsNew[-1][1] > start:  # misses the case where end == start
```

Intervals `[1,3]` and `[3,5]` share element 3, so they overlap. But `3 > 3` is `False`, so my code treats them as disjoint. This occasionally leads to over-counting.

---

## Part 3: The Correct Approach — Why It Works

### The Algorithm

```python
class Solution:
    def intersectionSizeTwo(self, intervals: List[List[int]]) -> int:
        intervals.sort(key=lambda x: (x[1], -x[0]))
        count = 0
        p1 = -1  # second largest chosen
        p2 = -1  # largest chosen

        for start, end in intervals:
            if start <= p1:
                continue
            elif start <= p2:
                p1 = p2
                p2 = end
                count += 1
            else:
                p1 = end - 1
                p2 = end
                count += 2
        return count
```

### Why Sort by End Ascending?

The interval that **ends earliest** is the most constrained — it has the fewest valid numbers to choose from. By processing it first, we ensure we don't accidentally make choices that miss it.

**Why `-x[0]` for ties?** Among intervals with the same right endpoint, the one with the **wider** range (smaller start) is easier to satisfy. Process the narrower (larger start) ones first so the wider ones get covered for free.

### Why Track Only `p1` and `p2`?

Since intervals are processed in order of increasing right endpoint, every future interval ends at or after the current one. The only question is whether its **start** overlaps with our chosen numbers.

The two **largest** chosen numbers are the most likely to overlap with future intervals. Older, smaller chosen numbers will never help a future interval that a larger number doesn't already help. So `p1` and `p2` are sufficient.

### The Three Cases

```
Interval: [start, end]
p1 = second largest chosen, p2 = largest chosen

Case 1: start ≤ p1
  → Both p1 and p2 fall inside [start, end]. Already covered. Skip.

Case 2: p1 < start ≤ p2
  → Only p2 is inside. Need 1 more. Pick `end` (rightmost possible).
  → Update: p1 = p2 (old largest becomes second), p2 = end (new largest).

Case 3: start > p2
  → Neither is inside. Need 2 more. Pick `end-1` and `end`.
  → Update: p1 = end-1, p2 = end.
```

**Why always pick from the right end?** Picking as far right as possible maximizes overlap with future intervals (which all end ≥ current end).

### Trace: `[[1,3], [3,5], [3,7]]`

```
Sort by (end, -start): [[1,3], [3,5], [3,7]]

[1,3]: start=1 > p2=-1 → Case 3 → pick 2,3    → p1=2, p2=3, count=2
[3,5]: start=3 ≤ p2=3  → Case 2 → pick 5       → p1=3, p2=5, count=3
[3,7]: start=3 ≤ p1=3  → Case 1 → skip          → count=3 ✓
```

---

## Part 4: Pattern — Greedy Interval Problems

### The Family

| Problem | Sort By | Greedy Strategy |
|---|---|---|
| **Max non-overlapping intervals** (LC 435) | End ↑ | Pick earliest-ending, skip conflicts |
| **Min arrows to burst balloons** (LC 452) | End ↑ | One arrow at each earliest end |
| **Intersection size ≥ 2** (LC 757) | End ↑ | Track 2 rightmost picks |
| **Interval scheduling** (classic) | End ↑ | Always pick earliest finish |
| **Min platforms** (classic) | Events | Sweep line |
| **Merge intervals** (LC 56) | Start ↑ | Extend or close |

### The Universal Rule

> **When selecting points/resources to cover intervals, sort by END ascending.**

Why? The earliest-ending interval is the bottleneck. It has the fewest valid positions. Handle it first, pick as late as possible within it, and future intervals benefit from the overlap.

### When to Sort by Start vs End

| Sort by Start | Sort by End |
|---|---|
| **Merging / grouping** intervals | **Selecting points** to hit intervals |
| "Which intervals overlap?" | "What's the minimum to cover all?" |
| LC 56 Merge Intervals | LC 435, 452, 757 |

### Template for "Cover Every Interval with K Points"

```python
def minCoveringSet(intervals, k):
    intervals.sort(key=lambda x: (x[1], -x[0]))
    chosen = []  # track k largest chosen numbers

    for start, end in intervals:
        # count how many of `chosen` fall inside [start, end]
        inside = sum(1 for c in chosen if c >= start)
        need = k - inside
        for i in range(need):
            # pick from the right: end, end-1, end-2, ...
            # but skip values already chosen
            val = end - i
            while val in chosen:
                val -= 1
            chosen.append(val)
        chosen.sort()
        chosen = chosen[-k:]  # only keep k largest

    return len(chosen_total)  # or track count separately
```

For k=2, this simplifies to the `p1`/`p2` solution (no list needed, just two variables).

---

## Part 5: Mistakes to Avoid

### 1. Don't Merge When You Should Select

Merging is for **"combine overlapping intervals into groups"** problems. Selection problems need you to **preserve every original interval's constraint**.

**Litmus test:** Does each interval impose an independent requirement (like "must contain 2 points")? If yes → don't merge.

### 2. Don't Sort by Start for Selection Problems

Sorting by start processes the easy (wide) intervals first and the hard (narrow, early-ending) ones later, when it's too late to adjust.

**Litmus test:** Am I choosing points/resources to satisfy constraints? → Sort by end.

### 3. Don't Compress State Lossily

My merge step replaced `[3,5]` with `[4,5]`, losing element 3. The correct approach tracks **chosen values** (p1, p2), not compressed intervals.

**Litmus test:** After my transformation, can I reconstruct all original constraints? If not → the compression is lossy and dangerous.

### 4. Watch Out for `>` vs `>=`

In interval problems, whether endpoints are inclusive matters. `[1,3]` and `[3,5]` share element 3 — they overlap. Always double-check boundary conditions.

---

## Part 6: Quick Reference

```
PROBLEM TYPE                     SORT BY       TRACK
─────────────────────────────────────────────────────
Merge overlapping intervals      start ↑       current end
Min points to hit all intervals  end ↑         last chosen point
Min points, ≥2 per interval      end ↑         last 2 chosen (p1, p2)
Min points, ≥k per interval      end ↑         last k chosen
Max non-overlapping intervals    end ↑         last chosen end
Min arrows (burst balloons)      end ↑         last arrow position
```

**Golden rule:** Sort by end. Pick rightmost. Track only what future intervals need.
