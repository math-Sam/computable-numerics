# Computable：Test and Benchmark Specification

Correctness 不只等於「最後顯示的數字對」。完整 correctness：

$$
\boxed{
\text{value correctness}
+
\text{termination correctness}
+
\text{representation invariants}
+
\text{knowledge consistency}
+
\text{graph correctness}
+
\text{performance behavior}.
}
$$

---

# 1. Test categories

## T1 — Exact-value tests

適用：

```text
Rational
GaussianRational
Polynomial
Algebraic
Exact DAG leaves
```

禁止只用 float tolerance 作 correctness oracle。

## T2 — Certified observation tests

對：

```python
x.bound(width=epsilon)
z.box(width=epsilon)
```

驗證 containment 與 requested width。

Synthetic source 可持 hidden exact oracle，只供 test framework 使用。

## T3 — Semantic process tests

測：

- finite-resolving non-boundary cases；
- equality boundary repeated finite `Pending`；
- certificate-assisted equality finite resolve；
- invalid partial-domain process finite raise；
- resolved result stability。

## T4 — Work-budget tests

`advance(work=N)` 對每個 finite valid $N$ 必 finite。

測：

```text
N=1
small N
large N
already-resolved
invalid N
```

並 instrument transition count，確認不超過 promised cooperative steps。

Validation：`work` 走 guaranteed-finite exact integer-valued numeric recognizer；`0` / `False` / `0.0` / `Rational(0)` 等 exact zero inputs 不推進，`True` / `1.0` / `Fraction(1,1)` / `Rational(1)` / `GaussianRational(1,0)` / `Algebraic(1)` / `complex(1,0)` 等都等同 one work unit。Exact negative integer -> `ValueError`；可 finite exact 分類但 non-integral/non-real numeric value -> `TypeError`；general computable classes與 parser-only syntax不啟動 hidden recognition。`resolve()` 不屬 finite-work test；它是明示允許不終止的 unbounded resolution boundary。Terminal exception process 後續 call 消耗 0 work，穩定 re-raise same exception class。

## T5 — Knowledge tests

測：

- provenance；
- immediate process commit；
- interval / rectangle as primary persistent knowledge；
- qualitative fact absorption into stronger enclosure；
- derived-node persistent knowledge；
- contradiction rejection；
- lossless compaction；
- trust-user assertion behavior；
- malformed / finitely invalid certificate finite `InvalidCertificateError`，且 failed verification 不得 commit knowledge。

---

# 2. Rational construction and invariants

Constructor conversion 必測：

- `Rational(Rational(...))` preserves exact value and returns frozen/interned canonical value；若 input 是 mutable working Rational，constructor 不得 side-effect freeze / intern 該 input；
- Python `int` maps exactly to denominator `1`; `False/True` map exactly to `0/1`；
- `fractions.Fraction(a,b)` maps exactly to the same reduced rational；
- finite `float` uses exact binary64 value: `Rational(0.1) == Rational(*0.1.as_integer_ratio())`；
- real finite Python `complex` is accepted by mathematical value: `Rational(complex(1.5, -0.0)) == Rational(3,2)`；nonzero imaginary coordinate finite `TypeError`, non-finite component `ValueError`；
- real `GaussianRational` and rational-valued `Algebraic` are accepted through guaranteed-finite exact downcast; non-real Gaussian and irrational/non-rational Algebraic finite `TypeError`；
- decimal string is decimal-exact: `Rational("0.1") == Rational(1,10)` and generally differs from `Rational(0.1)`；
- string forms cover integer, signed decimal, leading/trailing decimal point, scientific notation, and one `/` with optional whitespace around slash；
- malformed string -> finite `ValueError`；
- string zero denominator -> `ZeroDivisionError`；
- `float("inf")`, `float("-inf")`, `float("nan")` -> finite `ValueError`；
- unsupported input -> `TypeError`；
- `Rational(False) == Rational(0)` and `Rational(True) == Rational(1)`；
- tuple input recursively parses a ratio: `Rational((1,2)) == Rational(1,2)`；
- nested tuples recursively compose ratios: `Rational((1,2),(3,4)) == Rational(2,3)` and `Rational(((1,2),(3,4))) == Rational(2,3)`；
- two-argument constructor accepts arbitrary `RationalInput` recursively, e.g. strings / `Fraction` / finite float / real finite complex / real GaussianRational / rational-valued Algebraic / nested tuples；
- a divisor that recursively resolves to zero at any nesting depth -> `ZeroDivisionError`；
- malformed tuple length or unsupported nested element -> finite `TypeError`；
- nested `bool` follows the same recursive Python-int rule at every depth, e.g. `False -> 0`, `True -> 1`；
- external numeric scalar conversion covers Python `int` (including `bool` as `0/1`), `fractions.Fraction`, finite `float` through exact Rational lifting, and finite Python `complex` through coordinatewise exact GaussianRational lifting；tuple / `str` remain explicit-constructor syntax and are not v1 numeric value operands；
- Python numeric equality/hash interoperability: `Rational(1) == True`, `Rational(0) == False`, `Rational(1) == complex(1,0)`, reflected equality holds, and hashes agree with every equal Python numeric value；
- implicit `str` / tuple numeric coercion is forbidden in core dispatch：arithmetic/ordering dunders return `NotImplemented` for these unsupported operand types (leading to normal Python `TypeError` absent reflected handling), and equality does not parse them numerically；explicit `Rational(text_or_tuple)` is the v1 boundary。
- finite Python `complex` exact conversion: each coordinate equals its exact binary64 ratio; `complex(0.1, -0.0)` lifts to `GaussianRational(Rational(0.1), Rational(0))`; any NaN/inf component finite `ValueError`；
- arithmetic/equality reflected dispatch with finite Python `complex` preserves exact GaussianRational semantics rather than projecting library values to machine complex；

Lifecycle / representation 必測：

- denominator $>0$；
- `Rational(...)` / named constants return frozen/interned values；
- `copy.copy(r)` / `r.__copy__()` returns a distinct mutable same-value working object；
- mutable working value可 unreduced；
- `simplify()` on mutable unreduced value canonical-reduces in place, returns `None`, and leaves receiver mutable；on frozen canonical value it is a finite no-op；it never performs interning by itself；
- non-in-place arithmetic does not mutate operands and may return mutable working result；
- in-place arithmetic mutates same object iff receiver is working；frozen receiver is not changed and operation rebinds to a fresh working result；
- private `._numerator` / `._denominator` may deliberately be unreduced while maintaining positive denominator；public `.numerator` / `.denominator` getter access finite-simplifies first and returns the unique canonical pair；
- property reads on a mutable unreduced fixture mutate only its representation to canonical form, not its value, mutability, or interning state；
- mutable working direct setters are public and value-level：after RHS validation, receiver is first simplified to canonical pre-assignment pair `(n,d)`; then `r.numerator = u` yields exact value `parse(u)/d`, while `r.denominator = v` yields `n/parse(v)`；
- setter RHS covers every `RationalInput`, including nested tuple / string / `Fraction` / finite float / real finite complex / real `GaussianRational` / rational-valued `Algebraic`；setter never stores a non-`int` object in the integer fields；
- denominator setter with recursively parsed zero raises `ZeroDivisionError` transactionally and leaves receiver unchanged；malformed RHS similarly leaves receiver unchanged；
- successful setter clears stale hash state, updates simplification state, and preserves positive denominator even for negative rational denominator RHS；
- frozen receiver direct `.numerator` / `.denominator` assignment raises `ValueError` and leaves receiver unchanged；
- setter semantics are **independent of the pre-assignment raw working pair**：two equal mutable values with different unreduced `(_numerator,_denominator)` representations must produce equal results under the same property assignment；
- frozen receiver setter checks occur before RHS parsing, so malformed RHS on a frozen receiver still raises the frozen-mutation `ValueError`；
- direct writes to `._numerator` / `._denominator` are outside the supported API and need not preserve any contract；
- `hash(r)` on mutable working value succeeds finitely, simplifies as needed, computes stable value hash, and freezes that same object；
- after first hash, value mutation is rejected and repeated hash is identical；
- inserting a mutable Rational into `dict` / `set` therefore freezes it through normal Python hashing；
- Python numeric equal-hash compatibility：equal `int` / `fractions.Fraction` / finite `float` values have the same hash as `Rational`；include `1`, `1/2`, exact dyadic subnormals, huge integers, negative values, and values not exactly representable as float；
- `intern()` return value -> simplified + frozen + stable hash + canonical weak-interned sharing；
- cache-hit `intern()` returns the pre-existing canonical object；receiver 本身只要求 value simplified，不要求 freeze；
- cache-miss `intern()` may freeze/register receiver and return `self`；
- frozen cannot mutate value；
- equal interned rationals share canonical identity while live when cache hit；
- weak table不永久 retain；
- persistent structures拒絕 / 自動 intern mutable Rational according to API contract；
- no denominator-zero infinity / NaN state；
- `bool(r)` is `False` iff exact value is zero, including mutable unreduced zero fixtures；
- exact-class binary64 projection boundary: let $T_{64}=2^{1024}-2^{970}$; `float(Rational(T64-1))` / its negative counterpart round to finite `sys.float_info.max` magnitude, while exact $|r|\ge T_{64}$ raises `OverflowError` (including exact equality $|r|=T_{64}$); underflow to zero remains ordinary finite rounding；
- `complex(r)` has correctly-rounded finite real coordinate and exact binary64 zero imaginary coordinate, with the same overflow boundary and no feedback into correctness；exact-class projection never returns `±inf` for overflow。

