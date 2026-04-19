# Computable Current 技術規格報告


> 文件目的：整理 `ComputableRational` / `ComputableReal` 兩個核心類別的**物件不變量**、**狀態轉移規則**、以及**API 契約**。

---

## 1. 系統總覽

本模組刻意區分兩種數值表示：

- `ComputableRational`：精確有理數；適合做 exact arithmetic 與 canonicalization。
- `ComputableReal`：以 sign oracle 定義的可計算實數；適合做逐步 refinement、區間保證、與需求驅動近似。

兩者的分工不是「一個快、一個慢」，而是：

- `ComputableRational` 的值由 `(numerator, denominator)` 直接決定；
- `ComputableReal` 的值由「對任意有理查詢點 `q` 回答 `q < x`、`q = x` 或 `q > x`」的 oracle 決定。

因此：

- `ComputableRational` 的 mutation 是**值本身的變化**；
- `ComputableReal` 的 mutation 是**對同一真值累積更多資訊**。

---

## 2. 術語與記號

### 2.1 `RationalNumber`

- `numerator`, `denominator`：內部分子分母表示。
- `_is_simplified`：是否已達本系統承認的正規最簡有理數表示。
- `_hash`：已計算出的雜湊值；若為 `None`，表示尚未進入穩定 hash 狀態。
- `_is_frozen`：是否凍結；凍結後不得原地修改。

### 2.2 `RealNumber`

- `_init_sign_func(n, d, input_is_regular=False)`：內部 sign oracle，允許攜帶「此次輸入是否為 regular 測試點」資訊。
- `_sign_func(n, d)`：對外版本，另外處理分母為 0 等特例。
- `_nearest_left`, `_nearest_right`：動態查詢區間（dynamic interval）的左右界。
- `_left_answer`, `_right_answer`：查詢點恰等於 `_nearest_left` / `_nearest_right` 時應回傳的符號；通常分別為 `-1`、`1`，若端點即真值則為 `0`。
- `_left_rational`, `_right_rational`：結構化區間（structural interval）的左右界。
- `_is_regular`：結構化區間是否與當前動態知識同步。
- `_floor`, `_ceil`：真值的整數級夾逼界；初始化完成後，它們分別是真值的真正 `floor` 與 `ceil`。
- `_exact_rational`：若物件已塌縮成精確有理數，則記錄其 exact rational。

### 2.3 符號慣例

`RealNumber` 的 sign oracle 採用以下約定：

- `-1`：查詢有理數 `<` 真值
- `0`：查詢有理數 `==` 真值
- `1`：查詢有理數 `>` 真值

---

## 3. `ComputableRational` / `RationalNumber` 規格

## 3.1 抽象語意

`RationalNumber` 是「可 mutable、可 freeze、可 canonicalize」的 exact rational 實作。

它同時支援兩種執行時模式：

- **mutable 工作物件**：適合內層反覆更新與中間運算；
- **frozen canonical 物件**：適合共享、快取、`dict` / `set` 鍵值與穩定 hash。

---

## 3.2 物件不變量

### R-INV-1：未簡化狀態必為 mutable，且不帶有效 hash

若 `_is_simplified == False`，則在正常 API 路徑下必有：

- `_is_frozen == False`
- `_hash is None`

這代表「未簡化」狀態只允許存在於 mutable 中間值。

### R-INV-2：frozen 狀態必為已簡化且帶 hash

若 `_is_frozen == True`，則必有：

- `_is_simplified == True`
- `_hash is not None`

亦即 frozen 物件必定處於穩定 canonical / hashable 狀態。

### R-INV-3：`_hash is not None` 代表 hash 與**當前值**一致

只要 `_hash is not None`，則該 hash 對應目前的值表示；在正常 API 路徑下，任何真正改值的 mutation 都必須先清除 `_hash`。

注意：

- `_hash is not None` **不推出** `_is_frozen == True`；
- 因為 `__copy__()` 會複製 `_hash`，但回傳的新物件仍為 mutable。

因此，系統容許「mutable 但已預先持有有效 hash」的狀態存在；其正確性依賴於「值一旦被修改，hash 立即失效」。

