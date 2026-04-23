# Computable Current

給 Python 使用的**精確有理數**與**以 oracle 定義的可計算實數**。

`Computable_current.py` 是一個單檔數值模組，清楚區分兩種本質不同的數：

- `ComputableRational`：精確有理數
- `ComputableReal`：透過與有理數比較來定義的可計算實數

這個專案**不是**一個只是想印出更多位數的小數套件。它更像一個小型數值核心，適合用在你需要下列能力的場景：

- 精確分數運算
- 不必承諾固定小數展開、但仍可比較與逐步逼近的實數
- 分母受限的有理近似
- 以區間呈現的誤差保證
- 以及只在真正需要時才計算的精度

> [!IMPORTANT]
> 若你打算把 `ComputableReal` / `RealNumber` 放進 `set`、當作 `dict` 的 key，或主動對它呼叫 `hash()`，請先閱讀 **`realnumber_hash_policy.md`**。  
> `ComputableReal` 的哈希行為**不是**一般整數或分數那種「預設理所當然可哈希」的語意；它依賴額外的分母預算政策與物件狀態解析。

## 為什麼會有這個專案

多數 Python 數值工具優先考慮的是：

- 快速的浮點運算，或
- symbolic manipulation（符號操作）

這個模組走的是另一條路：

- 有理數始終保持精確
- 實數以 **sign oracle** 表示
- 近似值不是單一小數，而是帶保證的區間
- refinement 只會在下游操作真的需要時才發生

換句話說，這個模組更接近一個**可計算實數的執行時系統（exact / computable real runtime）**，而不是 arbitrary-precision decimal library。

## 特色

### `ComputableRational`

- 精確有理數四則運算
- 自動正規化與約分
- 具有全域快取的 canonical frozen 物件
- 適合中間計算的 mutable 物件
- 透過 `rational_bound()`、`rational_floor()`、`rational_ceil()`、`rational_round()` 提供分母受限近似
- 提供 `as_integer_ratio()`、`to_scientific_notation()`、`float_bound()` 等精確／區間安全輸出工具
- 額外支援整數根與有理對數等操作

### `ComputableReal`

- 不靠預先儲存小數展開，而是以比較 oracle 定義實數
- 內建常數 `PI` 與 `E`
- 在 `+`、`-`、`*`、`/` 下封閉
- 透過 `current_bound()` 提供有保證的有理區間
- 透過 `refine_to_width()` 支援需求驅動 refinement
- 透過 `rational_bound(max_denominator)` 提供分母受限的有理近似
- 透過 `float_bound()` 提供區間安全的浮點輸出
- 可用 `root_finding()` 從連續函數與異號區間建立根

> [!NOTE]
> `ComputableReal` 的主要設計目標是：**比較、區間保證、逐步 refinement**。  
> 它不是預設拿來當 `set` 成員或 `dict` key 的值型別。  
> 若你的使用情境涉及哈希，請直接閱讀 **`realnumber_hash_policy.md`**，不要只依賴本 README 最後的簡短摘要。

## 需求

- **Python 3.14+**
- 不需要第三方套件

## 安裝

目前這個專案是一個單檔模組。

把 `Computable_current.py` 放到你的 Python path 中，然後直接匯入：

```python
from Computable_current import ComputableRational, ComputableReal
```

或

```python
from Computable_current import ComputableRational as Q, ComputableReal as R
```

## 快速開始

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

## 可計算實數不是小數字串

`ComputableReal` **不會**儲存十進位數字。  
它儲存的是一個 sign oracle，用來回答下面這個問題：

> 對於某個有理查詢值 `q`，`q` 是小於、等於，還是大於目標實數 `x`？

其符號慣例為：

- `-1`：查詢有理數 `<` 真值
- `0`：查詢有理數 `==` 真值
- `1`：查詢有理數 `>` 真值

這表示 `ComputableReal` 的本質是**可比較、可逐步逼近的實數**，而不是「先算好很多位數的小數展開」。

## 定義你自己的可計算實數

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

對 `sqrt(2)` 這種無理值而言，sign function 不需要回傳 `0`。  
若某個值可能其實是有理數，則在適當時刻回傳 `0`，物件就可以收斂成精確有理表示。

## 區間與 refinement

`ComputableReal` 會持續攜帶區間資訊。  
你可以查看目前已知範圍，也可以只在需要時要求更細的 refinement。

```python
from Computable_current import ComputableRational as Q, ComputableReal as R

x = R.PI

print(x.current_bound())
print(x.current_width())

x.refine_to_width(Q(1, 10_000))
print(x.current_bound())
print(x.current_width())
```

這正是這個模組的核心模型：  
精度是**按需求傳播**的，而不是一開始就全域固定。

## 分母受限的有理近似

這個模組其中一個非常實用的操作，是在分母預算受限時取得有理近似。

```python
from Computable_current import ComputableReal as R

left, right = R.PI.rational_bound(100)
print(left, right)
```

