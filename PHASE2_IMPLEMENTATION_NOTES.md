# Phase 2 implementation checkpoint

This checkpoint implements Roadmap **Phase 2 — Rational exact substrate** on top of the Phase-1 architecture.  It was re-audited after a detailed reverse-engineering pass over the Rational-related portions of `Computable_v6.py`, especially `ComputableType.RationalType`, `RationalNumber`, delayed normalization, mutable in-place arithmetic, weak interning, hashing, denominator-bounded navigation, bulk arithmetic, and integer-root helpers.

## Implemented

- `Rational = Q` with no denominator-zero infinity/NaN denotation.
- Frozen/weak-interned public construction and mutable working copies/results.
- Private positive-denominator `_numerator` / `_denominator` working representation with lazy gcd reduction.
- Canonicalizing public `.numerator` / `.denominator` getters and transactional value-level setters.
- Recursive `RationalInput` parsing for supported Phase-2 finite numeric values, exact decimal/scientific/rational strings, and nested two-element tuple ratios.
- Exact binary64 decoding for finite Python `float`; real finite `complex` is accepted by Rational construction/recognition by mathematical value.
- Shared acyclic finite subdomain-recognition registry with separate direct integer recognizers so integerhood tests need not materialize Rational objects.
- `DecisionProcess.advance(work=...)` uses the shared exact integer-valued recognizer.
- Exact finite Rational arithmetic, comparison, integer powers, zero truth testing, integer/floor/ceil/half-even rounding protocols.
- Python numeric equal-hash compatibility using exact integer arithmetic; hashing a mutable working value freezes the same object.
- Explicit `intern()` with weak canonical sharing distinct from hash-triggered freezing.
- Correctly-rounded finite-output binary64 `float()` / `complex()` projection using integer arithmetic, with `OverflowError` exactly at and beyond `T64 = 2**1024 - 2**970`.
- Private Phase-2 integer-root, denominator-bounded rational, and bulk rational helpers for later grid/algebraic phases.
- Reproducible Rational benchmark harness covering 32–8192-bit workloads.

## Reference-derived hot-path architecture restored in the re-audit

The first Phase-2 implementation preserved the public semantics but accidentally standardized away several performance-critical ideas from `Computable_v6.py`.  The re-audit restores those ideas without restoring legacy special-value semantics.

### Public factory policy is separated from raw object birth

`Rational` deliberately defines **no** custom `__new__` and no `__init__`.  A small `_RationalMeta.__call__` owns the public `Rational(...)` factory policy: recursive parsing, canonical weak-cache lookup, normalization when actually required, stable hash initialization, freezing, and interning.

Internal working-object creation uses inherited `cls.__new__(cls)` as the raw allocation primitive.  Consequently the lowest-level instance-birth path remains free of public parser/cache/freeze machinery; internal code does not need to escape a heavyweight `Rational.__new__` by remembering to spell `object.__new__` specially.

### Canonicality is knowledge, not a command to recompute gcd

Internal construction distinguishes a raw working pair from a pair already *known* canonical:

- `_new_working_raw(...)` restores only cheap storage invariants and does no gcd;
- `_new_working_canonical(...)` trusts an already-proved canonical pair and does no gcd;
- `__copy__` copies the representation state and reusable hash knowledge directly.

The public factory first checks the weak cache with the parsed raw pair even when canonicality is only unknown.  A raw-key cache hit is already sufficient evidence that the pair is canonical, so gcd is skipped.  Only an actual miss with unknown canonicality triggers reduction and the second canonical-key lookup.

### Mutable in-place arithmetic is a real workspace

Mutable `+=`, `-=`, `*=`, `/=` compute integer result fields and write them directly into the same receiver.  They allocate **zero Rational result objects**.  A frozen receiver instead receives exactly one fresh mutable working result.  If an in-place operation leaves the raw pair unchanged, the implementation also preserves the existing representation/hash knowledge instead of rewriting the object.

This fixes the previous implementation, which first allocated a temporary result Rational and then copied its fields back into a mutable receiver.

### Exact integer recognition does not materialize Rational

