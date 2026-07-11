# SMOOTHER2_PRODUCER_EMU_REPORT

Local Unicorn emulation of OLMSmoother2 legacy producer path
(`aex/OLMSmoother2AE/Plugins/64/2025/OLMSmoother2.aex`, ImageBase
0x180000000). Functions driven directly; binary executed, no
Windows round-trip. All facts below are read from the binary via
Unicorn unless explicitly marked INFERRED. No source/notes/ledger
files modified; no commit.

## ABI / leaf 健全性
- .rdata 重み定数（mapped image から直接読取）:
  - `DAT_180022694(half)` = 0.5
  - `DAT_1800226a0(one)` = 1.0
  - `DAT_180022dd8` = 0.20000000298023224
  - `DAT_180022dd4` = 0.125
  - `DAT_180022de8` = 0.4000000059604645
  - `DAT_180022ddc` = 0.25
- leaf 検証 FUN_180013630（weight kernel）vs 独立 Python 再実装: PASS (全ケース一致)
  - p1=10.0, p2=3, p3=1.0: got=0.64999998 expected=0.65000000 match=True
  - p1=5.0, p2=2, p3=0.5: got=0.25000000 expected=0.25000000 match=True
  - p1=0.0, p2=1, p3=1.0: got=0.00000000 expected=0.00000000 match=True
  - p1=4.0, p2=5, p3=1.0: got=0.00000000 expected=0.00000000 match=True
  - p1=8.0, p2=1, p3=0.0: got=0.00000000 expected=0.00000000 match=True
  - p1=6.0, p2=6, p3=0.8: got=0.00000000 expected=0.00000000 match=True
- Win x64 ABI（XMM0/RDX/XMM2 引数, RET trampoline, __chkstk TEB）は この一致で健全と確認された。

## 0004 の分岐挙動（FUN_180013140 + scanners）
witness (1903,519) は Mac 側 count=0 / passthrough。ローカル 16x16 world
上で class-plane 状態を変えつつ、entry guard / emit guard / scanner 値
(iVar6=右scan, iVar5=下scan) / 頂点数・座標・重みを binary から読む。

- **empty-around-cur(8,8)** cur=(8, 8): entry_guard=True, iVar6(right)=1 (out=(8, 8),code=0), iVar5(down)=1 (out=(8, 8),code=0), class_prev_byte=0, emit_guard=True, **vcount=3**, verts=rgba=(0.000000,0.000000,0.000000,0.000000) w=0.40000001; rgba=(0.000000,0.000000,0.000000,0.000000) w=0.20000000; rgba=(0.000000,0.000000,0.000000,0.000000) w=0.40000001
- **isolated-class@cur(8,8)** cur=(8, 8): entry_guard=True, iVar6(right)=1 (out=(8, 8),code=0), iVar5(down)=1 (out=(8, 8),code=0), class_prev_byte=0, emit_guard=True, **vcount=3**, verts=rgba=(0.000000,0.000000,0.000000,0.000000) w=0.40000001; rgba=(0.000000,0.000000,0.000000,0.000000) w=0.20000000; rgba=(0.000000,0.000000,0.000000,0.000000) w=0.40000001
- **left-neighbour-set(7,8)** cur=(8, 8): entry_guard=True, iVar6(right)=1 (out=(8, 8),code=0), iVar5(down)=1 (out=(8, 8),code=0), class_prev_byte=0, emit_guard=True, **vcount=3**, verts=rgba=(0.000000,0.000000,0.000000,0.000000) w=0.40000001; rgba=(0.000000,0.000000,0.000000,0.000000) w=0.20000000; rgba=(0.000000,0.000000,0.000000,0.000000) w=0.40000001
- **edge cur_x==0** cur=(0, 8): entry_guard=False, iVar6(right)=1 (out=(0, 8),code=0), iVar5(down)=1 (out=(0, 8),code=0), class_prev_byte=None, emit_guard=None, **vcount=0**, verts=[]
- **edge cur_y==height-1** cur=(8, 15): entry_guard=False, iVar6(right)=1 (out=(8, 15),code=0), iVar5(down)=1 (out=(8, 15),code=0), class_prev_byte=None, emit_guard=None, **vcount=0**, verts=[]
- **dense NW block** cur=(8, 8): entry_guard=True, iVar6(right)=1 (out=(8, 8),code=5), iVar5(down)=4 (out=(8, 11),code=0), class_prev_byte=0, emit_guard=True, **vcount=3**, verts=rgba=(0.000000,0.000000,0.000000,0.000000) w=0.40000001; rgba=(0.000000,0.000000,0.000000,0.000000) w=0.20000000; rgba=(0.000000,0.000000,0.000000,0.000000) w=0.40000001
- **open-field cur(2,2)** cur=(2, 2): entry_guard=True, iVar6(right)=1 (out=(2, 2),code=0), iVar5(down)=1 (out=(2, 2),code=0), class_prev_byte=0, emit_guard=True, **vcount=3**, verts=rgba=(0.000000,0.000000,0.000000,0.000000) w=0.40000001; rgba=(0.000000,0.000000,0.000000,0.000000) w=0.20000000; rgba=(0.000000,0.000000,0.000000,0.000000) w=0.40000001
- **force-passthrough cur(8,4)** cur=(8, 4): entry_guard=True, iVar6(right)=7 (out=(14, 4),code=0), iVar5(down)=8 (out=(8, 11),code=0), class_prev_byte=1, emit_guard=False, **vcount=0**, verts=[]

