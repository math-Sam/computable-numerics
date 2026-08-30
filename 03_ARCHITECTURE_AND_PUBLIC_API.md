# Computable：Architecture and Public API

本文件把 `02_SEMANTIC_SPECIFICATION.md` 的 public semantics 映射到具體軟體結構。所有 architecture choice 都必須服從：

1. denotation 不變；
2. potentially divergent computation 必顯式；
3. finite-work API 必 guaranteed finite；
4. computation DAG 只預設屬於一般 `ComputableReal` / `ComputableComplex`；
5. exact complex probe domain 固定為 `GaussianRational` / $\mathbb Q(i)$；
6. evaluator 以 demand-driven obligations 為中心，且 history 只能做 semantics-preserving safe forgetting；
7. persistent knowledge 與 structural identity 分離。

---

# 1. Package layout

建議：

```text
computable/
│
├── core/
│   ├── kinds.py
│   ├── family.py
│   ├── promotion.py
│   ├── decision.py
│   ├── certificates.py
│   ├── knowledge.py
│   └── errors.py
│
├── rational.py
├── gaussian_rational.py
│
├── algebraic/
│   ├── polynomial.py
│   ├── isolation.py
│   ├── canonical.py
│   └── algebraic.py
│
├── real/
│   ├── real.py
│   ├── nodes.py
│   ├── factories.py
│   ├── sources.py
│   ├── evaluation.py
│   └── grids.py
│
├── complex/
│   ├── complex.py
│   ├── nodes.py
│   ├── factories.py
│   └── evaluation.py
│
├── projections/
│   └── binary.py       # exact classes / Binary64Grid support
│
└── _bootstrap.py
```

以上 package tree 是 **recommended concrete layout**，不是逐一 pathname 的 public compatibility contract；但下列 dependency rules 與 public/internal boundary 是 normative。elementary-functions、native constants、decimal projection 等 modules 位於第一版範圍外。任何額外 module 都不得反向改變本文件已固定的 dependency rules。

Dependency rules：

- `core/` 不 import concrete numeric classes；
- concrete modules 可 import `core/`；
- concrete numeric modules 不以 top-level circular import 完成 linking；
- `_bootstrap.py` 在 concrete classes 定義完成後註冊 family / promotion / conversion。

---

# 2. Numeric identity and family linking

## 2.1 `NumericKind`

```python
class NumericKind(Enum):
    RATIONAL = ...
    GAUSSIAN_RATIONAL = ...
    ALGEBRAIC = ...
    COMPUTABLE_REAL = ...
    COMPUTABLE_COMPLEX = ...
```

只用於 routing / registration，不取代 Python class identity。

## 2.2 `NumericFamily`

```python
@dataclass(frozen=True, slots=True)
class NumericFamily:
    rational: type
    gaussian_rational: type
    algebraic: type
    real: type
    complex: type
```

每個 numeric class 只需要 `_family` / `_kind`，不在 class body 裡保存另外三個 concrete class references。

---

# 3. Promotion architecture

Promotion 統一由 registry 處理，並遵守 **downgrade first, then lift**：

```text
inspect operands
→ guaranteed-finite downgrade each operand
→ inspect resulting mathematical regimes / realness
→ choose common target domain
→ guaranteed-finite lift
→ call same-domain operation
```

Promotion 不得為了取得更低 regime 啟動 `downgrade_process()`；只使用 ordinary `downgrade()` 已能有限恢復的資訊。

核心 value-level cost hierarchy：

$$
\mathbb Q
\subset
\mathbb Q(i)
\subset
\overline{\mathbb Q}
\subset
\mathbb C_C,
$$

以及 real branch $\mathbb Q\subset\overline{\mathbb Q}\cap\mathbb R\subset\mathbb R_C$。

Examples：

```text
Rational + GaussianRational -> GaussianRational
GaussianRational + Algebraic -> Algebraic
GaussianRational(real) + ComputableReal -> ComputableReal
GaussianRational(non-real) + ComputableReal -> ComputableComplex
Algebraic(real) + ComputableReal -> ComputableReal
Algebraic(non-real) + ComputableReal -> ComputableComplex
```

若 operand 的 nominal object regime 比目前可恢復 floor 更高，例如 algebraic object 已能 finite downcast 成 `Rational`，promotion 先使用該 `Rational` representation，再決定 target。這避免把不必要的 higher-regime machinery帶入 general computation DAG。

`GaussianRational.is_real()` 只是 finite Rational zero test；`Algebraic.is_real()` guaranteed finite，但只在 target selection 真正需要分流時呼叫。

Conceptual boundary：

```python
def numeric_add(a, b):
    a0 = a.downgrade()
    b0 = b.downgrade()
    left, right, target = promote_pair(a0, b0)
    return target._add_same_domain(left, right)
```

## 3.1 Guaranteed-finite exact subdomain recognizers

Promotion / coercion architecture 必另有一組 acyclic registry helpers，實作 `02` §14 的 mathematical-value-first subdomain recognition：

```python
recognize_rational_value(x) -> Rational | None
recognize_gaussian_rational_value(x) -> GaussianRational | None
recognize_integer_value(x) -> int | None
recognize_nonnegative_integer_value(x) -> int | None
recognize_positive_rational_value(x) -> Rational | None
recognize_real_coordinate_value(x) -> ComputableReal | None
```

The finite exact scalar-recognition bridge for rational / Gaussian-rational / integer subdomains固定涵蓋 Python `int/bool`、`Fraction`、finite `float`、finite `complex`、`Rational`、`GaussianRational`、`Algebraic`。`recognize_real_coordinate_value` additionally accepts an existing `ComputableReal` by identity/lift and may accept a general `ComputableComplex` only when its persistent knowledge already certifies realness, using `real_part()` with zero semantic advancement. An uncertified or certified-non-real general complex is rejected finitely; the recognizer never constructs or advances `membership_process(ComputableReal)` on its own. 未註冊第三方 numeric-like types不屬 frozen v1 coercion contract。These helpers only use guaranteed-finite exact decode/downcast or already-committed domain certificates；不得對 general computable values 啟動 rationality / integerhood / realness resolution。`str` / recursive tuple ratio屬 parser syntax，也不進 ordinary numeric recognizer。

凡 API semantic domain 本質上要求「integer」「nonnegative integer」「rational」等子域，應共用這些 recognizers，而不是每個 method 另寫 nominal type table。這包含 exact-class powers、rounding `ndigits`、Polynomial coefficients / powers / derivative order / scalar operands、DecisionProcess work budget，以及 bounded-denominator grid parameter。若來源 numeric value可 finite exact 分類但不在目標 domain，依 `02` 的 method-specific `TypeError` / `ValueError` contract finite reject。

---

# 4. `Rational` architecture

## 4.1 Constructor and external scalar conversion

