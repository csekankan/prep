# LLD Standard Problems - Interview Ready Solutions

> 25 classic Low-Level Design interview problems with detailed design approach, class diagrams, and Python implementation guidance.

---

## Table of Contents

| # | Problem | Category | Key Patterns |
|---|---------|----------|--------------|
| 1 | ATM Machine | State Machine | State, Strategy |
| 2 | Parking Lot | Resource Allocation | Strategy, Factory |
| 3 | Vending Machine | State Machine | State, Chain of Responsibility |
| 4 | Tic-Tac-Toe | Game | Strategy, Observer |
| 5 | Snake and Ladder | Game | Template Method, Observer |
| 6 | Minesweeper | Game | Command, Observer |
| 7 | Chess Game | Game | Strategy, Command |
| 8 | 2048 Game | Game | Command, Memento |
| 9 | Splitwise | Financial | Strategy, Observer |
| 10 | Movie Ticket Booking | Booking | Strategy, Observer, Singleton |
| 11 | Restaurant Management | Management | Observer, Command, State |
| 12 | Hotel Management | Management | Strategy, State, Observer |
| 13 | Car Rental System | Rental | Strategy, State |
| 14 | StackOverflow | Social/Q&A | Observer, Strategy, Decorator |
| 15 | Twitter | Social Media | Observer, Strategy |
| 16 | Gmail | Communication | Observer, Command |
| 17 | LinkedIn | Social/Professional | Observer, Strategy |
| 18 | Amazon E-commerce | E-commerce | Strategy, Observer, Factory |
| 19 | Amazon Prime Video | Streaming | Strategy, Observer |
| 20 | Google Drive | Storage | Composite, Observer |
| 21 | Dropbox | Storage/Sync | Observer, Strategy |
| 22 | Google Maps | Navigation | Strategy, Graph Algorithms |
| 23 | Google Docs | Collaboration | CRDT, Observer |
| 24 | Zoom Video | Communication | Mediator, Observer |
| 25 | File System | OS/Storage | Composite, Iterator |

---

## Problem 1: ATM Machine

### Requirements

**Functional:**
- User inserts card and enters PIN for authentication
- Support transactions: Withdrawal, Deposit, Balance Inquiry, Transfer
- Dispense cash in optimal denominations
- Print receipt after transaction
- Handle card retention after 3 failed PIN attempts

**Non-Functional:**
- Thread-safe for concurrent access to shared resources
- Transaction atomicity (all-or-nothing)
- Audit logging for all operations
- Timeout for inactive sessions

### Entities and Relationships

```
ATM (has-a) -> CardReader, CashDispenser, Screen, Keypad, Printer
ATM (has-a) -> ATMState (current state)
Account (is-a) -> SavingsAccount, CheckingAccount
Transaction (is-a) -> Withdrawal, Deposit, BalanceInquiry, Transfer
Bank (has-many) -> Account
ATMState (is-a) -> IdleState, CardInsertedState, PinEnteredState, TransactionState
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| State | ATM transitions (Idle -> CardInserted -> PinEntered -> Transaction) |
| Strategy | Cash dispensing algorithms (greedy, minimum notes) |
| Chain of Responsibility | Transaction validation (balance check, limit check, fraud check) |
| Singleton | ATM instance per physical machine |

### Class Diagram (Text UML)

```
┌─────────────────────┐
│      ATMState       │ <<abstract>>
├─────────────────────┤
│+ insert_card()      │
│+ enter_pin()        │
│+ select_transaction()│
│+ execute()          │
│+ cancel()           │
└────────┬────────────┘
         │ implements
    ┌────┼────────────────┬──────────────────┐
    ▼    ▼                ▼                  ▼
┌────────┐ ┌──────────────┐ ┌────────────┐ ┌──────────────┐
│IdleState│ │CardInserted  │ │PinEntered  │ │Transaction   │
│         │ │State         │ │State       │ │State         │
└────────┘ └──────────────┘ └────────────┘ └──────────────┘

┌─────────────────────┐        ┌─────────────────────┐
│        ATM          │        │    CashDispenser     │
├─────────────────────┤        ├─────────────────────┤
│- state: ATMState    │◆──────▶│- denominations: dict │
│- card_reader        │        │+ dispense(amount)    │
│- cash_dispenser     │        │+ has_sufficient()    │
│- bank_service       │        └─────────────────────┘
├─────────────────────┤
│+ set_state(state)   │        ┌─────────────────────┐
│+ insert_card(card)  │        │     BankService      │
│+ enter_pin(pin)     │◆──────▶├─────────────────────┤
│+ select_transaction()│       │+ authenticate(card,pin)│
│+ execute_transaction()│      │+ get_balance(acct)   │
└─────────────────────┘        │+ debit(acct, amt)    │
                               │+ credit(acct, amt)   │
                               └─────────────────────┘
```

### Implementation

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from threading import Lock
import time
import uuid


class TransactionType(Enum):
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    BALANCE_INQUIRY = "balance_inquiry"
    TRANSFER = "transfer"


@dataclass
class Card:
    card_number: str
    account_id: str
    bank_code: str
    expiry_date: str


@dataclass
class Account:
    account_id: str
    holder_name: str
    balance: float
    pin_hash: str
    daily_limit: float = 10000.0
    withdrawn_today: float = 0.0


@dataclass
class TransactionRecord:
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str = ""
    transaction_type: TransactionType = TransactionType.BALANCE_INQUIRY
    amount: float = 0.0
    timestamp: float = field(default_factory=time.time)
    success: bool = False


class BankService:
    """Simulates bank backend service."""

    def __init__(self):
        self._accounts: Dict[str, Account] = {}
        self._lock = Lock()

    def add_account(self, account: Account):
        self._accounts[account.account_id] = account

    def authenticate(self, card: Card, pin: str) -> bool:
        account = self._accounts.get(card.account_id)
        if not account:
            return False
        return account.pin_hash == self._hash_pin(pin)

    def get_balance(self, account_id: str) -> float:
        account = self._accounts.get(account_id)
        return account.balance if account else 0.0

    def debit(self, account_id: str, amount: float) -> bool:
        with self._lock:
            account = self._accounts.get(account_id)
            if not account:
                return False
            if account.balance < amount:
                return False
            if account.withdrawn_today + amount > account.daily_limit:
                return False
            account.balance -= amount
            account.withdrawn_today += amount
            return True

    def credit(self, account_id: str, amount: float) -> bool:
        with self._lock:
            account = self._accounts.get(account_id)
            if not account:
                return False
            account.balance += amount
            return True

    @staticmethod
    def _hash_pin(pin: str) -> str:
        import hashlib
        return hashlib.sha256(pin.encode()).hexdigest()


class CashDispenser:
    """Manages physical cash denominations."""

    def __init__(self, denominations: Dict[int, int] = None):
        self._denominations = denominations or {
            2000: 50, 500: 100, 200: 200, 100: 500
        }
        self._lock = Lock()

    def has_sufficient_cash(self, amount: int) -> bool:
        return self._calculate_dispensing(amount) is not None

    def dispense(self, amount: int) -> Optional[Dict[int, int]]:
        with self._lock:
            notes = self._calculate_dispensing(amount)
            if notes is None:
                return None
            for denom, count in notes.items():
                self._denominations[denom] -= count
            return notes

    def _calculate_dispensing(self, amount: int) -> Optional[Dict[int, int]]:
        """Greedy algorithm for cash dispensing."""
        remaining = amount
        notes = {}
        for denom in sorted(self._denominations.keys(), reverse=True):
            if remaining <= 0:
                break
            available = self._denominations[denom]
            needed = min(remaining // denom, available)
            if needed > 0:
                notes[denom] = needed
                remaining -= denom * needed
        return notes if remaining == 0 else None

    @property
    def total_cash(self) -> int:
        return sum(d * c for d, c in self._denominations.items())


class ATMState(ABC):
    """Abstract state for the ATM state machine."""

    def __init__(self, atm: 'ATM'):
        self._atm = atm

    @abstractmethod
    def insert_card(self, card: Card) -> str:
        pass

    @abstractmethod
    def enter_pin(self, pin: str) -> str:
        pass

    @abstractmethod
    def select_transaction(self, txn_type: TransactionType) -> str:
        pass

    @abstractmethod
    def execute(self, amount: float = 0) -> str:
        pass

    def cancel(self) -> str:
        self._atm.eject_card()
        self._atm.set_state(IdleState(self._atm))
        return "Transaction cancelled. Card ejected."


class IdleState(ATMState):
    def insert_card(self, card: Card) -> str:
        self._atm.current_card = card
        self._atm.set_state(CardInsertedState(self._atm))
        return "Card accepted. Please enter your PIN."

    def enter_pin(self, pin: str) -> str:
        return "Please insert your card first."

    def select_transaction(self, txn_type: TransactionType) -> str:
        return "Please insert your card first."

    def execute(self, amount: float = 0) -> str:
        return "Please insert your card first."


class CardInsertedState(ATMState):
    def __init__(self, atm: 'ATM'):
        super().__init__(atm)
        self._attempts = 0
        self._max_attempts = 3

    def insert_card(self, card: Card) -> str:
        return "Card already inserted."

    def enter_pin(self, pin: str) -> str:
        if self._atm.bank_service.authenticate(self._atm.current_card, pin):
            self._atm.set_state(PinEnteredState(self._atm))
            return "PIN verified. Select transaction type."
        self._attempts += 1
        if self._attempts >= self._max_attempts:
            self._atm.retain_card()
            self._atm.set_state(IdleState(self._atm))
            return "Card retained due to too many failed attempts."
        return f"Incorrect PIN. {self._max_attempts - self._attempts} attempts remaining."

    def select_transaction(self, txn_type: TransactionType) -> str:
        return "Please enter your PIN first."

    def execute(self, amount: float = 0) -> str:
        return "Please enter your PIN first."


class PinEnteredState(ATMState):
    def insert_card(self, card: Card) -> str:
        return "Session active. Complete or cancel current transaction."

    def enter_pin(self, pin: str) -> str:
        return "PIN already verified."

    def select_transaction(self, txn_type: TransactionType) -> str:
        self._atm.current_transaction_type = txn_type
        self._atm.set_state(TransactionState(self._atm))
        if txn_type == TransactionType.BALANCE_INQUIRY:
            return self._atm.state.execute()
        return f"Selected: {txn_type.value}. Enter amount."

    def execute(self, amount: float = 0) -> str:
        return "Please select a transaction type first."


class TransactionState(ATMState):
    def insert_card(self, card: Card) -> str:
        return "Transaction in progress."

    def enter_pin(self, pin: str) -> str:
        return "Transaction in progress."

    def select_transaction(self, txn_type: TransactionType) -> str:
        return "Transaction in progress. Cancel first to change."

    def execute(self, amount: float = 0) -> str:
        card = self._atm.current_card
        txn_type = self._atm.current_transaction_type
        account_id = card.account_id
        record = TransactionRecord(
            account_id=account_id,
            transaction_type=txn_type,
            amount=amount
        )

        result = ""
        if txn_type == TransactionType.BALANCE_INQUIRY:
            balance = self._atm.bank_service.get_balance(account_id)
            result = f"Current balance: ${balance:.2f}"
            record.success = True

        elif txn_type == TransactionType.WITHDRAWAL:
            int_amount = int(amount)
            if not self._atm.cash_dispenser.has_sufficient_cash(int_amount):
                result = "ATM has insufficient cash."
            elif self._atm.bank_service.debit(account_id, amount):
                notes = self._atm.cash_dispenser.dispense(int_amount)
                result = f"Dispensed ${amount:.2f}. Notes: {notes}"
                record.success = True
            else:
                result = "Insufficient funds or daily limit exceeded."

        elif txn_type == TransactionType.DEPOSIT:
            if self._atm.bank_service.credit(account_id, amount):
                result = f"Deposited ${amount:.2f} successfully."
                record.success = True
            else:
                result = "Deposit failed."

        self._atm.log_transaction(record)
        self._atm.set_state(PinEnteredState(self._atm))
        return result + "\n\nSelect another transaction or cancel."


class ATM:
    """Main ATM controller orchestrating all components."""

    def __init__(self, atm_id: str, bank_service: BankService,
                 cash_dispenser: CashDispenser):
        self.atm_id = atm_id
        self.bank_service = bank_service
        self.cash_dispenser = cash_dispenser
        self.state: ATMState = IdleState(self)
        self.current_card: Optional[Card] = None
        self.current_transaction_type: Optional[TransactionType] = None
        self._transaction_log: List[TransactionRecord] = []
        self._lock = Lock()

    def set_state(self, state: ATMState):
        self.state = state

    def insert_card(self, card: Card) -> str:
        return self.state.insert_card(card)

    def enter_pin(self, pin: str) -> str:
        return self.state.enter_pin(pin)

    def select_transaction(self, txn_type: TransactionType) -> str:
        return self.state.select_transaction(txn_type)

    def execute(self, amount: float = 0) -> str:
        return self.state.execute(amount)

    def cancel(self) -> str:
        return self.state.cancel()

    def eject_card(self):
        self.current_card = None
        self.current_transaction_type = None

    def retain_card(self):
        print(f"[ALERT] Card {self.current_card.card_number} retained.")
        self.current_card = None

    def log_transaction(self, record: TransactionRecord):
        self._transaction_log.append(record)
```

### Concurrency Considerations

- **Lock on CashDispenser**: Multiple ATMs in a branch share cash; lock during dispensing
- **Bank service transactions**: Use database-level locks or optimistic locking for account balance updates
- **Session timeout**: Background thread monitors inactive sessions and resets state
- **Card reader mutex**: Only one card operation at a time

### Extension Points

- Add support for contactless/NFC cards
- Multi-language screen support (Strategy pattern for language)
- Integration with multiple bank networks
- Fraud detection chain (Chain of Responsibility)
- Denomination preference (let user choose note types)

### Interview Tips

- Start by identifying states and transitions — draw the state diagram first
- Mention that real ATMs use HSM (Hardware Security Module) for PIN encryption
- Discuss idempotency for network failures during transactions
- Mention compensating transactions for partial failures

---

## Problem 2: Parking Lot

### Requirements

**Functional:**
- Multiple floors with different spot sizes (Compact, Regular, Large)
- Support vehicle types: Motorcycle, Car, Bus, Truck
- Assign nearest available spot based on vehicle type
- Track entry/exit times for billing
- Multiple entry/exit points
- Display available spots per floor

**Non-Functional:**
- Handle concurrent entry/exit (thread safety)
- Scalable to thousands of spots
- Real-time availability updates

### Entities and Relationships

```
ParkingLot (has-many) -> ParkingFloor
ParkingFloor (has-many) -> ParkingSpot
ParkingSpot (is-a) -> CompactSpot, RegularSpot, LargeSpot
Vehicle (is-a) -> Motorcycle, Car, Bus, Truck
ParkingTicket (has-a) -> Vehicle, ParkingSpot
Payment (has-a) -> ParkingTicket
ParkingLot (has-many) -> EntryPanel, ExitPanel
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| Strategy | Spot allocation (nearest, first-available, load-balanced) |
| Factory | Vehicle and Spot creation |
| Singleton | ParkingLot instance |
| Observer | Display boards update on availability change |

### Class Diagram (Text UML)

```
┌──────────────────┐       ┌──────────────────┐
│   ParkingLot     │       │  ParkingFloor    │
├──────────────────┤       ├──────────────────┤
│- floors: List    │◆─────▶│- spots: List     │
│- entry_panels    │       │- floor_number    │
│- exit_panels     │       │+ get_free_spot() │
│- allocation_strat│       │+ available_count()│
├──────────────────┤       └──────────────────┘
│+ park_vehicle()  │
│+ unpark_vehicle()│       ┌──────────────────┐
│+ get_availability│       │   ParkingSpot    │
└──────────────────┘       ├──────────────────┤
                           │- spot_id         │
┌──────────────────┐       │- spot_type       │
│    Vehicle       │       │- is_occupied     │
├──────────────────┤       │- vehicle: Vehicle│
│- license_plate   │       │+ assign(vehicle) │
│- vehicle_type    │       │+ release()       │
└──────┬───────────┘       └──────────────────┘
       │ is-a
  ┌────┼────┬────┐
  ▼    ▼    ▼    ▼
 Moto  Car  Bus  Truck