### R-INV-4：特殊值的正規表示固定

在已簡化語意下，特殊值採固定表示：

- `0` → `0/1`
- `+∞` → `1/0`
- `-∞` → `-1/0`
- `NaN` → `0/0`

### R-INV-5：凍結只能單向進行

單一物件只能由 mutable 轉為 frozen；不允許 in-place unfreeze。
如需 mutable 副本，必須使用 `__copy__()`。

---

## 3.3 狀態轉移規格

### `ComputableRational(...)`

- 走全域快取 / canonical path。
- 回傳值預設為 frozen。
- 若輸入值等於現有 canonical 物件，則可重用同一個物件。

### `__copy__()`

- 回傳**新 mutable 物件**。
- 複製目前值、`_is_simplified`、以及 `_hash`。
- 不保留 frozen 身分。

### `simplify()`

- 若 `_is_simplified == True`，不做事。
- 否則原地將 `(numerator, denominator)` 改寫為正規表示，並設 `_is_simplified = True`。
- 本方法不主動重算 `_hash`；其安全性依賴於未簡化狀態本就不帶有效 hash。

### `intern()`

- 先 `as_integer_ratio()`，亦即保證已簡化；
- 接著設定 `_hash`（若尚未存在）；
- 再把 `_is_frozen = True`；
- 最後透過全域快取做 canonicalization，可能回傳既有物件。

### `__hash__()`

- 若已 frozen，直接回傳 `_hash`；
- 若尚未 frozen，則會：
  1. 先做 `as_integer_ratio()`；
  2. 建立或重用 hash；
  3. 將物件凍結；
  4. 視情況註冊進全域快取。

### 原地修改族（`__setattr__`, `safe_setting`, `+=`, `-=`, `*=`, `/=`）

- 若 receiver 為 mutable：
  - 可原地修改；
  - 必須清掉 `_hash`；
  - 視結果是否特殊值決定 `_is_simplified`。
- 若 receiver 為 frozen：
  - 不得修改原物件；
  - `safe_setting` 與 in-place 算術會回傳**新 mutable 物件**。

---

## 3.4 API 契約

### `as_integer_ratio() -> tuple[int, int]`

**前置條件**
- 無。

**後置條件**
- 物件必定被簡化；
- 回傳值與物件當前 exact rational 值一致；
- 對特殊值也使用本模組自己的 ratio 表示（例如 `1/0`, `0/0`）。

---

### `rational_bound(max_denominator=1) -> tuple[RationalNumber, RationalNumber]`

**前置條件**
- `max_denominator` 必須是正整數。

**後置條件**
- 回傳 `(L, R)`，保證 `L <= self <= R`；
- `L.denominator <= max_denominator` 且 `R.denominator <= max_denominator`；
- 若本身分母已不超過限制，則回傳 point interval `(self, self)` 的 mutable copy；
- 否則回傳分母受限下的最佳夾逼界。

**設計意義**
- 這個 API 以「分母預算」為主要資源，而非十進位位數。

---

### `rational_round(max_denominator=1) -> RationalNumber`

**前置條件**
- `max_denominator` 必須是正整數。

**後置條件**
- 回傳分母不超過限制的單一有理近似；
- 當 `max_denominator == 1` 時，採 half-to-even；
- 對較一般的分母限制，使用夾逼界與中點比較做決策。

---

### `float_bound() -> tuple[float, float]`

**後置條件**
- 回傳 `(f_left, f_right)`，保證真值落在其中；
- 若本值恰可精確表示為 `float`，則回傳 point interval；
- 對 `±∞`、`NaN` 亦給出對應 float 特例。

---

### `to_scientific_notation(precision=17) -> str`

**前置條件**
- `precision >= 0`。

**後置條件**
- 對有限值回傳科學記號字串；
- 對特殊值回傳 `str(self)` 對應表示；
- 內部先走 `as_integer_ratio()`，因此輸出以簡化後 exact rational 為基準。

---

## 3.5 實作層備註

