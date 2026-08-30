# Computable：Implementation Roadmap

本 Roadmap 只描述程式實作順序。Formal mathematics 以 `06_MATHEMATICAL_FOUNDATIONS.md` 為 specification prerequisite，不列為 runtime phase。

每一 phase 完成時必同時具備：

- implementation；
- unit / property tests；
- semantic contract tests；
- benchmark（若涉及 hot path / scaling）；
- module-level documentation。

---

# Phase 1 — Core package skeleton

## Goal

建立五個 numeric domains 可共存、沒有 concrete-class circular import 的骨架。

## Implement

```text
computable/core/
    kinds.py
    family.py
    promotion.py
    decision.py
    certificates.py
    knowledge.py
    errors.py
```

建立 minimal shells：

```text
Rational
GaussianRational
Algebraic
ComputableReal
ComputableComplex
```

Infrastructure：

```text
NumericKind
NumericFamily
PromotionRegistry
ConversionRegistry
Order
Relation
Pending
Resolved
DecisionProcess
certificate provenance
knowledge-store interfaces
errors
```

## Completion

- five concrete modules import cleanly；
- bootstrap registration works；
- no circular import exception；
- `Pending` truth-test raises；
- synthetic `DecisionProcess.advance(work=N)` finite；
- resolved result stable。

---

# Phase 2 — Rational exact substrate

## Goal

建立 exact hot path。

## Implement

- private working integer fields `_numerator` / `_denominator` with positive-denominator invariant；
- public `@property` `.numerator` / `.denominator` getters that finite-simplify before reading canonical coordinates；
- denominator-positive normalization；
- public recursive `RationalInput` conversion kernel：finite-rational numeric values (`Rational` / Python `int-bool` / `fractions.Fraction` / finite `float` / real finite `complex` / real `GaussianRational` / rational-valued `Algebraic`) plus exact `str` / nested 2-tuple ratio；higher exact-class branches wire through the shared finite subdomain-recognition registry when those phases are available；
- one-argument tuple ratio and two-argument `Rational(u, v)` both recursively parse numerator / denominator before exact division；
- nested zero-divisor、non-finite-float、malformed-string、bad-tuple rejection；
- external numeric scalar conversion for arithmetic / exact-class relations：Python `int` (including `bool` as `0/1`) / `fractions.Fraction` / finite `float` -> `Rational`；finite Python `complex` -> coordinatewise exact `GaussianRational` lift（wire when GaussianRational phase is available）；non-finite component finite `ValueError`；
- central guaranteed-finite exact subdomain-recognition registry per `02` §14：rational-valued / Gaussian-rational-valued / integer-valued / nonnegative-integer-valued recognizers；numeric positions reuse this registry instead of nominal type checks；general computable classes and parser-only syntax do not enter hidden recognition；
- mutable working lifecycle；
- public `Rational(...)` / constants frozen-interned path；
- `copy.copy(r)` / `r.__copy__()` working path；
- in-place arithmetic mutable/frozen behavior per `02`；
- public mutable-working `.numerator` / `.denominator` value-level setters: reject frozen receiver first, parse/validate RHS transactionally, simplify receiver to canonical pre-assignment coordinates, then rewrite private integer fields; include hash invalidation, positive-denominator restoration, and recursive `RationalInput` support；
- keep direct writes to `._numerator` / `._denominator` unsupported; advanced/debug documentation may expose read-only inspection only；
- lazy gcd reduction + public finite `simplify()` (reduce in place without freezing mutable receiver; frozen no-op)；
- frozen state；
- `intern()`；
- weak canonical cache；
- stable exact hash compatible with every equal scalar in the finite exact bridge, including Python `int/bool` / `fractions.Fraction` / finite `float` / zero-imaginary finite `complex`；
- arithmetic / comparison + integer powers through the shared finite exact integer-valued recognizer, including negative-power zero checks and $0^0=1$；
- finite `bool()` zero-test；
- floor / ceil / round / integer conversion；
- correctly-rounded **finite-output** binary64 `float()` / `complex()` projection；follow Python `int` / `Fraction` exact-number overflow semantics, with `OverflowError` at and beyond $T_{64}=2^{1024}-2^{970}$；
- bigint integer-root helpers；
- denominator-bounded rational helpers。