## 0012 の分岐挙動（FUN_18000e170 / f270 / e3a0）
- desc=[5, 6, 1, 5, 8, 5]（record shape `91,841,1,91,843,5` を相対座標で再構成）
- **FUN_18000e170 bitsum c = 2**（record local: c=2）
- f270 scale 入力 = base_weight*DAT_180022dd8 + DAT_180022694 = 0.58000000
- **FUN_18000f270**: ret(append?)=1, count=1, verts=rgba=(0.000000,0.000000,0.000000,0.000000) w=0.42816091
- FUN_18000e3a0 (src=0): ret=1, count=1, **weight=0.42816091** 
- FUN_18000e3a0 (src rgba=0.991): ret=1, count=1, weight=0.42816091, rgba=(0.991067, 0.991067, 0.991067, 0.996078)

### 0012 e170 bitsum / append sweep
- desc=[5, 6, 1, 5, 8, 5], scale=0.58000000
| center_b0 | prev_b0 | left_b1 | e170 c | f270 count | e3a0 count |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 0 | 1 | 1 |
| 0 | 0 | 1 | 4 | 0 | 1 |
| 0 | 1 | 0 | 2 | 1 | 1 |
| 0 | 1 | 1 | 6 | 1 | 1 |
| 1 | 0 | 0 | 1 | 1 | 1 |
| 1 | 0 | 1 | 5 | 1 | 1 |
| 1 | 1 | 0 | 3 | 1 | 1 |
| 1 | 1 | 1 | 7 | 1 | 1 |
- Suppressing / no-append local patterns: (center=0,prev=0,left_b1=1,c=4)
- Reading: local Mac witness is `center=0, prev=1, left_b1=0 -> c=2 -> append`. The only local e170/f270 no-append pattern in this three-byte sweep is `center=0, prev=0, left_b1=1 -> c=4`. The `c=6` pattern still appends, so it is not a suppression proof by itself. The next Windows proof should read the exact three e170 bytes and the observed c value, not final writer bytes.

