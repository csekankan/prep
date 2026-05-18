# Clean Code — Complete Guide with Python Examples

> Based on *Clean Code: A Handbook of Agile Software Craftsmanship* by Robert C. Martin ("Uncle Bob")

---

## The Core Philosophy

> "Clean code always looks like it was written by someone who cares." — Michael Feathers

> "You know you are working on clean code when each routine turns out to be pretty much what you expected." — Ward Cunningham

**LeBlanc's Law**: *Later equals never.* If you leave messy code saying "I'll clean it up later" — you won't.

**The Boy Scout Rule**: *Leave the codebase cleaner than you found it.* Every commit should improve the surrounding code, even if just renaming one variable.

**The Reading-to-Writing Ratio**: We spend 10x more time *reading* code than *writing* it. Making code easy to read makes it easy to write.

---

## Chapter 1: What Is Clean Code?

The masters define clean code as:

| Who | Definition |
|-----|-----------|
| **Bjarne Stroustrup** (C++ creator) | Elegant, efficient, minimal dependencies, complete error handling, does *one thing well* |
| **Grady Booch** | Reads like well-written prose, crisp abstractions, straightforward control flow |
| **Dave Thomas** | Readable by others, has tests, minimal API, literate |
| **Ron Jeffries** | No duplication, expressive, tiny abstractions |
| **Ward Cunningham** | Each routine is *pretty much what you expected* |

**Beck's Rules of Simple Design** (priority order):
1. Runs all the tests
2. Contains no duplication
3. Expresses the design intent
4. Minimizes the number of classes/methods

---

## Chapter 2: Meaningful Names

### Use Intention-Revealing Names

Names should tell you *why it exists*, *what it does*, and *how it's used*.

```python
# BAD
d = 0  # elapsed time in days
temp = get_them()

# GOOD
elapsed_days = 0
flagged_cells = get_flagged_cells()
```

### Avoid Disinformation

Don't use names with hidden meanings or that contradict reality.

```python
# BAD — it's not actually a list, it's a set
account_list = {acc1, acc2, acc3}

# GOOD
accounts = {acc1, acc2, acc3}
```

### Make Meaningful Distinctions

Don't add noise words just to satisfy the interpreter.

```python
# BAD — what's the difference?
def get_active_account(): ...
def get_active_accounts(): ...
def get_active_account_info(): ...

# BAD — number-series naming
def copy_chars(a1, a2):
    for i in range(len(a1)):
        a2[i] = a1[i]

# GOOD
def copy_chars(source, destination):
    for i in range(len(source)):
        destination[i] = source[i]
```

### Use Pronounceable Names

```python
# BAD
class DtaRcrd102:
    gen_ymdhms: datetime  # generation year/month/day/hour/minute/second
    mod_ymdhms: datetime
    pszqint = "102"

# GOOD
class Customer:
    generation_timestamp: datetime
    modification_timestamp: datetime
    record_id = "102"
```

### Use Searchable Names

The length of a name should correspond to the size of its scope.

```python
# BAD — magic numbers, unsearchable
for j in range(34):
    s += t[j] * 4 / 5

# GOOD
REAL_DAYS_PER_IDEAL_DAY = 4
WORK_DAYS_PER_WEEK = 5
total = 0
for j in range(NUMBER_OF_TASKS):
    real_task_days = task_estimate[j] * REAL_DAYS_PER_IDEAL_DAY
    real_task_weeks = real_task_days / WORK_DAYS_PER_WEEK
    total += real_task_weeks
```

### Avoid Encodings & Mental Mapping

```python
# BAD — Hungarian notation, prefixes
str_name = "Alice"
i_count = 0
m_description = ""  # member prefix

# GOOD
name = "Alice"
count = 0
description = ""
```

### Class Names = Nouns, Method Names = Verbs

```python
# GOOD class names (nouns)
class Customer: ...
class WikiPage: ...
class AddressParser: ...

# BAD class names (vague/verb-like)
class Manager: ...
class Processor: ...
class Data: ...

# GOOD method names (verbs)
def post_payment(self): ...
def delete_page(self): ...
def save(self): ...
```

### Pick One Word Per Concept

```python
# BAD — inconsistent vocabulary across classes
class UserRepo:
    def fetch_user(self): ...

class ProductRepo:
    def retrieve_product(self): ...

class OrderRepo:
    def get_order(self): ...

# GOOD — consistent vocabulary
class UserRepo:
    def get_user(self): ...

class ProductRepo:
    def get_product(self): ...

class OrderRepo:
    def get_order(self): ...
```

### Don't Pun

Don't use the same word for two different operations.

```python
# In many classes, `add` means combining two values
class Calculator:
    def add(self, a, b):
        return a + b

# In a collection class, adding an item is a different concept — use `insert` or `append`
class ItemCollection:
    def insert(self, item):   # NOT `add` — different semantic
        self._items.append(item)
```

### Add Meaningful Context

