# Computable：核心目標與 Runtime 理論框架

本文件是數學基礎與工程規格之間的橋梁。形式化的 `Code`、machine、computability、interpretation 與 realization 定義以 `06_MATHEMATICAL_FOUNDATIONS.md` 為準；本文件只保留 runtime 設計真正需要的理論結論與直觀。

---

# 1. 專案目標

`Computable` 的目標是建立 **exact numerical runtime**。

它不是：

- arbitrary-precision floating-point package；
- interval arithmetic package 的別名；
- 完整 symbolic CAS；
- 以 timeout 猜測數學關係的 heuristic system。

核心要求是：

1. 數學值由 exact semantics 指定；
2. 可有限決定的 exact questions 提供 guaranteed-finite exact API；
3. 一般不保證有限決定的 exact questions 必須顯式暴露 potentially divergent computation；
4. 若使用者只要求有限解析度資訊，提供 guaranteed-finite certified observation；
5. approximation quality 與 computational effort 分開建模；
6. correctness 最終只依賴 finite exact data 與 finite effective computation。

---

# 2. 五個 public numeric regimes

系統固定提供：

$$
\boxed{
\texttt{Rational},\quad
\texttt{GaussianRational},\quad
\texttt{Algebraic},\quad
\texttt{ComputableReal},\quad
\texttt{ComputableComplex}
}
$$

它們不是 precision hierarchy，而是不同的 computational regimes。

## 2.1 `Rational`

數學值域為

$$
\mathbb Q.
$$

有限整數資料即可完整指定；field arithmetic、equality、order、rounding 等核心問題皆可有限 exact 決定。它是 runtime 的 exact real hot path，因此特別允許 mutable working state 與 lazy reduction；一旦需要 stable identity / persistent ownership，轉成 frozen canonical interned value。

## 2.2 `GaussianRational`

數學值域為

$$
\mathbb Q(i)=\{a+bi:a,b\in\mathbb Q\}.
$$

它是 finite exact complex field。Canonical representation 為一對 rational coordinates：

```python
(real: Rational, imag: Rational)
```

其中 components 在 persistent ownership 下必為 frozen / interned Rational。Field arithmetic、equality、zero、conjugation、realness 與 coordinate extraction 全部 finite exact。

`GaussianRational` 還具有第二個 architecture role：它是複平面的 canonical exact probe domain。Rational rectangles 的 corners、centers、binary-rational probe points / bounded-denominator product-grid points、polynomial boundary evaluation points與 complex localization probes 都可落在 $\mathbb Q(i)$ 中。

## 2.2.1 Public auxiliary exact type `Polynomial`

`Polynomial` 是 v1 public immutable exact algebraic type，mathematical domain 為

$$
\mathbb Z[X].
$$

它不列入五個 scalar numeric regimes，因為 polynomial 不是 scalar number；但它不是 internal-only implementation detail。使用者可以直接進行 guaranteed-finite integer-polynomial arithmetic、derivative、content / primitive part、pseudo/exact division、gcd、square-free decomposition、irreducible factorization、resultant、Sturm sequence，以及 exact real/complex distinct-root counting and isolation。

同一套 public exact polynomial kernel 也被 `Algebraic` construction、minimal-polynomial recovery、hash canonicalization 與 root-isolation geometry 重用。v1 不維護一套「public Polynomial algorithms」與另一套語意不同的 hidden Algebraic polynomial stack。

## 2.3 `Algebraic`

數學值域為

$$
\overline{\mathbb Q}
=
\left\{
\alpha\in\mathbb C:
\exists P\in\mathbb Z[X],\ \deg P\ge1,\ P(\alpha)=0
\right\}.
$$

`Algebraic` 仍是 finite exact representation。一般 representation 由：

- 一個非恆定整係數多項式；
- 一個唯一指定其中某個不同複根的有理閉矩形；

共同決定。

Equality、realness，以及實代數數的 ordering 都可有限決定。但「可有限決定」不表示 constructor 必須 eager 做完所有決定。Realness、minimal polynomial、canonical root index 都可 lazy 求值。

`GaussianRational` 是 `Algebraic` 的 cheap exact subfield，但保持獨立 public regime，因為它完全不需要 polynomial / root-isolation machinery，且同時承擔 complex probe role。

