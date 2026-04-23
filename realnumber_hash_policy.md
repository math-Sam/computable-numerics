# RealNumber 的哈希政策說明

> 本文件面向 **使用者**，說明 `RealNumber` 在 `set`、`dict` 鍵值、以及 `hash()` 使用情境下的行為與限制。  
> 本文件假設你已經讀過專案的 `README`，但**不假設你讀過內部技術規格或原始碼**。

---

## 這份文件要回答什麼？

`RealNumber` 是以比較 oracle 定義的可計算實數。  
因此，`RealNumber` 的哈希（`__hash__()`）**不能**像一般整數或分數那樣，直接視為理所當然。

這份文件要回答的核心問題是：

1. 哪些 `RealNumber` 物件可以安全地做 `hash()`？
2. 哪些 `RealNumber` 物件不可以？
3. 為什麼需要額外設定 `set_max_denominator_for_hash`？
4. 若要把 `RealNumber` 放進 `set` 或當作 `dict` 的 key，使用者必須遵守什麼規則？

---

## 先說結論

### `RealNumber` **不是預設建議**拿來放進 `set` 或當作 `dict` key 的型別。

你**可以**這樣做，但前提是你了解本文件描述的哈希政策。

最重要的原則只有一句：

> `RealNumber` 只有在目前哈希政策下，已經被解析為 **rational-only** 或 **irrational-only** 時，才可哈希。  
> 若物件仍處於 **undecided** 狀態，則它預設不應被視為可哈希。

---

## 為什麼 `RealNumber` 的哈希比一般數值型別麻煩？

對 `int`、`Fraction`、或明確的有限精度數值而言，值本身通常已經足夠清楚，因此哈希可以直接建立在那個值上。

但 `RealNumber` 的情況不同：

- 它可能代表無理數；
- 它也可能其實代表某個有理數，但系統**還沒辨認出來**；
- 系統對真值的認識，是透過比較查詢與逐步 refinement 累積而來；
- 因此，「這個物件現在是否已經足夠確定，能安全地給出穩定哈希」本身就是一個有狀態的問題。

也就是說：

> `RealNumber` 的可哈希性，不只取決於真值，也取決於目前已知資訊是否已經把它解析到足夠穩定的狀態。

---

## 本文件中的核心術語

### 1. 哈希（hash）

哈希值是 Python 用來支援：

- `set`
- `dict` 的 key
- 以及其他需要「可哈希物件」的情境

的一個整數值。

如果某個物件被放進 `set` 或當成 `dict` key，就必須能提供**穩定**的哈希行為。

---

### 2. denominator budget（分母預算）

本系統使用類別屬性：

```python
RealNumber.set_max_denominator_for_hash = ...
```

來指定哈希時所採用的**分母預算**。

這個預算的用途有兩個：

1. 嘗試辨認某個 `RealNumber` 是否其實是**小分母有理數**；
2. 對已知無理數的 `RealNumber`，在固定分母預算下選出穩定的代表方式，以產生哈希值。

你可以把它理解成：

> 「系統在做哈希時，允許自己使用多大分母的有理數來辨認或近似這個 real object。」

---

### 3. bounded rational discovery（有界有理數辨認）

在哈希過程中，系統可能會呼叫：

```python
rational_bound(set_max_denominator_for_hash)
```

這不是單純為了近似，而是為了在**固定分母預算**下，嘗試回答：

> 這個 `RealNumber` 是否其實已經可以被辨認成某個 exact rational？

若可以，則物件的狀態會被解析得更明確。

---

## `RealNumber` 的三種狀態

`RealNumber` 的哈希政策，建立在三種數值狀態之上。

---

### A. `rational-only`

表示：

- 這個物件已經被確認為**精確有理數**；
- 它不再可能是無理數；
- 系統已經知道它對應的 exact rational 是哪一個。

你可以把它想成：

> 「這個 `RealNumber` 雖然外表還是 `RealNumber`，但本質上已經確定是一個 exact rational value。」

---

### B. `irrational-only`

表示：

- 這個物件已經被確認為**不是有理數**；
- 它不再可能塌縮成某個 exact rational；
- 但它仍然代表一個穩定的實數真值。

你可以把它想成：

> 「這個 `RealNumber` 已經確定是無理數，接下來只剩 refinement 的問題，不再有『其實可能是有理數』的懸念。」

---

### C. `undecided`

表示：

- 目前系統仍保留兩種可能：
  - 它可能是有理數；
  - 它也可能是無理數。
- 換句話說，系統目前還**沒有足夠資訊**把它解析到 `rational-only` 或 `irrational-only`。

你可以把它想成：

> 「真值本身沒有改變，但系統目前對這個真值的了解還不夠完整。」

---

## 一個重要的語意承諾

這是本文件最重要的承諾之一：

> `RealNumber` 的狀態只會由 **undecided** 單向轉移到 **rational-only** 或 **irrational-only**。  
> 它**不會**從 `rational-only` 或 `irrational-only` 回退成 `undecided`。

這表示：