```python
# BAD — ambiguous standing alone
def print_guess_statistics(candidate: str, count: int):
    number = ""
    verb = ""
    plural_modifier = ""
    if count == 0:
        number = "no"
        verb = "are"
        plural_modifier = "s"
    elif count == 1:
        number = "1"
        verb = "is"
        plural_modifier = ""
    else:
        number = str(count)
        verb = "are"
        plural_modifier = "s"
    guess_message = f"There {verb} {number} {candidate}{plural_modifier}"
    print(guess_message)

# GOOD — context provided by a class
class GuessStatisticsMessage:
    def __init__(self):
        self._number = ""
        self._verb = ""
        self._plural_modifier = ""

    def make(self, candidate: str, count: int) -> str:
        self._create_plural_dependent_parts(count)
        return f"There {self._verb} {self._number} {candidate}{self._plural_modifier}"

    def _create_plural_dependent_parts(self, count: int):
        if count == 0:
            self._there_are_no_letters()
        elif count == 1:
            self._there_is_one_letter()
        else:
            self._there_are_many_letters(count)

    def _there_are_no_letters(self):
        self._number = "no"
        self._verb = "are"
        self._plural_modifier = "s"

    def _there_is_one_letter(self):
        self._number = "1"
        self._verb = "is"
        self._plural_modifier = ""

    def _there_are_many_letters(self, count: int):
        self._number = str(count)
        self._verb = "are"
        self._plural_modifier = "s"
```

---

## Chapter 3: Functions

### Rule 1: Functions Should Be Small

Functions should be 5-15 lines. If it's more than 20 lines, it's doing too much.

```python
# BAD — 40+ lines doing everything
def render_page(page_data, include_suite_setup):
    wiki_page = page_data.get_wiki_page()
    buffer = []
    if page_data.has_attribute("Test"):
        if include_suite_setup:
            suite_setup = find_inherited_page("SuiteSetUp", wiki_page)
            if suite_setup:
                path = get_path(suite_setup)
                buffer.append(f"!include -setup .{path}\n")
        setup = find_inherited_page("SetUp", wiki_page)
        if setup:
            path = get_path(setup)
            buffer.append(f"!include -setup .{path}\n")
    buffer.append(page_data.get_content())
    if page_data.has_attribute("Test"):
        teardown = find_inherited_page("TearDown", wiki_page)
        if teardown:
            path = get_path(teardown)
            buffer.append(f"\n!include -teardown .{path}\n")
        if include_suite_setup:
            suite_teardown = find_inherited_page("SuiteTearDown", wiki_page)
            if suite_teardown:
                path = get_path(suite_teardown)
                buffer.append(f"\n!include -teardown .{path}\n")
    page_data.set_content("".join(buffer))
    return page_data.get_html()

# GOOD — each function does one thing, reads like a story
def render_page_with_setups_and_teardowns(page_data, is_suite):
    if is_test_page(page_data):
        include_setup_and_teardown_pages(page_data, is_suite)
    return page_data.get_html()
```

### Rule 2: Do One Thing

> **FUNCTIONS SHOULD DO ONE THING. THEY SHOULD DO IT WELL. THEY SHOULD DO IT ONLY.**

If you can extract another function from it with a name that isn't a restatement, it's doing more than one thing.

```python
# BAD — does 3 things: validates, saves, and sends email
def create_user(name, email):
    if not name or not email:
        raise ValueError("Name and email required")
    if "@" not in email:
        raise ValueError("Invalid email")
    user = User(name=name, email=email)
    db.session.add(user)
    db.session.commit()
    send_welcome_email(user)
    return user

# GOOD — each function does one thing
def create_user(name: str, email: str) -> User:
    validate_user_input(name, email)
    user = save_user(name, email)
    send_welcome_email(user)
    return user

def validate_user_input(name: str, email: str):
    if not name or not email:
        raise ValueError("Name and email required")
    if "@" not in email:
        raise ValueError("Invalid email")

def save_user(name: str, email: str) -> User:
    user = User(name=name, email=email)
    db.session.add(user)
    db.session.commit()
    return user
```

### Rule 3: One Level of Abstraction Per Function (The Stepdown Rule)

Read code top-down like a newspaper — high-level summary first, details later.

```python
# BAD — mixed abstraction levels
def generate_report(data):
    report = Report()
    report.title = "Q4 Sales"                        # high level
    conn = psycopg2.connect("dbname=sales")           # low level detail
    cursor = conn.cursor()                             # low level detail
    cursor.execute("SELECT * FROM sales WHERE q=4")    # low level detail
    rows = cursor.fetchall()                           # low level detail
    report.add_summary(calculate_summary(rows))        # high level
    for row in rows:
        report.add_line(row[0], row[1], float(row[2])) # mid level
    return report.render()                             # high level

# GOOD — consistent abstraction, reads like a TO paragraph
# TO generate_report: we fetch the data, build the report, and render it.
def generate_report(quarter: int) -> str:
    data = fetch_sales_data(quarter)
    report = build_report(data)
    return report.render()

# TO fetch_sales_data: we query the sales database for the given quarter.
def fetch_sales_data(quarter: int) -> list[SalesRecord]:
    return sales_repository.find_by_quarter(quarter)

# TO build_report: we create a report with a summary and line items.
def build_report(data: list[SalesRecord]) -> Report:
    report = Report(title=f"Q{data[0].quarter} Sales")
    report.add_summary(calculate_summary(data))
    for record in data:
        report.add_line_item(record)
    return report
```

### Rule 4: Switch/If-Else Chains → Polymorphism