## 2.4 `ComputableReal`

數學值域記為

$$
\mathbb R_C.
$$

其 representation 是 finite algorithmic semantics，而不是一個有限 closed-form exact value record。對一般兩個不同的 computable reals，strict separation 最終可由有限 evidence 顯現；但 equality 一般不保證有限決定。

因此 runtime 必須同時提供：

- guaranteed-finite certified enclosures；
- explicit semantic processes。

## 2.5 `ComputableComplex`

數學值域記為

$$
\mathbb C_C.
$$

一般 equality 不保證有限決定；也沒有 natural total order。更重要的是，對 $z\in\mathbb C_C$，

$$
z\in\mathbb R
\iff
\operatorname{Im}z=0
$$

本身就是一般 computable-real equality problem，因此 realness 不可作為一般 `ComputableComplex` 的 guaranteed-finite property。

---

# 3. Public type boundaries 的理論理由

## 3.1 為什麼 `Algebraic` 不分 Real / Complex

對 algebraic number，realness 可由 finite algebraic algorithms 決定，因此 real / non-real 只是同一 exact domain 中的 property。

所以不設：

```text
AlgebraicReal
AlgebraicComplex
```

相反地，若把 `ComputableReal` 與 `ComputableComplex` 合併成一個 class，那麼「這個 object 能否使用 real ordering semantics」本身會變成一般不可保證有限決定的問題。

因此 public type boundary 必須保留：

```text
ComputableReal
ComputableComplex
```

型別本身即保存「值必為 real」這份 finite structural information。

## 3.2 為什麼 `GaussianRational` 值得獨立

雖然

$$
\mathbb Q(i)\subset\overline{\mathbb Q},
$$

但 $a+bi$ 的 exact identity 已由兩個 rationals 完整指定。若把 $1+2i$ 直接表示成 general `Algebraic`，就必須引入 annihilating polynomial 與 isolating rectangle，這在數學上正確、在 runtime cost model 上卻不必要。

此外 $\mathbb Q(i)$ 對四則運算封閉，且對複平面具有：

- dense exact probes；
- finite coordinate comparison；
- exact polynomial evaluation；
- rational-rectangle corner / center representation；
- binary-rational probe families / denominator-bounded product-grid representation。

因此 `GaussianRational` 不是任意抽出的 algebraic subfield，而是「最輕量 exact complex value」與「complex search probe」兩個角色重合的 computational regime。

---

# 4. `Code`、formal machine 與 realization

形式理論固定

$$
\mathrm{Code}:=2^{<\omega}.
$$

在 `06` 中，algorithm 由 Code-register machine 形式化，而不是停留在未定義的 meta-language notion。

理論鏈為：

$$
\mathrm{Code}
\longrightarrow
\text{typed codes}
\longrightarrow
\text{Program / Configuration}
\longrightarrow
\text{machine execution}
\longrightarrow
\text{partial computable functions}
\longrightarrow
\text{interpretation / realization}.
$$

這讓「finite termination」「resumable computation」「semantic realization」最後都能還原成 ZFC 中的有限物件與 transition relation。

---

# 5. Format domain 與 semantic domain

Interpretation 同時保存 format domain 與 semantic domain。

對 mathematical set $X$，有：

$$
D\subseteq F\subseteq\mathrm{Code},
$$

其中：

- $F$：format domain，表示格式上合法、可被 type/parser 接受的 codes；要求可判定；
- $D$：semantic domain，表示真正具有 $X$-denotation 的 codes；不要求一般可判定；
- interpretation：

$$
\llbracket\cdot\rrbracket:D\to X
$$

為 surjection。

因此：

$$
\text{well-formed code}
\neq
\text{semantically valid code}
\neq
\text{mathematical value}.
$$

這個區分對一般 semantic representations 非常重要。例如一個 program description 可以格式上完全合法，但不一定滿足「它真的表示一個 computable real」所需的語意 promise。

---

# 6. Semantic / Exact / Normal / Perfect realization

## 6.1 Semantic realization

Semantic realization 允許

$$
D\subsetneq F.
$$

對 primitive partial operation，realizer 只需在 mathematical domain 的 promised-valid input 上有限終止；不要求 domain membership 本身可決定。

