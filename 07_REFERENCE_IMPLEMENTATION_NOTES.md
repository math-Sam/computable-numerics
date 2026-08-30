# Computable：Reference Implementation Notes

本文件是 **non-normative engineering companion**。它整理 reference module `Computable_v6.py` 中值得保留、再次驗證或改寫的演算法與工程技巧。

它不定義 public semantics，也不覆蓋 `02_SEMANTIC_SPECIFICATION.md`、`03_ARCHITECTURE_AND_PUBLIC_API.md` 或 `06_MATHEMATICAL_FOUNDATIONS.md`。

使用本文件時應遵守：

> **Reuse the idea, not the surrounding data model.**

某段 reference code 即使演算法有價值，也不表示它所在的 class hierarchy、special-value convention、control-flow behavior 或 object graph 可以直接移植。

---

# 1. Reference source map

主要參考檔：

```text
Computable_v6.py
```

值得優先閱讀的區域包括：

| Topic | Main symbols / regions |
|---|---|
| Rational mutable/frozen lifecycle | `RationalNumber`, `simplify`, `intern`, `__hash__` |
| Rational recursive input parsing | `_analyze_input_for_one_argument`, `_analyze_input`, `_special_div` |
| Weak canonical sharing | `memo_dict`, `WeakValueDictionary` |
| $\pi$ comparator | `_compute_series_generator_for_pi`, `_sign_func_for_pi` |
| $e$ comparator | `_compute_series_generator_for_e`, `_sign_func_for_e` |
| bounded-denominator localization | `_rational_bound_for_regular`, `rational_bound` |
| simplest rational in interval | `_simplest_rational_in_interval`, `simplest_rational_in_interval` |
| bulk rational arithmetic | `_sum_integer_ratios`, `_product_integer_ratios` |
| integer root | `_iroot_integer`, `iroot_integer`, `_iroot_rational` |
| arithmetic common scaffolding | `_generated_operator_add`, `_generated_operator_sub`, `_generated_operator_mul`, `_generated_operator_div` |
| comparator-progress reuse | `_wrapper_for_sign_function`, nearest-left/right state |
| projection / formatting algorithms | `float_bound`, `__float__`, `to_scientific_notation` |

---

# 2. `Rational`: lazy reduction, freezing, and interning

The reference implementation contains a useful two-state lifecycle:

```text
mutable working Rational
        ↓ normalize when required
frozen/hash-stable Rational
        ↓ explicit intern lookup
canonical shared Rational when available
```

The important idea is not the surrounding class/metaclass machinery, but the separation between:

1. arithmetic working state, where numerator/denominator may remain unreduced;
2. value-stable state, where sign and gcd normalization have been completed;
3. weak canonical sharing, where an equal live canonical object may be reused.

## 2.1 `hash()` as a freezing trigger

`__hash__()` in the reference code does **not** treat a mutable Rational as unhashable. Instead, first hashing:

1. obtains the reduced integer ratio;
2. computes the stable value hash;
3. freezes the current object;
4. optionally registers it in the weak cache.

This is directly useful for the current `Rational` contract:

$$
\text{working mutable}
\xrightarrow{\operatorname{hash}}
\text{normalized + frozen + hash-stable}.
$$

A Python `__hash__` call cannot replace the caller's object by another object, so hashing and interning should remain distinct operations.

## 2.2 `intern()` as explicit canonical sharing

`intern()` first canonicalizes the receiver's integer ratio and then performs a weak-cache lookup. If an equal canonical value is already alive, the reference code returns that cached frozen object **without freezing the receiver itself**; otherwise the receiver is frozen, inserted, and returned.

This distinction is worth preserving:

```text
hash(r):   freeze this object and return a stable value hash
intern(r): return the live canonical object for this value when available
```

## 2.3 Required adaptation

The useful lifecycle survives almost directly in the v1 contract:

