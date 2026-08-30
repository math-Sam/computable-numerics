# Computable 文件集

這是一套從數學基礎、公開語意、程式架構、實作順序到測試契約彼此對齊的 exact numerical runtime 設計文件。

專案的核心不是「把浮點數做得更精準」，而是建立一套能明確區分下列六件事的數值系統：

1. 數學值本身（mathematical denotation）；
2. 當前 finite representation；
3. 對該值已經取得的 certified knowledge；
4. 為回答某個問題而進行中的 computation / process state；
5. 使用者要求的答案解析度；
6. 使用者願意投入的有限工作量。

五個 public numeric classes 固定為：

```text
Rational
GaussianRational
Algebraic
ComputableReal
ComputableComplex
```

其數學值域分別為

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
\mathbb Q(i)=\{a+bi:a,b\in\mathbb Q\}
$$

同時是最輕量的 exact complex field，以及複平面搜尋、定位、矩形 subdivision 與 root-isolation 演算法的標準 exact probe domain。

它們不是五種 precision，而是五種不同的 computational regime。

此外，v1 另提供 public immutable exact auxiliary algebraic type：

```text
Polynomial
```

其 mathematical denotation 位於 $\mathbb Z[X]$。`Polynomial` 是可由 library 使用者直接操作的 public exact algebraic object，也是 `Algebraic` factorization / resultant / root-isolation machinery 的共同 kernel；但它不是第六個 scalar numeric regime，因為它表示 polynomial 而不是一個 scalar number。

---

# 1. 文件清單

## `00_README.md`

本文件。提供：

- 文件地圖；
- 權威順序；
- 建議閱讀路徑；
- 專案最重要的不變量與術語。

## `01_CORE_GOALS_AND_THEORETICAL_FRAMEWORK.md`

Runtime 導向的理論總覽。回答：

- 專案要解決什麼問題；
- 為什麼需要五個 public numeric classes；
- exact realization 與 semantic realization 對 runtime 的意義；
- 為什麼一般可計算數的不可判定性必須顯示在 computation time；
- 為什麼 resolution budget 與 work budget 必須分離；
- 為什麼一般可計算數需要 explicit computation graph，而 `Rational` / `GaussianRational` / `Algebraic` 不需要預設成圖節點；
- locally finite grid sets、searchable computably embedded exact ordered grid realizations，以及 finite grid-point embedding如何自動導出 target-grid comparison / midpoint probes；
- 五個 grid termination theorems 如何形成兩組 fixed-shape pair（near-adjacent / off-grid adjacent enclosure；near-nearest / no-midpoint strict-nearest projection）與最後的 mixed optimal theorem；
- 為什麼 v1 只凍結已有 termination theorem 支撐的 enclosure / grid observation，而 correctly-rounded、unconditional fixed-output strict-nearest 或 hard-threshold boundary-sensitive projection 仍需額外 termination contract。

形式化的 `Code`、machine、computability 與 realization 定義不在本文件重建，而以 `06_MATHEMATICAL_FOUNDATIONS.md` 為準。

## `02_SEMANTIC_SPECIFICATION.md`

**最高權威的 public runtime semantic specification。**

固定：

- 五個 public classes 的 mathematical domain；
- denotation immutability 與 representational interior mutability；
- `Rational` mutable-working / frozen-interned lifecycle；
- `GaussianRational` 的 $\mathbb Q(i)$ exact field semantics、canonical rational-coordinate representation 與 complex-probe role；
- public exact `Polynomial` type over $\mathbb Z[X]$，包含 finite arithmetic、factorization、resultant、Sturm 與 exact root-query contracts；
- `Algebraic` polynomial + rational closed isolating rectangle；
- `DecisionProcess` 的 `advance(...)` / `resolve()` termination boundary；
- `Relation`、`relation_process(...)` 與 mathematical-domain `membership_process(...)`；
- work budget；
- resolution budget；
- persistent certified knowledge、geometry-first compaction、residual semantics 與 recoverable floor；
- `assume_relation(...)`、`assume_membership(...)`、`assume_grid_membership(...)` 三類 trust-user assertions；
- `try_as(...)`、`downgrade()`、`downgrade_process()`、`upgrade(...)` regime transition；
- ordinary partial-operation API 與 explicit `*_process` API；
- Python dunder safety；
- downgrade-first promotion / conversion；
- `ComputableReal` / `ComputableComplex` 的 guaranteed-finite enclosure/grid observations、core semantic processes 與 partial-operation process boundary。