對 primitive relation family，只要求除了至多一個 exceptional cell 外，其餘 cells 可被 finite semantic evidence 識別。

典型例子是：

$$
<,\ =,\ >
$$

其中 equality 是唯一可永久 unresolved 的 boundary。

## 6.2 Exact realization

Exact realization 具有兩個核心特色。

第一：

$$
\boxed{F=D.}
$$

也就是 every well-formed code is semantically valid。

第二：對每個 primitive partial operation，其 mathematical domain 在 representation codes 上的 preimage membership 必可有限判定；每個 primitive relation family 的所有 cells 都可有限分類。

也就是若 $f:A\subseteq X^d\to X$，exactness 要求能在 $F^d$ 上有限判斷代表的 mathematical tuple 是否落在 $A$。它不要求把 $A$ 本身額外賦予某種機器外的「decidable」結構。

所以 exactness 不只是「算出 exact result」，而是連 representation validity 與 primitive operation applicability 都具有 finite exact decision capability。

## 6.3 Bilateral interpretation

Bilateral 只描述 semantic representation uniqueness：

$$
\llbracket\cdot\rrbracket:D\to X
$$

為 bijection。

它**不**額外要求 $F=D$。

因此 exactness 與 bilaterality 是兩個正交概念。

## 6.4 Normal realization

Normal realization 是 exact realization，加上一個 terminating normalizer

$$
\Lambda:F\to F
$$

令

$$
A:=\Lambda(F),
$$

只要求：

$$
\llbracket\Lambda(a)\rrbracket=\llbracket a\rrbracket
$$

以及

$$
\left.\llbracket\cdot\rrbracket\right|_A
$$

為 injective。

其餘性質都應作為 theorem 推出，而不是塞入定義：

$$
\Lambda|_A=\operatorname{id}_A,
$$

$$
\Lambda\circ\Lambda=\Lambda,
$$

$$
A=\{a\in F:\Lambda(a)=a\},
$$

$A$ 可判定，而且 restriction 自動為 bijection。

## 6.5 Perfect realization

Perfect realization 定義為：

$$
\boxed{
\text{exact realization}
+
\text{bilateral interpretation}.
}
$$

所以：

$$
F=D
$$

且

$$
\llbracket\cdot\rrbracket:F\to X
$$

為 bijection。

---

# 7. Existence-collapse theorem

若某個 exact realization 的 semantic equality 可有限判定，即可決定

$$
\llbracket a\rrbracket=\llbracket b\rrbracket,
$$

則固定 `Code` 上一個 computable well-order，例如：

1. 先比 code length；
2. 同長度用 lexicographic order；

可以搜尋每個 value 的最早 representation，得到 terminating normalizer。

為避免把假設藏在術語裡，令：

> **equality-decidable exact-realizable** = 存在一個 exact realization，且其 semantic equality finite decidable。

則 existence level 的正確結論是：

$$
\boxed{
\text{equality-decidable exact-realizable}
\iff
\text{normal-realizable}
\iff
\text{perfect-realizable}.
}
$$

Normal realization 的 normalizer 本身就給 semantic equality decision：

$$
\llbracket a\rrbracket=\llbracket b\rrbracket
\iff
\Lambda(a)=\Lambda(b),
$$

而 perfect realization 更直接把 semantic equality 化成 canonical code equality。

因此不能在完全沒有額外假設時寫成

```text
exact-realizable iff normal-realizable iff perfect-realizable
```

因為一般 exact realization 的 semantic equality 未必已知 finite decidable。只有當 primitive binary relations 透過有限 union / intersection，更一般地 finite Boolean combination，可構造 diagonal

$$
\Delta_X:=\{(x,x):x\in X\},
$$

使 primitive classifiers 可導出 semantic equality decision 時，才可在該 class of structures 中把左側進一步簡寫成 `exact-realizable`，因為

$$
(x,y)\in\Delta_X\iff x=y.
$$

這個 theorem 只談 realization **存在性**，不表示三種 concrete representation organization 相同。

---

# 8. Potential divergence 必須在 API syntax 上顯示

對 semantic classes，最核心的工程律是：

$$
\boxed{
\text{Potential semantic divergence must always be explicit in the public API.}
}
$$

因此 ordinary numerical operator、dunder 與面向 arbitrary well-formed input 的普通 semantic method 只能：