---

# 3. Rational arithmetic properties

Integer-power contract：exponent 走 guaranteed-finite exact integer-valued numeric recognizer；同一整數以 `int/bool`、integral `Fraction`、integral finite `float`、real-integral finite `complex`、`Rational`、real-integral `GaussianRational`、integer-valued `Algebraic` 表示時結果完全一致；positive/zero/negative exponents exact；$0^0=1$；zero to negative exponent -> `ZeroDivisionError`；finitely recognized non-integer numeric exponent -> `TypeError`；general computable exponent不 hidden resolve。

$$
(a+b)-b=a,
$$

$$
(ab)/b=a\qquad(b\ne0),
$$

$$
a(b+c)=ab+ac.
$$

Cover：

- negative；
- zero；
- huge numerator / denominator；
- mutable / frozen mixtures；
- cancellation-heavy inputs。

`fractions.Fraction` 可同時作 constructor interoperability input 與 test oracle；runtime correctness 不得依賴把 general internal arithmetic delegated 給 `Fraction`。

---

# 4. Rational benchmarks

## B-R1 random multiplication chains

## B-R2 random addition chains

Bit sizes至少：

```text
32
128
512
2048
8192
```

比較：

- lazy normalization；
- eager reduction；
- cross-cancel variants。

## B-R3 high cancellation

例如反覆：

$$
\frac pq\frac qp.
$$

## B-R4 shared denominator

大量：

$$
\frac{a_i}{D}.
$$

## B-R5 long bulk sum / product

任何 Rational reduction strategy 修改必跑完整 workload family。

---

# 5. GaussianRational invariants and exact arithmetic

Required properties：

- constructor dispatch covers `GaussianRational()`, `GaussianRational(value)`, and `GaussianRational(real, imag)`；zero-argument construction denotes zero；
- one-argument existing `GaussianRational` preserves denotation；finite Python `complex` exact-lifts both coordinates；Gaussian-rational-valued `Algebraic` downcasts finitely, while non-$\mathbb Q(i)$ `Algebraic` finite `TypeError`；general computable inputs never trigger hidden recognition；
- one-argument `RationalInput` is interpreted as a real value with zero imaginary coordinate, so `GaussianRational((1,2)) == GaussianRational(Rational(1,2), 0)`；
- two-argument coordinates accept the full recursive `RationalInput` syntax；nested examples such as `GaussianRational((1,2), (3,4))` denote $1/2+(3/4)i$ exactly；
- coordinate parse errors / zero-divisor errors propagate finitely according to Rational constructor semantics；
- coordinates are canonical frozen/interned `Rational` under persistent ownership；
- exact field laws against a pair-of-`fractions.Fraction` oracle in tests only；
- denominator-zero impossible inside coordinates；
- zero iff both coordinates zero；
- `bool(z)` iff at least one coordinate is nonzero；
- real iff imaginary coordinate zero；
- conjugation involutive；
- $z\overline z$ is nonnegative Rational；
- division finite and exact for nonzero denominator；
- integer powers use the shared finite exact integer-valued recognizer across all supported finite numeric representations; $0^0=1$, and zero negative exponent raises `ZeroDivisionError`；
- non-real ordering raises `TypeError`；
- real-valued `int` truncates toward zero；`floor` / `ceil` exact；`round` uses half-to-even；
- `round(z, ndigits)` uses the shared finite exact integer-valued recognizer；different supported numeric representations of the same positive / zero / negative integer `ndigits` return the same exact `Rational`；
- non-real `int` / floor / ceil / round all raise `TypeError` finitely；
- `float()` non-real raises `TypeError`; real-valued projection follows the same $T_{64}$ exact-number overflow boundary as Rational and raises `OverflowError` at/beyond it；
- `complex()` projects both coordinates to finite binary64 values; either coordinate at/beyond $T_{64}$ raises `OverflowError`; projection does not feed back into correctness and never uses `±inf` as exact-class overflow output；
- finite Python `complex` operands exact-lift coordinatewise: arithmetic/equality agree with the corresponding `GaussianRational(Rational(real_float), Rational(imag_float))`; any NaN/inf component finite `ValueError`；
- reflected operations such as `complex(1,2) + GaussianRational(...)` preserve exact GaussianRational semantics and do not first project the library operand to machine complex。

Cross-type hash rule：if exact cross-class equality says `GaussianRational(a,0) == Rational(a)`, hashes must agree。If a `GaussianRational` equals a finite Python `complex`, its hash must also equal the Python complex hash。Equivalent algebraic values must satisfy the same Python equal-hash contract once hashed。

Explicit fixtures：

- rational-valued `Algebraic` hash == corresponding `Rational` hash；
- non-real $a+bi\in\mathbb Q(i)$ represented as `Algebraic` hash == corresponding `GaussianRational` hash；
- hashing / later isolator refinement does not change hash within one Python execution。

---

# 6. RationalRectangle and complex-probe tests

Public representation fixture：

```python
((a, b), (c, d))
```

If architecture uses internal `RationalClosedBox`, round-trip `tuple -> box -> tuple` must be exact and preserve canonical endpoint objects。

Test：

- endpoint ordering；
- closed-boundary containment；
- intersection；
- origin containment；
- center and all four corners return exact `GaussianRational`；
- repeated dyadic subdivision covers parent exactly；
- root / target lying on rectangle boundary is not dropped；
- exact Horner polynomial evaluation at Gaussian-rational probes matches direct exact arithmetic。

---

# 7. GaussianRational benchmarks

Benchmark：

- coordinate bit sizes 32–8192+；
- random add/multiply/divide chains；
- high cancellation；
- repeated conjugate / norm-square；
- rectangle subdivision；
- polynomial Horner evaluation for increasing degree / coefficient height。

The point is to confirm this regime stays dramatically cheaper than promoting the same values into general `Algebraic` root representations。

---

# 8. Polynomial tests

Every public `Polynomial` operation in `02` §7.9–§7.13 is guaranteed finite and must have direct conformance tests.

## 8.1 Construction and value protocol

必測：