若 Python implementation 與本文件衝突，原則上視為 implementation bug。

## `03_ARCHITECTURE_AND_PUBLIC_API.md`

將 `02` 的語意映射到軟體架構。固定：

- package / module boundaries；
- promotion registry；
- `DecisionProcess` runtime；
- certificate / knowledge-store architecture；
- `Rational` weak interning；
- `GaussianRational` exact complex leaf / probe representation；
- `Algebraic` lazy representational refinement；
- `ComputableReal` / `ComputableComplex` computation DAG；
- weak hash-consing 與 canonical structural identity；
- graph flattening；
- persistent knowledge sharing、recoverable-floor propagation；
- query-local evaluation memo；
- source adapters；
- grid / exact binary-format helper interfaces；
- thread-safety boundary。

## `04_IMPLEMENTATION_ROADMAP.md`

程式實作順序。每個 phase 指定：

- dependency；
- required implementation；
- tests；
- benchmark（若為 hot path）；
- completion criteria。

Roadmap 只決定「先做什麼」，不能修改 public semantics 或 formal mathematics。

## `05_TEST_AND_BENCHMARK_SPEC.md`

Correctness contract 的一部分。涵蓋：

- exact-value correctness；
- semantic termination behavior；
- finite-work guarantees；
- persistent-knowledge monotonicity；
- relation / membership / grid trust assertions、geometry absorption、residual semantics、recoverable floor 與 contradiction handling；
- Algebraic lazy canonicalization / hash stability；
- Theorem 1 / 3 / 5 三個 public grid observation contracts，以及 Theorem 2 / 4 的 promised optimal strengthenings；
- DAG normalization / weak interning；
- graph depth / memory behavior；
- no-float correctness audit；
- Python protocol safety。

## `06_MATHEMATICAL_FOUNDATIONS.md`

**形式數學定義與定理的最高權威。**

它從 ZFC 中的

$$
\mathrm{Code}:=2^{<\omega}
$$

開始，依序建立：

- finite binary code；
- prefix-free coding；
- type-expression syntax 與 first-class typed values；
- first-class `Type`、`Program`、`Configuration`；
- Code-register machine；
- program execution；
- partial computable functions；
- cooperative finite-step computation；
- interpretation；
- semantic / exact / normal / perfect realization；
- existence-collapse theorem；
- computable-real semantic comparison；
- locally finite grid sets、searchable representations、exact ordered grid realizations與 finite-point computable-real embedding；
- computable-real presentation、grid embedding所導出的 uniform target-grid resumable comparability與 arbitrary finite-pair midpoint probes；
- 五個 localization/projection termination theorems：次佳包圍、off-grid 最佳包圍、次佳投影、no-midpoint 最佳投影、mixed optimal output；
- boundary-sensitive finite-output selection 為何不應在缺乏 termination theorem 時進入 v1 frozen surface。

本文件的目的是讓「algorithm」「terminating」「resumable process」「computable real」最後都能沿定義鏈追溯回 `Code` 與有限 machine transitions，而不把 algorithm 當作未定義的 meta-level primitive。

## `07_REFERENCE_IMPLEMENTATION_NOTES.md`

**Non-normative engineering companion。**

集中整理 reference module `Computable_v6.py` 中仍值得重用或再次驗證的：

- `Rational` lazy reduction / freeze / interning 技巧；
- `WeakValueDictionary` canonical sharing；
- $\pi$、$e$ 的 exact rational-comparator construction；
- bounded-denominator / continued-fraction / Farey 類演算法；
- `simplest_rational_in_interval`；
- integer Newton `iroot`；
- bulk rational arithmetic；
- arithmetic-operation common scaffolding；
- interval / comparator progress caching。

本文件不是 public semantics、formal mathematics 或 architecture 的權威來源。任何參考程式碼都必須先依 `02`、`03`、`06` 的 contract 再次驗證與改寫。

---

# 2. 文件權威順序

不同文件處理不同層次，因此不使用單一線性順位處理所有衝突。

