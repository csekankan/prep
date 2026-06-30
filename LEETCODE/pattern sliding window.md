# Sliding Window — Counting Subarrays / Substrings

## What Is This Pattern?

A subclass of sliding window where instead of finding the **longest/shortest** window, you need to **count** how many valid subarrays or substrings exist.

The key insight that separates this from length-finding problems:

> **For each right endpoint, count valid left endpoints directly — don't enumerate all pairs.**

Why brute force fails: checking all O(n²) pairs is too slow. The sliding window observes that validity often has a **monotone** property — once a window becomes valid (or invalid), extending it in one direction keeps it valid (or invalid). This lets you count with a single pass.

---

## Core Intuition: Why `result += left` Works

This is the hardest idea to internalize, so let's build it from scratch.

**Problem:** Count substrings of `"xyzabc"` containing all of 'a', 'b', 'c'.

Imagine you're at `right = 5` (the 'c'). You need all substrings **ending here** that contain a, b, c.

```
Index:  0  1  2  3  4  5
Char:   x  y  z  a  b  c
                  ^  ^  ^
                  |  |  right
```

Which starting indices form valid substrings ending at 5?
- Start 0: "xyzabc" → has a,b,c ✓
- Start 1: "yzabc"  → has a,b,c ✓
- Start 2: "zabc"   → has a,b,c ✓
- Start 3: "abc"    → has a,b,c ✓
- Start 4: "bc"     → missing a ✗
- Start 5: "c"      → missing a,b ✗

So starts 0,1,2,3 work → 4 valid substrings.

Now, using the sliding window: shrink `left` while window is valid.
After shrinking: `left = 4` (first position that makes window invalid).
`result += left = 4`. ✓

**The key:** `left` is the **boundary** between valid and invalid start positions.
Every index `0..left-1` is a valid start. There are exactly `left` of them.

```
  start here → valid ✓    start here → invalid ✗
  ↓                        ↓
  0   1   2   3   |   4   5
  ←── left valid ──→   ←── invalid ──→
                   ↑
                  left = 4
  result += 4
```

---

## The Four Variants

### Variant A — "At Least" / "Contains All": `result += left`

**When to use:**
- "Contains at least one of each character"
- "Subarray with at least K occurrences of some element"
- "Sum ≥ K" (but counting, not finding length)

**The property:** If `s[i..j]` is valid, then `s[i-1..j]` is also valid (extending left keeps it valid).

**Shrink direction:** Shrink `left` **while valid** → left lands at the first invalid position → count = `left`.

**Template:**
```python
left = 0
result = 0
state = {}   # or array, counter, etc.

for right in range(n):
    add(state, arr[right])              # expand right

    while window_is_valid(state):       # ← while VALID (not invalid!)
        remove(state, arr[left])
        left += 1

    result += left                      # 0..left-1 are all valid starts
```

---

#### Example A-1: LC 1358 — Substrings Containing All Three Characters

**Problem:** Count substrings of `s` (only 'a','b','c') that contain at least one of each.

**Why Variant A?** If `s[i..j]` contains a,b,c, then `s[i-1..j]` (any extension left) also contains a,b,c. ✓

```python
def numberOfSubstrings(self, s: str) -> int:
    count = [0, 0, 0]
    left = 0
    result = 0

    for right in range(len(s)):
        count[ord(s[right]) - ord('a')] += 1

        while count[0] > 0 and count[1] > 0 and count[2] > 0:
            count[ord(s[left]) - ord('a')] -= 1
            left += 1

        result += left   # starts 0..left-1 all give valid substrings ending at right

    return result
```

**Full dry run on `"abcabc"`:**

```
State before each step: count=[a,b,c], left, result

right=0, s[0]='a':  count=[1,0,0] → not valid, while skipped
                    left=0, result += 0 → result=0

right=1, s[1]='b':  count=[1,1,0] → not valid, while skipped
                    left=0, result += 0 → result=0

right=2, s[2]='c':  count=[1,1,1] → valid! enter while:
                       remove s[0]='a' → count=[0,1,1], left=1 → not valid, exit
                    result += left=1 → result=1
                    (substrings ending at 2 with all 3: "abc"[0..2])

right=3, s[3]='a':  count=[1,1,1] → valid! enter while:
                       remove s[1]='b' → count=[1,0,1], left=2 → not valid, exit
                    result += left=2 → result=3
                    (substrings ending at 3: "abca"[0..3], "bca"[1..3])

right=4, s[4]='b':  count=[1,1,1] → valid! enter while:
                       remove s[2]='c' → count=[1,1,0], left=3 → not valid, exit
                    result += left=3 → result=6
                    (substrings ending at 4: [0..4],[1..4],[2..4])

right=5, s[5]='c':  count=[1,1,1] → valid! enter while:
                       remove s[3]='a' → count=[0,1,1], left=4 → not valid, exit
                    result += left=4 → result=10
                    (substrings ending at 5: [0..5],[1..5],[2..5],[3..5])

Final: 10 ✓
```