```python
# BAD — switch/if-else on type
def calculate_pay(employee):
    if employee.type == "COMMISSIONED":
        return calculate_commissioned_pay(employee)
    elif employee.type == "HOURLY":
        return calculate_hourly_pay(employee)
    elif employee.type == "SALARIED":
        return calculate_salaried_pay(employee)

# GOOD — polymorphism via inheritance
from abc import ABC, abstractmethod

class Employee(ABC):
    @abstractmethod
    def calculate_pay(self) -> Money: ...

class CommissionedEmployee(Employee):
    def calculate_pay(self) -> Money:
        return self.base_pay + self.commission

class HourlyEmployee(Employee):
    def calculate_pay(self) -> Money:
        return self.hours_worked * self.hourly_rate

class SalariedEmployee(Employee):
    def calculate_pay(self) -> Money:
        return self.monthly_salary

# Factory hides the only switch that should exist
class EmployeeFactory:
    @staticmethod
    def create(record: dict) -> Employee:
        match record["type"]:
            case "COMMISSIONED": return CommissionedEmployee(record)
            case "HOURLY":       return HourlyEmployee(record)
            case "SALARIED":     return SalariedEmployee(record)
            case _: raise InvalidEmployeeType(record["type"])
```

### Rule 5: Function Arguments — Fewer Is Better

**Ideal: 0 (niladic) → 1 (monadic) → 2 (dyadic) → 3 (triadic, avoid)**

```python
# BAD — too many positional arguments
def create_menu(title, background, color, font, size, is_visible, is_enabled):
    ...

# GOOD — wrap related args in an object
@dataclass
class MenuConfig:
    title: str
    background: str = "white"
    color: str = "black"
    font: str = "Arial"
    size: int = 12
    is_visible: bool = True
    is_enabled: bool = True

def create_menu(config: MenuConfig):
    ...
```

### Rule 6: No Flag Arguments

A boolean argument screams: "this function does two things."

```python
# BAD
def render(page_data, is_suite: bool):
    ...  # does different things based on boolean

# GOOD
def render_for_suite(page_data):
    ...

def render_for_single_test(page_data):
    ...
```

### Rule 7: No Side Effects

Your function promises to do one thing but secretly does another.

```python
# BAD — "check_password" secretly initializes the session
def check_password(username: str, password: str) -> bool:
    user = UserGateway.find_by_name(username)
    if user:
        coded_phrase = user.get_phrase_encoded_by_password()
        phrase = cryptographer.decrypt(coded_phrase, password)
        if phrase == "Valid Password":
            session.initialize()  # <-- HIDDEN SIDE EFFECT!
            return True
    return False

# GOOD — name reflects what it really does, or split it
def check_password_and_initialize_session(username: str, password: str) -> bool:
    ...

# BETTER — separate the two concerns
def is_valid_password(username: str, password: str) -> bool:
    user = UserGateway.find_by_name(username)
    if not user:
        return False
    return cryptographer.verify(user.encoded_phrase, password)

def login(username: str, password: str):
    if is_valid_password(username, password):
        session.initialize()
```

### Rule 8: Command-Query Separation

Functions should either **do something** (command) or **answer something** (query) — never both.

```python
# BAD — is it asking or setting?
# "if set("username", "unclebob")" — is it checking or assigning?
def set(attribute: str, value: str) -> bool:
    ...

# GOOD — separate command and query
def attribute_exists(attribute: str) -> bool:
    ...

def set_attribute(attribute: str, value: str):
    ...

if attribute_exists("username"):
    set_attribute("username", "unclebob")
```

### Rule 9: Prefer Exceptions to Error Codes

```python
# BAD — error codes lead to deeply nested if-else
if delete_page(page) == E_OK:
    if registry.delete_reference(page.name) == E_OK:
        if config_keys.delete_key(page.name) == E_OK:
            logger.info("page deleted")
        else:
            logger.error("configKey not deleted")
    else:
        logger.error("deleteReference failed")
else:
    logger.error("delete failed")

# GOOD — exceptions separate happy path from error handling
try:
    delete_page(page)
    registry.delete_reference(page.name)
    config_keys.delete_key(page.name)
except Exception as e:
    logger.error(e)
```

### Rule 10: Extract Try/Catch Blocks

Error handling is one thing — extract the body.

```python
# GOOD
def delete(page):
    try:
        delete_page_and_all_references(page)
    except Exception as e:
        log_error(e)

def delete_page_and_all_references(page):
    delete_page(page)
    registry.delete_reference(page.name)
    config_keys.delete_key(page.name)
```

### Rule 11: DRY (Don't Repeat Yourself)

> "Duplication may be the root of all evil in software."

```python
# BAD — validation duplicated everywhere
def create_user(data):
    if not data.get("email") or "@" not in data["email"]:
        raise ValueError("Invalid email")
    ...

def update_user(user_id, data):
    if not data.get("email") or "@" not in data["email"]:
        raise ValueError("Invalid email")
    ...

# GOOD — extract the shared logic
def validate_email(email: str):
    if not email or "@" not in email:
        raise ValueError("Invalid email")

def create_user(data):
    validate_email(data.get("email", ""))
    ...

def update_user(user_id, data):
    validate_email(data.get("email", ""))
    ...
```

---

## Chapter 4: Comments

### The Golden Rule

> "Don't comment bad code — rewrite it." — Kernighan & Plaugher

> "The proper use of comments is to compensate for our failure to express ourselves in code."

Comments lie. Code changes, comments don't always follow.  
**Truth can only be found in one place: the code.**

