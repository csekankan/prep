# Clean Architecture — Complete Reference Guide

Everything from Robert C. Martin's "Clean Architecture: A Craftsman's Guide to Software Structure and Design" — distilled with Python examples so you can skip the 404-page book.

---

## Table of Contents

1. [The Goal of Architecture](#1-the-goal-of-architecture)
2. [Behavior vs. Structure — A Tale of Two Values](#2-behavior-vs-structure--a-tale-of-two-values)
3. [Programming Paradigms](#3-programming-paradigms)
4. [SOLID Principles](#4-solid-principles)
5. [Component Principles — Cohesion](#5-component-principles--cohesion)
6. [Component Principles — Coupling](#6-component-principles--coupling)
7. [What Is Architecture?](#7-what-is-architecture)
8. [Independence](#8-independence)
9. [Boundaries: Drawing Lines](#9-boundaries-drawing-lines)
10. [Boundary Anatomy](#10-boundary-anatomy)
11. [Policy and Level](#11-policy-and-level)
12. [Business Rules — Entities & Use Cases](#12-business-rules--entities--use-cases)
13. [Screaming Architecture](#13-screaming-architecture)
14. [The Clean Architecture](#14-the-clean-architecture)
15. [Presenters and Humble Objects](#15-presenters-and-humble-objects)
16. [Partial Boundaries](#16-partial-boundaries)
17. [The Main Component](#17-the-main-component)
18. [Services: Great and Small](#18-services-great-and-small)
19. [The Test Boundary](#19-the-test-boundary)
20. [The Database Is a Detail](#20-the-database-is-a-detail)
21. [The Web Is a Detail](#21-the-web-is-a-detail)
22. [Frameworks Are Details](#22-frameworks-are-details)
23. [Package Organization Strategies](#23-package-organization-strategies)
24. [Full Example: E-Commerce System](#24-full-example-e-commerce-system)
25. [Full Example: Blog Platform](#25-full-example-blog-platform)
26. [Clean Architecture Cheatsheet](#26-clean-architecture-cheatsheet)

---

## 1. The Goal of Architecture

**The goal of software architecture is to minimize the human resources required to build and maintain the required system.**

Good design = low effort to deliver features, and that effort stays low over the lifetime of the system. Bad design = every release gets harder, slower, and more expensive.

```
Release 1: 5 devs,  fast delivery      ← looks great
Release 2: 10 devs, same speed         ← hmm
Release 5: 30 devs, slower than R1     ← disaster
Release 8: 60 devs, almost nothing ships ← the "signature of a mess"
```

**Why does this happen?**

Developers tell themselves: *"We can clean it up later; we just have to get to market first."* But later never comes. The mess compounds. Productivity asymptotically approaches zero.

**Uncle Bob's core truth:**

> The only way to go fast, is to go well.

Making messes is **always** slower than staying clean — even in the short term.

---

## 2. Behavior vs. Structure — A Tale of Two Values

Software provides two kinds of value:

| Value | Description | Urgency | Importance |
|-------|-------------|---------|------------|
| **Behavior** | Making the machine do what stakeholders want | Often urgent | Not always important |
| **Structure** | Keeping the software "soft" — easy to change | Rarely urgent | Always important |

**Eisenhower's Matrix applied to software:**

```
                    Urgent          Not Urgent
Important       [1] Architecture   [2] Architecture
                    + Behavior
Not Important   [3] Behavior       [4] Neither
```

Architecture (structure) occupies positions 1 and 2. The cost of change should be proportional to the **scope** of change, not its **shape**. When architecture degrades, every change costs more regardless of how small it is.

**The developer's responsibility:** Fight for architecture. You are a stakeholder. If architecture comes last, the system becomes ever more costly to develop.

---

## 3. Programming Paradigms

Three paradigms — each **removes** a capability, none adds one:

### 3.1 Structured Programming

> Discipline imposed on **direct transfer of control** (no goto).

Dijkstra proved that all programs can be built from three structures: **sequence**, **selection** (`if/else`), and **iteration** (`while`). This enables **functional decomposition** — breaking problems into provable, testable units.

**Architectural relevance:** Falsifiability. We write tests that try to prove our modules incorrect. Modules that survive testing are deemed correct enough.

### 3.2 Object-Oriented Programming

> Discipline imposed on **indirect transfer of control** (safe polymorphism).

OO's real superpower is **dependency inversion through polymorphism**. Before OO, source code dependencies followed the flow of control. With polymorphism, an architect can point dependencies in **any** direction.

```python
# Without DIP — high-level depends on low-level
class OrderService:
    def save(self, order):
        db = MySQLDatabase()  # locked to MySQL
        db.insert(order)

# With DIP — both depend on abstraction
from abc import ABC, abstractmethod

class OrderRepository(ABC):
    @abstractmethod
    def save(self, order): ...

class MySQLOrderRepository(OrderRepository):
    def save(self, order):
        # MySQL-specific code
        ...

class OrderService:
    def __init__(self, repo: OrderRepository):
        self.repo = repo

    def place_order(self, order):
        # business logic...
        self.repo.save(order)
```

**Result:** The database becomes a *plugin* to the business rules.

### 3.3 Functional Programming

> Discipline imposed on **assignment** (immutability).

Variables in functional languages do not vary. All race conditions, deadlocks, and concurrent update problems are caused by mutable variables. If nothing mutates, concurrency is trivial.

**Architectural tactic — Segregation of Mutability:**

```python
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class Transaction:
    amount: float
    type: str  # "deposit" or "withdrawal"

# Immutable component: pure calculation
def compute_balance(transactions: List[Transaction]) -> float:
    return sum(
        t.amount if t.type == "deposit" else -t.amount
        for t in transactions
    )

# Mutable component: isolated, protected
class TransactionStore:
    def __init__(self):
        self._transactions: List[Transaction] = []

    def add(self, txn: Transaction):
        self._transactions.append(txn)

    @property
    def balance(self) -> float:
        return compute_balance(self._transactions)
```

**Event Sourcing** is this idea at scale: store transactions, not state. Compute state on demand. Nothing is ever deleted or updated — only appended. (This is how source control works.)

---

## 4. SOLID Principles

SOLID tells us how to arrange functions and data into classes/modules so they **tolerate change**, are **easy to understand**, and form **reusable components**.

### 4.1 SRP — Single Responsibility Principle

> A module should be responsible to one, and only one, **actor** (group of stakeholders).

SRP is **NOT** "a function should do one thing." It's about who requests changes.

```python
# BAD — one class, three actors
class Employee:
    def calculate_pay(self): ...      # Accounting (CFO)
    def report_hours(self): ...       # HR (COO)
    def save(self): ...               # DBA (CTO)

# GOOD — separate classes per actor
class PayCalculator:
    def calculate_pay(self, employee_data): ...

class HourReporter:
    def report_hours(self, employee_data): ...

class EmployeeSaver:
    def save(self, employee_data): ...

# Facade ties them together
class EmployeeFacade:
    def __init__(self):
        self._pay = PayCalculator()
        self._hours = HourReporter()
        self._saver = EmployeeSaver()

    def calculate_pay(self, data):
        return self._pay.calculate_pay(data)

    def report_hours(self, data):
        return self._hours.report_hours(data)

    def save(self, data):
        return self._saver.save(data)
```

**Danger of violating SRP:** The CFO's team changes `calculate_pay()`, unknowingly breaking `report_hours()` because both share a helper function (`regularHours()`). The COO's budget is now wrong by millions.

### 4.2 OCP — Open-Closed Principle

> Software should be open for extension but closed for modification.

Achieve this by organizing components into a **dependency hierarchy**. Higher-level components (business rules) are protected from changes in lower-level components (UI, database).

```python
from abc import ABC, abstractmethod

class ReportGenerator(ABC):
    @abstractmethod
    def generate(self, data: dict) -> str: ...

class WebReportGenerator(ReportGenerator):
    def generate(self, data: dict) -> str:
        return f"<html><body>{data}</body></html>"

class PDFReportGenerator(ReportGenerator):
    def generate(self, data: dict) -> str:
        return f"PDF: {data}"

class FinancialInteractor:
    """Highest-level policy — protected from presenter changes."""
    def __init__(self, report_gen: ReportGenerator):
        self.report_gen = report_gen

    def create_report(self, financial_data: dict) -> str:
        summary = self._analyze(financial_data)
        return self.report_gen.generate(summary)

    def _analyze(self, data: dict) -> dict:
        return {"total": sum(data.values()), "items": len(data)}
```

Adding a new output format (CSV, Excel) = add a new class. Zero changes to `FinancialInteractor`.

### 4.3 LSP — Liskov Substitution Principle

> If S is a subtype of T, objects of type T can be replaced with objects of type S without altering the correctness of the program.

```python
# VIOLATION — the classic Square/Rectangle problem
class Rectangle:
    def __init__(self, w, h):
        self._w = w
        self._h = h

    def set_width(self, w):
        self._w = w

    def set_height(self, h):
        self._h = h

    def area(self):
        return self._w * self._h

class Square(Rectangle):
    def set_width(self, w):
        self._w = w
        self._h = w  # side effect!

    def set_height(self, h):
        self._w = h
        self._h = h  # side effect!

r: Rectangle = Square(5, 5)
r.set_width(10)
r.set_height(2)
assert r.area() == 20  # FAILS! area is 4

# FIX: don't use inheritance here; use separate types
# or use immutable value objects
```

**LSP applies to architecture too.** If your taxi aggregator relies on REST interfaces, and one provider abbreviates `destination` to `dest`, you need special-case code. This pollutes the architecture with `if` statements and configuration tables.

### 4.4 ISP — Interface Segregation Principle

> Don't force clients to depend on methods they don't use.

```python
# BAD — fat interface
class MultiFunctionDevice(ABC):
    @abstractmethod
    def print(self, doc): ...
    @abstractmethod
    def scan(self, doc): ...
    @abstractmethod
    def fax(self, doc): ...

# SimplePrinter is forced to implement scan() and fax()

# GOOD — segregated interfaces
class Printer(ABC):
    @abstractmethod
    def print(self, doc): ...

class Scanner(ABC):
    @abstractmethod
    def scan(self, doc): ...

class SimplePrinter(Printer):
    def print(self, doc):
        ...
```

**At the architectural level:** If your system depends on a framework F, and F depends on database D, then features in D you don't use can still force redeployments of your system.

### 4.5 DIP — Dependency Inversion Principle

> High-level modules should not depend on low-level modules. Both should depend on abstractions.

**Practical rules:**
- Don't refer to volatile concrete classes — refer to abstract interfaces
- Don't derive from volatile concrete classes
- Don't override concrete functions
- Never mention the name of anything concrete and volatile

```python
from abc import ABC, abstractmethod

# Abstraction (defined in high-level module)
class NotificationSender(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str): ...

# Concrete implementation (low-level module)
class EmailSender(NotificationSender):
    def send(self, recipient: str, message: str):
        print(f"Email to {recipient}: {message}")

class SMSSender(NotificationSender):
    def send(self, recipient: str, message: str):
        print(f"SMS to {recipient}: {message}")

# High-level policy
class OrderService:
    def __init__(self, notifier: NotificationSender):
        self.notifier = notifier

    def complete_order(self, order):
        # ... business logic ...
        self.notifier.send(order.customer_email, "Order confirmed!")

# Factory / Main wires it up
service = OrderService(EmailSender())
```

All source code dependencies cross the boundary pointing **toward** the abstraction.

---

## 5. Component Principles — Cohesion

Components are the **units of deployment** (jar files, pip packages, DLLs). Three principles guide what goes inside them:

### 5.1 REP — Reuse/Release Equivalence Principle

> The granule of reuse is the granule of release.

Classes grouped into a component must share a common theme and be **releasable together** with a version number. If you can't explain why they're in the same package, they shouldn't be.

### 5.2 CCP — Common Closure Principle

> Gather classes that change for the same reasons and at the same times. Separate classes that change at different times or for different reasons.

This is SRP for components. Minimize the number of components affected by any single change.

### 5.3 CRP — Common Reuse Principle

> Don't force users of a component to depend on things they don't need.

This is ISP for components. If you depend on a component, you should use *every* class in it. Otherwise you'll be redeployed for changes you don't care about.

### The Tension Triangle

```
          REP
         /    \
  (too many     (too many
   unneeded      releases)
   releases)
       /            \
     CCP ---------- CRP
      (too many components
       changed per feature)
```

- **REP + CCP** → components too big, dragging in unneeded stuff
- **REP + CRP** → too many components affected per change
- **CCP + CRP** → not reusable

**A good architect finds the right position in this triangle for the project's current needs.** Early in development, favor CCP (develop-ability). As the project matures and others reuse it, shift toward REP.

---

## 6. Component Principles — Coupling

### 6.1 ADP — Acyclic Dependencies Principle

> Allow no cycles in the component dependency graph.

Cycles create "morning after syndrome" — someone changes a component you depend on, and your code breaks.

```
✅ Acyclic (DAG):
  Main → Controllers → Interactors → Entities
                    ↘ Presenters ↗

❌ Cyclic:
  Entities → Authorizer → Interactors → Entities  (CYCLE!)
```

**Breaking cycles:**
1. **Dependency Inversion:** Create an interface in Entities, implement it in Authorizer
2. **New component:** Extract shared code into a new component both depend on

### 6.2 SDP — Stable Dependencies Principle

> Depend in the direction of stability.

**Stability** = hard to change (many dependents). Measured by Instability metric:

```
I = Fan-out / (Fan-in + Fan-out)

I = 0  →  maximally stable (many depend on you, you depend on nothing)
I = 1  →  maximally unstable (nobody depends on you, you depend on many)
```

Dependencies should flow from high-I to low-I components.

### 6.3 SAP — Stable Abstractions Principle

> A component should be as abstract as it is stable.

Stable components should be abstract (so they can be extended without modification). Unstable components should be concrete (easy to change).

```
Abstractness (A) = abstract classes / total classes

The Main Sequence: the line from (I=1, A=0) to (I=0, A=1)

Zone of Pain (0,0):   concrete + stable    = rigid, hard to change
Zone of Uselessness (1,1): abstract + unstable = nobody uses it

Good components sit ON or NEAR the Main Sequence.
```

---

## 7. What Is Architecture?

> The architecture of a software system is the shape given to it by those who build it — the division into components, their arrangement, and the ways they communicate.

**Purpose:** Facilitate development, deployment, operation, and maintenance.

**Strategy:** Leave as many options open as possible, for as long as possible.

### Policy vs. Detail

| Policy | Detail |
|--------|--------|
| Business rules | Database |
| Domain logic | Web framework |
| Use case workflows | UI technology |
| Core calculations | Communication protocols |

**The architect's job:** Make policy independent of details so detail decisions can be deferred.

```python
# The high-level policy doesn't know about the database
class LoanInteractor:
    def __init__(self, loan_repo, interest_calculator):
        self.loan_repo = loan_repo
        self.interest_calculator = interest_calculator

    def calculate_monthly_payment(self, loan_id: str) -> float:
        loan = self.loan_repo.find(loan_id)
        return self.interest_calculator.monthly_payment(
            loan.balance, loan.rate, loan.term_months
        )

# Database decision deferred — could be file, SQL, NoSQL, in-memory
# Framework decision deferred — could be Flask, FastAPI, CLI, gRPC
```

**FitNesse example from the book:** Uncle Bob's team built FitNesse for 18 months without a database. They used an interface (`WikiPage`) with in-memory and then flat-file implementations. When a customer needed MySQL, he wrote a `MySqlWikiPage` derivative in one day. The flat files worked so well that MySQL was never needed.

> A good architect maximizes the number of decisions NOT made.

---

## 8. Independence

A good architecture supports:

1. **Use cases** — the intent of the system is visible in the structure
2. **Operation** — throughput, latency, and scalability requirements
3. **Development** — independent teams can work without interference (Conway's Law)
4. **Deployment** — "immediate deployment" with a single action

### Decoupling Strategies

**Horizontal layers:** UI, business rules, database — separated because they change for different reasons.

**Vertical slices:** Each use case cuts through all layers. The "add order" use case is separate from "delete order."

```
┌─────────────────────────────────────────┐
│              UI Layer                   │
├────────┬────────┬────────┬──────────────┤
│ Add    │ Delete │ View   │ Search       │  ← Vertical use cases
│ Order  │ Order  │ Order  │ Orders       │
├────────┴────────┴────────┴──────────────┤
│          Business Rules Layer           │
├─────────────────────────────────────────┤
│          Database Layer                 │
└─────────────────────────────────────────┘
```

### Decoupling Modes

| Mode | Mechanism | When |
|------|-----------|------|
| **Source level** | Modules in same process, function calls | Start here |
| **Deployment level** | Separate jars/packages, still function calls | When teams need independent deployment |
| **Service level** | Separate processes, network calls | When operational scaling demands it |

> A good architecture allows a system to be born as a monolith, grow into deployable units, and eventually become independent services — and reverse if needed.

### True vs. Accidental Duplication

Two screens look similar? Two database schemas look similar? **Don't unify them.** If they change for different reasons and at different rates, it's *accidental* duplication. Merging them will couple unrelated things.

---

## 9. Boundaries: Drawing Lines

> Software architecture is the art of drawing lines (boundaries) that separate software elements and restrict knowledge between them.

**Where to draw lines:** Between things that matter (business rules) and things that don't (details like DB, UI, frameworks).

```python
from abc import ABC, abstractmethod

# ─── BOUNDARY ─────────────────────────────
# Business Rules side (knows nothing about DB)

class ProductRepository(ABC):
    @abstractmethod
    def find_by_id(self, product_id: str) -> dict: ...

    @abstractmethod
    def save(self, product: dict): ...

class PricingService:
    def __init__(self, repo: ProductRepository):
        self.repo = repo

    def apply_discount(self, product_id: str, pct: float) -> dict:
        product = self.repo.find_by_id(product_id)
        product["price"] *= (1 - pct)
        self.repo.save(product)
        return product

# ─── BOUNDARY ─────────────────────────────
# Database side (depends on Business Rules via interface)

class PostgresProductRepository(ProductRepository):
    def find_by_id(self, product_id: str) -> dict:
        # SELECT * FROM products WHERE id = ...
        ...

    def save(self, product: dict):
        # UPDATE products SET ...
        ...
```

The boundary arrow points **inward** — the database knows about business rules (it implements their interfaces), but business rules know nothing about the database.

### Plugin Architecture

The database is a plugin. The UI is a plugin. Frameworks are plugins. Just like ReSharper is a plugin to Visual Studio — the plugin team can't damage the host, but the host could break the plugin.

---

## 10. Boundary Anatomy

Boundaries come in different physical forms:

| Boundary Type | Communication Cost | Deployment |
|---|---|---|
| **Monolith** (source-level) | Function calls — nearly free | Single executable |
| **Deployment components** (DLLs, jars) | Function calls — nearly free | Independent binaries |
| **Local processes** | IPC, sockets — moderate cost | Separate address spaces |
| **Services** | Network — expensive, high latency | Fully independent |

**Key insight:** Even in a monolith, proper boundaries with polymorphism allow teams to work independently. Boundaries are about managing **source code dependencies**, not physical separation.

---

## 11. Policy and Level

> **Level** = the distance from the inputs and outputs. Higher level = farther from I/O.

```python
# BAD — high-level encrypt depends on low-level I/O
def encrypt():
    while True:
        char = read_from_keyboard()
        translated = translate(char)
        write_to_screen(translated)

# GOOD — I/O plugs into the high-level policy
from abc import ABC, abstractmethod

class CharReader(ABC):
    @abstractmethod
    def read(self) -> str: ...

class CharWriter(ABC):
    @abstractmethod
    def write(self, char: str): ...

class Encryptor:
    def __init__(self, reader: CharReader, writer: CharWriter, table: dict):
        self.reader = reader
        self.writer = writer
        self.table = table

    def run(self):
        while True:
            char = self.reader.read()
            if char is None:
                break
            self.writer.write(self.table.get(char, char))

class ConsoleReader(CharReader):
    def read(self) -> str:
        return input()

class FileWriter(CharWriter):
    def __init__(self, path: str):
        self.f = open(path, "w")

    def write(self, char: str):
        self.f.write(char)
```

**Higher-level policies change less frequently and for more important reasons.** Lower-level policies (I/O) change often and for trivial reasons. Dependencies should point from low-level to high-level.

---

## 12. Business Rules — Entities & Use Cases

### Entities — Critical Business Rules

An Entity encapsulates **Critical Business Rules** operating on **Critical Business Data**. These rules would exist even without a computer.

```python
from dataclasses import dataclass

@dataclass
class Loan:
    balance: float
    rate: float
    term_months: int

    def monthly_payment(self) -> float:
        """Critical Business Rule: exists whether automated or not."""
        monthly_rate = self.rate / 12
        return self.balance * (
            monthly_rate * (1 + monthly_rate) ** self.term_months
        ) / (
            (1 + monthly_rate) ** self.term_months - 1
        )

    def is_in_good_standing(self, months_paid: int) -> bool:
        return months_paid >= 0
```

Entities are **pure business** — no knowledge of databases, UIs, or frameworks.

### Use Cases — Application-Specific Business Rules

A Use Case orchestrates Entities. It describes how an automated system is used — input, processing steps, output.

```python
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Request/Response models — plain data structures
@dataclass
class CreateLoanRequest:
    customer_id: str
    amount: float
    rate: float
    term_months: int

@dataclass
class CreateLoanResponse:
    loan_id: str
    monthly_payment: float
    approved: bool
    rejection_reason: str = ""

# Gateway interface (defined here, implemented in DB layer)
class LoanGateway(ABC):
    @abstractmethod
    def save(self, loan: Loan) -> str: ...

    @abstractmethod
    def find_by_id(self, loan_id: str) -> Loan: ...

class CreditScoreService(ABC):
    @abstractmethod
    def get_score(self, customer_id: str) -> int: ...

# The Use Case
class CreateLoanUseCase:
    def __init__(self, loan_gateway: LoanGateway, credit: CreditScoreService):
        self.loan_gateway = loan_gateway
        self.credit = credit

    def execute(self, request: CreateLoanRequest) -> CreateLoanResponse:
        score = self.credit.get_score(request.customer_id)

        if score < 500:
            return CreateLoanResponse(
                loan_id="", monthly_payment=0,
                approved=False, rejection_reason="Credit score too low"
            )

        loan = Loan(
            balance=request.amount,
            rate=request.rate,
            term_months=request.term_months,
        )

        loan_id = self.loan_gateway.save(loan)

        return CreateLoanResponse(
            loan_id=loan_id,
            monthly_payment=loan.monthly_payment(),
            approved=True,
        )
```

**Key rules:**
- Entities know **nothing** about use cases (DIP — higher level)
- Use cases know nothing about the UI or database format
- Request/Response models are **not** Entity objects — they change for different reasons
- Use cases don't mention HTTP, HTML, SQL, or any framework

---

## 13. Screaming Architecture

> When you look at the top-level directory structure, does it scream "Health Care System" or does it scream "Django"?

```
# BAD — screams "framework"
myapp/
  views/
  models/
  serializers/
  urls.py

# GOOD — screams "health care system"
healthcare/
  patients/
    entities.py
    use_cases.py
    repository.py
  appointments/
    entities.py
    use_cases.py
    repository.py
  prescriptions/
    entities.py
    use_cases.py
    repository.py
  infrastructure/
    django_views.py
    postgres_repos.py
    api_routes.py
```

**Tests prove this:** If your architecture is truly about use cases, you can unit-test all business rules **without** a web server, without a database, without any framework.

> Frameworks are options to be left open, not architectures to be conformed to.

---

## 14. The Clean Architecture

The famous concentric circles diagram. All prior architectures (Hexagonal/Ports & Adapters, DCI, BCE) converge on the same idea:

```
┌──────────────────────────────────────────────────────┐
│                 Frameworks & Drivers                 │
│   (Web, DB, Devices, External Interfaces, UI)        │
│  ┌────────────────────────────────────────────────┐  │
│  │            Interface Adapters                  │  │
│  │   (Controllers, Presenters, Gateways)          │  │
│  │  ┌──────────────────────────────────────────┐  │  │
│  │  │          Use Cases                       │  │  │
│  │  │   (Application Business Rules)           │  │  │
│  │  │  ┌────────────────────────────────────┐  │  │  │
│  │  │  │         Entities                   │  │  │  │
│  │  │  │  (Enterprise Business Rules)       │  │  │  │
│  │  │  └────────────────────────────────────┘  │  │  │
│  │  └──────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### THE DEPENDENCY RULE

> Source code dependencies must point only **inward**, toward higher-level policies.

Nothing in an inner circle can know anything about an outer circle. No name declared in an outer circle may be mentioned by code in an inner circle.

### The Four Layers

| Layer | Contains | Changes When |
|-------|----------|--------------|
| **Entities** | Critical business rules + data | Business rules change (rare) |
| **Use Cases** | Application-specific workflows | Application behavior changes |
| **Interface Adapters** | Controllers, presenters, gateways, MVC | Format/protocol changes |
| **Frameworks & Drivers** | Web framework, DB driver, UI toolkit | Tool/library changes |

### Crossing Boundaries

Use DIP. When a use case needs to call a presenter (outer circle), it calls an **output port interface** defined in the inner circle, implemented in the outer circle.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

# ──── ENTITIES (innermost) ────
@dataclass
class User:
    id: str
    name: str
    email: str

# ──── USE CASES ────
@dataclass
class GetUserRequest:
    user_id: str

@dataclass
class GetUserResponse:
    name: str
    email: str

class UserOutputPort(ABC):
    @abstractmethod
    def present(self, response: GetUserResponse): ...

class UserRepository(ABC):
    @abstractmethod
    def find_by_id(self, user_id: str) -> User: ...

class GetUserUseCase:
    def __init__(self, repo: UserRepository, presenter: UserOutputPort):
        self.repo = repo
        self.presenter = presenter

    def execute(self, request: GetUserRequest):
        user = self.repo.find_by_id(request.user_id)
        response = GetUserResponse(name=user.name, email=user.email)
        self.presenter.present(response)

# ──── INTERFACE ADAPTERS ────
class JsonPresenter(UserOutputPort):
    def __init__(self):
        self.view_model = {}

    def present(self, response: GetUserResponse):
        self.view_model = {
            "user_name": response.name,
            "user_email": response.email,
        }

class SqlUserRepository(UserRepository):
    def find_by_id(self, user_id: str) -> User:
        # SELECT * FROM users WHERE id = ...
        return User(id=user_id, name="Alice", email="alice@example.com")

# ──── FRAMEWORKS & DRIVERS (outermost) ────
# FastAPI route, Django view, CLI command, etc.
def handle_get_user(user_id: str) -> dict:
    repo = SqlUserRepository()
    presenter = JsonPresenter()
    use_case = GetUserUseCase(repo, presenter)
    use_case.execute(GetUserRequest(user_id=user_id))
    return presenter.view_model
```

### Data Crossing Boundaries

Always pass **simple data structures** (dataclasses, dicts, tuples) — never Entity objects or database rows. The data format should be whatever is most convenient for the **inner** circle.

---

## 15. Presenters and Humble Objects

### The Humble Object Pattern

Split behavior into two parts:
1. **Humble Object** — hard to test, kept stupidly simple (e.g., the View)
2. **Testable Object** — contains all the interesting logic (e.g., the Presenter)

```python
from dataclasses import dataclass, field
from typing import List

# Presenter (testable)
@dataclass
class InvoiceViewModel:
    customer_name: str = ""
    total: str = ""
    line_items: List[dict] = field(default_factory=list)
    is_overdue: bool = False
    overdue_color: str = ""

class InvoicePresenter:
    def present(self, invoice_data: dict) -> InvoiceViewModel:
        vm = InvoiceViewModel()
        vm.customer_name = invoice_data["customer"]
        vm.total = f"${invoice_data['total']:,.2f}"
        vm.is_overdue = invoice_data["days_past_due"] > 30
        vm.overdue_color = "red" if vm.is_overdue else "black"
        vm.line_items = [
            {"desc": li["desc"], "amount": f"${li['amount']:,.2f}"}
            for li in invoice_data["items"]
        ]
        return vm

# View (humble — just dumps ViewModel to screen)
def render_invoice_html(vm: InvoiceViewModel) -> str:
    color = vm.overdue_color
    return f"<h1>{vm.customer_name}</h1><p style='color:{color}'>{vm.total}</p>"
```

### Where Humble Objects Appear

| Boundary | Testable Side | Humble Side |
|----------|---------------|-------------|
| UI | Presenter | View |
| Database | Use Case Interactor | Database Gateway implementation |
| Services | Application logic | Service listener/formatter |
| ORMs | — | Data Mapper (ORM is in DB layer) |

**ORMs are not object-relational mappers.** Objects aren't data structures from their user's perspective. ORMs are data mappers — they load data into structures from relational tables. They belong in the database layer.

---

## 16. Partial Boundaries

Full architectural boundaries are expensive. Three lighter alternatives:

### Strategy 1: Skip the Last Step

Do all the design work (interfaces, data structures, dependency inversion) but keep everything in the **same component**. No separate deployment, no version tracking.

### Strategy 2: One-Dimensional Boundary (Strategy Pattern)

```python
from abc import ABC, abstractmethod

class ServiceBoundary(ABC):
    @abstractmethod
    def execute(self, data): ...

class ServiceImpl(ServiceBoundary):
    def execute(self, data):
        return process(data)

class Client:
    def __init__(self, service: ServiceBoundary):
        self.service = service
```

Dependency inversion in one direction only. Cheaper, but easier to degrade.

### Strategy 3: Facade

```python
class PaymentFacade:
    """Client only knows about this facade."""
    def charge(self, amount, card):
        return StripeGateway().charge(amount, card)

    def refund(self, transaction_id):
        return StripeGateway().refund(transaction_id)
```

No dependency inversion at all. Very simple. But the client has transitive dependencies on everything behind the facade.

---

## 17. The Main Component

`Main` is the **dirtiest, lowest-level component**. It is a plugin that:
- Creates factories, strategies, and global facilities
- Wires dependencies (this is where DI frameworks belong)
- Hands control to the high-level abstract system

```python
# main.py — the ultimate detail
from infrastructure.postgres_repos import PostgresUserRepository
from infrastructure.smtp_notifier import SmtpNotifier
from use_cases.register_user import RegisterUserUseCase
from interface_adapters.web.flask_app import create_app

def main():
    # Wire everything up
    user_repo = PostgresUserRepository(connection_string="...")
    notifier = SmtpNotifier(smtp_host="mail.example.com")
    register_use_case = RegisterUserUseCase(user_repo, notifier)

    app = create_app(register_use_case=register_use_case)
    app.run(port=8080)

if __name__ == "__main__":
    main()
```

You can have **multiple Main components**: one for dev, one for test, one for production, one per region/customer.

---

## 18. Services: Great and Small

**Services are NOT inherently architectural.** They're just function calls across process/network boundaries. A service might be a single component or might contain multiple components separated by architectural boundaries.

### The Decoupling Fallacy

Services are decoupled at the variable level but **strongly coupled by shared data**. Add a field to a data record, and every service touching that record must change.

### The Kitty Problem

Imagine a taxi aggregator with microservices: `TaxiUI`, `TaxiFinder`, `TaxiSelector`, `TaxiDispatcher`. Marketing says: "Add kitten delivery service." How many services change? **All of them.** The services are coupled by cross-cutting concerns.

### The Fix: Component-Based Services

Design services with internal component architectures following SOLID:

```python
# The TaxiFinder service uses internal polymorphism
from abc import ABC, abstractmethod

class TransportFinder(ABC):
    @abstractmethod
    def find_candidates(self, pickup, destination): ...

class RideFinder(TransportFinder):
    def find_candidates(self, pickup, destination):
        # find available taxis
        ...

class KittenDeliveryFinder(TransportFinder):
    def find_candidates(self, pickup, destination):
        # find taxis near kitten collection points
        ...

# Adding KittenDeliveryFinder doesn't change RideFinder
# New jar/package deployed alongside existing code (OCP)
```

> Architectural boundaries don't fall **between** services. They run **through** services, dividing them into components.

---

## 19. The Test Boundary

Tests are part of the system architecture. They are the **outermost circle** — nothing depends on them, they depend on everything.

### The Fragile Tests Problem

Tests coupled to the GUI are fragile. Change a navigation structure and 1,000 tests break. Fragile tests make the system **rigid** — developers resist changes because tests break.

### Design for Testability

Create a **Testing API** that lets tests verify business rules without the UI:

```python
# Don't test through the GUI
def test_order_total_bad():
    browser.click("add_to_cart")
    browser.click("checkout")
    assert browser.find("#total").text == "$42.00"  # fragile!

# Test through the use case directly
def test_order_total_good():
    repo = InMemoryProductRepo({"SKU1": Product("Widget", 42.0)})
    use_case = CalculateOrderTotal(repo)
    result = use_case.execute(OrderRequest(items=[("SKU1", 1)]))
    assert result.total == 42.0  # stable!
```

### Avoid Structural Coupling

Don't mirror production class hierarchy 1:1 in tests. Test behaviors through the API, not individual methods. This frees production code to evolve (become more abstract) while tests evolve in the opposite direction (become more concrete and specific).

---

## 20. The Database Is a Detail

The database is a mechanism for storing and retrieving data. **It is not the data model.** The data model is significant; the technology is a detail.

```python
# Your business rules don't care if it's SQL, NoSQL, or flat files

class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> str: ...

    @abstractmethod
    def find_by_id(self, order_id: str) -> Order: ...

# Implementations are details — interchangeable plugins
class PostgresOrderRepo(OrderRepository): ...
class MongoOrderRepo(OrderRepository): ...
class InMemoryOrderRepo(OrderRepository): ...  # great for tests
class FileSystemOrderRepo(OrderRepository): ...
```

The data flows between use cases and entities as plain data structures. SQL, schemas, and query languages stay behind the boundary.

---

## 21. The Web Is a Detail

The web is a **delivery mechanism** — an I/O device. Your architecture should not know whether it's being delivered over the web, as a desktop app, a CLI, or a gRPC service.

```python
# The use case doesn't know about HTTP
class PlaceOrderUseCase:
    def execute(self, request: PlaceOrderRequest) -> PlaceOrderResponse:
        ...  # pure business logic

# Web adapter — thin glue
from fastapi import FastAPI
app = FastAPI()

@app.post("/orders")
def place_order_endpoint(body: dict):
    request = PlaceOrderRequest(**body)
    use_case = get_place_order_use_case()  # from DI
    response = use_case.execute(request)
    return {"order_id": response.order_id, "total": response.total}

# CLI adapter — equally thin glue
import sys
def cli_main():
    data = json.loads(sys.argv[1])
    request = PlaceOrderRequest(**data)
    use_case = get_place_order_use_case()
    response = use_case.execute(request)
    print(f"Order {response.order_id}: ${response.total}")
```

Same business logic, different delivery mechanisms. The decision about web vs. CLI vs. gRPC is deferred.

---

## 22. Frameworks Are Details

Framework authors want you to couple **tightly**. They show you the all-in, let-the-framework-do-everything approach. This is an **asymmetric marriage** — you take on all the risk.

**The risks:**
- Framework evolves in a direction that doesn't serve you
- New, better framework appears but you're locked in
- Framework features you don't need drag in dependencies

**The strategy:**
- Treat the framework as a plugin in the outer circle
- Don't let framework base classes creep into your entities or use cases
- Use the framework — don't marry it

```python
# BAD — Entity inherits from Django Model (framework in core)
from django.db import models

class Order(models.Model):
    customer = models.CharField(max_length=100)
    total = models.DecimalField(...)

# GOOD — Entity is framework-free
@dataclass
class Order:
    customer: str
    total: float

# Django model is in the infrastructure layer
class OrderModel(models.Model):
    customer = models.CharField(max_length=100)
    total = models.DecimalField(...)

class DjangoOrderRepository(OrderRepository):
    def save(self, order: Order) -> str:
        model = OrderModel(customer=order.customer, total=order.total)
        model.save()
        return str(model.pk)
```

---

## 23. Package Organization Strategies

Four ways to organize source code (Chapter 34 — "The Missing Chapter" by Simon Brown):

### Package by Layer

```
com.myapp/
  controllers/
    OrderController.py
  services/
    OrderService.py
  repositories/
    OrderRepository.py
```

Simple horizontal slicing. Doesn't scale — the "services" folder becomes a dumping ground.

### Package by Feature

```
com.myapp/
  orders/
    OrderController.py
    OrderService.py
    OrderRepository.py
  customers/
    CustomerController.py
    ...
```

Better — related code is co-located. But still doesn't enforce dependency rules.

### Ports and Adapters

```
com.myapp/
  domain/
    Order.py
    OrderRepository.py    # port (interface)
  application/
    PlaceOrderUseCase.py  # orchestration
  adapters/
    web/
      OrderController.py  # driving adapter
    persistence/
      SqlOrderRepository.py  # driven adapter
```

Domain is at the center. Adapters plug in. Dependency arrows point inward.

### Package by Component

```
com.myapp/
  orders/
    OrderComponent.py        # facade
    internal/
      OrderService.py
      OrderRepository.py     # interface
      SqlOrderRepository.py
  web/
    OrderController.py
```

Bundles the "inside" of a component. The component exposes a single facade. Internal classes are implementation details.

**The best approach depends on your team and project.** But regardless of choice, **enforce the dependency rules** — ideally with compiler/linter checks, not just developer discipline.

---

## 24. Full Example: E-Commerce System

A complete Clean Architecture implementation:

```
ecommerce/
├── entities/
│   ├── product.py
│   ├── order.py
│   └── customer.py
├── use_cases/
│   ├── place_order.py
│   ├── cancel_order.py
│   ├── ports/
│   │   ├── order_repository.py
│   │   ├── payment_gateway.py
│   │   ├── inventory_service.py
│   │   └── notification_sender.py
│   └── dto/
│       ├── place_order_request.py
│       └── place_order_response.py
├── interface_adapters/
│   ├── presenters/
│   │   └── order_json_presenter.py
│   └── controllers/
│       └── order_controller.py
├── infrastructure/
│   ├── persistence/
│   │   ├── postgres_order_repo.py
│   │   └── in_memory_order_repo.py
│   ├── payment/
│   │   └── stripe_payment_gateway.py
│   ├── notifications/
│   │   └── email_notification_sender.py
│   └── web/
│       └── fastapi_app.py
└── main.py
```

### Entities

```python
# entities/product.py
from dataclasses import dataclass

@dataclass
class Product:
    id: str
    name: str
    price: float
    stock: int

    def is_available(self, quantity: int) -> bool:
        return self.stock >= quantity

    def reserve(self, quantity: int) -> "Product":
        if not self.is_available(quantity):
            raise ValueError(f"Insufficient stock for {self.name}")
        return Product(
            id=self.id, name=self.name,
            price=self.price, stock=self.stock - quantity,
        )
```

```python
# entities/order.py
from dataclasses import dataclass, field
from typing import List
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

@dataclass
class OrderLine:
    product_id: str
    product_name: str
    unit_price: float
    quantity: int

    @property
    def subtotal(self) -> float:
        return self.unit_price * self.quantity

@dataclass
class Order:
    id: str
    customer_id: str
    lines: List[OrderLine] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PENDING

    @property
    def total(self) -> float:
        return sum(line.subtotal for line in self.lines)

    def confirm(self) -> "Order":
        if self.status != OrderStatus.PENDING:
            raise ValueError("Only pending orders can be confirmed")
        return Order(
            id=self.id, customer_id=self.customer_id,
            lines=self.lines, status=OrderStatus.CONFIRMED,
        )

    def cancel(self) -> "Order":
        if self.status == OrderStatus.CANCELLED:
            raise ValueError("Order already cancelled")
        return Order(
            id=self.id, customer_id=self.customer_id,
            lines=self.lines, status=OrderStatus.CANCELLED,
        )
```

### Ports (Interfaces)

```python
# use_cases/ports/order_repository.py
from abc import ABC, abstractmethod
from entities.order import Order

class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> str: ...

    @abstractmethod
    def find_by_id(self, order_id: str) -> Order: ...

# use_cases/ports/payment_gateway.py
class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, customer_id: str, amount: float) -> str: ...

# use_cases/ports/notification_sender.py
class NotificationSender(ABC):
    @abstractmethod
    def send_order_confirmation(self, customer_id: str, order_id: str): ...
```

### Use Case

```python
# use_cases/place_order.py
from dataclasses import dataclass
from typing import List
from entities.order import Order, OrderLine
from use_cases.ports.order_repository import OrderRepository
from use_cases.ports.payment_gateway import PaymentGateway
from use_cases.ports.notification_sender import NotificationSender
import uuid

@dataclass
class PlaceOrderRequest:
    customer_id: str
    items: List[dict]  # [{"product_id": ..., "name": ..., "price": ..., "qty": ...}]

@dataclass
class PlaceOrderResponse:
    order_id: str
    total: float
    success: bool
    error: str = ""

class PlaceOrderUseCase:
    def __init__(
        self,
        order_repo: OrderRepository,
        payment: PaymentGateway,
        notifier: NotificationSender,
    ):
        self.order_repo = order_repo
        self.payment = payment
        self.notifier = notifier

    def execute(self, request: PlaceOrderRequest) -> PlaceOrderResponse:
        lines = [
            OrderLine(
                product_id=item["product_id"],
                product_name=item["name"],
                unit_price=item["price"],
                quantity=item["qty"],
            )
            for item in request.items
        ]

        order = Order(
            id=str(uuid.uuid4()),
            customer_id=request.customer_id,
            lines=lines,
        )

        try:
            self.payment.charge(request.customer_id, order.total)
        except Exception as e:
            return PlaceOrderResponse(
                order_id="", total=0, success=False,
                error=f"Payment failed: {e}"
            )

        confirmed_order = order.confirm()
        self.order_repo.save(confirmed_order)
        self.notifier.send_order_confirmation(
            request.customer_id, confirmed_order.id
        )

        return PlaceOrderResponse(
            order_id=confirmed_order.id,
            total=confirmed_order.total,
            success=True,
        )
```

### Infrastructure (Plugins)

```python
# infrastructure/persistence/in_memory_order_repo.py
from entities.order import Order
from use_cases.ports.order_repository import OrderRepository

class InMemoryOrderRepository(OrderRepository):
    def __init__(self):
        self._store: dict[str, Order] = {}

    def save(self, order: Order) -> str:
        self._store[order.id] = order
        return order.id

    def find_by_id(self, order_id: str) -> Order:
        if order_id not in self._store:
            raise KeyError(f"Order {order_id} not found")
        return self._store[order_id]
```

### Tests (Outermost Circle)

```python
# tests/test_place_order.py
from use_cases.place_order import PlaceOrderUseCase, PlaceOrderRequest
from infrastructure.persistence.in_memory_order_repo import InMemoryOrderRepository

class FakePaymentGateway:
    def charge(self, customer_id, amount):
        return "txn_123"

class FakeNotifier:
    def __init__(self):
        self.sent = []

    def send_order_confirmation(self, customer_id, order_id):
        self.sent.append((customer_id, order_id))

def test_place_order_success():
    repo = InMemoryOrderRepository()
    payment = FakePaymentGateway()
    notifier = FakeNotifier()
    use_case = PlaceOrderUseCase(repo, payment, notifier)

    request = PlaceOrderRequest(
        customer_id="cust_1",
        items=[{"product_id": "p1", "name": "Widget", "price": 25.0, "qty": 2}],
    )

    response = use_case.execute(request)

    assert response.success is True
    assert response.total == 50.0
    assert len(notifier.sent) == 1

    saved = repo.find_by_id(response.order_id)
    assert saved.status.value == "confirmed"
```

No database. No web server. No framework. Pure business logic testing.

---

## 25. Full Example: Blog Platform

Showing how the same architecture works for a completely different domain:

```python
# ──── ENTITIES ────
from dataclasses import dataclass, field
from datetime import datetime
from typing import List

@dataclass(frozen=True)
class Comment:
    author: str
    body: str
    created_at: datetime

@dataclass
class Article:
    id: str
    title: str
    body: str
    author_id: str
    published: bool = False
    comments: List[Comment] = field(default_factory=list)

    def publish(self) -> "Article":
        if not self.title or not self.body:
            raise ValueError("Cannot publish article without title and body")
        return Article(
            id=self.id, title=self.title, body=self.body,
            author_id=self.author_id, published=True,
            comments=self.comments,
        )

    def add_comment(self, author: str, body: str) -> "Article":
        if not self.published:
            raise ValueError("Cannot comment on unpublished article")
        comment = Comment(author=author, body=body, created_at=datetime.now())
        return Article(
            id=self.id, title=self.title, body=self.body,
            author_id=self.author_id, published=self.published,
            comments=[*self.comments, comment],
        )

# ──── USE CASE ────
from abc import ABC, abstractmethod

class ArticleRepository(ABC):
    @abstractmethod
    def save(self, article: Article) -> str: ...
    @abstractmethod
    def find_by_id(self, article_id: str) -> Article: ...

@dataclass
class PublishArticleRequest:
    article_id: str
    editor_id: str

@dataclass
class PublishArticleResponse:
    success: bool
    error: str = ""

class PublishArticleUseCase:
    def __init__(self, repo: ArticleRepository):
        self.repo = repo

    def execute(self, request: PublishArticleRequest) -> PublishArticleResponse:
        article = self.repo.find_by_id(request.article_id)

        if article.author_id != request.editor_id:
            return PublishArticleResponse(
                success=False, error="Only the author can publish"
            )

        try:
            published = article.publish()
        except ValueError as e:
            return PublishArticleResponse(success=False, error=str(e))

        self.repo.save(published)
        return PublishArticleResponse(success=True)

# ──── INFRASTRUCTURE ADAPTER ────
class InMemoryArticleRepo(ArticleRepository):
    def __init__(self):
        self._store = {}

    def save(self, article: Article) -> str:
        self._store[article.id] = article
        return article.id

    def find_by_id(self, article_id: str) -> Article:
        return self._store[article_id]

# ──── TEST ────
def test_publish_article():
    repo = InMemoryArticleRepo()
    article = Article(id="a1", title="Clean Arch", body="Content here...", author_id="u1")
    repo.save(article)

    use_case = PublishArticleUseCase(repo)
    response = use_case.execute(PublishArticleRequest(article_id="a1", editor_id="u1"))

    assert response.success is True
    assert repo.find_by_id("a1").published is True

def test_only_author_can_publish():
    repo = InMemoryArticleRepo()
    article = Article(id="a1", title="My Post", body="...", author_id="u1")
    repo.save(article)

    use_case = PublishArticleUseCase(repo)
    response = use_case.execute(PublishArticleRequest(article_id="a1", editor_id="u999"))

    assert response.success is False
    assert "Only the author" in response.error
```

---

## 26. Clean Architecture Cheatsheet

### The Dependency Rule — One Sentence

> Source code dependencies point **inward** — from low-level details to high-level policies.

### Quick Decision Guide

```
"Where does this code go?"

Is it a business rule that exists even without a computer?
  → Entity (innermost circle)

Is it a workflow/use case that orchestrates entities?
  → Use Case layer

Is it converting data formats between layers?
  → Interface Adapter (controller, presenter, gateway)

Is it a framework, library, database, or I/O mechanism?
  → Frameworks & Drivers (outermost circle)

Does it wire everything together at startup?
  → Main component (the dirtiest detail)
```

### Principles Summary

| Principle | One-Liner |
|-----------|-----------|
| **SRP** | One module, one actor, one reason to change |
| **OCP** | Extend behavior without modifying existing code |
| **LSP** | Subtypes must be substitutable for their base types |
| **ISP** | Don't depend on things you don't use |
| **DIP** | Depend on abstractions, not concretions |
| **REP** | Group classes that are released together |
| **CCP** | Group classes that change together |
| **CRP** | Don't group classes that aren't used together |
| **ADP** | No cycles in the dependency graph |
| **SDP** | Depend in the direction of stability |
| **SAP** | Stable components should be abstract |

### Boundaries Cheatsheet

```
Draw a boundary between things that change for different reasons.

Business Rules ←── boundary ──→ Database
Business Rules ←── boundary ──→ UI
Business Rules ←── boundary ──→ Framework
Business Rules ←── boundary ──→ External Services

Arrow direction: Details depend on Policies (never the reverse)
```

### Architecture Smells

| Smell | Violation | Fix |
|-------|-----------|-----|
| Entity imports Flask/Django | DIP, Dependency Rule | Move framework to outer circle |
| Use case constructs SQL | Dependency Rule | Extract repository interface |
| Controller contains business logic | SRP | Move logic to use case |
| Test requires running database | Testability | Use in-memory repository |
| Changing UI breaks business rules | Missing boundary | Add interface adapter layer |
| Adding a feature requires changing many services | Cross-cutting concern | Use SOLID within services |
| Database schema is the domain model | DB is a detail | Separate entity from ORM model |

### The Architect's Mindset

1. **A good architect is still a programmer.** Stay close to the code.
2. **Maximize decisions not made.** Defer details as long as possible.
3. **Policy is more important than detail.** Protect business rules above all.
4. **Watch and adapt.** The right boundary decisions evolve with the project.
5. **The only way to go fast, is to go well.**

---

*Based on "Clean Architecture: A Craftsman's Guide to Software Structure and Design" by Robert C. Martin (2018). All concepts, principles, and stories attributed to the original work.*