```text
Rational(...) / constants  -> frozen + weak-interned canonical value
copy.copy(r) / r.__copy__() -> distinct mutable working copy
ordinary + - * /            -> fresh mutable working result
in-place op on mutable      -> mutate same object
in-place op on frozen       -> return fresh mutable result
hash(r)                     -> freeze this object
intern()                     -> return canonical weak-shared object
                               cache miss may freeze self; cache hit returns cached object
```

This lifecycle is intentionally modeled on `Computable_v6.py`; the adaptation removes only semantics incompatible with `Rational = Q`, especially denominator-zero special values.

The reference implementation also exposes mutable-working `numerator` / `denominator` assignment. v1 retains the useful **value-level setter** idea but deliberately strengthens the abstraction boundary: raw working coordinates live in private `._numerator` / `._denominator`, while public `.numerator` / `.denominator` are canonicalizing properties. Public reads simplify before returning; public setters parse/validate the RHS, simplify the receiver to canonical pre-assignment coordinates, then rewrite the private fields. This removes dependence of public semantics on whichever unreduced pair a particular arithmetic kernel happened to leave behind.

Advanced/debug documentation may mention read-only inspection of the underscore fields for performance investigation, but this is representation-sensitive and not a compatibility promise. Direct private-field writes are unsupported.

The reference representation in which denominator zero encodes infinities / NaN is not part of the formal `Rational = \mathbb Q` contract. Any reused arithmetic code must be simplified around the invariant

$$
q>0
$$

for every stored rational denominator.

## 2.4 Recursive Rational input composition

The reference parser separates scalar decoding from ratio composition. In particular, `_analyze_input_for_one_argument` recursively accepts a two-element tuple, while `_analyze_input` recursively parses both arguments of the two-argument constructor before applying exact division. This compositional idea matches the recursive `RationalInput` grammar fixed by the specification.

Conceptually:

```text
parse((u, v))       = parse(u) / parse(v)
Rational(u, v)      = parse(u) / parse(v)
```

where `u` and `v` may themselves be nested ratio inputs. The specification excludes the reference module's denominator-zero special-value semantics and follows Python numeric convention for `bool`, parsing `False/True` exactly as the integer values `0/1`. Constructor acceptance is determined by mathematical value: finite numeric objects with a guaranteed-finite exact rational-valued recognizer (for example real finite `complex`, real `GaussianRational`, or rational-valued `Algebraic`) may enter `RationalInput`. Tuple / string parsing remain explicit constructor syntax rather than implicit arithmetic coercion.

The same value-first principle is used more broadly for numeric subdomain parameters: if a numeric object can be finitely and exactly recognized as an integer / nonnegative integer / rational value, the runtime accepts or rejects it by that mathematical value rather than by nominal source type. The reference implementation is not normative for this coercion policy.

---

# 3. `GaussianRational`: architecture layer built from Rational primitives

`Computable_v6.py` does **not** provide the public `GaussianRational` regime, so this section is not an extraction claim about the reference source。It records how the architecture should reuse only the validated Rational substrate。

Recommended representation：

```python
(real: Rational, imag: Rational)
```

with persistent coordinates frozen / interned。Arithmetic stays entirely in Rational kernels：

$$
(a+bi)(c+di)=(ac-bd)+(ad+bc)i,
$$

$$
(a+bi)^{-1}=\frac{a-bi}{a^2+b^2}.
$$

The same type should be reused as：

- exact complex leaf payload；
- rational-rectangle corner / center；
- complex grid probe；
- exact polynomial-evaluation point。

This behavior is specification-driven and is not inferred from `Computable_v6.py`。

---

# 4. `WeakValueDictionary` as a canonical-sharing mechanism

The reference code uses a class-level

```python
WeakValueDictionary
```

keyed by canonical rational integer ratios. This is a strong implementation pattern for values or graph nodes that should be shared **only while some ordinary strong reference keeps them alive**.

The same general mechanism is useful in two separate places, with separate tables and keys:

1. frozen/interned `Rational` values;
2. structurally canonical `ComputableReal` / `ComputableComplex` DAG nodes.

The two uses must not be conflated:

