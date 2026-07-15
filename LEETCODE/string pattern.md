# String Problem Patterns — The Complete Map

> Every major string algorithm and pattern for interviews, with trigger words,
> templates, complexity, and practice problems.

---

## Quick Lookup Table

| You see in the problem... | Pattern | Jump to |
|---|---|---|
| "Find substring/anagram in a window" | [Sliding Window on Strings](#1-sliding-window-on-strings) | §1 |
| "Two pointers" + palindrome / reverse / partition | [Two Pointers on Strings](#2-two-pointers-on-strings) | §2 |
| "Pattern matching" / "find needle in haystack" | [KMP / Prefix Function](#3-kmp--prefix-function) | §3 |
| "Common prefix/suffix" / "period of string" | [Z-Algorithm](#4-z-algorithm) | §4 |
| "Substring hash" / "rolling hash" / "Rabin-Karp" | [String Hashing (Rabin-Karp)](#5-string-hashing-rabin-karp) | §5 |
| "Prefix lookup" / "autocomplete" / "word dictionary" | [Trie (Prefix Tree)](#6-trie-prefix-tree) | §6 |
| "Longest palindromic substring" (in O(n)) | [Manacher's Algorithm](#7-manachers-algorithm) | §7 |
| "Two strings" + transform/match/common | [Two-String DP](#8-two-string-dp) | §8 |
| "Palindrome" + count/partition | [Palindrome DP](#9-palindrome-dp) | §9 |
| "Count distinct subsequences" / "subsequence matching" | [Subsequence DP on Strings](#10-subsequence-dp-on-strings) | §10 |
| "Count valid strings" + forbidden pattern | [Automaton DP (KMP + DP)](#11-automaton-dp-kmp--dp) | §11 |
| "Decode ways" / "word break" / "partition string" | [String Partition DP](#12-string-partition-dp) | §12 |
| "Lexicographically smallest/largest" | [Greedy + Stack on Strings](#13-greedy--stack-on-strings) | §13 |
| "Parentheses" / "brackets" / "valid nesting" | [Stack-Based String Problems](#14-stack-based-string-problems) | §14 |

---

## §1: Sliding Window on Strings

### Trigger Words
- "Substring containing all characters of T"
- "Anagram" / "permutation in string"
- "Longest substring without repeating characters"
- "Window of size k" on a string
- "At most k distinct characters"

### Mental Model
Maintain a window `[left, right)`. Expand right to include more characters,
shrink left when the window violates a constraint. Track character frequencies
with a hashmap or array of size 26/128.

### Template (Variable-Size Window)
```python
from collections import Counter

def sliding_window(s, t):
    need = Counter(t)
    have = {}
    formed = 0
    required = len(need)
    left = 0
    result = float('inf'), 0, 0

    for right in range(len(s)):
        ch = s[right]
        have[ch] = have.get(ch, 0) + 1

        if ch in need and have[ch] == need[ch]:
            formed += 1

        while formed == required:
            # valid window — try to shrink
            window_len = right - left + 1
            if window_len < result[0]:
                result = window_len, left, right

            out = s[left]
            have[out] -= 1
            if out in need and have[out] < need[out]:
                formed -= 1
            left += 1

    return result
```

### Template (Fixed-Size Window for Anagrams)
```python
def find_anagrams(s, p):
    if len(p) > len(s): return []
    p_count = Counter(p)
    s_count = Counter(s[:len(p)])
    result = []

    if s_count == p_count:
        result.append(0)

    for i in range(len(p), len(s)):
        s_count[s[i]] += 1
        left_char = s[i - len(p)]
        s_count[left_char] -= 1
        if s_count[left_char] == 0:
            del s_count[left_char]
        if s_count == p_count:
            result.append(i - len(p) + 1)

    return result
```

### Key Problems

| Problem | Window type |
|---|---|
| [Minimum Window Substring](https://leetcode.com/problems/minimum-window-substring/) (LC 76) | Shrinkable, must contain all of T |
| [Longest Substring Without Repeating Characters](https://leetcode.com/problems/longest-substring-without-repeating-characters/) (LC 3) | Max window, no repeats |
| [Find All Anagrams in a String](https://leetcode.com/problems/find-all-anagrams-in-a-string/) (LC 438) | Fixed-size window |
| [Permutation in String](https://leetcode.com/problems/permutation-in-string/) (LC 567) | Fixed-size window |
| [Longest Substring with At Most K Distinct](https://leetcode.com/problems/longest-substring-with-at-most-k-distinct-characters/) (LC 340) | Shrinkable, k distinct |
| [Longest Repeating Character Replacement](https://leetcode.com/problems/longest-repeating-character-replacement/) (LC 424) | Max window, at most k replacements |
| [Substring with Concatenation of All Words](https://leetcode.com/problems/substring-with-concatenation-of-all-words/) (LC 30) | Multi-word window |

---

## §2: Two Pointers on Strings

### Trigger Words
- "Palindrome" check
- "Reverse" / "compare from both ends"
- "Valid palindrome with at most k removals"
- "Two strings, merge/interleave"
- "Compress / expand"

### Techniques

**Palindrome check (inward pointers):**
```python
def is_palindrome(s):
    left, right = 0, len(s) - 1
    while left < right:
        if s[left] != s[right]:
            return False
        left += 1
        right -= 1
    return True
```

**Expand around center (outward pointers):**
```python
def expand(s, left, right):
    while left >= 0 and right < len(s) and s[left] == s[right]:
        left -= 1
        right += 1
    return s[left + 1 : right]
```

**Merge two sorted strings / compare versions:**
```python
def compare(s1, s2):
    i, j = 0, 0
    while i < len(s1) and j < len(s2):
        if s1[i] != s2[j]:
            return s1[i] < s2[j]
        i += 1
        j += 1
    return len(s1) < len(s2)
```

### Key Problems

| Problem | Pointer type |
|---|---|
| [Valid Palindrome](https://leetcode.com/problems/valid-palindrome/) (LC 125) | Inward |
| [Valid Palindrome II](https://leetcode.com/problems/valid-palindrome-ii/) (LC 680) | Inward + skip one |
| [Longest Palindromic Substring](https://leetcode.com/problems/longest-palindromic-substring/) (LC 5) | Expand around center |
| [String Compression](https://leetcode.com/problems/string-compression/) (LC 443) | Read/write pointers |
| [Backspace String Compare](https://leetcode.com/problems/backspace-string-compare/) (LC 844) | Reverse traverse |
| [Is Subsequence](https://leetcode.com/problems/is-subsequence/) (LC 392) | Two-string scan |

---

## §3: KMP / Prefix Function

### When to Use
- Find pattern P in text T in O(n + m)
- Find the shortest repeating unit of a string
- Find all occurrences of a pattern (not just first)
- Building block for Automaton DP (§11)

### The Prefix Function (Failure Function)

`pi[i]` = length of the longest **proper** prefix of `P[0..i]` that is also a suffix.

```python
def compute_prefix(pattern):
    m = len(pattern)
    pi = [0] * m
    k = 0
    for i in range(1, m):
        while k > 0 and pattern[k] != pattern[i]:
            k = pi[k - 1]
        if pattern[k] == pattern[i]:
            k += 1
        pi[i] = k
    return pi
```

### KMP Search

```python
def kmp_search(text, pattern):
    n, m = len(text), len(pattern)
    pi = compute_prefix(pattern)
    matches = []
    k = 0

    for i in range(n):
        while k > 0 and pattern[k] != text[i]:
            k = pi[k - 1]
        if pattern[k] == text[i]:
            k += 1
        if k == m:
            matches.append(i - m + 1)
            k = pi[k - 1]

    return matches
```

### Useful Properties

| Property | Formula | Use case |
|---|---|---|
| Shortest repeating period | `period = m - pi[m-1]` | String is periodic iff `m % period == 0` |
| All border lengths | Follow `pi[m-1] → pi[pi[m-1]-1] → ...` chain | All prefixes that are also suffixes |

### Key Problems

| Problem | What KMP gives you |
|---|---|
| [Find the Index of the First Occurrence](https://leetcode.com/problems/find-the-index-of-the-first-occurrence-in-a-string/) (LC 28) | Basic pattern matching |
| [Repeated Substring Pattern](https://leetcode.com/problems/repeated-substring-pattern/) (LC 459) | `m % (m - pi[m-1]) == 0` |
| [Shortest Palindrome](https://leetcode.com/problems/shortest-palindrome/) (LC 214) | KMP on `s + "#" + reverse(s)` |
| [Remove All Occurrences of a Substring](https://leetcode.com/problems/remove-all-occurrences-of-a-substring/) (LC 1910) | Repeated KMP / stack |

---

## §4: Z-Algorithm

### When to Use
- Same problems as KMP but sometimes easier to reason about
- "Longest common prefix of suffix `s[i..]` with `s[0..]`"
- Period detection, string matching

### The Z-Array

`z[i]` = length of the longest substring starting at `i` that matches a prefix of `s`.

```python
def z_function(s):
    n = len(s)
    z = [0] * n
    z[0] = n
    left, right = 0, 0

    for i in range(1, n):
        if i < right:
            z[i] = min(right - i, z[i - left])
        while i + z[i] < n and s[z[i]] == s[i + z[i]]:
            z[i] += 1
        if i + z[i] > right:
            left, right = i, i + z[i]

    return z
```

### Pattern Matching via Z-Array
Concatenate: `combined = pattern + "$" + text`
Wherever `z[i] == len(pattern)`, pattern occurs at `i - len(pattern) - 1` in text.

### KMP vs Z-Algorithm

| | KMP | Z-Algorithm |
|---|---|---|
| What it computes | Longest prefix-suffix for each prefix | Longest prefix match starting at each position |
| Easier for | Automaton DP, failure links | Direct string comparison, multi-pattern via concatenation |
| Complexity | O(n + m) | O(n + m) |

### Key Problems

| Problem | How Z helps |
|---|---|
| [Find the Index of the First Occurrence](https://leetcode.com/problems/find-the-index-of-the-first-occurrence-in-a-string/) (LC 28) | Z on `P$T` |
| [Longest Happy Prefix](https://leetcode.com/problems/longest-happy-prefix/) (LC 1392) | Z or KMP prefix function |
| [Sum of Scores of Built Strings](https://leetcode.com/problems/sum-of-scores-of-built-strings/) (LC 2223) | Sum of z-values |

---

## §5: String Hashing (Rabin-Karp)

### When to Use
- Substring comparison in O(1) after O(n) preprocessing
- "Longest duplicate substring"
- "Count distinct substrings"
- Pattern matching with wildcards or multiple patterns
- Any problem where you need to compare many substrings quickly

### Rolling Hash Template

```python
class StringHash:
    def __init__(self, s, base=131, mod=10**18 + 9):
        n = len(s)
        self.mod = mod
        self.base = base
        self.h = [0] * (n + 1)
        self.pw = [1] * (n + 1)

        for i in range(n):
            self.h[i + 1] = (self.h[i] * base + ord(s[i])) % mod
            self.pw[i + 1] = (self.pw[i] * base) % mod

    def get_hash(self, left, right):
        """Hash of s[left:right+1] (inclusive both ends)."""
        return (self.h[right + 1] - self.h[left] * self.pw[right - left + 1]) % self.mod
```

### Double Hashing (Avoid Collisions)
```python
h1 = StringHash(s, base=131, mod=10**18 + 9)
h2 = StringHash(s, base=137, mod=10**18 + 7)

def get_hash(left, right):
    return (h1.get_hash(left, right), h2.get_hash(left, right))
```

### Key Problems

| Problem | Why hashing |
|---|---|
| [Longest Duplicate Substring](https://leetcode.com/problems/longest-duplicate-substring/) (LC 1044) | Binary search + rolling hash |
| [Distinct Echo Substrings](https://leetcode.com/problems/distinct-echo-substrings/) (LC 1316) | Hash to count distinct |
| [Longest Common Subpath](https://leetcode.com/problems/longest-common-subpath/) (LC 1923) | Binary search + hash sets |
| [Rabin-Karp Pattern Matching](https://leetcode.com/problems/find-the-index-of-the-first-occurrence-in-a-string/) (LC 28) | Alternative to KMP |
| [Repeated DNA Sequences](https://leetcode.com/problems/repeated-dna-sequences/) (LC 187) | Fixed-length rolling hash |

---

## §6: Trie (Prefix Tree)

### When to Use
- "Prefix search" / "autocomplete"
- "Word dictionary with wildcard search"
- "Longest common prefix" among many strings
- "XOR maximum" (binary trie)
- "Count words with given prefix"

### Template

```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.count = 0

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
            node.count += 1
        node.is_end = True

    def search(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return node.is_end

    def starts_with(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return True

    def count_prefix(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return 0
            node = node.children[ch]
        return node.count
```

### Trie + DFS (Wildcard Search)
```python
def search_with_dots(self, word):
    def dfs(node, i):
        if i == len(word):
            return node.is_end
        if word[i] == '.':
            return any(dfs(child, i + 1) for child in node.children.values())
        if word[i] not in node.children:
            return False
        return dfs(node.children[word[i]], i + 1)
    return dfs(self.root, 0)
```

### Key Problems

| Problem | Trie variant |
|---|---|
| [Implement Trie](https://leetcode.com/problems/implement-trie-prefix-tree/) (LC 208) | Basic trie |
| [Design Add and Search Words](https://leetcode.com/problems/design-add-and-search-words-data-structure/) (LC 211) | Trie + DFS for '.' |
| [Word Search II](https://leetcode.com/problems/word-search-ii/) (LC 212) | Trie + grid backtracking |
| [Longest Word in Dictionary](https://leetcode.com/problems/longest-word-in-dictionary/) (LC 720) | Trie + BFS/DFS |
| [Maximum XOR of Two Numbers](https://leetcode.com/problems/maximum-xor-of-two-numbers-in-an-array/) (LC 421) | Binary trie |
| [Palindrome Pairs](https://leetcode.com/problems/palindrome-pairs/) (LC 336) | Trie + palindrome check |
| [Word Break II](https://leetcode.com/problems/word-break-ii/) (LC 140) | Trie + backtrack |

---

## §7: Manacher's Algorithm

### When to Use
- "Longest palindromic substring" in O(n)
- "Count palindromic substrings" in O(n)
- Need ALL palindrome radii, not just the longest

### Mental Model

Expand around centers like the naive approach, but reuse previously computed
palindromes by tracking a rightmost boundary. If current center is inside a
known palindrome, mirror a previously computed radius to skip redundant comparisons.

### Template

```python
def manacher(s):
    # Transform "abc" → "^#a#b#c#$" to handle even-length palindromes uniformly
    t = '^#' + '#'.join(s) + '#$'
    n = len(t)
    p = [0] * n
    center = right = 0

    for i in range(1, n - 1):
        mirror = 2 * center - i
        if i < right:
            p[i] = min(right - i, p[mirror])

        while t[i + p[i] + 1] == t[i - p[i] - 1]:
            p[i] += 1

        if i + p[i] > right:
            center, right = i, i + p[i]

    return p

def longest_palindrome(s):
    p = manacher(s)
    max_len = max(p)
    center_idx = p.index(max_len)
    start = (center_idx - max_len) // 2
    return s[start : start + max_len]
```

### When to Use Manacher vs DP vs Expand

| Approach | Time | When |
|---|---|---|
| Expand around center | O(n²) | Simple, short strings, interview default |
| DP `is_pal[i][j]` | O(n²) | Need palindrome info for ALL substrings (then use in another DP) |
| Manacher's | O(n) | Need O(n) or very long strings |

### Key Problems

| Problem | Why Manacher |
|---|---|
| [Longest Palindromic Substring](https://leetcode.com/problems/longest-palindromic-substring/) (LC 5) | O(n) solution (expand is fine too) |
| [Palindromic Substrings](https://leetcode.com/problems/palindromic-substrings/) (LC 647) | Count all palindromic substrings |
| [Shortest Palindrome](https://leetcode.com/problems/shortest-palindrome/) (LC 214) | Longest palindromic prefix |
| [Maximum Product of the Length of Two Palindromic Substrings](https://leetcode.com/problems/maximum-product-of-the-length-of-two-palindromic-substrings/) (LC 1960) | Must be O(n) — expand too slow |

---

## §8: Two-String DP

*(Cross-reference: DP Pattern §3)*

### Trigger Words
- "Two strings" + "transform" / "match" / "common"
- "Minimum operations to convert A to B"
- "Longest common subsequence / substring"
- "Interleaving" / "regex matching"

### State
`dp[i][j]` = answer considering first `i` chars of s1 and first `j` chars of s2.

### The Three Core Problems

**LCS (Longest Common Subsequence):**
```python
if s1[i-1] == s2[j-1]:
    dp[i][j] = dp[i-1][j-1] + 1
else:
    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
```

**Edit Distance:**
```python
if s1[i-1] == s2[j-1]:
    dp[i][j] = dp[i-1][j-1]
else:
    dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
```

**Longest Common Substring (contiguous):**
```python
if s1[i-1] == s2[j-1]:
    dp[i][j] = dp[i-1][j-1] + 1
    answer = max(answer, dp[i][j])
else:
    dp[i][j] = 0  # reset — must be contiguous
```

### Key Problems

| Problem | Variant |
|---|---|
| [Longest Common Subsequence](https://leetcode.com/problems/longest-common-subsequence/) (LC 1143) | Classic LCS |
| [Edit Distance](https://leetcode.com/problems/edit-distance/) (LC 72) | Insert/delete/replace |
| [Interleaving String](https://leetcode.com/problems/interleaving-string/) (LC 97) | Can s3 interleave s1+s2? |
| [Regular Expression Matching](https://leetcode.com/problems/regular-expression-matching/) (LC 10) | `.` and `*` |
| [Wildcard Matching](https://leetcode.com/problems/wildcard-matching/) (LC 44) | `?` and `*` |
| [Shortest Common Supersequence](https://leetcode.com/problems/shortest-common-supersequence/) (LC 1092) | LCS + reconstruct |
| [Delete Operation for Two Strings](https://leetcode.com/problems/delete-operation-for-two-strings/) (LC 583) | Min deletions = related to LCS |
| [Minimum ASCII Delete Sum](https://leetcode.com/problems/minimum-ascii-delete-sum-for-two-strings/) (LC 712) | Weighted LCS variant |

---

## §9: Palindrome DP

*(Cross-reference: DP Pattern §11)*

### Trigger Words
- "Palindrome" + "partition" / "count" / "subsequence"
- "Minimum cuts for palindrome partition"
- "Longest palindromic subsequence"

### Two Layers

**Layer 1: Precompute palindrome info**
```python
# is s[i..j] a palindrome?
for length in range(2, n + 1):
    for i in range(n - length + 1):
        j = i + length - 1
        is_pal[i][j] = (s[i] == s[j]) and (length <= 3 or is_pal[i+1][j-1])
```

**Layer 2: Use it in outer DP**

### Longest Palindromic Subsequence (Interval DP)
```python
# dp[i][j] = LPS in s[i..j]
for i in range(n - 1, -1, -1):
    dp[i][i] = 1
    for j in range(i + 1, n):
        if s[i] == s[j]:
            dp[i][j] = dp[i+1][j-1] + 2
        else:
            dp[i][j] = max(dp[i+1][j], dp[i][j-1])
```

### Key Problems

| Problem | Structure |
|---|---|
| [Longest Palindromic Subsequence](https://leetcode.com/problems/longest-palindromic-subsequence/) (LC 516) | Interval DP |
| [Palindrome Partitioning II](https://leetcode.com/problems/palindrome-partitioning-ii/) (LC 132) | Min cuts = precompute + 1D DP |
| [Palindrome Partitioning](https://leetcode.com/problems/palindrome-partitioning/) (LC 131) | Backtracking + palindrome check |
| [Count Different Palindromic Subsequences](https://leetcode.com/problems/count-different-palindromic-subsequences/) (LC 730) | Hard counting |
| [Palindrome Partitioning III](https://leetcode.com/problems/palindrome-partitioning-iii/) (LC 1278) | Partition DP + palindrome cost |
| [Minimum Insertion Steps to Make Palindrome](https://leetcode.com/problems/minimum-insertion-steps-to-make-a-string-palindrome/) (LC 1312) | n - LPS |

---

## §10: Subsequence DP on Strings

### Trigger Words
- "Count distinct subsequences"
- "Is s a subsequence of t?"
- "Number of subsequences matching a pattern"
- "Distinct subsequences" of a string

### Two Variants

**Variant A: Count subsequences of s that equal t**
```python
# dp[i][j] = ways to match t[0..j-1] using s[0..i-1]
for i in range(1, m + 1):
    for j in range(1, n + 1):
        dp[i][j] = dp[i-1][j]               # skip s[i-1]
        if s[i-1] == t[j-1]:
            dp[i][j] += dp[i-1][j-1]        # use s[i-1] to match t[j-1]
```

**Variant B: Count distinct subsequences of s**
```python
# Track last occurrence of each character
dp = [0] * (n + 1)
dp[0] = 1  # empty subsequence
last = {}

for i in range(1, n + 1):
    dp[i] = 2 * dp[i - 1]
    if s[i - 1] in last:
        dp[i] -= dp[last[s[i - 1]] - 1]
    last[s[i - 1]] = i
```

### Key Problems

| Problem | Variant |
|---|---|
| [Distinct Subsequences](https://leetcode.com/problems/distinct-subsequences/) (LC 115) | Count subseq of s matching t |
| [Distinct Subsequences II](https://leetcode.com/problems/distinct-subsequences-ii/) (LC 940) | Count distinct subseq of s |
| [Is Subsequence](https://leetcode.com/problems/is-subsequence/) (LC 392) | Two-pointer check |
| [Number of Matching Subsequences](https://leetcode.com/problems/number-of-matching-subsequences/) (LC 792) | Multi-pointer / bucket |
| [Count Different Palindromic Subsequences](https://leetcode.com/problems/count-different-palindromic-subsequences/) (LC 730) | Palindromic variant |

---

## §11: Automaton DP (KMP + DP)

### Trigger Words
- "Count strings of length n that DON'T contain pattern P"
- "Count binary strings avoiding substring X"
- "Number of valid strings" + forbidden pattern
- "Expected occurrences of pattern in random string"

### Mental Model

Build the KMP failure function for the forbidden pattern.
Then run DP where state = `(position in result string, state in KMP automaton)`.
At each position, try each character and use the KMP automaton to compute the
next state. If you reach the accept state (full match), that string is forbidden.

### Template
```python
def count_valid_strings(n, pattern, alphabet='ab'):
    m = len(pattern)
    pi = compute_prefix(pattern)

    # Build automaton: next_state[state][char] = new KMP state
    next_state = [[0] * len(alphabet) for _ in range(m)]
    for state in range(m):
        for ci, ch in enumerate(alphabet):
            k = state
            while k > 0 and pattern[k] != ch:
                k = pi[k - 1]
            if pattern[k] == ch:
                k += 1
            next_state[state][ci] = k

    # DP: dp[state] = count of strings that reach this KMP state
    dp = [0] * m
    dp[0] = 1

    for _ in range(n):
        dp_new = [0] * m
        for state in range(m):
            if dp[state] == 0:
                continue
            for ci in range(len(alphabet)):
                ns = next_state[state][ci]
                if ns < m:  # not a full match (forbidden)
                    dp_new[ns] = (dp_new[ns] + dp[state]) % MOD
        dp = dp_new

    return sum(dp) % MOD
```

### Key Insight
This needs a **new DP array** per step (§17 fan-out rule): each state fans out to
`|alphabet|` destinations.

### Key Problems

| Problem | Automaton type |
|---|---|
| [Find All Good Strings](https://leetcode.com/problems/find-all-good-strings/) (LC 1397) | Digit DP + KMP automaton |
| [Count Strings That Do Not Contain Binary Substring](https://codeforces.com/problemset/problem/1400/E) | KMP + DP |
| [Freedom Trail](https://leetcode.com/problems/freedom-trail/) (LC 514) | Ring automaton |
| [Stamping The Sequence](https://leetcode.com/problems/stamping-the-sequence/) (LC 936) | Reverse automaton |

---

## §12: String Partition DP

### Trigger Words
- "Word break" / "can the string be segmented into dictionary words?"
- "Decode ways" / "count decodings"
- "Minimum cuts to partition string with property X"
- "Split string into k valid parts"

### Mental Model

`dp[i]` = answer for the prefix `s[0..i-1]`.
For each position `i`, look back at all valid "last segments" `s[j..i-1]` and
combine with `dp[j]`.

### Template
```python
# Word Break
dp = [False] * (n + 1)
dp[0] = True
word_set = set(wordDict)

for i in range(1, n + 1):
    for j in range(i):
        if dp[j] and s[j:i] in word_set:
            dp[i] = True
            break
```

### Optimization with Trie
Instead of checking all `j` values, walk backwards through a Trie:
```python
# Insert reversed words into trie
# At each position i, walk backwards through trie to find valid segments
```

### Key Problems

| Problem | Partition type |
|---|---|
| [Word Break](https://leetcode.com/problems/word-break/) (LC 139) | Can it be segmented? |
| [Word Break II](https://leetcode.com/problems/word-break-ii/) (LC 140) | All segmentations (backtrack) |
| [Decode Ways](https://leetcode.com/problems/decode-ways/) (LC 91) | 1-2 digit groups |
| [Decode Ways II](https://leetcode.com/problems/decode-ways-ii/) (LC 639) | With wildcards |
| [Palindrome Partitioning II](https://leetcode.com/problems/palindrome-partitioning-ii/) (LC 132) | Min cuts for palindrome parts |
| [Restore IP Addresses](https://leetcode.com/problems/restore-ip-addresses/) (LC 93) | 4 valid octets |
| [Extra Characters in a String](https://leetcode.com/problems/extra-characters-in-a-string/) (LC 2707) | Min leftover chars |

---

## §13: Greedy + Stack on Strings

### Trigger Words
- "Lexicographically smallest/largest"
- "Remove k characters to make smallest string"
- "Remove duplicate letters, keep smallest"
- "Build string character by character, can pop previous choices"

### Mental Model

Process characters left to right. Maintain a **monotonic stack**.
At each character, pop the stack while:
1. Current char is better (smaller for lex-smallest)
2. There are enough remaining characters to fill the required length
3. The popped character can still appear later (or duplicates exist)

### Template
```python
def remove_k_digits(num, k):
    stack = []
    for digit in num:
        while k > 0 and stack and stack[-1] > digit:
            stack.pop()
            k -= 1
        stack.append(digit)
    stack = stack[:len(stack) - k] if k > 0 else stack
    return ''.join(stack).lstrip('0') or '0'
```

### Key Problems

| Problem | Greedy rule |
|---|---|
| [Remove K Digits](https://leetcode.com/problems/remove-k-digits/) (LC 402) | Remove to make smallest |
| [Remove Duplicate Letters](https://leetcode.com/problems/remove-duplicate-letters/) (LC 316) | Smallest with each char once |
| [Smallest Subsequence of Distinct Characters](https://leetcode.com/problems/smallest-subsequence-of-distinct-characters/) (LC 1081) | Same as LC 316 |
| [Create Maximum Number](https://leetcode.com/problems/create-maximum-number/) (LC 321) | Pick k digits from two arrays |
| [Largest Number](https://leetcode.com/problems/largest-number/) (LC 179) | Custom sort by concatenation |
| [Reorganize String](https://leetcode.com/problems/reorganize-string/) (LC 767) | Greedy + heap |

---

## §14: Stack-Based String Problems

### Trigger Words
- "Valid parentheses" / "balanced brackets"
- "Minimum add/remove to make valid"
- "Decode nested structure" (like `3[a2[c]]`)
- "Evaluate expression"
- "Remove outermost parentheses"

### Template (Balanced Parentheses)
```python
def is_valid(s):
    stack = []
    mapping = {')': '(', ']': '[', '}': '{'}
    for ch in s:
        if ch in mapping.values():
            stack.append(ch)
        elif ch in mapping:
            if not stack or stack[-1] != mapping[ch]:
                return False
            stack.pop()
    return len(stack) == 0
```

### Template (Decode String)
```python
def decode_string(s):
    stack = []
    current_str = ""
    current_num = 0
    for ch in s:
        if ch.isdigit():
            current_num = current_num * 10 + int(ch)
        elif ch == '[':
            stack.append((current_str, current_num))
            current_str, current_num = "", 0
        elif ch == ']':
            prev_str, num = stack.pop()
            current_str = prev_str + current_str * num
        else:
            current_str += ch
    return current_str
```

### Key Problems

| Problem | Stack usage |
|---|---|
| [Valid Parentheses](https://leetcode.com/problems/valid-parentheses/) (LC 20) | Match open/close |
| [Longest Valid Parentheses](https://leetcode.com/problems/longest-valid-parentheses/) (LC 32) | Stack of indices |
| [Minimum Add to Make Parentheses Valid](https://leetcode.com/problems/minimum-add-to-make-parentheses-valid/) (LC 921) | Counter or stack |
| [Minimum Remove to Make Valid Parentheses](https://leetcode.com/problems/minimum-remove-to-make-valid-parentheses/) (LC 1249) | Mark invalid indices |
| [Decode String](https://leetcode.com/problems/decode-string/) (LC 394) | Nested decode |
| [Basic Calculator](https://leetcode.com/problems/basic-calculator/) (LC 224) | Expression evaluation |
| [Basic Calculator II](https://leetcode.com/problems/basic-calculator-ii/) (LC 227) | Operator precedence |
| [Score of Parentheses](https://leetcode.com/problems/score-of-parentheses/) (LC 856) | Nested scoring |

---

## The String Pattern Decision Flowchart

```
START: What does the problem ask?
│
├── "Find/count substring pattern in text"?
│   ├── Single pattern → §3 KMP or §4 Z-Algorithm
│   ├── Multiple patterns → §6 Trie (Aho-Corasick for advanced)
│   ├── Approximate/rolling match → §5 String Hashing
│   └── Substring in a sliding window → §1 Sliding Window
│
├── "Palindrome"?
│   ├── Check if palindrome → §2 Two Pointers
│   ├── Longest palindromic substring → §7 Manacher's or §2 Expand
│   ├── Longest palindromic subsequence → §9 Palindrome DP
│   ├── Partition into palindromes → §9 Palindrome DP + §12 Partition DP
│   └── Palindrome pairs / construction → §6 Trie + §3 KMP
│
├── "Two strings" + transform/match/common?
│   └── → §8 Two-String DP
│
├── "Count/check subsequences"?
│   └── → §10 Subsequence DP
│
├── "Build valid strings" / "avoid pattern"?
│   └── → §11 Automaton DP (KMP + DP)
│
├── "Segment string into valid parts"?
│   └── → §12 String Partition DP (+ §6 Trie optimization)
│
├── "Lexicographically smallest" + removal/selection?
│   └── → §13 Greedy + Stack
│
├── "Parentheses" / "brackets" / "nested structure"?
│   └── → §14 Stack-Based
│
├── "Prefix search" / "autocomplete" / "word dictionary"?
│   └── → §6 Trie
│
└── "Longest/shortest substring with property"?
    └── → §1 Sliding Window or §2 Two Pointers
```

---

## Suggested Practice Order

### Phase 1: Foundations (do these first)
```
LC 3   Longest Substring Without Repeating  (Sliding Window)
LC 125 Valid Palindrome                     (Two Pointers)
LC 20  Valid Parentheses                    (Stack)
LC 392 Is Subsequence                      (Two Pointers)
LC 208 Implement Trie                      (Trie)
LC 5   Longest Palindromic Substring       (Expand/DP)
LC 72  Edit Distance                       (Two-String DP)
```

### Phase 2: Core Patterns
```
LC 76  Minimum Window Substring            (Sliding Window)
LC 28  Find First Occurrence               (KMP)
LC 459 Repeated Substring Pattern          (KMP prefix function)
LC 139 Word Break                          (Partition DP)
LC 91  Decode Ways                         (Partition DP)
LC 1143 Longest Common Subsequence         (Two-String DP)
LC 516 Longest Palindromic Subsequence     (Palindrome DP)
LC 131 Palindrome Partitioning             (Backtrack + Palindrome)
LC 316 Remove Duplicate Letters            (Greedy Stack)
LC 394 Decode String                       (Stack)
```

### Phase 3: Advanced
```
LC 10  Regular Expression Matching         (Two-String DP)
LC 44  Wildcard Matching                   (Two-String DP)
LC 115 Distinct Subsequences              (Subsequence DP)
LC 940 Distinct Subsequences II           (Counting trick)
LC 214 Shortest Palindrome                (KMP on s + # + rev(s))
LC 32  Longest Valid Parentheses          (Stack + DP)
LC 132 Palindrome Partitioning II         (Palindrome DP + Partition)
LC 212 Word Search II                     (Trie + Grid backtrack)
LC 1044 Longest Duplicate Substring       (Hashing + Binary Search)
LC 336 Palindrome Pairs                   (Trie + Palindrome)
LC 402 Remove K Digits                    (Greedy Stack)
```

### Phase 4: Hard / Contest
```
LC 1397 Find All Good Strings             (Digit DP + KMP Automaton)
LC 1092 Shortest Common Supersequence     (LCS + Reconstruct)
LC 30  Substring Concatenation of All Words (Multi-word Window)
LC 730 Count Different Palindromic Subseq (Hard Palindrome DP)
LC 1960 Max Product of Palindromic Substrings (Manacher's)
LC 321 Create Maximum Number              (Greedy + Merge)
```