Public constructor input 與 exact conversion 以 `02` §6.2 為準。Implementation 應集中成單一 finite recursive conversion kernel。其 public constructor input type 以 `02` 的 `RationalInput` 為準：

```text
RationalInput :=
      finite-rational numeric value
    | str
    | tuple[RationalInput, RationalInput]

finite-rational numeric value includes
Rational / int-bool / Fraction / finite float / real finite complex /
real GaussianRational / rational-valued Algebraic
```

其中 finite `float` 必用 `as_integer_ratio()` 或語意等價的 exact binary64-to-rational conversion；finite `complex` 只有 exact-zero imaginary coordinate 才能進 Rational；real `GaussianRational` 與 rational-valued `Algebraic` 透過 §3.1 finite recognizer/downcast；`str` 必走 exact decimal/scientific/rational parser，不能先轉 machine float；tuple 與 two-argument `Rational(u, v)` 都遞迴解析 children 後做 exact quotient。Non-finite machine values reject；numeric value 可 finite 分類但不在 $\mathbb Q$ 時 finite `TypeError`；任一遞迴 divisor 為 zero 時 raise `ZeroDivisionError`。

Promotion / conversion registry 對 numeric arithmetic 與 exact-class relations finite 接受 Python `int`（包含依 Python convention 作為 `0/1` 的 `bool`）、`fractions.Fraction`、finite `float`，exact lift 成 `Rational`；finite Python `complex` 則 coordinatewise exact decode 成 `GaussianRational`。任一 float/complex component non-finite 時 finite `ValueError`。`str` / recursive tuple ratio 僅屬 explicit constructor syntax，numeric dunder dispatch 不解析它們，而依 Python protocol 回 `NotImplemented`。

## 4.2 Working vs canonical object

Public `Rational` 保留兩種 lifecycle states：

```text
mutable working Rational
    ├── hash()   → simplify as needed + freeze this same object + stable hash
    └── intern() → return canonical frozen weak-interned Rational
                   (cache hit may return another object; receiver need not freeze)
```

`hash()` 不改變目前 Python object identity；若已有另一個等值 canonical object 存活，它也不能把目前物件「替換」成該 object。`intern()` 才是可回傳既有 canonical object 的 sharing operation。

依 `02` 固定的 public lifecycle：`Rational(...)` constructor / named constants 走 frozen-interned path；`copy.copy(r)` / `r.__copy__()` 建立 distinct mutable working copy；non-in-place field arithmetic 可回 working result；in-place arithmetic 對 mutable receiver 原地修改、對 frozen receiver 保持原值並回 fresh working result。

Mutable working object 的 raw representation 存在 private integer fields：

```python
r._numerator
r._denominator
```

它們可 unreduced，但永遠維持 `r._denominator > 0`。Public `.numerator` / `.denominator` 是 `@property` canonical-value views：getter 先呼叫 finite `simplify()`，再回傳 canonical integer field，因此 public coordinate read 不依賴 arithmetic kernel 暫存的 unreduced pair。

Properties 另保留 public value-level setters：

```python
r.numerator = u
r.denominator = v
```

其中 `u` / `v` 接受完整 `RationalInput`。Frozen receiver 先 finite reject `ValueError`；mutable receiver 先把 RHS parse/validate 到暫存值，再 `simplify()` receiver，故 setter 使用 assignment 前 mathematical value 的 canonical pair $(n,d)$，而不是 raw working pair。之後分別將 denotation 設為 `parse(u) / d` 或 `n / parse(v)`，並只把 integer data 寫回 `._numerator` / `._denominator`。Denominator setter 若 parsed value 為 zero，transactionally raise `ZeroDivisionError`；成功 mutation 清除 hash cache、同步 simplification state並維持 positive-denominator invariant，結果可再次是 unreduced working state。

`simplify()` 是 public finite lifecycle operation：mutable working object 原地 canonical reduce但保持 mutable；frozen object no-op。它不查 weak intern table，也不建立 canonical sharing。

Advanced/debug documentation may show **read-only inspection** of `._numerator` / `._denominator` to expose lazy working state. These underscore fields are representation-sensitive private details, not compatibility-stable public API; direct writes are unsupported.

Working object 適合 arithmetic loops，直到 hash / intern 觸發 freeze；canonical interned object 適合：

- persistent ownership；
- dict / set key；
- numeric graph leaf payload；
- certificate endpoint；
- algebraic isolation endpoint。

## 4.3 Weak interning

使用：

```python
WeakValueDictionary[(numerator, denominator), Rational]
```

或等價結構。

Intern table 不得因 cache 本身造成 permanent retention。

## 4.4 Ownership boundary

任何 persistent structure 接受 Rational 時：

```python
r = r.intern()
```

後再保存。

不允許保存仍可 value-mutate 的 Rational reference。

## 4.5 Performance strategy

Cross-cancellation、private accumulators、bulk reducers 都只是可 benchmark 的 implementation strategy。

Public invariant 不要求每一步 gcd simplify。

---

# 5. `GaussianRational` architecture

`GaussianRational` 是 immutable exact value。Public constructor 固定三個 dispatch shapes：

```python
GaussianRational()
GaussianRational(value)
GaussianRational(real, imag)
```

Zero-argument construction 表示 $0$。One-argument path 是 guaranteed-finite exact value construction：existing `GaussianRational` 保留同 denotation；finite Python `complex` exact decode 兩 coordinates；`Algebraic` 只在 finite `try_as(GaussianRational)` 成功時接受；任何 `RationalInput` 則解析成 real coordinate、imaginary coordinate 為 $0$。Two-argument path 專屬 coordinate construction，兩 coordinates 都走 `RationalInput` recursive parser。所有 persistent coordinates 保存前 `intern()`。Conceptual payload：

```python
@dataclass(frozen=True, slots=True)
class GaussianRational:
    real: Rational
    imag: Rational
```

實際 implementation 可不用 dataclass，但 semantic payload 固定等價於 `(real, imag)`。Constructor 必確保 persistent coordinates 為 frozen / interned Rational。

建議提供 internal weak interning keyed by the two canonical Rational identities；是否保證 constructor identity-sharing 不屬 public semantic contract。

Public/API rational rectangle shape 固定為：

```python
RationalRectangle = tuple[
    tuple[Rational, Rational],  # real [a,b]
    tuple[Rational, Rational],  # imag [c,d]
]
```

這是 `02` / `06` 的 interchange contract。Internal geometry layer **可以**使用 immutable `RationalClosedBox` object，但必提供 exact lossless `from_tuple()` / `as_tuple()`（或等價）轉換；不得讓 internal class 悄悄改變 public return shape。

Helper layer 至少提供：

- containment / intersection；
- width per coordinate；
- center / corners as `GaussianRational`；
- exact subdivision；
- origin containment；
- rectangle dominance。