- coefficient tuples are interpreted constant-first；in particular `Polynomial((2, -3, 1))` denotes $2-3X+X^2$；
- constructor、stored `.coefficients`、serialization / structural key、Horner evaluation and derivative all agree on the same constant-first orientation；
- coefficients use the finite exact integer-valued recognizer：integral `int/bool`、`Fraction`、finite `float`、real finite `complex`、`Rational`、real `GaussianRational`、integer-valued `Algebraic` all canonicalize to ordinary Python `int` coefficients；finitely classifiable non-integral/non-real numeric coefficients finite `TypeError`；parser-only `str` / tuple ratio and general computable classes are not accepted；
- `Polynomial((True, False, True)) == Polynomial((1, 0, 1))`, and `.coefficients` contains ordinary `int` values rather than stored `bool` objects；
- canonicalization trims trailing high-degree zeros: `Polynomial((0, 0, 0)) == Polynomial((0,))` and `Polynomial((1, 2, 0, 0)) == Polynomial((1, 2))`；
- constructor canonicalization never divides out content or changes sign: `Polynomial((2, 2))` remains $2+2X$ and differs from `Polynomial((1, 1))`；
- `Polynomial((0,))` is the unique canonical zero representation；
- polynomial equality/hash are finite and consistent with the canonical coefficient tuple；
- for every tested Python `int` $n$, `Polynomial((n,)) == n` and `n == Polynomial((n,))` are both true, and `hash(Polynomial((n,))) == hash(n)`；
- Python `bool` follows integer equality: `Polynomial((1,)) == True`, `Polynomial((0,)) == False`, reflected equality also holds, and hashes agree；
- full constant-scalar equality bridge: for representative positive, negative, and zero integers $n$, test reflected equality and equal-hash against `Fraction(n,1)`, exact finite floats denoting $n$ (including `-0.0` for zero), finite `complex(n,0)`, `Rational(n)`, `GaussianRational(n,0)`, and `Algebraic(n)`；
- non-integral/non-real values such as `Fraction(3,2)`, `Rational(3,2)`, finite non-integral floats, `complex(1,2)`, non-real `GaussianRational`, and non-real/non-integral `Algebraic` compare unequal to every constant polynomial；
- nonconstant polynomials compare unequal to every scalar in the finite equality bridge, even when the scalar equals the polynomial's constant coefficient；
- `str` / recursive tuple `RationalInput` are never parsed by polynomial equality；
- general `ComputableReal` / `ComputableComplex` do not enter this finite equality bridge and continue to obey semantic-class rich-comparison rules；
- `hash(Polynomial((1,))) == hash(True) == hash(1) == hash(1.0) == hash(complex(1,0)) == hash(Fraction(1,1)) == hash(Rational(1)) == hash(GaussianRational(1,0)) == hash(Algebraic(1))`, with the analogous zero and negative-integer cases；
- zero polynomial has `.degree == -1` and `.leading_coefficient == 0`; nonzero degree / leading coefficient agree with the canonical tuple；
- `bool(p)` is false exactly for canonical zero；
- `Polynomial` is immutable after construction。

## 8.2 Arithmetic, powers, derivative, evaluation

Test unary `+/-`, `+ - *`, and reflected scalar operations through the finite integer-scalar recognizer. Integral representatives from `int/bool`, `Fraction`, finite `float`, finite `complex`, `Rational`, `GaussianRational`, and `Algebraic` must produce the same constant-polynomial arithmetic; recognized non-integral or non-real representatives must finite `TypeError` and never silently change the polynomial ring. General computable operands remain unsupported for polynomial scalar arithmetic because integerhood is not guaranteed finitely decidable.

For powers:

- exponent uses the finite exact integer-valued recognizer; every supported numeric representation of the same nonnegative integer gives the same result；
- `p**0 == Polynomial((1,))`, including zero polynomial；
- exact negative integer exponent finite `ValueError`；
- finitely recognized non-integral/non-real numeric exponent finite `TypeError`; general computable exponent does not trigger hidden recognition；
- repeated multiplication identities on random small cases。

For `derivative(order)`:

- `order` uses the same finite exact integer-valued recognizer；
- `order=0` identity；
- first/second derivative coefficient identities across multiple exact numeric representations of `0/1/2`；
- sufficiently high derivative canonical zero；
- exact negative integer order `ValueError`; finitely recognized non-integral/non-real numeric order `TypeError`。

For `evaluate` / `__call__`:

- exact Horner result for `int`, `Fraction`, finite `float` (via exact Rational coercion), finite `complex` (via exact GaussianRational coercion), `Rational`, `GaussianRational`, and `Algebraic` points；
- `ComputableReal` / `ComputableComplex` inputs return the correct promoted expression construction finitely and do not resolve semantic relations during evaluation；
- `str` / recursive tuple constructor syntax is not implicitly parsed by evaluation；
- `p(x)` and `p.evaluate(x)` have identical dispatch / denotation semantics；
- evaluation orientation catches accidental leading-first implementations；
- no machine-float arithmetic/tolerance correctness path。

## 8.3 Content, primitive part, pseudo-division, exact division, gcd

Test:

- `content(0) == 0`；nonzero content is gcd of absolute coefficients and non-negative；
- `primitive_part(0) == 0`；for nonzero `p`, `content(p) * primitive_part(p) == p` and primitive part preserves overall sign；
- `pseudo_divmod` accepts every integral representative from the shared scalar bridge as the corresponding constant divisor, rejects recognized non-integral/non-real scalars with finite `TypeError`, and zero divisor finite `ZeroDivisionError`；
- for every pseudo-division result `(s,Q,R)`, exactly `s*A == B*Q + R`, `s == abs(lc(B))**max(deg(A)-deg(B)+1,0)`, and `R==0 or deg(R)<deg(B)`；
- include negative-leading-divisor cases to confirm public `scale` is positive and canonical；
- `exact_div` uses the same integral-scalar constant embedding；non-integral/non-real recognized scalar finite `TypeError`; `exact_div(0)` finite `ZeroDivisionError`；divisible cases reconstruct exactly；non-divisible cases finite `ValueError`；
- scalar second operands for `gcd` use the same integral recognizer, so e.g. `p.gcd(2.0) == p.gcd(Polynomial((2,)))`; non-integral/non-real recognized scalars finite `TypeError`；
- `gcd(0,0) == 0`；`gcd(p,0)` is the positive-leading associate of `p`；
- gcd includes content gcd, e.g. `gcd(2X,4X)=2X`, divides both inputs, and has positive leading coefficient when nonzero；
- random small polynomial Bézout/content cross-checks may use an independent rational-polynomial oracle in tests, but the library implementation itself must remain exact integer/Rational based。

## 8.4 Square-free decomposition and factorization

For every nonzero `p`, both public result payloads must reconstruct exactly

$$
p=unit\cdot content\prod_j factor_j^{multiplicity_j}.
$$

Test result invariants:

- `unit in {-1,+1}`；`content > 0`；multiplicities positive Python `int`；
- returned factors are nonconstant, primitive, positive-leading；
- nonzero constants produce empty factor list with sign/content split；
- zero finite `ValueError` for both APIs；
- square-free decomposition factors are square-free and pairwise coprime；same multiplicity is combined and multiplicities are strictly increasing；
- irreducible `factor()` combines equal factors and deterministically sorts by `(degree, coefficients)`；
- factor irreducibility is independently checked on bounded test cases；
- repeated-root examples such as $(X-1)^3(X+2)^2$ preserve multiplicities exactly。

## 8.5 Resultant and Sturm sequence

Resultant tests:

- integral scalar second operands are coerced to constant polynomials; recognized non-integral/non-real scalar and otherwise unsupported operands finite `TypeError`；
- either zero input finite `ValueError`；
- constant cases satisfy the stated powers and two nonzero constants return `1`；
- `Res(p,q)=0` iff sampled nonconstant cases have a common complex root / nontrivial gcd；
- symmetry law
  $$
  \operatorname{Res}(p,q)=(-1)^{\deg p\deg q}\operatorname{Res}(q,p)
  $$
  on nonzero inputs；
