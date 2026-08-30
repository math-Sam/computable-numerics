# Computable：Public Semantic Specification

本文件固定 `Computable` 的 public numerical semantics。Implementation 不得因效能方便、Python 慣例、cache policy 或內部資料結構而修改以下契約。

---

# 1. Public numeric classes

系統固定提供：

```python
Rational
GaussianRational
Algebraic
ComputableReal
ComputableComplex
```

其 mathematical domains 分別為：

$$
\mathbb Q,
\qquad
\mathbb Q(i),
\qquad
\overline{\mathbb Q},
\qquad
\mathbb R_C,
\qquad
\mathbb C_C.
$$

其中

$$
\mathbb Q(i)=\{a+bi:a,b\in\mathbb Q\}.
$$

---

# 2. Global invariants

## INV-1 — Denotation immutability

`GaussianRational`、`Algebraic`、`ComputableReal`、`ComputableComplex` 一旦建立，其 mathematical denotation 永遠不變。

`Rational` 是唯一例外：mutable working `Rational` 允許 in-place value mutation；一旦 frozen / interned 即不可再改值。

## INV-2 — Semantic immutability allows representational interior mutability

Denotation immutable 不等於所有 Python attributes 永久 bitwise 不變。

只要 mathematical value 不變，下列 internal state 可 lazy 改善：

- `Algebraic` defining polynomial；
- `Algebraic` isolating rectangle；
- `Algebraic` minimal-polynomial / root-index / hash cache；
- `ComputableReal` / `ComputableComplex` certified knowledge；
- source progress；
- process-local continuation state。

## INV-3 — Potential divergence is explicit

對 `ComputableReal` / `ComputableComplex`：

$$
\boxed{
\text{任何可能不停止的 semantic computation，都必須在 public API 上明示。}
}
$$

Ordinary Python operator、dunder，以及面向 arbitrary well-formed input 的普通 semantic method，不得內部偷偷執行一個不保證 termination 的 exact semantic computation。

`assume_*` 類 user-assertion method 是明示的 **trust-boundary operation**，不屬於上述 arbitrary-input guarantee：其 assertion truth 是 promised precondition。若 promise 為假，這類 method 可不終止；method name 與 documentation 必明示其 trust semantics。這不允許普通 arithmetic / comparison / projection API 以相同理由隱藏 divergence。

Potentially divergent semantic decision 若不是 trust-boundary promised-input operation，必以：

```python
*_process(...)
```

或：

```python
process.resolve()
```

明示。

## INV-4 — Resolution and work are distinct

`width` 與 grid object 的有限結構參數描述 output quality；`work` 描述 process 最多推進多少 cooperative finite transitions。

不得提供含糊的單一 `budget=` 同時承擔兩種語意。

## INV-5 — Persistent knowledge is monotone

對同一 numeric object 的 persistent knowledge states $K_0,K_1,\ldots$，要求：

$$
K_{n+1}\models K_n.
$$

Implementation 可移除被更強 fact 支配的冗餘 representation，但不得造成 logical information loss。

## INV-6 — Geometry-first persistent knowledge with residual semantics

對 general real / complex semantic objects，persistent knowledge 的主要幾何 carrier 分別是 strongest useful certified interval / rectangle；若 runtime 已持有可有限恢復的較低數值制度 representation，亦可保存 **recoverable floor**。

若某個 semantic fact 已被 enclosure / rectangle / recoverable floor 完整蘊含，例如：

```text
0 < L <= x <= R           -> x > 0 and x != 0
L <= x <= R < 0           -> x < 0 and x != 0
I_x ∩ I_y = ∅             -> x != y
z in rectangle B, 0 ∉ B   -> z != 0
recoverable floor = Rational(3,7)
                           -> rational / Gaussian-rational / algebraic membership
```

則 implementation 不要求永久保留等價的獨立 predicate representation。只有 enclosure、rectangle、recoverable floor 尚不能完整蘊含的 semantic content 才保留為 residual knowledge。

## INV-7 — Trust-user assertion principle

Trust-boundary assertions 固定分成三類：

```python
x.assume_relation(y, relation)
x.assume_membership(numeric_class, truth)
x.assume_grid_membership(grid, truth)
```

`assume_membership(...)` 與 `assume_grid_membership(...)` 的 `truth` 必為 Python `bool`；其他型別 finite raise `TypeError`。`assume_membership(...)` 的 `numeric_class` 必為五個 public numeric classes 之一。

`assume_relation` 對 real-valued operands使用 §3.1.1 的六種 `Relation`；對 complex-valued relation 只接受 `EQUAL` / `NOT_EQUAL`，其餘 finite raise `TypeError`。Assertion truth 是使用者提供的 semantic promise，不要求 runtime 先證明。

若 relation 不含 equality cell，即 `LESS` / `GREATER` / `NOT_EQUAL`，true promise 必在 method 返回前被幾何吸收：real values refine 到 strict ordered separation 或 disjoint intervals；complex `NOT_EQUAL` refine 到至少一個 coordinate rectangles / intervals strict separation。若 relation 含 equality cell，即 `EQUAL` / `LESS_EQUAL` / `GREATER_EQUAL`，runtime 應立即做所有 sound geometric propagation，但一般仍需保留 enclosure 無法取代的 residual relation knowledge。

`assume_membership(numeric_class, truth)` 表示 mathematical denotation 是否屬於該 class 的數值域，而不是 Python `isinstance`。這類 domain fact 一般不能保證完全由有限 enclosure / rectangle 表示，因此可保存 residual membership knowledge；已由 exact/recoverable representation 或 geometry 完整蘊含的部分仍應 compact。Finite domain-inclusion implications 必立即 propagation。

`assume_grid_membership(grid, True)` 對 §9.3 支援的 standard real grids，必利用 promise、local finiteness、searchability 與 target refinement，在返回前有限辨識唯一 exact grid point，並把可恢復的最低 exact representation commit 到 knowledge store。`assume_grid_membership(grid, False)` 必在返回前 refine 到 certified interval 完全落在一個 grid gap 中，使 enclosure 本身蘊含 off-grid fact。

如果 assertion 已與現有 knowledge 形成 finite-detectable contradiction，立即 raise `InconsistentKnowledgeError`。如果 assertion 為假但矛盾尚不能有限辨認，任何依 promise 才保證完成的 absorption / identification 都**不保證 termination**。這被視為使用者違反 trust-boundary precondition，不是數值庫必須以 timeout 或猜測處理的正常使用方式。

## INV-8 — Lazy computation

可有限決定的 property 不代表 constructor 必須 eager 決定。

沒有被當前 operation / API contract 要求的 exact property，不應只因「算得出來」就預先計算。

## INV-9 — Computation DAG scope

預設 computation DAG 只屬於：

```text
ComputableReal
ComputableComplex
```

`Rational` / `GaussianRational` / `Algebraic` 本身不是預設 graph nodes；只有 lift 進一般可計算運算鏈時才作為 exact leaf payload。

## INV-10 — Thread-safety boundary

本規格不保證：

- node knowledge commits；
- weak interning；
- `DecisionProcess` mutation；
- shared source progress；

在無 external synchronization 的多 thread access 下 thread-safe。

---

# 3. Common support types

## 3.1 `Order`

```python
class Order(Enum):
    LESS = -1
    EQUAL = 0
    GREATER = 1
```

Public comparison direction 固定為 receiver compared with argument。

例如：

```python
x.compare_process(y)
```

中：

- `LESS` iff $x<y$；
- `EQUAL` iff $x=y$；
- `GREATER` iff $x>y$。

## 3.1.1 `Relation`

```python
class Relation(Enum):
    LESS = ...
    LESS_EQUAL = ...
    EQUAL = ...
    NOT_EQUAL = ...
    GREATER_EQUAL = ...
    GREATER = ...
```

對 real order trichotomy，六個 relation 分別對應：

```text
LESS          = {Order.LESS}
LESS_EQUAL    = {Order.LESS, Order.EQUAL}
EQUAL         = {Order.EQUAL}
NOT_EQUAL     = {Order.LESS, Order.GREATER}
GREATER_EQUAL = {Order.EQUAL, Order.GREATER}
GREATER       = {Order.GREATER}
```

`Relation` 同時供 `relation_process(...)` 與 `assume_relation(...)` 使用。General complex values 沒有 natural order，所以 complex relation API 只接受 `EQUAL` / `NOT_EQUAL`。

## 3.2 `Pending` / `Resolved[T]`

```python
@dataclass(frozen=True)
class Pending:
    pass

@dataclass(frozen=True)
class Resolved[T]:
    value: T
```

`Pending` 不具有 Boolean false 語意。

```python
bool(Pending())
```

必 raise `TypeError`。

`Pending` 只表示：

> 此 process 的最終問題目前尚未 resolve。

它不表示：

- exceptional outcome 已成立；
- computation 沒有取得額外知識；
- timeout 可當作 negative evidence。

## 3.3 `DecisionProcess[T]`

```python
process.advance(work: ExactIntegerInput = 1) -> Pending | Resolved[T]
process.resolve() -> T
```

### Finite-work contract

一個 work unit 是一個 **cooperative finite state transition**。

每個 transition 本身必 guaranteed finite。

`work` 的 public validation 固定為：

- `work` 使用 §14 guaranteed-finite exact integer-valued numeric recognizer；若 exact integer value $n\ge0$ 即接受並以 $n$ 作 work budget；
- 若 numeric input 可 finite exact 分類但不是整數，raise `TypeError`；若 exact integer value $n<0$，raise `ValueError`；
- `work=0` 不推進 transition，只回報目前 terminal / pending 狀態。

因此對任意 finite valid $N$：

```python
process.advance(work=N)
```

必在最多 $N$ 個 cooperative transitions 內 finite return 或 finite raise；若 process 提前 resolve / fail，立即停止，不必耗盡 budget。Public finite-work surface 只使用 `advance(...)`，避免與無界 `resolve()` 的語意邊界重疊。

### Stateful resumability

`DecisionProcess` 是 mutable resumable object。

```python
p.advance(work=100)
p.advance(work=100)
```

第二次從第一次留下的 continuation 繼續，而不是從頭開始。

一旦 resolved，之後所有 finite-work calls 直接有限回傳同一 result，且不消耗 semantic work。

若 process 在 finite transition 中進入 terminal exception state（例如已證明 division denominator 為零），該 exception 亦視為 terminal：後續 finite-work call 不推進 semantic work，並穩定地再次 raise 同一 mathematical exception class。

### Unbounded resolution

```python
process.resolve()
```

持續推進直到 resolved，明確允許永不返回。

所有 docstring 必清楚標明 `may not terminate`。

## 3.4 Grid localization result types

第一版只固定一維 real grid localization。Public result types conceptually 為：

```python
@dataclass(frozen=True)
class GridBracket[T]:
    lower: T
    upper: T

class GridDirection(Enum):
    STRICT_LEFT = -2       # grid point g < target x
    LEFT_OR_EQUAL = -1    # g <= x
    EQUAL = 0             # g == x
    RIGHT_OR_EQUAL = 1    # g >= x
    STRICT_RIGHT = 2      # g > x

@dataclass(frozen=True)
class GridApproximation[T]:
    point: T
    direction: GridDirection | None

@dataclass(frozen=True)
class GridLocalization[T]:
    bound: GridBracket[T] | None
    approx: GridApproximation[T] | None
```

`GridLocalization` invariant：`bound` 與 `approx` 不得同時為 `None`。

`GridDirection` 描述的是 **grid point `g` 相對於 target `x`** 的關係。`None` 表示 theorem 已經提供 strict-nearest point，但目前不宣告額外方向資訊。

這些資料型別承載 theorem 1 的 `GridBracket` 與 theorem 5 的 mixed `GridLocalization` / strict-nearest channel；theorem 3 `grid_project()` 直接回 grid canonical finite point，不使用額外 wrapper。它們都不代表一般數值 equality 已被決定。

---

# 4. Persistent certified knowledge and provenance

## 4.1 Provenance classes

Persistent facts 可來自：

```text
kernel_verified
trusted_source
user_asserted
derived
```

### Kernel-verified

帶 finite proof object，可由 trusted kernel finite verify。

### Trusted-source

由明確註冊為 trusted 的 native source 依 contract 直接提供。

### User-asserted

使用者明確宣告某 fact 成立。Runtime 不將其偽裝成 proof；後續 exact correctness 對該 object 依賴 assertion 真實性。

`USER_ASSERTED` 不要求永久對應到一個獨立 predicate record。若 assertion 已被 interval / rectangle absorption，provenance 可以附著於 strengthened enclosure、其 provenance summary，或在後續取得不依賴 assertion 的 kernel/trusted-source enclosure 後變成可丟棄的冗餘歷史。

### Derived

由已接受 facts 經固定 sound inference rules 推出。

## 4.2 User assertion API — trusted promises, absorption, and residual knowledge

Public trust-boundary surface：

```python
x.assume_relation(y, relation)
x.assume_membership(numeric_class, truth)
x.assume_grid_membership(grid, truth)   # ComputableReal only
```

### Relation assertions

`assume_relation(y, relation)` 先做 finite contradiction check 與 finite operand promotion。對 `ComputableReal` 可使用全部六種 `Relation`；對 `ComputableComplex` 只接受 `EQUAL` / `NOT_EQUAL`。

對不含 equality cell 的 relation，true promise 足以保證有限 strict separation，因此 method 返回前必完成幾何吸收：

```text
x < y   -> refine until R_x < L_y
x > y   -> refine until R_y < L_x
x != y  -> refine until I_x ∩ I_y = ∅
```

Complex `NOT_EQUAL` 則 refine 到 real 或 imaginary coordinate 之一出現 strict separation。完成後不必另存同義 predicate；`USER_ASSERTED` provenance 可附著於 resulting enclosure / rectangle 或其 summary。

對 `EQUAL` / `LESS_EQUAL` / `GREATER_EQUAL`，assertion 含 equality boundary，不能一般要求 enclosure 最終完全取代 relation。Runtime 仍應做所有 finite sound propagation，例如 `x == y` 可把兩側 enclosure 都 strengthen 到目前可得的交會資訊；剩餘無法由 geometry 蘊含的部分保存為 residual relation knowledge。

### Numeric-domain membership assertions