- finite return；
- 或 finite raise。

唯一重要例外是明示的 trust-boundary assertion API，例如 `assume_*`。這些 operation 把 assertion 真實性當作 semantic precondition；若使用者違反承諾，runtime 不負責保證 termination。這不是把 semantic decision 偷藏在普通 operator 中，而是把「我承諾此命題為真」本身作為 public API contract 的一部分。

若某 exact semantic computation 可能永不完成，且不是上述 trust-boundary promised-input operation，必使用：

```python
*_process(...)
```

或 explicit：

```python
process.resolve()
```

不能有普通 operator 在內部偷偷 `.resolve()`。

---

# 9. Partial operation：數學 domain 與 runtime domain decision

對 partial mathematical operation

$$
f:A\subseteq X^d\to X,
$$

數學理論中的 realizer 只需要在輸入確實屬於 $A$ 時有限成功。

所以：

$$
\boxed{
\text{mathematical domain membership}
\neq
\text{effective domain-decision capability}.
}
$$

Runtime 面對 arbitrary user input 時採兩層 API：

## Ordinary API

v1 的核心例子是 division：

```python
x / y
```

`sqrt`、`log` 等其他 partial mathematical operations 若納入 public surface，沿用同一 policy；它們不屬第一版 frozen surface。

必有限完成：

- domain 已 certified：finite construct result；
- invalidity 已 finite known：raise mathematical exception；
- domain 目前 unresolved：raise `UnresolvedDomainError`。

## Explicit process API

第一版的 division process surface：

```python
divide_process(x, y)
```

倒數以 `divide_process(1, y)` 表達；reciprocal-specific evaluator / DAG node可作 internal primitive，但不形成第二個 public spelling。

建立 process 本身 finite；process 可投入任意有限 work，或 explicit `.resolve()`。

若 process 在有限工作中證明 mathematical domain illegal，立即 raise 對應 exception；不回傳假的 `Undefined` value。

---

# 10. Resolution budget 與 Work budget

## 10.1 Resolution budget

描述答案需要多細，例如：

$$
R-L\le\varepsilon
$$

或 bounded-denominator grid

$$
\operatorname{den}(L),\operatorname{den}(R)\le N.
$$

典型 API：

```python
x.bound(width=epsilon)
x.grid_bound(BoundedDenominatorGrid(max_denominator=N))
z.box(width=epsilon)
```

對 enclosure / grid localization 這類已有 termination theorem 支撐的合法 request，contract 可以要求 guaranteed finite termination。

但「resolution parameter 是有限的」本身**不**推出任意 single-value selection 一定可有限決定。例如要求找一個 binary64 $f$ 使 $|x-f|\le e$，其 feasibility 在 $\inf_f|x-f|=e$ 時又落到 exact equality boundary；因此不能只因輸出格式有限就宣稱 unconditional guaranteed-finite。第一版的 `grid_project(grid)` 並不違反此原則：它有獨立的 near-nearest termination theorem，contract 只要求至多一個 grid point 嚴格比輸出點更近；它不是 correctly-rounded、strict-nearest 或 hard-error-threshold machine projection。其他沒有 termination theorem 的 boundary-sensitive single-value selection仍不進 frozen surface。

## 10.2 Work budget

只描述 semantic process 目前最多推進多少 cooperative finite transitions：

```python
p.advance(work=N)
```

每個 transition 本身必 guaranteed finite，因此有限 $N$ 必 finite return / raise。`resolve()` 則是明示允許不終止的 unbounded resolution boundary；有限工作與無界 resolution 使用不同 spelling。

`Pending` 只表示：

> 這個 process 的最終問題目前尚未 resolve。

它不表示「沒有取得任何額外 knowledge」。

---

# 11. Persistent certified knowledge

一般可計算數的 object 可保存 persistent certified knowledge，包括 native 與 derived nodes。

Knowledge sources 分為：

1. kernel-verified；
2. trusted-source；
3. user-asserted；
4. derived。

Knowledge 必：

- sound relative to trust assumptions；
- monotone；
- 在可有限發現 contradiction 時立即拒絕 inconsistent commit。