---

#### Example A-2: LC 2962 — Count Subarrays Where Max Element Appears At Least K Times

**Problem:** Given `nums` and `k`, count subarrays where the maximum element of `nums` appears at least `k` times.

**Key insight:** First find the global max. Then count subarrays where it appears ≥ k times.
If a subarray has max appearing ≥k times, extending it left keeps it valid. → Variant A.

```python
def countSubarrays(self, nums: List[int], k: int) -> int:
    global_max = max(nums)
    max_count = 0
    left = 0
    result = 0

    for right in range(len(nums)):
        if nums[right] == global_max:
            max_count += 1

        # shrink while max appears ≥ k times (window is "valid")
        while max_count >= k:
            if nums[left] == global_max:
                max_count -= 1
            left += 1

        # starts 0..left-1 all give subarrays ending at right with ≥k max elements
        result += left

    return result
```

**Dry run on `nums=[1,3,2,3,3], k=2`:**

```
global_max = 3

right=0, nums[0]=1:  max_count=0, not valid → left=0, result+=0 → 0
right=1, nums[1]=3:  max_count=1, not valid → left=0, result+=0 → 0
right=2, nums[2]=2:  max_count=1, not valid → left=0, result+=0 → 0
right=3, nums[3]=3:  max_count=2, ≥k=2 → valid! enter while:
                        remove nums[0]=1 (not max), left=1 → still 2, valid
                        remove nums[1]=3 (max!), max_count=1, left=2 → not valid
                     result += left=2 → result=2
                     (subarrays ending at 3: [0..3]=[1,3,2,3], [1..3]=[3,2,3])

right=4, nums[4]=3:  max_count=2, ≥k=2 → valid! enter while:
                        remove nums[2]=2 (not max), left=3 → still 2, valid
                        remove nums[3]=3 (max!), max_count=1, left=4 → not valid
                     result += left=4 → result=6

Final: 6 ✓
Subarrays: [0..3],[1..3],[0..4],[1..4],[2..4],[3..4] ← all have 3 appearing ≥2 times
```

---

#### Example A-3: LC 2537 — Count the Number of Good Subarrays

**Problem:** Count subarrays with at least `k` pairs `(i,j)` where `i < j` and `nums[i] == nums[j]`.

**Key insight:** Track `pairs` = number of equal pairs in current window. When we add `nums[right]`, new pairs = frequency of that value so far. Extend left keeps pairs valid. → Variant A.

```python
def countGood(self, nums: List[int], k: int) -> int:
    freq = {}
    pairs = 0
    left = 0
    result = 0

    for right in range(len(nums)):
        freq[nums[right]] = freq.get(nums[right], 0) + 1
        pairs += freq[nums[right]] - 1   # new pairs formed with nums[right]

        while pairs >= k:
            freq[nums[left]] -= 1
            pairs -= freq[nums[left]]    # pairs removed when left shrinks
            left += 1

        result += left

    return result
```

**Why `pairs -= freq[nums[left]]`?** Before decrementing `freq[nums[left]]`, there are `freq[nums[left]]` copies. After removing one from left, the remaining copies is `freq[nums[left]] - 1`. The removed pairs = `freq[nums[left]] - 1` = (new freq). So: decrement first, then subtract new freq.

---

### Variant B — "At Most K": `result += right - left + 1`

**When to use:**
- "At most K distinct elements"
- "Product less than K"
- "Sum ≤ K"

**The property:** If `s[i..j]` is valid, then `s[i+1..j]` is also valid (shrinking keeps it valid).

**Shrink direction:** Shrink `left` **while invalid** → left lands at the first valid position → all windows `[left..right], [left+1..right], ..., [right..right]` are valid → count = `right - left + 1`.

**Template:**
```python
left = 0
result = 0
state = {}

for right in range(n):
    add(state, arr[right])              # expand right

    while window_is_invalid(state):     # ← while INVALID (not valid!)
        remove(state, arr[left])
        left += 1

    result += right - left + 1         # all windows ending at right, starting left..right
```

---

#### Example B-1: LC 713 — Subarray Product Less Than K

**Problem:** Count subarrays where the product of all elements is strictly less than `k`.

**Why Variant B?** If product < k in window [i..j], shrinking to [i+1..j] keeps product < k (it gets smaller). ✓