- rational interning is value-canonical sharing in $\mathbb Q$;
- DAG hash-consing is structural sharing of semantic-computation nodes and must not invoke general numerical equality.

---

# 5. Exact comparator source for $e$

The reference implementation constructs $e$ through a stateful exact comparator rather than through floating-point approximation.

The generator behind `_compute_series_generator_for_e` produces alternating rational partial sums of

$$
e^{-1}
=
\sum_{k=0}^{\infty}\frac{(-1)^k}{k!}.
$$

For example, the stored sequence begins with alternating enclosures such as

$$
\frac12,
\qquad
\frac13,
\qquad
\frac38,
\ldots
$$

around $e^{-1}$. Taking reciprocal inequalities yields rational lower/upper information for $e$. `_sign_func_for_e` keeps the most recently useful pair and advances the series only when the queried rational lies inside the current unresolved region.

The reusable pattern is:

```text
exact rational query q
        ↓
check against persistent certified bounds
        ↓ unresolved
advance a mathematically certified series by finite work
        ↓
strict comparison once separation appears
```

For the current runtime this should be recast as a native source with:

- persistent monotone source progress;
- finite cooperative transitions;
- explicit potentially divergent comparison process;
- certified bounds committed to the node knowledge store.

No ordinary dunder should run the unbounded refinement loop implicitly.

---

# 6. Exact comparator source for $\pi$

The reference implementation uses the Chudnovsky series in a form adapted to exact rational comparison.

Let

$$
S
=
\sum_{k=0}^{\infty}
\frac{(-1)^k(6k)!(13591409+545140134k)}{(3k)!(k!)^3(640320)^{3k}}.
$$

The Chudnovsky identity can be written as

$$
\pi
=
\frac{426880\sqrt{10005}}{S}.
$$

The constants visible in the code satisfy

$$
\frac{640320^3}{24}
=
10939058860032000,
$$

and

$$
426880^2\cdot10005
=
1823176476672000.
$$

The comparator avoids introducing an approximate square root by squaring positive inequalities. If $q=n/d>0$, comparison with $\pi$ can be reduced to exact integer/rational inequalities involving

$$
q^2S^2
\quad\text{and}\quad
426880^2\cdot10005.
$$

The generator retains successive rational partial sums, and the comparator advances only until the query is strictly separated.

This is a valuable pattern for native computable constants:

1. choose a rapidly convergent exact series;
2. derive certified one-sided rational information;
3. transform the target comparison so only integer/rational arithmetic remains;
4. retain source progress across queries;
5. expose unbounded refinement only through explicit process APIs.

Before direct reuse, the exact alternating/error-bound proof should be written next to the implementation and tested independently from the code.

---

# 7. Bounded-denominator rational localization

`_rational_bound_for_regular` and `rational_bound` contain an efficient Euclidean/continued-fraction style traversal for locating a rational relative to a denominator bound.

The useful ideas are:

- avoid enumerating all fractions with denominator at most $N$;
- use quotient steps analogous to continued fractions / Farey navigation;
- jump by the largest admissible multiple before the denominator would exceed the bound;
- construct the two local grid representatives directly.

For exact rational input this can serve as the fast finite base case for the general searchable-grid localization machinery.

For `ComputableReal`, the public contracts are supplied by the theorem-backed grid layer rather than by copying this method literally. The same continued-fraction / Farey navigation ideas may serve as finite subroutines for `grid_bound(BoundedDenominatorGrid(...))`, `grid_localize(...)`, and the outer-neighbor search used by `grid_project(...)`. The guarantees sit inside the five-theorem grid structure: Theorems 1/2 form the near-adjacent / off-grid-adjacent enclosure pair, Theorems 3/4 form the near-nearest / no-midpoint-strict-nearest projection pair, and Theorem 5 gives mixed optimal output. Only Theorems 1, 3, and 5 map to the three unconditional v1 public observation methods. The reference method by itself establishes none of these semantic termination contracts.

---

# 8. `simplest_rational_in_interval`