## Required benchmark

- random multiplication chains；
- random addition chains；
- high cancellation；
- shared denominator；
- long bulk sum / product；
- bigint sizes 32–8192+ bits。

## Completion

- constructor accepted-input / error semantics match `02`；
- `Rational(0.1)` captures exact binary64 value while `Rational("0.1") == Rational(1,10)`；
- constructor / `copy.copy` / non-in-place / in-place lifecycle semantics match `02`；
- `hash()` is total on mutable working values and freezes them after finite normalization；
- repeated hash is stable and frozen values reject value mutation；
- `intern()` returns canonical + frozen + hash-stable weak-interned value；
- persistent ownership only stores interned rationals；
- no infinity / NaN Rational values；
- correctness path不得以 machine floating arithmetic / tolerance 作 exact evidence；finite-float input decoding via exact binary64 representation is allowed。

---

# Phase 3 — GaussianRational exact complex substrate

## Goal

建立 $\mathbb Q(i)$ 的 cheap exact field、rational rectangle geometry 與 complex probe substrate，讓簡單 exact complex values 不必進 general `Algebraic` machinery。

## Implement

```text
GaussianRational()
GaussianRational(value)
GaussianRational(real, imag)
RationalRectangle = ((a,b),(c,d))  # public/API shape
RationalClosedBox              # optional internal immutable geometry wrapper
```

Requirements：

- zero-argument construction gives $0$；one-argument value construction accepts existing `GaussianRational`, finite Python `complex`, Gaussian-rational-valued `Algebraic`, or `RationalInput` as a real value；two-argument construction is exclusively coordinate construction；
- coordinate paths recursively parse `RationalInput`，then persistent coordinates frozen / interned；general computable inputs never trigger hidden $\mathbb Q(i)$ membership search；
- finite exact `+ - * /` + integer powers through the shared finite exact integer-valued recognizer, including negative-power zero checks and $0^0=1$；
- conjugation / norm-square；
- realness / zero / coordinate extraction；
- finite `bool()` zero-test；
- real-only ordering；
- real-only `int` / floor / ceil / half-to-even `round`；`ndigits` 走 shared finite exact integer-valued recognizer，指定 digits 時回 exact `Rational`；
- cross-type equality / hash compatibility；
- correctly-rounded finite-coordinate projections；any coordinate at/beyond $T_{64}$ raises `OverflowError`, never returns projection infinity；
- exact lossless conversion between public tuple rectangle and any internal `RationalClosedBox`；
- rectangle containment / intersection / subdivision / center / corners；
- exact Horner polynomial evaluation scaffold over $\mathbb Q(i)$；
- optional weak interning keyed by canonical rational coordinates。

## Required benchmark

- random Gaussian-rational arithmetic chains；
- repeated multiplication/division with large rational coordinates；
- rectangle subdivision at increasing endpoint bit sizes；
- exact polynomial evaluation at Gaussian-rational points。

## Completion

- all field laws property-tested；
- real-only integer/rounding protocols are finite exact and non-real inputs finite `TypeError`；
- `GaussianRational(a,0)` behaves consistently with exact real promotion；
- rectangle endpoints/corners remain exact；finite-float RationalInput may be decoded exactly, but no machine floating arithmetic / tolerance participates in correctness；
- polynomial evaluation stays inside Rational/GaussianRational kernel。

---

# Phase 4 — Integer polynomial kernel

## Goal

建立 Algebraic 的 finite exact foundation。

## Implement order