1. `RationalNumber` 的 canonical frozen 物件使用全域 `WeakValueDictionary` 快取。
2. 允許 mutable 副本攜帶舊 hash，但所有正常 mutation 路徑都必須讓 `_hash` 失效。
3. 對高頻率中間計算，建議以 `__copy__()` 取得 mutable 工作副本，再於最終結果呼叫 `intern()`。

---

## 4. `ComputableReal` / `RealNumber` 規格

## 4.1 抽象語意

`RealNumber` 表示一個由 sign oracle 定義的可計算實數。它不是小數字串，也不是預先展開的 digits cache；它的核心介面是：

> 對任一有理查詢點 `q = n/d`，回答 `q < x`、`q = x` 或 `q > x`。

`RealNumber` 的 mutation 原則上不是 value mutation，而是 knowledge refinement：

- 真值 `x` 固定不變；
- 會改變的是目前已知的有理夾逼區間、是否已辨識成 exact rational、以及若干輸出層快取。

---

## 4.2 區間分層設計

`RealNumber` 同時維護兩層區間：

### 4.2.1 動態查詢區間（dynamic interval）

由 `_nearest_left`, `_nearest_right` 表示。

語意：

- `_nearest_left`：目前已知的最佳左界；
- `_nearest_right`：目前已知的最佳右界；
- 每一次 sign query 都可能把它們往內縮。

### 4.2.2 結構化區間（structural interval）

由 `_left_rational`, `_right_rational` 表示。

語意：

- 不一定是目前最緊的已知界；
- 但必須是適合後續 refinement / denominator-bounded search / 測試點產生的規整結構。

### 4.2.3 `regular` 狀態

`_is_regular == True` 表示 structural interval 已與目前動態知識同步。  
`_is_regular == False` 不表示 structural interval 錯了；只表示它**可能比較鬆**、尚未同步到最新 `_nearest_left/_nearest_right`。

---

## 4.3 結構化區間的設計補充

1. **在區間態（尚未塌縮為 exact rational）下，結構化區間的兩端點永遠是 Farey 鄰居。**
2. 此設計最初的主要目標，是為了快速尋找「分母受限下的最佳有理數上下界」。
3. 後來也用於缺乏額外網格結構時的通用 refinement，例如：
   - 不依賴浮點網格；
   - 不依賴十進位網格；
   - 直接由結構化區間產生下一個測試點。
4. 選擇 Farey / Stern–Brocot 型測試點的原因包括：
   - 計算只需整數加法，公式簡單；
   - 分母膨脹相對受控；
   - 對記憶體占用較友善；
   - 與 `rational_bound()`、`_regularize()`、`refine_to_width()` 的設計完全相容。

> 備註：當物件已 exact-rationalized 時，`_left_rational == _right_rational`，此時區間退化為單點，不再談「兩端點是 Farey 鄰居」。因此「Farey 鄰居」應理解為**區間態**下的 structural interval 不變量。

---

## 4.4 物件不變量

### RE-INV-1：可能性旗標不可矛盾

任何已建立完成的 `RealNumber` 都必須滿足：

- `(_is_possible_rational, _is_possible_irrational) != (False, False)`。

---

### RE-INV-2：若已排除 irrational，則物件必為 exact rational state

若 `_is_possible_irrational == False`，則必有：

- `_exact_rational is not None`
- `_nearest_left == _nearest_right == _exact_rational`
- `_left_rational == _right_rational == _exact_rational`
- `_left_answer == _right_answer == 0`
- `_is_regular == True`

亦即一旦 oracle 命中 `0`，物件就會塌縮成 exact rational 單點狀態。

---

### RE-INV-3：動態區間永遠夾住真值

在任何已完成的狀態下，必有：

- `_nearest_left <= x <= _nearest_right`

若尚未 exact rationalize，通常是嚴格夾逼；若已 exact rationalize，則退化為等號。

---

### RE-INV-4：結構化區間包住動態區間

在正常狀態轉移下，維持：

- `_left_rational <= _nearest_left <= x <= _nearest_right <= _right_rational`

也就是說：

- dynamic interval 是目前查詢累積出的最新內層知識；
- structural interval 是規整化後的外層知識。

---

### RE-INV-5：初始化完成後，`_floor` / `_ceil` 是真值的真正 `floor` / `ceil`