The helper `_simplest_rational_in_interval` uses continued-fraction / Euclidean structure to find a rational of minimal structural complexity inside a rational interval, instead of scanning candidate denominators.

This is useful for:

- interval simplification;
- human-readable exact output;
- choosing compact rational witnesses;
- local grid utilities.

The implementation should be retained as an algorithmic reference, with its preconditions rewritten around finite `Rational` values only.

---

# 9. Bulk rational arithmetic with delayed normalization

`_sum_integer_ratios` and `_product_integer_ratios` accumulate numerator/denominator products without forcing gcd reduction after every term.

Ignoring the special-value branches, the central idea is exactly aligned with the mutable-working `Rational` model:

$$
\sum_i \frac{a_i}{b_i}
$$

or

$$
\prod_i \frac{a_i}{b_i}
$$

can be accumulated in an unreduced workspace and normalized only at a boundary where canonical value identity, hashing, interning, or persistent storage is required.

Possible further optimization should be benchmark-driven; for very large products, periodic gcd cancellation may outperform completely deferred normalization. The important reference idea is **normalization is a lifecycle decision, not an obligation after every arithmetic primitive**.

---

# 10. Integer $n$-th root by integer Newton iteration

`_iroot_integer` implements a pure-integer Newton iteration. For $n\ge0$ and degree $d\ge1$, it starts from a bit-length-based upper estimate and iterates

$$
x_{k+1}
=
\left\lfloor
\frac{(d-1)x_k+\left\lfloor n/x_k^{d-1}\right\rfloor}{d}
\right\rfloor
$$

while the estimate decreases.

It returns both the integer root candidate and an exactness flag. This is useful for:

- rational perfect-power detection;
- exact radical simplification;
- algebraic constructors;
- finite domain/canonicalization helpers.

It is especially valuable because correctness depends only on arbitrary-precision integer arithmetic.

---

# 11. Common scaffolding for arithmetic operations

The reference code has large factories such as:

```text
_generated_operator_add
_generated_operator_sub
_generated_operator_mul
_generated_operator_div
```

that centralize repeated dispatch patterns across rational/irrational operand categories, interval propagation, reflected operations, and special cases.

The **idea of centralizing common arithmetic scaffolding is worth retaining**, but the metaclass-driven injection mechanism is not required by the architecture.

A cleaner adaptation is to separate:

1. finite promotion/dispatch;
2. exact finite kernels for `Rational` / `GaussianRational` / `Algebraic`;
3. DAG-node constructors for general computable values;
4. operation-specific certificate propagation;
5. explicit domain-process factories for partial operations.

This prevents four arithmetic operators from independently reimplementing the same coercion and node-building rules while keeping control flow explicit and testable.

---

# 12. Persistent comparator and interval progress

`RealNumber._wrapper_for_sign_function` maintains information such as nearest known rational values on the left/right of a represented real and reuses them before asking the underlying source to do more work.

This is a useful precursor to the persistent certified-knowledge design:

```text
query arrives
    ↓
answer from stored certified facts if possible
    ↓ otherwise
advance source / process
    ↓
commit newly certified facts
```

The architecture generalizes this from a few hard-coded fields to a **geometry-first** monotone knowledge store with provenance, recoverable floors, residual semantic facts, and consistency checking. The preferred geometric representation is the strongest useful certified interval / rectangle; relation or membership information need not survive as separate records once enclosure / rectangle / recoverable floor already entails it.

User assertions follow three shared paths rather than one method per predicate:

```python
x.assume_relation(y, relation)
x.assume_membership(numeric_class, truth)
x.assume_grid_membership(grid, truth)
```

For strict-separable relations (`LESS`, `GREATER`, `NOT_EQUAL`), a true promise lets the evaluator keep refining until interval / rectangle geometry itself entails the relation. Equality-containing relations retain only the residual semantic content not captured by geometry. Numeric-domain membership promises are semantic facts about denotation and may remain residual. Grid membership is stronger: on a true standard-grid promise, locally finite candidate separation lets the runtime identify the exact grid point before return; on a false promise, refinement continues until the persistent interval lies entirely in a grid gap.