```

### Implementation

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from threading import Lock, RLock
from datetime import datetime
import uuid


class VehicleType(Enum):
    MOTORCYCLE = 1
    CAR = 2
    BUS = 3
    TRUCK = 4


class SpotType(Enum):
    COMPACT = 1
    REGULAR = 2
    LARGE = 3


VEHICLE_TO_SPOT = {
    VehicleType.MOTORCYCLE: [SpotType.COMPACT, SpotType.REGULAR, SpotType.LARGE],
    VehicleType.CAR: [SpotType.REGULAR, SpotType.LARGE],
    VehicleType.BUS: [SpotType.LARGE],
    VehicleType.TRUCK: [SpotType.LARGE],
}


@dataclass
class Vehicle:
    license_plate: str
    vehicle_type: VehicleType


@dataclass
class ParkingSpot:
    spot_id: str
    spot_type: SpotType
    floor_number: int
    row: int
    column: int
    is_occupied: bool = False
    vehicle: Optional[Vehicle] = None
    _lock: Lock = field(default_factory=Lock, repr=False)

    def assign(self, vehicle: Vehicle) -> bool:
        with self._lock:
            if self.is_occupied:
                return False
            self.is_occupied = True
            self.vehicle = vehicle
            return True

    def release(self) -> Optional[Vehicle]:
        with self._lock:
            vehicle = self.vehicle
            self.is_occupied = False
            self.vehicle = None
            return vehicle

    def can_fit(self, vehicle_type: VehicleType) -> bool:
        return self.spot_type in VEHICLE_TO_SPOT.get(vehicle_type, [])


class ParkingFloor:
    def __init__(self, floor_number: int, spots: List[ParkingSpot]):
        self.floor_number = floor_number
        self.spots = spots
        self._spots_by_type: Dict[SpotType, List[ParkingSpot]] = {}
        for spot in spots:
            self._spots_by_type.setdefault(spot.spot_type, []).append(spot)

    def get_available_spot(self, vehicle_type: VehicleType) -> Optional[ParkingSpot]:
        compatible_types = VEHICLE_TO_SPOT.get(vehicle_type, [])
        for spot_type in compatible_types:
            for spot in self._spots_by_type.get(spot_type, []):
                if not spot.is_occupied:
                    return spot
        return None

    def available_count(self, spot_type: SpotType = None) -> int:
        if spot_type:
            return sum(1 for s in self._spots_by_type.get(spot_type, [])
                       if not s.is_occupied)
        return sum(1 for s in self.spots if not s.is_occupied)


@dataclass
class ParkingTicket:
    ticket_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    vehicle: Vehicle = None
    spot: ParkingSpot = None
    entry_time: datetime = field(default_factory=datetime.now)
    exit_time: Optional[datetime] = None
    amount_paid: float = 0.0
    is_paid: bool = False


class PricingStrategy(ABC):
    @abstractmethod
    def calculate(self, ticket: ParkingTicket) -> float:
        pass


class HourlyPricing(PricingStrategy):
    RATES = {
        SpotType.COMPACT: 10.0,
        SpotType.REGULAR: 20.0,
        SpotType.LARGE: 30.0,
    }

    def calculate(self, ticket: ParkingTicket) -> float:
        exit_time = ticket.exit_time or datetime.now()
        hours = (exit_time - ticket.entry_time).total_seconds() / 3600
        hours = max(1.0, hours)  # minimum 1 hour
        rate = self.RATES.get(ticket.spot.spot_type, 20.0)
        return round(hours * rate, 2)


class AllocationStrategy(ABC):
    @abstractmethod
    def find_spot(self, floors: List[ParkingFloor],
                  vehicle: Vehicle) -> Optional[ParkingSpot]:
        pass


class NearestSpotStrategy(AllocationStrategy):
    """Allocate the nearest available spot (lowest floor, lowest index)."""

    def find_spot(self, floors: List[ParkingFloor],
                  vehicle: Vehicle) -> Optional[ParkingSpot]:
        for floor in sorted(floors, key=lambda f: f.floor_number):
            spot = floor.get_available_spot(vehicle.vehicle_type)
            if spot:
                return spot
        return None


class SpreadEvenlyStrategy(AllocationStrategy):
    """Distribute vehicles evenly across floors."""

    def find_spot(self, floors: List[ParkingFloor],
                  vehicle: Vehicle) -> Optional[ParkingSpot]:
        best_floor = max(floors, key=lambda f: f.available_count())
        return best_floor.get_available_spot(vehicle.vehicle_type)


class ParkingLot:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self, name: str = "Main Lot"):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.name = name
        self.floors: List[ParkingFloor] = []
        self.active_tickets: Dict[str, ParkingTicket] = {}  # license -> ticket
        self.allocation_strategy: AllocationStrategy = NearestSpotStrategy()
        self.pricing_strategy: PricingStrategy = HourlyPricing()
        self._lock = RLock()

    def add_floor(self, floor: ParkingFloor):
        self.floors.append(floor)

    def park_vehicle(self, vehicle: Vehicle) -> Optional[ParkingTicket]:
        with self._lock:
            if vehicle.license_plate in self.active_tickets:
                return None  # already parked

            spot = self.allocation_strategy.find_spot(self.floors, vehicle)
            if spot is None:
                return None  # lot full for this vehicle type

            if not spot.assign(vehicle):
                return None  # race condition fallback

            ticket = ParkingTicket(vehicle=vehicle, spot=spot)
            self.active_tickets[vehicle.license_plate] = ticket
            return ticket

    def unpark_vehicle(self, license_plate: str) -> Optional[ParkingTicket]:
        with self._lock:
            ticket = self.active_tickets.get(license_plate)
            if not ticket:
                return None
            ticket.exit_time = datetime.now()
            ticket.amount_paid = self.pricing_strategy.calculate(ticket)
            ticket.spot.release()
            del self.active_tickets[license_plate]
            return ticket

    def get_availability(self) -> Dict[int, Dict[str, int]]:
        result = {}
        for floor in self.floors:
            result[floor.floor_number] = {
                st.name: floor.available_count(st) for st in SpotType
            }
        return result

    @classmethod
    def reset(cls):
        """For testing - reset singleton."""
        cls._instance = None


class DisplayBoard:
    """Observer that shows real-time availability."""

    def __init__(self, parking_lot: ParkingLot):
        self._lot = parking_lot

    def show(self) -> str:
        availability = self._lot.get_availability()
        lines = [f"=== {self._lot.name} Availability ==="]
        for floor_num, spots in availability.items():
            lines.append(f"Floor {floor_num}: {spots}")
        return "\n".join(lines)


def create_sample_lot() -> ParkingLot:
    """Factory function to create a sample parking lot."""
    ParkingLot.reset()
    lot = ParkingLot("City Center Parking")

    for floor_num in range(1, 4):
        spots = []
        spot_idx = 0
        for row in range(5):
            for col in range(10):
                if col < 2:
                    spot_type = SpotType.COMPACT
                elif col < 8:
                    spot_type = SpotType.REGULAR
                else:
                    spot_type = SpotType.LARGE
                spots.append(ParkingSpot(
                    spot_id=f"F{floor_num}-R{row}-C{col}",
                    spot_type=spot_type,
                    floor_number=floor_num,
                    row=row, column=col
                ))
                spot_idx += 1
        lot.add_floor(ParkingFloor(floor_num, spots))

    return lot
```

### Concurrency Considerations

- **Spot-level locking**: Each spot has its own lock to allow parallel parking on different spots
- **Re-entrant lock on ParkingLot**: Prevents double-parking of same vehicle
- **Atomic spot assignment**: Check-and-assign in single locked operation
- **Read-write lock for display**: Multiple readers for availability, exclusive writes

### Extension Points

- Add EV charging spots with reserved allocation
- Valet parking mode (special queue-based allocation)
- Subscription/membership pricing
- License plate recognition (auto entry/exit)
- Dynamic pricing based on occupancy

### Interview Tips

- Always clarify: single vs multi-floor, vehicle types supported, pricing model
- Start with the spot allocation strategy — it's the core algorithm
- Mention that real systems use database transactions, not in-memory locks
- Discuss how to handle power failures (persistent ticket storage)

---

## Problem 3: Vending Machine

### Requirements

**Functional:**
- Display available products with prices
- Accept multiple payment methods (coin, note, card)
- Dispense product after payment
- Return change
- Handle out-of-stock scenarios
- Admin: refill products, collect cash

**Non-Functional:**
- State machine integrity (no invalid transitions)
- Accurate change calculation
- Audit trail for all transactions

### Entities and Relationships

```
VendingMachine (has-a) -> VendingState, Inventory, PaymentProcessor
Inventory (has-many) -> Slot -> Product
VendingState (is-a) -> IdleState, ProductSelectedState, PaymentState, DispenseState
Payment (is-a) -> CoinPayment, NotePayment, CardPayment
```

### Design Patterns

| Pattern | Usage |
|---------|-------|
| State | Machine states (Idle, Selected, Payment, Dispense) |
| Strategy | Payment processing methods |
| Observer | Notify admin on low stock |

### Implementation

```python
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from threading import Lock


class MachineState(Enum):
    IDLE = auto()
    PRODUCT_SELECTED = auto()
    PAYMENT_PENDING = auto()
    DISPENSING = auto()
    OUT_OF_SERVICE = auto()


@dataclass
class Product:
    product_id: str
    name: str
    price: float
    category: str = "general"


@dataclass
class Slot:
    slot_id: str
    product: Optional[Product] = None
    quantity: int = 0
    max_capacity: int = 10

    def is_available(self) -> bool:
        return self.product is not None and self.quantity > 0

    def dispense_one(self) -> Optional[Product]:
        if self.quantity > 0:
            self.quantity -= 1
            return self.product
        return None

    def refill(self, quantity: int):
        self.quantity = min(self.quantity + quantity, self.max_capacity)


class Inventory:
    def __init__(self):
        self._slots: Dict[str, Slot] = {}
        self._lock = Lock()

    def add_slot(self, slot: Slot):
        self._slots[slot.slot_id] = slot

    def get_slot(self, slot_id: str) -> Optional[Slot]:
        return self._slots.get(slot_id)

    def get_available_products(self) -> List[Tuple[str, Product, int]]:
        return [
            (sid, slot.product, slot.quantity)
            for sid, slot in self._slots.items()
            if slot.is_available()
        ]

    def dispense(self, slot_id: str) -> Optional[Product]:
        with self._lock:
            slot = self._slots.get(slot_id)
            if slot and slot.is_available():
                return slot.dispense_one()
            return None


class PaymentMethod(ABC):
    @abstractmethod
    def pay(self, amount: float) -> bool:
        pass

    @abstractmethod
    def refund(self, amount: float) -> bool:
        pass


class CoinPayment(PaymentMethod):
    VALID_COINS = {0.25, 0.50, 1.0, 2.0, 5.0}

    def __init__(self):
        self._inserted: float = 0.0

    def insert_coin(self, value: float) -> bool:
        if value in self.VALID_COINS:
            self._inserted += value
            return True
        return False

    @property
    def amount_inserted(self) -> float:
        return self._inserted

    def pay(self, amount: float) -> bool:
        return self._inserted >= amount

    def refund(self, amount: float) -> bool:
        self._inserted = 0.0
        return True

    def get_change(self, price: float) -> float:
        change = self._inserted - price
        self._inserted = 0.0
        return max(0, change)


class CardPayment(PaymentMethod):
    def __init__(self, card_number: str):
        self._card_number = card_number
        self._charged = 0.0

    def pay(self, amount: float) -> bool:
        # Simulate card charge
        self._charged = amount
        return True

    def refund(self, amount: float) -> bool:
        self._charged = 0.0
        return True


class VendingState(ABC):
    def __init__(self, machine: 'VendingMachine'):
        self._machine = machine

    @abstractmethod
    def select_product(self, slot_id: str) -> str:
        pass

    @abstractmethod
    def insert_money(self, amount: float) -> str:
        pass

    @abstractmethod
    def dispense(self) -> str:
        pass

    def cancel(self) -> str:
        self._machine.refund_payment()
        self._machine.set_state(IdleVendingState(self._machine))
        return "Cancelled. Money returned."


class IdleVendingState(VendingState):
    def select_product(self, slot_id: str) -> str:
        slot = self._machine.inventory.get_slot(slot_id)
        if not slot or not slot.is_available():
            return f"Product in slot {slot_id} is unavailable."
        self._machine.selected_slot = slot_id
        self._machine.set_state(ProductSelectedVendingState(self._machine))
        return f"Selected: {slot.product.name} (${slot.product.price:.2f}). Insert payment."

    def insert_money(self, amount: float) -> str:
        return "Please select a product first."

    def dispense(self) -> str:
        return "Please select a product first."


class ProductSelectedVendingState(VendingState):
    def select_product(self, slot_id: str) -> str:
        slot = self._machine.inventory.get_slot(slot_id)
        if slot and slot.is_available():
            self._machine.selected_slot = slot_id
            return f"Changed selection to: {slot.product.name}"
        return "Product unavailable."

    def insert_money(self, amount: float) -> str:
        self._machine.payment_handler.insert_coin(amount)
        inserted = self._machine.payment_handler.amount_inserted
        slot = self._machine.inventory.get_slot(self._machine.selected_slot)
        price = slot.product.price

        if inserted >= price:
            self._machine.set_state(DispensingVendingState(self._machine))
            return self._machine.state.dispense()
        return f"Inserted: ${inserted:.2f}. Remaining: ${price - inserted:.2f}"

    def dispense(self) -> str:
        return "Please complete payment first."


class DispensingVendingState(VendingState):
    def select_product(self, slot_id: str) -> str:
        return "Dispensing in progress..."

    def insert_money(self, amount: float) -> str:
        return "Dispensing in progress..."

    def dispense(self) -> str:
        slot = self._machine.inventory.get_slot(self._machine.selected_slot)
        product = self._machine.inventory.dispense(self._machine.selected_slot)
        if product:
            change = self._machine.payment_handler.get_change(slot.product.price)
            self._machine.set_state(IdleVendingState(self._machine))
            msg = f"Dispensed: {product.name}."
            if change > 0:
                msg += f" Change: ${change:.2f}"
            return msg
        self._machine.refund_payment()
        self._machine.set_state(IdleVendingState(self._machine))
        return "Dispense failed. Full refund issued."


class VendingMachine:
    def __init__(self, machine_id: str):
        self.machine_id = machine_id
        self.inventory = Inventory()
        self.payment_handler = CoinPayment()
        self.state: VendingState = IdleVendingState(self)
        self.selected_slot: Optional[str] = None
        self._cash_collected: float = 0.0
        self._lock = Lock()

    def set_state(self, state: VendingState):
        self.state = state

    def select_product(self, slot_id: str) -> str:
        return self.state.select_product(slot_id)

    def insert_money(self, amount: float) -> str:
        return self.state.insert_money(amount)

    def dispense(self) -> str:
        return self.state.dispense()

    def cancel(self) -> str:
        return self.state.cancel()

    def refund_payment(self):
        if hasattr(self.payment_handler, 'amount_inserted'):
            refund = self.payment_handler.amount_inserted
            self.payment_handler.refund(refund)

    def admin_refill(self, slot_id: str, quantity: int):
        slot = self.inventory.get_slot(slot_id)
        if slot:
            slot.refill(quantity)

    def admin_collect_cash(self) -> float:
        collected = self._cash_collected
        self._cash_collected = 0.0
        return collected

    def display_products(self) -> str:
        products = self.inventory.get_available_products()
        lines = ["=== Available Products ==="]
        for slot_id, product, qty in products:
            lines.append(f"[{slot_id}] {product.name} - ${product.price:.2f} ({qty} left)")
        return "\n".join(lines)
```

### Concurrency Considerations

- **Inventory lock**: Prevent two buyers from getting the last item simultaneously
- **State integrity**: Transitions are atomic — no partial state changes
- **Payment timeout**: Auto-cancel and refund after inactivity period

### Extension Points

- Multiple payment methods simultaneously (partial coin + card)
- Loyalty/rewards integration
- Remote monitoring dashboard
- Temperature-controlled slots for beverages
- Combo deals (buy 2, get discount)

### Interview Tips

- Draw the state diagram first — it's the backbone of the design
- Clarify how change is returned (what denominations are available)
- Discuss what happens if the machine can't make exact change
- Mention how inventory is synced with a central system in reality

---

## Problem 4: Tic-Tac-Toe

### Requirements

**Functional:**
- 3x3 board (extensible to NxN)
- Two players (Human vs Human, Human vs AI)
- Win detection (row, column, diagonal)
- Draw detection
- Player turn management
- Undo move support

**Non-Functional:**
- O(1) win checking per move
- Extensible AI strategies (Easy, Medium, Hard)
- Clean separation of game logic from UI

### Design Patterns

| Pattern | Usage |
|---------|-------|
| Strategy | AI difficulty levels (Random, Minimax, Alpha-Beta) |
| Observer | UI updates on board change |
| Command | Move execution with undo support |
| Template Method | Game flow (init -> play -> check_winner -> end) |

### Implementation

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, List, Tuple
from dataclasses import dataclass
import random
import copy


class Symbol(Enum):
    EMPTY = "."
    X = "X"
    O = "O"


@dataclass
class Move:
    row: int
    col: int
    symbol: Symbol


class Player:
    def __init__(self, name: str, symbol: Symbol):
        self.name = name
        self.symbol = symbol
        self.wins = 0

    def __str__(self):
        return f"{self.name}({self.symbol.value})"


class Board:
    def __init__(self, size: int = 3):
        self.size = size
        self.grid = [[Symbol.EMPTY] * size for _ in range(size)]
        self._move_count = 0
        self._row_counts = [[0, 0] for _ in range(size)]  # [X_count, O_count]
        self._col_counts = [[0, 0] for _ in range(size)]
        self._diag_counts = [[0, 0], [0, 0]]  # main, anti

    def place(self, move: Move) -> bool:
        if not self._is_valid(move.row, move.col):
            return False
        if self.grid[move.row][move.col] != Symbol.EMPTY:
            return False

        self.grid[move.row][move.col] = move.symbol
        self._move_count += 1
        idx = 0 if move.symbol == Symbol.X else 1
        self._row_counts[move.row][idx] += 1
        self._col_counts[move.col][idx] += 1
        if move.row == move.col:
            self._diag_counts[0][idx] += 1
        if move.row + move.col == self.size - 1:
            self._diag_counts[1][idx] += 1
        return True

    def undo(self, move: Move):
        self.grid[move.row][move.col] = Symbol.EMPTY
        self._move_count -= 1
        idx = 0 if move.symbol == Symbol.X else 1
        self._row_counts[move.row][idx] -= 1
        self._col_counts[move.col][idx] -= 1
        if move.row == move.col:
            self._diag_counts[0][idx] -= 1
        if move.row + move.col == self.size - 1:
            self._diag_counts[1][idx] -= 1

    def check_winner(self, move: Move) -> bool:
        """O(1) win detection using running counts."""
        idx = 0 if move.symbol == Symbol.X else 1
        if self._row_counts[move.row][idx] == self.size:
            return True
        if self._col_counts[move.col][idx] == self.size:
            return True
        if move.row == move.col and self._diag_counts[0][idx] == self.size:
            return True
        if (move.row + move.col == self.size - 1 and
                self._diag_counts[1][idx] == self.size):
            return True
        return False

    def is_full(self) -> bool:
        return self._move_count == self.size * self.size

    def get_empty_cells(self) -> List[Tuple[int, int]]:
        return [(r, c) for r in range(self.size) for c in range(self.size)
                if self.grid[r][c] == Symbol.EMPTY]

    def _is_valid(self, row: int, col: int) -> bool:
        return 0 <= row < self.size and 0 <= col < self.size

    def display(self) -> str:
        lines = []
        for row in self.grid:
            lines.append(" | ".join(s.value for s in row))
            lines.append("-" * (self.size * 4 - 3))
        return "\n".join(lines[:-1])


class AIStrategy(ABC):
    @abstractmethod
    def get_move(self, board: Board, symbol: Symbol) -> Tuple[int, int]:
        pass


class RandomStrategy(AIStrategy):
    def get_move(self, board: Board, symbol: Symbol) -> Tuple[int, int]:
        empty = board.get_empty_cells()
        return random.choice(empty)


class MinimaxStrategy(AIStrategy):
    """Unbeatable AI using minimax with alpha-beta pruning."""

    def __init__(self, max_depth: int = 9):
        self._max_depth = max_depth

    def get_move(self, board: Board, symbol: Symbol) -> Tuple[int, int]:
        opponent = Symbol.O if symbol == Symbol.X else Symbol.X
        best_score = float('-inf')
        best_move = None

        for row, col in board.get_empty_cells():
            move = Move(row, col, symbol)
            board.place(move)
            if board.check_winner(move):
                score = 100
            else:
                score = self._minimax(board, opponent, symbol, False, 0,
                                      float('-inf'), float('inf'))
            board.undo(move)
            if score > best_score:
                best_score = score
                best_move = (row, col)

        return best_move

    def _minimax(self, board: Board, current: Symbol, ai_symbol: Symbol,
                 is_maximizing: bool, depth: int,
                 alpha: float, beta: float) -> int:
        if depth >= self._max_depth or board.is_full():
            return 0

        opponent = Symbol.O if current == Symbol.X else Symbol.X
        best = float('-inf') if is_maximizing else float('inf')

        for row, col in board.get_empty_cells():
            move = Move(row, col, current)
            board.place(move)
            if board.check_winner(move):
                score = (100 - depth) if current == ai_symbol else -(100 - depth)
                board.undo(move)
                return score

            score = self._minimax(board, opponent, ai_symbol,
                                  not is_maximizing, depth + 1, alpha, beta)
            board.undo(move)

            if is_maximizing:
                best = max(best, score)
                alpha = max(alpha, score)
            else:
                best = min(best, score)
                beta = min(beta, score)
            if beta <= alpha:
                break

        return best


class MediumStrategy(AIStrategy):
    """Mix of random and smart moves."""

    def __init__(self):
        self._random = RandomStrategy()
        self._minimax = MinimaxStrategy()

    def get_move(self, board: Board, symbol: Symbol) -> Tuple[int, int]:
        if random.random() < 0.4:
            return self._random.get_move(board, symbol)
        return self._minimax.get_move(board, symbol)