## 2.1 Formal mathematics

若衝突涉及：

- `Code`；
- formal machine；
- computability；
- interpretation；
- realization；
- formal theorem；

則以：

1. `06_MATHEMATICAL_FOUNDATIONS.md`
2. `01_CORE_GOALS_AND_THEORETICAL_FRAMEWORK.md`

為準。

## 2.2 Public runtime semantics

若衝突涉及：

- public classes；
- method behavior；
- exceptions；
- termination contract；
- Python protocol；
- certificate behavior；
- promotion；

則以：

1. `02_SEMANTIC_SPECIFICATION.md`
2. `01_CORE_GOALS_AND_THEORETICAL_FRAMEWORK.md`
3. `03_ARCHITECTURE_AND_PUBLIC_API.md`

為準。

## 2.3 Engineering execution

架構與實作順序依序以：

1. `03_ARCHITECTURE_AND_PUBLIC_API.md`
2. `05_TEST_AND_BENCHMARK_SPEC.md`
3. `04_IMPLEMENTATION_ROADMAP.md`

為準，但它們不得反向修改 `02` 或 `06`。

`07_REFERENCE_IMPLEMENTATION_NOTES.md` 僅提供 implementation reference，不參與任何規格衝突的權威排序。

---

# 3. 建議閱讀路徑

## Runtime / implementation reader

```text
00 → 01 → 02 → 03 → 04 → 05
                 ↘ 06（需要 formal justification 時）
                 ↘ 07（需要 reference implementation ideas 時）
```

## Mathematical foundations reader

```text
00 → 06 → 01 → 02
```

## Test / review reader

```text
00 → 02 → 05 → 03 → 04
```

---

# 4. 一句話描述系統

`Computable` 是建立在 arbitrary-precision integer arithmetic 與 finite effective computation 上的 exact numerical runtime；它把 guaranteed-finite exact computation、guaranteed-finite certified observation、potentially divergent semantic decision，以及 lazy persistent knowledge 明確分離。

---

# 5. 最重要的設計原則

