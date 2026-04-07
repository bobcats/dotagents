---
name: python
description: "Idiomatic Python patterns, anti-patterns, and code quality detection. Use when writing, reviewing, or refactoring Python code."
metadata:
  category: languages
---

# Python

Apply these patterns when writing, reviewing, or refactoring Python code.

## Detection Patterns

### Dead Code

```bash
rg "^def \w+|^class \w+" --type py -o | sort | uniq
rg "^#.*\n#.*\n#" --multiline --type py  # commented blocks
```

### Types

```bash
# Any violations
rg ": Any\b|-> Any\b" --type py
rg "Dict\[str, Any\]|dict\[str, Any\]" --type py
rg "# type: ignore" --type py
rg "cast\(" --type py  # type casts

# Legacy patterns (prefer modern equivalents)
rg "Optional\[" --type py        # prefer X | None (3.10+)
rg "Union\[" --type py           # prefer X | Y (3.10+)
rg "List\[|Dict\[|Set\[|Tuple\[" --type py  # prefer lowercase (3.9+)
rg "TypeVar\(" --type py         # prefer type parameter syntax (3.12+)

# Boolean parameters (boolean blindness)
rg "def \w+\([^)]*: bool" --type py
rg "\w+\(True\)|\w+\(False\)" --type py
```

### Tests

```bash
rg "@pytest.mark.skip|@unittest.skip" --type py
rg "(assert|self\.assert)" --type py -c | sort -t: -k2 -n
```

### Performance

```bash
rg "for .* in .*:.*\.append\(" --type py  # list comprehension candidate
rg "if .* in \[" --type py                # set lookup candidate
rg '"\s*\+\s*"|\'\s*\+\s*\'' --type py   # str.join candidate
rg "await.*\n.*await.*\n.*await" --multiline --type py  # gather candidate
```

### Anti-Patterns

```bash
rg "except:" --type py                    # bare except
rg "from \w+ import \*" --type py         # wildcard import
rg "@staticmethod" --type py              # static-only class smell
rg "def __new__\(" --type py              # dunder abuse smell
```

## Modern Type Hints (3.12+)

```python
# Native type parameter syntax (3.12+) — no TypeVar import needed:
def first[T](items: list[T]) -> T:
    return items[0]

class Stack[T]:
    def __init__(self) -> None:
        self._items: list[T] = []
    def push(self, item: T) -> None:
        self._items.append(item)

# Type aliases (3.12+):
type Vector = list[float]
type UserID = int
type Result[T] = T | Error

# Use X | Y instead of Union, X | None instead of Optional:
def process(value: int | str) -> None: ...
def find(id: int) -> User | None: ...

# Lowercase built-in generics (3.9+):
def get_items() -> list[str]: ...
def get_mapping() -> dict[str, int]: ...

# Protocol for structural typing:
from typing import Protocol

class Comparable(Protocol):
    def __lt__(self, other: Self) -> bool: ...

def sort_items[T: Comparable](items: list[T]) -> list[T]:
    return sorted(items)
```

## Dataclasses Over Manual Classes

```python
# Immutable and memory-efficient:
@dataclass(frozen=True, slots=True)
class Config:
    host: str
    port: int = 8080

# Mutable defaults require field():
@dataclass
class Container:
    items: list[str] = field(default_factory=list)

# Use replace() for updates (returns new instance):
moved = replace(point, x=10.0)  # point unchanged
```

## Performance

### Data Structure Selection

```python
# Set for membership tests — O(1) vs O(n) for list:
allowed: set[str] = {"admin", "editor", "viewer"}
if role in allowed: ...

# defaultdict to eliminate branching:
from collections import defaultdict
groups: defaultdict[str, list[str]] = defaultdict(list)
for item in items:
    groups[item.category].append(item.name)

# deque for queues/sliding windows — O(1) popleft vs O(n) for list:
from collections import deque
window: deque[float] = deque(maxlen=100)

# namedtuple for lightweight immutable records:
from typing import NamedTuple
class Point(NamedTuple):
    x: float
    y: float
```

### Comprehensions and Generators

```python
# List comprehension over loop — 30-40% faster:
result = [x.value for x in items if x.valid]

# Generator for single-pass over large data — O(1) memory:
total = sum(x.price for x in orders if x.shipped)

# Dict/set comprehensions:
lookup = {u.id: u for u in users}
unique_ids = {x.id for x in items}

# Rule: generator for single-pass, list for multiple passes
```

### String Building

```python
# str.join over concatenation — O(n) vs O(n²):
result = ", ".join(names)

# f-strings over format:
f"Hello, {name}"
```

## Async Patterns

