# Computable Numerics

> [!WARNING]
> **This branch is under active development.**  
> This README describes the frozen **v1 target semantics**; the implementation is currently incomplete.

一個以**精確數值、可計算分析、可驗證近似與顯式停機語意**為核心的 Python 數值執行環境。

`Computable` 不把「更高精度浮點數」當成所有問題的答案。它把一個數的**數學值**、**有限表示**、**目前已取得的可驗證知識**、**尚未完成的語意程序**與**使用者這次要求的答案品質／工作量**分開處理。

核心想法可以濃縮成一句話：

> **近似是對數值已取得的知識，不是數值本身。**

因此，一個一般可計算實數可以被保留為能持續精化的演算法語意；目前的區間只是已經證明知道的資訊。當某個精確問題在理論上可能永遠無法有限判定時，函式庫也不會用容差、超時或猜測把它偽裝成普通布林值。

---

## 特色

- 五種公開純量數值制度：
  - `Rational`：\(\mathbb Q\)
  - `GaussianRational`：\(\mathbb Q(i)\)
  - `Algebraic`：\(\overline{\mathbb Q}\)
  - `ComputableReal`：可計算實數
  - `ComputableComplex`：可計算複數
- 公開、不可變的精確 `Polynomial`，係數環為 \(\mathbb Z[X]\)。
- `Rational` / `GaussianRational` / `Algebraic` 的有限精確算術。
- 一般 `ComputableReal` / `ComputableComplex` 的 demand-driven 計算 DAG。
- 可持久重用的 certified interval / rectangle / exact lower-regime knowledge。
- 對一般可計算實數提供 guaranteed-finite 的任意寬度包圍。
- 三種標準可搜尋格點：
  - `IntegerGrid()`
  - `BoundedDenominatorGrid(N)`
  - `Binary64Grid()`
- `DecisionProcess` 明確表達「可能永遠無法完成」的精確語意問題。
- `downgrade()` / `downgrade_process()` / `upgrade()` 把「目前可恢復的最便宜表示」與「數學上真正屬於哪一層」分開。
- trust-user assertions 可以把使用者已知的數學前提轉成可重用的 certified knowledge。
- exact correctness 不以 machine-float tolerance 作證據。

---

## 五種數值制度不是五種精度

這五個類別的區別不是「精度越來越高」，而是它們具有不同的**有限可判定能力**。

| 類別 | 數學值域 | 主要特性 |
|---|---|---|
| `Rational` | \(\mathbb Q\) | 四則、等號、次序、整數轉換與核心投影都可有限精確完成 |
| `GaussianRational` | \(\mathbb Q(i)\) | 兩個有理座標組成的 exact complex field；也是複平面上的精確探針 |
| `Algebraic` | \(\overline{\mathbb Q}\) | 由整係數多項式與唯一根隔離區域精確指定；等號與實代數數次序仍可有限決定 |
| `ComputableReal` | 可計算實數 | 可任意精化，但一般等號不保證有限決定 |
| `ComputableComplex` | 可計算複數 | 一般等號不保證有限決定；「是否為實數」本身也可能是等號問題 |

`Polynomial` 是公開的精確代數工具，但不是第六種純量制度。

---

## 安裝

Python import package 名為：

```python
import computable
```

從 PyPI 安裝：

```bash
python -m pip install computable-number-tower
```

Python import package 名稱仍然是：

```python
import computable
```

從 source checkout 安裝：

```bash
python -m pip install .
```

PyPI distribution name 與 Python import package name 刻意分開：

```text
PyPI distribution: computable-number-tower
Python package:     computable
```

---

## 快速開始

```python
from computable import (
    Rational,
    GaussianRational,
    Algebraic,
    Polynomial,
)
```

### 精確有理數

```python
x = Rational(3, 4)
y = Rational("1.25")

print(x + y)            # exact 2
print(x * y)            # exact 15/16
print(x < y)            # finite exact comparison
```

`Rational` 對 Python `float` 的處理是**精確解碼 binary64 值**，不是把浮點數當十進位字串：

```python
Rational(0.1) == Rational(*0.1.as_integer_ratio())   # True
Rational("0.1") == Rational(1, 10)                   # True

Rational(0.1) == Rational("0.1")                     # 通常 False
```

`str` 與遞迴二元 tuple ratio 是明確的 constructor syntax：

```python
Rational((1, 2))                  # 1/2
Rational((1, 2), (3, 4))          # (1/2) / (3/4) = 2/3
Rational(((1, 2), (3, 4)))        # 同樣是 2/3
```