Persistent representation 採 **geometry-first + residual semantics** 原則：`ComputableReal` 以 strongest useful certified rational interval、`ComputableComplex` 以 strongest useful certified rational rectangle為主要幾何 carrier；若 runtime 已能有限恢復較低 numeric regime，也保存 recoverable floor。任何 relation / membership fact 若已被 enclosure、rectangle 或 recoverable floor 完整蘊含，就不必另存平行 predicate；只有尚有獨立資訊量的 semantic content 才保留為 residual knowledge。

Trust-boundary assertions分三類：

```python
x.assume_relation(y, relation)
x.assume_membership(numeric_class, truth)
x.assume_grid_membership(grid, truth)
```

`assume_relation` 中不含 equality cell 的 `LESS` / `GREATER` / `NOT_EQUAL`，若 promise真實，runtime在返回前持續 refinement，直到 geometry 本身 strict-separate而完整吸收 assertion。含 equality cell 的 `EQUAL` / `LESS_EQUAL` / `GREATER_EQUAL` 則做所有可得的 enclosure propagation，但一般仍需保存 residual relation knowledge。

`assume_membership(numeric_class, truth)` 談 mathematical denotation 是否屬於 `Rational`、`GaussianRational`、`Algebraic`、`ComputableReal`、`ComputableComplex` 對應的數值域，不是 Python class identity。這種 abstract domain fact 一般不能只靠有限 enclosure / rectangle完整表示，所以允許 residual membership knowledge；domain inclusion所導出的 finite implications立即 propagation。

`assume_grid_membership(grid, True)` 比抽象的 rationality assertion更強。Standard grid locally finite且 searchable，因此在 membership promise 下，runtime可先取得 finite target enclosure，再把 bounded region內的 grid candidates有限分離；method必在返回前辨識唯一 exact grid point並 commit可恢復的 exact floor。對 `BoundedDenominatorGrid(N)`，這使「分母不超過 $N$ 的有理數」promise finite collapse成具體 `Rational`。`assume_grid_membership(grid, False)` 則在返回前 refine 到整個 certified interval落在 grid gap，讓 off-grid fact被 geometry完整吸收。

Assertion truth 是 promised precondition。若 assertion 為假而目前又沒有 finite contradiction evidence，任何依 promise才保證完成的 strict separation / grid identification / gap absorption都可以永遠不完成；runtime 不以 timeout、猜測或額外 classifier防禦錯誤 promise。若矛盾已可有限辨認，立即 reject。

Process 中途取得的可持久化 fact或較低 recoverable floor立即 commit，不必等 process resolve。因此 `Pending` 只代表最終問題尚未 resolve，不表示此次 finite work沒有帶來可重用資訊。

Semantic knowledge 永不遺失，但 implementation 可以做 lossless compaction。若更強 enclosure / rectangle / recoverable floor已蘊含某 relation或 membership fact，獨立 representation可移除；必要 provenance可壓縮成 summary。

# 12. Lazy computation principle

專案採：

$$
\boxed{
\text{finitely decidable does not imply eagerly decidable.}
}
$$

例如 `Algebraic.is_real()` 可 finite total，不代表 constructor 必先判定 realness。

同理：

- minimal polynomial；
- canonical root index；
- tighter isolating rectangle；
- stronger sign facts；

都只在真正需要時算。

Representation invariant 只應要求 exact identity / correctness 所必要的條件，不把所有可有限推出的 property 都變成 construction-time prerequisite。

---

# 13. Minimal sufficient knowledge、regime transition 與 safe forgetting

Runtime 的 performance philosophy 不只是 lazy evaluation，而是 **demand-driven certified evaluation**。

## 13.1 Regime recognition and conversion

Public regime transition分成四種不同問題：

```python
x.try_as(T)
x.downgrade()
x.downgrade_process()
x.upgrade(T)
```

`try_as(T)` 只允許 source-to-target 本身已有 guaranteed-finite exact recognition / reconstruction algorithm 的 pair；例如 `Algebraic.try_as(Rational)` / `Algebraic.try_as(GaussianRational)`。它不能把一般 rationality / algebraicity search藏進 ordinary call。

`downgrade()` guaranteed finite，只問「依目前 representation、persistent constructive evidence與 recoverable floor，現在最低能具體恢復到哪個 public regime？」它不追求 mathematical value 在抽象上可能屬於的最低 regime，所以 general computable object在沒有更強 evidence時可保持原 regime。