- 狀態解析是**單向收斂**的；
- 一旦物件從不可哈希的 `undecided` 狀態解析成可哈希狀態，它不會再因為後續 refinement 回到不可哈希狀態；
- refinement 改變的是**你已知多少資訊**，不是物件的數學真值。

用哈希語言說就是：

> `RealNumber` 的狀態只會從「可能不可哈希」走向「可哈希」，不會反向退回。

---

## 面對使用者的哈希契約

若你要把 `RealNumber` 放進 `set` 或當成 `dict` 的 key，請遵守以下契約。

---

### 1. 若物件是 `rational-only`

則其哈希值定義為：

> **exact rational 的 hash**

也就是說，這時候它的哈希行為與對應的 exact rational 一致。

---

### 2. 第一次對非 `rational-only` 的物件做 hash 之前，必須先設定 `set_max_denominator_for_hash`

如果你預期會對：

- `irrational-only`
- 或 `undecided`

狀態的 `RealNumber` 呼叫 `hash()`，  
那麼在第一次這樣做之前，必須先設定：

```python
RealNumber.set_max_denominator_for_hash = 正整數
```

而且：

> 一旦這個值設定完成，就**不應再改成不同的值**。

原因是：

- 哈希政策必須穩定；
- 同一個物件不能在今天用分母預算 50 算 hash，明天又改成 100 重新算出另一個不相容的 hash。

---

### 3. 若物件是 `irrational-only`

則其哈希值定義為：

> **固定 denominator budget 下的 representative hash**

這個 representative hash 不是 exact rational hash，  
而是在固定分母預算下，根據 `rational_bound(...)` 與相關判定規則，選出穩定代表值後得到的 hash。

使用者不必記住內部細節，但要知道這件事：

> 對於 `irrational-only` 的 `RealNumber`，其 hash 是**政策化且穩定的**，而不是 exact rational 式的 hash。

---

### 4. 若物件是 `undecided`

此時 `__hash__()` **不會**立刻放棄，而是會執行一次 bounded rational discovery ，並在需要時再做一次中點測試。

這一步的目的，是避免把「其實已經在目前分母預算下可被辨認為小分母有理數」的物件，過早判成不可哈希。

執行後有三種可能：

#### 情況 A：物件被解析為 `rational-only`
則回到第 1 條，用 exact rational 的 hash。

#### 情況 B：物件被解析為 `irrational-only`
則回到第 3 條，用 fixed-budget representative hash。

#### 情況 C：物件執行後仍是 `undecided`
則：

> `__hash__()` 拋出 `TypeError`，該物件被視為目前不可哈希。

這表示：

- 系統在目前分母預算下，仍無法安全決定應該走有理數 hash 還是無理數 representative hash；
- 因此，這個物件不應進入 `set` 或 `dict` key 的哈希宇宙。

---

## 一個簡短的使用建議

如果你的程式中根本不需要把 `RealNumber` 放進 `set` 或當成 `dict` key，  
那麼最簡單的做法就是：

> **不要對它呼叫 `hash()`。**

這是最保守、也最自然的使用方式。

---

## 如果你真的需要把 `RealNumber` 放進 `set` 或作為 `dict` key`

建議流程如下。

### 建議做法

```python
from Computable_current import ComputableReal as R

R.set_max_denominator_for_hash = 1000

x = ...
h = hash(x)   # 若成功，表示 x 已在目前政策下可哈希
```

---

### 若你不想事先檢查狀態，且可以接受失敗

你可以使用：

```python
try:
    my_set.add(x)
except TypeError:
    ...
```

或：

```python
try:
    my_dict[x] = value
except TypeError:
    ...
```

這表示：

- 你允許 `x` 先嘗試進入 hashable universe；
- 若它在目前 denominator budget 下仍然維持 `undecided`，則接受 `TypeError`。

---

## 為什麼系統不直接讓所有 `RealNumber` 都可哈希？

因為這會產生一個根本問題：

- 某些 `RealNumber` 物件實際上可能等於某個有理數；
- 但在一般情況下，系統不一定能立刻判定它是否真的為 rational；
- 若在這種狀態下仍強行給它一個哈希值，就可能破壞「相等物件應具有相同哈希值」的基本要求。

所以本系統採取的策略是：

> **只有在目前哈希政策下，物件的 number-kind 已經解析到足夠穩定時，才允許它可哈希。**

這是為了讓：

- 哈希值穩定；
- 狀態演化單向；
- 與 exact rational 的對齊在可辨認時成立；
- 並避免把仍含有「是否其實是有理數」不確定性的物件，放進 `set`/`dict` 所要求的穩定哈希環境。

---

## 最後的總結

請記住下面這三句話：

### 1.
`RealNumber` **不是預設建議**拿來放進 `set` 或作為 `dict` key 的型別。

### 2.
只有在目前 hash denominator budget 下已解析為：

- `rational-only`
- 或 `irrational-only`

的 `RealNumber`，才應被視為可哈希。

### 3.
對 `undecided` 物件，`__hash__()` 會先嘗試做一次 bounded rational discovery；  
若執行後仍為 `undecided`，則拋出 `TypeError`，該物件不可哈希。