```python
x.assume_membership(Rational, True)
x.assume_membership(GaussianRational, False)
x.assume_membership(Algebraic, True)
z.assume_membership(ComputableReal, True)
```

這些 assertions 談 mathematical denotation：例如 `assume_membership(Rational, True)` 表示 $\llbracket x\rrbracket\in\mathbb Q$，不表示 object 的 Python class 是 `Rational`，也不自動提供 numerator / denominator reconstruction data。

Domain-membership knowledge 一般作 residual semantic knowledge保存，並沿數值域包含關係做 finite implication propagation。若某 fact 已被 recoverable floor 或其他 persistent representation完整蘊含，則依 §4.4 compact，不重複保存。

### Grid-membership assertions

對 `ComputableReal`：

```python
x.assume_grid_membership(grid, True)
x.assume_grid_membership(grid, False)
```

`grid` 的合法 public domain 與 §9.3 相同。

True branch 是 **identification promise**。Method 必在返回前持續 target refinement / grid search，直到唯一 grid point 被有限辨識。Standard grids 的 finite point 都有 exact computable embedding，因此 identification 後立即 materialize exact point value並 commit recoverable floor：`IntegerGrid` / `BoundedDenominatorGrid` 得到 `Rational`；`Binary64Grid` 的 finite binary64 point exact decode 成 dyadic `Rational`。這不是只保存 `x in G` flag。

False branch 是 **gap promise**。Method 必在返回前 refine 到 certified rational interval $[L,R]$，使

$$
G\cap[L,R]=\varnothing.
$$

因此 off-grid knowledge 被 geometry 完整吸收；後續 theorem-2 adjacent localization可直接重用這份 separation evidence。

### False promises and contradiction handling

對任何 trust assertion，若現有 knowledge 已 finite 證明相反命題，立即 raise `InconsistentKnowledgeError` 且不 commit。若 promise 實際為假但尚無 finite contradiction evidence，依 promise 才能完成的 strict separation / grid identification / gap absorption 可以永久執行；runtime 不 fabricate success、negative result 或 timeout semantics。

## 4.3 Immediate commit from processes

Semantic process 中途只要得到 sound、可持久化的 certified fact，即可立即 commit 到相關 numeric nodes，即使該 process 最後回 `Pending()`。

因此：

$$
\texttt{Pending}
\not\Rightarrow
\text{no additional persistent knowledge}.
$$

## 4.4 Knowledge compaction

Implementation 可做：

- interval / rectangle intersection；
- dominance elimination；
- qualitative-fact absorption into stronger enclosure；
- equivalent-fact merge；
- provenance summary；
- redundant proof-object / certificate garbage collection；

但 compaction 後的 knowledge 必至少蘊含 compaction 前全部 persistent semantics relative to the same trust assumptions。

特別地，`PositiveCertificate`、`NonZeroCertificate` 等可只是 inference / transport 時的 transient object；一旦 strongest persistent enclosure 已經蘊含該 fact，就不要求 node 長期保存 certificate 本體或同名 Boolean flag。

---

# 5. Certificates

核心 certificate categories 至少包含：

```text
ZeroCertificate
NonZeroCertificate
PositiveCertificate
NonNegativeCertificate
NegativeCertificate
RealCertificate
IntervalCertificate
RectangleCertificate
```

Certificate 不得由：

- timeout；
- float tolerance；
- sampling；
- 「目前沒有找到反例」；

產生。

User assertion 可以作為 explicit trust assumption，但不得偽裝成 kernel proof。由 assertion 直接取得的 enclosure strengthening 必保留相應 trust provenance；若 assertion 只負責保證某 refinement search 的 promised termination，而最後得到的 enclosure 本身由 independent certified source 驗證，則該 enclosure 可具有更強、與 assertion 分離的 provenance。

對 certificate-seeking semantic APIs，每個 method 的 termination guarantee 必個別寫清楚，不得用一句「命題若為真就一定 resolve」概括所有 boundary cases。

特別是 non-strict predicate 如 $x\ge0$，在 $x=0$ 但沒有 equality / zero certificate 時，可以永久 pending。

---

# 6. `Rational`

## 6.1 Mathematical domain

`Rational` 嚴格只表示：

$$
\mathbb Q.
$$

不包含：

- $+\infty$；
- $-\infty$；
- NaN。

若 enclosure / grid mathematics 需要 infinity endpoint，該 endpoint 必使用 **non-`Rational`** representation；例如 v1 `Binary64Grid` 的 public infinity endpoints 明確使用 Python `float('-inf')` / `float('inf')`。這不改變 `Rational` 僅表示 $\mathbb Q$ 的 domain。

## 6.2 Construction, accepted input, and representation lifecycle

### 6.2.1 Public constructor input

`Rational` 的 public constructor 必 finite 接受下列 forms：

```python
Rational(value)
Rational(numerator, denominator)
```

v1 將 constructor input 以遞迴型別 `RationalInput` 描述：

```text
RationalInput :=
      finite-rational numeric value
    | str
    | tuple[RationalInput, RationalInput]

finite-rational numeric value :=
      Rational
    | int / bool
    | fractions.Fraction
    | finite float
    | finite complex with exact-zero imaginary coordinate
    | real GaussianRational
    | rational-valued Algebraic
```

其中 tuple 必恰有兩個 elements；它表示「前者除以後者」，而兩個 elements 再依同一規則遞迴解析。這是 constructor boundary 的 compositional syntax，不代表 tuple 會被 ordinary numeric operators 隱式視為數字。

定義有限 exact parser `parse_rational_input` 的 denotation 規則如下。

- `Rational`：取相同 mathematical value；constructor 不得為了 conversion 改變 input object 的 lifecycle state。若 input 已是 live canonical frozen object，可直接回該 object；若 input 是 mutable working object，讀取其 exact numerator/denominator value 後另行 lookup / construct canonical result，input 保持原 mutable/frozen state不變。
- `int`：exactly 表示該 integer，即 denominator 為 `1`。依 Python numeric convention，`bool` 是 `int` subclass，因此 `False` 與 `True` 在 numeric input position 分別 exact 解析為 $0$ 與 $1$；canonical Rational storage 不保留 `bool` object。
- `fractions.Fraction`：exactly 取其 `numerator` / `denominator`；不得經 `float`。
- finite `float`：exactly 表示該 **binary64 value 本身**，使用 `float.as_integer_ratio()` 或語意等價的 exact conversion。特別地，`Rational(0.1)` 一般不等於 `Rational("0.1")`；前者是 Python binary64 `0.1` 的精確 dyadic rational，後者是十進位字串所表示的 $1/10$。`-0.0` canonicalize 為 rational zero。
- finite `complex`：coordinatewise exact decode 兩個 binary64 components；只有 imaginary coordinate exact 為 zero 時才屬於 $\mathbb Q$ 並接受，其 real coordinate 依 finite-float 規則轉成 Rational。Nonzero imaginary coordinate finite raise `TypeError`；任一 component 為 non-finite 則 finite raise `ValueError`。
- `GaussianRational`：finite exact 檢查 imaginary coordinate；只有 real value 接受並取其 Rational real coordinate，non-real value finite raise `TypeError`。
- `Algebraic`：呼叫其 guaranteed-finite exact `try_as(Rational)` recognizer；成功時取該 Rational value，否則 finite raise `TypeError`。這不允許對 general `ComputableReal` / `ComputableComplex` 做 hidden rationality search。
- `str`：依下述 exact decimal/rational grammar parse，不得先轉成 machine `float`。
- `tuple[u, v]`：先遞迴取得 $p=\operatorname{parse}(u)$ 與 $q=\operatorname{parse}(v)$，再取 exact quotient $p/q$；若 $q=0$，finite raise `ZeroDivisionError`。Tuple 長度不是 `2` 則 finite raise `TypeError`。

Two-argument form `Rational(numerator, denominator)` 與 tuple form 使用**同一個遞迴規則**：先分別令

$$
p=\operatorname{parse}(\texttt{numerator}),
\qquad
q=\operatorname{parse}(\texttt{denominator}),
$$

再令 constructor denotation 為 $p/q$。因此例如：

```python
Rational((1, 2))                  # 1/2
Rational((1, 2), (3, 4))          # (1/2)/(3/4) = 2/3
Rational("1/2", Fraction(3, 4))  # (1/2)/(3/4) = 2/3
```

皆屬 v1 contract。任一遞迴層級的 divisor 解析成 rational zero 時都 finite raise `ZeroDivisionError`。

Non-finite float (`+inf`, `-inf`, `nan`) 不屬於 $\mathbb Q$，在任何遞迴層級遇到時 constructor 必 finite raise `ValueError`。Unsupported type raise `TypeError`。

### 6.2.2 Exact string grammar

先移除整個字串首尾 whitespace；內部 whitespace 除了 `/` 兩側可有 whitespace 外皆不接受。Case-sensitive / case-insensitive special tokens 如 `inf`, `infinity`, `nan` 均不屬合法 Rational string。

一個 decimal scalar 的 grammar 概念上為：

```text
sign? mantissa exponent?

sign      := "+" | "-"
mantissa  := DIGITS
           | DIGITS "." DIGITS?
           | "." DIGITS
exponent  := ("e" | "E") sign? DIGITS
```

其中 `DIGITS` 至少含一個十進位 digit。其 denotation 由有限十進位展開與十的整數次方 exact 定義。例如：

```text
"12"       -> 12
"-3.25"    -> -13/4
".5"       -> 1/2
"1."       -> 1
"2.5e-3"   -> 1/400
```

此外允許恰好一個 `/`：

```text
scalar "/" scalar
```

其 denotation 為左 scalar 除以右 scalar；右 scalar 若為 zero，raise `ZeroDivisionError`。因此 `"1.5 / 0.5"` 合法且表示 `3`。多個 `/`、空 scalar、malformed exponent、非 grammar 字元等 finite raise `ValueError`。

這個 string parser 的目的只是 exact Rational I/O；它不是 symbolic expression parser。

### 6.2.3 Representation lifecycle

至少保存下列 internal working fields：

```text
_numerator: int
_denominator: int
_is_simplified: bool
_is_frozen: bool
_hash: int | None
```

永遠要求：

$$
\_denominator>0.
$$

Public `.numerator` / `.denominator` **不是 raw fields**，而是 `@property` canonical-value views。Private `._numerator` / `._denominator` 可在 mutable working state 中保持 unreduced；它們不屬 v1 compatibility contract，也不得作為 public writable state。進階／除錯文件可說明如何唯讀觀察這兩個 private fields，但依賴其具體 unreduced pair 的程式是 representation-sensitive。

v1 固定下列 lifecycle；`Rational` 只表示有限有理數，因此不存在 denominator-zero special-value branch：

```text
public constructor / canonical constant
        -> frozen + interned Rational

copy.copy(r) / r.__copy__()
        -> distinct mutable working Rational

ordinary + - * /
        -> fresh mutable working Rational

in-place += -= *= /=
        -> mutable receiver: mutate same object
        -> frozen receiver: leave original untouched and return fresh mutable result

hash(r)
        -> normalize as needed + freeze this same object + stable hash

r.intern()
        -> normalize current value and return frozen canonical object
        -> cache miss: current object may become the canonical frozen object
        -> cache hit: return existing canonical object; current receiver need not freeze
```

Working Rational 可 unreduced、mutable；`simplify() -> None` 是 v1 public guaranteed-finite lifecycle operation，只做原地 sign/gcd canonical reduction，不 freeze mutable receiver、不做 interning。Frozen Rational 已 canonical，因此 `simplify()` 對 frozen receiver finite no-op。單一 object 的 state 只允許：

$$
\text{mutable}\longrightarrow\text{frozen},
$$

不存在 in-place unfreeze。若需要 frozen value 的 mutable equivalent，使用 `copy.copy(r)`（其語意等價於 `r.__copy__()`）。

Frozen Rational 必：

$$
\gcd(|n|,d)=1,
$$

sign canonical、value immutable、stable hash。這裡的「stable hash」只表示同一 Python execution 中，物件 frozen 後 hash 不因內部 cache 的後續變動而改變；不承諾跨 process / 跨 Python version 的 serialized hash stability。

Public constructor 與 canonical constants 回 frozen/interned value；這讓一般使用者拿到的 Rational 預設安全。Mutable working objects 主要由 `copy.copy`、普通 arithmetic results 或 private bulk workspace 產生。

### 6.2.4 Public canonical numerator / denominator properties

v1 保留 `.numerator` / `.denominator` 作為 public read/write properties，但兩者是 **canonical-value properties**，不是 raw working fields。

Getter contract 等價於：

```python
@property
def numerator(self) -> int:
    self.simplify()
    return self._numerator

@property
def denominator(self) -> int:
    self.simplify()
    return self._denominator
```

因此讀取任一 property 都 finite；若 receiver 是 mutable unreduced working value，讀取會先原地 gcd/sign canonicalize，但不 freeze、不 intern。Frozen receiver 本來已 canonical，因此 property read 是 finite no-op + field read。

所以對同一 mathematical Rational，public

```python
(r.numerator, r.denominator)
```

具有唯一語意，與 arithmetic kernel 暫時留下何種 unreduced `(_numerator, _denominator)` 無關。

Setter 仍是 **value-level setter**。右側接受完整 `RationalInput`，但不得把 `Rational` object 或其他非-`int` object 直接存進 private integer fields。為固定 exception precedence 與 transactional behavior，setter 依下列順序工作：

1. 若 receiver frozen，finite raise `ValueError`，不解析 RHS、不修改 receiver；
2. 將 RHS finite exact parse 到暫存 Rational value；
3. `denominator` setter 若暫存值為 rational zero，finite raise `ZeroDivisionError`，receiver 完全不變；
4. 呼叫 `self.simplify()`，取得 assignment 前 mathematical value 的 canonical integer pair
   $$
   \frac nd,\qquad d>0,
   $$
   但 receiver 仍保持 mutable；
5. 根據下列 value-level semantics 重寫 `._numerator` / `._denominator`，恢復 positive-denominator invariant、清除既存 hash cache，並同步 `_is_simplified`。

若

$$
\operatorname{parse}(u)=\frac pq,
\qquad q>0,
$$

則

```python
r.numerator = u
```

把 receiver 的 mathematical value 改成

$$
\boxed{
\frac{p/q}{d}=\frac{p}{qd}
}.
$$