1. **Mathematical denotation 優先。** Public numeric object 代表的數學值一旦固定，不因後續 refinement、canonicalization 或 cache 調整而改變。
2. **Semantic immutability 不等於所有欄位 bitwise immutable。** `Algebraic` 的 defining polynomial / isolator、一般可計算數的 certified knowledge 都可在不改變 denotation 的前提下 lazy 改善。
3. **`Rational` 是唯一允許 working-value mutation 的 public numeric class。** Public constructor 使用 recursive `RationalInput`：可 exact 接受所有具 guaranteed-finite rational-valued recognizer 的 numeric values（包括 `Rational`、Python `int/bool`、`fractions.Fraction`、finite `float`、real finite `complex`、real `GaussianRational`、rational-valued `Algebraic`）、明確 grammar 的 `str`，以及由這些輸入遞迴組成的二元 tuple ratio；一旦被其他 persistent numeric structure 引用，必須先 `intern()` 成 frozen canonical value。
4. **`GaussianRational` 是 semantic-immutable 的 exact complex field。** 其 canonical payload 是兩個 frozen / interned `Rational` coordinates；它同時作為複平面的 canonical exact probe domain。
5. **Exactness 是 computational capability，不是 precision level。**
6. **Potential divergence 必須在 API syntax 上可見。** Ordinary operators / dunders 不得暗中執行可能永不停止的 semantic computation。
7. **Partial mathematical operation 的 domain 是 mathematical promise；domain membership 不等於 domain decidability。** Runtime 對 arbitrary user input另外以 knowledge / certificate-gated ordinary API 與 explicit `*_process` API 處理。
8. **Resolution budget 與 work budget 永遠分離。** `width`、`max_denominator` 描述答案品質；`work` 描述 process 目前最多推進多少 cooperative finite transitions。Finite resolution request 本身不保證任意 single-value selection feasibility 可有限決定；只有具 termination theorem 的 observation 才能 unconditional guaranteed-finite。v1 的 `grid_project()` 是其中一個特例：它由 near-nearest theorem 保證 finite，但不宣稱 correctly-rounded / strict-nearest。
9. **`Pending` 不是 False。** 它只表示問題目前尚未 resolve。
10. **Persistent knowledge 可存在於 native 或 derived computable nodes。** Knowledge 在語意上只增不減，但可做 lossless / dominance-based compaction。
11. **User assertion 採 trust-user principle。** Public assertion 分成 `assume_relation(...)`、`assume_membership(...)`、`assume_grid_membership(...)`。不含 equality cell 的 strict / inequality relation 在真 promise 下必於返回前被幾何 separation完整吸收；numeric-domain membership一般保存 residual semantics；grid-membership True 必辨識 exact grid point，False 必細化到 grid gap。
12. **錯誤 assertion 不享有 termination guarantee。** 若 assertion 已與現有 knowledge 形成有限可辨認矛盾，立即 raise `InconsistentKnowledgeError`；否則 strict / disconnected assertions 可能因使用者承諾為假而永不返回。
13. **Persistent knowledge 採 geometry-first + residual semantics。** Real 以 strongest useful certified interval、complex 以 strongest useful certified rectangle為主要 carrier；可有限恢復的較低 numeric representation保存為 recoverable floor。只有 geometry / floor 無法完整蘊含的 semantic content 才保留 residual knowledge。
14. **可有限發現的 knowledge contradiction 必須立即拒絕。** Persistent knowledge store 不允許在已知矛盾下完成 commit。
15. **可有限決定不等於應 eager 決定。** `Algebraic.is_real()`、minimal polynomial、canonical root index 等只在真正需要時求值。
16. **General complex real-domain membership is explicit semantic state.** Real `compare_process` 不會在收到尚未 certified-real 的 general `ComputableComplex` 時偷偷啟動 domain 判斷。推薦先建立 / 推進 `z.membership_process(ComputableReal)`；只有 resolve `True` 後再進行 real ordering，若 `Pending` 就保留並繼續推進該 process。End-user guide 必明確強調這個最佳實踐。
17. **Minimal Sufficient Knowledge Principle。** Runtime 應以當前 query 為中心，只取得足以滿足當前 contract 的 certified information；這是一條 demand-driven 設計原則，不要求求解昂貴的全域最優 precision allocation。
18. **Evaluation 是雙向資訊流。** Downstream query 向 upstream 傳播 resolution / proof obligations；upstream source 與 intermediate nodes 再向 downstream 提交 certified knowledge；一旦 target contract 已滿足即停止。
19. **Safe Forgetting Principle。** 只有當一段 computation history 的 semantic content 已被另一個 exact、可繼續支援未來 public contracts 的 representation 完整取代時，才能安全丟棄該 history。Finite approximation / enclosure 本身不能取代 general computable value 的 algorithmic denotation。
20. **Computation DAG 的預設作用域只有 `ComputableReal` / `ComputableComplex`。** `Rational`、`GaussianRational` 與 `Algebraic` 是 finite exact values；只有在 lift 進一般可計算運算鏈時才成為 DAG leaf payload。
21. **DAG 是對 semantic realization 不可避免的引用鏈做控制與利用，不是 universal symbolic representation。**
22. **DAG structural identity 永遠不得依賴一般 semantic numerical equality。**
23. **Structurally identical computable DAG nodes weak-intern。** Canonical structure 相同的 live nodes 共享 object 與 persistent knowledge。
24. **Exact subgraph 能安全 collapse 就應 collapse。** Rational / Gaussian-rational / algebraic exact results 可以取代已被完整涵蓋的 expression history；general semantic subgraph 只能在存在 semantics-preserving compiled source、recoverable lower-regime representation或其他 exact algorithmic replacement 時壓縮。
25. **Python `float` / `complex` 只作 finite exact classes 的 terminal projection / interoperability formats，以及 `Binary64Grid` 的 public point/endpoint container；不作 correctness substrate。** Exact classes 的 projection跟 Python `int` / `Fraction` exact-number overflow規則走，超出 finite-output boundary finite `OverflowError`。General semantic classes仍不把 `float(x)` / `complex(x)` 當作 correctly-rounded machine projection；binary64 語意觀察由 `Binary64Grid` 的 `grid_bound()` / `grid_localize()` / `grid_project()` 承擔，其中 bracket endpoint 可為真正的 Python `±inf`，strict-nearest channel與 near-nearest projection point對 finite target都必為 finite。
26. **General semantic classes 不使用 Python truthiness / rich equality / hash 偷渡 semantic decision。** `bool`、rich comparison、hash 等 protocol 依 `02` 明確 finite raise 或 unavailable。
27. **本規格不提供 thread-safety guarantee。** Shared mutable knowledge / process state 的 concurrent access 需 external synchronization。
28. **Grid mathematics 與 grid representation 分層。** `locally finite` 是 underlying set 的純數學性質；v1 built-in grids 採 searchable **computably embedded exact ordered grid realization**：grid-point order/equality finite exact，且每個 finite grid code都能由 terminating algorithm嵌入同值 computable-real presentation。Target-grid resumable comparison與任意 finite grid-point pair的 midpoint probes因此是 embedding 的推論，而不是每個 theorem 重複增加的 ad hoc hypotheses。
29. **Grid localization 的五定理結構固定為「兩組成對 + 一個混合」。** Theorems 1 / 2 處理 enclosure：unconditional near-adjacent 與 off-grid promised adjacent；Theorems 3 / 4 處理 projection：unconditional near-nearest 與 no-midpoint promised strict-nearest；Theorem 5 最後 fair-dovetail 兩種 optimal search。其核心幾何事實是 finite grid-hit obstruction $G_{\mathrm{fin}}$ 與 adjacent-midpoint obstruction $M_G$ 不相交，所以最佳包圍與最佳投影的障礙不會同時發生；因此 mixed output 至少有一個 optimal channel guaranteed-finite。
30. **v1 scope 以 termination semantics 為主要節制標準，不以功能數量為目標。** Guaranteed-finite exact operations / conversions / Python convenience protocols 可以在第一版保留；真正應延後的是非核心、又需要額外 potentially-divergent boundary contract 的 API。
31. **Numeric regime transition 先降後升。** `downgrade()` 只使用目前 guaranteed-finite 可恢復資訊；`downgrade_process()` 明示承擔可能不停止的 semantic search；`upgrade(T)` 先 `downgrade()` 再 legal finite lift，並保存足以回復 pre-upgrade floor 的資訊。Ordinary promotion共用此 downgrade-first原則，但不啟動 process。
32. **Numeric coercion 以 guaranteed-finite exact embedding / subdomain recognition 與 mathematical-domain membership 為準，不以來源型別硬編碼。** 只要來源本身是 numeric value object，而且 runtime 能 guaranteed-finite、exact 地認出其 mathematical value 是否落在 operation 所需子域，就依值接受或拒絕；這同樣適用於 scalar operands、integer powers、rounding digits、derivative order、work budget、grid integer parameters、integer-polynomial coefficients等 numeric positions。General `ComputableReal` / `ComputableComplex` 不因個別 instance 看似簡單就 hidden resolve integerhood/rationality；text / tuple ratio仍只是 explicit parsing syntax。