### Good Comments (rare but valuable)

```python
# 1. Legal/copyright
# Copyright (c) 2024 Acme Corp. Licensed under MIT.

# 2. Explanation of intent — WHY, not WHAT
# We sort these higher because the business rule prioritizes premium customers
return 1 if isinstance(other, StandardCustomer) else 0

# 3. Clarification of obscure library behavior
# SimpleDateFormat is not thread-safe, so we create a new instance each time
formatter = SimpleDateFormat("yyyy-MM-dd")

# 4. Warning of consequences
# WARNING: This test takes 30 minutes to run against production-sized data
def test_with_really_big_file(): ...

# 5. TODO (scan and eliminate regularly)
# TODO: We expect this to go away when we implement the checkout model
def make_version():
    return None

# 6. Amplification of non-obvious importance
trimmed = match.group(3).strip()
# the strip() is critical — leading spaces cause the parser
# to misidentify the item as a nested list
```

### Bad Comments (most comments)

```python
# BAD: Redundant — just restates the code
i += 1  # increment i

# BAD: Mumbling — unclear meaning
except IOError:
    # No properties files means all defaults are loaded
    pass  # WHO loads the defaults? WHEN?

# BAD: Journal comments — use git instead
# Changes:
# 11-Oct-2001: Reorganised the class (DG)
# 05-Nov-2001: Added getDescription() method (DG)

# BAD: Noise
class AnnualDateRule:
    """Default constructor."""
    def __init__(self):  # "Default constructor" adds nothing
        pass

    day_of_month: int  # The day of the month  <-- pure noise

# BAD: Commented-out code — just delete it, git remembers
# results_stream = formatter.get_result_stream()
# reader = StreamReader(results_stream)
# response.set_content(reader.read(formatter.byte_count))

# BAD: Closing brace comments — make the function shorter instead
for item in items:
    for sub in item.subs:
        process(sub)
    # end for sub
# end for item

# BAD: Attribution — git blame exists
# Added by Rick  <-- git knows this already
```

### Explain Yourself in Code, Not Comments

```python
# BAD
# Check to see if the employee is eligible for full benefits
if (employee.flags & HOURLY_FLAG) and employee.age > 65:
    ...

# GOOD — the code IS the documentation
if employee.is_eligible_for_full_benefits():
    ...
```

---

## Chapter 5: Formatting

### Vertical Formatting

**The Newspaper Metaphor**: A source file should read like a newspaper article.  
- **Top**: Name tells you if you're in the right place  
- **Upper**: High-level concepts and algorithms  
- **Lower**: Increasing detail  
- **Bottom**: Lowest-level helper functions  

**Guidelines**:
- Files should be 200-500 lines (most can be under 200)
- Blank lines separate concepts (like paragraphs)
- Related code should be vertically close
- Variables declared near their usage
- Instance variables at the top of the class
- Caller above the callee (Stepdown Rule)

```python
# GOOD — reads top to bottom, high-level first
class WikiPageResponder:
    def make_response(self, context, request) -> Response:
        page_name = self._get_page_name_or_default(request, "FrontPage")
        self._load_page(page_name, context)
        if self._page is None:
            return self._not_found_response(context, request)
        return self._make_page_response(context)

    def _get_page_name_or_default(self, request, default):
        name = request.get_resource()
        return name if name else default

    def _load_page(self, resource, context):
        path = PathParser.parse(resource)
        self._page = context.root.get_page(path)

    def _not_found_response(self, context, request):
        return NotFoundResponder().make_response(context, request)

    def _make_page_response(self, context):
        html = self._make_html(context)
        response = SimpleResponse()
        response.set_content(html)
        return response
```

### Horizontal Formatting

- Lines should be **80-120 characters** max
- Use whitespace to associate related things and separate unrelated things
- Consistent indentation is critical

```python
# GOOD — whitespace shows operator precedence
determinant = b*b - 4*a*c
root1 = (-b + math.sqrt(determinant)) / (2*a)
```

### Team Rules

- A team agrees on **one** formatting style
- Use automated formatters (`black`, `ruff` for Python)
- Consistency across the codebase matters more than individual preference

---

## Chapter 6: Objects and Data Structures

### Data Abstraction — Hide Implementation

```python
# BAD — exposes implementation (it's a Cartesian point)
class Point:
    x: float
    y: float

# GOOD — hides implementation (could be Cartesian OR polar)
class Point:
    def get_x(self) -> float: ...
    def get_y(self) -> float: ...
    def set_cartesian(self, x: float, y: float): ...
    def get_r(self) -> float: ...
    def get_theta(self) -> float: ...
    def set_polar(self, r: float, theta: float): ...
```

### Objects vs Data Structures — The Asymmetry

| | **Data Structures** | **Objects** |
|---|---|---|
| **Expose** | Data, no behavior | Behavior, hide data |
| **Easy to add** | New functions (without changing existing structures) | New types (without changing existing functions) |
| **Hard to add** | New types (must change all functions) | New functions (must change all classes) |

```python
# PROCEDURAL APPROACH — easy to add new functions, hard to add new shapes
class Square:
    side: float

class Circle:
    radius: float

def area(shape):
    if isinstance(shape, Square):
        return shape.side ** 2
    elif isinstance(shape, Circle):
        return math.pi * shape.radius ** 2

# OOP APPROACH — easy to add new shapes, hard to add new functions
class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

class Square(Shape):
    def __init__(self, side): self.side = side
    def area(self): return self.side ** 2

class Circle(Shape):
    def __init__(self, radius): self.radius = radius
    def area(self): return math.pi * self.radius ** 2
```