class AIPlayer(Player):
    def __init__(self, name: str, symbol: Symbol, strategy: AIStrategy):
        super().__init__(name, symbol)
        self.strategy = strategy

    def get_move(self, board: Board) -> Tuple[int, int]:
        return self.strategy.get_move(board, self.symbol)


class TicTacToeGame:
    def __init__(self, player1: Player, player2: Player, board_size: int = 3):
        self.board = Board(board_size)
        self.players = [player1, player2]
        self.current_player_idx = 0
        self.move_history: List[Move] = []
        self.is_over = False
        self.winner: Optional[Player] = None

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_idx]

    def make_move(self, row: int, col: int) -> str:
        if self.is_over:
            return "Game is over."

        move = Move(row, col, self.current_player.symbol)
        if not self.board.place(move):
            return "Invalid move."

        self.move_history.append(move)

        if self.board.check_winner(move):
            self.is_over = True
            self.winner = self.current_player
            self.winner.wins += 1
            return f"{self.current_player} wins!"

        if self.board.is_full():
            self.is_over = True
            return "It's a draw!"

        self.current_player_idx = 1 - self.current_player_idx
        return f"{self.current_player}'s turn."

    def undo_last_move(self) -> str:
        if not self.move_history:
            return "No moves to undo."
        last_move = self.move_history.pop()
        self.board.undo(last_move)
        self.is_over = False
        self.winner = None
        self.current_player_idx = 1 - self.current_player_idx
        return f"Undid move at ({last_move.row}, {last_move.col})."

    def play_ai_turn(self) -> str:
        if isinstance(self.current_player, AIPlayer):
            row, col = self.current_player.get_move(self.board)
            return self.make_move(row, col)
        return "Current player is not AI."

    def reset(self):
        self.board = Board(self.board.size)
        self.move_history.clear()
        self.is_over = False
        self.winner = None
        self.current_player_idx = 0
```

### Concurrency Considerations

- For online multiplayer: lock the board during a player's turn
- Use turn-based synchronization (only accept moves from the active player)
- For AI computation: run minimax in a separate thread with timeout

### Extension Points

- NxN board with configurable win length (e.g., 5-in-a-row on 15x15)
- Tournament mode (best of N)
- Network multiplayer with WebSocket
- Move replay/analysis
- Custom board shapes

### Interview Tips

- Emphasize O(1) win detection using row/col/diagonal counters
- Show you understand minimax and alpha-beta pruning
- Discuss the Strategy pattern for pluggable AI levels
- Mention how Command pattern enables undo

---

## Problem 5: Snake and Ladder

### Requirements

**Functional:**
- Configurable board size (default 100 cells)
- Multiple players taking turns
- Random dice rolls (1-6)
- Snakes move player down, Ladders move player up
- First player to reach or exceed final cell wins
- No two snakes/ladders at the same position

**Non-Functional:**
- Fair randomization
- Configurable board (snakes and ladders positions)
- Support for multiple dice

### Design Patterns

| Pattern | Usage |
|---------|-------|
| Template Method | Game flow (roll -> move -> check special -> next turn) |
| Observer | Notify UI of player movements |
| Builder | Board construction with snakes and ladders |
| Strategy | Different dice types (single, double, loaded) |

### Implementation

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import random


class Dice(ABC):
    @abstractmethod
    def roll(self) -> int:
        pass


class StandardDice(Dice):
    def __init__(self, num_dice: int = 1, faces: int = 6):
        self._num_dice = num_dice
        self._faces = faces

    def roll(self) -> int:
        return sum(random.randint(1, self._faces) for _ in range(self._num_dice))


class LoadedDice(Dice):
    """For testing — always rolls a specific value."""
    def __init__(self, values: List[int]):
        self._values = values
        self._index = 0

    def roll(self) -> int:
        val = self._values[self._index % len(self._values)]
        self._index += 1
        return val


@dataclass
class BoardEntity:
    start: int
    end: int

    @property
    def is_snake(self) -> bool:
        return self.end < self.start

    @property
    def is_ladder(self) -> bool:
        return self.end > self.start


@dataclass
class GamePlayer:
    name: str
    position: int = 0
    has_won: bool = False


class BoardBuilder:
    def __init__(self, size: int = 100):
        self._size = size
        self._entities: Dict[int, BoardEntity] = {}

    def add_snake(self, head: int, tail: int) -> 'BoardBuilder':
        assert head > tail, "Snake head must be above tail"
        assert 1 <= tail and head <= self._size
        assert head not in self._entities
        self._entities[head] = BoardEntity(head, tail)
        return self

    def add_ladder(self, bottom: int, top: int) -> 'BoardBuilder':
        assert top > bottom, "Ladder top must be above bottom"
        assert 1 <= bottom and top <= self._size
        assert bottom not in self._entities
        self._entities[bottom] = BoardEntity(bottom, top)
        return self

    def build(self) -> 'GameBoard':
        return GameBoard(self._size, self._entities)


class GameBoard:
    def __init__(self, size: int, entities: Dict[int, BoardEntity]):
        self.size = size
        self._entities = entities

    def get_final_position(self, position: int) -> Tuple[int, Optional[BoardEntity]]:
        """Returns final position after applying snake/ladder, and the entity hit."""
        entity = self._entities.get(position)
        if entity:
            return entity.end, entity
        return position, None

    @property
    def snakes(self) -> List[BoardEntity]:
        return [e for e in self._entities.values() if e.is_snake]

    @property
    def ladders(self) -> List[BoardEntity]:
        return [e for e in self._entities.values() if e.is_ladder]


class GameObserver(ABC):
    @abstractmethod
    def on_roll(self, player: GamePlayer, roll: int):
        pass

    @abstractmethod
    def on_move(self, player: GamePlayer, from_pos: int, to_pos: int):
        pass

    @abstractmethod
    def on_snake(self, player: GamePlayer, entity: BoardEntity):
        pass

    @abstractmethod
    def on_ladder(self, player: GamePlayer, entity: BoardEntity):
        pass

    @abstractmethod
    def on_win(self, player: GamePlayer):
        pass


class ConsoleObserver(GameObserver):
    def on_roll(self, player: GamePlayer, roll: int):
        print(f"  {player.name} rolled a {roll}")

    def on_move(self, player: GamePlayer, from_pos: int, to_pos: int):
        print(f"  {player.name} moves from {from_pos} to {to_pos}")

    def on_snake(self, player: GamePlayer, entity: BoardEntity):
        print(f"  🐍 Snake! {player.name} slides from {entity.start} to {entity.end}")

    def on_ladder(self, player: GamePlayer, entity: BoardEntity):
        print(f"  🪜 Ladder! {player.name} climbs from {entity.start} to {entity.end}")

    def on_win(self, player: GamePlayer):
        print(f"  🏆 {player.name} WINS!")


class SnakeAndLadderGame:
    def __init__(self, board: GameBoard, players: List[GamePlayer],
                 dice: Dice = None):
        self.board = board
        self.players = players
        self.dice = dice or StandardDice()
        self._current_idx = 0
        self._is_over = False
        self._winner: Optional[GamePlayer] = None
        self._observers: List[GameObserver] = []
        self._turn_count = 0

    def add_observer(self, observer: GameObserver):
        self._observers.append(observer)

    @property
    def current_player(self) -> GamePlayer:
        return self.players[self._current_idx]

    @property
    def is_over(self) -> bool:
        return self._is_over

    @property
    def winner(self) -> Optional[GamePlayer]:
        return self._winner

    def play_turn(self) -> str:
        if self._is_over:
            return "Game is over."

        player = self.current_player
        roll = self.dice.roll()
        self._notify_roll(player, roll)

        old_position = player.position
        new_position = player.position + roll

        if new_position > self.board.size:
            self._advance_turn()
            return f"{player.name} rolled {roll} but can't move (would exceed board)."

        if new_position == self.board.size:
            player.position = new_position
            player.has_won = True
            self._is_over = True
            self._winner = player
            self._notify_move(player, old_position, new_position)
            self._notify_win(player)
            return f"{player.name} wins!"

        player.position = new_position
        self._notify_move(player, old_position, new_position)

        final_pos, entity = self.board.get_final_position(new_position)
        if entity:
            player.position = final_pos
            if entity.is_snake:
                self._notify_snake(player, entity)
            else:
                self._notify_ladder(player, entity)

        self._advance_turn()
        self._turn_count += 1
        return f"{player.name}: rolled {roll}, now at {player.position}"

    def play_full_game(self, max_turns: int = 1000) -> GamePlayer:
        while not self._is_over and self._turn_count < max_turns:
            self.play_turn()
        return self._winner

    def _advance_turn(self):
        self._current_idx = (self._current_idx + 1) % len(self.players)

    def _notify_roll(self, player, roll):
        for obs in self._observers:
            obs.on_roll(player, roll)

    def _notify_move(self, player, from_pos, to_pos):
        for obs in self._observers:
            obs.on_move(player, from_pos, to_pos)

    def _notify_snake(self, player, entity):
        for obs in self._observers:
            obs.on_snake(player, entity)

    def _notify_ladder(self, player, entity):
        for obs in self._observers:
            obs.on_ladder(player, entity)

    def _notify_win(self, player):
        for obs in self._observers:
            obs.on_win(player)


def create_standard_game(player_names: List[str]) -> SnakeAndLadderGame:
    board = (BoardBuilder(100)
             .add_snake(99, 54).add_snake(70, 55).add_snake(52, 42)
             .add_snake(25, 2).add_snake(95, 72)
             .add_ladder(6, 25).add_ladder(11, 40).add_ladder(60, 85)
             .add_ladder(46, 90).add_ladder(17, 69)
             .build())
    players = [GamePlayer(name) for name in player_names]
    game = SnakeAndLadderGame(board, players)
    game.add_observer(ConsoleObserver())
    return game
```

### Concurrency Considerations

- Turn-based game: no real concurrency needed for local play
- For online: server validates moves, clients send roll requests
- Random seed management for replay/audit

### Extension Points

- Special cells (skip turn, roll again, go back to start)
- Power-ups (immunity from next snake)
- Variable board sizes and custom themes
- Multiplayer networking
- Game replay from recorded moves

### Interview Tips

- Clarify if player must land exactly on 100 or can exceed
- Show Builder pattern for flexible board configuration
- Mention Observer for clean UI separation
- Discuss fairness of dice (uniform distribution)

---

## Problem 6: Minesweeper

### Requirements

**Functional:**
- Configurable grid (rows, columns, mine count)
- Reveal cell (cascade reveal for empty cells using BFS)
- Flag/unflag cell for suspected mines
- Game over on mine reveal
- Win when all non-mine cells revealed
- First click is never a mine

**Non-Functional:**
- Efficient cascade reveal (BFS/DFS)
- Responsive even on large grids
- Undo support for flags

### Design Patterns

| Pattern | Usage |
|---------|-------|
| Observer | UI updates on cell state change |
| Command | Actions (reveal, flag) with potential undo |
| Strategy | Mine placement algorithms |
| State | Game states (Playing, Won, Lost) |

### Implementation

```python
from enum import Enum, auto
from typing import List, Set, Tuple, Optional
from dataclasses import dataclass, field
from collections import deque
import random


class CellState(Enum):
    HIDDEN = auto()
    REVEALED = auto()
    FLAGGED = auto()


class GameStatus(Enum):
    PLAYING = auto()
    WON = auto()
    LOST = auto()


@dataclass
class Cell:
    row: int
    col: int
    is_mine: bool = False
    state: CellState = CellState.HIDDEN
    adjacent_mines: int = 0

    @property
    def is_revealed(self) -> bool:
        return self.state == CellState.REVEALED

    @property
    def is_flagged(self) -> bool:
        return self.state == CellState.FLAGGED


class MinesweeperBoard:
    def __init__(self, rows: int, cols: int, mine_count: int):
        self.rows = rows
        self.cols = cols
        self.mine_count = mine_count
        self.grid: List[List[Cell]] = [
            [Cell(r, c) for c in range(cols)] for r in range(rows)
        ]
        self._mines_placed = False
        self._revealed_count = 0
        self._total_safe = rows * cols - mine_count
        self.status = GameStatus.PLAYING

    def place_mines(self, exclude_row: int, exclude_col: int):
        """Place mines randomly, excluding the first click position."""
        if self._mines_placed:
            return

        all_positions = [
            (r, c) for r in range(self.rows) for c in range(self.cols)
            if not (r == exclude_row and c == exclude_col)
        ]
        mine_positions = random.sample(all_positions, self.mine_count)
        for r, c in mine_positions:
            self.grid[r][c].is_mine = True

        self._calculate_adjacency()
        self._mines_placed = True

    def _calculate_adjacency(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c].is_mine:
                    continue
                count = sum(
                    1 for nr, nc in self._neighbors(r, c)
                    if self.grid[nr][nc].is_mine
                )
                self.grid[r][c].adjacent_mines = count

    def reveal(self, row: int, col: int) -> List[Cell]:
        """Reveal a cell. Returns list of all cells revealed (for UI update)."""
        if self.status != GameStatus.PLAYING:
            return []

        if not self._mines_placed:
            self.place_mines(row, col)

        cell = self.grid[row][col]
        if cell.is_revealed or cell.is_flagged:
            return []

        if cell.is_mine:
            cell.state = CellState.REVEALED
            self.status = GameStatus.LOST
            return [cell]

        revealed = self._bfs_reveal(row, col)
        if self._revealed_count == self._total_safe:
            self.status = GameStatus.WON
        return revealed

    def _bfs_reveal(self, start_row: int, start_col: int) -> List[Cell]:
        """Cascade reveal using BFS for cells with 0 adjacent mines."""
        revealed = []
        queue = deque([(start_row, start_col)])
        visited: Set[Tuple[int, int]] = {(start_row, start_col)}

        while queue:
            r, c = queue.popleft()
            cell = self.grid[r][c]
            if cell.is_revealed or cell.is_flagged or cell.is_mine:
                continue

            cell.state = CellState.REVEALED
            self._revealed_count += 1
            revealed.append(cell)

            if cell.adjacent_mines == 0:
                for nr, nc in self._neighbors(r, c):
                    if (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))

        return revealed

    def toggle_flag(self, row: int, col: int) -> Optional[Cell]:
        if self.status != GameStatus.PLAYING:
            return None
        cell = self.grid[row][col]
        if cell.is_revealed:
            return None
        cell.state = (CellState.FLAGGED if cell.state == CellState.HIDDEN
                      else CellState.HIDDEN)
        return cell

    def _neighbors(self, row: int, col: int) -> List[Tuple[int, int]]:
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                      (0, 1), (1, -1), (1, 0), (1, 1)]
        return [
            (row + dr, col + dc) for dr, dc in directions
            if 0 <= row + dr < self.rows and 0 <= col + dc < self.cols
        ]

    @property
    def flags_remaining(self) -> int:
        flagged = sum(
            1 for r in range(self.rows) for c in range(self.cols)
            if self.grid[r][c].is_flagged
        )
        return self.mine_count - flagged

    def display(self) -> str:
        lines = []
        for row in self.grid:
            line = ""
            for cell in row:
                if cell.state == CellState.HIDDEN:
                    line += "█ "
                elif cell.state == CellState.FLAGGED:
                    line += "⚑ "
                elif cell.is_mine:
                    line += "💣"
                elif cell.adjacent_mines == 0:
                    line += "  "
                else:
                    line += f"{cell.adjacent_mines} "
            lines.append(line)
        return "\n".join(lines)


class MinesweeperGame:
    DIFFICULTIES = {
        "easy": (9, 9, 10),
        "medium": (16, 16, 40),
        "hard": (16, 30, 99),
    }

    def __init__(self, difficulty: str = "easy"):
        rows, cols, mines = self.DIFFICULTIES.get(difficulty, (9, 9, 10))
        self.board = MinesweeperBoard(rows, cols, mines)
        self._moves: List[Tuple[str, int, int]] = []

    def reveal(self, row: int, col: int) -> str:
        revealed = self.board.reveal(row, col)
        self._moves.append(("reveal", row, col))
        if self.board.status == GameStatus.LOST:
            return "BOOM! Game Over."
        if self.board.status == GameStatus.WON:
            return "Congratulations! You won!"
        return f"Revealed {len(revealed)} cell(s)."

    def flag(self, row: int, col: int) -> str:
        cell = self.board.toggle_flag(row, col)
        if cell:
            self._moves.append(("flag", row, col))
            action = "Flagged" if cell.is_flagged else "Unflagged"
            return f"{action} ({row},{col}). Flags remaining: {self.board.flags_remaining}"
        return "Cannot flag this cell."

    @property
    def is_over(self) -> bool:
        return self.board.status != GameStatus.PLAYING
```

### Concurrency Considerations

- Single-player game: typically no concurrency needed
- For online version: server generates board, client sends reveal requests
- First-click guarantee requires server-side mine placement

### Extension Points

- Hint system (auto-reveal a safe cell)
- Custom board shapes (hexagonal, triangular)
- Multiplayer race mode (same board, fastest to clear wins)
- Replay from recorded moves
- Statistics tracking (win rate, fastest time)

### Interview Tips

- The BFS cascade reveal is the core algorithm — explain it clearly
- Mention first-click safety (mines placed after first reveal)
- Show O(1) win check using revealed count vs total safe cells
- Discuss how professional implementations handle very large boards efficiently

---

## Problem 7: Chess Game

### Requirements

**Functional:**
- Standard 8x8 board with all piece types
- Move validation per piece type
- Special moves: castling, en passant, pawn promotion
- Check, checkmate, and stalemate detection
- Move history and notation
- Turn alternation

**Non-Functional:**
- Efficient move validation
- Extensible for chess variants
- Clean piece polymorphism

### Design Patterns

| Pattern | Usage |
|---------|-------|
| Strategy | Piece movement rules (each piece type is a strategy) |
| Command | Moves with undo capability |
| Observer | UI updates, move logging |
| Flyweight | Shared piece behavior definitions |

### Implementation

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass, field
from copy import deepcopy


class Color(Enum):
    WHITE = "white"
    BLACK = "black"

    @property
    def opposite(self) -> 'Color':
        return Color.BLACK if self == Color.WHITE else Color.WHITE


class PieceType(Enum):
    PAWN = "P"
    KNIGHT = "N"
    BISHOP = "B"
    ROOK = "R"
    QUEEN = "Q"
    KING = "K"


@dataclass
class Position:
    row: int
    col: int

    def is_valid(self) -> bool:
        return 0 <= self.row < 8 and 0 <= self.col < 8

    def __hash__(self):
        return hash((self.row, self.col))

    def __eq__(self, other):
        return self.row == other.row and self.col == other.col


class Piece(ABC):
    def __init__(self, color: Color, piece_type: PieceType):
        self.color = color
        self.piece_type = piece_type
        self.has_moved = False

    @abstractmethod
    def get_possible_moves(self, position: Position,
                           board: 'ChessBoard') -> List[Position]:
        pass

    def symbol(self) -> str:
        s = self.piece_type.value
        return s if self.color == Color.WHITE else s.lower()

    def _slide_moves(self, position: Position, board: 'ChessBoard',
                     directions: List[Tuple[int, int]]) -> List[Position]:
        """Generate moves along directions (for Bishop, Rook, Queen)."""
        moves = []
        for dr, dc in directions:
            r, c = position.row + dr, position.col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                target = Position(r, c)
                occupant = board.get_piece(target)
                if occupant is None:
                    moves.append(target)
                elif occupant.color != self.color:
                    moves.append(target)
                    break
                else:
                    break
                r += dr
                c += dc
        return moves