1. freeze constant-first coefficient convention $(a_0,\ldots,a_n)\leftrightarrow a_0+\cdots+a_nX^n$ across constructor、storage、serialization and all kernels；
2. validate every coefficient through the shared finite exact integer-valued recognizer and store the resulting ordinary Python `int`；
3. canonicalize by trailing-zero trimming only, preserve content/sign exactly, and use the unique zero representation `Polynomial((0,))`；
4. public immutable observations `.coefficients / .degree / .leading_coefficient / bool`; one shared finite integer-scalar recognizer across Python `int` / `bool`, `Fraction`, finite `float`, finite `complex`, `Rational`, `GaussianRational`, and `Algebraic`, reused by constant-polynomial equality/hash and scalar arithmetic；
5. unary sign, add/sub/mul, reflected scalar arithmetic: accept exactly the recognized mathematical integers and embed them as constant polynomials; recognized non-integral/non-real scalars finite `TypeError`; powers use the same integer recognizer and then require non-negative value；
6. `derivative(order=1)` uses the same finite integer recognizer and then requires non-negative value；public Horner `evaluate/__call__` goes through the scalar promotion registry；finite Python `complex` evaluates through exact Gaussian lift, exact classes evaluate finitely, and general computable inputs construct the promoted DAG finitely；
7. `content()` / `primitive_part()` with non-negative content and sign-preserving primitive part；
8. frozen `PseudoDivisionResult` and canonical positive-scale `pseudo_divmod()`；polynomial-operand argument uses the shared integer-scalar recognizer for constant embedding；
9. `exact_div()` with the same operand coercion and `TypeError` / `ZeroDivisionError` / non-divisibility `ValueError` split；
10. canonical integer-polynomial `gcd()` including content gcd and positive-leading associate normalization；
11. frozen `PolynomialFactor` / `PolynomialFactorization` payloads；
12. `square_free_decomposition()` with one combined positive-leading primitive square-free factor per multiplicity；
13. exact irreducible `factor()` over $\mathbb Z[X]$ / $\mathbb Q[X]$ with deterministic factor ordering；
14. nonzero-input `resultant()` exact integer contract；
15. canonical positive-rescaled integer `sturm_sequence()`；
16. public closed-interval distinct `real_root_count()` and `isolate_real_roots()`；
17. public closed-rectangle distinct `complex_root_count()` and `isolate_complex_roots()`；
18. endpoint parser / canonical frozen Rational geometry shared with `Algebraic(polynomial, box)`；
19. reuse factorization / resultant / isolation kernels for minimal-polynomial support needed by lazy `Algebraic` hash；do not build a divergent internal polynomial stack。

## Completion

- every `02` §7.9–§7.13 public `Polynomial` spelling exists with the specified return type and finite exception behavior；
- constant-polynomial equality implements the full finite exact scalar bridge from `02`: both operand orders agree for Python `int` / `bool`, `Fraction`, finite `float`, finite `complex`, `Rational`, `GaussianRational`, and `Algebraic`; non-integral/non-real values compare false, general computable classes do not enter this bridge, and every equal scalar shares the constant polynomial's Python-integer hash；
- all polynomial methods are guaranteed finite；zero-polynomial root/factorization domains finite `ValueError` rather than semantic divergence；
- arithmetic remains in $\mathbb Z[X]$ and does not silently promote coefficient domain；
- all algorithms use integer / Rational exact arithmetic；
- pseudo-division identity, exact division, gcd normalization, reconstruction from factorization, and resultant identities hold exactly；
- root counts count distinct roots, include closed-boundary roots, and agree with isolation output；
- real isolation returns pairwise disjoint sorted rational closed intervals；complex isolation returns pairwise disjoint deterministic rational closed rectangles；
- closed rectangle unique-distinct-root certificates work even if root lies on boundary；
- no float correctness dependency。

---
# Phase 5 — Unified Algebraic

## Goal

完整支援 $\overline{\mathbb Q}$ 的 finite exact class，同時保留 lazy representation refinement。

## Implement order