### The Law of Demeter

A method should only call methods on:
1. Its own object (`self`)
2. Objects passed as parameters
3. Objects it creates
4. Its direct component objects

```python
# BAD — "Train Wreck" (chaining through strangers)
output_dir = context.get_options().get_scratch_dir().get_absolute_path()

# GOOD — tell, don't ask
output_dir = context.get_scratch_directory_path()
```

---

## Chapter 7: Error Handling

### Use Exceptions, Not Return Codes

```python
# BAD
def get_user(user_id):
    user = db.find(user_id)
    if user is None:
        return None, "User not found"
    return user, None

user, error = get_user(123)
if error:
    handle_error(error)

# GOOD
def get_user(user_id: int) -> User:
    user = db.find(user_id)
    if user is None:
        raise UserNotFoundError(f"User {user_id} not found")
    return user
```

### Write Try-Catch-Finally First

Start with the exception behavior — it defines a scope like a transaction.

### Provide Context with Exceptions

```python
# BAD
raise Exception("Error")

# GOOD
raise OrderProcessingError(
    f"Failed to process order {order_id} for customer {customer_id}: "
    f"insufficient inventory for product {product_id}"
)
```

### Define Exception Classes by Caller's Needs

```python
# BAD — caller must catch many different exceptions
try:
    port.open()
except DeviceResponseError:
    report_port_error()
except ATM1212UnlockError:
    report_port_error()
except GMXError:
    report_port_error()

# GOOD — wrap third-party API with a single exception
class LocalPort:
    def __init__(self, inner_port):
        self._inner = inner_port

    def open(self):
        try:
            self._inner.open()
        except (DeviceResponseError, ATM1212UnlockError, GMXError) as e:
            raise PortDeviceError(e)

# Now the caller is clean:
try:
    port.open()
except PortDeviceError:
    report_port_error()
```

### Don't Return None / Don't Pass None

```python
# BAD — forces null checks everywhere
def get_employees():
    if no_employees:
        return None  # caller must remember to check

employees = get_employees()
if employees is not None:  # easy to forget this check
    total_pay = sum(e.pay for e in employees)

# GOOD — return empty collection
def get_employees() -> list[Employee]:
    if no_employees:
        return []

total_pay = sum(e.pay for e in get_employees())  # always safe
```

### The Special Case Pattern (Null Object)

```python
# Instead of checking for None everywhere, return a special case object
class MealExpenses:
    def get_total(self) -> int:
        raise NotImplementedError

class ActualMealExpenses(MealExpenses):
    def get_total(self) -> int:
        return self._actual_total

class PerDiemMealExpenses(MealExpenses):
    """Default when no meal expenses were filed."""
    def get_total(self) -> int:
        return PER_DIEM_DEFAULT

# Now the calling code is clean — no null checks
total = expenses.get_meal_expenses().get_total()
```

---

## Chapter 8: Boundaries

### Wrapping Third-Party Code

Don't let third-party APIs leak through your codebase.

```python
# BAD — Map/dict with broad interface passed everywhere
sensors: dict[str, Sensor] = {}
# anyone can clear() it, put wrong types, etc.

# GOOD — wrap it
class SensorRegistry:
    def __init__(self):
        self._sensors: dict[str, Sensor] = {}

    def get_by_id(self, sensor_id: str) -> Sensor:
        return self._sensors[sensor_id]

    def register(self, sensor: Sensor):
        self._sensors[sensor.id] = sensor
```

### Learning Tests

Write tests to explore third-party APIs. When the library upgrades, your learning tests tell you if anything changed.

### The Adapter Pattern for Code That Doesn't Exist Yet

When you need to integrate with a system that doesn't exist yet, define the interface you *wish* you had, then write an adapter later.

```python
# Define the interface you want
class Transmitter(ABC):
    @abstractmethod
    def transmit(self, frequency: float, data: bytes): ...

# Later, when the real API exists, write an adapter
class RealTransmitterAdapter(Transmitter):
    def __init__(self, real_api):
        self._api = real_api

    def transmit(self, frequency: float, data: bytes):
        self._api.send_signal(freq=frequency, payload=data)
```

---

## Chapter 9: Unit Tests

### The Three Laws of TDD

1. You may not write production code until you have a failing unit test
2. You may not write more of a unit test than is sufficient to fail
3. You may not write more production code than is sufficient to pass the test

### Test Code Is as Important as Production Code

Dirty tests are worse than no tests. Without clean tests, you lose the ability to change production code confidently.

### Clean Tests: Readable Above All

```python
# BAD — obscure test
def test_page():
    crawler.add_page(root, PathParser.parse("PageOne"))
    crawler.add_page(root, PathParser.parse("PageOne.ChildOne"))
    request = Request("root", "type:pages")
    response = responder.make_response(context, request)
    xml = response.get_content()
    assert "<name>PageOne</name>" in xml
    assert "<name>ChildOne</name>" in xml

# GOOD — Build-Operate-Check pattern
def test_get_page_hierarchy_as_xml():
    make_pages("PageOne", "PageOne.ChildOne", "PageOne.ChildOne.GrandChild")

    response = submit_request("root", "type:pages")

    assert_response_is_xml(response)
    assert_response_contains(response, "PageOne", "ChildOne", "GrandChild")
```