`_int_bound_for_init()` 的責任不是只給粗略整數外框，而是：

- 若真值恰為整數，初始化期間就直接打中並 rationalize；
- 否則留下真正相鄰的整數 `floor(x), ceil(x)`。

因此初始化完成後：

- `_floor == floor(x)`
- `_ceil == ceil(x)`

---

### RE-INV-6：初始化完成後，只要尚未塌縮為 exact rational，就不可能是整數

因為整數情況會在 `_int_bound_for_init()` 階段被精確辨識；所以對已完成初始化但仍處於區間態的物件：

- 它不是整數；
- 特別地，若仍保有 `_is_possible_irrational == True`，則 `bool(self)` 可以直接判定為 `True`，因為此時它不可能是 `0`。

---

### RE-INV-7：區間態下，結構化區間兩端點是 Farey 鄰居

在物件尚未 exact-rationalized 時，`_left_rational` 與 `_right_rational` 維持為 Farey / Stern–Brocot 鄰居。這提供：

- 以 mediant `(a+c)/(b+d)` 產生下一個 canonical 測試點；
- 用 `1 / (b d)` 直接表示 structural interval width；
- 快速實作 `rational_bound(max_denominator)` 與 `_regularize()` 的 bulk step。

---

### RE-INV-8：`_is_regular` 只表示「同步程度」，不表示「區間是否合法」

- `_is_regular == True`：表示 structural interval 已同步到最新動態知識；
- `_is_regular == False`：表示 structural interval 可能比 dynamic interval 鬆，但仍為合法 outer interval。

---

### RE-INV-9：輸出快取不需因 refinement 失效

以下欄位都屬於「同一真值的輸出／快取資訊」：

- `_exponent_10`
- `_float_bound`
- `_hash`

由於 refinement 不改變真值本身，只改變已知資訊，因此這些欄位一般不需因更深 refinement 而主動失效。

---

## 4.5 內部核心方法契約

### `_wrapper_for_sign_function(sign_function)`

**責任**
- 將裸 sign function 升級成會更新內部狀態的 oracle。

**效果**
- 對落在已知區間外的查詢直接回傳；
- 對新查詢：
  - 若落在左側，更新 `_nearest_left`；
  - 若落在右側，更新 `_nearest_right`；
  - 若打中真值，呼叫 `_rationalized()`；
- 若 `input_is_regular == True`，同步更新 structural endpoint；
- 否則只會把 `_is_regular` 設為 `False`。

---

### `_rationalized(rational)`

**前置條件**
- 物件仍允許 rational possibility。

**後置條件**
- 將物件轉換成 exact rational state；
- 所有區間端點塌縮成同一個 rational；
- `_is_possible_irrational = False`；
- `_is_regular = True`。

---

### `_regularize()`

**責任**
- 用目前 dynamic interval `[_nearest_left, _nearest_right]` 修復 structural interval。

**輸入假設**
- structural interval 與 dynamic interval 都仍包住真值；
- 但 structural interval 可能落後於 dynamic interval。

**後置條件**
- `_is_regular = True`；
- structural interval 重新成為與 dynamic interval 一致的 Farey-鄰居區間；
- 仍保持 `_left_rational <= _nearest_left <= x <= _nearest_right <= _right_rational`。

**實作原則**
- 以 mediant `(a+c)/(b+d)` 判斷當前結構區間是否已與 dynamic interval 對齊；
- 若 mediant 仍落在 dynamic 左界左側，則用整數 quotient 做 `push_left()`；
- 若 mediant 落在 dynamic 右界右側，則做 `push_right()`；
- 每次不是只推一步，而是做 Euclidean-style bulk move，以減少 query-free 結構修復的成本。

---

## 4.6 公開 API 契約

### 建構子 `ComputableReal(...)`

支援兩類輸入：

#### A. exact rational / rational-like 輸入

**後置條件**
- 直接建立 rational-only 物件；
- `_is_possible_rational = True`
- `_is_possible_irrational = False`
- `dynamic interval == structural interval == exact rational`

#### B. sign function 輸入