`ExactSubdomainRegistry` now has a direct integer-recognizer table in addition to rational/Gaussian-rational recognizers.  Phase-2 direct handlers cover `int`, `bool`, `Fraction`, finite `float`, finite `complex`, and `Rational`.

For a `Rational`, an already-simplified value is integral iff its denominator is `1`; an unreduced working value is checked by exact divisibility `n % d == 0`.  Neither path simplifies, freezes, interns, or allocates a Rational.  The older rational-materialization fallback is retained only for a future exact type that has a rational recognizer but has not yet installed its own integer recognizer.

### Existing canonical/hash knowledge is reused

- `__copy__` carries a valid cached hash from a frozen canonical source into the mutable same-value copy; every supported mutation invalidates it.
- `hash()` checks the live canonical weak cache after normalization and reuses the cached canonical object's stable hash when available instead of recomputing the modular inverse.
- nonnegative `abs(r)` is a representation-preserving mutable copy.
- denominator-bounded helpers simplify once at their boundary and then call the continued-fraction kernel with a reduced-input certificate rather than gcd-reducing the same pair again.
- bulk sum skips exact-zero terms; finite-only bulk product returns canonical zero immediately after the first zero factor.

These are all instances of the same rule: **already-established exact representation knowledge should flow forward rather than be re-proved.**

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

Two phase-boundary consequences are derived from the Roadmap rather than chosen as new semantics. First, the Phase-1 regression that required all five constructors to remain shells is narrowed to the four future-phase shells once Rational is implemented. Second, GaussianRational/Algebraic branches of the cumulative v1 finite-exact bridge are represented by acyclic registry hooks but cannot be completed until their Roadmap phases provide real denotations. Finite Python `complex` arithmetic is therefore not allowed to fall back to machine-complex arithmetic in this checkpoint; the exact Gaussian lift is wired in Phase 3.

The specifications mention frozen/interned Rational “named constants” but do not freeze public names for such constants in Phase 2.  No arbitrary `ZERO`/`ONE` API spelling was invented; constructor values already satisfy the required frozen/interned lifecycle, and a public constant naming surface can be added only when normatively specified.

## Implementation choices (non-normative)

- Weak interning uses `WeakValueDictionary[(numerator, denominator), Rational]`.
- General Rational arithmetic deliberately delays gcd reduction; canonical reads/hash/intern/storage boundaries reduce on demand.
- Cheap canonicality certificates include normalized zero, denominator `1`, and numerator magnitude `1`; other raw pairs conservatively remain “unknown” until a boundary actually needs gcd.
- Rational hashing implements Python's rational numeric hash directly with integer modular arithmetic; denominator `1` delegates to Python integer hashing.
- Binary64 rounding constructs the final IEEE-754 bit pattern from exact integer comparisons/divisions; `struct` is used only to materialize the already-decided bit pattern as a Python `float`.
- Denominator-bounded navigation is adapted from the continued-fraction/Farey-style reference algorithm, stripped of legacy special-value branches.
- Cross-cancellation remains benchmark-selectable rather than a public invariant; no premature global reduction policy was imposed.

## Tests

The committed Phase-2 suite includes the existing Phase-1 regression tests plus Rational construction/error semantics, recursive parsing, lifecycle/in-place behavior, transactional setters, weak interning, Python equal-hash interoperability, exact field properties, shared integer recognition/work budgets, rounding, binary64 projection boundary/random-oracle tests, integer roots, bounded-denominator helpers, bulk helpers, and explicit hot-path topology tests.

The topology tests additionally verify:

- `Rational.__dict__` does not define `__new__`, and `Rational.__new__ is object.__new__`;
- public construction is intercepted by the Rational metaclass;
- known-canonical construction/copy/unary paths do not invoke gcd;
- a raw weak-cache hit occurs before gcd for conservatively-unsimplified input;
- mutable in-place arithmetic allocates no Rational result, while frozen in-place allocates exactly one;
- direct integer recognition does not call the rational-materialization handler and does not simplify a mutable Rational;
- hashing can reuse an already-live canonical object's stable hash;
- denominator-bounded helpers do not re-prove gcd for a canonical receiver.