### One Concept Per Test

```python
# BAD — multiple concepts in one test
def test_month_operations():
    # Test adding months
    assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)
    # Test getting last day
    assert get_last_day_of_month(date(2024, 2, 1)) == 29
    # Test quarter calculation
    assert get_quarter(date(2024, 3, 15)) == 1

# GOOD — separate test per concept
def test_adding_months_adjusts_for_shorter_month():
    assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)

def test_leap_year_february_has_29_days():
    assert get_last_day_of_month(date(2024, 2, 1)) == 29

def test_march_is_in_first_quarter():
    assert get_quarter(date(2024, 3, 15)) == 1
```

### F.I.R.S.T. Principles

| Principle | Meaning |
|-----------|---------|
| **F**ast | Tests should run quickly (milliseconds, not seconds) |
| **I**ndependent | Tests should not depend on each other |
| **R**epeatable | Tests should work in any environment (dev, CI, offline) |
| **S**elf-Validating | Tests should have a boolean output (pass/fail, not manual inspection) |
| **T**imely | Tests should be written just before the production code |

---

## Chapter 10: Classes

### Classes Should Be Small (Measured by Responsibilities, Not Lines)

```python
# BAD — God class with too many responsibilities
class Employee:
    def calculate_pay(self): ...
    def report_hours(self): ...
    def save(self): ...
    def generate_report(self): ...
    def send_email(self): ...
    def format_address(self): ...

# GOOD — Single Responsibility Principle
class Employee:
    def __init__(self, name, pay_calculator):
        self.name = name
        self._pay_calculator = pay_calculator

    def calculate_pay(self):
        return self._pay_calculator.calculate(self)

class HourReporter:
    def report_hours(self, employee): ...

class EmployeeRepository:
    def save(self, employee): ...
```

### The Single Responsibility Principle (SRP)

> A class should have one, and only one, reason to change.

```python
# BAD — two reasons to change: business rules AND persistence
class Employee:
    def calculate_pay(self): ...  # business rule change
    def save(self): ...           # database change

# GOOD — separated responsibilities
class Employee:
    def calculate_pay(self): ...

class EmployeeRepository:
    def save(self, employee): ...
```

**How to name it**: If you can't describe a class in ~25 words without "and", "or", "if", "but" — it has too many responsibilities.

### Cohesion

A class is maximally cohesive when every method uses every instance variable. Strive for high cohesion.

```python
# HIGH COHESION — every method uses the instance variables
class Stack:
    def __init__(self):
        self._top = 0
        self._elements = [None] * 10

    def size(self):
        return self._top

    def push(self, element):
        self._elements[self._top] = element
        self._top += 1

    def pop(self):
        if self._top == 0:
            raise EmptyStackError()
        self._top -= 1
        return self._elements[self._top]
```

When cohesion drops (some methods use some variables, other methods use others), **split the class**.

### Open/Closed Principle (OCP) — Isolating from Change

```python
# BAD — must modify existing class for every new SQL provider
class Sql:
    def create(self, table, columns): ...
    def insert(self, table, fields, values): ...
    def select(self, table, column, pattern): ...
    def find_by_key(self, table, column, key): ...
    # every new statement type requires modifying this class

# GOOD — open for extension, closed for modification
class Sql(ABC):
    @abstractmethod
    def generate(self) -> str: ...

class CreateSql(Sql):
    def generate(self) -> str: ...

class InsertSql(Sql):
    def generate(self) -> str: ...

class SelectSql(Sql):
    def generate(self) -> str: ...
```

---

## Chapter 11: Systems

### Separate Construction from Use

```python
# BAD — construction mixed with business logic
class LineItemProcessor:
    def process(self, order):
        service = CreditCardService()  # hard-coded dependency
        ...

# GOOD — Dependency Injection
class LineItemProcessor:
    def __init__(self, payment_service: PaymentService):
        self._payment_service = payment_service

    def process(self, order):
        self._payment_service.charge(order.total)
```

### Cross-Cutting Concerns

Use decorators/aspects for logging, transactions, caching, security — don't pollute business logic.

```python
# BAD — cross-cutting concern pollutes business logic
class BankAccount:
    def transfer(self, target, amount):
        logger.info(f"Transfer {amount} to {target}")
        if not self.has_permission("transfer"):
            raise PermissionError()
        db.begin_transaction()
        try:
            self.balance -= amount
            target.balance += amount
            db.commit()
        except:
            db.rollback()
            raise
        logger.info("Transfer complete")

# GOOD — decorators handle cross-cutting concerns
class BankAccount:
    @logged
    @requires_permission("transfer")
    @transactional
    def transfer(self, target, amount):
        self.balance -= amount
        target.balance += amount
```

---

## Chapter 12: Emergence — Simple Design Rules

Kent Beck's four rules of *Simple Design* (priority order):

### 1. Runs All the Tests

A system that can't be verified can't be trusted. Testable systems naturally end up with small, single-purpose classes.

### 2. No Duplication