Implementation 可直接令 raw working fields 為 `(p, q*d)`（再做必要 sign normalization），因此 assignment 後仍可是 unreduced working representation。

同理，若

$$
\operatorname{parse}(v)=\frac pq\ne0,
\qquad q>0,
$$

則

```python
r.denominator = v
```

把 receiver 的 mathematical value改成

$$
\boxed{
\frac{n}{d(p/q)}=\frac{nq}{dp}
}.
$$

若 $p<0$，implementation 必把 sign 移到 numerator，使 `._denominator > 0`；結果仍可暫時 unreduced。

例如 mutable receiver 的 raw fields 即使暫時是 `(4,4)`，public read：

```python
r.numerator
r.denominator
```

會先 canonicalize 成 `(1,1)`。之後

```python
r.numerator = 2
```

必得到 mathematical value $2$，而不能因某 implementation 原先留下 `(4,4)` 而得到 $1/2$。

Private `._numerator` / `._denominator` 的**唯讀觀察**可在進階／除錯使用說明中介紹，用來查看 lazy working representation；但它們不是 compatibility-stable public API。直接寫 `r._numerator = ...` / `r._denominator = ...` 不受支援，可能破壞 invariants，v1 不為其結果提供任何語意保證。

## 6.3 `intern()`

```python
canonical = r.intern()
```

固定 contract 是：**return value** 必為與 `r` 等值的 normalized、frozen、hash-stable、weak-interned canonical `Rational`。

Reference-style flow：

1. 先在 current receiver 上 finite sign normalization / gcd reduction，取得 canonical integer ratio；
2. 查 weak intern table；
3. 若已有 live canonical object，直接回該 object；receiver 本身不要求 freeze，可以保持 mutable（但已 simplified）；
4. 若 cache miss，計算 stable hash、freeze current receiver、register，並回 current receiver。

因此 `intern()` 和 `hash()` 有意不同：`hash(r)` 必 freeze **this object**；`r.intern()` 只保證**回傳的 canonical object** frozen，cache hit 時可以是另一個 object。

Equal live canonical rationals 應共享 canonical identity while live。Persistent owner 必使用 `r = r.intern()` 的回傳值，而不能假設呼叫後原 receiver 一定 frozen。

## 6.4 Ownership rule

任何其他 numeric object 或 persistent structure 若要保存 `Rational` reference，必須先取得 frozen interned value。

禁止 `Algebraic`、DAG node、certificate、persistent interval 等持有之後還可改值的 Rational。

## 6.5 Python protocol

核心 exact operations total finite：

```text
+ - * /
integer powers
== != < <= > >=
bool
int
floor
ceil
round
float
complex
```

Integer-power exponent 使用 §14 的 guaranteed-finite exact integer-valued numeric recognizer，而不是 nominal Python type test。若 exponent 的 mathematical value 可 finite exact 認出為整數 $n$，則對 $n\ge0$，`r ** exponent` finite exact；對 $n<0$，先 finite 判斷 $r=0$，若為零 raise `ZeroDivisionError`，否則 finite exact reciprocal power。採 Python/field convention $r^0=1$，包括 $0^0=1$。可 finite exact 辨認但不是整數的 numeric exponent finite `TypeError`；沒有 guaranteed-finite integer recognizer 的 numeric classes（例如 general `ComputableReal` / `ComputableComplex`）不進此 coercion path。

除以零 raise `ZeroDivisionError`。`bool(r)` 是 finite exact zero-test：只在 $r=0$ 時為 `False`，其餘為 `True`。`complex(r)` finite correctly-round real coordinate 並令 imaginary coordinate 為 binary64 zero；只作 projection，不參與 correctness。

`Rational` 始終提供 total finite 的 `hash(r)`。Hash 必遵守 Python numeric equal-hash contract，不只對本套 exact classes，也包括 v1 明確支援 exact numeric coercion 的 built-ins / stdlib types：若 finite `int` / `fractions.Fraction` / finite `float` / finite `complex` 與 `r` 依 exact conversion semantics 比較相等，則 hash 必相等；finite `complex` 只有在 imaginary coordinate 為 exact zero 時才可能與 Rational 相等。特別地：

```python
hash(Rational(1, 2)) == hash(0.5)
hash(Rational(1)) == hash(1)
hash(Rational(1, 3)) == hash(Fraction(1, 3))
hash(Rational(1)) == hash(True)
hash(Rational(0)) == hash(False)
hash(Rational(1)) == hash(complex(1, 0))
```

這個要求應由 integer/rational exact hash algorithm 實現；不能先把一般 Rational 轉成 machine float。

若 `r` 尚為 mutable，第一次 `hash(r)` 必有限地：

1. normalize sign；
2. gcd reduction；
3. compute stable value hash；
4. freeze 目前物件。

之後該物件不得再原地改值，且重複 `hash(r)` 必回相同結果。

`hash()` 與 `intern()` 的角色不同：`hash()` 保留目前 Python object identity，只保證其 value representation 與 hash 進入 stable frozen state；`intern()` 則回傳 weak cache 中的等值 canonical object；cache miss 時可 freeze/register receiver，cache hit 時 receiver 本身不必 freeze。

因此把 mutable Rational 直接放入 `dict` / `set` 是合法的；容器呼叫 `hash()` 時會使它凍結。若某 persistent numeric structure 的 contract 要求 canonical object sharing，仍必顯式使用 `r = r.intern()`。

Integer / rounding protocol 固定為：`int(r)` 向 $0$ 截斷；`floor` / `ceil` 回 exact Python `int`；`round(r)` 回 nearest integer 並採 half-to-even；`round(r, ndigits)` 的 `ndigits` 使用 §14 guaranteed-finite exact integer-valued numeric recognizer；其 mathematical value只要可 finite exact 認出為整數 $n$ 即接受，並回 exact `Rational`，表示 decimal-place half-to-even rounding 的結果。這些 operation 全部只用 integer/rational arithmetic。

`float()` 必用 exact rational-to-binary64 rounding logic，不以 intermediate machine float 參與 correctness。Exact classes 的 Python machine projection 採 **Python exact-number conversion family**（`int` / `fractions.Fraction`）的 overflow policy，而不是 IEEE arithmetic overflow policy。令

$$
T_{64}:=2^{1024}-2^{970}.
$$

對任意 finite real exact value $x$，若 $|x|<T_{64}$，則 `float(x)` 回其 correctly-rounded **finite** binary64 value；若 $|x|\ge T_{64}$，包括剛好位於最大 finite binary64 與 ideal value $2^{1024}$ 的 ties-to-even overflow boundary $|x|=T_{64}$，finite raise Python built-in `OverflowError`。負值完全對稱。Underflow 到 binary64 zero 只是正常 finite rounding，不是 error。

因此 `complex(r)` 亦只在 real coordinate 的 finite binary64 projection 成功時回 machine complex；若 real coordinate 達 overflow boundary 或更大，finite raise `OverflowError`。Exact-class machine projection不以 `±inf` 表示 overflow。

---

# 7. `GaussianRational`

## 7.1 Mathematical domain

$$
\mathbb Q(i)=\{a+bi:a,b\in\mathbb Q\}.
$$

`GaussianRational` 是 finite exact complex field，也是 canonical complex-plane probe domain。

## 7.2 Representation

Canonical semantic payload：

```python
(real: Rational, imag: Rational)
```

Persistent object 中兩個 coordinates 必為 normalized、frozen、interned `Rational`。Public object 的 denotation immutable；coordinate pair 不做 working-value mutation。Hash cache 等不影響 denotation 的 interior state 可 lazy 維護。

Public constructor 固定有三個 dispatch shapes：

```python
GaussianRational()
GaussianRational(value)
GaussianRational(real, imag)
```

Zero-argument construction denotes $0+0i$. One-argument construction is a finite exact **value construction**. Existing `GaussianRational` preserves the same denotation; finite Python `complex` is decoded coordinatewise exactly and lifted to $\mathbb Q(i)$; an `Algebraic` is accepted exactly when the guaranteed-finite `try_as(GaussianRational)` recognizer returns a value, otherwise finite raises `TypeError`; and any `RationalInput` (§6.2.1), including exact `str` / recursive tuple ratio syntax, is parsed as a real coordinate with imaginary coordinate $0$. Thus `GaussianRational((1,2))` denotes $1/2+0i$, whereas `GaussianRational(complex(1,2))` denotes $1+2i$. General `ComputableReal` / `ComputableComplex` never trigger hidden Gaussian-rationality resolution.

Two-argument construction is reserved for coordinate construction: `real` and `imag` each accept `RationalInput` and are parsed by the same recursive exact Rational parser. Before persistent ownership both coordinates are normalized, frozen, and interned. Any parse/downcast failure is finite and follows the source recognizer/parser contract; a finite Python `complex` with any non-finite component raises `ValueError`. Constructor parsing syntax remains explicit and does not by itself expand ordinary operator coercion.

Rational closed rectangle 固定表示為：

```python
((a, b), (c, d))
```

其中 $a,b,c,d$ 皆為 `Rational`，第一個 pair 是 real range，第二個 pair 是 imaginary range。Rectangle corners 與 center 自然都是 `GaussianRational`。

## 7.3 Exact arithmetic

若 $z=a+bi$、$w=c+di$，則 `+ - * /`、integer powers、conjugation 全部 finite exact；division 在 $w=0$ 時有限 raise `ZeroDivisionError`。Integer-power exponent 使用 §14 guaranteed-finite exact integer-valued numeric recognizer；若 exact integer value為負，zero base finite `ZeroDivisionError`，其餘 finite exact；固定 $z^0=1$，包括 $0^0=1$。可 finite exact 辨認但不是整數的 numeric exponent finite `TypeError`；general computable classes不啟動 hidden integerhood resolution。

```python
z.real_part() -> Rational
z.imag_part() -> Rational
z.is_real() -> bool
bool(z) -> bool
```

皆 finite total；`bool(z)` iff $z\ne0$，只需 finite exact 檢查兩個 Rational coordinates 是否同時為 zero。

## 7.4 Equality, ordering, and hash

Equality / inequality finite total。Ordering 只在兩 operands 都 real 時存在；non-real ordering raise `TypeError`。

`hash(z)` finite total。若 `imag == 0`，必使用與等值 `Rational` 相容的 hash。若 `imag != 0`，使用 canonical Gaussian-rational value hash；若存在與 `z` exact-equal 的 finite Python `complex`，hash 亦必與該 Python `complex` 相等。任何等值 `Algebraic` 在 hash 時必落到同一 cross-type hash tier。

所有 hashable exact numeric classes 必遵守 Python rule：

$$
x==y\Longrightarrow hash(x)=hash(y).
$$

這裡的 hash stability 只要求同一 Python execution 內穩定，不承諾跨 process serialization。

## 7.5 Integer conversion and rounding

`GaussianRational` 的 integer / rounding Python protocols 只在 `imag == 0` 時定義；non-real input 一律 finite raise `TypeError`。Real case 完全委派給 exact `Rational` coordinate semantics：

```python
int(z)              # truncation toward zero -> int
math.floor(z)       # -> int
math.ceil(z)        # -> int
round(z)            # nearest integer, ties-to-even -> int
round(z, ndigits)   # ndigits: finitely exact-recognizable integer-valued numeric scalar -> Rational
```

其中 `round(z, ndigits)` 的結果是 $10^{-\texttt{ndigits}}$ 的整數倍（`ndigits < 0` 時等價解讀），並以 exact half-to-even rule 決定；整個 operation finite exact，不經 machine floating arithmetic。

## 7.6 Projection

`float(z)` 僅在 `imag == 0` 時定義；否則 finite raise `TypeError`。Real case使用 §6.5 的 exact-number binary64 projection policy：correctly-rounded result 必為 finite Python `float`，若 $|\operatorname{Re}z|\ge T_{64}$ 則 finite raise `OverflowError`。

`complex(z)` 對兩個 Rational coordinates分別使用同一 projection policy；只有兩個 coordinates 都成功投影為 finite binary64 時才回 Python `complex`。任一 coordinate 達 overflow boundary或更大即 finite raise `OverflowError`。Machine complex 只作 terminal projection，不作 correctness substrate；exact-class projection不以 `±inf` 表示 overflow。

## 7.7 Probe role

`GaussianRational` 可作：

- rational rectangle corner / center；
- binary-rational / bounded-denominator product-grid point；
- exact polynomial evaluation point；
- algebraic root-isolation boundary probe；
- `ComputableComplex` localization / directional probe parameter；
- `ExactComplexLeaf` payload。

---


## 7.8 `Polynomial` coefficient convention

v1 public integer-polynomial kernel uses the immutable constructor:

```python
Polynomial(coefficients: tuple[ExactIntegerInput, ...])
```

Coefficient order is **constant-first**. Thus

$$
\operatorname{Polynomial}((a_0,a_1,\ldots,a_n))
$$

denotes

$$
a_0+a_1X+\cdots+a_nX^n.
$$

For example:

```python
Polynomial((2, -3, 1))
```

denotes $2-3X+X^2$. All polynomial algorithms, serialization, structural keys, derivative formulas, Horner evaluation, and `Algebraic(polynomial, box)` construction use this same coefficient orientation. v1 does not permit an implementation to reinterpret the same tuple in leading-coefficient-first order.

Construction is canonical: `coefficients` must be a tuple whose entries are numeric values accepted by the §14 guaranteed-finite exact integer-valued recognizer. Each coefficient is accepted exactly when its mathematical value is an integer $n$, then canonical storage stores the ordinary Python `int` $n$. Thus `bool`, integral `Fraction`, integral finite `float`, real-integral finite `complex`, integral `Rational`, real-integral `GaussianRational`, and integer-valued `Algebraic` coefficients are all equivalent inputs; a finitely classifiable non-integral/non-real numeric coefficient finite raises `TypeError`. `str` / recursive tuple ratio syntax are not coefficient values. Constructor canonicalization is **value-preserving only**: it removes trailing high-degree zero coefficients, but must not divide out content, make the polynomial primitive, or change an overall sign. Thus `Polynomial((2, 2))` denotes and remains $2+2X$; `primitive_part()` is a separate exact operation.

The unique canonical zero polynomial is

```python
Polynomial((0,))
```