1. public `Algebraic(value)` overload following the finite exact scalar bridge：existing `Algebraic` preserves denotation；finite Python `complex` exact-lifts to `GaussianRational`；`GaussianRational` embeds directly；recursive `RationalInput` first parses exactly to `Rational`；general computable classes do not trigger algebraicity search；
2. public `Algebraic(polynomial, box)` overload reserved for `Polynomial` + rational closed-rectangle unique-root representation；box endpoints accept `RationalInput` at the boundary and are interned before storage；
3. representation-preserving isolation refinement；
4. exact zero test + finite `bool()`；
5. exact equality；
6. lazy `is_real()`；
7. conjugation；
8. real / imaginary parts；
9. real ordering；
10. negation；
11. addition / subtraction；
12. multiplication；
13. division semantics（reciprocal 以 numerator $1$ 的 division／internal reciprocal primitive 實作）；
14. integer powers through the shared finite exact integer-valued recognizer（negative-power zero checks, $0^0=1$）；
15. public finite `try_as(Rational)`；
16. public finite `try_as(GaussianRational)`（同一 capability 亦供 cross-type hash tier internal reuse）；
17. lazy minimal polynomial；
18. canonical root ordering by $(|z|,\operatorname{Arg}z)$ with $\operatorname{Arg}\in[0,2\pi)$；
19. canonical root index；
20. stable value hash；
21. real-only `int` / floor / ceil / half-to-even `round`；`ndigits` 走 shared finite exact integer-valued recognizer，指定 digits 時回 exact `Rational`；
22. correctly-rounded finite real `float()` with exact-number overflow boundary $T_{64}=2^{1024}-2^{970}$ and `OverflowError` at/beyond boundary；
23. finite-coordinate `complex()` projection with the same per-coordinate overflow rule。

## Completion

- no real / complex algebraic subclasses；
- constructor does not eager force minimal polynomial / realness；
- defining polynomial may lazy change without denotation change；
- isolator may refine；
- equal values from distinct $(P,B)$ compare equal；
- equal values hash equal；
- real-only integer/rounding protocols are finite exact, midpoint ties use half-to-even, and non-real inputs finite `TypeError`；
- Algebraic values in $\mathbb Q$ / $\mathbb Q(i)$ use cross-type compatible Rational / GaussianRational hash tier；
- hash remains stable after later refinement。

---

# Phase 6 — Knowledge store and assertion substrate

## Goal

建立 persistent certified knowledge infrastructure before general semantic graphs depend on it；此 phase 完成 assertion / residual-knowledge / recoverable-floor substrate，不要求 general semantic refinement engine 已存在。

## Implement

- provenance kinds；
- interval / rectangle as primary geometric carriers；
- residual relation / membership fact store；
- recoverable-floor record與 dominance ordering；
- finite inference rules from enclosure geometry與 numeric-domain inclusion；
- contradiction detection；
- `InconsistentKnowledgeError`；
- geometry / floor dominance compaction；
- transient certificate -> persistent carrier absorption；
- `Relation` enum與 assertion transaction skeleton：

```python
assume_relation
assume_membership
assume_grid_membership
```

Assertion substrate rules：

- `LESS` / `GREATER` / `NOT_EQUAL`：定義 `RefinementProvider` / callback protocol與 transaction semantics，synthetic provider可測「refine until geometry entails relation」；
- `EQUAL` / `LESS_EQUAL` / `GREATER_EQUAL`：允許 geometric propagation + residual relation commit；
- numeric-domain membership：保存 mathematical-domain fact並做 inclusion implications，不把 Python class identity當 semantics；
- grid-membership True：定義 unique-grid-point identification transaction與 exact-floor commit hook；
- grid-membership False：定義 refine-to-grid-gap transaction；
- false user promise need not terminate unless contradiction becomes finitely detectable。

General `ComputableReal` / `ComputableComplex` evaluator integration在 Phase 12 / 15 完成。

## Completion

- synthetic strict relation promise只在 geometry已 entail後返回；
- equality-containing relation可保存 residual semantics且做 sound geometric propagation；
- membership facts依 domain lattice propagation；
- grid True synthetic provider可在返回前 commit exact identified point；grid False可在返回前 commit gap enclosure；
- no redundant standalone predicate remains when enclosure / rectangle / recoverable floor already subsumes it, except required provenance summary；
- detectable contradiction rejects transaction；
- false trusted assertions are documented outside termination guarantee；
- compaction never loses semantic knowledge relative to accepted trust assumptions。