Polynomial evaluation at `GaussianRational` points 應走 exact $\mathbb Q(i)$ Horner kernel，不升級成 general `Algebraic`。這是 algebraic root-isolation geometry 與 general complex localization 共用的 probe substrate。

Real-valued Python integer / rounding protocols 直接委派給 canonical real `Rational` coordinate：`int` / floor / ceil / `round` 全部 finite exact；non-real inputs finite `TypeError`。`round(..., ndigits)` 的 `ndigits` 走 §3.1 finite integer-valued recognizer；接受條件由 exact integer value 決定，結果回 exact `Rational`，採 half-to-even，不經 float。

---

# 6. Polynomial kernel

v1 固定為 immutable exact value type：

```python
Polynomial(coefficients: tuple[ExactIntegerInput, ...])
```

Coefficient order is normative and **constant-first**:

$$
(a_0,a_1,\ldots,a_n)\longleftrightarrow a_0+a_1X+\cdots+a_nX^n.
$$

For example `Polynomial((2, -3, 1))` denotes $2-3X+X^2$. Internal packed storage、structural keys、Horner evaluation、derivative kernels、serialization and `Algebraic(polynomial, box)` must preserve this orientation.

Public construction requires a tuple of numeric coefficient values accepted by the §3.1 finite integer-valued recognizer; every accepted coefficient is canonicalized to an ordinary Python `int`. Thus integral `bool` / `Fraction` / finite `float` / real finite `complex` / `Rational` / real `GaussianRational` / integer-valued `Algebraic` inputs are equivalent. Canonical storage trims only trailing high-degree zeros; it must not content-normalize, primitive-normalize, or sign-normalize the polynomial value. `Polynomial((0,))` is the unique zero representation. Equality/hash are finite on the exact equality bridge defined by `02`. Polynomial-to-polynomial equality uses the canonical coefficient tuple. A constant polynomial `Polynomial((n,))` also compares by exact value against Python `int` / `bool`, `fractions.Fraction`, finite `float`, finite `complex`, `Rational`, `GaussianRational`, and `Algebraic`; implementations should route this through one finite integer-recognition helper rather than duplicate conversion logic. General `ComputableReal` / `ComputableComplex` are excluded from this bridge. Constant-polynomial hashing reuses the corresponding Python integer hash, which by the scalar equal-hash contracts is also the hash of every bridged scalar equal to that integer. Nonconstant polynomial hashes use a type-separated canonical coefficient key. v1 fixes `.degree == -1` and `.leading_coefficient == 0` for that zero object; `-1` is a runtime sentinel rather than a mathematical assertion about the conventional degree of the zero polynomial.

`Polynomial` is not merely an internal kernel in v1; it is a public immutable exact type. The normative public surface is:

```python
p.coefficients
p.degree
p.leading_coefficient
bool(p)

+p
-p
p + q
p - q
p * q
p ** n
p.derivative(order=1)
p.evaluate(x)
p(x)

p.content()
p.primitive_part()
p.pseudo_divmod(q)        # -> PseudoDivisionResult
p.exact_div(q)            # -> Polynomial
p.gcd(q)                  # -> Polynomial
p.square_free_decomposition()  # -> PolynomialFactorization
p.factor()                       # -> PolynomialFactorization
p.resultant(q)             # -> int
p.sturm_sequence()         # -> tuple[Polynomial, ...]

p.real_root_count(interval=None)
p.isolate_real_roots(interval=None)
p.complex_root_count(box)
p.isolate_complex_roots(box=None)
```

The public helper payloads are immutable:

```python
@dataclass(frozen=True, slots=True)
class PseudoDivisionResult:
    scale: int
    quotient: Polynomial
    remainder: Polynomial

@dataclass(frozen=True, slots=True)
class PolynomialFactor:
    factor: Polynomial
    multiplicity: int

@dataclass(frozen=True, slots=True)
class PolynomialFactorization:
    unit: int
    content: int
    factors: tuple[PolynomialFactor, ...]
```

Public interval geometry uses:

```python
RationalInterval = tuple[Rational, Rational]
RationalRectangle = tuple[RationalInterval, RationalInterval]
```

All spelling, canonical result conventions, root-boundary inclusion rules, zero-polynomial exceptions, pseudo-division scale, gcd sign normalization, factor ordering, and endpoint parsing are normative from `02` §7.9–§7.13.

`Polynomial` uses the same finite exact integer-recognition bridge rather than source-type-only coercion. Python `int` / `bool`, `Fraction`, finite `float`, finite `complex`, `Rational`, `GaussianRational`, and `Algebraic` are finitely decoded/downcast; scalar arithmetic is accepted exactly when the mathematical scalar is an integer, then embedded as the corresponding constant polynomial. Recognized non-integral/non-real scalar values finite `TypeError`, so coefficient domain remains $\mathbb Z[X]$. The same helper is reused by every public method position that semantically expects a polynomial operand (`+ - *`, `pseudo_divmod`, `exact_div`, `gcd`, `resultant`), by constructor coefficients, by `p ** exponent`, and by `derivative(order=...)`. Powers / derivative first recognize an exact integer value, then apply their own nonnegative-domain check. Equality uses the same finite integer-recognition bridge for constant polynomials and works in both operand orders; nonconstant polynomials compare unequal to those scalar values. General `ComputableReal` / `ComputableComplex` do not enter this integer recognizer. `evaluate()` / `__call__` use the registered scalar conversion/promotion layer and therefore also support finite Python `complex` through exact `GaussianRational` lifting. The polynomial module must not import higher concrete numeric classes merely for this purpose: implement Horner evaluation through core promotion/operation dispatch or another acyclic protocol so evaluating at `Algebraic` / general computable values remains finite construction without a circular module dependency.

Polynomial kernel 不依賴 general computable runtime concrete modules。Exact factorization / resultant / isolation support is also reused by lazy `Algebraic` minimal-polynomial and hash machinery, but those internal consumers must call the same exact kernel semantics rather than maintain a divergent second implementation.

---

# 7. `Algebraic` architecture

Public construction has exactly two dispatch shapes:

```python
Algebraic(value)
Algebraic(polynomial, box)
```

`value` follows the finite exact scalar-embedding bridge: existing `Algebraic` preserves the same denotation, finite Python `complex` exact-lifts to `GaussianRational`, `GaussianRational` embeds directly, and any `RationalInput` is parsed by the Rational recursive exact parser before embedding. General computable classes do not trigger algebraicity search. Two-argument construction is reserved exclusively for `(Polynomial, RationalRectangle)` root representation. Rectangle endpoints may be `RationalInput` at the constructor boundary but are interned to canonical `Rational` before persistent ownership. Do not add a second `from_root()` public path in v1 unless it is merely a documented alias; the overload above is the normative spelling.

