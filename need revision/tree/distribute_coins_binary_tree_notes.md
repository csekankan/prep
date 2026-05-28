# LeetCode 979 — Distribute Coins in Binary Tree

## Core Intuition

The hardest part of this problem is not coding.

It is understanding:

> What information should a subtree return to its parent?

The answer is:

```text
net coin balance
```

Positive:
- subtree has extra coins

Negative:
- subtree needs coins

---

# Step 1 — Understand the Brute Force First

Suppose:

```text
      0
     / \
    3   0
```

Goal:

```text
      1
     / \
    1   1
```

---

## What does brute force do?

Your brute force literally simulates moving coins.

### First move

Node `3` has extra coins.

Nearest node needing coin:

```text
root (0)
```

Distance:

```text
3 -> root = 1 edge
```

So:

```python
moves += 1
```

Tree becomes:

```text
      1
     / \
    2   0
```

---

### Second move

Now left node still has extra:

```text
2
```

Nearest node needing coin:

```text
right node
```

Path:

```text
left -> root -> right
```

Distance:

```text
2
```

So:

```python
moves += 2
```

Tree becomes:

```text
      1
     / \
    1   1
```

Total:

```text
3 moves
```

---

# Understanding This Line

```python
moves += self.bfs_distance(node, target, parent_map)
```

This means:

```text
How many edges must the coin travel?
```

Because:

```text
1 edge crossed = 1 move
```

---

# Understanding This

```python
node.val -= 1
target.val += 1
```

This simulates moving ONE coin.

Source loses coin.
Destination gains coin.

Intermediate nodes are ignored because they only act as paths.

---

# The Real Problem With Brute Force

Brute force repeatedly:

- finds donor
- finds receiver
- computes path
- moves one coin

again and again.

Very repetitive.

---

# The Big DFS Insight

Instead of tracking individual coins:

Ask:

```text
How many coins must cross this edge overall?
```

That is MUCH simpler.

---

# Step 2 — Think in Terms of Subtrees

Suppose subtree has:

```text
5 coins
3 nodes
```

Every node needs one coin.

So subtree keeps:

```text
3 coins
```

Extra:

```text
5 - 3 = 2
```

Meaning:

```text
2 coins must leave subtree
```

Similarly:

```text
2 coins
5 nodes
```

Means:

```text
2 - 5 = -3
```

Meaning:

```text
subtree needs 3 coins
```

---

# THIS Is What DFS Returns

DFS returns:

```text
(coins in subtree) - (nodes in subtree)
```

Equivalent compact formula:

```python
left + right + node.val - 1
```

Why?

Because:

```text
left balance
+ right balance
+ current node coins
- one coin current node keeps
```

---

# Postorder DFS

We must solve children first.

Because current node needs to know:

```text
Does left subtree need coins?
Does right subtree have extra coins?
```

So traversal is:

```text
left
right
node
```

Classic postorder DFS.

---

# MOST IMPORTANT VISUALIZATION

Example:

```text
      0
     / \
    3   0
```

Left subtree returns:

```text
+2
```

because:

```text
3 coins - 1 node = 2 extra
```

Right subtree returns:

```text
-1
```

because:

```text
0 coins - 1 node = needs 1
```

Root receives:

```python
left = 2
right = -1
```

Meaning:

- 2 coins cross left edge
- 1 coin crosses right edge

So:

```python
moves += abs(left) + abs(right)
```

becomes:

```python
2 + 1 = 3
```

Exactly correct.

---

# Why Does abs() Work?

Because:

```text
positive -> coins move upward
negative -> coins move downward
```

Either way:

```text
absolute value = number of coins crossing edge
```

And:

```text
1 coin crossing edge = 1 move
```

---

# Final Elegant DFS

```python
class Solution:
    def distributeCoins(self, root):
        self.moves = 0

        def dfs(node):
            if not node:
                return 0

            left = dfs(node.left)
            right = dfs(node.right)

            self.moves += abs(left) + abs(right)

            return node.val + left + right - 1

        dfs(root)
        return self.moves
```

---

# One Sentence Summary

The entire problem becomes easy once you realize:

> Every subtree only needs to tell its parent:
>
> "How many extra coins do I have?"
>
> or
>
> "How many coins do I need?"
>
> That single number solves everything.

---

# Reference Notes

The following ideas were also used as reference while building this intuition:

- Think from the edge perspective instead of node perspective.
- Every edge acts like a highway for coin flow.
- Excess coins in subtree must cross the parent edge.
- Deficit coins must come through the parent edge.
- Postorder DFS naturally aggregates subtree information bottom-up.