so `Polynomial((0, 0, 0)) == Polynomial((0,))` and `Polynomial((1, 2, 0, 0)) == Polynomial((1, 2))`. Polynomial equality is finite total on every operand class for which v1 specifies polynomial equality. Between two `Polynomial` objects it is determined by the canonical coefficient tuple.

For a **constant** polynomial `Polynomial((n,))`, v1 exposes the canonical integer embedding not only against Python `int`, but against every scalar representation whose equality with the integer $n$ is guaranteed finite and exact. Thus the following are all equal exactly when the scalar denotes the same integer $n$:

```text
Python int / bool
fractions.Fraction
finite float
finite complex
Rational
GaussianRational
Algebraic
```

The check is value-based and finite: `Fraction` must have denominator $1$; a finite `float` is decoded exactly (equivalently through `as_integer_ratio()`) and must denote the integer $n$; a finite Python `complex` is decoded exactly coordinatewise and must have zero imaginary coordinate with integral real coordinate; a `Rational` must have denominator $1$; a `GaussianRational` must have zero imaginary coordinate and integral real coordinate; an `Algebraic` uses its finite exact rational recognizer and must downcast to the integer $n$. Non-real or non-integral exact scalars compare unequal. `str` and recursive tuple `RationalInput` remain explicit-constructor syntax and are never parsed by polynomial equality. General `ComputableReal` / `ComputableComplex` are **not** added to this finite equality bridge; comparison with them continues to follow the semantic-class rich-comparison rule rather than hidden resolution.

Consequently, examples such as

```python
Polynomial((1,)) == True
Polynomial((1,)) == 1.0
Polynomial((1,)) == complex(1, 0)
Polynomial((1,)) == Fraction(1, 1)
Polynomial((1,)) == Rational(1)
Polynomial((1,)) == GaussianRational(1, 0)
Polynomial((1,)) == Algebraic(1)
```

are all `True`, including reflected operand order, whereas `Polynomial((1,)) == Rational(3, 2)` and every comparison of a nonconstant polynomial with these scalar values are `False`.

Hashing obeys the same cross-type value contract. Every constant polynomial has the same hash as its corresponding Python integer value; by the already-required Python/exact-class equal-hash contracts, this is also the hash of every equal `Fraction`, finite `float`, finite `complex`, `Rational`, `GaussianRational`, or `Algebraic` value. Nonconstant polynomial hashes are computed from a type-separated canonical coefficient key. For runtime convenience, v1 fixes

$$
\deg 0=-1,
$$

so `.degree` always returns an `int`; `.leading_coefficient` returns `0` for the zero polynomial. The value `-1` is a runtime sentinel convention, not a claim about the conventional abstract-algebra definition of the zero polynomial's degree.

## 7.9 Public value protocol and arithmetic

`Polynomial` is a v1 **public exact value type**, not merely an internal Algebraic kernel. In addition to the constructor, v1 fixes the following finite public observations:

```python
p.coefficients -> tuple[int, ...]
p.degree -> int
p.leading_coefficient -> int
bool(p) -> bool
```

`.coefficients` returns the canonical constant-first tuple. `bool(p)` is `False` exactly for `Polynomial((0,))` and is otherwise `True`.

Unary `+` / `-` and binary `+ - *` are finite exact. Scalar arithmetic uses a finite **integer-scalar recognizer** rather than checking only the operand's source type. For an operand from the guaranteed-finite exact scalar bridge

```text
Python int / bool
fractions.Fraction
finite float
finite complex
Rational
GaussianRational
Algebraic
```

the runtime first decodes / downcasts it exactly, then accepts the operation iff its mathematical value is an integer $n$. The accepted value is embedded as the constant polynomial `Polynomial((n,))`. Thus `p + 1.0`, `p + Rational(1)`, `p + GaussianRational(1,0)`, `p + Algebraic(1)`, and `p + complex(1,0)` are valid and remain in $\mathbb Z[X]$; `p + 0.5`, `p + Rational(3,2)`, `p + GaussianRational(1,1)`, `p + Algebraic(\sqrt{2})`, and `p + complex(1,2)` are finitely rejected because their exact values are not integers. Such recognized-but-nonintegral scalar operands produce a finite public `TypeError` rather than silently changing the coefficient domain. General `ComputableReal` / `ComputableComplex` do not enter this recognizer because integerhood is not guaranteed finitely decidable there. `str` / recursive tuple `RationalInput` remain constructor parsing syntax and are not numeric arithmetic operands.

```python
+p
-p
p + q
p - q
p * q
p ** n
```

`p ** exponent` uses the §14 guaranteed-finite exact integer-valued numeric recognizer. If the exact integer value is $n\ge0$, the power is finite exact; if $n<0$, finite raise `ValueError`. A finitely classifiable numeric value that is not an integer finite raises `TypeError`. `p ** 0 == Polynomial((1,))`, including for the zero polynomial.

Derivative is public:

```python
p.derivative(order=1) -> Polynomial
```

`order` uses the §14 guaranteed-finite exact integer-valued numeric recognizer. Exact integer value $n\ge0$ is accepted; $n<0$ finite raises `ValueError`; a finitely classifiable numeric value that is not an integer finite raises `TypeError`. `order=0` returns `p`; sufficiently high order returns the canonical zero polynomial.

For exact public evaluation v1 provides:

```python
p.evaluate(x)
p(x)                  # exact alias of evaluate
```

where `x` may be any v1 scalar numeric operand accepted by the ordinary numeric conversion/promotion registry: Python `int` (including `bool` as `0/1`), `fractions.Fraction`, finite `float`, finite `complex`, or one of `Rational`, `GaussianRational`, `Algebraic`, `ComputableReal`, `ComputableComplex`. `Fraction` / finite `float` first enter through exact Rational coercion, while finite Python `complex` enters through the exact coordinatewise `GaussianRational` lift; `str` and recursive tuple `RationalInput` remain explicit-constructor syntax and are not parsed here. Evaluation uses constant-first Horner arithmetic and returns the normal promoted scalar regime. For general computable inputs this is still a guaranteed-finite **construction** of the expression DAG; it does not attempt semantic equality or boundary resolution. Machine floating arithmetic is never correctness evidence.

## 7.10 Content, primitive part, division, and gcd

Content is normalized to be non-negative:

```python
p.content() -> int
```

For

$$
p=a_0+a_1X+\cdots+a_nX^n,
$$

$$
\operatorname{content}(p)=\gcd(|a_0|,\ldots,|a_n|),
$$

with `Polynomial((0,)).content() == 0`.

```python
p.primitive_part() -> Polynomial
```

returns `p / content(p)` for nonzero `p`, using the positive content above, and returns the canonical zero polynomial for zero. Therefore primitive-part extraction **preserves the overall sign**; it does not force positive leading coefficient.

Pseudo-division uses the frozen result type:

```python
@dataclass(frozen=True)
class PseudoDivisionResult:
    scale: int
    quotient: Polynomial
    remainder: Polynomial
```

```python
A.pseudo_divmod(B) -> PseudoDivisionResult
```

`B` may be a `Polynomial` or any scalar accepted by the §7.9 finite integer-scalar recognizer; an accepted integer scalar $n$ is treated as `Polynomial((n,))`. A recognized non-integral/non-real scalar finite raises `TypeError`. The resulting divisor must be nonzero, otherwise finite raises `ZeroDivisionError`. Let

$$
m=\max(\deg A-\deg B+1,0),
\qquad
s=|\operatorname{lc}(B)|^m.
$$

The returned result is the unique triple satisfying

$$
sA=BQ+R,
$$

with `scale == s`, `quotient == Q`, and either `R == 0` or

$$
\deg R<\deg B.
$$

Using the positive scale $|\operatorname{lc}(B)|^m$ rather than a sign-sensitive scale makes this public result canonical; it is equivalent to ordinary pseudo-division up to the corresponding unit sign.

Exact integer-polynomial division is:

```python
A.exact_div(B) -> Polynomial
```

`B` uses the same polynomial-or-integral-scalar coercion as `pseudo_divmod`. It finite raises `TypeError` for a recognized scalar outside the integer subdomain and `ZeroDivisionError` for zero divisor. If no $Q\in\mathbb Z[X]$ satisfies $A=BQ$, it finite raises `ValueError`; otherwise it returns that unique exact quotient. v1 does not assign `//`, `%`, or `/` a second polynomial-division meaning.

```python
A.gcd(B) -> Polynomial
```

`B` likewise accepts a `Polynomial` or finitely recognized integer scalar. It returns the canonical gcd in $\mathbb Z[X]$: it includes the gcd of integer contents and chooses the associate with positive leading coefficient. Thus `gcd(0,0) == 0`; for nonzero `p`, `p.gcd(0)` is `p` up to the unique sign making the leading coefficient positive. The result divides both inputs in $\mathbb Z[X]$ and is finite exact.

## 7.11 Square-free decomposition and irreducible factorization

Public factor payloads are explicit frozen values:

```python
@dataclass(frozen=True)
class PolynomialFactor:
    factor: Polynomial
    multiplicity: int

@dataclass(frozen=True)
class PolynomialFactorization:
    unit: int
    content: int
    factors: tuple[PolynomialFactor, ...]
```

For every nonzero polynomial, `unit` is `+1` or `-1`, `content` is a positive Python `int`, each `factor` is nonconstant, primitive, and has positive leading coefficient, and each multiplicity is a positive Python `int`. Every returned object must reconstruct exactly:

$$
p=\operatorname{unit}\cdot\operatorname{content}
  \prod_j f_j^{m_j}.
$$

For a nonzero constant polynomial, `factors == ()`, `content == abs(constant)`, and `unit == sign(constant)`. The zero polynomial has no finite factorization in this convention, so both methods below finite raise `ValueError` on zero.

```python
p.square_free_decomposition() -> PolynomialFactorization
```

returns the canonical square-free decomposition: every returned factor is square-free; distinct returned factors are pairwise coprime; factors having the same multiplicity are combined, so multiplicities in the result are distinct. Entries are ordered by increasing multiplicity.

```python
p.factor() -> PolynomialFactorization
```