# Phase 7 — Decision runtime

## Goal

建立 explicit potentially divergent computation model。

## Implement

- mutable resumable `DecisionProcess[T]`；
- exactly bounded finite transition loop；
- public work validation through shared finite exact integer-valued recognizer, followed by non-negative check；
- terminal exception caching；
- map / combine / short-circuit；
- fair dovetail scheduler；
- certificate emission / immediate knowledge commit；
- unbounded `.resolve()`。

## Completion

- every finite-work call returns / raises finitely；
- work count means at most N cooperative transitions；
- repeated calls continue, not restart；
- `work=0` performs no transition；
- terminal exception re-raises without extra work；
- permanently pending synthetic process stable；
- fair scheduling no starvation。

---

# Phase 8 — Minimal ComputableReal source layer

## Goal

建立 rational-comparator native-source entry，並由它提供 guaranteed-finite width enclosure。Rational-probe comparison是 internal source capability；public semantic comparison在 Phase 14 統一由 `compare_process` / `relation_process` 暴露。

## Implement

```text
RationalComparatorSource protocol
NativeComparatorRealNode
ExactRealLeaf
```

Public capability：

```python
ComputableReal.from_comparator_source(source)
x.bound(width=epsilon)
```

Internal source capability：

```python
source.compare_rational_process(q)
```

`width` goes through the shared guaranteed-finite positive-rational numeric-value recognizer; do not require nominal `Rational` type and do not attempt hidden recognition on general computable inputs.

Requirements：

- rational query 在交給 source 前 frozen/interned；
- source denotation lifetime-stable；
- emitted comparison result sound；
- source progress persistent / reusable；
- node strongly owns source unless safe compiled replacement exists；
- comparator -> bound 使用 equality-safe fair search / optimized equivalent，不採 exact-hit 會卡住的 naive bisection。

## Completion

- exact rational hit source comparison可 Pending；
- `bound(width)` always finite；
- repeated queries reuse source progress / certified knowledge；
- public surface沒有第二個 rational-specific comparison method。

# Phase 9 — Grid-resolution layer

## Goal

把 `06` 的五個 localization/projection termination theorems落到一維 real grid layer。Formal順序固定為：

1. unconditional near-adjacent enclosure；
2. off-grid promised adjacent enclosure；
3. unconditional near-nearest projection；
4. no-midpoint promised strict-nearest projection；
5. mixed optimal output。

其中只有 Theorems 1 / 3 / 5 形成三個 unconditional v1 public observation APIs；Theorems 2 / 4 是必須有 regression coverage 的 promised mathematical strengthenings，不對應額外 public method。

## Standard grids

```python
IntegerGrid()
BoundedDenominatorGrid(max_denominator=N)
Binary64Grid()
```

`max_denominator` uses the shared finite exact integer-valued recognizer and then requires $N\ge1$; integral numeric values from different exact source types are equivalent inputs.

可有 internal `Grid` protocol；v1 不要求 arbitrary user-defined grid plugin API，也不包含 `DyadicGrid`。
三個 built-in grid 的 canonical representations 必成為 `06` 的 **searchable computably embedded exact ordered grid realizations**：

- grid-point equality / order trichotomy finite total；
- searchability由 terminating interior-search operation提供；
- 每個 finite grid point都有 guaranteed-finite same-value lift到 internal `ComputableReal` / comparator presentation；
- standard grid adapter提供對 arbitrary `ComputableReal` 的 global two-sided bounding。

Target-vs-grid comparison與 finite-pair midpoint probes走共同 embedding / real-comparator path，不各自實作一套 grid-specific semantic hook。一般 theorem不反向要求所有可能 grid interpretations都採 v1 的 canonical exact representation discipline。

## Public API

```python
x.grid_bound(grid)
x.grid_project(grid)
x.grid_localize(grid)
```

並實作 `GridBracket`、`GridApproximation`、`GridLocalization`、`GridDirection`。`grid_project()` 直接回 canonical finite grid point，直接回傳 canonical finite grid point，不另加 wrapper payload。