### 精確高斯有理數

```python
z = GaussianRational(Rational(1, 2), Rational(3, 4))
w = GaussianRational(1, -2)

print(z + w)
print(z * w)
print(z.conjugate())
```

`GaussianRational` 表示的是 \(\mathbb Q(i)\)，不是近似複數。有限 Python `complex` 會先依兩個 binary64 座標精確解碼，再進入 exact arithmetic。

### 整係數多項式

`Polynomial` 的係數順序固定為 **constant-first**：

```python
p = Polynomial((-2, 0, 1))   # -2 + X^2
q = Polynomial((1, 1))       # 1 + X

print(p.degree)
print(p.derivative())
print(p.gcd(q))
print(p.factor())
```

公開多項式核心包含：

```python
p.content()
p.primitive_part()
p.pseudo_divmod(q)
p.exact_div(q)
p.gcd(q)
p.square_free_decomposition()
p.factor()
p.resultant(q)
p.sturm_sequence()

p.real_root_count(interval=None)
p.isolate_real_roots(interval=None)
p.complex_root_count(box)
p.isolate_complex_roots(box=None)
```

多項式也可以直接在五種 scalar regime 上求值：

```python
value = p(Rational(3, 2))
```

若輸入是一般 `ComputableReal` / `ComputableComplex`，求值仍然是 guaranteed-finite 的**表達式建構**；它不會偷偷啟動一般等號或邊界判定。

### 代數數

可以直接從 finite exact scalar 建立：

```python
a = Algebraic(Rational(3, 2))
b = Algebraic(GaussianRational(1, 2))
```

也可以用「整係數多項式 + 唯一根隔離矩形」指定：

```python
p = Polynomial((-2, 0, 1))

sqrt2 = Algebraic(
    p,
    (
        (Rational(1), Rational(2)),   # real interval
        (Rational(0), Rational(0)),   # imaginary interval
    ),
)
```

`Algebraic` 的 mathematical denotation 不變，但內部表示可以 lazy 改善，例如 refine isolating rectangle、求 minimal polynomial 或 canonical root index。

---

## 一般可計算實數：有限近似與精確語意問題是兩件事

一個 `ComputableReal` 表示固定的可計算實數，但它的來源、已知區間與計算進度可以隨查詢逐步改善。

第一版的 native extension point 是 rational-comparator source：

```python
x = ComputableReal.from_comparator_source(source)
```

### 任意寬度的 certified bound 保證有限完成

對任何正有理寬度：

```python
epsilon = Rational(1, 10**80)
interval = x.bound(width=epsilon)
```

這是一個 guaranteed-finite observation。

即使「`x` 是否恰好等於某個值」可能永遠無法決定，也不妨礙函式庫有限取得任意細的 certified enclosure。

---

## `DecisionProcess`：把可能不停止寫進 API

一般可計算實數／複數的精確等號、membership、某些 ordering 與部分運算的 domain 判斷，可能沒有一般的有限決策程序。

這類問題不藏在普通 Python operator 裡，而是回傳可恢復的 `DecisionProcess`：

```python
from computable import Pending, Resolved

p = x.compare_process(y)

state = p.advance(work=1000)

if isinstance(state, Resolved):
    print(state.value)
else:
    assert isinstance(state, Pending)
```

`advance(work=N)` 對任何有限合法的 `N` 都保證有限返回或有限拋出例外，而且最多推進 `N` 個 cooperative finite transitions。

之後可以從原進度繼續：

```python
state = p.advance(work=1000)
```

如果你明確願意等待直到答案出現：

```python
answer = p.resolve()     # may not terminate
```

### `Pending` 不是 `False`

```python
bool(Pending())          # TypeError
```

`Pending` 只表示：

> 目前累積的有限資訊還不足以解決這個 process 的最終問題。

它不代表「答案是否定的」、不代表 timeout，也不代表這次計算沒有得到任何有用知識。

---

## 比較與關係

對 exact regimes：

```python
Rational
GaussianRational
Algebraic
```

exact equality 是有限總判定；若兩個值都是實數，ordering 也可有限精確完成。

對一般可計算數，使用顯式 semantic processes：

```python
from computable import Relation

p = x.compare_process(y)

q = x.relation_process(y, Relation.LESS)
r = x.relation_process(y, Relation.EQUAL)
s = x.relation_process(y, Relation.NOT_EQUAL)
```

`compare_process` 的方向是 receiver compared with argument：

```text
Order.LESS     iff x < y
Order.EQUAL    iff x = y
Order.GREATER  iff x > y
```