```python
def numSubarrayProductLessThanK(self, nums: List[int], k: int) -> int:
    if k <= 1:
        return 0       # product ≥ 1 always, so nothing works
    product = 1
    left = 0
    result = 0

    for right in range(len(nums)):
        product *= nums[right]

        while product >= k:         # invalid: shrink until valid
            product //= nums[left]
            left += 1

        result += right - left + 1  # subarrays ending at right: [left..right]..[right..right]

    return result
```

**Full dry run on `nums=[10,5,2,6], k=100`:**

```
right=0, nums[0]=10:  product=10 < 100, valid
                      result += 0-0+1=1 → result=1
                      (subarrays ending at 0: [10])

right=1, nums[1]=5:   product=50 < 100, valid
                      result += 1-0+1=2 → result=3
                      (subarrays ending at 1: [10,5] and [5])

right=2, nums[2]=2:   product=100 ≥ 100 → invalid, shrink:
                         product//=10 → product=10, left=1, now valid
                      result += 2-1+1=2 → result=5
                      (subarrays ending at 2: [5,2] and [2])

right=3, nums[3]=6:   product=60 < 100, valid
                      result += 3-1+1=3 → result=8
                      (subarrays ending at 3: [5,2,6],[2,6],[6])

Final: 8 ✓
All valid subarrays: [10],[5],[2],[6],[10,5],[5,2],[2,6],[5,2,6]
```

**Verify [10,5] = 50 < 100 ✓, [10,5,2] = 100 ✗ (excluded), [5,2,6] = 60 < 100 ✓**

---

#### Example B-2: LC 2302 — Count Subarrays With Score Less Than K

**Problem:** Score of a subarray = sum × length. Count subarrays with score < k.

```python
def countSubarrays(self, nums: List[int], k: int) -> int:
    left = 0
    curr_sum = 0
    result = 0

    for right in range(len(nums)):
        curr_sum += nums[right]

        while curr_sum * (right - left + 1) >= k:   # score invalid
            curr_sum -= nums[left]
            left += 1

        result += right - left + 1

    return result
```

**Dry run on `nums=[2,1,4,3,5], k=10`:**

```
right=0: sum=2, length=1, score=2 < 10 ✓, result+=1 → 1
right=1: sum=3, length=2, score=6 < 10 ✓, result+=2 → 3
right=2: sum=7, length=3, score=21 ≥ 10 → shrink:
           remove 2, sum=5, left=1, score=5×2=10 ≥ 10 → shrink:
           remove 1, sum=4, left=2, score=4×1=4 < 10 ✓
         result += 2-2+1=1 → 4
right=3: sum=7, length=2, score=14 ≥ 10 → shrink:
           remove 4, sum=3, left=3, score=3×1=3 < 10 ✓
         result += 3-3+1=1 → 5
right=4: sum=8, length=2, score=16 ≥ 10 → shrink:
           remove 3, sum=5, left=4, score=5×1=5 < 10 ✓
         result += 4-4+1=1 → 6

Final: 6
```

---

### Variant C — Exactly K: `at_most(k) − at_most(k−1)`

**When to use:**
- "Exactly K distinct elements"
- "Sum equals exactly K"
- "Exactly K odd numbers"

**Why direct sliding window fails for "exactly K":**
When you add an element and reach exactly K distinct, the window is valid. But if you add another element of a new type, you have K+1 and must shrink. The problem: after shrinking, you might end up with K-1 distinct, not K. The window "jumps" over exactly-K states. So you can't accumulate counts cleanly.

**The fix:** Count with two "at most" calls:
```
exactly(k) = at_most(k) − at_most(k−1)
```

**Visual proof:**
```
Subarrays with ≤ 3 distinct:  ●●●●●●●●●●●●●●●  (some count)
Subarrays with ≤ 2 distinct:  ●●●●●●●●●●        (smaller count)
─────────────────────────────────────────────────
Subarrays with exactly 3:     ─────────●●●●●    (difference)
```

**Template:**
```python
def count_exactly_k(nums, k):
    return at_most(nums, k) - at_most(nums, k - 1)

def at_most(nums, k):
    if k < 0:
        return 0
    freq = {}
    left = 0
    result = 0
    for right in range(len(nums)):
        freq[nums[right]] = freq.get(nums[right], 0) + 1
        while len(freq) > k:
            freq[nums[left]] -= 1
            if freq[nums[left]] == 0:
                del freq[nums[left]]
            left += 1
        result += right - left + 1
    return result
```

---

#### Example C-1: LC 992 — Subarrays with K Different Integers

**Problem:** Count subarrays with exactly `k` distinct integers.