Finite exact coercion into this regime must include identity/copy-value `Algebraic`, `Rational`, `GaussianRational`, and finite Python `complex` through its Gaussian lift; non-real Gaussian values use the specification-prescribed quadratic/point-box embedding. Promotion registry may share this conversion kernel with public construction, but must not route cheap Gaussian arithmetic through Algebraic unless the target regime actually requires promotion.

## 7.1 Object model

Conceptually：

```text
Algebraic
│
├── denotation α                         # semantic, immutable
├── defining_polynomial: Polynomial      # representational, mutable-in-place logically
├── isolating_box: RationalClosedBox     # representational, refinable
├── persistent exact facts               # is_real, zero, sign if real, ...
├── minimal_polynomial cache             # lazy
├── canonical_root_index cache           # lazy
└── hash cache                            # lazy
```

Python implementation 可透過 private setters / controlled state object 實現 interior mutability；public contract 是 denotation immutable，不是 fields frozen。

## 7.2 Isolation box

Algebraic **internal representation** 建議統一使用：

```python
@dataclass(frozen=True, slots=True)
class RationalClosedBox:
    real_lower: Rational
    real_upper: Rational
    imag_lower: Rational
    imag_upper: Rational
```

四個 Rational 必 frozen / interned。`RationalClosedBox` 與 public `RationalRectangle=((a,b),(c,d))` 必 exact bijective convert。

不需要 `RealIsolation` / `ComplexIsolation` 作 public or semantic bifurcation。

Real root 可自然出現在：

```text
[a,b] × [c,d]
```

其中 $c<0<d$；也可以退化成 $[a,b]\times\{0\}$。兩者皆合法。

## 7.3 Representation updates

Allowed：

```text
(P, B0)
→ (P, B1)              # box refinement
→ (Mα, B1)             # lazy minimal polynomial
→ (Mα, B2)              # further refinement
```

每一步都必 finite verify / construct to preserve same target root。

## 7.4 Lazy hash

第一次 `hash(alpha)`：

1. 求 canonical minimal polynomial $M_\alpha$；
2. 對其 roots 用 $(|z|,\operatorname{Arg}z)$ 排序，$\operatorname{Arg}\in[0,2\pi)$；
3. 求 target root index；
4. cache canonical identity；
5. 先做 finite $\mathbb Q$ / $\mathbb Q(i)$ recognizer：若可 downcast，使用對應 `Rational` / `GaussianRational` cross-type hash；否則由 canonical algebraic identity compute hash；
6. 可將 defining polynomial 設為 $M_\alpha$。

Root ordering 的 implementation 不要求 numerically evaluate transcendental argument；可由 exact algebraic comparisons / half-plane / orientation predicates實現。Hash 的「stable」只指同一 Python execution 內不受 later refinement 影響，不是 serialized hash guarantee。

Real-valued `int` / floor / ceil / `round` 使用 finite exact algebraic ordering / rational-boundary comparisons；non-real inputs finite `TypeError`。`round(alpha, ndigits)` 的 `ndigits` 走 §3.1 finite integer-valued recognizer；finite result 為 exact `Rational`，half-grid equality 由 algebraic equality/order直接決定，因此沒有 semantic pending boundary。

## 7.5 Algebraic objects are not DAG nodes by default

Standalone：

```python
a = Algebraic(...)
b = a + a
```

結果直接是 finite exact `Algebraic`，不建立 general semantic computation graph。

只有：

```python
x = ComputableReal.from_comparator_source(source)
y = x + a
```

才把 `a` lift 成 graph exact leaf payload。

---

# 8. Decision runtime

## 8.1 Core process object

```python
class DecisionProcess(Generic[T]):
    def advance(self, work=1) -> Pending | Resolved[T]: ...
    def resolve(self) -> T: ...
```

Process 保存 mutable continuation state。`work` validation 依 `02` §3.3 / §14 與本文件 §3.1：先 guaranteed-finite exact recognize integer value，再要求 $work\ge0$；可 finite 分類但非整數則 `TypeError`，負整數 `ValueError`。Finite-work public surface只有 `advance(...)`；`resolve()` 是明示允許不終止的 blocking resolution boundary。

## 8.2 Work unit

一次 work unit = 一次 guaranteed-finite cooperative logical transition。

禁止在單一 transition 中：

```python
run_unknown_program_until_halt()
```

若要模擬可能 diverge 的 computation，保存其 finite configuration，每個 work unit 只推進有限步。

## 8.3 Process combinators

至少：

```text
map
flat_map / bind if needed
combine
short_circuit
fair_dovetail
certificate_emission
```

Dovetail scheduler 必保證：任何在有限自身 steps 內可 resolve 的 branch，不得被 permanently pending branches starvation。

## 8.4 Resolved stability

Resolved process 的後續 call 不做實質 work；結果 immutable / stable。Terminal exception state 亦需 cache：後續 call 不推進 semantic work，穩定 re-raise 同一 mathematical exception class。

---

# 9. Knowledge-store architecture

## 9.1 Knowledge vs source progress

兩者分離。

### Certified knowledge

Persistent representation 優先採 geometry-first design，並可保存 recoverable floor：

```text
real:    strongest useful L <= x <= R
complex: strongest useful z in rectangle B
```

relation / membership facts仍可作 inference input、certificate 或 process result；只要 strongest enclosure / rectangle / recoverable floor 已完整蘊含其 semantic content，就不要求以平行 predicate record永久保存。無法由這些 carrier 完整取代的部分保存為 residual semantic knowledge。

例如：

```text
0 < L <= x <= R        already entails x > 0 and x != 0
z in B with 0 ∉ B      already entails z != 0
```

此 knowledge 可 persistent 保存於 native **或 derived** computable node。

### Source execution progress

例如：

```text
series term index
partial product state
native comparator continuation
source-specific recursion state
```

通常只屬於真正的 native source，或屬於 explicit `DecisionProcess` continuation。

Derived node 有 persistent knowledge 不代表它必保存 upstream source execution internals。

### Recoverable floor

Recoverable floor 是足以 guaranteed-finite 重建某個較低 public numeric regime representation 的 persistent constructive state。Exact finite floor 可直接保存 `Rational` / `GaussianRational` / `Algebraic` payload；`ComputableReal -> ComputableComplex` lift 則可保存可有限恢復的 real node / view。Floor 只能往更低 regime改善，不得遺失已承諾的 recoverability。

## 9.2 Provenance

建議：

```python
class ProvenanceKind(Enum):
    KERNEL_VERIFIED = ...
    TRUSTED_SOURCE = ...
    USER_ASSERTED = ...
    DERIVED = ...
```

Knowledge fact 應能保留足夠 provenance 供：

- consistency diagnostics；
- debugging；
- trust-boundary inspection。

## 9.3 User assertions — trust boundary, absorption, and residual knowledge

Public trust-boundary surface：

```python
x.assume_relation(y, relation)
x.assume_membership(numeric_class, truth)
x.assume_grid_membership(grid, truth)   # real only
```

### Relation path

