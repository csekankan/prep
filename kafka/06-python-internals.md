# Python Internals — Under the Hood

> A deep-dive into how CPython actually works: from source code to bytecode execution, memory management, the object model, metaclasses, descriptors, and every mechanism that separates a Python *user* from a Python *expert*.

---

## Table of Contents

1. [CPython Architecture](#1-cpython-architecture)
2. [Bytecode](#2-bytecode)
3. [Python Virtual Machine (PVM)](#3-python-virtual-machine-pvm)
4. [Object Model](#4-object-model)
5. [Memory Layout](#5-memory-layout)
6. [Weak References](#6-weak-references)
7. [__slots__](#7-__slots__)
8. [Descriptors](#8-descriptors)
9. [Metaclasses](#9-metaclasses)
10. [Import System Internals](#10-import-system-internals)
11. [Monkey Patching](#11-monkey-patching)

---

## 1. CPython Architecture

### 1.1 What Is CPython?

CPython is the **reference implementation** of Python, written in C. When you download Python from [python.org](https://python.org), you get CPython. Other implementations exist — PyPy (JIT-compiled), Jython (JVM), IronPython (.NET), GraalPy — but CPython defines what Python *is*.

Key facts:

- The CPython source lives at [github.com/python/cpython](https://github.com/python/cpython).
- The interpreter is roughly 500K lines of C plus 700K lines of Python (stdlib).
- Every language feature is ultimately a C function or struct.

### 1.2 Compilation Pipeline: Source → Tokens → AST → Bytecode

Python is **not** purely interpreted. The CPython pipeline has four distinct stages:

```
Source Code (.py)
      │
      ▼
   Tokenizer  (Lib/tokenize.py, Parser/tokenizer.c)
      │
      ▼
   Parser → AST  (Parser/parser.c → Python/ast.c)
      │
      ▼
   Compiler → Bytecode  (Python/compile.c)
      │
      ▼
   PVM Execution  (Python/ceval.c)
```

#### Stage 1 — Tokenization

The tokenizer breaks source text into tokens (keywords, identifiers, literals, operators).

```python
import tokenize
import io

source = "x = 42 + y\n"
tokens = tokenize.generate_tokens(io.StringIO(source).readline)

for tok in tokens:
    print(tok)
```

Output:

```
TokenInfo(type=1 (NAME),     string='x', start=(1, 0), end=(1, 1))
TokenInfo(type=54 (OP),      string='=', start=(1, 2), end=(1, 3))
TokenInfo(type=2 (NUMBER),   string='42', start=(1, 4), end=(1, 6))
TokenInfo(type=54 (OP),      string='+', start=(1, 7), end=(1, 8))
TokenInfo(type=1 (NAME),     string='y', start=(1, 9), end=(1, 10))
TokenInfo(type=4 (NEWLINE),  string='\n', start=(1, 10), end=(1, 11))
TokenInfo(type=0 (ENDMARKER),string='',  start=(2, 0), end=(2, 0))
```

#### Stage 2 — Parsing into an AST

The parser turns the token stream into an Abstract Syntax Tree:

```python
import ast

source = "x = 42 + y"
tree = ast.parse(source)
print(ast.dump(tree, indent=2))
```

```
Module(
  body=[
    Assign(
      targets=[Name(id='x', ctx=Store())],
      value=BinOp(
        left=Constant(value=42),
        op=Add(),
        right=Name(id='y', ctx=Load())
      )
    )
  ],
  type_ignores=[]
)
```

You can manipulate the AST before compilation — this is how tools like `pytest` rewrite assertions.

```python
import ast

class DoubleConstants(ast.NodeTransformer):
    """Double every integer constant in the AST."""
    def visit_Constant(self, node):
        if isinstance(node.value, int):
            node.value *= 2
        return node

source = "print(21)"
tree = ast.parse(source)
tree = DoubleConstants().visit(tree)
ast.fix_missing_locations(tree)
exec(compile(tree, "<ast>", "exec"))  # prints 42
```

#### Stage 3 — Compilation to Bytecode

`compile()` turns the AST into a **code object** containing bytecode:

```python
source = "x = 42 + y"
code = compile(source, "<string>", "exec")

print(type(code))        # <class 'code'>
print(code.co_code)       # raw bytes
print(code.co_consts)     # (42, None)
print(code.co_names)      # ('x', 'y')
```

#### Stage 4 — Execution

The PVM (covered in §3) executes the bytecode on a stack machine.

### 1.3 Key C Structures

Everything in CPython rests on two C structs.

#### PyObject — The Universal Base

Every Python object starts with a `PyObject` header:

```c
// Include/object.h (simplified)
typedef struct _object {
    Py_ssize_t ob_refcnt;     // reference count
    PyTypeObject *ob_type;    // pointer to type object
} PyObject;
```

Variable-length objects (lists, tuples, strings) extend this:

```c
typedef struct {
    PyObject ob_base;
    Py_ssize_t ob_size;       // number of items
} PyVarObject;
```

#### PyTypeObject — The Type Blueprint

Every type (int, str, list, your custom classes) is described by a massive `PyTypeObject` struct:

```c
// Simplified — the real struct has 50+ fields
typedef struct _typeobject {
    PyObject_VAR_HEAD
    const char *tp_name;           // "int", "str", etc.
    Py_ssize_t tp_basicsize;       // size of instances
    destructor tp_dealloc;         // destructor
    reprfunc tp_repr;              // __repr__
    hashfunc tp_hash;              // __hash__
    ternaryfunc tp_call;           // __call__
    getattrofunc tp_getattro;      // __getattr__
    PyMappingMethods *tp_as_mapping;   // __getitem__, etc.
    PySequenceMethods *tp_as_sequence; // __len__, etc.
    // ... many more slots
} PyTypeObject;
```

When you call `len(obj)`, CPython looks up `obj->ob_type->tp_as_sequence->sq_length` — the C function pointer behind `__len__`.

### 1.4 Reference Counting

CPython's **primary** garbage collection strategy is reference counting.

```python
import sys

a = [1, 2, 3]
print(sys.getrefcount(a))  # 2 (a + the getrefcount argument)

b = a
print(sys.getrefcount(a))  # 3

del b
print(sys.getrefcount(a))  # 2
```

How it works at the C level:

```c
// Incrementing (e.g., assignment)
#define Py_INCREF(op)  (++(op)->ob_refcnt)

// Decrementing (e.g., del, leaving scope)
#define Py_DECREF(op)                       \
    do {                                    \
        if (--(op)->ob_refcnt == 0)         \
            _Py_Dealloc(op);               \
    } while (0)
```

When the reference count hits zero, the object is **immediately** deallocated — no waiting for a GC cycle.

**The cycle problem:** Reference counting alone cannot handle circular references:

```python
a = []
b = []
a.append(b)
b.append(a)
del a, b
# refcounts are 1 (from each other), never reach 0
```

CPython has a **cyclic garbage collector** (`gc` module) that periodically scans for unreachable cycles:

```python
import gc

gc.collect()                # force a collection
print(gc.get_threshold())   # (700, 10, 10) — generation thresholds
gc.set_debug(gc.DEBUG_STATS)
```

The GC uses a **generational** scheme with three generations (0, 1, 2). New objects enter generation 0; survivors are promoted.

### 1.5 Memory Allocator Layers

CPython has a layered memory architecture:

```
┌─────────────────────────────────────────┐
│  Layer 3: Object-specific allocators    │  (list, dict, etc.)
├─────────────────────────────────────────┤
│  Layer 2: Python object allocator       │  (pymalloc)
├─────────────────────────────────────────┤
│  Layer 1: Python raw memory allocator   │  (PyMem_Malloc)
├─────────────────────────────────────────┤
│  Layer 0: OS allocator                  │  (malloc/free)
└─────────────────────────────────────────┘
```

#### pymalloc

For objects ≤ 512 bytes, CPython uses **pymalloc** instead of calling `malloc()`:

- Memory is carved into **arenas** (256 KB each).
- Arenas contain **pools** (4 KB each), one pool per size class.
- Size classes are multiples of 8 bytes: 8, 16, 24, …, 512.
- This avoids expensive system calls for the many tiny objects Python creates.

```python
import sys

# A small int uses pymalloc; a huge bytes object uses malloc
small = 42
big = b"x" * 1_000_000

print(sys.getsizeof(small))  # 28
print(sys.getsizeof(big))    # 1000033
```

### 1.6 How CPython Executes Code

End-to-end flow when you run `python script.py`:

1. **Read** the source file.
2. **Check** for a cached `.pyc` in `__pycache__/`. If valid (matching magic number + timestamp), load it.
3. Otherwise **tokenize → parse → compile** to bytecode.
4. **Write** the `.pyc` file for next time.
5. **Create** a module code object and a top-level frame.
6. **Enter** the evaluation loop (`_PyEval_EvalFrameDefault` in `ceval.c`).
7. **Execute** bytecode instructions one by one on the value stack.

```python
import py_compile, dis

py_compile.compile("script.py")  # force .pyc generation

# Examine what was compiled
with open("script.py") as f:
    code = compile(f.read(), "script.py", "exec")
dis.dis(code)
```

### Interview Relevance

- "How does Python execute code?" → Describe the four-stage pipeline.
- "Is Python compiled or interpreted?" → Both. Compiled to bytecode, then interpreted by the PVM.
- "How does Python manage memory?" → Reference counting + cyclic GC + pymalloc.

### Common Misconceptions

| Misconception | Reality |
|---|---|
| Python is purely interpreted | It compiles to bytecode first |
| GC is the primary cleanup mechanism | Reference counting frees most objects immediately |
| `del` calls `__del__` immediately | `del` decrements refcount; `__del__` runs when refcount hits 0 |
| `.pyc` files make Python faster | They skip parsing, not execution — minimal speedup |

---

## 2. Bytecode

### 2.1 What Is Bytecode?

Bytecode is the **intermediate representation** that CPython actually executes. Each bytecode instruction is 2 bytes wide (1 byte opcode + 1 byte argument, with extended args for larger values).

`.pyc` files contain:
- A 4-byte magic number (changes per Python version).
- A 4-byte flags field.
- An 8-byte timestamp + source size (or hash, since 3.7+).
- A marshalled code object.

```python
import struct, marshal, dis

with open("__pycache__/script.cpython-312.pyc", "rb") as f:
    magic = f.read(4)
    flags = struct.unpack("<I", f.read(4))[0]
    timestamp = struct.unpack("<I", f.read(4))[0]
    size = struct.unpack("<I", f.read(4))[0]
    code = marshal.load(f)

print(f"Magic: {magic.hex()}")
print(f"Flags: {flags}")
dis.dis(code)
```

### 2.2 The `dis` Module

`dis` is your window into the bytecode world:

```python
import dis

def add(a, b):
    return a + b

dis.dis(add)
```

```
  2           0 LOAD_FAST                0 (a)
              2 LOAD_FAST                1 (b)
              4 BINARY_ADD
              6 RETURN_VALUE
```

Each line shows:
- **Source line number** (left column)
- **Bytecode offset** (byte position)
- **Opcode name** (the instruction)
- **Argument** (index into co_consts, co_names, etc.)
- **Human-readable argument** (in parentheses)

### 2.3 Common Opcodes

| Opcode | Description |
|---|---|
| `LOAD_FAST` | Push a local variable onto the stack |
| `STORE_FAST` | Pop TOS and store in a local variable |
| `LOAD_CONST` | Push a constant onto the stack |
| `LOAD_GLOBAL` | Push a global variable (with name lookup) |
| `LOAD_ATTR` | Push `TOS.attr` |
| `STORE_ATTR` | `TOS1.attr = TOS` |
| `BINARY_ADD` | `TOS = TOS1 + TOS` |
| `BINARY_SUBSCR` | `TOS = TOS1[TOS]` |
| `CALL_FUNCTION` | Call a function with N positional args |
| `RETURN_VALUE` | Return TOS to the caller |
| `POP_TOP` | Discard TOS |
| `JUMP_FORWARD` | Unconditional relative jump |
| `POP_JUMP_IF_FALSE` | Jump if TOS is falsy |
| `BUILD_LIST` | Create a list from N stack items |
| `BUILD_TUPLE` | Create a tuple from N stack items |
| `FOR_ITER` | Get next item from iterator or jump |
| `COMPARE_OP` | Perform a comparison |
| `SETUP_FINALLY` | Push a try block for exception handling |
| `RAISE_VARARGS` | Raise an exception |
| `MAKE_FUNCTION` | Create a function object |
| `UNPACK_SEQUENCE` | Unpack an iterable into N stack items |

### 2.4 How to Read Bytecode Output

Let's trace through a more complex function:

```python
import dis

def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

dis.dis(factorial)
```

```
  2           0 LOAD_FAST                0 (n)
              2 LOAD_CONST               1 (1)
              4 COMPARE_OP               1 (<=)
              6 POP_JUMP_IF_FALSE       12

  3           8 LOAD_CONST               1 (1)
             10 RETURN_VALUE

  4     >>   12 LOAD_FAST                0 (n)
             14 LOAD_GLOBAL              0 (factorial)
             16 LOAD_FAST                0 (n)
             18 LOAD_CONST               1 (1)
             20 BINARY_SUBTRACT
             22 CALL_FUNCTION            1
             24 BINARY_MULTIPLY
             26 RETURN_VALUE
```

Execution trace for `factorial(3)`:

1. `LOAD_FAST 0` → push `n=3` onto stack: `[3]`
2. `LOAD_CONST 1` → push `1`: `[3, 1]`
3. `COMPARE_OP <=` → `3 <= 1` → `False`: `[False]`
4. `POP_JUMP_IF_FALSE 12` → jump to offset 12
5. `LOAD_FAST 0` → push `3`: `[3]`
6. `LOAD_GLOBAL 0` → push `factorial` function: `[3, <func>]`
7. `LOAD_FAST 0` → push `3`: `[3, <func>, 3]`
8. `LOAD_CONST 1` → push `1`: `[3, <func>, 3, 1]`
9. `BINARY_SUBTRACT` → `3-1=2`: `[3, <func>, 2]`
10. `CALL_FUNCTION 1` → call `factorial(2)`: (new frame)
11. Eventually returns `2`, stack becomes: `[3, 2]`
12. `BINARY_MULTIPLY` → `3 * 2 = 6`: `[6]`
13. `RETURN_VALUE` → return `6`

### 2.5 Performance Implications of Bytecode

Understanding bytecode helps you write faster Python:

```python
import dis

# Slow: global lookup each iteration
def sum_slow(items):
    total = 0
    for x in items:
        total = total + x  # LOAD_FAST + LOAD_FAST + BINARY_ADD + STORE_FAST
    return total

# Faster: use augmented assignment
def sum_fast(items):
    total = 0
    for x in items:
        total += x  # LOAD_FAST + LOAD_FAST + INPLACE_ADD + STORE_FAST (same ops, but cleaner)
    return total

# Fastest: use built-in (implemented in C)
def sum_fastest(items):
    return sum(items)  # LOAD_GLOBAL + LOAD_FAST + CALL_FUNCTION + RETURN_VALUE

dis.dis(sum_slow)
print("---")
dis.dis(sum_fast)
print("---")
dis.dis(sum_fastest)
```

**Local vs. global variable access:**

```python
import dis

GLOBAL_VAR = 42

def use_global():
    return GLOBAL_VAR   # LOAD_GLOBAL — hash table lookup

def use_local():
    local = 42
    return local         # LOAD_FAST — array index

dis.dis(use_global)
# LOAD_GLOBAL    0 (GLOBAL_VAR)
# RETURN_VALUE

dis.dis(use_local)
# LOAD_CONST     1 (42)
# STORE_FAST     0 (local)
# LOAD_FAST      0 (local)
# RETURN_VALUE
```

`LOAD_FAST` uses a C array index (`fastlocals[oparg]`) — O(1).
`LOAD_GLOBAL` does a dict lookup in the global and then builtin namespace — much slower.

### 2.6 Examining Code Objects

Every function has a code object with rich metadata:

```python
def example(a, b, c=10):
    x = a + b
    y = x * c
    return y

co = example.__code__

print(f"Name:       {co.co_name}")          # 'example'
print(f"Filename:   {co.co_filename}")      # '<stdin>' or file path
print(f"Arg count:  {co.co_argcount}")      # 3
print(f"Locals:     {co.co_varnames}")      # ('a', 'b', 'c', 'x', 'y')
print(f"Constants:  {co.co_consts}")        # (None, 10)
print(f"Stack size: {co.co_stacksize}")     # 2
print(f"Flags:      {co.co_flags:#x}")      # 0x43 (CO_OPTIMIZED | CO_NEWLOCALS | CO_NOFREE)
print(f"Bytecode:   {co.co_code.hex()}")    # raw bytes
```

### 2.7 Bytecode Optimization: Constant Folding

CPython's peephole optimizer performs limited optimizations:

```python
import dis

def constant_fold():
    return 2 * 3 * 7   # Folded at compile time

dis.dis(constant_fold)
# LOAD_CONST   1 (42)     ← compiler pre-computed 2*3*7 = 42
# RETURN_VALUE
```

```python
def no_fold():
    x = 2
    return x * 3 * 7   # NOT folded — x is a variable

dis.dis(no_fold)
# LOAD_CONST   1 (2)
# STORE_FAST   0 (x)
# LOAD_FAST    0 (x)
# LOAD_CONST   2 (3)
# BINARY_MULTIPLY
# LOAD_CONST   3 (7)
# BINARY_MULTIPLY
# RETURN_VALUE
```

### Practical Applications in LLD

- **Profiling hotspots:** Disassemble critical paths to count operations.
- **Understanding frameworks:** ORMs, decorators, and metaclasses all generate code objects.
- **Debugging mysterious behavior:** Bytecode never lies.

### Interview Relevance

- "What is a `.pyc` file?" → Cached bytecode to skip tokenization + parsing.
- "Why are local variables faster than global?" → `LOAD_FAST` vs `LOAD_GLOBAL`.
- "Does Python optimize code?" → Minimal: constant folding, dead code elimination.

---

## 3. Python Virtual Machine (PVM)

### 3.1 Stack-Based Virtual Machine

The PVM is a **stack machine**. Every operation pushes to or pops from a value stack.

```
Expression: a + b * c

Bytecode:          Stack state:
LOAD_FAST  a       [a]
LOAD_FAST  b       [a, b]
LOAD_FAST  c       [a, b, c]
BINARY_MULTIPLY    [a, b*c]
BINARY_ADD         [a + b*c]
RETURN_VALUE       (return top of stack)
```

Contrast with a **register machine** (like Lua): operations specify source/destination registers. Stack machines have simpler instruction encoding but potentially more push/pop overhead.

### 3.2 Frame Objects

Every function call creates a **frame object** — the execution context:

```python
import sys

def inner():
    frame = sys._getframe(0)  # current frame
    print(f"Function:  {frame.f_code.co_name}")
    print(f"Locals:    {frame.f_locals}")
    print(f"Globals:   {list(frame.f_globals.keys())[:5]}...")
    print(f"Line no:   {frame.f_lineno}")
    print(f"Caller:    {frame.f_back.f_code.co_name}")

def outer():
    x = 42
    inner()

outer()
```

Frame structure:

```
┌──────────────────────────────────┐
│           Frame Object           │
├──────────────────────────────────┤
│  f_code    → Code Object         │
│  f_locals  → {name: value}       │
│  f_globals → module globals      │
│  f_builtins → built-in names     │
│  f_back    → caller's frame      │
│  f_lasti   → last bytecode index │
│  f_lineno  → current line number │
│  Value Stack (array)             │
│  Block Stack (try/except/loop)   │
└──────────────────────────────────┘
```

### 3.3 Code Objects

A code object is an **immutable** container for compiled bytecode:

```python
def make_adder(n):
    def adder(x):
        return x + n
    return adder

# The outer function's code object
outer_code = make_adder.__code__
print(f"Name:       {outer_code.co_name}")        # 'make_adder'
print(f"Constants:  {outer_code.co_consts}")       # (None, <code object adder>)
print(f"Free vars:  {outer_code.co_freevars}")     # ()
print(f"Cell vars:  {outer_code.co_cellvars}")     # ('n',)

# The inner function's code object (stored as a constant!)
inner_code = outer_code.co_consts[1]
print(f"Name:       {inner_code.co_name}")         # 'adder'
print(f"Free vars:  {inner_code.co_freevars}")     # ('n',)
```

Notice: the inner code object is a **constant** inside the outer code object. Closures capture variables via cell/free variable machinery.

### 3.4 The Evaluation Loop (ceval.c)

The heart of CPython is `_PyEval_EvalFrameDefault` in `Python/ceval.c`. Simplified:

```c
// Pseudo-code of the evaluation loop
PyObject *
_PyEval_EvalFrameDefault(PyFrameObject *f, int throwflag)
{
    PyObject **stack_pointer;       // top of value stack
    const _Py_CODEUNIT *next_instr; // instruction pointer
    int opcode;                     // current opcode
    int oparg;                      // current argument

    for (;;) {
        opcode = _Py_OPCODE(*next_instr);
        oparg  = _Py_OPARG(*next_instr);
        next_instr++;

        switch (opcode) {

        case LOAD_FAST:
            PyObject *value = fastlocals[oparg];
            PUSH(value);
            Py_INCREF(value);
            break;

        case STORE_FAST:
            PyObject *value = POP();
            PyObject *old = fastlocals[oparg];
            fastlocals[oparg] = value;
            Py_XDECREF(old);
            break;

        case BINARY_ADD:
            PyObject *right = POP();
            PyObject *left  = POP();
            PyObject *sum   = PyNumber_Add(left, right);
            PUSH(sum);
            Py_DECREF(left);
            Py_DECREF(right);
            break;

        case RETURN_VALUE:
            retval = POP();
            goto exit_eval_frame;

        // ... hundreds more cases
        }

        // Check for pending signals, GIL release, etc.
        if (_Py_atomic_load_relaxed(&eval_breaker))
            handle_eval_breaker();
    }
}
```

The `eval_breaker` check is where the GIL (Global Interpreter Lock) gets released periodically (every 5ms by default since Python 3.2).

### 3.5 How Function Calls Work Internally

When Python calls a function, here's what happens at the VM level:

```python
def greet(name):
    return f"Hello, {name}!"

result = greet("World")
```

Step by step:

1. `LOAD_GLOBAL 0 (greet)` → push function object
2. `LOAD_CONST 1 ('World')` → push argument
3. `CALL_FUNCTION 1` → CPython:
   a. Extracts the code object from the function.
   b. Creates a new `PyFrameObject`.
   c. Binds arguments to local variables: `fastlocals[0] = "World"`.
   d. Sets `f_back` to the caller's frame.
   e. Enters the evaluation loop recursively (or via trampoline in 3.12+).
4. Inside the new frame, `greet` runs to `RETURN_VALUE`.
5. The return value is pushed onto the **caller's** stack.
6. The frame is deallocated (or cached for reuse in 3.12+).

### 3.6 Tracing Execution Through the VM

Python provides hooks to trace execution:

```python
import sys

def trace_calls(frame, event, arg):
    if event == 'call':
        print(f"CALL: {frame.f_code.co_name} at line {frame.f_lineno}")
    elif event == 'return':
        print(f"RETURN: {frame.f_code.co_name} → {arg!r}")
    elif event == 'line':
        print(f"LINE: {frame.f_lineno} in {frame.f_code.co_name}")
    return trace_calls

def add(a, b):
    result = a + b
    return result

def main():
    x = add(3, 4)
    y = add(x, 10)
    return y

sys.settrace(trace_calls)
main()
sys.settrace(None)
```

Output:

```
CALL: main at line 13
LINE: 14 in main
CALL: add at line 10
LINE: 11 in add
LINE: 12 in add
RETURN: add → 7
LINE: 15 in main
CALL: add at line 10
LINE: 11 in add
LINE: 12 in add
RETURN: add → 17
LINE: 16 in main
RETURN: main → 17
```

### 3.7 Python 3.11+ Frame Optimizations

Starting from Python 3.11, CPython underwent major changes:

- **Adaptive interpreter:** Instructions specialize themselves at runtime.
- **Quickened bytecode:** Frequently executed instructions get replaced with faster, type-specialized variants (e.g., `BINARY_ADD` → `BINARY_ADD_INT` for integers).
- **Inline caches:** Each instruction can have associated cache entries for attribute lookups.
- **Frame objects are lazily created:** Only materialized when someone calls `sys._getframe()`.

```python
import dis
import sys

def add_ints(a, b):
    return a + b

# After calling it many times with ints, the bytecode specializes
for _ in range(100):
    add_ints(1, 2)

# In 3.11+: dis.dis shows BINARY_OP with adaptive/quickened info
dis.dis(add_ints, adaptive=True)  # 3.11+ only
```

### Practical Applications in LLD

- **Custom profilers:** Build instrumentation using `sys.settrace()`.
- **Debuggers:** Frame objects provide full introspection (PyCharm, pdb use this).
- **Understanding recursion limits:** Each call creates a frame; `sys.setrecursionlimit()` bounds the frame stack.

### Interview Relevance

- "How does Python call a function?" → New frame, bind args, enter eval loop.
- "What's the call stack?" → Linked list of frame objects via `f_back`.
- "Why does Python have a recursion limit?" → Each call allocates a C stack frame + Python frame.

---

## 4. Object Model

### 4.1 Everything Is an Object

In Python, **everything** is a `PyObject` — integers, strings, functions, classes, modules, even `type` itself.

```python
print(isinstance(42, object))           # True
print(isinstance("hello", object))      # True
print(isinstance(print, object))        # True
print(isinstance(int, object))          # True
print(isinstance(type, object))         # True
print(isinstance(object, object))       # True — turtles all the way down
```

The type hierarchy:

```
object ← base of everything
  ├── int
  ├── str
  ├── float
  ├── list
  ├── dict
  ├── type ← metaclass of all classes
  │    └── (type is an instance of itself!)
  └── function
```

```python
print(type(42))          # <class 'int'>
print(type(int))         # <class 'type'>
print(type(type))        # <class 'type'> — type is its own metaclass
print(type(object))      # <class 'type'>

# The circular relationship
print(isinstance(type, object))    # True — type is a subclass of object
print(isinstance(object, type))    # True — object is an instance of type
```

### 4.2 PyObject Structure Revisited

Every object in memory has this layout:

```
┌────────────────────────┐
│  ob_refcnt (8 bytes)   │  reference count
├────────────────────────┤
│  ob_type   (8 bytes)   │  pointer to type object
├────────────────────────┤
│  ... type-specific     │  data (depends on type)
│       data ...         │
└────────────────────────┘
```

For a Python `int` with value 42:

```
┌────────────────────────┐
│  ob_refcnt = N         │
├────────────────────────┤
│  ob_type → PyLong_Type │
├────────────────────────┤
│  ob_size = 1           │  number of "digits"
├────────────────────────┤
│  ob_digit[0] = 42      │  the actual value
└────────────────────────┘
```

### 4.3 id(), type(), isinstance()

```python
a = [1, 2, 3]

# id() returns the memory address (in CPython)
print(id(a))             # e.g., 140234567890
print(hex(id(a)))        # e.g., 0x7f8a1c3b2340

# type() returns the type object
print(type(a))           # <class 'list'>
print(type(a) is list)   # True

# isinstance() checks the type hierarchy
print(isinstance(a, list))     # True
print(isinstance(a, object))   # True — everything is an object
print(isinstance(True, int))   # True — bool is a subclass of int!

# issubclass() checks class hierarchy
print(issubclass(bool, int))      # True
print(issubclass(int, object))    # True
```

**CPython integer caching:**

```python
a = 256
b = 256
print(a is b)   # True — integers -5 to 256 are cached singletons

a = 257
b = 257
print(a is b)   # False (usually) — different objects
                 # (may be True in some contexts due to compiler optimization)
```

### 4.4 Object Creation and Destruction

Object creation involves two steps: **allocation** (`__new__`) and **initialization** (`__init__`).

```python
class Point:
    def __new__(cls, x, y):
        print(f"__new__ called: creating instance of {cls.__name__}")
        instance = super().__new__(cls)
        return instance

    def __init__(self, x, y):
        print(f"__init__ called: initializing with ({x}, {y})")
        self.x = x
        self.y = y

    def __del__(self):
        print(f"__del__ called: destroying Point({self.x}, {self.y})")

p = Point(3, 4)
# Output:
# __new__ called: creating instance of Point
# __init__ called: initializing with (3, 4)

del p
# Output:
# __del__ called: destroying Point(3, 4)
```

### 4.5 `__new__` vs `__init__`

| Aspect | `__new__` | `__init__` |
|---|---|---|
| Purpose | Allocate and return instance | Initialize instance |
| First argument | `cls` (the class) | `self` (the instance) |
| Returns | The new instance | `None` |
| Called | Before `__init__` | After `__new__` |
| Can return different type | Yes | No |
| Use for immutable types | Yes (only way to set value) | Cannot modify immutable |

`__new__` is essential for immutable types:

```python
class UpperStr(str):
    """A string that's always uppercase."""
    def __new__(cls, value):
        return super().__new__(cls, value.upper())

    def __init__(self, value):
        # Cannot modify the string here — it's already immutable
        pass

s = UpperStr("hello")
print(s)           # HELLO
print(type(s))     # <class '__main__.UpperStr'>
```

**Singleton pattern using `__new__`:**

```python
class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, value=None):
        self.value = value

a = Singleton(1)
b = Singleton(2)
print(a is b)        # True
print(a.value)       # 2 — __init__ runs twice on the same instance!
```

### 4.6 Slots and Dictionaries

By default, each Python object has a `__dict__` for attribute storage:

```python
class Regular:
    def __init__(self, x, y):
        self.x = x
        self.y = y

obj = Regular(1, 2)
print(obj.__dict__)        # {'x': 1, 'y': 2}
obj.z = 3                  # dynamic attribute — works fine
print(obj.__dict__)        # {'x': 1, 'y': 2, 'z': 3}
```

With `__slots__`, attributes are stored in a fixed-size array instead:

```python
class Slotted:
    __slots__ = ('x', 'y')

    def __init__(self, x, y):
        self.x = x
        self.y = y

obj = Slotted(1, 2)
# obj.__dict__  → AttributeError: 'Slotted' has no '__dict__'
# obj.z = 3    → AttributeError: 'Slotted' has no attribute 'z'
```

(More on `__slots__` in §7.)

### 4.7 Method Resolution Order (MRO) — C3 Linearization

When a class inherits from multiple parents, Python uses the **C3 linearization** algorithm to determine the method lookup order:

```python
class A:
    def method(self):
        return "A"

class B(A):
    def method(self):
        return "B"

class C(A):
    def method(self):
        return "C"

class D(B, C):
    pass

print(D.__mro__)
# (<class 'D'>, <class 'B'>, <class 'C'>, <class 'A'>, <class 'object'>)

print(D().method())  # "B" — B comes before C in the MRO
```

C3 linearization guarantees:
1. **Subclasses come before parents.**
2. **Parent order is preserved** (B before C if declared `class D(B, C)`).
3. **Monotonicity:** If B comes before C in D's MRO, B comes before C in every subclass of D.

```python
# Diamond inheritance with super()
class A:
    def method(self):
        print("A.method")

class B(A):
    def method(self):
        print("B.method")
        super().method()  # calls C.method, NOT A.method!

class C(A):
    def method(self):
        print("C.method")
        super().method()

class D(B, C):
    def method(self):
        print("D.method")
        super().method()

D().method()
# D.method
# B.method
# C.method
# A.method
```

`super()` follows the MRO, not the class hierarchy. This is called **cooperative multiple inheritance**.

**Invalid MRO — C3 will reject it:**

```python
class X: pass
class Y: pass
class A(X, Y): pass
class B(Y, X): pass

try:
    class C(A, B): pass  # Contradictory ordering: X before Y vs Y before X
except TypeError as e:
    print(e)
    # Cannot create a consistent method resolution order (MRO) for bases X, Y
```

### 4.8 Descriptor Protocol

Descriptors are the mechanism behind properties, methods, class methods, static methods, and more. Covered in detail in §8.

### Practical Applications in LLD

- **Singleton pattern:** `__new__` for controlling instance creation.
- **Immutable value objects:** `__new__` for types like `UpperStr`.
- **Plugin systems:** MRO enables cooperative method chains.
- **Framework design:** Understanding type/object relationship is key for ORMs.

### Interview Relevance

- "What's the difference between `is` and `==`?" → `is` compares `id()` (identity), `==` compares `__eq__` (equality).
- "Explain MRO" → C3 linearization; `super()` follows MRO, not parent class.
- "What's the difference between `__new__` and `__init__`?" → Allocation vs initialization.

### Common Misconceptions

| Misconception | Reality |
|---|---|
| `type()` and `isinstance()` are the same | `isinstance()` checks the entire hierarchy |
| `super()` calls the parent class | `super()` follows the MRO |
| `__del__` is a destructor (like C++) | `__del__` is a finalizer; timing is not guaranteed |
| Objects can only have attributes from `__init__` | Any attribute can be added anytime (unless `__slots__`) |

---

## 5. Memory Layout

### 5.1 Object Header

Every CPython object begins with a 16-byte header (on 64-bit systems):

```
┌──────────────────────┐
│  ob_refcnt  (8 bytes)│  Py_ssize_t — reference count
├──────────────────────┤
│  ob_type    (8 bytes)│  PyTypeObject* — type pointer
└──────────────────────┘
Total header: 16 bytes
```

Variable-size objects (`PyVarObject`) add an `ob_size` field:

```
┌──────────────────────┐
│  ob_refcnt  (8 bytes)│
├──────────────────────┤
│  ob_type    (8 bytes)│
├──────────────────────┤
│  ob_size    (8 bytes)│  Py_ssize_t — number of items
└──────────────────────┘
Total header: 24 bytes
```

### 5.2 Memory Layout of Built-in Types

#### int

Python integers have arbitrary precision (big integers):

```python
import sys

print(sys.getsizeof(0))      # 28 bytes — header + 0 digits
print(sys.getsizeof(1))      # 28 bytes — header + 1 digit (30-bit)
print(sys.getsizeof(2**30))  # 32 bytes — header + 2 digits
print(sys.getsizeof(2**60))  # 36 bytes — header + 3 digits
```

Layout:

```
┌──────────────────────┐
│  ob_refcnt  (8)      │
│  ob_type    (8)      │  → PyLong_Type
│  ob_size    (4)      │  number of digits (sign-encoded)
│  ob_digit[] (4*N)    │  array of 30-bit "digits"
└──────────────────────┘
```

Small integers (-5 to 256) are **pre-allocated singletons** — they're never freed.

#### str

Strings use different internal representations based on the maximum character:

```python
import sys

# ASCII — 1 byte per char (compact ASCII)
s1 = "hello"
print(sys.getsizeof(s1))     # 54 bytes

# Latin-1 — 1 byte per char
s2 = "héllo"
print(sys.getsizeof(s2))     # 54 bytes

# UCS-2 — 2 bytes per char (has a character > U+00FF)
s3 = "h€llo"
print(sys.getsizeof(s3))     # 78 bytes

# UCS-4 — 4 bytes per char (has a character > U+FFFF)
s4 = "h😀llo"
print(sys.getsizeof(s4))     # 76 bytes
```

This is **flexible string representation** (PEP 393, Python 3.3+):

```
┌──────────────────────┐
│  PyObject header     │  16 bytes
│  hash               │  cached hash value
│  length             │  number of characters
│  kind               │  1=Latin-1, 2=UCS-2, 4=UCS-4
│  data[]             │  actual characters
└──────────────────────┘
```

#### list

Lists are dynamic arrays of pointers:

```python
import sys

# Empty list
print(sys.getsizeof([]))          # 56 bytes (header + pointer to array)

# List with items
print(sys.getsizeof([1]))         # 64 bytes
print(sys.getsizeof([1, 2, 3]))   # 80 bytes

# But this doesn't include the elements themselves!
# Each int object is 28 bytes — not counted
```

Layout:

```
┌──────────────────────────┐
│  ob_refcnt    (8)        │
│  ob_type      (8)        │  → PyList_Type
│  ob_size      (8)        │  number of items
│  ob_item      (8)        │  → pointer to array of PyObject*
│  allocated    (8)        │  capacity (over-allocation)
└──────────────────────────┘
  Total fixed: 56 bytes

  ob_item → [ptr0, ptr1, ptr2, ...]  (8 bytes each)
```

Lists over-allocate to amortize growth:

```python
import sys

sizes = []
lst = []
for i in range(20):
    lst.append(i)
    sizes.append(sys.getsizeof(lst))

for i, s in enumerate(sizes):
    print(f"len={i+1:2d}  size={s:4d}  capacity≈{(s-56)//8}")
```

Output shows the over-allocation pattern:

```
len= 1  size=  88  capacity≈4
len= 2  size=  88  capacity≈4
len= 3  size=  88  capacity≈4
len= 4  size=  88  capacity≈4
len= 5  size= 120  capacity≈8
...
```

#### dict

Python dicts are hash tables with open addressing (since 3.6, compact + ordered):

```python
import sys

print(sys.getsizeof({}))                # 64 bytes (empty)
print(sys.getsizeof({'a': 1}))          # 184 bytes
print(sys.getsizeof({'a': 1, 'b': 2}))  # 184 bytes
```

Layout (Python 3.6+ compact dict):

```
┌──────────────────────────┐
│  PyObject header         │
│  ma_used     (8)         │  number of items
│  ma_version  (8)         │  version tag (for optimization)
│  ma_keys     (8)         │  → keys table
│  ma_values   (8)         │  → values array (split tables for instances)
└──────────────────────────┘

Keys table:
┌──────────────────────────┐
│  dk_refcnt               │
│  dk_size                 │  hash table size (power of 2)
│  dk_indices[]            │  sparse array: hash → index
│  dk_entries[]            │  dense array: [(hash, key, value), ...]
└──────────────────────────┘
```

### 5.3 sys.getsizeof() vs Actual Memory

`sys.getsizeof()` returns the **shallow** size — it doesn't recurse into contained objects:

```python
import sys

# Shallow size of a list
lst = [[1, 2, 3], [4, 5, 6]]
print(sys.getsizeof(lst))    # 72 bytes (just the list object + 2 pointers)

# Total (deep) size is much larger
def deep_getsizeof(obj, seen=None):
    """Recursively calculate total memory usage."""
    if seen is None:
        seen = set()

    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    size = sys.getsizeof(obj)

    if isinstance(obj, dict):
        size += sum(deep_getsizeof(k, seen) + deep_getsizeof(v, seen)
                    for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set, frozenset)):
        size += sum(deep_getsizeof(item, seen) for item in obj)

    return size

print(deep_getsizeof(lst))   # ~300+ bytes (includes sublists and ints)
```

### 5.4 Memory Profiling Tools

```python
# tracemalloc — built-in memory tracer
import tracemalloc

tracemalloc.start()

# Allocate some memory
data = [dict(name=f"user_{i}", age=i) for i in range(10000)]

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

print("Top 5 memory allocations:")
for stat in top_stats[:5]:
    print(stat)
```

```python
# objgraph — visualize object references (pip install objgraph)
import objgraph

class Node:
    def __init__(self, value):
        self.value = value
        self.children = []

root = Node(1)
root.children.append(Node(2))
root.children.append(Node(3))

objgraph.show_refs([root], filename='refs.png')  # generates a graph
print(objgraph.count('Node'))                      # count Node objects
```

### 5.5 Small Object Optimization

CPython optimizes several small objects:

```python
# Small integer cache: -5 to 256
a = 100
b = 100
assert a is b  # same object

# String interning: identifiers and small strings
s1 = "hello"
s2 = "hello"
assert s1 is s2  # interned

# But not for computed strings
s3 = "hel" + "lo"
s4 = "hello"
assert s3 is s4  # True — compiler optimizes concatenation of literals

import sys
s5 = sys.intern("dynamic_string_" + str(42))
s6 = sys.intern("dynamic_string_42")
assert s5 is s6  # True — manually interned

# Empty tuple singleton
assert () is ()  # True — only one empty tuple exists

# True/False/None are singletons
assert True is True
assert None is None
```

### 5.6 Memory Layout: tuple vs list

```python
import sys

# Tuple is fixed-size — no over-allocation, no resize machinery
t = (1, 2, 3)
l = [1, 2, 3]

print(sys.getsizeof(t))  # 64 bytes
print(sys.getsizeof(l))  # 88 bytes (includes allocated field + over-allocation)
```

Tuple layout:

```
┌──────────────────────┐
│  ob_refcnt  (8)      │
│  ob_type    (8)      │  → PyTuple_Type
│  ob_size    (8)      │  number of items
│  ob_item[0] (8)      │  pointer to first item
│  ob_item[1] (8)      │  pointer to second item
│  ob_item[2] (8)      │  pointer to third item
└──────────────────────┘
Total: 24 + 8*3 = 48 bytes (+ GC overhead = 64)
```

### Practical Applications in LLD

- **Choosing containers:** Know the memory cost of list vs tuple vs dict vs set.
- **Large-scale data:** Use `__slots__`, `array` module, or `numpy` for memory-critical apps.
- **Memory leak detection:** `tracemalloc` + `objgraph` to find leaks.
- **Cache sizing:** Calculate actual memory usage for cache eviction policies.

### Interview Relevance

- "Why are tuples more memory-efficient than lists?" → No over-allocation, no resize pointer.
- "How does Python store strings?" → Flexible representation (1/2/4 bytes per char).
- "How would you profile memory usage?" → `tracemalloc`, `sys.getsizeof()`, `objgraph`.

---

## 6. Weak References

### 6.1 What Are Weak References?

A **weak reference** is a reference to an object that does **not** prevent it from being garbage collected. When the object's strong reference count drops to zero, it's collected — and the weak reference becomes invalid.

```python
import weakref

class Cacheable:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"Cacheable({self.name!r})"

obj = Cacheable("data")
weak = weakref.ref(obj)

print(weak())       # Cacheable('data') — dereference the weak ref
print(weak() is obj) # True

del obj
print(weak())       # None — object was garbage collected
```

### 6.2 The weakref Module

```python
import weakref

class Resource:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"Resource({self.name!r})"

# Basic weak reference
r = Resource("db_connection")
ref = weakref.ref(r)

# Weak reference with callback
def on_finalize(ref):
    print(f"Object has been collected! ref() = {ref()}")

r2 = Resource("cache_entry")
ref2 = weakref.ref(r2, on_finalize)

del r2  # prints: Object has been collected! ref() = None

# weakref.proxy — transparent access (raises ReferenceError when dead)
r3 = Resource("file_handle")
proxy = weakref.proxy(r3)
print(proxy.name)   # "file_handle" — transparent attribute access

del r3
try:
    print(proxy.name)
except ReferenceError as e:
    print(f"ReferenceError: {e}")  # weakly-referenced object no longer exists
```

### 6.3 WeakValueDictionary and WeakSet

```python
import weakref

class User:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"User({self.name!r})"

# WeakValueDictionary — values are weak references
cache = weakref.WeakValueDictionary()

user1 = User("Alice")
user2 = User("Bob")

cache["alice"] = user1
cache["bob"] = user2

print(dict(cache))  # {'alice': User('Alice'), 'bob': User('Bob')}

del user1
print(dict(cache))  # {'bob': User('Bob')} — alice was collected!

# WeakSet — elements are weak references
active_users = weakref.WeakSet()

u1 = User("Charlie")
u2 = User("Diana")

active_users.add(u1)
active_users.add(u2)

print(list(active_users))  # [User('Charlie'), User('Diana')]

del u1
print(list(active_users))  # [User('Diana')]
```

### 6.4 weakref.finalize — Better Than __del__

`weakref.finalize` is the recommended way to run cleanup code:

```python
import weakref
import tempfile
import os

class TempFileManager:
    def __init__(self):
        fd, self.path = tempfile.mkstemp()
        os.close(fd)
        # Register cleanup — guaranteed to run, even during interpreter shutdown
        self._finalizer = weakref.finalize(self, self._cleanup, self.path)

    @staticmethod
    def _cleanup(path):
        print(f"Cleaning up temp file: {path}")
        if os.path.exists(path):
            os.unlink(path)

    def detach(self):
        """Prevent cleanup (e.g., if the file was moved)."""
        self._finalizer.detach()

mgr = TempFileManager()
print(f"Temp file: {mgr.path}")
del mgr  # prints: Cleaning up temp file: /tmp/...
```

Why `finalize` is better than `__del__`:

| `__del__` | `weakref.finalize` |
|---|---|
| May not run during shutdown | Guaranteed to run at shutdown |
| Prevents reference cycles from being collected | Does not prevent collection |
| Cannot easily be cancelled | Can be detached or called early |
| Hard to test | Easy to test |

### 6.5 Use Cases

#### Cache Implementation with Weak References

```python
import weakref
import time

class ExpensiveObject:
    """Simulates an expensive-to-create object."""
    _creation_count = 0

    def __init__(self, key):
        ExpensiveObject._creation_count += 1
        self.key = key
        self.data = f"expensive_data_for_{key}"
        time.sleep(0.01)  # simulate expensive computation

    def __repr__(self):
        return f"ExpensiveObject({self.key!r})"

class WeakCache:
    """
    A cache that doesn't prevent objects from being garbage collected.

    When memory pressure is high, cached objects can be collected.
    The cache transparently recreates them on next access.
    """

    def __init__(self, factory):
        self._factory = factory
        self._cache = weakref.WeakValueDictionary()
        self._hits = 0
        self._misses = 0

    def get(self, key):
        obj = self._cache.get(key)
        if obj is not None:
            self._hits += 1
            return obj

        self._misses += 1
        obj = self._factory(key)
        self._cache[key] = obj
        return obj

    @property
    def stats(self):
        return {"hits": self._hits, "misses": self._misses,
                "cached": len(self._cache)}

# Usage
cache = WeakCache(ExpensiveObject)

# First access — cache miss
obj1 = cache.get("user_1")
obj2 = cache.get("user_2")
print(cache.stats)  # {'hits': 0, 'misses': 2, 'cached': 2}

# Second access — cache hit
obj1_again = cache.get("user_1")
print(cache.stats)  # {'hits': 1, 'misses': 2, 'cached': 2}
print(obj1 is obj1_again)  # True

# Delete strong references
del obj1, obj1_again
import gc; gc.collect()
print(cache.stats)  # {'hits': 1, 'misses': 2, 'cached': 1} — user_1 was collected
```

#### Observer Pattern with Weak References

```python
import weakref

class EventEmitter:
    """
    Event emitter that uses weak references to observers.

    Observers are automatically removed when they are garbage collected,
    preventing memory leaks from forgotten unsubscriptions.
    """

    def __init__(self):
        self._listeners = {}  # event_name → list of WeakMethod/ref

    def on(self, event, callback):
        if event not in self._listeners:
            self._listeners[event] = []

        if hasattr(callback, '__self__'):
            ref = weakref.WeakMethod(callback, self._make_cleanup(event))
        else:
            ref = weakref.ref(callback, self._make_cleanup(event))

        self._listeners[event].append(ref)

    def _make_cleanup(self, event):
        def cleanup(ref):
            if event in self._listeners:
                self._listeners[event] = [
                    r for r in self._listeners[event] if r() is not None
                ]
        return cleanup

    def emit(self, event, *args, **kwargs):
        if event not in self._listeners:
            return
        for ref in self._listeners[event]:
            callback = ref()
            if callback is not None:
                callback(*args, **kwargs)

class Logger:
    def __init__(self, name):
        self.name = name

    def on_event(self, data):
        print(f"[{self.name}] received: {data}")

emitter = EventEmitter()

logger1 = Logger("FileLogger")
logger2 = Logger("ConsoleLogger")

emitter.on("data", logger1.on_event)
emitter.on("data", logger2.on_event)

emitter.emit("data", "hello")
# [FileLogger] received: hello
# [ConsoleLogger] received: hello

del logger1
emitter.emit("data", "world")
# [ConsoleLogger] received: world
# FileLogger was automatically removed!
```

### 6.6 Objects That Don't Support Weak References

Not all objects can be weakly referenced:

```python
import weakref

# These CANNOT be weakly referenced (no __weakref__ slot):
for obj in [42, "hello", (1, 2), [1, 2], {}, set()]:
    try:
        weakref.ref(obj)
    except TypeError as e:
        print(f"{type(obj).__name__:10s} → {e}")

# Output:
# int        → cannot create weak reference to 'int' object
# str        → cannot create weak reference to 'str' object
# tuple      → cannot create weak reference to 'tuple' object
# list       → cannot create weak reference to 'list' object
# dict       → cannot create weak reference to 'dict' object
# set        → cannot create weak reference to 'set' object
```

Custom classes support weak references by default (they have a `__weakref__` slot). Subclasses of built-ins can add it:

```python
class WeakableList(list):
    __slots__ = ('__weakref__',)

lst = WeakableList([1, 2, 3])
ref = weakref.ref(lst)  # works!
```

### Practical Applications in LLD

- **Caches:** Let cached objects be collected under memory pressure.
- **Observer/Event systems:** Auto-unsubscribe dead observers.
- **Flyweight pattern:** Share objects without preventing cleanup.
- **Parent-child references:** Break reference cycles (child → parent via weakref).

### Interview Relevance

- "How do you prevent memory leaks in observer patterns?" → Weak references.
- "What is a weak reference?" → A reference that doesn't prevent GC.
- "When would you use `WeakValueDictionary`?" → Caches where values should be collectible.

### Common Misconceptions

| Misconception | Reality |
|---|---|
| Weak refs work on all types | Built-in types (int, str, list, dict) don't support them |
| `__del__` is the right cleanup tool | `weakref.finalize` is safer and more predictable |
| Weak refs prevent circular references | They don't — they prevent *preventing* GC |

---

## 7. `__slots__`

### 7.1 What Slots Do

By default, Python objects store attributes in a per-instance `__dict__` — a full hash table. `__slots__` replaces this with a fixed-size struct, saving memory and enabling faster attribute access.

```python
class WithDict:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class WithSlots:
    __slots__ = ('x', 'y', 'z')
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
```

Memory layout comparison:

```
WithDict instance:                WithSlots instance:
┌─────────────────────┐           ┌─────────────────────┐
│ ob_refcnt     (8)   │           │ ob_refcnt     (8)   │
│ ob_type       (8)   │           │ ob_type       (8)   │
│ __dict__      (8) ──┼───→ dict  │ x             (8)   │
│ __weakref__   (8)   │  (232+)   │ y             (8)   │
└─────────────────────┘           │ z             (8)   │
Total: ~296 bytes                 └─────────────────────┘
                                  Total: ~64 bytes (78% less!)
```

### 7.2 Memory Savings — Benchmarked

```python
import sys

class WithDict:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class WithSlots:
    __slots__ = ('x', 'y', 'z')
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

d = WithDict(1, 2, 3)
s = WithSlots(1, 2, 3)

# Instance size
print(f"WithDict:  {sys.getsizeof(d)} bytes")         # 48 bytes
print(f"WithSlots: {sys.getsizeof(s)} bytes")          # 64 bytes (wait, what?)

# But WithDict has a __dict__!
print(f"WithDict.__dict__: {sys.getsizeof(d.__dict__)} bytes")  # 232+ bytes
print(f"Total WithDict:    {sys.getsizeof(d) + sys.getsizeof(d.__dict__)} bytes")

# At scale — 1 million objects
import tracemalloc

tracemalloc.start()
dicts = [WithDict(i, i+1, i+2) for i in range(1_000_000)]
snap1 = tracemalloc.take_snapshot()
dicts.clear()
import gc; gc.collect()

slots = [WithSlots(i, i+1, i+2) for i in range(1_000_000)]
snap2 = tracemalloc.take_snapshot()

for snap, name in [(snap1, "WithDict"), (snap2, "WithSlots")]:
    total = sum(s.size for s in snap.statistics('filename'))
    print(f"{name}: {total / 1024 / 1024:.1f} MB")

# Typical results:
# WithDict:  ~210 MB
# WithSlots: ~72 MB
```

### 7.3 Speed Improvements

Attribute access is faster because it's a C array index, not a dict lookup:

```python
import timeit

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class PointSlots:
    __slots__ = ('x', 'y')
    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(3, 4)
ps = PointSlots(3, 4)

# Read performance
t1 = timeit.timeit("p.x", globals={"p": p}, number=10_000_000)
t2 = timeit.timeit("ps.x", globals={"ps": ps}, number=10_000_000)
print(f"Dict read:  {t1:.3f}s")
print(f"Slots read: {t2:.3f}s")
print(f"Speedup:    {t1/t2:.1f}x")

# Write performance
t3 = timeit.timeit("p.x = 5", globals={"p": p}, number=10_000_000)
t4 = timeit.timeit("ps.x = 5", globals={"ps": ps}, number=10_000_000)
print(f"Dict write:  {t3:.3f}s")
print(f"Slots write: {t4:.3f}s")
print(f"Speedup:     {t3/t4:.1f}x")

# Typical results:
# Dict read:  0.42s
# Slots read: 0.35s
# Speedup:    1.2x
#
# Dict write:  0.55s
# Slots write: 0.40s
# Speedup:     1.4x
```

### 7.4 Limitations

```python
# 1. No dynamic attributes
class Rigid:
    __slots__ = ('x', 'y')

r = Rigid()
r.x = 1
r.y = 2
try:
    r.z = 3  # AttributeError!
except AttributeError as e:
    print(e)  # 'Rigid' object has no attribute 'z'

# 2. Inheritance issues — child must also declare __slots__
class Parent:
    __slots__ = ('x',)

class Child(Parent):
    pass  # No __slots__ → gets a __dict__ → negates parent's savings!

c = Child()
c.x = 1
c.y = 2  # Works! Child has __dict__
print(hasattr(c, '__dict__'))  # True

# Proper inheritance
class ProperChild(Parent):
    __slots__ = ('y',)  # Only NEW attributes

pc = ProperChild()
pc.x = 1  # from Parent
pc.y = 2  # from ProperChild
# pc.z = 3  # AttributeError

# 3. No multiple inheritance with conflicting non-empty __slots__
class A:
    __slots__ = ('x',)

class B:
    __slots__ = ('y',)

class C(A, B):  # This works — slots don't overlap
    __slots__ = ('z',)

# 4. Can't use with default mutable attributes
class Bad:
    __slots__ = ('items',)
    items = []  # This is a CLASS attribute, not a default!

# 5. No weak references by default (unless included)
class NoWeakRef:
    __slots__ = ('x',)

class WithWeakRef:
    __slots__ = ('x', '__weakref__')

# 6. Pickling needs __getstate__ and __setstate__
import pickle

class SlottedPickle:
    __slots__ = ('x', 'y')
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __getstate__(self):
        return {slot: getattr(self, slot) for slot in self.__slots__}
    def __setstate__(self, state):
        for slot, value in state.items():
            setattr(self, slot, value)

sp = SlottedPickle(1, 2)
data = pickle.dumps(sp)
sp2 = pickle.loads(data)
print(sp2.x, sp2.y)  # 1 2
```

### 7.5 When to Use `__slots__` in LLD

Use `__slots__` when:

1. **Many instances** — thousands or millions of objects (nodes, events, records).
2. **Known attributes** — the set of attributes is fixed at design time.
3. **Performance-critical** — attribute access is in a hot loop.
4. **Memory-constrained** — embedded systems, large data processing.

Don't use `__slots__` when:

1. **Few instances** — the savings are negligible.
2. **Dynamic attributes needed** — plugins, metaprogramming.
3. **Complex inheritance** — unless you carefully slot every class.

### 7.6 High-Performance Data Containers

```python
class Vector3D:
    """A high-performance 3D vector using __slots__."""
    __slots__ = ('x', 'y', 'z')

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        return Vector3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Vector3D(self.x - other.x, self.y - other.y, self.z - other.z)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z

    def magnitude(self):
        return (self.x**2 + self.y**2 + self.z**2) ** 0.5

    def __repr__(self):
        return f"Vector3D({self.x}, {self.y}, {self.z})"

# Efficient linked list node
class LinkedNode:
    __slots__ = ('value', 'next')

    def __init__(self, value, next_node=None):
        self.value = value
        self.next = next_node

# Efficient tree node
class TreeNode:
    __slots__ = ('value', 'left', 'right', 'parent', '__weakref__')

    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None
        self.parent = None

# Efficient graph edge
class Edge:
    __slots__ = ('source', 'target', 'weight')

    def __init__(self, source, target, weight=1.0):
        self.source = source
        self.target = target
        self.weight = weight

    def __repr__(self):
        return f"Edge({self.source} → {self.target}, w={self.weight})"
```

### 7.7 Combining `__slots__` with Properties and Descriptors

```python
class Temperature:
    __slots__ = ('_celsius',)

    def __init__(self, celsius):
        self.celsius = celsius  # uses the property setter

    @property
    def celsius(self):
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError("Temperature below absolute zero")
        self._celsius = value

    @property
    def fahrenheit(self):
        return self._celsius * 9/5 + 32

t = Temperature(100)
print(t.celsius)      # 100
print(t.fahrenheit)   # 212.0
```

### Practical Applications in LLD

- **Data-intensive systems:** Event stores, time-series data, graph algorithms.
- **Protocol buffers / serialization:** Fixed-schema message types.
- **Game engines:** Entity components (position, velocity, etc.).
- **Real-time systems:** Minimize GC pauses via fewer dict objects.

### Interview Relevance

- "What are `__slots__`?" → Replace `__dict__` with fixed-size storage.
- "When would you use them?" → Many instances, known attributes, performance-critical code.
- "What are the trade-offs?" → No dynamic attrs, inheritance complexity, no `__dict__`.

---

## 8. Descriptors

### 8.1 The Descriptor Protocol

A **descriptor** is any object that defines `__get__`, `__set__`, or `__delete__`. Descriptors are the machinery behind properties, methods, `classmethod`, `staticmethod`, and `super`.

```python
class Descriptor:
    """A minimal descriptor that logs access."""

    def __set_name__(self, owner, name):
        self.name = name
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self  # accessed on the class
        value = getattr(obj, self.private_name, None)
        print(f"Getting {self.name}: {value}")
        return value

    def __set__(self, obj, value):
        print(f"Setting {self.name} = {value}")
        setattr(obj, self.private_name, value)

    def __delete__(self, obj):
        print(f"Deleting {self.name}")
        delattr(obj, self.private_name)

class MyClass:
    attr = Descriptor()

    def __init__(self, value):
        self.attr = value  # triggers __set__

obj = MyClass(42)
# Setting attr = 42

print(obj.attr)
# Getting attr: 42
# 42

del obj.attr
# Deleting attr
```

### 8.2 Data Descriptors vs Non-Data Descriptors

The distinction is critical for understanding Python's attribute lookup:

| Type | Defines | Priority |
|---|---|---|
| **Data descriptor** | `__get__` + `__set__` (and/or `__delete__`) | Higher than instance `__dict__` |
| **Non-data descriptor** | `__get__` only | Lower than instance `__dict__` |

```python
class DataDescriptor:
    """Has both __get__ and __set__."""
    def __get__(self, obj, objtype=None):
        return "data_descriptor_value"
    def __set__(self, obj, value):
        pass  # ignore writes

class NonDataDescriptor:
    """Has only __get__."""
    def __get__(self, obj, objtype=None):
        return "non_data_descriptor_value"

class MyClass:
    data = DataDescriptor()
    nondata = NonDataDescriptor()

obj = MyClass()
obj.__dict__['data'] = "instance_value"
obj.__dict__['nondata'] = "instance_value"

print(obj.data)     # "data_descriptor_value" — data descriptor wins!
print(obj.nondata)  # "instance_value" — instance __dict__ wins!
```

**Attribute lookup order:**

```
obj.attr
  1. type(obj).__mro__ → find data descriptor (has __set__)?  → descriptor.__get__()
  2. obj.__dict__['attr'] exists?  → return it
  3. type(obj).__mro__ → find non-data descriptor (has only __get__)?  → descriptor.__get__()
  4. raise AttributeError
```

### 8.3 How Properties Work Internally

`property` is just a **data descriptor** implemented in C:

```python
# This is roughly what property does under the hood:
class Property:
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        self.__doc__ = doc or (fget.__doc__ if fget else None)

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError("unreadable attribute")
        return self.fget(obj)

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError("can't set attribute")
        self.fset(obj, value)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        self.fdel(obj)

    def getter(self, fget):
        return type(self)(fget, self.fset, self.fdel, self.__doc__)

    def setter(self, fset):
        return type(self)(self.fget, fset, self.fdel, self.__doc__)

    def deleter(self, fdel):
        return type(self)(self.fget, self.fset, fdel, self.__doc__)
```

### 8.4 How Methods Work Internally (Bound Methods)

Functions are **non-data descriptors**. When accessed on an instance, `__get__` creates a **bound method**:

```python
class Greeter:
    def hello(self, name):
        return f"Hello, {name}!"

# Functions are descriptors
print(type(Greeter.__dict__['hello']))   # <class 'function'>
print(hasattr(Greeter.__dict__['hello'], '__get__'))  # True

# Accessing via instance triggers __get__ → creates bound method
g = Greeter()
method = g.hello
print(type(method))        # <class 'method'>
print(method.__self__)     # <__main__.Greeter object at 0x...>
print(method.__func__)     # <function Greeter.hello at 0x...>

# This is what happens internally:
# g.hello → Greeter.__dict__['hello'].__get__(g, Greeter)
# → creates a bound method wrapping (hello_function, g)

# So calling g.hello("World") is equivalent to:
Greeter.hello(g, "World")
```

This is why `self` works — it's not magic syntax, it's the descriptor protocol binding the instance!

### 8.5 Custom Descriptors for Validation

```python
class Validated:
    """Base class for validated descriptors."""

    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.private_name, None)

    def __set__(self, obj, value):
        self.validate(value)
        setattr(obj, self.private_name, value)

    def validate(self, value):
        raise NotImplementedError

class PositiveNumber(Validated):
    def validate(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError(f"{self.public_name} must be a number, got {type(value).__name__}")
        if value <= 0:
            raise ValueError(f"{self.public_name} must be positive, got {value}")

class NonEmptyString(Validated):
    def __init__(self, max_length=None):
        self.max_length = max_length

    def validate(self, value):
        if not isinstance(value, str):
            raise TypeError(f"{self.public_name} must be a string")
        if not value.strip():
            raise ValueError(f"{self.public_name} cannot be empty")
        if self.max_length and len(value) > self.max_length:
            raise ValueError(f"{self.public_name} exceeds {self.max_length} chars")

class OneOf(Validated):
    def __init__(self, *options):
        self.options = set(options)

    def validate(self, value):
        if value not in self.options:
            raise ValueError(f"{self.public_name} must be one of {self.options}, got {value!r}")

# Usage in a domain model
class Product:
    name = NonEmptyString(max_length=100)
    price = PositiveNumber()
    category = OneOf("electronics", "clothing", "food", "books")

    def __init__(self, name, price, category):
        self.name = name
        self.price = price
        self.category = category

    def __repr__(self):
        return f"Product({self.name!r}, ${self.price}, {self.category})"

p = Product("Laptop", 999.99, "electronics")
print(p)  # Product('Laptop', $999.99, electronics)

try:
    p.price = -100  # ValueError: price must be positive
except ValueError as e:
    print(e)

try:
    p.category = "toys"  # ValueError: category must be one of...
except ValueError as e:
    print(e)
```

### 8.6 Lazy Properties (Computed Once)

```python
class LazyProperty:
    """
    A descriptor that computes a value on first access,
    then caches it in the instance __dict__.

    Because this is a non-data descriptor (no __set__),
    the cached value in __dict__ takes precedence on subsequent access.
    """

    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        value = self.func(obj)
        obj.__dict__[self.name] = value  # cache in instance dict
        return value

class DataAnalyzer:
    def __init__(self, data):
        self.data = data

    @LazyProperty
    def mean(self):
        """Computed only once, then cached."""
        print("Computing mean...")
        return sum(self.data) / len(self.data)

    @LazyProperty
    def variance(self):
        """Computed only once, then cached."""
        print("Computing variance...")
        m = self.mean
        return sum((x - m) ** 2 for x in self.data) / len(self.data)

    @LazyProperty
    def std_dev(self):
        print("Computing std_dev...")
        return self.variance ** 0.5

analyzer = DataAnalyzer([10, 20, 30, 40, 50])

print(analyzer.mean)      # Computing mean... → 30.0
print(analyzer.mean)      # 30.0 (no recomputation!)
print(analyzer.variance)  # Computing variance... → 200.0
print(analyzer.std_dev)   # Computing std_dev... → 14.14...
```

Note: Python 3.8+ has `functools.cached_property` which does the same thing.

### 8.7 Descriptor for Type Coercion

```python
class Coerce:
    """Descriptor that automatically coerces values to a target type."""

    def __init__(self, target_type, default=None):
        self.target_type = target_type
        self.default = default

    def __set_name__(self, owner, name):
        self.name = name
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.private_name, self.default)

    def __set__(self, obj, value):
        try:
            coerced = self.target_type(value)
        except (TypeError, ValueError) as e:
            raise TypeError(
                f"Cannot coerce {value!r} to {self.target_type.__name__} "
                f"for {self.name}"
            ) from e
        setattr(obj, self.private_name, coerced)

class Config:
    port = Coerce(int, default=8080)
    host = Coerce(str, default="localhost")
    debug = Coerce(bool, default=False)
    timeout = Coerce(float, default=30.0)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

config = Config(port="3000", host=127, debug=1, timeout="5.5")
print(config.port)     # 3000 (int)
print(config.host)     # "127" (str)
print(config.debug)    # True (bool)
print(config.timeout)  # 5.5 (float)
```

### Practical Applications in LLD

- **Validation layers:** Type-checked, range-validated attributes in domain models.
- **ORM fields:** Each column type is a descriptor (`CharField`, `IntegerField`).
- **Lazy computation:** Expensive computations cached on first access.
- **Access control:** Descriptors can implement read-only, write-once, or logged access.

### Interview Relevance

- "How do properties work?" → `property` is a data descriptor with `__get__`/`__set__`.
- "Why does `self` work in methods?" → Functions are non-data descriptors; `__get__` creates bound methods.
- "What's the difference between data and non-data descriptors?" → Data descriptors override instance `__dict__`.

### Common Misconceptions

| Misconception | Reality |
|---|---|
| Properties are special syntax | Properties are just descriptors |
| `@staticmethod` does nothing | It wraps the function to suppress binding |
| Descriptors only work for validation | They power methods, properties, classmethod, super, etc. |
| `obj.attr = val` always writes to `__dict__` | Data descriptors intercept assignment |

---

## 9. Metaclasses

### 9.1 What Is a Metaclass?

A **metaclass** is the class of a class. Just as objects are instances of classes, classes are instances of metaclasses.

```python
class Foo:
    pass

print(type(Foo))           # <class 'type'>
print(type(type))          # <class 'type'>
print(isinstance(Foo, type))  # True

# Creating a class is literally calling type():
Bar = type('Bar', (object,), {'x': 42, 'greet': lambda self: "hello"})
print(Bar.x)               # 42
print(Bar().greet())        # hello
```

The class creation process:

```
class Foo(Base, metaclass=Meta):
    attr = value

# Is equivalent to:
Foo = Meta('Foo', (Base,), {'attr': value})

# Which calls:
Meta.__new__(Meta, 'Foo', (Base,), {'attr': value})
Meta.__init__(Foo, 'Foo', (Base,), {'attr': value})
```

### 9.2 `type` as the Default Metaclass

`type` serves double duty:

1. **As a function:** `type(obj)` returns the type of `obj`.
2. **As a metaclass:** `type(name, bases, dict)` creates a new class.

```python
# These are equivalent:
class MyClass:
    x = 10
    def method(self):
        return self.x

MyClass2 = type('MyClass2', (), {'x': 10, 'method': lambda self: self.x})

print(MyClass().method())   # 10
print(MyClass2().method())  # 10
```

### 9.3 Writing a Custom Metaclass

```python
class Meta(type):
    def __new__(mcs, name, bases, namespace):
        print(f"Meta.__new__: Creating class {name}")
        print(f"  Bases: {bases}")
        print(f"  Namespace keys: {list(namespace.keys())}")

        cls = super().__new__(mcs, name, bases, namespace)
        return cls

    def __init__(cls, name, bases, namespace):
        print(f"Meta.__init__: Initializing class {name}")
        super().__init__(name, bases, namespace)

    def __call__(cls, *args, **kwargs):
        print(f"Meta.__call__: Creating instance of {cls.__name__}")
        instance = super().__call__(*args, **kwargs)
        return instance

class MyClass(metaclass=Meta):
    def __init__(self, value):
        self.value = value

# Output during class creation:
# Meta.__new__: Creating class MyClass
#   Bases: ()
#   Namespace keys: ['__module__', '__qualname__', '__init__']
# Meta.__init__: Initializing class MyClass

obj = MyClass(42)
# Output: Meta.__call__: Creating instance of MyClass
```

### 9.4 `__init_subclass__` — The Simpler Alternative

Python 3.6+ added `__init_subclass__` as a lighter-weight alternative to metaclasses:

```python
class Plugin:
    _registry = {}

    def __init_subclass__(cls, plugin_name=None, **kwargs):
        super().__init_subclass__(**kwargs)
        name = plugin_name or cls.__name__.lower()
        Plugin._registry[name] = cls
        print(f"Registered plugin: {name}")

    @classmethod
    def get_plugin(cls, name):
        return cls._registry.get(name)

class JSONPlugin(Plugin, plugin_name="json"):
    def process(self, data):
        return f"Processing JSON: {data}"

class XMLPlugin(Plugin, plugin_name="xml"):
    def process(self, data):
        return f"Processing XML: {data}"

# Registered automatically!
print(Plugin._registry)
# {'json': <class 'JSONPlugin'>, 'xml': <class 'XMLPlugin'>}

plugin = Plugin.get_plugin("json")()
print(plugin.process("data"))  # Processing JSON: data
```

### 9.5 Real Use Cases

#### Automatic API Registration

```python
class APIMeta(type):
    """Metaclass that auto-registers API endpoints."""

    _endpoints = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)

        if bases:  # skip the base class itself
            for attr_name, attr_value in namespace.items():
                if callable(attr_value) and hasattr(attr_value, '_route'):
                    route = attr_value._route
                    method = attr_value._method
                    APIMeta._endpoints[(method, route)] = (cls, attr_name)

        return cls

    @classmethod
    def list_endpoints(mcs):
        for (method, route), (cls, handler) in mcs._endpoints.items():
            print(f"  {method:6s} {route:20s} → {cls.__name__}.{handler}")

def route(path, method="GET"):
    def decorator(func):
        func._route = path
        func._method = method
        return func
    return decorator

class APIHandler(metaclass=APIMeta):
    pass

class UserAPI(APIHandler):
    @route("/users", "GET")
    def list_users(self):
        return [{"name": "Alice"}, {"name": "Bob"}]

    @route("/users", "POST")
    def create_user(self, data):
        return {"created": data}

    @route("/users/{id}", "GET")
    def get_user(self, id):
        return {"id": id, "name": "Alice"}

class ProductAPI(APIHandler):
    @route("/products", "GET")
    def list_products(self):
        return []

    @route("/products", "POST")
    def create_product(self, data):
        return {"created": data}

APIMeta.list_endpoints()
# GET    /users                → UserAPI.list_users
# POST   /users                → UserAPI.create_user
# GET    /users/{id}           → UserAPI.get_user
# GET    /products             → ProductAPI.list_products
# POST   /products             → ProductAPI.create_product
```

#### Attribute Validation Metaclass

```python
class ValidatedMeta(type):
    """Metaclass that enforces type annotations at __init__ time."""

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)

        annotations = namespace.get('__annotations__', {})
        if annotations and '__init__' not in namespace:
            # Auto-generate __init__ from annotations
            def make_init(annotations):
                def __init__(self, **kwargs):
                    for attr, expected_type in annotations.items():
                        if attr not in kwargs:
                            raise TypeError(f"Missing required argument: {attr}")
                        value = kwargs[attr]
                        if not isinstance(value, expected_type):
                            raise TypeError(
                                f"{attr} must be {expected_type.__name__}, "
                                f"got {type(value).__name__}"
                            )
                        setattr(self, attr, value)
                return __init__

            cls.__init__ = make_init(annotations)

        return cls

class User(metaclass=ValidatedMeta):
    name: str
    age: int
    email: str

user = User(name="Alice", age=30, email="alice@example.com")
print(user.name)   # Alice

try:
    User(name="Bob", age="thirty", email="bob@example.com")
except TypeError as e:
    print(e)  # age must be int, got str
```

#### Building a Simple ORM with Metaclasses

```python
class Field:
    """Base field descriptor for ORM columns."""

    def __init__(self, column_type, primary_key=False, nullable=False, default=None):
        self.column_type = column_type
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(self.name, self.default)

    def __set__(self, obj, value):
        if value is None and not self.nullable:
            raise ValueError(f"{self.name} cannot be None")
        obj.__dict__[self.name] = value

class IntegerField(Field):
    def __init__(self, **kwargs):
        super().__init__("INTEGER", **kwargs)

    def __set__(self, obj, value):
        if value is not None and not isinstance(value, int):
            raise TypeError(f"{self.name} must be int, got {type(value).__name__}")
        super().__set__(obj, value)

class StringField(Field):
    def __init__(self, max_length=255, **kwargs):
        super().__init__(f"VARCHAR({max_length})", **kwargs)
        self.max_length = max_length

    def __set__(self, obj, value):
        if value is not None:
            if not isinstance(value, str):
                raise TypeError(f"{self.name} must be str")
            if len(value) > self.max_length:
                raise ValueError(f"{self.name} exceeds max length {self.max_length}")
        super().__set__(obj, value)

class ModelMeta(type):
    """Metaclass for ORM models."""

    def __new__(mcs, name, bases, namespace):
        fields = {}
        for key, value in namespace.items():
            if isinstance(value, Field):
                fields[key] = value

        namespace['_fields'] = fields
        namespace['_table_name'] = namespace.get('_table_name', name.lower() + 's')

        cls = super().__new__(mcs, name, bases, namespace)
        return cls

    def create_table_sql(cls):
        columns = []
        for name, field in cls._fields.items():
            col = f"    {name} {field.column_type}"
            if field.primary_key:
                col += " PRIMARY KEY"
            if not field.nullable:
                col += " NOT NULL"
            columns.append(col)
        return f"CREATE TABLE {cls._table_name} (\n" + ",\n".join(columns) + "\n);"

    def insert_sql(cls, instance):
        names = []
        values = []
        for name, field in cls._fields.items():
            val = getattr(instance, name)
            if val is not None:
                names.append(name)
                values.append(repr(val))
        return (
            f"INSERT INTO {cls._table_name} ({', '.join(names)}) "
            f"VALUES ({', '.join(values)});"
        )

class Model(metaclass=ModelMeta):
    def __init__(self, **kwargs):
        for name, field in self._fields.items():
            value = kwargs.get(name, field.default)
            setattr(self, name, value)

    def __repr__(self):
        attrs = ", ".join(f"{n}={getattr(self, n)!r}" for n in self._fields)
        return f"{type(self).__name__}({attrs})"

# Define models
class User(Model):
    id = IntegerField(primary_key=True)
    name = StringField(max_length=100)
    email = StringField(max_length=255)
    age = IntegerField(nullable=True)

class Post(Model):
    id = IntegerField(primary_key=True)
    title = StringField(max_length=200)
    author_id = IntegerField()

# Usage
print(User.create_table_sql())
# CREATE TABLE users (
#     id INTEGER PRIMARY KEY NOT NULL,
#     name VARCHAR(100) NOT NULL,
#     email VARCHAR(255) NOT NULL,
#     age INTEGER
# );

user = User(id=1, name="Alice", email="alice@example.com", age=30)
print(user)  # User(id=1, name='Alice', email='alice@example.com', age=30)
print(User.insert_sql(user))
# INSERT INTO users (id, name, email, age) VALUES (1, 'Alice', 'alice@example.com', 30);

print(Post.create_table_sql())
# CREATE TABLE posts (
#     id INTEGER PRIMARY KEY NOT NULL,
#     title VARCHAR(200) NOT NULL,
#     author_id INTEGER NOT NULL
# );
```

### 9.6 `__prepare__` — Controlling the Namespace

```python
from collections import OrderedDict

class OrderedMeta(type):
    @classmethod
    def __prepare__(mcs, name, bases):
        return OrderedDict()

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, dict(namespace))
        cls._field_order = [
            key for key in namespace
            if not key.startswith('_') and not callable(namespace.get(key))
        ]
        return cls

class Schema(metaclass=OrderedMeta):
    name = "string"
    age = "integer"
    email = "string"
    active = "boolean"

print(Schema._field_order)
# ['name', 'age', 'email', 'active'] — order preserved!
```

Note: Since Python 3.7+, regular dicts are insertion-ordered, so `__prepare__` is less critical for ordering. But it's still useful for custom namespace behaviors (e.g., preventing duplicate definitions).

### 9.7 When to Avoid Metaclasses

Metaclasses are powerful but complex. Prefer simpler alternatives when possible:

```
Complexity scale (prefer left):

  decorators  <  __init_subclass__  <  metaclasses

Use decorators when: you need to modify a single class
Use __init_subclass__ when: you need to hook into subclass creation
Use metaclasses when: you need to control class creation itself (namespace, MRO, etc.)
```

```python
# Often a class decorator is enough:
_registry = {}

def register(cls):
    _registry[cls.__name__] = cls
    return cls

@register
class Handler:
    pass

@register
class Processor:
    pass

print(_registry)  # {'Handler': <class 'Handler'>, 'Processor': <class 'Processor'>}
```

### Practical Applications in LLD

- **ORM frameworks:** Django/SQLAlchemy use metaclasses for model definitions.
- **Plugin systems:** Auto-registration of handlers, serializers, etc.
- **API frameworks:** Automatic endpoint discovery and routing.
- **Validation:** Enforce contracts on class definitions.
- **Abstract interfaces:** `ABCMeta` prevents instantiation of incomplete implementations.

### Interview Relevance

- "What is a metaclass?" → A class whose instances are classes; `type` is the default.
- "When would you use a metaclass?" → ORM, validation, registration, API frameworks.
- "What's the difference between `__init_subclass__` and a metaclass?" → `__init_subclass__` is simpler, runs after class creation; metaclasses control the creation process.

### Common Misconceptions

| Misconception | Reality |
|---|---|
| Metaclasses are needed for class customization | Decorators or `__init_subclass__` usually suffice |
| `__init_subclass__` replaces metaclasses entirely | Metaclasses can do more (custom namespace, MRO control) |
| Only one metaclass per class | True, but it must be a subclass of all base metaclasses |
| Metaclasses are slow | Overhead is at class creation (once), not instance creation |

---

## 10. Import System Internals

### 10.1 How Import Works Step by Step

When Python encounters `import foo`, here's the full process:

```
import foo
  │
  ├─ 1. Check sys.modules (cache)
  │     └─ if found → return it, done
  │
  ├─ 2. Find the module (finders)
  │     ├─ sys.meta_path[0]: BuiltinImporter (built-in modules: sys, os)
  │     ├─ sys.meta_path[1]: FrozenImporter (frozen modules)
  │     └─ sys.meta_path[2]: PathFinder (file-based modules)
  │           └─ searches sys.path entries
  │               ├─ check for package (directory with __init__.py)
  │               └─ check for module (foo.py, foo.so, foo.pyc)
  │
  ├─ 3. Load the module (loaders)
  │     ├─ Create a new module object
  │     ├─ Add to sys.modules BEFORE executing (prevents infinite recursion)
  │     ├─ Execute the module code
  │     └─ Return the module
  │
  └─ 4. Bind the name in the importing namespace
```

```python
import sys

# The module cache
print(list(sys.modules.keys())[:10])
# ['sys', 'builtins', '_frozen_importlib', ...]

# The finder chain
print(sys.meta_path)
# [<class '_frozen_importlib.BuiltinImporter'>,
#  <class '_frozen_importlib.FrozenImporter'>,
#  <class '_frozen_importlib_external.PathFinder'>]

# The search path
print(sys.path[:5])
# ['', '/usr/lib/python312.zip', '/usr/lib/python3.12', ...]
```

### 10.2 sys.modules Cache

`sys.modules` is a dict that caches all imported modules:

```python
import sys

# Modules are cached after first import
import json
print('json' in sys.modules)  # True

# You can "unimport" by removing from cache (not recommended in production)
del sys.modules['json']
import json  # re-imports from scratch

# You can inject fake modules
import types

fake = types.ModuleType('fake_module')
fake.value = 42
sys.modules['fake_module'] = fake

import fake_module
print(fake_module.value)  # 42

# Pre-population prevents file-based import
sys.modules['nonexistent'] = types.ModuleType('nonexistent')
import nonexistent  # no ImportError — it's in the cache!
```

### 10.3 Finders and Loaders

The import system uses a **finder → loader** chain:

```python
import importlib
import importlib.abc

class DebugFinder(importlib.abc.MetaPathFinder):
    """A finder that logs import attempts."""

    def find_module(self, fullname, path=None):
        print(f"[DebugFinder] Looking for: {fullname}")
        print(f"  Path: {path}")
        return None  # we don't handle anything — just log

# Install our finder at the front
import sys
sys.meta_path.insert(0, DebugFinder())

import collections  # triggers logging
# [DebugFinder] Looking for: collections
#   Path: None

sys.meta_path.remove(sys.meta_path[0])  # clean up
```

### 10.4 importlib — Programmatic Imports

```python
import importlib

# Dynamic import by name
json_mod = importlib.import_module('json')
print(json_mod.dumps([1, 2, 3]))  # [1, 2, 3]

# Relative imports
# importlib.import_module('.utils', package='mypackage')

# Reloading a module (re-executes it)
import my_module  # hypothetical
importlib.reload(my_module)  # re-reads and re-executes

# Getting module spec (metadata without importing)
spec = importlib.util.find_spec('json')
print(spec)
# ModuleSpec(name='json', loader=<_frozen_importlib_external.SourceFileLoader>,
#            origin='/usr/lib/python3.12/json/__init__.py')
print(spec.origin)        # file path
print(spec.submodule_search_locations)  # package paths
```

### 10.5 Circular Imports and How to Fix Them

Circular imports are a common problem:

```python
# ---- module_a.py ----
from module_b import func_b  # tries to import module_b

def func_a():
    return "A" + func_b()

# ---- module_b.py ----
from module_a import func_a  # tries to import module_a → circular!

def func_b():
    return "B" + func_a()

# ImportError: cannot import name 'func_a' from partially initialized module
```

**Why it happens:**

1. Python starts importing `module_a`.
2. `module_a` is added to `sys.modules` (partially initialized).
3. `module_a` hits `from module_b import func_b`.
4. Python starts importing `module_b`.
5. `module_b` hits `from module_a import func_a`.
6. Python finds `module_a` in `sys.modules` but `func_a` isn't defined yet!

**Fix 1: Import at the top level, use qualified names**

```python
# ---- module_a.py ----
import module_b

def func_a():
    return "A" + module_b.func_b()

# ---- module_b.py ----
import module_a

def func_b():
    return "B" + module_a.func_a()
```

**Fix 2: Move import inside the function (lazy)**

```python
# ---- module_a.py ----
def func_a():
    from module_b import func_b
    return "A" + func_b()
```

**Fix 3: Restructure — extract shared code**

```python
# ---- shared.py ----
def func_a():
    return "A"

def func_b():
    return "B"

# ---- module_a.py ----
from shared import func_a, func_b
```

### 10.6 Lazy Imports

Lazy imports delay module loading until first use:

```python
class LazyModule:
    """A proxy that imports the module on first attribute access."""

    def __init__(self, module_name):
        self._module_name = module_name
        self._module = None

    def _load(self):
        if self._module is None:
            import importlib
            self._module = importlib.import_module(self._module_name)
        return self._module

    def __getattr__(self, name):
        return getattr(self._load(), name)

# Usage — module isn't imported until first use
numpy = LazyModule('numpy')
# ... much later, only if needed:
# arr = numpy.array([1, 2, 3])  # imports numpy here
```

Python 3.12+ has a standard way: PEP 690 proposed lazy imports, and tools like `importlib.util.LazyLoader` exist:

```python
import importlib.util

def lazy_import(name):
    spec = importlib.util.find_spec(name)
    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[name] = module
    loader.exec_module(module)
    return module

json = lazy_import('json')  # not yet loaded
print(json.dumps([1, 2]))   # loaded on first access: [1, 2]
```

### 10.7 Import Hooks — Custom Importers

You can intercept and customize the import process:

```python
import sys
import importlib.abc
import importlib.util
import types

class DictImporter(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """
    An importer that loads modules from a dictionary of source code.

    Useful for:
    - Loading code from databases
    - Loading code from network
    - Sandboxed execution
    """

    def __init__(self):
        self._modules = {}

    def register(self, name, source):
        self._modules[name] = source

    def find_module(self, fullname, path=None):
        if fullname in self._modules:
            return self
        return None

    def create_module(self, spec):
        return None  # use default module creation

    def exec_module(self, module):
        source = self._modules[module.__name__]
        code = compile(source, f"<dict:{module.__name__}>", "exec")
        exec(code, module.__dict__)

    def find_spec(self, fullname, path, target=None):
        if fullname in self._modules:
            return importlib.util.spec_from_loader(fullname, self)
        return None

# Usage
importer = DictImporter()
importer.register("greetings", """
def hello(name):
    return f"Hello, {name}!"

def goodbye(name):
    return f"Goodbye, {name}!"

GREETING_COUNT = 2
""")

sys.meta_path.insert(0, importer)

import greetings
print(greetings.hello("World"))      # Hello, World!
print(greetings.goodbye("World"))    # Goodbye, World!
print(greetings.GREETING_COUNT)      # 2

sys.meta_path.remove(importer)
```

#### Import Hook: Auto-installing Missing Packages

```python
import sys
import subprocess
import importlib

class AutoInstaller(importlib.abc.MetaPathFinder):
    """
    Automatically pip-installs missing packages on import.

    WARNING: This is for development/prototyping only!
    Never use this in production.
    """

    def find_module(self, fullname, path=None):
        if fullname in sys.modules:
            return None

        try:
            importlib.util.find_spec(fullname)
        except (ModuleNotFoundError, ValueError):
            print(f"[AutoInstaller] Installing {fullname}...")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", fullname],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        return None  # let the normal import machinery take over

# sys.meta_path.append(AutoInstaller())
# import some_package  # auto-installed if missing!
```

### 10.8 Package __init__.py and __all__

```python
# mypackage/__init__.py
print(f"Initializing package {__name__}")

# Control what 'from mypackage import *' exports
__all__ = ['module_a', 'public_func']

def public_func():
    return "I'm public"

def _private_func():
    return "I'm private"

# Lazy submodule access
def __getattr__(name):
    if name == "heavy_module":
        import importlib
        return importlib.import_module(f".heavy_module", __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

### Practical Applications in LLD

- **Plugin architectures:** Custom importers load plugins from databases or ZIP files.
- **Microservices:** Lazy imports reduce startup time.
- **Testing:** `sys.modules` manipulation for mocking.
- **Dependency injection:** Dynamic imports based on configuration.

### Interview Relevance

- "How does Python's import system work?" → Finders, loaders, `sys.modules` cache.
- "How do you fix circular imports?" → Lazy import, restructuring, qualified names.
- "What is `sys.path`?" → List of directories/ZIP files Python searches for modules.

### Common Misconceptions

| Misconception | Reality |
|---|---|
| `import` reads the file every time | Cached in `sys.modules` after first import |
| Circular imports are impossible | They work with `import module` (not `from module import name`) |
| `__init__.py` is required for packages | Since 3.3, namespace packages work without it |
| Relative imports work from scripts | Only from within packages; scripts use absolute imports |

---

## 11. Monkey Patching

### 11.1 What Is Monkey Patching?

**Monkey patching** is dynamically modifying classes, modules, or objects at runtime — replacing or adding methods/attributes after they've been defined.

```python
class Calculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b

calc = Calculator()
print(calc.add(2, 3))       # 5
print(calc.multiply(2, 3))  # 6

# Monkey patch: add a new method
def subtract(self, a, b):
    return a - b

Calculator.subtract = subtract
print(calc.subtract(10, 4))  # 6 — works on existing instances!

# Monkey patch: replace an existing method
original_add = Calculator.add

def logging_add(self, a, b):
    result = original_add(self, a, b)
    print(f"add({a}, {b}) = {result}")
    return result

Calculator.add = logging_add
calc.add(2, 3)  # add(2, 3) = 5
```

### 11.2 How It Works

Monkey patching works because Python looks up methods at call time, not definition time:

```python
class Dog:
    def speak(self):
        return "Woof!"

d = Dog()
print(d.speak())  # Woof!

# Python resolves d.speak() as: type(d).__dict__['speak'].__get__(d, type(d))
# Changing the class dict changes what all instances see

Dog.speak = lambda self: "Bark!"
print(d.speak())  # Bark! — same instance, different behavior
```

**Patching modules:**

```python
import time

# Patch time.time to return a fixed value
original_time = time.time
time.time = lambda: 1000000.0
print(time.time())    # 1000000.0

time.time = original_time  # restore
```

**Patching instances (not the class):**

```python
import types

class Greeter:
    def greet(self):
        return "Hello!"

g = Greeter()

def custom_greet(self):
    return "Hey there!"

g.greet = types.MethodType(custom_greet, g)
print(g.greet())         # Hey there!

g2 = Greeter()
print(g2.greet())        # Hello! — other instances unaffected
```

### 11.3 When Monkey Patching Is Appropriate

#### Testing — The Primary Legitimate Use

```python
import unittest
from unittest.mock import patch, MagicMock

class PaymentService:
    def charge(self, amount, card_token):
        # In production, calls Stripe/PayPal API
        import stripe
        return stripe.Charge.create(amount=amount, source=card_token)

class OrderService:
    def __init__(self):
        self.payment = PaymentService()

    def place_order(self, items, card_token):
        total = sum(item['price'] for item in items)
        charge = self.payment.charge(total, card_token)
        return {"order_id": "ORD-001", "charge_id": charge.id, "total": total}

class TestOrderService(unittest.TestCase):
    @patch.object(PaymentService, 'charge')
    def test_place_order(self, mock_charge):
        mock_charge.return_value = MagicMock(id="ch_test_123")

        service = OrderService()
        result = service.place_order(
            [{"name": "Widget", "price": 10}, {"name": "Gadget", "price": 20}],
            "tok_test"
        )

        self.assertEqual(result['total'], 30)
        self.assertEqual(result['charge_id'], "ch_test_123")
        mock_charge.assert_called_once_with(30, "tok_test")
```

#### Hotfixes — Emergency Production Patches

```python
def apply_hotfix():
    """
    Emergency patch for a bug in a third-party library.

    Apply this until the library releases a fix.
    """
    import third_party_lib

    original_process = third_party_lib.DataProcessor.process

    def patched_process(self, data):
        if data is None:
            return []  # the bug: original crashes on None input
        return original_process(self, data)

    third_party_lib.DataProcessor.process = patched_process
    print("[HOTFIX] Patched DataProcessor.process for None handling")

# apply_hotfix()  # call at application startup
```

#### Instrumentation and Monitoring

```python
import time
import functools

def instrument_class(cls, metrics_collector=None):
    """Add timing instrumentation to all public methods of a class."""
    for name in list(vars(cls)):
        if name.startswith('_'):
            continue
        method = getattr(cls, name)
        if not callable(method):
            continue

        original = method

        @functools.wraps(original)
        def timed_method(*args, _original=original, _name=name, **kwargs):
            start = time.perf_counter()
            try:
                return _original(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                print(f"[METRIC] {cls.__name__}.{_name}: {elapsed:.4f}s")

        setattr(cls, name, timed_method)

class DatabaseService:
    def query(self, sql):
        time.sleep(0.1)
        return [{"id": 1}]

    def insert(self, table, data):
        time.sleep(0.05)
        return True

instrument_class(DatabaseService)
db = DatabaseService()
db.query("SELECT * FROM users")   # [METRIC] DatabaseService.query: 0.1003s
db.insert("users", {"name": "A"}) # [METRIC] DatabaseService.insert: 0.0502s
```

### 11.4 Dangers and Risks

```python
# 1. Breaking encapsulation — patching internals you don't own
import json

# BAD: patching internal implementation details
# json._default_decoder = ...  # will break with version updates

# 2. Invisible side effects — code that reads differently than it behaves
class UserService:
    def get_user(self, id):
        return {"id": id, "name": "Alice"}

# Somewhere else in the codebase, someone patches it:
UserService.get_user = lambda self, id: {"id": id, "name": "REDACTED"}
# Now anyone reading UserService.get_user is deceived

# 3. Order dependency — patches must be applied in the right order
# If module A patches X, and module B patches X, order matters!

# 4. Concurrency issues — patches are not thread-safe
import threading

# This is a race condition:
def patch_in_thread():
    import some_module
    some_module.func = new_func  # other threads see partial state
```

### 11.5 `unittest.mock.patch` — Controlled Monkey Patching

`mock.patch` is the right way to monkey patch in tests — it automatically restores:

```python
from unittest.mock import patch, MagicMock, PropertyMock
import datetime

class WeatherService:
    def get_temperature(self, city):
        # Would call a real API
        raise NotImplementedError("Call weather API")

    @property
    def is_configured(self):
        return bool(self.api_key)

class WeatherApp:
    def __init__(self, service):
        self.service = service

    def should_wear_jacket(self, city):
        temp = self.service.get_temperature(city)
        return temp < 15

# Patch as context manager (auto-restores)
def test_jacket_recommendation():
    service = WeatherService()
    app = WeatherApp(service)

    with patch.object(service, 'get_temperature', return_value=10):
        assert app.should_wear_jacket("London") is True

    with patch.object(service, 'get_temperature', return_value=25):
        assert app.should_wear_jacket("Miami") is False

    print("All tests passed!")

test_jacket_recommendation()

# Patch as decorator
from unittest.mock import patch

class TestWeatherApp:
    @patch('datetime.datetime')
    def test_with_frozen_time(self, mock_dt):
        mock_dt.now.return_value = datetime.datetime(2024, 1, 15, 12, 0)
        now = datetime.datetime.now()
        assert now.month == 1

# Patch with side_effect for sequential returns
def test_retries():
    service = WeatherService()

    with patch.object(
        service, 'get_temperature',
        side_effect=[ConnectionError, ConnectionError, 20]
    ):
        for attempt in range(3):
            try:
                temp = service.get_temperature("NYC")
                print(f"Success on attempt {attempt + 1}: {temp}°C")
                break
            except ConnectionError:
                print(f"Attempt {attempt + 1} failed, retrying...")

test_retries()
# Attempt 1 failed, retrying...
# Attempt 2 failed, retrying...
# Success on attempt 3: 20°C
```

### 11.6 Feature Flags with Monkey Patching

```python
class FeatureFlags:
    """
    Runtime feature flag system using controlled monkey patching.

    In LLD interviews, this pattern appears in:
    - A/B testing systems
    - Gradual rollouts
    - Feature toggles
    """

    _flags = {}
    _patches = {}

    @classmethod
    def register(cls, flag_name, target_class, method_name, new_implementation):
        cls._flags[flag_name] = {
            'target_class': target_class,
            'method_name': method_name,
            'new_implementation': new_implementation,
            'original': getattr(target_class, method_name),
            'enabled': False,
        }

    @classmethod
    def enable(cls, flag_name):
        flag = cls._flags[flag_name]
        if not flag['enabled']:
            setattr(flag['target_class'], flag['method_name'], flag['new_implementation'])
            flag['enabled'] = True
            print(f"[FeatureFlag] Enabled: {flag_name}")

    @classmethod
    def disable(cls, flag_name):
        flag = cls._flags[flag_name]
        if flag['enabled']:
            setattr(flag['target_class'], flag['method_name'], flag['original'])
            flag['enabled'] = False
            print(f"[FeatureFlag] Disabled: {flag_name}")

    @classmethod
    def is_enabled(cls, flag_name):
        return cls._flags.get(flag_name, {}).get('enabled', False)

# Search service with feature flags
class SearchService:
    def search(self, query):
        return [f"Result for '{query}' (basic search)"]

def enhanced_search(self, query):
    return [
        f"Result for '{query}' (enhanced)",
        f"Related: '{query} tutorial'",
        f"Related: '{query} examples'",
    ]

FeatureFlags.register("enhanced_search", SearchService, "search", enhanced_search)

svc = SearchService()
print(svc.search("python"))
# ['Result for \'python\' (basic search)']

FeatureFlags.enable("enhanced_search")
print(svc.search("python"))
# ['Result for \'python\' (enhanced)', ...]

FeatureFlags.disable("enhanced_search")
print(svc.search("python"))
# ['Result for \'python\' (basic search)']
```

### 11.7 Safe Monkey Patching Pattern

```python
import functools

class MonkeyPatch:
    """
    A context manager for safe, reversible monkey patching.

    Automatically restores the original implementation on exit.
    """

    def __init__(self):
        self._patches = []

    def setattr(self, target, name, value):
        """Patch an attribute, remembering the original."""
        original = getattr(target, name, _MISSING)
        self._patches.append((target, name, original))
        setattr(target, name, value)

    def undo(self):
        """Undo all patches in reverse order."""
        while self._patches:
            target, name, original = self._patches.pop()
            if original is _MISSING:
                delattr(target, name)
            else:
                setattr(target, name, original)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.undo()

_MISSING = object()

# Usage
class EmailService:
    def send(self, to, subject, body):
        print(f"Sending email to {to}: {subject}")
        return True

with MonkeyPatch() as mp:
    sent_emails = []

    def mock_send(self, to, subject, body):
        sent_emails.append({"to": to, "subject": subject, "body": body})
        return True

    mp.setattr(EmailService, 'send', mock_send)

    svc = EmailService()
    svc.send("alice@example.com", "Test", "Hello!")
    print(f"Captured: {sent_emails}")
    # Captured: [{'to': 'alice@example.com', 'subject': 'Test', 'body': 'Hello!'}]

# After the context manager, original behavior is restored
svc2 = EmailService()
svc2.send("bob@example.com", "Real", "Hi!")
# Sending email to bob@example.com: Real
```

### Practical Applications in LLD

- **Testing:** Isolate units by patching dependencies (databases, APIs, time).
- **Feature flags:** Toggle behavior at runtime without code changes.
- **Hotfixes:** Emergency patches for third-party library bugs.
- **Instrumentation:** Add logging/metrics without modifying source code.
- **A/B testing:** Swap implementations for different user cohorts.

### Interview Relevance

- "What is monkey patching?" → Modifying classes/modules at runtime.
- "When is it appropriate?" → Testing, hotfixes, instrumentation.
- "What are the risks?" → Hard to debug, invisible side effects, order dependency, not thread-safe.
- "How does `unittest.mock.patch` work?" → Controlled monkey patching with automatic restoration.

### Common Misconceptions

| Misconception | Reality |
|---|---|
| Monkey patching is always bad | It's essential for testing; `mock.patch` is monkey patching |
| Patches only affect new instances | Class-level patches affect all instances (existing and new) |
| Patches are thread-safe | They're not — races are possible in multi-threaded code |
| You can patch anything | Some C extension types resist patching (immutable type objects) |

---

## Appendix A: Quick Reference — Key Modules

| Module | Purpose | Section |
|---|---|---|
| `dis` | Disassemble bytecode | §2 |
| `ast` | Parse/manipulate AST | §1 |
| `sys` | System-level introspection (`_getframe`, `getrefcount`, `getsizeof`) | §1-5 |
| `gc` | Garbage collector control | §1 |
| `weakref` | Weak references | §6 |
| `tracemalloc` | Memory allocation tracking | §5 |
| `importlib` | Programmatic imports, hooks | §10 |
| `tokenize` | Source code tokenization | §1 |
| `marshal` | Internal serialization (code objects) | §2 |
| `types` | Dynamic type creation | §3, 11 |
| `inspect` | Runtime introspection | §3 |
| `unittest.mock` | Controlled monkey patching | §11 |

## Appendix B: Interview Quick-Fire Answers

| Question | Answer |
|---|---|
| Is Python compiled or interpreted? | Both — compiled to bytecode, then interpreted by the PVM |
| How does GC work? | Reference counting (primary) + cyclic GC (for cycles) |
| What is `__slots__`? | Replaces `__dict__` with fixed-size storage; saves memory |
| What is a descriptor? | Object with `__get__`/`__set__`/`__delete__`; powers properties and methods |
| What is a metaclass? | A class whose instances are classes; `type` is the default |
| How does `super()` work? | Follows the MRO (C3 linearization), not just the parent |
| Why are local variables faster? | `LOAD_FAST` (array index) vs `LOAD_GLOBAL` (dict lookup) |
| What's a `.pyc` file? | Cached bytecode; skips tokenization and parsing |
| What's a weak reference? | A reference that doesn't prevent garbage collection |
| What is monkey patching? | Modifying classes/modules at runtime |
| How do imports work? | Finders → Loaders → `sys.modules` cache |
| What's a code object? | Immutable container for compiled bytecode + metadata |
| What's a frame object? | Execution context for a function call |
| Why does `self` work? | Functions are non-data descriptors; `__get__` creates bound methods |
| What's MRO? | Method Resolution Order — the linearized class hierarchy |

## Appendix C: Putting It All Together — A Complete Example

Here's a mini-framework that uses most of the concepts from this tutorial:

```python
"""
A tiny ORM framework demonstrating:
- Metaclasses (ModelMeta)
- Descriptors (Field subclasses)
- __slots__ (Field storage)
- Weak references (identity map cache)
- Import hooks (auto-discovery)
- The object model (__new__, __init__, MRO)
"""

import weakref
from collections import OrderedDict

# --- Descriptors (§8) ---

class Field:
    __slots__ = ('name', 'column_type', 'primary_key', 'nullable', 'default')

    def __init__(self, column_type, primary_key=False, nullable=False, default=None):
        self.column_type = column_type
        self.primary_key = primary_key
        self.nullable = nullable
        self.default = default

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj._data.get(self.name, self.default)

    def __set__(self, obj, value):
        self.validate(value)
        obj._data[self.name] = value
        obj._dirty.add(self.name)

    def validate(self, value):
        if value is None and not self.nullable:
            raise ValueError(f"{self.name} cannot be None")

class IntField(Field):
    def __init__(self, **kw):
        super().__init__("INTEGER", **kw)

    def validate(self, value):
        super().validate(value)
        if value is not None and not isinstance(value, int):
            raise TypeError(f"{self.name}: expected int, got {type(value).__name__}")

class StrField(Field):
    __slots__ = ('max_length',)

    def __init__(self, max_length=255, **kw):
        super().__init__(f"VARCHAR({max_length})", **kw)
        self.max_length = max_length

    def validate(self, value):
        super().validate(value)
        if value is not None:
            if not isinstance(value, str):
                raise TypeError(f"{self.name}: expected str, got {type(value).__name__}")
            if len(value) > self.max_length:
                raise ValueError(f"{self.name}: max length {self.max_length}, got {len(value)}")

# --- Metaclass (§9) ---

class ModelMeta(type):
    _models = OrderedDict()

    def __new__(mcs, name, bases, namespace):
        fields = OrderedDict()
        for key, val in namespace.items():
            if isinstance(val, Field):
                fields[key] = val

        namespace['_fields'] = fields
        namespace['_table'] = name.lower() + 's'

        cls = super().__new__(mcs, name, bases, namespace)

        if bases:
            mcs._models[name] = cls

        return cls

# --- Identity Map with Weak References (§6) ---

class IdentityMap:
    """Caches loaded objects so the same DB row always maps to the same Python object."""

    def __init__(self):
        self._cache = weakref.WeakValueDictionary()

    def get(self, cls, pk):
        return self._cache.get((cls.__name__, pk))

    def put(self, obj):
        pk_field = next(
            (f for f in type(obj)._fields.values() if f.primary_key), None
        )
        if pk_field:
            pk = getattr(obj, pk_field.name)
            self._cache[(type(obj).__name__, pk)] = obj

    def __len__(self):
        return len(self._cache)

# --- Base Model (§4 Object Model — __new__, __init__) ---

class Model(metaclass=ModelMeta):
    _identity_map = IdentityMap()

    def __new__(cls, **kwargs):
        pk_field = next(
            (f for f in cls._fields.values() if f.primary_key), None
        )
        if pk_field and pk_field.name in kwargs:
            existing = cls._identity_map.get(cls, kwargs[pk_field.name])
            if existing is not None:
                return existing

        instance = super().__new__(cls)
        instance._data = {}
        instance._dirty = set()
        return instance

    def __init__(self, **kwargs):
        if hasattr(self, '_initialized'):
            for key, value in kwargs.items():
                setattr(self, key, value)
            return

        for name, field in self._fields.items():
            value = kwargs.get(name, field.default)
            if value is not None:
                setattr(self, name, value)

        self._initialized = True
        self._identity_map.put(self)

    def __repr__(self):
        attrs = ", ".join(f"{n}={self._data.get(n)!r}" for n in self._fields)
        return f"{type(self).__name__}({attrs})"

    @classmethod
    def ddl(cls):
        cols = []
        for name, field in cls._fields.items():
            parts = [name, field.column_type]
            if field.primary_key:
                parts.append("PRIMARY KEY")
            if not field.nullable:
                parts.append("NOT NULL")
            cols.append(" ".join(parts))
        return f"CREATE TABLE {cls._table} (\n  " + ",\n  ".join(cols) + "\n);"

# --- Define models ---

class User(Model):
    id = IntField(primary_key=True)
    name = StrField(max_length=100)
    email = StrField(max_length=255)

class Post(Model):
    id = IntField(primary_key=True)
    title = StrField(max_length=200)
    author_id = IntField()

# --- Demo ---

print("=== DDL ===")
print(User.ddl())
print()
print(Post.ddl())
print()

print("=== Identity Map ===")
u1 = User(id=1, name="Alice", email="alice@example.com")
u2 = User(id=1, name="Alice Updated")
print(f"u1 is u2: {u1 is u2}")   # True — identity map returned same object
print(f"u1: {u1}")                # name was updated

print(f"Identity map size: {len(Model._identity_map)}")

print()
print("=== Registered Models ===")
for name, cls in ModelMeta._models.items():
    print(f"  {name}: {list(cls._fields.keys())}")
```

---

> **Final Note:** Understanding Python internals transforms you from someone who *uses* Python to someone who *thinks in* Python. These concepts appear constantly in system design interviews, framework development, and performance optimization. The key takeaway: Python's elegance comes from a small set of powerful mechanisms — descriptors, the object model, the C3 MRO, and the eval loop — that compose to create everything else.