- multiplicativity on bounded random cases。

Sturm tests:

- zero finite `ValueError`; nonzero constant gives a one-element sequence；
- every returned member is primitive integer polynomial；
- only positive rescaling relative to the ordinary rational Sturm chain is permitted, so sign-variation behavior is preserved；
- root counts derived independently from the returned sequence agree with `real_root_count()` on intervals whose endpoints include root and non-root cases。

## 8.6 Exact real root queries

Test `real_root_count(interval=None)` and `isolate_real_roots(interval=None)`:

- zero finite `ValueError`; nonzero constant returns `0` / `()`；
- counts are **distinct-root** counts under multiplicity；
- no-interval count covers all real roots；
- closed intervals include roots at both endpoints；
- reversed endpoints finite `ValueError`; malformed interval shape/type finite `TypeError`; endpoint `RationalInput` errors propagate；
- returned intervals contain canonical frozen/interned Rational endpoints；
- isolation intervals are pairwise disjoint, sorted left-to-right, and each contains exactly one distinct root；
- rational roots may produce degenerate `[q,q]` intervals；
- with an input interval every output interval lies inside it and output cardinality equals `real_root_count(input_interval)`；
- include repeated roots, closely spaced roots, and input-boundary roots。

## 8.7 Exact complex root queries

Test `complex_root_count(box)` and `isolate_complex_roots(box=None)`:

- zero finite `ValueError`; nonzero constant returns `0` / `()`；
- malformed rectangle shape/type finite `TypeError`; reversed real or imaginary endpoints finite `ValueError`; endpoint parse errors propagate；
- closed rectangles count roots on edges and corners；
- counts are distinct-root counts under multiplicity；
- global isolation covers every distinct complex root exactly once；
- box-restricted isolation covers exactly the roots counted by `complex_root_count(box)` and every returned box lies inside the requested box；
- returned boxes are pairwise disjoint and each has exact distinct-root count `1`；
- deterministic output ordering uses `(real_lower, imag_lower, real_upper, imag_upper)`；
- conjugate-pair, repeated-root, rational-real-root, root-on-boundary, and tightly clustered complex-root cases；
- all endpoint payloads are canonical frozen/interned Rational and no float/tolerance path is correctness-relevant。

---

# 9. Algebraic construction

Public overload tests：

```python
Algebraic(value)
Algebraic(polynomial, box)
```

必測：

- `Algebraic(2)`、`Algebraic("1/3")`、`Algebraic((1,3))` 皆 finite exact embed to the corresponding Rational algebraic value；
- `Algebraic(GaussianRational(a,b))` finite exact embeds without floating root search；
- two-argument form is interpreted only as `(Polynomial, box)` and never as Rational-style numerator/denominator；
- box endpoints recursively accept `RationalInput`, then persistent storage contains frozen/interned `Rational` endpoints；
- unsupported polynomial type / malformed box container shape finite `TypeError`；degree $<1$、invalid endpoint order、or failure of the unique-distinct-root invariant finite `ValueError`；nested endpoint parser errors propagate according to RationalInput rules；
- a single tuple `(polynomial, box)` is not silently reinterpreted as the root constructor.

同一 mathematical value 使用不同：

- annihilating polynomial；
- reducible polynomial；
- repeated-factor polynomial；
- isolating rectangle width；
- rectangle crossing real axis；
- root-on-boundary isolation；

建立，全部應得到相同 equality semantics。

Constructor 不應因 test root 為 real 就強制把 imaginary interval壓成 zero。

Finite embedding tests：

- every `Rational` embeds to equal `Algebraic` finitely；
- non-real `GaussianRational(a,b)` embeds using an exact integer polynomial equivalent to $X^2-2aX+(a^2+b^2)$ and a rational point box selecting $a+bi$；
- embedded Gaussian value compares equal to the source and uses the same cross-type hash tier；
- embedding performs no floating root search。

---

# 10. Algebraic representation refinement

建立 $\alpha$ 後記錄：

```text
initial polynomial
initial box
```

觸發：

- `is_real()`；
- isolation refinement；
- equality；
- hash；

確認 working representation 可以改變，但：

$$
\text{denotation before}=\text{denotation after}.
$$

尤其 hash canonicalization 後：

- defining polynomial 可變成 minimal polynomial；
- box 可保持或 refine；
- cached hash stable。

---

# 11. Algebraic equality

測：

- same root / different rectangles；
- same root / different polynomials；
- distinct roots same polynomial；
- conjugates；
- real vs non-real；
- rational embedded as algebraic；
- multiplicity > 1 but same distinct root。

全部 finite total。另測 `bool(alpha)`：iff $\alpha\ne0$，對 real / non-real algebraic values 都 finite total。

---

# 12. Algebraic realness

測：

- rational；
- real irrational；
- pure imaginary；
- generic non-real；
- real root with box crossing real axis；
- real root on box boundary；
- non-real box initially crossing real axis but uniquely selecting non-real root if valid。

`is_real()` finite total；constructor 本身不應 eager 觸發除非 required by input validation。

Public finite recognizers：

- `try_as(Rational)` returns exact `Rational` iff value lies in $\mathbb Q$, otherwise `None`；
- `try_as(GaussianRational)` returns exact `GaussianRational` iff value lies in $\mathbb Q(i)$, otherwise `None`；
- both terminate on rational, Gaussian-rational, real/non-real algebraic irrational fixtures；
- recognizers may populate exact caches but never change denotation。

---

# 13. Algebraic arithmetic

$$
(\alpha+\beta)-\beta=\alpha,
$$

$$
\frac{\alpha\beta}{\beta}=\alpha
\qquad(\beta\ne0).
$$

另外：

- conjugation respects `+` / `*` and `conjugate()` / `real_part()` / `imag_part()` all return exact `Algebraic` values with the expected denotations；
- target-root identification；
- real result 不要求 eager `is_real` cache unless path needs it；
- no incorrect realness tagging；
- integer powers use the shared finite exact integer-valued recognizer across all supported finite numeric representations; $0^0=1$, and zero negative exponent raises `ZeroDivisionError`；
- real algebraic `int` truncates toward zero，`floor` / `ceil` exact；
- `round(alpha)` / `round(alpha, ndigits)` 使用 exact midpoint comparison + half-to-even；`ndigits` 走 shared finite exact integer-valued recognizer，各種 exact numeric representations of the same integer必回相同 exact `Rational`；
- midpoint fixtures 必含恰好落在 half-grid boundary 的 algebraic/rational cases，不得用 tolerance；
- non-real algebraic integer/rounding protocols finite `TypeError`；
- `Algebraic(value)` accepts an existing non-rational/non-real `Algebraic` without forcing it through the Rational parser, preserving denotation；finite Python `complex` is accepted by exact GaussianRational lifting；general computable inputs do not trigger algebraicity search；
- finite Python `complex` operands enter Algebraic arithmetic/equality through exact GaussianRational lifting; values with non-finite components finite `ValueError`；
- if an `Algebraic` value equals a finite Python `complex`, the cross-type hash tier agrees with that Python complex hash；
- real `float(alpha)` and both-coordinate `complex(alpha)` use exact comparisons against $T_{64}=2^{1024}-2^{970}$: every required coordinate with magnitude $<T_{64}$ correctly rounds to a finite binary64 value, while equality to or excess beyond the boundary raises `OverflowError`; include positive/negative boundary, one-unit-below boundary, and complex one-coordinate-overflow fixtures；exact-class projection never returns `±inf` for overflow。

---

# 14. Algebraic canonical hash

Equal values -> equal hash，即使 initial representation 不同。