class Pawn(Piece):
    def __init__(self, color: Color):
        super().__init__(color, PieceType.PAWN)

    def get_possible_moves(self, position: Position,
                           board: 'ChessBoard') -> List[Position]:
        moves = []
        direction = -1 if self.color == Color.WHITE else 1
        start_row = 6 if self.color == Color.WHITE else 1

        # Forward one
        forward = Position(position.row + direction, position.col)
        if forward.is_valid() and board.get_piece(forward) is None:
            moves.append(forward)
            # Forward two from start
            if position.row == start_row:
                double = Position(position.row + 2 * direction, position.col)
                if board.get_piece(double) is None:
                    moves.append(double)

        # Diagonal captures
        for dc in [-1, 1]:
            diag = Position(position.row + direction, position.col + dc)
            if diag.is_valid():
                target = board.get_piece(diag)
                if target and target.color != self.color:
                    moves.append(diag)
                # En passant
                if diag == board.en_passant_target:
                    moves.append(diag)
        return moves


class Knight(Piece):
    def __init__(self, color: Color):
        super().__init__(color, PieceType.KNIGHT)

    def get_possible_moves(self, position: Position,
                           board: 'ChessBoard') -> List[Position]:
        offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                   (1, -2), (1, 2), (2, -1), (2, 1)]
        moves = []
        for dr, dc in offsets:
            target = Position(position.row + dr, position.col + dc)
            if target.is_valid():
                occupant = board.get_piece(target)
                if occupant is None or occupant.color != self.color:
                    moves.append(target)
        return moves


class Bishop(Piece):
    def __init__(self, color: Color):
        super().__init__(color, PieceType.BISHOP)

    def get_possible_moves(self, position: Position,
                           board: 'ChessBoard') -> List[Position]:
        return self._slide_moves(position, board,
                                 [(-1, -1), (-1, 1), (1, -1), (1, 1)])


class Rook(Piece):
    def __init__(self, color: Color):
        super().__init__(color, PieceType.ROOK)

    def get_possible_moves(self, position: Position,
                           board: 'ChessBoard') -> List[Position]:
        return self._slide_moves(position, board,
                                 [(-1, 0), (1, 0), (0, -1), (0, 1)])


class Queen(Piece):
    def __init__(self, color: Color):
        super().__init__(color, PieceType.QUEEN)

    def get_possible_moves(self, position: Position,
                           board: 'ChessBoard') -> List[Position]:
        return self._slide_moves(position, board,
                                 [(-1, -1), (-1, 1), (1, -1), (1, 1),
                                  (-1, 0), (1, 0), (0, -1), (0, 1)])


class King(Piece):
    def __init__(self, color: Color):
        super().__init__(color, PieceType.KING)

    def get_possible_moves(self, position: Position,
                           board: 'ChessBoard') -> List[Position]:
        moves = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                target = Position(position.row + dr, position.col + dc)
                if target.is_valid():
                    occupant = board.get_piece(target)
                    if occupant is None or occupant.color != self.color:
                        moves.append(target)
        return moves


@dataclass
class ChessMove:
    piece: Piece
    from_pos: Position
    to_pos: Position
    captured_piece: Optional[Piece] = None
    is_castling: bool = False
    is_en_passant: bool = False
    promoted_to: Optional[Piece] = None


class ChessBoard:
    def __init__(self):
        self.grid: List[List[Optional[Piece]]] = [[None] * 8 for _ in range(8)]
        self.en_passant_target: Optional[Position] = None
        self._setup_initial_position()

    def _setup_initial_position(self):
        piece_order = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col, piece_cls in enumerate(piece_order):
            self.grid[7][col] = piece_cls(Color.WHITE)
            self.grid[0][col] = piece_cls(Color.BLACK)
        for col in range(8):
            self.grid[6][col] = Pawn(Color.WHITE)
            self.grid[1][col] = Pawn(Color.BLACK)

    def get_piece(self, pos: Position) -> Optional[Piece]:
        if pos.is_valid():
            return self.grid[pos.row][pos.col]
        return None

    def move_piece(self, from_pos: Position, to_pos: Position) -> ChessMove:
        piece = self.grid[from_pos.row][from_pos.col]
        captured = self.grid[to_pos.row][to_pos.col]
        chess_move = ChessMove(piece, from_pos, to_pos, captured)

        self.grid[to_pos.row][to_pos.col] = piece
        self.grid[from_pos.row][from_pos.col] = None
        piece.has_moved = True

        # En passant capture
        if (isinstance(piece, Pawn) and to_pos == self.en_passant_target):
            direction = 1 if piece.color == Color.WHITE else -1
            self.grid[to_pos.row + direction][to_pos.col] = None
            chess_move.is_en_passant = True

        # Update en passant target
        self.en_passant_target = None
        if isinstance(piece, Pawn) and abs(from_pos.row - to_pos.row) == 2:
            mid_row = (from_pos.row + to_pos.row) // 2
            self.en_passant_target = Position(mid_row, from_pos.col)

        return chess_move

    def find_king(self, color: Color) -> Position:
        for r in range(8):
            for c in range(8):
                piece = self.grid[r][c]
                if isinstance(piece, King) and piece.color == color:
                    return Position(r, c)
        raise ValueError(f"No {color.value} king found")

    def is_square_attacked(self, pos: Position, by_color: Color) -> bool:
        for r in range(8):
            for c in range(8):
                piece = self.grid[r][c]
                if piece and piece.color == by_color:
                    moves = piece.get_possible_moves(Position(r, c), self)
                    if pos in moves:
                        return True
        return False

    def is_in_check(self, color: Color) -> bool:
        king_pos = self.find_king(color)
        return self.is_square_attacked(king_pos, color.opposite)


class ChessGame:
    def __init__(self):
        self.board = ChessBoard()
        self.current_turn = Color.WHITE
        self.move_history: List[ChessMove] = []
        self.is_over = False
        self.winner: Optional[Color] = None

    def get_legal_moves(self, pos: Position) -> List[Position]:
        piece = self.board.get_piece(pos)
        if not piece or piece.color != self.current_turn:
            return []

        possible = piece.get_possible_moves(pos, self.board)
        legal = []
        for target in possible:
            if self._is_move_legal(pos, target):
                legal.append(target)
        return legal

    def _is_move_legal(self, from_pos: Position, to_pos: Position) -> bool:
        """A move is legal if it doesn't leave own king in check."""
        board_copy = deepcopy(self.board)
        board_copy.move_piece(from_pos, to_pos)
        return not board_copy.is_in_check(self.current_turn)

    def make_move(self, from_pos: Position, to_pos: Position) -> Optional[ChessMove]:
        legal_moves = self.get_legal_moves(from_pos)
        if to_pos not in legal_moves:
            return None

        chess_move = self.board.move_piece(from_pos, to_pos)
        self.move_history.append(chess_move)
        self.current_turn = self.current_turn.opposite

        if self._is_checkmate(self.current_turn):
            self.is_over = True
            self.winner = self.current_turn.opposite
        elif self._is_stalemate(self.current_turn):
            self.is_over = True
            self.winner = None  # draw

        return chess_move

    def _is_checkmate(self, color: Color) -> bool:
        if not self.board.is_in_check(color):
            return False
        return not self._has_legal_moves(color)

    def _is_stalemate(self, color: Color) -> bool:
        if self.board.is_in_check(color):
            return False
        return not self._has_legal_moves(color)

    def _has_legal_moves(self, color: Color) -> bool:
        for r in range(8):
            for c in range(8):
                piece = self.board.grid[r][c]
                if piece and piece.color == color:
                    pos = Position(r, c)
                    if self.get_legal_moves(pos):
                        return True
        return False
```

### Concurrency Considerations

- Turn-based: no concurrency for local play
- Online: server validates all moves, clients submit move requests
- Timer management in separate thread for timed games

### Extension Points

- Chess960 (Fischer Random) variant
- Move notation (algebraic notation converter)
- PGN import/export
- AI opponents (integrate Stockfish or implement negamax)
- ELO rating calculation

### Interview Tips

- Focus on piece polymorphism for move generation
- Explain check detection: simulate move, check if king attacked
- Mention that castling has 3 conditions: king/rook unmoved, no pieces between, not through check
- Discuss bitboard representation for advanced optimization

---

## Problem 8: 2048 Game

### Requirements

**Functional:**
- 4x4 grid with sliding tiles
- Merge tiles of same value
- Spawn new tile (2 or 4) after each move
- Score tracking (sum of merged values)
- Game over detection (no valid moves)
- Win condition (reach 2048 tile)

**Non-Functional:**
- Smooth merge logic (only merge once per slide)
- Deterministic sliding mechanics
- Undo support

### Design Patterns

| Pattern | Usage |
|---------|-------|
| Command | Move directions with undo |
| Memento | Save/restore game state |
| Observer | Score updates, win/loss notification |
| Strategy | Tile spawning strategy (random vs weighted) |

### Implementation

```python
from enum import Enum
from typing import List, Optional, Tuple
from dataclasses import dataclass, field
from copy import deepcopy
import random