If a trusted promise is false and no finite contradiction is already known, any promise-dependent refinement may fail to terminate. This is outside the arbitrary-input termination guarantee.

A particularly useful behavior to preserve is exact-rational collapse: if a comparator ever obtains certified equality with a rational, subsequent queries can use that exact fact immediately; the same exact payload can serve as a recoverable floor for `downgrade()`.

---

## 12.1 Demand-driven evaluation lesson from the reference closures

The reference `RealNumber` arithmetic already contains a primitive form of downstream-driven refinement：a result comparator asks operands for tighter information only when current bounds are insufficient。The architecture preserves this **idea**, but replaces recursive closures with explicit DAG obligations。

Target design：

```text
query target
→ inspect persistent knowledge
→ derive only required child obligations
→ advance native / derived sources incrementally
→ commit certified facts
→ stop immediately when target contract is satisfied
```

Do not transplant uniform precision escalation or recursive closure chains。The evaluator should be iterative and query-centered。

## 12.2 Safe forgetting

The reference source frequently collapses exact Rational work into an equal Rational value; that is safe because the exact value fully replaces the arithmetic history。The same principle extends to `GaussianRational` and `Algebraic`。

It does **not** extend to replacing a general computable-real/complex subgraph by one current interval/rectangle. Such an enclosure is only partial knowledge and cannot support arbitrary future refinement。Graph compaction therefore needs an exact / algorithmically equivalent replacement, not a mere approximation。

---

## 12.3 Regime conversion and recoverable floors

The reference source contains several places where exact structure is discovered and cached. The specification gives this a uniform regime-conversion meaning:

```python
value.try_as(T)
value.downgrade()
value.downgrade_process()
value.upgrade(T)
```

`try_as(T)` is only for source-target pairs with guaranteed-finite exact recognition. `downgrade()` uses only currently available constructive information. `downgrade_process()` may search indefinitely and must commit every lower representation as soon as it is soundly discovered. `upgrade(T)` first performs ordinary downgrade, then lifts the lowest currently recoverable representation, while preserving enough information to recover that representation later.

For engineering reuse, this means exact-collapse opportunities should be surfaced as recoverable representations rather than merely as formatting/cache hints. Promotion should consume ordinary downgrade results before selecting the common target, but must never start `downgrade_process()` implicitly.

---

# 13. Binary64 / formatting reference utilities

`float_bound`, `__float__`, and `to_scientific_notation` remain useful **reference material**. v1 general semantic classes still do not expose Python correctly-rounded / exact-nearest machine-number conversion APIs such as `float(x)`, but they now do expose the theorem-backed single-point grid observation `grid_project(Binary64Grid())`, whose contract is only **near-nearest** rather than correctly rounded or strict nearest。

The highest-value reuse is narrower：

- exact binary64 bit-pattern / integer-ratio conversion helpers, including coordinatewise exact decoding of finite Python `complex` for interoperability；
- adjacent / near-adjacent binary64 navigation ideas for `Binary64Grid`, including predecessor / successor traversal useful for the near-nearest projection theorem；
- correctly-rounded projection code for finite exact classes (`Rational`, real `GaussianRational`, real `Algebraic`)；
- formatting algorithms that never feed machine-float tolerance back into correctness。

Reference `float_bound` method names / control flow are **not** normative public API. General `ComputableReal` uses `grid_bound(Binary64Grid())`, `grid_project(Binary64Grid())`, and `grid_localize(Binary64Grid())`. These correspond respectively to Theorem 1's near-adjacent bracket, Theorem 3's finite near-nearest point, and Theorem 5's mixed optimal localization. Theorems 2 and 4 are promised mathematical strengthenings rather than additional public spellings. None of these licenses `ComputableReal.__float__` or claims correctly-rounded machine projection。

---

# 14. Small local algebraic simplifications

The arithmetic code contains finite identities such as detecting the same operand in

```python
x + x
```