## Completion

- built-in grids 的 exact ordered realization / equality / order / finite-point computable-real embedding / search contracts通過；
- global ComputableReal bounding adapter通過；
- target-grid comparison與 arbitrary finite-pair midpoint construction從共同 embedding path導出；
- theorem-1 near-adjacent `grid_bound()` contract通過；
- theorem-2 off-grid promise regression：同一 search在 $x\notin G$ 時 guaranteed-finite 升級成 adjacent bracket，promise外不得輸出 unsound bracket；
- theorem-3 near-nearest `grid_project()` contract通過：output $g$ 至多有一個 finite grid point嚴格更近；
- theorem-4 no-midpoint promise regression：在 $x\notin M_G$ 時 strict-nearest search guaranteed finite，midpoint boundary外不得靠 tolerance決定；
- theorem-5 mixed `grid_localize()` contract通過：adjacent bracket / strict-nearest channels至少一個存在，且 implementation fair-dovetail兩個 optimal partial searches；
- exact grid hit不要求 `grid_bound()` point result，midpoint tie不阻塞 `grid_project()`；
- `Binary64Grid()` 含真正的 Python `±inf` endpoints、排除 NaN；strict-nearest channel與 near-nearest projection point對 finite target必 finite，即使 target超出 finite binary64 range；
- infinite initial span regression仍 finite terminate；
- implementation 不做 whole-span exhaustive enumeration作一般策略。

---

# Phase 10 — Real computation DAG core

## Goal

建立只屬於 general semantic real 的 explicit dependency graph。

## Implement

```text
RealNode
NativeRealNode
ExactRealLeaf
DerivedRealNode
```

第一批 derived：

```text
SumNode
ProductNode
NegNode
ReciprocalNode
```

並建立：

- immutable structural key；
- weak hash-cons table；
- iterative traversal；
- `EvaluationTask`；
- query-local memo；
- persistent knowledge on all nodes；
- finite structural introspection `ComputableReal.exact_source()`：only exact leaf / semantics-preserving exact replacement returns payload, otherwise `None`。

## Completion

- Rational / GaussianRational / Algebraic standalone arithmetic不進 DAG；
- exact values only lift when entering ComputableReal / ComputableComplex graph；
- same structural key -> same live node identity；
- $10^5$-scale deep chain evaluation avoids recursion limit。

---

## Demand-driven evaluator requirement

Before structural normalization is considered complete, the real graph layer must expose an iterative evaluation-task skeleton capable of：

```text
target query
→ inspect persistent knowledge
→ derive child resolution/proof obligations
→ refine only needed upstream nodes
→ commit certified facts
→ stop as soon as target contract is satisfied
```

First implementation may use conservative obligation allocation；global optimal precision allocation is not required。Unqueried branches must not advance native source progress merely because they exist in the graph。

---

# Phase 11 — Structural normalization

## Goal

抵抗 reference-chain complexity growth，同時利用 graph 做 safe finite rewrites。

## Implement

### Sum

- associative flatten；
- Rational constant fold；
- structural-key coefficient collection；
- zero elimination。

### Product

- associative flatten；
- Rational coefficient fold；
- structural-key **non-negative** occurrence counts / exponents；
- zero / one rules。

### Negation

- double negation；
- coefficient absorption。

## Construction-scaling requirement

不得因每次 append 重複 copy accumulated map 造成 long-chain obvious quadratic behavior。

## Completion

- $x+x+x\to3x$ by structural identity only；
- no semantic equality call in normalization；
- node weak interning stable；
- rewrite property tests complete。

---

# Phase 12 — Persistent graph knowledge and regime-floor integration

## Goal

讓 native / derived real nodes 都能跨 query reuse certified facts，並完成 real-side trust assertions與 guaranteed-finite regime transitions。

## Implement

- node knowledge store integration；
- immediate process-to-node commit；
- interval intersection and strengthening；
- relation consequences read from enclosure geometry；
- residual relation / membership store；
- geometry-first knowledge compaction；
- recoverable floor commit / dominance；
- source progress reuse on native nodes；
- public real assertions integration：

