# Company-Specific LLD Problems

A curated collection of Low-Level Design problems frequently asked at **Microsoft**, **Amazon**, and **Adobe**. Each problem includes requirements, key entities, design patterns, core class structures, implementation highlights, concurrency strategies, and company-specific interview tips.

> **How to use this chapter:** Pick a company you're interviewing with, solve each problem in 45–60 minutes under timed conditions, then compare with the reference design. Focus on the patterns and trade-offs — interviewers care more about your design reasoning than perfect code.

---

## Table of Contents

### Microsoft LLD Series
1. [Online Book System](#1-online-book-system-microsoft)
2. [Sudoku Board Game](#2-sudoku-board-game-microsoft)
3. [MS Excel](#3-ms-excel-microsoft)
4. [Design malloc() API](#4-design-malloc-api-microsoft)
5. [Design strtok() API](#5-design-strtok-api-microsoft)

### Amazon Series
6. [BookMyShow](#6-bookmyshow-amazon)
7. [Job Scheduler](#7-job-scheduler-amazon)
8. [Stock Broker Platform](#8-stock-broker-platform-amazon)
9. [YouTube](#9-youtube-amazon)
10. [Google Photos](#10-google-photos-amazon)
11. [Twitch](#11-twitch-amazon)

### Adobe Series
12. [Notification Service](#12-notification-service-adobe)
13. [Cache System](#13-cache-system-adobe)
14. [Configuration Management Service](#14-configuration-management-service-adobe)
15. [Train Ticket Booking](#15-train-ticket-booking-adobe)
16. [Warehouse Management System](#16-warehouse-management-system-adobe)
17. [Task Scheduler (DAG-based)](#17-task-scheduler-dag-based-adobe)
18. [Client-Side Rate Limiter](#18-client-side-rate-limiter-adobe)

---

# Microsoft LLD Series

---

## 1. Online Book System (Microsoft)

### Requirements

- Users can search the catalog by title, author, ISBN, or genre
- Users can borrow available books and return them before the due date
- The system tracks borrowing history for each user
- Users can reserve books that are currently checked out
- Admins can add, remove, and update books in the catalog
- Late returns incur fines calculated per day
- Each user has a borrowing limit (max concurrent borrows)
- The system sends notifications when reserved books become available

### Key Entities and Relationships

```
User ──borrows──▶ BookCopy ──instanceOf──▶ Book
User ──reserves──▶ Book
BookCopy ──status──▶ {AVAILABLE, BORROWED, RESERVED, LOST}
BorrowRecord links User ↔ BookCopy with dates and fines
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **Repository** | `BookCatalog` abstracts storage and search |
| **Observer** | Notify waiting users when a reserved book is returned |
| **Strategy** | Pluggable search strategies (by title, author, full-text) |
| **State** | `BookCopy` transitions through availability states |

### Core Class Structure

```python
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import threading
import uuid


class BookStatus(Enum):
    AVAILABLE = "available"
    BORROWED = "borrowed"
    RESERVED = "reserved"
    LOST = "lost"


class MembershipType(Enum):
    BASIC = "basic"
    PREMIUM = "premium"


@dataclass
class Book:
    isbn: str
    title: str
    author: str
    genre: str
    publication_year: int
    total_copies: int = 0

    def matches(self, query: str) -> bool:
        query_lower = query.lower()
        return (
            query_lower in self.title.lower()
            or query_lower in self.author.lower()
            or query_lower == self.isbn.lower()
            or query_lower in self.genre.lower()
        )


@dataclass
class BookCopy:
    copy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    book: Book = None
    status: BookStatus = BookStatus.AVAILABLE
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def checkout(self) -> bool:
        with self._lock:
            if self.status == BookStatus.AVAILABLE:
                self.status = BookStatus.BORROWED
                return True
            return False

    def return_copy(self) -> None:
        with self._lock:
            self.status = BookStatus.AVAILABLE

    def mark_reserved(self) -> None:
        with self._lock:
            self.status = BookStatus.RESERVED


@dataclass
class BorrowRecord:
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    copy_id: str = ""
    borrow_date: datetime = field(default_factory=datetime.now)
    due_date: datetime = None
    return_date: Optional[datetime] = None
    fine: float = 0.0

    def __post_init__(self):
        if self.due_date is None:
            self.due_date = self.borrow_date + timedelta(days=14)

    def calculate_fine(self, rate_per_day: float = 1.0) -> float:
        if self.return_date and self.return_date > self.due_date:
            overdue_days = (self.return_date - self.due_date).days
            self.fine = overdue_days * rate_per_day
        return self.fine


class ReservationObserver(ABC):
    @abstractmethod
    def on_book_available(self, book: Book, user_id: str) -> None:
        pass


class EmailNotifier(ReservationObserver):
    def on_book_available(self, book: Book, user_id: str) -> None:
        print(f"[Email] '{book.title}' is now available for user {user_id}")


class User:
    BORROW_LIMITS = {MembershipType.BASIC: 3, MembershipType.PREMIUM: 10}

    def __init__(self, user_id: str, name: str,
                 membership: MembershipType = MembershipType.BASIC):
        self.user_id = user_id
        self.name = name
        self.membership = membership
        self.active_borrows: list[BorrowRecord] = []
        self.borrow_history: list[BorrowRecord] = []
        self.total_fines: float = 0.0

    @property
    def borrow_limit(self) -> int:
        return self.BORROW_LIMITS[self.membership]

    def can_borrow(self) -> bool:
        return len(self.active_borrows) < self.borrow_limit and self.total_fines == 0.0


class BookCatalog:
    def __init__(self):
        self._books: dict[str, Book] = {}
        self._copies: dict[str, list[BookCopy]] = {}
        self._lock = threading.Lock()

    def add_book(self, book: Book, num_copies: int = 1) -> None:
        with self._lock:
            self._books[book.isbn] = book
            book.total_copies = num_copies
            self._copies[book.isbn] = [
                BookCopy(book=book) for _ in range(num_copies)
            ]

    def search(self, query: str) -> list[Book]:
        return [b for b in self._books.values() if b.matches(query)]

    def find_available_copy(self, isbn: str) -> Optional[BookCopy]:
        for copy in self._copies.get(isbn, []):
            if copy.status == BookStatus.AVAILABLE:
                return copy
        return None

    def get_all_copies(self, isbn: str) -> list[BookCopy]:
        return self._copies.get(isbn, [])


class LibrarySystem:
    def __init__(self):
        self.catalog = BookCatalog()
        self._users: dict[str, User] = {}
        self._reservations: dict[str, list[str]] = {}  # isbn -> [user_ids]
        self._observers: list[ReservationObserver] = [EmailNotifier()]
        self._lock = threading.Lock()

    def register_user(self, user: User) -> None:
        self._users[user.user_id] = user

    def borrow_book(self, user_id: str, isbn: str) -> Optional[BorrowRecord]:
        user = self._users.get(user_id)
        if not user or not user.can_borrow():
            return None

        copy = self.catalog.find_available_copy(isbn)
        if not copy:
            return None

        if not copy.checkout():
            return None

        record = BorrowRecord(user_id=user_id, copy_id=copy.copy_id)
        user.active_borrows.append(record)
        return record

    def return_book(self, user_id: str, copy_id: str) -> float:
        user = self._users.get(user_id)
        if not user:
            return 0.0

        record = next(
            (r for r in user.active_borrows if r.copy_id == copy_id), None
        )
        if not record:
            return 0.0

        record.return_date = datetime.now()
        fine = record.calculate_fine()
        user.total_fines += fine
        user.active_borrows.remove(record)
        user.borrow_history.append(record)

        for copies in self.catalog._copies.values():
            for copy in copies:
                if copy.copy_id == copy_id:
                    copy.return_copy()
                    self._notify_reservations(copy.book)
                    break

        return fine

    def reserve_book(self, user_id: str, isbn: str) -> bool:
        with self._lock:
            if isbn not in self._reservations:
                self._reservations[isbn] = []
            if user_id not in self._reservations[isbn]:
                self._reservations[isbn].append(user_id)
                return True
            return False

    def _notify_reservations(self, book: Book) -> None:
        with self._lock:
            waitlist = self._reservations.get(book.isbn, [])
            if waitlist:
                next_user = waitlist.pop(0)
                for observer in self._observers:
                    observer.on_book_available(book, next_user)
```

### Key Implementation Logic

The `borrow_book` flow validates the user's eligibility (under borrow limit, no outstanding fines), locates an available copy using the catalog, atomically transitions the copy status via `BookCopy.checkout()`, and creates a `BorrowRecord`. The per-copy lock prevents two threads from checking out the same physical copy simultaneously.

### Concurrency Handling

- **Per-copy locks** on `BookCopy` prevent double-checkout of the same physical copy
- **Catalog-level lock** protects structural mutations (adding/removing books)
- **System-level lock** guards the reservation queue to prevent lost notifications
- Fine calculation is idempotent — safe to retry on failure

### Interview Tips (Microsoft)

- **Start with the data model** — Microsoft interviewers value clean entity design. Draw `Book`, `BookCopy`, `User`, and `BorrowRecord` before writing code.
- **Discuss state transitions** explicitly — the `BookStatus` enum and its valid transitions show attention to correctness.
- **Mention extensibility** — how would you add eBooks, audiobooks, or inter-library loans? Show you think beyond the immediate requirements.
- **Highlight the Observer pattern** for reservations — Microsoft values pattern awareness.
- **Discuss fine policies** as a Strategy pattern — interviewers appreciate configurable business rules.

---

## 2. Sudoku Board Game (Microsoft)

### Requirements

- Support standard 9×9 Sudoku boards with 3×3 sub-grids
- Validate board state (row, column, and box constraints) efficiently
- Implement a solver using backtracking with constraint propagation
- Provide a hint system that reveals one correct cell value
- Support multiple difficulty levels (Easy, Medium, Hard, Expert)
- Generate valid Sudoku puzzles by removing cells from a solved board
- Allow undo/redo of player moves
- Detect when the puzzle is complete and correct

### Key Entities and Relationships

```
SudokuGame ──has──▶ Board ──contains──▶ Cell[9][9]
SudokuGame ──uses──▶ Solver
SudokuGame ──uses──▶ PuzzleGenerator
Cell ──status──▶ {GIVEN, PLAYER_FILLED, EMPTY}
MoveHistory tracks undo/redo stack
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **Command** | `PlaceNumberCommand` / `ClearCellCommand` with undo/redo |
| **Strategy** | Different solver strategies (backtracking, constraint propagation) |
| **Memento** | Save/restore board state for undo |
| **Template Method** | `PuzzleGenerator` with varying difficulty removal strategies |

### Core Class Structure

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import random
import copy


class Difficulty(Enum):
    EASY = 36        # cells to remove
    MEDIUM = 46
    HARD = 52
    EXPERT = 58


class CellType(Enum):
    GIVEN = "given"
    PLAYER = "player"
    EMPTY = "empty"


@dataclass
class Cell:
    row: int
    col: int
    value: int = 0
    cell_type: CellType = CellType.EMPTY
    notes: set[int] = field(default_factory=set)

    @property
    def is_empty(self) -> bool:
        return self.value == 0

    @property
    def is_modifiable(self) -> bool:
        return self.cell_type != CellType.GIVEN

    def set_value(self, value: int) -> bool:
        if not self.is_modifiable:
            return False
        self.value = value
        self.cell_type = CellType.PLAYER if value != 0 else CellType.EMPTY
        self.notes.clear()
        return True


class Board:
    SIZE = 9
    BOX_SIZE = 3

    def __init__(self):
        self.grid: list[list[Cell]] = [
            [Cell(r, c) for c in range(self.SIZE)] for r in range(self.SIZE)
        ]

    def get_cell(self, row: int, col: int) -> Cell:
        return self.grid[row][col]

    def is_valid_placement(self, row: int, col: int, num: int) -> bool:
        for c in range(self.SIZE):
            if c != col and self.grid[row][c].value == num:
                return False

        for r in range(self.SIZE):
            if r != row and self.grid[r][col].value == num:
                return False

        box_row, box_col = (row // self.BOX_SIZE) * self.BOX_SIZE, (col // self.BOX_SIZE) * self.BOX_SIZE
        for r in range(box_row, box_row + self.BOX_SIZE):
            for c in range(box_col, box_col + self.BOX_SIZE):
                if (r, c) != (row, col) and self.grid[r][c].value == num:
                    return False

        return True

    def is_complete(self) -> bool:
        return all(
            not cell.is_empty and self.is_valid_placement(cell.row, cell.col, cell.value)
            for row in self.grid for cell in row
        )

    def get_candidates(self, row: int, col: int) -> set[int]:
        if not self.grid[row][col].is_empty:
            return set()
        return {n for n in range(1, 10) if self.is_valid_placement(row, col, n)}

    def clone(self) -> "Board":
        return copy.deepcopy(self)

    def __str__(self) -> str:
        lines = []
        for r in range(self.SIZE):
            if r % self.BOX_SIZE == 0 and r != 0:
                lines.append("------+-------+------")
            row_str = ""
            for c in range(self.SIZE):
                if c % self.BOX_SIZE == 0 and c != 0:
                    row_str += "| "
                val = self.grid[r][c].value
                row_str += f"{val if val != 0 else '.'} "
            lines.append(row_str)
        return "\n".join(lines)


@dataclass
class Move:
    row: int
    col: int
    old_value: int
    new_value: int


class MoveHistory:
    def __init__(self):
        self._undo_stack: list[Move] = []
        self._redo_stack: list[Move] = []

    def record(self, move: Move) -> None:
        self._undo_stack.append(move)
        self._redo_stack.clear()

    def undo(self) -> Optional[Move]:
        if not self._undo_stack:
            return None
        move = self._undo_stack.pop()
        self._redo_stack.append(move)
        return move

    def redo(self) -> Optional[Move]:
        if not self._redo_stack:
            return None
        move = self._redo_stack.pop()
        self._undo_stack.append(move)
        return move


class SudokuSolver:
    def solve(self, board: Board) -> bool:
        empty = self._find_most_constrained(board)
        if empty is None:
            return True

        row, col = empty
        for num in board.get_candidates(row, col):
            board.grid[row][col].value = num
            if self.solve(board):
                return True
            board.grid[row][col].value = 0

        return False

    def _find_most_constrained(self, board: Board) -> Optional[tuple[int, int]]:
        """MRV heuristic: pick the empty cell with fewest candidates."""
        best, min_candidates = None, 10
        for r in range(board.SIZE):
            for c in range(board.SIZE):
                if board.grid[r][c].is_empty:
                    count = len(board.get_candidates(r, c))
                    if count < min_candidates:
                        min_candidates = count
                        best = (r, c)
                        if count == 1:
                            return best
        return best

    def count_solutions(self, board: Board, limit: int = 2) -> int:
        empty = self._find_most_constrained(board)
        if empty is None:
            return 1

        row, col = empty
        total = 0
        for num in board.get_candidates(row, col):
            board.grid[row][col].value = num
            total += self.count_solutions(board, limit)
            board.grid[row][col].value = 0
            if total >= limit:
                break
        return total


class PuzzleGenerator:
    def __init__(self):
        self._solver = SudokuSolver()

    def generate(self, difficulty: Difficulty) -> Board:
        board = Board()
        self._fill_diagonal_boxes(board)
        self._solver.solve(board)

        for r in range(Board.SIZE):
            for c in range(Board.SIZE):
                board.grid[r][c].cell_type = CellType.GIVEN

        cells_to_remove = difficulty.value
        positions = [(r, c) for r in range(9) for c in range(9)]
        random.shuffle(positions)

        removed = 0
        for r, c in positions:
            if removed >= cells_to_remove:
                break
            backup = board.grid[r][c].value
            board.grid[r][c].value = 0
            board.grid[r][c].cell_type = CellType.EMPTY

            test = board.clone()
            if self._solver.count_solutions(test) == 1:
                removed += 1
            else:
                board.grid[r][c].value = backup
                board.grid[r][c].cell_type = CellType.GIVEN

        return board

    def _fill_diagonal_boxes(self, board: Board) -> None:
        for box in range(0, Board.SIZE, Board.BOX_SIZE):
            nums = list(range(1, 10))
            random.shuffle(nums)
            idx = 0
            for r in range(box, box + Board.BOX_SIZE):
                for c in range(box, box + Board.BOX_SIZE):
                    board.grid[r][c].value = nums[idx]
                    idx += 1


class SudokuGame:
    def __init__(self, difficulty: Difficulty = Difficulty.MEDIUM):
        generator = PuzzleGenerator()
        self.board = generator.generate(difficulty)
        self._solution = self.board.clone()
        SudokuSolver().solve(self._solution)
        self.history = MoveHistory()
        self.difficulty = difficulty

    def place_number(self, row: int, col: int, num: int) -> bool:
        cell = self.board.get_cell(row, col)
        if not cell.is_modifiable:
            return False

        old_value = cell.value
        if cell.set_value(num):
            self.history.record(Move(row, col, old_value, num))
            return True
        return False

    def undo(self) -> bool:
        move = self.history.undo()
        if move:
            self.board.grid[move.row][move.col].value = move.old_value
            return True
        return False

    def redo(self) -> bool:
        move = self.history.redo()
        if move:
            self.board.grid[move.row][move.col].value = move.new_value
            return True
        return False

    def get_hint(self) -> Optional[tuple[int, int, int]]:
        empty_cells = [
            (r, c) for r in range(9) for c in range(9)
            if self.board.grid[r][c].is_empty
        ]
        if not empty_cells:
            return None
        row, col = random.choice(empty_cells)
        value = self._solution.grid[row][col].value
        return (row, col, value)

    def is_solved(self) -> bool:
        return self.board.is_complete()
```

### Key Implementation Logic

The solver uses **backtracking** with the **Minimum Remaining Values (MRV)** heuristic — it always picks the empty cell with the fewest valid candidates, drastically reducing the search space. The puzzle generator works backward: fill a complete valid board, then remove cells one at a time, checking that the puzzle retains a unique solution after each removal.

### Concurrency Handling

Sudoku is primarily single-player, so concurrency is minimal. For a multiplayer variant:
- Each player's move is validated atomically before applying to the shared board
- Move history per player avoids conflicts in undo/redo
- A read-write lock on the board allows concurrent reads (display) with exclusive writes (placing numbers)

### Interview Tips (Microsoft)

- **Start with `is_valid_placement`** — this is the core constraint and Microsoft will expect you to optimize it. Mention using bitsets or hash sets per row/column/box for O(1) validation.
- **Discuss the MRV heuristic** — it shows algorithmic sophistication beyond naive backtracking.
- **Draw the board data structure** clearly. Microsoft likes concrete data structure discussions.
- **Mention the uniqueness check** in puzzle generation — it's a subtle correctness requirement that separates good answers from great ones.
- **Be ready to discuss time complexity** of the solver: O(9^(n)) worst case where n is empty cells, but MRV and constraint propagation make it practical.

---

## 3. MS Excel (Microsoft)

### Requirements

- Support a 2D grid of cells, each holding a value or formula
- Parse formulas like `=A1+B2*C3` and `=SUM(A1:A10)`
- Build and maintain a dependency graph between cells
- Recalculate dependent cells automatically when a source cell changes
- Detect circular references and report errors
- Support cell references (A1 notation) and ranges (A1:B5)
- Handle data types: numbers, strings, booleans, errors
- Support copy-paste with relative reference adjustment

### Key Entities and Relationships

```
Spreadsheet ──contains──▶ Cell[row][col]
Cell ──has──▶ Formula | RawValue
Formula ──references──▶ Cell* (dependency edges)
DependencyGraph tracks Cell → dependents (forward edges)
FormulaParser tokenizes and evaluates expressions
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **Observer** | Cells observe their dependencies; recalculate on change |
| **Interpreter** | Formula parsing and evaluation via AST |
| **Graph / Topological Sort** | Dependency resolution and circular reference detection |
| **Composite** | Formula AST nodes (binary ops, functions, cell refs) |

### Core Class Structure

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Union
import re
from collections import deque


class CellError(Enum):
    CIRCULAR_REF = "#CIRC!"
    INVALID_REF = "#REF!"
    DIV_ZERO = "#DIV/0!"
    VALUE_ERROR = "#VALUE!"


CellValue = Union[int, float, str, bool, CellError, None]


@dataclass
class CellAddress:
    col: int  # 0-based
    row: int  # 0-based

    @classmethod
    def from_notation(cls, notation: str) -> "CellAddress":
        match = re.match(r"([A-Z]+)(\d+)", notation.upper())
        if not match:
            raise ValueError(f"Invalid cell reference: {notation}")
        col_str, row_str = match.groups()
        col = 0
        for ch in col_str:
            col = col * 26 + (ord(ch) - ord('A') + 1)
        return cls(col=col - 1, row=int(row_str) - 1)

    def to_notation(self) -> str:
        col, result = self.col, ""
        while col >= 0:
            result = chr(col % 26 + ord('A')) + result
            col = col // 26 - 1
        return f"{result}{self.row + 1}"

    def __hash__(self):
        return hash((self.row, self.col))

    def __eq__(self, other):
        return isinstance(other, CellAddress) and self.row == other.row and self.col == other.col


class ASTNode(ABC):
    @abstractmethod
    def evaluate(self, spreadsheet: "Spreadsheet") -> CellValue:
        pass

    @abstractmethod
    def get_references(self) -> list[CellAddress]:
        pass


class NumberNode(ASTNode):
    def __init__(self, value: float):
        self.value = value

    def evaluate(self, spreadsheet: "Spreadsheet") -> CellValue:
        return self.value

    def get_references(self) -> list[CellAddress]:
        return []


class CellRefNode(ASTNode):
    def __init__(self, address: CellAddress):
        self.address = address

    def evaluate(self, spreadsheet: "Spreadsheet") -> CellValue:
        cell = spreadsheet.get_cell(self.address)
        if cell is None:
            return 0
        return cell.evaluated_value

    def get_references(self) -> list[CellAddress]:
        return [self.address]


class BinaryOpNode(ASTNode):
    OPS = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: CellError.DIV_ZERO if b == 0 else a / b,
    }

    def __init__(self, op: str, left: ASTNode, right: ASTNode):
        self.op = op
        self.left = left
        self.right = right

    def evaluate(self, spreadsheet: "Spreadsheet") -> CellValue:
        left_val = self.left.evaluate(spreadsheet)
        right_val = self.right.evaluate(spreadsheet)

        if isinstance(left_val, CellError):
            return left_val
        if isinstance(right_val, CellError):
            return right_val

        try:
            return self.OPS[self.op](float(left_val), float(right_val))
        except (TypeError, ValueError):
            return CellError.VALUE_ERROR

    def get_references(self) -> list[CellAddress]:
        return self.left.get_references() + self.right.get_references()


class RangeNode(ASTNode):
    def __init__(self, start: CellAddress, end: CellAddress):
        self.start = start
        self.end = end

    def evaluate(self, spreadsheet: "Spreadsheet") -> list[CellValue]:
        values = []
        for r in range(self.start.row, self.end.row + 1):
            for c in range(self.start.col, self.end.col + 1):
                cell = spreadsheet.get_cell(CellAddress(col=c, row=r))
                values.append(cell.evaluated_value if cell else 0)
        return values

    def get_references(self) -> list[CellAddress]:
        refs = []
        for r in range(self.start.row, self.end.row + 1):
            for c in range(self.start.col, self.end.col + 1):
                refs.append(CellAddress(col=c, row=r))
        return refs


class FunctionNode(ASTNode):
    def __init__(self, name: str, args: list[ASTNode]):
        self.name = name.upper()
        self.args = args

    def evaluate(self, spreadsheet: "Spreadsheet") -> CellValue:
        values = []
        for arg in self.args:
            result = arg.evaluate(spreadsheet)
            if isinstance(result, list):
                values.extend(result)
            else:
                values.append(result)

        numeric = []
        for v in values:
            if isinstance(v, CellError):
                return v
            try:
                numeric.append(float(v) if v is not None else 0.0)
            except (TypeError, ValueError):
                return CellError.VALUE_ERROR

        if self.name == "SUM":
            return sum(numeric)
        elif self.name == "AVG" or self.name == "AVERAGE":
            return sum(numeric) / len(numeric) if numeric else 0
        elif self.name == "MIN":
            return min(numeric) if numeric else 0
        elif self.name == "MAX":
            return max(numeric) if numeric else 0
        elif self.name == "COUNT":
            return len(numeric)
        return CellError.VALUE_ERROR

    def get_references(self) -> list[CellAddress]:
        refs = []
        for arg in self.args:
            refs.extend(arg.get_references())
        return refs


class FormulaParser:
    """Recursive descent parser for spreadsheet formulas."""

    def __init__(self, formula: str):
        self.formula = formula.lstrip("=")
        self.pos = 0

    def parse(self) -> ASTNode:
        node = self._parse_expression()
        return node

    def _parse_expression(self) -> ASTNode:
        left = self._parse_term()
        while self.pos < len(self.formula) and self.formula[self.pos] in ('+', '-'):
            op = self.formula[self.pos]
            self.pos += 1
            right = self._parse_term()
            left = BinaryOpNode(op, left, right)
        return left

    def _parse_term(self) -> ASTNode:
        left = self._parse_factor()
        while self.pos < len(self.formula) and self.formula[self.pos] in ('*', '/'):
            op = self.formula[self.pos]
            self.pos += 1
            right = self._parse_factor()
            left = BinaryOpNode(op, left, right)
        return left

    def _parse_factor(self) -> ASTNode:
        self._skip_whitespace()

        if self.pos < len(self.formula) and self.formula[self.pos] == '(':
            self.pos += 1
            node = self._parse_expression()
            if self.pos < len(self.formula) and self.formula[self.pos] == ')':
                self.pos += 1
            return node

        func_match = re.match(r"([A-Z]+)\(", self.formula[self.pos:], re.IGNORECASE)
        if func_match:
            name = func_match.group(1)
            self.pos += len(func_match.group(0))
            args = self._parse_func_args()
            if self.pos < len(self.formula) and self.formula[self.pos] == ')':
                self.pos += 1
            return FunctionNode(name, args)

        ref_match = re.match(r"([A-Z]+\d+):([A-Z]+\d+)", self.formula[self.pos:], re.IGNORECASE)
        if ref_match:
            self.pos += len(ref_match.group(0))
            return RangeNode(
                CellAddress.from_notation(ref_match.group(1)),
                CellAddress.from_notation(ref_match.group(2)),
            )

        ref_match = re.match(r"[A-Z]+\d+", self.formula[self.pos:], re.IGNORECASE)
        if ref_match:
            self.pos += len(ref_match.group(0))
            return CellRefNode(CellAddress.from_notation(ref_match.group(0)))

        num_match = re.match(r"\d+\.?\d*", self.formula[self.pos:])
        if num_match:
            self.pos += len(num_match.group(0))
            return NumberNode(float(num_match.group(0)))

        return NumberNode(0)

    def _parse_func_args(self) -> list[ASTNode]:
        args = [self._parse_expression()]
        while self.pos < len(self.formula) and self.formula[self.pos] == ',':
            self.pos += 1
            args.append(self._parse_expression())
        return args

    def _skip_whitespace(self):
        while self.pos < len(self.formula) and self.formula[self.pos] == ' ':
            self.pos += 1


class Cell:
    def __init__(self, address: CellAddress):
        self.address = address
        self.raw_value: str = ""
        self.formula: ASTNode | None = None
        self.evaluated_value: CellValue = None
        self.dependencies: set[CellAddress] = set()

    def set_content(self, content: str, spreadsheet: "Spreadsheet") -> None:
        self.raw_value = content
        old_deps = self.dependencies.copy()

        if content.startswith("="):
            parser = FormulaParser(content)
            self.formula = parser.parse()
            self.dependencies = set(self.formula.get_references())
        else:
            self.formula = None
            self.dependencies = set()
            try:
                self.evaluated_value = float(content) if '.' in content else int(content)
            except ValueError:
                self.evaluated_value = content

        spreadsheet.update_dependency_graph(self.address, old_deps, self.dependencies)

    def recalculate(self, spreadsheet: "Spreadsheet") -> None:
        if self.formula:
            self.evaluated_value = self.formula.evaluate(spreadsheet)


class DependencyGraph:
    def __init__(self):
        self._dependents: dict[CellAddress, set[CellAddress]] = {}

    def add_edge(self, source: CellAddress, dependent: CellAddress) -> None:
        if source not in self._dependents:
            self._dependents[source] = set()
        self._dependents[source].add(dependent)

    def remove_edge(self, source: CellAddress, dependent: CellAddress) -> None:
        if source in self._dependents:
            self._dependents[source].discard(dependent)

    def get_dependents(self, address: CellAddress) -> set[CellAddress]:
        return self._dependents.get(address, set())

    def has_cycle(self, start: CellAddress) -> bool:
        visited, rec_stack = set(), set()

        def dfs(node: CellAddress) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for dep in self.get_dependents(node):
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    return True
            rec_stack.discard(node)
            return False

        return dfs(start)

    def topological_order(self, start: CellAddress) -> list[CellAddress]:
        visited = set()
        order = []

        queue = deque([start])
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            order.append(node)
            for dep in self.get_dependents(node):
                if dep not in visited:
                    queue.append(dep)

        return order[1:]  # exclude the start cell itself


class Spreadsheet:
    def __init__(self, rows: int = 1000, cols: int = 26):
        self.rows = rows
        self.cols = cols
        self._cells: dict[CellAddress, Cell] = {}
        self._dep_graph = DependencyGraph()

    def get_cell(self, address: CellAddress) -> Cell | None:
        return self._cells.get(address)

    def set_cell(self, notation: str, content: str) -> CellValue:
        address = CellAddress.from_notation(notation)

        if address not in self._cells:
            self._cells[address] = Cell(address)

        cell = self._cells[address]
        cell.set_content(content, self)

        if cell.formula and self._dep_graph.has_cycle(address):
            cell.evaluated_value = CellError.CIRCULAR_REF
            return CellError.CIRCULAR_REF

        cell.recalculate(self)
        self._propagate_recalculation(address)
        return cell.evaluated_value

    def update_dependency_graph(self, address: CellAddress,
                                 old_deps: set[CellAddress],
                                 new_deps: set[CellAddress]) -> None:
        for dep in old_deps - new_deps:
            self._dep_graph.remove_edge(dep, address)
        for dep in new_deps - old_deps:
            self._dep_graph.add_edge(dep, address)

    def _propagate_recalculation(self, changed: CellAddress) -> None:
        to_recalc = self._dep_graph.topological_order(changed)
        for addr in to_recalc:
            cell = self._cells.get(addr)
            if cell:
                cell.recalculate(self)
```

### Key Implementation Logic

The formula parser uses **recursive descent** to build an AST. When a cell changes, the dependency graph identifies all transitively dependent cells via BFS, then recalculates them in topological order. Circular references are detected by checking for cycles in the dependency graph before applying the formula.

### Concurrency Handling

- Cell evaluation is single-threaded in the basic model (like real Excel)
- For a concurrent version, use a **read-write lock** on the spreadsheet: multiple readers can evaluate cells simultaneously, but writes (cell updates) are exclusive
- Recalculation can be parallelized by processing independent branches of the dependency graph concurrently
- Use a **versioned snapshot** approach for consistent reads during recalculation

### Interview Tips (Microsoft)

- **This is a Microsoft classic** — they literally built Excel. Show deep understanding of the dependency graph.
- **Draw the graph first**: cells are nodes, formula references are edges. Explain topological sort clearly.
- **Discuss circular reference detection** early — it shows you think about edge cases.
- **Optimize the parser**: mention operator precedence, parentheses, and how you'd extend to support more functions.
- **Talk about incremental recalculation** — only recalculate affected cells, not the entire sheet. This is the key performance optimization interviewers expect.
- **Be prepared to discuss how `INDIRECT()` or volatile functions break static dependency analysis.**

---

## 4. Design malloc() API (Microsoft)

### Requirements

- Implement `malloc(size)` that allocates a contiguous block of `size` bytes
- Implement `free(ptr)` that releases a previously allocated block
- Manage a fixed-size memory pool (e.g., 1 MB)
- Support multiple allocation strategies: first-fit, best-fit, worst-fit
- Coalesce adjacent free blocks to reduce fragmentation
- Track allocation metadata (block size, allocation status)
- Handle edge cases: zero-size allocation, double-free, invalid pointer
- Minimize fragmentation and maximize memory utilization

### Key Entities and Relationships

```
MemoryAllocator ──manages──▶ MemoryPool (byte array)
MemoryPool ──divided into──▶ Block* (linked list)
Block ──status──▶ {FREE, ALLOCATED}
AllocationStrategy defines how to pick a free block
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **Strategy** | Pluggable allocation strategies (first-fit, best-fit, worst-fit) |
| **Flyweight** | Block headers share common structure, only metadata differs |
| **Template Method** | Base allocator with strategy-specific `find_block` |

### Core Class Structure

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import threading


@dataclass
class Block:
    start: int
    size: int
    is_free: bool = True
    next_block: Optional["Block"] = None
    prev_block: Optional["Block"] = None

    @property
    def end(self) -> int:
        return self.start + self.size

    def split(self, requested_size: int) -> Optional["Block"]:
        """Split block if remaining space can hold at least a minimum block."""
        min_block_size = 16
        remaining = self.size - requested_size
        if remaining >= min_block_size:
            new_block = Block(
                start=self.start + requested_size,
                size=remaining,
                is_free=True,
                next_block=self.next_block,
                prev_block=self,
            )
            if self.next_block:
                self.next_block.prev_block = new_block
            self.next_block = new_block
            self.size = requested_size
            return new_block
        return None

    def can_fit(self, size: int) -> bool:
        return self.is_free and self.size >= size


class AllocationStrategy(ABC):
    @abstractmethod
    def find_block(self, head: Block, size: int) -> Optional[Block]:
        pass


class FirstFit(AllocationStrategy):
    def find_block(self, head: Block, size: int) -> Optional[Block]:
        current = head
        while current:
            if current.can_fit(size):
                return current
            current = current.next_block
        return None


class BestFit(AllocationStrategy):
    def find_block(self, head: Block, size: int) -> Optional[Block]:
        best: Optional[Block] = None
        current = head
        while current:
            if current.can_fit(size):
                if best is None or current.size < best.size:
                    best = current
                    if current.size == size:
                        return best
            current = current.next_block
        return best


class WorstFit(AllocationStrategy):
    def find_block(self, head: Block, size: int) -> Optional[Block]:
        worst: Optional[Block] = None
        current = head
        while current:
            if current.can_fit(size):
                if worst is None or current.size > worst.size:
                    worst = current
            current = current.next_block
        return worst


class MemoryAllocator:
    ALIGNMENT = 8  # 8-byte alignment

    def __init__(self, pool_size: int = 1024 * 1024,
                 strategy: AllocationStrategy = None):
        self.pool_size = pool_size
        self._memory = bytearray(pool_size)
        self._head = Block(start=0, size=pool_size)
        self._strategy = strategy or FirstFit()
        self._allocations: dict[int, Block] = {}
        self._lock = threading.Lock()

        self._stats_allocated = 0
        self._stats_free = pool_size
        self._stats_num_allocs = 0

    def _align(self, size: int) -> int:
        return (size + self.ALIGNMENT - 1) & ~(self.ALIGNMENT - 1)

    def malloc(self, size: int) -> Optional[int]:
        if size <= 0:
            return None

        aligned_size = self._align(size)

        with self._lock:
            block = self._strategy.find_block(self._head, aligned_size)
            if block is None:
                return None

            block.split(aligned_size)
            block.is_free = False
            self._allocations[block.start] = block

            self._stats_allocated += block.size
            self._stats_free -= block.size
            self._stats_num_allocs += 1

            return block.start

    def free(self, ptr: int) -> bool:
        if ptr is None:
            return False

        with self._lock:
            block = self._allocations.pop(ptr, None)
            if block is None:
                return False

            block.is_free = True
            self._stats_allocated -= block.size
            self._stats_free += block.size
            self._stats_num_allocs -= 1

            self._coalesce(block)
            return True

    def _coalesce(self, block: Block) -> None:
        if block.next_block and block.next_block.is_free:
            next_b = block.next_block
            block.size += next_b.size
            block.next_block = next_b.next_block
            if next_b.next_block:
                next_b.next_block.prev_block = block
            self._allocations.pop(next_b.start, None)

        if block.prev_block and block.prev_block.is_free:
            prev_b = block.prev_block
            prev_b.size += block.size
            prev_b.next_block = block.next_block
            if block.next_block:
                block.next_block.prev_block = prev_b
            self._allocations.pop(block.start, None)

    def realloc(self, ptr: int, new_size: int) -> Optional[int]:
        if ptr is None:
            return self.malloc(new_size)
        if new_size <= 0:
            self.free(ptr)
            return None

        with self._lock:
            block = self._allocations.get(ptr)
            if block is None:
                return None
            if block.size >= self._align(new_size):
                return ptr

        new_ptr = self.malloc(new_size)
        if new_ptr is None:
            return None
        copy_size = min(block.size, new_size)
        self._memory[new_ptr:new_ptr + copy_size] = self._memory[ptr:ptr + copy_size]
        self.free(ptr)
        return new_ptr

    def get_stats(self) -> dict:
        return {
            "total": self.pool_size,
            "allocated": self._stats_allocated,
            "free": self._stats_free,
            "num_allocations": self._stats_num_allocs,
            "fragmentation": self._calculate_fragmentation(),
        }

    def _calculate_fragmentation(self) -> float:
        if self._stats_free == 0:
            return 0.0
        largest_free = 0
        current = self._head
        while current:
            if current.is_free and current.size > largest_free:
                largest_free = current.size
            current = current.next_block
        return 1.0 - (largest_free / self._stats_free) if self._stats_free > 0 else 0.0

    def dump_blocks(self) -> list[dict]:
        blocks = []
        current = self._head
        while current:
            blocks.append({
                "start": current.start,
                "size": current.size,
                "free": current.is_free,
            })
            current = current.next_block
        return blocks
```

### Key Implementation Logic

The allocator manages a doubly-linked list of blocks over a contiguous memory pool. On `malloc`, the chosen strategy scans for a suitable free block. If the block is larger than needed, `split()` creates a new free block from the remainder. On `free`, `coalesce()` merges the freed block with adjacent free neighbors, reducing external fragmentation. All sizes are aligned to 8-byte boundaries.

### Concurrency Handling

- A single `threading.Lock` serializes all `malloc`/`free` operations
- For higher concurrency, consider **arena-based allocation** with per-thread arenas, each with its own lock
- `realloc` needs careful lock management — it performs malloc + copy + free, so it must avoid holding the lock across the copy operation for large blocks

### Interview Tips (Microsoft)

- **This is a systems design question** — Microsoft loves it because it tests low-level thinking. Start by drawing the memory layout.
- **Compare strategies**: First-fit is fast (O(n) but typically finds blocks early), best-fit minimizes waste but causes more fragmentation of small blocks, worst-fit leaves larger remainders.
- **Coalescing is critical** — forgetting it is an immediate red flag. Explain why adjacent free blocks must be merged.
- **Discuss alignment** — modern systems require aligned memory access. Show you understand why.
- **Mention the metadata overhead** — each block header consumes space. In real allocators, this is typically 16–32 bytes.
- **Extensions to discuss**: thread-local caches (like tcmalloc), size classes (like jemalloc), buddy system allocation.

---

## 5. Design strtok() API (Microsoft)

### Requirements

- Implement `strtok(string, delimiters)` that splits a string into tokens
- First call provides the string; subsequent calls with `None` continue tokenizing
- Support multiple delimiter characters
- Handle consecutive delimiters (skip empty tokens)
- Maintain internal state between calls
- Provide a thread-safe reentrant version (`strtok_r`)
- Support custom tokenization rules (quoted strings, escape characters)
- Handle edge cases: empty string, empty delimiters, all-delimiter string

### Key Entities and Relationships

```
Tokenizer ──processes──▶ input string
Tokenizer ──uses──▶ DelimiterSet
TokenizerState holds position between calls
TokenRule defines custom parsing (quotes, escapes)
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **Iterator** | Tokenizer implements the iterator protocol |
| **State** | Internal parsing state (NORMAL, IN_QUOTES, ESCAPED) |
| **Strategy** | Pluggable delimiter/tokenization strategies |
| **Memento** | Save/restore tokenizer state for backtracking |

### Core Class Structure

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Iterator
import threading


class TokenState(Enum):
    NORMAL = auto()
    IN_SINGLE_QUOTE = auto()
    IN_DOUBLE_QUOTE = auto()
    ESCAPED = auto()


@dataclass
class TokenizerConfig:
    skip_empty: bool = True
    respect_quotes: bool = False
    escape_char: str = '\\'
    strip_quotes: bool = True
    max_token_length: int = 0  # 0 = unlimited


class SimpleStrtok:
    """Mimics C strtok() behavior with internal state."""

    _state_lock = threading.Lock()
    _string: Optional[str] = None
    _position: int = 0

    @classmethod
    def strtok(cls, string: Optional[str], delimiters: str) -> Optional[str]:
        with cls._state_lock:
            if string is not None:
                cls._string = string
                cls._position = 0

            if cls._string is None or cls._position >= len(cls._string):
                return None

            while cls._position < len(cls._string) and cls._string[cls._position] in delimiters:
                cls._position += 1

            if cls._position >= len(cls._string):
                return None

            start = cls._position
            while cls._position < len(cls._string) and cls._string[cls._position] not in delimiters:
                cls._position += 1

            token = cls._string[start:cls._position]
            cls._position += 1
            return token


class ReentrantTokenizer:
    """Thread-safe version equivalent to strtok_r."""

    def __init__(self, string: str, delimiters: str,
                 config: TokenizerConfig = None):
        self._string = string
        self._delimiters = set(delimiters)
        self._position = 0
        self._config = config or TokenizerConfig()
        self._state = TokenState.NORMAL

    def next_token(self) -> Optional[str]:
        if self._position >= len(self._string):
            return None

        if self._config.skip_empty:
            while (self._position < len(self._string)
                   and self._string[self._position] in self._delimiters
                   and self._state == TokenState.NORMAL):
                self._position += 1

        if self._position >= len(self._string):
            return None

        return self._extract_token()

    def _extract_token(self) -> str:
        token_chars: list[str] = []
        self._state = TokenState.NORMAL

        while self._position < len(self._string):
            char = self._string[self._position]

            if self._state == TokenState.ESCAPED:
                token_chars.append(char)
                self._state = TokenState.NORMAL
                self._position += 1
                continue

            if self._config.respect_quotes:
                if char == self._config.escape_char and self._state != TokenState.NORMAL:
                    self._state = TokenState.ESCAPED
                    self._position += 1
                    continue

                if char == '"' and self._state == TokenState.NORMAL:
                    self._state = TokenState.IN_DOUBLE_QUOTE
                    if not self._config.strip_quotes:
                        token_chars.append(char)
                    self._position += 1
                    continue

                if char == '"' and self._state == TokenState.IN_DOUBLE_QUOTE:
                    self._state = TokenState.NORMAL
                    if not self._config.strip_quotes:
                        token_chars.append(char)
                    self._position += 1
                    continue

                if char == "'" and self._state == TokenState.NORMAL:
                    self._state = TokenState.IN_SINGLE_QUOTE
                    if not self._config.strip_quotes:
                        token_chars.append(char)
                    self._position += 1
                    continue

                if char == "'" and self._state == TokenState.IN_SINGLE_QUOTE:
                    self._state = TokenState.NORMAL
                    if not self._config.strip_quotes:
                        token_chars.append(char)
                    self._position += 1
                    continue

            if char in self._delimiters and self._state == TokenState.NORMAL:
                self._position += 1
                break

            token_chars.append(char)
            self._position += 1

        token = "".join(token_chars)
        if self._config.max_token_length > 0:
            token = token[:self._config.max_token_length]
        return token

    def tokenize_all(self) -> list[str]:
        tokens = []
        while True:
            token = self.next_token()
            if token is None:
                break
            tokens.append(token)
        return tokens

    def __iter__(self) -> Iterator[str]:
        return self

    def __next__(self) -> str:
        token = self.next_token()
        if token is None:
            raise StopIteration
        return token

    def save_state(self) -> dict:
        return {
            "position": self._position,
            "state": self._state,
        }

    def restore_state(self, state: dict) -> None:
        self._position = state["position"]
        self._state = state["state"]


class DelimiterStrategy(ABC):
    @abstractmethod
    def is_delimiter(self, char: str, context: str, position: int) -> bool:
        pass


class CharDelimiters(DelimiterStrategy):
    def __init__(self, delimiters: str):
        self._delims = set(delimiters)

    def is_delimiter(self, char: str, context: str, position: int) -> bool:
        return char in self._delims


class RegexDelimiters(DelimiterStrategy):
    def __init__(self, pattern: str):
        import re
        self._pattern = re.compile(pattern)

    def is_delimiter(self, char: str, context: str, position: int) -> bool:
        return bool(self._pattern.match(context[position:]))


class WhitespaceDelimiters(DelimiterStrategy):
    def is_delimiter(self, char: str, context: str, position: int) -> bool:
        return char.isspace()


class AdvancedTokenizer:
    """Tokenizer with pluggable delimiter strategies."""

    def __init__(self, string: str, strategy: DelimiterStrategy,
                 config: TokenizerConfig = None):
        self._string = string
        self._strategy = strategy
        self._position = 0
        self._config = config or TokenizerConfig()

    def next_token(self) -> Optional[str]:
        if self._config.skip_empty:
            while (self._position < len(self._string)
                   and self._strategy.is_delimiter(
                       self._string[self._position],
                       self._string,
                       self._position)):
                self._position += 1

        if self._position >= len(self._string):
            return None

        start = self._position
        while (self._position < len(self._string)
               and not self._strategy.is_delimiter(
                   self._string[self._position],
                   self._string,
                   self._position)):
            self._position += 1

        return self._string[start:self._position]

    def __iter__(self) -> Iterator[str]:
        return self

    def __next__(self) -> str:
        token = self.next_token()
        if token is None:
            raise StopIteration
        return token


class ThreadSafeTokenizerPool:
    """Per-thread tokenizer instances, avoiding shared mutable state."""

    def __init__(self):
        self._local = threading.local()

    def tokenize(self, string: Optional[str], delimiters: str) -> Optional[str]:
        if string is not None:
            self._local.tokenizer = ReentrantTokenizer(string, delimiters)

        tokenizer = getattr(self._local, 'tokenizer', None)
        if tokenizer is None:
            return None
        return tokenizer.next_token()
```

### Key Implementation Logic

The `SimpleStrtok` mimics C's `strtok()` using class-level state — deliberately showcasing the thread-safety problem. The `ReentrantTokenizer` fixes this by keeping all state per-instance. The state machine handles quoted strings: when a quote is encountered, the parser enters a quoted state where delimiters are treated as regular characters until the matching closing quote.

### Concurrency Handling

- `SimpleStrtok` uses a class-level lock to demonstrate the fundamental flaw of shared mutable state — it serializes all tokenization globally
- `ReentrantTokenizer` is thread-safe by design — each instance has its own state, so no locks are needed
- `ThreadSafeTokenizerPool` uses `threading.local()` for per-thread state, combining the convenience of a shared API with the safety of independent instances

### Interview Tips (Microsoft)

- **This question tests API design skills** — Microsoft cares deeply about API contracts and backward compatibility.
- **Start by criticizing C's `strtok()`**: it uses global state, is not reentrant, modifies the input string, and can't tokenize two strings simultaneously. This shows you understand the problem.
- **Implement the simple version first**, then evolve to reentrant. This shows iterative design thinking.
- **Discuss the Iterator protocol** — making the tokenizer iterable is Pythonic and shows language mastery.
- **Mention `str.split()` and why it's different** — `split()` doesn't support stateful iteration or quoted strings.
- **Edge cases to cover**: empty string → `None`, empty delimiters → return whole string, only delimiters → `None`, consecutive delimiters → skip or return empty tokens.

---

# Amazon Series

---

## 6. BookMyShow (Amazon)

### Requirements

- Users can browse movies, theaters, and showtimes
- Users can view seat maps and select specific seats
- Booking must handle concurrent seat selection (prevent double-booking)
- Support temporary seat holds with expiration (e.g., 10 minutes)
- Process payments through multiple payment gateways
- Generate booking confirmations with unique booking IDs
- Support booking cancellation with refund policies
- Admins can manage theaters, screens, and show schedules

### Key Entities and Relationships

```
Movie ──screenedAt──▶ Show ──in──▶ Screen ──partOf──▶ Theater
Show ──has──▶ ShowSeat* ──status──▶ {AVAILABLE, HELD, BOOKED}
User ──makes──▶ Booking ──contains──▶ ShowSeat*
Booking ──processedBy──▶ Payment
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **Strategy** | Multiple payment gateways |
| **State** | Seat transitions: Available → Held → Booked (or Released) |
| **Observer** | Notify users when held seats are released |
| **Factory** | Create different seat types (Regular, Premium, VIP) |

### Core Class Structure

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import threading
import uuid
import time


class SeatType(Enum):
    REGULAR = "regular"
    PREMIUM = "premium"
    VIP = "vip"


class SeatStatus(Enum):
    AVAILABLE = "available"
    HELD = "held"
    BOOKED = "booked"


class BookingStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class PaymentStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class Movie:
    movie_id: str
    title: str
    genre: str
    duration_minutes: int
    rating: float = 0.0


@dataclass
class Theater:
    theater_id: str
    name: str
    city: str
    screens: list["Screen"] = field(default_factory=list)


@dataclass
class Screen:
    screen_id: str
    name: str
    total_seats: int
    seat_layout: dict[str, SeatType] = field(default_factory=dict)


@dataclass
class Show:
    show_id: str
    movie: Movie
    screen: Screen
    theater: Theater
    start_time: datetime
    end_time: datetime
    price_map: dict[SeatType, float] = field(default_factory=dict)


class ShowSeat:
    HOLD_TIMEOUT = timedelta(minutes=10)

    def __init__(self, seat_id: str, show: Show, seat_type: SeatType):
        self.seat_id = seat_id
        self.show = show
        self.seat_type = seat_type
        self.status = SeatStatus.AVAILABLE
        self.held_by: Optional[str] = None
        self.held_at: Optional[datetime] = None
        self.booked_by: Optional[str] = None
        self._lock = threading.Lock()

    @property
    def price(self) -> float:
        return self.show.price_map.get(self.seat_type, 0.0)

    def hold(self, user_id: str) -> bool:
        with self._lock:
            self._release_if_expired()
            if self.status != SeatStatus.AVAILABLE:
                return False
            self.status = SeatStatus.HELD
            self.held_by = user_id
            self.held_at = datetime.now()
            return True

    def confirm(self, user_id: str) -> bool:
        with self._lock:
            if self.status != SeatStatus.HELD or self.held_by != user_id:
                return False
            if self._is_hold_expired():
                self._release()
                return False
            self.status = SeatStatus.BOOKED
            self.booked_by = user_id
            return True

    def release(self) -> bool:
        with self._lock:
            return self._release()

    def _release(self) -> bool:
        if self.status in (SeatStatus.HELD, SeatStatus.BOOKED):
            self.status = SeatStatus.AVAILABLE
            self.held_by = None
            self.held_at = None
            self.booked_by = None
            return True
        return False

    def _is_hold_expired(self) -> bool:
        if self.held_at is None:
            return True
        return datetime.now() - self.held_at > self.HOLD_TIMEOUT

    def _release_if_expired(self) -> None:
        if self.status == SeatStatus.HELD and self._is_hold_expired():
            self._release()


class PaymentGateway(ABC):
    @abstractmethod
    def process_payment(self, amount: float, booking_id: str) -> PaymentStatus:
        pass

    @abstractmethod
    def process_refund(self, amount: float, booking_id: str) -> PaymentStatus:
        pass


class CreditCardGateway(PaymentGateway):
    def process_payment(self, amount: float, booking_id: str) -> PaymentStatus:
        print(f"[CreditCard] Processing ${amount} for booking {booking_id}")
        return PaymentStatus.SUCCESS

    def process_refund(self, amount: float, booking_id: str) -> PaymentStatus:
        print(f"[CreditCard] Refunding ${amount} for booking {booking_id}")
        return PaymentStatus.REFUNDED


class UPIGateway(PaymentGateway):
    def process_payment(self, amount: float, booking_id: str) -> PaymentStatus:
        print(f"[UPI] Processing ₹{amount} for booking {booking_id}")
        return PaymentStatus.SUCCESS

    def process_refund(self, amount: float, booking_id: str) -> PaymentStatus:
        print(f"[UPI] Refunding ₹{amount} for booking {booking_id}")
        return PaymentStatus.REFUNDED


@dataclass
class Booking:
    booking_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    user_id: str = ""
    show: Show = None
    seats: list[ShowSeat] = field(default_factory=list)
    total_amount: float = 0.0
    status: BookingStatus = BookingStatus.PENDING
    payment_status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)


class BookingService:
    def __init__(self):
        self._shows: dict[str, Show] = {}
        self._show_seats: dict[str, list[ShowSeat]] = {}
        self._bookings: dict[str, Booking] = {}
        self._payment_gateways: dict[str, PaymentGateway] = {
            "credit_card": CreditCardGateway(),
            "upi": UPIGateway(),
        }
        self._lock = threading.Lock()

    def add_show(self, show: Show) -> None:
        self._shows[show.show_id] = show
        seats = []
        for seat_id, seat_type in show.screen.seat_layout.items():
            seats.append(ShowSeat(seat_id, show, seat_type))
        self._show_seats[show.show_id] = seats

    def get_available_seats(self, show_id: str) -> list[ShowSeat]:
        seats = self._show_seats.get(show_id, [])
        return [s for s in seats if s.status == SeatStatus.AVAILABLE]

    def hold_seats(self, user_id: str, show_id: str,
                   seat_ids: list[str]) -> Optional[Booking]:
        seats = self._show_seats.get(show_id, [])
        target_seats = [s for s in seats if s.seat_id in seat_ids]

        if len(target_seats) != len(seat_ids):
            return None

        held_seats = []
        for seat in target_seats:
            if seat.hold(user_id):
                held_seats.append(seat)
            else:
                for s in held_seats:
                    s.release()
                return None

        total = sum(s.price for s in held_seats)
        booking = Booking(
            user_id=user_id,
            show=self._shows[show_id],
            seats=held_seats,
            total_amount=total,
        )
        self._bookings[booking.booking_id] = booking
        return booking

    def confirm_booking(self, booking_id: str,
                        payment_method: str) -> bool:
        booking = self._bookings.get(booking_id)
        if not booking or booking.status != BookingStatus.PENDING:
            return False

        gateway = self._payment_gateways.get(payment_method)
        if not gateway:
            return False

        payment_status = gateway.process_payment(
            booking.total_amount, booking_id
        )

        if payment_status == PaymentStatus.SUCCESS:
            all_confirmed = all(
                seat.confirm(booking.user_id) for seat in booking.seats
            )
            if all_confirmed:
                booking.status = BookingStatus.CONFIRMED
                booking.payment_status = PaymentStatus.SUCCESS
                return True
            else:
                gateway.process_refund(booking.total_amount, booking_id)
                for seat in booking.seats:
                    seat.release()
                booking.status = BookingStatus.CANCELLED
                return False

        booking.payment_status = payment_status
        for seat in booking.seats:
            seat.release()
        return False

    def cancel_booking(self, booking_id: str) -> bool:
        booking = self._bookings.get(booking_id)
        if not booking or booking.status != BookingStatus.CONFIRMED:
            return False

        gateway = None
        for gw in self._payment_gateways.values():
            gateway = gw
            break

        if gateway:
            gateway.process_refund(booking.total_amount, booking_id)

        for seat in booking.seats:
            seat.release()

        booking.status = BookingStatus.CANCELLED
        booking.payment_status = PaymentStatus.REFUNDED
        return True
```

### Key Implementation Logic

The critical flow is the **two-phase booking**: first, seats are *held* (reserving them temporarily), then after payment, they are *confirmed*. If payment fails or the hold expires, seats are released. Per-seat locks ensure atomic state transitions, while the `hold_seats` method implements all-or-nothing semantics — if any seat can't be held, all previously held seats in the same request are rolled back.

### Concurrency Handling

- **Per-seat locks** prevent two users from holding the same seat simultaneously
- **Temporal holds with expiry** prevent seats from being locked indefinitely if a user abandons checkout
- **All-or-nothing** seat holding — partial holds are rolled back to avoid orphaned reservations
- **Payment + confirmation** is a critical section — if payment succeeds but seat confirmation fails (expired hold), the payment is refunded automatically

### Interview Tips (Amazon)

- **Lead with concurrency** — Amazon interviewers will immediately ask "What happens if two users try to book the same seat?" Have the two-phase hold-confirm answer ready.
- **Discuss the hold timeout** — how long? What background process cleans up expired holds? Amazon loves operational thinking.
- **Show the payment failure path** — Amazon values resilience. What happens if payment fails midway? Show rollback logic.
- **Mention scalability**: how would you shard shows across servers? By city? By theater? Amazon thinks at scale.
- **Discuss idempotency** — what if the user double-clicks the "Book" button? Use idempotency keys.

---

## 7. Job Scheduler (Amazon)

### Requirements

- Submit jobs with priority, scheduled time, and optional dependencies
- Support recurring jobs with cron-like schedules
- Worker pool executes jobs concurrently with configurable pool size
- Jobs with dependencies execute only after all dependencies complete
- Failed jobs can be retried with configurable retry policy (count, backoff)
- Support job cancellation and status tracking
- Provide job execution history and logging
- Handle worker failures gracefully (reassign jobs)

### Key Entities and Relationships

```
JobScheduler ──manages──▶ JobQueue (priority-based)
JobScheduler ──dispatches to──▶ WorkerPool ──contains──▶ Worker*
Job ──depends on──▶ Job* (DAG)
Job ──has──▶ RetryPolicy
Job ──status──▶ {PENDING, SCHEDULED, RUNNING, COMPLETED, FAILED, CANCELLED}
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **Command** | Jobs encapsulate work as command objects |
| **Observer** | Notify scheduler when job completes (to unblock dependents) |
| **Strategy** | Pluggable retry strategies (fixed, exponential backoff) |
| **Producer-Consumer** | Workers consume jobs from a shared priority queue |

### Core Class Structure

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional
import threading
import heapq
import time
import uuid
import traceback


class JobStatus(Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RetryStrategy(ABC):
    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        pass


class FixedRetry(RetryStrategy):
    def __init__(self, delay_seconds: float = 5.0):
        self._delay = delay_seconds

    def get_delay(self, attempt: int) -> float:
        return self._delay


class ExponentialBackoff(RetryStrategy):
    def __init__(self, base_seconds: float = 1.0, max_seconds: float = 60.0):
        self._base = base_seconds
        self._max = max_seconds

    def get_delay(self, attempt: int) -> float:
        return min(self._base * (2 ** attempt), self._max)


@dataclass
class RetryPolicy:
    max_retries: int = 3
    strategy: RetryStrategy = field(default_factory=ExponentialBackoff)


@dataclass
class JobResult:
    success: bool
    output: str = ""
    error: str = ""
    duration_ms: float = 0


class Job:
    def __init__(self, job_id: str = None, name: str = "",
                 task: Callable[[], str] = None, priority: int = 0,
                 scheduled_time: datetime = None,
                 dependencies: list[str] = None,
                 retry_policy: RetryPolicy = None,
                 cron_expression: str = None):
        self.job_id = job_id or str(uuid.uuid4())[:8]
        self.name = name
        self.task = task
        self.priority = priority
        self.scheduled_time = scheduled_time or datetime.now()
        self.dependencies = dependencies or []
        self.retry_policy = retry_policy or RetryPolicy()
        self.cron_expression = cron_expression

        self.status = JobStatus.PENDING
        self.attempt = 0
        self.result: Optional[JobResult] = None
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def __lt__(self, other: "Job"):
        if self.priority != other.priority:
            return self.priority > other.priority  # higher priority first
        return self.scheduled_time < other.scheduled_time


class Worker:
    def __init__(self, worker_id: int, job_queue: "JobQueue",
                 scheduler: "JobScheduler"):
        self.worker_id = worker_id
        self._queue = job_queue
        self._scheduler = scheduler
        self._running = True
        self._thread = threading.Thread(
            target=self._run, daemon=True, name=f"Worker-{worker_id}"
        )
        self._current_job: Optional[Job] = None

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _run(self) -> None:
        while self._running:
            job = self._queue.dequeue(timeout=1.0)
            if job is None:
                continue

            self._current_job = job
            self._execute(job)
            self._current_job = None

    def _execute(self, job: Job) -> None:
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        job.attempt += 1

        try:
            start = time.monotonic()
            output = job.task() if job.task else ""
            duration = (time.monotonic() - start) * 1000

            job.result = JobResult(success=True, output=str(output),
                                   duration_ms=duration)
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            self._scheduler.on_job_completed(job)

        except Exception as e:
            duration = (time.monotonic() - start) * 1000
            job.result = JobResult(
                success=False, error=traceback.format_exc(),
                duration_ms=duration
            )

            if job.attempt < job.retry_policy.max_retries:
                delay = job.retry_policy.strategy.get_delay(job.attempt)
                job.scheduled_time = datetime.now() + timedelta(seconds=delay)
                job.status = JobStatus.SCHEDULED
                self._queue.enqueue(job)
            else:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now()
                self._scheduler.on_job_failed(job)


class JobQueue:
    def __init__(self):
        self._heap: list[tuple[datetime, int, Job]] = []
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._counter = 0

    def enqueue(self, job: Job) -> None:
        with self._not_empty:
            self._counter += 1
            heapq.heappush(
                self._heap,
                (job.scheduled_time, -job.priority, self._counter, job)
            )
            self._not_empty.notify()

    def dequeue(self, timeout: float = None) -> Optional[Job]:
        with self._not_empty:
            while True:
                if not self._heap:
                    self._not_empty.wait(timeout=timeout)
                    if not self._heap:
                        return None

                scheduled_time = self._heap[0][0]
                now = datetime.now()
                if scheduled_time <= now:
                    _, _, _, job = heapq.heappop(self._heap)
                    if job.status == JobStatus.CANCELLED:
                        continue
                    return job

                wait_seconds = (scheduled_time - now).total_seconds()
                self._not_empty.wait(timeout=min(wait_seconds, timeout or wait_seconds))
                if not self._heap:
                    return None

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._heap)


class WorkerPool:
    def __init__(self, size: int, job_queue: JobQueue,
                 scheduler: "JobScheduler"):
        self._workers = [
            Worker(i, job_queue, scheduler) for i in range(size)
        ]

    def start(self) -> None:
        for worker in self._workers:
            worker.start()

    def shutdown(self, wait: bool = True) -> None:
        for worker in self._workers:
            worker.stop()
        if wait:
            for worker in self._workers:
                worker._thread.join(timeout=5.0)


class JobScheduler:
    def __init__(self, worker_count: int = 4):
        self._jobs: dict[str, Job] = {}
        self._queue = JobQueue()
        self._pool = WorkerPool(worker_count, self._queue, self)
        self._dependency_map: dict[str, set[str]] = {}  # job_id -> pending deps
        self._dependents: dict[str, list[str]] = {}  # job_id -> downstream jobs
        self._lock = threading.Lock()
        self._listeners: list[Callable[[Job], None]] = []

    def start(self) -> None:
        self._pool.start()

    def shutdown(self) -> None:
        self._pool.shutdown()

    def submit(self, job: Job) -> str:
        with self._lock:
            self._jobs[job.job_id] = job

            unmet = {
                dep for dep in job.dependencies
                if dep in self._jobs and self._jobs[dep].status != JobStatus.COMPLETED
            }

            if unmet:
                self._dependency_map[job.job_id] = unmet
                for dep in unmet:
                    if dep not in self._dependents:
                        self._dependents[dep] = []
                    self._dependents[dep].append(job.job_id)
                job.status = JobStatus.PENDING
            else:
                job.status = JobStatus.SCHEDULED
                self._queue.enqueue(job)

        return job.job_id

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.status in (JobStatus.COMPLETED, JobStatus.RUNNING):
                return False
            job.status = JobStatus.CANCELLED
            return True

    def get_status(self, job_id: str) -> Optional[JobStatus]:
        job = self._jobs.get(job_id)
        return job.status if job else None

    def on_job_completed(self, job: Job) -> None:
        with self._lock:
            downstream = self._dependents.pop(job.job_id, [])
            for dep_id in downstream:
                pending = self._dependency_map.get(dep_id, set())
                pending.discard(job.job_id)
                if not pending:
                    self._dependency_map.pop(dep_id, None)
                    dependent_job = self._jobs[dep_id]
                    dependent_job.status = JobStatus.SCHEDULED
                    self._queue.enqueue(dependent_job)

            if job.cron_expression:
                next_job = Job(
                    name=job.name,
                    task=job.task,
                    priority=job.priority,
                    scheduled_time=self._next_cron_time(job.cron_expression),
                    retry_policy=job.retry_policy,
                    cron_expression=job.cron_expression,
                )
                self._jobs[next_job.job_id] = next_job
                self._queue.enqueue(next_job)

        for listener in self._listeners:
            listener(job)

    def on_job_failed(self, job: Job) -> None:
        for listener in self._listeners:
            listener(job)

    def _next_cron_time(self, cron_expr: str) -> datetime:
        return datetime.now() + timedelta(minutes=1)
```

### Concurrency Handling

- **Priority queue** with `Condition` for efficient blocking when the queue is empty or the next job isn't due yet
- **Worker threads** independently pull from the shared queue — no coordination needed between workers
- **Dependency tracking** is protected by a scheduler-level lock — updates to dependency maps must be atomic
- **Retry scheduling** doesn't require a separate timer — the job is re-enqueued with an updated `scheduled_time`

### Interview Tips (Amazon)

- **Amazon loves operational excellence** — discuss monitoring, alerting, dead-letter queues for repeatedly failing jobs.
- **Start with the dependency DAG** — cycle detection prevents deadlocks. Amazon will ask about this.
- **Discuss scaling**: how does this work with hundreds of thousands of jobs? Mention partitioning by job type or priority band.
- **Talk about idempotency** — what if a worker crashes mid-execution and the job is re-dispatched? Jobs should be idempotent.
- **Mention backpressure** — what happens when the queue grows faster than workers can process? Rejection policies matter.

---

## 8. Stock Broker Platform (Amazon)

### Requirements

- Users can place market orders (execute immediately at best price) and limit orders (execute at a specific price or better)
- An order matching engine pairs buy and sell orders
- Support real-time portfolio tracking with current market value
- Handle partial order fills (large orders matched across multiple counterparties)
- Maintain an order book with price-time priority
- Provide real-time price updates via observer pattern
- Support order cancellation and modification
- Track transaction history and P&L per user

### Key Entities and Relationships

```
User ──places──▶ Order ──matched by──▶ MatchingEngine
MatchingEngine ──maintains──▶ OrderBook (per stock)
OrderBook ──has──▶ BuyQueue + SellQueue (sorted by price-time)
Trade records matched Order pairs
Portfolio tracks User holdings
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **Observer** | Real-time price updates to subscribers |
| **Strategy** | Different order types (Market, Limit, Stop-Loss) |
| **Mediator** | Matching engine mediates between buy/sell sides |
| **Command** | Orders as command objects with undo (cancel) |

### Core Class Structure

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import threading
import heapq
import uuid


class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(Enum):
    PENDING = "pending"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"


@dataclass
class Order:
    order_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    user_id: str = ""
    stock_symbol: str = ""
    side: OrderSide = OrderSide.BUY
    order_type: OrderType = OrderType.LIMIT
    price: float = 0.0
    quantity: int = 0
    filled_quantity: int = 0
    status: OrderStatus = OrderStatus.PENDING
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def remaining(self) -> int:
        return self.quantity - self.filled_quantity

    def fill(self, qty: int, price: float) -> None:
        self.filled_quantity += qty
        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIALLY_FILLED


@dataclass
class Trade:
    trade_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    buy_order_id: str = ""
    sell_order_id: str = ""
    stock_symbol: str = ""
    price: float = 0.0
    quantity: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


class PriceObserver(ABC):
    @abstractmethod
    def on_price_update(self, symbol: str, price: float, volume: int) -> None:
        pass


class OrderBook:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self._buy_orders: list[tuple[float, datetime, Order]] = []  # max-heap by price
        self._sell_orders: list[tuple[float, datetime, Order]] = []  # min-heap by price
        self._lock = threading.Lock()
        self._observers: list[PriceObserver] = []
        self.last_trade_price: float = 0.0

    def add_observer(self, observer: PriceObserver) -> None:
        self._observers.append(observer)

    def add_order(self, order: Order) -> list[Trade]:
        with self._lock:
            trades = self._match(order)
            if order.remaining > 0 and order.order_type == OrderType.LIMIT:
                self._insert(order)
            return trades

    def cancel_order(self, order_id: str) -> bool:
        with self._lock:
            for heap in (self._buy_orders, self._sell_orders):
                for i, (_, _, order) in enumerate(heap):
                    if order.order_id == order_id and order.status != OrderStatus.FILLED:
                        order.status = OrderStatus.CANCELLED
                        return True
            return False

    def _match(self, incoming: Order) -> list[Trade]:
        trades = []
        if incoming.side == OrderSide.BUY:
            trades = self._match_buy(incoming)
        else:
            trades = self._match_sell(incoming)
        return trades

    def _match_buy(self, buy: Order) -> list[Trade]:
        trades = []
        while buy.remaining > 0 and self._sell_orders:
            best_price, _, best_sell = self._sell_orders[0]
            if best_sell.status == OrderStatus.CANCELLED:
                heapq.heappop(self._sell_orders)
                continue

            if buy.order_type == OrderType.LIMIT and best_price > buy.price:
                break

            trade_qty = min(buy.remaining, best_sell.remaining)
            trade_price = best_sell.price

            trade = Trade(
                buy_order_id=buy.order_id,
                sell_order_id=best_sell.order_id,
                stock_symbol=self.symbol,
                price=trade_price,
                quantity=trade_qty,
            )
            trades.append(trade)

            buy.fill(trade_qty, trade_price)
            best_sell.fill(trade_qty, trade_price)
            self.last_trade_price = trade_price

            if best_sell.remaining == 0:
                heapq.heappop(self._sell_orders)

            self._notify_price(trade_price, trade_qty)

        return trades

    def _match_sell(self, sell: Order) -> list[Trade]:
        trades = []
        while sell.remaining > 0 and self._buy_orders:
            neg_price, _, best_buy = self._buy_orders[0]
            best_price = -neg_price
            if best_buy.status == OrderStatus.CANCELLED:
                heapq.heappop(self._buy_orders)
                continue

            if sell.order_type == OrderType.LIMIT and best_price < sell.price:
                break

            trade_qty = min(sell.remaining, best_buy.remaining)
            trade_price = best_buy.price

            trade = Trade(
                buy_order_id=best_buy.order_id,
                sell_order_id=sell.order_id,
                stock_symbol=self.symbol,
                price=trade_price,
                quantity=trade_qty,
            )
            trades.append(trade)

            sell.fill(trade_qty, trade_price)
            best_buy.fill(trade_qty, trade_price)
            self.last_trade_price = trade_price

            if best_buy.remaining == 0:
                heapq.heappop(self._buy_orders)

            self._notify_price(trade_price, trade_qty)

        return trades

    def _insert(self, order: Order) -> None:
        if order.side == OrderSide.BUY:
            heapq.heappush(self._buy_orders,
                           (-order.price, order.timestamp, order))
        else:
            heapq.heappush(self._sell_orders,
                           (order.price, order.timestamp, order))

    def _notify_price(self, price: float, volume: int) -> None:
        for observer in self._observers:
            observer.on_price_update(self.symbol, price, volume)

    def get_best_bid(self) -> Optional[float]:
        for neg_price, _, order in self._buy_orders:
            if order.status != OrderStatus.CANCELLED:
                return -neg_price
        return None

    def get_best_ask(self) -> Optional[float]:
        for price, _, order in self._sell_orders:
            if order.status != OrderStatus.CANCELLED:
                return price
        return None


@dataclass
class Holding:
    symbol: str
    quantity: int = 0
    avg_cost: float = 0.0

    def add(self, qty: int, price: float) -> None:
        total_cost = self.avg_cost * self.quantity + price * qty
        self.quantity += qty
        self.avg_cost = total_cost / self.quantity if self.quantity > 0 else 0

    def remove(self, qty: int) -> None:
        self.quantity = max(0, self.quantity - qty)


class Portfolio:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.cash_balance: float = 0.0
        self.holdings: dict[str, Holding] = {}
        self._lock = threading.Lock()

    def deposit(self, amount: float) -> None:
        with self._lock:
            self.cash_balance += amount

    def update_on_trade(self, trade: Trade, side: OrderSide) -> None:
        with self._lock:
            symbol = trade.stock_symbol
            if symbol not in self.holdings:
                self.holdings[symbol] = Holding(symbol)

            if side == OrderSide.BUY:
                self.holdings[symbol].add(trade.quantity, trade.price)
                self.cash_balance -= trade.price * trade.quantity
            else:
                self.holdings[symbol].remove(trade.quantity)
                self.cash_balance += trade.price * trade.quantity

    def get_portfolio_value(self, market_prices: dict[str, float]) -> float:
        total = self.cash_balance
        for symbol, holding in self.holdings.items():
            price = market_prices.get(symbol, holding.avg_cost)
            total += holding.quantity * price
        return total


class StockBroker:
    def __init__(self):
        self._order_books: dict[str, OrderBook] = {}
        self._portfolios: dict[str, Portfolio] = {}
        self._all_trades: list[Trade] = []
        self._all_orders: dict[str, Order] = {}
        self._lock = threading.Lock()

    def register_user(self, user_id: str, initial_balance: float = 0) -> None:
        portfolio = Portfolio(user_id)
        portfolio.deposit(initial_balance)
        self._portfolios[user_id] = portfolio

    def place_order(self, order: Order) -> list[Trade]:
        with self._lock:
            if order.stock_symbol not in self._order_books:
                self._order_books[order.stock_symbol] = OrderBook(order.stock_symbol)

        self._all_orders[order.order_id] = order
        book = self._order_books[order.stock_symbol]
        trades = book.add_order(order)

        portfolio = self._portfolios.get(order.user_id)
        if portfolio:
            for trade in trades:
                portfolio.update_on_trade(trade, order.side)

        self._all_trades.extend(trades)
        return trades

    def cancel_order(self, order_id: str) -> bool:
        order = self._all_orders.get(order_id)
        if not order:
            return False
        book = self._order_books.get(order.stock_symbol)
        if not book:
            return False
        return book.cancel_order(order_id)

    def get_market_price(self, symbol: str) -> Optional[float]:
        book = self._order_books.get(symbol)
        return book.last_trade_price if book else None
```

### Concurrency Handling

- **Per-order-book locks** allow different stocks to be traded concurrently
- **Portfolio locks** ensure atomic balance updates
- **Price-time priority** in the heap ensures fair ordering — orders at the same price execute in FIFO order
- For high-frequency scenarios, consider lock-free data structures or an event-sourced architecture

### Interview Tips (Amazon)

- **Explain price-time priority clearly** — this is the core of any matching engine. "Among orders at the same price, the earliest order gets filled first."
- **Walk through a matching example**: "If there's a sell order at $100 and a buy order at $102, they match at the seller's price ($100)."
- **Discuss partial fills** — Amazon tests edge case thinking. A buy order for 1000 shares might match against three sell orders of 300, 400, and 300.
- **Mention market vs limit semantics** — market orders match at any price; limit orders only at their specified price or better.
- **Scalability**: separate order books per stock means horizontal scaling is natural.

---

## 9. YouTube (Amazon)

### Requirements

- Users can upload videos with metadata (title, description, tags)
- Videos go through an encoding pipeline (multiple resolutions)
- Support streaming with adaptive bitrate selection
- Users can like, comment, and subscribe to channels
- Recommendation engine suggests videos based on watch history
- Support video search by title, tags, and description
- Track view counts and watch duration analytics
- Content moderation interface for flagging inappropriate content

### Key Entities and Relationships

```
User ──uploads──▶ Video ──encodedTo──▶ EncodedVideo* (per resolution)
User ──subscribesTo──▶ Channel
Video ──has──▶ Comment*, Like*
RecommendationEngine ──suggests──▶ Video* to User
Video ──status──▶ {UPLOADING, ENCODING, PUBLISHED, FLAGGED, REMOVED}
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **Observer** | Notify subscribers when a channel uploads a new video |
| **Strategy** | Different recommendation algorithms |
| **Pipeline** | Video encoding as a sequence of processing steps |
| **State** | Video lifecycle (Uploading → Encoding → Published) |
| **Proxy** | Lazy-load video metadata vs. actual stream data |

### Core Class Structure

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid
import threading
from collections import defaultdict


class VideoStatus(Enum):
    UPLOADING = "uploading"
    ENCODING = "encoding"
    PUBLISHED = "published"
    FLAGGED = "flagged"
    REMOVED = "removed"


class Resolution(Enum):
    P360 = "360p"
    P480 = "480p"
    P720 = "720p"
    P1080 = "1080p"
    P4K = "4k"


@dataclass
class VideoMetadata:
    title: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    category: str = ""
    duration_seconds: int = 0
    upload_date: datetime = field(default_factory=datetime.now)


@dataclass
class EncodedVideo:
    resolution: Resolution
    url: str
    size_bytes: int
    bitrate_kbps: int


@dataclass
class Comment:
    comment_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    user_id: str = ""
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    likes: int = 0
    replies: list["Comment"] = field(default_factory=list)


class Video:
    def __init__(self, video_id: str = None, uploader_id: str = "",
                 metadata: VideoMetadata = None):
        self.video_id = video_id or str(uuid.uuid4())[:8]
        self.uploader_id = uploader_id
        self.metadata = metadata or VideoMetadata()
        self.status = VideoStatus.UPLOADING
        self.encoded_versions: dict[Resolution, EncodedVideo] = {}
        self.view_count: int = 0
        self.likes: set[str] = set()
        self.dislikes: set[str] = set()
        self.comments: list[Comment] = []
        self._lock = threading.Lock()

    def add_encoded_version(self, encoded: EncodedVideo) -> None:
        self.encoded_versions[encoded.resolution] = encoded

    def get_stream_url(self, preferred: Resolution = Resolution.P720) -> Optional[str]:
        if preferred in self.encoded_versions:
            return self.encoded_versions[preferred].url
        for res in Resolution:
            if res in self.encoded_versions:
                return self.encoded_versions[res].url
        return None

    def increment_view(self) -> None:
        with self._lock:
            self.view_count += 1

    def toggle_like(self, user_id: str) -> None:
        with self._lock:
            self.dislikes.discard(user_id)
            if user_id in self.likes:
                self.likes.discard(user_id)
            else:
                self.likes.add(user_id)

    def add_comment(self, comment: Comment) -> None:
        with self._lock:
            self.comments.append(comment)


class Channel:
    def __init__(self, channel_id: str, owner_id: str, name: str):
        self.channel_id = channel_id
        self.owner_id = owner_id
        self.name = name
        self.videos: list[str] = []
        self.subscribers: set[str] = set()
        self._lock = threading.Lock()

    def subscribe(self, user_id: str) -> None:
        with self._lock:
            self.subscribers.add(user_id)

    def unsubscribe(self, user_id: str) -> None:
        with self._lock:
            self.subscribers.discard(user_id)

    @property
    def subscriber_count(self) -> int:
        return len(self.subscribers)


class SubscriptionObserver(ABC):
    @abstractmethod
    def on_new_video(self, channel: Channel, video: Video) -> None:
        pass


class NotificationService(SubscriptionObserver):
    def on_new_video(self, channel: Channel, video: Video) -> None:
        for user_id in channel.subscribers:
            print(f"[Notification] {channel.name} uploaded: {video.metadata.title} → user {user_id}")


class EncodingStep(ABC):
    @abstractmethod
    def process(self, video: Video) -> None:
        pass


class TranscodeStep(EncodingStep):
    def __init__(self, target: Resolution, bitrate: int):
        self.target = target
        self.bitrate = bitrate

    def process(self, video: Video) -> None:
        encoded = EncodedVideo(
            resolution=self.target,
            url=f"/videos/{video.video_id}/{self.target.value}",
            size_bytes=video.metadata.duration_seconds * self.bitrate * 125,
            bitrate_kbps=self.bitrate,
        )
        video.add_encoded_version(encoded)


class ThumbnailStep(EncodingStep):
    def process(self, video: Video) -> None:
        pass  # generate thumbnail from keyframe


class EncodingPipeline:
    def __init__(self):
        self._steps: list[EncodingStep] = [
            TranscodeStep(Resolution.P360, 800),
            TranscodeStep(Resolution.P720, 2500),
            TranscodeStep(Resolution.P1080, 5000),
            ThumbnailStep(),
        ]

    def encode(self, video: Video) -> None:
        video.status = VideoStatus.ENCODING
        for step in self._steps:
            step.process(video)
        video.status = VideoStatus.PUBLISHED


class RecommendationStrategy(ABC):
    @abstractmethod
    def recommend(self, user_id: str, watch_history: list[str],
                  all_videos: dict[str, Video], count: int) -> list[Video]:
        pass


class PopularityRecommender(RecommendationStrategy):
    def recommend(self, user_id: str, watch_history: list[str],
                  all_videos: dict[str, Video], count: int) -> list[Video]:
        unwatched = [
            v for vid, v in all_videos.items()
            if vid not in watch_history and v.status == VideoStatus.PUBLISHED
        ]
        unwatched.sort(key=lambda v: v.view_count, reverse=True)
        return unwatched[:count]


class TagBasedRecommender(RecommendationStrategy):
    def recommend(self, user_id: str, watch_history: list[str],
                  all_videos: dict[str, Video], count: int) -> list[Video]:
        watched_tags: set[str] = set()
        for vid in watch_history:
            if vid in all_videos:
                watched_tags.update(all_videos[vid].metadata.tags)

        candidates = []
        for vid, video in all_videos.items():
            if vid in watch_history or video.status != VideoStatus.PUBLISHED:
                continue
            overlap = len(watched_tags & set(video.metadata.tags))
            if overlap > 0:
                candidates.append((overlap, video))

        candidates.sort(key=lambda x: (-x[0], -x[1].view_count))
        return [v for _, v in candidates[:count]]


class YouTubeService:
    def __init__(self, rec_strategy: RecommendationStrategy = None):
        self._videos: dict[str, Video] = {}
        self._channels: dict[str, Channel] = {}
        self._watch_history: dict[str, list[str]] = defaultdict(list)
        self._encoding_pipeline = EncodingPipeline()
        self._rec_strategy = rec_strategy or TagBasedRecommender()
        self._observers: list[SubscriptionObserver] = [NotificationService()]
        self._lock = threading.Lock()

    def create_channel(self, owner_id: str, name: str) -> Channel:
        channel = Channel(str(uuid.uuid4())[:8], owner_id, name)
        self._channels[channel.channel_id] = channel
        return channel

    def upload_video(self, channel_id: str, metadata: VideoMetadata) -> Video:
        channel = self._channels.get(channel_id)
        if not channel:
            raise ValueError("Channel not found")

        video = Video(uploader_id=channel.owner_id, metadata=metadata)
        self._videos[video.video_id] = video
        channel.videos.append(video.video_id)

        self._encoding_pipeline.encode(video)

        for observer in self._observers:
            observer.on_new_video(channel, video)

        return video

    def watch_video(self, user_id: str, video_id: str,
                    resolution: Resolution = Resolution.P720) -> Optional[str]:
        video = self._videos.get(video_id)
        if not video or video.status != VideoStatus.PUBLISHED:
            return None

        video.increment_view()
        self._watch_history[user_id].append(video_id)
        return video.get_stream_url(resolution)

    def search(self, query: str) -> list[Video]:
        query_lower = query.lower()
        results = []
        for video in self._videos.values():
            if video.status != VideoStatus.PUBLISHED:
                continue
            if (query_lower in video.metadata.title.lower()
                    or query_lower in video.metadata.description.lower()
                    or any(query_lower in t.lower() for t in video.metadata.tags)):
                results.append(video)
        results.sort(key=lambda v: v.view_count, reverse=True)
        return results

    def get_recommendations(self, user_id: str, count: int = 10) -> list[Video]:
        history = self._watch_history.get(user_id, [])
        return self._rec_strategy.recommend(user_id, history, self._videos, count)

    def subscribe(self, user_id: str, channel_id: str) -> None:
        channel = self._channels.get(channel_id)
        if channel:
            channel.subscribe(user_id)
```

### Concurrency Handling

- **Per-video locks** for view counts, likes, and comments — high-contention resources
- **Encoding pipeline** runs in a background thread pool — multiple videos can be encoded concurrently
- **View count** is an approximate counter (eventual consistency acceptable for display)
- **Search** is read-only and doesn't need locks if the video collection is append-only

### Interview Tips (Amazon)

- **Don't try to design all of YouTube** — scope to 3-4 core features (upload, stream, recommend). Ask the interviewer what to focus on.
- **Discuss the encoding pipeline** — Amazon loves async processing. Show how video upload triggers a pipeline that runs in the background.
- **Recommendation strategies** — even a simple tag-overlap approach shows you understand the Strategy pattern. Mention collaborative filtering as an extension.
- **Talk about CDN integration** — how would encoded videos be served globally? Amazon (AWS) knows CDNs intimately.
- **Mention eventual consistency** — view counts don't need to be exactly right in real time. This shows you understand distributed systems trade-offs.

---

## 10. Google Photos (Amazon)

### Requirements

- Users can upload, view, and delete photos with metadata (EXIF)
- Organize photos into albums with add/remove operations
- Search photos by date, location, tags, and text descriptions
- Face recognition interface for grouping photos by person
- Share albums or individual photos with other users via links
- Support multiple storage tiers (hot, warm, cold) based on access patterns
- Automatic tagging using an image classification interface
- Generate thumbnails and multiple resolutions on upload

### Key Entities and Relationships

```
User ──owns──▶ Photo* ──storedIn──▶ StorageTier
User ──creates──▶ Album ──contains──▶ Photo*
Photo ──has──▶ PhotoMetadata (EXIF, tags, faces)
ShareLink ──grants access to──▶ Album | Photo
FaceCluster ──groups──▶ Photo* by detected face
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **Strategy** | Storage tier selection, search algorithms |
| **Observer** | Notify when shared album gets new photos |
| **Facade** | `PhotoService` simplifies complex subsystems |
| **Proxy** | Lazy-load full resolution; serve thumbnails by default |
| **Template Method** | Upload pipeline (validate → process → store → index) |

### Core Class Structure

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid
import threading


class StorageTier(Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


@dataclass
class GeoLocation:
    latitude: float = 0.0
    longitude: float = 0.0
    city: str = ""
    country: str = ""


@dataclass
class PhotoMetadata:
    taken_at: datetime = field(default_factory=datetime.now)
    location: Optional[GeoLocation] = None
    camera_model: str = ""
    width: int = 0
    height: int = 0
    file_size_bytes: int = 0
    tags: list[str] = field(default_factory=list)
    detected_faces: list[str] = field(default_factory=list)  # face cluster IDs


@dataclass
class PhotoVariant:
    resolution: str
    url: str
    size_bytes: int


class Photo:
    def __init__(self, photo_id: str = None, owner_id: str = "",
                 metadata: PhotoMetadata = None):
        self.photo_id = photo_id or str(uuid.uuid4())[:8]
        self.owner_id = owner_id
        self.metadata = metadata or PhotoMetadata()
        self.storage_tier = StorageTier.HOT
        self.variants: dict[str, PhotoVariant] = {}
        self.last_accessed: datetime = datetime.now()
        self.access_count: int = 0

    def add_variant(self, resolution: str, url: str, size: int) -> None:
        self.variants[resolution] = PhotoVariant(resolution, url, size)

    def access(self) -> None:
        self.last_accessed = datetime.now()
        self.access_count += 1

    def get_url(self, resolution: str = "thumbnail") -> Optional[str]:
        variant = self.variants.get(resolution)
        return variant.url if variant else None


class Album:
    def __init__(self, album_id: str = None, owner_id: str = "",
                 name: str = ""):
        self.album_id = album_id or str(uuid.uuid4())[:8]
        self.owner_id = owner_id
        self.name = name
        self.photo_ids: list[str] = []
        self.cover_photo_id: Optional[str] = None
        self.created_at: datetime = datetime.now()
        self._lock = threading.Lock()

    def add_photo(self, photo_id: str) -> None:
        with self._lock:
            if photo_id not in self.photo_ids:
                self.photo_ids.append(photo_id)
                if self.cover_photo_id is None:
                    self.cover_photo_id = photo_id

    def remove_photo(self, photo_id: str) -> None:
        with self._lock:
            if photo_id in self.photo_ids:
                self.photo_ids.remove(photo_id)


@dataclass
class ShareLink:
    link_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    owner_id: str = ""
    resource_type: str = ""  # "photo" or "album"
    resource_id: str = ""
    allowed_users: set[str] = field(default_factory=set)
    is_public: bool = False
    expires_at: Optional[datetime] = None

    def is_valid(self) -> bool:
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True

    def can_access(self, user_id: str) -> bool:
        if self.is_public:
            return True
        return user_id == self.owner_id or user_id in self.allowed_users


class FaceCluster:
    def __init__(self, cluster_id: str = None, label: str = ""):
        self.cluster_id = cluster_id or str(uuid.uuid4())[:8]
        self.label = label  # user-assigned name
        self.photo_ids: set[str] = set()
        self.representative_embedding: list[float] = []

    def add_photo(self, photo_id: str) -> None:
        self.photo_ids.add(photo_id)


class ImageClassifier(ABC):
    @abstractmethod
    def classify(self, photo: Photo) -> list[str]:
        pass


class FaceDetector(ABC):
    @abstractmethod
    def detect_faces(self, photo: Photo) -> list[tuple[str, list[float]]]:
        """Returns list of (cluster_id_hint, embedding_vector)."""
        pass


class StorageTierStrategy(ABC):
    @abstractmethod
    def determine_tier(self, photo: Photo) -> StorageTier:
        pass


class AccessBasedTiering(StorageTierStrategy):
    def determine_tier(self, photo: Photo) -> StorageTier:
        days_since_access = (datetime.now() - photo.last_accessed).days
        if days_since_access < 30:
            return StorageTier.HOT
        elif days_since_access < 180:
            return StorageTier.WARM
        return StorageTier.COLD


class PhotoService:
    def __init__(self):
        self._photos: dict[str, Photo] = {}
        self._albums: dict[str, Album] = {}
        self._share_links: dict[str, ShareLink] = {}
        self._face_clusters: dict[str, FaceCluster] = {}
        self._tiering = AccessBasedTiering()
        self._classifier: Optional[ImageClassifier] = None
        self._face_detector: Optional[FaceDetector] = None
        self._lock = threading.Lock()

    def upload_photo(self, owner_id: str,
                     metadata: PhotoMetadata) -> Photo:
        photo = Photo(owner_id=owner_id, metadata=metadata)

        photo.add_variant("thumbnail", f"/photos/{photo.photo_id}/thumb", 50_000)
        photo.add_variant("medium", f"/photos/{photo.photo_id}/medium", 500_000)
        photo.add_variant("original", f"/photos/{photo.photo_id}/original",
                          metadata.file_size_bytes)

        if self._classifier:
            tags = self._classifier.classify(photo)
            photo.metadata.tags.extend(tags)

        if self._face_detector:
            faces = self._face_detector.detect_faces(photo)
            for cluster_hint, embedding in faces:
                cluster = self._find_or_create_cluster(cluster_hint, embedding)
                cluster.add_photo(photo.photo_id)
                photo.metadata.detected_faces.append(cluster.cluster_id)

        with self._lock:
            self._photos[photo.photo_id] = photo
        return photo

    def search(self, owner_id: str, query: str = "",
               date_from: datetime = None,
               date_to: datetime = None,
               location: str = "") -> list[Photo]:
        results = []
        for photo in self._photos.values():
            if photo.owner_id != owner_id:
                continue
            if query and not any(query.lower() in t.lower() for t in photo.metadata.tags):
                continue
            if date_from and photo.metadata.taken_at < date_from:
                continue
            if date_to and photo.metadata.taken_at > date_to:
                continue
            if location and photo.metadata.location:
                if location.lower() not in photo.metadata.location.city.lower():
                    continue
            results.append(photo)
        return results

    def create_album(self, owner_id: str, name: str) -> Album:
        album = Album(owner_id=owner_id, name=name)
        self._albums[album.album_id] = album
        return album

    def share(self, owner_id: str, resource_type: str,
              resource_id: str, target_users: set[str] = None,
              is_public: bool = False) -> ShareLink:
        link = ShareLink(
            owner_id=owner_id,
            resource_type=resource_type,
            resource_id=resource_id,
            allowed_users=target_users or set(),
            is_public=is_public,
        )
        self._share_links[link.link_id] = link
        return link

    def migrate_tiers(self) -> int:
        migrated = 0
        for photo in self._photos.values():
            new_tier = self._tiering.determine_tier(photo)
            if new_tier != photo.storage_tier:
                photo.storage_tier = new_tier
                migrated += 1
        return migrated

    def _find_or_create_cluster(self, hint: str,
                                 embedding: list[float]) -> FaceCluster:
        if hint in self._face_clusters:
            return self._face_clusters[hint]
        cluster = FaceCluster()
        cluster.representative_embedding = embedding
        self._face_clusters[cluster.cluster_id] = cluster
        return cluster
```

### Concurrency Handling

- **Per-album locks** for concurrent add/remove operations
- **Photo uploads** can be parallelized — each photo processes independently
- **Tier migration** runs as a background task, scanning photos periodically
- **Face clustering** can use batch processing with a work queue for newly uploaded photos

### Interview Tips (Amazon)

- **Scope aggressively** — Google Photos has hundreds of features. Focus on upload + search + albums + sharing.
- **Discuss the upload pipeline** — validate, generate variants, classify, index. Amazon expects you to think in pipelines.
- **Storage tiering** is an Amazon favorite — S3 has these exact tiers. Explain the cost trade-offs (hot is expensive but fast, cold is cheap but slow to retrieve).
- **Face recognition** should be an interface/strategy, not a concrete implementation. Show you separate ML concerns from application logic.
- **Talk about deduplication** — hash-based detection of duplicate uploads saves storage and money.

---

## 11. Twitch (Amazon)

### Requirements

- Streamers can start/stop live streams with title, category, and tags
- Viewers can watch live streams with low latency
- Real-time chat with message broadcasting to all viewers in a channel
- Subscription system with multiple tiers (free, Tier 1/2/3)
- Custom emote support for subscribers
- Moderation tools: timeout, ban, slow mode, subscriber-only chat
- Clip creation from live streams (short highlight segments)
- Stream analytics: viewer count, chat activity, peak viewers

### Key Entities and Relationships

```
Streamer ──starts──▶ LiveStream ──watched by──▶ Viewer*
LiveStream ──has──▶ ChatRoom ──receives──▶ ChatMessage*
Viewer ──subscribesTo──▶ Channel (with tier)
ChatRoom ──moderated by──▶ Moderator*
ChatMessage ──may contain──▶ Emote*
Clip ──extracted from──▶ LiveStream
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **Observer** | Broadcast chat messages and stream events to viewers |
| **Chain of Responsibility** | Chat message filters (banned words, slow mode, sub-only) |
| **State** | Stream lifecycle (Offline → Live → Ending → Offline) |
| **Strategy** | Different subscription tier benefits |
| **Mediator** | ChatRoom mediates between chatters |

### Core Class Structure

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import threading
import uuid
from collections import defaultdict


class StreamStatus(Enum):
    OFFLINE = "offline"
    LIVE = "live"
    ENDING = "ending"


class SubTier(Enum):
    FREE = 0
    TIER1 = 1
    TIER2 = 2
    TIER3 = 3


@dataclass
class Emote:
    emote_id: str
    code: str  # e.g., "Kappa"
    url: str
    tier_required: SubTier = SubTier.FREE


@dataclass
class ChatMessage:
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    user_id: str = ""
    username: str = ""
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    emotes_used: list[str] = field(default_factory=list)
    is_deleted: bool = False


class ChatFilter(ABC):
    def __init__(self):
        self._next: Optional["ChatFilter"] = None

    def set_next(self, next_filter: "ChatFilter") -> "ChatFilter":
        self._next = next_filter
        return next_filter

    def handle(self, message: ChatMessage, chat_room: "ChatRoom") -> Optional[str]:
        result = self.check(message, chat_room)
        if result:
            return result
        if self._next:
            return self._next.handle(message, chat_room)
        return None

    @abstractmethod
    def check(self, message: ChatMessage, chat_room: "ChatRoom") -> Optional[str]:
        pass


class BannedUserFilter(ChatFilter):
    def check(self, message: ChatMessage, chat_room: "ChatRoom") -> Optional[str]:
        if message.user_id in chat_room.banned_users:
            return "User is banned"
        return None


class SlowModeFilter(ChatFilter):
    def check(self, message: ChatMessage, chat_room: "ChatRoom") -> Optional[str]:
        if not chat_room.slow_mode_seconds:
            return None
        last_msg_time = chat_room.last_message_time.get(message.user_id)
        if last_msg_time:
            elapsed = (datetime.now() - last_msg_time).total_seconds()
            if elapsed < chat_room.slow_mode_seconds:
                return f"Slow mode: wait {chat_room.slow_mode_seconds - elapsed:.0f}s"
        return None


class SubOnlyFilter(ChatFilter):
    def check(self, message: ChatMessage, chat_room: "ChatRoom") -> Optional[str]:
        if not chat_room.sub_only_mode:
            return None
        if message.user_id not in chat_room.subscribers:
            return "Subscriber-only mode is enabled"
        return None


class BannedWordFilter(ChatFilter):
    BANNED_WORDS = {"spam", "scam"}  # simplified

    def check(self, message: ChatMessage, chat_room: "ChatRoom") -> Optional[str]:
        words = set(message.content.lower().split())
        if words & self.BANNED_WORDS:
            return "Message contains banned words"
        return None


class ChatViewer(ABC):
    @abstractmethod
    def on_message(self, message: ChatMessage) -> None:
        pass

    @abstractmethod
    def on_system_event(self, event: str) -> None:
        pass


class ChatRoom:
    def __init__(self, channel_id: str):
        self.channel_id = channel_id
        self.viewers: dict[str, ChatViewer] = {}
        self.subscribers: set[str] = set()
        self.moderators: set[str] = set()
        self.banned_users: set[str] = set()
        self.timed_out_users: dict[str, datetime] = {}
        self.messages: list[ChatMessage] = []
        self.last_message_time: dict[str, datetime] = {}
        self.slow_mode_seconds: int = 0
        self.sub_only_mode: bool = False
        self._lock = threading.Lock()

        self._filter_chain = BannedUserFilter()
        self._filter_chain.set_next(SlowModeFilter()).set_next(
            SubOnlyFilter()
        ).set_next(BannedWordFilter())

    def join(self, user_id: str, viewer: ChatViewer) -> None:
        with self._lock:
            self.viewers[user_id] = viewer
            self._broadcast_event(f"{user_id} joined the chat")

    def leave(self, user_id: str) -> None:
        with self._lock:
            self.viewers.pop(user_id, None)

    def send_message(self, message: ChatMessage) -> Optional[str]:
        with self._lock:
            self._cleanup_timeouts()

            if message.user_id in self.timed_out_users:
                remaining = (self.timed_out_users[message.user_id] - datetime.now()).seconds
                return f"Timed out for {remaining}s"

            rejection = self._filter_chain.handle(message, self)
            if rejection:
                return rejection

            self.messages.append(message)
            self.last_message_time[message.user_id] = datetime.now()

            for uid, viewer in self.viewers.items():
                viewer.on_message(message)

            return None

    def timeout_user(self, mod_id: str, target_id: str, seconds: int) -> bool:
        if mod_id not in self.moderators:
            return False
        with self._lock:
            self.timed_out_users[target_id] = datetime.now() + timedelta(seconds=seconds)
            self._broadcast_event(f"{target_id} has been timed out for {seconds}s")
            return True

    def ban_user(self, mod_id: str, target_id: str) -> bool:
        if mod_id not in self.moderators:
            return False
        with self._lock:
            self.banned_users.add(target_id)
            self.viewers.pop(target_id, None)
            self._broadcast_event(f"{target_id} has been banned")
            return True

    def toggle_slow_mode(self, seconds: int = 0) -> None:
        self.slow_mode_seconds = seconds

    def toggle_sub_only(self, enabled: bool) -> None:
        self.sub_only_mode = enabled

    def _broadcast_event(self, event: str) -> None:
        for viewer in self.viewers.values():
            viewer.on_system_event(event)

    def _cleanup_timeouts(self) -> None:
        now = datetime.now()
        expired = [uid for uid, exp in self.timed_out_users.items() if exp <= now]
        for uid in expired:
            del self.timed_out_users[uid]


@dataclass
class Clip:
    clip_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    stream_id: str = ""
    creator_id: str = ""
    title: str = ""
    start_offset_seconds: int = 0
    duration_seconds: int = 30
    view_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)


class LiveStream:
    def __init__(self, stream_id: str = None, streamer_id: str = "",
                 title: str = "", category: str = ""):
        self.stream_id = stream_id or str(uuid.uuid4())[:8]
        self.streamer_id = streamer_id
        self.title = title
        self.category = category
        self.status = StreamStatus.OFFLINE
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None
        self.chat_room = ChatRoom(stream_id or "")
        self.viewer_count: int = 0
        self.peak_viewers: int = 0
        self.clips: list[Clip] = []
        self._lock = threading.Lock()

    def go_live(self) -> None:
        self.status = StreamStatus.LIVE
        self.started_at = datetime.now()
        self.viewer_count = 0
        self.peak_viewers = 0

    def end_stream(self) -> None:
        self.status = StreamStatus.ENDING
        self.ended_at = datetime.now()
        self.status = StreamStatus.OFFLINE

    def add_viewer(self, user_id: str, viewer: ChatViewer) -> None:
        with self._lock:
            self.viewer_count += 1
            self.peak_viewers = max(self.peak_viewers, self.viewer_count)
        self.chat_room.join(user_id, viewer)

    def remove_viewer(self, user_id: str) -> None:
        with self._lock:
            self.viewer_count = max(0, self.viewer_count - 1)
        self.chat_room.leave(user_id)

    def create_clip(self, creator_id: str, title: str,
                    offset: int, duration: int = 30) -> Clip:
        clip = Clip(
            stream_id=self.stream_id,
            creator_id=creator_id,
            title=title,
            start_offset_seconds=offset,
            duration_seconds=duration,
        )
        self.clips.append(clip)
        return clip


class Subscription:
    def __init__(self, user_id: str, channel_id: str,
                 tier: SubTier = SubTier.TIER1):
        self.user_id = user_id
        self.channel_id = channel_id
        self.tier = tier
        self.started_at = datetime.now()
        self.months_subscribed = 1


class TwitchPlatform:
    def __init__(self):
        self._streams: dict[str, LiveStream] = {}
        self._subscriptions: dict[str, dict[str, Subscription]] = defaultdict(dict)
        self._emotes: dict[str, list[Emote]] = defaultdict(list)
        self._lock = threading.Lock()

    def start_stream(self, streamer_id: str, title: str,
                     category: str) -> LiveStream:
        stream = LiveStream(streamer_id=streamer_id, title=title,
                            category=category)
        stream.go_live()
        with self._lock:
            self._streams[stream.stream_id] = stream
        return stream

    def subscribe(self, user_id: str, channel_id: str,
                  tier: SubTier = SubTier.TIER1) -> Subscription:
        sub = Subscription(user_id, channel_id, tier)
        self._subscriptions[channel_id][user_id] = sub

        for stream in self._streams.values():
            if stream.streamer_id == channel_id:
                stream.chat_room.subscribers.add(user_id)

        return sub

    def get_live_streams(self, category: str = None) -> list[LiveStream]:
        streams = [
            s for s in self._streams.values()
            if s.status == StreamStatus.LIVE
        ]
        if category:
            streams = [s for s in streams if s.category == category]
        streams.sort(key=lambda s: s.viewer_count, reverse=True)
        return streams

    def add_emote(self, channel_id: str, emote: Emote) -> None:
        self._emotes[channel_id].append(emote)

    def get_emotes(self, user_id: str, channel_id: str) -> list[Emote]:
        sub = self._subscriptions.get(channel_id, {}).get(user_id)
        user_tier = sub.tier if sub else SubTier.FREE
        return [
            e for e in self._emotes.get(channel_id, [])
            if e.tier_required.value <= user_tier.value
        ]
```

### Concurrency Handling

- **Chat rooms** use a lock for message broadcasting — messages must be delivered in order
- **Chain of Responsibility** filters run within the lock to ensure consistent rule enforcement (e.g., slow mode checks are atomic with message delivery)
- **Viewer count** updates are locked per-stream — high concurrency when popular streams gain/lose viewers rapidly
- For production scale, chat would use a pub/sub system (Redis Pub/Sub or Kafka) instead of in-process broadcasting

### Interview Tips (Amazon)

- **Focus on the chat system** — it's the most interesting LLD problem within Twitch. Real-time message delivery to thousands of viewers is challenging.
- **Chain of Responsibility for moderation** is a strong pattern choice. Explain how filters are composable and order-independent (mostly).
- **Discuss scaling chat**: at Twitch scale, a single chat room can have 100K+ viewers. Mention sharding chat servers, fan-out strategies, and message buffering.
- **Subscription tiers** are a business logic problem — show you can model tiered access with clean abstractions.
- **Amazon will ask about failure modes**: what happens if a chat server dies? How do you reconnect viewers? Mention WebSocket reconnection and message replay from an offset.

---

# Adobe Series

---

## 12. Notification Service (Adobe)

### Requirements

- Support multiple notification channels: Email, SMS, Push notification
- Template-based notification content with variable substitution
- Priority levels (Critical, High, Normal, Low) with channel routing
- Rate limiting per user per channel to prevent spam
- Batch notifications for digest-style delivery
- Retry failed notifications with exponential backoff
- Track delivery status (Sent, Delivered, Failed, Read)
- Support scheduled notifications (send at a specific time)

### Key Entities and Relationships

```
NotificationRequest ──routed to──▶ Channel(s)
NotificationTemplate ──rendered with──▶ context variables
Channel ──sends via──▶ ChannelProvider (Email, SMS, Push)
RateLimiter ──guards──▶ Channel per user
DeliveryRecord tracks attempt history
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **Strategy** | Different channel providers |
| **Template Method** | Render → validate → send → track delivery |
| **Observer** | Delivery status callbacks |
| **Builder** | Construct complex notification requests |
| **Chain of Responsibility** | Priority routing, rate limiting, deduplication |

### Core Class Structure

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from collections import defaultdict
import threading
import uuid
import time
import re


class NotificationPriority(Enum):
    CRITICAL = 4
    HIGH = 3
    NORMAL = 2
    LOW = 1


class ChannelType(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class DeliveryStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


@dataclass
class NotificationTemplate:
    template_id: str
    name: str
    channel: ChannelType
    subject_template: str = ""
    body_template: str = ""

    def render(self, context: dict[str, str]) -> tuple[str, str]:
        subject = self._substitute(self.subject_template, context)
        body = self._substitute(self.body_template, context)
        return subject, body

    def _substitute(self, template: str, context: dict[str, str]) -> str:
        def replacer(match):
            key = match.group(1)
            return context.get(key, match.group(0))
        return re.sub(r"\{\{(\w+)\}\}", replacer, template)


@dataclass
class DeliveryRecord:
    record_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    notification_id: str = ""
    channel: ChannelType = ChannelType.EMAIL
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempts: int = 0
    last_attempt: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error: str = ""


class NotificationRequest:
    """Builder pattern for constructing notification requests."""

    def __init__(self):
        self.notification_id = str(uuid.uuid4())[:8]
        self.user_id: str = ""
        self.template_id: str = ""
        self.context: dict[str, str] = {}
        self.priority: NotificationPriority = NotificationPriority.NORMAL
        self.channels: list[ChannelType] = []
        self.scheduled_at: Optional[datetime] = None
        self.created_at: datetime = datetime.now()

    def to_user(self, user_id: str) -> "NotificationRequest":
        self.user_id = user_id
        return self

    def using_template(self, template_id: str) -> "NotificationRequest":
        self.template_id = template_id
        return self

    def with_context(self, **kwargs: str) -> "NotificationRequest":
        self.context.update(kwargs)
        return self

    def with_priority(self, priority: NotificationPriority) -> "NotificationRequest":
        self.priority = priority
        return self

    def via(self, *channels: ChannelType) -> "NotificationRequest":
        self.channels = list(channels)
        return self

    def schedule_at(self, when: datetime) -> "NotificationRequest":
        self.scheduled_at = when
        return self

    def build(self) -> "NotificationRequest":
        if not self.channels:
            self.channels = [ChannelType.EMAIL]
        return self


class ChannelProvider(ABC):
    @abstractmethod
    def send(self, user_id: str, subject: str, body: str) -> bool:
        pass


class EmailProvider(ChannelProvider):
    def send(self, user_id: str, subject: str, body: str) -> bool:
        print(f"[Email → {user_id}] {subject}: {body[:50]}...")
        return True


class SMSProvider(ChannelProvider):
    def send(self, user_id: str, subject: str, body: str) -> bool:
        print(f"[SMS → {user_id}] {body[:160]}")
        return True


class PushProvider(ChannelProvider):
    def send(self, user_id: str, subject: str, body: str) -> bool:
        print(f"[Push → {user_id}] {subject}")
        return True


class RateLimiter:
    def __init__(self, max_per_hour: int = 10, max_per_day: int = 50):
        self._max_per_hour = max_per_hour
        self._max_per_day = max_per_day
        self._hourly: dict[str, list[datetime]] = defaultdict(list)
        self._daily: dict[str, list[datetime]] = defaultdict(list)
        self._lock = threading.Lock()

    def allow(self, user_id: str, channel: ChannelType) -> bool:
        key = f"{user_id}:{channel.value}"
        now = datetime.now()

        with self._lock:
            hour_ago = now - timedelta(hours=1)
            self._hourly[key] = [t for t in self._hourly[key] if t > hour_ago]
            if len(self._hourly[key]) >= self._max_per_hour:
                return False

            day_ago = now - timedelta(days=1)
            self._daily[key] = [t for t in self._daily[key] if t > day_ago]
            if len(self._daily[key]) >= self._max_per_day:
                return False

            self._hourly[key].append(now)
            self._daily[key].append(now)
            return True


class NotificationService:
    MAX_RETRIES = 3

    def __init__(self):
        self._templates: dict[str, NotificationTemplate] = {}
        self._providers: dict[ChannelType, ChannelProvider] = {
            ChannelType.EMAIL: EmailProvider(),
            ChannelType.SMS: SMSProvider(),
            ChannelType.PUSH: PushProvider(),
        }
        self._rate_limiter = RateLimiter()
        self._delivery_records: dict[str, list[DeliveryRecord]] = defaultdict(list)
        self._priority_routing: dict[NotificationPriority, list[ChannelType]] = {
            NotificationPriority.CRITICAL: [ChannelType.SMS, ChannelType.PUSH, ChannelType.EMAIL],
            NotificationPriority.HIGH: [ChannelType.PUSH, ChannelType.EMAIL],
            NotificationPriority.NORMAL: [ChannelType.EMAIL],
            NotificationPriority.LOW: [ChannelType.EMAIL],
        }
        self._lock = threading.Lock()

    def register_template(self, template: NotificationTemplate) -> None:
        self._templates[template.template_id] = template

    def send(self, request: NotificationRequest) -> list[DeliveryRecord]:
        channels = request.channels or self._priority_routing.get(
            request.priority, [ChannelType.EMAIL]
        )
        records = []

        for channel in channels:
            record = self._send_to_channel(request, channel)
            records.append(record)

        return records

    def _send_to_channel(self, request: NotificationRequest,
                          channel: ChannelType) -> DeliveryRecord:
        record = DeliveryRecord(
            notification_id=request.notification_id,
            channel=channel,
        )

        if not self._rate_limiter.allow(request.user_id, channel):
            record.status = DeliveryStatus.FAILED
            record.error = "Rate limited"
            self._delivery_records[request.notification_id].append(record)
            return record

        template = self._templates.get(request.template_id)
        if template:
            subject, body = template.render(request.context)
        else:
            subject = request.context.get("subject", "Notification")
            body = request.context.get("body", "")

        provider = self._providers.get(channel)
        if not provider:
            record.status = DeliveryStatus.FAILED
            record.error = f"No provider for {channel.value}"
            return record

        for attempt in range(self.MAX_RETRIES):
            record.attempts = attempt + 1
            record.last_attempt = datetime.now()
            try:
                if provider.send(request.user_id, subject, body):
                    record.status = DeliveryStatus.SENT
                    record.delivered_at = datetime.now()
                    break
                record.status = DeliveryStatus.FAILED
                record.error = "Provider returned failure"
            except Exception as e:
                record.status = DeliveryStatus.FAILED
                record.error = str(e)

            if attempt < self.MAX_RETRIES - 1:
                time.sleep(min(2 ** attempt, 10))

        self._delivery_records[request.notification_id].append(record)
        return record

    def get_delivery_status(self, notification_id: str) -> list[DeliveryRecord]:
        return self._delivery_records.get(notification_id, [])
```

### Concurrency Handling

- **Rate limiter** uses a lock to atomically check and record send times, preventing burst overflows
- **Channel providers** are stateless and can be called concurrently — different channels for the same notification are sent in parallel
- **Retry backoff** uses `time.sleep` in the current thread; in production, retries would be scheduled via a persistent queue
- For high throughput, use a **work queue** (Redis, SQS) to decouple request ingestion from delivery

### Interview Tips (Adobe)

- **Adobe focuses on extensibility** — show how adding a new channel (Slack, WhatsApp) requires only a new `ChannelProvider` implementation.
- **Template rendering** is important — Adobe builds creative tools. Show proper variable substitution with escaping.
- **Rate limiting** should be discussed early — it's a common follow-up question. Explain the sliding window approach.
- **Priority routing** is a nice touch — critical alerts go to SMS + Push, low-priority goes to email only. This shows you think about user experience.
- **Discuss the builder pattern** for `NotificationRequest` — Adobe appreciates fluent APIs.

---

## 13. Cache System (Adobe)

### Requirements

- Support multiple eviction policies: LRU, LFU, FIFO, TTL-based
- Multi-level caching (L1 in-memory, L2 distributed interface)
- Configurable maximum size per cache level
- Time-to-live (TTL) per entry with lazy and active expiration
- Cache statistics: hit rate, miss rate, eviction count
- Thread-safe concurrent access
- Support for cache-aside, read-through, and write-through patterns
- Distributed cache interface with consistent hashing

### Key Entities and Relationships

```
CacheManager ──manages──▶ CacheLevel* (L1, L2, ...)
CacheLevel ──uses──▶ EvictionPolicy
CacheLevel ──contains──▶ CacheEntry*
CacheEntry ──has──▶ value, TTL, access metadata
EvictionPolicy decides which entry to evict
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **Strategy** | Pluggable eviction policies |
| **Chain of Responsibility** | Multi-level cache lookup (L1 → L2 → origin) |
| **Decorator** | Add TTL, stats, or logging to any cache |
| **Proxy** | Cache as a proxy for expensive data source |
| **Singleton** | Global cache manager instance |

### Core Class Structure

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Optional, Callable
from collections import OrderedDict, defaultdict
import threading
import time
import heapq


@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: float = field(default_factory=time.monotonic)
    last_accessed: float = field(default_factory=time.monotonic)
    access_count: int = 0
    ttl_seconds: Optional[float] = None

    @property
    def is_expired(self) -> bool:
        if self.ttl_seconds is None:
            return False
        return (time.monotonic() - self.created_at) > self.ttl_seconds

    def touch(self) -> None:
        self.last_accessed = time.monotonic()
        self.access_count += 1


class EvictionPolicy(ABC):
    @abstractmethod
    def on_access(self, key: str) -> None:
        pass

    @abstractmethod
    def on_insert(self, key: str) -> None:
        pass

    @abstractmethod
    def evict(self) -> Optional[str]:
        pass

    @abstractmethod
    def remove(self, key: str) -> None:
        pass


class LRUPolicy(EvictionPolicy):
    def __init__(self):
        self._order: OrderedDict[str, None] = OrderedDict()

    def on_access(self, key: str) -> None:
        if key in self._order:
            self._order.move_to_end(key)

    def on_insert(self, key: str) -> None:
        self._order[key] = None
        self._order.move_to_end(key)

    def evict(self) -> Optional[str]:
        if self._order:
            return self._order.popitem(last=False)[0]
        return None

    def remove(self, key: str) -> None:
        self._order.pop(key, None)


class LFUPolicy(EvictionPolicy):
    def __init__(self):
        self._freq: dict[str, int] = {}
        self._freq_buckets: dict[int, OrderedDict] = defaultdict(OrderedDict)
        self._min_freq = 0

    def on_access(self, key: str) -> None:
        if key not in self._freq:
            return
        old_freq = self._freq[key]
        self._freq[key] = old_freq + 1
        del self._freq_buckets[old_freq][key]
        if not self._freq_buckets[old_freq] and self._min_freq == old_freq:
            self._min_freq += 1
        self._freq_buckets[old_freq + 1][key] = None

    def on_insert(self, key: str) -> None:
        self._freq[key] = 1
        self._freq_buckets[1][key] = None
        self._min_freq = 1

    def evict(self) -> Optional[str]:
        if not self._freq_buckets[self._min_freq]:
            return None
        key, _ = self._freq_buckets[self._min_freq].popitem(last=False)
        del self._freq[key]
        return key

    def remove(self, key: str) -> None:
        if key in self._freq:
            freq = self._freq.pop(key)
            self._freq_buckets[freq].pop(key, None)


class FIFOPolicy(EvictionPolicy):
    def __init__(self):
        self._order: OrderedDict[str, None] = OrderedDict()

    def on_access(self, key: str) -> None:
        pass

    def on_insert(self, key: str) -> None:
        self._order[key] = None

    def evict(self) -> Optional[str]:
        if self._order:
            return self._order.popitem(last=False)[0]
        return None

    def remove(self, key: str) -> None:
        self._order.pop(key, None)


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class Cache(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def put(self, key: str, value: Any, ttl: float = None) -> None:
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass


class InMemoryCache(Cache):
    def __init__(self, max_size: int = 1000,
                 policy: EvictionPolicy = None,
                 default_ttl: float = None):
        self._max_size = max_size
        self._policy = policy or LRUPolicy()
        self._default_ttl = default_ttl
        self._store: dict[str, CacheEntry] = {}
        self._stats = CacheStats()
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._stats.misses += 1
                return None

            if entry.is_expired:
                self._remove(key)
                self._stats.misses += 1
                self._stats.expirations += 1
                return None

            entry.touch()
            self._policy.on_access(key)
            self._stats.hits += 1
            return entry.value

    def put(self, key: str, value: Any, ttl: float = None) -> None:
        with self._lock:
            if key in self._store:
                self._remove(key)

            while len(self._store) >= self._max_size:
                evicted_key = self._policy.evict()
                if evicted_key:
                    del self._store[evicted_key]
                    self._stats.evictions += 1
                else:
                    break

            entry = CacheEntry(
                key=key, value=value,
                ttl_seconds=ttl or self._default_ttl
            )
            self._store[key] = entry
            self._policy.on_insert(key)

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._remove(key)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def _remove(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            self._policy.remove(key)
            return True
        return False

    @property
    def stats(self) -> CacheStats:
        return self._stats

    @property
    def size(self) -> int:
        return len(self._store)

    def cleanup_expired(self) -> int:
        with self._lock:
            expired = [k for k, v in self._store.items() if v.is_expired]
            for key in expired:
                self._remove(key)
                self._stats.expirations += 1
            return len(expired)


class MultiLevelCache(Cache):
    def __init__(self, levels: list[Cache]):
        self._levels = levels

    def get(self, key: str) -> Optional[Any]:
        for i, level in enumerate(self._levels):
            value = level.get(key)
            if value is not None:
                for j in range(i):
                    self._levels[j].put(key, value)
                return value
        return None

    def put(self, key: str, value: Any, ttl: float = None) -> None:
        for level in self._levels:
            level.put(key, value, ttl)

    def delete(self, key: str) -> bool:
        deleted = False
        for level in self._levels:
            if level.delete(key):
                deleted = True
        return deleted

    def clear(self) -> None:
        for level in self._levels:
            level.clear()


class ReadThroughCache(Cache):
    """Cache that auto-loads from a data source on miss."""

    def __init__(self, cache: Cache,
                 loader: Callable[[str], Optional[Any]],
                 default_ttl: float = 300):
        self._cache = cache
        self._loader = loader
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        value = self._cache.get(key)
        if value is not None:
            return value

        value = self._loader(key)
        if value is not None:
            self._cache.put(key, value, self._default_ttl)
        return value

    def put(self, key: str, value: Any, ttl: float = None) -> None:
        self._cache.put(key, value, ttl or self._default_ttl)

    def delete(self, key: str) -> bool:
        return self._cache.delete(key)

    def clear(self) -> None:
        self._cache.clear()
```

### Concurrency Handling

- **RLock** (reentrant lock) allows nested cache operations without deadlock
- **Lazy expiration** on `get()` — expired entries are only cleaned up when accessed, reducing lock contention
- **Active cleanup** via `cleanup_expired()` can run in a background thread on a schedule
- **Multi-level cache** write-back is sequential (L1 → L2) ensuring consistency
- For distributed caches, use **optimistic locking** with version numbers

### Interview Tips (Adobe)

- **Adobe loves the Strategy pattern here** — show clean separation between cache storage and eviction policy.
- **Explain LRU vs LFU trade-offs**: LRU is simpler and works well for temporal locality; LFU handles frequency-based access patterns but has a "cache pollution" problem with old high-frequency entries.
- **Multi-level caching** impresses — explain L1 (local, fast, small) vs L2 (distributed, slower, larger).
- **Discuss cache stampede** — when a popular key expires, many threads hit the data source simultaneously. Solutions: locking, probabilistic early expiration.
- **TTL management** — mention both lazy (check on access) and active (background sweeper) expiration.

---

## 14. Configuration Management Service (Adobe)

### Requirements

- Support hierarchical configuration (global → environment → service → instance)
- Version all configuration changes with rollback capability
- Support multiple data types: strings, integers, booleans, JSON objects
- A/B testing support with traffic splitting by percentage
- Real-time config propagation to subscribed services
- Access control: read/write permissions per config namespace
- Audit log of all configuration changes
- Environment-aware configuration (dev, staging, production)

### Key Entities and Relationships

```
ConfigNamespace ──contains──▶ ConfigEntry*
ConfigEntry ──has──▶ ConfigVersion* (history)
ConfigEntry ──may have──▶ ABTestConfig (variants)
Environment ──overrides──▶ ConfigEntry values
ConfigSubscriber ──watches──▶ ConfigNamespace changes
AuditLog records all mutations
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **Observer** | Real-time config change propagation |
| **Chain of Responsibility** | Hierarchical config resolution (instance → service → env → global) |
| **Memento** | Config versioning and rollback |
| **Strategy** | A/B test traffic splitting strategies |
| **Proxy** | Access control wrapper around config operations |

### Core Class Structure

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import threading
import copy
import uuid
import hashlib
import json


class Environment(Enum):
    DEVELOPMENT = "dev"
    STAGING = "staging"
    PRODUCTION = "prod"


class ConfigType(Enum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    FLOAT = "float"
    JSON = "json"


@dataclass
class ConfigVersion:
    version: int
    value: Any
    config_type: ConfigType
    changed_by: str
    changed_at: datetime = field(default_factory=datetime.now)
    comment: str = ""


@dataclass
class ABVariant:
    variant_name: str
    value: Any
    traffic_percentage: float  # 0.0 to 1.0


@dataclass
class ABTestConfig:
    test_id: str
    variants: list[ABVariant] = field(default_factory=list)
    is_active: bool = True

    def get_variant(self, user_id: str) -> ABVariant:
        hash_val = int(hashlib.md5(
            f"{self.test_id}:{user_id}".encode()
        ).hexdigest(), 16)
        bucket = (hash_val % 100) / 100.0

        cumulative = 0.0
        for variant in self.variants:
            cumulative += variant.traffic_percentage
            if bucket < cumulative:
                return variant
        return self.variants[-1] if self.variants else None


@dataclass
class AuditEntry:
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    namespace: str = ""
    key: str = ""
    action: str = ""
    old_value: Any = None
    new_value: Any = None
    changed_by: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


class ConfigEntry:
    def __init__(self, key: str, value: Any,
                 config_type: ConfigType = ConfigType.STRING):
        self.key = key
        self.current_value = value
        self.config_type = config_type
        self.versions: list[ConfigVersion] = [
            ConfigVersion(version=1, value=value, config_type=config_type,
                          changed_by="system", comment="Initial value")
        ]
        self.ab_test: Optional[ABTestConfig] = None
        self._lock = threading.Lock()

    @property
    def current_version(self) -> int:
        return len(self.versions)

    def update(self, value: Any, changed_by: str, comment: str = "") -> int:
        with self._lock:
            version = ConfigVersion(
                version=self.current_version + 1,
                value=value,
                config_type=self.config_type,
                changed_by=changed_by,
                comment=comment,
            )
            self.versions.append(version)
            self.current_value = value
            return version.version

    def rollback(self, target_version: int, changed_by: str) -> bool:
        with self._lock:
            if target_version < 1 or target_version > len(self.versions):
                return False
            old_value = self.versions[target_version - 1].value
            self.update(old_value, changed_by,
                        f"Rollback to version {target_version}")
            return True

    def get_value(self, user_id: str = None) -> Any:
        if self.ab_test and self.ab_test.is_active and user_id:
            variant = self.ab_test.get_variant(user_id)
            if variant:
                return variant.value
        return self.current_value


class ConfigChangeListener(ABC):
    @abstractmethod
    def on_config_change(self, namespace: str, key: str,
                          old_value: Any, new_value: Any) -> None:
        pass


class ConfigNamespace:
    def __init__(self, name: str, parent: "ConfigNamespace" = None):
        self.name = name
        self.parent = parent
        self._entries: dict[str, ConfigEntry] = {}
        self._listeners: list[ConfigChangeListener] = []
        self._lock = threading.RLock()

    def set(self, key: str, value: Any, config_type: ConfigType,
            changed_by: str, comment: str = "") -> int:
        with self._lock:
            if key in self._entries:
                old_value = self._entries[key].current_value
                version = self._entries[key].update(value, changed_by, comment)
                self._notify(key, old_value, value)
                return version

            entry = ConfigEntry(key, value, config_type)
            self._entries[key] = entry
            self._notify(key, None, value)
            return 1

    def get(self, key: str, user_id: str = None,
            default: Any = None) -> Any:
        with self._lock:
            entry = self._entries.get(key)
            if entry:
                return entry.get_value(user_id)
            if self.parent:
                return self.parent.get(key, user_id, default)
            return default

    def get_entry(self, key: str) -> Optional[ConfigEntry]:
        return self._entries.get(key)

    def rollback(self, key: str, version: int, changed_by: str) -> bool:
        entry = self._entries.get(key)
        if not entry:
            return False
        old_value = entry.current_value
        result = entry.rollback(version, changed_by)
        if result:
            self._notify(key, old_value, entry.current_value)
        return result

    def add_listener(self, listener: ConfigChangeListener) -> None:
        self._listeners.append(listener)

    def _notify(self, key: str, old_value: Any, new_value: Any) -> None:
        for listener in self._listeners:
            listener.on_config_change(self.name, key, old_value, new_value)

    def all_keys(self) -> list[str]:
        keys = set(self._entries.keys())
        if self.parent:
            keys |= set(self.parent.all_keys())
        return sorted(keys)


class ConfigService:
    def __init__(self):
        self._namespaces: dict[str, ConfigNamespace] = {}
        self._env_overrides: dict[Environment, dict[str, ConfigNamespace]] = {
            env: {} for env in Environment
        }
        self._audit_log: list[AuditEntry] = []
        self._permissions: dict[str, set[str]] = {}  # user -> allowed namespaces
        self._lock = threading.Lock()

    def create_namespace(self, name: str,
                          parent_name: str = None) -> ConfigNamespace:
        parent = self._namespaces.get(parent_name)
        ns = ConfigNamespace(name, parent)
        self._namespaces[name] = ns
        return ns

    def set_config(self, namespace: str, key: str, value: Any,
                   config_type: ConfigType, changed_by: str,
                   environment: Environment = None,
                   comment: str = "") -> bool:
        if not self._check_permission(changed_by, namespace):
            return False

        ns = self._resolve_namespace(namespace, environment)
        if not ns:
            return False

        old_value = ns.get(key)
        ns.set(key, value, config_type, changed_by, comment)

        self._audit_log.append(AuditEntry(
            namespace=namespace, key=key, action="set",
            old_value=old_value, new_value=value, changed_by=changed_by,
        ))
        return True

    def get_config(self, namespace: str, key: str,
                   environment: Environment = None,
                   user_id: str = None,
                   default: Any = None) -> Any:
        if environment:
            env_ns = self._env_overrides.get(environment, {}).get(namespace)
            if env_ns:
                val = env_ns.get(key, user_id)
                if val is not None:
                    return val

        ns = self._namespaces.get(namespace)
        if ns:
            return ns.get(key, user_id, default)
        return default

    def setup_ab_test(self, namespace: str, key: str,
                       test_id: str, variants: list[ABVariant]) -> bool:
        ns = self._namespaces.get(namespace)
        if not ns:
            return False
        entry = ns.get_entry(key)
        if not entry:
            return False
        entry.ab_test = ABTestConfig(test_id=test_id, variants=variants)
        return True

    def grant_permission(self, user_id: str, namespace: str) -> None:
        if user_id not in self._permissions:
            self._permissions[user_id] = set()
        self._permissions[user_id].add(namespace)

    def get_audit_log(self, namespace: str = None,
                       limit: int = 50) -> list[AuditEntry]:
        entries = self._audit_log
        if namespace:
            entries = [e for e in entries if e.namespace == namespace]
        return entries[-limit:]

    def _check_permission(self, user_id: str, namespace: str) -> bool:
        if user_id == "admin":
            return True
        allowed = self._permissions.get(user_id, set())
        return namespace in allowed

    def _resolve_namespace(self, name: str,
                            environment: Environment = None) -> Optional[ConfigNamespace]:
        if environment:
            env_namespaces = self._env_overrides.setdefault(environment, {})
            if name not in env_namespaces:
                parent = self._namespaces.get(name)
                env_namespaces[name] = ConfigNamespace(
                    f"{name}:{environment.value}", parent
                )
            return env_namespaces[name]
        return self._namespaces.get(name)
```

### Concurrency Handling

- **Per-entry locks** for atomic version updates — multiple keys can be updated concurrently
- **RLock** on namespaces allows nested get operations during hierarchical resolution
- **Listener notifications** are synchronous within the lock — consider async dispatch for production
- **A/B test bucketing** is deterministic (hash-based) and requires no locks

### Interview Tips (Adobe)

- **Hierarchical resolution** is the key insight — Adobe uses layered configs extensively. Show how instance config overrides service config, which overrides global.
- **Versioning and rollback** demonstrate operational maturity — Adobe ships software to millions of users and needs safe rollback.
- **A/B testing** shows business awareness — Adobe Sensei and Target are A/B testing products. Show deterministic bucketing with consistent hashing.
- **Audit logging** is non-negotiable for enterprise software — every config change must be traceable.
- **Discuss config drift detection** — how do you know if running services have stale config? Mention heartbeat-based version checks.

---

## 15. Train Ticket Booking (Adobe)

### Requirements

- Browse available trains by route, date, and class
- Support multiple seat classes (1AC, 2AC, 3AC, Sleeper, General)
- Implement RAC (Reservation Against Cancellation) and waiting list
- Handle concurrent booking with proper seat allocation
- Support booking cancellation with automatic RAC/waitlist promotion
- Calculate fare based on distance, class, and dynamic pricing
- Generate PNR (Passenger Name Record) for each booking
- Support multiple passengers per booking

### Key Entities and Relationships

```
Train ──runs on──▶ Route ──has──▶ Station*
Train ──has──▶ Coach* ──contains──▶ Seat*
Booking ──has──▶ Passenger* ──assigned──▶ Seat | RAC | WaitList
Booking ──identified by──▶ PNR
SeatClass defines quota: Confirmed + RAC + WaitList
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **State** | Booking status transitions (Confirmed → RAC → WaitList → Cancelled) |
| **Strategy** | Fare calculation strategies |
| **Observer** | Notify waitlisted passengers when seats become available |
| **Template Method** | Booking flow (validate → allocate → pay → confirm) |

### Core Class Structure

```python
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional
import threading
import uuid
from collections import deque


class SeatClass(Enum):
    FIRST_AC = "1AC"
    SECOND_AC = "2AC"
    THIRD_AC = "3AC"
    SLEEPER = "SL"
    GENERAL = "GEN"


class BookingStatus(Enum):
    CONFIRMED = "CNF"
    RAC = "RAC"
    WAITLISTED = "WL"
    CANCELLED = "CAN"


class SeatPosition(Enum):
    LOWER = "lower"
    MIDDLE = "middle"
    UPPER = "upper"
    SIDE_LOWER = "side_lower"
    SIDE_UPPER = "side_upper"


@dataclass
class Station:
    code: str
    name: str
    distance_km: float = 0.0  # from origin of route


@dataclass
class Route:
    route_id: str
    stations: list[Station] = field(default_factory=list)

    def get_distance(self, from_code: str, to_code: str) -> float:
        from_dist = next((s.distance_km for s in self.stations if s.code == from_code), 0)
        to_dist = next((s.distance_km for s in self.stations if s.code == to_code), 0)
        return abs(to_dist - from_dist)


@dataclass
class Seat:
    seat_id: str
    coach_number: str
    seat_number: int
    seat_class: SeatClass
    position: SeatPosition
    is_available: bool = True


@dataclass
class Passenger:
    name: str
    age: int
    gender: str
    seat: Optional[Seat] = None
    status: BookingStatus = BookingStatus.WAITLISTED
    rac_number: int = 0
    waitlist_number: int = 0


@dataclass
class Coach:
    coach_number: str
    seat_class: SeatClass
    seats: list[Seat] = field(default_factory=list)
    total_seats: int = 0
    rac_quota: int = 0
    waitlist_quota: int = 0


class ClassQuota:
    """Manages seat allocation, RAC, and waiting list for a seat class on a specific train-date."""

    def __init__(self, seat_class: SeatClass, seats: list[Seat],
                 rac_quota: int, waitlist_quota: int):
        self.seat_class = seat_class
        self._available_seats: deque[Seat] = deque(seats)
        self._rac_quota = rac_quota
        self._rac_count = 0
        self._rac_queue: deque[Passenger] = deque()
        self._waitlist_quota = waitlist_quota
        self._waitlist_count = 0
        self._waitlist_queue: deque[Passenger] = deque()
        self._lock = threading.Lock()

    @property
    def available_count(self) -> int:
        return len(self._available_seats)

    @property
    def rac_available(self) -> int:
        return self._rac_quota - self._rac_count

    @property
    def waitlist_available(self) -> int:
        return self._waitlist_quota - self._waitlist_count

    def allocate(self, passenger: Passenger) -> BookingStatus:
        with self._lock:
            if self._available_seats:
                seat = self._available_seats.popleft()
                seat.is_available = False
                passenger.seat = seat
                passenger.status = BookingStatus.CONFIRMED
                return BookingStatus.CONFIRMED

            if self._rac_count < self._rac_quota:
                self._rac_count += 1
                passenger.rac_number = self._rac_count
                passenger.status = BookingStatus.RAC
                self._rac_queue.append(passenger)
                return BookingStatus.RAC

            if self._waitlist_count < self._waitlist_quota:
                self._waitlist_count += 1
                passenger.waitlist_number = self._waitlist_count
                passenger.status = BookingStatus.WAITLISTED
                self._waitlist_queue.append(passenger)
                return BookingStatus.WAITLISTED

            return None

    def release(self, passenger: Passenger) -> Optional[Passenger]:
        """Release a seat and promote RAC/waitlist passengers."""
        with self._lock:
            promoted = None

            if passenger.status == BookingStatus.CONFIRMED and passenger.seat:
                passenger.seat.is_available = True

                if self._rac_queue:
                    rac_passenger = self._rac_queue.popleft()
                    rac_passenger.seat = passenger.seat
                    rac_passenger.status = BookingStatus.CONFIRMED
                    passenger.seat.is_available = False
                    self._rac_count -= 1
                    promoted = rac_passenger

                    if self._waitlist_queue:
                        wl_passenger = self._waitlist_queue.popleft()
                        wl_passenger.status = BookingStatus.RAC
                        self._rac_count += 1
                        self._rac_queue.append(wl_passenger)
                        self._waitlist_count -= 1
                else:
                    self._available_seats.append(passenger.seat)

            elif passenger.status == BookingStatus.RAC:
                self._rac_queue.remove(passenger)
                self._rac_count -= 1
                if self._waitlist_queue:
                    wl_passenger = self._waitlist_queue.popleft()
                    wl_passenger.status = BookingStatus.RAC
                    self._rac_queue.append(wl_passenger)
                    self._waitlist_count -= 1

            elif passenger.status == BookingStatus.WAITLISTED:
                self._waitlist_queue.remove(passenger)
                self._waitlist_count -= 1

            passenger.status = BookingStatus.CANCELLED
            passenger.seat = None
            return promoted


class FareCalculator:
    BASE_RATES = {
        SeatClass.FIRST_AC: 4.0,
        SeatClass.SECOND_AC: 2.5,
        SeatClass.THIRD_AC: 1.8,
        SeatClass.SLEEPER: 1.0,
        SeatClass.GENERAL: 0.5,
    }

    def calculate(self, distance_km: float, seat_class: SeatClass,
                  passenger_count: int = 1) -> float:
        rate = self.BASE_RATES.get(seat_class, 1.0)
        base_fare = distance_km * rate
        return round(base_fare * passenger_count, 2)


@dataclass
class Booking:
    pnr: str = field(default_factory=lambda: str(uuid.uuid4().int)[:10])
    user_id: str = ""
    train_number: str = ""
    from_station: str = ""
    to_station: str = ""
    travel_date: date = None
    seat_class: SeatClass = SeatClass.SLEEPER
    passengers: list[Passenger] = field(default_factory=list)
    total_fare: float = 0.0
    booked_at: datetime = field(default_factory=datetime.now)

    @property
    def overall_status(self) -> BookingStatus:
        statuses = [p.status for p in self.passengers]
        if all(s == BookingStatus.CONFIRMED for s in statuses):
            return BookingStatus.CONFIRMED
        if all(s == BookingStatus.CANCELLED for s in statuses):
            return BookingStatus.CANCELLED
        if any(s == BookingStatus.WAITLISTED for s in statuses):
            return BookingStatus.WAITLISTED
        return BookingStatus.RAC


@dataclass
class Train:
    train_number: str
    name: str
    route: Route
    coaches: list[Coach] = field(default_factory=list)


class TrainBookingService:
    def __init__(self):
        self._trains: dict[str, Train] = {}
        self._quotas: dict[str, dict[SeatClass, ClassQuota]] = {}
        self._bookings: dict[str, Booking] = {}
        self._fare_calculator = FareCalculator()
        self._lock = threading.Lock()

    def add_train(self, train: Train) -> None:
        self._trains[train.train_number] = train
        quotas: dict[SeatClass, ClassQuota] = {}
        for coach in train.coaches:
            if coach.seat_class not in quotas:
                quotas[coach.seat_class] = ClassQuota(
                    coach.seat_class, list(coach.seats),
                    coach.rac_quota, coach.waitlist_quota,
                )
            else:
                existing = quotas[coach.seat_class]
                existing._available_seats.extend(coach.seats)
        self._quotas[train.train_number] = quotas

    def check_availability(self, train_number: str,
                            seat_class: SeatClass) -> dict[str, int]:
        quotas = self._quotas.get(train_number, {})
        quota = quotas.get(seat_class)
        if not quota:
            return {"available": 0, "rac": 0, "waitlist": 0}
        return {
            "available": quota.available_count,
            "rac": quota.rac_available,
            "waitlist": quota.waitlist_available,
        }

    def book(self, user_id: str, train_number: str,
             from_station: str, to_station: str,
             travel_date: date, seat_class: SeatClass,
             passengers: list[Passenger]) -> Optional[Booking]:
        train = self._trains.get(train_number)
        if not train:
            return None

        quotas = self._quotas.get(train_number, {})
        quota = quotas.get(seat_class)
        if not quota:
            return None

        allocated_passengers = []
        for passenger in passengers:
            status = quota.allocate(passenger)
            if status is None:
                for p in allocated_passengers:
                    quota.release(p)
                return None
            allocated_passengers.append(passenger)

        distance = train.route.get_distance(from_station, to_station)
        fare = self._fare_calculator.calculate(
            distance, seat_class, len(passengers)
        )

        booking = Booking(
            user_id=user_id,
            train_number=train_number,
            from_station=from_station,
            to_station=to_station,
            travel_date=travel_date,
            seat_class=seat_class,
            passengers=passengers,
            total_fare=fare,
        )
        self._bookings[booking.pnr] = booking
        return booking

    def cancel_booking(self, pnr: str) -> bool:
        booking = self._bookings.get(pnr)
        if not booking:
            return False

        quotas = self._quotas.get(booking.train_number, {})
        quota = quotas.get(booking.seat_class)
        if not quota:
            return False

        for passenger in booking.passengers:
            quota.release(passenger)

        return True

    def get_booking(self, pnr: str) -> Optional[Booking]:
        return self._bookings.get(pnr)
```

### Concurrency Handling

- **Per-class-quota locks** ensure atomic seat allocation — two bookings for different classes don't contend
- **All-or-nothing booking** for multi-passenger — if any passenger can't be allocated, all are rolled back
- **RAC → Confirmed promotion** happens atomically within the lock during cancellation, preventing race conditions
- **Waitlist → RAC promotion** cascades within the same lock acquisition

### Interview Tips (Adobe)

- **RAC and waitlist promotion is the tricky part** — walk through the cascade: cancellation → RAC passenger gets the seat → waitlisted passenger moves to RAC.
- **Draw the state diagram**: Waitlisted → RAC → Confirmed → Cancelled. Show all valid transitions.
- **Discuss the all-or-nothing booking** — a family of 4 should either all get seats or none should. This is a transaction problem.
- **Fare calculation as a Strategy** — different pricing for Tatkal, senior citizens, children shows extensibility.
- **Mention real IRCTC challenges**: tatkal booking stampede (flash sale concurrency), chart preparation (freezing allocations at a cutoff time).

---

## 16. Warehouse Management System (Adobe)

### Requirements

- Track inventory across multiple warehouse zones (receiving, storage, packing, shipping)
- Support product categorization with SKU management
- Implement pick, pack, and ship workflow for order fulfillment
- Real-time inventory tracking with stock level alerts
- Support multiple storage strategies (FIFO, LIFO, by expiry date)
- Generate picking lists optimized by zone location
- Handle returns and restocking
- Provide inventory reports and analytics

### Key Entities and Relationships

```
Warehouse ──divided into──▶ Zone* ──contains──▶ StorageLocation*
Product ──stored as──▶ InventoryItem* (at specific locations)
Order ──fulfilled by──▶ FulfillmentProcess (Pick → Pack → Ship)
PickList ──guides──▶ Picker to collect items
Shipment ──tracks──▶ shipped Order
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **State** | Order fulfillment states (Received → Picking → Packing → Shipped) |
| **Strategy** | Storage assignment and picking optimization |
| **Observer** | Low stock alerts, order status updates |
| **Template Method** | Fulfillment workflow (pick → validate → pack → label → ship) |
| **Command** | Inventory operations with audit trail |

### Core Class Structure

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import threading
import uuid
from collections import defaultdict


class ZoneType(Enum):
    RECEIVING = "receiving"
    STORAGE = "storage"
    PACKING = "packing"
    SHIPPING = "shipping"
    RETURNS = "returns"


class FulfillmentStatus(Enum):
    RECEIVED = "received"
    PICKING = "picking"
    PICKED = "picked"
    PACKING = "packing"
    PACKED = "packed"
    SHIPPING = "shipping"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    RETURNED = "returned"


@dataclass
class Product:
    sku: str
    name: str
    category: str
    weight_kg: float = 0.0
    dimensions: tuple[float, float, float] = (0, 0, 0)
    requires_cold_storage: bool = False
    min_stock_level: int = 10


@dataclass
class StorageLocation:
    location_id: str
    zone_type: ZoneType
    aisle: str
    rack: str
    shelf: str
    max_capacity: int = 100
    current_quantity: int = 0
    is_cold_storage: bool = False

    @property
    def available_space(self) -> int:
        return self.max_capacity - self.current_quantity

    @property
    def location_code(self) -> str:
        return f"{self.aisle}-{self.rack}-{self.shelf}"


@dataclass
class InventoryItem:
    item_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    product: Product = None
    location: StorageLocation = None
    quantity: int = 0
    received_at: datetime = field(default_factory=datetime.now)
    expiry_date: Optional[datetime] = None
    batch_number: str = ""

    @property
    def is_expired(self) -> bool:
        if self.expiry_date is None:
            return False
        return datetime.now() > self.expiry_date


@dataclass
class OrderItem:
    product: Product
    quantity: int
    picked_quantity: int = 0

    @property
    def is_fully_picked(self) -> bool:
        return self.picked_quantity >= self.quantity


@dataclass
class FulfillmentOrder:
    order_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    items: list[OrderItem] = field(default_factory=list)
    status: FulfillmentStatus = FulfillmentStatus.RECEIVED
    created_at: datetime = field(default_factory=datetime.now)
    picked_at: Optional[datetime] = None
    packed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    tracking_number: str = ""


@dataclass
class PickInstruction:
    location: StorageLocation
    product: Product
    quantity: int
    inventory_item: InventoryItem


class PickingStrategy(ABC):
    @abstractmethod
    def generate_pick_list(self, order: FulfillmentOrder,
                            inventory: dict[str, list[InventoryItem]]) -> list[PickInstruction]:
        pass


class FIFOPicking(PickingStrategy):
    def generate_pick_list(self, order: FulfillmentOrder,
                            inventory: dict[str, list[InventoryItem]]) -> list[PickInstruction]:
        instructions = []
        for item in order.items:
            remaining = item.quantity
            items_for_sku = sorted(
                inventory.get(item.product.sku, []),
                key=lambda i: i.received_at
            )
            for inv_item in items_for_sku:
                if remaining <= 0:
                    break
                if inv_item.quantity <= 0 or inv_item.is_expired:
                    continue
                pick_qty = min(remaining, inv_item.quantity)
                instructions.append(PickInstruction(
                    location=inv_item.location,
                    product=item.product,
                    quantity=pick_qty,
                    inventory_item=inv_item,
                ))
                remaining -= pick_qty
        return instructions


class ZoneOptimizedPicking(PickingStrategy):
    def generate_pick_list(self, order: FulfillmentOrder,
                            inventory: dict[str, list[InventoryItem]]) -> list[PickInstruction]:
        instructions = []
        for item in order.items:
            remaining = item.quantity
            items_for_sku = sorted(
                inventory.get(item.product.sku, []),
                key=lambda i: (i.location.aisle, i.location.rack, i.location.shelf)
            )
            for inv_item in items_for_sku:
                if remaining <= 0:
                    break
                if inv_item.quantity <= 0 or inv_item.is_expired:
                    continue
                pick_qty = min(remaining, inv_item.quantity)
                instructions.append(PickInstruction(
                    location=inv_item.location,
                    product=item.product,
                    quantity=pick_qty,
                    inventory_item=inv_item,
                ))
                remaining -= pick_qty

        instructions.sort(key=lambda i: i.location.location_code)
        return instructions


class StockAlertObserver(ABC):
    @abstractmethod
    def on_low_stock(self, product: Product, current_qty: int) -> None:
        pass


class WarehouseManagement:
    def __init__(self, picking_strategy: PickingStrategy = None):
        self._locations: dict[str, StorageLocation] = {}
        self._inventory: dict[str, list[InventoryItem]] = defaultdict(list)
        self._orders: dict[str, FulfillmentOrder] = {}
        self._picking = picking_strategy or FIFOPicking()
        self._stock_observers: list[StockAlertObserver] = []
        self._lock = threading.Lock()

    def add_location(self, location: StorageLocation) -> None:
        self._locations[location.location_id] = location

    def receive_stock(self, product: Product, quantity: int,
                       location_id: str, batch: str = "",
                       expiry: datetime = None) -> InventoryItem:
        location = self._locations.get(location_id)
        if not location or location.available_space < quantity:
            raise ValueError("Insufficient space or invalid location")

        item = InventoryItem(
            product=product,
            location=location,
            quantity=quantity,
            batch_number=batch,
            expiry_date=expiry,
        )

        with self._lock:
            self._inventory[product.sku].append(item)
            location.current_quantity += quantity

        return item

    def get_stock_level(self, sku: str) -> int:
        return sum(
            i.quantity for i in self._inventory.get(sku, [])
            if not i.is_expired
        )

    def create_order(self, items: list[OrderItem]) -> FulfillmentOrder:
        order = FulfillmentOrder(items=items)
        self._orders[order.order_id] = order
        return order

    def pick_order(self, order_id: str) -> list[PickInstruction]:
        order = self._orders.get(order_id)
        if not order or order.status != FulfillmentStatus.RECEIVED:
            return []

        order.status = FulfillmentStatus.PICKING
        pick_list = self._picking.generate_pick_list(order, self._inventory)

        with self._lock:
            for instruction in pick_list:
                instruction.inventory_item.quantity -= instruction.quantity
                instruction.location.current_quantity -= instruction.quantity

                for oi in order.items:
                    if oi.product.sku == instruction.product.sku:
                        oi.picked_quantity += instruction.quantity
                        break

                self._check_stock_alert(instruction.product)

        order.status = FulfillmentStatus.PICKED
        order.picked_at = datetime.now()
        return pick_list

    def pack_order(self, order_id: str) -> bool:
        order = self._orders.get(order_id)
        if not order or order.status != FulfillmentStatus.PICKED:
            return False
        if not all(item.is_fully_picked for item in order.items):
            return False
        order.status = FulfillmentStatus.PACKED
        order.packed_at = datetime.now()
        return True

    def ship_order(self, order_id: str, tracking: str) -> bool:
        order = self._orders.get(order_id)
        if not order or order.status != FulfillmentStatus.PACKED:
            return False
        order.status = FulfillmentStatus.SHIPPED
        order.shipped_at = datetime.now()
        order.tracking_number = tracking
        return True

    def process_return(self, order_id: str, sku: str,
                        quantity: int, location_id: str) -> bool:
        order = self._orders.get(order_id)
        if not order:
            return False

        product = next(
            (item.product for item in order.items if item.product.sku == sku),
            None
        )
        if not product:
            return False

        self.receive_stock(product, quantity, location_id)
        return True

    def add_stock_observer(self, observer: StockAlertObserver) -> None:
        self._stock_observers.append(observer)

    def _check_stock_alert(self, product: Product) -> None:
        current = self.get_stock_level(product.sku)
        if current <= product.min_stock_level:
            for observer in self._stock_observers:
                observer.on_low_stock(product, current)
```

### Concurrency Handling

- **System-level lock** for inventory mutations (receive, pick) — prevents overselling
- **Pick operations** decrement inventory atomically — two orders picking the same SKU are serialized
- **Stock alert checks** run inside the lock to ensure consistent stock readings
- For high-throughput warehouses, consider per-SKU locks or optimistic concurrency with version numbers

### Interview Tips (Adobe)

- **State machine for order fulfillment** is critical — draw the full lifecycle: Received → Picking → Picked → Packing → Packed → Shipping → Shipped → Delivered.
- **FIFO vs zone-optimized picking** — Adobe likes hearing about real-world trade-offs. FIFO ensures freshness (important for perishables), zone-optimized reduces picker walking distance.
- **Discuss inventory accuracy** — what happens if a picker finds less stock than expected? Handle partial picks gracefully.
- **Mention real warehouse concepts**: wave picking (batch multiple orders), zone picking (each picker handles one zone), and pick-to-light systems.
- **Low stock alerts** show Observer pattern mastery and operational awareness.

---

## 17. Task Scheduler (DAG-based) (Adobe)

### Requirements

- Define tasks with dependencies forming a Directed Acyclic Graph (DAG)
- Execute tasks respecting dependency order (topological sort)
- Support parallel execution of independent tasks
- Configurable retry policies per task with exponential backoff
- Multiple scheduling policies: immediate, scheduled, periodic
- Task monitoring with status, duration, and error tracking
- Detect circular dependencies before execution
- Support task cancellation and DAG-level abort

### Key Entities and Relationships

```
DAG ──contains──▶ TaskNode*
TaskNode ──depends on──▶ TaskNode* (edges)
DAGExecutor ──runs──▶ DAG using topological order
TaskNode ──has──▶ RetryPolicy, SchedulePolicy
ExecutionContext tracks runtime state
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **Command** | Tasks as executable command objects |
| **Observer** | Monitor task completion and failure |
| **Strategy** | Scheduling and retry policies |
| **Template Method** | Task lifecycle: setup → execute → teardown |
| **Iterator** | Topological traversal of the DAG |

### Core Class Structure

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional
import threading
import time
import uuid
from collections import deque
from concurrent.futures import ThreadPoolExecutor, Future


class TaskStatus(Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class TaskResult:
    success: bool
    output: str = ""
    error: str = ""
    duration_seconds: float = 0
    attempts: int = 0


class RetryPolicy:
    def __init__(self, max_retries: int = 3,
                 base_delay: float = 1.0, max_delay: float = 30.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    def get_delay(self, attempt: int) -> float:
        return min(self.base_delay * (2 ** attempt), self.max_delay)


class TaskNode:
    def __init__(self, task_id: str = None, name: str = "",
                 action: Callable[[], str] = None,
                 retry_policy: RetryPolicy = None):
        self.task_id = task_id or str(uuid.uuid4())[:8]
        self.name = name
        self.action = action
        self.retry_policy = retry_policy or RetryPolicy()
        self.dependencies: list["TaskNode"] = []
        self.status = TaskStatus.PENDING
        self.result: Optional[TaskResult] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

    def add_dependency(self, task: "TaskNode") -> None:
        self.dependencies.append(task)

    @property
    def is_ready(self) -> bool:
        return all(
            dep.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED)
            for dep in self.dependencies
        )

    def execute(self) -> TaskResult:
        self.started_at = datetime.now()
        self.status = TaskStatus.RUNNING

        for attempt in range(self.retry_policy.max_retries + 1):
            start = time.monotonic()
            try:
                output = self.action() if self.action else ""
                duration = time.monotonic() - start
                self.result = TaskResult(
                    success=True, output=str(output),
                    duration_seconds=duration, attempts=attempt + 1,
                )
                self.status = TaskStatus.COMPLETED
                self.completed_at = datetime.now()
                return self.result

            except Exception as e:
                duration = time.monotonic() - start
                if attempt < self.retry_policy.max_retries:
                    delay = self.retry_policy.get_delay(attempt)
                    time.sleep(delay)
                else:
                    self.result = TaskResult(
                        success=False, error=str(e),
                        duration_seconds=duration, attempts=attempt + 1,
                    )
                    self.status = TaskStatus.FAILED
                    self.completed_at = datetime.now()
                    return self.result


class DAGExecutionListener(ABC):
    @abstractmethod
    def on_task_started(self, task: TaskNode) -> None:
        pass

    @abstractmethod
    def on_task_completed(self, task: TaskNode) -> None:
        pass

    @abstractmethod
    def on_task_failed(self, task: TaskNode) -> None:
        pass

    @abstractmethod
    def on_dag_completed(self, dag: "DAG", success: bool) -> None:
        pass


class DAG:
    def __init__(self, dag_id: str = None, name: str = ""):
        self.dag_id = dag_id or str(uuid.uuid4())[:8]
        self.name = name
        self.tasks: dict[str, TaskNode] = {}

    def add_task(self, task: TaskNode) -> None:
        self.tasks[task.task_id] = task

    def add_edge(self, from_id: str, to_id: str) -> None:
        """from_id must complete before to_id can start."""
        from_task = self.tasks[from_id]
        to_task = self.tasks[to_id]
        to_task.add_dependency(from_task)

    def has_cycle(self) -> bool:
        visited, rec_stack = set(), set()

        def dfs(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)
            task = self.tasks[task_id]
            for dep in task.dependencies:
                if dep.task_id not in visited:
                    if dfs(dep.task_id):
                        return True
                elif dep.task_id in rec_stack:
                    return True
            rec_stack.discard(task_id)
            return False

        for tid in self.tasks:
            if tid not in visited:
                if dfs(tid):
                    return True
        return False

    def get_root_tasks(self) -> list[TaskNode]:
        return [t for t in self.tasks.values() if not t.dependencies]

    def topological_order(self) -> list[list[TaskNode]]:
        """Returns tasks in layers — each layer can execute in parallel."""
        in_degree: dict[str, int] = {
            tid: len(t.dependencies) for tid, t in self.tasks.items()
        }
        layers = []
        remaining = set(self.tasks.keys())

        while remaining:
            layer = [
                self.tasks[tid] for tid in remaining
                if in_degree[tid] == 0
            ]
            if not layer:
                raise ValueError("Cycle detected in DAG")
            layers.append(layer)
            for task in layer:
                remaining.discard(task.task_id)
                for tid in remaining:
                    other = self.tasks[tid]
                    if task in other.dependencies:
                        in_degree[tid] -= 1

        return layers


class DAGExecutor:
    def __init__(self, max_workers: int = 4,
                 fail_fast: bool = True):
        self.max_workers = max_workers
        self.fail_fast = fail_fast
        self._listeners: list[DAGExecutionListener] = []
        self._cancelled = threading.Event()

    def add_listener(self, listener: DAGExecutionListener) -> None:
        self._listeners.append(listener)

    def execute(self, dag: DAG) -> bool:
        if dag.has_cycle():
            raise ValueError("DAG contains a cycle")

        self._cancelled.clear()
        dag_success = True

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            layers = dag.topological_order()

            for layer in layers:
                if self._cancelled.is_set():
                    for task in layer:
                        task.status = TaskStatus.SKIPPED
                    continue

                futures: dict[Future, TaskNode] = {}
                for task in layer:
                    if task.status == TaskStatus.CANCELLED:
                        continue

                    any_dep_failed = any(
                        d.status == TaskStatus.FAILED for d in task.dependencies
                    )
                    if any_dep_failed:
                        task.status = TaskStatus.SKIPPED
                        continue

                    for listener in self._listeners:
                        listener.on_task_started(task)

                    future = pool.submit(task.execute)
                    futures[future] = task

                for future in futures:
                    task = futures[future]
                    try:
                        result = future.result()
                        if result.success:
                            for listener in self._listeners:
                                listener.on_task_completed(task)
                        else:
                            dag_success = False
                            for listener in self._listeners:
                                listener.on_task_failed(task)
                            if self.fail_fast:
                                self._cancelled.set()
                    except Exception:
                        dag_success = False
                        task.status = TaskStatus.FAILED
                        if self.fail_fast:
                            self._cancelled.set()

        for listener in self._listeners:
            listener.on_dag_completed(dag, dag_success)

        return dag_success

    def cancel(self) -> None:
        self._cancelled.set()
```

### Concurrency Handling

- **Layer-based parallel execution** — tasks within the same topological layer have no dependencies on each other and run concurrently via `ThreadPoolExecutor`
- **Fail-fast mode** uses a `threading.Event` to signal cancellation to remaining layers
- **Per-task retries** include backoff delays that don't block other tasks (each task runs in its own thread)
- **Task status** is only written by its executing thread, avoiding races

### Interview Tips (Adobe)

- **Draw the DAG first** — literally draw nodes and edges. Adobe likes visual thinking.
- **Explain topological sort clearly** — the layer-based approach (Kahn's algorithm) naturally identifies parallelizable groups.
- **Discuss fail-fast vs fail-safe** — should the entire DAG abort when one task fails? Or continue executing unaffected branches? Adobe values configurability.
- **Mention real-world parallels**: Apache Airflow, Luigi, Prefect. Show you know the production landscape.
- **Discuss monitoring** — how would you visualize DAG execution? Show task durations, dependencies, and bottlenecks.

---

## 18. Client-Side Rate Limiter (Adobe)

### Requirements

- Implement token bucket algorithm with configurable capacity and refill rate
- Queue requests that exceed the rate limit instead of rejecting them
- Support burst handling (allow short bursts above the steady-state rate)
- Implement exponential backoff for retries on server 429 responses
- Per-endpoint rate limiting (different limits for different APIs)
- Provide rate limit status (remaining tokens, next refill time)
- Thread-safe for use in multi-threaded HTTP clients
- Support graceful degradation when rate limited

### Key Entities and Relationships

```
RateLimiter ──uses──▶ TokenBucket (per endpoint)
RequestQueue ──holds──▶ pending requests
TokenBucket ──refills at──▶ configured rate
BackoffStrategy ──calculates──▶ retry delays
RateLimitedClient wraps HTTP client with rate limiting
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| **Strategy** | Different rate limiting algorithms (token bucket, sliding window) |
| **Decorator** | Wrap HTTP client with rate limiting behavior |
| **Observer** | Notify when rate limit is approaching |
| **Producer-Consumer** | Queued requests consumed at the allowed rate |

### Core Class Structure

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Optional, Any
import threading
import time
import math
from collections import defaultdict, deque
from concurrent.futures import Future
from enum import Enum


class RateLimitStatus(Enum):
    ALLOWED = "allowed"
    QUEUED = "queued"
    REJECTED = "rejected"


@dataclass
class RateLimitInfo:
    remaining_tokens: float
    max_tokens: float
    refill_rate: float  # tokens per second
    next_refill_at: float
    queue_size: int

    @property
    def utilization(self) -> float:
        return 1.0 - (self.remaining_tokens / self.max_tokens)


class TokenBucket:
    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self._tokens = capacity
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(
            self.capacity,
            self._tokens + elapsed * self.refill_rate
        )
        self._last_refill = now

    def try_acquire(self, tokens: float = 1.0) -> bool:
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def acquire_blocking(self, tokens: float = 1.0,
                          timeout: float = None) -> bool:
        deadline = time.monotonic() + timeout if timeout else None

        while True:
            with self._lock:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True
                wait_time = (tokens - self._tokens) / self.refill_rate

            if deadline:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                wait_time = min(wait_time, remaining)

            time.sleep(wait_time)

    def get_info(self) -> RateLimitInfo:
        with self._lock:
            self._refill()
            next_refill = (1.0 / self.refill_rate) if self.refill_rate > 0 else float('inf')
            return RateLimitInfo(
                remaining_tokens=self._tokens,
                max_tokens=self.capacity,
                refill_rate=self.refill_rate,
                next_refill_at=time.monotonic() + next_refill,
                queue_size=0,
            )


class SlidingWindowCounter:
    """Alternative algorithm using a sliding window of fixed intervals."""

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._current_count = 0
        self._previous_count = 0
        self._current_window_start = time.monotonic()
        self._lock = threading.Lock()

    def try_acquire(self) -> bool:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._current_window_start

            if elapsed >= self.window_seconds:
                windows_passed = int(elapsed / self.window_seconds)
                if windows_passed == 1:
                    self._previous_count = self._current_count
                else:
                    self._previous_count = 0
                self._current_count = 0
                self._current_window_start += windows_passed * self.window_seconds

            weight = 1.0 - ((now - self._current_window_start) / self.window_seconds)
            estimated = self._previous_count * weight + self._current_count

            if estimated < self.max_requests:
                self._current_count += 1
                return True
            return False


class BackoffStrategy(ABC):
    @abstractmethod
    def get_delay(self, attempt: int) -> float:
        pass


class ExponentialBackoff(BackoffStrategy):
    def __init__(self, base: float = 1.0, max_delay: float = 60.0,
                 jitter: bool = True):
        self._base = base
        self._max = max_delay
        self._jitter = jitter

    def get_delay(self, attempt: int) -> float:
        delay = min(self._base * (2 ** attempt), self._max)
        if self._jitter:
            import random
            delay = delay * (0.5 + random.random() * 0.5)
        return delay


class LinearBackoff(BackoffStrategy):
    def __init__(self, increment: float = 2.0, max_delay: float = 30.0):
        self._increment = increment
        self._max = max_delay

    def get_delay(self, attempt: int) -> float:
        return min(self._increment * (attempt + 1), self._max)


@dataclass
class QueuedRequest:
    request_fn: Callable[[], Any]
    future: Future
    enqueued_at: float = field(default_factory=time.monotonic)
    attempts: int = 0
    max_retries: int = 3


class RequestQueue:
    def __init__(self, max_size: int = 1000):
        self._queue: deque[QueuedRequest] = deque()
        self._max_size = max_size
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)

    def enqueue(self, request: QueuedRequest) -> bool:
        with self._not_empty:
            if len(self._queue) >= self._max_size:
                return False
            self._queue.append(request)
            self._not_empty.notify()
            return True

    def dequeue(self, timeout: float = 1.0) -> Optional[QueuedRequest]:
        with self._not_empty:
            if not self._queue:
                self._not_empty.wait(timeout=timeout)
            if self._queue:
                return self._queue.popleft()
            return None

    @property
    def size(self) -> int:
        return len(self._queue)


class RateLimitedClient:
    """Decorates an HTTP-like client with per-endpoint rate limiting."""

    def __init__(self, default_capacity: float = 10,
                 default_rate: float = 2.0,
                 backoff: BackoffStrategy = None,
                 queue_size: int = 100):
        self._buckets: dict[str, TokenBucket] = {}
        self._queues: dict[str, RequestQueue] = {}
        self._default_capacity = default_capacity
        self._default_rate = default_rate
        self._backoff = backoff or ExponentialBackoff()
        self._queue_size = queue_size
        self._workers: dict[str, threading.Thread] = {}
        self._running = True
        self._lock = threading.Lock()
        self._threshold_listeners: list[Callable[[str, RateLimitInfo], None]] = []

    def configure_endpoint(self, endpoint: str, capacity: float,
                            rate: float) -> None:
        self._buckets[endpoint] = TokenBucket(capacity, rate)

    def _get_bucket(self, endpoint: str) -> TokenBucket:
        if endpoint not in self._buckets:
            with self._lock:
                if endpoint not in self._buckets:
                    self._buckets[endpoint] = TokenBucket(
                        self._default_capacity, self._default_rate
                    )
        return self._buckets[endpoint]

    def _get_queue(self, endpoint: str) -> RequestQueue:
        if endpoint not in self._queues:
            with self._lock:
                if endpoint not in self._queues:
                    self._queues[endpoint] = RequestQueue(self._queue_size)
                    self._start_worker(endpoint)
        return self._queues[endpoint]

    def execute(self, endpoint: str,
                request_fn: Callable[[], Any],
                block: bool = True,
                timeout: float = 30.0) -> Any:
        bucket = self._get_bucket(endpoint)

        if bucket.try_acquire():
            self._check_threshold(endpoint)
            return request_fn()

        if block:
            if bucket.acquire_blocking(timeout=timeout):
                self._check_threshold(endpoint)
                return request_fn()
            raise TimeoutError(f"Rate limit timeout for {endpoint}")

        future = Future()
        queued = QueuedRequest(request_fn=request_fn, future=future)
        queue = self._get_queue(endpoint)
        if not queue.enqueue(queued):
            raise RuntimeError(f"Request queue full for {endpoint}")
        return future

    def _start_worker(self, endpoint: str) -> None:
        def worker():
            bucket = self._get_bucket(endpoint)
            queue = self._get_queue(endpoint)
            while self._running:
                request = queue.dequeue(timeout=1.0)
                if request is None:
                    continue
                bucket.acquire_blocking()
                try:
                    result = request.request_fn()
                    request.future.set_result(result)
                except Exception as e:
                    request.attempts += 1
                    if request.attempts < request.max_retries:
                        delay = self._backoff.get_delay(request.attempts)
                        time.sleep(delay)
                        queue.enqueue(request)
                    else:
                        request.future.set_exception(e)

        thread = threading.Thread(target=worker, daemon=True,
                                  name=f"RateLimiter-{endpoint}")
        thread.start()
        self._workers[endpoint] = thread

    def get_status(self, endpoint: str) -> RateLimitInfo:
        bucket = self._get_bucket(endpoint)
        info = bucket.get_info()
        queue = self._queues.get(endpoint)
        if queue:
            info.queue_size = queue.size
        return info

    def on_threshold(self, callback: Callable[[str, RateLimitInfo], None]) -> None:
        self._threshold_listeners.append(callback)

    def _check_threshold(self, endpoint: str) -> None:
        info = self.get_status(endpoint)
        if info.utilization > 0.8:
            for listener in self._threshold_listeners:
                listener(endpoint, info)

    def shutdown(self) -> None:
        self._running = False
        for thread in self._workers.values():
            thread.join(timeout=5.0)
```

### Concurrency Handling

- **Per-bucket locks** in `TokenBucket` allow different endpoints to be rate-limited independently
- **Blocking acquire** sleeps for the calculated refill time, avoiding busy-waiting
- **Per-endpoint worker threads** process queued requests at the allowed rate
- **Future-based async interface** lets callers choose between blocking and non-blocking modes
- **Jitter in backoff** prevents thundering herd when many requests hit the limit simultaneously

### Interview Tips (Adobe)

- **Start with the token bucket algorithm** — draw the bucket filling with tokens at a constant rate. Explain capacity (burst) vs rate (sustained throughput).
- **Compare token bucket vs sliding window** — token bucket is simpler and handles bursts naturally; sliding window gives more precise rate control.
- **Discuss the request queue** — Adobe's products make many API calls. Show how queuing prevents request loss.
- **Mention jitter** — without jitter, all rate-limited clients retry at the same time, causing another spike. This is a production insight that impresses interviewers.
- **Talk about per-endpoint configuration** — different APIs have different limits. Adobe Target might allow 100 req/s while Analytics allows 10 req/s.
- **Discuss 429 response handling** — parse `Retry-After` headers from the server and adjust the bucket accordingly.

---

## Summary: Pattern Frequency Across Companies

| Pattern | Microsoft | Amazon | Adobe |
|---------|-----------|--------|-------|
| **Strategy** | ●●●●● | ●●●●● | ●●●●● |
| **Observer** | ●●●● | ●●●●● | ●●●● |
| **State** | ●●● | ●●●● | ●●●● |
| **Command** | ●●● | ●●● | ●●● |
| **Factory** | ●● | ●●● | ●● |
| **Template Method** | ●● | ●● | ●●●● |
| **Chain of Responsibility** | ● | ●● | ●●●● |
| **Iterator** | ●●● | ● | ●● |
| **Builder** | ● | ●● | ●●● |
| **Composite** | ●●● | ● | ● |
| **Decorator** | ● | ● | ●●●● |
| **Proxy** | ●● | ●● | ●● |

### Key Takeaway

- **Microsoft** emphasizes data structures and algorithmic design within OOP (graphs, trees, state machines)
- **Amazon** focuses on scalability, concurrency, and operational resilience (retry, monitoring, idempotency)
- **Adobe** values extensibility, clean abstractions, and enterprise patterns (versioning, audit, rate limiting)

Tailor your preparation and vocabulary to the company. Use Microsoft's terms (dependency graph, constraint propagation), Amazon's terms (backpressure, idempotency, blast radius), or Adobe's terms (namespace, audit trail, configuration drift) as appropriate.