**參數**
- `sign_function`
- `is_possible_rational`
- `is_possible_irrational`
- `left`, `right`（可選初始有理端點提示）

**前置條件**
- 兩個可能性旗標不能同時為 `False`；
- 若給 `left/right`，需與真值相容，且端點須有限或可轉為無界提示。

**後置條件**
- 建立動態查詢區間與結構化區間；
- `_floor`, `_ceil` 被初始化為真正的整數夾逼界；
- 若初始化期間已命中 exact rational，則會直接塌縮成 rational state。

---

### `sign_func(*args) -> CompareResult`

**前置條件**
- 參數必須可解析為有限 rational-like 值。

**後置條件**
- 回傳 `-1 / 0 / 1`，意義遵守 sign oracle 契約；
- 本呼叫可能更新 `_nearest_left` / `_nearest_right`，甚至觸發 rationalization。

---

### `current_bound(depend_on_structure=False) -> tuple[Q, Q]`

**後置條件**
- `depend_on_structure=False`：回傳 dynamic interval；
- `depend_on_structure=True`：回傳 structural interval。

**保證**
- 兩種回傳都應包住真值；
- structural interval 可能比 dynamic interval 鬆。

---

### `current_width(depend_on_structure=False) -> Q`

**後置條件**
- `False`：回傳 dynamic interval width；
- `True`：
  - 若已 exact rationalized，回傳 `0`；
  - 否則回傳 structural width。

**說明**
- 在區間態下，structural width 使用 Farey-鄰居公式 `1/(b d)`。

---

### `refine_to_width(epsilon)`

**前置條件**
- `epsilon` 必須是正的有限有理數。

**後置條件**
- 完成後 structural interval width `<= epsilon`；
- 若過程中命中 exact rational，物件可直接塌縮；
- 本方法先呼叫 `_regularize()`，再沿 mediant 路徑細化。

**重要性質**
- 它保證的是 structural width，而不是十進位位數。

---

### `rational_bound(max_denominator)`

**前置條件**
- `max_denominator` 必須是正整數。

**後置條件**
- 回傳 `(L, R)`，保證 `L <= x <= R`；
- `L.denominator <= max_denominator` 且 `R.denominator <= max_denominator`；
- 若值已 exact rational 且分母已足夠小，可回傳 point interval；
- 若尚在區間態，則以 structural interval 為基礎搜尋分母受限下的最佳夾逼界。

**設計重點**
- 此方法是 structural interval 設計的主要受益者之一；
- Farey-鄰居結構使得 denominator-bounded search 可用簡單整數運算快速完成。

---

### `as_integer_ratio(fallback_max_denominator=None)`

#### 無 fallback 時

**前置條件**
- 物件必須已知為 exact rational。

**失敗條件**
- 若已知為 exactly irrational，拋出 `ValueError`；
- 若尚未判定到 rational，亦拋出 `ValueError`。

#### 有 fallback 時

**前置條件**
- `fallback_max_denominator` 必須為正整數。

**後置條件**
- 若已 exact rational，回傳 exact ratio；
- 否則以 `rational_bound(fallback_max_denominator)` 給出分母受限下的單一 rational fallback，並用一次中點比較決定選左界或右界。

---

### `to_scientific_notation(precision=17) -> str`

**前置條件**
- `precision` 必須是非負整數。

**後置條件**
- 對 exact rational 值，委派給 `RationalNumber.to_scientific_notation()`；
- 對區間態，透過 sign oracle、整數級夾逼、以及十進尺度搜尋建立保證一致的科學記號輸出；
- 可快取 `_exponent_10`。

**說明**
- 這個 API 的目標是「語意安全的十進輸出」，不是傳統顯示層的最近值格式化。

---

### `float_bound() -> tuple[float, float]`

**後置條件**
- 回傳一對 Python `float`，保證真值落於其中；
- 若能精確命中單一 float，回傳 point interval；
- 可快取 `_float_bound`。

**說明**
- 對區間態，它直接在 dyadic / IEEE-754 格點上搜尋相鄰包圍浮點，而不是先做十進位展開再轉 float。

---

### `__float__() -> float`