```python
x.assume_relation(y, relation)
x.assume_membership(numeric_class, truth)
x.assume_grid_membership(grid, truth)
```

- grid True promise在 return前 unique-point identification + exact `Rational` floor commit；grid False promise在 return前 gap enclosure commit；
- `downgrade()` guaranteed-finite floor selection；
- `upgrade(T)`：先 `downgrade()` 再 legal lift，並保存 pre-upgrade recoverability；
- ordinary promotion改為 downgrade-first target selection；
- derived certified result reuse independent of query-local memo。

## Completion

- downstream query A proves fact -> branch B reuses；
- true strict relation assertions return only after enclosure geometry entails them；
- equality-containing assertions保留必要 residual relation；
- bounded-denominator grid membership True可 finite collapse成 exact `Rational`；
- off-grid promise可 finite commit gap enclosure；
- upgrade後再次 `downgrade()` 可恢復 pre-upgrade lowest representation；
- derived node can retain proven enclosure / recoverable floor；
- query memo may disappear without losing persistent facts；
- source computation prefixes not repeated unnecessarily。

# Phase 13 — Partial-operation semantics

## Goal

完整落實 field division 的「ordinary finite / process explicit divergence」。

## Implement

```python
divide_process
```

Ordinary：

```python
x / y
```

Domain predicate透過 common relation/evidence machinery判斷 denominator是否已 certified nonzero。倒數 public process不另設名稱，以 `divide_process(1, y)` 表達；internal evaluator仍可使用 reciprocal-specific task / `ReciprocalNode`。

本 phase 先完成 `ComputableReal` division；`ComputableComplex` 的同一 semantics 在 Phase 15 接線。

## Completion

- nonzero 已由 persistent enclosure / accepted evidence certified -> finite construction；
- zero certified -> finite `ZeroDivisionError`；
- unresolved domain -> `UnresolvedDomainError`；
- process invalidity discovered -> terminal `ZeroDivisionError`；
- no ordinary API calls `.resolve()` internally；
- only one public partial-operation process spelling for division。

# Phase 14 — General real semantic decisions and semantic downgrade search

Implement：

```python
x.compare_process(y)
x.relation_process(y, relation)
x.membership_process(numeric_class)
x.downgrade_process()
```

Implementation contract：

- `compare_process` handles full three-way real order；rational probe uses the same public method；
- `relation_process` derives the six `Relation` predicates from shared comparison/equality evidence rather than separate sign/nonzero/equality process classes；
- `membership_process` asks mathematical-domain membership and may remain `Pending` where positive/negative recognition is unavailable；
- `downgrade_process` fair-dovetails registered sound recognition / reconstruction strategies；every lower representation found is committed immediately as recoverable floor；resolve only when the lowest regime is established；
- implement value-based finite promotion for `ComputableReal` and registered finite exact numeric operands；known non-real exact values finite `TypeError` for ordered relations；
- keep dispatch extensible for complex integration without depending on a concrete complex implementation；
- public semantic query surface is limited to `compare_process`、`relation_process`、`membership_process` plus explicitly specified operation processes；source-specific rational probes remain internal protocol capabilities。

## Completion

- strict inequality cases eventually resolve；
- equality boundary may remain Pending without certificate；
- relation truth matches the six order-cell subsets；
- membership process commits reusable domain facts；
- lower floor discovered by `downgrade_process` is visible to ordinary `downgrade()` even while process remains `Pending`；
- rich comparisons、truthiness、hash、machine projections all obey finite Python protocol restrictions；
- process docs state boundary behavior。

# Phase 15 — ComputableComplex core

## Goal

建立 general semantic complex graph，並把 relation / membership / assertions / regime transitions接到 coordinate evaluators。

## Implement

```text
ExactComplexLeaf          # Rational / GaussianRational / Algebraic payloads
RealEmbeddingComplexNode # child = ComputableReal
ComplexFromPartsNode     # real + imag*i from two ComputableReal children
DerivedComplexNode
```

API：