```python
def subarraysWithKDistinct(self, nums: List[int], k: int) -> int:
    def at_most(k):
        freq = {}
        left = 0
        result = 0
        for right in range(len(nums)):
            freq[nums[right]] = freq.get(nums[right], 0) + 1
            while len(freq) > k:
                freq[nums[left]] -= 1
                if freq[nums[left]] == 0:
                    del freq[nums[left]]
                left += 1
            result += right - left + 1
        return result

    return at_most(k) - at_most(k - 1)
```

**Full dry run on `nums=[1,2,1,2,3], k=2`:**

First, `at_most(2)`:
```
right=0, val=1: freq={1:1}, distinct=1 ≤ 2 ✓ → result+=1 → 1
right=1, val=2: freq={1:1,2:1}, distinct=2 ≤ 2 ✓ → result+=2 → 3
right=2, val=1: freq={1:2,2:1}, distinct=2 ≤ 2 ✓ → result+=3 → 6
right=3, val=2: freq={1:2,2:2}, distinct=2 ≤ 2 ✓ → result+=4 → 10
right=4, val=3: freq={1:2,2:2,3:1}, distinct=3 > 2 → shrink:
                   remove nums[0]=1, freq={1:1,2:2,3:1}, left=1, distinct=3 still > 2
                   remove nums[1]=2, freq={1:1,2:1,3:1}, left=2, distinct=3 still > 2
                   remove nums[2]=1, freq={2:1,3:1}, left=3, distinct=2 ≤ 2 ✓
                result += 4-3+1=2 → 12
at_most(2) = 12
```

Now `at_most(1)`:
```
right=0, val=1: freq={1:1}, distinct=1 ✓ → result+=1 → 1
right=1, val=2: freq={1:1,2:1}, distinct=2 > 1 → shrink:
                   remove nums[0]=1, freq={2:1}, left=1, distinct=1 ✓
                result += 1-1+1=1 → 2
right=2, val=1: freq={2:1,1:1}, distinct=2 > 1 → shrink:
                   remove nums[1]=2, freq={1:1}, left=2, distinct=1 ✓
                result += 2-2+1=1 → 3
right=3, val=2: freq={1:1,2:1}, distinct=2 > 1 → shrink:
                   remove nums[2]=1, freq={2:1}, left=3, distinct=1 ✓
                result += 3-3+1=1 → 4
right=4, val=3: freq={2:1,3:1}, distinct=2 > 1 → shrink:
                   remove nums[3]=2, freq={3:1}, left=4, distinct=1 ✓
                result += 4-4+1=1 → 5
at_most(1) = 5
```

**Answer: 12 - 5 = 7 ✓**

Verify: subarrays with exactly 2 distinct:
[1,2], [2,1], [1,2], [2,3], [1,2,1], [2,1,2], [1,2,1,2] → 7 ✓

---

#### Example C-2: LC 1248 — Count Number of Nice Subarrays

**Problem:** Count subarrays with exactly `k` odd numbers.

**Key insight:** Reframe — treat odd=1, even=0. Then "exactly k odd numbers" = "subarray sum exactly k". Use the complementary trick.

```python
def numberOfSubarrays(self, nums: List[int], k: int) -> int:
    def at_most(k):
        if k < 0:
            return 0
        left = 0
        result = 0
        odd_count = 0
        for right in range(len(nums)):
            if nums[right] % 2 == 1:
                odd_count += 1
            while odd_count > k:
                if nums[left] % 2 == 1:
                    odd_count -= 1
                left += 1
            result += right - left + 1
        return result

    return at_most(k) - at_most(k - 1)
```

**Dry run on `nums=[1,1,2,1,1], k=3`:**

```
at_most(3):
right=0, odd=1: count=1 ✓, result+=1 → 1
right=1, odd=1: count=2 ✓, result+=2 → 3
right=2, even:  count=2 ✓, result+=3 → 6
right=3, odd=1: count=3 ✓, result+=4 → 10
right=4, odd=1: count=4 > 3 → shrink:
                  remove nums[0]=1(odd), count=3, left=1 ✓
                result += 4-1+1=4 → 14
at_most(3) = 14

at_most(2):
right=0: count=1, result+=1 → 1
right=1: count=2, result+=2 → 3
right=2: count=2, result+=3 → 6
right=3: count=3 > 2 → shrink:
           remove nums[0]=1, count=2, left=1 ✓
           result += 3-1+1=3 → 9
right=4: count=3 > 2 → shrink:
           remove nums[1]=1, count=2, left=2 ✓
           result += 4-2+1=3 → 12
at_most(2) = 12

Answer: 14 - 12 = 2 ✓
Subarrays with exactly 3 odds: [1,1,2,1] and [1,2,1,1]
```