一般 `ComputableComplex` 沒有自然 total order，因此 complex `relation_process` 只接受：

```python
Relation.EQUAL
Relation.NOT_EQUAL
```

---

## 一般複數的「是否為實數」必須顯式

對一般 `ComputableComplex`：

\[
z\in\mathbb R
\iff
\operatorname{Im}(z)=0
\]

右邊本身就是一般可計算實數的 equality boundary，因此 realness 不保證有限可判定。

推薦流程：

```python
p = z.membership_process(ComputableReal)
state = p.advance(work=1000)
```

只有在 `Resolved(True)` 之後，才把 real ordering 視為已取得的能力。

`ComputableReal.compare_process(...)` **不會**因為收到一個尚未證明為實數的 general `ComputableComplex`，就偷偷啟動另一個 realness search。

---

## 一般可計算複數

```python
z = ComputableComplex.from_parts(real_part, imag_part)

real = z.real_part()
imag = z.imag_part()

box = z.box(width=Rational(1, 10**50))
```

`box(width=...)` 對正有理寬度提供 guaranteed-finite 的 certified rectangle observation。

一般複數還提供：

```python
z.membership_process(numeric_class)
z.relation_process(w, relation)
z.component_compare_process(w)
z.direction_process(w, direction=u)
z.downgrade_process()
```

---

## 部分運算：普通 API 不偷跑 domain search

以除法為例：

```python
x / y
```

普通除法只在目前 knowledge 已足以有限確認 domain 狀態時工作：

- 已 certified `y != 0`：有限建立結果；
- 已 certified `y == 0`：有限 `ZeroDivisionError`；
- 是否為零仍 unresolved：有限 `UnresolvedDomainError`。

如果你真的要追下去：

```python
from computable import divide_process

p = divide_process(x, y)
state = p.advance(work=1000)
```

倒數使用：

```python
divide_process(1, y)
```

而不是另一套 public reciprocal process API。

---

## 格點觀察：保證有限的離散輸出

第一版提供三種標準一維 real grid：

```python
from computable import (
    IntegerGrid,
    BoundedDenominatorGrid,
    Binary64Grid,
)
```

### 整數格點

```python
grid = IntegerGrid()
```

public grid points 是 Python `int`。

### 分母有界有理格點

```python
grid = BoundedDenominatorGrid(100)
```

它表示所有約分後分母不超過 `100` 的有理數；public grid points 是 canonical `Rational`。

### Binary64 格點

```python
grid = Binary64Grid()
```

它包含所有 finite IEEE-754 binary64 real values，並以 Python `-inf` / `+inf` 作為 extended-real global bounding endpoints；NaN 不屬於格點。

這不表示 `Rational` 或 `ComputableReal` 本身允許 infinity denotation。

### `grid_bound`

```python
bracket = x.grid_bound(grid)
```

guaranteed finite，回傳 near-adjacent bracket：

```text
lower <= x <= upper
```

而 `(lower, upper)` 的開區間內至多還有一個 finite grid point。

### `grid_project`

```python
point = x.grid_project(Binary64Grid())
```

guaranteed finite，直接回 canonical grid point。

這是 **near-nearest** theorem-backed projection，不宣稱 correctly rounded，也不宣稱 strict nearest。

### `grid_localize`

```python
loc = x.grid_localize(grid)
```

guaranteed finite。它保留兩個 optimal channels 的強度，但允許 runtime 回傳目前可有限決定的那一種：

- adjacent bracket，或
- strict-nearest point。

---

## Trust-user assertions

如果你**已經知道**某個額外數學事實，可以把它當成 promised precondition：

```python
x.assume_relation(y, Relation.LESS)

x.assume_membership(Rational, True)

x.assume_grid_membership(
    BoundedDenominatorGrid(100),
    True,
)
```

這不是「關掉驗證」。

例如：

```python
x.assume_grid_membership(grid, True)
```

在 promise 為真的前提下，runtime 會利用局部有限性與 certified separation，在返回前真正辨識 exact grid point，並保存可有限恢復的較低 exact representation。

### 錯誤 assertion 的語意

- 如果 assertion 已與目前 knowledge 形成有限可辨認矛盾，立即 `InconsistentKnowledgeError`。
- 如果 promise 是假的、但矛盾尚無法有限顯現，依賴該 promise 才保證完成的 refinement **可以永遠不返回**。
- timeout 不會被當成「promise 為假」的證據。
- runtime 不會因為使用者給錯 promise 就在 promise domain 外 fabricated 一個不正確答案。