**後置條件**
- 若 `float_bound()` 已為 point interval，直接回傳；
- 否則在安全 enclosure 上做一次中點比較，從左右相鄰 float 中選出單一代表值。

**注意**
- `float(self)` 是單一近似值；若在乎保證，應優先使用 `float_bound()`。

---

### `keep_away_from_zero()`

**用途**
- 為 division 前的 denominator-side safety 做準備。

**後置條件**
- 若值已 exact rational 且非 0，可能無需動作；
- 若值為 0，拋出錯誤；
- 若值仍在區間態且目前整數級夾逼碰觸 0，則 refine 到可明確遠離 0 的程度。

---

### `compare(other) -> Literal[-1, 0, 1]`

**回傳語意**
- `1`：`self < other`
- `0`：`self == other`
- `-1`：`self > other`

> 注意：這與傳統 `cmp` 慣例相反；rich comparison 會再把它轉回 Python 常見語意。

**行為**
- 先嘗試用當前動態區間直接分離；
- 若無法分離，則 regularize 雙方，並利用較窄 structural interval 幫另一方同步知識；
- 最後必要時沿共同 mediant 路徑做同步 refinement。

---

### `root_finding(func, interval)`

**前置條件（呼叫者責任）**
- `func` 連續；
- 輸入有限 rational interval 中恰有一根；
- 區間端點函數值異號；
- `func` 接受 `(numerator, denominator)` 並回傳 real-like 值。

**後置條件**
- 若端點本身即為根，直接回傳 exact rational 狀態；
- 否則建立新的 `RealNumber` 作為根節點，其 sign oracle 由 `func` 所誘導。

---

## 4.7 雜湊與快取契約

### `RealNumber.__hash__()`

**前置條件**
- 類別屬性 `set_max_denominator_for_hash` 必須先被設定；
- 且這個設定只能指定一次。

**後置條件**
- 雜湊會盡量與小分母 rational 的 hash 相容；
- 內部藉由 `rational_bound(max_denominator)` 與中點比較決定採左界或右界；
- 一旦 `_hash` 被設定，即可重複重用。

---

## 5. 交互設計摘要

## 5.1 `RealNumber` 為何依賴 `RationalNumber`

`RealNumber` 的所有 refinement、比較、顯示與哈希，最後都依賴 `RationalNumber` 提供：

- 精確 ratio 表示；
- 可共享的 frozen 小物件；
- 分母受限近似；
- 特殊值一致處理。

## 5.2 為何 structural interval 不直接等於 dynamic interval

因為 dynamic interval 來自任意查詢歷史，不一定適合：

- denominator-bounded best bounds 搜尋；
- 產生下一個 canonical 測試點；
- 在沒有浮點／十進網格可用時做 refinement；
- 控制分母膨脹與記憶體占用。

因此系統刻意把「我最新知道什麼」和「我用什麼幾何結構來做後續演算法」分成兩層。

---

## 6. 已知語意特徵與實作風格提醒

1. `RationalNumber` 容許 mutable 副本暫時攜帶有效 hash；不要假設「有 hash 就一定 frozen」。  
2. `RealNumber.compare()` 的符號慣例與傳統 `cmp` 相反：`1` 表示 `<`，`-1` 表示 `>`。  
3. `RealNumber.__pos__()` 回傳 `self`，不是副本；因此它保留同一個 refinement 狀態。  
4. `RealNumber` 的快取欄位通常不需失效，因為 refinement 改的是知識，不是真值。  
5. Structural interval 的存在是演算法層設計，不只是狀態冗餘。

---

## 7. 文件結語

- `RationalNumber` 是 exact rational engine + canonical cache node；
- `RealNumber` 是 sign-oracle-driven computable real runtime node。

`RationalNumber` 的可變 / 凍結的雙態設計，是有理數類別同時兼顧：

- 中間運算效率、
- canonical identity 與雜湊一致性、
- 全域快取共享、
- 以及記憶體配置控制

的關鍵。

`RealNumber` 的動態查詢區間 / 結構化區間的雙層設計，是實數類別同時兼顧：

- 正確性、
- 漸進 refinement、
- 分母受限近似、
- 以及記憶體控制

的關鍵。