---

### Variant D — Fixed-Size Window Counting

**When to use:**
- "Subarrays of EXACTLY size K with..."
- "Every window of size K satisfying a condition"

The window size is fixed. You don't shrink based on validity — you slide a rigid window.

**Template:**
```python
def count_fixed_window(arr, k, is_valid):
    n = len(arr)
    result = 0
    state = initial_state()

    # build first window
    for i in range(k):
        add(state, arr[i])
    if is_valid(state):
        result += 1

    # slide
    for right in range(k, n):
        add(state, arr[right])
        remove(state, arr[right - k])    # always remove the element k steps back
        if is_valid(state):
            result += 1

    return result
```

---

#### Example D-1: LC 1876 — Substrings of Size Three with Distinct Characters

**Problem:** Count substrings of length exactly 3 with all distinct characters.

```python
def countGoodSubstrings(self, s: str) -> int:
    result = 0
    for i in range(len(s) - 2):
        if s[i] != s[i+1] and s[i+1] != s[i+2] and s[i] != s[i+2]:
            result += 1
    return result
```

Or the sliding window form:
```python
def countGoodSubstrings(self, s: str) -> int:
    freq = {}
    result = 0
    k = 3

    for i in range(len(s)):
        freq[s[i]] = freq.get(s[i], 0) + 1
        if i >= k:
            freq[s[i - k]] -= 1
            if freq[s[i - k]] == 0:
                del freq[s[i - k]]
        if i >= k - 1 and len(freq) == k:
            result += 1

    return result
```

---

#### Example D-2: LC 2841 — Maximum Sum of Almost Unique Subarrays

**Problem:** Given `nums`, find the maximum sum of a subarray of length `k` with at least `m` distinct elements.

```python
def maxSum(self, nums: List[int], m: int, k: int) -> int:
    freq = {}
    window_sum = 0
    result = 0

    for right in range(len(nums)):
        freq[nums[right]] = freq.get(nums[right], 0) + 1
        window_sum += nums[right]

        if right >= k:
            old = nums[right - k]
            window_sum -= old
            freq[old] -= 1
            if freq[old] == 0:
                del freq[old]

        if right >= k - 1 and len(freq) >= m:
            result = max(result, window_sum)

    return result
```

---

### Variant E — Two Boundaries (Double Invalid Pointer)

**When to use:**
- Subarray must have `min ≥ minK` AND `max ≤ maxK`
- Subarray must satisfy both a lower and an upper bound simultaneously

The standard shrinking approach breaks down because a window can be invalid for **two independent reasons** (value too small OR value too large). You can't restore validity by removing just the left element.

**The trick:** Track three pointers:
- `bad`: last index where element was out of range (invalid element)
- `lo`: last index where element == minK
- `hi`: last index where element == maxK

For each `right`: valid subarrays ending here must start **after** `bad` AND have seen both `minK` and `maxK`. That means start must be in range `(bad, min(lo, hi)]`.

Count = `max(0, min(lo, hi) - bad)`

---

#### Example E-1: LC 2444 — Count Subarrays with Fixed Bounds

**Problem:** Count subarrays where `min = minK` AND `max = maxK`.

```python
def countSubarrays(self, nums: List[int], minK: int, maxK: int) -> int:
    result = 0
    bad = lo = hi = -1          # -1 = "never seen"

    for right, val in enumerate(nums):
        # if val is out of [minK, maxK], the subarray is broken here
        if not (minK <= val <= maxK):
            bad = right

        if val == minK:
            lo = right          # last time we saw minK
        if val == maxK:
            hi = right          # last time we saw maxK

        # subarray ending at right with both minK and maxK:
        # must start after bad (exclusive)
        # must include both lo and hi → start ≤ min(lo, hi)
        # count = min(lo, hi) - bad  (if positive)
        result += max(0, min(lo, hi) - bad)

    return result
```

**Dry run on `nums=[1,3,5,2,7,5], minK=1, maxK=5`:**

```
right=0, val=1: bad=-1, lo=0, hi=-1
                min(lo,hi)=min(0,-1)=-1, -1-(-1)=0, result+=0 → 0
right=1, val=3: in range, lo=0, hi=-1
                min=-1, result+=0 → 0
right=2, val=5: in range, lo=0, hi=2
                min(0,2)=0, 0-(-1)=1, result+=1 → 1
                (subarray [0..2]=[1,3,5]: min=1✓ max=5✓)
right=3, val=2: in range, lo=0, hi=2
                min(0,2)=0, 0-(-1)=1, result+=1 → 2
                (subarray [0..3]=[1,3,5,2]: min=1✓ max=5✓)
right=4, val=7: 7 > maxK=5 → bad=4, lo=0, hi=2
                min(0,2)=0, 0-4=-4, max(0,-4)=0, result+=0 → 2
right=5, val=5: in range, lo=0, hi=5
                min(0,5)=0, 0-4=-4, max(0,-4)=0, result+=0 → 2

Final: 2 ✓  ([1,3,5] and [1,3,5,2])
```