and replacing it by a scaled form. The specific object-identity shortcuts are not a general equality mechanism, but they illustrate a useful principle for the `ComputableReal` / `ComputableComplex` DAG:

> Perform only simplifications justified by finite structural information; never invoke general semantic equality merely to normalize the graph.

In the computation DAG this principle becomes canonical structural identity, flattening, rational coefficient collection, and weak hash-consing.

---

# 15. Mechanisms not to transplant directly

Several mechanisms in the reference module are tightly coupled to a different low-level representation strategy and should be treated only as cautionary examples.

## 15.1 Denominator-zero special values

A `Rational` in the formal runtime denotes exactly an element of $\mathbb Q$. Infinity and NaN, if needed for auxiliary bounds or projections, require separate sentinels or types.

## 15.2 Implicit closure-based computation graph

The reference `RealNumber` arithmetic captures operand dependencies through Python closures. For general computable numbers this makes dependency structure harder to inspect, flatten, hash-cons, traverse iteratively, and benchmark.

The architecture uses an explicit DAG for `ComputableReal` / `ComputableComplex` only; `GaussianRational` is an exact leaf/value regime, not a semantic DAG domain.

## 15.3 Hidden unbounded semantic work in ordinary operators

Any loop whose termination depends on resolving a generally undecidable semantic fact must not be hidden in ordinary Python dunders or ordinary knowledge / certificate-gated operations. Such work belongs in explicit `DecisionProcess` / `*_process` APIs.

The deliberate exception is a documented trust-boundary assertion operation: there the user supplies the semantic fact as a promised precondition. Promise-dependent refinement may be unbounded when required to absorb strict relations or grid membership/nonmembership into persistent geometry or exact recoverable representation. Nontermination on a false assertion is therefore a precondition violation, not a hidden semantic decision strategy.

## 15.4 Metaclass-generated public behavior

Metaclass code can remove duplication, but it also makes public control flow, state ownership, and debugging much harder to audit. Reuse the shared-operation factoring idea through ordinary helpers/builders/registries unless a metaclass provides a measurable benefit without obscuring the semantic contract.

## 15.5 Global mutable source state without an explicit ownership contract

The $\pi$ and $e$ constants demonstrate useful persistent series progress. In the runtime architecture, that progress should be an explicit native-source state with documented ownership and finite cooperative transitions. The project does not promise unsynchronized thread safety.

---

# 16. Suggested extraction order

When implementing from the reference source, the highest-value extraction order is:

1. `Rational` normalization / freeze / weak-intern mechanics;
2. build the `GaussianRational` / rational-rectangle layer from those Rational primitives (specification-driven work, not direct extraction);
3. integer `iroot`;
4. bounded-denominator and simplest-rational utilities;
5. bulk rational arithmetic;
6. $e$ native comparator source;
7. $\pi$ native comparator source;
8. persistent comparator-bound reuse generalized into certified knowledge;
9. common arithmetic scaffolding rewritten around explicit promotion and DAG builders;
10. projection / formatting algorithms.

Each extraction should be accompanied by tests written from `05_TEST_AND_BENCHMARK_SPEC.md`, not by behavioral equivalence tests against the reference module alone.

## GaussianRational constructor note

The normative constructor is overloaded as `GaussianRational()`, `GaussianRational(value)`, and `GaussianRational(real, imag)`. One-argument construction follows the guaranteed-finite exact value-recognition bridge; two-argument construction is coordinate parsing. Do not infer the public constructor surface from `Computable_v6.py`.

## General-complex realness and comparison boundary

Real-domain discovery is explicit for general `ComputableComplex`. `ComputableReal.compare_process(...)` must not hidden-start a potentially divergent domain check when given an uncertified complex operand. `ComputableComplex.membership_process(ComputableReal)` is the explicit resumable operation; when it resolves, the resulting membership evidence is persistent and later real comparison may reuse it. End-user documentation should teach this workflow directly and explain that a still-`Pending` process means real ordering is not yet available. This semantic/API contract is defined by the specification, not inferred from `Computable_v6.py`.
