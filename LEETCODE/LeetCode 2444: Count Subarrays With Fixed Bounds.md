# LeetCode 2444: Count Subarrays With Fixed Bounds

## Problem Summary

Given `nums`, `minK`, `maxK` — count subarrays where min == minK and max == maxK.

---

## Your Mistake Analysis

### The Bug: Addition Instead of Multiplication

```python
# WRONG
count += (leastIndex - l) + (i - q2[0]) + 1

# CORRECT
count += (leastIndex - l + 1) * (i - q2[0] + 1)
```

### Why the Sum Formula Feels Right (But Isn't)

Your intuition was: "there are some extra starts on the left, some extra ends on the right, plus the base pair — add them up."

This treats the flexibility like a **linear extension**:
- "I can stretch left by `a` positions"
- "I can stretch right by `b` positions"
- "Total extras = a + b + 1 (the base)"

But that's wrong because stretching left and stretching right are **independent choices**.

#### Analogy

> You have 2 shirts and 3 pants. How many outfits?
> - WRONG: 2 + 3 = 5
> - RIGHT: 2 × 3 = 6

Each start position can combine with EACH end position. That's the **counting principle (rule of product)**.

### When the Bug Was Hidden

The sum formula `a + b + 1` equals the product `(a+1) × (b+1)` ONLY when `a == 0` or `b == 0`:

```
a=0, b=2: sum = 0+2+1 = 3,  product = 1×3 = 3  ✓ (same)
a=1, b=0: sum = 1+0+1 = 2,  product = 2×1 = 2  ✓ (same)
a=1, b=1: sum = 1+1+1 = 3,  product = 2×2 = 4  ✗ (DIFFERENT)
```

Most simple test cases have only one minK or one maxK occurrence, keeping one dimension at 1. The bug only surfaces when both dimensions > 1.

**Lesson:** Always test with cases where BOTH degrees of freedom are > 1.

### The Thought Process Error

The root cause is confusing **"or"** with **"and"**:
- "I can extend left OR right" → addition (mutually exclusive choices)
- "I choose a start AND an end" → multiplication (independent choices)

In this problem, the start and end are chosen **independently**, so it's always multiplication.

---

## Your Working Solution (Queue-Based)

```python
from collections import deque
from typing import List

class Solution:
    def countSubarrays(self, nums: List[int], minK: int, maxK: int) -> int:
        n = len(nums)
        count = 0
        i = 0

        while i < n:
            if nums[i] < minK or nums[i] > maxK:
                i += 1
                continue

            q1 = deque()  # indices where nums[j] == minK
            q2 = deque()  # indices where nums[j] == maxK
            l = i

            # Build the valid segment
            while i < n and minK <= nums[i] <= maxK:
                if nums[i] == minK:
                    q1.append(i)
                if nums[i] == maxK:
                    q2.append(i)
                i += 1
            i -= 1

            # Count valid subarrays by partitioning start positions
            while q1 and q2:
                if q1[0] > q2[0]:
                    q1, q2 = q2, q1
                leastIndex = q1.popleft()
                count += (leastIndex - l + 1) * (i - q2[0] + 1)
                l = leastIndex + 1

            i += 1

        return count
```

### Why This Works

1. **Segment isolation:** Split array at out-of-bound elements. Within a segment, all elements are in `[minK, maxK]`.

2. **Queue-based anchor pairing:** `q1` and `q2` hold positions of minK and maxK. Always process the smaller front first (swap to ensure `q1[0] < q2[0]`).

3. **Start partitioning:** After processing anchor at `leastIndex`, set `l = leastIndex + 1`. This ensures each start position is counted exactly once.

4. **Counting formula:** For anchor pair `(leastIndex, q2[0])`:
   - Valid starts: `[l, leastIndex]` → the subarray includes `leastIndex` (one required value)
   - Valid ends: `[q2[0], segment_end]` → the subarray includes `q2[0]` (the other required value)
   - Since `leastIndex ≤ q2[0]`, any subarray with start ≤ leastIndex and end ≥ q2[0] contains both.

### Note on the `minK == maxK` Special Case

