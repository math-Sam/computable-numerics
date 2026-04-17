# Computable Current

Exact rationals and oracle-defined computable reals for Python.

`Computable_current.py` is a single-file numeric module that cleanly separates two different kinds of numbers:

- `ComputableRational`: exact rational numbers
- `ComputableReal`: computable real numbers defined by comparison against rationals

This project is **not** a decimal package that tries to print more digits. It is a small numeric core for situations where you want:

- exact fraction arithmetic,
- real numbers that can be compared and refined without committing to a fixed decimal expansion,
- denominator-bounded rational approximations,
- interval-based error reporting,
- and precision that is computed **only when demanded**.

## Why this exists

Most Python numeric tools optimize for fast floating-point arithmetic or for symbolic manipulation.
This module takes a different approach:

- rationals are kept exact,
- reals are represented by a **sign oracle**,
- approximation is tracked as a guaranteed interval,
- and refinement propagates only when some downstream operation actually needs it.

In other words, this module is closer to an **exact / computable real runtime** than to an arbitrary-precision decimal library.

## Highlights

### `ComputableRational`

- exact rational arithmetic
- automatic normalization and reduction
- canonical frozen objects with global caching
- mutable objects for efficient intermediate computation
- bounded-denominator approximation via `rational_bound()`, `rational_floor()`, `rational_ceil()`, and `rational_round()`
- exact / interval-safe output helpers such as `as_integer_ratio()`, `to_scientific_notation()`, and `float_bound()`
- extra operations including integer root extraction and rational logarithms

### `ComputableReal`

- computable reals defined by a comparison oracle instead of a stored decimal expansion
- built-in constants `PI` and `E`
- arithmetic closed under `+`, `-`, `*`, `/`
- guaranteed rational intervals through `current_bound()`
- demand-driven refinement through `refine_to_width()`
- bounded-denominator rational approximation through `rational_bound(max_denominator)`
- interval-safe floating-point output through `float_bound()`
- root construction from a continuous sign-changing interval via `root_finding()`

## Requirements

- **Python 3.14+**
- no third-party dependencies

## Installation

This project is currently a single-file module.

Place `Computable_current.py` somewhere on your Python path, then import it:

```python
from Computable_current import ComputableRational, ComputableReal
```

or

```python
from Computable_current import ComputableRational as Q, ComputableReal as R
```

## Quick Start

```python
from Computable_current import ComputableRational as Q, ComputableReal as R

x = Q(3, 4)
y = Q("1.25")
pi = R.PI
sqrt2 = Q(2) ** Q(1, 2)

print(x)                # 3/4
print(y)                # 5/4
print(x + y)            # 2
print(float(pi))        # 3.141592653589793
print(float(sqrt2))     # 1.4142135623730951
print(pi.current_bound())
```

## A computable real is not a decimal string

`ComputableReal` does **not** store digits.
It stores a sign oracle that answers the question:

> for a rational query `q`, is `q` less than, equal to, or greater than the target real number `x`?

The sign convention is:

- `-1`: queried rational `<` true value
- `0`: queried rational `==` true value
- `1`: queried rational `>` true value

That means a `ComputableReal` is fundamentally a **comparable and refinable real number**, not a precomputed decimal expansion.

## Define your own computable real

```python
from Computable_current import ComputableReal as R


def sqrt2_sign(n: int, d: int) -> int:
    if n * n < 2 * d * d:
        return -1
    return 1


sqrt2 = R(
    sqrt2_sign,
    is_possible_rational=False,
    is_possible_irrational=True,
    left=1,
    right=2,
)

print(sqrt2.current_bound())
print(float(sqrt2))
```

For irrational values like `sqrt(2)`, the sign function never needs to return `0`.
For values that may be rational, returning `0` allows the object to collapse to an exact rational representation.

## Working with intervals and refinement

A `ComputableReal` always carries interval information.
You can inspect the current state, or force refinement only when you need it.