驗：

1. minimal polynomial canonical convention；
2. roots sorted by modulus；
3. equal modulus sorted by principal argument in $[0,2\pi)$；
4. lower root index deterministic；
5. hash finite；
6. hash stable after later box refinement；
7. hash stable after other exact caches change；
8. hash computation does not change denotation；
9. $\alpha\in\mathbb Q$ / $\mathbb Q(i)$ uses the cross-type compatible hash tier rather than an unrelated algebraic-only tuple hash。

Special cases：

- roots on positive real ray have argument $0$；
- lower-half-plane roots use argument near $2\pi$；
- equal-modulus conjugate pairs；
- zero root。

---

# 15. DecisionProcess statefulness

Synthetic process：resolve after exactly $k$ transitions。

Verify：

```python
p.advance(work=a)
p.advance(work=b)
```

continues from state $a$ and resolves according to cumulative progress, not restart。

Already-resolved call consumes no semantic work。

Synthetic failing process：raise after exactly $k$ transitions；after first terminal raise, repeated finite-work calls consume zero additional transitions and re-raise same exception class。

Public process object exposes exactly the finite-work `advance(...)` and unbounded `resolve()` execution surfaces；public-surface enumeration tests must match this pair。

# 16. DecisionProcess fairness

Scenarios：

- one permanent pending + one resolves after 10；
- 100 pending + one resolves；
- nested combines；
- short-circuit；
- certificate emission；
- branches that commit knowledge before final resolution。

Finite branch不得 starvation。

---

# 17. Pending semantics

`bool(Pending())` -> `TypeError`。

Repeated pending must never be interpreted as equality / false / domain invalidity。

---

# 18. Knowledge provenance and trust-user assertions

## Relation assertions — strict absorption

For synthetic real sources with hidden exact oracle, test：

```python
x.assume_relation(y, Relation.LESS)
x.assume_relation(y, Relation.GREATER)
x.assume_relation(y, Relation.NOT_EQUAL)
```

True promises return only after persistent intervals geometrically entail the relation：

```text
LESS       -> R_x < L_y
GREATER    -> R_y < L_x
NOT_EQUAL  -> I_x ∩ I_y = ∅
```

No parallel `positive=True` / `nonzero=True` / relation flag is required once geometry entails the fact。Complex `NOT_EQUAL` must return only after at least one coordinate obtains strict separation。

## Relation assertions — equality-containing residual semantics

Test：

```python
x.assume_relation(y, Relation.EQUAL)
x.assume_relation(y, Relation.LESS_EQUAL)
x.assume_relation(y, Relation.GREATER_EQUAL)
```

Requirements：

- finite contradiction already known -> immediate `InconsistentKnowledgeError`；
- all sound geometric propagation is committed；for equality, current compatible bounds may be intersected / transported between both nodes；
- relation content not entailed by geometry remains persistent residual knowledge；
- compaction removes the residual only after another carrier fully entails it。

## Numeric-domain membership assertions

Test both truth values for：

```python
x.assume_membership(Rational, truth)
x.assume_membership(GaussianRational, truth)
x.assume_membership(Algebraic, truth)
z.assume_membership(ComputableReal, truth)
```

Verify mathematical-domain semantics rather than Python `isinstance`。Domain-inclusion implications must propagate finitely；for example Rational-True entails GaussianRational-True and Algebraic-True, while Algebraic-False entails GaussianRational-False and Rational-False。A bare Rational-True promise on a general `ComputableReal` must **not** fabricate numerator/denominator or force ordinary `downgrade()` to `Rational` without constructive evidence。

## Grid-membership assertion — True branch identifies exact point

For all standard real grids：

```python
x.assume_grid_membership(grid, True)
```

Use target fixtures known to lie on the grid。The call must return only after unique point identification and exact-floor commit。Verify：

- `IntegerGrid()` -> `x.downgrade()` returns exact integer-valued `Rational`；
- `BoundedDenominatorGrid(N)` -> exact reduced `Rational` with denominator $\le N$；
- `Binary64Grid()` finite hit -> exact dyadic `Rational` equal to the binary64 point；
- no general equality classifier is required to prove the final identity; the trust promise + locally finite candidate separation is sufficient；
- after return, repeated exact-floor queries require no semantic source advancement。

Include the key distinction：`assume_membership(Rational, True)` alone need not identify a rational, while `assume_grid_membership(BoundedDenominatorGrid(N), True)` must identify it finitely。

## Grid-membership assertion — False branch absorbs into a gap

```python
x.assume_grid_membership(grid, False)
```

For off-grid targets, return only after persistent interval $[L,R]$ satisfies

$$
grid\cap[L,R]=\varnothing.
$$

Then verify theorem-2 adjacent localization can reuse the committed gap evidence without re-proving the promise。

## Contradiction and false promise

Contradictory trusted assertions must be transactional：finite-detectable contradiction raises `InconsistentKnowledgeError` and leaves prior state valid。Examples include `LESS` after known reverse strict order, `EQUAL` after disjoint intervals, membership True after exact lower-regime evidence proves impossibility, and grid True after a committed grid-gap enclosure。

False-but-not-yet-finitely-contradicted promises have **no termination requirement**。Tests must not treat timeout as mathematical evidence；instrumented synthetic providers / isolated subprocesses only verify that implementation never fabricates success or a negative semantic result。

# 19. Knowledge monotonicity / geometry-and-floor compaction

Sequential certified intervals：

$$
[-100,100],
[-10,10],
[-1,1],
[1/4,1].
$$

After compaction，可只保留 strongest interval（加必要 provenance summary），但 query semantics must still imply all earlier interval facts，並能直接回答相應 `Relation` queries。另測 recoverable floor由 `Algebraic -> GaussianRational -> Rational` 單調改善時，不遺失任何可恢復能力。

不要求 retain every historical proof object，也不要求 retain 已被 enclosure 完整 subsume 的 standalone predicate certificate。

---

# 20. Comparator-source contract, relation processes, and membership processes

建立 synthetic comparator sources 表示 hidden exact reals，並一律透過：

```python
x = ComputableReal.from_comparator_source(source)
```

建立 runtime object。驗證：

- constructor / classmethod finite，runtime 強持有 `source`；
- mutable working Rational probe在 source/process ownership boundary canonicalize 成 frozen/interned Rational；
- internal `source.compare_rational_process(q)` result sound；strict cases eventually resolve，exact hit without equality evidence可 `Pending`；
- public rational query使用 `x.compare_process(q)` / `x.relation_process(q, relation)`，不暴露 rational-specific public comparison spelling；
- source progress / cached certified bounds 在 repeated queries 中重用；
- one object lifetime內 source denotation不變；
- source若沒有 immutable construction key，不得與另一 source instance只因程式形狀相似而 structural-merge。

違反 trusted source semantic promises 的 adversarial fixture 不要求 runtime 自動判錯；測試只確認 runtime 不 fabricated 額外 semantic claims。

## Real semantic-process matrix

對 negative / zero / positive / equal-distinct pair fixtures測：

```python
x.compare_process(y)
x.relation_process(y, Relation.LESS)
x.relation_process(y, Relation.LESS_EQUAL)
x.relation_process(y, Relation.EQUAL)
x.relation_process(y, Relation.NOT_EQUAL)
x.relation_process(y, Relation.GREATER_EQUAL)
x.relation_process(y, Relation.GREATER)
x.membership_process(numeric_class)
```

Required behavior：strict order separation eventually resolves corresponding cells；equality boundary在無 equality evidence時可 repeated finite `Pending`；加入 valid equality certificate後相應 relation resolve。`Pending`不得被當作 False。

Operand-promotion matrix additionally verifies：

