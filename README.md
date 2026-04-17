# Computable Current

> 一個以「精確有理數 + 比較 oracle 定義的可計算實數」為核心的單檔數值模組。

`Computable_current.py` 的目標不是提供「更多位數的浮點數」，而是把數值拆成兩個本質不同的層次：

- **`ComputableRational`**：精確有理數
- **`ComputableReal`**：以「對任意有理數的比較 oracle」定義的可計算實數

**這個模組適合的場景：**

- 精確分數運算
- 將不可直接寫成分數的值表示為可比較、可逼近的實數
- 在需要時才要求更高精度
- 取得分母受限的有理近似
- 以嚴格區間而非單點浮點近似來描述誤差

## 目錄

- [設計核心](#設計核心)
- [模組結構](#模組結構)
- [這個模組不是什麼](#這個模組不是什麼)
- [快速開始](#快速開始)
- [心智模型](#心智模型)
- [精度與表示](#精度與表示)
- [內建常數](#內建常數)
- [根尋找](#根尋找)
- [雜湊與快取](#雜湊與快取)
- [目前功能範圍](#目前功能範圍)
- [需求](#需求)
- [匯入方式](#匯入方式)
- [一句話總結](#一句話總結)

## 設計核心

### 1. 有理數與實數分開建模

這個模組最重要的設計不是 API，而是數學模型：

- `ComputableRational` 直接儲存分子、分母，所有值都可精確表示
- `ComputableReal` 不直接儲存十進位展開，而是儲存一個 **sign oracle**

對任意有理數 `q`，這個 oracle 會回答 `q` 與目標實數 `x` 的大小關係：

- `-1`：查詢值 `<` 真值
- `0`：查詢值 `==` 真值
- `1`：查詢值 `>` 真值

也就是說，`ComputableReal` 的本質是「可比較的實數」，不是「預先算好的高精度小數」。

### 2. 精度是按需求傳播的

`ComputableReal` 會維護目前已知的有理區間，並在比較、輸出、或要求更細近似時才做 refinement。這使得：

- 上游節點一旦被逼近，下游節點可以重用這些資訊
- 不需要在每一步運算都主動把值算到固定精度
- 誤差控制是系統的一級功能，不是附帶效果

### 3. 運算圖是隱式的

`ComputableReal` 的四則運算不會直接把值壓成浮點數，而是建立新的 `ComputableReal`，其 sign function 會閉包引用上游運算元。整體上，所有 `ComputableReal` 物件形成一張 **隱式 DAG**：

- 邊不是顯式資料結構
- 依賴關係由 Python closure 表示
- 精度由下游需求反向推動到上游

### 4. 有理數物件有 mutable / frozen 兩種生命週期

`ComputableRational` 不是單純的 immutable fraction 類別。它同時支援：

- **frozen / canonical** 物件：適合共享、快取、hash、做 key
- **mutable** 物件：適合大量中間運算，避免每一步都重新 canonicalize

這個設計讓模組可以同時兼顧：

- 精確語意
- 記憶體共享
- 中間運算效能

## 模組結構

| 型別 | 角色 | 核心特性 |
| --- | --- | --- |
| `ComputableRational` | 精確有理數 | 精確表示、可 canonicalize、可快取 |
| `ComputableReal` | 可計算實數 | 以比較 oracle 定義、可逐步 refinement |

### `ComputableRational`

`ComputableRational` 是精確有理數型別。

**支援的輸入：**

- `int`
- `(numerator, denominator)`
- `fractions.Fraction`
- `str`
- `float`
- 巢狀 tuple
- 另一個 `ComputableRational`

**重點能力：**

- 自動正規化與約分
- 以全域快取維護 canonical frozen 值
- 內建 `ZERO`, `ONE`, `infty`, `minfty`, `nan`
- 支援 `+ - * / // % divmod **`
- 支援分母受限近似：`rational_bound`, `rational_floor`, `rational_ceil`, `rational_round`
- 支援 `iroot()` 與 `logarithm()`
- 當結果仍為有理數時，優先保留在 `ComputableRational`

### `ComputableReal`

`ComputableReal` 是可計算實數型別。

**建立方式：**

1. 從精確有理數建立
2. 使用內建常數 `PI`, `E`
3. 提供 sign function 建立新實數

**重點能力：**

- 不是固定精度數值，而是可逐步逼近的數值物件
- 同時追蹤兩層區間資訊：動態查詢區間與結構化 refinement 區間
- 支援 `+ - * /`，且運算結果仍維持在 `ComputableReal`
- 支援 `current_bound`, `current_width`, `refine_to_width`
- 支援 `rational_bound(max_denominator)` 取得受限分母近似
- 支援 `float_bound()`，以區間方式描述浮點輸出誤差
- 支援 `root_finding()` 以連續函數和異號區間建立實數根

## 這個模組不是什麼

**它不是：**

- 一般意義上的 arbitrary precision decimal library
- 以小數位數為中心的高精度浮點包裝器
- 純 symbolic CAS

**它更接近：**

> 一個把精確有理數、可計算實數、區間逼近、與需求驅動精度傳播整合在一起的數值核心。

## 快速開始

### 基本範例

```python
from Computable_current import ComputableRational as Q, ComputableReal as R

a = Q(3, 4)
b = Q("1.25")
pi = R.PI
sqrt2 = Q(2) ** Q(1, 2)

print(a)             # 3/4
print(b)             # 5/4
print(float(pi))     # 3.141592653589793
print(float(sqrt2))  # 1.4142135623730951
```

### 自訂可計算實數

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

print(float(sqrt2))
```

## 心智模型

### `ComputableRational`

**把它想成：**

- 精確值容器
- 可 canonicalize 的快取節點
- 中間運算時可暫時保持 mutable 的 fraction engine

**使用建議：**

- 大量迴圈更新前，用 `__copy__()` 取得 mutable 副本
- 完成後用 `intern()` 收斂成 canonical frozen 值
- 要放進 `dict` / `set` 前，先 `intern()`

### `ComputableReal`

**把它想成：**

- 一個知道如何回答「`q` 跟我相比在哪邊」的實數物件
- 一個會隨查詢而累積更多界資訊的 stateful oracle
- 一個位於隱式計算圖上的節點

**常見建議：**

- 先用 `current_bound()` 看目前已知範圍
- 需要更細近似時，再呼叫 `refine_to_width()`
- 需要受限分母表示時，用 `rational_bound(max_denominator)`
- 不要把 `float(x)` 當成唯一真相；若你在乎保證，應搭配 `float_bound()` 或有理區間 API

## 精度與表示

### `ComputableRational` 的輸出 API

| API | 用途 |
| --- | --- |
| `as_integer_ratio()` | 取得精確分子分母 |
| `to_scientific_notation()` | 輸出科學記號字串 |
| `float_bound()` | 取得保證包含真值的浮點區間 |

### `ComputableReal` 的輸出 API

| API | 用途 |
| --- | --- |
| `current_bound()` | 取得目前已知的有理區間 |
| `refine_to_width(epsilon)` | 把區間縮到指定寬度 |
| `rational_bound(max_denominator)` | 取得受限分母的夾擠近似 |
| `float_bound()` | 取得區間安全的浮點表示 |
| `float(x)` | 根據目前可得資訊選出的浮點近似 |

## 內建常數

| 常數 | 說明 |
| --- | --- |
| `ComputableReal.PI` | 圓周率的 `ComputableReal` 表示 |
| `ComputableReal.E` | 自然常數的 `ComputableReal` 表示 |

這兩個常數不是硬編碼的小數，而是以級數驅動的比較機制建立出的 `ComputableReal` 物件。

## 根尋找

`ComputableReal.root_finding(func, interval)` 可以根據連續函數與異號區間建立一個根。

**這個 API 適合：**

- 已知區間內有唯一根
- 想把根納入同一套 `ComputableReal` 表示系統
- 想讓後續比較、逼近、與有理近似沿用同一套機制

## 雜湊與快取

### `ComputableRational`

- canonical frozen 值會進入全域快取
- `__hash__()` 會促使 mutable 物件凍結
- 相等值可共享同一個 frozen 物件

### `ComputableReal`

- 第一次 hash 前必須先設定 `ComputableReal.set_max_denominator_for_hash`
- 這個值只能設定一次
- 目的是讓小分母有理值的 hash 儘量與 `ComputableRational` 相容

## 目前功能範圍

### `ComputableRational`

- 精確四則運算
- 整數商餘
- 有理次方
- 有理對數
- 分母受限近似
- 精確／近似格式輸出

### `ComputableReal`

- 由有理數、sign function、內建常數建立
- 四則運算
- 比較與相等判定
- 結構化 refinement
- 有理與浮點近似輸出
- 根尋找

## 需求

- **Python 3.14+**
- 不需第三方套件，僅依賴標準函式庫

## 匯入方式

```python
from Computable_current import ComputableRational, ComputableReal
```

或

```python
from Computable_current import ComputableRational as Q, ComputableReal as R
```

## 一句話總結

這個模組的核心不是「把數字算成很多位小數」，而是：

> 用精確有理數作為基底，
> 用有理數比較 oracle 定義可計算實數，
> 用區間與需求驅動 refinement 管理近似。