`downgrade_process()` 則明示允許不終止。它 fair-dovetail sound recognition / reconstruction strategies；任何較低 representation一旦取得就立即 commit並改善 recoverable floor。Process只有在目前 representation已能 finite確立為最低時才 resolve；即使 mathematical value真的更低，若相關 evidence無法有限發現，也可能永久 `Pending`。

`upgrade(T)` 對合法 target guaranteed finite，而且固定 **先 `downgrade()`，再 lift**。升階結果必保留足以 guaranteed-finite 回復 pre-upgrade downgrade result 的資訊。Ordinary arithmetic promotion採相同的 downgrade-first policy，但永遠不啟動 `downgrade_process()`。

這使 regime transition遵守一個重要原則：進入較一般 representation不應白白忘掉已知可恢復的較簡單 identity。

## 13.2 Minimal sufficient knowledge

對一個 final query，evaluation 應先檢查目前 persistent knowledge 是否已足以回答；若不足，再把 target requirement 反向分解成 upstream obligations，僅 refine 必要 sources / children，並把取得的 certified facts正向 commit回 graph。

理想資訊流為：

```text
final query
    ↓
required target contract
    ↑ backward obligations
upstream refinement
    ↓ certified facts
shared persistent knowledge
    ↓
query satisfied -> stop
```

這稱為 **Minimal Sufficient Knowledge Principle**：runtime 不應因「也許之後會用到」而主動取得與當前 contract 無關的 semantic facts 或過高 resolution。此原則不要求 evaluator 解一個昂貴的 global optimal-allocation problem；保守但可證正確的 obligation allocation 可以逐步 feedback refine。

## 13.3 Safe Forgetting Principle

> 只有當 history 所攜帶的 semantic content 已被另一個 exact 或 algorithmically equivalent、可支援未來 public contracts 的 representation 完整取代時，才能安全丟棄 history。

因此：

- Rational expression 可 collapse 成 `Rational`；
- Gaussian-rational expression 可 collapse 成 `GaussianRational`；
- algebraic expression 可 collapse 成 `Algebraic`；
- general computable subgraph 不能只因已有一個 finite interval / rectangle 就丟掉 algorithmic history；
- general subgraph 只有在被 semantics-equivalent compiled source、exact leaf、recoverable lower-regime representation或其他可 arbitrary-refine 的 finite algorithmic representation完整取代後，才可 graph-compaction。

因此真正的問題不是單純「eager 還是 lazy」，而是：**什麼資訊已足夠讓某段 history 可以安全失憶？**

# 14. Searchable grids 與 guaranteed-finite localization

Computable-real localization 的核心原則是：不要把 guaranteed-finite API 設計成必須辨認 exact grid hit 或 exact nearest-neighbor boundary。

形式理論將 grid 分成幾個不同層次：

1. `locally finite` 是 underlying set $G$ 的純數學性質；
2. **exact ordered grid realization** 要求 grid-point equality / order trichotomy finite exact；
3. **effective computable-real embedding** 要求存在 terminating algorithm，把每個 finite-valued grid code轉成代表同一數值的 computable-real presentation；
4. `searchable` 要求對 denotationally distinct endpoints 可 finite 判斷 open interval內是否有 grid point並給 witness。

v1 standard runtime grids 採 **searchable computably embedded exact ordered grid realization**。這個 embedding 是重要的橋樑：一旦 target representation 本身也可 finite 編譯成 computable-real presentation，target-vs-grid-point resumable comparison 就由共同 computable-real comparator 系統自動得到；任意兩個 finite grid points 的 midpoint 也能先在 computable-real system中 finite construct，再和 target 比較。因此 target-grid comparison 與 midpoint probe 不是 localization theorem 需要逐一額外列出的 ad hoc capabilities。

## 14.1 Localization Theorem 1 — unconditional near-adjacent enclosure

對 locally finite set $G\subseteq\overline{\mathbb R}$，若 grid representation searchable、computably embedded、order-level exact，且能對 target domain 提供 two-sided bounding，則存在 finite algorithm 回傳

$$
L,R\in G
$$

使

$$
L\le x\le R
$$

且