`assume_*` 因此是明確的 trust boundary，不是一般 arithmetic API 的替代品。

---

## Persistent knowledge

一般 `ComputableReal` / `ComputableComplex` 會累積 certified information。

主要 carrier 是：

```text
real:    strongest useful rational interval
complex: strongest useful rational rectangle
```

如果系統已經有限恢復出較低制度的 exact representation，也會保存 recoverable floor。

一個尚未 resolve 的 process 仍然可能讓系統變得更聰明：

```text
advance()
→ 取得更窄 interval / strict separation / lower exact representation
→ 立即 commit
→ 最終問題仍 Pending
```

後續其他 query 可以直接重用這些知識與 source progress。

---

## Computation DAG

一般 `ComputableReal` / `ComputableComplex` 的衍生運算使用 explicit DAG。

`Rational`、`GaussianRational`、`Algebraic` standalone arithmetic 不會預設進入 DAG；它們只有在 lift 到一般 semantic computation chain 時才成為 exact leaves。

DAG 的目標不是把函式庫變成 universal CAS，而是：

- 保存依賴關係；
- 避免深 closure/reference chain；
- 共享結構相同的 live nodes；
- 讓 shared subexpression 共用 persistent knowledge；
- 讓 evaluator 只精化當前 query 真正需要的 upstream sources；
- 避免為了 graph normalization 偷做一般 semantic equality。

---

## Regime conversion

所有五種公開 numeric regimes 共用：

```python
value.try_as(numeric_class)
value.downgrade()
value.downgrade_process()
value.upgrade(numeric_class)
```

### `try_as(T)`

只使用已註冊的 guaranteed-finite exact recognition / reconstruction。

例如：

```python
q = alpha.try_as(Rational)
g = alpha.try_as(GaussianRational)
```

不會暗中啟動一般 rationality / algebraicity / realness search。

### `downgrade()`

guaranteed finite。

它回答的是：

> 依目前 representation、persistent constructive evidence 與 recoverable floor，現在最低能有限恢復到哪個公開數值制度？

它不承諾找出數學上抽象的最低制度。

### `downgrade_process()`

顯式搜尋更低 regime，可能永久 `Pending`。

任何較低 representation 一旦 soundly discover，就會立刻 commit，因此即使 outer process 尚未 resolve：

```python
value.downgrade()
```

也可能已經能看到新的 recoverable floor。

### `upgrade(T)`

先做 ordinary `downgrade()`，再有限 lift 到目標制度，並保留原本可恢復的較低表示。

ordinary promotion 也採相同的 downgrade-first 原則，但永遠不會偷偷啟動 `downgrade_process()`。

---

## `Rational` 的 working / frozen lifecycle

`Rational` 是唯一允許 public working-value mutation 的 numeric class。

一般 public constructor 產生 canonical frozen/interned value；如果需要 arithmetic workspace：

```python
import copy

r = Rational(1, 3)
w = copy.copy(r)     # distinct mutable working Rational
```

working value 可以暫時保持未約分，以減少 hot-path gcd 成本：

```python
w += Rational(1, 6)
w.simplify()
```

需要 canonical sharing：

```python
stable = w.intern()
```

第一次對 mutable working value做：

```python
hash(w)
```

會有限 normalize 並 freeze **同一個 Python object**。

`hash()` 與 `intern()` 是兩個不同概念：

- `hash(w)`：凍結目前這個 object；
- `w.intern()`：尋找／建立目前 live canonical shared object。

---

## Exact classes 與 Python numeric interoperability

有限 exact bridge 依**數學值**而不是 nominal source type 判斷。

例如 integral：

```python
1
True
1.0
complex(1, 0)
fractions.Fraction(1, 1)
Rational(1)
GaussianRational(1, 0)
Algebraic(1)
```

在需要 exact integer-valued numeric input 的位置具有相同數學語意。

對 exact scalar equality，跨類別相等值必遵守 Python 的 equal-hash contract。

一般 `ComputableReal` / `ComputableComplex` 不會為了融入這個 bridge 而偷偷啟動 semantic recognition。

---

## Machine-number projection

### Exact classes

`Rational`、real `GaussianRational` 與 real `Algebraic` 可以做 finite correctly-rounded binary64 projection：

```python
float(q)
float(alpha)
complex(z)
```

如果 exact magnitude 已超出 finite-output boundary，拋出 `OverflowError`，而不是把 `±inf` 當成 exact-class overflow value。

### General semantic classes

一般 `ComputableReal` / `ComputableComplex` 不透過 Python `float()` / `complex()` 偷做 potentially problematic semantic selection。