```python
from Computable_current import ComputableRational as Q, ComputableReal as R

x = R.PI

print(x.current_bound())
print(x.current_width())

x.refine_to_width(Q(1, 10_000))
print(x.current_bound())
print(x.current_width())
```

This is the core model of the library:
precision is **demand-driven**, not globally fixed in advance.

## Denominator-bounded rational approximations

One of the most useful operations in this module is to ask for a rational approximation under a denominator budget.

```python
from Computable_current import ComputableReal as R

left, right = R.PI.rational_bound(100)
print(left, right)
```

This gives a guaranteed rational bracket whose denominators are bounded by `100`.
That is often more meaningful than asking for “10 decimal places”, especially when you care about exact downstream arithmetic.

## Exact rationals with mutable / frozen lifecycle

`ComputableRational` is not just an immutable `Fraction` clone.
It supports two practical runtime modes:

- **mutable** objects for heavy intermediate arithmetic
- **frozen / canonical** objects for sharing, hashing, and caching

A typical pattern is:

```python
from Computable_current import ComputableRational as Q

x = Q(1, 3).__copy__()   # mutable working copy
x += Q(1, 6)
result = x.intern()      # freeze + canonicalize

print(result)            # 1/2
```

This design lets the module preserve exact semantics while avoiding unnecessary canonicalization in inner loops.

## Root finding

You can create a computable real root from a continuous function and a finite rational interval whose endpoints have opposite signs.

```python
from Computable_current import ComputableRational as Q, ComputableReal as R

root = R.root_finding(
    lambda n, d: Q(n, d) * Q(n, d) - 2,
    (1, 2),
)

print(root.current_bound())
print(float(root))
```

The callback passed to `root_finding()` receives two integers `(numerator, denominator)` and should return something real-like.

## Output and approximation APIs

### Rational values

Use `ComputableRational` when the value is exact and should stay exact.

```python
from Computable_current import ComputableRational as Q

x = Q("3.125")
print(x.as_integer_ratio())
print(x.to_scientific_notation())
print(x.float_bound())
```

### Real values

Use `ComputableReal` when the value may be irrational or when you want approximation to remain explicit.

```python
from Computable_current import ComputableReal as R

x = R.E
print(x.current_bound())
print(x.rational_bound(50))
print(x.float_bound())
print(float(x))
```

If correctness matters, prefer `current_bound()`, `rational_bound()`, or `float_bound()` over treating `float(x)` as the full story.

## Mental model

### `ComputableRational`

Think of it as:

- an exact value container,
- a canonical cache node,
- and a mutable fraction engine for intermediate work.

### `ComputableReal`

Think of it as:

- a real number that knows how to answer “where is rational `q` relative to me?”,
- a stateful oracle that accumulates information as it is queried,
- and a node in an implicit computation graph.

Arithmetic on `ComputableReal` objects does not immediately collapse to floats.
Instead, it builds new `ComputableReal` objects whose sign functions close over upstream operands.
In practice, this forms an implicit DAG where refinement requests can propagate backward through dependencies.

## What this project is not

This module is **not**:

- a general arbitrary-precision decimal package,
- a fixed-digit high-precision float wrapper,
- or a symbolic CAS.

It is best understood as a numeric core that integrates:

- exact rationals,
- computable reals,
- interval guarantees,
- and demand-driven refinement.

## Hashing and caching

### `ComputableRational`

- canonical frozen rationals are globally cached
- hashing a mutable rational freezes it
- equal rational values can share one canonical object

### `ComputableReal`

Before hashing a `ComputableReal`, you must set:

```python
from Computable_current import ComputableReal as R

R.set_max_denominator_for_hash = 100
```

This setting can be assigned only once.
It defines the denominator budget used when trying to keep hashes compatible with nearby small-denominator rational values.

## Built-in constants

- `ComputableReal.PI`
- `ComputableReal.E`

These are not hard-coded decimal strings.
They are computable real objects driven by comparison procedures.

## One-line summary

`Computable_current.py` is a single-file Python module for working with **exact rationals** and **oracle-defined computable reals**, with **interval guarantees** and **demand-driven refinement** built into the representation itself.
