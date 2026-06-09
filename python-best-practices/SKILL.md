---
name: python-best-practices
description: Python coding guidelines and best practices (PEP 8, type hints, Pythonic patterns, testing with pytest). Use when writing, reviewing, or refactoring Python code to ensure clean, maintainable, production-quality code.
version: 1.0.0
author: adarshdigievo
license: MIT-0
---

# Python Coding Guidelines

Best practices for writing clean, maintainable Python code. Apply when writing, reviewing, or refactoring any Python code.

## Code Style (PEP 8)

- Use 4 spaces for indentation (never tabs)
- Max line length: 88 characters (Black default) or 79 (strict PEP 8)
- Two blank lines before top-level definitions, one blank line within classes
- Import order: stdlib → third-party → local, alphabetical within each group
- Naming: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants

## Python Version Requirements

- **Minimum**: Python 3.10+ (3.9 reached end-of-life October 2025)
- **Target**: Python 3.11–3.13 for new projects
- Never use Python 2 syntax or patterns
- Use modern features: match statements, walrus operator, type hints

## Pythonic Patterns

```python
# List comprehensions instead of loops
squares = [x**2 for x in range(10) if x % 2 == 0]

# Context managers for resources
with open('file.txt', 'r') as f:
    content = f.read()

# f-strings for formatting
name = "World"
greeting = f"Hello, {name}!"

# Type hints
def greet(name: str) -> str:
    return f"Hello, {name}"

# Dataclasses for data containers
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int
    email: str = ""

# pathlib instead of os.path
from pathlib import Path
config_path = Path.home() / ".config" / "app.json"

# enumerate and zip
for idx, item in enumerate(items):
    print(f"{idx}: {item}")

# Walrus operator (Python 3.8+)
if (n := len(data)) > 10:
    print(f"Data has {n} elements")

# Match statement (Python 3.10+)
match command:
    case "quit":
        quit()
    case "go" | "move":
        move()
    case _:
        print("Unknown command")
```

## Anti-Patterns to Avoid

```python
# ❌ Mutable default arguments
def add_item(item, lst=[]):  # Bug!
    lst.append(item)

# ✅ Use None instead
def add_item(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)

# ❌ Bare except
try:
    risky()
except:  # Catches everything including SystemExit!
    pass

# ✅ Specific exceptions
try:
    risky()
except ValueError as e:
    handle(e)

# ❌ String concatenation in loops
result = ""
for s in strings:
    result += s  # O(n²)

# ✅ Use join
result = "".join(strings)

# ❌ == None
if x == None:
    ...

# ✅ is None
if x is None:
    ...

# ❌ len(x) == 0
if len(items) == 0:
    ...

# ✅ Truthiness check
if not items:
    ...
```

## Dependency Management

```bash
# Prefer uv (faster), fallback to pip
if command -v uv &>/dev/null; then
    uv pip install <package>
    uv pip compile requirements.in -o requirements.txt
else
    pip install <package>
fi
```

## Testing (pytest)

```python
# test_example.py
import pytest

def test_basic():
    assert add(1, 2) == 3

def test_raises():
    with pytest.raises(ValueError):
        parse_age(-1)

@pytest.fixture
def sample_user():
    return User(name="Alice", age=30)

def test_with_fixture(sample_user):
    assert sample_user.name == "Alice"
```

```bash
# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest --cov=mypackage tests/
```

## Docstring Format

```python
def calculate_area(width: float, height: float) -> float:
    """Calculate the area of a rectangle.

    Args:
        width: The width of the rectangle in meters.
        height: The height of the rectangle in meters.

    Returns:
        The area of the rectangle in square meters.

    Raises:
        ValueError: If width or height is negative.
    """
    if width < 0 or height < 0:
        raise ValueError("Dimensions must be non-negative")
    return width * height
```

## Pre-commit Checklist

```bash
# Syntax check
python -m py_compile *.py

# Run tests
python -m pytest tests/ -v

# Format check
ruff check . --fix 2>/dev/null || python -m black --check .

# Type check (optional but recommended)
mypy src/
```

## Quick Checklist

- [ ] Syntax validates without errors
- [ ] Tests pass
- [ ] Type hints added to all public functions
- [ ] No hardcoded secrets/credentials
- [ ] Docstrings on public functions/classes
- [ ] No unused imports
- [ ] No mutable default arguments
- [ ] Specific exception handling (no bare `except`)