```python
# DUPLICATION — two methods share the same structure
def scale_to_one_dimension(desired_dimension, image_dimension):
    if abs(desired_dimension - image_dimension) < ERROR_THRESHOLD:
        return
    scaling_factor = desired_dimension / image_dimension
    scaling_factor = max(min(scaling_factor, MAX_SCALE), MIN_SCALE)
    replicate_image(scaling_factor)

def rotate(degrees):
    replicate_image(degrees)  # shares replicate_image

# Both methods share a "replicate" step — extract the common part
```

### 3. Expressive

- Good names
- Small functions and classes
- Standard design patterns (use names like `Command`, `Visitor`, `Decorator`)
- Well-written tests that act as documentation

### 4. Minimal Classes and Methods

Don't create classes/methods just because of dogma. This rule has the *lowest* priority — don't over-engineer.

---

## Chapter 13: Concurrency

### Why Concurrency Is Hard

Concurrency is a *decoupling* strategy — it separates **what** gets done from **when**.

### Myths and Misconceptions

| Myth | Reality |
|------|---------|
| Concurrency always improves performance | Only when there's wait time to share between threads |
| Design doesn't change with concurrency | Concurrency design is fundamentally different |
| Understanding concurrency isn't important with containers | You must understand it to debug issues |

### Defense Principles

```python
# 1. SRP — Keep concurrency code separate from business logic
# 2. Limit shared data scope
# 3. Use copies of data rather than sharing
# 4. Threads should be as independent as possible

# BAD — shared mutable state
class Counter:
    def __init__(self):
        self.count = 0  # shared, unprotected

    def increment(self):
        self.count += 1  # NOT atomic!

# GOOD — use thread-safe primitives
import threading

class Counter:
    def __init__(self):
        self._count = 0
        self._lock = threading.Lock()

    def increment(self):
        with self._lock:
            self._count += 1

    @property
    def count(self):
        with self._lock:
            return self._count
```

### Know Your Execution Models

| Model | Description |
|-------|-------------|
| **Producer-Consumer** | Producers create work, consumers process it, bounded queue between |
| **Readers-Writers** | Many readers, few writers; balance throughput vs. starvation |
| **Dining Philosophers** | Competing processes need multiple resources; beware deadlock |

### Testing Threaded Code

- Treat spurious failures as candidate threading issues
- Get nonthreaded code working first
- Make threaded code pluggable (vary thread count, speed)
- Run with more threads than processors
- Run on different platforms

---

## Chapter 17: Smells and Heuristics — The Complete Checklist

### Comments

| Code | Smell | Fix |
|------|-------|-----|
| C1 | Inappropriate information (changelogs, metadata) | Use source control |
| C2 | Obsolete comment | Delete it |
| C3 | Redundant comment (restates code) | Delete it |
| C4 | Poorly written comment | Rewrite clearly or delete |
| C5 | Commented-out code | Delete it — git remembers |

### Environment

| Code | Smell | Fix |
|------|-------|-----|
| E1 | Build requires more than one step | One command: `make` / `pip install` |
| E2 | Tests require more than one step | One command: `pytest` |

### Functions

| Code | Smell | Fix |
|------|-------|-----|
| F1 | Too many arguments | Wrap in objects, reduce to ≤2 |
| F2 | Output arguments | Use return values or `self` |
| F3 | Flag arguments | Split into two functions |
| F4 | Dead function | Delete it |

### General

| Code | Smell | Fix |
|------|-------|-----|
| G1 | Multiple languages in one file | Minimize; isolate if unavoidable |
| G2 | Obvious behavior not implemented | `day_of_week("MONDAY")` should return `Day.MONDAY` |
| G3 | Incorrect behavior at boundaries | Test edge cases exhaustively |
| G4 | Overridden safeties | Don't turn off compiler warnings or failing tests |
| G5 | Duplication | **THE cardinal rule** — DRY, always |
| G6 | Code at wrong level of abstraction | Base class shouldn't know implementation details |
| G7 | Base class depends on derivatives | Base should know nothing about subclasses |
| G8 | Too much information | Narrow interfaces; hide data; few methods |
| G9 | Dead code | Delete unreachable code |
| G10 | Vertical separation | Define variables/functions close to where they're used |
| G11 | Inconsistency | If you name one `process_request`, don't name another `handle_query` |
| G12 | Clutter | Remove unused variables, unreachable code, needless comments |
| G13 | Artificial coupling | Don't put general enums inside specific classes |
| G14 | Feature envy | A method uses another class's data more than its own → move it |
| G15 | Selector arguments | Booleans/enums that pick behavior → use polymorphism |
| G16 | Obscured intent | Code is too clever/compressed to read |
| G17 | Misplaced responsibility | Put code where the reader expects it |
| G18 | Inappropriate static | If it might need polymorphism, make it non-static |
| G19 | Use explanatory variables | Break up complex expressions |
| G20 | Function names should say what they do | `date.add(5)` — add what? → `date.add_days(5)` |
| G21 | Understand the algorithm | Don't just hack until tests pass; truly understand it |
| G22 | Make logical dependencies physical | Don't assume; pass the data explicitly |
| G23 | Prefer polymorphism to if/else or switch/case | One switch max (in a factory) |
| G24 | Follow standard conventions | Team-agreed style and patterns |
| G25 | Replace magic numbers with named constants | `SECONDS_PER_DAY = 86400` |
| G26 | Be precise | Don't use `float` for currency; don't ignore concurrency |
| G27 | Structure over convention | Use language features over relying on discipline |
| G28 | Encapsulate conditionals | `if is_eligible(employee)` not `if (flags & HOURLY) and age > 65` |
| G29 | Avoid negative conditionals | `if is_buffer_ready()` not `if not is_buffer_empty()` |
| G30 | Functions should do one thing | Already said — it's that important |
| G31 | Hidden temporal couplings | Make time ordering explicit via return values |
| G32 | Don't be arbitrary | Structure should communicate intent |
| G33 | Encapsulate boundary conditions | `next_level = level + 1` → use throughout |
| G34 | Functions should descend one level of abstraction | Don't mix `getHtml()` with `.append("\n")` |
| G35 | Keep configurable data at high levels | Constants belong in top-level configs |
| G36 | Avoid transitive navigation | A shouldn't know about C through B (Law of Demeter) |