`LESS` / `GREATER` / `NOT_EQUAL` 的 true promise 必在返回前被幾何吸收。Evaluator 向兩側 operand propagation refinement obligation，直到 real intervals strict separate；complex `NOT_EQUAL` 則直到至少一個 coordinate strict separate。Resulting enclosure / rectangle承載 `USER_ASSERTED` provenance，不必保留同義 relation flag。

`EQUAL` / `LESS_EQUAL` / `GREATER_EQUAL` 含 equality boundary。Architecture 應做所有 finite geometric propagation，例如 equality-linked nodes可交換 / intersect目前 certified bounds；但無法被 geometry 完整取代的 relation content必進 residual store。

### Numeric-domain membership path

`assume_membership(numeric_class, truth)` 保存 mathematical-domain fact，不是 Python class mutation。Membership facts走 domain-inclusion inference graph；如果 recoverable floor或其他 representation已蘊含該 fact，commit後立即 dominance-compaction。一般 rationality / algebraicity / realness promise不要求 assertion call找出具體 lower representation。

### Grid-membership path

`assume_grid_membership(grid, True)` 使用 standard-grid search adapter + target evaluator，在 method 返回前完成 unique grid-point identification。Identified finite point轉成 exact value並 commit recoverable floor：integer / bounded-denominator / binary64 finite point都可落到 exact `Rational` payload。

`assume_grid_membership(grid, False)` 使用 off-grid promise持續 refinement，直到 persistent interval整體落在 grid gap，亦即 grid 與 closed interval交集為空。這份 geometry可直接供 adjacent-localization machinery重用。

### False promise and contradiction

每條 assertion path先做 finite contradiction check。若矛盾已知，transactionally raise `InconsistentKnowledgeError`。若 promise實際為假但尚無 finite contradiction evidence，依 promise才能完成的 strict separation / grid identification / gap absorption可以永久執行；不得以 timeout生成 semantic結論。

## 9.4 Commit / absorption protocol

Single-threaded conceptual flow：

```text
incoming certified fact / trusted assertion P
→ finite contradiction check
→ derive finite domain/relation implications
→ propagate every immediately available enclosure / rectangle strengthening
→ if P is a strict-separable promise:
      refine until geometry entails P
→ if P is grid-membership True:
      refine/search until unique grid point is identified; commit recoverable floor
→ if P is grid-membership False:
      refine until enclosure lies inside a grid gap
→ retain only residual semantic content not entailed by geometry / recoverable floor
→ dominance compaction
→ publish knowledge state
```

Process取得較低 regime representation時也走同一 commit path；即使外層 `DecisionProcess.advance(...)` 回 `Pending()`，recoverable floor仍立即改善。

## 9.5 Lossless compaction

例如 interval knowledge：

```text
[-100,100]
[-10,10]
[-1,1]
```

可只保留最強：

```text
[-1,1]
```

若後續又取得：

```text
[1/4,1]
```

那麼 `positive`、`nonzero`、`nonnegative` 等獨立 fact representation 都可被此 interval subsume。前提是 compaction 後保留足夠 provenance / trust summary，且不丟失任何仍無法由 enclosure 推出的 persistent semantics。

---

# 10. General computable graph architecture

## 10.1 Why a graph exists

General semantic results naturally引用 operands：

```text
x, y
  ↓
Sum(x,y)
  ↓
Product(...)
  ↓
...
```

Graph 不是 symbolic CAS 先驗 representation，而是對 unavoidable dependency chain 做 explicit control。

## 10.2 Real taxonomy

```text
RealNode
├── NativeRealNode
├── ExactRealLeaf
└── DerivedRealNode
```

### NativeRealNode

真正能從 source algorithm 生產額外 certified information。

可保存：

```text
source_progress
source-specific reusable state
persistent certified knowledge
```

### ExactRealLeaf

Payload：

```text
Rational
real Algebraic
```

Real `GaussianRational(a, 0)` 在 lift 前 canonicalize 為其 `Rational` real coordinate，避免同一 cheap exact scalar 產生兩種 trivial real-leaf shapes。Leaf 不複製 underlying exact data。

### DerivedRealNode

v1 核心 node kinds 至少包含：

```text
SumNode
ProductNode
NegNode
ReciprocalNode
RealPartViewNode
ImagPartViewNode
```

可 persistent 保存已證 facts / bounds，但 operation dependency structure immutable。Elementary functions、general power nodes 與其他 function-specific nodes 位於第一版範圍外。

## 10.3 Complex taxonomy

v1 不要求獨立的 public native-complex source protocol。General complex values 由 exact leaves、real embedding、two-coordinate construction 與 derived operations 組成：

```text
ComplexNode
├── ExactComplexLeaf
├── RealEmbeddingComplexNode
├── ComplexFromPartsNode
└── DerivedComplexNode
```

### `ExactComplexLeaf`

Payload 只可為 finite exact value：

- `Rational`；
- `GaussianRational`；
- arbitrary `Algebraic`。

任意 `Algebraic` 可直接作 exact leaf，不必 eager 分解成 real / imaginary algebraic components。

### `RealEmbeddingComplexNode`

General `ComputableReal` 嵌入複平面時使用 dedicated node，denotation 為 $x+0i$。它不是 exact leaf，因為 child 本身仍是 general semantic value。

### `ComplexFromPartsNode`

對

```python
ComputableComplex.from_parts(real, imag)
```

建立 structural node，denotation 為 `real + imag*i`，並持有兩個 `ComputableReal` children。

# 11. Canonical structural identity and weak hash-consing

## 11.1 Structural key

每個 real/complex DAG node 有 finite structural key：

```text
(node kind,
 immutable exact parameters,
 canonical child structural identities)
```

不包含：

- persistent knowledge；
- best interval；
- source progress；
- task memo；
- general semantic equality result。

Node-kind specific key rule：

- exact leaf：canonical exact payload identity；
- derived node：node kind + immutable parameters + canonical child structural identities；
- native source node：只有 source 明確提供 immutable **construction key** 並保證同 key 可安全共享 denotation / progress 時才跨 construction merge；否則 key 必含 unique source-instance token，禁止因「看起來像同一算法」而合併。

Public `ComputableReal` / `ComputableComplex` 仍是 unhashable；internal `Node` 可用 structural key / internal identity 作 evaluator dictionary key。不得把 internal node hashing 暴露成 public numerical hash。

## 11.2 Structural equality is not semantic equality

$$
\operatorname{structKey}(x)=\operatorname{structKey}(y)
$$

可用於 safe node sharing。

但：

$$
\llbracket x\rrbracket=\llbracket y\rrbracket
$$

一般不可用於 DAG identity。

## 11.3 Weak interning

Node factory：

```text
compute structural key
→ weak intern lookup
→ existing live node? return it
→ otherwise create, register weakly, return
```

因此同一 structural construction 的 branches 自動共享 persistent knowledge。