這會回傳一組保證夾住真值、且分母不超過 `100` 的有理區間。  
在很多情況下，這比單純要求「小數點後 10 位」更有意義，尤其是當你在乎後續仍要做精確運算時。

## `ComputableRational` 的 mutable / frozen 生命週期

`ComputableRational` 不只是 immutable `Fraction` 的複製品。  
它支援兩種實用的執行時模式：

- **mutable**：適合大量中間運算
- **frozen / canonical**：適合共享、hash 與快取

典型用法如下：

```python
from Computable_current import ComputableRational as Q

x = Q(1, 3).__copy__()   # mutable 工作副本
x += Q(1, 6)
result = x.intern()      # freeze + canonicalize

print(result)            # 1/2
```

這樣的設計讓模組在維持精確語意的同時，也避免在內層迴圈中做過多不必要的 canonicalization。

## 根尋找

你可以從一個連續函數，以及一個端點異號的有限有理區間，建立可計算實數根。

```python
from Computable_current import ComputableRational as Q, ComputableReal as R

root = R.root_finding(
    lambda n, d: Q(n, d) * Q(n, d) - 2,
    (1, 2),
)

print(root.current_bound())
print(float(root))
```

傳給 `root_finding()` 的 callback 會收到兩個整數 `(numerator, denominator)`，並應回傳某種 real-like 的值。

## 輸出與近似 API

### 有理值

當值是精確的，而且你希望它保持精確時，請使用 `ComputableRational`。

```python
from Computable_current import ComputableRational as Q

x = Q("3.125")
print(x.as_integer_ratio())
print(x.to_scientific_notation())
print(x.float_bound())
```

### 實數值

當值可能是無理數，或你希望近似過程保持顯式時，請使用 `ComputableReal`。

```python
from Computable_current import ComputableReal as R

x = R.E
print(x.current_bound())
print(x.rational_bound(50))
print(x.float_bound())
print(float(x))
```

若你在乎正確性，應優先使用 `current_bound()`、`rational_bound()` 或 `float_bound()`，而不是把 `float(x)` 當成完整真相。

## 心智模型

### `ComputableRational`

可以把它想成：

- 一個精確值容器
- 一個 canonical cache 節點
- 一個適合中間運算的 mutable fraction engine

### `ComputableReal`

可以把它想成：

- 一個知道如何回答「有理數 `q` 跟我相比在哪裡」的實數
- 一個會隨著查詢累積資訊的 stateful oracle
- 一個位於隱式計算圖上的節點

對 `ComputableReal` 做四則運算時，系統不會立刻把它壓成 float。  
相反地，它會建立新的 `ComputableReal`，其 sign function 會閉包引用上游運算元。  
實務上，這會形成一張隱式 DAG；當下游節點需要更高精度時，refinement 可以沿著依賴關係向上游傳播。

## 這個專案不是什麼

這個模組**不是**：

- 一般意義上的 arbitrary-precision decimal package
- 以固定小數位數為中心的高精度浮點包裝器
- symbolic CAS

更準確地說，它是一個整合了下列能力的數值核心：

- 精確有理數
- 可計算實數
- 區間保證
- 需求驅動 refinement

## 雜湊與快取

### `ComputableRational`

- canonical frozen rationals 會進入全域快取
- 對 mutable rational 做 hash 會使其凍結
- 相等的有理值可以共享同一個 canonical 物件

### `ComputableReal`

在對 `ComputableReal` 做 hash 之前，必須先設定：

```python
from Computable_current import ComputableReal as R

R.set_max_denominator_for_hash = 100
```

這個設定只能指定一次。  
它決定了系統在計算無理數的 hash 時所採用的分母預算。

> [!IMPORTANT]
> 上面這段只是最小提醒，不是完整哈希政策。  
> **`ComputableReal` 的 hashability 不是單純「設定一個分母預算就好」**，它還取決於物件當前是否已解析為 `rational-only` 或 `irrational-only`，以及對 `undecided` 狀態要如何處理。  
> 如果你要把 `ComputableReal` 放進 `set`、作為 `dict` key，或準備在公開 API 中對它做 hash，請務必閱讀 **`realnumber_hash_policy.md`**。

## 內建常數

- `ComputableReal.PI`
- `ComputableReal.E`

它們不是硬編碼的小數字串，  
而是由比較程序驅動的可計算實數物件。

## 一句話總結

`Computable_current.py` 是一個單檔 Python 模組，用來處理**精確有理數**與**以 oracle 定義的可計算實數**；而且**區間保證**與**需求驅動 refinement**本身就是表示法的一部分。

> [!TIP]
> 若你只把 `ComputableReal` 當作可比較、可逼近、可取區間界的實數物件使用，閱讀本 README 通常就夠了。  
> 若你要讓 `ComputableReal` 參與 Python 的哈希語意（`hash()`、`set`、`dict` key），請繼續閱讀 **`realnumber_hash_policy.md`**。