$$
\boxed{|G\cap(L,R)|\le1.}
$$

這是 exact-adjacent bracket 的「放寬一階」版本：exact grid-hit boundary 不需要被判定，output contract 以最多一個 interior grid point 吸收 ambiguity。

對 bounded-denominator grid

$$
G_N
=
\left\{
\frac pq\in\mathbb Q:
1\le q\le N,\ \gcd(|p|,q)=1
\right\},
$$

這直接成為

```python
x.grid_bound(BoundedDenominatorGrid(max_denominator=N))
```

的 finite semantic contract。

## 14.2 Localization Theorem 2 — off-grid promise restores optimal enclosure

若再有 semantic promise

$$
x\notin G,
$$

則 Theorem 1 的 near-adjacent bracket可 guaranteed-finite 升級成真正 adjacent bracket：

$$
L\le x\le R,
\qquad
G\cap(L,R)=\varnothing.
$$

原因很直接：Theorem 1 的 bracket 內至多只有一個 grid witness $g$；若真的有這個 witness，off-grid promise 保證 $x\ne g$，所以 $x\mathrel?g$ 一定是 strict comparison並 finite resolve，從而選出 $(L,g)$ 或 $(g,R)$ 的 adjacent half。

因此第一、第二定理形成 enclosure pair：

$$
\boxed{
\text{unconditional near-adjacent}
\quad\leftrightarrow\quad
\text{off-grid promised adjacent}.
}
$$

Theorem 2 是數學上的 promised strengthening；v1 不因此增加另一個 public method。

## 14.3 Localization Theorem 3 — unconditional near-nearest projection

單點 projection 有完全平行的 relaxed theorem。對 finite grid point $g$，定義

$$
\operatorname{Better}_G(x,g)
:=
\{h\in G\cap\mathbb R:|h-x|<|g-x|\}.
$$

若

$$
\boxed{|\operatorname{Better}_G(x,g)|\le1,}
$$

則稱 $g$ 為 **near-nearest** point。Strict nearest 對應更強的 cardinality $0$。

在 standard grids 的 global computable-real bounding / search / embedding hypotheses下，可 guaranteed-finite 回一個 near-nearest point：

```python
x.grid_project(grid)
```

這是「次佳投影點」版本。Strict-nearest selection的 boundary 在相鄰 grid points midpoint；near-nearest contract 把兩個候選的合法區域擴張成重疊 safe regions。若 adjacent bracket外側 neighbors為

$$
P<L<R<S,
$$

則兩個 rescue thresholds 滿足

$$
\frac{P+R}{2}
<
\frac{L+S}{2}.
$$

所以即使 target 恰等於其中一個 threshold，另一個 strict branch 仍 guaranteed-finite resolve。

## 14.4 Localization Theorem 4 — no-midpoint promise restores optimal projection

對 adjacent finite grid pair $a<b$ 定義 midpoint obstruction set

$$
M_G
:=
\left\{
\frac{a+b}{2}:
 a,b\in G\cap\mathbb R,\ G\cap(a,b)=\varnothing
\right\}.
$$

若再有 promise

$$
x\notin M_G,
$$

則 relevant adjacent midpoint comparisons全部是 strict cases，因而可以 guaranteed-finite 選出真正 strict-nearest grid point。

所以第三、第四定理形成 projection pair：

$$
\boxed{
\text{unconditional near-nearest}
\quad\leftrightarrow\quad
\text{no-midpoint promised strict-nearest}.
}
$$

和 Theorem 2 一樣，Theorem 4 是 promised mathematical strengthening，不對應額外 public method。

## 14.5 Localization Theorem 5 — mixed optimal output and complementary obstructions

第五定理最後才把前面兩種**最佳**問題一起看。

最佳包圍的 semantic obstruction 是 exact grid hit：

$$
B_{\mathrm{enc}}=G\cap\mathbb R.
$$

這裡 adjacent bracket 仍存在，但 target-directed search 可能卡在 $x=g$ 的 equality boundary。

最佳投影的 obstruction 則是 adjacent midpoint：

$$
B_{\mathrm{proj}}=M_G.
$$

在這裡 strict nearest 本身不存在，因兩個 adjacent endpoints 等距。

關鍵是

$$
\boxed{(G\cap\mathbb R)\cap M_G=\varnothing.}
$$