```python
ComputableComplex.from_parts(real, imag)
z.real_part()
z.imag_part()
z.box(width=...)
z.exact_source()
z.membership_process(numeric_class)
z.relation_process(w, relation)  # EQUAL / NOT_EQUAL only
z.component_compare_process(w)
z.direction_process(w, direction=u)
z.downgrade()
z.downgrade_process()
z.upgrade(numeric_class)
z.assume_relation(w, relation)
z.assume_membership(numeric_class, truth)
divide_process(z, w)
```

`membership_process(ComputableReal)` 必 commit persistent real/non-real evidence。Complete the cross-regime process dispatch from Phase 14: real `compare_process` may consume already-persisted real-domain evidence and compare through `real_part()`, but finite-rejects uncertified / certified-non-real complex without starting membership work. The same certified-real bridge is reused by `from_parts(...)` coordinate coercion. End-user documentation explicitly teaches `membership_process(ComputableReal)` first, then real-domain APIs only after `True`; a `Pending` process remains user-owned state。

Complex `relation_process`只接受 equality / inequality；`NOT_EQUAL` strict-separation evidence eventually resolves true，`EQUAL` boundary可 Pending。Assertions use the same geometry/residual rules as `02`。Arithmetic：`+ - *` + certificate-gated `/`；division process沿用 Phase 13 framework。

## Completion

- arbitrary Algebraic direct exact leaf payload；
- general ComputableReal embedding uses `RealEmbeddingComplexNode`, never `ExactComplexLeaf`；
- `from_parts` uses a dedicated two-coordinate derived node；
- no native-complex source protocol required；
- zero direction rejected finitely；
- no eager Algebraic real/imag split required；
- general real-domain membership remains non-total；
- graph weak interning / knowledge rules mirror real graph；
- `upgrade(ComputableComplex)` preserves any lower recoverable real/exact floor。

# Phase 16 — Complex structural normalization

Flatten complex sums / products、exact coefficients、coordinate view nodes、iterative evaluation、persistent facts、query memo。

## Completion

- deep graph safe；
- no semantic equality normalization；
- real / imag view does not materialize approximate value；
- shared nodes share knowledge。

---

# Phase 17 — Performance and memory hardening

Profile axes：

- native-node count；
- derived-node count；
- fan-out / graph depth；
- one-shot / repeated-query；
- knowledge density；
- source progress size；
- bigint size；
- target width；
- selected standard grid / grid parameter。

Possible optimizations only after profiler evidence：

- specialized builders；
- persistent map implementation；
- packed polynomial storage；
- adaptive Rational reduction；
- knowledge compaction tuning；
- source-specific fast paths。

Safe-forgetting measurements 必區分 weak GC、knowledge compaction 與 semantics-preserving graph compaction。Never replace a general computable subtree by one finite interval / rectangle alone。

---

# Phase 18 — Packaging and documentation

Complete：

- public API reference；
- nontermination / `Pending` examples；
- trust-user assertion semantics；
- theorem-1 / theorem-3 / theorem-5 (`grid_bound` / `grid_project` / `grid_localize`) examples for all three standard grids，並說明 theorem-2 / theorem-4 promised strengthenings；
- user-defined comparator-source guide；
- benchmark report；
- package build；
- optional generated single-file distribution。

Release only after full regression gate。

---

# Explicitly out of first-edition scope

以下不屬 v1 completion criteria：

- stronger machine-format single-value approximation (`approx_float`, `approx_complex`, correctly-rounded / strict-nearest semantic processes)；`grid_project()` 的 theorem-backed near-nearest projection已屬 v1；
- `floor_process` / `ceil_process` / `round_process`；
- `sqrt` / `log` / elementary real or complex functions；
- built-in native constants such as $\pi,e$；
- additional public grid families such as dyadic grids；
- advanced algebraic / transcendental DAG rewrites beyond v1 structural normalization；
- thread-safe shared graph runtime。

任何 deferred feature 要進 public surface，先修改 `02`，再同步 `03` / `05` / `06`（若涉及額外 theorem）。