---

# 12. Structural node factories

Python dunder 不直接 construct `SumNode(...)`。

## 12.1 `make_sum()`

責任：

- flatten nested sum；
- fold Rational constants；
- collect structurally identical terms；
- combine Rational coefficients；
- exact zero elimination；
- canonical deterministic ordering of structural entries if needed for key stability；
- weak-intern final node。

## 12.2 `make_product()`

責任：

- flatten；
- Rational coefficient fold；
- non-negative integer occurrence/exponent collection；
- exact zero / one rules；
- safe structural fusion；
- weak-intern final node。

Negative-exponent fusion is not a default structural rule，因為它需要 nonzero domain evidence；只可在 certificate 已存在且 rewrite theorem 明示時加入。

## 12.3 Construction complexity

Flattened representation 不得透過每次 `+` 複製整張 accumulated map 而退化成 obvious $O(n^2)$ long-chain construction。

Implementation 可選：

- private builders；
- persistent maps；
- batched flattening；
- ownership-aware temporary accumulators；

但必用 benchmark 驗證。

---

# 13. Demand-driven evaluation tasks

每次 external query 建立 task-local evaluator：

```python
@dataclass
class EvaluationTask:
    memo: dict[Node, QueryLocalResult]
    agenda: ...
    obligations: ...
```

核心不是「把 reachable graph 全算到同一 precision」，而是：

```text
1. inspect target persistent knowledge
2. if target contract already satisfied -> return
3. derive finite child obligations from node semantics + current bounds
4. choose one or more unresolved / high-impact obligations
5. evaluate/refine upstream iteratively
6. commit newly certified facts immediately
7. retry target and stop as soon as contract is met
```

`ResolutionRequirement` / `ChildObligation` 建議成為 internal first-class data objects；具體 class naming 可在 implementation pass 調整。Operation-specific planner 可先使用保守 correctness-first allocation，再由 benchmark 演進成 adaptive feedback scheduler。

Task-local memo 目的：

- 同一 external query 中 shared subexpression 不重複 evaluation；
- iterative traversal 避免 Python recursion-depth dependence；
- process / query-local search state 在 query 結束可釋放。

Persistent node knowledge 與 task memo 分離：

```text
persistent knowledge: reusable certified facts
query memo: this-query assembly / scheduling artifacts
```

## 13.1 Minimal sufficient knowledge

Evaluator 不承諾 globally optimal minimum work；它承諾不把與 current contract 無關的 eager semantic computation 當成預設策略。Coarse bounds 可先取得以估計 sensitivity，再 feedback 決定下一個 refinement target。

## 13.2 Safe forgetting and graph compaction

History 可被丟棄的條件不是「已有一個近似值」，而是存在 semantics-preserving replacement：

```text
exact Rational subtree          -> Rational leaf
exact Gaussian subtree          -> GaussianRational leaf
finite algebraic subtree        -> Algebraic leaf
general semantic subtree        -> equivalent compiled/native source only if arbitrary future refinement is preserved
```

Finite interval / rectangle 只能作 knowledge cache，不足以取代 general computable denotation。

Weak GC 處理 unreachable graph；safe compaction 處理仍 reachable 但可被 exact / algorithmically equivalent replacement 壓縮的 graph。

---

# 14. Source capability unification

v1 public native-real extension只凍結 comparator-native source。Conceptual protocol：

```python
source.compare_rational_process(q: Rational) -> DecisionProcess[Order]
```

Public source-entry spelling 固定為：

```python
ComputableReal.from_comparator_source(source)
```

其中 `source` 必實作上述 comparator-source protocol。Runtime 在把 rational query 交給 source 前必先取得 `q = q.intern()` 的 frozen/interned value；source / returned process 不得 persistent 持有仍可 value-mutate 的 Rational reference。Source 必具有 lifetime-stable denotation；不同 query/process 的結果不得互相矛盾。Runtime 對 source 持 strong ownership，除非已由 semantics-equivalent compiled replacement 安全取代。

## Comparator-native -> bound

`ComputableReal.bound(width=epsilon)` 必有一條不依賴 bound-native adapter 的 primitive path。Comparator-native source 可使用 `06` 的 rational enclosure theorem，或語意等價且更高效的 equality-safe construction，取得 finite certified rational enclosure；不得使用在 exact rational hit 會卡死的 naive midpoint bisection。

## Derived node capabilities

Derived node可依 operation semantics 直接傳播 child enclosures；若需要 rational comparator，可由其 bound capability與 `06` 的 shrinking-enclosure theorem建立。每個 node kind 必至少有一條 primitive direction，禁止 default adapters形成：

```text
bound -> compare -> bound -> ...
```

的 recursion loop。

Bound-native **public source extension** 不屬 v1 frozen surface；日後加入時才需要固定其 source protocol。

# 15. Grid architecture

形式理論 `06` 將 local finiteness（underlying set property）與 representation capabilities 分開。v1 runtime 的三個 standard one-dimensional grids採 canonical **searchable computably embedded exact ordered grid realizations**：

```python
IntegerGrid()
BoundedDenominatorGrid(max_denominator=N)
Binary64Grid()
```

Grid objects為 immutable value objects；zero-argument `IntegerGrid()` / `Binary64Grid()` 是否 internally singleton/interned不屬 public identity contract。Implementation可有 internal `Grid` protocol，但 v1 不要求 arbitrary user-defined grid plugin API。

Internal grid capability至少能提供：

- exact/canonical point representation，且 canonical interpretation exact-realizes `06` 的 ordered-grid structure；
- finite total grid-point equality / order trichotomy；
- **finite-point computable-real embedding**：對每個 finite grid point，finite produce一個同 denotation的 internal real presentation / exact leaf；其 formal semantics realizes `06` 的 $D_{\mathrm{CR}}$ embedding。Runtime hot path不要求真的 materialize Code-register `Program` code；
- `06` Definition 66.1 的 search operation；
- target-independent representation constraints；
- finite construction / decoding of any distinguished grid sentinels or canonical grid witnesses required by that standard grid。

這個 embedding boundary很重要。Architecture 不把「target-vs-finite-grid-point comparator」與「adjacent midpoint probe」設成 grid-specific duplicated hooks。Finite grid point先走共同 embedding；target node的 formal interpretation本身 effectively computable-real-presented；generic semantic comparator即可比較兩者。任意 finite grid-point pair的 midpoint則由兩個 embedded reals經 generic rational-affine node / presentation builder構造，再走同一 comparator。因而 `06` Propositions 67.2 / 67.3 是 runtime architecture的共同 derived path。實作可以直接以 DAG/evaluator capability實現這條語意路徑，不必在 hot path實際輸出 formal machine program code。