Final local validation on Python 3.13:

- `python -m unittest discover -s tests -v`: **46 tests passed**.
- Additional exact randomized audits outside the committed test suite:
  - **20,000** rational-to-binary64 cases matched `Fraction.__float__` bit-for-bit or matched its exact `OverflowError` behavior;
  - **10,000** random exact field/in-place arithmetic cases matched independent `Fraction` oracles;
  - **5,000** denominator-bounded helper cases matched an exact brute-force nearest oracle and returned reduced certified outputs;
  - **5,000** integer-root cases satisfied exact floor-root inequalities and exactness flags;
  - **5,000** setter fixtures confirmed representation-independent value-level assignment;
  - **5,000** unreduced integral Rational fixtures confirmed direct integer recognition without lifecycle/representation mutation.
- `python -m compileall -q computable tests benchmarks`: passed.
- Import checks for the public package, Rational/core modules, projection helper, and four future-phase shells: passed.
- Static correctness grep found no tolerance/`isclose`-style approximate decision path.

## Benchmarks

`benchmarks/bench_phase2_rational.py` provides deterministic smoke and full modes covering random addition/multiplication chains, eager-vs-lazy/cross-cancel comparison kernels, high cancellation, shared denominators, bulk sum/product, and 32/128/512/2048/8192-bit operands. It also contains small hot-path diagnostics for mutable in-place updates and direct integer recognition, and can be executed directly from a source checkout (`python benchmarks/bench_phase2_rational.py`) without requiring an installed package.

The reproducible **smoke** benchmark was run successfully after the re-audit. It used chain length 8, bulk length 24, and 12 cancellation pairs at each required bit size. Representative seconds from the final run were:

| bits | lazy add | eager `Fraction` add | lazy mul | eager `Fraction` mul | cross-cancel mul | high cancellation | shared denominator | bulk sum | bulk product |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 32 | 0.000177 | 0.000044 | 0.000075 | 0.000023 | 0.000013 | 0.000154 | 0.000168 | 0.000050 | 0.000157 |
| 128 | 0.000093 | 0.000031 | 0.000119 | 0.000035 | 0.000029 | 0.000165 | 0.000266 | 0.000079 | 0.000066 |
| 512 | 0.000168 | 0.000120 | 0.000154 | 0.000221 | 0.000133 | 0.000391 | 0.000521 | 0.000543 | 0.000369 |
| 2048 | 0.000884 | 0.000784 | 0.001021 | 0.000968 | 0.001475 | 0.002757 | 0.004715 | 0.007191 | 0.006288 |
| 8192 | 0.011928 | 0.008058 | 0.010766 | 0.010483 | 0.016611 | 0.018226 | 0.047275 | 0.098512 | 0.086802 |

The final smoke hot-path diagnostics measured about **0.0202 s** for 10,000 `+=1; -=1` mutable update pairs and **0.00103 s** for 10,000 direct Python-int integer recognitions in this environment.

Relative to the earlier pre-re-audit smoke run recorded in this file's previous revision, the largest lazy workloads improved substantially (for example the 8192-bit lazy-add/high-cancellation/shared-denominator timings fell from roughly 0.0220/0.0344/0.0898 s to roughly 0.0119/0.0182/0.0473 s). These are diagnostic single-run timings, not stable performance guarantees, but they confirm that the removed allocations/redundant normalizations were material.

The complete `--full` mode was also attempted during this re-audit, but the deliberately extreme all-workload run did not finish inside a 120-second validation cap. This is not a correctness-test failure; every required workload family and every required 32–8192-bit size is exercised by the completed deterministic smoke mode. The full mode remains available for dedicated benchmark runs without changing correctness semantics.

## Known deferred work

- GaussianRational exact complex construction/arithmetic and finite Python-complex promotion are Phase 3.
- Polynomial and Algebraic recognition branches are Phases 4–5.
- Public bounded-denominator grid spelling and theorem-backed localization are Phase 9; Phase 2 only supplies exact finite helpers.