- ordered relation / `compare_process` accepts every registered finite exact operand finitely certifiable as real；known non-real exact values finite `TypeError`；
- uncertified general `ComputableComplex` finite `TypeError` without starting hidden real-domain membership work；
- after `z.membership_process(ComputableReal)` resolves `True` and commits persistent evidence, real `compare_process` accepts `z` through `real_part()` and ordinary `z.downgrade()` can recover the same-value `ComputableReal` view；after `False`, real APIs finite `TypeError`；while `Pending`, real comparison remains unavailable and no duplicate hidden process is started；
- `Relation.EQUAL` / `NOT_EQUAL` accept the full scalar tower including general complex values and promote to complex semantics when needed；
- `membership_process(Rational/GaussianRational/Algebraic/ComputableReal/ComputableComplex)` never confuses denotation membership with nominal Python class。

## Semantic downgrade process

Synthetic recognizers must test：

- `downgrade_process()` construction finite；
- a discovered lower representation commits immediately to recoverable floor even when outer call returns `Pending`；
- ordinary `downgrade()` observes that floor with zero unbounded search；
- reaching `Rational` resolves immediately as the absolute lowest regime；
- a mathematically rational general real with no finitely discoverable reconstruction evidence may remain `Pending` indefinitely；
- no test assumes that allowing nontermination makes rationality/algebraicity positively semidecidable in general。

# 21. Comparator -> bound exact-hit safety

專門建立 $x$ 等於大量 dyadic / rational query points 的 fixtures。

Generic adapter 不得因 naive midpoint equality 永久卡住。

對每個 legal width request 必 finite。

---

# 22. Width-resolution tests

Width coercion is value-based and guaranteed finite for both `ComputableReal.bound(width=...)` and `ComputableComplex.box(width=...)`. Equivalent positive-rational representatives from `int/bool`, `Fraction`, finite real `float/complex`, `Rational`, real `GaussianRational`, and rational-valued `Algebraic` must satisfy the same width contract. Exact zero/negative rational values finite `ValueError`; registered non-real/non-rational exact numeric values finite `TypeError`; general computable values and parser-only `str` / tuple syntax do not trigger hidden recognition.

Widths：

$$
1,
\quad
\frac12,
\quad
2^{-20},
\quad
10^{-50}.
$$

驗：

$$
L\le x\le R,
$$

$$
R-L\le\varepsilon.
$$

Source / node types：

- native comparator；
- exact leaf；
- derived node。

---

# 23. Theorem-1 `grid_bound()` tests

對三個 v1 standard grids 都測：

```python
IntegerGrid()
BoundedDenominatorGrid(max_denominator=N)
Binary64Grid()
```

在 localization tests 前，先驗證每個 canonical grid representation 的 **searchable computably embedded exact ordered realization** contract：

- well-formed canonical point codes semantic-valid；
- grid-point `< / = / >` finite total classify；equal denotations（含 binary64 signed zero canonicalization）finite recognize；
- search algorithm只在 denotationally distinct endpoints 的 promised domain上使用並 finite terminate；
- 每個 finite grid point的 embedding call guaranteed finite，且 embedded `ComputableReal` / comparator presentation與原 grid point exact 同值；
- infinity sentinels（若存在）不誤進 finite-point embedding domain；
- target-vs-grid-point semantic comparison由共同 embedding path導出，而不是 grid-specific duplicated comparator；
- 任意兩個 finite grid points（不只 adjacent pair）的 midpoint都可由 embedding + real affine construction finite 建立，並可對 target建立 resumable comparison；
- standard grid global bounding adapter對 arbitrary synthetic `ComputableReal` guaranteed finite。

回傳 $L,R\in G$ 必滿足：

$$
L\le x\le R,
$$

$$
|G\cap(L,R)|\le1.
$$

Additional checks：

- `BoundedDenominatorGrid(max_denominator=N)` endpoints 為最簡 Rational 且 denominator $\le N$；
- `max_denominator` 走 finite exact integer-valued recognizer：`1` / `True` / `1.0` / `Fraction(1,1)` / `Rational(1)` / `GaussianRational(1,0)` / `Algebraic(1)` / `complex(1,0)` 等價；exact integer $<1$ -> `ValueError`；non-integral/non-real finite numeric -> `TypeError`；
- `Binary64Grid()` endpoints 可為真正的 Python `float('-inf')` / `float('inf')`，不得為 NaN；finite endpoints 以 exact binary64 bit-pattern semantics 驗證；
- semantic projection overflow fixtures far above finite binary64 range still return a finite theorem-1 near-adjacent pair with an infinity endpoint rather than raising exact-class `OverflowError`；
- exact grid hit fixture 不要求 `(x,x)`；
- exact grid hit with explicit equality evidence may return a point bracket immediately；without equality evidence theorem-1 localization must still terminate via the near-adjacent rescue path；
- implementation 不得以「先 enumerate initial bracket 中全部 grid points」作一般 theorem strategy。

### Infinite-initial-span regression

建立 synthetic grid set $G$ 與 interpretation，其中 $G$ locally finite、interpretation searchable + computably embedded exact ordered

$$
G=\mathbb Z\cup\{-\infty,+\infty\}
$$

及 two-sided-bounding algorithm 固定回

$$
(-\infty,+\infty).
$$

此 initial bracket 含 infinitely many grid points，但 `grid_bound()` 仍必 finite terminate。Instrument search / comparison calls，確認 algorithm 是 target-directed adaptive refinement，而不是嘗試完成 whole-span enumeration。

這個 regression 專門防止錯誤再次引入「finite initial span」作 theorem hypothesis。

---

# 24. Theorem-2 off-grid adjacent-enclosure regression tests

Theorem 2 does not add a public method, but its promised strengthening is part of the formal correctness contract and must be tested through an internal theorem harness / shared localization helper.

For targets satisfying

$$
x\notin G,
$$

test that a Theorem-1 near-adjacent bracket guaranteed-finitely upgrades to a true adjacent bracket

$$
L\le x\le R,
\qquad
G\cap(L,R)=\varnothing.
$$

Required fixtures:

- target strictly between adjacent points;
- Theorem-1 bracket containing exactly one interior witness $g$, with target on each strict side of $g$;
- large / infinite initial spans;
- all three standard grids;
- promise-violation fixture $x=g\in G$: the internal search is allowed to remain pending, but must never emit an unsound adjacent bracket merely to force termination;
- no timeout / tolerance / guessed inequality may be used to exploit the promise.

This suite verifies the distinction “promise guarantees termination; it does not license unsound behavior outside the promised domain.”

---

# 25. Theorem-3 `grid_project()` tests

For all three v1 standard grids test:

```python
x.grid_project(IntegerGrid())
x.grid_project(BoundedDenominatorGrid(max_denominator=N))
x.grid_project(Binary64Grid())
```

For output finite grid point $g$, use an independent exact oracle to compute

$$
B_G(x,g):=\{h\in G\cap\mathbb R:|h-x|<|g-x|\}
$$

inside a finite local region proven sufficient to contain every possible closer point, and verify

$$
\boxed{|B_G(x,g)|\le1.}
$$

Do not merely test that the point “looks close”, and do not use floating tolerance.

Required cases:

- strict-nearest ordinary cases;
- exact grid hit: do not require the exact hit to be returned, only the near-nearest contract;
- exact midpoint of adjacent grid points;
- highly nonuniform spacing, preventing a fixed left/right endpoint from being incorrectly treated as universally near-nearest;
- a Theorem-1 near-adjacent bracket with one interior point, exercising the direct finite reduction to strict-nearest point or adjacent bracket before the outer-neighbor step;
- adjacent bracket $L<R$ with both immediate outer neighbors $P,S$ finite;
- exact boundaries
  $$
  x=(P+R)/2
  $$
  and
  $$
  x=(L+S)/2
  $$
  where one comparison may remain pending but the overlapping safe-region branch must finite terminate;
