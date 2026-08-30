# Computable：Mathematical Foundations

本文件建立 `Computable` 所使用的形式數學基礎。目標是把下列詞彙全部還原為 ZFC 中明確定義的對象：

```text
code
format type
program
configuration
finite computation
partial computable function
resumable process
interpretation
semantic realization
exact realization
normal realization
perfect realization
computable real
searchable-grid finite observation
```

Runtime implementation 不需要真的以 bit string 執行所有 hot paths；本文件只固定「所有 finite effective information 最終可被如此形式化」。

---

# Part I — Foundational notation

# 1. ZFC convention

全文工作於 ZFC。

使用 von Neumann natural numbers：

$$
\omega=\{0,1,2,\ldots\},
$$

並記：

$$
\mathbb N_{>0}:=\omega\setminus\{0\}.
$$

標準 ordered pair、Cartesian product、integer、finite sequence construction 皆取 ZFC usual construction。

---

# 2. Partial functions

## Definition 2.1 — Partial function

令 $X,Y$ 為 sets。Relation

$$
f\subseteq X\times Y
$$

稱為從 $X$ 到 $Y$ 的 partial function，若：

$$
(x,y)\in f\land(x,y')\in f
\Longrightarrow
y=y'.
$$

記：

$$
f:X\rightharpoonup Y.
$$

其 domain：

$$
\operatorname{dom}(f)
:=
\{x\in X:\exists y\in Y,\ (x,y)\in f\}.
$$

若：

$$
\operatorname{dom}(f)=X,
$$

則稱 $f$ 為 total function 並寫：

$$
f:X\to Y.
$$

---

# 3. Finite sequences

對 set $A$，定義：

$$
A^{<\omega}:=\bigcup_{n\in\omega}A^n.
$$

若 $x\in A^n$，記 sequence length：

$$
|x|:=n.
$$

空 sequence 記為：

$$
\varepsilon.
$$

對 $x,y\in A^{<\omega}$，concatenation 記為：

$$
x\oplus y.
$$

則：

$$
(A^{<\omega},\oplus)
$$

為 monoid，identity 為 $\varepsilon$。

---

# Part II — Code and finite framing

# 4. Code

## Definition 4.1 — Code

$$
\boxed{
\mathrm{Code}:=2^{<\omega}=\{0,1\}^{<\omega}.
}
$$

因此每個 code 是有限 binary string。

`Code` 是 countable。

---

# 5. Prefix

## Definition 5.1

對 $x,z\in\mathrm{Code}$：

$$
x\preceq z
$$

iff 存在 $y\in\mathrm{Code}$ 使：

$$
x\oplus y=z.
$$

## Definition 5.2 — Prefix-free set

$A\subseteq\mathrm{Code}$ 稱 prefix-free，若：

$$
x,y\in A\land x\preceq y
\Longrightarrow x=y.
$$

## Definition 5.3 — Encoder

對 set $X$，injective function

$$
E:X\to\mathrm{Code}
$$

稱為 encoder。

若 $E(X)$ prefix-free，稱為 prefix-free encoder。

---

# 6. Reduction space and positive-integer prefix-free encoder

本節建立 reduction-space 的核心結構，並固定一個**完全明確、無未定義輔助符號**的 positive-integer prefix-free encoder。後續 machine / type theory 只依賴已形式化的 encoder properties，不依賴額外的 code-length optimization。

## 6.1 Partial iterates

令 $f:X\to Y$，其中允許 $X\cap Y\ne\varnothing$。定義 partial iterates $f^n$：

$$
D_0:=X\cup Y,
\qquad
f^0:=\operatorname{id}_{D_0}.
$$

遞迴令：

$$
D_{n+1}
:=
\{x\in D_n:f^n(x)\in X\},
$$

且對 $x\in D_{n+1}$：

$$
f^{n+1}(x):=f(f^n(x)).
$$

因此 $f^n:D_n\to Y$ 對 $n\ge1$ 是 partial iterate。

### Proposition 6.1 — Composition law

對 $a,b\in\omega$：

$$
D_{a+b}
=
\{x\in D_a:f^a(x)\in D_b\},
$$

且對所有 $x\in D_{a+b}$：

$$
f^{a+b}(x)=f^b(f^a(x)).
$$

證明由 $b$ 的歸納直接得到。

## 6.2 Reductions

令：

$$
\mathbb N_{>0}=\{1,2,3,\ldots\}.
$$

### Definition 6.2 — Reduction

函數：

$$
f:\mathbb N_{>0}\to\omega
$$

稱為 reduction，若：

$$
f^{-1}(\{0\})\subseteq\{1\},
$$

且：

$$
\forall x\in\mathbb N_{>0},
\qquad
f(x)<x.
$$

記所有 reductions 的集合為：

$$
\mathcal R.
$$

由定義立即得：

$$
f(1)=0,
\qquad
f(2)=1.
$$

### Proposition 6.2 — Unique reduction depth to $1$

對任意 $f\in\mathcal R$ 與 $x\in\mathbb N_{>0}$，存在唯一 $n\in\omega$ 使：

$$
x\in D(f^n)
$$

且：

$$
f^n(x)=1.
$$

存在性來自每次 positive iterate 嚴格下降；唯一性來自 $f(1)=0$，所以到達 $1$ 後下一步便離開 positive integers。

### Definition 6.3 — Step reduction

定義：

$$
\operatorname{Step}_f(x)
$$

為 Proposition 6.2 中唯一的 $n$。

則：

$$
\operatorname{Step}_f:\mathbb N_{>0}\to\omega.
$$

### Proposition 6.3

若 $f\in\mathcal R$，則：

$$
\operatorname{Step}_f\in\mathcal R.
$$

此外：

$$
\operatorname{Step}_f(x)\le f(x)
$$

對所有 $x\in\mathbb N_{>0}$ 成立。

若 $f$ non-decreasing，則 $\operatorname{Step}_f$ 亦 non-decreasing。

這些性質保留 reduction-space 作為研究更短 self-delimiting integer encoders 的工具；但後續 formal machine 不需要依賴其最佳化結果。

## 6.3 Binary representation and tail

定義 usual binary encoder：

$$
\operatorname{bin}:\omega\to\mathrm{Code}.
$$

其中 $\operatorname{bin}(0)=0$，而正整數使用無 leading-zero 的 binary representation。

對 $n\in\mathbb N_{>0}$，唯一寫成：

$$
\operatorname{bin}(n)
=
1\oplus\operatorname{tail}(n).
$$

令：

$$
R_1(n):=|\operatorname{tail}(n)|,
$$

$$
T_1(n):=\operatorname{tail}(n).
$$

## 6.4 Explicit fixed prefix-free encoder

對 $k\in\omega$，記 $1^{[k]}$ 為 $k$ 個 `1` 的 concatenation。

定義：

$$
\boxed{
E_{>0}(n)
:=
1^{[R_1(n)]}\oplus0\oplus T_1(n).
}
$$

這提供一個明確的 fixed positive-integer prefix-free encoder。

### Theorem 6.4

$E_{>0}$ 是 $\mathbb N_{>0}$ 的 prefix-free encoder。

### Proof

若 $R_1(n)=r$，code 的前段恰為：

$$
1^{[r]}0,
$$

所以 decoder 先讀取第一個 `0` 前的 `1` 數量 $r$，再讀恰好 $r$ bits 作為 $T_1(n)$。因此 code boundary 唯一。

若兩個 outputs 有 prefix relation，較短 code 的 delimiter 與 payload length 迫使兩者具有相同 $r$ 與相同 $r$-bit payload，故兩 codes 相等。Injectivity 再由 binary representation uniqueness 得到。

因此：

$$
E_{>0}(\mathbb N_{>0})
$$

prefix-free。

## 6.5 Encoder-substitution principle

後續 type system 與 machine theory 不依賴 $E_{>0}$ 的特定 code-length profile，而只使用下列性質：

1. $E_{>0}$ injective；
2. $E_{>0}(\mathbb N_{>0})$ prefix-free；
3. encoder 與 decoder 皆 computable。

因此，任何經完整形式化並證明滿足上述三項性質的 length-optimized positive-integer encoder，都可以替換本節的 explicit construction，而不改變後續 type system、machine computability 或 realization theory。Reduction-space 可作為研究這類 encoder 的工具，但 code-length optimality 不屬於後續 foundational dependency。

---

# 7. Natural-number framing encoder

保留 positive-integer encoder，不把 $0$ 塞進其 domain。

定義：

$$
E_0(n):=E_{>0}(n+1),
\qquad n\in\omega.
$$

因此 $E_0$ 也是 prefix-free encoder of $\omega$。

它用於：

- lengths；
- arities；
- indices；
- element counts；
- program counters；
- register indices。

---

# 8. Length framing

對 $c\in\mathrm{Code}$，定義：

$$
\operatorname{Frame}(c)
:=
E_0(|c|)\oplus c.
$$

由 $E_0$ prefix-free，可先有限讀出 $|c|$，再精確讀取後續 $|c|$ bits。

因此 variable-length payload 不需要本身 prefix-free。

對有限 sequence $(c_0,\ldots,c_{n-1})$，可 canonical encode 為：

$$
E_0(n)
\oplus
\operatorname{Frame}(c_0)
\oplus\cdots\oplus
\operatorname{Frame}(c_{n-1}).
$$

---

# Part III — Machine-level type system

# 9. Type constructors

固定一個 **effectively decidable**、在 formal language 中預先指定的 constructor vocabulary：

$$
\mathsf{Ctor}.
$$

也就是 constructor ID 是否屬於這一版 formal theory 的 vocabulary，必能由 terminating parser 判定；program runtime 不可動態擴充此 vocabulary。

每個 constructor $C\in\mathsf{Ctor}$ 配一個唯一 positive integer ID：

$$
\operatorname{id}(C)\in\mathbb N_{>0}.
$$

ID encoder 使用：

$$
E_{>0}(\operatorname{id}(C)).
$$

並記 constructor tag：

$$
\boxed{
\operatorname{Tag}(C)
:=
E_{>0}(\operatorname{id}(C)).
}
$$

由 $E_{>0}$ prefix-free，讀取 typed value 時可唯一有限切出最外層 constructor tag。

Constructor vocabulary 在 formal theory 中固定；program runtime 不可自行創造額外 constructor grammar。引入 primitive constructor 是擴充 formal theory，而不是 machine runtime operation。

核心 constructors 至少包含：

```text
Code
Bool
Nat
Int
Type
Program
Configuration
List
Tuple
```

並可加入其他 fixed constructors。

---

# 10. Raw type expressions

## Definition 10.1 — `TyExpr`

`TyExpr` 是由 fixed constructor formation rules 歸納生成的 finite syntax-tree set。對每個 constructor $C$，formal theory 固定一個 decidable arity rule：

$$
\operatorname{Arity}_C\subseteq\omega.
$$

若：

$$
k\in\operatorname{Arity}_C
$$

且：

$$
\tau_0,\ldots,\tau_{k-1}\in\mathrm{TyExpr},
$$

則：

$$
C(\tau_0,\ldots,\tau_{k-1})\in\mathrm{TyExpr}.
$$

Nullary primitive types 對應 $0\in\operatorname{Arity}_C$。Variable-arity constructors 亦可由其 decidable arity rule 表達。

Canonical encoding 遞迴定義為：

$$
\operatorname{enc}_{\mathrm{Ty}}
\bigl(C(\tau_0,\ldots,\tau_{k-1})\bigr)
:=
\operatorname{Tag}(C)
\oplus E_0(k)
\oplus
\bigoplus_{j<k}
\operatorname{Frame}(\operatorname{enc}_{\mathrm{Ty}}(\tau_j)).
$$

因此：

$$
\operatorname{enc}_{\mathrm{Ty}}:\mathrm{TyExpr}\to\mathrm{Code}
$$

injective。令：

$$
\operatorname{TyCode}
:=
\operatorname{enc}_{\mathrm{Ty}}(\mathrm{TyExpr}).
$$

由 prefix-free constructor tag、explicit arity、length framing 與 decidable formation rules，可建立 terminating parser；故 `TyCode` 是 Code-decidable。

此處的 “Code-decidable” 是對 Definition 29.2 的 forward reference；machine semantics 建立後，以上 parser 必由 Code-register program 實現。這個 forward reference 不把 decidability 當作 meta-level primitive。

`TyExpr` 是 raw syntax，不需要再帶 `Type` tag，因此不存在：

$$
\mathsf{Type}:\mathsf{Type}:\mathsf{Type}:\cdots
$$

的 encoding regress。

---

# 11. First-class `Type`

真正 machine-level `Type` value 才包外層 tag：

$$
F_{\mathsf{Type}}
:=
\left\{
E_{>0}(\operatorname{id}(\mathsf{Type}))
\oplus
\operatorname{Frame}(t)
:
 t\in\operatorname{TyCode}
\right\}.
$$

因此 type expression 可作為 ordinary machine data：

- input；
- output；
- list element；
- tuple element；
- dynamic dispatch information。

---

# 12. Ordinary typed values

普通 typed value **不**在最前面重複完整 type expression，而只攜帶最外層 constructor tag：

$$
E_{>0}(\operatorname{id}(C))\oplus p,
$$

其中 payload $p$ 依 constructor-specific decidable grammar parse。

Composite values 中每個 child 自己是完整 typed value，並由 parent 使用 length framing 分隔。

例如 heterogeneous tuple 概念上：

```text
[Tuple]
    Frame([Int] ...)
    Frame([Bool] ...)
    Frame([Rational-like payload] ...)
```

---

# 13. Heterogeneous `List`

`List` 本身不要求 homogeneous element type。

Format 可取：

$$
\operatorname{Tag}(\mathsf{List})
\oplus
E_0(n)
\oplus
\operatorname{Frame}(v_0)
\oplus\cdots\oplus
\operatorname{Frame}(v_{n-1}),
$$

其中每個 $v_i$ 是任意 well-formed typed value。

因此 mixed-type list of tuples 是原生合法格式。

Homogeneous-list property 若需要，可作為更高階 predicate / semantic subtype，而非底層 format invariant。

---

# 14. Format type

對 machine-level type $\tau$，記其 format domain：

$$
F_\tau\subseteq\mathrm{Code}.
$$

要求：

$$
\boxed{F_\tau\text{ is Code-decidable}.}
$$

型別系統只保證 syntactic / format validity，不保證 semantic promise。

這是後續 distinction：

$$
D_\tau\subseteq F_\tau.
$$

---

# Part IV — Program syntax

# 15. Code-register machine instruction set

Machine registers：

$$
R_0,R_1,R_2,\ldots
$$

每個 register 存一個 `Code`。

Primitive instructions 固定為：

$$
\mathsf{CLEAR}(i),
$$

$$
\mathsf{APPEND0}(i),
$$

$$
\mathsf{APPEND1}(i),
$$

$$
\mathsf{POP}(i),
$$

$$
\mathsf{COPY}(i,j),
$$

$$
\mathsf{BRANCH}(i,a,b,c),
$$

$$
\mathsf{HALT}.
$$

其中 $i,j,a,b,c\in\omega$。

Machine primitive 不內建：

- string length；
- concatenation；
- equality；
- substring；
- integer arithmetic；
- parser；
- function call。

這些都在後續證明為可實現後作高階 abstraction。

---

# 16. Abstract programs

## Definition 16.1

Abstract program 是 finite instruction sequence：

$$
p=(I_0,\ldots,I_{n-1}),
\qquad n\in\omega.
$$

空 program：

$$
p=()
$$

合法。

## Control-flow validity

若 $I_q=\mathsf{BRANCH}(i,a,b,c)$，要求：

$$
a,b,c<n.
$$

因此 well-formed program 不存在 dangling jump target。

Ordinary final instruction 可 fall through 並停止；不要求最後一條一定是 `HALT`。

---

# 17. Canonical raw program encoding

固定 opcode IDs：

```text
1 CLEAR
2 APPEND0
3 APPEND1
4 POP
5 COPY
6 BRANCH
7 HALT
```

例如：

$$
\operatorname{enc}_I(\mathsf{COPY}(i,j))
=
E_{>0}(5)\oplus E_0(i)\oplus E_0(j).
$$

$$
\operatorname{enc}_I(\mathsf{BRANCH}(i,a,b,c))
=
E_{>0}(6)
\oplus E_0(i)
\oplus E_0(a)
\oplus E_0(b)
\oplus E_0(c).
$$

整個 program：

$$
\operatorname{enc}_{\mathrm{Prog}}(p)
=
E_0(n)
\oplus
\operatorname{enc}_I(I_0)
\oplus\cdots\oplus
\operatorname{enc}_I(I_{n-1}).
$$

只有 control-flow-valid sequences 的 canonical codes 屬於：

$$
\mathrm{ProgExpr}\subseteq\mathrm{Code}.
$$

Encoder injective，因此每個 abstract program 恰一個 raw code。

Program syntax equality 是 decidable；program extensional equality：

$$
\varphi_p=\varphi_q
$$

是另一個問題，不等同 syntax equality。

---

# 18. First-class `Program`

Machine-level Program value：

$$
F_{\mathsf{Program}}
:=
\left\{
\operatorname{Tag}(\mathsf{Program})
\oplus
\operatorname{Frame}(p)
:
p\in\mathrm{ProgExpr}
\right\}.
$$

因此 program 可以被：

- 儲存；
- 傳遞；
- 比較 syntactic code；
- 由另一個 program 模擬。

執行中的 program 本身 immutable；machine 不提供 self-modifying instruction。

---

# Part V — Register states and configurations

# 19. Sparse register state

Register state 是 finite partial map：

$$
\rho:\omega\rightharpoonup\mathrm{Code}
$$

且：

$$
i\in\operatorname{dom}(\rho)
\Longrightarrow
\rho(i)\ne\varepsilon.
$$

未出現在 domain 的 register 解釋為 empty string：

$$
R_i^\rho
:=
\begin{cases}
\rho(i),&i\in\operatorname{dom}(\rho),\\
\varepsilon,&i\notin\operatorname{dom}(\rho).
\end{cases}
$$

因此 empty register 不顯式儲存。

---

# 20. Canonical register-state encoding

令：

$$
\operatorname{dom}(\rho)
=
\{i_0<\cdots<i_{k-1}\}.
$$

Canonical encoding 依 index 嚴格遞增：

$$
E_0(k)
\oplus
\bigoplus_{j<k}
\left(
E_0(i_j)
\oplus
\operatorname{Frame}(\rho(i_j))
\right).
$$

因此同一 abstract sparse state 只有一個 raw encoding。

---

# 21. Running and halted configurations

令 $\mathrm{Cfg}$ 為 abstract configurations 的集合，分成兩個 disjoint variants。

## Running

$$
\operatorname{Running}(p,q,\rho),
$$

其中：

- $p=(I_0,\ldots,I_{n-1})$；
- $n>0$；
- $q<n$；
- $\rho$ 是 sparse register state。

記所有 running configurations 為 $\mathrm{Cfg}_{\mathrm{run}}$。

## Halted

$$
\operatorname{Halted}(p,\rho).
$$

Halted configuration 沒有 program counter。記所有 halted configurations 為 $\mathrm{Cfg}_{\mathrm{halt}}$。

因此：

$$
\mathrm{Cfg}
=
\mathrm{Cfg}_{\mathrm{run}}
\mathbin{\dot\cup}
\mathrm{Cfg}_{\mathrm{halt}}.
$$

每個 configuration self-contained：完整包含 program，不依賴 external program registry。

令 $\operatorname{enc}_{\mathrm{Reg}}(\rho)$ 為 Definition 20 的 canonical register-state code。固定 raw configuration encoding：

$$
\operatorname{enc}_{\mathrm{Cfg}}
\bigl(\operatorname{Running}(p,q,\rho)\bigr)
:=
E_0(0)
\oplus
\operatorname{Frame}(\operatorname{enc}_{\mathrm{Prog}}(p))
\oplus E_0(q)
\oplus
\operatorname{Frame}(\operatorname{enc}_{\mathrm{Reg}}(\rho)),
$$

以及：

$$
\operatorname{enc}_{\mathrm{Cfg}}
\bigl(\operatorname{Halted}(p,\rho)\bigr)
:=
E_0(1)
\oplus
\operatorname{Frame}(\operatorname{enc}_{\mathrm{Prog}}(p))
\oplus
\operatorname{Frame}(\operatorname{enc}_{\mathrm{Reg}}(\rho)).
$$

`0` / `1` 在此只是 canonical variant IDs；不是額外 machine status state。

令：

$$
\mathrm{CfgExpr}
:=
\operatorname{enc}_{\mathrm{Cfg}}(\mathrm{Cfg}).
$$

真正 first-class machine-level `Configuration` value format 為：

$$
F_{\mathsf{Configuration}}
:=
\left\{
\operatorname{Tag}(\mathsf{Configuration})
\oplus
\operatorname{Frame}(c)
:
c\in\mathrm{CfgExpr}
\right\}.
$$

Running / halted subsets 的 typed codes 分別記為：

$$
F_{\mathsf{RunningConfig}},
\qquad
F_{\mathsf{HaltedConfig}}.
$$

由 canonical program parser、register-state parser、variant parser 與 range checks，以上 format domains 都 Code-decidable。

後文為了不讓 notation 過重，會在 abstract configuration 與其 canonical first-class code 之間作明確可計算的 encode/decode identification；machine transition 首先定義在 abstract $\mathrm{Cfg}$ 上，再由 canonical encoding誘導對 first-class configuration codes 的 computable operation。

---

# 22. Initial configuration

輸入永遠是單一：

$$
x\in\mathrm{Code}.
$$

初始 register state：

$$
\rho_x
=
\begin{cases}
\varnothing,&x=\varepsilon,\\
\{0\mapsto x\},&x\ne\varepsilon.
\end{cases}
$$

若 $p=()$，初始 configuration 直接為：

$$
\operatorname{Halted}(p,\rho_x).
$$

因此空 program 實現 identity。

若 $|p|>0$：

$$
\operatorname{Init}(p,x)
:=
\operatorname{Running}(p,0,\rho_x).
$$

---

# Part VI — One-step machine semantics

# 23. Register update notation

令 $\rho[i\leftarrow c]$ 表示：

- 若 $c=\varepsilon$，從 sparse map 移除 $i$；
- 若 $c\ne\varepsilon$，設 $R_i=c$。

---

# 24. Primitive instruction semantics

令目前 configuration：

$$
C=\operatorname{Running}(p,q,\rho),
$$

且 $I_q$ 為 current instruction。

## `CLEAR(i)`

$$
R_i:=\varepsilon.
$$

## `APPEND0(i)`

$$
R_i:=R_i0.
$$

## `APPEND1(i)`

$$
R_i:=R_i1.
$$

## `POP(i)`

若：

$$
R_i=xb,
\qquad b\in\{0,1\},
$$

則：

$$
R_i:=x.
$$

若：

$$
R_i=\varepsilon,
$$

保持 empty。

## `COPY(i,j)`

$$
R_j:=R_i.
$$

## `BRANCH(i,a,b,c)`

不修改 registers。

- $R_i=\varepsilon$ -> next PC $a$；
- $R_i=x0$ -> next PC $b$；
- $R_i=x1$ -> next PC $c$。

## `HALT`

立即產生：

$$
\operatorname{Halted}(p,\rho).
$$

---

# 25. Fall-through

對 ordinary non-branch / non-HALT instruction，若 $q+1<|p|$：

$$
q':=q+1.
$$

若 $q=|p|-1$，該 instruction 對 registers 的 effect 完成後，直接轉成：

$$
\operatorname{Halted}(p,\rho').
$$

因此 program 結尾是 implicit halt。

---

# 26. Step

先在 abstract configurations 上定義：

$$
\operatorname{Step}:
\mathrm{Cfg}_{\mathrm{run}}
\to
\mathrm{Cfg}.
$$

把它視為 $\mathrm{Cfg}\rightharpoonup\mathrm{Cfg}$ 時，其 domain 恰為 $\mathrm{Cfg}_{\mathrm{run}}$；因此 `Step` 不定義於 halted configuration。

由 canonical configuration encode/decode，可誘導 first-class code 上的 computable partial operation：

$$
F_{\mathsf{Configuration}}
\rightharpoonup
F_{\mathsf{Configuration}},
$$

其 domain 恰為 $F_{\mathsf{RunningConfig}}$。

由 program well-formedness，任何 running configuration 都有唯一 next configuration。

所以合法 execution 不存在：

```text
running but stuck
```

狀態。

---

# 27. Finite and infinite execution

對 program $p$ 與 input $x$，令：

$$
C_0:=\operatorname{Init}(p,x).
$$

若 $C_0$ halted，execution length 為 $0$。

否則遞迴：

$$
C_{n+1}:=\operatorname{Step}(C_n)
$$

只要 $C_n$ running。

有兩種情況：

1. 存在 least $N\in\omega$ 使 $C_N$ halted；
2. 對所有 $n$，$C_n$ running，得到 infinite execution。

---

# 28. Program denotation

若：

$$
C_N=\operatorname{Halted}(p,\rho),
$$

output 定義為：

$$
\operatorname{Out}(C_N):=R_0^\rho.
$$

每個 program $p$ 定義 partial function：

$$
\boxed{
\varphi_p:\mathrm{Code}\rightharpoonup\mathrm{Code}.
}
$$

若 execution finite halt，令：

$$
\varphi_p(x):=\operatorname{Out}(C_N).
$$

若 execution infinite，則：

$$
x\notin\operatorname{dom}(\varphi_p).
$$

空 program滿足：

$$
\varphi_{()}=\operatorname{id}_{\mathrm{Code}}.
$$

---

# Part VII — Computability

# 29. Partial computable functions

## Definition 29.1

Partial function：

$$
f:\mathrm{Code}\rightharpoonup\mathrm{Code}
$$

稱為 computable，若存在 well-formed program $p$ 使：

$$
f=\varphi_p.
$$

若：

$$
\operatorname{dom}(f)=\mathrm{Code},
$$

則稱 total computable。

## Definition 29.2 — Relative decidability

令：

$$
A\subseteq B\subseteq\mathrm{Code}.
$$

稱 $A$ **$B$-decidable**，若存在 program $p$，使對每個 $x\in B$，execution 都 finite halt，且 output 恰為 one-bit code `1` 或 `0`，並滿足：

$$
\varphi_p(x)=1
\iff
x\in A,
$$

$$
\varphi_p(x)=0
\iff
x\in B\setminus A.
$$

對 $x\notin B$ 不作要求。

若 $B=\mathrm{Code}$，則稱 $A$ **Code-decidable**。

這個定義只用 raw one-bit outputs 作 classifier convention；若需要 first-class `Bool` value，可再由固定 computable wrapper 加上 `Bool` type tag，兩者 computability strength 相同。

---

# 30. Typed algorithms

底層 machine 永遠只有：

$$
\mathrm{Code}\rightharpoonup\mathrm{Code}.
$$

多參數與多輸出由 framing / tuple code 作高階 abstraction。

## Definition 30.1

令 $A,B\subseteq\mathrm{Code}$。Program $p$ realizes total typed function

$$
f:A\to B
$$

若：

$$
\forall x\in A,
\qquad
\varphi_p(x)\downarrow
\land
\varphi_p(x)=f(x).
$$

對：

$$
x\notin A,
$$

不作任何要求。

因此 typed precondition 不強迫每個 algorithm 自己先做 runtime type checking。

---

# 31. Partial typed algorithms

令：

$$
A\subseteq F_\tau,
$$

$$
f:A\to F_\sigma.
$$

Program $p$ realizes $f$ iff：

$$
\forall x\in A,
\qquad
\varphi_p(x)\downarrow
\land
\varphi_p(x)=f(x).
$$

對：

$$
x\in F_\tau\setminus A
$$

完全不要求 termination、error detection 或特定 output。

因此：

$$
\boxed{
\text{mathematical domain promise}
\neq
\text{domain-decision ability}.
}
$$

---

# 32. Derived high-level computable constructions

可由 primitive instructions explicit programming 證明下列 operations computable：

- code equality；
- code length；
- concatenation；
- prefix / suffix extraction；
- finite tuple framing / projection；
- natural-number arithmetic；
- integer arithmetic；
- finite loops；
- conditional branch；
- finite-map parsing；
- program parsing；
- configuration parsing；
- one-step simulation。

一旦這些 theorem 證明完成，後文可直接用高階 notation，不必每次展開為 `APPEND0` / `POP` instructions。

這是本理論的「先嚴格定義，再升格成高階概念」原則。

---

# 33. Universal evaluation

因 `Program` 與 `Configuration` 都是 first-class finite codes，存在 universal simulator program $U$，使其可 step-by-step 模擬任意 encoded program。

形式上可建立 computable partial function：

$$
\operatorname{Eval}:
F_{\mathsf{Program}}\times\mathrm{Code}
\rightharpoonup
\mathrm{Code},
$$

滿足：

$$
\operatorname{Eval}(p,x)=\varphi_p(x)
$$

whenever right-hand side defined。

`Eval` 在被模擬 program diverges 時也 diverges。

---

# 34. Equivalence with standard Turing computability

## Theorem 34.1

Code-register computability 與 standard Turing computability extensionally equivalent。

### Proof strategy

**Code-register -> Turing machine.**

每個 finite sparse register map、program counter 與 program code 可在 Turing tape 上 finite encode。每個 primitive instruction 對 finite string 的 update 可由 finite Turing procedure 模擬。因此整個 execution 可逐步模擬。

**Turing machine -> Code-register.**

把 tape head 左側與右側內容分別存成 finite code stacks，再以 registers 保存 finite control state。`APPEND0/1`、`POP` 與 `BRANCH` 足以實現 tape-symbol read/write/head movement；有限 control table可編成 program branch structure。

因此兩者計算相同 partial functions up to fixed effective encodings。

### Consequence

後續「computable」不依賴我們挑了奇怪的 machine model；它符合 Church–Turing standard class。

---

# Part VIII — Resumable computation and work units

# 35. Resumable computation state

由於 `Configuration` 是 finite first-class data，一個 paused computation 可直接由 configuration 表示。

若 $C$ running，one cooperative machine step就是：

$$
C\mapsto\operatorname{Step}(C).
$$

高階 process transition 可一次做固定有限個 machine steps與 finite bookkeeping；核心要求是每個 transition guaranteed finite。

---

# 36. Finite work budget

對 state transition system：

$$
S\to S'
$$

若每次 transition guaranteed finite，則執行至多 $N\in\omega$ 次 transition 必 finite terminate。

這形式化 runtime：

```python
process.advance(work=N)
```

的 termination contract。

---

# 37. Fair dovetailing

給 countable / finite family of resumable processes，fair scheduler 以 round-robin 或任何每個 active branch 都 infinitely often receiving steps 的規則 interleave。

## Theorem 37.1

若某 branch 在 $k<\infty$ 個自身 transitions 後 resolve，fair dovetail scheduler 最終在 finite global transitions 後 observe resolution。

這是 comparator-to-bound search、compound semantic decision 等 construction 的核心工具。

---

# Part IX — Interpretation and realization

# 38. Interpretation with format domain

## Definition 38.1

令 $X$ 為 mathematical set。

一個 interpretation 是 triple：

$$
\mathcal I=(F,D,\llbracket\cdot\rrbracket)
$$

使：

$$
D\subseteq F\subseteq\mathrm{Code},
$$

$F$ Code-decidable，且：

$$
\llbracket\cdot\rrbracket:D\to X
$$

surjective。

- $F$：format domain；
- $D$：semantic domain。

一般不要求 $D$ decidable。

---

# 39. Bilateral interpretation

## Definition 39.1

Interpretation $\mathcal I$ 稱 bilateral iff：

$$
\llbracket\cdot\rrbracket:D\to X
$$

bijective。

不要求：

$$
F=D.
$$

因此 bilateral 只表示 semantic representation uniqueness。

---

# 40. Product interpretation

對 finite arity $d\in\omega$，使用已證 computable 的 tuple framing，把：

$$
F^d
$$

與 finite tuple codes作有效對應。

Semantic domain：

$$
D^d.
$$

Denotation componentwise：

$$
\llbracket(a_1,\ldots,a_d)\rrbracket_d
:=
(\llbracket a_1\rrbracket,\ldots,\llbracket a_d\rrbracket).
$$

---

# 41. Mathematical structures

## Definition 41.1

Finite-signature single-carrier mathematical structure：

$$
M
=
\left(
X;
 c_1,\ldots,c_{n_c};
 (d_1,A_1,f_1),\ldots,(d_{n_f},A_{n_f},f_{n_f});
 \mathcal R_1,\ldots,\mathcal R_{n_R}
\right),
$$

其中：

- $X$ carrier；
- $c_i\in X$；
- $d_i\in\omega$；
- $A_i\subseteq X^{d_i}$；
- $f_i:A_i\to X$ partial mathematical operation；
- 每個 $\mathcal R_j$ 是 $X^{r_j}$ 的 finite partition；
- $r_j\in\omega$ 可為任意有限 arity。

Relation family 不限 binary。

---

# 42. Constant realizability

$c\in X$ 對 interpretation $\mathcal I$ realizable iff 存在 terminating typed algorithm輸出某 $a\in D$ 使：

$$
\llbracket a\rrbracket=c.
$$

---

# 43. Set / domain realizability

對：

$$
A\subseteq X^d,
$$

令其 code-preimage：

$$
\widetilde A
:=
\left\{
\mathbf a\in D^d:
\llbracket\mathbf a\rrbracket_d\in A
\right\}.
$$

稱 $A$ **decidable with respect to $\mathcal I$** iff $\widetilde A$ 在 promised semantic domain $D^d$ 上有 terminating membership classifier；也就是對每個 $\mathbf a\in D^d$ 必 finite halt 並正確判定

$$
\llbracket\mathbf a\rrbracket_d\in A,
$$

對 $F^d\setminus D^d$ 不作要求。

這是 Definition 29.2 的 relative-decidability / §31 promised-domain convention。只有在 exact realization 中 $F=D$，它才自動成為對全部 well-formed inputs $F^d$ 的 finite classifier。

注意 semantic realization 不要求 primitive operation domain 都 decidable。

---

# 44. Partial-operation realizability

對：

$$
f:A\subseteq X^d\to X,
$$

$f$ realizable iff 存在 program $p$，對每個：

$$
\mathbf a\in D^d,
\qquad
\llbracket\mathbf a\rrbracket_d\in A,
$$

$p$ finite halt，輸出 $b\in D$，且：

$$
\llbracket b\rrbracket
=
f(\llbracket\mathbf a\rrbracket_d).
$$

對不在 $A$ 的 semantic inputs 無 requirement。

---

# 45. Relation-family realizability

令：

$$
\mathcal R=\{R_1,\ldots,R_m\}
$$

為 $X^r$ 的 finite partition，並令：

$$
C\subseteq\mathcal R,
\qquad
E_C:=\bigcup_{R\in C}R\subseteq X^r.
$$

取 $C$ 的任意 bilateral interpretation：

$$
\mathcal J_C
=
(F_C,D_C,\llbracket\cdot\rrbracket_C).
$$

由 bilaterality：

$$
\llbracket\cdot\rrbracket_C:D_C\to C
$$

bijective。

### Definition 45.1 — Realizing classifier for $C$

一個 realizing classifier 是 partial typed algorithm，其 promised domain 為：

$$
\widetilde E_C
:=
\left\{
\mathbf a\in D^r:
\llbracket\mathbf a\rrbracket_r\in E_C
\right\}.
$$

對每個 $\mathbf a\in\widetilde E_C$，algorithm 必 finite halt 並輸出 $c\in D_C$，使：

$$
\llbracket\mathbf a\rrbracket_r
\in
\llbracket c\rrbracket_C.
$$

對 true relation cell 不屬於 $C$ 的 inputs 不作 termination 或 output requirement。

$C$ 稱為 realizable，若對 $C$ 的**任意 bilateral interpretation** $\mathcal J_C$ 都存在上述 realizing classifier。

這保留 relation classification 的 representation independence；理論不固定某個 enum code 作 cell identity。

注意這裡的 potential divergence 直接來自 partial computable algorithm 在 promised domain 外的未定義性；這是 mathematical realization theory。本專案 runtime 的 `DecisionProcess` 是把同一現象工程化成可暫停、可投入有限 work 的 explicit API，兩者不可混為同一定義。

---

# 46. Semantic realization

## Definition 46.1

Interpretation $\mathcal I=(F,D,\llbracket\cdot\rrbracket)$ 稱為 structure $M$ 的 semantic realization iff：

1. 每個 primitive constant realizable；
2. 每個 primitive partial operation realizable；
3. 對每個 primitive relation family $\mathcal R_i$，存在：

$$
C_i\subseteq\mathcal R_i
$$

使：

$$
|\mathcal R_i\setminus C_i|\le1,
$$

且 $C_i$ realizable。

因此每個 primitive relation family 至多一個 exceptional cell 不要求 finite recognition。

---

# 47. Exact realization

## Definition 47.1

Semantic interpretation $\mathcal I$ 稱 exact realization iff：

1. 

$$
\boxed{F=D;}
$$

2. every primitive constant realizable；
3. every primitive partial operation realizable；
4. 對每個 primitive operation domain $A_i\subseteq X^{d_i}$，其 code-preimage

$$
\widetilde A_i
=
\left\{
\mathbf a\in F^{d_i}:
\llbracket\mathbf a\rrbracket_{d_i}\in A_i
\right\}
$$

在 $F^{d_i}$ 上可 finite decide；
5. 對每個 relation family $\mathcal R_i$，整個 $\mathcal R_i$ realizable，即所有 cells 可 finite classify。

因此 exact realization 的「domain decidability」不是對 partial operation realizer本身的 implicit requirement，而是 exactness 額外提供的能力。

---

# 48. Normal realization

## Definition 48.1

Exact realization $\mathcal I=(F,F,\llbracket\cdot\rrbracket)$ 稱 normal iff存在 terminating：

$$
\Lambda:F\to F
$$

令：

$$
A:=\Lambda(F),
$$

且：

$$
\forall a\in F,
\qquad
\llbracket\Lambda(a)\rrbracket=\llbracket a\rrbracket,
$$

以及 restriction：

$$
\left.\llbracket\cdot\rrbracket\right|_A
$$

injective。

這是 minimal-condition definition。

---

# 49. Basic normalizer theorem

## Theorem 49.1

在 Definition 48.1 下：

### (i) Restriction is surjective

因 $\llbracket\cdot\rrbracket:F\to X$ surjective，任取 $x\in X$，取 $a\in F$ 使：

$$
\llbracket a\rrbracket=x.
$$

則：

$$
\Lambda(a)\in A
$$

且：

$$
\llbracket\Lambda(a)\rrbracket=x.
$$

所以 restriction bijective。

### (ii) Normalizer fixes its image

若 $a\in A$，則 $\Lambda(a)\in A$，且二者 denotation 相同。由 restriction injective：

$$
\Lambda(a)=a.
$$

故：

$$
\Lambda|_A=\operatorname{id}_A.
$$

### (iii) Fixed-point characterization

$$
\boxed{
A=\{a\in F:\Lambda(a)=a\}.
}
$$

### (iv) Idempotence

$$
\boxed{
\Lambda\circ\Lambda=\Lambda.
}
$$

### (v) Canonical image decidable

因 $F$ decidable、$\Lambda$ terminating、Code equality decidable：

$$
a\in A
\iff
\Lambda(a)=a.
$$

故 $A$ Code-decidable。

---

# 50. Perfect realization

## Definition 50.1

Perfect realization 定義為：

$$
\boxed{
\text{exact realization}
+
\text{bilateral interpretation}.
}
$$

即：

$$
F=D
$$

且：

$$
\llbracket\cdot\rrbracket:F\to X
$$

bijective。

---

# 51. Normal / perfect existence equivalence

## Theorem 51.1

$$
M\text{ normal-realizable}
\iff
M\text{ perfect-realizable}.
$$

### Proof

Perfect -> normal：取：

$$
\Lambda=\operatorname{id}_F.
$$

Normal -> perfect：令 $\Lambda:F\to F$ 為 normalizer，$A:=\Lambda(F)$。Theorem 49.1 給 $A$ Code-decidable，且：

$$
\left.\llbracket\cdot\rrbracket\right|_A:A\to X
$$

bijective。

還需確認 structure realization 能 transport 到 $A$；不能只由 interpretation bijective 本身推出。

- **Constants.** 若原 constant realizer 輸出 $a\in F$，再輸出 $\Lambda(a)\in A$；denotation 不變。
- **Partial operations.** 對 inputs in $A$，先使用原 exact realizer 得到 $b\in F$，再輸出 $\Lambda(b)\in A$。Operation-domain decision algorithm 直接限制到 $A^d$。
- **Relations.** 原 exact classifier 直接限制到 $A^r$。Relation-cell 的 output interpretation 是獨立的 bilateral interpretation，因此不需對 output cell code 套用 $\Lambda$。

因此：

$$
\left(
A,A,
\left.\llbracket\cdot\rrbracket\right|_A
\right)
$$

不只是 perfect interpretation，而是 $M$ 的 perfect realization。

這一步不需要 semantic equality 額外 decidable。

---

# 52. Semantic equality

對 interpretation

$$
\mathcal I=(F,D,\llbracket\cdot\rrbracket),
$$

semantic equality 只定義在具有 denotation 的 promised domain $D^2$：

$$
a\equiv_{\mathcal I}b
\iff
\llbracket a\rrbracket=\llbracket b\rrbracket,
\qquad (a,b)\in D^2.
$$

稱 semantic equality **decidable with respect to $\mathcal I$** iff存在 terminating classifier，其 promised domain 為 $D^2$，並在每個 $(a,b)\in D^2$ 上正確判定上述 equality；對 $F^2\setminus D^2$ 不作要求。

若 $\mathcal I$ exact，則 $F=D$，所以這恰好成為對全部 $F^2$ 的 terminating semantic-equality classifier。

---

# 53. Exact / normal / perfect existence collapse

固定 `Code` 上 computable well-order：先比 length，同長度 lexicographic，記為：

$$
\prec_{\mathrm{Code}}.
$$

每個 code 之前只有 finitely many predecessors。

## Theorem 53.1

若 $M$ 有 exact realization $\mathcal I=(F,F,\llbracket\cdot\rrbracket)$，且 semantic equality decidable，則 $M$ 有 normal realization。

### Construction

對 $a\in F$ 定義：

$$
\Lambda(a)
:=
\min_{\prec_{\mathrm{Code}}}
\left\{
 b\in F:
 b\equiv_{\mathcal I}a
\right\}.
$$

集合非空，因 $a$ 本身為候選。

由：

- $F$ decidable；
- semantic equality decidable；
- $a$ 之前候選 finite；

可 finite 搜尋最小者。

此 $\Lambda$ preserve denotation，且 image 上 representation unique，故 normal。

定義「**equality-decidable exact-realizable**」為：存在至少一個 exact realization，其 semantic equality 在該 representation 上可有限判定。結合 Theorem 51.1，得到精確的 existence statement：

$$
\boxed{
\text{equality-decidable exact-realizable}
\iff
\text{normal-realizable}
\iff
\text{perfect-realizable}.
}
$$

反向方向也成立：perfect realization 的 semantic equality 就是 code equality；normal realization 則可用 terminating normalizer 判斷 $\Lambda(a)=\Lambda(b)$，所以 semantic equality finite decidable。

因此**不能無條件把左側縮寫成單純 `exact-realizable`**。只有在額外 theorem（例如 §54 的 diagonal criterion）保證任何所考慮 exact realization 都具有 finite semantic-equality decision 時，才可在該 context 中簡寫成 exact / normal / perfect 三者 existence collapse。

---

# 54. Equality from primitive binary relations

令：

$$
\Delta_X:=\{(x,x):x\in X\}.
$$

若 exact realization 中的 finitely decidable primitive binary relations 經有限 union / intersection 可構造 $\Delta_X$，則 diagonal membership decidable，因而 semantic equality decidable。

更一般地，只要 $\Delta_X$ 屬於這些 decidable binary relations 所生成的 finite Boolean algebra 即可。

---

# Part X — Computable real numbers

# 55. Standard rational exact representation

取一個 perfect / exact rational interpretation：

$$
\mathcal I_{\mathbb Q}
=
(F_{\mathbb Q},F_{\mathbb Q},\llbracket\cdot\rrbracket_{\mathbb Q}).
$$

Runtime `Rational` 的 mutable working states不必直接作此 formal perfect representation；formal theory 可使用 canonical reduced fraction codes。

---

## 55.1 Gaussian rational exact representation

定義

$$
\mathbb Q(i):=\{a+bi:a,b\in\mathbb Q\}.
$$

由 canonical rational perfect interpretation $\mathcal I_{\mathbb Q}$ 可建立 product interpretation：canonical code 為 ordered pair of canonical rational codes，denotation

$$
(a,b)\longmapsto a+bi.
$$

因此 $\mathbb Q(i)$ 有 finite exact / bilateral representation。其：

- equality；
- zero test；
- realness；
- conjugation；
- field operations；
- coordinate projections；

皆由有限 rational algorithms構造。

Rational closed rectangle 定義為

$$
[a,b]\times[c,d],\qquad a,b,c,d\in\mathbb Q,
$$

並在 runtime 以 `((a,b),(c,d))` 表示。其 four corners 與 center 皆屬 $\mathbb Q(i)$。因此 $\mathbb Q(i)$ 可作為複平面的 exact finite probe domain，而不需引入 general algebraic-root representation。

---

# 56. Semantic comparison outcome

對 $x\in\mathbb R$、$q\in\mathbb Q$，定義：

$$
\operatorname{cmp}(x,q)
=
\begin{cases}
\mathsf{LESS},&x<q,\\
\mathsf{EQUAL},&x=q,\\
\mathsf{GREATER},&x>q.
\end{cases}
$$

固定三元素集合：

$$
\mathsf{Order}:=\{\mathsf{LESS},\mathsf{EQUAL},\mathsf{GREATER}\}
$$

的一個 bilateral finite interpretation：

$$
\mathcal I_{\mathsf{Order}}
=
(F_{\mathsf{Order}},D_{\mathsf{Order}},\llbracket\cdot\rrbracket_{\mathsf{Order}}).
$$

因 $\mathsf{Order}$ finite，此選擇只負責把 finite outcome 落到 Code；它不是一般 relation-family realizability 的 canonical-output 假設。

---

# 57. Resumable rational comparator

對固定 real $x$，一個 rational semantic comparator 由一個 **total computable typed constructor**：

$$
\Sigma:F_{\mathbb Q}\to F_{\mathsf{Configuration}}
$$

組成。對每個 rational code $q\in F_{\mathbb Q}$，$\Sigma(q)$ 是 self-contained resumable computation configuration。

若該 configuration 在有限步後 halt，要求其 output $o$ 滿足：

$$
o\in D_{\mathsf{Order}}
$$

且：

$$
\llbracket o\rrbracket_{\mathsf{Order}}
=
\operatorname{cmp}(x,\llbracket q\rrbracket_{\mathbb Q}).
$$

此外必滿足 semi-decision termination condition：

1. 若 $x<\llbracket q\rrbracket_{\mathbb Q}$，execution 必在有限步後 halt；
2. 若 $x>\llbracket q\rrbracket_{\mathbb Q}$，execution 必在有限步後 halt；
3. 若 $x=\llbracket q\rrbracket_{\mathbb Q}$，允許 infinite execution；若該 representation 另有 equality capability，也允許 finite halt with `EQUAL`。

Comparator **construction** 必 finite；potential divergence 只存在於 returned configuration 的 execution。

Comparison orientation 固定為 runtime 採用的 receiver-first convention $x\mathrel? q$。

---

# 58. Computable real

## Definition 58.1

Real number $x\in\mathbb R$ 稱 computable iff存在 rational semantic comparator constructor $\Sigma$ 如 Definition 57。

記所有 computable reals：

$$
\mathbb R_C.
$$

此定義把 rational semi-decision comparison 直接落在 explicit Program / Configuration machine theory 上。

## Definition 58.2 — Comparator-program presentation of computable reals

為了讓不同 semantic representations 能有效地「送進同一個 computable-real system」，固定下列 first-class presentation。令

$$
F_{\mathrm{CR}}:=F_{\mathsf{Program}}.
$$

對 $p\in F_{\mathrm{CR}}$，若其 underlying program 在每個 rational code

$$
q\in F_{\mathbb Q}
$$

上都 finite halt，並輸出一個 first-class `Configuration` code，且所得 total constructor

$$
\Sigma_p:F_{\mathbb Q}\to F_{\mathsf{Configuration}}
$$

對某個 $x\in\mathbb R$ 滿足 Definition 57 的 rational semantic comparator contract，則稱 $p$ 為 $x$ 的 **computable-real presentation code**。令所有這類 codes 的集合為

$$
D_{\mathrm{CR}}\subseteq F_{\mathrm{CR}}.
$$

這裡 $F_{\mathrm{CR}}$ 只保證 program syntax well-formed；「此 program 確實 total construct 一個 sound rational comparator」是 semantic promise，因此一般不要求 $D_{\mathrm{CR}}$ Code-decidable。

### Proposition 58.3 — Denotation uniqueness

若同一個 $p\in D_{\mathrm{CR}}$ 同時滿足 Definition 57 對 $x,y\in\mathbb R$ 的 comparator contract，則 $x=y$。

若反設 $x<y$，由 $\mathbb Q$ 在 $\mathbb R$ 中稠密，可取

$$
x<q<y.
$$

同一個 configuration $\Sigma_p(q)$ 若代表 $x$，其 strict comparison 必 finite halt with `LESS`；若代表 $y$，同一 deterministic computation 又必 finite halt with `GREATER`，矛盾。$y<x$ 同理。

因此可定義 semantic interpretation

$$
\boxed{
\mathcal I_{\mathrm{CR}}
:=
(F_{\mathrm{CR}},D_{\mathrm{CR}},\llbracket\cdot\rrbracket_{\mathrm{CR}})
}
$$

其中

$$
\llbracket p\rrbracket_{\mathrm{CR}}
$$

是 $p$ 唯一表示的 computable real。由 Definition 58.1，每個 $x\in\mathbb R_C$ 至少有一個 comparator program presentation，故

$$
\llbracket\cdot\rrbracket_{\mathrm{CR}}:D_{\mathrm{CR}}\to\mathbb R_C
$$

為 surjection。這個 interpretation 不宣稱 canonicality、bilaterality 或 semantic-domain decidability。

## Definition 58.4 — Effectively computable-real-presented interpretation

令 $S\subseteq\mathbb R_C$ 且

$$
\mathcal I_S=(F_S,D_S,\llbracket\cdot\rrbracket_S)
$$

為 semantic interpretation。稱 $\mathcal I_S$ **effectively computable-real-presented**，若存在 terminating promised-domain typed algorithm

$$
E_S:D_S\to D_{\mathrm{CR}}
$$

使所有 $a\in D_S$ 都滿足

$$
\boxed{
\llbracket E_S(a)\rrbracket_{\mathrm{CR}}
=
\llbracket a\rrbracket_S.
}
$$

也就是 representation code 可以在 finite work 後被編譯／嵌入到共同的 comparator-program presentation，而不改變 mathematical denotation。這不要求 $E_S$ injective；「presentation」描述的是 semantic inclusion / compilation capability，不是 code identity。

---

# 59. Distinct computable reals have finite separation evidence

## Proposition 59.1 — Uniform resumable comparison from presentations

存在一個 terminating computable constructor，輸入

$$
p_x,p_y\in D_{\mathrm{CR}},
$$

finite 建立 receiver-first resumable comparison of

$$
x:=\llbracket p_x\rrbracket_{\mathrm{CR}},
\qquad
y:=\llbracket p_y\rrbracket_{\mathrm{CR}}.
$$

其 behavior 為：

- $x<y$ 時 eventually halt with `LESS`；
- $x>y$ 時 eventually halt with `GREATER`；
- $x=y$ 時允許 diverge；若另有 equality evidence，也允許 finite halt with `EQUAL`。

### Construction

Effective enumerate rational codes $q_0,q_1,\ldots$。對每個 $q_i$，由 $p_x,p_y$ finite construct

$$
x\mathrel? q_i,
\qquad
y\mathrel? q_i
$$

兩個 comparator configurations，並對所有 active branches fair dovetail。若某個 $q_i$ 得到

$$
x<q_i<y,
$$

resolve `LESS`；若得到

$$
y<q_i<x,
$$

resolve `GREATER`。

若 $x\ne y$，由 density of $\mathbb Q$ 存在 strict separating rational；對該 rational 的兩個 strict comparator processes 都 finite halt，因此 fair scheduler eventually取得 finite separation evidence。若 $x=y$，不存在 strict separating rational，所以 construction 可永久繼續。

因此 distinct computable reals具有 finite separation evidence，而且這個 evidence extraction 對 presentation codes 是 uniform 的。Equality 本身不因此變成 finite decidable。

---

# 60. Certified rational enclosure from comparator

## Theorem 60.1

若 $x\in\mathbb R_C$ 以 rational semantic comparator表示，則對任意：

$$
\varepsilon\in\mathbb Q,
\qquad
\varepsilon>0,
$$

存在 terminating algorithm輸出 rationals $L,R$ 使：

$$
L\le x\le R,
$$

$$
R-L\le\varepsilon.
$$

### Proof idea

Effective enumerate all rational pairs $(L,R)$ satisfying：

$$
L<R,
\qquad
R-L\le\varepsilon.
$$

對每對同時啟動 comparator processes：

$$
x\mathrel?L,
\qquad
x\mathrel?R.
$$

以 fair dovetailing interleave。

由 rational density，可選 strict bracket：

$$
L<x<R
$$

且 width滿足 $\varepsilon$。該 pair 的兩個 strict comparisons 都會 finite resolve，所以 fair scheduler 最終找到它。

此 construction 不要求測試 $x$ 是否等於某個 query rational，因此避免 exact-hit bisection nontermination。

---

# 61. Comparator from shrinking certified enclosure

## Theorem 61.1

若 representation 能對每個 $n$ terminating輸出：

$$
L_n\le x\le R_n,
$$

且：

$$
R_n-L_n\to0
$$

effectively，則可構造 rational semantic comparator。

給 $q\in\mathbb Q$：

- 若 $R_n<q$，resolve `LESS`；
- 若 $L_n>q$，resolve `GREATER`；
- 否則 refine。

若 $x\ne q$，eventually interval width小於 $|x-q|$，必 strict separate。

若 $x=q$，可永久 unresolved。

## Proposition 61.2 — Effective rational-affine closure of presentations

存在 terminating computable constructors，使對任意

$$
p_x,p_y\in D_{\mathrm{CR}},
\qquad
a,b,c\in\mathbb Q,
$$

可 finite construct $p\in D_{\mathrm{CR}}$ 代表

$$
a\llbracket p_x\rrbracket_{\mathrm{CR}}
+b\llbracket p_y\rrbracket_{\mathrm{CR}}+c.
$$

特別地，可 finite construct presentations for

$$
x+r,
\qquad
\frac{x+y}{2}
$$

for every rational $r$。

### Proof idea

對 requested stage $n$，利用 Theorem 60.1 對 operands取得 sufficiently narrow certified rational enclosures，再以 exact rational interval arithmetic 得到 affine image enclosure。可有效選擇 operand widths，使 resulting enclosure width趨於 $0$ effectively。Theorem 61.1 因而把這組 shrinking certified enclosures編譯成 rational semantic comparator。Program / Configuration 的 first-class encoding與 universal simulation使整個 wrapper construction可由 input presentation codes finite 產生，而不需要先決定任何 operand equality。

因此 $D_{\mathrm{CR}}$ 在 rational affine constructions 下具有 uniform effective closure；後續 grid midpoint probes不需要另列為 independent representation hypothesis。

---

# 62. Computable complex

定義：

$$
\mathbb C_C
:=
\{a+bi:a,b\in\mathbb R_C\}.
$$

因此：

$$
z\in\mathbb C_C
$$

的 real / imaginary coordinate 都 computable real。

但：

$$
z\in\mathbb R
\iff
\operatorname{Im}z=0
$$

所以一般 realness 不 guaranteed finite decidable。

---

# Part XI — Searchable grids

# 63. Extended real set for grid mathematics

為 grid theorem 的純數學方便，記：

$$
\overline{\mathbb R}
:=
\mathbb R\cup\{-\infty,+\infty\}.
$$

這不表示 runtime `Rational` 包含 infinity；runtime 可用 separate endpoint sentinels。

只在本 Part 的 grid-distance notation 中，對 finite $x\in\mathbb R$ 約定：

$$
|(+\infty)-x|=|(-\infty)-x|:=+\infty,
$$

並採 $\inf\varnothing:=+\infty$。這只是 extended-real theorem notation，不把 infinity 當成 numeric-runtime value。
特別地，此 distance convention 只服務 grid-localization theorem；它不是 IEEE-754 rounding metric。故含 $\pm\infty$ 的 binary64 grid 可以用 infinity 作 global bracket endpoint，但 finite target 的 strict-nearest winner 不會是 infinity。

---

# 64. Locally finite grid

$G\subseteq\overline{\mathbb R}$ 稱 locally finite iff對每個 real bounded interval：

$$
[a,b],
\qquad a<b,
$$

有：

$$
|G\cap[a,b]|<\infty.
$$

---

# 65. Adjacency and near-adjacency

對 $L,R\in G$：

## Adjacent

$$
(L,R)\text{ is }G\text{-adjacent}
$$

iff：

$$
L\le R
$$

且：

$$
G\cap(L,R)=\varnothing.
$$

## Near-adjacent

$$
(L,R)\text{ is }G\text{-near-adjacent}
$$

iff：

$$
L\le R
$$

且：

$$
|G\cap(L,R)|\le1.
$$

---

# 66. Effective searchable and computably embedded grids

令

$$
\mathcal I_G
=
(F_G,D_G,\llbracket\cdot\rrbracket_G)
$$

為 grid $G\subseteq\overline{\mathbb R}$ 的 semantic interpretation。定義 promised input domain

$$
D_G^{\ne}
:=
\left\{
(a,b)\in D_G^2:
\llbracket a\rrbracket_G\ne\llbracket b\rrbracket_G
\right\},
$$

以及 finite-valued grid-code domain

$$
\boxed{
D_G^{\mathrm{fin}}
:=
\left\{
a\in D_G:
\llbracket a\rrbracket_G\in\mathbb R
\right\}.
}
$$

$D_G^{\mathrm{fin}}$ 排除可能存在的 $\pm\infty$ grid sentinels；不要求 arbitrary code 的 finite-valued membership 本身可判定。

這裡 $D_G\sqcup\{\mathsf{None}\}$ 表示一個固定 tagged option output format；$\mathsf{None}$ 不屬於 $D_G$。

## Definition 66.1 — Searchable grid interpretation

稱 $\mathcal I_G$ **searchable**，若存在 terminating typed algorithm

$$
\Lambda_G:
D_G^{\ne}
\longrightarrow
D_G\sqcup\{\mathsf{None}\}
$$

使對每個 $(a,b)\in D_G^{\ne}$，令

$$
\ell(a,b)
:=
\min\!\left(
\llbracket a\rrbracket_G,
\llbracket b\rrbracket_G
\right),
$$

$$
u(a,b)
:=
\max\!\left(
\llbracket a\rrbracket_G,
\llbracket b\rrbracket_G
\right).
$$

則滿足：

1. **Symmetry**

$$
\Lambda_G(a,b)=\Lambda_G(b,a).
$$

2. **Adjacent case**

若

$$
G\cap(\ell(a,b),u(a,b))=\varnothing,
$$

則

$$
\Lambda_G(a,b)=\mathsf{None}.
$$

3. **Non-adjacent case**

若

$$
G\cap(\ell(a,b),u(a,b))\ne\varnothing,
$$

則

$$
\Lambda_G(a,b)\in D_G
$$

且

$$
\ell(a,b)
<
\llbracket\Lambda_G(a,b)\rrbracket_G
<
u(a,b).
$$

因此對 denotationally distinct endpoints，

$$
\boxed{
\Lambda_G(a,b)=\mathsf{None}
\iff
G\cap(\ell(a,b),u(a,b))=\varnothing.
}
$$

任一滿足上述條件的 $\Lambda_G$ 稱為 $\mathcal I_G$ 的 **search algorithm**。

**Terminology discipline.** `locally finite` 是 underlying set $G$ 的純數學性質；`searchable` 則是 interpretation $\mathcal I_G$ 的 effective property。即使 context 已固定 representation，後文在 formal statement 中仍保留這個區分，不把 searchability 當成集合 $G$ 單獨的性質。

這一定義只要求在 promised semantic domain $D_G^{\ne}$ 上 finite termination；不要求 runtime 能有限判斷 arbitrary $(a,b)\in F_G^2$ 是否屬於 $D_G^{\ne}$。這與 §31 的 partial typed algorithm convention 一致。

## Definition 66.2 — Equality-decidable grid interpretation

稱 grid interpretation $\mathcal I_G$ **equality-decidable**，若 §52 的 semantic equality 對 $\mathcal I_G$ 可有限判定；也就是存在 terminating classifier，其 promised domain 為 $D_G^2$，並對每個 $(a,b)\in D_G^2$ 正確判斷

$$
\llbracket a\rrbracket_G=\llbracket b\rrbracket_G.
$$

這只是 representation capability，不是 underlying set $G$ 的集合論性質。

## Definition 66.3 — Exact ordered grid realization

對 $G\subseteq\overline{\mathbb R}$，令其 **ordered-grid structure** 為

$$
\mathbf{Ord}(G)
:=
\left(
G;
\mathcal O_G
\right),
$$

其中沒有 primitive constants / operations，而唯一 primitive relation family 是 extended-real order trichotomy

$$
\mathcal O_G
:=
\{O_<^G,O_=^G,O_>^G\},
$$

$$
O_<^G:=\{(x,y)\in G^2:x<y\},
$$

$$
O_=^G:=\{(x,y)\in G^2:x=y\},
$$

$$
O_>^G:=\{(x,y)\in G^2:x>y\}.
$$

稱 $\mathcal I_G$ 為 $G$ 的 **exact ordered grid realization**，若它是 $\mathbf{Ord}(G)$ 的 exact realization。由 Definition 47.1，這立即給出

$$
F_G=D_G
$$

以及 grid-point order trichotomy的 finite total classification；特別地，$\mathcal I_G$ 自動 equality-decidable。

## Definition 66.4 — Effective computable-real embedding of finite grid points

稱 grid interpretation $\mathcal I_G$ **effectively computable-real embeddable**，若存在 terminating promised-domain typed algorithm

$$
\boxed{
E_G:D_G^{\mathrm{fin}}\to D_{\mathrm{CR}}
}
$$

使對每個 finite-valued grid code $a\in D_G^{\mathrm{fin}}$，

$$
\boxed{
\llbracket E_G(a)\rrbracket_{\mathrm{CR}}
=
\llbracket a\rrbracket_G.
}
$$

也就是下圖 commute：

$$
\begin{array}{ccc}
D_G^{\mathrm{fin}} & \xrightarrow{\;E_G\;} & D_{\mathrm{CR}}\\[4pt]
\downarrow\scriptstyle{\llbracket\cdot\rrbracket_G} &&\downarrow\scriptstyle{\llbracket\cdot\rrbracket_{\mathrm{CR}}}\\[4pt]
G\cap\mathbb R & \hookrightarrow & \mathbb R_C.
\end{array}
$$

「embedding」指的是 mathematical inclusion $G\cap\mathbb R\hookrightarrow\mathbb R_C$ 被 representation-level terminating algorithm effective realize；**不要求 $E_G$ 在 code level injective**。

這個條件比單純集合論敘述

$$
G\cap\mathbb R\subseteq\mathbb R_C
$$

更強：後者只說每個 finite grid value 存在某個 computable-real representation；Definition 66.4 要求從 arbitrary finite grid code **uniformly 且 finite 地產生**一個同值 presentation。這正是 grid points 能被拿去和一般 semantic computable reals共同計算所需的 bridge。

## Definition 66.5 — Computably embedded exact ordered grid realization

稱 $\mathcal I_G$ 為 **computably embedded exact ordered grid realization**，若：

1. $\mathcal I_G$ 是 Definition 66.3 的 exact ordered grid realization；
2. $\mathcal I_G$ 滿足 Definition 66.4 的 effective computable-real embedding。

若另外滿足 Definition 66.1，稱之為 **searchable computably embedded exact ordered grid realization**。

因此本 Part 的分層為：

1. `locally finite`：underlying set 的純數學性質；
2. `exact ordered`：grid code 內部的 equality / order finite exactness；
3. `computably embedded`：finite grid points 能 finite 編譯進共同 $\mathbb R_C$ presentation；
4. `searchable`：grid interval interior 是否存在 grid point可在 promised distinct-endpoint domain finite search。

v1 standard runtime grids採第 2–4 項的完整組合。這避免把 target-grid comparison與 midpoint comparison當成每個 localization theorem 都要重複列出的 ad hoc cross-capabilities。

### Example 66.6 — Scalar images of rational grids

令 $N\ge1$，固定一個已給定 presentation $p_\alpha\in D_{\mathrm{CR}}$ 的 $\alpha\in\mathbb R_C$，且先驗知道 $\alpha\ne0$，並考慮

$$
\alpha G_N:=\{\alpha q:q\in G_N\}.
$$

可用 $G_N$ 的 canonical rational code表示 $\alpha q$。因 $\alpha\ne0$，

$$
\alpha q_1=\alpha q_2
\iff
q_1=q_2,
$$

所以 semantic equality 可由 rational equality finite decide，而不必把兩個 ambient computable-real values丟進一般 equality problem。由 Proposition 61.2，給 rational code $q$ 可 finite construct presentation for $\alpha q$，因此此 representation滿足 Definition 66.4 的 effective computable-real embedding。又因乘上一個 fixed finite nonzero scalar 是 $\mathbb R$ 上的 homeomorphism，$G_N$ locally finite立即推出 $\alpha G_N$ locally finite。因 nonzero scalar multiplication保留 betweenness（$\alpha<0$ 時只反轉 orientation），$G_N$ 的 interior-search algorithm也可直接 transport，故此 interpretation searchable。若此外 $\operatorname{sgn}(\alpha)$ 也是 construction data 中 finitely certified 的資訊，則 order亦可由 rational order（必要時反向）finite classify，因此得到 computably embedded exact ordered grid realization。

---

# 67. Bounding and derived cross-representation capabilities

令 $S\subseteq\mathbb R_C$ 有 semantic interpretation

$$
\mathcal I_S=(F_S,D_S,\llbracket\cdot\rrbracket_S).
$$

## Definition 67.1 — Two-sided bounding

稱 $\mathcal I_G$ **two-sided-bounding for $\mathcal I_S$**，若存在 terminating typed algorithm $B$，對每個 $x\in D_S$ 回

$$
B(x)=(a,b)\in D_G^2
$$

使

$$
\llbracket a\rrbracket_G
\le
\llbracket x\rrbracket_S
\le
\llbracket b\rrbracket_G.
$$

不要求 $a,b$ 為有限實數；例如 extended binary64 grid可使用 $\pm\infty$ sentinels。

特別地，若 $\mathcal I_G$ two-sided-bounding for $\mathcal I_{\mathrm{CR}}$，則稱其具有 **global computable-real bounding**。若 $\mathcal I_S$ effectively computable-real-presented，先套 $E_S$ 再套此 global bound，即自動得到對 $\mathcal I_S$ 的 two-sided bounding。

## Proposition 67.2 — Embedding induces uniform target-grid resumable comparison

若：

1. $\mathcal I_S$ effectively computable-real-presented；
2. $\mathcal I_G$ effectively computable-real embeddable；

則對所有 codes representing

$$
x\in S,
\qquad
g\in G\cap\mathbb R,
$$

可在 promised domain 上 finite construct self-contained receiver-first resumable comparison

$$
x\mathrel?g.
$$

Construction只是先 finite 得到

$$
E_S(x),\qquad E_G(g)\in D_{\mathrm{CR}},
$$

再套 Proposition 59.1。故：

- $x<g$ 時 eventually `LESS`；
- $x>g$ 時 eventually `GREATER`；
- $x=g$ 時允許 diverge，若另有 equality evidence也可 `EQUAL`。

若 grid 含 $\pm\infty$ sentinels，target 與 sentinel 的 extended-real order直接 finite known。

因此「uniform target-grid comparability」不是 computably embedded grid theorem 的額外 hypothesis，而是 representation embedding 的 derived capability。

## Proposition 67.3 — Embedding induces finite-pair midpoint probes

在 Proposition 67.2 的 hypotheses 下，對任意 finite grid codes

$$
a,b\in D_G^{\mathrm{fin}},
$$

不要求 adjacency，可在 promised domain 上 finite construct target $x$ 與

$$
m(a,b)
:=
\frac{\llbracket a\rrbracket_G+\llbracket b\rrbracket_G}{2}
$$

的 resumable comparison。

Indeed，先由 $E_G(a),E_G(b)$ 取得同值 computable-real presentations；Proposition 61.2 finite construct midpoint presentation，再由 Proposition 59.1 與 $E_S(x)$ 建立 target-vs-midpoint comparison。Strict cases finite halt，equality case允許 diverge。

這比只對 adjacent endpoints 要求 midpoint-probe capability 更強：**任意兩個 finite grid points** 的 midpoint都可被送進同一 computable-real system。因而 near-nearest projection、promised strict-nearest construction、mixed-format localization，以及任何只需要有限個 grid-point rational-affine combinations 的後續 theorem，都不必再額外列 midpoint constructor hypothesis。

---

# 68. First termination theorem — Near-adjacent localization

## Theorem 68.1 — Localization Theorem 1: unconditional near-adjacent enclosure

令 $S\subseteq\mathbb R_C$、$G\subseteq\overline{\mathbb R}$，並固定 interpretations $\mathcal I_S$、$\mathcal I_G$。若：

1. $G$ locally finite；
2. $\mathcal I_G$ searchable；
3. $\mathcal I_G$ 是 computably embedded exact ordered grid realization；
4. $\mathcal I_G$ two-sided-bounding for $\mathcal I_S$；
5. $\mathcal I_S$ effectively computable-real-presented；

則存在 terminating algorithm，對每個 semantic code representing $x\in S$ 回 $L,R\in G$ 使：

$$
L\le x\le R,
$$

且：

$$
\boxed{|G\cap(L,R)|\le1.}
$$

### Proof / termination mechanism

核心不是列舉 initial bracket 中的所有 grid points，而是**只沿著 target 所在位置 adaptive refinement**。

由 two-sided-bounding 取得 current bracket codes $a,b\in D_G$，其 denotations 滿足

$$
\llbracket a\rrbracket_G
\le x\le
\llbracket b\rrbracket_G.
$$

先用 exact ordered grid realization 所提供的 equality classifier finite 判斷

$$
\llbracket a\rrbracket_G
=
\llbracket b\rrbracket_G.
$$

若相等，則 bracket contract 立即推出

$$
x=\llbracket a\rrbracket_G=\llbracket b\rrbracket_G,
$$

可直接回 point bracket。若不相等，才在已 certified 屬於 $D_G^{\ne}$ 的 promised domain 上呼叫 search algorithm $\Lambda_G$：

- 若回 $\mathsf{None}$，則 $(a,b)$ 已 $G$-adjacent，直接回傳；
- 否則得到 strict-interior witness

$$
a<g<b,
\qquad g\in G.
$$

除 $x\mathrel? g$ 的 resumable comparison 外，同時 fair-dovetail 一個 **exact-hit rescue branch**：

1. 從 $(a,g)$ 沿 $g$ 的方向反覆使用 $\Lambda_G$。若 search 回 interior witness $h$，以 $(h,g)$ 繼續；若回 $\mathsf{None}$，得到 $g$ 的 current-left adjacent neighbor $g^-$.  
2. 同理從 $(g,b)$ 得到 current-right adjacent neighbor $g^+$.  
3. 對 receiver-first processes
   $$
   x\mathrel?g^-,
   \qquad
   x\mathrel?g^+
   $$
   作 fair dovetail。若第一個 resolve `GREATER`、第二個 resolve `LESS`，即可證
   $$
   g^-<x<g^+,
   $$
   就回
   $$
   (g^-,g^+).
   $$
   因 $(g^-,g)$ 與 $(g,g^+)$ 都 adjacent，故
   $$
   G\cap(g^-,g^+)\subseteq\{g\},
   $$
   所以此 output 為 near-adjacent bracket。

這個 rescue branch 在 $x=g$ 時一定 finite resolve，而完全不需要判定 equality：$g$ 是 finite real grid point；若 $a=-\infty$，第一次在 $(-\infty,g)$ 找到 strict-interior witness後便得到 finite left endpoint，之後所有 refinement 都落在 bounded interval；由 local finiteness，只能再經過 finitely many grid points 才到達 $g$ 的 adjacent neighbor。右側同理。若某側本來就與 $g$ adjacent，則該側立即完成。最後 $g^-<g<g^+$，所以在 $x=g$ 時兩個 endpoint strict comparisons 都 finite resolve。

另一方面，main comparison $x\mathrel?g$ 若在 finite work 中 resolve：

- `LESS`：令 resulting bracket 為 $(a,g)$；
- `GREATER`：令 resulting bracket 為 $(g,b)$；
- `EQUAL`（representation 恰有 equality evidence）：直接回 point bracket $(g,g)$。

若 $x\ne g$，main comparison 必在 finite work 後以 strict outcome resolve；若 $x=g$ 而沒有 equality evidence，則由前述 rescue branch finite resolve。因此每一輪都會在 finite time 內**要嘛直接回 near-adjacent bracket，要嘛以一個 strict-interior witness 取代 current bracket 的其中一端**。

現在證明不可能有 infinitely many successful side refinements。

第一次取得 finite witness $g$ 後，current bracket 至少有一個 finite endpoint。假設例如 finite right endpoint $r>x$ 已存在而 left endpoint 仍可能為 $-\infty$。只要後續 search witness 仍落在 $x$ 的右側，每次 refinement 都產生 strictly decreasing grid values

$$
r>r_1>r_2>\cdots>x.
$$

但所有這些值都落在 bounded interval $[x,r]$ 中；由 local finiteness，該 interval 只含 finitely many grid points。因此這種 same-side refinement 不可能無限持續。有限步後必發生下列之一：

- search 已得到 adjacent bracket；
- witness 落到 $x$ 左側，於是另一個 endpoint 也變成 finite；
- witness 恰為 $x$，exact-hit rescue branch finite resolve。

一旦兩個 current endpoints 都 finite，整個 current bounded interval 中只有 finitely many grid points。之後每次 strict-side refinement 都丟棄至少一個 current strict-interior grid point，因此也只能發生 finitely many 次。

故 algorithm 必 finite terminate，並回滿足

$$
L\le x\le R,
\qquad
|G\cap(L,R)|\le1
$$

的結果。

特別地，**initial bracket 本身不需要包含 finitely many grid points**。即使 initial bracket 為

$$
(-\infty,+\infty)
$$

且其中有 infinitely many grid points，$G$ 的 local finiteness + $\mathcal I_G$ 的 searchable adaptive refinement 已足以保證 termination。對整個 initial bracket 做 exhaustive enumeration 只是某些特殊 grid 上可行的 implementation strategy，不是 theorem hypothesis，也不是一般 proof 所需步驟。

### Corollary 68.2 — Standard v1 grids

對 runtime `ComputableReal` representation，formal compiler提供 Definition 58.4 的 effective $E_S$。三個 standard grids另具有下列 canonical embedding。

#### Integer grid

$$
G_{\mathbb Z}:=\mathbb Z.
$$

$G_{\mathbb Z}$ locally finite，而 canonical integer representation是 searchable computably embedded exact ordered grid realization：order/equality由 integer arithmetic finite classify；finite grid code $n$ 可 finite lift 成 exact rational comparator presentation of $n$。Theorem 60.1 的 finite rational enclosure再取 exact floor / ceil，提供對 $\mathcal I_{\mathrm{CR}}$ 的 global two-sided bounding。

#### Bounded-denominator rational grid

對 $N\ge1$：

$$
G_N
=
\left\{
\frac pq\in\mathbb Q:
1\le q\le N,
\gcd(|p|,q)=1
\right\}.
$$

它 locally finite；canonical reduced-rational interpretation exact-realizes $\mathbf{Ord}(G_N)$，而每個 finite grid point本來就是 rational，故可 finite lift成同值 $D_{\mathrm{CR}}$ presentation。給定兩個 finite rational endpoints，可對 $1\le q\le N$ 與相應 bounded numerator range作 finite exact enumeration，因而得到 terminating search algorithm；實作可改用 continued-fraction / Farey fast path。又因 $\mathbb Z\subseteq G_N$，對 arbitrary computable-real presentation先取 finite rational enclosure，再取 integer outer endpoints即提供 global two-sided bound。

#### Extended Binary64 grid

令 $F_{64}$ 為 binary64 的 finite real values，將 signed zero 在 grid denotation中識別為同一個 $0$，並定義

$$
G_{64}:=F_{64}\cup\{-\infty,+\infty\}.
$$

NaN 不屬於 $G_{64}$。$G_{64}$ 本身 finite，因此特別是 locally finite；canonical bit-pattern / infinity-sentinel interpretation exact-realizes $\mathbf{Ord}(G_{64})$ 且具有 terminating interior search。每個 finite binary64 code可 finite exact decode成 dyadic rational，再 lift成同值 $D_{\mathrm{CR}}$ presentation，所以 finite-point embedding成立。$(-\infty,+\infty)$ distinguished endpoints提供 global two-sided bound；target 與 sentinel 的 order finite known。

因此三個 v1 standard grids 的 canonical interpretations都是 **searchable computably embedded exact ordered grid realizations**，且都 globally two-sided-bound $\mathcal I_{\mathrm{CR}}$。Target-grid comparison與任意 finite-pair midpoint probe分別由 Propositions 67.2 / 67.3 自動導出，不是 standard-grid corollary 需要逐一另證的獨立 capability。

---

# 69. Second termination theorem — Adjacent localization under the off-grid promise

## Theorem 69.1 — Localization Theorem 2: promised-optimal enclosure

在 Theorem 68.1 的 hypotheses 下，若另外有 semantic promise

$$
S\cap G=\varnothing,
$$

則存在 terminating algorithm，對每個 semantic code representing $x\in S$ 回 $L,R\in G$ 使

$$
L\le x\le R,
$$

且

$$
\boxed{G\cap(L,R)=\varnothing.}
$$

也就是回傳真正的 $G$-adjacent bracket，而不是只保證 near-adjacent。

### Proof

先執行 Theorem 68.1，得到

$$
L\le x\le R,
\qquad
|G\cap(L,R)|\le1.
$$

因 $x\notin G$，不可能有 $L=R$。對 distinct endpoint codes 使用 searchable-grid algorithm：

- 若回 $\mathsf{None}$，則 $(L,R)$ 已 adjacent，直接回傳；
- 否則，由 near-adjacent contract，searcher 回到的 strict-interior witness $g$ 是 $(L,R)$ 中唯一的 grid point，因此 $(L,g)$ 與 $(g,R)$ 都 adjacent。

由 off-grid promise 有 $x\ne g$。Definition 66.4 與 Proposition 67.2 提供 $x\mathrel?g$ 的 resumable comparison，而此處必為 strict case，所以 finite resolve：

- 若 $x<g$，由 $L\le x<g$ 回 $(L,g)$；
- 若 $x>g$，由 $g<x\le R$ 回 $(g,R)$。

兩種輸出都是真正 adjacent bracket，故 finite terminate。

值得特別記錄的是：這個 construction 在 promise 外仍是 **sound partial search**。若 $x=g$，它不需要輸出任何結果；若 comparison 有 explicit equality evidence，可把該 branch 留在 non-emitting terminal/pending state。所有真正輸出的 bracket 仍然 sound。Promise只負責 termination；這個「promise 外不亂輸出」的性質也讓此 search可以安全地和其他 partial search fair-dovetail。

### Interpretation

Theorem 68.1 的次佳退讓只是在避免判定

$$
x=g
$$

這個 exact grid-hit boundary。當使用者／上層 theorem 已承諾

$$
x\notin G,
$$

這個障礙消失，near-adjacent bracket便可 guaranteed-finite 升級成 adjacent bracket。

因此 Localization Theorem 1 / 2 形成 enclosure pair：

$$
\boxed{
\text{unconditional near-adjacent}
\quad\longrightarrow\quad
\text{off-grid promised adjacent}.
}
$$

## Theorem 69.2 — Exact grid-point identification under a grid-membership promise

Assume the hypotheses of Theorem 68.1 and let $x\in\mathbb R$ be the target. Under the additional semantic promise

$$
x\in G,
$$

there is a terminating promised-domain algorithm that returns a finite grid code $g$ with

$$
\llbracket g\rrbracket_G=x.
$$

### Proof

Run Theorem 68.1 and obtain a near-adjacent bracket

$$
L\le x\le R,
\qquad
|G\cap(L,R)|\le1.
$$

Use the searchable-grid procedure on distinct finite/code endpoints where applicable. The finite grid values that can equal $x$ are contained in the finite candidate set consisting of the finite-valued endpoints together with the at-most-one strict-interior witness. Infinity sentinels are excluded because $x$ is finite. Thus there are at most three finite candidates.

For every candidate $g_i$, use Proposition 67.2 to run the resumable comparison $x\mathrel?g_i$ in fair dovetail. The promise $x\in G$ implies exactly one candidate denotes $x$. Every other candidate is denotationally distinct from $x$, so Proposition 59.1 gives finite strict-separation evidence for it. Hence after finite total work every wrong candidate has been eliminated. The unique remaining candidate must denote $x$ by the promise, even if its equality comparison itself never resolves.

Therefore exact grid-point identification terminates without requiring a total equality classifier for arbitrary computable reals. $\square$

### Interpretation

The computational content of

$$
x\in\mathbb Q
$$

and

$$
x\in G_N
=\left\{\frac pq:1\le q\le N,\ \gcd(|p|,q)=1\right\}
$$

is different. Rationality alone does not provide a finite denominator bound and does not in general permit exact reconstruction from an arbitrary computable-real presentation. Membership in the locally finite searchable grid $G_N$ reduces the relevant candidates to a finite set, so the promise determines an exact rational after finite elimination of all wrong candidates.

## Corollary 69.3 — Geometric absorption of an off-grid promise

Under the hypotheses of Theorem 69.1, assume $x\notin G$. There is a terminating algorithm that produces a certified rational interval

$$
[a,b]\ni x
$$

such that

$$
\boxed{G\cap[a,b]=\varnothing.}
$$

### Proof

Theorem 69.1 returns an adjacent grid bracket $L\le x\le R$. Since $x\notin G$, in fact

$$
L<x<R
$$

for finite endpoints, with the evident one-sided interpretation when an endpoint is an infinity sentinel. Arbitrarily shrinking certified rational enclosures for $x$ eventually produce a finite rational interval $[a,b]$ lying strictly inside the open adjacent gap $(L,R)$ on every finite side. Adjacency then gives $G\cap[a,b]=\varnothing$. $\square$

This corollary is the formal reason an off-grid trust promise can be fully absorbed into ordinary enclosure geometry.

---

# 70. Third termination theorem — Near-nearest projection

## Definition 70.1 — Near-nearest grid point

令

$$
G_{\mathrm{fin}}:=G\cap\mathbb R.
$$

對 finite target $x\in\mathbb R$ 與 $g\in G_{\mathrm{fin}}$，定義

$$
\operatorname{Better}_G(x,g)
:=
\left\{
h\in G_{\mathrm{fin}}:
|h-x|<|g-x|
\right\}.
$$

稱 $g$ 為 $x$ 的 **near-nearest grid point**，若

$$
\boxed{
|\operatorname{Better}_G(x,g)|\le1.
}
$$

所以 strict nearest是 stronger special case

$$
|\operatorname{Better}_G(x,g)|=0.
$$

此定義刻意不用「second nearest」排名語言，避免 distance ties造成名次歧義。

## Theorem 70.2 — Localization Theorem 3: guaranteed-finite near-nearest projection

在 Theorem 68.1 的 hypotheses 下，若另外 $\mathcal I_G$ 具有 Definition 67.1 的 global computable-real bounding，且

$$
G_{\mathrm{fin}}\ne\varnothing,
$$

則存在 terminating algorithm，對每個 semantic code representing $x\in S$ 回一個 finite grid code representing $g\in G_{\mathrm{fin}}$，使

$$
\boxed{
|\operatorname{Better}_G(x,g)|\le1.
}
$$

也就是 guaranteed-finite single-point **near-nearest projection**。

### Proof / termination mechanism

先執行 Theorem 68.1，取得 near-adjacent bracket

$$
L\le x\le R,
\qquad
|G\cap(L,R)|\le1.
$$

若 $L=R$，則 $x=L=R$；該 finite grid point本身 strict nearest，直接回傳。以下假設 $L<R$。

對 $(L,R)$ 使用 searchable-grid algorithm。由 near-adjacent contract，只有兩種可能：

1. $(L,R)$ 已 adjacent；
2. 存在唯一 strict-interior grid point $q$，且 $(L,q)$、$(q,R)$ 都 adjacent。

在第二種情況，先把 near-adjacent bracket finite reduction 成「strict-nearest point」或「adjacent bracket」，但**不引用後面的 mixed-format theorem**：

- fair-dovetail main comparison $x\mathrel?q$；
- 同時檢查 $x$ 是否落在 $q$ 的 open Voronoi cell：若 $L$ finite，比較
  $$
  x\mathrel?\frac{L+q}{2}
  $$
  並等待 `GREATER`；若 $L=-\infty$，左條件自動成立；若 $R$ finite，比較
  $$
  x\mathrel?\frac{q+R}{2}
  $$
  並等待 `LESS`；若 $R=+\infty$，右條件自動成立。

若 main comparison strict resolve，$x<q$ 時得到 adjacent bracket $(L,q)$，$x>q$ 時得到 adjacent bracket $(q,R)$。若 representation finite給出 equality evidence，直接回 $q$。若 $x=q$ 但 equality不 resolve，兩個存在的 midpoint comparisons 都是 strict，因此 Voronoi rescue finite證明 $q$ strict nearest並直接回傳。

所以 finite work 後，要嘛已得到 strict-nearest grid point並完成，要嘛得到一個 adjacent bracket

$$
A\le x\le B,
\qquad
G\cap(A,B)=\varnothing.
$$

若 $A=-\infty$，則 $B$ 是最左 finite grid point，故 $B$ strict nearest；$B=+\infty$ 對稱。以下只需處理 finite adjacent endpoints

$$
A<B.
$$

#### Finite construction of outer neighbors

由 Definition 66.4 把 $A$ lift 成 computable-real presentation，再由 Proposition 61.2 finite construct $A-1$ 的 presentation。利用 global computable-real bounding取得 grid code $a$ with

$$
\llbracket a\rrbracket_G\le A-1<A.
$$

在 distinct pair $(a,A)$ 上反覆用 search algorithm，把 outer endpoint向 $A$ 移動；local finiteness保證 bounded tail只能經過 finitely many grid points。故 finite得到 $A$ 的 immediate predecessor $P$，或確認 $P=-\infty$。同理 finite得到 $B$ 的 immediate successor $S$，或 $S=+\infty$。

若 $P=-\infty$，則 $B$ 左側只有 $A$ 可能比 $B$ 更近，因此 $B$ 已 near-nearest。若 $S=+\infty$，對稱地 $A$ 已 near-nearest。

剩下

$$
P<A<B<S
$$

皆 finite。由 Proposition 67.3 finite construct midpoint presentations

$$
m_-:=\frac{P+B}{2},
\qquad
m_+:=\frac{A+S}{2}.
$$

由

$$
P<A<B<S
$$

立即得

$$
\boxed{m_-<m_+.}
$$

Fair-dovetail兩個 resumable conditions：

1. 等待 $x>m_-$；一旦成立回 $B$；
2. 等待 $x<m_+$；一旦成立回 $A$。

至少一個 condition 必 strict 成立；否則會同時有

$$
x\le m_-
\quad\text{與}\quad
x\ge m_+,
$$

矛盾於 $m_-<m_+$。因此即使 $x$ 恰等於其中一個 midpoint，另一個 branch仍是 strict case並 finite resolve。

若 $x>m_-$，對任何 $h<B$ 且 $h\ne A$，adjacency of $(P,A)$ and $(A,B)$ 給 $h\le P$，故

$$
|x-h|\ge|x-P|>|x-B|.
$$

而任意 $h>B$ 因 $x\le B<h$ 有

$$
|x-h|>|x-B|.
$$

所以只有 $A$ 可能比 $B$ 更近：

$$
|\operatorname{Better}_G(x,B)|\le1.
$$

$x<m_+$ 時對 $A$ 的證明完全對稱。故 algorithm finite terminate且 output sound。

### Interpretation — overlapping safe regions

真正 strict-nearest point 的 boundary 位於 adjacent grid pair的 midpoint。若強迫選 exact nearest，midpoint equality可能成為 semantic boundary；near-nearest contract則把兩側候選的合法區域各向另一側延伸一格，使它們形成 overlap：

$$
m_-<m_+.
$$

因此不需要判定 target 是否恰好位於某個 midpoint；如果一個 safe-region comparison卡在 equality，另一個 strict branch仍會 finite resolve。這是 projection 版本與 Theorem 68.1 exact-hit rescue完全平行的「退讓一階換 unconditional termination」。

### Corollary 70.3 — Standard v1 grids

Corollary 68.2 的三個 standard grids都有 nonempty finite part與 global ComputableReal bounding，所以 `grid_project(grid)` guaranteed finite。Return types按 canonical grid point representation為：

```text
IntegerGrid()                  -> int
BoundedDenominatorGrid(N)     -> Rational
Binary64Grid()                -> finite Python float
```

對 `Binary64Grid()`，Theorem 70.2 的 codomain明確限制在 $G_{\mathrm{fin}}$，所以 `grid_project(Binary64Grid())` 永不回 `±inf` 或 NaN，即使 target magnitude超過最大 finite binary64。

---

# 71. Fourth termination theorem — Strict-nearest projection under the no-midpoint promise

## Definition 71.1 — Adjacent-midpoint obstruction set

令 $G\subseteq\overline{\mathbb R}$。只對 **finite adjacent endpoints** 定義 midpoint set：

$$
M_G
:=
\left\{
\frac{a+b}{2}:
 a,b\in G_{\mathrm{fin}},\ a<b,\ G\cap(a,b)=\varnothing
\right\}.
$$

含 $\pm\infty$ 的 adjacent pair沒有 finite midpoint，因此不進入 $M_G$。

## Theorem 71.2 — Localization Theorem 4: promised-optimal projection

在 Theorem 68.1 的 hypotheses 下，若

$$
G_{\mathrm{fin}}\ne\varnothing
$$

且另有 semantic promise

$$
S\cap M_G=\varnothing,
$$

則存在 terminating algorithm，對每個 semantic code representing $x\in S$ 回 finite $g\in G_{\mathrm{fin}}$ 使

$$
\boxed{
|g-x|
<
\inf_{h\in G,\ h\ne g}|h-x|.
}
$$

也就是 guaranteed-finite **strict-nearest projection**。

### Proof

先執行 Theorem 68.1 得

$$
L\le x\le R,
\qquad
|G\cap(L,R)|\le1.
$$

若 $L=R$，則 $x=L$，直接回該 strict-nearest grid point。

對 distinct $(L,R)$ 使用 searchable-grid algorithm。

### Case 1 — $(L,R)$ adjacent

若一端為 infinity，另一個 finite endpoint是唯一最近的 finite grid point，直接回傳。

若 $L,R$ 都 finite，令

$$
m:=\frac{L+R}{2}.
$$

因 $m\in M_G$ 且 $x\notin M_G$，target-vs-midpoint comparison必是 strict case並 finite resolve：

- $x<m$ 時回 $L$；
- $x>m$ 時回 $R$。

Adjacency保證所選 endpoint比任何其他 grid point都嚴格更近。

### Case 2 — 唯一 interior point $q$

此時

$$
L<q<R,
$$

且 $(L,q)$、$(q,R)$ 都 adjacent。若 $L$ finite，令

$$
m_L:=\frac{L+q}{2}\in M_G;
$$

若 $R$ finite，令

$$
m_R:=\frac{q+R}{2}\in M_G.
$$

No-midpoint promise使所有存在的 target-vs-$m_L,m_R$ comparisons都是 strict並 finite resolve。

- 若 $L$ finite 且 $x<m_L$，回 $L$；
- 否則若 $R$ finite 且 $x>m_R$，回 $R$；
- 其餘情況回 $q$。

若某側 endpoint為 infinity，相應 boundary condition simply absent。由 adjacency，這正是 $L,q,R$ 的 Voronoi decomposition；promise排除了 tie boundary，所以選出的 grid point對所有其他 grid points都嚴格最近。

因此 algorithm finite terminate。

和 Theorem 69.1 一樣，這個 construction在 promise 外可視為 sound partial search：只有 strict midpoint evidence才觸發輸出；若 target恰等於 relevant midpoint，可讓該 branch保持 non-emitting pending。Promise的作用是保證 termination，不是讓演算法在 promise 外可以輸出錯誤答案。

### Interpretation

Localization Theorem 3 / 4 形成 projection pair：

$$
\boxed{
\text{unconditional near-nearest}
\quad\longrightarrow\quad
\text{no-midpoint promised strict-nearest}.
}
$$

Theorem 3 固定 single-point output shape並把 optimality退讓一階；Theorem 4 則在排除唯一的 projection boundary後恢復真正 strict nearest。

---

# 72. Fifth termination theorem — Mixed-format optimal localization

定義 direction symbols：

$$
U:=\{-2,-1,0,1,2,\bot\}.
$$

其中 $\bot$ 表示不宣告 direction。

## Theorem 72.1 — Localization Theorem 5: mixed optimal output

在 Theorem 68.1 的 hypotheses 下，存在 terminating algorithm回

$$
(\mathrm{bound},\mathrm{approx})
$$

滿足：

1. `bound` 與 `approx` 至少一個 present；
2. 若
   $$
   \mathrm{bound}=(L,R),
   $$
   則
   $$
   L\le x\le R,
   \qquad
   G\cap(L,R)=\varnothing;
   $$
3. 若
   $$
   \mathrm{approx}=(g,d),
   $$
   則 $g$ 是 strict nearest grid value：
   $$
   \boxed{
   |g-x|
   <
   \inf_{h\in G,\ h\ne g}|h-x|,
   }
   $$
   且
   $$
   d=-2\Longrightarrow g<x,
   $$
   $$
   d=-1\Longrightarrow g\le x,
   $$
   $$
   d=0\Longrightarrow g=x,
   $$
   $$
   d=1\Longrightarrow g\ge x,
   $$
   $$
   d=2\Longrightarrow g>x,
   $$
   $$
   d=\bot\Longrightarrow\text{no directional assertion}.
   $$

也就是：**固定要求最佳品質，但不固定輸出 shape**。算法 guaranteed-finite交付「最佳包圍」或「最佳投影」至少其中之一。

### The two optimality obstructions

對 finite target，定義兩個 boundary / obstruction sets：

$$
B_{\mathrm{enc}}:=G_{\mathrm{fin}},
$$

$$
B_{\mathrm{proj}}:=M_G.
$$

它們代表兩種不同的 semantic obstruction：

- **optimal enclosure obstruction**：adjacent bracket本身對 grid hit仍存在，但以 target-directed comparison搜尋時，若 $x=g\in G$，exact equality可能讓 bracket-selection search永久 Pending；
- **optimal projection obstruction**：若 $x$ 是 adjacent finite grid pair的 midpoint，兩個 endpoints等距，因此 strict nearest甚至不存在。

關鍵幾何事實是

$$
\boxed{G_{\mathrm{fin}}\cap M_G=\varnothing.}
$$

Indeed，若

$$
m=\frac{a+b}{2}
$$

其中 $a<b$ adjacent，則

$$
a<m<b.
$$

若 $m\in G$，便得到一個 strict-interior grid point，與 adjacency矛盾。

所以兩種最佳化障礙**不可能同時發生**。

### Proof by fair dovetailing

若 $G_{\mathrm{fin}}=\varnothing$，finite target自動滿足 $x\notin G$；Theorem 69.1 的 optimal-enclosure construction因此 guaranteed finite，直接回 adjacent bracket。以下假設 $G_{\mathrm{fin}}\ne\varnothing$。

同時 fair-dovetail兩個 semantically sound partial searches：

1. **optimal-enclosure search**：使用 Theorem 69.1 proof 中的 construction。它只在 strict target-vs-interior-grid comparison resolve時輸出 adjacent bracket；若 $x\notin G$ guaranteed finite terminate。
2. **optimal-projection search**：使用 Theorem 71.2 proof 中的 construction。它只在 strict midpoint evidence足夠時輸出 strict-nearest point；若 $x\notin M_G$ guaranteed finite terminate。

兩個 search在各自 promise 外都不需要 terminate，但所有實際輸出都 sound。

對任意 finite target $x$：

- 若 $x\notin G$，optimal-enclosure search guaranteed finite resolve；
- 若 $x\in G$，由 $G_{\mathrm{fin}}\cap M_G=\varnothing$ 得 $x\notin M_G$，所以 optimal-projection search guaranteed finite resolve。

等價地，若 projection obstruction $x\in M_G$ 發生，則 $x\notin G$，因此 enclosure channel必 finite resolve。

故至少一個 channel必在 finite work 後產生 sound optimal output；fair dovetail scheduler因此 finite terminate。若另一個 channel在停止前也已 resolve，可一併回傳；contract只要求兩者不可以同時 absent。

Direction field不是 termination所必需。Strict-nearest search若另外已有 finite target-vs-$g$ evidence可輸出較強 direction；否則可用 $d=\bot$。

### Interpretation — fixed shape versus optimality

五個 theorem現在形成一個對稱結構：

| Goal | Unconditional fixed-shape theorem | Promised optimal theorem |
|---|---|---|
| enclosure | Theorem 1: near-adjacent | Theorem 2: adjacent if $x\notin G$ |
| projection | Theorem 3: near-nearest | Theorem 4: strict-nearest if $x\notin M_G$ |

Theorem 5採第三種策略：

$$
\boxed{
\text{保留 unconditional termination + optimality，退讓 fixed output shape。}
}
$$

因此可以把三種 public observation philosophy理解成：

- `grid_bound()`：固定 bracket shape，所以從 adjacent退讓成 near-adjacent；
- `grid_project()`：固定 point shape，所以從 strict-nearest退讓成 near-nearest；
- `grid_localize()`：不退讓兩種輸出的 optimality，而允許 runtime在 adjacent bracket與 strict-nearest point之間選擇 whichever boundary is currently decidable。

這不是偶然的 implementation trick。它來自兩個 obstruction sets

$$
G_{\mathrm{fin}}
\qquad\text{與}\qquad
M_G
$$

的互斥性。最佳包圍會卡住的地方，最佳投影反而沒有 midpoint obstruction；最佳投影會卡住的地方，又必然不在 grid 上，所以最佳包圍可 strict resolve。

### Corollary 72.2 — Standard v1 grids and runtime mapping

Corollary 68.2 的三個 standard grids都適用 Theorem 72.1，因此 v1 `grid_localize(grid)` guaranteed finite。

對 `Binary64Grid()` 與 finite real target，§63 約定 target 到 `±∞` 的 distance為 $+∞$；grid亦含 finite binary64 values，所以 strict-nearest winner必為 finite grid value。Runtime可用 Python float infinities實現 bracket endpoint sentinels；這是 localization endpoint semantics，不是 exact-class machine projection overflow semantics。

三個 public observation surface與五個 formal theorem的關係固定為：

```text
Theorem 1  near-adjacent enclosure     -> grid_bound(grid)
Theorem 2  off-grid adjacent enclosure -> promised mathematical strengthening; no additional first-edition public API
Theorem 3  near-nearest projection     -> grid_project(grid)
Theorem 4  no-midpoint strict nearest  -> promised mathematical strengthening; no additional first-edition public API
Theorem 5  mixed optimal output        -> grid_localize(grid)
```

## 72.3 Complex-plane product-grid corollary

令 $G\subseteq\mathbb Q$ 為 finitely represented one-dimensional grid。定義

$$
G^{(2)}:=\{a+bi:a,b\in G\}\subseteq\mathbb Q(i).
$$

若 $G$ 在 bounded real regions locally finite，則 $G^{(2)}$ 在 bounded rectangles locally finite。若另固定一個對 $G$ 的 representation / search layer，使 bounded-region finite enumeration或 interior-search primitives可有效實現，則對應 product representation亦可 finite enumerate bounded rectangle中的 Gaussian-rational probes。這裡 local finiteness仍是 underlying set的純數學性質；effective enumeration / search是 representation capability。

這個 corollary不主張一般二維 nearest-point boundary可以無條件 total decide；它只固定一個 exact finite probe substrate。v1 runtime若需要 coordinatewise grid observation，對 `ComputableComplex.real_part()` / `imag_part()` 分別套用一維 theorem；algebraic root isolation / complex search可使用 $G^{(2)}$ 作 exact probe family。

---

# Part XII — Consequences for numerical API design

# 73. Exact-hit questions and finite observations

Theorems 68–72 展示 general pattern：

若 boundary relation 一般不可 guaranteed finite decide，不應：

- timeout guess；
- force total equality；
- 回 approximate bool。

而應設計 finite output contract，使 boundary ambiguity被 representation 吸收。

Examples：

- near-adjacent rather than exact adjacency for unconditional fixed-shape enclosure；
- exact adjacency restored under the off-grid promise；
- near-nearest rather than strict-nearest for unconditional fixed-shape projection；
- strict-nearest restored under the no-midpoint promise；
- mixed-format optimal output when the runtime is allowed to choose between the two optimal shapes。

---

# 74. Resolution vs semantic decision

Resolution API 問：

> 給我有限品質的 certified information。

Semantic process 問：

> 告訴我 exact boundary relation；若數學語意不保證 finite decision，我接受 computation 可能永遠繼續。

兩者是不同的 mathematical problem，不是同一 algorithm 加不同 timeout。

## 74.1 Fixed machine-format error thresholds have their own boundary

本小節只作 hard-threshold / exact-nearest machine projection 的 design warning。v1 現在提供 theorem-backed `grid_project(grid)`，但它的 contract 是 near-nearest grid point，而**不是** correctly-rounded、strict-nearest、或「誤差不超過指定 threshold否則證明不可能」的 machine-format projection。

令 $H\subset\mathbb R$ 為 discrete finite target set（例如 finite binary64 values），$e\in\mathbb Q_{>0}$。Query

> 找 $h\in H$ 使 $|x-h|\le e$；若不存在則證明不存在。

等價於判定

$$
d_H(x):=\min_{h\in H}|x-h|\le e.
$$

在 boundary

$$
d_H(x)=e
$$

上，若 $x$ 的 semantic representation 沒有相應 equality evidence，comparator / shrinking-enclosure semantics 一般不保證 finite 識別「恰好等於 threshold」。因此不能僅由 `ComputableReal` 定義推出「single machine value with hard error threshold or certified impossible」是 unconditional guaranteed-finite API。

正確的 runtime split 是：

- grid **bound / enclosure** 以 near-adjacent contract guaranteed finite；
- grid **single-point projection** 可用 Theorem 70.2 的 near-nearest contract guaranteed finite；
- correctly-rounded / strict-nearest / hard-error-threshold single-value selection若未有額外 theorem，不能冒充上述 near-nearest contract；ordinary version可以 certificate-gated，unresolved 時 finite raise；
- exact feasibility decision 放 explicit process，boundary 可 Pending。

同一現象逐 coordinate / product-grid 延伸到 machine complex approximation。

---

## Safe forgetting as preservation of interpretation capability

若 runtime state $s$ 被 finite state $s'$ 取代並丟棄某段 history，這個 replacement 只有在 $s'$ 仍指定同一 denotation，且保留該 public representation 承諾的 future effective observations / operations 時，才是 semantics-preserving。

因此 finite exact domains可安全以等值 exact representative取代 expression history；但對 general computable real / complex，單一 finite enclosure只證明 membership in a region，不能唯一指定原 denotation，也不能一般恢復 arbitrary future refinement。

Formal foundations 不固定具體 graph-compaction algorithm；`02` / `03` 將此工程原則稱為 Safe Forgetting Principle。

## 74.2 Recoverable regime representations

令 runtime 的五個 public regimes denotationally 對應

$$
\mathbb Q,\quad
\mathbb Q(i),\quad
\overline{\mathbb Q},\quad
\mathbb R_C,\quad
\mathbb C_C.
$$

對某一 runtime state $s$ representing value $x$，稱 target-regime representation $t$ 是 **finitely recoverable from $s$**，若存在 terminating algorithm由 $s$ 的當前 finite state產生 $t$，且 $t$ 代表同一 denotation $x$。

這個概念是 state-relative，而不是只看抽象 mathematical membership。即使 $x\in\mathbb Q$，任意 computable-real presentation未必提供 terminating procedure可抽取其 numerator / denominator；因此 rational membership不自動意味 rational representation finitely recoverable。

對每個具體 value，五個 regimes 的最低值依下列 value-sensitive classification唯一：rational；否則 non-real Gaussian rational；否則 algebraic；否則 computable real if real；否則 computable complex。Runtime ordinary `downgrade()` 只在**當前 finitely recoverable representations**中取此順序的最低者，因此 guaranteed finite 不要求解一般 membership problem。

若 state $s$ 的 ordinary downgrade result為 $t$，而 $t$ 有 guaranteed-finite same-value embedding到 target regime $U$，則升階可 compositionally 定義為

$$
s\xrightarrow{\mathrm{downgrade}}t
\xrightarrow{\mathrm{embed}}u.
$$

若 $u$ 同時保存足以 terminatingly recover $t$ 的 constructive information，則

$$
\mathrm{downgrade}(u)
$$

至少可恢復到與 $t$ 相同的最低當前可恢復 regime。這是升階保持 recoverability 的形式基礎。

允許 unbounded search 的 `downgrade_process()` 對應另一種 partial computation：它可以 fair-dovetail sound recognition / reconstruction procedures，並在每次 finite discovery後改善目前 recoverable representation；但 formal computability theory不保證任意真 membership 都是 positively semidecidable。因此 process 即使對實際上較低的 value也可能永久不 resolve。

---

# 75. Formal basis for runtime `DecisionProcess`

## Trust-boundary assertion as promised-domain computation

Runtime user assertion 不需要被解釋成 total domain-decision algorithm。它更接近 Part VII / Part IX 的 promised-domain computation：對 assertion $P$，API contract直接把 $P$ 的真實性放進 promised domain。

### Strict-separable relation promises

對 real values，若 promise是

$$
x<y,
\qquad
x>y,
\qquad
x\ne y,
$$

則 distinct values具有正 separation。由 arbitrarily shrinking certified enclosures，存在 finite stage使兩 enclosure strict ordered或 disjoint。因此 `LESS` / `GREATER` / `NOT_EQUAL` relation promise可以在 promised domain內 terminatingly編譯成幾何 separation；一旦 geometry已蘊含 relation，獨立 predicate即可省略。

對 complex inequality $z\ne w$，至少一個 coordinate不同；該 coordinate的 real presentations同樣有限 strict separate，所以 rectangle / coordinate geometry可吸收 `NOT_EQUAL` promise。

### Equality-containing relation promises

對

$$
x=y,
\qquad
x\le y,
\qquad
x\ge y,
$$

enclosure overlap本身一般不能證明 equality cell。這類 promise仍可做 sound geometric propagation，例如 equality下把兩側目前 certified regions取相容交會；但 formal theory不保證存在 finite stage讓各自 enclosure單獨完整編碼 relation。因此 runtime可保留 residual semantic relation knowledge。

### Numeric-domain membership promises

Promise

$$
x\in\mathbb Q,
\quad
x\in\mathbb Q(i),
\quad
x\in\overline{\mathbb Q},
\quad
x\in\mathbb R_C
$$

或其否定，談的是 denotation membership，不是 representation code class。一般有限 enclosure / rectangle不能完整表達 rationality / algebraicity等 property，也不能由 membership promise本身必然重建相應 lower-regime code；因此這類 assertion可作 residual semantic knowledge。由集合包含關係導出的 implication是 finite logical inference，不需要 semantic search。

### Grid-membership promises

對 standard searchable computably embedded exact ordered grids：

- promise $x\in G$ 由 Theorem 69.2 保證 exact grid-point identification finite terminate；
- promise $x\notin G$ 由 Corollary 69.3 保證可 finite產生整體避開 grid 的 rational enclosure。

因此這兩個 branches都可在 promised domain內把 assertion完整編譯成更具體 representation：前者是 exact identified point / recoverable lower representation，後者是 gap enclosure。

### False promises

若 promise為假，partial typed algorithm在 promised domain外本來就沒有 termination requirement。Runtime允許依 promise執行的 strict separation、grid identification或gap absorption永久不完成；這不需要改造成 total classifier。若 contradiction已由既有 finite knowledge可辨認，runtime仍可立即拒絕。

這與一般 semantic decision 的 public `DecisionProcess` 規則不矛盾：trust-boundary operation由使用者提供 semantic promise；process則是在沒有該 promise的 arbitrary semantic input上由 runtime自己尋找 sound evidence。

Formal theory只提供這個 distinction與上述 termination facts；具體 provenance、residual-store layout、compaction policy由 `02` / `03` 固定。

Machine-level `Configuration` first-class + partial `Step` + finite-work iteration，提供 runtime process 的形式原型。

Public `DecisionProcess` 可以是更高階 state machine，但必保持同一原則：

1. state finite representable；
2. one work transition guaranteed finite；
3. finite work budget guaranteed finite；
4. unbounded resolution may diverge；
5. intermediate certified facts可在 finite transition後提交到 persistent runtime knowledge。

---

# 76. Formal basis for exact vs semantic numeric classes

Whenever the v1 integer-polynomial representation is referenced below, its code-level coefficient tuple follows the semantic-specification constant-first convention $(a_0,\ldots,a_n)\leftrightarrow a_0+a_1X+\cdots+a_nX^n$. This is a representation convention, not an additional mathematical hypothesis.


`Rational` / `GaussianRational` / `Algebraic` 對應 exact-style finite representation world。`GaussianRational` 特別在本文件中由 rational product interpretation 明確給出 $\mathbb Q(i)$ 的 finite exact representation與 complex probe geometry。

`Polynomial` / `Algebraic` 的 integer-polynomial、factorization、resultant、Sturm、root-count / isolation algorithms 與 exactness contract 由 `02` / `03` 指定；**本版 `06` 並未逐條形式化這些 algebraic algorithms 的 machine program 或另行證明其 classical termination/correctness theorems**。因此 `Polynomial` 在 v1 是 public guaranteed-finite exact type，但此處只記其 architecture / computability classification，不把 `02` 的 library contract 冒充成本文件已完整形式化的 theorem。

`ComputableReal` / `ComputableComplex` 對應 semantic realization world：value由 finite algorithmic representation指定，但 equality / boundary predicates不必 total finite。

因此五個 runtime classes 的差異不是 arbitrary software taxonomy，而是 realization regime、finite-decision capability 與 exact-probe role 的直接工程反映。

---

# 77. Scope and future formal work

本版 foundations 已固定：

- `Code`；
- framing；
- first-class types/programs/configurations；
- Code-register machine；
- partial computability；
- typed / partial algorithms；
- interpretation with $D\subseteq F$；
- semantic / exact / normal / perfect realization；
- normalizer theorem；
- existence collapse；
- computable real semantic comparator；
- comparator/enclosure equivalence principle；
- five localization/projection termination theorems arranged as two fixed-shape pairs plus one mixed theorem: near-adjacent / off-grid adjacent enclosure, near-nearest / no-midpoint strict-nearest projection, and mixed optimal output. Only Theorems 1, 3, and 5 add the three v1 public observation surfaces；
- Gaussian-rational exact product representation and complex product-grid probe corollary；
- exact grid-membership promise identification and off-grid gap-enclosure absorption；
- recoverable-regime / downgrade-first lift semantics；
- trust-boundary strict relation absorption versus residual equality/membership semantics；
- safe-forgetting semantic preservation principle。

未來可在不改變上述 public foundation 的前提下繼續擴充：

- optimized positive-integer prefix-free encoder 的完整 reduction-space asymptotic theory；
- formal compilation library for all high-level code operations；
- §33 universal simulation theorem 的 fully expanded low-level instruction-by-instruction construction / verification；
- multi-sorted mathematical structures；
- formal complexity measures beyond computability / termination；
- proof-carrying certificate calculus。