若 $m=(a+b)/2$ 且 $a<b$ adjacent，則 $a<m<b$；若 $m$ 也是 grid point 便違反 adjacency。所以兩種障礙不可能同時發生。

因此可以 fair-dovetail：

- Theorem 2 背後的 optimal adjacent-bracket search；
- Theorem 4 背後的 strict-nearest search。

若 $x\notin G$，第一個必 finite resolve；若 $x\in G$，則必 $x\notin M_G$，第二個必 finite resolve。反過來，若 midpoint obstruction發生，target 一定 off-grid，所以 enclosure channel 必 finite resolve。

這得到 mixed-format output：

- optional **adjacent bracket**；
- optional **strict-nearest point** + partial direction；
- 兩個 channel 至少一個存在。

在 v1 對應：

```python
x.grid_localize(grid)
```

所以三個 public one-dimensional grid observation surface的角色是：

```python
x.grid_bound(grid)      # Theorem 1: fixed bracket shape, relaxed to near-adjacent
x.grid_project(grid)    # Theorem 3: fixed point shape, relaxed to near-nearest
x.grid_localize(grid)   # Theorem 5: keep optimality, relax which output shape is returned
```

可以把它看成一個很乾淨的三角：Theorems 1 / 3 為了 unconditional termination 而固定 shape、退讓 optimality；Theorem 5 反過來保留 optimality 與 unconditional termination，退讓 fixed shape。

`grid_project` 仍然不是 Python `float()` 的替代拼字，也不承諾 correctly-rounded / strict-nearest；`grid_localize` 的 strict-nearest channel 則是 exact optimal point information，但不保證每次一定走 point channel。

## 14.6 Complex-plane rational probes

複平面的 exact probe domain 固定採

$$
\mathbb Q(i)=\mathbb Q\times\mathbb Q.
$$

對任何 one-dimensional rational grid $G\subset\mathbb Q$，可構造 product grid

$$
G^{(2)}:=G\times G\subset\mathbb Q(i).
$$

Rational rectangle

$$
[a,b]\times[c,d]
$$

的 corners / center 都屬於 $\mathbb Q(i)$。因此 `Algebraic` root isolation、`ComputableComplex` box refinement、directional probes與 complex search utilities可共用同一 exact geometry substrate。

這裡不要求 general `ComputableComplex` 提供二維 public nearest-neighbor API；v1 的 coordinatewise grid observation直接對 `real_part()` / `imag_part()` 分別套用一維 `grid_bound()` / `grid_localize()` / `grid_project()`。`GaussianRational` 的角色是提供 canonical exact point / probe representation。

---

# 15. Computation graph 的真正角色

`Rational`、`GaussianRational` 與 `Algebraic` 都是 finite exact values，不需要預設成 graph nodes。

一般 `ComputableReal` / `ComputableComplex` 不同：derived semantic value 通常天然依賴 operands 的 semantic capability，因此出現不可避免的 object-reference chain：

$$
x,y
\longrightarrow
x+y
\longrightarrow
f(x+y)
\longrightarrow\cdots
$$

Computation DAG 的目的首先是：

- 抵抗引用鏈帶來的 depth / memory / repeated-work 膨脹；
- flatten associative operations；
- share identical constructions；
- 讓 evaluation iterative；
- 共享 persistent knowledge。

其次才是利用既有 graph 做安全 structural rewrites。

因此：

$$
\boxed{
\text{The computation graph is not a universal representation of exact numbers.}
}
$$

它是一般 semantic realizations 的 controlled dependency graph。

`Rational` / `GaussianRational` / `Algebraic` 只有在 lift 進 `ComputableReal` / `ComputableComplex` graph 時，才作為 exact leaf payload 參與圖結構。

---

# 16. Correctness substrate

核心 correctness 不依賴 machine floating point。

基本 substrate 是：

$$
\boxed{
\text{Python arbitrary-precision integers}
+
\text{finite exact data structures}
+
\text{finite effective computation}.
}
$$

`float` / `complex` 只可用於：

- I/O；
- interoperability；
- projection result；
- diagnostics；
- test oracle 的非核心部分。

不能用 floating tolerance 決定 exact equality、certificate validity、root isolation correctness 或 semantic relation。