- one-sided grid extreme / infinity outer-neighbor cases;
- repeated calls may reuse source / grid-search progress, but result choice need not be canonical when several legal near-nearest points exist;
- `Binary64Grid()` result is always a finite Python `float`, canonical zero is `+0.0`, and result is never NaN / `±inf`;
- targets far above/below finite binary64 range still finite return and satisfy the exact near-nearest oracle, with no exact-class `float()` `OverflowError` policy.

Instrumentation additionally verifies:

- implementation does **not** call Theorem-5 / `grid_localize()` as a prerequisite;
- midpoint probes use the shared computable-real embedding / affine path;
- no exact-midpoint equality test is required for termination;
- no whole-grid exhaustive enumeration is used as the generic strategy.

---

# 26. Theorem-4 no-midpoint strict-nearest regression tests

Theorem 4 likewise has no separate v1 public method. Test the internal promised search on targets satisfying

$$
x\notin M_G.
$$

Required fixtures:

- adjacent finite bracket with target on each strict side of the midpoint;
- exact grid hit;
- Theorem-1 near-adjacent bracket containing one interior point $q$, with targets in each of the three strict Voronoi regions determined by $(L+q)/2$ and $(q+R)/2$;
- one-sided infinity endpoint cases;
- exact midpoint promise violation: the relevant branch may remain pending / non-emitting, but must never choose one tied endpoint as “strict nearest” by tolerance;
- exact oracle verifies
  $$
  |g-x|<|h-x|
  $$
  for every other grid point in a provably sufficient finite region.

This suite specifically guards the theorem pair: Theorem 3 relaxes optimality unconditionally; Theorem 4 restores strict-nearest optimality only after the midpoint obstruction is excluded.

---

# 27. Theorem-5 `grid_localize()` mixed-optimal tests

For all three v1 standard grids test output

```text
(bound, approx)
```

and verify:

- not both `None`;
- bound exists -> exact adjacency + enclosure;
- approx exists -> strict nearest-grid-point inequality;
- `approx.point` is finite; for `Binary64Grid()`, `±inf` may appear only as a bound endpoint and the public endpoint is Python float infinity;
- for targets above `sys.float_info.max` or below its negative, any strict-nearest channel still returns the finite extreme binary64 value; infinity is never a nearest-point winner under the extended-distance convention;
- direction `-2,-1,0,1,2,None` semantics are correct;
- strict nearest property uses an exact oracle, never float distance tolerance.

The central theorem-5 obstruction-complementarity regression must explicitly cover:

1. **ordinary off-grid, non-midpoint target**: both optimal searches are in their promised domains; either channel may win the fair race;
2. **exact grid hit $x\in G$**: optimal adjacent-bracket search may stall on equality, but strict-nearest search must finite resolve because $G_{\mathrm{fin}}\cap M_G=\varnothing$;
3. **exact adjacent midpoint $x\in M_G$**: strict-nearest search may stall / has no strict winner, but adjacent-bracket search must finite resolve because midpoint is not a grid point;
4. verify independently that every generated adjacent midpoint lies strictly between its endpoints and therefore is not a grid point;
5. scheduler fairness: neither optimal search may starve the other;
6. shared refinement / comparator state may be reused across the two channels, but one channel's pending boundary must not be interpreted as negative evidence for the other.

This is the key test of the intuitive theorem structure: Theorem 5 keeps optimality and unconditional termination by relaxing only the fixed output shape.

---

# 28. Partial-domain ordinary API tests

## Division

Unknown semantic denominator：

```python
x / y
```

-> finite `UnresolvedDomainError`。

Known zero -> `ZeroDivisionError`。

Known nonzero -> finite node construction。

Complex division 使用 rectangle-origin exclusion / zero evidence 的同一 pattern。

---

# 29. Partial-operation process tests

```python
divide_process(x, y)
```

驗：

- construction finite；
- finite work finite；
- denominator mathematically nonzero -> eventually resolve $x/y$；
- denominator mathematically zero + finite zero evidence -> terminal `ZeroDivisionError`；
- denominator mathematically zero but lacking zero/equality evidence -> may remain `Pending` indefinitely；
- `divide_process(1, y)` covers reciprocal semantics；
- public API contains no separate reciprocal-process spelling；
- no `Resolved(Undefined)` surrogate。

# 30. Python protocol safety

For `ComputableReal`：

```text
== != < <= > >=
bool
hash
float
int
round
floor
ceil
```

不得啟動 potentially infinite semantic resolution。

For `ComputableComplex` 同理。

Instrumentation 確認 dunder 不呼叫 `.resolve()`。`bool(x)` / `bool(z)` 必 `TypeError`，不得因 object truthiness 默認成 `True`。`repr()` / `str()` 亦必 finite 且不得推進 unbounded semantic process。

---

# 31. Exact-source structural introspection and DAG scope tests

`ComputableReal.exact_source()` / `ComputableComplex.exact_source()` 必 finite：

- exact leaf returns the canonical exact payload permitted by `02`；
- general native / derived semantic node returns `None` unless a semantics-preserving exact replacement has already been finitely installed；
- calling `exact_source()` performs zero semantic source advancement and never starts equality / algebraicity search；
- safe exact compaction may change a later `exact_source()` result from `None` to an exact payload without changing denotation。


```python
a = Algebraic(...)
b = a + a
```

不得建立 general ComputableReal DAG。

```python
x = ComputableReal.from_comparator_source(source)
y = x + a
```

才建立 exact leaf / derived node。

Embedding `x` into `ComputableComplex` must create `RealEmbeddingComplexNode` (or equivalent), **not** `ExactComplexLeaf(payload=x)`。`ComputableComplex.from_parts(x, y)` uses a dedicated two-coordinate derived node and preserves both child dependencies。

---

# 31A. Regime recognition / downgrade / upgrade tests

For exact classes：

- `GaussianRational(a, 0).downgrade()` -> `Rational(a)`；non-real Gaussian remains `GaussianRational`；
- algebraic rational -> `Rational`；non-real Gaussian-rational algebraic -> `GaussianRational`；other algebraic -> `Algebraic`；
- `Algebraic.try_as(Rational)` / `try_as(GaussianRational)` terminate on both success and failure fixtures；
- a `try_as(T)` pair without registered guaranteed-finite recognition finite `TypeError` rather than starting semantic search。

For general semantic classes：

- without constructive lower evidence, `downgrade()` performs no semantic advancement and returns the current lowest recoverable regime；
- after exact-floor / recoverable-floor commit, `downgrade()` returns the lowest finitely recoverable representation；
- `upgrade(U)` first observes the same downgrade result, then performs a legal finite lift；
- for every legal fixture, `upgrade(U).downgrade()` is mathematically equal to the pre-upgrade `downgrade()` result and returns the same lowest recoverable regime；
- illegal target regime finite `TypeError`；for example a known non-real value cannot upgrade to `ComputableReal`；
- ordinary promotion instrumentation confirms it calls only guaranteed-finite downgrade logic and never starts `downgrade_process()`。

---

# 32. DAG weak interning

建立兩次 identical structural expression：

```python
u = x + y
v = x + y
```

在 live cache條件下要求：

```python
u is v
```

或依公開 factory invariant等價檢驗。

刪除所有 strong refs + GC 後 weak table 不得永久 retain node。

Native-source identity tests：

- two native source instances without declared immutable construction key must **not** merge even if test oracle says same denotation；
- sources declaring same safe construction key may merge and must then share progress/knowledge consistently；
- source progress mutation never changes structural key。

---

# 33. Structural key independence from knowledge

同一 node 在取得額外 enclosure / sign fact 前後：

$$
\operatorname{structKey}_{\mathrm{before}}
=
\operatorname{structKey}_{\mathrm{after}}.
$$

Knowledge mutation不得破壞 intern-table identity。

---

# 34. Coefficient collection

$$
x+x+x\to3x,
$$