對一般 real 的 binary64 離散觀察，使用：

```python
x.grid_bound(Binary64Grid())
x.grid_project(Binary64Grid())
x.grid_localize(Binary64Grid())
```

---

## 自訂 `ComputableReal` source

第一版凍結的 native-real extension 是 rational comparator source。

概念 protocol：

```python
class RationalComparatorSource:
    def compare_rational_process(
        self,
        q: Rational,
    ) -> DecisionProcess[Order]:
        ...
```

對某個固定 denotation `x`：

```text
x < q  -> eventually Order.LESS
x > q  -> eventually Order.GREATER
x = q  -> 可以永久 Pending；若 source 有 equality evidence 也可 Order.EQUAL
```

source 必須在整個 lifetime 表示同一個數，而且所有已 resolve comparison 都必須 sound、彼此一致。

這是 trusted semantic contract；runtime 不可能一般有限驗證任意 Python source 是否真的滿足這些承諾。

建立：

```python
x = ComputableReal.from_comparator_source(source)
```

之後，同一 source 的 progress 與已取得的 certified knowledge 可以跨 query 重用。

---

## 這個函式庫不是什麼

`Computable` 不是：

- 任意精度浮點函式庫的另一個名字；
- 單純把所有數都包成 interval 的區間算術套件；
- universal symbolic CAS；
- 用 tolerance 代替 exact equality 的系統；
- 用 timeout 猜測「大概不相等」的系統。

它的核心目標是：

> 在 exact algebra、certified approximation、computable analysis 與 Python runtime 之間，清楚保留哪些事情可以有限完成、哪些事情可能需要無界搜尋，以及目前到底已經可靠地知道多少。

---

## 第一版刻意不包含

第一版完整實作後，以下仍不屬 v1 frozen public surface：

- `sqrt` / `log` / 一般 elementary real or complex functions；
- 內建 native constants，例如 \(\pi\)、\(e\)；
- `floor_process` / `ceil_process` / `round_process`；
- correctly-rounded / strict-nearest 的 general semantic machine-number process；
- 額外 public grid families，例如 `DyadicGrid`；
- 任意 user-defined grid plugin API；
- advanced algebraic / transcendental DAG rewrites；
- 無外部同步下的 shared-runtime thread safety。

這些能力若未來加入，必須先擴充 public semantic specification 與必要的 termination theorem，而不是只在 implementation 裡偷偷增加行為。

---

## Thread-safety

第一版不保證以下共享 mutable runtime state 在沒有 external synchronization 時 thread-safe：

- node knowledge commits；
- weak interning；
- `DecisionProcess` mutation；
- shared source progress。

如果多個 thread 會同時操作同一個 semantic object / process / source，請自行提供同步。

---

## 規格與正確性

這個專案的 correctness 不只定義為「最後顯示的數字看起來對」：

```text
value correctness
+ termination correctness
+ representation invariants
+ knowledge consistency
+ graph correctness
+ performance behavior
```

完整設計文件：

- `00_README.md`：文件地圖與全域設計不變量
- `01_CORE_GOALS_AND_THEORETICAL_FRAMEWORK.md`：核心目標與理論框架
- `02_SEMANTIC_SPECIFICATION.md`：**public runtime semantics 的最高權威**
- `03_ARCHITECTURE_AND_PUBLIC_API.md`：架構與 public API 映射
- `04_IMPLEMENTATION_ROADMAP.md`：實作順序
- `05_TEST_AND_BENCHMARK_SPEC.md`：correctness / benchmark contract
- `06_MATHEMATICAL_FOUNDATIONS.md`：**形式數學定義與定理的最高權威**
- `07_REFERENCE_IMPLEMENTATION_NOTES.md`：舊 reference implementation 的工程抽取筆記

若 README 的簡化說明與 `02_SEMANTIC_SPECIFICATION.md` 衝突，以 `02` 為準；若涉及形式數學定義與定理，以 `06_MATHEMATICAL_FOUNDATIONS.md` 為準。

---

## 設計哲學

這套系統的使用者介面背後有幾個簡單原則：

- 盡力理解使用者真正要求的數學資訊；
- 儘量完成使用者想完成的事；
- 不替使用者偷偷決定「精度、工作量、是否願意等待」之間的交換；
- 不做當前 query 不需要的昂貴語意工作；
- 不要求電腦有限完成理論上沒有一般有限解法的問題。

當一個精確問題真的可能永遠沉默時，`Computable` 不把沉默偽裝成答案。

它把那個邊界直接放進 API。