class Direction(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


@dataclass
class GameState:
    """Memento for undo functionality."""
    grid: List[List[int]]
    score: int


class Grid2048:
    def __init__(self, size: int = 4):
        self.size = size
        self.grid: List[List[int]] = [[0] * size for _ in range(size)]
        self.score = 0
        self._history: List[GameState] = []

    def spawn_tile(self):
        empty = [(r, c) for r in range(self.size) for c in range(self.size)
                 if self.grid[r][c] == 0]
        if empty:
            r, c = random.choice(empty)
            self.grid[r][c] = 4 if random.random() < 0.1 else 2

    def slide(self, direction: Direction) -> bool:
        """Slide all tiles in direction. Returns True if board changed."""
        self._save_state()
        original = deepcopy(self.grid)

        if direction == Direction.LEFT:
            self._slide_left()
        elif direction == Direction.RIGHT:
            self._slide_right()
        elif direction == Direction.UP:
            self._slide_up()
        elif direction == Direction.DOWN:
            self._slide_down()

        changed = self.grid != original
        if not changed:
            self._history.pop()  # no change, don't save
        return changed

    def _slide_left(self):
        for row in range(self.size):
            self.grid[row] = self._merge_line(self.grid[row])

    def _slide_right(self):
        for row in range(self.size):
            self.grid[row] = self._merge_line(self.grid[row][::-1])[::-1]

    def _slide_up(self):
        for col in range(self.size):
            column = [self.grid[row][col] for row in range(self.size)]
            merged = self._merge_line(column)
            for row in range(self.size):
                self.grid[row][col] = merged[row]

    def _slide_down(self):
        for col in range(self.size):
            column = [self.grid[row][col] for row in range(self.size)]
            merged = self._merge_line(column[::-1])[::-1]
            for row in range(self.size):
                self.grid[row][col] = merged[row]

    def _merge_line(self, line: List[int]) -> List[int]:
        """Core merge logic: compact, then merge adjacent equals."""
        # Remove zeros
        non_zero = [x for x in line if x != 0]
        merged = []
        skip = False
        for i in range(len(non_zero)):
            if skip:
                skip = False
                continue
            if i + 1 < len(non_zero) and non_zero[i] == non_zero[i + 1]:
                merged_val = non_zero[i] * 2
                merged.append(merged_val)
                self.score += merged_val
                skip = True
            else:
                merged.append(non_zero[i])
        # Pad with zeros
        return merged + [0] * (self.size - len(merged))

    def has_valid_moves(self) -> bool:
        # Check for empty cells
        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == 0:
                    return True
        # Check for adjacent equal values
        for r in range(self.size):
            for c in range(self.size):
                val = self.grid[r][c]
                if c + 1 < self.size and self.grid[r][c + 1] == val:
                    return True
                if r + 1 < self.size and self.grid[r + 1][c] == val:
                    return True
        return False

    def has_won(self, target: int = 2048) -> bool:
        return any(self.grid[r][c] >= target
                   for r in range(self.size) for c in range(self.size))

    def undo(self) -> bool:
        if not self._history:
            return False
        state = self._history.pop()
        self.grid = state.grid
        self.score = state.score
        return True

    def _save_state(self):
        self._history.append(GameState(deepcopy(self.grid), self.score))

    @property
    def max_tile(self) -> int:
        return max(self.grid[r][c] for r in range(self.size)
                   for c in range(self.size))

    def display(self) -> str:
        width = max(len(str(self.max_tile)), 4)
        lines = [f"Score: {self.score}"]
        lines.append("+" + ("-" * (width + 2) + "+") * self.size)
        for row in self.grid:
            cells = []
            for val in row:
                s = str(val) if val else "."
                cells.append(f" {s:^{width}} ")
            lines.append("|" + "|".join(cells) + "|")
            lines.append("+" + ("-" * (width + 2) + "+") * self.size)
        return "\n".join(lines)


class Game2048:
    def __init__(self, size: int = 4, target: int = 2048):
        self.grid = Grid2048(size)
        self.target = target
        self.is_over = False
        self.has_won = False
        # Start with 2 tiles
        self.grid.spawn_tile()
        self.grid.spawn_tile()

    def move(self, direction: Direction) -> str:
        if self.is_over:
            return "Game Over!"

        if not self.grid.slide(direction):
            return "No movement possible in that direction."

        self.grid.spawn_tile()

        if self.grid.has_won(self.target) and not self.has_won:
            self.has_won = True
            return f"You reached {self.target}! Continue or quit?"

        if not self.grid.has_valid_moves():
            self.is_over = True
            return f"Game Over! Final score: {self.grid.score}"

        return f"Score: {self.grid.score} | Max tile: {self.grid.max_tile}"

    def undo(self) -> str:
        if self.grid.undo():
            self.is_over = False
            return "Move undone."
        return "Nothing to undo."
```

### Concurrency Considerations

- Single-player: no concurrency needed for core game
- For leaderboard: concurrent score submissions need atomic updates
- Animation timing (separate render thread from game logic)

### Extension Points

- Variable grid sizes (3x3 to 8x8)
- Different merge rules (3-merge, Fibonacci variant)
- AI solver (expectimax algorithm)
- Multiplayer mode (shared board, alternate turns)
- Custom themes and tile values

### Interview Tips

- The merge logic is the core algorithm — explain the compress-then-merge approach
- Show how all 4 directions reduce to the same merge_line operation with transforms
- Mention Memento pattern for undo
- Discuss the AI approach (expectimax for probabilistic tile spawning)

---

## Problem 9: Splitwise

### Requirements

**Functional:**
- Add expenses: Equal split, Exact amounts, Percentage split
- Track balances between pairs of users
- Simplify debts (minimize transactions)
- Group expenses
- Expense history and settlement
- Notifications for pending balances

**Non-Functional:**
- Accurate floating-point handling (use cents/integer arithmetic)
- Efficient balance computation
- Support large groups

### Design Patterns

| Pattern | Usage |
|---------|-------|
| Strategy | Split calculation methods (Equal, Exact, Percentage) |
| Observer | Notify users of new expenses and settlements |
| Command | Add/settle expenses with undo |

### Implementation

```python
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from collections import defaultdict
import heapq


class SplitType(Enum):
    EQUAL = auto()
    EXACT = auto()
    PERCENTAGE = auto()


@dataclass
class User:
    user_id: str
    name: str
    email: str
    phone: str = ""


@dataclass
class Split:
    user: User
    amount: float = 0.0
    percentage: float = 0.0


class SplitStrategy(ABC):
    @abstractmethod
    def calculate_splits(self, total: float, splits: List[Split]) -> List[Split]:
        pass

    @abstractmethod
    def validate(self, total: float, splits: List[Split]) -> bool:
        pass


class EqualSplitStrategy(SplitStrategy):
    def calculate_splits(self, total: float, splits: List[Split]) -> List[Split]:
        n = len(splits)
        per_person = round(total / n, 2)
        remainder = round(total - per_person * n, 2)
        for i, split in enumerate(splits):
            split.amount = per_person + (0.01 if i < int(remainder * 100) else 0)
        return splits

    def validate(self, total: float, splits: List[Split]) -> bool:
        return len(splits) > 0


class ExactSplitStrategy(SplitStrategy):
    def calculate_splits(self, total: float, splits: List[Split]) -> List[Split]:
        return splits  # amounts already set

    def validate(self, total: float, splits: List[Split]) -> bool:
        split_total = sum(s.amount for s in splits)
        return abs(split_total - total) < 0.01


class PercentageSplitStrategy(SplitStrategy):
    def calculate_splits(self, total: float, splits: List[Split]) -> List[Split]:
        for split in splits:
            split.amount = round(total * split.percentage / 100, 2)
        return splits

    def validate(self, total: float, splits: List[Split]) -> bool:
        total_pct = sum(s.percentage for s in splits)
        return abs(total_pct - 100.0) < 0.01


SPLIT_STRATEGIES = {
    SplitType.EQUAL: EqualSplitStrategy(),
    SplitType.EXACT: ExactSplitStrategy(),
    SplitType.PERCENTAGE: PercentageSplitStrategy(),
}


@dataclass
class Expense:
    expense_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    amount: float = 0.0
    paid_by: User = None
    split_type: SplitType = SplitType.EQUAL
    splits: List[Split] = field(default_factory=list)
    group_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Group:
    group_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    members: List[User] = field(default_factory=list)
    expenses: List[Expense] = field(default_factory=list)


class BalanceSheet:
    """Tracks net balances between all user pairs."""

    def __init__(self):
        # balance_map[A][B] > 0 means B owes A
        self._balances: Dict[str, Dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )

    def record_expense(self, expense: Expense):
        payer_id = expense.paid_by.user_id
        for split in expense.splits:
            if split.user.user_id == payer_id:
                continue
            debtor_id = split.user.user_id
            self._balances[payer_id][debtor_id] += split.amount
            self._balances[debtor_id][payer_id] -= split.amount

    def settle(self, from_user_id: str, to_user_id: str, amount: float):
        self._balances[to_user_id][from_user_id] -= amount
        self._balances[from_user_id][to_user_id] += amount

    def get_balance(self, user_id: str) -> Dict[str, float]:
        """Get what others owe this user (positive) or what user owes (negative)."""
        return dict(self._balances[user_id])

    def get_net_balance(self, user_id: str) -> float:
        """Positive = others owe user. Negative = user owes others."""
        return sum(self._balances[user_id].values())

    def simplify_debts(self, user_ids: Set[str]) -> List[Tuple[str, str, float]]:
        """
        Minimize number of transactions using greedy algorithm.
        Returns list of (debtor, creditor, amount) tuples.
        """
        net = {}
        for uid in user_ids:
            net[uid] = sum(
                self._balances[uid].get(other, 0) for other in user_ids
                if other != uid
            )

        # Separate into creditors and debtors
        creditors = []  # max-heap (negative for max)
        debtors = []    # max-heap (negative for max)
        for uid, amount in net.items():
            if amount > 0.01:
                heapq.heappush(creditors, (-amount, uid))
            elif amount < -0.01:
                heapq.heappush(debtors, (amount, uid))  # most negative first

        transactions = []
        while creditors and debtors:
            credit_amt, creditor = heapq.heappop(creditors)
            debt_amt, debtor = heapq.heappop(debtors)
            credit_amt = -credit_amt
            debt_amt = -debt_amt

            settle_amount = min(credit_amt, debt_amt)
            transactions.append((debtor, creditor, round(settle_amount, 2)))

            remaining_credit = credit_amt - settle_amount
            remaining_debt = debt_amt - settle_amount
            if remaining_credit > 0.01:
                heapq.heappush(creditors, (-remaining_credit, creditor))
            if remaining_debt > 0.01:
                heapq.heappush(debtors, (-remaining_debt, debtor))

        return transactions


class SplitwiseService:
    def __init__(self):
        self._users: Dict[str, User] = {}
        self._groups: Dict[str, Group] = {}
        self._balance_sheet = BalanceSheet()
        self._expenses: List[Expense] = []

    def add_user(self, user: User):
        self._users[user.user_id] = user

    def create_group(self, name: str, members: List[User]) -> Group:
        group = Group(name=name, members=members)
        self._groups[group.group_id] = group
        return group

    def add_expense(self, description: str, amount: float,
                    paid_by: User, split_type: SplitType,
                    splits: List[Split],
                    group_id: Optional[str] = None) -> Optional[Expense]:
        strategy = SPLIT_STRATEGIES[split_type]
        if not strategy.validate(amount, splits):
            return None

        calculated_splits = strategy.calculate_splits(amount, splits)
        expense = Expense(
            description=description, amount=amount,
            paid_by=paid_by, split_type=split_type,
            splits=calculated_splits, group_id=group_id
        )

        self._balance_sheet.record_expense(expense)
        self._expenses.append(expense)
        if group_id and group_id in self._groups:
            self._groups[group_id].expenses.append(expense)
        return expense

    def settle_up(self, from_user: User, to_user: User, amount: float):
        self._balance_sheet.settle(from_user.user_id, to_user.user_id, amount)

    def get_balances(self, user: User) -> Dict[str, float]:
        return self._balance_sheet.get_balance(user.user_id)

    def simplify_group_debts(self, group_id: str) -> List[Tuple[str, str, float]]:
        group = self._groups.get(group_id)
        if not group:
            return []
        member_ids = {m.user_id for m in group.members}
        return self._balance_sheet.simplify_debts(member_ids)

    def get_expense_history(self, user_id: str) -> List[Expense]:
        return [e for e in self._expenses
                if e.paid_by.user_id == user_id or
                any(s.user.user_id == user_id for s in e.splits)]
```

### Concurrency Considerations

- **Concurrent expense additions**: Lock per group to prevent race conditions
- **Balance computation**: Read-write lock (multiple readers, exclusive writers)
- **Settlement atomicity**: Both sides of the balance must update together
- **Eventual consistency**: For distributed systems, use event sourcing

### Extension Points

- Recurring expenses (monthly rent split)
- Multi-currency support with exchange rates
- Receipt scanning (OCR integration)
- Payment gateway integration for direct settlements
- Expense categories and analytics

### Interview Tips

- The debt simplification algorithm is key — explain the greedy approach
- Discuss why floating-point arithmetic is dangerous (use integers/cents)
- Mention the difference between pairwise simplification and global minimum transactions (NP-hard for optimal, greedy is good enough)
- Show understanding of Equal split remainder handling

---

## Problem 10: Movie Ticket Booking (BookMyShow)

### Requirements

**Functional:**
- Browse movies by city, genre, language
- View theaters showing a movie with available showtimes
- Seat selection with real-time availability
- Temporary seat locking during payment (5 min timeout)
- Payment processing and ticket generation
- Booking cancellation with refund policy

**Non-Functional:**
- Handle concurrent seat bookings (no double-booking)
- Low latency for seat availability checks
- Scalable to millions of users
- Seat lock timeout and auto-release

### Design Patterns

| Pattern | Usage |
|---------|-------|
| Strategy | Pricing (weekday/weekend, premium/regular) |
| Observer | Notify on booking confirmation, cancellation |
| Singleton | Booking service instance |
| State | Seat states (Available, Locked, Booked) |

### Class Diagram (Text UML)

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│  Movie   │     │ Theater  │     │  Screen  │
├──────────┤     ├──────────┤     ├──────────┤
│- title   │     │- name    │◆───▶│- seats   │
│- genre   │     │- city    │     │- capacity│
│- duration│     │- screens │     └──────────┘
└──────────┘     └──────────┘
      │                │
      └───────┐  ┌─────┘
              ▼  ▼
         ┌──────────┐        ┌──────────┐
         │   Show   │        │   Seat   │
         ├──────────┤        ├──────────┤
         │- movie   │◆──────▶│- row     │
         │- screen  │        │- number  │
         │- time    │        │- type    │
         │- seats   │        │- state   │
         └──────────┘        └──────────┘
               │
               ▼
         ┌──────────┐        ┌──────────┐
         │ Booking  │        │ Payment  │
         ├──────────┤◆──────▶├──────────┤
         │- show    │        │- amount  │
         │- seats   │        │- method  │
         │- user    │        │- status  │
         │- status  │        └──────────┘
         └──────────┘
```

### Implementation

```python
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock, Timer
import uuid


class SeatType(Enum):
    REGULAR = "regular"
    PREMIUM = "premium"
    VIP = "vip"


class SeatState(Enum):
    AVAILABLE = auto()
    LOCKED = auto()
    BOOKED = auto()


class BookingStatus(Enum):
    PENDING = auto()
    CONFIRMED = auto()
    CANCELLED = auto()
    EXPIRED = auto()


class PaymentStatus(Enum):
    PENDING = auto()
    COMPLETED = auto()
    FAILED = auto()
    REFUNDED = auto()


@dataclass
class Movie:
    movie_id: str
    title: str
    genre: str
    language: str
    duration_minutes: int
    rating: float = 0.0


@dataclass
class Seat:
    row: str
    number: int
    seat_type: SeatType = SeatType.REGULAR
    state: SeatState = SeatState.AVAILABLE
    locked_by: Optional[str] = None
    lock_expiry: Optional[datetime] = None
    _lock: Lock = field(default_factory=Lock, repr=False)

    @property
    def seat_id(self) -> str:
        return f"{self.row}{self.number}"

    def try_lock(self, user_id: str, duration_seconds: int = 300) -> bool:
        with self._lock:
            if self.state == SeatState.AVAILABLE:
                self.state = SeatState.LOCKED
                self.locked_by = user_id
                self.lock_expiry = datetime.now() + timedelta(seconds=duration_seconds)
                return True
            if (self.state == SeatState.LOCKED and
                    self.lock_expiry and datetime.now() > self.lock_expiry):
                # Lock expired, re-lock
                self.state = SeatState.LOCKED
                self.locked_by = user_id
                self.lock_expiry = datetime.now() + timedelta(seconds=duration_seconds)
                return True
            return False

    def confirm_booking(self, user_id: str) -> bool:
        with self._lock:
            if self.state == SeatState.LOCKED and self.locked_by == user_id:
                self.state = SeatState.BOOKED
                return True
            return False

    def release(self, user_id: str = None) -> bool:
        with self._lock:
            if user_id and self.locked_by != user_id:
                return False
            self.state = SeatState.AVAILABLE
            self.locked_by = None
            self.lock_expiry = None
            return True


@dataclass
class Screen:
    screen_id: str
    name: str
    seats: List[List[Seat]] = field(default_factory=list)

    @property
    def capacity(self) -> int:
        return sum(len(row) for row in self.seats)


@dataclass
class Show:
    show_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    movie: Movie = None
    screen: Screen = None
    start_time: datetime = None
    end_time: datetime = None
    _seat_map: Dict[str, Seat] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        if self.screen:
            for row in self.screen.seats:
                for seat in row:
                    self._seat_map[seat.seat_id] = Seat(
                        row=seat.row, number=seat.number,
                        seat_type=seat.seat_type
                    )

    def get_available_seats(self) -> List[Seat]:
        now = datetime.now()
        return [
            s for s in self._seat_map.values()
            if s.state == SeatState.AVAILABLE or
            (s.state == SeatState.LOCKED and s.lock_expiry and now > s.lock_expiry)
        ]

    def get_seat(self, seat_id: str) -> Optional[Seat]:
        return self._seat_map.get(seat_id)

    def lock_seats(self, seat_ids: List[str], user_id: str) -> bool:
        seats = [self._seat_map.get(sid) for sid in seat_ids]
        if any(s is None for s in seats):
            return False
        locked = []
        for seat in seats:
            if seat.try_lock(user_id):
                locked.append(seat)
            else:
                for s in locked:
                    s.release(user_id)
                return False
        return True

    def confirm_seats(self, seat_ids: List[str], user_id: str) -> bool:
        return all(
            self._seat_map[sid].confirm_booking(user_id)
            for sid in seat_ids if sid in self._seat_map
        )

    def release_seats(self, seat_ids: List[str], user_id: str):
        for sid in seat_ids:
            seat = self._seat_map.get(sid)
            if seat:
                seat.release(user_id)


@dataclass
class Theater:
    theater_id: str
    name: str
    city: str
    address: str
    screens: List[Screen] = field(default_factory=list)


class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, seat: Seat, show: Show) -> float:
        pass


class StandardPricing(PricingStrategy):
    BASE_PRICES = {
        SeatType.REGULAR: 200.0,
        SeatType.PREMIUM: 350.0,
        SeatType.VIP: 500.0,
    }

    def calculate_price(self, seat: Seat, show: Show) -> float:
        base = self.BASE_PRICES.get(seat.seat_type, 200.0)
        # Weekend surcharge
        if show.start_time and show.start_time.weekday() >= 5:
            base *= 1.2
        # Prime time surcharge (6pm-9pm)
        if show.start_time and 18 <= show.start_time.hour <= 21:
            base *= 1.1
        return round(base, 2)


@dataclass
class Payment:
    payment_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    amount: float = 0.0
    method: str = "card"
    status: PaymentStatus = PaymentStatus.PENDING
    timestamp: datetime = field(default_factory=datetime.now)

    def process(self) -> bool:
        # Simulate payment processing
        self.status = PaymentStatus.COMPLETED
        return True

    def refund(self) -> bool:
        if self.status == PaymentStatus.COMPLETED:
            self.status = PaymentStatus.REFUNDED
            return True
        return False


@dataclass
class Booking:
    booking_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    user_id: str = ""
    show: Show = None
    seat_ids: List[str] = field(default_factory=list)
    status: BookingStatus = BookingStatus.PENDING
    payment: Optional[Payment] = None
    total_amount: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)


class BookingService:
    """Central service managing the booking workflow."""

    LOCK_DURATION_SECONDS = 300  # 5 minutes

    def __init__(self, pricing: PricingStrategy = None):
        self._bookings: Dict[str, Booking] = {}
        self._shows: Dict[str, Show] = {}
        self._pricing = pricing or StandardPricing()
        self._lock = Lock()
        self._lock_timers: Dict[str, Timer] = {}

    def add_show(self, show: Show):
        self._shows[show.show_id] = show

    def get_available_seats(self, show_id: str) -> List[Seat]:
        show = self._shows.get(show_id)
        return show.get_available_seats() if show else []

    def initiate_booking(self, user_id: str, show_id: str,
                         seat_ids: List[str]) -> Optional[Booking]:
        """Lock seats and create pending booking."""
        show = self._shows.get(show_id)
        if not show:
            return None

        if not show.lock_seats(seat_ids, user_id):
            return None

        total = sum(
            self._pricing.calculate_price(show.get_seat(sid), show)
            for sid in seat_ids
        )

        booking = Booking(
            user_id=user_id, show=show,
            seat_ids=seat_ids, total_amount=total
        )
        self._bookings[booking.booking_id] = booking

        # Schedule auto-release
        timer = Timer(
            self.LOCK_DURATION_SECONDS,
            self._auto_release, [booking.booking_id]
        )
        timer.daemon = True
        timer.start()
        self._lock_timers[booking.booking_id] = timer

        return booking

    def confirm_booking(self, booking_id: str,
                        payment_method: str = "card") -> Optional[Booking]:
        """Process payment and confirm booking."""
        booking = self._bookings.get(booking_id)
        if not booking or booking.status != BookingStatus.PENDING:
            return None

        payment = Payment(amount=booking.total_amount, method=payment_method)
        if not payment.process():
            self._cancel_booking_internal(booking)
            return None

        booking.payment = payment
        booking.show.confirm_seats(booking.seat_ids, booking.user_id)
        booking.status = BookingStatus.CONFIRMED

        # Cancel the auto-release timer
        timer = self._lock_timers.pop(booking_id, None)
        if timer:
            timer.cancel()

        return booking

    def cancel_booking(self, booking_id: str) -> bool:
        booking = self._bookings.get(booking_id)
        if not booking:
            return False
        if booking.status == BookingStatus.CONFIRMED:
            if booking.payment:
                booking.payment.refund()
        self._cancel_booking_internal(booking)
        return True

    def _cancel_booking_internal(self, booking: Booking):
        booking.show.release_seats(booking.seat_ids, booking.user_id)
        booking.status = BookingStatus.CANCELLED

    def _auto_release(self, booking_id: str):
        """Called by timer when lock expires."""
        booking = self._bookings.get(booking_id)
        if booking and booking.status == BookingStatus.PENDING:
            booking.show.release_seats(booking.seat_ids, booking.user_id)
            booking.status = BookingStatus.EXPIRED
```

### Concurrency Considerations

- **Seat-level locking**: Each seat has its own mutex — parallel bookings on different seats
- **Lock timeout with Timer**: Auto-release seats after 5 minutes if payment not completed
- **All-or-nothing seat locking**: Either all requested seats lock or none (prevents partial bookings)
- **Database-level**: In production, use SELECT FOR UPDATE or optimistic locking with version columns
- **Distributed locking**: Redis-based locks for multi-server deployments

### Extension Points

- Waitlist for sold-out shows
- Bulk booking discounts
- Food/beverage add-ons during booking
- Loyalty points integration
- Dynamic pricing based on demand (surge pricing)

### Interview Tips

- Emphasize the seat locking mechanism — it's the most asked follow-up
- Explain why all-or-nothing is important (no partial bookings)
- Discuss how to handle payment gateway timeouts
- Mention the CAP theorem trade-offs for distributed booking systems
- Talk about read replicas for browsing (eventually consistent) vs strong consistency for booking

---

## Problem 11: Restaurant Management System

### Requirements

**Functional:**
- Table management (seat capacity, availability, reservation)
- Menu management (categories, items, prices, availability)
- Order placement and tracking (ordered, preparing, ready, served)
- Kitchen queue management (priority, prep time)
- Bill generation with taxes and discounts
- Waiter assignment to tables

**Non-Functional:**
- Real-time order status updates
- Concurrent order processing
- Peak load handling

### Key Entities

```
Restaurant (has-many) -> Table, Menu, Staff
Table (has-a) -> Order (active), Reservation
Menu (has-many) -> Category -> MenuItem
Order (has-many) -> OrderItem
OrderItem (has-a) -> MenuItem, Status
Kitchen (has-a) -> OrderQueue
Bill (has-a) -> Order, Payment
Staff (is-a) -> Waiter, Chef, Manager
```

### Core Design

```python
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from queue import PriorityQueue
from threading import Lock
import uuid


class TableStatus(Enum):
    AVAILABLE = auto()
    OCCUPIED = auto()
    RESERVED = auto()


class OrderStatus(Enum):
    PLACED = auto()
    PREPARING = auto()
    READY = auto()
    SERVED = auto()
    CANCELLED = auto()


@dataclass
class MenuItem:
    item_id: str
    name: str
    price: float
    category: str
    prep_time_minutes: int = 10
    is_available: bool = True


@dataclass
class OrderItem:
    menu_item: MenuItem
    quantity: int = 1
    status: OrderStatus = OrderStatus.PLACED
    special_instructions: str = ""

    @property
    def subtotal(self) -> float:
        return self.menu_item.price * self.quantity


@dataclass
class Table:
    table_id: str
    capacity: int
    status: TableStatus = TableStatus.AVAILABLE
    current_order: Optional['Order'] = None


@dataclass
class Order:
    order_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    table: Table = None
    items: List[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PLACED
    created_at: datetime = field(default_factory=datetime.now)
    waiter_id: str = ""

    @property
    def total(self) -> float:
        return sum(item.subtotal for item in self.items)

    def add_item(self, menu_item: MenuItem, qty: int = 1, instructions: str = ""):
        self.items.append(OrderItem(menu_item, qty, special_instructions=instructions))


class KitchenQueue:
    """Priority queue for kitchen order processing."""

    def __init__(self):
        self._queue: PriorityQueue = PriorityQueue()
        self._lock = Lock()

    def add_order(self, order: Order, priority: int = 5):
        """Lower priority number = higher priority."""
        with self._lock:
            self._queue.put((priority, order.created_at, order))

    def get_next_order(self) -> Optional[Order]:
        if not self._queue.empty():
            _, _, order = self._queue.get()
            return order
        return None


class BillGenerator:
    TAX_RATE = 0.18  # GST
    SERVICE_CHARGE = 0.05

    def generate(self, order: Order, discount_pct: float = 0) -> Dict:
        subtotal = order.total
        discount = subtotal * (discount_pct / 100)
        after_discount = subtotal - discount
        tax = after_discount * self.TAX_RATE
        service = after_discount * self.SERVICE_CHARGE
        total = after_discount + tax + service
        return {
            "order_id": order.order_id,
            "subtotal": round(subtotal, 2),
            "discount": round(discount, 2),
            "tax": round(tax, 2),
            "service_charge": round(service, 2),
            "total": round(total, 2),
        }


class RestaurantService:
    def __init__(self):
        self.tables: Dict[str, Table] = {}
        self.menu_items: Dict[str, MenuItem] = {}
        self.orders: Dict[str, Order] = {}
        self.kitchen = KitchenQueue()
        self.bill_generator = BillGenerator()

    def seat_party(self, party_size: int) -> Optional[Table]:
        for table in self.tables.values():
            if table.status == TableStatus.AVAILABLE and table.capacity >= party_size:
                table.status = TableStatus.OCCUPIED
                return table
        return None

    def place_order(self, table_id: str, items: List[tuple]) -> Optional[Order]:
        table = self.tables.get(table_id)
        if not table or table.status != TableStatus.OCCUPIED:
            return None
        order = Order(table=table)
        for item_id, qty in items:
            menu_item = self.menu_items.get(item_id)
            if menu_item and menu_item.is_available:
                order.add_item(menu_item, qty)
        self.orders[order.order_id] = order
        table.current_order = order
        self.kitchen.add_order(order)
        return order

    def generate_bill(self, table_id: str, discount: float = 0) -> Optional[Dict]:
        table = self.tables.get(table_id)
        if table and table.current_order:
            return self.bill_generator.generate(table.current_order, discount)
        return None

    def free_table(self, table_id: str):
        table = self.tables.get(table_id)
        if table:
            table.status = TableStatus.AVAILABLE
            table.current_order = None
```

### Interview Tips

- Focus on the Order lifecycle (state machine)
- Kitchen queue ordering (FIFO with priority for VIP tables)
- Discuss how to handle menu item availability changes mid-order
- Mention reservation system integration with table management

---

## Problem 12: Hotel Management System

### Requirements

**Functional:**
- Room types (Single, Double, Suite, Presidential)
- Room booking with check-in/check-out dates
- Room service orders
- Housekeeping management
- Multiple pricing strategies (seasonal, dynamic)
- Guest profile management

**Non-Functional:**
- No double-booking of rooms
- Concurrent reservation handling
- Scalable to large hotel chains

### Core Design

```python
from enum import Enum, auto
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import date, timedelta
from threading import Lock
import uuid


class RoomType(Enum):
    SINGLE = auto()
    DOUBLE = auto()
    SUITE = auto()
    PRESIDENTIAL = auto()


class RoomStatus(Enum):
    AVAILABLE = auto()
    OCCUPIED = auto()
    MAINTENANCE = auto()
    CLEANING = auto()


class ReservationStatus(Enum):
    CONFIRMED = auto()
    CHECKED_IN = auto()
    CHECKED_OUT = auto()
    CANCELLED = auto()


@dataclass
class Room:
    room_number: str
    room_type: RoomType
    floor: int
    price_per_night: float
    status: RoomStatus = RoomStatus.AVAILABLE
    _lock: Lock = field(default_factory=Lock, repr=False)


@dataclass
class Guest:
    guest_id: str
    name: str
    email: str
    phone: str
    id_proof: str = ""


@dataclass
class Reservation:
    reservation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    guest: Guest = None
    room: Room = None
    check_in: date = None
    check_out: date = None
    status: ReservationStatus = ReservationStatus.CONFIRMED
    total_amount: float = 0.0

    @property
    def nights(self) -> int:
        return (self.check_out - self.check_in).days


class HotelService:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.reservations: Dict[str, Reservation] = {}
        self._room_bookings: Dict[str, List[Reservation]] = {}
        self._lock = Lock()

    def search_available_rooms(self, room_type: RoomType,
                               check_in: date, check_out: date) -> List[Room]:
        available = []
        for room in self.rooms.values():
            if room.room_type == room_type and self._is_room_free(room, check_in, check_out):
                available.append(room)
        return available

    def _is_room_free(self, room: Room, check_in: date, check_out: date) -> bool:
        bookings = self._room_bookings.get(room.room_number, [])
        for res in bookings:
            if res.status in (ReservationStatus.CANCELLED, ReservationStatus.CHECKED_OUT):
                continue
            if not (check_out <= res.check_in or check_in >= res.check_out):
                return False
        return True

    def make_reservation(self, guest: Guest, room_number: str,
                         check_in: date, check_out: date) -> Optional[Reservation]:
        with self._lock:
            room = self.rooms.get(room_number)
            if not room or not self._is_room_free(room, check_in, check_out):
                return None
            reservation = Reservation(
                guest=guest, room=room,
                check_in=check_in, check_out=check_out,
                total_amount=room.price_per_night * (check_out - check_in).days
            )
            self.reservations[reservation.reservation_id] = reservation
            self._room_bookings.setdefault(room_number, []).append(reservation)
            return reservation

    def check_in(self, reservation_id: str) -> bool:
        res = self.reservations.get(reservation_id)
        if res and res.status == ReservationStatus.CONFIRMED:
            res.status = ReservationStatus.CHECKED_IN
            res.room.status = RoomStatus.OCCUPIED
            return True
        return False

    def check_out(self, reservation_id: str) -> float:
        res = self.reservations.get(reservation_id)
        if res and res.status == ReservationStatus.CHECKED_IN:
            res.status = ReservationStatus.CHECKED_OUT
            res.room.status = RoomStatus.CLEANING
            return res.total_amount
        return 0.0
```

### Interview Tips

- Discuss date range overlap checking for room availability
- Mention overbooking strategy used by real hotels
- Explain how to handle early check-in/late check-out pricing
- Talk about room upgrade logic when reserved type is unavailable

---

## Problem 13: Car Rental System

### Requirements

**Functional:**
- Vehicle catalog (type, model, features, availability)
- Reservation with pickup/drop-off locations
- Pricing strategies (daily, weekly, mileage-based)
- Insurance options
- Vehicle maintenance tracking
- Late return penalties

### Core Design

```python
from enum import Enum, auto
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import date, datetime
from abc import ABC, abstractmethod
import uuid


class VehicleType(Enum):
    ECONOMY = auto()
    COMPACT = auto()
    MIDSIZE = auto()
    SUV = auto()
    LUXURY = auto()


class VehicleStatus(Enum):
    AVAILABLE = auto()
    RENTED = auto()
    MAINTENANCE = auto()
    RESERVED = auto()


class RentalStatus(Enum):
    RESERVED = auto()
    ACTIVE = auto()
    COMPLETED = auto()
    CANCELLED = auto()


@dataclass
class Vehicle:
    vehicle_id: str
    make: str
    model: str
    year: int
    vehicle_type: VehicleType
    license_plate: str
    mileage: int
    status: VehicleStatus = VehicleStatus.AVAILABLE
    daily_rate: float = 50.0
    location_id: str = ""


class PricingStrategy(ABC):
    @abstractmethod
    def calculate(self, vehicle: Vehicle, days: int, miles: int = 0) -> float:
        pass


class DailyPricing(PricingStrategy):
    def calculate(self, vehicle: Vehicle, days: int, miles: int = 0) -> float:
        return vehicle.daily_rate * days


class WeeklyPricing(PricingStrategy):
    WEEKLY_DISCOUNT = 0.85

    def calculate(self, vehicle: Vehicle, days: int, miles: int = 0) -> float:
        weeks = days // 7
        remaining_days = days % 7
        weekly_rate = vehicle.daily_rate * 7 * self.WEEKLY_DISCOUNT
        return weeks * weekly_rate + remaining_days * vehicle.daily_rate


@dataclass
class Rental:
    rental_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    customer_id: str = ""
    vehicle: Vehicle = None
    pickup_date: date = None
    return_date: date = None
    actual_return: Optional[date] = None
    status: RentalStatus = RentalStatus.RESERVED
    total_cost: float = 0.0
    insurance_opted: bool = False


class CarRentalService:
    def __init__(self):
        self.vehicles: Dict[str, Vehicle] = {}
        self.rentals: Dict[str, Rental] = {}
        self.pricing: PricingStrategy = DailyPricing()

    def search_vehicles(self, vehicle_type: VehicleType,
                        pickup: date, return_date: date,
                        location: str = "") -> List[Vehicle]:
        return [
            v for v in self.vehicles.values()
            if v.vehicle_type == vehicle_type
            and v.status == VehicleStatus.AVAILABLE
            and (not location or v.location_id == location)
        ]

    def reserve(self, customer_id: str, vehicle_id: str,
                pickup: date, return_date: date) -> Optional[Rental]:
        vehicle = self.vehicles.get(vehicle_id)
        if not vehicle or vehicle.status != VehicleStatus.AVAILABLE:
            return None
        days = (return_date - pickup).days
        cost = self.pricing.calculate(vehicle, days)
        rental = Rental(
            customer_id=customer_id, vehicle=vehicle,
            pickup_date=pickup, return_date=return_date, total_cost=cost
        )
        vehicle.status = VehicleStatus.RESERVED
        self.rentals[rental.rental_id] = rental
        return rental

    def pickup_vehicle(self, rental_id: str) -> bool:
        rental = self.rentals.get(rental_id)
        if rental and rental.status == RentalStatus.RESERVED:
            rental.status = RentalStatus.ACTIVE
            rental.vehicle.status = VehicleStatus.RENTED
            return True
        return False

    def return_vehicle(self, rental_id: str, return_date: date) -> float:
        rental = self.rentals.get(rental_id)
        if not rental or rental.status != RentalStatus.ACTIVE:
            return 0.0
        rental.actual_return = return_date
        rental.status = RentalStatus.COMPLETED
        rental.vehicle.status = VehicleStatus.AVAILABLE
        late_days = max(0, (return_date - rental.return_date).days)
        late_fee = late_days * rental.vehicle.daily_rate * 1.5
        rental.total_cost += late_fee
        return rental.total_cost
```

### Interview Tips

- Discuss vehicle allocation strategies (closest location, best match)
- Mention how insurance pricing varies by vehicle type and driver age
- Talk about one-way rental surcharges
- Explain how to handle fleet rebalancing between locations

---

## Problem 14: StackOverflow

### Requirements

**Functional:**
- Post questions with tags
- Answer questions, vote on questions/answers
- Accept answers
- Reputation system (upvote = +10, accepted = +15)
- Tag-based search
- Bounty system

### Core Design

```python
from enum import Enum, auto
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class VoteType(Enum):
    UPVOTE = 1
    DOWNVOTE = -1


@dataclass
class User:
    user_id: str
    username: str
    email: str
    reputation: int = 1
    badges: List[str] = field(default_factory=list)

    def update_reputation(self, delta: int):
        self.reputation = max(1, self.reputation + delta)

    def can_upvote(self) -> bool:
        return self.reputation >= 15

    def can_downvote(self) -> bool:
        return self.reputation >= 125

    def can_comment(self) -> bool:
        return self.reputation >= 50


@dataclass
class Vote:
    user_id: str
    vote_type: VoteType
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Comment:
    comment_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    author: User = None
    body: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    votes: int = 0


@dataclass
class Answer:
    answer_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    author: User = None
    body: str = ""
    is_accepted: bool = False
    votes: List[Vote] = field(default_factory=list)
    comments: List[Comment] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def score(self) -> int:
        return sum(v.vote_type.value for v in self.votes)


@dataclass
class Question:
    question_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    author: User = None
    title: str = ""
    body: str = ""
    tags: Set[str] = field(default_factory=set)
    answers: List[Answer] = field(default_factory=list)
    votes: List[Vote] = field(default_factory=list)
    comments: List[Comment] = field(default_factory=list)
    views: int = 0
    bounty: int = 0
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def score(self) -> int:
        return sum(v.vote_type.value for v in self.votes)

    @property
    def is_answered(self) -> bool:
        return any(a.is_accepted for a in self.answers)


class StackOverflowService:
    UPVOTE_REPUTATION = 10
    DOWNVOTE_REPUTATION = -2
    ACCEPTED_ANSWER_REP = 15

    def __init__(self):
        self.users: Dict[str, User] = {}
        self.questions: Dict[str, Question] = {}
        self._tag_index: Dict[str, List[str]] = {}

    def post_question(self, user_id: str, title: str,
                      body: str, tags: Set[str]) -> Optional[Question]:
        user = self.users.get(user_id)
        if not user:
            return None
        question = Question(author=user, title=title, body=body, tags=tags)
        self.questions[question.question_id] = question
        for tag in tags:
            self._tag_index.setdefault(tag, []).append(question.question_id)
        return question

    def post_answer(self, user_id: str, question_id: str,
                    body: str) -> Optional[Answer]:
        user = self.users.get(user_id)
        question = self.questions.get(question_id)
        if not user or not question:
            return None
        answer = Answer(author=user, body=body)
        question.answers.append(answer)
        return answer

    def vote(self, user_id: str, question_id: str,
             vote_type: VoteType, answer_id: str = None) -> bool:
        user = self.users.get(user_id)
        if not user:
            return False
        if vote_type == VoteType.UPVOTE and not user.can_upvote():
            return False
        if vote_type == VoteType.DOWNVOTE and not user.can_downvote():
            return False

        question = self.questions.get(question_id)
        if not question:
            return False

        vote = Vote(user_id=user_id, vote_type=vote_type)
        if answer_id:
            answer = next((a for a in question.answers if a.answer_id == answer_id), None)
            if answer:
                answer.votes.append(vote)
                rep_delta = self.UPVOTE_REPUTATION if vote_type == VoteType.UPVOTE else self.DOWNVOTE_REPUTATION
                answer.author.update_reputation(rep_delta)
        else:
            question.votes.append(vote)
            rep_delta = self.UPVOTE_REPUTATION if vote_type == VoteType.UPVOTE else self.DOWNVOTE_REPUTATION
            question.author.update_reputation(rep_delta)
        return True

    def accept_answer(self, question_id: str, answer_id: str, user_id: str) -> bool:
        question = self.questions.get(question_id)
        if not question or question.author.user_id != user_id:
            return False
        answer = next((a for a in question.answers if a.answer_id == answer_id), None)
        if answer:
            answer.is_accepted = True
            answer.author.update_reputation(self.ACCEPTED_ANSWER_REP)
            return True
        return False

    def search_by_tag(self, tag: str) -> List[Question]:
        qids = self._tag_index.get(tag, [])
        return [self.questions[qid] for qid in qids if qid in self.questions]
```

### Interview Tips

- Reputation thresholds gate actions (prevents spam)
- Tag-based indexing for efficient search
- Discuss how to rank answers (accepted first, then by votes)
- Mention edit history and community moderation

---

## Problem 15: Twitter (X)

### Requirements

**Functional:**
- Post tweets (280 chars), reply, retweet, like
- Follow/unfollow users
- Timeline generation (home feed)
- Hashtag trending
- Direct messages

### Core Design

```python
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import uuid
import heapq


@dataclass
class Tweet:
    tweet_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    author_id: str = ""
    content: str = ""
    hashtags: Set[str] = field(default_factory=set)
    likes: Set[str] = field(default_factory=set)
    retweet_of: Optional[str] = None
    reply_to: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def like_count(self) -> int:
        return len(self.likes)


@dataclass
class UserProfile:
    user_id: str
    username: str
    bio: str = ""
    followers: Set[str] = field(default_factory=set)
    following: Set[str] = field(default_factory=set)
    tweets: List[str] = field(default_factory=list)


class TwitterService:
    def __init__(self):
        self.users: Dict[str, UserProfile] = {}
        self.tweets: Dict[str, Tweet] = {}
        self._hashtag_index: Dict[str, List[str]] = defaultdict(list)

    def post_tweet(self, user_id: str, content: str) -> Optional[Tweet]:
        if len(content) > 280:
            return None
        hashtags = {word[1:] for word in content.split() if word.startswith("#")}
        tweet = Tweet(author_id=user_id, content=content, hashtags=hashtags)
        self.tweets[tweet.tweet_id] = tweet
        self.users[user_id].tweets.append(tweet.tweet_id)
        for tag in hashtags:
            self._hashtag_index[tag].append(tweet.tweet_id)
        return tweet

    def follow(self, follower_id: str, followee_id: str):
        self.users[follower_id].following.add(followee_id)
        self.users[followee_id].followers.add(follower_id)

    def unfollow(self, follower_id: str, followee_id: str):
        self.users[follower_id].following.discard(followee_id)
        self.users[followee_id].followers.discard(follower_id)

    def get_timeline(self, user_id: str, limit: int = 20) -> List[Tweet]:
        """Fan-out on read: merge recent tweets from followed users."""
        user = self.users.get(user_id)
        if not user:
            return []
        candidate_tweets = []
        for followed_id in user.following:
            followed = self.users.get(followed_id)
            if followed:
                for tid in followed.tweets[-50:]:
                    tweet = self.tweets.get(tid)
                    if tweet:
                        candidate_tweets.append(tweet)
        candidate_tweets.sort(key=lambda t: t.created_at, reverse=True)
        return candidate_tweets[:limit]

    def like_tweet(self, user_id: str, tweet_id: str):
        tweet = self.tweets.get(tweet_id)
        if tweet:
            tweet.likes.add(user_id)

    def get_trending(self, top_n: int = 10) -> List[tuple]:
        counts = {tag: len(tids) for tag, tids in self._hashtag_index.items()}
        return heapq.nlargest(top_n, counts.items(), key=lambda x: x[1])
```

### Interview Tips

- Discuss fan-out on write vs fan-out on read for timeline
- Mention eventual consistency for like counts
- Talk about caching strategies (Redis for timeline cache)
- Explain how trending is computed (sliding window + decay)

---

## Problem 16: Gmail / Email System

### Requirements

**Functional:**
- Compose, send, receive emails
- Folders (Inbox, Sent, Drafts, Trash, Spam)
- Labels (user-defined tags)
- Search by sender, subject, body, date
- Attachments
- Filters and auto-labeling

### Core Design

```python
from enum import Enum, auto
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class Folder(Enum):
    INBOX = "inbox"
    SENT = "sent"
    DRAFTS = "drafts"
    TRASH = "trash"
    SPAM = "spam"


@dataclass
class Attachment:
    filename: str
    size_bytes: int
    content_type: str
    url: str = ""


@dataclass
class Email:
    email_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    sender: str = ""
    recipients: List[str] = field(default_factory=list)
    cc: List[str] = field(default_factory=list)
    subject: str = ""
    body: str = ""
    attachments: List[Attachment] = field(default_factory=list)
    labels: Set[str] = field(default_factory=set)
    folder: Folder = Folder.INBOX
    is_read: bool = False
    is_starred: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    thread_id: Optional[str] = None


@dataclass
class Filter:
    filter_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    from_contains: str = ""
    subject_contains: str = ""
    apply_label: str = ""
    move_to: Optional[Folder] = None
    mark_read: bool = False

    def matches(self, email: Email) -> bool:
        if self.from_contains and self.from_contains not in email.sender:
            return False
        if self.subject_contains and self.subject_contains not in email.subject:
            return False
        return True

    def apply(self, email: Email):
        if self.apply_label:
            email.labels.add(self.apply_label)
        if self.move_to:
            email.folder = self.move_to
        if self.mark_read:
            email.is_read = True


class Mailbox:
    def __init__(self, user_email: str):
        self.user_email = user_email
        self.emails: Dict[str, Email] = {}
        self.filters: List[Filter] = []
        self._folder_index: Dict[Folder, List[str]] = {f: [] for f in Folder}
        self._label_index: Dict[str, List[str]] = {}

    def receive(self, email: Email):
        self.emails[email.email_id] = email
        for f in self.filters:
            if f.matches(email):
                f.apply(email)
        self._folder_index[email.folder].append(email.email_id)
        for label in email.labels:
            self._label_index.setdefault(label, []).append(email.email_id)

    def send(self, to: List[str], subject: str, body: str,
             attachments: List[Attachment] = None) -> Email:
        email = Email(
            sender=self.user_email, recipients=to,
            subject=subject, body=body, folder=Folder.SENT,
            attachments=attachments or []
        )
        self.emails[email.email_id] = email
        self._folder_index[Folder.SENT].append(email.email_id)
        return email

    def move_to_folder(self, email_id: str, folder: Folder):
        email = self.emails.get(email_id)
        if email:
            self._folder_index[email.folder].remove(email_id)
            email.folder = folder
            self._folder_index[folder].append(email_id)

    def search(self, query: str) -> List[Email]:
        query_lower = query.lower()
        return [
            e for e in self.emails.values()
            if query_lower in e.subject.lower() or
               query_lower in e.body.lower() or
               query_lower in e.sender.lower()
        ]

    def get_folder(self, folder: Folder) -> List[Email]:
        return [self.emails[eid] for eid in self._folder_index[folder]
                if eid in self.emails]
```

### Interview Tips

- Discuss threading (group emails by conversation)
- Mention full-text search indexing (inverted index)
- Talk about push notifications vs polling
- Explain filter execution order and conflicts

---

## Problem 17: LinkedIn

### Requirements

**Functional:**
- User profiles (experience, education, skills)
- Connections (1st, 2nd, 3rd degree)
- Posts, comments, likes
- Job postings and applications
- Recommendations and endorsements
- Messaging

### Core Design

```python
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime, date
from collections import deque
import uuid


@dataclass
class Experience:
    company: str
    title: str
    start_date: date
    end_date: Optional[date] = None
    description: str = ""


@dataclass
class Education:
    institution: str
    degree: str
    field_of_study: str
    graduation_year: int


@dataclass
class Profile:
    user_id: str
    name: str
    headline: str = ""
    summary: str = ""
    experience: List[Experience] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    connections: Set[str] = field(default_factory=set)
    endorsements: Dict[str, int] = field(default_factory=dict)


@dataclass
class JobPosting:
    job_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    company: str = ""
    title: str = ""
    description: str = ""
    required_skills: List[str] = field(default_factory=list)
    location: str = ""
    posted_by: str = ""
    applicants: List[str] = field(default_factory=list)


class ConnectionService:
    def __init__(self, profiles: Dict[str, Profile]):
        self._profiles = profiles

    def connect(self, user_a: str, user_b: str):
        self._profiles[user_a].connections.add(user_b)
        self._profiles[user_b].connections.add(user_a)

    def get_degree(self, from_user: str, to_user: str) -> int:
        """BFS to find connection degree (1st, 2nd, 3rd)."""
        if from_user == to_user:
            return 0
        visited = {from_user}
        queue = deque([(from_user, 0)])
        while queue:
            current, depth = queue.popleft()
            if depth >= 3:
                break
            for conn in self._profiles[current].connections:
                if conn == to_user:
                    return depth + 1
                if conn not in visited:
                    visited.add(conn)
                    queue.append((conn, depth + 1))
        return -1  # not connected within 3 degrees

    def get_mutual_connections(self, user_a: str, user_b: str) -> Set[str]:
        return (self._profiles[user_a].connections &
                self._profiles[user_b].connections)

    def suggest_connections(self, user_id: str, limit: int = 10) -> List[str]:
        """Suggest 2nd-degree connections with most mutual connections."""
        user = self._profiles[user_id]
        suggestions = {}
        for conn in user.connections:
            for second in self._profiles[conn].connections:
                if second != user_id and second not in user.connections:
                    suggestions[second] = suggestions.get(second, 0) + 1
        sorted_suggestions = sorted(suggestions.items(), key=lambda x: -x[1])
        return [uid for uid, _ in sorted_suggestions[:limit]]
```

### Interview Tips

- Connection degree via BFS (limit depth to 3)
- Discuss feed ranking algorithm (engagement-based)
- Mention skills endorsement as a graph problem
- Talk about job matching using skill overlap scoring

---

## Problem 18: Amazon E-commerce

### Requirements

**Functional:**
- Product catalog with categories
- Shopping cart management
- Order placement and tracking
- Payment processing
- Inventory management
- Product reviews and ratings
- Search with filters

### Core Design

```python
from enum import Enum, auto
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
import uuid


class OrderStatus(Enum):
    PLACED = auto()
    CONFIRMED = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()
    RETURNED = auto()


@dataclass
class Product:
    product_id: str
    name: str
    description: str
    price: float
    category: str
    seller_id: str
    stock: int = 0
    rating: float = 0.0
    review_count: int = 0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def reserve_stock(self, quantity: int) -> bool:
        with self._lock:
            if self.stock >= quantity:
                self.stock -= quantity
                return True
            return False

    def release_stock(self, quantity: int):
        with self._lock:
            self.stock += quantity


@dataclass
class CartItem:
    product: Product
    quantity: int


class ShoppingCart:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.items: Dict[str, CartItem] = {}

    def add_item(self, product: Product, quantity: int = 1):
        if product.product_id in self.items:
            self.items[product.product_id].quantity += quantity
        else:
            self.items[product.product_id] = CartItem(product, quantity)

    def remove_item(self, product_id: str):
        self.items.pop(product_id, None)

    def update_quantity(self, product_id: str, quantity: int):
        if product_id in self.items:
            if quantity <= 0:
                self.remove_item(product_id)
            else:
                self.items[product_id].quantity = quantity

    @property
    def total(self) -> float:
        return sum(item.product.price * item.quantity for item in self.items.values())

    def clear(self):
        self.items.clear()


@dataclass
class OrderItem:
    product_id: str
    product_name: str
    price: float
    quantity: int


@dataclass
class Order:
    order_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    user_id: str = ""
    items: List[OrderItem] = field(default_factory=list)
    total: float = 0.0
    status: OrderStatus = OrderStatus.PLACED
    shipping_address: str = ""
    placed_at: datetime = field(default_factory=datetime.now)


class OrderService:
    def __init__(self):
        self.orders: Dict[str, Order] = {}
        self.products: Dict[str, Product] = {}
        self._lock = Lock()

    def place_order(self, cart: ShoppingCart, address: str) -> Optional[Order]:
        with self._lock:
            reserved = []
            for item in cart.items.values():
                if not item.product.reserve_stock(item.quantity):
                    for prod, qty in reserved:
                        prod.release_stock(qty)
                    return None
                reserved.append((item.product, item.quantity))

            order = Order(
                user_id=cart.user_id,
                items=[OrderItem(i.product.product_id, i.product.name,
                                 i.product.price, i.quantity) for i in cart.items.values()],
                total=cart.total,
                shipping_address=address
            )
            self.orders[order.order_id] = order
            cart.clear()
            return order

    def cancel_order(self, order_id: str) -> bool:
        order = self.orders.get(order_id)
        if not order or order.status not in (OrderStatus.PLACED, OrderStatus.CONFIRMED):
            return False
        for item in order.items:
            product = self.products.get(item.product_id)
            if product:
                product.release_stock(item.quantity)
        order.status = OrderStatus.CANCELLED
        return True
```

### Interview Tips

- Stock reservation is the critical concurrent operation
- Discuss inventory consistency (what if payment fails after stock reserved)
- Mention saga pattern for distributed order processing
- Talk about search ranking (relevance + popularity + recency)

---

## Problem 19: Amazon Prime Video / Streaming Platform

### Requirements

**Functional:**
- Content catalog (movies, series, episodes)
- User subscriptions and plans
- Video streaming with quality selection
- Watch history and resume playback
- Recommendations
- Reviews and ratings

### Core Design

```python
from enum import Enum, auto
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime


class ContentType(Enum):
    MOVIE = auto()
    SERIES = auto()
    DOCUMENTARY = auto()


class SubscriptionTier(Enum):
    FREE = auto()
    BASIC = auto()
    PREMIUM = auto()


class VideoQuality(Enum):
    SD = "480p"
    HD = "720p"
    FULL_HD = "1080p"
    UHD = "4K"


@dataclass
class Episode:
    episode_id: str
    title: str
    season: int
    episode_number: int
    duration_minutes: int
    video_url: str


@dataclass
class Content:
    content_id: str
    title: str
    content_type: ContentType
    genre: List[str] = field(default_factory=list)
    duration_minutes: int = 0
    release_year: int = 2024
    rating: float = 0.0
    required_tier: SubscriptionTier = SubscriptionTier.FREE
    episodes: List[Episode] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)


@dataclass
class WatchHistory:
    content_id: str
    episode_id: Optional[str] = None
    progress_seconds: int = 0
    total_seconds: int = 0
    last_watched: datetime = field(default_factory=datetime.now)
    completed: bool = False


@dataclass
class UserSubscription:
    user_id: str
    tier: SubscriptionTier = SubscriptionTier.FREE
    max_quality: VideoQuality = VideoQuality.SD
    watch_history: List[WatchHistory] = field(default_factory=list)
    watchlist: List[str] = field(default_factory=list)


class StreamingService:
    def __init__(self):
        self.catalog: Dict[str, Content] = {}
        self.users: Dict[str, UserSubscription] = {}

    def can_watch(self, user_id: str, content_id: str) -> bool:
        user = self.users.get(user_id)
        content = self.catalog.get(content_id)
        if not user or not content:
            return False
        return user.tier.value >= content.required_tier.value

    def start_stream(self, user_id: str, content_id: str,
                     episode_id: str = None) -> Optional[str]:
        if not self.can_watch(user_id, content_id):
            return None
        user = self.users[user_id]
        # Find resume point
        for h in user.watch_history:
            if h.content_id == content_id and h.episode_id == episode_id:
                return f"Resuming at {h.progress_seconds}s"
        return "Starting from beginning"

    def update_progress(self, user_id: str, content_id: str,
                        progress: int, total: int, episode_id: str = None):
        user = self.users.get(user_id)
        if not user:
            return
        for h in user.watch_history:
            if h.content_id == content_id and h.episode_id == episode_id:
                h.progress_seconds = progress
                h.last_watched = datetime.now()
                h.completed = (progress >= total * 0.9)
                return
        user.watch_history.append(WatchHistory(
            content_id=content_id, episode_id=episode_id,
            progress_seconds=progress, total_seconds=total
        ))

    def recommend(self, user_id: str, limit: int = 10) -> List[Content]:
        """Simple content-based recommendation."""
        user = self.users.get(user_id)
        if not user:
            return []
        watched_genres = set()
        watched_ids = set()
        for h in user.watch_history:
            content = self.catalog.get(h.content_id)
            if content:
                watched_genres.update(content.genre)
                watched_ids.add(h.content_id)
        recommendations = [
            c for c in self.catalog.values()
            if c.content_id not in watched_ids
            and any(g in watched_genres for g in c.genre)
            and user.tier.value >= c.required_tier.value
        ]
        recommendations.sort(key=lambda c: c.rating, reverse=True)
        return recommendations[:limit]
```

### Interview Tips

- Discuss adaptive bitrate streaming (quality based on bandwidth)
- Mention CDN for content delivery
- Talk about recommendation algorithms (collaborative vs content-based filtering)
- Explain how to handle concurrent streams limit per subscription

---

## Problem 20: Google Drive / Cloud Storage

### Requirements

**Functional:**
- Create/delete files and folders
- Upload/download files
- Share with permissions (view, edit, owner)
- Search files by name, type
- File versioning
- Storage quota management

### Core Design

```python
from abc import ABC
from enum import Enum, auto
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class Permission(Enum):
    VIEWER = auto()
    EDITOR = auto()
    OWNER = auto()


class FileType(Enum):
    DOCUMENT = auto()
    SPREADSHEET = auto()
    IMAGE = auto()
    VIDEO = auto()
    OTHER = auto()


@dataclass
class FileVersion:
    version_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    size_bytes: int = 0
    modified_by: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    checksum: str = ""


@dataclass
class FileSystemNode(ABC):
    node_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    owner_id: str = ""
    parent_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    shared_with: Dict[str, Permission] = field(default_factory=dict)
    is_trashed: bool = False


@dataclass
class File(FileSystemNode):
    file_type: FileType = FileType.OTHER
    size_bytes: int = 0
    versions: List[FileVersion] = field(default_factory=list)
    content_url: str = ""


@dataclass
class Folder(FileSystemNode):
    children: List[str] = field(default_factory=list)  # node IDs


class DriveService:
    def __init__(self):
        self._nodes: Dict[str, FileSystemNode] = {}
        self._user_roots: Dict[str, str] = {}  # user_id -> root folder ID
        self._user_quota: Dict[str, int] = {}  # user_id -> bytes used

    def create_user_drive(self, user_id: str, quota_bytes: int = 15 * 1024**3):
        root = Folder(name="My Drive", owner_id=user_id)
        self._nodes[root.node_id] = root
        self._user_roots[user_id] = root.node_id
        self._user_quota[user_id] = 0

    def create_folder(self, user_id: str, name: str,
                      parent_id: str) -> Optional[Folder]:
        parent = self._nodes.get(parent_id)
        if not isinstance(parent, Folder):
            return None
        if not self._has_permission(user_id, parent_id, Permission.EDITOR):
            return None
        folder = Folder(name=name, owner_id=user_id, parent_id=parent_id)
        self._nodes[folder.node_id] = folder
        parent.children.append(folder.node_id)
        return folder

    def upload_file(self, user_id: str, name: str, parent_id: str,
                    size_bytes: int, file_type: FileType) -> Optional[File]:
        parent = self._nodes.get(parent_id)
        if not isinstance(parent, Folder):
            return None
        if not self._has_permission(user_id, parent_id, Permission.EDITOR):
            return None
        file = File(name=name, owner_id=user_id, parent_id=parent_id,
                    size_bytes=size_bytes, file_type=file_type)
        file.versions.append(FileVersion(size_bytes=size_bytes, modified_by=user_id))
        self._nodes[file.node_id] = file
        parent.children.append(file.node_id)
        self._user_quota[user_id] = self._user_quota.get(user_id, 0) + size_bytes
        return file

    def share(self, owner_id: str, node_id: str,
              target_user: str, permission: Permission) -> bool:
        node = self._nodes.get(node_id)
        if not node or node.owner_id != owner_id:
            return False
        node.shared_with[target_user] = permission
        return True

    def _has_permission(self, user_id: str, node_id: str,
                        required: Permission) -> bool:
        node = self._nodes.get(node_id)
        if not node:
            return False
        if node.owner_id == user_id:
            return True
        user_perm = node.shared_with.get(user_id)
        if user_perm and user_perm.value >= required.value:
            return True
        if node.parent_id:
            return self._has_permission(user_id, node.parent_id, required)
        return False

    def search(self, user_id: str, query: str) -> List[FileSystemNode]:
        results = []
        for node in self._nodes.values():
            if query.lower() in node.name.lower():
                if self._has_permission(user_id, node.node_id, Permission.VIEWER):
                    results.append(node)
        return results

    def move_to_trash(self, user_id: str, node_id: str) -> bool:
        node = self._nodes.get(node_id)
        if not node or not self._has_permission(user_id, node_id, Permission.OWNER):
            return False
        node.is_trashed = True
        return True
```

### Interview Tips

- Discuss Composite pattern for file/folder hierarchy
- Permission inheritance from parent folders
- Mention conflict resolution for concurrent edits
- Talk about chunked upload for large files

---

## Problem 21: Dropbox / File Sync

### Requirements

**Functional:**
- File upload with chunking
- Sync across devices
- File versioning and conflict resolution
- Sharing with links
- Offline access with sync queue

### Core Design

```python
from enum import Enum, auto
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import uuid


class SyncStatus(Enum):
    SYNCED = auto()
    PENDING_UPLOAD = auto()
    PENDING_DOWNLOAD = auto()
    CONFLICT = auto()


@dataclass
class FileChunk:
    chunk_id: str
    chunk_index: int
    size_bytes: int
    checksum: str
    storage_url: str = ""


@dataclass
class FileMetadata:
    file_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    path: str = ""
    size_bytes: int = 0
    checksum: str = ""
    version: int = 1
    chunks: List[FileChunk] = field(default_factory=list)
    modified_at: datetime = field(default_factory=datetime.now)
    sync_status: SyncStatus = SyncStatus.SYNCED


class ChunkingService:
    CHUNK_SIZE = 4 * 1024 * 1024  # 4MB

    def split_file(self, file_data: bytes) -> List[FileChunk]:
        chunks = []
        for i in range(0, len(file_data), self.CHUNK_SIZE):
            chunk_data = file_data[i:i + self.CHUNK_SIZE]
            chunk = FileChunk(
                chunk_id=str(uuid.uuid4())[:8],
                chunk_index=len(chunks),
                size_bytes=len(chunk_data),
                checksum=hashlib.md5(chunk_data).hexdigest()
            )
            chunks.append(chunk)
        return chunks

    def get_changed_chunks(self, old_chunks: List[FileChunk],
                           new_chunks: List[FileChunk]) -> List[int]:
        """Delta sync: only upload chunks that changed."""
        changed = []
        for i, new_chunk in enumerate(new_chunks):
            if i >= len(old_chunks) or old_chunks[i].checksum != new_chunk.checksum:
                changed.append(i)
        return changed


class SyncService:
    def __init__(self):
        self._files: Dict[str, FileMetadata] = {}
        self._sync_queue: List[FileMetadata] = []
        self._chunker = ChunkingService()

    def upload(self, path: str, file_data: bytes, user_id: str) -> FileMetadata:
        chunks = self._chunker.split_file(file_data)
        existing = self._find_by_path(path)
        if existing:
            changed = self._chunker.get_changed_chunks(existing.chunks, chunks)
            existing.chunks = chunks
            existing.version += 1
            existing.size_bytes = len(file_data)
            existing.checksum = hashlib.md5(file_data).hexdigest()
            existing.modified_at = datetime.now()
            return existing
        metadata = FileMetadata(
            name=path.split("/")[-1], path=path,
            size_bytes=len(file_data), chunks=chunks,
            checksum=hashlib.md5(file_data).hexdigest()
        )
        self._files[metadata.file_id] = metadata
        return metadata

    def detect_conflict(self, local: FileMetadata,
                        remote: FileMetadata) -> bool:
        return (local.version == remote.version and
                local.checksum != remote.checksum)

    def _find_by_path(self, path: str) -> Optional[FileMetadata]:
        for f in self._files.values():
            if f.path == path:
                return f
        return None
```

### Interview Tips

- Chunking enables delta sync (only upload changed chunks)
- Discuss conflict resolution strategies (last-write-wins vs fork)
- Mention content-addressable storage (deduplication via checksum)
- Talk about notification system for sync events across devices

---

## Problem 22: Google Maps / Navigation

### Requirements

**Functional:**
- Map with locations (nodes) and roads (edges)
- Find shortest path between two points
- Points of interest search
- Turn-by-turn navigation
- Traffic-aware routing
- ETA calculation

### Core Design

```python
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import heapq
import math


class TransportMode(Enum):
    DRIVING = auto()
    WALKING = auto()
    CYCLING = auto()
    TRANSIT = auto()


@dataclass
class Location:
    location_id: str
    name: str
    latitude: float
    longitude: float
    category: str = ""


@dataclass
class Road:
    road_id: str
    from_location: str
    to_location: str
    distance_km: float
    speed_limit_kmh: float = 60.0
    traffic_factor: float = 1.0  # 1.0 = free flow, >1 = congested
    is_bidirectional: bool = True

    @property
    def travel_time_minutes(self) -> float:
        effective_speed = self.speed_limit_kmh / self.traffic_factor
        return (self.distance_km / effective_speed) * 60


@dataclass
class Route:
    locations: List[str] = field(default_factory=list)
    total_distance_km: float = 0.0
    total_time_minutes: float = 0.0
    directions: List[str] = field(default_factory=list)


class MapGraph:
    def __init__(self):
        self.locations: Dict[str, Location] = {}
        self.adjacency: Dict[str, List[Tuple[str, Road]]] = {}

    def add_location(self, location: Location):
        self.locations[location.location_id] = location
        self.adjacency.setdefault(location.location_id, [])

    def add_road(self, road: Road):
        self.adjacency.setdefault(road.from_location, []).append(
            (road.to_location, road))
        if road.is_bidirectional:
            self.adjacency.setdefault(road.to_location, []).append(
                (road.from_location, road))

    def shortest_path(self, start: str, end: str,
                      optimize: str = "time") -> Optional[Route]:
        """Dijkstra's algorithm with configurable weight (time or distance)."""
        if start not in self.locations or end not in self.locations:
            return None

        distances = {start: 0.0}
        previous = {}
        pq = [(0.0, start)]
        visited: Set[str] = set()

        while pq:
            current_dist, current = heapq.heappop(pq)
            if current in visited:
                continue
            visited.add(current)

            if current == end:
                return self._build_route(start, end, previous, distances[end])

            for neighbor, road in self.adjacency.get(current, []):
                if neighbor in visited:
                    continue
                weight = (road.travel_time_minutes if optimize == "time"
                          else road.distance_km)
                new_dist = current_dist + weight
                if new_dist < distances.get(neighbor, float('inf')):
                    distances[neighbor] = new_dist
                    previous[neighbor] = (current, road)
                    heapq.heappush(pq, (new_dist, neighbor))

        return None

    def _build_route(self, start: str, end: str,
                     previous: Dict, total_weight: float) -> Route:
        path = []
        current = end
        total_dist = 0.0
        total_time = 0.0
        while current != start:
            path.append(current)
            prev_node, road = previous[current]
            total_dist += road.distance_km
            total_time += road.travel_time_minutes
            current = prev_node
        path.append(start)
        path.reverse()
        return Route(locations=path, total_distance_km=round(total_dist, 2),
                     total_time_minutes=round(total_time, 1))

    def find_nearby(self, lat: float, lng: float,
                    radius_km: float, category: str = "") -> List[Location]:
        results = []
        for loc in self.locations.values():
            dist = self._haversine(lat, lng, loc.latitude, loc.longitude)
            if dist <= radius_km:
                if not category or loc.category == category:
                    results.append(loc)
        results.sort(key=lambda l: self._haversine(lat, lng, l.latitude, l.longitude))
        return results

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2)**2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon/2)**2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
```

### Interview Tips

- Dijkstra's is the core algorithm — mention A* for heuristic optimization
- Discuss how traffic data is updated in real-time (edge weight updates)
- Talk about map tiling for rendering
- Mention precomputation (contraction hierarchies) for faster routing at scale

---

## Problem 23: Google Docs / Collaborative Editing

### Requirements

**Functional:**
- Real-time collaborative editing
- Multiple cursors visible
- Conflict resolution (OT or CRDT)
- Version history
- Comments and suggestions
- Access control

### Core Design

```python
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import uuid


class OperationType(Enum):
    INSERT = auto()
    DELETE = auto()
    RETAIN = auto()


@dataclass
class Operation:
    """Operational Transformation unit."""
    op_type: OperationType
    position: int
    content: str = ""
    length: int = 0
    user_id: str = ""
    revision: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CursorPosition:
    user_id: str
    position: int
    selection_end: Optional[int] = None


@dataclass
class DocumentVersion:
    version_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    content: str = ""
    revision: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    author: str = ""


class OTEngine:
    """Simplified Operational Transformation engine."""

    @staticmethod
    def transform(op1: Operation, op2: Operation) -> Operation:
        """Transform op1 against op2 (op2 was applied first)."""
        if op1.op_type == OperationType.INSERT and op2.op_type == OperationType.INSERT:
            if op1.position <= op2.position:
                return op1
            return Operation(
                op_type=OperationType.INSERT,
                position=op1.position + len(op2.content),
                content=op1.content, user_id=op1.user_id
            )
        if op1.op_type == OperationType.INSERT and op2.op_type == OperationType.DELETE:
            if op1.position <= op2.position:
                return op1
            return Operation(
                op_type=OperationType.INSERT,
                position=max(op1.position - op2.length, op2.position),
                content=op1.content, user_id=op1.user_id
            )
        if op1.op_type == OperationType.DELETE and op2.op_type == OperationType.INSERT:
            if op1.position < op2.position:
                return op1
            return Operation(
                op_type=OperationType.DELETE,
                position=op1.position + len(op2.content),
                length=op1.length, user_id=op1.user_id
            )
        return op1


class CollaborativeDocument:
    def __init__(self, doc_id: str, title: str = "Untitled"):
        self.doc_id = doc_id
        self.title = title
        self.content = ""
        self.revision = 0
        self.history: List[Operation] = []
        self.versions: List[DocumentVersion] = []
        self.cursors: Dict[str, CursorPosition] = {}
        self._ot_engine = OTEngine()

    def apply_operation(self, op: Operation) -> Operation:
        """Apply operation with OT if needed."""
        if op.revision < self.revision:
            for hist_op in self.history[op.revision:]:
                op = self._ot_engine.transform(op, hist_op)

        if op.op_type == OperationType.INSERT:
            self.content = (self.content[:op.position] +
                            op.content + self.content[op.position:])
        elif op.op_type == OperationType.DELETE:
            self.content = (self.content[:op.position] +
                            self.content[op.position + op.length:])

        op.revision = self.revision
        self.revision += 1
        self.history.append(op)
        return op

    def update_cursor(self, user_id: str, position: int,
                      selection_end: int = None):
        self.cursors[user_id] = CursorPosition(user_id, position, selection_end)

    def save_version(self, user_id: str):
        version = DocumentVersion(
            content=self.content, revision=self.revision, author=user_id
        )
        self.versions.append(version)
```

### Interview Tips

- Explain OT vs CRDT trade-offs (OT needs central server, CRDT is peer-to-peer)
- Discuss how cursor positions transform alongside text operations
- Mention WebSocket for real-time communication
- Talk about operation buffering and batching for performance

---

## Problem 24: Zoom / Video Conferencing

### Requirements

**Functional:**
- Create/join meeting rooms
- Audio/video streaming
- Screen sharing
- Chat messaging
- Participant management (mute, kick, roles)
- Recording
- Breakout rooms

### Core Design

```python
from enum import Enum, auto
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class ParticipantRole(Enum):
    HOST = auto()
    CO_HOST = auto()
    PARTICIPANT = auto()


class MeetingStatus(Enum):
    SCHEDULED = auto()
    IN_PROGRESS = auto()
    ENDED = auto()


class MediaType(Enum):
    AUDIO = auto()
    VIDEO = auto()
    SCREEN_SHARE = auto()


@dataclass
class Participant:
    user_id: str
    display_name: str
    role: ParticipantRole = ParticipantRole.PARTICIPANT
    is_audio_on: bool = True
    is_video_on: bool = True
    is_screen_sharing: bool = False
    joined_at: datetime = field(default_factory=datetime.now)


@dataclass
class ChatMessage:
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    sender_id: str = ""
    content: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    is_private: bool = False
    recipient_id: Optional[str] = None


@dataclass
class Meeting:
    meeting_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    host_id: str = ""
    password: str = ""
    status: MeetingStatus = MeetingStatus.SCHEDULED
    participants: Dict[str, Participant] = field(default_factory=dict)
    chat_history: List[ChatMessage] = field(default_factory=list)
    max_participants: int = 100
    is_recording: bool = False
    waiting_room: List[str] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class MeetingService:
    def __init__(self):
        self.meetings: Dict[str, Meeting] = {}

    def create_meeting(self, host_id: str, title: str,
                       password: str = "", max_participants: int = 100) -> Meeting:
        meeting = Meeting(
            title=title, host_id=host_id,
            password=password, max_participants=max_participants
        )
        self.meetings[meeting.meeting_id] = meeting
        return meeting

    def join_meeting(self, meeting_id: str, user_id: str,
                     display_name: str, password: str = "") -> Optional[str]:
        meeting = self.meetings.get(meeting_id)
        if not meeting or meeting.status == MeetingStatus.ENDED:
            return "Meeting not found or ended."
        if meeting.password and meeting.password != password:
            return "Incorrect password."
        if len(meeting.participants) >= meeting.max_participants:
            return "Meeting is full."
        role = (ParticipantRole.HOST if user_id == meeting.host_id
                else ParticipantRole.PARTICIPANT)
        meeting.participants[user_id] = Participant(
            user_id=user_id, display_name=display_name, role=role
        )
        if meeting.status == MeetingStatus.SCHEDULED:
            meeting.status = MeetingStatus.IN_PROGRESS
            meeting.start_time = datetime.now()
        return None

    def toggle_mute(self, meeting_id: str, user_id: str,
                    target_id: str) -> bool:
        meeting = self.meetings.get(meeting_id)
        if not meeting:
            return False
        requester = meeting.participants.get(user_id)
        target = meeting.participants.get(target_id)
        if not requester or not target:
            return False
        if user_id == target_id or requester.role in (
                ParticipantRole.HOST, ParticipantRole.CO_HOST):
            target.is_audio_on = not target.is_audio_on
            return True
        return False

    def send_chat(self, meeting_id: str, sender_id: str,
                  content: str, recipient_id: str = None) -> Optional[ChatMessage]:
        meeting = self.meetings.get(meeting_id)
        if not meeting or sender_id not in meeting.participants:
            return None
        msg = ChatMessage(
            sender_id=sender_id, content=content,
            is_private=recipient_id is not None,
            recipient_id=recipient_id
        )
        meeting.chat_history.append(msg)
        return msg

    def end_meeting(self, meeting_id: str, user_id: str) -> bool:
        meeting = self.meetings.get(meeting_id)
        if not meeting or meeting.host_id != user_id:
            return False
        meeting.status = MeetingStatus.ENDED
        meeting.end_time = datetime.now()
        meeting.participants.clear()
        return True
```

### Interview Tips

- Discuss Mediator pattern (server relays streams between participants)
- Mention SFU vs MCU architectures for video routing
- Talk about bandwidth adaptation (reduce quality for slow connections)
- Explain how recording works (server-side mixing vs client-side)

---

## Problem 25: File System (In-Memory)

### Requirements

**Functional:**
- Create files and directories
- Read/write file content
- Navigate directory structure (ls, cd, pwd)
- File permissions (read, write, execute)
- Hard links and symbolic links
- File metadata (size, timestamps, owner)

### Core Design

```python
from abc import ABC
from enum import Flag, auto
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


class Permission(Flag):
    NONE = 0
    READ = auto()
    WRITE = auto()
    EXECUTE = auto()
    ALL = READ | WRITE | EXECUTE


@dataclass
class Inode:
    inode_number: int
    size: int = 0
    link_count: int = 1
    owner: str = "root"
    group: str = "root"
    permissions: Permission = Permission.ALL
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    is_directory: bool = False
    content: str = ""
    children: Dict[str, int] = field(default_factory=dict)  # name -> inode_number


class FileSystem:
    def __init__(self):
        self._inodes: Dict[int, Inode] = {}
        self._next_inode = 1
        self._cwd_inode = self._create_root()
        self._cwd_path = "/"

    def _create_root(self) -> int:
        inode = Inode(
            inode_number=self._next_inode,
            is_directory=True
        )
        inode.children["."] = inode.inode_number
        inode.children[".."] = inode.inode_number
        self._inodes[inode.inode_number] = inode
        self._next_inode += 1
        return inode.inode_number

    def _allocate_inode(self, is_directory: bool = False,
                        owner: str = "root") -> Inode:
        inode = Inode(
            inode_number=self._next_inode,
            is_directory=is_directory, owner=owner
        )
        if is_directory:
            inode.children["."] = inode.inode_number
        self._inodes[inode.inode_number] = inode
        self._next_inode += 1
        return inode

    def _resolve_path(self, path: str) -> Optional[int]:
        if path.startswith("/"):
            current = 1  # root
            parts = [p for p in path.split("/") if p]
        else:
            current = self._cwd_inode
            parts = [p for p in path.split("/") if p]

        for part in parts:
            inode = self._inodes.get(current)
            if not inode or not inode.is_directory:
                return None
            if part not in inode.children:
                return None
            current = inode.children[part]
        return current

    def mkdir(self, path: str) -> bool:
        parts = [p for p in path.rstrip("/").split("/") if p]
        name = parts[-1]
        parent_path = "/".join(parts[:-1]) or "/"
        if not path.startswith("/"):
            parent_path = self._cwd_path.rstrip("/") + "/" + "/".join(parts[:-1])

        parent_inode_num = self._resolve_path(parent_path if parent_path != "/" else "/")
        if parent_inode_num is None:
            parent_inode_num = self._cwd_inode

        parent = self._inodes.get(parent_inode_num)
        if not parent or not parent.is_directory:
            return False
        if name in parent.children:
            return False

        new_dir = self._allocate_inode(is_directory=True)
        new_dir.children[".."] = parent_inode_num
        parent.children[name] = new_dir.inode_number
        return True

    def create_file(self, path: str, content: str = "") -> bool:
        parts = [p for p in path.split("/") if p]
        name = parts[-1]
        parent_path = "/".join(parts[:-1])

        if path.startswith("/"):
            parent_inode_num = self._resolve_path("/" + parent_path if parent_path else "/")
        else:
            parent_inode_num = (self._resolve_path(parent_path)
                                if parent_path else self._cwd_inode)

        parent = self._inodes.get(parent_inode_num)
        if not parent or not parent.is_directory:
            return False
        if name in parent.children:
            return False

        new_file = self._allocate_inode(is_directory=False)
        new_file.content = content
        new_file.size = len(content)
        parent.children[name] = new_file.inode_number
        return True

    def read_file(self, path: str) -> Optional[str]:
        inode_num = self._resolve_path(path)
        if inode_num is None:
            return None
        inode = self._inodes[inode_num]
        if inode.is_directory:
            return None
        inode.accessed_at = datetime.now()
        return inode.content

    def write_file(self, path: str, content: str) -> bool:
        inode_num = self._resolve_path(path)
        if inode_num is None:
            return False
        inode = self._inodes[inode_num]
        if inode.is_directory:
            return False
        if not (inode.permissions & Permission.WRITE):
            return False
        inode.content = content
        inode.size = len(content)
        inode.modified_at = datetime.now()
        return True

    def ls(self, path: str = ".") -> List[str]:
        inode_num = self._resolve_path(path)
        if inode_num is None:
            return []
        inode = self._inodes[inode_num]
        if not inode.is_directory:
            return [path.split("/")[-1]]
        return [name for name in inode.children.keys()
                if name not in (".", "..")]

    def cd(self, path: str) -> bool:
        inode_num = self._resolve_path(path)
        if inode_num is None:
            return False
        inode = self._inodes[inode_num]
        if not inode.is_directory:
            return False
        self._cwd_inode = inode_num
        if path.startswith("/"):
            self._cwd_path = path
        elif path == "..":
            self._cwd_path = "/".join(self._cwd_path.rstrip("/").split("/")[:-1]) or "/"
        else:
            self._cwd_path = self._cwd_path.rstrip("/") + "/" + path
        return True

    def pwd(self) -> str:
        return self._cwd_path

    def rm(self, path: str) -> bool:
        parts = [p for p in path.split("/") if p]
        name = parts[-1]
        parent_path = "/".join(parts[:-1])

        if path.startswith("/"):
            parent_inode_num = self._resolve_path("/" + parent_path if parent_path else "/")
        else:
            parent_inode_num = (self._resolve_path(parent_path)
                                if parent_path else self._cwd_inode)

        parent = self._inodes.get(parent_inode_num)
        if not parent or name not in parent.children:
            return False

        target_num = parent.children[name]
        target = self._inodes[target_num]
        if target.is_directory and len(target.children) > 2:
            return False  # not empty

        target.link_count -= 1
        if target.link_count <= 0:
            del self._inodes[target_num]
        del parent.children[name]
        return True

    def stat(self, path: str) -> Optional[Dict]:
        inode_num = self._resolve_path(path)
        if inode_num is None:
            return None
        inode = self._inodes[inode_num]
        return {
            "inode": inode.inode_number,
            "size": inode.size,
            "is_directory": inode.is_directory,
            "owner": inode.owner,
            "permissions": str(inode.permissions),
            "link_count": inode.link_count,
            "created": inode.created_at.isoformat(),
            "modified": inode.modified_at.isoformat(),
        }
```

### Interview Tips

- Discuss Composite pattern (files and directories share common interface)
- Mention inode-based design (separation of metadata from directory entries)
- Explain hard links (multiple directory entries pointing to same inode)
- Talk about the difference between this and a real filesystem (block allocation, journaling)
- Discuss permission checking with inheritance

---

## Cross-Cutting Design Principles

### SOLID Principles Applied

| Principle | Application |
|-----------|-------------|
| **S**ingle Responsibility | Each class handles one concern (e.g., Seat manages its own state) |
| **O**pen/Closed | Strategy pattern allows new algorithms without modifying existing code |
| **L**iskov Substitution | All Piece subclasses are interchangeable in Chess |
| **I**nterface Segregation | Small, focused interfaces (e.g., separate Read/Write permissions) |
| **D**ependency Inversion | Services depend on abstractions (PricingStrategy), not concrete implementations |

### Common Concurrency Patterns

```python
# Pattern 1: Per-resource locking
class Resource:
    def __init__(self):
        self._lock = Lock()
    
    def modify(self):
        with self._lock:
            # atomic operation
            pass

# Pattern 2: Lock ordering (prevent deadlocks)
def transfer(account_a, account_b, amount):
    first, second = sorted([account_a, account_b], key=lambda a: a.id)
    with first._lock:
        with second._lock:
            # safe transfer
            pass

# Pattern 3: Optimistic locking
class VersionedEntity:
    def __init__(self):
        self.version = 0
    
    def update(self, expected_version, new_data):
        if self.version != expected_version:
            raise ConcurrencyError("Stale data")
        self.version += 1
        # apply update

# Pattern 4: Read-write lock
from threading import RLock
class ReadWriteLock:
    def __init__(self):
        self._readers = 0
        self._lock = RLock()
        self._write_lock = Lock()
```

### Interview Approach Template

```
1. CLARIFY (2 min)
   - Ask about scale, users, key features
   - Confirm functional vs non-functional priorities

2. IDENTIFY ENTITIES (3 min)
   - List core objects
   - Define relationships (has-a, is-a)
   - Identify enums and value objects

3. DESIGN PATTERNS (2 min)
   - State machines for lifecycle management
   - Strategy for pluggable algorithms
   - Observer for event notification
   - Factory for object creation

4. CLASS DESIGN (10 min)
   - Core classes with key methods
   - Focus on the "interesting" logic
   - Show polymorphism where applicable

5. DEEP DIVE (5 min)
   - Concurrency handling
   - Edge cases
   - Extension points

6. TRADE-OFFS (3 min)
   - In-memory vs persistent storage
   - Consistency vs availability
   - Simplicity vs completeness
```

### Pattern Selection Guide

| Scenario | Pattern |
|----------|---------|
| Object with multiple states and transitions | State |
| Multiple algorithms for same operation | Strategy |
| Need undo/redo capability | Command + Memento |
| Tree/hierarchical structure | Composite |
| Notify multiple components of changes | Observer |
| Control object creation complexity | Factory / Builder |
| Single global instance needed | Singleton |
| Add behavior without modifying class | Decorator |
| Simplify complex subsystem interface | Facade |
| Iterate over collection without exposure | Iterator |

---

## Summary

These 25 problems cover the most commonly asked LLD interview questions. Key takeaways:

1. **Always start with requirements clarification** — never jump into code
2. **Identify the core algorithm** — every problem has one (BFS in Minesweeper, Dijkstra in Maps, etc.)
3. **Use design patterns purposefully** — don't force them, apply where they naturally fit
4. **Think about concurrency early** — interviewers love follow-up questions on thread safety
5. **Keep it extensible** — show you think beyond the immediate requirements
6. **Practice the State pattern** — it appears in 40%+ of LLD problems
7. **Know your data structures** — the right structure makes the design clean (heaps for priority, graphs for relationships, hashmaps for lookups)
