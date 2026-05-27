# Sum of Subarray Minimums — Real Intuition

## Core Shift in Thinking

Most beginners think:

> Generate all subarrays and compute minimum.

But the efficient solution thinks differently:

> For each element, count how many subarrays use it as the minimum.

That is the entire trick.

---

# Example

```python
arr = [3,1,2]
```

All subarrays:

```python
[3]
[3,1]
[3,1,2]
[1]
[1,2]
[2]
```

Minimums:

```python
3
1
1
1
1
2
```

Total:

```python
9
```

---

# Contribution View

Instead of generating subarrays:

## Element 3

Minimum only in:

```python
[3]
```

Contribution:

```python
3 * 1
```

---

## Element 1

Minimum in:

```python
[1]
[3,1]
[1,2]
[3,1,2]
```

Contribution:

```python
1 * 4
```

---

## Element 2

Minimum in:

```python
[2]
```

Contribution:

```python
2 * 1
```

---

Total:

```python
3 + 4 + 2 = 9
```

---

# The Master Formula

For every element:

```text
contribution = value × leftChoices × rightChoices
```

Where:

- leftChoices = how many starting positions possible
- rightChoices = how many ending positions possible

---

# Example for Element 1

```python
arr = [3,1,2]
```

## Expand Left

```python
3 > 1
```

Can include 3.

Possible left starts:

```python
[1]
[3,1]
```

So:

```python
leftChoices = 2
```

---

## Expand Right

```python
2 > 1
```

Can include 2.

Possible right endings:

```python
[1]
[1,2]
```

So:

```python
rightChoices = 2
```

---

Total subarrays where 1 is minimum:

```python
2 * 2 = 4
```

Exactly correct.

---

# Why Monotonic Stack Is Used

The stack is NOT the main idea.

The real idea is:

```text
Find how far an element can dominate.
```

The stack is only an efficient tool to find:

- previous smaller element
- next smaller element

in O(n).

---

# Common Pattern of Similar Problems

These are NOT just “monotonic stack problems”.

These are:

# Contribution / Dominance / Span Problems

You should train your brain to recognize:

```text
How much influence does each element have?
```

---

# Similar Problems of Same Kind

These problems use the SAME contribution/span thinking.

---

# 1. Sum of Subarray Ranges

LeetCode 2104

Idea:

```text
Answer = contribution as maximum - contribution as minimum
```

You calculate:

- how many subarrays an element is maximum in
- how many subarrays an element is minimum in

Very important problem.

---

# 2. Largest Rectangle in Histogram

LeetCode 84

Idea:

For every height:

```text
How far can this height expand?
```

Formula:

```text
height × width
```

Same span thinking.

---

# 3. Maximum Subarray Min Product

LeetCode 1856

Idea:

For every element:

```text
Treat it as minimum.
Find largest valid span.
```

Then:

```text
minimum × subarraySum
```

Very similar thinking.

---

# 4. Total Strength of Wizards

LeetCode 2281

Hard problem.

Direct extension of:

```text
Sum of Subarray Minimums
```

One of the best advanced problems for this pattern.

---

# 5. Count Subarrays Where Element Is Maximum

Pattern:

```text
How many subarrays does this element dominate?
```

Very similar contribution thinking.

---

# 6. Subarray Minimum Queries

Many segment-tree or stack problems reduce to:

```text
Which element controls this interval?
```

Same dominance idea.

---

# 7. Trapping Rain Water

Different formula.

But same thought process:

```text
How much area does each boundary influence?
```

---

# Recognition Trick

When problem asks:

- total over all subarrays
- min/max over all subarrays
- influence/span/range
- nearest smaller/greater
- how far an element expands
- contribution of each element

You should think:

```text
Can I solve by counting contribution per element?
```

---

# The Biggest Mental Upgrade

Brute force thinks:

```text
Generate subarrays.
```

Advanced thinking asks:

```text
What role does each element play globally?
```

That shift is what separates intermediate from advanced DSA thinking.

---

# Clean O(n) Solution

```python
class Solution:
    def sumSubarrayMins(self, arr):
        MOD = 10**9 + 7

        stack = []
        curSum = 0
        ans = 0

        for val in arr:
            count = 1

            while stack and stack[-1][0] >= val:
                v, c = stack.pop()

                curSum -= v * c
                count += c

            stack.append((val, count))

            curSum += val * count

            ans += curSum

        return ans % MOD
```

---

# Important Intuition for curSum

```python
curSum
```

stores:

```text
sum of minimums of ALL subarrays ending at current index
```

When a smaller value comes:

- old larger minimums become invalid
- remove them
- new smaller value takes over their ranges

That is why:

```python
curSum -= v * c
```

is necessary.