Your code handles `minK == maxK` separately, but it's not needed. The main logic works for this case too (an element that equals both minK and maxK goes into BOTH queues). You can remove the special case for cleaner code.

---

## Optimal Solution (O(n) time, O(1) space)

```python
class Solution:
    def countSubarrays(self, nums: List[int], minK: int, maxK: int) -> int:
        ans = 0
        bad = -1       # last index with element outside [minK, maxK]
        lastMin = -1   # last index with element == minK
        lastMax = -1   # last index with element == maxK

        for i, num in enumerate(nums):
            if num < minK or num > maxK:
                bad = i
            if num == minK:
                lastMin = i
            if num == maxK:
                lastMax = i
            ans += max(0, min(lastMin, lastMax) - bad)

        return ans
```

### Why This Works

For each right endpoint `i`, count valid subarrays **ending** at `i`:
- Start must be > `bad` (no out-of-bound elements)
- Start must be ≤ `lastMin` (to include a minK)
- Start must be ≤ `lastMax` (to include a maxK)
- Valid starts: `(bad, min(lastMin, lastMax)]`
- Count = `min(lastMin, lastMax) - bad` (0 if negative)

### Why This Is Better

| Aspect | Queue Solution | Optimal Solution |
|--------|---------------|-----------------|
| Time | O(n) | O(n) |
| Space | O(n) for queues | O(1) |
| Code | ~30 lines | ~12 lines |
| Edge cases | Needs segment handling | Handles everything uniformly |
| `minK == maxK` | Works (or needs special case) | Works naturally |

---

## Pattern Recognition

### Pattern: "Count Subarrays With Property X"

When you see "count subarrays satisfying some condition," think:

**For each right endpoint `i`, how many valid left endpoints exist?**

This converts an O(n²) enumeration into O(n) by maintaining running state.

### Key Signals for This Pattern

1. The condition involves **extremes** (min, max) or **presence** of specific values
2. The array has a "validity boundary" (elements that break all subarrays crossing them)
3. You can express validity as: "the subarray must include at least one X and at least one Y"

### Template

```python
ans = 0
bad = -1       # last position that invalidates everything
lastX = -1     # last position satisfying condition X
lastY = -1     # last position satisfying condition Y

for i, num in enumerate(nums):
    if <invalidates subarray>:
        bad = i
    if <satisfies X>:
        lastX = i
    if <satisfies Y>:
        lastY = i
    ans += max(0, min(lastX, lastY) - bad)
```

---

## Similar Problems to Practice

### Direct Variants (Same Pattern)

| # | Problem | Key Idea |
|---|---------|----------|
| 795 | Number of Subarrays with Bounded Maximum | Track last valid, last invalid positions |
| 1248 | Count Number of Nice Subarrays | Track positions of odd numbers, count valid starts |
| 2062 | Count Vowel Substrings of a String | Must contain all 5 vowels, no consonants |
| 1358 | Number of Substrings Containing All Three Characters | Track last positions of 'a', 'b', 'c' |

### Sliding Window / Two Pointer Counting

| # | Problem | Key Idea |
|---|---------|----------|
| 992 | Subarrays with K Different Integers | atMost(K) - atMost(K-1) trick |
| 1695 | Maximum Erasure Value | Sliding window max sum with unique elements |
| 2537 | Count the Number of Good Subarrays | Track pairs count in window |

### Monotonic Queue/Stack Counting

| # | Problem | Key Idea |
|---|---------|----------|
| 907 | Sum of Subarray Minimums | Monotonic stack to find boundaries |
| 2104 | Sum of Subarray Ranges | Combine min and max contributions |
| 239 | Sliding Window Maximum | Classic monotonic deque |

---

## Key Takeaways

1. **Independent choices → multiply, not add.** When counting objects defined by multiple independent parameters (start AND end), use the rule of product.

2. **"For each endpoint, count valid partners"** is the go-to pattern for subarray counting problems. Maintains O(n) by tracking running state.

3. **Boundary-breaking elements** naturally partition the array. Track the last "bad" position to know where valid subarrays can start.

4. **Test with cases where all degrees of freedom are > 1.** If your formula has multiple terms, construct inputs where no term is zero to catch additive vs multiplicative errors.