Two-sided bounding仍需區分 formal relation與 runtime ownership：`06` Definition 67.1 是 grid relative to target interpretation的 capability，不由 ordered-grid code本身推出。三個 standard grids則實作更強的 **global ComputableReal bounding adapter**，可對任意 `ComputableReal` target guaranteed-finite產生 outer grid bracket；Theorem 3 `grid_project()` 會用此 capability在 adjacent bracket外側有限取得 immediate outer neighbors。Adapter可以由 grid-specific helper + target enclosure evaluator共同實現，不要求純 `Grid` value object單獨執行 semantic refinement。

Guaranteed-finite API不強迫 exact grid-hit或 exact nearest-neighbor detection。

## 15.1 Theorem-1 result

```python
@dataclass(frozen=True)
class GridBracket[T]:
    lower: T
    upper: T
```

`x.grid_bound(grid)` guaranteed finite回 near-adjacent bracket，語意完全依 `02` / `06` Theorem 68.1。

## 15.2 Theorem-3 near-nearest projection

```python
x.grid_project(grid)
```

No extra wrapper type is required; the return object is the grid's canonical **finite** point representation. If the output is $g$, the semantic invariant is

$$
\left|
\{h\in G\cap\mathbb R:|h-x|<|g-x|\}
\right|
\le1.
$$

Implementation must follow the forward dependency of `06` Theorem 70.2 and must **not** call `grid_localize()` as a theorem prerequisite. A conforming architecture may share internal helpers, but the proof/implementation dependency is:

```text
Theorem-1 near-adjacent bracket
→ finite reduction to strict-nearest point OR adjacent bracket
→ if adjacent: obtain immediate outer neighbors through global bounding + search
→ construct the two overlapping affine midpoint probes through common real embedding
→ fair-dovetail the two safe-region comparisons
→ return a finite near-nearest point
```

If the Theorem-1 bracket contains one interior point $q$, the finite reduction runs target-vs-$q$ together with the open-Voronoi rescue around $q$. Strict target-vs-$q$ evidence produces an adjacent half-bracket; exact-hit behavior is rescued by the adjacent midpoint comparisons and may directly return $q$ as strict nearest. This helper is shared with later mixed localization, but Theorem 3 does not semantically depend on Theorem 5.

No float distance, tolerance, midpoint equality test, or later-theorem call may replace this construction.

Theorems 2 and 4 are promised mathematical strengthenings and therefore do not require additional public payload classes or methods in v1.

## 15.3 Theorem-5 mixed optimal result

```python
class GridDirection(Enum):
    STRICT_LEFT = -2       # grid point g < target x
    LEFT_OR_EQUAL = -1     # g <= x
    EQUAL = 0              # g == x
    RIGHT_OR_EQUAL = 1     # g >= x
    STRICT_RIGHT = 2       # g > x

@dataclass(frozen=True)
class GridApproximation[T]:
    point: T
    direction: GridDirection | None

@dataclass(frozen=True)
class GridLocalization[T]:
    bound: GridBracket[T] | None
    approx: GridApproximation[T] | None
```

Invariant: `bound` / `approx` may not both be `None`. `x.grid_localize(grid)` bound / strict-nearest / direction semantics are fixed by `02` §3.4, `02` §9.8, and `06` Theorem 72.1.

Architecturally, Theorem 5 should be implemented as a fair dovetail of the two sound optimal partial searches already justified before it:

- adjacent-bracket search, guaranteed to terminate off the grid (Theorem 2 construction);
- strict-nearest search, guaranteed to terminate away from adjacent midpoints (Theorem 4 construction).

The scheduler may share Theorem-1 refinement state, grid search witnesses, embedded point presentations, and midpoint comparisons between the two channels. It must not duplicate native-source progress merely because the theorem is described as two searches. The mathematical reason termination is guaranteed is

$$
(G\cap\mathbb R)\cap M_G=\varnothing,
$$

so the two optimality obstructions cannot occur simultaneously.

## 15.4 Standard grids

### `IntegerGrid()`

Carrier為 $\mathbb Z$，public point使用 Python `int`。Finite point embedding可直接建立 exact Rational/real leaf。

### `BoundedDenominatorGrid(max_denominator=N)`

`max_denominator`走 §3.1 finite integer-valued recognizer，再要求 exact integer value $N\ge1$；不因來源 nominal type不同而拒絕 integral finite numeric values。

Carrier：

$$
G_N=\left\{\frac pq:\ 1\le q\le N,\ \gcd(|p|,q)=1\right\}.
$$

Public point使用 frozen/interned `Rational`。Finite-point embedding直接 lift該 Rational。Search hot path可採 continued-fraction / Farey類技巧，但 theorem contract不依賴特定演算法。

### `Binary64Grid()`

Carrier為所有 finite binary64 real values加 `-inf` / `+inf` boundary values，排除 NaN；signed zero semantic-canonicalize為單一 $0$，public canonical output使用 `+0.0`。Finite-point correctness由 bit-pattern / exact integer-ratio semantics支撐，不以 tolerance判定。Finite binary64 point先 exact decode為 dyadic Rational後嵌入 semantic real；infinity sentinels不進 finite embedding domain。Public infinity endpoints使用真正的 Python `float('-inf')` / `float('inf')`；它們只屬 localization grid endpoint semantics。

對 finite target，`±inf`可作 bracket endpoints，但 theorem-5 strict-nearest `approx.point`與 theorem-3 `grid_project()` result都必為 finite binary64 value。即使 target超出最大 finite binary64 magnitude，`grid_project(Binary64Grid())`仍回 finite near-nearest point，不套 exact-class conversion overflow policy；public contract 不額外指定在多個合法 near-nearest points 間的 tie-breaking。

Exact classes的 `float()` / `complex()`不透過這個 grid決定 overflow：它們遵循 `02` 的 Python exact-number conversion contract，在 exact overflow boundary finite raise `OverflowError`。General semantic classes仍不提供 Python correctly-rounded machine conversion；其 binary64 observation由本 grid的 `grid_bound` / `grid_localize` / `grid_project`提供，而 `grid_project`只承諾 near-nearest。

## 15.5 Complex product grids and probes

對 algebraic isolation / internal geometry，可由一維 rational grids建立 product grids，其 exact points materialize為 `GaussianRational`。這只是 internal probe substrate；v1不提供 general `ComputableComplex` 的二維 public grid-localization/projection API。Coordinatewise observation透過 `real_part()` / `imag_part()` 的 real `grid_bound()` / `grid_localize()` / `grid_project()`完成。

# 16. Public computational categories

## Category A — Guaranteed-finite ordinary API

例如：

```python
x.bound(width=epsilon)
x.grid_bound(grid)
x.grid_project(grid)
x.grid_localize(grid)
alpha.is_real()
value.downgrade()
value.upgrade(numeric_class)
```

對合法 request guaranteed finite return / finite raise。`try_as(numeric_class)` 亦屬此類，但只對 registry 已固定 guaranteed-finite recognition 的 source-target pair合法。