### Names

| Code | Smell | Fix |
|------|-------|-----|
| N1 | Choose descriptive names | Take time; the payoff is huge |
| N2 | Names at appropriate abstraction level | `Phone` not `CellPhone` in a base class |
| N3 | Use standard nomenclature | `Decorator`, `Iterator`, `Visitor` — patterns have names |
| N4 | Unambiguous names | `rename_page_and_optionally_all_references` not just `rename` |
| N5 | Use long names for long scopes | `i` is fine in a 3-line loop; `employeePaymentHistory` for a class field |
| N6 | Avoid encodings | No Hungarian notation; no `m_` prefixes |
| N7 | Names should describe side effects | `create_or_return_oos` not `get_oos` if it creates on miss |

### Tests

| Code | Smell | Fix |
|------|-------|-----|
| T1 | Insufficient tests | Test everything that could break |
| T2 | Use a coverage tool | Make untested code visible |
| T3 | Don't skip trivial tests | They document behavior cheaply |
| T4 | An ignored test = a question about ambiguity | Don't `@skip` without reason |
| T5 | Test boundary conditions | Off-by-one, empty, null, max, min |
| T6 | Exhaustively test near bugs | Bugs cluster — test neighboring code |
| T7 | Patterns of failure are revealing | If tests fail for inputs > 5 chars, that's a clue |
| T8 | Test coverage patterns are revealing | Untested code near tested code = risk |
| T9 | Tests should be fast | Slow tests don't get run |

---

## Quick Reference: The Clean Code Cheat Sheet

```
┌──────────────────────────────────────────────────────┐
│                 CLEAN CODE RULES                     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  NAMES                                               │
│  ├─ Reveal intent (why, what, how)                   │
│  ├─ Pronounceable and searchable                     │
│  ├─ No encodings or mental mapping                   │
│  ├─ Classes = Nouns, Methods = Verbs                 │
│  └─ One word per concept, no puns                    │
│                                                      │
│  FUNCTIONS                                           │
│  ├─ Small (5-15 lines)                               │
│  ├─ Do ONE thing                                     │
│  ├─ One level of abstraction                         │
│  ├─ ≤ 2 arguments                                    │
│  ├─ No side effects                                  │
│  ├─ No flag arguments                                │
│  ├─ Command-Query Separation                         │
│  ├─ Prefer exceptions over error codes               │
│  └─ DRY (Don't Repeat Yourself)                      │
│                                                      │
│  COMMENTS                                            │
│  ├─ Express yourself in code first                   │
│  ├─ Only: legal, intent, warning, TODO               │
│  ├─ Never: redundant, journal, noise                 │
│  └─ Delete commented-out code                        │
│                                                      │
│  FORMATTING                                          │
│  ├─ Newspaper metaphor (high → low)                  │
│  ├─ Blank lines separate concepts                    │
│  ├─ Related code stays close                         │
│  ├─ 80-120 char lines                                │
│  └─ Team rules > personal preference                 │
│                                                      │
│  CLASSES                                             │
│  ├─ Small (by responsibility count)                  │
│  ├─ Single Responsibility Principle                  │
│  ├─ High cohesion                                    │
│  ├─ Open/Closed Principle                            │
│  └─ Depend on abstractions                           │
│                                                      │
│  ERROR HANDLING                                      │
│  ├─ Use exceptions, not return codes                 │
│  ├─ Provide context in exceptions                    │
│  ├─ Define exceptions by caller needs                │
│  ├─ Don't return None                                │
│  └─ Don't pass None                                  │
│                                                      │
│  TESTS                                               │
│  ├─ F.I.R.S.T. (Fast, Independent, Repeatable,      │
│  │   Self-Validating, Timely)                        │
│  ├─ One concept per test                             │
│  ├─ Test code = production quality                   │
│  └─ Build-Operate-Check pattern                      │
│                                                      │
│  DESIGN                                              │
│  ├─ Runs all tests                                   │
│  ├─ No duplication                                   │
│  ├─ Expressive                                       │
│  └─ Minimal classes and methods                      │
│                                                      │
└──────────────────────────────────────────────────────┘
```

---

## The Professional's Oath

> "The only way to go fast is to keep the code clean."

> "A programmer who writes clean code is an artist who can take a blank screen through a series of transformations until it is an elegantly coded system."

> "Master programmers think of systems as stories to be told rather than programs to be written."

The goal isn't perfection — it's **continuous improvement**. Every time you touch code, leave it a little better than you found it. That is the essence of clean code.