$$
2x-\frac52x\to-\frac12x.
$$

Identification 只依 structural identity。

建立兩個 semantic-equal-but-structurally-different fixtures，確認 normalization 不呼叫 equality process合併它們。

Product normalization only fuses non-negative occurrence/exponents by default。Fixture with reciprocal / negative exponent and unknown nonzero fact must **not** be algebraically cancelled；only certified-nonzero advanced rewrite may do so。

---

# 35. Graph flattening / depth

至少 $10^5$ terms 的 repeated sum / product。

要求：

- construction completes；
- no Python recursion-limit failure；
- graph不形成同深 binary execution chain；
- iterative evaluation works。

---

# 36. Long-chain construction benchmark

防止 flattened map每次全 copy 的 hidden $O(n^2)$。

Measure construction sizes：

```text
10^3
10^4
10^5
```

檢查 empirical scaling；若超線性顯著，需 profile / justify。

---

# 37. Query-local memo vs persistent knowledge

Diamond DAG：同一 external query 中 shared subexpression expensive evaluation once。

Second query：

- query-local assembly artifacts可消失；
- persistent certified facts仍存在；
- native source progress仍可 reuse。

---

# 38. Derived persistent knowledge tests

對 derived node：

```python
z = x * x
```

若 runtime有限證得 $z\ge0$ 或 tighter enclosure，應優先把可幾何化資訊吸收進 persistent enclosure；第二個 unrelated query 必能由 retained enclosure / residual knowledge 重用該結果。

這驗證 derived node 的 certified knowledge 確實能跨 query 持久重用，而不要求每個 theorem consequence 都有獨立 Boolean cache。

---

# 39. Demand-driven obligation and inactive-branch tests

Construct graphs containing many reachable-by-object but query-irrelevant branches and instrument native sources。Required：

- graph construction performs no semantic source advancement；
- querying one target advances only native sources needed for that target；
- a sibling branch not required by the target remains untouched；
- if existing persistent knowledge already satisfies target resolution, query performs no additional source work；
- conservative child obligations may over-refine, but no whole-graph uniform-precision sweep is allowed；
- newly certified upstream facts are reusable by later sibling queries。

Benchmark large graphs with native-frontier sizes 1, 4, 16, 256 while holding derived-node count fixed。Record cost as a function of **active** native frontier, not just total object count。

---

# 40. Memory scaling

Profile：

- node structural storage；
- weak intern table；
- persistent knowledge bytes；
- source progress；
- query-local peak；
- post-query retained memory。

因 derived nodes 現在允許 persistent knowledge，「heavy cache 只能隨 native count growth」不作為 invariant；要求：

> retained knowledge growth 必能由實際已取得的 reusable certified information 解釋，且 compaction 可避免保存被完全支配的歷史 facts。

---

## Safe-forgetting tests

- exact Rational subtree may be replaced by exact Rational leaf without changing any future exact observation；
- exact Gaussian subtree may be replaced by `GaussianRational` leaf；
- algebraic subtree may be replaced by an exact `Algebraic` value when that value has actually been finitely constructed；
- replacing a general computable subtree by its current finite interval / rectangle alone is forbidden；
- optional compiled-source compaction must pass arbitrary increasing-resolution equivalence tests against the original graph；
- provenance summary compaction must not erase active trust dependencies。

---

# 41. One-shot workload benchmark

大量 expressions each queried once。

測：

- persistent-knowledge policy 是否造成不合理 retained memory；
- weak interning overhead；
- structural normalization overhead。

---

# 42. Repeated-query benchmark

Fixed graph，多次 increasing resolution / different certified observations or localizations / semantic attempts。

確認：

- prior certified work reusable；
- no unnecessary source restart；
- stronger knowledge不使 downstream work退化成重頭計算。

---

# 43. ComputableComplex tests

- `ComputableComplex.from_parts(real, imag)` uses guaranteed-finite real-coordinate bridge；a general `ComputableComplex` becomes acceptable as a coordinate only after persistent `ComputableReal` membership evidence is committed；construction never starts hidden membership work；
- certified box；
- coordinatewise `grid_bound` / `grid_localize` / `grid_project` through real/imag views；
- `z.membership_process(ComputableReal)`：non-real strict case eventually `False`；zero-certified imaginary coordinate -> `True`；real but uncertified zero-imag boundary may remain `Pending`；resolution commits reusable membership fact；
- `z.membership_process(Rational/GaussianRational/Algebraic)` uses sound registered evidence and may remain `Pending` where membership is not decidable；
- `z.relation_process(w, Relation.EQUAL/NOT_EQUAL)` follows coordinate equality semantics；equal boundary may remain `Pending` without both coordinate zero evidence；clear inequality eventually resolves；
- ordered `Relation` values on general complex finite `TypeError`；
- `component_compare_process` returns two independent coordinate processes；one pending equality coordinate must not block the other；
- relation / component processes accept all scalar regimes and registered finite Python numeric bridge through finite promotion；
- direction observable accepts every registered finite exact $\mathbb Q(i)$-valued direction；zero finite `ValueError`, finitely classifiable non-$\mathbb Q(i)$ finite `TypeError`；
- `z.assume_relation(w, Relation.NOT_EQUAL)` returns only after coordinate geometry separates；`EQUAL` preserves necessary residual equality knowledge；
- `z.assume_membership(ComputableReal, truth)` follows trust-boundary domain semantics；
- `z.downgrade()` / `z.downgrade_process()` / `z.upgrade(...)` preserve recoverable-floor contracts；
- arbitrary Algebraic exact leaf without eager coordinate split；
- general ComputableReal complex embedding is a dedicated embedding node, not an exact leaf。

---

# 44. No-float correctness audit

Static / code-review gate：以下不得用 machine float arithmetic / tolerance 作 correctness decision。Exact interoperability decoding（例如 binary64 bit-pattern inspection、`float.as_integer_ratio()`、finite/infinity/NaN classification）是允許的，因為它只是有限格式解碼，不是 approximate numerical evidence。

以下尤其不得用 machine float 作 correctness decision：

- Rational arithmetic；
- polynomial algorithms；
- algebraic root count / isolation；
- minimal polynomial / root index；
- certificate verification；
- semantic comparison；
- grid theorem validation，包括 finite-point embedding、midpoint construction與 near-nearest projection；
- bounds verification。

---

# 45. Threading scope test

不測無鎖 shared graph 的 thread-safety correctness，因其不在 contract。

但 docs/tests 必確認：

- thread-safety 明確標為 unsupported；
- 不宣稱 operations atomic。

---

# 46. Regression gate

Release candidate 必跑：

```text
Rational correctness + benchmarks
GaussianRational exact arithmetic / hash / rectangle probes
Polynomial exactness
Algebraic representation/refinement/equality/hash
DecisionProcess finite-work + fairness
Knowledge provenance/relation-membership-grid assertions/geometry absorption/residual semantics/recoverable-floor consistency/compaction
Comparator-source + comparator-to-bound adapter
Built-in computably embedded exact ordered grid realization + searchability + global bounding
Derived target-grid comparison + arbitrary finite-pair midpoint construction
Theorem-1 near-adjacent grid behavior
Theorem-2 off-grid adjacent-enclosure promised regression
Theorem-3 near-nearest `grid_project` + overlapping-safe-region midpoint boundaries
Theorem-4 no-midpoint strict-nearest promised regression
Theorem-5 mixed-optimal localization + disjoint-obstruction / fairness cases
Regime recognition/downgrade/downgrade-process/upgrade + partial-operation ordinary/process semantics
Real/complex DAG scope + weak interning
Structural normalization + construction scaling
Persistent derived knowledge
Memory scaling
Python protocol safety including bool/rich-comparison/hash boundaries
No-float audit
```

只看 test 數量或最後 decimal output 不足以通過 release gate。
