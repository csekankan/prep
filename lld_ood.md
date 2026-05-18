# LLD & Object-Oriented Design — Complete Interview Reference

A comprehensive guide covering every critical concept in Low-Level Design and Object-Oriented Design needed to crack top-tier software engineering interviews.

---

## Table of Contents

1. [OOP Core Principles](#1-oop-core-principles)
2. [SOLID Principles](#2-solid-principles)
3. [GRASP Principles](#3-grasp-principles)
4. [UML & Class Diagrams](#4-uml--class-diagrams)
5. [Design Patterns — Creational](#5-design-patterns--creational)
6. [Design Patterns — Structural](#6-design-patterns--structural)
7. [Design Patterns — Behavioral](#7-design-patterns--behavioral)
8. [Relationships Between Classes](#8-relationships-between-classes)
9. [Coupling & Cohesion](#9-coupling--cohesion)
10. [Design Principles Cheatsheet](#10-design-principles-cheatsheet)
11. [LLD Interview Problems — Step-by-Step](#11-lld-interview-problems--step-by-step)
    - [Parking Lot](#111-parking-lot)
    - [Library Management System](#112-library-management-system)
    - [Elevator System](#113-elevator-system)
    - [Chess Game](#114-chess-game)
    - [Snake and Ladder](#115-snake-and-ladder)
    - [ATM Machine](#116-atm-machine)
    - [Ride Sharing (Uber/Ola)](#117-ride-sharing-uberola)
    - [Hotel Booking](#118-hotel-booking)
    - [Food Delivery (Zomato/Swiggy)](#119-food-delivery-zomatoswiggy)
    - [Splitwise / Bill Splitting](#1110-splitwise--bill-splitting)
    - [Rate Limiter](#1111-rate-limiter)
    - [Logger](#1112-logger)
    - [Cache (LRU)](#1113-cache-lru)
12. [Concurrency in LLD](#12-concurrency-in-lld)
13. [Common Interview Mistakes & Red Flags](#13-common-interview-mistakes--red-flags)

---

## 1. OOP Core Principles

### 1.1 Encapsulation
Bundling data (attributes) and behavior (methods) together and hiding internal state from the outside world.

```
Goal: Protect internal state. Expose only what is necessary.
Mechanism: private/protected fields, public getters/setters
```

```python
class BankAccount:
    def __init__(self, balance: float):
        self.__balance = balance          # private

    def deposit(self, amount: float) -> None:
        if amount > 0:
            self.__balance += amount

    def get_balance(self) -> float:
        return self.__balance             # controlled access
```

**Interview Tip:** Encapsulation ≠ data hiding alone. It also means keeping related state and behavior together.

---

### 1.2 Abstraction
Exposing only what is essential and hiding complex implementation details.

```
Goal: Simplify interaction. User works with intent, not implementation.
Mechanism: abstract classes, interfaces
```

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

    @abstractmethod
    def perimeter(self) -> float: ...

class Circle(Shape):
    def __init__(self, radius: float):
        self.radius = radius

    def area(self) -> float:
        return 3.14 * self.radius ** 2

    def perimeter(self) -> float:
        return 2 * 3.14 * self.radius
```

**Interview Tip:** Abstract class = partial implementation allowed. Interface = contract only.

---

### 1.3 Inheritance
A class (child) derives properties and behavior from another class (parent), enabling code reuse.

```
Types: Single, Multilevel, Multiple (via interfaces), Hierarchical
Rule: "IS-A" relationship → use inheritance
      "HAS-A" relationship → use composition
```

```python
class Vehicle:
    def __init__(self, brand: str):
        self.brand = brand

    def start(self) -> str:
        return f"{self.brand} starting..."

class Car(Vehicle):
    def __init__(self, brand: str, doors: int):
        super().__init__(brand)
        self.doors = doors

    def start(self) -> str:             # method overriding
        return f"{self.brand} car starting with {self.doors} doors"
```

**Interview Tip:** Prefer composition over inheritance. Inheritance creates tight coupling.

---

### 1.4 Polymorphism
The ability of different objects to respond to the same interface in different ways.

```
Compile-time (Static): Method overloading (same name, different params)
Runtime (Dynamic):     Method overriding (same signature, different behavior)
```

```python
class Animal(ABC):
    @abstractmethod
    def sound(self) -> str: ...

class Dog(Animal):
    def sound(self) -> str:
        return "Woof"

class Cat(Animal):
    def sound(self) -> str:
        return "Meow"

def make_sound(animal: Animal) -> None:
    print(animal.sound())              # runtime dispatch

make_sound(Dog())   # Woof
make_sound(Cat())   # Meow
```

**Interview Tip:** Polymorphism enables the Open/Closed Principle — add new types without changing existing code.

---

## 2. SOLID Principles

### 2.1 S — Single Responsibility Principle (SRP)
> A class should have only one reason to change.

```
Bad:  Invoice class that calculates, formats, AND prints invoice
Good: InvoiceCalculator | InvoiceFormatter | InvoicePrinter
```

```python
# BAD
class Invoice:
    def calculate_total(self): ...
    def print_invoice(self): ...        # printing is a separate concern
    def save_to_db(self): ...           # persistence is a separate concern

# GOOD
class Invoice:
    def calculate_total(self): ...

class InvoicePrinter:
    def print(self, invoice: Invoice): ...

class InvoiceRepository:
    def save(self, invoice: Invoice): ...
```

---

### 2.2 O — Open/Closed Principle (OCP)
> Software entities should be open for extension, closed for modification.

```
Bad:  Add if/elif for every new shape in area calculation
Good: Each shape knows its own area; add new shapes without touching existing code
```

```python
# BAD
def total_area(shapes):
    total = 0
    for s in shapes:
        if isinstance(s, Circle):
            total += 3.14 * s.radius ** 2
        elif isinstance(s, Rectangle):
            total += s.width * s.height   # must modify for every new shape
    return total

# GOOD
class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

def total_area(shapes: list[Shape]) -> float:
    return sum(s.area() for s in shapes) # closed for modification
```

---

### 2.3 L — Liskov Substitution Principle (LSP)
> Subtypes must be substitutable for their base types without altering program correctness.

```
Bad:  Square inherits Rectangle but breaks setWidth/setHeight invariants
Good: Square and Rectangle are siblings, not parent-child
```

```python
# BAD — violates LSP
class Rectangle:
    def set_width(self, w): self.width = w
    def set_height(self, h): self.height = h
    def area(self): return self.width * self.height

class Square(Rectangle):
    def set_width(self, w):             # breaks Rectangle contract
        self.width = self.height = w
    def set_height(self, h):
        self.width = self.height = h

# A caller that assumes r.set_width(5); r.set_height(4) → area == 20
# will get area == 16 for Square — contract broken!

# GOOD
class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

class Rectangle(Shape):
    def __init__(self, w, h): self.width = w; self.height = h
    def area(self): return self.width * self.height

class Square(Shape):
    def __init__(self, side): self.side = side
    def area(self): return self.side ** 2
```

---

### 2.4 I — Interface Segregation Principle (ISP)
> Clients should not be forced to depend on interfaces they do not use.

```
Bad:  Fat interface with 10 methods, half of which implementors leave empty
Good: Split into focused, cohesive interfaces
```

```python
# BAD
class Worker(ABC):
    @abstractmethod
    def work(self): ...
    @abstractmethod
    def eat(self): ...      # robots don't eat!

# GOOD
class Workable(ABC):
    @abstractmethod
    def work(self): ...

class Eatable(ABC):
    @abstractmethod
    def eat(self): ...

class HumanWorker(Workable, Eatable):
    def work(self): ...
    def eat(self): ...

class RobotWorker(Workable):
    def work(self): ...     # only what it needs
```

---

### 2.5 D — Dependency Inversion Principle (DIP)
> High-level modules should not depend on low-level modules. Both should depend on abstractions.

```
Bad:  Business logic class directly instantiates MySQLDatabase
Good: Business logic depends on a DatabaseInterface; inject concrete implementation
```

```python
# BAD
class OrderService:
    def __init__(self):
        self.db = MySQLDatabase()           # hardcoded dependency

# GOOD
class Database(ABC):
    @abstractmethod
    def save(self, data): ...

class MySQLDatabase(Database):
    def save(self, data): ...

class OrderService:
    def __init__(self, db: Database):       # depends on abstraction
        self.db = db

# Usage
service = OrderService(MySQLDatabase())     # inject at runtime
```

---

## 3. GRASP Principles

General Responsibility Assignment Software Patterns — who should own what responsibility.

| Principle | One-Line Meaning |
|-----------|-----------------|
| **Information Expert** | Assign responsibility to the class that has the information needed to fulfill it |
| **Creator** | Class B creates A if B contains/aggregates/uses A closely |
| **Controller** | Use a dedicated class to handle system events; don't put logic in UI |
| **Low Coupling** | Minimize dependencies between classes |
| **High Cohesion** | Keep related things together; one class, one purpose |
| **Polymorphism** | Use polymorphism instead of conditionals for type-based variation |
| **Pure Fabrication** | Invent a class with no domain counterpart to achieve low coupling/high cohesion |
| **Indirection** | Introduce an intermediate object to avoid direct coupling |
| **Protected Variations** | Identify variation points; shield the system behind stable interfaces |

---

## 4. UML & Class Diagrams

### 4.1 Class Notation

```
┌─────────────────────┐
│      ClassName      │  ← Class name (bold/italic if abstract)
├─────────────────────┤
│ - privateField: int │  ← Attributes
│ # protectedField    │
│ + publicField       │
├─────────────────────┤
│ + publicMethod()    │  ← Methods
│ - privateMethod()   │
│ {abstract} method() │
└─────────────────────┘

Visibility: + public  # protected  - private  ~ package
```

### 4.2 Relationships

```
Association     ────────────────     A uses B (loosely)
Aggregation     ────────────────◇    A "has" B; B can exist without A
Composition     ────────────────◆    A "owns" B; B cannot exist without A
Inheritance     ────────────────▷    A extends B (IS-A)
Realization     - - - - - - - -▷    A implements interface B
Dependency      - - - - - - - ->    A temporarily uses B (method param)
```

### 4.3 Multiplicity

```
1       exactly one
0..1    zero or one
*       zero or many
1..*    one or many
m..n    between m and n
```

### 4.4 Example: Order System Class Diagram

```
Customer                Order                  OrderItem
─────────               ─────                  ─────────
- id: int        1    *│- id: int        1   *│- id: int
- name: str   ────────>│- date: datetime ────>│- quantity: int
- email: str            │- status: Status      │- price: float
                        │+ total(): float      │
                        └─────────────────     └──────────
                                │                    │
                                │ uses               │ has
                                ▼                    ▼
                          PaymentMethod          Product
```

---

## 5. Design Patterns — Creational

Creational patterns deal with **object creation** mechanisms.

---

### 5.1 Singleton
Ensure a class has only one instance and provide global access to it.

```
Use when: Logger, Config, Thread pool, Database connection pool
Pitfall:  Hard to test; hidden global state; breaks SRP
```

```python
import threading

class Singleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:             # thread-safe
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

# Usage
s1 = Singleton()
s2 = Singleton()
assert s1 is s2                         # True
```

---

### 5.2 Factory Method
Define an interface for creating an object, but let subclasses decide which class to instantiate.

```
Use when: You don't know ahead of time what class to instantiate
          Subclasses should control what objects they create
```

```python
class Notification(ABC):
    @abstractmethod
    def send(self, msg: str) -> None: ...

class EmailNotification(Notification):
    def send(self, msg: str) -> None:
        print(f"Email: {msg}")

class SMSNotification(Notification):
    def send(self, msg: str) -> None:
        print(f"SMS: {msg}")

class NotificationFactory:
    @staticmethod
    def create(channel: str) -> Notification:
        match channel:
            case "email": return EmailNotification()
            case "sms":   return SMSNotification()
            case _: raise ValueError(f"Unknown channel: {channel}")

notif = NotificationFactory.create("email")
notif.send("Hello!")
```

---

### 5.3 Abstract Factory
Create families of related objects without specifying their concrete classes.

```
Use when: System must be independent of how its products are created
          System works with multiple families of products (e.g., UI themes)
```

```python
class Button(ABC):
    @abstractmethod
    def render(self) -> str: ...

class Checkbox(ABC):
    @abstractmethod
    def render(self) -> str: ...

class MacButton(Button):
    def render(self) -> str: return "Mac Button"

class MacCheckbox(Checkbox):
    def render(self) -> str: return "Mac Checkbox"

class WinButton(Button):
    def render(self) -> str: return "Win Button"

class WinCheckbox(Checkbox):
    def render(self) -> str: return "Win Checkbox"

class GUIFactory(ABC):
    @abstractmethod
    def create_button(self) -> Button: ...
    @abstractmethod
    def create_checkbox(self) -> Checkbox: ...

class MacFactory(GUIFactory):
    def create_button(self) -> Button: return MacButton()
    def create_checkbox(self) -> Checkbox: return MacCheckbox()

class WinFactory(GUIFactory):
    def create_button(self) -> Button: return WinButton()
    def create_checkbox(self) -> Checkbox: return WinCheckbox()
```

---

### 5.4 Builder
Construct complex objects step by step.

```
Use when: Object has many optional parts or requires complex initialization
          Same construction process should create different representations
```

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Pizza:
    size: str
    crust: str
    toppings: list[str] = field(default_factory=list)
    extra_cheese: bool = False

class PizzaBuilder:
    def __init__(self):
        self._size = "medium"
        self._crust = "thin"
        self._toppings: list[str] = []
        self._extra_cheese = False

    def size(self, size: str) -> "PizzaBuilder":
        self._size = size
        return self

    def crust(self, crust: str) -> "PizzaBuilder":
        self._crust = crust
        return self

    def topping(self, topping: str) -> "PizzaBuilder":
        self._toppings.append(topping)
        return self

    def extra_cheese(self) -> "PizzaBuilder":
        self._extra_cheese = True
        return self

    def build(self) -> Pizza:
        return Pizza(self._size, self._crust, self._toppings, self._extra_cheese)

pizza = (PizzaBuilder()
         .size("large")
         .crust("thick")
         .topping("mushroom")
         .topping("pepper")
         .extra_cheese()
         .build())
```

---

### 5.5 Prototype
Copy existing objects without making code dependent on their classes.

```
Use when: Cost of creating an object is expensive (DB call, API hit)
          You need copies of an object with slight variations
```

```python
import copy

class Config:
    def __init__(self, host: str, port: int, settings: dict):
        self.host = host
        self.port = port
        self.settings = settings

    def clone(self) -> "Config":
        return copy.deepcopy(self)      # deep copy for nested objects

base_config = Config("localhost", 5432, {"timeout": 30})
replica_config = base_config.clone()
replica_config.port = 5433
```

---

## 6. Design Patterns — Structural

Structural patterns deal with **how classes and objects are composed** to form larger structures.

---

### 6.1 Adapter
Convert the interface of a class into another interface the client expects.

```
Use when: Integrating legacy code or third-party libraries with different interfaces
Analogy:  Power socket adapter
```

```python
class EuropeanSocket:
    def power_220v(self) -> str:
        return "220V power"

class USASocket(ABC):
    @abstractmethod
    def power_110v(self) -> str: ...

class SocketAdapter(USASocket):
    def __init__(self, european: EuropeanSocket):
        self._european = european

    def power_110v(self) -> str:
        v220 = self._european.power_220v()
        return f"Converted {v220} to 110V"
```

---

### 6.2 Decorator
Attach additional responsibilities to an object dynamically without modifying its class.

```
Use when: Adding behavior at runtime without subclassing
          Multiple optional features that can be combined (like coffee toppings)
```

```python
class Coffee(ABC):
    @abstractmethod
    def cost(self) -> float: ...
    @abstractmethod
    def description(self) -> str: ...

class SimpleCoffee(Coffee):
    def cost(self) -> float: return 1.0
    def description(self) -> str: return "Coffee"

class MilkDecorator(Coffee):
    def __init__(self, coffee: Coffee):
        self._coffee = coffee

    def cost(self) -> float: return self._coffee.cost() + 0.25
    def description(self) -> str: return self._coffee.description() + ", Milk"

class SugarDecorator(Coffee):
    def __init__(self, coffee: Coffee):
        self._coffee = coffee

    def cost(self) -> float: return self._coffee.cost() + 0.10
    def description(self) -> str: return self._coffee.description() + ", Sugar"

coffee = SugarDecorator(MilkDecorator(SimpleCoffee()))
print(coffee.cost())         # 1.35
print(coffee.description())  # Coffee, Milk, Sugar
```

---

### 6.3 Facade
Provide a simplified interface to a complex subsystem.

```
Use when: Simplifying a complex library/framework for clients
          Layering a subsystem (present simple API to UI, hide complexity)
```

```python
class CPU:
    def freeze(self): ...
    def jump(self, pos): ...
    def execute(self): ...

class Memory:
    def load(self, pos, data): ...

class HardDrive:
    def read(self, lba, size) -> bytes: ...

class ComputerFacade:
    """Client only needs to call start()"""
    def __init__(self):
        self.cpu = CPU()
        self.memory = Memory()
        self.hd = HardDrive()

    def start(self) -> None:
        self.cpu.freeze()
        self.memory.load(0, self.hd.read(0, 1024))
        self.cpu.jump(0)
        self.cpu.execute()
```

---

### 6.4 Composite
Compose objects into tree structures to represent part-whole hierarchies.

```
Use when: File system (files and folders), UI components, org charts
          Clients should treat individual objects and compositions uniformly
```

```python
class FileSystemComponent(ABC):
    @abstractmethod
    def display(self, indent: int = 0) -> None: ...
    @abstractmethod
    def size(self) -> int: ...

class File(FileSystemComponent):
    def __init__(self, name: str, size: int):
        self.name = name
        self._size = size

    def display(self, indent: int = 0) -> None:
        print(" " * indent + f"📄 {self.name} ({self._size}B)")

    def size(self) -> int:
        return self._size

class Folder(FileSystemComponent):
    def __init__(self, name: str):
        self.name = name
        self._children: list[FileSystemComponent] = []

    def add(self, component: FileSystemComponent) -> None:
        self._children.append(component)

    def display(self, indent: int = 0) -> None:
        print(" " * indent + f"📁 {self.name}")
        for child in self._children:
            child.display(indent + 2)

    def size(self) -> int:
        return sum(c.size() for c in self._children)
```

---

### 6.5 Proxy
Provide a surrogate or placeholder to control access to another object.

```
Use when: Lazy initialization, caching, access control, logging, remote objects
Types:    Virtual proxy (lazy load), Protection proxy (auth), Remote proxy
```

```python
class Image(ABC):
    @abstractmethod
    def display(self) -> None: ...

class RealImage(Image):
    def __init__(self, filename: str):
        self.filename = filename
        self._load()                            # expensive operation

    def _load(self) -> None:
        print(f"Loading {self.filename} from disk...")

    def display(self) -> None:
        print(f"Displaying {self.filename}")

class ProxyImage(Image):
    def __init__(self, filename: str):
        self.filename = filename
        self._real: RealImage | None = None

    def display(self) -> None:
        if self._real is None:
            self._real = RealImage(self.filename) # lazy load
        self._real.display()
```

---

### 6.6 Bridge
Decouple an abstraction from its implementation so both can vary independently.

```
Use when: You want to avoid a permanent binding between abstraction and implementation
          Both abstraction and implementation should be extensible via subclassing
```

```python
class Renderer(ABC):
    @abstractmethod
    def render_circle(self, radius: float) -> str: ...

class VectorRenderer(Renderer):
    def render_circle(self, radius: float) -> str:
        return f"Vector circle, radius={radius}"

class RasterRenderer(Renderer):
    def render_circle(self, radius: float) -> str:
        return f"Raster circle, radius={radius}"

class Shape(ABC):
    def __init__(self, renderer: Renderer):
        self.renderer = renderer                # bridge

class Circle(Shape):
    def __init__(self, renderer: Renderer, radius: float):
        super().__init__(renderer)
        self.radius = radius

    def draw(self) -> str:
        return self.renderer.render_circle(self.radius)
```

---

### 6.7 Flyweight
Use sharing to support a large number of similar objects efficiently.

```
Use when: Large number of similar objects consuming too much memory
          Objects share state that can be externalized
Intrinsic state: shared (stored in flyweight)
Extrinsic state: unique per object (passed by client)
```

```python
class CharacterStyle:
    """Flyweight — shared object"""
    def __init__(self, font: str, size: int, color: str):
        self.font = font
        self.size = size
        self.color = color

class StyleFactory:
    _styles: dict[tuple, CharacterStyle] = {}

    @classmethod
    def get_style(cls, font: str, size: int, color: str) -> CharacterStyle:
        key = (font, size, color)
        if key not in cls._styles:
            cls._styles[key] = CharacterStyle(font, size, color)
        return cls._styles[key]

class Character:
    def __init__(self, char: str, style: CharacterStyle, position: tuple):
        self.char = char
        self.style = style            # shared flyweight
        self.position = position      # extrinsic — unique
```

---

## 7. Design Patterns — Behavioral

Behavioral patterns deal with **communication and responsibility** between objects.

---

### 7.1 Observer
Define a one-to-many dependency so when one object changes state, all dependents are notified automatically.

```
Use when: Event systems, news feeds, UI data bindings, pub/sub
```

```python
from abc import ABC, abstractmethod

class Observer(ABC):
    @abstractmethod
    def update(self, event: str, data: any) -> None: ...

class Observable:
    def __init__(self):
        self._observers: list[Observer] = []

    def subscribe(self, observer: Observer) -> None:
        self._observers.append(observer)

    def unsubscribe(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def notify(self, event: str, data: any = None) -> None:
        for observer in self._observers:
            observer.update(event, data)

class StockMarket(Observable):
    def __init__(self):
        super().__init__()
        self._price: float = 0.0

    def set_price(self, price: float) -> None:
        self._price = price
        self.notify("price_changed", price)

class StockAlert(Observer):
    def update(self, event: str, data: any) -> None:
        print(f"Alert! Stock price changed to {data}")
```

---

### 7.2 Strategy
Define a family of algorithms, encapsulate each one, and make them interchangeable.

```
Use when: You need different variants of an algorithm
          Eliminate conditionals for selecting behavior
```

```python
class SortStrategy(ABC):
    @abstractmethod
    def sort(self, data: list) -> list: ...

class BubbleSortStrategy(SortStrategy):
    def sort(self, data: list) -> list:
        arr = data.copy()
        for i in range(len(arr)):
            for j in range(len(arr) - i - 1):
                if arr[j] > arr[j+1]:
                    arr[j], arr[j+1] = arr[j+1], arr[j]
        return arr

class MergeSortStrategy(SortStrategy):
    def sort(self, data: list) -> list:
        if len(data) <= 1: return data
        mid = len(data) // 2
        left = self.sort(data[:mid])
        right = self.sort(data[mid:])
        return self._merge(left, right)

    def _merge(self, left, right):
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                result.append(left[i]); i += 1
            else:
                result.append(right[j]); j += 1
        return result + left[i:] + right[j:]

class Sorter:
    def __init__(self, strategy: SortStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: SortStrategy) -> None:
        self._strategy = strategy

    def sort(self, data: list) -> list:
        return self._strategy.sort(data)
```

---

### 7.3 Command
Encapsulate a request as an object, allowing undo/redo, queueing, and logging.

```
Use when: Undo/redo, task queues, macros, transactional behavior
```

```python
class Command(ABC):
    @abstractmethod
    def execute(self) -> None: ...
    @abstractmethod
    def undo(self) -> None: ...

class TextEditor:
    def __init__(self):
        self.text = ""

class TypeCommand(Command):
    def __init__(self, editor: TextEditor, text: str):
        self.editor = editor
        self.text = text

    def execute(self) -> None:
        self.editor.text += self.text

    def undo(self) -> None:
        self.editor.text = self.editor.text[:-len(self.text)]

class CommandHistory:
    def __init__(self):
        self._history: list[Command] = []

    def execute(self, command: Command) -> None:
        command.execute()
        self._history.append(command)

    def undo(self) -> None:
        if self._history:
            self._history.pop().undo()
```

---

### 7.4 Chain of Responsibility
Pass a request along a chain of handlers; each handler decides to process or pass it on.

```
Use when: Multiple handlers can handle a request; handler is not known ahead of time
          Middleware pipelines, approval workflows, event bubbling
```

```python
class Handler(ABC):
    def __init__(self):
        self._next: "Handler | None" = None

    def set_next(self, handler: "Handler") -> "Handler":
        self._next = handler
        return handler

    def handle(self, request: int) -> str | None:
        if self._next:
            return self._next.handle(request)
        return None

class LowLevelHandler(Handler):
    def handle(self, request: int) -> str | None:
        if request < 10:
            return f"LowLevel handled {request}"
        return super().handle(request)

class MidLevelHandler(Handler):
    def handle(self, request: int) -> str | None:
        if request < 100:
            return f"MidLevel handled {request}"
        return super().handle(request)

class HighLevelHandler(Handler):
    def handle(self, request: int) -> str | None:
        return f"HighLevel handled {request}"

# Build chain
low = LowLevelHandler()
mid = MidLevelHandler()
high = HighLevelHandler()
low.set_next(mid).set_next(high)

print(low.handle(5))    # LowLevel handled 5
print(low.handle(50))   # MidLevel handled 50
print(low.handle(500))  # HighLevel handled 500
```

---

### 7.5 Template Method
Define the skeleton of an algorithm in a base class; let subclasses fill in specific steps.

```
Use when: Invariant parts of an algorithm should not be repeated; variant parts delegated to subclasses
          Hollywood Principle: "Don't call us, we'll call you"
```

```python
class DataProcessor(ABC):
    def process(self) -> None:          # template method
        self.read_data()
        self.process_data()
        self.write_data()

    @abstractmethod
    def read_data(self) -> None: ...

    @abstractmethod
    def process_data(self) -> None: ...

    def write_data(self) -> None:       # optional hook with default
        print("Writing to default output")

class CSVProcessor(DataProcessor):
    def read_data(self) -> None:
        print("Reading CSV")

    def process_data(self) -> None:
        print("Processing CSV data")

class JSONProcessor(DataProcessor):
    def read_data(self) -> None:
        print("Reading JSON")

    def process_data(self) -> None:
        print("Processing JSON data")

    def write_data(self) -> None:
        print("Writing JSON to DB")
```

---

### 7.6 Iterator
Provide a way to sequentially access elements of a collection without exposing its representation.

```python
class NumberRange:
    def __init__(self, start: int, end: int):
        self.start = start
        self.end = end

    def __iter__(self):
        current = self.start
        while current <= self.end:
            yield current
            current += 1

for n in NumberRange(1, 5):
    print(n)    # 1 2 3 4 5
```

---

### 7.7 State
Allow an object to alter its behavior when its internal state changes. The object will appear to change its class.

```
Use when: Object behavior depends heavily on its state; state transitions are explicit
          Eliminate large if/elif state-checking blocks
```

```python
class TrafficLight:
    def __init__(self):
        self._state = "RED"
        self._transitions = {
            "RED":    "GREEN",
            "GREEN":  "YELLOW",
            "YELLOW": "RED"
        }

    def next(self) -> None:
        self._state = self._transitions[self._state]

    def action(self) -> str:
        return {"RED": "Stop", "GREEN": "Go", "YELLOW": "Slow down"}[self._state]
```

---

### 7.8 Mediator
Define an object that encapsulates how a set of objects interact.

```
Use when: Many objects communicate in complex ways (many-to-many)
          Reduces coupling; objects only know the mediator, not each other
Use case: Chat room, air traffic control, UI event bus
```

```python
class ChatMediator:
    def __init__(self):
        self._users: list["ChatUser"] = []

    def add_user(self, user: "ChatUser") -> None:
        self._users.append(user)

    def send(self, message: str, sender: "ChatUser") -> None:
        for user in self._users:
            if user is not sender:
                user.receive(message, sender.name)

class ChatUser:
    def __init__(self, name: str, mediator: ChatMediator):
        self.name = name
        self._mediator = mediator

    def send(self, message: str) -> None:
        self._mediator.send(message, self)

    def receive(self, message: str, from_user: str) -> None:
        print(f"{self.name} received from {from_user}: {message}")
```

---

### 7.9 Visitor
Add new operations to existing class hierarchies without modifying them.

```
Use when: You need to add new operations to stable class hierarchies
          Operations are different for different types (AST traversal, tax calculation)
```

```python
class Visitor(ABC):
    @abstractmethod
    def visit_circle(self, circle: "Circle") -> None: ...
    @abstractmethod
    def visit_rectangle(self, rect: "Rectangle") -> None: ...

class AreaVisitor(Visitor):
    def visit_circle(self, circle: "Circle") -> None:
        print(f"Circle area: {3.14 * circle.radius ** 2:.2f}")

    def visit_rectangle(self, rect: "Rectangle") -> None:
        print(f"Rectangle area: {rect.width * rect.height}")

class Shape(ABC):
    @abstractmethod
    def accept(self, visitor: Visitor) -> None: ...

class Circle(Shape):
    def __init__(self, radius: float): self.radius = radius
    def accept(self, visitor: Visitor) -> None: visitor.visit_circle(self)

class Rectangle(Shape):
    def __init__(self, w: float, h: float): self.width = w; self.height = h
    def accept(self, visitor: Visitor) -> None: visitor.visit_rectangle(self)
```

---

### 7.10 Memento
Capture and externalize an object's internal state without violating encapsulation; restore it later.

```
Use when: Undo/redo/snapshot/checkpointing
```

```python
class EditorMemento:
    def __init__(self, text: str):
        self._text = text

    def get_text(self) -> str:
        return self._text

class Editor:
    def __init__(self):
        self.text = ""

    def save(self) -> EditorMemento:
        return EditorMemento(self.text)

    def restore(self, memento: EditorMemento) -> None:
        self.text = memento.get_text()

class History:
    def __init__(self):
        self._stack: list[EditorMemento] = []

    def push(self, m: EditorMemento) -> None:
        self._stack.append(m)

    def pop(self) -> EditorMemento | None:
        return self._stack.pop() if self._stack else None
```

---

## 8. Relationships Between Classes

| Relationship | Symbol | Strength | Example |
|---|---|---|---|
| Dependency | `- - ->` | Weakest | Method uses object as parameter |
| Association | `────` | Weak | Customer places Orders |
| Aggregation | `────◇` | Medium | Department has Employees (employees exist independently) |
| Composition | `────◆` | Strong | House has Rooms (rooms don't exist without house) |
| Realization | `- - -▷` | — | Dog implements Animal interface |
| Inheritance | `────▷` | Strongest | Car extends Vehicle |

### When to Use Composition Over Inheritance

```
Use Inheritance when:
  ✓ Relationship is truly IS-A (a Dog IS-A Animal)
  ✓ Child class needs all parent functionality
  ✓ Behavior won't change at runtime

Use Composition when:
  ✓ Relationship is HAS-A (a Car HAS-A Engine)
  ✓ You want to change behavior at runtime
  ✓ You need to combine multiple behaviors
  ✓ Subclassing leads to explosion of subclasses
```

---

## 9. Coupling & Cohesion

### Coupling
The degree of interdependence between modules/classes.

```
Goal: LOW coupling

Types (worst to best):
  Content coupling  — one module modifies internals of another         ← worst
  Common coupling   — modules share global data
  Control coupling  — one module controls flow of another via flag
  Stamp coupling    — share complex data structure but use only parts
  Data coupling     — share data via parameters only                   ← best
```

### Cohesion
How strongly related and focused the responsibilities of a module are.

```
Goal: HIGH cohesion

Types (best to worst):
  Functional    — all elements contribute to a single, well-defined task    ← best
  Sequential    — output of one element is input of another
  Communicational — elements operate on same data
  Procedural    — elements follow a sequence of execution
  Temporal      — elements grouped because they happen at the same time
  Logical       — elements do similar things but are logically different
  Coincidental  — elements have no meaningful relationship                  ← worst
```

---

## 10. Design Principles Cheatsheet

| Principle | One-Line Rule | Violation Signal |
|---|---|---|
| SRP | One class, one reason to change | "And" in class responsibility |
| OCP | Extend without modifying | `if isinstance(...)` chains |
| LSP | Subtypes behave like parent | Overridden method throws or weakens contract |
| ISP | Small, focused interfaces | Empty method implementations |
| DIP | Depend on abstractions | `new ConcreteClass()` inside business logic |
| DRY | Don't Repeat Yourself | Copy-paste code |
| KISS | Keep It Simple, Stupid | Over-engineered for current needs |
| YAGNI | You Aren't Gonna Need It | Adding features "just in case" |
| Law of Demeter | Only talk to direct friends | `a.getB().getC().doSomething()` |
| Composition > Inheritance | Prefer HAS-A over IS-A | Deep inheritance hierarchies |
| Fail Fast | Report errors as early as possible | Silent failure |
| Tell, Don't Ask | Tell objects what to do, not ask for their state | Long getter chains in logic |

---

## 11. LLD Interview Problems — Step-by-Step

> **Interview Framework:**
> 1. Clarify requirements & constraints (5 min)
> 2. Identify entities/nouns → classes
> 3. Identify behaviors/verbs → methods
> 4. Define relationships & cardinalities
> 5. Apply design patterns where appropriate
> 6. Discuss extensibility & trade-offs

---

### 11.1 Parking Lot

**Requirements:** Multiple floors, multiple spot sizes (small/medium/large), vehicles (motorcycle/car/bus), ticketing, payment.

**Key Classes:**

```python
from enum import Enum
from datetime import datetime

class SpotSize(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

class VehicleType(Enum):
    MOTORCYCLE = "motorcycle"
    CAR = "car"
    BUS = "bus"

# Strategy pattern for spot-vehicle compatibility
SPOT_COMPATIBILITY = {
    VehicleType.MOTORCYCLE: [SpotSize.SMALL, SpotSize.MEDIUM, SpotSize.LARGE],
    VehicleType.CAR:        [SpotSize.MEDIUM, SpotSize.LARGE],
    VehicleType.BUS:        [SpotSize.LARGE],
}

class Vehicle:
    def __init__(self, plate: str, v_type: VehicleType):
        self.plate = plate
        self.type = v_type

class ParkingSpot:
    def __init__(self, spot_id: str, size: SpotSize, floor: int):
        self.spot_id = spot_id
        self.size = size
        self.floor = floor
        self.vehicle: Vehicle | None = None

    @property
    def is_free(self) -> bool:
        return self.vehicle is None

    def can_fit(self, vehicle: Vehicle) -> bool:
        return self.size in SPOT_COMPATIBILITY[vehicle.type]

    def park(self, vehicle: Vehicle) -> None:
        if not self.can_fit(vehicle):
            raise ValueError("Vehicle too large for this spot")
        self.vehicle = vehicle

    def unpark(self) -> Vehicle:
        v = self.vehicle
        self.vehicle = None
        return v

class Ticket:
    def __init__(self, ticket_id: str, vehicle: Vehicle, spot: ParkingSpot):
        self.ticket_id = ticket_id
        self.vehicle = vehicle
        self.spot = spot
        self.entry_time = datetime.now()
        self.exit_time: datetime | None = None

class PricingStrategy(ABC):
    @abstractmethod
    def calculate(self, duration_hours: float) -> float: ...

class HourlyPricing(PricingStrategy):
    RATES = {SpotSize.SMALL: 2.0, SpotSize.MEDIUM: 3.5, SpotSize.LARGE: 5.0}

    def __init__(self, spot_size: SpotSize):
        self.rate = self.RATES[spot_size]

    def calculate(self, duration_hours: float) -> float:
        return self.rate * duration_hours

class ParkingLot:
    _instance = None                        # Singleton

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        self._floors: list[list[ParkingSpot]] = []
        self._tickets: dict[str, Ticket] = {}
        self._ticket_counter = 0
        self._initialized = True

    def add_floor(self, spots: list[ParkingSpot]) -> None:
        self._floors.append(spots)

    def park_vehicle(self, vehicle: Vehicle) -> Ticket:
        for floor in self._floors:
            for spot in floor:
                if spot.is_free and spot.can_fit(vehicle):
                    spot.park(vehicle)
                    self._ticket_counter += 1
                    ticket = Ticket(f"T{self._ticket_counter}", vehicle, spot)
                    self._tickets[ticket.ticket_id] = ticket
                    return ticket
        raise Exception("Parking full")

    def exit_vehicle(self, ticket_id: str) -> float:
        ticket = self._tickets[ticket_id]
        ticket.exit_time = datetime.now()
        duration = (ticket.exit_time - ticket.entry_time).seconds / 3600
        ticket.spot.unpark()
        pricing = HourlyPricing(ticket.spot.size)
        return pricing.calculate(duration)
```

**Design Decisions:**
- Singleton for `ParkingLot` (one lot in system)
- Strategy pattern for pricing (hourly, daily, flat-rate)
- Compatibility map instead of hardcoded `isinstance` checks

---

### 11.2 Library Management System

**Requirements:** Books, members, checkout/return, reservations, fines, search.

**Key Classes:**

```python
class BookStatus(Enum):
    AVAILABLE = "available"
    CHECKED_OUT = "checked_out"
    RESERVED = "reserved"

class Book:
    def __init__(self, isbn: str, title: str, author: str, copies: int):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.total_copies = copies
        self.available_copies = copies

    def checkout(self) -> bool:
        if self.available_copies > 0:
            self.available_copies -= 1
            return True
        return False

    def return_book(self) -> None:
        self.available_copies = min(self.available_copies + 1, self.total_copies)

class Member:
    MAX_BOOKS = 5
    FINE_PER_DAY = 1.0

    def __init__(self, member_id: str, name: str):
        self.member_id = member_id
        self.name = name
        self.borrowed: list["Loan"] = []
        self.fine: float = 0.0

    def can_borrow(self) -> bool:
        return len(self.borrowed) < self.MAX_BOOKS

class Loan:
    LOAN_DAYS = 14

    def __init__(self, book: Book, member: Member):
        self.book = book
        self.member = member
        self.issue_date = datetime.now()
        self.due_date = self.issue_date + timedelta(days=self.LOAN_DAYS)
        self.return_date: datetime | None = None

    def is_overdue(self) -> bool:
        return datetime.now() > self.due_date and self.return_date is None

    def fine_amount(self) -> float:
        if not self.is_overdue(): return 0.0
        overdue_days = (datetime.now() - self.due_date).days
        return overdue_days * Member.FINE_PER_DAY

class Library:
    def __init__(self):
        self._books: dict[str, Book] = {}
        self._members: dict[str, Member] = {}
        self._loans: list[Loan] = []

    def add_book(self, book: Book) -> None:
        self._books[book.isbn] = book

    def register_member(self, member: Member) -> None:
        self._members[member.member_id] = member

    def checkout_book(self, member_id: str, isbn: str) -> Loan:
        member = self._members[member_id]
        book = self._books[isbn]
        if not member.can_borrow():
            raise Exception("Borrow limit reached")
        if not book.checkout():
            raise Exception("No copies available")
        loan = Loan(book, member)
        member.borrowed.append(loan)
        self._loans.append(loan)
        return loan

    def return_book(self, loan: Loan) -> float:
        loan.return_date = datetime.now()
        loan.book.return_book()
        loan.member.borrowed.remove(loan)
        fine = loan.fine_amount()
        loan.member.fine += fine
        return fine

    def search_by_title(self, title: str) -> list[Book]:
        return [b for b in self._books.values()
                if title.lower() in b.title.lower()]
```

---

### 11.3 Elevator System

**Requirements:** N elevators, M floors, requests from inside/outside, scheduling.

**Key Classes:**

```python
class Direction(Enum):
    UP = "up"
    DOWN = "down"
    IDLE = "idle"

class ElevatorState(Enum):
    MOVING = "moving"
    IDLE = "idle"
    DOOR_OPEN = "door_open"

class ElevatorRequest:
    def __init__(self, floor: int, direction: Direction):
        self.floor = floor
        self.direction = direction

class Elevator:
    def __init__(self, elevator_id: int, total_floors: int):
        self.id = elevator_id
        self.current_floor = 1
        self.direction = Direction.IDLE
        self.state = ElevatorState.IDLE
        self.destination_floors: set[int] = set()

    def add_destination(self, floor: int) -> None:
        self.destination_floors.add(floor)

    def move(self) -> None:
        if not self.destination_floors:
            self.direction = Direction.IDLE
            self.state = ElevatorState.IDLE
            return
        next_floor = min(self.destination_floors,
                         key=lambda f: abs(f - self.current_floor))
        self.direction = Direction.UP if next_floor > self.current_floor else Direction.DOWN
        self.state = ElevatorState.MOVING
        self.current_floor += 1 if self.direction == Direction.UP else -1
        if self.current_floor in self.destination_floors:
            self.destination_floors.remove(self.current_floor)
            self.state = ElevatorState.DOOR_OPEN

    def cost_to_serve(self, request: ElevatorRequest) -> int:
        return abs(self.current_floor - request.floor)

class ElevatorScheduler(ABC):
    @abstractmethod
    def assign(self, elevators: list[Elevator],
               request: ElevatorRequest) -> Elevator: ...

class NearestCarScheduler(ElevatorScheduler):
    def assign(self, elevators: list[Elevator],
               request: ElevatorRequest) -> Elevator:
        return min(elevators, key=lambda e: e.cost_to_serve(request))

class ElevatorController:
    def __init__(self, num_elevators: int, num_floors: int,
                 scheduler: ElevatorScheduler):
        self.elevators = [Elevator(i, num_floors) for i in range(num_elevators)]
        self.scheduler = scheduler

    def request(self, floor: int, direction: Direction) -> None:
        req = ElevatorRequest(floor, direction)
        elevator = self.scheduler.assign(self.elevators, req)
        elevator.add_destination(floor)

    def step(self) -> None:
        for elevator in self.elevators:
            elevator.move()
```

---

### 11.4 Chess Game

**Requirements:** 8x8 board, all pieces, legal moves, check/checkmate detection.

**Key Classes:**

```python
class Color(Enum):
    WHITE = "white"
    BLACK = "black"

class Position:
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col

    def is_valid(self) -> bool:
        return 0 <= self.row < 8 and 0 <= self.col < 8

    def __eq__(self, other): return self.row == other.row and self.col == other.col

class Piece(ABC):
    def __init__(self, color: Color, position: Position):
        self.color = color
        self.position = position

    @abstractmethod
    def valid_moves(self, board: "Board") -> list[Position]: ...

class King(Piece):
    def valid_moves(self, board: "Board") -> list[Position]:
        moves = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                new_pos = Position(self.position.row + dr, self.position.col + dc)
                if new_pos.is_valid():
                    piece_at = board.get_piece(new_pos)
                    if piece_at is None or piece_at.color != self.color:
                        moves.append(new_pos)
        return moves

class Pawn(Piece):
    def valid_moves(self, board: "Board") -> list[Position]:
        moves = []
        direction = 1 if self.color == Color.WHITE else -1
        forward = Position(self.position.row + direction, self.position.col)
        if forward.is_valid() and board.get_piece(forward) is None:
            moves.append(forward)
        return moves

class Board:
    def __init__(self):
        self._grid: list[list[Piece | None]] = [[None] * 8 for _ in range(8)]

    def place(self, piece: Piece) -> None:
        self._grid[piece.position.row][piece.position.col] = piece

    def get_piece(self, pos: Position) -> Piece | None:
        return self._grid[pos.row][pos.col]

    def move_piece(self, from_pos: Position, to_pos: Position) -> None:
        piece = self.get_piece(from_pos)
        self._grid[from_pos.row][from_pos.col] = None
        piece.position = to_pos
        self._grid[to_pos.row][to_pos.col] = piece

class Player:
    def __init__(self, name: str, color: Color):
        self.name = name
        self.color = color

class Game:
    def __init__(self, white: Player, black: Player):
        self.board = Board()
        self.players = {Color.WHITE: white, Color.BLACK: black}
        self.current_turn = Color.WHITE
        self._setup_board()

    def _setup_board(self) -> None:
        pass   # place pieces in starting positions

    def make_move(self, from_pos: Position, to_pos: Position) -> bool:
        piece = self.board.get_piece(from_pos)
        if piece is None or piece.color != self.current_turn:
            return False
        if to_pos not in piece.valid_moves(self.board):
            return False
        self.board.move_piece(from_pos, to_pos)
        self.current_turn = Color.BLACK if self.current_turn == Color.WHITE else Color.WHITE
        return True
```

---

### 11.5 Snake and Ladder

```python
class Dice:
    def roll(self) -> int:
        import random
        return random.randint(1, 6)

class Player:
    def __init__(self, name: str):
        self.name = name
        self.position = 0

class Board:
    def __init__(self, size: int, snakes: dict[int, int], ladders: dict[int, int]):
        self.size = size
        self.snakes = snakes        # head -> tail
        self.ladders = ladders      # bottom -> top

    def get_final_position(self, pos: int) -> int:
        if pos in self.snakes:
            print(f"  Snake! {pos} -> {self.snakes[pos]}")
            return self.snakes[pos]
        if pos in self.ladders:
            print(f"  Ladder! {pos} -> {self.ladders[pos]}")
            return self.ladders[pos]
        return pos

class SnakeLadderGame:
    def __init__(self, players: list[Player]):
        self.dice = Dice()
        self.board = Board(
            size=100,
            snakes={17: 7, 54: 34, 62: 19, 98: 79},
            ladders={3: 22, 5: 8, 20: 29, 41: 67}
        )
        self.players = players
        self.current = 0

    def play_turn(self) -> Player | None:
        player = self.players[self.current]
        roll = self.dice.roll()
        new_pos = player.position + roll
        if new_pos > self.board.size:
            pass    # can't move
        else:
            player.position = self.board.get_final_position(new_pos)
        print(f"{player.name} rolled {roll} -> position {player.position}")
        if player.position == self.board.size:
            return player                               # winner
        self.current = (self.current + 1) % len(self.players)
        return None
```

---

### 11.6 ATM Machine

**State pattern application:**

```python
class ATMState(Enum):
    IDLE = "idle"
    CARD_INSERTED = "card_inserted"
    AUTHENTICATED = "authenticated"
    TRANSACTION = "transaction"

class ATM:
    def __init__(self, cash: float):
        self._state = ATMState.IDLE
        self._cash = cash
        self._current_card: str | None = None
        self._accounts: dict[str, tuple[str, float]] = {}  # card -> (pin, balance)

    def insert_card(self, card_number: str) -> str:
        if self._state != ATMState.IDLE:
            return "ATM busy"
        if card_number not in self._accounts:
            return "Card not recognized"
        self._current_card = card_number
        self._state = ATMState.CARD_INSERTED
        return "Card inserted. Enter PIN."

    def enter_pin(self, pin: str) -> str:
        if self._state != ATMState.CARD_INSERTED:
            return "Please insert card first"
        stored_pin, _ = self._accounts[self._current_card]
        if pin != stored_pin:
            self._state = ATMState.IDLE
            self._current_card = None
            return "Wrong PIN. Card ejected."
        self._state = ATMState.AUTHENTICATED
        return "Authenticated."

    def withdraw(self, amount: float) -> str:
        if self._state != ATMState.AUTHENTICATED:
            return "Not authenticated"
        _, balance = self._accounts[self._current_card]
        if amount > balance:
            return "Insufficient account balance"
        if amount > self._cash:
            return "ATM has insufficient cash"
        self._accounts[self._current_card] = (
            self._accounts[self._current_card][0], balance - amount
        )
        self._cash -= amount
        self._state = ATMState.IDLE
        self._current_card = None
        return f"Dispensed ${amount:.2f}"

    def eject_card(self) -> str:
        self._state = ATMState.IDLE
        self._current_card = None
        return "Card ejected"
```

---

### 11.7 Ride Sharing (Uber/Ola)

```python
class RideStatus(Enum):
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Location:
    def __init__(self, lat: float, lng: float):
        self.lat = lat
        self.lng = lng

    def distance_to(self, other: "Location") -> float:
        return ((self.lat - other.lat)**2 + (self.lng - other.lng)**2) ** 0.5

class Driver:
    def __init__(self, driver_id: str, name: str):
        self.id = driver_id
        self.name = name
        self.location: Location | None = None
        self.is_available = True
        self.rating = 5.0

    def update_location(self, loc: Location) -> None:
        self.location = loc

class Rider:
    def __init__(self, rider_id: str, name: str):
        self.id = rider_id
        self.name = name

class Ride:
    def __init__(self, ride_id: str, rider: Rider,
                 pickup: Location, dropoff: Location):
        self.id = ride_id
        self.rider = rider
        self.driver: Driver | None = None
        self.pickup = pickup
        self.dropoff = dropoff
        self.status = RideStatus.REQUESTED
        self.fare: float = 0.0

class FareCalculator(ABC):
    @abstractmethod
    def calculate(self, distance: float) -> float: ...

class StandardFare(FareCalculator):
    BASE = 2.0
    PER_KM = 1.5

    def calculate(self, distance: float) -> float:
        return self.BASE + self.PER_KM * distance

class SurgeFare(FareCalculator):
    def __init__(self, base: FareCalculator, multiplier: float):
        self._base = base
        self._multiplier = multiplier

    def calculate(self, distance: float) -> float:
        return self._base.calculate(distance) * self._multiplier

class RideMatchingService:
    @staticmethod
    def find_nearest_driver(drivers: list[Driver],
                            pickup: Location) -> Driver | None:
        available = [d for d in drivers if d.is_available and d.location]
        if not available: return None
        return min(available, key=lambda d: d.location.distance_to(pickup))

class RideService:
    def __init__(self):
        self._rides: dict[str, Ride] = {}
        self._drivers: list[Driver] = []
        self._counter = 0

    def request_ride(self, rider: Rider,
                     pickup: Location, dropoff: Location) -> Ride:
        self._counter += 1
        ride = Ride(f"R{self._counter}", rider, pickup, dropoff)
        driver = RideMatchingService.find_nearest_driver(self._drivers, pickup)
        if not driver:
            raise Exception("No drivers available")
        ride.driver = driver
        driver.is_available = False
        ride.status = RideStatus.ACCEPTED
        self._rides[ride.id] = ride
        return ride

    def complete_ride(self, ride_id: str) -> float:
        ride = self._rides[ride_id]
        distance = ride.pickup.distance_to(ride.dropoff)
        ride.fare = StandardFare().calculate(distance)
        ride.status = RideStatus.COMPLETED
        ride.driver.is_available = True
        return ride.fare
```

---

### 11.8 Hotel Booking

```python
class RoomType(Enum):
    SINGLE = "single"
    DOUBLE = "double"
    SUITE = "suite"

class RoomStatus(Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"

class Room:
    def __init__(self, number: str, room_type: RoomType, price_per_night: float):
        self.number = number
        self.type = room_type
        self.price = price_per_night
        self.status = RoomStatus.AVAILABLE

class Booking:
    def __init__(self, booking_id: str, guest_name: str, room: Room,
                 check_in: datetime, check_out: datetime):
        self.id = booking_id
        self.guest_name = guest_name
        self.room = room
        self.check_in = check_in
        self.check_out = check_out

    @property
    def total_amount(self) -> float:
        nights = (self.check_out - self.check_in).days
        return self.room.price * nights

class Hotel:
    def __init__(self, name: str):
        self.name = name
        self._rooms: list[Room] = []
        self._bookings: dict[str, Booking] = {}
        self._counter = 0

    def add_room(self, room: Room) -> None:
        self._rooms.append(room)

    def search_available(self, room_type: RoomType,
                         check_in: datetime, check_out: datetime) -> list[Room]:
        return [r for r in self._rooms
                if r.type == room_type and r.status == RoomStatus.AVAILABLE
                and not self._is_conflicting(r, check_in, check_out)]

    def _is_conflicting(self, room: Room,
                        check_in: datetime, check_out: datetime) -> bool:
        for b in self._bookings.values():
            if b.room == room:
                if not (check_out <= b.check_in or check_in >= b.check_out):
                    return True
        return False

    def book_room(self, guest: str, room: Room,
                  check_in: datetime, check_out: datetime) -> Booking:
        if self._is_conflicting(room, check_in, check_out):
            raise Exception("Room not available for these dates")
        self._counter += 1
        booking = Booking(f"B{self._counter}", guest, room, check_in, check_out)
        self._bookings[booking.id] = booking
        return booking
```

---

### 11.9 Food Delivery (Zomato/Swiggy)

```python
class OrderStatus(Enum):
    PLACED = "placed"
    ACCEPTED = "accepted"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class MenuItem:
    def __init__(self, item_id: str, name: str, price: float):
        self.id = item_id
        self.name = name
        self.price = price

class Restaurant:
    def __init__(self, res_id: str, name: str):
        self.id = res_id
        self.name = name
        self.menu: dict[str, MenuItem] = {}
        self.is_open = True

    def add_item(self, item: MenuItem) -> None:
        self.menu[item.id] = item

class Cart:
    def __init__(self):
        self._items: dict[MenuItem, int] = {}

    def add(self, item: MenuItem, qty: int = 1) -> None:
        self._items[item] = self._items.get(item, 0) + qty

    def remove(self, item: MenuItem) -> None:
        self._items.pop(item, None)

    @property
    def total(self) -> float:
        return sum(item.price * qty for item, qty in self._items.items())

class Order:
    def __init__(self, order_id: str, user_id: str,
                 restaurant: Restaurant, items: dict[MenuItem, int]):
        self.id = order_id
        self.user_id = user_id
        self.restaurant = restaurant
        self.items = items
        self.status = OrderStatus.PLACED
        self.delivery_agent: str | None = None

    @property
    def total(self) -> float:
        return sum(item.price * qty for item, qty in self.items.items())

class DeliveryAgent:
    def __init__(self, agent_id: str, name: str):
        self.id = agent_id
        self.name = name
        self.is_available = True
        self.current_order: Order | None = None

class NotificationService:
    def notify(self, user_id: str, message: str) -> None:
        print(f"[Notification to {user_id}]: {message}")

class OrderService:
    def __init__(self):
        self._orders: dict[str, Order] = {}
        self._agents: list[DeliveryAgent] = []
        self._counter = 0
        self._notifier = NotificationService()

    def place_order(self, user_id: str, cart: Cart,
                    restaurant: Restaurant) -> Order:
        self._counter += 1
        order = Order(f"O{self._counter}", user_id, restaurant, dict(cart._items))
        self._orders[order.id] = order
        self._notifier.notify(user_id, f"Order {order.id} placed!")
        return order

    def update_status(self, order_id: str, status: OrderStatus) -> None:
        order = self._orders[order_id]
        order.status = status
        self._notifier.notify(order.user_id, f"Order {order_id}: {status.value}")
```

---

### 11.10 Splitwise / Bill Splitting

```python
from collections import defaultdict

class SplitType(Enum):
    EQUAL = "equal"
    EXACT = "exact"
    PERCENTAGE = "percentage"

class Expense:
    def __init__(self, expense_id: str, description: str,
                 amount: float, paid_by: str,
                 split_type: SplitType, split_with: dict[str, float]):
        """
        split_with: {user_id: share}
          EQUAL      → all shares equal, values are weights (1.0 each)
          EXACT      → values are exact amounts
          PERCENTAGE → values are percentages (must sum to 100)
        """
        self.id = expense_id
        self.description = description
        self.amount = amount
        self.paid_by = paid_by
        self.split_type = split_type
        self.split_with = split_with

    def get_shares(self) -> dict[str, float]:
        if self.split_type == SplitType.EQUAL:
            each = self.amount / len(self.split_with)
            return {u: each for u in self.split_with}
        if self.split_type == SplitType.EXACT:
            return dict(self.split_with)
        if self.split_type == SplitType.PERCENTAGE:
            return {u: self.amount * (p / 100) for u, p in self.split_with.items()}

class BalanceSheet:
    def __init__(self):
        self._balances: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    def add_expense(self, expense: Expense) -> None:
        shares = expense.get_shares()
        for user, share in shares.items():
            if user == expense.paid_by: continue
            self._balances[user][expense.paid_by] += share
            self._balances[expense.paid_by][user] -= share

    def simplify(self) -> list[tuple[str, str, float]]:
        """Minimum cash flow algorithm"""
        net: dict[str, float] = defaultdict(float)
        for debtor, creditors in self._balances.items():
            for creditor, amount in creditors.items():
                net[debtor] -= amount
                net[creditor] += amount

        debtors = sorted((v, k) for k, v in net.items() if v < 0)
        creditors = sorted((v, k) for k, v in net.items() if v > 0)
        transactions = []
        i, j = 0, 0
        while i < len(debtors) and j < len(creditors):
            debt, debtor = debtors[i]
            credit, creditor = creditors[j]
            paid = min(-debt, credit)
            transactions.append((debtor, creditor, paid))
            debtors[i] = (debt + paid, debtor)
            creditors[j] = (credit - paid, creditor)
            if debtors[i][0] == 0: i += 1
            if creditors[j][0] == 0: j += 1
        return transactions
```

---

### 11.11 Rate Limiter

```python
import time
from collections import deque

class RateLimiter(ABC):
    @abstractmethod
    def allow_request(self, user_id: str) -> bool: ...

class TokenBucketRateLimiter(RateLimiter):
    """Allows burst; smooths over time."""
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._buckets: dict[str, tuple[float, float]] = {}

    def allow_request(self, user_id: str) -> bool:
        now = time.time()
        tokens, last_refill = self._buckets.get(user_id, (self.capacity, now))
        tokens = min(self.capacity, tokens + (now - last_refill) * self.refill_rate)
        if tokens >= 1:
            self._buckets[user_id] = (tokens - 1, now)
            return True
        self._buckets[user_id] = (tokens, now)
        return False

class SlidingWindowRateLimiter(RateLimiter):
    """Strict: allows max N requests in last T seconds."""
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window = window_seconds
        self._windows: dict[str, deque] = {}

    def allow_request(self, user_id: str) -> bool:
        now = time.time()
        if user_id not in self._windows:
            self._windows[user_id] = deque()
        window = self._windows[user_id]
        while window and window[0] < now - self.window:
            window.popleft()
        if len(window) < self.max_requests:
            window.append(now)
            return True
        return False

class FixedWindowRateLimiter(RateLimiter):
    """Simple: N requests per window. Boundary burst issue."""
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window = window_seconds
        self._counts: dict[str, tuple[int, float]] = {}

    def allow_request(self, user_id: str) -> bool:
        now = time.time()
        count, start = self._counts.get(user_id, (0, now))
        if now - start > self.window:
            count, start = 0, now
        if count < self.max_requests:
            self._counts[user_id] = (count + 1, start)
            return True
        return False
```

---

### 11.12 Logger

```python
class LogLevel(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

class LogSink(ABC):
    @abstractmethod
    def write(self, message: str) -> None: ...

class ConsoleLogSink(LogSink):
    def write(self, message: str) -> None:
        print(message)

class FileLogSink(LogSink):
    def __init__(self, filepath: str):
        self._filepath = filepath

    def write(self, message: str) -> None:
        with open(self._filepath, "a") as f:
            f.write(message + "\n")

class LogFormatter(ABC):
    @abstractmethod
    def format(self, level: LogLevel, message: str) -> str: ...

class SimpleFormatter(LogFormatter):
    def format(self, level: LogLevel, message: str) -> str:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"[{ts}] [{level.name}] {message}"

class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._level = LogLevel.DEBUG
            cls._instance._sinks: list[LogSink] = [ConsoleLogSink()]
            cls._instance._formatter = SimpleFormatter()
        return cls._instance

    def set_level(self, level: LogLevel) -> None:
        self._level = level

    def add_sink(self, sink: LogSink) -> None:
        self._sinks.append(sink)

    def _log(self, level: LogLevel, message: str) -> None:
        if level.value >= self._level.value:
            formatted = self._formatter.format(level, message)
            for sink in self._sinks:
                sink.write(formatted)

    def debug(self, msg: str) -> None: self._log(LogLevel.DEBUG, msg)
    def info(self, msg: str) -> None: self._log(LogLevel.INFO, msg)
    def warning(self, msg: str) -> None: self._log(LogLevel.WARNING, msg)
    def error(self, msg: str) -> None: self._log(LogLevel.ERROR, msg)
    def critical(self, msg: str) -> None: self._log(LogLevel.CRITICAL, msg)
```

---

### 11.13 Cache (LRU)

```python
from collections import OrderedDict
from threading import Lock

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self._cache: OrderedDict = OrderedDict()
        self._lock = Lock()

    def get(self, key: str) -> any:
        with self._lock:
            if key not in self._cache:
                return None
            self._cache.move_to_end(key)        # mark as recently used
            return self._cache[key]

    def put(self, key: str, value: any) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = value
            if len(self._cache) > self.capacity:
                self._cache.popitem(last=False)  # evict LRU

    def __len__(self) -> int:
        return len(self._cache)

class CacheEntry:
    """For TTL-aware cache"""
    def __init__(self, value: any, ttl_seconds: float | None = None):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl_seconds

    def is_expired(self) -> bool:
        if self.ttl is None: return False
        return time.time() - self.created_at > self.ttl
```

---

## 12. Concurrency in LLD

### 12.1 Thread-Safe Singleton

```python
import threading

class ThreadSafeSingleton:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:        # double-checked locking
                    cls._instance = super().__new__(cls)
        return cls._instance
```

### 12.2 Producer-Consumer

```python
import threading
import queue

class ProducerConsumer:
    def __init__(self, buffer_size: int):
        self._queue = queue.Queue(maxsize=buffer_size)

    def producer(self, item: any) -> None:
        self._queue.put(item)          # blocks if full

    def consumer(self) -> any:
        return self._queue.get()       # blocks if empty
```

### 12.3 Read-Write Lock Pattern

```python
import threading

class ReadWriteLock:
    def __init__(self):
        self._read_count = 0
        self._write_lock = threading.Lock()
        self._read_lock = threading.Lock()

    def acquire_read(self):
        with self._read_lock:
            self._read_count += 1
            if self._read_count == 1:
                self._write_lock.acquire()

    def release_read(self):
        with self._read_lock:
            self._read_count -= 1
            if self._read_count == 0:
                self._write_lock.release()

    def acquire_write(self):
        self._write_lock.acquire()

    def release_write(self):
        self._write_lock.release()
```

### 12.4 Key Concurrency Concepts

| Concept | Meaning |
|---|---|
| **Race Condition** | Two threads access shared data simultaneously with unexpected result |
| **Deadlock** | Two threads wait for each other's lock forever |
| **Livelock** | Threads keep changing state in response to each other, making no progress |
| **Starvation** | A thread never gets CPU time |
| **Mutex** | Only one thread can hold it at a time |
| **Semaphore** | Allow N threads simultaneously |
| **Monitor** | Object-level lock with wait/notify |
| **Atomic operation** | Indivisible; no other thread sees intermediate state |

---

## 13. Common Interview Mistakes & Red Flags

### Red Flags Interviewers Watch For

```
✗ Jumping to code without clarifying requirements
✗ Making assumptions without stating them
✗ Using global variables instead of encapsulation
✗ God class (one class does everything)
✗ Deep inheritance hierarchies (> 3 levels)
✗ Concrete types in method signatures instead of abstractions
✗ No error handling / edge case discussion
✗ Not discussing thread safety when relevant
✗ Ignoring extensibility ("What if we add X later?")
✗ Forgetting to discuss trade-offs of chosen approach
```

### Green Flags

```
✓ Start with use cases and actors
✓ Draw class diagram before coding
✓ Name classes after domain concepts (ubiquitous language)
✓ Use enums for fixed sets of values
✓ Prefer composition over inheritance
✓ Program to interfaces, not implementations
✓ Discuss which design pattern you're using and why
✓ Consider thread safety explicitly
✓ Explain trade-offs (e.g., Singleton vs. dependency injection)
✓ Talk about extensibility: "If we need to add X, we'd..."
```

### Interview Template (30-45 min problem)

```
Minutes 0-5:   Clarify requirements, identify actors & use cases
Minutes 5-10:  Identify classes, attributes, relationships (class diagram)
Minutes 10-20: Core class implementations
Minutes 20-30: Key methods, edge cases, design patterns applied
Minutes 30-40: Extensibility discussion, concurrency if needed
Minutes 40-45: Walk through a scenario end-to-end
```

### Quick Pattern Selection Guide

```
Need one instance?                      → Singleton
Creating objects of many types?         → Factory Method or Abstract Factory
Complex object construction?            → Builder
Copy existing objects?                  → Prototype
Incompatible interfaces?                → Adapter
Add features without subclassing?       → Decorator
Simplify complex subsystem?             → Facade
Tree/part-whole hierarchy?              → Composite
Control expensive object access?        → Proxy
One-to-many change notification?        → Observer
Swap algorithms at runtime?             → Strategy
Undo/redo/queue actions?               → Command
Multiple handlers for one request?      → Chain of Responsibility
Freeze algorithm skeleton?              → Template Method
State-dependent behavior?               → State
Objects without tight coupling?         → Mediator
New ops on stable hierarchy?            → Visitor
```

---

*This file pairs with `DSA_PATTERNS.md` and `CONCEPTS.md` to form a complete interview preparation suite.*
