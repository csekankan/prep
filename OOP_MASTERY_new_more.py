"""
OOP_MASTERY.py  —  Staff-Engineer-Level Python OOP Reference (Beginner -> Staff Engineer)
==========================================================================================
Run any section independently.  Every concept is executable.

SECTIONS
─────────────────────────────────────────────────────────────
 0.  Beginner Primer — read this first if any of the below is unfamiliar
 1.  Dunder / Magic Methods
 2.  Properties — getter / setter / deleter / cached_property
 3.  Class Methods & Static Methods
 4.  __slots__ — memory & attribute control
 5.  Dataclasses — full API
 6.  NamedTuple — typed immutable records
 7.  Inheritance, MRO, super()
 8.  Abstract Base Classes (ABC)
 9.  Protocols — structural subtyping (PEP 544)
10.  Descriptors — data vs. non-data
11.  Metaclasses
12.  __init_subclass__ & __class_getitem__
13.  Context Managers
14.  Iterator & Generator Protocol
15.  Operator Overloading
16.  Generics — Generic[T], TypeVar, ParamSpec
17.  Mixins
18.  Singleton — 4 patterns
19.  __new__ — object creation hook
20.  copy / deepcopy protocol
21.  weakref — weak references
22.  functools helpers (total_ordering, cached_property, singledispatch)
23.  Design Patterns in idiomatic Python

────────────────────────────────────────────────────────────────────────────────
SECTION 0 — BEGINNER PRIMER (read this first)
────────────────────────────────────────────────────────────────────────────────
This file assumes you already know the absolute basics of a Python class (`class Foo:`,
`__init__`, `self`, calling a method). If any of THAT is unfamiliar, see the
"What is a class and an object, concretely?" primer in LLD_OOD_new_more.md's Section 0 first.

What this file IS: a tour of Python's more advanced, less commonly taught OOP features —
the ones that make Python feel "magical" when you see them in library code (Pydantic,
Django, dataclasses) without understanding how they work. Each section below is a small,
runnable example of ONE such feature in isolation.

A few terms you'll see constantly in the sections below:

  "Dunder" (double underscore) methods, e.g. `__init__`, `__eq__`, `__add__` — these are
  methods Python calls AUTOMATICALLY in response to built-in syntax, rather than being
  called directly by your code. E.g. writing `vector1 + vector2` secretly calls
  `vector1.__add__(vector2)` behind the scenes — Section 1 and Section 15 cover this "operator
  overloading" idea in depth. This is exactly HOW a custom class can support `+`, `==`, `len()`,
  `for x in obj`, and so on, even though those all look like built-in language features.

  "Protocol" (Section 9) — a way to say "any object with THESE methods counts as this type,"
  without requiring formal inheritance — Python calls this "structural subtyping" ("if it
  walks like a duck and quacks like a duck..."), as opposed to the more traditional
  "nominal subtyping" you get from `class Dog(Animal)`.

  "Descriptor" (Section 10) — the mechanism that makes `@property` work; understanding it
  demystifies a lot of "magic" attribute behavior in libraries like Django's ORM.

  "Metaclass" (Section 11) — "the class of a class." Just like a class controls how ITS
  instances behave, a metaclass controls how CLASSES THEMSELVES get created — this is what
  lets a library "hook into" the moment you write `class MyModel(BaseModel): ...` and do
  custom setup automatically (exactly what Pydantic does).

How to use this file: run it top to bottom (`python OOP_MASTERY_new_more.py`) — every
section prints its own header and runnable output, so you can see each concept's actual
behavior rather than just reading about it abstractly.
────────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — DUNDER / MAGIC METHODS
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 1 — Dunder / Magic Methods")
print("=" * 60)


class Vector:
    """2-D vector showcasing the most important dunder methods."""

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    # ── Representation ────────────────────────────────────────
    def __repr__(self) -> str:
        """Machine-readable; used in REPL and logging. eval(repr(v)) == v."""
        return f"Vector({self.x!r}, {self.y!r})"

    def __str__(self) -> str:
        """Human-readable; used by print() and str()."""
        return f"({self.x}, {self.y})"

    def __format__(self, spec: str) -> str:
        """f'{v:.2f}' support."""
        if spec == "":
            return str(self)
        return f"({self.x:{spec}}, {self.y:{spec}})"

    # ── Equality & Hashing ────────────────────────────────────
    # Rule: objects that compare equal MUST have the same hash.
    # Defining __eq__ without __hash__ makes the class unhashable.
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return NotImplemented  # let the other side try
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    # ── Ordering ──────────────────────────────────────────────
    def __lt__(self, other: Vector) -> bool:
        return abs(self) < abs(other)

    def __le__(self, other: Vector) -> bool:
        return abs(self) <= abs(other)

    # ── Arithmetic ────────────────────────────────────────────
    def __add__(self, other: Vector) -> Vector:
        return Vector(self.x + other.x, self.y + other.y)

    def __radd__(self, other: object) -> Vector:
        """Called when left operand doesn't support __add__ (e.g. 0 + v)."""
        if other == 0:
            return self
        return NotImplemented

    def __iadd__(self, other: Vector) -> Vector:
        """In-place += (return self for mutation, or new obj for immutable)."""
        self.x += other.x
        self.y += other.y
        return self

    def __mul__(self, scalar: float) -> Vector:
        return Vector(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> Vector:
        return self.__mul__(scalar)

    def __neg__(self) -> Vector:
        return Vector(-self.x, -self.y)

    def __abs__(self) -> float:
        return (self.x**2 + self.y**2) ** 0.5

    # ── Boolean ───────────────────────────────────────────────
    def __bool__(self) -> bool:
        """Falsy when zero vector."""
        return bool(self.x or self.y)

    # ── Container-like ────────────────────────────────────────
    def __len__(self) -> int:
        return 2

    def __getitem__(self, index: int) -> float:
        return (self.x, self.y)[index]

    def __iter__(self):
        yield self.x
        yield self.y

    def __contains__(self, value: float) -> bool:
        return value in (self.x, self.y)

    # ── Attribute access hooks ────────────────────────────────
    def __setattr__(self, name: str, value: object) -> None:
        # Could add validation here; must call super to avoid recursion
        super().__setattr__(name, value)

    def __delattr__(self, name: str) -> None:
        raise AttributeError("Vector fields are write-once after init")


v1 = Vector(3, 4)
v2 = Vector(1, 2)
print(repr(v1))                   # Vector(3, 4)
print(str(v1))                    # (3, 4)
print(f"{v1:.1f}")                # (3.0, 4.0)
print(v1 + v2)                    # (4, 6)
print(3 * v1)                     # (9, 12)
print(abs(v1))                    # 5.0
print(v1 == Vector(3, 4))         # True
print(v1 in {Vector(3, 4)})       # True (uses __hash__ + __eq__)
print(list(v1))                   # [3, 4]
print(4 in v1)                    # True
print(bool(Vector(0, 0)))         # False


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — PROPERTIES
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 2 — Properties")
print("=" * 60)

import math
from functools import cached_property


class Circle:
    def __init__(self, radius: float) -> None:
        self._radius = radius  # private backing store

    # ── Read-write property ───────────────────────────────────
    @property
    def radius(self) -> float:
        return self._radius

    @radius.setter
    def radius(self, value: float) -> None:
        if value < 0:
            raise ValueError("Radius must be non-negative")
        self._radius = value
        # Invalidate cached_property manually when state changes
        self.__dict__.pop("area", None)

    @radius.deleter
    def radius(self) -> None:
        del self._radius

    # ── Computed read-only property ───────────────────────────
    @property
    def diameter(self) -> float:
        return self._radius * 2

    # ── cached_property — computed once, then stored in instance dict ─────
    # Faster than @property for expensive computations.
    # NOT thread-safe by default (use lock if needed).
    # Stored in instance.__dict__, so it shadows the class descriptor.
    @cached_property
    def area(self) -> float:
        print("  [computing area...]")
        return math.pi * self._radius**2


c = Circle(5)
print(c.radius)           # 5
print(c.diameter)         # 10
print(c.area)             # [computing area...]  3.14…
print(c.area)             # cached — no print
c.radius = 10             # setter invalidates cache
print(c.area)             # [computing area...]  recomputed


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — CLASS METHODS & STATIC METHODS
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 3 — Class Methods & Static Methods")
print("=" * 60)


class Date:
    def __init__(self, year: int, month: int, day: int) -> None:
        self.year, self.month, self.day = year, month, day

    # ── @classmethod — receives the class (cls), not the instance ─────────
    # Primary use: alternative constructors (factory methods)
    @classmethod
    def from_iso(cls, s: str) -> "Date":
        """Works correctly when subclassed — cls is the subclass."""
        year, month, day = map(int, s.split("-"))
        return cls(year, month, day)

    @classmethod
    def today(cls) -> "Date":
        import datetime
        d = datetime.date.today()
        return cls(d.year, d.month, d.day)

    # ── @staticmethod — no implicit first arg; pure utility ───────────────
    @staticmethod
    def is_leap_year(year: int) -> bool:
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    def __repr__(self) -> str:
        return f"Date({self.year}, {self.month}, {self.day})"


print(Date.from_iso("2026-04-07"))   # Date(2026, 4, 7)
print(Date.is_leap_year(2024))       # True
print(Date.today())


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — __slots__
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 4 — __slots__")
print("=" * 60)

import sys


class PointSlotted:
    """
    __slots__ replaces the instance __dict__ with fixed-size C arrays.
    Benefits: ~40-50% memory reduction, faster attribute access.
    Cost: no instance __dict__, no dynamic attributes, harder to pickle.

    Key rules:
    - All subclasses must also define __slots__ or they get a __dict__ back.
    - To allow both slots AND arbitrary attrs, add '__dict__' to __slots__.
    - To allow weakrefs, add '__weakref__' to __slots__.
    """
    __slots__ = ("x", "y", "__weakref__")

    def __init__(self, x: float, y: float) -> None:
        self.x, self.y = x, y

    def __repr__(self) -> str:
        return f"PointSlotted({self.x}, {self.y})"


class PointDict:
    def __init__(self, x: float, y: float) -> None:
        self.x, self.y = x, y


ps = PointSlotted(1.0, 2.0)
pd = PointDict(1.0, 2.0)
print(f"Slotted size: {sys.getsizeof(ps)} bytes")   # ~48 bytes
print(f"Dict size:    {sys.getsizeof(pd)} bytes")   # ~48 bytes (just the obj)
print(f"  + __dict__: {sys.getsizeof(pd.__dict__)} bytes")  # ~184 bytes extra

# Slotted classes don't have __dict__:
try:
    ps.__dict__
except AttributeError as e:
    print(f"No __dict__: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — DATACLASSES — FULL API
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 5 — Dataclasses")
print("=" * 60)

from dataclasses import (
    dataclass, field, fields, asdict, astuple, replace, KW_ONLY, InitVar
)
from typing import ClassVar


# ── 5a. Basic dataclass ──────────────────────────────────────────────────────
@dataclass
class Employee:
    name: str
    department: str
    salary: float = 0.0

    # ClassVar — not a field, shared across all instances
    headcount: ClassVar[int] = 0

    def __post_init__(self) -> None:
        """Called after __init__. Ideal for validation & derived fields."""
        Employee.headcount += 1
        if self.salary < 0:
            raise ValueError("Salary cannot be negative")
        # Normalize name
        self.name = self.name.strip().title()


# ── 5b. Advanced field() options ─────────────────────────────────────────────
@dataclass
class Team:
    name: str
    # field() gives full control over each attribute
    members: list[str] = field(default_factory=list)   # mutable default
    _internal: str = field(default="secret", repr=False, compare=False)
    tags: set[str] = field(default_factory=set, hash=False)

    # KW_ONLY sentinel — everything after is keyword-only in __init__
    _: KW_ONLY
    max_size: int = 10


# ── 5c. Frozen dataclass — hashable, immutable ────────────────────────────────
@dataclass(frozen=True, order=True)
class Point:
    """
    frozen=True  → __setattr__ and __delattr__ raise FrozenInstanceError
    order=True   → generates __lt__, __le__, __gt__, __ge__ from field order
    """
    x: float
    y: float = 0.0

    @property
    def magnitude(self) -> float:
        return (self.x**2 + self.y**2) ** 0.5


# ── 5d. Slots dataclass (Python 3.10+) ────────────────────────────────────────
@dataclass(slots=True)
class Pixel:
    """slots=True generates __slots__ automatically."""
    x: int
    y: int
    color: str = "black"


# ── 5e. InitVar — init-only parameters ───────────────────────────────────────
@dataclass
class Rectangle:
    width: float
    height: float
    # InitVar fields appear in __init__ but are NOT stored as attributes
    unit: InitVar[str] = "m"
    area: float = field(init=False)

    def __post_init__(self, unit: str) -> None:
        scale = {"m": 1, "cm": 0.01, "ft": 0.3048}[unit]
        self.area = self.width * scale * self.height * scale


# ── 5f. Inheritance with dataclasses ─────────────────────────────────────────
@dataclass
class Shape:
    color: str = "red"


@dataclass
class ColoredPoint(Shape):
    x: float = 0.0
    y: float = 0.0
    # Rule: parent fields with defaults must come before child fields without.


# ── 5g. dataclass utilities ───────────────────────────────────────────────────
e1 = Employee("alice smith", "engineering", 120_000)
e2 = Employee("bob jones", "product", 95_000)
print(e1)                          # Employee(name='Alice Smith', ...)
print(Employee.headcount)          # 2

t = Team("backend", members=["Alice"], max_size=5)
print(t)

p = Point(3.0, 4.0)
print(p.magnitude)                 # 5.0
print(sorted([Point(5,0), Point(1,1), Point(3,4)]))  # ordered

r = Rectangle(10, 5, unit="cm")
print(f"Area: {r.area:.4f} m²")   # Area: 0.0050 m²  (10cm × 5cm)

print(asdict(e1))                  # {'name': 'Alice Smith', ...}
print(astuple(p))                  # (3.0, 4.0)
e3 = replace(e1, department="data")  # shallow copy with changes
print(e3)

print([f.name for f in fields(Employee)])   # field names


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — NamedTuple
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 6 — NamedTuple")
print("=" * 60)

from typing import NamedTuple


class Coordinate(NamedTuple):
    """
    NamedTuple vs dataclass:
    - NamedTuple: immutable, tuple-compatible, faster iteration, no __dict__
    - dataclass:  mutable by default, more features (__post_init__, ClassVar)
    Use NamedTuple when you need tuple unpacking or legacy tuple APIs.
    """
    latitude: float
    longitude: float
    altitude: float = 0.0

    def distance_to(self, other: "Coordinate") -> float:
        return math.sqrt(
            (self.latitude - other.latitude)**2 +
            (self.longitude - other.longitude)**2
        )


c1 = Coordinate(37.7749, -122.4194)
c2 = Coordinate(34.0522, -118.2437)
lat, lon, alt = c1     # tuple unpacking works (3 fields)
print(f"{lat}, {lon}")
print(c1._asdict())    # OrderedDict
print(c1._replace(altitude=100))


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — INHERITANCE, MRO, super()
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 7 — Inheritance, MRO, super()")
print("=" * 60)


class A:
    def ping(self) -> str:
        return "A"


class B(A):
    def ping(self) -> str:
        # super() resolves next in MRO — critical for cooperative inheritance
        return f"B → {super().ping()}"


class C(A):
    def ping(self) -> str:
        return f"C → {super().ping()}"


class D(B, C):
    """
    MRO (Method Resolution Order) — Python uses C3 Linearization:
    D → B → C → A → object
    Guarantees: local precedence + monotonicity.
    """
    def ping(self) -> str:
        return f"D → {super().ping()}"


print(D().ping())             # D → B → C → A
print(D.__mro__)              # shows the full chain

# ── Practical: calling parent __init__ correctly ──────────────────────────────


class Animal:
    def __init__(self, name: str) -> None:
        self.name = name
        print(f"Animal.__init__({name!r})")


class Flyable:
    def __init__(self, max_altitude: float, **kwargs) -> None:
        # Accept and forward **kwargs so cooperative MRO works down to object
        super().__init__(**kwargs)
        self.max_altitude = max_altitude
        print(f"Flyable.__init__({max_altitude})")


class Bird(Flyable, Animal):
    def __init__(self, name: str, max_altitude: float) -> None:
        # Pass all args as kwargs so each mixin can pull what it needs
        super().__init__(name=name, max_altitude=max_altitude)
        print(f"Bird.__init__()")


b = Bird("Eagle", 3000)
print(f"{b.name} flies up to {b.max_altitude}m")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8 — ABSTRACT BASE CLASSES
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 8 — Abstract Base Classes")
print("=" * 60)

from abc import ABC, abstractmethod
import abc


class Shape2D(ABC):
    """
    ABC prevents direct instantiation.  Subclasses must implement all
    @abstractmethod methods or they too become abstract.
    """

    @abstractmethod
    def area(self) -> float: ...

    @abstractmethod
    def perimeter(self) -> float: ...

    # Abstract class method
    @classmethod
    @abstractmethod
    def unit_shape(cls) -> "Shape2D": ...

    # Concrete method — shared implementation
    def describe(self) -> str:
        return (
            f"{type(self).__name__}: "
            f"area={self.area():.2f}, perimeter={self.perimeter():.2f}"
        )


class Rect(Shape2D):
    def __init__(self, w: float, h: float) -> None:
        self.w, self.h = w, h

    def area(self) -> float:
        return self.w * self.h

    def perimeter(self) -> float:
        return 2 * (self.w + self.h)

    @classmethod
    def unit_shape(cls) -> "Rect":
        return cls(1, 1)


try:
    Shape2D()   # raises TypeError
except TypeError as e:
    print(f"Cannot instantiate abstract: {e}")

r = Rect(3, 4)
print(r.describe())
print(isinstance(r, Shape2D))   # True

# ── Virtual subclass registration (no inheritance needed) ─────────────────────
from abc import ABCMeta


class Drawable(ABC):
    @abstractmethod
    def draw(self) -> None: ...


class LegacyWidget:
    """Third-party class we can't modify."""
    def draw(self) -> None:
        print("LegacyWidget.draw()")


# Register without inheritance — duck-typing meets ABCs
Drawable.register(LegacyWidget)
lw = LegacyWidget()
print(isinstance(lw, Drawable))   # True


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9 — PROTOCOLS (Structural Subtyping)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 9 — Protocols (PEP 544)")
print("=" * 60)

from typing import Protocol, runtime_checkable


@runtime_checkable
class Drawable2(Protocol):
    """
    Protocol = structural subtyping ("duck typing with types").
    No registration or inheritance needed — if an object has the
    required methods/attributes, it satisfies the protocol.

    @runtime_checkable enables isinstance() checks (method names only,
    NOT signatures, so use with care).
    """
    def draw(self) -> None: ...


class Canvas:
    def draw(self) -> None:
        print("Canvas.draw()")


class Button:
    """Satisfies Drawable2 implicitly — no inheritance required."""
    def draw(self) -> None:
        print("Button.draw()")


def render(item: Drawable2) -> None:
    item.draw()


render(Canvas())
render(Button())
print(isinstance(Button(), Drawable2))   # True (runtime_checkable)


# ── Protocol with attributes ──────────────────────────────────────────────────
@runtime_checkable
class HasName(Protocol):
    name: str


@dataclass
class User:
    name: str
    email: str


print(isinstance(User("Alice", "a@b.com"), HasName))   # True


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 10 — DESCRIPTORS
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 10 — Descriptors")
print("=" * 60)

"""
Descriptor protocol:
  __get__(self, obj, objtype=None)   — attribute read
  __set__(self, obj, value)          — attribute write
  __delete__(self, obj)              — attribute delete
  __set_name__(self, owner, name)    — called when class is defined

Data descriptor:     defines __set__ or __delete__  → overrides instance __dict__
Non-data descriptor: only __get__                   → instance __dict__ wins

Lookup order: data descriptors > instance __dict__ > non-data descriptors
"""


class Validated:
    """Generic data descriptor for type + range validation."""

    def __set_name__(self, owner: type, name: str) -> None:
        # Called automatically when the owning class is created
        self.name = name
        self.private = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self          # accessed on the class itself
        return getattr(obj, self.private, None)

    def __set__(self, obj, value) -> None:
        self._validate(value)
        setattr(obj, self.private, value)

    def __delete__(self, obj) -> None:
        delattr(obj, self.private)

    def _validate(self, value) -> None:
        pass   # override in subclasses


class PositiveFloat(Validated):
    def _validate(self, value) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError(f"{self.name} must be numeric")
        if value <= 0:
            raise ValueError(f"{self.name} must be positive")


class NonEmptyStr(Validated):
    def _validate(self, value) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{self.name} must be a non-empty string")


class Product:
    name = NonEmptyStr()
    price = PositiveFloat()
    stock = PositiveFloat()

    def __init__(self, name: str, price: float, stock: float) -> None:
        self.name = name       # calls NonEmptyStr.__set__
        self.price = price     # calls PositiveFloat.__set__
        self.stock = stock


p = Product("Widget", 9.99, 100)
print(p.name, p.price, p.stock)

try:
    p.price = -5
except ValueError as e:
    print(f"Descriptor caught: {e}")


# ── Non-data descriptor example: lazy method binding ─────────────────────────
class LazyProperty:
    """Non-data descriptor: computed once, then stored in instance dict."""
    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        value = self.func(obj)
        # Store in instance dict — next access bypasses the descriptor
        obj.__dict__[self.func.__name__] = value
        return value


class HeavyComputation:
    @LazyProperty
    def result(self) -> int:
        print("  [computing...]")
        return sum(range(1_000_000))


hc = HeavyComputation()
print(hc.result)   # [computing...] 499999500000
print(hc.result)   # cached — no print


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 11 — METACLASSES
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 11 — Metaclasses")
print("=" * 60)

"""
Everything in Python is an object, including classes.
The type of a class is its metaclass (default: type).

Creation order when Python sees `class Foo(Bar, metaclass=Meta): ...`:
  1. Meta.__prepare__(name, bases) → returns namespace dict
  2. Execute class body inside that namespace
  3. Meta.__new__(mcs, name, bases, namespace) → creates the class object
  4. Meta.__init__(cls, name, bases, namespace) → initializes it

Use metaclasses for:
  - Enforcing coding standards at class definition time
  - Auto-registering subclasses
  - Adding class-level behavior (e.g., ORM field collection)
  - Singleton enforcement

Prefer __init_subclass__ for simpler cases (Section 12).
"""


class SingletonMeta(type):
    """Metaclass-based Singleton."""
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Config(metaclass=SingletonMeta):
    def __init__(self) -> None:
        self.debug = False
        self.version = "1.0"


c1, c2 = Config(), Config()
print(c1 is c2)   # True — same instance


class InterfaceMeta(type):
    """
    Metaclass that enforces all methods declared in __required__ are implemented.
    A simpler alternative to ABC for interface enforcement.
    """
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        required = namespace.get("__required__", [])
        for base in bases:
            required += getattr(base, "__required__", [])
        missing = [m for m in required if not callable(getattr(cls, m, None))
                   or getattr(cls, m, None) is None]
        if bases and missing:   # skip the base class itself
            raise TypeError(f"{name} must implement: {missing}")
        return cls


class RegistryMeta(type):
    """Auto-register all concrete subclasses — common in plugin systems."""
    _registry: dict[str, type] = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if bases:   # skip the base class
            mcs._registry[name] = cls
        return cls

    @classmethod
    def get(mcs, name: str) -> type:
        return mcs._registry[name]


class Plugin(metaclass=RegistryMeta):
    """Base plugin — auto-registers all subclasses."""
    def run(self) -> str: ...


class CSVPlugin(Plugin):
    def run(self) -> str:
        return "CSV"


class JSONPlugin(Plugin):
    def run(self) -> str:
        return "JSON"


print(RegistryMeta._registry)   # {'CSVPlugin': ..., 'JSONPlugin': ...}
plugin = RegistryMeta.get("CSVPlugin")()
print(plugin.run())


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 12 — __init_subclass__ & __class_getitem__
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 12 — __init_subclass__ & __class_getitem__")
print("=" * 60)


class BaseModel:
    """
    __init_subclass__ — cleaner than metaclasses for subclass hooks.
    Called on the base class when any subclass is defined.
    """
    _registry: dict[str, type] = {}

    def __init_subclass__(cls, table_name: str | None = None, **kwargs) -> None:
        super().__init_subclass__(**kwargs)  # always forward kwargs
        name = table_name or cls.__name__.lower()
        BaseModel._registry[name] = cls
        cls._table = name

    @classmethod
    def table(cls) -> str:
        return cls._table


class UserModel(BaseModel, table_name="users"):
    pass


class OrderModel(BaseModel, table_name="orders"):
    pass


print(BaseModel._registry)    # {'users': UserModel, 'orders': OrderModel}
print(UserModel.table())      # users


class TypedList:
    """
    __class_getitem__ — enables MyClass[SomeType] syntax without Generic.
    Used internally by list, dict, etc. for runtime parameterization.
    """
    def __class_getitem__(cls, item: type) -> type:
        # Returns a new class specialized for this item type
        return type(f"{cls.__name__}[{item.__name__}]", (cls,), {"_type": item})


IntList = TypedList[int]
print(IntList.__name__)   # TypedList[int]


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 13 — CONTEXT MANAGERS
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 13 — Context Managers")
print("=" * 60)

from contextlib import contextmanager, asynccontextmanager, suppress
import time


class Timer:
    """
    Class-based context manager.
    __enter__ → called on 'with' entry; return value bound to 'as' target.
    __exit__  → called on exit (normal or exception).
                Return True to suppress the exception.
    """
    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.elapsed = time.perf_counter() - self._start
        if exc_type:
            print(f"  Exception {exc_type.__name__} occurred after {self.elapsed:.4f}s")
        return False   # don't suppress exceptions


with Timer() as t:
    sum(range(1_000_000))
print(f"Elapsed: {t.elapsed:.4f}s")


# ── Generator-based context manager ──────────────────────────────────────────
@contextmanager
def managed_resource(name: str):
    """Simplest way to write a context manager for one-shot resources."""
    print(f"Acquiring {name}")
    try:
        yield name.upper()   # value bound to 'as' target
    except Exception as e:
        print(f"  Handling error: {e}")
        raise
    finally:
        print(f"Releasing {name}")


with managed_resource("db_connection") as res:
    print(f"Using {res}")

# ── suppress — silently ignore specific exceptions ────────────────────────────
with suppress(FileNotFoundError):
    open("/nonexistent/path.txt")
print("Continued after suppressed error")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 14 — ITERATOR & GENERATOR PROTOCOL
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 14 — Iterator & Generator Protocol")
print("=" * 60)


class Range2D:
    """
    Custom iterator: iterates over all (row, col) pairs in a grid.
    An object is an iterator if it has __iter__ returning self and __next__.
    """
    def __init__(self, rows: int, cols: int) -> None:
        self.rows, self.cols = rows, cols

    def __iter__(self):
        # Using a generator inside __iter__ is the cleanest pattern.
        # Separates the iterable (Range2D) from the iterator state.
        for r in range(self.rows):
            for c in range(self.cols):
                yield (r, c)

    def __len__(self) -> int:
        return self.rows * self.cols

    def __reversed__(self):
        for r in range(self.rows - 1, -1, -1):
            for c in range(self.cols - 1, -1, -1):
                yield (r, c)


grid = Range2D(2, 3)
print(list(grid))               # [(0,0),(0,1),(0,2),(1,0),(1,1),(1,2)]
print(list(reversed(grid)))


# ── Iterable vs Iterator distinction ─────────────────────────────────────────
class InfiniteCounter:
    """
    Infinite iterator — can only be iterated once (iterator IS the iterable).
    Use itertools.islice() to take finite slices.
    """
    def __init__(self, start: int = 0) -> None:
        self.n = start

    def __iter__(self):   # returns self — it IS its own iterator
        return self

    def __next__(self) -> int:
        val = self.n
        self.n += 1
        return val


import itertools
counter = InfiniteCounter(10)
print(list(itertools.islice(counter, 5)))   # [10, 11, 12, 13, 14]


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 15 — OPERATOR OVERLOADING (advanced patterns)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 15 — Operator Overloading")
print("=" * 60)

from functools import total_ordering


@total_ordering
class Money:
    """
    @total_ordering — define __eq__ and ONE of __lt__/__le__/__gt__/__ge__,
    and the decorator fills in the remaining comparison methods.
    """
    def __init__(self, amount: float, currency: str = "USD") -> None:
        self.amount = round(amount, 2)
        self.currency = currency

    def _check_currency(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise ValueError(f"Cannot mix {self.currency} and {other.currency}")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        self._check_currency(other)
        return self.amount == other.amount

    def __lt__(self, other: "Money") -> bool:
        self._check_currency(other)
        return self.amount < other.amount

    def __add__(self, other: "Money") -> "Money":
        self._check_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._check_currency(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: float) -> "Money":
        return Money(self.amount * factor, self.currency)

    def __truediv__(self, divisor: float) -> "Money":
        return Money(self.amount / divisor, self.currency)

    def __repr__(self) -> str:
        return f"Money({self.amount}, {self.currency!r})"

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"

    def __hash__(self) -> int:
        return hash((self.amount, self.currency))


m1 = Money(10.50)
m2 = Money(3.25)
print(m1 + m2)          # USD 13.75
print(m1 > m2)          # True
print(m1 * 2)           # USD 21.00
print(sorted([Money(5), Money(1), Money(3)]))   # sorted by amount


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 16 — GENERICS
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 16 — Generics")
print("=" * 60)

from typing import Generic, TypeVar, Iterator, Sequence

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class Stack(Generic[T]):
    """
    Generic class — parameterized by type T.
    At runtime T is erased (Python uses type erasure), but type checkers use it.
    """
    def __init__(self) -> None:
        self._data: list[T] = []

    def push(self, item: T) -> None:
        self._data.append(item)

    def pop(self) -> T:
        if not self._data:
            raise IndexError("pop from empty stack")
        return self._data.pop()

    def peek(self) -> T:
        return self._data[-1]

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[T]:
        return iter(reversed(self._data))

    def __repr__(self) -> str:
        return f"Stack({self._data!r})"


s: Stack[int] = Stack()
s.push(1); s.push(2); s.push(3)
print(s)           # Stack([1, 2, 3])
print(s.pop())     # 3


# ── Bounded TypeVar ───────────────────────────────────────────────────────────
Comparable = TypeVar("Comparable", bound="SupportsLessThan")


class BinarySearchTree(Generic[T]):
    """Sketch — T must be orderable."""
    def __init__(self) -> None:
        self._root: T | None = None

    def insert(self, value: T) -> None:
        self._root = value   # simplified


# ── Python 3.12+ syntax (PEP 695) — shown as comment for compatibility ────────
# class Stack[T]:       # new syntax, no import needed
#     def push(self, item: T) -> None: ...


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 17 — MIXINS
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 17 — Mixins")
print("=" * 60)

"""
Mixin guidelines:
  1. Never call super().__init__() without **kwargs (breaks cooperative MRO).
  2. Never hold state that conflicts with target class state.
  3. Name mixins with 'Mixin' suffix for clarity.
  4. Mixins should depend on an interface, not a concrete class.
"""
import json
import logging


class LoggableMixin:
    """Injects a logger named after the concrete class."""
    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, "_logger"):
            self._logger = logging.getLogger(type(self).__name__)
        return self._logger

    def log_action(self, action: str) -> None:
        self.logger.debug(f"[{type(self).__name__}] {action}")


class SerializableMixin:
    """JSON serialization for dataclass-like objects."""
    def to_json(self) -> str:
        return json.dumps(self.__dict__, default=str)

    @classmethod
    def from_json(cls, data: str):
        return cls(**json.loads(data))


class ValidatableMixin:
    """Enforce a validate() hook before saving."""
    def validate(self) -> list[str]:
        """Return list of validation error messages."""
        return []

    def save(self) -> bool:
        errors = self.validate()
        if errors:
            raise ValueError(f"Validation failed: {errors}")
        return True


class TimestampMixin:
    """Adds created_at / updated_at fields."""
    import datetime as _dt

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        import datetime
        self.created_at = datetime.datetime.utcnow().isoformat()
        self.updated_at = self.created_at

    def touch(self) -> None:
        import datetime
        self.updated_at = datetime.datetime.utcnow().isoformat()


class Order(LoggableMixin, SerializableMixin, ValidatableMixin):
    def __init__(self, order_id: str, amount: float) -> None:
        self.order_id = order_id
        self.amount = amount

    def validate(self) -> list[str]:
        errors = []
        if self.amount <= 0:
            errors.append("Amount must be positive")
        if not self.order_id:
            errors.append("order_id is required")
        return errors


o = Order("ORD-001", 99.99)
print(o.to_json())
o.save()   # passes validation

bad = Order("", -5)
try:
    bad.save()
except ValueError as e:
    print(f"Caught: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 18 — SINGLETON — 4 PATTERNS
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 18 — Singleton Patterns")
print("=" * 60)

import threading


# Pattern 1: Module-level (simplest — Python modules are singletons by default)
# Just put the instance in a module. Import the module to get the singleton.


# Pattern 2: __new__-based
class SingletonNew:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:   # double-checked locking
                    cls._instance = super().__new__(cls)
        return cls._instance


a, b = SingletonNew(), SingletonNew()
print(a is b)   # True


# Pattern 3: Metaclass-based (shown in Section 11 above)


# Pattern 4: Class decorator
def singleton(cls):
    instances = {}
    lock = threading.Lock()

    def get_instance(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance


@singleton
class DatabasePool:
    def __init__(self) -> None:
        self.connections: list = []


db1, db2 = DatabasePool(), DatabasePool()
print(db1 is db2)   # True


# Pattern 5: Borg (monostate — different instances, shared state)
class Borg:
    """
    All instances share the same __dict__.  Good when you need pickle support
    (which breaks with classic singleton since __new__ isn't symmetric).
    """
    _shared: dict = {}

    def __init__(self) -> None:
        self.__dict__ = Borg._shared


x, y = Borg(), Borg()
x.value = 42
print(y.value)      # 42 — shared state
print(x is y)       # False — different objects


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 19 — __new__ — OBJECT CREATION HOOK
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 19 — __new__")
print("=" * 60)

"""
object creation sequence:
  1. cls.__new__(cls, *args, **kwargs)  → creates the raw object
  2. obj.__init__(*args, **kwargs)      → initializes it
  3. return obj

Use __new__ for:
  - Immutable types (int, str, tuple) — can't modify in __init__
  - Singleton / Flyweight patterns
  - Custom allocation (e.g., from a pool)
  - Returning an instance of a different class
"""


class Celsius(float):
    """Immutable subclass of float — must use __new__."""
    def __new__(cls, value: float) -> "Celsius":
        if value < -273.15:
            raise ValueError("Temperature below absolute zero")
        return super().__new__(cls, value)

    def to_fahrenheit(self) -> float:
        return self * 9 / 5 + 32


temp = Celsius(100)
print(type(temp), temp, temp.to_fahrenheit())   # Celsius 100.0 212.0

try:
    Celsius(-300)
except ValueError as e:
    print(f"Caught: {e}")


class Flyweight:
    """Flyweight pattern: reuse objects with the same key."""
    _pool: dict = {}

    def __new__(cls, key: str):
        if key not in cls._pool:
            instance = super().__new__(cls)
            cls._pool[key] = instance
        return cls._pool[key]

    def __init__(self, key: str) -> None:
        self.key = key   # safe to call multiple times since it's idempotent


fw1 = Flyweight("A")
fw2 = Flyweight("A")
print(fw1 is fw2)   # True


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 20 — COPY PROTOCOL
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 20 — copy / deepcopy Protocol")
print("=" * 60)

import copy


class Graph:
    """
    Custom copy/deepcopy hooks let you control exactly how an object is copied.
    Common in large objects with cycles or shared state.
    """
    def __init__(self, nodes: list, edges: list) -> None:
        self.nodes = nodes
        self.edges = edges

    def __copy__(self) -> "Graph":
        """Shallow copy — new Graph, same lists (shared references)."""
        new = Graph.__new__(Graph)
        new.__dict__.update(self.__dict__)
        return new

    def __deepcopy__(self, memo: dict) -> "Graph":
        """
        Deep copy — memo dict prevents infinite recursion for cyclic structures.
        Always pass memo to nested deepcopy calls.
        """
        new = Graph.__new__(Graph)
        memo[id(self)] = new   # register before recursing
        new.nodes = copy.deepcopy(self.nodes, memo)
        new.edges = copy.deepcopy(self.edges, memo)
        return new


g1 = Graph(["A", "B"], [("A", "B")])
g2 = copy.copy(g1)
g3 = copy.deepcopy(g1)

g1.nodes.append("C")
print(g2.nodes)   # ['A', 'B', 'C']  — shared (shallow)
print(g3.nodes)   # ['A', 'B']       — independent (deep)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 21 — WEAKREF
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 21 — weakref")
print("=" * 60)

import weakref


class Cache:
    """
    WeakValueDictionary — values are held weakly.
    When the only remaining reference to a value is this dict, GC can collect it.
    Useful for caches that shouldn't prevent GC of their entries.
    """
    def __init__(self) -> None:
        self._store: weakref.WeakValueDictionary = weakref.WeakValueDictionary()

    def get(self, key: str):
        return self._store.get(key)

    def set(self, key: str, value) -> None:
        self._store[key] = value


class Resource:
    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return f"Resource({self.name!r})"


cache = Cache()
r = Resource("widget")
cache.set("w", r)
print(cache.get("w"))    # Resource('widget')

del r                    # only strong reference removed
import gc; gc.collect()
print(cache.get("w"))    # None — GC collected it

# ── Weak reference callback ───────────────────────────────────────────────────
def on_finalized(ref) -> None:
    print(f"  Object finalized: {ref}")


r2 = Resource("gadget")
weak = weakref.ref(r2, on_finalized)
print(weak())    # Resource('gadget')
del r2
gc.collect()     # triggers callback


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 22 — functools HELPERS
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 22 — functools helpers")
print("=" * 60)

from functools import singledispatch, singledispatchmethod, lru_cache, wraps


# ── singledispatch — function overloading on first argument type ──────────────
@singledispatch
def process(value) -> str:
    return f"generic: {value!r}"


@process.register(int)
def _(value: int) -> str:
    return f"int: {value * 2}"


@process.register(str)
def _(value: str) -> str:
    return f"str: {value.upper()}"


@process.register(list)
@process.register(tuple)
def _(value) -> str:
    return f"sequence of {len(value)}"


print(process(42))          # int: 84
print(process("hello"))     # str: HELLO
print(process([1, 2, 3]))   # sequence of 3
print(process(3.14))        # generic: 3.14


# ── singledispatchmethod — same but for methods ───────────────────────────────
class Formatter:
    @singledispatchmethod
    def format(self, value) -> str:
        return str(value)

    @format.register
    def _(self, value: int) -> str:
        return f"int:{value:,}"

    @format.register
    def _(self, value: float) -> str:
        return f"float:{value:.4f}"


fmt = Formatter()
print(fmt.format(1_000_000))   # int:1,000,000
print(fmt.format(3.14159))     # float:3.1416


# ── lru_cache on class methods ────────────────────────────────────────────────
class FibCalculator:
    @lru_cache(maxsize=None)   # unbounded cache
    def fib(self, n: int) -> int:
        if n < 2:
            return n
        return self.fib(n - 1) + self.fib(n - 2)


calc = FibCalculator()
print(calc.fib(50))   # 12586269025


# ── Custom decorator preserving metadata ──────────────────────────────────────
def retry(times: int = 3):
    """Decorator factory — retry on exception."""
    def decorator(func):
        @wraps(func)   # preserves __name__, __doc__, __wrapped__
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == times:
                        raise
                    print(f"  Retry {attempt}/{times} after: {e}")
        return wrapper
    return decorator


@retry(times=2)
def unstable_operation(fail: bool):
    if fail:
        raise ConnectionError("timeout")
    return "success"


print(unstable_operation(False))
print(unstable_operation.__name__)   # unstable_operation (not 'wrapper')


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 23 — DESIGN PATTERNS IN IDIOMATIC PYTHON
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SECTION 23 — Design Patterns")
print("=" * 60)


# ── Observer (Event system) ────────────────────────────────────────────────────
from typing import Callable


class EventBus:
    """Thread-safe publish/subscribe event bus."""
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event: str) -> Callable:
        """Decorator factory — @bus.subscribe('event.name')"""
        def decorator(handler: Callable) -> Callable:
            with self._lock:
                self._handlers.setdefault(event, []).append(handler)
            return handler
        return decorator

    def unsubscribe(self, event: str, handler: Callable) -> None:
        with self._lock:
            if event in self._handlers:
                self._handlers[event].remove(handler)

    def publish(self, event: str, **data) -> None:
        for handler in self._handlers.get(event, []):
            handler(**data)


bus = EventBus()

@bus.subscribe("user.created")
def send_welcome(user_id: str, email: str) -> None:
    print(f"  Welcome email → {email}")

@bus.subscribe("user.created")
def log_signup(user_id: str, **_) -> None:
    print(f"  Logged signup: {user_id}")

bus.publish("user.created", user_id="u123", email="alice@example.com")


# ── Strategy — swap algorithms at runtime ─────────────────────────────────────
from typing import Protocol as Proto


class SortStrategy(Proto):
    def sort(self, data: list) -> list: ...


class QuickSort:
    def sort(self, data: list) -> list:
        return sorted(data)   # simplified


class BucketSort:
    def sort(self, data: list) -> list:
        return sorted(data)   # simplified


class Sorter:
    def __init__(self, strategy: SortStrategy) -> None:
        self._strategy = strategy

    @property
    def strategy(self) -> SortStrategy:
        return self._strategy

    @strategy.setter
    def strategy(self, s: SortStrategy) -> None:
        self._strategy = s

    def sort(self, data: list) -> list:
        return self._strategy.sort(data)


sorter = Sorter(QuickSort())
print(sorter.sort([3, 1, 4, 1, 5]))
sorter.strategy = BucketSort()
print(sorter.sort([3, 1, 4, 1, 5]))


# ── Builder — construct complex objects step by step ──────────────────────────
@dataclass
class QueryConfig:
    table: str
    columns: list[str]
    conditions: list[str]
    limit: int | None
    order_by: str | None


class QueryBuilder:
    """Fluent builder — each method returns self."""
    def __init__(self, table: str) -> None:
        self._table = table
        self._columns: list[str] = ["*"]
        self._conditions: list[str] = []
        self._limit: int | None = None
        self._order_by: str | None = None

    def select(self, *columns: str) -> "QueryBuilder":
        self._columns = list(columns)
        return self

    def where(self, condition: str) -> "QueryBuilder":
        self._conditions.append(condition)
        return self

    def order(self, column: str) -> "QueryBuilder":
        self._order_by = column
        return self

    def limit(self, n: int) -> "QueryBuilder":
        self._limit = n
        return self

    def build(self) -> QueryConfig:
        return QueryConfig(
            table=self._table,
            columns=self._columns,
            conditions=self._conditions,
            limit=self._limit,
            order_by=self._order_by,
        )

    def to_sql(self) -> str:
        cols = ", ".join(self._columns)
        sql = f"SELECT {cols} FROM {self._table}"
        if self._conditions:
            sql += " WHERE " + " AND ".join(self._conditions)
        if self._order_by:
            sql += f" ORDER BY {self._order_by}"
        if self._limit:
            sql += f" LIMIT {self._limit}"
        return sql


query = (
    QueryBuilder("users")
    .select("id", "name", "email")
    .where("active = 1")
    .where("age > 18")
    .order("name")
    .limit(50)
    .to_sql()
)
print(query)


# ── Command — encapsulate actions for undo/redo ───────────────────────────────
from abc import ABC as AbcBase, abstractmethod as abstractm


class Command(AbcBase):
    @abstractm
    def execute(self) -> None: ...
    @abstractm
    def undo(self) -> None: ...


class TextEditor:
    def __init__(self) -> None:
        self.text = ""
        self._history: list[Command] = []
        self._undo_stack: list[Command] = []

    def execute(self, cmd: Command) -> None:
        cmd.execute()
        self._history.append(cmd)
        self._undo_stack.clear()

    def undo(self) -> None:
        if self._history:
            cmd = self._history.pop()
            cmd.undo()
            self._undo_stack.append(cmd)

    def redo(self) -> None:
        if self._undo_stack:
            cmd = self._undo_stack.pop()
            cmd.execute()
            self._history.append(cmd)


class InsertText(Command):
    def __init__(self, editor: TextEditor, text: str) -> None:
        self._editor = editor
        self._text = text

    def execute(self) -> None:
        self._editor.text += self._text

    def undo(self) -> None:
        self._editor.text = self._editor.text[: -len(self._text)]


editor = TextEditor()
editor.execute(InsertText(editor, "Hello"))
editor.execute(InsertText(editor, " World"))
print(editor.text)   # Hello World
editor.undo()
print(editor.text)   # Hello
editor.redo()
print(editor.text)   # Hello World


# ── Factory Method + Abstract Factory ─────────────────────────────────────────
class Notification(AbcBase):
    @abstractm
    def send(self, message: str, recipient: str) -> None: ...


class EmailNotification(Notification):
    def send(self, message: str, recipient: str) -> None:
        print(f"  Email → {recipient}: {message}")


class SMSNotification(Notification):
    def send(self, message: str, recipient: str) -> None:
        print(f"  SMS → {recipient}: {message}")


class PushNotification(Notification):
    def send(self, message: str, recipient: str) -> None:
        print(f"  Push → {recipient}: {message}")


class NotificationFactory:
    _map: dict[str, type[Notification]] = {
        "email": EmailNotification,
        "sms": SMSNotification,
        "push": PushNotification,
    }

    @classmethod
    def create(cls, channel: str) -> Notification:
        klass = cls._map.get(channel)
        if klass is None:
            raise ValueError(f"Unknown channel: {channel!r}")
        return klass()

    @classmethod
    def register(cls, channel: str, klass: type[Notification]) -> None:
        """Extensible — register new channels at runtime."""
        cls._map[channel] = klass


for ch in ("email", "sms", "push"):
    n = NotificationFactory.create(ch)
    n.send("Your order shipped!", "alice@example.com")


print("\n" + "=" * 60)
print("All sections complete.")
print("=" * 60)