---

# 6. 五個數值制度的核心差異

| Class | Domain | Finite exact representation | General equality finite? | Default DAG node? | Hash | Additional role |
|---|---|---:|---:|---:|---:|---|
| `Rational` | $\mathbb Q$ | yes | yes | no | yes; first hash may normalize + freeze | exact real scalar / real probe |
| `GaussianRational` | $\mathbb Q(i)$ | yes | yes | no | yes | exact complex scalar / complex probe |
| `Algebraic` | $\overline{\mathbb Q}$ | yes | yes | no | yes, lazy canonical identity | finite exact algebraic closure |
| `ComputableReal` | $\mathbb R_C$ | finite algorithmic semantics | no | yes | unavailable | general algorithmic real |
| `ComputableComplex` | $\mathbb C_C$ | finite algorithmic semantics | no | yes | unavailable | general algorithmic complex |

---

# 7. Reference implementation policy

`Computable_v6.py` 是 implementation reference source，而不是本文件集的規格來源。可重用的演算法與工程技巧集中整理於 `07_REFERENCE_IMPLEMENTATION_NOTES.md`。

核心規則只有兩條：

1. reference code 可以提供 algorithmic idea、benchmark workload、optimization pattern 與 implementation caution；
2. 任何要進入正式 implementation 的內容，都必須先再次驗證是否符合 `02` 的 public semantics、`03` 的 architecture 與 `06` 的 formal mathematics。
