# Phase 2 implementation checkpoint

This checkpoint implements Roadmap **Phase 2 — Rational exact substrate** on top of the Phase-1 architecture.

## Implemented

- `Rational = Q` with no denominator-zero infinity/NaN denotation.
- Frozen/weak-interned public construction and mutable working copies/results.
- Private positive-denominator `_numerator` / `_denominator` working representation with lazy gcd reduction.
- Canonicalizing public `.numerator` / `.denominator` getters and transactional value-level setters.
- Recursive `RationalInput` parsing for supported Phase-2 finite numeric values, exact decimal/scientific/rational strings, and nested two-element tuple ratios.
- Exact binary64 decoding for finite Python `float`; real finite `complex` is accepted by Rational construction/recognition by mathematical value.
- Shared acyclic finite subdomain-recognition registry and Phase-2 rational/integer/nonnegative-integer recognition bridge.
- `DecisionProcess.advance(work=...)` now uses the shared exact integer-valued recognizer.
- Exact finite Rational arithmetic, comparison, integer powers, zero truth testing, integer/floor/ceil/half-even rounding protocols.
- Python numeric equal-hash compatibility using an integer-ratio hash algorithm; hashing a mutable working value freezes the same object.
- Explicit `intern()` with weak canonical sharing distinct from hash-triggered freezing.
- Correctly-rounded finite-output binary64 `float()` / `complex()` projection using integer arithmetic, with `OverflowError` exactly at and beyond `T64 = 2**1024 - 2**970`.
- Private Phase-2 integer-root, denominator-bounded rational, and bulk rational helpers for later grid/algebraic phases.
- Reproducible Rational benchmark harness covering 32–8192-bit workloads.

## Normative semantic decisions applied directly from the specification

The implementation does not introduce new public semantics. In particular:

- `Rational` denotes only finite rational numbers; legacy denominator-zero special values were deliberately not transplanted.
- `Rational(0.1)` denotes the exact binary64 value, while decimal strings are parsed as exact decimal rationals.
- Numeric subdomain recognition is mathematical-value-first and never launches hidden general-computable recognition.
- Public constructor values are frozen/interned; `copy.copy()` creates a mutable working value; ordinary Rational arithmetic creates working results; in-place arithmetic mutates only a mutable receiver.
- Public coordinate setters use the canonical pre-assignment mathematical value and validate the RHS transactionally; frozen rejection precedes RHS parsing.
- `hash()` and `intern()` remain distinct lifecycle operations.
- `0**0 == 1`; zero to a negative integer power raises `ZeroDivisionError`.
- Exact-class binary64 projection never returns infinity for overflow.

Two Phase-boundary consequences are derived from the Roadmap rather than chosen as new semantics. First, the Phase-1 regression that required all five constructors to remain shells is narrowed to the four future-phase shells once Rational is implemented. Second, GaussianRational/Algebraic branches of the cumulative v1 finite-exact bridge are represented by acyclic registry hooks but cannot be completed until their Roadmap phases provide real denotations. Finite Python `complex` arithmetic is therefore not allowed to fall back to machine-complex arithmetic in this checkpoint; the exact Gaussian lift is wired in Phase 3.

## Implementation choices (non-normative)

- Weak interning uses `WeakValueDictionary[(numerator, denominator), Rational]`.
- General Rational arithmetic deliberately delays gcd reduction; canonical reads/hash/intern/storage boundaries reduce on demand.
- Rational hashing implements Python's rational numeric hash directly with integer modular arithmetic rather than delegating runtime arithmetic to `Fraction`.
- Binary64 rounding constructs the final IEEE-754 bit pattern from exact integer comparisons/divisions; `struct` is used only to materialize the already-decided bit pattern as a Python `float`.
- Denominator-bounded navigation is adapted from the continued-fraction/Farey-style reference algorithm, stripped of legacy special-value branches.

## Tests

The Phase-2 suite includes the existing Phase-1 regression tests plus Rational construction/error semantics, recursive parsing, lifecycle/in-place behavior, transactional setters, weak interning, Python equal-hash interoperability, exact field properties, shared integer recognition/work budgets, rounding, binary64 projection boundary/random-oracle tests, integer roots, bounded-denominator helpers, and bulk helpers.

Release-candidate validation on Python 3.13:

- `python -m unittest discover -s tests -v`: **34 tests passed**.
- Additional exact randomized audits outside the committed test suite: 20,000 rational-to-binary64 cases matched `Fraction.__float__` bit-for-bit; 5,000 denominator-bounded helper cases matched an exact brute-force oracle; 5,000 integer-root cases satisfied the exact floor-root inequalities; 1,000 setter fixtures confirmed representation-independent value-level assignment.
- `python -m compileall -q computable tests benchmarks`: passed.
- Import checks for the public package, Rational/core modules, projection helper, and four future-phase shells: passed.

## Benchmarks

`benchmarks/bench_phase2_rational.py` provides deterministic smoke and full modes covering random addition/multiplication chains, eager-vs-lazy/cross-cancel comparison kernels, high cancellation, shared denominators, bulk sum/product, and 32/128/512/2048/8192-bit operands.

The reproducible **smoke** benchmark was run successfully.  It used chain length 8, bulk length 24, and 12 cancellation pairs at each required bit size.  Representative total seconds per workload were:

| bits | lazy add | eager `Fraction` add | lazy mul | cross-cancel mul | high cancellation | shared denominator | bulk sum | bulk product |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 32 | 0.000161 | 0.000053 | 0.000096 | 0.000021 | 0.000479 | 0.000308 | 0.000064 | 0.000049 |
| 128 | 0.000136 | 0.000058 | 0.000124 | 0.000055 | 0.000215 | 0.000440 | 0.000143 | 0.000113 |
| 512 | 0.000299 | 0.000238 | 0.000490 | 0.000358 | 0.000494 | 0.000833 | 0.000870 | 0.000646 |
| 2048 | 0.001581 | 0.001165 | 0.001307 | 0.001846 | 0.003222 | 0.006854 | 0.017074 | 0.012846 |
| 8192 | 0.022046 | 0.010508 | 0.015902 | 0.024744 | 0.034358 | 0.089774 | 0.120797 | 0.099598 |

The full `--full` workload is provided but was **not run in this checkpoint**; the user explicitly allowed a reproducible smoke benchmark when the complete benchmark is potentially expensive.  These timings are diagnostic only and show that no single reduction strategy dominates every size/workload; future optimization should therefore remain benchmark-driven.

## Known deferred work

- GaussianRational exact complex construction/arithmetic and finite Python-complex promotion are Phase 3.
- Polynomial and Algebraic recognition branches are Phases 4–5.
- Public bounded-denominator grid spelling and theorem-backed localization are Phase 9; Phase 2 only supplies exact finite helpers.