```python
# Concurrent independent tasks with gather:
results = await asyncio.gather(
    fetch_user(uid),
    fetch_posts(uid),
    fetch_comments(uid),
)

# Background tasks with create_task:
task = asyncio.create_task(send_notification(user))
# ... do other work ...
await task  # collect result or propagate exception

# Limit concurrency with semaphore:
sem = asyncio.Semaphore(10)
async def limited_fetch(url: str) -> bytes:
    async with sem:
        return await fetch(url)

# Async context manager for resource cleanup:
async with aiohttp.ClientSession() as session:
    async with session.get(url) as resp:
        data = await resp.json()
```

## Design Principles

### Early Return

```python
# Reduce nesting with guard clauses:
def process(data: Data | None) -> Result:
    if data is None:
        return Result.empty()
    if not data.valid:
        raise ValueError("invalid data")
    # main logic at top level, not nested
    return transform(data)
```

### Dependency Injection

```python
# Accept dependencies, don't hardcode them:
class OrderService:
    def __init__(self, repo: OrderRepository, notifier: Notifier) -> None:
        self.repo = repo
        self.notifier = notifier
```

### Pure Functions

```python
# Prefer pure functions — deterministic, no side effects:
def calculate_total(prices: list[float], tax_rate: float) -> float:
    return sum(prices) * (1 + tax_rate)

# Side effects at the edges, pure logic in the core
```

## Pattern Matching (3.10+)

```python
# Replace isinstance chains:
match shape:
    case Circle(radius=r):
        area = math.pi * r ** 2
    case Square(side=s):
        area = s ** 2
    case _:
        raise ValueError(f"Unknown shape: {shape}")

# With guards:
match command:
    case ["move", x, y] if x > 0 and y > 0:
        move_to(x, y)
    case ["quit"]:
        exit()
```

## Context Managers

```python
# Always use with for resource cleanup:
with open(path) as f:
    data = f.read()

# Custom context manager:
from contextlib import contextmanager

@contextmanager
def timer(name: str):
    start = time.time()
    yield
    print(f"{name}: {time.time() - start:.2f}s")
```

## Pythonic Patterns

```python
# any/all over loops:
found = any(x.valid for x in items)
all_valid = all(x.valid for x in items)

# enumerate over range(len()):
for i, item in enumerate(items):
    print(i, item)

# zip for parallel iteration:
for name, age in zip(names, ages, strict=True):
    print(f"{name}: {age}")

# Walrus operator (3.8+):
if (match := pattern.search(text)):
    process(match)

# dict.get with default:
value = d.get(key, default)

# Unpacking:
first, *rest = items
head, *middle, tail = items
```

## Avoiding Common Mistakes

```python
# Mutable default argument (bug):
def append_to(item, items=[]):  # DON'T — shared list
    ...
# →
def append_to(item, items: list | None = None):
    if items is None:
        items = []
    items.append(item)
    return items

# Late binding in closures (bug):
funcs = [lambda: i for i in range(3)]  # all return 2!
# →
funcs = [lambda i=i: i for i in range(3)]

# Use is for None/True/False:
if x is None: ...  # not ==

# Exceptions as control flow (anti-pattern):
# DON'T nest try/except for branching — use explicit conditionals

# Bare except (anti-pattern):
except:  # DON'T — catches SystemExit, KeyboardInterrupt
# →
except Exception:  # or a specific type

# Wildcard imports (anti-pattern):
from module import *  # DON'T — pollutes namespace, breaks tools
# →
from module import specific_name

# Static-only classes (anti-pattern):
class Utils:
    @staticmethod
    def clean(text): ...
# → just use a module with functions
```

## Boolean Blindness

```python
# Boolean parameter hides intent:
send_email(user, True)  # what does True mean? →

# Use Enum for self-documenting call sites:
class Priority(Enum):
    NORMAL = auto()
    URGENT = auto()

def send_email(user: User, priority: Priority = Priority.NORMAL) -> None: ...
send_email(user, Priority.URGENT)

# Or Literal for simple cases:
def send_email(user: User, priority: Literal["normal", "urgent"] = "normal") -> None: ...
```

## Parse, Don't Validate

```python
# Parse into typed structure at boundary:
@dataclass(frozen=True, slots=True)
class UserInput:
    email: str
    age: int

    @classmethod
    def parse(cls, data: dict[str, Any]) -> "UserInput":
        email = data.get("email")
        age = data.get("age")
        if not isinstance(email, str) or "@" not in email:
            raise ValueError("invalid email")
        if not isinstance(age, int) or age <= 0:
            raise ValueError("invalid age")
        return cls(email=email, age=age)

# Or use pydantic for declarative parsing:
class UserInput(BaseModel):
    email: EmailStr
    age: PositiveInt

user = UserInput.model_validate(data)  # raises if invalid
```

## Immutability

```python
# Prefer frozen dataclasses:
@dataclass(frozen=True, slots=True)
class Point:
    x: float
    y: float

# For collections, prefer tuple over list when immutable:
ALLOWED_STATUSES: tuple[str, ...] = ("pending", "active", "closed")
```