returns factorization into primitive irreducible factors over $\mathbb Z[X]$ (equivalently over $\mathbb Q[X]$ by Gauss's lemma). Equal irreducible factors are combined into one `PolynomialFactor`; entries are deterministically sorted by `(factor.degree, factor.coefficients)`.

## 7.12 Resultant and Sturm sequence

```python
p.resultant(q) -> int
```

is the exact integer resultant. `q` may be a `Polynomial` or a scalar accepted by the finite integer-scalar recognizer, in which case an integer value $n$ is interpreted as the constant polynomial `Polynomial((n,))`; a recognized non-integral/non-real scalar finite raises `TypeError`. Other unsupported operand types also finite raise `TypeError`. Because the zero polynomial has no ordinary finite degree, v1 defines this public method only for nonzero inputs; if either input is zero it finite raises `ValueError`. Nonzero constants follow the standard resultant convention, including

$$
\operatorname{Res}(c,q)=c^{\deg q},
\qquad
\operatorname{Res}(p,c)=c^{\deg p},
$$

and the resultant of two nonzero constants is `1`.

```python
p.sturm_sequence() -> tuple[Polynomial, ...]
```

is defined for nonzero `p`; zero finite raises `ValueError`. The public result is the following **canonical integer-scaled Sturm sequence**. First form the ordinary exact Sturm chain in $\mathbb Q[X]$:

$$
S_0=p,\qquad S_1=p',\qquad
S_{k+1}=-\operatorname{rem}_{\mathbb Q[X]}(S_{k-1},S_k),
$$

stopping immediately before the first zero remainder. (For a nonzero constant polynomial the chain is just $(p)$.) Then, independently for each nonzero $S_k$, multiply by the unique **positive** rational scalar that turns it into a primitive integer polynomial. The positive scalar preserves the sign of $S_k$, so the returned tuple is uniquely determined and has the same Sturm sign-variation semantics as the rational chain.

Implementations may internally use subresultant/Sturm-Habicht machinery or another exact integer algorithm, but the **public returned tuple must equal this canonicalized chain**, not merely an arbitrary sign-variation-equivalent sequence.

## 7.13 Exact real and complex root queries

For root-query APIs, v1 uses the public exact shapes

```python
RationalInterval = tuple[Rational, Rational]
RationalRectangle = tuple[RationalInterval, RationalInterval]
```

Constructor-boundary endpoints may be supplied as `RationalInput`; persistent returned endpoints are canonical frozen/interned `Rational` values. An interval requires `lower <= upper`; a rectangle requires ordered real and imaginary endpoint pairs. Malformed container/type shape finite raises `TypeError`; valid endpoint types with reversed ordering finite raise `ValueError`.

All root counts in this section count **distinct roots**, not algebraic multiplicity. The zero polynomial has infinitely many roots, so every root-count / root-isolation method below finite raises `ValueError` on zero. A nonzero constant polynomial returns count `0` and empty isolation tuples.

```python
p.real_root_count(interval: tuple[RationalInput, RationalInput] | None = None) -> int
```

With `interval=None`, returns the number of distinct real roots in all of $\mathbb R$. With an interval, counts distinct roots in the **closed** interval, including endpoint roots.

```python
p.isolate_real_roots(
    interval: tuple[RationalInput, RationalInput] | None = None,
) -> tuple[RationalInterval, ...]
```

returns pairwise disjoint closed rational intervals, sorted from left to right, each containing exactly one distinct real root and collectively containing exactly the roots requested by the optional closed input interval. Degenerate `[q,q]` intervals are permitted for exactly rational roots. When an input interval is supplied, every returned interval is contained in it, including boundary-root cases.

```python
p.complex_root_count(
    box: tuple[tuple[RationalInput, RationalInput],
               tuple[RationalInput, RationalInput]],
) -> int
```

returns the exact number of distinct complex roots in the **closed** rational rectangle, including roots on edges or corners.

```python
p.isolate_complex_roots(
    box: tuple[tuple[RationalInput, RationalInput],
               tuple[RationalInput, RationalInput]] | None = None,
) -> tuple[RationalRectangle, ...]
```

returns pairwise disjoint closed rational rectangles, each containing exactly one distinct complex root. With `box=None`, the rectangles cover all distinct complex roots of `p`; with a box, they cover exactly the distinct roots in that closed box and every returned rectangle is contained in the input box. Roots on the input boundary remain included. Output order is deterministic lexicographic order by

```text
(real_lower, imag_lower, real_upper, imag_upper)
```

using exact Rational ordering.

These APIs are all guaranteed finite for integer polynomials. Their implementation may use square-free decomposition, exact resultants/subresultants, Sturm/Sturm-Habicht sequences, rational rectangle boundary tests, and certified subdivision; machine floating arithmetic or tolerance is never correctness evidence.

# 8. `Algebraic`

## 8.1 Mathematical domain

$$
\overline{\mathbb Q}.
$$

不設 real / complex public subclasses。

## 8.2 Semantic identity and working representation

一個 `Algebraic` 的 mathematical denotation $\alpha$ immutable。

其當前 working representation 至少由：

$$
(P,B)
$$

共同指定，其中：

$$
P\in\mathbb Z[X],
\qquad
\deg P\ge1,
$$

以及有理閉矩形：

$$
B=[a,b]\times[c,d],
\qquad
a,b,c,d\in\mathbb Q,
\qquad
a\le b,
\qquad
c\le d.
$$

核心 invariant：$B$ 中恰好包含 $P$ 的**一個不同複根**，即唯一指定 denotation $\alpha$。

允許：

- $\alpha$ 位於 $B$ 的 boundary；
- $c<0<d$；
- 實根使用非退化 complex rectangle；
- $P$ 非 minimal；
- $P$ 可 reducible；
- $P$ 可含 repeated factors，只要 unique distinct-root condition 正確處理。

Constructor 不要求 eager 把 $P$ 化成 minimal polynomial。

### 8.2.1 Public constructor overloads

v1 固定兩種且僅兩種 positional constructor forms：

```python
Algebraic(value)
Algebraic(polynomial, box)
```

單參數 `value` 是 finite exact scalar embedding boundary，採 §14 mathematical-value-first 原則。它接受：

```text
Algebraic
GaussianRational
finite Python complex
RationalInput
```

`Algebraic` input 直接保留相同 denotation，不因 copy-like construction 強迫 minimal-polynomial / isolator canonicalization；finite Python `complex` 先 coordinatewise exact lift 成 `GaussianRational`；`GaussianRational` 直接走 $\mathbb Q(i)$ finite embedding；`RationalInput` 依 §6.2 的遞迴 exact parser 轉成 canonical `Rational` 再嵌入。因而例如：

```python
Algebraic(2)
Algebraic("1/3")
Algebraic((1, 3))
Algebraic(complex(1, 2))
Algebraic(GaussianRational(1, 2))
Algebraic(existing_algebraic)
```

皆屬 v1 public contract。含 non-finite component 的 Python `complex` finite `ValueError`；general `ComputableReal` / `ComputableComplex` 不因某個 instance 可能 algebraic 就 hidden resolve。其他 unsupported one-argument type finite raise `TypeError`；任何 nested `RationalInput` parsing error 依 §6.2 原樣 finite propagate。

Two-argument form `Algebraic(polynomial, box)` **唯一**解讀成 polynomial + isolating-box root representation，不與 Rational two-argument ratio syntax 混用。`polynomial` 必為 v1 `Polynomial` object，且 degree 至少 `1`；`box` 採 public `RationalRectangle=((a,b),(c,d))` shape，四個 endpoints 可各自提供 `RationalInput`，constructor 先有限 exact parse 並 intern 成 canonical `Rational` endpoints，再驗證 endpoint ordering 與 unique-distinct-root invariant。Unsupported `polynomial` type、box container shape / arity 不合法 finite raise `TypeError`；合法型別下若 polynomial degree $<1$、endpoint order 不合法、或 box 未唯一選取一個 distinct root，finite raise `ValueError`。Endpoint 自身的 `RationalInput` parsing error 依 §6.2 原樣 propagate。

除上述兩種 arity 外，constructor finite raise `TypeError`。這個 overload 不建立 symbolic-expression parser，也不將 `(polynomial, box)` 單一 tuple 自動視為 root constructor。

### 8.2.2 Finite exact embeddings into `Algebraic`

v1 必提供 finite exact embedding：

```text
Rational -> Algebraic
GaussianRational -> Algebraic
```

`Rational` 可由清分母後的 linear polynomial 與 degenerate rational point box 表示。對

$$
z=a+bi\in\mathbb Q(i),
$$

若 $b=0$，先 canonicalize 為 real `Rational` embedding；若 $b\ne0$，可使用 rational-coefficient polynomial

$$
X^2-2aX+(a^2+b^2),
$$

清分母並 primitive-normalize 成 integer polynomial，再以

$$
[a,a]\times[b,b]
$$

作 rational closed point rectangle，唯一選取 root $a+bi$。這個 embedding 全程 finite exact，不需 general root search。

因此 promotion `Q/G + A -> A` 有明確 finite coercion path。External `int` / `Fraction` / finite `float` 先依 §14 exact lift 成 `Rational`，finite Python `complex` exact lift 成 `GaussianRational`，再嵌入；`str` / recursive tuple ratio只在 explicit `Algebraic(value)` 透過 `RationalInput` parser 時接受，不作 ordinary implicit Algebraic coercion。

## 8.3 Representational interior mutability

下列資料可在不改變 $\alpha$ 的前提下改變：

- $P$ 可換成另一個仍唯一指向 $\alpha$ 的 annihilating polynomial；
- $B$ 可 refine；
- hash 時可將 $P$ lazy 升級成 canonical minimal polynomial。

任何 representation update 都必維持：

$$
(P_t,B_t)\text{ 指向同一個 }\alpha.
$$

## 8.4 Realness

```python
alpha.is_real() -> bool
```

finite total。

但 constructor 不 eager 判定。

Result 可 persistent cache。

## 8.5 Equality and ordering

```python
alpha == beta
alpha != beta
```

finite total mathematical equality。

`< <= > >=`：

1. finite 判斷 operands 是否 real；
2. 任一 non-real -> `TypeError`；
3. 皆 real -> finite exact algebraic order。

`bool(alpha)` 是 finite exact zero-test：利用 algebraic zero decision，僅在 $\alpha=0$ 時為 `False`，否則為 `True`；它不要求 `alpha` 為 real。

## 8.6 Arithmetic

支援：

```python
alpha + beta
alpha - beta
alpha * beta
alpha / beta
alpha ** n
alpha.conjugate() -> Algebraic
alpha.real_part() -> Algebraic
alpha.imag_part() -> Algebraic
```

Field arithmetic、conjugation 與 coordinate extraction 結果仍為 `Algebraic`。

Integer-power exponent 使用 §14 guaranteed-finite exact integer-valued numeric recognizer；negative exact integer exponent 對 zero base finite `ZeroDivisionError`，其餘 finite exact；固定 $\alpha^0=1$，包括 $0^0=1$。可 finite exact 辨認但不是整數的 numeric exponent finite `TypeError`；general computable classes不啟動 hidden integerhood resolution。

Division 可 finite exact 判斷 denominator zero。

## 8.7 Lazy canonical value hash

`Algebraic` 可 hash。

第一次真正需要 canonical value identity 時，允許 finite lazy canonicalization。

Canonical minimal polynomial $M_\alpha$ 固定採 primitive integer polynomial、positive leading coefficient 的唯一 convention。

其不同複根固定以下全序：先比較 modulus，再比較 principal argument。

對 $z\ne0$：

$$
\operatorname{Arg}z\in[0,2\pi).
$$

若 $\alpha,\beta$ 為同一 canonical minimal polynomial 的不同根，則：

$$
\alpha\prec\beta
$$

iff：

1. $|\alpha|<|\beta|$；或
2. $|\alpha|=|\beta|$ 且 $\operatorname{Arg}\alpha<\operatorname{Arg}\beta$。

Root index 為此全序中的 index。

Canonical value identity：

$$
\boxed{
(M_\alpha,\operatorname{rootIndex}(\alpha)).
}
$$

其中「minimal polynomial」指 $\mathbb Q$ 上 irreducible、primitive、positive-leading-coefficient 的 canonical integer polynomial。若 $0$ 是 root，因 modulus 已唯一最小，root ordering 不需要對 $0$ 定義 argument。

**Canonical value identity 與 Python hash key 不必完全相同。** 為滿足 exact cross-class equality 的 Python equal-hash rule，hash 固定採分層策略：

1. 若 $\alpha\in\mathbb Q$，使用等值 `Rational` 的 hash；
2. 否則若 $\alpha\in\mathbb Q(i)$，使用等值 `GaussianRational` 的 hash；
3. 否則使用由 $(M_\alpha,\operatorname{rootIndex}(\alpha))$ 導出的 algebraic hash。

因此 implementation 必具備 finite recognizer 足以在 hash path 判定 $\alpha\in\mathbb Q$ / $\mathbb Q(i)$ 並抽取 coordinates；同一 capability 亦支援 §14.1 已固定為 public 的 `try_as(Rational)` / `try_as(GaussianRational)`。

Hash 可 cache，並可同時把 working polynomial 設為 $M_\alpha$；後續 isolator refinement 或其他 representational cache 調整不得改變 hash。這裡同樣只承諾單一 Python execution 內的 hash stability。

## 8.8 Integer conversion and rounding

`Algebraic` 的 integer / rounding Python protocols 只在 `alpha.is_real()` 為 True 時定義；non-real input 一律 finite raise `TypeError`。因 real algebraic ordering finite exact，以下全部 guaranteed finite：

```python
int(alpha)              # truncation toward zero -> int
math.floor(alpha)       # -> int
math.ceil(alpha)        # -> int
round(alpha)            # nearest integer, ties-to-even -> int
round(alpha, ndigits)   # ndigits: finitely exact-recognizable integer-valued numeric scalar -> Rational
```

`round(alpha, ndigits)` 以 exact algebraic-vs-rational comparisons 判斷相鄰 decimal-grid points 與 midpoint；若恰位於 midpoint，使用 half-to-even rule。結果必為 exact `Rational`，不得先投影成 float 再 rounding。

## 8.9 Projection

若 `is_real()` 為 True：

```python
float(alpha)
```

使用與 §6.5 相同的 Python exact-number projection policy。對 $|\alpha|<T_{64}$ finite correctly round 到 finite binary64；對 $|\alpha|\ge T_{64}$ finite raise `OverflowError`。

若 non-real，`float(alpha)` finite raise `TypeError`，不因 machine projection需求改變 realness contract。

```python
complex(alpha)
```

對 exact real / imaginary coordinates分別做 correctly-rounded binary64 projection；只有兩者皆落在 finite-output range 時回 Python `complex`，任一 coordinate 達 overflow boundary或更大即 finite raise `OverflowError`。Exact-class projection不以 `±inf` 表示 overflow。

---

# 9. `ComputableReal`

## 9.1 Mathematical semantics and native-source entry

一個 `ComputableReal` 表示固定：

$$
x\in\mathbb R_C.
$$

當下 enclosure、source progress、certificates 都只是 knowledge / computation state，不是 value identity。

第一版只要求一種 general native-source entry：**rational-comparator source**。Conceptually：

```python
class RationalComparatorSource(Protocol):
    def compare_rational_process(self, q: Rational) -> DecisionProcess[Order]: ...

ComputableReal.from_comparator_source(source)
```

Source contract 固定存在某一個 $x\in\mathbb R_C$，使對每個 Rational $q$：

- runtime 在 persistent/process ownership boundary 先使用 `q = q.intern()`，source 所見 query 必為 frozen/interned Rational；
- process construction finite；
- 每個 finite work transition finite；
- $x<q$ 時 eventually resolve `LESS`；
- $x>q$ 時 eventually resolve `GREATER`；
- $x=q$ 時可永久 `Pending`，若 source 有 equality evidence 亦可 resolve `EQUAL`。

這是 user-defined source extension 的 **trusted semantic contract**。除上述 eventual-termination 條件外，還要求：

- source lifetime 內存在同一個固定 denotation $x$；source progress / cache mutation 不得改變該 denotation；
- process 若回 `LESS/EQUAL/GREATER`，該 result 必對這個固定 $x$ sound；
- 同一 source 的不同 query / process 不得互相矛盾。

Runtime 不可能一般有限驗證任意 Python source 是否滿足這些 semantic promises。違反 source contract 的 object 不在 correctness guarantee 內。`ComputableReal` 必持有足以保證 source lifetime 的 strong ownership reference，除非 source 已被 semantics-equivalent compiled replacement 安全取代。

Bound-native source adapter、native constants與其他 source kinds 可以日後加入，但不屬 v1 frozen surface。

Exact `Rational`、real `GaussianRational`、real `Algebraic` 仍可經 promotion / exact leaf 有限 lift 成 `ComputableReal`。

## 9.2 Guaranteed-finite enclosure

```python
x.bound(width=epsilon)
```

`width` is a numeric-value parameter. It uses the §14 guaranteed-finite exact rational-valued recognizer and is accepted exactly when its mathematical value is a positive rational

$$
\epsilon\in\mathbb Q_{>0}.
$$

Thus equivalent positive rational values represented by Python `int/bool`, `Fraction`, finite real `float/complex`, `Rational`, real `GaussianRational`, or rational-valued `Algebraic` are interchangeable. Exact zero/negative rational width finite raises `ValueError`; a registered finite numeric value that is non-real or non-rational finite raises `TypeError`. General `ComputableReal` / `ComputableComplex` do not trigger hidden rationality/positivity resolution, and parser-only `str` / tuple ratio syntax is not accepted here.

有限回 frozen/interned Rational endpoints $L,R$，使：

$$
L\le x\le R,
$$

$$
R-L\le\epsilon.
$$

允許 point interval，但不要求辨認 exact rational hit。

## 9.3 Standard real grids

v1 public runtime 固定三種標準 grid。Public grid parameters 都是 immutable value objects；`IntegerGrid()` / `Binary64Grid()` 是 zero-argument constructions，`BoundedDenominatorGrid(max_denominator=N)` 攜帶 denominator parameter。Stateless grid instance 是否 singleton / weak-interned 不屬 public identity contract；相同參數只要求具有相同 grid semantics。形式理論 `06` 將 `G` 的 local finiteness（純數學性質）與 representation capabilities 分開。v1 三種 built-in grid 的 canonical representations 都是 **searchable computably embedded exact ordered grid realizations**：grid-point equality / order finite exact；每個 finite-valued grid point 都能由 terminating algorithm轉成代表同一數值的 computable-real presentation；search operation在 denotationally distinct endpoints 的 promised domain finite terminate。由此 embedding 自動導出 target-vs-grid-point resumable comparison，以及任意兩個 finite grid points midpoint 的 computable-real presentation / comparison，不另把 midpoint probe列成獨立 public capability。 三個 built-in grids 另外都提供對 arbitrary `ComputableReal` target 的 guaranteed-finite global two-sided bounding capability；這是 `grid_project()` 在 adjacent bracket 外側取得 immediate outer neighbors 所需的 standard-grid capability，不由 ordered-grid embedding 本身推出。

### `IntegerGrid()`

$$
G_{\mathbb Z}:=\mathbb Z.
$$

Public grid point 使用 Python `int`。Canonical integer representation 對 extended-real order trichotomy構成 exact ordered grid realization；finite integer point可 finite lift成同值 exact-rational/computable-real presentation，因此滿足 computable-real embedding。

### `BoundedDenominatorGrid(max_denominator=N)`

對 integer $N\ge1$：

$$
G_N
=
\left\{
\frac pq\in\mathbb Q:
1\le q\le N,
\ \gcd(|p|,q)=1
\right\}.
$$

Public grid point 使用 frozen/interned `Rational`；canonical reduced-rational representation 對 grid order trichotomy構成 exact ordered grid realization，且 finite point本身即可 finite lift成同值 computable-real presentation。`N` 使用 §14 guaranteed-finite exact integer-valued numeric recognizer。若 exact integer value $N<1$，finite raise `ValueError`；若 numeric value 可 finite exact 分類但不是整數，finite raise `TypeError`。因此 `True`、`1.0`、`Rational(1)`、`Algebraic(1)` 等都等同 $N=1$，而 `False` 等同 $N=0$ 後因 $N<1$ raise `ValueError`。

這是 v1 的典型 rational grid。`DyadicGrid` 不屬第一版 public/core specification；若有獨立需求，可作 specialization，而一般 theorem 不依賴此 specialization。

### `Binary64Grid()`

令 $F_{64}$ 為 IEEE-754 binary64 的所有 **finite real values**，其中 `+0.0` 與 `-0.0` 在 grid semantic set 中視為同一個 real point $0$，public canonical output 使用 `+0.0`。定義 ordered grid：

$$
G_{64}:=F_{64}\cup\{-\infty,+\infty\}.
$$

因此 `Binary64Grid()` **包含** IEEE-754 的兩個 infinity values，排除所有 NaN。這兩個 infinity 是 extended-real grid elements / boundary values，不表示 `Rational` 或 `ComputableReal` 本身具有 infinity denotation。

加入 $\pm\infty$ 的理由是 global two-sided bounding：finite binary64 set 單獨無法 bracket 超出最大 finite magnitude 的任意 real target。

Canonical binary64 bit-pattern / infinity-sentinel representation 對 grid order trichotomy構成 exact ordered grid realization。Public grid point使用 Python `float`；finite points 的 correctness 以 exact binary64 bit-pattern / integer-ratio semantics 驗證，不能以 machine floating tolerance 作 correctness substrate。每個 finite binary64 point可 finite exact decode成 dyadic Rational並嵌入同值 computable-real presentation；`±inf` 不在 finite-point embedding domain。
`Binary64Grid` 是 **ordered localization/projection grid**，不是 exact-class `float()` / `complex()` protocol。對 general semantic `ComputableReal`，binary64 output information 由 `grid_bound(Binary64Grid())` / `grid_localize(Binary64Grid())` / `grid_project(Binary64Grid())` 提供。`grid_project` 雖回單一 machine-format point，但其 contract 是 theorem-backed **near-nearest**，不是 correctly-rounded或 strict-nearest。依 `06` §63 的 extended-distance convention，$\pm\infty$ 對 finite target 的 distance 為 $+\infty$，所以 theorem-5 strict-nearest channel與 theorem-3 near-nearest projection都永遠不回 infinity。Exact classes 的 Python machine projection另依 §6.5 / §7.6 / §8.9：overflow raise `OverflowError`，不以 infinity 作 exact-class projection結果。

## 9.4 Theorem-1 API — near-adjacent grid bound

第一版所有 public standard grids 都採 searchable computably embedded exact ordered grid realization，並暴露 theorem-backed 的三種一維 observation surface：near-adjacent bound、near-nearest projection、mixed optimal localization。Theorem 1 對應：

```python
x.grid_bound(grid) -> GridBracket
```

`grid` 在 v1 必為三種 built-in grid object 之一；unsupported object finite raise `TypeError`。對合法 built-in grid guaranteed finite，回 $L,R\in G$，使：

$$
L\le x\le R,
$$

且：

$$
\boxed{|G\cap(L,R)|\le1.}
$$

不要求辨認 exact grid hit，也不保證 `(x,x)`。

對 `Binary64Grid()`，`L,R` 可為真正的 Python `float('-inf')` / `float('inf')`，但永不為 NaN。這些 infinity 是 grid endpoint values；它們不表示 target 本身具有 infinite denotation，也不觸發 exact-class projection 的 overflow policy。

## 9.5 Theorem-2 promised strengthening — adjacent enclosure off the grid

`06` Localization Theorem 2 states that if the target additionally satisfies the semantic promise

$$
x\notin G,
$$

then the Theorem-1 near-adjacent bracket can be guaranteed-finitely strengthened to a truly adjacent bracket

$$
L\le x\le R,
\qquad
G\cap(L,R)=\varnothing.
$$

This theorem does **not** add a separate v1 public method. It records the exact mathematical strengthening available when the grid-hit obstruction is excluded. Public unconditional enclosure remains `grid_bound(grid)` with the near-adjacent contract.

## 9.6 Theorem-3 API — near-nearest grid projection

Theorem 3 corresponds to:

```python
x.grid_project(grid)
```

`grid` in v1 must be one of the three built-in grid objects; unsupported objects finite raise `TypeError`. For a valid built-in grid the call is guaranteed finite, and the result is a **finite grid point** $g\in G\cap\mathbb R$. Define

$$
\operatorname{Better}_G(x,g)
:=
\{h\in G\cap\mathbb R:|h-x|<|g-x|\}.
$$

The contract is

$$
\boxed{|\operatorname{Better}_G(x,g)|\le1.}
$$

Thus at most one finite grid point is strictly closer to the target than the returned point. Strict-nearest is a stronger special case; `grid_project()` does **not** promise to identify or select a strict nearest point, and it is not a correctly-rounded machine conversion.

Return type follows the canonical point type of the grid:

```text
IntegerGrid()                  -> int
BoundedDenominatorGrid(N)     -> Rational
Binary64Grid()                -> finite Python float
```

For `Binary64Grid()`, even when $|x|$ is far larger than the largest finite binary64 value, the result is still a finite binary64 point; it never returns `±inf` / NaN and does not use the exact-class `float()` overflow contract. This is semantic grid projection, not Python numeric conversion.

The termination theorem uses immediate outer neighbors of an adjacent bracket to create overlapping near-nearest safe regions. Hence exact midpoint equality need not be decided. The formal contract is `06` Theorem 70.2. If the same target admits multiple legal near-nearest outputs, v1 specifies no extra tie-breaking / canonical-choice rule; an implementation may return any canonical grid point satisfying the invariant, and repeated calls need not select the same mathematical point under every internal progress state.

## 9.7 Theorem-4 promised strengthening — strict nearest away from adjacent midpoints

Let $M_G$ be the set of midpoints of finite adjacent grid pairs as defined in `06` Definition 71.1. Under the additional semantic promise

$$
x\notin M_G,
$$

Localization Theorem 4 guaranteed-finitely strengthens the projection result to a true strict-nearest grid point.

This theorem likewise does **not** add a separate v1 public method. It explains exactly which boundary must be excluded to recover optimal single-point projection. The unconditional public point API remains `grid_project(grid)` with the near-nearest contract.

## 9.8 Theorem-5 API — mixed optimal localization

Theorem 5 corresponds to:

```python
x.grid_localize(grid) -> GridLocalization
```

`grid` in v1 must be one of the three built-in grid objects; unsupported objects finite raise `TypeError`. For a valid built-in grid the call is guaranteed finite. The result contains at least one channel:

### Adjacent bracket channel

If

```text
result.bound = (L, R)
```

then

$$
L\le x\le R,
\qquad
G\cap(L,R)=\varnothing.
$$

### Strict-nearest channel

If

```text
result.approx = (g, direction)
```

then $g$ must be a **finite grid point**, and under the `06` §63 extended-distance convention

$$
|g-x|
<
\inf_{h\in G,\ h\ne g}|h-x|.
$$

`direction` is `GridDirection | None`, with semantics fixed by §3.4.

For `Binary64Grid()`, `±inf` may appear as adjacent bracket endpoints and are represented by Python float infinities; but for every finite target the strict-nearest `approx.point` is always a finite binary64 value and can never be `±inf`.

The conceptual reason for guaranteed termination is the complementarity of the two optimality obstructions. Optimal adjacent-bracket search can stall only on an exact grid hit $x\in G\cap\mathbb R$; strict-nearest projection can stall / fail exactly on the adjacent-midpoint set $M_G$. These sets are disjoint:

$$
\boxed{(G\cap\mathbb R)\cap M_G=\varnothing.}
$$

Therefore the two sound partial searches may be fair-dovetailed, and at least one channel must finite resolve. In this sense Theorem 5 keeps **optimality + unconditional termination** and relaxes only the fixed output shape.

The first-edition grid-observation surface is expressed uniformly through standard grid objects with `grid_bound()` / `grid_project()` / `grid_localize()`; format-specific parallel observation names are outside the public surface.

## 9.9 General comparison and relation processes

完整三分比較：

```python
x.compare_process(y) -> DecisionProcess[Order]
```

其 mathematical domain 是 real-valued operands。Public `y` 採 §14 mathematical-value-first finite promotion：

- `ComputableReal` 直接接受；
- Python `int/bool`、`Fraction`、finite `float`、finite `complex`、`Rational`、`GaussianRational`、`Algebraic` 在可 guaranteed-finite exact 判定為 real-valued 時接受並 finite promote 到 `ComputableReal`；
- finitely known non-real exact numeric value finite raise `TypeError`；
- `ComputableComplex` 只有在 persistent knowledge 已證明其 denotation 屬於 `ComputableReal` domain 時可 finite 取 `real_part()` view；已知 non-real 或尚未 certified real 的 general complex finite raise `TypeError`。`compare_process` 不得 hidden-start `membership_process(ComputableReal)`。

一旦 operand 已 finite 確認落在 real domain，`compare_process` 在 $x<y$ / $x>y$ 時 eventually resolve `LESS` / `GREATER`；若 $x=y$，可永久 `Pending`，除非已有 equality evidence。

特定關係詢問統一為：

```python
x.relation_process(y, relation) -> DecisionProcess[bool]
```

`relation` 為 §3.1.1 的 `Relation`。Operand domain / promotion 與 relation 本身一致：ordered relations `LESS` / `LESS_EQUAL` / `GREATER_EQUAL` / `GREATER` 要求 real-valued operands；`EQUAL` / `NOT_EQUAL` 接受完整 scalar tower，必要時 finite promote receiver 到 complex equality semantics。

Boundary behavior由 `Relation` 對 `Order` cells 的集合語意決定。若 finite evidence 已足以確定最終 order cell 是否屬於 relation，process resolve對應 Boolean；若唯一未決 boundary 是 equality且目前沒有 equality evidence，process 可永久 `Pending`。因此：

- `Relation.NOT_EQUAL` 在值確實不同時 eventually `True`；相等且無 equality evidence時可 `Pending`；
- `Relation.EQUAL` 在值不同時 eventually `False`；相等且無 equality evidence時可 `Pending`；
- strict ordered relations在 strict case eventually resolve；equality boundary依 equality evidence決定是否 finite resolve。

Native comparator source 的 rational-probe method仍是 §9.1 internal source protocol，不形成第二個 public `ComputableReal` comparison spelling；public rational comparison直接使用 `x.compare_process(q)` 或 `x.relation_process(q, relation)`。

## 9.10 Numeric-domain membership process

```python
x.membership_process(numeric_class) -> DecisionProcess[bool]
```

`numeric_class` 必為五個 public numeric classes之一；其他 input finite raise `TypeError`。Process 問的是 denotation 是否屬於該 class 的 mathematical domain，而不是 Python runtime class identity。

Process construction finite；每個 transition finite。Runtime 可使用 persistent membership facts、recoverable floor、exact-class finite recognizers、coordinate separation、registered sound semantic recognition procedures與 derived implications。任何已取得的 sound fact立即 commit。

一般 membership question 不承諾兩側皆半可判定。例如 arbitrary `ComputableReal` 是否 rational / algebraic，或 arbitrary `ComputableComplex` 是否 real，都可能在某些真值與 representation 上永久 `Pending`。若已有足夠 positive 或 negative evidence則 finite resolve。

對 `ComputableComplex`：

```python
z.membership_process(ComputableReal)
```

就是 explicit realness process：若 imaginary coordinate strict nonzero evidence出現，eventually `False`；若 zero/equality evidence成立則 `True`；real 但缺少 zero evidence時可永久 `Pending`。Resolution 必 commit reusable real/non-real membership knowledge。若結果為 `True`，`z.real_part()` 同時構成 guaranteed-finite 可恢復的同值 `ComputableReal` representation，因此可改善 recoverable floor；這與單純的 `assume_membership(Rational, True)` 不同，後者沒有 numerator / denominator reconstruction data。

## 9.11 Trust-boundary assertions

`ComputableReal` 使用 §4.2 的三類 assertions：

```python
x.assume_relation(y, relation)
x.assume_membership(numeric_class, truth)
x.assume_grid_membership(grid, truth)
```

零值與符號關係直接使用同一個 relation surface 表達：

```python
x.assume_relation(0, Relation.EQUAL)
x.assume_relation(0, Relation.NOT_EQUAL)
x.assume_relation(0, Relation.GREATER)
x.assume_relation(0, Relation.GREATER_EQUAL)
```

Absorption、residual knowledge、false-promise 與 contradiction semantics 以 §4.2 為準。

## 9.12 Regime conversion surface

所有 public numeric classes共用 §14.1 的制度轉換語意：

```python
x.try_as(numeric_class)
x.downgrade()
x.downgrade_process()
x.upgrade(numeric_class)
```

其中 ordinary `downgrade()` / `upgrade()` guaranteed finite；`downgrade_process()` 是 explicit potentially divergent semantic search。

## 9.13 Python protocol safety

對 general `ComputableReal`，下列 ordinary Python protocols都不得啟動 semantic resolution：

```text
== != < <= > >=
bool
int float complex
round floor ceil
```

它們在 public use 上 finite raise `TypeError`。

```python
ComputableReal.__hash__ = None
```

`repr()` / `str()` 亦必 finite，且不得為了顯示內容執行 unbounded semantic work。

v1 **不提供** `approx_float`、`approx_decimal`、`floor_process`、`ceil_process`、`round_process`、`correctly_rounded_float_process` 等 correctly-rounded / hard-threshold machine-format projection API。這不包含 §9.6 的 theorem-backed `grid_project()`：後者只有 near-nearest grid contract。若規格納入更強 single-value projection，仍必另行固定 boundary termination semantics。

---

# 10. Partial-operation policy for semantic classes

Ordinary API 絕不隱藏 domain-decision nontermination。

## 10.1 Generic rule

對 ordinary partial operation：

1. required domain fact 已 certified -> finite construct；
2. mathematical invalidity 已 finite known -> raise 對應 mathematical exception；
3. domain 目前 unresolved -> finite raise `UnresolvedDomainError`。

第一版對 general semantic numeric classes 的核心 partial field operation 是 division；倒數以 numerator 為 $1$ 的 division 表達，internal evaluator 可使用 reciprocal primitive。

## 10.2 Division

Ordinary：

```python
x / y
```

若 denominator 的 current persistent knowledge 已足以 certified nonzero（典型是 real interval / complex rectangle 已排除 $0$），finite construct result。

Known zero -> `ZeroDivisionError`。

Unknown -> `UnresolvedDomainError`。

Explicit process：

```python
divide_process(x, y)
```

Process construction finite；finite work finite。若 eventually strict-separate denominator from zero，resolve $x/y$；若取得 zero evidence，raise `ZeroDivisionError`；真正 zero boundary在無 equality evidence時可永久 `Pending`。

倒數不另設 public process spelling；需要 $1/y$ 時使用 `divide_process(1, y)`。Implementation / DAG 仍可使用 reciprocal-specific internal task或 `ReciprocalNode` 作 primitive。

第一版不把 `sqrt_real`、`log` 或其他 elementary partial functions列入 frozen public surface；它們若納入 public surface，沿用同一 termination policy。

---

# 11. `ComputableReal` / `ComputableComplex` computation-node semantics

## 11.1 Default node scope

Only general semantic classes are default graph objects。

```text
ComputableReal   -> RealNode
ComputableComplex -> ComplexNode
```

`Rational` / `GaussianRational` / `Algebraic` standalone objects do not become graph nodes merely by existing。

## 11.2 Exact leaves

When exact values enter semantic graph：

```text
ExactRealLeaf(payload=Rational or real Algebraic)
ExactComplexLeaf(payload=Rational / GaussianRational / Algebraic)
RealEmbeddingComplexNode(child=ComputableReal)
```

Leaf key may require stable value identity of payload. For `Algebraic`, lift into a weak-interned graph leaf may trigger lazy canonical hash / identity computation if needed。

`ComputableReal` **不是 finite exact payload**，因此不得標成 `ExactComplexLeaf`；把 general real semantic value嵌入複平面時使用 structural `RealEmbeddingComplexNode`（imaginary part exactly zero）或語意等價的 dedicated embedding node。

## 11.3 Structural identity

DAG normalization / interning uses finite canonical structural identity, never general semantic numerical equality。

$$
\operatorname{structKey}(u)=\operatorname{structKey}(v)
$$

may imply same construction / denotation, but semantic equality of different structures does not imply structural-key equality。

## 11.4 Weak interning

Structurally identical live real/complex DAG nodes are weak-interned and share object identity + persistent knowledge。

Structural key must not contain mutable knowledge state。

## 11.5 Persistent knowledge on all nodes

Native and derived nodes may both accumulate persistent certified knowledge。

Task-local memo may additionally avoid repeated work within one external query。

---

# 12. `ComputableComplex`

## 12.1 Mathematical semantics and construction

一個 object 表示固定：

$$
z\in\mathbb C_C.
$$

型別不承諾 finite total realness test。

v1 的一般 public construction 可由兩個 real-valued coordinates 建立：

```python
ComputableComplex.from_parts(real, imag)
```

Each coordinate follows a guaranteed-finite exact real-coordinate bridge. An existing `ComputableReal` is accepted directly; Python `int/bool`, `Fraction`, finite `float`, finite Python `complex` with exact-zero imaginary coordinate, `Rational`, real `GaussianRational`, and real `Algebraic` are finitely recognized and lifted to the appropriate exact real leaf. A general `ComputableComplex` is also accepted **only when persistent knowledge already certifies it real**, in which case the bridge uses its finite `real_part()` view; certified-non-real or uncertified general complex input finite raises `TypeError`. The bridge never starts or advances `membership_process(ComputableReal)` implicitly. Parser-only `str` / recursive tuple ratio syntax is not ordinary numeric coordinate coercion.

Its denotation is `real + imag*i` after those finite lifts. Exact `Rational` / `GaussianRational` / `Algebraic` values may also enter the complex regime directly through ordinary promotion / exact leaves.

## 12.2 Guaranteed-finite observation

```python
z.box(width=epsilon)
```

`width` uses the same §9.2 guaranteed-finite positive-rational value recognizer as `ComputableReal.bound(width=...)`. Equivalent finite exact representations of the same positive rational are accepted; zero/negative rational values finite raise `ValueError`, registered non-real/non-rational numeric values finite raise `TypeError`, and general computable values do not trigger hidden rationality search. The method then guaranteed finite 回 rational closed rectangle：

```python
((a, b), (c, d))
```

使：

$$
a\le\operatorname{Re}z\le b,
\qquad
c\le\operatorname{Im}z\le d,
$$

$$
b-a\le\epsilon,
\qquad
d-c\le\epsilon.
$$

四個 endpoints 必 frozen / interned Rational；corners / center 可 materialize 為 `GaussianRational`。

v1 不另設 public two-dimensional grid-localization API。若使用者需要 coordinatewise grid observation，可對 `real_part()` / `imag_part()` 分別呼叫 real `grid_bound()` / `grid_localize()` / `grid_project()`。Product grids 保留作 internal algebraic / geometry probe substrate。

## 12.3 Coordinate views

```python
z.real_part() -> ComputableReal
z.imag_part() -> ComputableReal
```

construction finite，可為 thin graph view nodes。

## 12.4 Membership and relation processes

```python
z.membership_process(numeric_class) -> DecisionProcess[bool]
z.relation_process(w, relation) -> DecisionProcess[bool]
```

`membership_process` 使用 §9.10 的 mathematical-domain semantics。特別地：

```python
z.membership_process(ComputableReal)
```

取代任何 realness-specific public process spelling，並把 resolution commit 成可重用的 real / non-real membership fact。

Complex `relation_process` 只接受：

```text
Relation.EQUAL
Relation.NOT_EQUAL
```

其他 `Relation` finite raise `TypeError`，因 general complex domain沒有 natural order。`w` 接受五個 scalar regimes與 §14 registered finite Python numeric bridge，全部 finite promote到 `ComputableComplex` 後比較。令 $d=z-w$；若至少一個 coordinate取得 strict nonzero evidence，`NOT_EQUAL` eventually `True`、`EQUAL` eventually `False`。若兩 coordinates 都取得 zero/equality evidence，結果反向 resolve；當 $z=w$ 而缺少至少一個 coordinate zero evidence時，兩個 relation processes都可永久 `Pending`。

## 12.5 Directional semantics

不提供 natural `<`。

```python
z.component_compare_process(w)
    -> tuple[DecisionProcess[Order], DecisionProcess[Order]]

z.direction_process(w, direction=u)
    -> DecisionProcess[Order]
```

`component_compare_process(w)` 接受五個 scalar regimes與 §14 registered finite Python numeric bridge，先 finite promote `w` 到 `ComputableComplex`。它回 `(real_process, imag_process)`，兩 coordinate processes彼此獨立；每個 process 的 boundary behavior 與 `ComputableReal.compare_process()` 相同。

`direction` is a numeric-value parameter and uses the §14 guaranteed-finite exact Gaussian-rational-valued recognizer. Any registered finite exact numeric value whose mathematical value lies in $\mathbb Q(i)$ is accepted and canonicalized to `GaussianRational`; a finitely classifiable value outside $\mathbb Q(i)$ finite raises `TypeError`. General computable values and parser-only syntax do not trigger hidden recognition. The recognized direction must satisfy $u\ne0$；zero direction finite raise `ValueError`。Process 比較：

$$
\operatorname{Re}\bigl((z-w)\overline u\bigr)
$$

與 $0$，依 receiver-first convention 回 `LESS/EQUAL/GREATER`。若此 real observable 非零，strict case eventually resolve；若 observable 恰為零但沒有 equality evidence，可永久 `Pending`。

### User-facing best practice for real-domain operations on a possibly-real complex

使用者若持有 general `ComputableComplex z` 而希望把它交給 real `compare_process`，推薦先顯式建立並推進：

```python
realness = z.membership_process(ComputableReal)
```

只有當 process resolve `True`（或 object 已有等價 persistent real-domain certificate）後，再把 `z` 作為 real comparison operand；若 resolve `False` 則它不在 real-order domain；若仍 `Pending`，就保存 / 繼續推進該 process，而不要期待 `compare_process` 替使用者啟動同一個 potentially divergent 判斷。End-user documentation 必明確強調這個 workflow。

## 12.6 Assertions and arithmetic

```python
z.assume_relation(w, relation)
z.assume_membership(numeric_class, truth)
```

Complex relation assertion 只接受 `EQUAL` / `NOT_EQUAL`。`NOT_EQUAL` true promise 在返回前 refine 到至少一個 coordinate 出現 strict separation；`EQUAL` 做可得的 coordinate enclosure propagation並保存必要 residual equality knowledge。Membership assertion 依 §4.2 保存 / propagation mathematical-domain knowledge。

`+ - *` construction finite；`/` certificate-gated，並提供 `divide_process(z, w)`；倒數 process 以 `divide_process(1, z)` 表達。

## 12.7 Python protocol

對 general `ComputableComplex`：

```text
== != < <= > >=
bool
int float complex
round floor ceil
```

全部 finite raise `TypeError`，不得啟動 semantic resolution。

```python
ComputableComplex.__hash__ = None
```

`repr()` / `str()` 必 finite。

v1 不提供 `approx_complex` 或 machine-complex single-value approximation process。

---

# 13. Structural normalization of semantic DAGs

Graph normalization 只處理 `ComputableReal` / `ComputableComplex` dependency graph。

## 13.1 Sum

Repeated associative addition flatten。

可 finite 收集：

- Rational constant；
- structurally identical terms 的 Rational coefficients；
- remaining terms。

例如：

$$
2x+3y-\frac52x+7
\longrightarrow
-\frac12x+3y+7.
$$

## 13.2 Product

Repeated multiplication flatten。

可收集：

- Rational coefficient；
- structurally identical factors 的 **non-negative integer occurrence/exponents**；
- remaining factors。

Negative-exponent fusion 會引入 nonzero domain precondition，不屬於 unconditional structural normalization；只有在所需 nonzero fact 已 certified 且有獨立 rewrite theorem 時，才可作 advanced rewrite。

例如，對 repeated structural occurrences：

$$
x\cdot x\cdot x\cdot y
\longrightarrow
x^3y,
$$

其中右側的 exponent 是 `ProductNode` 內部 canonical occurrence count 的表示，不表示 v1 已提供 general semantic `x ** 3` public operator / `PowerNode`.

## 13.3 Rewrite safety

每條 rewrite 必具備：

1. explicit precondition；
2. exact semantic theorem；
3. finite structural applicability test；
4. property test。

不得為了 simplification 呼叫一般 semantic equality process。

---

# 14. Promotion and conversion

記：

```text
Q = Rational
G = GaussianRational
A = Algebraic
R = ComputableReal
C = ComputableComplex
```

| Left | Right | Arithmetic target |
|---|---|---|
| Q | Q | Q |
| Q | G | G |
| G | Q | G |
| G | G | G |
| Q | A | A |
| A | Q | A |
| G | A | A |
| A | G | A |
| A | A | A |
| Q | R | R |
| R | Q | R |
| G(real) | R | R |
| R | G(real) | R |
| G(non-real) | R | C |
| R | G(non-real) | C |
| A(real) | R | R |
| R | A(real) | R |
| A(non-real) | R | C |
| R | A(non-real) | C |
| Q/G/A | C | C |
| C | Q/G/A | C |
| R | R | R |
| R | C | C |
| C | R | C |
| C | C | C |

`G(real/non-real)` 只需檢查 imaginary Rational 是否為零；`A(real/non-real)` 可 finite 判定，但只在 promotion 真正需要知道時 lazy 呼叫 `is_real()`。

### External Python scalar conversion

Public conversion registry 對 ordinary numeric arithmetic 與 exact-class equality / ordering dispatch 提供下列 guaranteed-finite exact lifts：

```text
int / bool                  -> Rational
fractions.Fraction          -> Rational
finite float                -> Rational
finite complex              -> GaussianRational
```

前三者的 conversion semantics 完全等同 §6.2 的 `Rational(value)`；`bool` 依 Python numeric convention 作為 `int` subclass，`False/True` 分別 exact lift 為 `Rational(0)` / `Rational(1)`。Finite Python `complex` 則以其兩個 binary64 coordinates 的**精確 machine values**分別作 `float.as_integer_ratio()`-equivalent conversion，再 lift 成 `GaussianRational(real, imag)`；`-0.0` coordinates canonicalize 為 rational zero。任一 float/complex component 為 `+inf`、`-inf` 或 `nan` 時不可進 exact conversion registry，finite raise `ValueError`。Machine float / complex arithmetic 本身仍不得作 correctness evidence。

`str` 與 recursive 2-tuple ratio 是 `Rational(...)` 的合法 **explicit constructor syntax**，但不是 ordinary numeric value objects；v1 numeric dunder dispatch 不隱式解析它們。也就是 `Rational("1/3")`、`Rational((1,3))` 有明確 exact semantics，但 `x + "1/3"`、`p + (1,3)` 之類運算不啟動 parser，而遵守 Python `NotImplemented` / final `TypeError` fallback。

### Guaranteed-finite exact subdomain recognition

v1 的 numeric coercion 採 **mathematical-value first** 原則。若來源 object 本身屬 numeric value class，而且 runtime 有 guaranteed-finite exact recognizer 可以判定其 denotation 是否落在某 operation 所要求的 mathematical subdomain，則接受與否由 denotation 決定，不由 nominal source type 決定。

至少固定下列 finite recognizer chain：

```text
finite rational-valued recognizer
    -> Rational | None

finite Gaussian-rational-valued recognizer
    -> GaussianRational | None

finite integer-valued recognizer
    -> int | None

finite nonnegative-integer-valued recognizer
    -> int | None
```

本文以下以 `ExactIntegerInput` 作**語意型別別名**：它不是額外的 runtime class，而是指「可由上述 guaranteed-finite recognizer 成功得到 ordinary Python `int` 的 numeric input」。同理，需非負整數時是在 recognition 後再檢查 $n\ge0$。

v1 core 的 guaranteed-finite input bridge固定為 Python `int/bool`、`fractions.Fraction`、finite `float`、finite `complex`、`Rational`、`GaussianRational`、`Algebraic`。未註冊的第三方 numeric-like types不屬第一版 coercion contract；若提供 explicit extension registry，必另行規範。Rational recognizer要求 complex/Gaussian imaginary part exact zero，並對 `Algebraic` 使用 `try_as(Rational)`；Gaussian-rational recognizer對 `Algebraic` 使用 `try_as(GaussianRational)`；integer recognizer再要求 rational denominator為 `1`；nonnegative recognizer再要求 integer $\ge0$。

`str` 與 recursive tuple ratio 雖可作 explicit Rational constructor syntax，但不是 numeric value objects，因此不進這組 recognizers。General `ComputableReal` / `ComputableComplex` 也不進 generic subdomain recognizer：對它們的 rationality / integerhood / Gaussian-rationality一般無 guaranteed-finite semantic decision，implementation 不得因某個 instance 看似 simple 就 hidden resolve。

這條規則適用於 scalar operands，也適用於 exponent、`ndigits`、derivative order、work budget、bounded-denominator parameter、integer-polynomial coefficients等凡其 semantic contract 本質上要求某數學子域的 numeric positions。若 exact value可 finite recognizer判定在 domain 中，就接受；若可 finite 判定但不在 domain中，依該 API 的 domain error contract finite reject。只有來源不是 numeric value object、或 overload 會造成真正語意歧義時，才以明確 syntax/type boundary 拒絕。

### Exact cross-class relations

對 $Q/G/A$ 任意兩 operands：

- `==` / `!=` finite total mathematical equality；
- `< <= > >=` 先 finite 判斷兩 denotations 是否 real，若任一 non-real raise `TypeError`，否則 finite exact order；
- 若 equality 為 True，hash 必相同，依 §7.4 / §8.7 的 cross-type hash tiers 實作。

只要 comparison 的任一側是 general `ComputableReal` / `ComputableComplex`，user-level rich comparison 都遵守 semantic-class protocol：finite `TypeError`，不得因另一 operand 是 exact value 就 hidden resolve。

## 14.1 Regime recognition, downgrade, and upgrade

Public regime-conversion surface：

```python
value.try_as(numeric_class)
value.downgrade()
value.downgrade_process()
value.upgrade(numeric_class)
```

`numeric_class` 必為五個 public numeric classes之一；其他 input finite raise `TypeError`。

### `try_as(numeric_class)` — guaranteed-finite specified recognition

`try_as(T)` 只在 source representation / source class 對 target `T` 有 registered guaranteed-finite exact recognition / reconstruction algorithm 時屬合法 request。它不得啟動一般 equality、rationality、algebraicity 或 realness semantic search。

核心 finite recognizers至少包含：

```python
alpha.try_as(Rational) -> Rational | None
alpha.try_as(GaussianRational) -> GaussianRational | None
```

以及 exact regimes 間由 canonical coordinates / finite exact classifiers直接決定的 trivial paths。對沒有 guaranteed-finite recognizer的 source-target pair，finite raise `TypeError`，而不是把 potentially divergent search藏進 ordinary method。General semantic membership search使用 `membership_process(T)` / `downgrade_process()`。

### `downgrade()` — lowest currently recoverable regime

`downgrade()` guaranteed finite。它不承諾找 mathematical value 在抽象上可能屬於的最低 regime，而是回傳**依目前 representation、recoverable floor、persistent constructive evidence與 registered finite recognizers，現在能 guaranteed-finite 具體恢復的最低 public numeric representation**。

最低 regime 依 mathematical value分類：

| Mathematical value | Lowest public regime |
|---|---|
| rational | `Rational` |
| non-real Gaussian rational | `GaussianRational` |
| algebraic but not Gaussian rational | `Algebraic` |
| non-algebraic computable real | `ComputableReal` |
| other computable complex | `ComputableComplex` |

Examples：

```text
GaussianRational(a, 0) -> Rational(a)
Algebraic rational value -> Rational
Algebraic non-real Gaussian-rational value -> GaussianRational
Algebraic otherwise -> Algebraic
```

對 general `ComputableReal` / `ComputableComplex`，若目前沒有 constructive evidence 支援更低 representation，`downgrade()` 直接保留目前 regime；它不得為了追求抽象上真正最低的 regime而啟動無界搜尋。

### Recoverable floor

General semantic node 可保存一個 **recoverable floor**：足以 guaranteed-finite 重建某個較低 public regime representation的 persistent constructive information。若 floor 是 `Algebraic` / `GaussianRational` / `Rational`，payload 本身是 finite exact representation；若 `ComputableReal` 被 lift 到 `ComputableComplex`，floor 亦可保存可有限恢復的 real representation / view。更一般地，只要 `ComputableComplex` 已有可信且持久的 real-membership knowledge，`real_part()` 就是同 denotation 的 guaranteed-finite `ComputableReal` reconstruction，可作 real recoverable floor。

Recoverable floor 是 semantic-quality knowledge，不只是 performance hint。若後續取得更低 representation，floor 單調改善；被更低 floor 完整蘊含的 higher-regime membership facts可依 §4.4 compact。

### `downgrade_process()` — explicit semantic search for a lower regime

`downgrade_process()` 建立 mutable `DecisionProcess`，resolved value 是五個 public numeric classes 之一的 object，代表目前已確立的最低 public regime；construction finite、每個 transition finite，但整體可能永不 resolve。Process fair-advance所有 registered sound semantic recognition / reconstruction strategies，並維持目前 best recoverable floor。

任何較低 representation一旦取得，必立即 commit，即使此次 `advance(...)` 仍回 `Pending()`。Process 只有在已能 finite 確立目前取得的 representation 不可能再降到任何更低 public regime時才 resolve；到達 `Rational` 時因已是全域最低 regime可立即 resolve。

「允許不終止」不等於「所有真 membership 都可半判定」。例如 arbitrary `ComputableReal` 即使 mathematical value 恰為 rational，若 representation 沒有可有限發現的 equality / reconstruction evidence，`downgrade_process()` 仍可永久 `Pending`。同理，證明某 general value 不屬於 `Algebraic` 等 negative membership通常也不能假設 guaranteed finite。

### `upgrade(numeric_class)` — downgrade first, then guaranteed-finite lift

`upgrade(U)` guaranteed finite for every **legal target regime**。它固定先執行：

```text
T_value = self.downgrade()
```

取得目前最低可恢復 representation `T_value`，再使用 registered guaranteed-finite embedding把它 lift到指定 `U`。Target 必能表示該 mathematical value且位於合法 upward path；否則 finite raise `TypeError`。Same-regime request可作 idempotent canonical lift。

升階所得 object 必保留足以 guaranteed-finite 恢復 `T_value` 的 recoverable-floor information，因此滿足：

$$
\operatorname{downgrade}(\operatorname{upgrade}_U(x))
=\operatorname{downgrade}(x)
$$

在 mathematical value與最低目前可恢復 regime 的意義下成立。

Ordinary arithmetic promotion 使用同一 **downgrade-first, then lift** 原則：先對 operands 做 guaranteed-finite `downgrade()`，再依 resulting mathematical regimes / realness選共同 target，最後 finite lift後構造結果。這避免把已知可恢復的簡單 exact value以較複雜 representation帶入 DAG，同時不得為 promotion啟動 `downgrade_process()`。

### `exact_source()` remains structural introspection

```python
x.exact_source() -> Rational | Algebraic | None
z.exact_source() -> Rational | GaussianRational | Algebraic | None
```

`exact_source()` 只做 finite structural introspection：僅在目前 object 已是 exact leaf、或已由 semantics-preserving safe compaction取得 finite exact replacement時回 payload；否則回 `None`。它不執行 regime search。`downgrade()` 則可綜合 recoverable floor 與 registered finite recognizers，語意較高階；兩者不可互相偷渡 potentially divergent work。

---

# 15. Resolution requests

v1 只固定兩類 resolution request。

## 15.1 Width enclosure

```python
x.bound(width=epsilon)
z.box(width=epsilon)
```

其中 `epsilon` 依 §9.2 的 guaranteed-finite positive-rational numeric-value recognizer 取得 mathematical value $\epsilon\in\mathbb Q_{>0}$。

## 15.2 Locally-finite grid localization

```python
x.grid_bound(grid)       # Theorem 1 / near-adjacent
x.grid_project(grid)     # Theorem 3 / near-nearest single point
x.grid_localize(grid)    # Theorem 5 / mixed optimal localization
```

Public standard grids：

```python
IntegerGrid()
BoundedDenominatorGrid(max_denominator=N)
Binary64Grid()
```

Grid object 本身承載其 representation constraint，例如 denominator bound 或 binary64 format；因此 v1 不另設 `max_denominator=`、`bits=`、`format=` 等平行 resolution keywords。

Resolution budget 與 `DecisionProcess.work` 永遠是不同概念。

---

# 16. Python protocol summary

`Polynomial` 是 public exact auxiliary algebraic type rather than a scalar numeric regime. Its v1 public methods in §7.9–§7.13 are all guaranteed finite. In particular, construction / observations / equality / hash / integer-coefficient arithmetic / derivative / exact evaluation / division-gcd / factorization / resultant / Sturm / root counting / isolation never return `DecisionProcess` and never use semantic nontermination as an ordinary outcome.

| Operation | Rational | GaussianRational | Algebraic | ComputableReal | ComputableComplex |
|---|---:|---:|---:|---:|---:|
| `+ - *` | finite total | finite total | finite total | finite construction | finite construction |
| `/` | finite domain decision | finite domain decision | finite domain decision | certificate-gated | certificate-gated |
| `== !=` | total exact | total exact | total exact | `TypeError` | `TypeError` |
| `< <= > >=` | total | real-only total | real-only total | `TypeError` | `TypeError` |
| `bool()` | finite zero-test | finite zero-test | finite zero-test | `TypeError` | `TypeError` |
| `hash` | total; first hash may normalize + freeze | total | total, lazy canonical identity + cross-type tier | unavailable | unavailable |
| `int/floor/ceil/round` | finite | real-only finite | real-only finite | `TypeError` | `TypeError` |
| `float()` | finite correctly-rounded projection; overflow -> `OverflowError` | real-only finite projection; overflow -> `OverflowError` | real-only finite projection; overflow -> `OverflowError` | `TypeError` | `TypeError` |
| `complex()` | finite-coordinate projection; overflow -> `OverflowError` | finite-coordinate projection; overflow -> `OverflowError` | finite-coordinate projection; overflow -> `OverflowError` | `TypeError` | `TypeError` |
| certified finite bounds | trivial | point rectangle / trivial | finite exact refinement | guaranteed finite | guaranteed finite |
| exact semantic relation processes | unnecessary for core relations | unnecessary for core relations | unnecessary for core relations | required | required |

Exact-class `float()` / `complex()` 是 terminal Python interoperability projection，遵循 Python `int` / `Fraction` 類 exact-number conversion 的 overflow behavior：若任何 required real coordinate 位於 $|x|\ge T_{64}$，finite raise `OverflowError`，不回 `±inf`。General semantic classes 不提供 Python correctly-rounded single-value machine conversion；其 binary64 語意輸出使用 `Binary64Grid` 的 theorem-backed observation：bound endpoint 可是真正的 Python `±inf`，但 strict-nearest channel point 與 `grid_project()` 的 near-nearest point對 finite target都必為 finite。Machine float / complex 不得反向參與 exact correctness。

---

# 17. Required error classes

v1 至少：

```text
UnresolvedDomainError
InvalidCertificateError
InconsistentKnowledgeError
```

其中：

- `UnresolvedDomainError`：ordinary partial mathematical operation 的 domain truth 尚未 certified；
- `InvalidCertificateError`：提供的 certificate 格式或 finite verification 失敗；
- `InconsistentKnowledgeError`：incoming trusted / certified fact 與既有 persistent knowledge 存在 finite-detectable contradiction。

其餘 argument / protocol errors 使用 Python standard `TypeError` / `ValueError`；division by zero 使用 `ZeroDivisionError`。

v1 因不提供 hard-error single-value approximation / combined-resolution API，所以不需要 `UnresolvedResolutionError`、`ResolutionImpossibleError`、`InvalidResolutionRequestError`。

---

# 18. Correctness substrate

Core correctness 不依賴 Python machine `float` / `complex` arithmetic。

允許對 interoperability / grid format 做 **exact representation decoding**，例如讀取 binary64 bit pattern、`float.as_integer_ratio()`、finite / infinity / NaN category，以及把已知 exact value correctly round 到 output float。禁止的是以 machine floating arithmetic、tolerance、sampling 或 approximate comparison 充當 exact equality、certificate、root isolation、semantic relation 或 theorem validity 的 correctness evidence。

Exact decisions、certificates、root isolation、bounds verification、hash identity 等最終建立在：

$$
\text{arbitrary-precision integers}
+
\text{Rational}
+
\text{finite exact algorithms}.
$$