## 0004 scanner span sweep
- cur=(8, 4)
| right_span | down_span | class_prev_b3 | iVar6 | iVar5 | emit_guard | vcount |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 1 | 1 | True | 3 |
| 0 | 0 | 1 | 1 | 1 | True | 3 |
| 0 | 1 | 0 | 1 | 2 | True | 3 |
| 0 | 1 | 1 | 1 | 2 | True | 3 |
| 0 | 2 | 0 | 1 | 3 | True | 3 |
| 0 | 2 | 1 | 1 | 3 | True | 3 |
| 0 | 3 | 0 | 1 | 4 | True | 3 |
| 0 | 3 | 1 | 1 | 4 | True | 3 |
| 0 | 6 | 0 | 1 | 7 | True | 3 |
| 0 | 6 | 1 | 1 | 7 | True | 3 |
| 1 | 0 | 0 | 2 | 1 | True | 3 |
| 1 | 0 | 1 | 2 | 1 | True | 3 |
| 1 | 1 | 0 | 2 | 2 | True | 3 |
| 1 | 1 | 1 | 2 | 2 | False | 0 |
| 1 | 2 | 0 | 2 | 3 | True | 3 |
| 1 | 2 | 1 | 2 | 3 | False | 0 |
| 1 | 3 | 0 | 2 | 4 | True | 3 |
| 1 | 3 | 1 | 2 | 4 | False | 0 |
| 1 | 6 | 0 | 2 | 7 | True | 3 |
| 1 | 6 | 1 | 2 | 7 | False | 0 |
| 2 | 0 | 0 | 3 | 1 | True | 3 |
| 2 | 0 | 1 | 3 | 1 | True | 3 |
| 2 | 1 | 0 | 3 | 2 | True | 3 |
| 2 | 1 | 1 | 3 | 2 | False | 0 |
| 2 | 2 | 0 | 3 | 3 | True | 3 |
| 2 | 2 | 1 | 3 | 3 | False | 0 |
| 2 | 3 | 0 | 3 | 4 | True | 3 |
| 2 | 3 | 1 | 3 | 4 | False | 0 |
| 2 | 6 | 0 | 3 | 7 | True | 3 |
| 2 | 6 | 1 | 3 | 7 | False | 0 |
| 3 | 0 | 0 | 4 | 1 | True | 3 |
| 3 | 0 | 1 | 4 | 1 | True | 3 |
| 3 | 1 | 0 | 4 | 2 | True | 3 |
| 3 | 1 | 1 | 4 | 2 | False | 0 |
| 3 | 2 | 0 | 4 | 3 | True | 3 |
| 3 | 2 | 1 | 4 | 3 | False | 0 |
| 3 | 3 | 0 | 4 | 4 | False | 0 |
| 3 | 3 | 1 | 4 | 4 | False | 0 |
| 3 | 6 | 0 | 4 | 7 | False | 0 |
| 3 | 6 | 1 | 4 | 7 | False | 0 |
| 6 | 0 | 0 | 7 | 1 | True | 3 |
| 6 | 0 | 1 | 7 | 1 | True | 3 |
| 6 | 1 | 0 | 7 | 2 | True | 3 |
| 6 | 1 | 1 | 7 | 2 | False | 0 |
| 6 | 2 | 0 | 7 | 3 | True | 3 |
| 6 | 2 | 1 | 7 | 3 | False | 0 |
| 6 | 3 | 0 | 7 | 4 | False | 0 |
| 6 | 3 | 1 | 7 | 4 | False | 0 |
| 6 | 6 | 0 | 7 | 7 | False | 0 |
| 6 | 6 | 1 | 7 | 7 | False | 0 |
- Reading: `FUN_180013140` no-emit happens in two local shapes: (1) both scanner spans reach >=4 (`iVar6>=4` and `iVar5>=4`), or (2) both spans reach >=2 while `class_prev_b3 != 0`. The earlier `force-passthrough` synthetic remains the stronger branch, with both spans long and `class_prev_b3=1`.
- The earlier `left-neighbour-set(7,8)` scenario left `class_prev_byte=0` because the guard reads left-pixel byte3, not byte0. This sweep pins that byte-level requirement directly.

## Mac↔Windows 乖離の局在（取れた範囲）
- **0004 (1903,519)**: Windows writer は semitransparent gray `[103,103,103,113]` (raw 0xe8e8e871, float ~0.808/0.442)。Mac は count=0 passthrough で透明中心 `[1,1,1,0]`→`[0,0,0,0]`。上の scenario 群で 「どの class-plane 状態で FUN_180013140 が頂点を append する／しないか」を binary で確定した（vcount 参照）。Windows 側の正解 class-plane 状態・cce0 出力 float は本 run では持たないため、Mac 分岐の fact 化までで停止。
- **0012 (91,841)**: Windows writer は透明 `0xffffff00`→`[0,0,0,0]`、Mac は cardinal6 append 生存 → cce0 blend で visible `[90,90,90,91]`。乖離は e170 の c 値（append 抑制の分岐点: c==4 で f270 が抑制）に局在する。本 run で Mac 側 e170 の実 c 値と f270/e3a0 の append 有無・weight を binary から確定した（上記）。Windows 側の実 c 値（class-plane 実状態）は 本 run では未取得のため、そこが残差。

## 残課題
- Windows 側の実 class-plane bytes / desc / cce0 出力 float は本 run に無い。上記は全て **Mac(=当該.aex) 側の分岐挙動の binary-grounding** であり、Windows 比較は writer-anchor（既確定）以外は未架橋。
- 0012 の完全 chain（FUN_1800125c0→FUN_180010760→c280 polygon builder→cce0 blend）は本 run では通していない（c280 polygon 構築の scaffold が別途必要）。producer の分岐点である e170/f270/e3a0 は直接駆動で確定済み。
- 0012 の座標は 16x16 world 上の相対座標 (5,6) で再構成（絶対 91/841 は world に収まらないが、class 近傍と desc 差分のみが producer 判定に効く）。これは INFERRED な座標移送であり、絶対座標依存の分岐が別に無いことは decomp 上は確認したが Windows 実データでは未確認。