## Category B — Guaranteed-finite certificate-gated partial operation

例如 general semantic division：

```python
x / y
z / w
```

ordinary call 本身不得 semantic-block：domain 已 certified 時 finite construct；invalidity 已 certified 時 finite mathematical exception；否則 finite `UnresolvedDomainError`。

## Category C — Explicit semantic process

例如：

```python
x.compare_process(y)
x.relation_process(y, relation)
x.membership_process(numeric_class)
x.downgrade_process()
divide_process(x, y)
```

Process construction finite；resolution 可 diverge。

## Category D — Explicit unbounded resolve

```python
process.resolve()
```

明確允許不返回。

## Category E — Trust-boundary assertion

例如：

```python
x.assume_relation(y, relation)
x.assume_membership(numeric_class, truth)
x.assume_grid_membership(grid, truth)
```

Assertion truth 是 promised precondition。若 promise 為假且目前無 finite contradiction evidence，依 promise才能完成的 absorption / identification可不終止；這個例外不得被 ordinary arithmetic/comparison API 模仿。

Machine-format correctly-rounded selection、floor/ceil/round semantic processes與 elementary functions不屬第一版 frozen categories。

# 17. Partial operation architecture

Ordinary operation flow：

```text
inspect persistent enclosure / residual exact knowledge
→ domain validity already entailed (for example enclosure excludes 0 / lies in positive region)?
      yes -> construct finite
→ invalidity certified?
      yes -> raise mathematical error
→ otherwise
      raise UnresolvedDomainError
```

Explicit process flow：

```text
create resumable domain/result process
→ each finite work unit advances finite state
→ commit any certified intermediate facts immediately
→ valid domain established -> resolve result
→ invalid domain established -> raise mathematical error
→ boundary may remain Pending indefinitely
```

---

# 18. Public API surface

## 18.0 Common support and regime-conversion surface

Relation enum：

```python
Relation.LESS
Relation.LESS_EQUAL
Relation.EQUAL
Relation.NOT_EQUAL
Relation.GREATER_EQUAL
Relation.GREATER
```

All five public numeric regimes use the conversion contract from `02` §14.1：

```python
value.try_as(numeric_class)      # only registered guaranteed-finite source-target recognition
value.downgrade()                # guaranteed finite; lowest currently recoverable regime
value.downgrade_process()        # explicit semantic search; may remain Pending
value.upgrade(numeric_class)     # downgrade first, then legal guaranteed-finite lift
```

`upgrade()` 必把 pre-upgrade `downgrade()` result保存為可有限恢復的 floor；ordinary promotion共用 downgrade-first target selection，但不啟動 `downgrade_process()`。

## 18.1 `ComputableReal`

Construction：

```python
ComputableReal.from_comparator_source(source)
```

Guaranteed-finite observation：

```python
x.bound(width=epsilon)
x.grid_bound(grid)
x.grid_project(grid)
x.grid_localize(grid)
```

Guaranteed-finite structural introspection：

```python
x.exact_source()  # never semantic-searches
```

Semantic process：

```python
x.compare_process(y) -> DecisionProcess[Order]
x.relation_process(y, relation) -> DecisionProcess[bool]
x.membership_process(numeric_class) -> DecisionProcess[bool]
x.downgrade_process()
```

`compare_process` accepts operands already known by guaranteed-finite evidence to be real-valued. A general `ComputableComplex` is accepted only when persistent membership knowledge already certifies `ComputableReal`; the call itself never starts a membership process. `relation_process` uses ordered relations on real operands and promotes `EQUAL` / `NOT_EQUAL` to complex semantics when needed. Rational probes use these same public methods; `compare_rational_process(q)` remains internal to comparator-source protocol only.

Partial-operation process：

```python
divide_process(x, y)
```

倒數寫成 `divide_process(1, y)`；reciprocal-specific state / `ReciprocalNode` 可以是 internal primitive，但不是第二個 public process spelling。

Assertions：

```python
x.assume_relation(y, relation)
x.assume_membership(numeric_class, truth)
x.assume_grid_membership(grid, truth)
```

General semantic Python truthiness/rich comparison/hash/correctly-rounded machine projection遵守 `02` 的 finite-safety contract：`float()` / `complex()` finite `TypeError`。Binary64語意輸出由 `Binary64Grid` theorem-backed observation承擔，其中 `grid_project()` 是 guaranteed-finite near-nearest single point，而不是 Python conversion。

## 18.2 `ComputableComplex`

Construction / guaranteed-finite observation：

```python
ComputableComplex.from_parts(real, imag)
z.real_part()
z.imag_part()
z.box(width=epsilon)
z.exact_source()  # finite structural introspection; never semantic-searches
```

Semantic process：

```python
z.membership_process(numeric_class) -> DecisionProcess[bool]
z.relation_process(w, relation) -> DecisionProcess[bool]
z.component_compare_process(w)
    -> tuple[DecisionProcess[Order], DecisionProcess[Order]]
z.direction_process(w, direction=u)
    -> DecisionProcess[Order]
z.downgrade_process()
```

Complex `relation_process` only accepts `Relation.EQUAL` / `Relation.NOT_EQUAL`; ordered relations finite `TypeError`. `membership_process(ComputableReal)` is the explicit semantic-domain bridge for later real ordering and commits persistent real/non-real evidence on resolution. A `True` result also makes `real_part()` a guaranteed-finite same-value `ComputableReal` reconstruction, so the recoverable floor may move to the real regime. `component_compare_process` accepts the full scalar numeric tower through finite promotion to `ComputableComplex`. `direction` 走 §3.1 finite Gaussian-rational-valued recognizer，recognized zero finite raise `ValueError`，recognized non-$\mathbb Q(i)$ numeric value finite `TypeError`。

A real `compare_process` must not hidden-start `z.membership_process(ComputableReal)` when handed an uncertified general `ComputableComplex`. User-facing documentation must recommend: create/advance that membership process first; use `z` in real-domain APIs only after it resolves `True`; keep the process `Pending` otherwise.

Assertions：

```python
z.assume_relation(w, relation)                 # EQUAL / NOT_EQUAL only
z.assume_membership(numeric_class, truth)
```

Partial-operation process：

```python
divide_process(z, w)
```

Coordinatewise standard-grid localization透過 `real_part()` / `imag_part()` 的 real APIs；第一版不提供二維 public grid localization或 `approx_complex`。

# 19. Thread-safety policy

本規格 explicitly **not thread-safe by contract**。

Users sharing the same numeric graph / process across threads must externally synchronize。

Thread-safe implementation may additionally use：

- atomic knowledge transactions；
- intern-table locks；
- process locks；

without changing mathematical semantics。

---

# 20. Distribution

開發採多模組 package。

若需要 single-file release：

```text
package source
→ build script
→ generated Computable.py
```

Distribution format 不得反向決定 internal architecture。