---

## Similar Adjacent Patterns

### Pattern: Prefix Sum + HashMap for Counting

**When:** The condition is a specific target sum (not "at most" or "at least"), and elements can be negative or zero (so shrinking doesn't guarantee monotone validity).

Sliding window **fails** when:
- Elements can be 0 or negative (sum can decrease while extending right)
- You need exact count of subarrays with sum = target

**Use instead:** Prefix sums + hash map to count in O(n).

```
prefix[j] - prefix[i] = target
⟺ prefix[i] = prefix[j] - target
```

For each `j`, count how many previous `i`s had `prefix[i] = prefix[j] - target`.

```python
def subarraySum(self, nums: List[int], k: int) -> int:
    count = {0: 1}   # prefix_sum → frequency; 0 seen once (empty prefix)
    prefix_sum = 0
    result = 0

    for num in nums:
        prefix_sum += num
        result += count.get(prefix_sum - k, 0)
        count[prefix_sum] = count.get(prefix_sum, 0) + 1

    return result
```

**When to use prefix sum vs sliding window:**

| Situation | Use |
|---|---|
| Elements are all positive | Sliding window (sum is monotone) |
| Elements can be 0 or negative | Prefix sum + hashmap |
| Condition is "at most K" or "exactly K" with positive elements | Sliding window Variant B/C |
| Condition is "sum = K" with any elements | Prefix sum + hashmap |
| Condition is "sum divisible by K" | Prefix sum + hashmap (modular arithmetic) |

---

### Pattern: Monotonic Deque for Counting with Min/Max Constraints

**When:** You need to count subarrays where `max - min ≤ k` (or some condition involving both min and max simultaneously).

Two deques — one tracking min, one tracking max — let you maintain window bounds efficiently.

```python
def countSubarrays(self, nums: List[int], k: int) -> int:
    from collections import deque
    min_d = deque()   # increasing (front = min)
    max_d = deque()   # decreasing (front = max)
    left = 0
    result = 0

    for right in range(len(nums)):
        while min_d and nums[min_d[-1]] >= nums[right]:
            min_d.pop()
        while max_d and nums[max_d[-1]] <= nums[right]:
            max_d.pop()
        min_d.append(right)
        max_d.append(right)

        while nums[max_d[0]] - nums[min_d[0]] > k:
            left += 1
            if min_d[0] < left: min_d.popleft()
            if max_d[0] < left: max_d.popleft()

        result += right - left + 1   # Variant B: all valid windows ending here

    return result
```

**Example:** LC 2401 — Longest Nice Subarray (every pair of elements shares no bits), LC 1438 — Longest Continuous Subarray With Absolute Diff ≤ Limit.

---

### Pattern: Two-Pass / Contribution Counting

**When:** You can count each element's "contribution" to the answer independently.

Instead of sliding a window, for each element ask: "In how many subarrays does this element satisfy the condition?"

**Example:** LC 828 — Count Unique Characters of All Substrings:

```python
def uniqueLetterString(self, s: str) -> int:
    # For each character, count subarrays where it's the ONLY occurrence
    # Contribution of s[i] = (i - prev_occurrence) × (next_occurrence - i)
    last = {}
    result = 0
    prev = [-1] * len(s)

    for i, ch in enumerate(s):
        prev[i] = last.get(ch, -1)
        last[ch] = i

    last = {ch: len(s) for ch in s}
    for i in range(len(s) - 1, -1, -1):
        ch = s[i]
        result += (i - prev[i]) * (last[ch] - i)
        last[ch] = i

    return result
```

---

## How to Identify Which Variant to Use

### Step-by-step identification flowchart

```
Read the problem carefully.
         │
         ▼
Is it asking to COUNT subarrays / substrings?
         │
    YES  │   NO → probably "find longest/shortest" → standard sliding window
         ▼
Can elements be negative or zero?
         │
    YES  │   NO ──────────────────────────────────────────────────────────────┐
         ▼                                                                     │
Use Prefix Sum + HashMap                                                       │
(sliding window fails with negatives)                                          │
                                              ┌────────────────────────────────┘
                                              ▼
                             Does condition use "exactly K"?
                                              │
                                         YES  │  NO
                                              ▼    ▼
                                     Variant C     │
                              at_most(k)−at_most(k-1)
                                                   │
                                Does condition use "at most K"?
                                                   │
                                              YES  │  NO
                                              ▼         ▼
                                         Variant B      │
                                     result += right-left+1
                                                        │
                                Does condition use "at least / contains all"?
                                                        │
                                                   YES  │  NO
                                                   ▼         ▼
                                              Variant A      │
                                          result += left     │
                                                        Is window size FIXED?
                                                             │
                                                        YES  │  NO
                                                        ▼         ▼
                                                   Variant D   Variant E
                                                (fixed window)  (dual bounds)
```

### Keyword → Variant quick lookup

| Keyword in problem | Variant | Result line |
|---|---|---|
| "containing all three / every / all of" | A | `+= left` |
| "at least K times" | A | `+= left` |
| "at most K distinct" | B | `+= right-left+1` |
| "product < K" | B | `+= right-left+1` |
| "score < K" (sum×length) | B | `+= right-left+1` |
| "exactly K distinct" | C | `at_most(K) - at_most(K-1)` |
| "exactly K odd/even numbers" | C | `at_most(K) - at_most(K-1)` |
| "sum equals K" (positive elements) | C | `at_most(K) - at_most(K-1)` |
| "sum equals K" (any elements) | Prefix sum | HashMap lookup |
| "size exactly K with condition" | D | Fixed slide |
| "min = X AND max = Y" | E | Track 3 pointers |
| "max - min ≤ K" | Deque + B | Deque for min/max |

---

## Common Mistakes and How to Avoid Them

### Mistake 1: Pair counting as a proxy for substring counting

The original bug that led to this document.

```python
# WRONG: bc + cb counts ordered index PAIRS
# "bcbc" → bc=3, cb=1 → 4 pairs
# But only 3 substrings of "bcbc" contain both b and c

# WHY IT FAILS:
# substring "bcbc" [0..3] covers pairs (b@0,c@1), (b@0,c@3), (b@2,c@3) = 3 pairs alone
# One substring inflates the count by covering multiple pairs
```

**Fix:** Use `result += left` (count starting positions, not pairs).

---

### Mistake 2: Using `if` instead of `while`

```python
# WRONG — only removes ONE element, window may still be invalid
for right in range(n):
    add(arr[right])
    if invalid():               # ← if: only handles single violation
        remove(arr[left])
        left += 1
    result += ...

# CORRECT — removes until valid (or invalid, per variant)
for right in range(n):
    add(arr[right])
    while invalid():            # ← while: handles any number of violations
        remove(arr[left])
        left += 1
    result += ...
```

---

### Mistake 3: Confusing which direction to shrink in A vs B

```
Variant A:                    Variant B:
shrink WHILE valid            shrink WHILE invalid
left lands at INVALID         left lands at VALID
result += left                result += right - left + 1
(count from outside)          (count from inside)
```

Memory device: In A, the "valid zone" is to the left of `left` (outside the current window). In B, the "valid zone" IS the current window.

---

### Mistake 4: Missing the guard `if k < 0: return 0` in Variant C

```python
# at_most(-1) is called when goal=0 and you compute at_most(goal-1)
def at_most(k):
    if k < 0:
        return 0    # ← must guard; negative "at most" = 0 subarrays
    ...
```

---

### Mistake 5: Zero-count keys polluting `len(freq)`

```python
# WRONG: freq = {a:0, b:1} → len(freq) = 2 (misleading!)
freq[s[left]] -= 1
left += 1

# CORRECT: always clean up
freq[s[left]] -= 1
if freq[s[left]] == 0:
    del freq[s[left]]     # remove key so len(freq) stays accurate
left += 1
```

---

### Mistake 6: Applying sliding window when elements can be negative

```python
# nums = [1, -1, 1], target = 1
# If you shrink whenever sum > target, you might skip valid subarrays
# because removing a negative element INCREASES the sum → window not monotone

# CORRECT: use prefix sum + hashmap for arbitrary elements
prefix = {0: 1}
curr = 0
result = 0
for num in nums:
    curr += num
    result += prefix.get(curr - target, 0)
    prefix[curr] = prefix.get(curr, 0) + 1
```

---

## Complete Practice Problem List

### Tier 1 — Core variants, must solve first

| # | Problem | Difficulty | Variant | What makes it this variant |
|---|---------|-----------|---------|---------------------------|
| 1358 | Substrings Containing All Three Characters | Medium | A | "All three" = at least one of each |
| 713 | Subarray Product Less Than K | Medium | B | "Less than K" = at-most condition |
| 930 | Binary Subarrays With Sum | Medium | C | "Exactly goal" with binary array |
| 1876 | Substrings of Size Three with Distinct Characters | Easy | D | Fixed window size = 3 |
| 560 | Subarray Sum Equals K | Medium | Prefix sum | Negatives possible, exact sum |

### Tier 2 — Solidify with different state types

| # | Problem | Difficulty | Variant | What tracks state |
|---|---------|-----------|---------|------------------|
| 2962 | Count Subarrays Where Max Element Appears ≥ K Times | Medium | A | count of global_max appearances |
| 2537 | Count the Number of Good Subarrays | Medium | A | pair count from frequency |
| 1248 | Count Number of Nice Subarrays | Medium | C | odd count (treat odds as 1s) |
| 992 | Subarrays with K Different Integers | Hard | C | frequency map, distinct count |
| 2302 | Count Subarrays With Score Less Than K | Medium | B | sum × length as score |
| 2799 | Count Complete Subarrays in an Array | Medium | B/C | distinct in window vs total |
| 1343 | Number of Sub-arrays of Size K and Average ≥ Threshold | Medium | D | fixed window average |

### Tier 3 — Advanced state and dual pointers

| # | Problem | Difficulty | Variant | Challenge |
|---|---------|-----------|---------|-----------|
| 2444 | Count Subarrays with Fixed Bounds | Hard | E | Three pointers: bad, lo, hi |
| 2461 | Maximum Sum of Distinct Subarrays With Length K | Medium | D | Fixed window + distinct check |
| 2841 | Maximum Sum of Almost Unique Subarrays | Medium | D | Fixed window, ≥m distinct |
| 2653 | Sliding Subarray Beauty | Medium | D | Fixed window with frequency |
| 1438 | Longest Continuous Subarray With Absolute Diff ≤ Limit | Medium | Deque+B | Monotone deque for min/max |
| 2090 | K Radius Subarray Averages | Medium | D | Fixed window, handle edge |
| 828 | Count Unique Characters of All Substrings | Hard | Contribution | Per-character contribution |

### Tier 4 — Contest-level and generalizations

| # | Problem | Difficulty | Variant | What to learn |
|---|---------|-----------|---------|--------------|
| 2958 | Length of Longest Subarray With at Most K Frequency | Medium | B (length) | Frequency cap, not distinct count |
| 2875 | Minimum Size Subarray in Infinite Array | Medium | A+math | Circular array variant |
| 2904 | Shortest and Lexicographically Smallest Beautiful String | Medium | D+B | Multi-condition window |
| 3325 | Count Substrings With K-Frequency Characters | Medium | A | At least K of any character |
| 2024 | Maximize the Confusion of an Exam | Medium | B (length) | At most K replacements |
| 1004 | Max Consecutive Ones III | Medium | B (length) | At most K zeros → flip |
| 2271 | Maximum White Tiles Covered by a Carpet | Medium | Binary search+prefix | Carpet placement |

---

## Cheat Sheet

```python
# ── Variant A: "at least" / "contains all" ─────────────────────────────────
left = 0; result = 0
for right in range(n):
    add(arr[right])
    while window_is_VALID():        # shrink while valid
        remove(arr[left]); left += 1
    result += left                  # 0..left-1 are valid starts

# ── Variant B: "at most K" ─────────────────────────────────────────────────
left = 0; result = 0
for right in range(n):
    add(arr[right])
    while window_is_INVALID():      # shrink while invalid
        remove(arr[left]); left += 1
    result += right - left + 1     # left..right are all valid starts

# ── Variant C: "exactly K" ─────────────────────────────────────────────────
result = at_most(k) - at_most(k - 1)   # call Variant B twice

# ── Variant D: fixed window size K ─────────────────────────────────────────
for i in range(k): add(arr[i])
if valid(): result += 1
for right in range(k, n):
    add(arr[right]); remove(arr[right - k])
    if valid(): result += 1

# ── Variant E: dual bounds (min=X and max=Y) ───────────────────────────────
bad = lo = hi = -1
for right, val in enumerate(arr):
    if not in_range(val): bad = right
    if val == minK: lo = right
    if val == maxK: hi = right
    result += max(0, min(lo, hi) - bad)

# ── Prefix sum: exact sum with negative elements ────────────────────────────
seen = {0: 1}; prefix = 0
for num in nums:
    prefix += num
    result += seen.get(prefix - target, 0)
    seen[prefix] = seen.get(prefix, 0) + 1
```

**The single most important rule:**
- Variant A: `while valid` → `+= left`
- Variant B: `while invalid` → `+= right-left+1`

Everything else is just recognizing which variant applies.
