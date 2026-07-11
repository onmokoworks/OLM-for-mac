# DG_NORMALIZE_65PX_REPORT — case_0023 65px `inside=1.0` 系の原因確定 (2026-07-06)

DistanceGradation case_0023 の 73px 残差のうち `65px inside_EDT=1.0` 系を対象に、
`FUN_1812aef70`（変換段）と正規化段を decomp/disasm/バイナリ定数から確定し、
Windows CPU .aex パイプラインを Python で構造再現して乖離段を特定した。

分析は `decomp/DistanceGradation.aex.c.txt`, `disasm/DistanceGradation.aex.asm.txt`,
`plugins_2025/DistanceGradation.aex`（PE を直接パースして DAT 定数を読取）に基づく。
**FACT / INFERENCE を明記する。推測補正はしない。**

---

## FUN_1812aef70 の実体

**FACT: `FUN_1812aef70` は `cv::Mat::convertTo` 相当（型変換 + スケール）で、実体は
cvResize ではなく `FUN_1812acec0` を介した convert-scale。** decomp 3791340-3791396
で読むと、末尾に `cvResize` (`imgproc/src/resize.cpp`) のアサート失敗パスがあるため
Ghidra は "cvResize" とラベル付けしているが、これは同一 TU 内の共有エラーハンドラで
あり、正常経路（`if (((local_e8[0]^local_88[0]) & 0xfff)==0)` ブロック）は:

```
local_120[0] = 0x2010000;    // cv::Mat 型コード (dst type, CV_32F 系)
local_108[0] = 0x1010000;    // cv::Mat 型コード (src type, CV_8U 系)
local_138 = (double)local_e0 / (double)local_80;   // スケール比 (行方向)
local_130 = ... param_3;                            // 追加フラグ (0 or 1)
FUN_1812acec0(local_108, local_120, CONCAT44(...), (double)local_dc/(double)local_7c);
```

つまり `FUN_1812aef70(src, dst, flag)` は **src を dst の型へ変換しつつ寸法比で
スケールする convert 段**。`FUN_181174760` 内では 2 回呼ばれる:
1. `FUN_1812aef70(param_2, local_48, 0)` — 入力マスクを distanceTransform 用の作業型へ変換（flag=0）。
2. `FUN_1812aef70(local_88, local_68, 1)` — distanceTransform 出力（距離）を threshold 前の型へ変換（flag=1）。

**重要: この変換段はスケール係数を掛けるが offset は無く、距離値の 0/正の符号を
変えない。** したがって threshold の `> t` 判定を反転させる要素は持たない。
（型変換の丸めが距離を ±1LSB 動かす可能性はあるが、`inside_EDT=1.0` を `>36` 側へ
押し上げることは不可能なので 65px 系には無関係。）

---

## 正規化段の有無と式（Mac との対応）

**FACT（今回の決定的発見）: `FUN_181174760` の書き出し段 `FUN_18117ca50` は
単なるバッファコピーではなく `cv::normalize`（`core/src/convert_c.cpp`, エラー文字列
`"cvNormalize"`）。さらに内部 `FUN_1811e9900` は `cv::normalize`（`core/src/norm.cpp`,
`"cv::normalize"`）で、`param_5 == 0x20` = `NORM_MINMAX (=32)` 分岐を持つ。**

disasm 181174906-181174942 で cvNormalize の引数構築を直読:

```
181174906  CMP EAX,0x8            ; 深度 == 8bpc ?
18117490b  MOVSD XMM3,[0x181504ab0]   ; beta = 255.0
181174915  CMP EAX,0x10           ; 深度 == 16bpc ?
18117491a  MOVSD XMM3,[0x181504ab8]   ; beta = 32768.0
181174924  MOVSD XMM3,[0x181504aa0]   ; else (float/32bpc) beta = 1.0
18117492c  MOV [RSP+0x28],R13         ; arg6 (mask/dtype)
181174931  MOV dword [RSP+0x20],0x20  ; arg5 norm_type = 0x20 = NORM_MINMAX
181174939  XORPS XMM2,XMM2            ; arg3 alpha = 0.0
18117493c  MOV RDX,R15 ; MOV RCX,R14  ; src=thresholded, dst=param_3
181174942  CALL 0x18117ca50           ; cv::normalize(src,dst, alpha=0, beta, NORM_MINMAX)
```

PE を直接読んだ DAT 定数（`plugins_2025/DistanceGradation.aex`）:
- `DAT_181504ab0 = 255.0` (double) — 8bpc の beta
- `DAT_181504ab8 = 32768.0` (double) — **16bpc の beta（case_0023）**
- `DAT_181504aa0 = 1.0` (double) — float/32bpc の beta
- `DAT_181504a90 = 1.0` (float) — threshold maxval / invert の "1.0"
- `DAT_181504a8c = 0.1` (float) — TRUNC 分岐の thresh==0 代替（CONSTANT 分岐では未使用）
- `DAT_181504a80 = 1/32768` (float), `DAT_181504ac4 = 32768.0` (float) — compose の読み書きスケール
- `DAT_181504aa8 = 2.0` (double) — Sphere 指数

**FUN_181174760 の完全パイプライン（FACT, decomp 3542522-3542554 + disasm）:**
```
convert(1812aef70,flag0) -> distanceTransform(1812b15a0, DIST_L2/PRECISE)
 -> convert(1812aef70,flag1) -> threshold(1812b6a40, cv::threshold)
 -> normalize(18117ca50 -> 1811e9900, NORM_MINMAX, alpha=0, beta=depth_max)
```

`cv::normalize NORM_MINMAX` の式（`FUN_1811e9900`, 3629347-3629375）:
`scale = beta/(max-min)`（min<max のとき）、`dst = (src-min)*scale + alpha(=0)`。
つまり **threshold 後の場を [0, beta] へ min-max 引き伸ばし**する。

**Mac との対応:**
- Mac `dt_to_normalized`（`OLMDistanceGradation.cpp:432-455`）は、非 CONSTANT で
  `TRUNC(→t) + denom=max(raw_max,1.0) で割る` = NORM_MINMAX 相当（min=0 前提、beta=1）。
  Windows は beta=32768（16bpc）だが、これは正規化空間 [0,1] を 16bpc へ写すだけで
  比率は同一。**非 CONSTANT の正規化式は Mac=Windows で一致（比率同型）。**
- CONSTANT（case_0023）では Mac は L438-442 で `out = raw>t ? 1.0 : 0.0` を直接生成し
  normalize を **スキップ**する。Windows は THRESH_BINARY（`raw>t ? maxval : 0`,
  maxval=max(1.0,thresh)）→ NORM_MINMAX で {0, beta} に写す。
  **数値的には両者とも二値 {0, 1(=beta)} を生成し等価**（min=0, max=maxval →
  正規化後は {0, beta}）。したがって CONSTANT 経路でも正規化式の差は 65px を生まない。

---

## case_0023 interp_mode と経路

**FACT（`refs/reference_requests/olm_bitdepth_16bpc_normalized_exact_20260625.json`
の `olmdistancegradation_extended__case_0023` を直読）:**
- `Interpolation Mode = 1` = **INTERP_CONSTANT**（`mac/OLMDistanceGradation/OLMDistanceGradation.h:85`）
- `In/Out = 3` = **Both**, `Inside Threshold = 36`, `Outside Threshold = 0`
- `Use Background Color = 1`, `Invert = 0`, `Render Mode = 1`(RGB/Gradation)
- `Gradation Color = [0.1098, 0, 0.9333]`(青), `BG Color = [1,0,0]`(赤)
- **`GPU Rendering = 1`**（後述の provenance に関わる）

**経路（FACT, decomp 3541080-3541133 の Both 分岐 `iVar5==3`）:**
```
uVar1 = *(param_6+0xcc)          // interp mode = 1 (CONSTANT)
inside : FUN_181174760(mask, local_688, thresh=param_6[0x17]=Inside=36, param_8=uVar1=1)
outside: FUN_181174ad0(1-mask 種)  // = cvSub(1, mask)  (FACT: FUN_181182d60=cvSub)
         FUN_181174760(1-mask, local_6a8, thresh=param_6+0xbc=Outside=0, param_8=1)
combine: FUN_181182b20(local_688, local_6a8, local_6f8, 0)   // = cv::add
```
- `FUN_181174760` の 8番目引数 `param_8`（THRESH_BINARY 選択子）は **interp mode**（=1=CONSTANT）
  から来る。よって inside/outside 両呼び出しとも **THRESH_BINARY**（strict `>`）。
- **FACT: Both 合成は `FUN_181182b20` = `cv::add`（`core/src/arithm.cpp`,
  `"cvAdd"`）。Windows は `inside + outside`（16bpc で saturate）で合成する。**
  Mac は `build_distance_field` L508 で `std::max(inside, outside)`。**これは既知の
  Mac/Windows 差（IR §Binary Notes でも cvAdd と記録済）だが、下記の通り 65px の
  原因ではない。**

---

## 65px inside=1.0 の乖離段の特定（取れた範囲）

### エンドポイント方向の確定（emulation-grounded, compose を Python 再現）
compose（invert=0, use_bg=1, CONSTANT）を case_0023 の実色で駆動:
- `field_x = 0.0 → RGB16 (7195,0,61165)` = **青/Gradation** = Mac の 65px 出力
- `field_x = 1.0 → RGB16 (65535,0,0)` = **赤/BG** = 参照(Windows)の 65px 出力

（promotion は DG_STRATEGY_A で検証済の `round(x*32768)/32768*65535`。両端点で参照と一致。）

したがって **65px で Windows は field_x=1、Mac は field_x=0**。
これは live field witness（`(1699,7)` Mac `field_x=0`）とも整合。

### Windows CPU .aex パイプラインの構造再現（emulation-grounded, scipy EDT + 確定した各段）
記録済 raw 距離（`inside_EDT=1.0`, `outside_EDT=0.0`; residual_split_20260630）を、
確定した各段（THRESH_BINARY strict`>` → NORM_MINMAX → cvAdd saturate）へ通すと:
- inside: `1.0 > 36 ?` → **0**（→normalize→0）
- outside: `0.0 > 0 ?` → **0**（→normalize→0）
- cvAdd: `0 + 0 = 0` → **field_x = 0 → 青**

合成円マスクでの全画素検証でも、1px 内側画素で `win_fx == mac_fx == 0`（差 0px）。
**すなわち今回確定した Windows CPU パイプラインは、記録済 raw 距離のもとで
Mac と同じく field_x=0（青）を出す。参照の赤(field_x=1)は再現できない。**

### 乖離段の結論（FACT + 限定 INFERENCE）
記録済 raw 距離のもとでは、`inside_EDT=1.0` 画素は **どちら側の threshold でも
必ず 0 に落ちる**（inside は `>36` 不成立、outside は `>0` 不成立、strict `>`）。
cvAdd(0,0)=0 なので、正規化・合成・writeback のいずれの段を通しても field_x=1 には
到達し得ない（enumerate で確認）。

したがって **65px の乖離は `FUN_1812aef70`（変換）・normalize・cvAdd-vs-max の
いずれの段でも生じない**（これらは今回すべて binary-grounding 済で、記録済距離では
青を生む）。参照が赤(field_x=1)になるには次のいずれかが必要:
- **(a)** Windows 側の実 raw 距離が記録値と異なる（inside が `>36`、または outside が
  `>0`）。= distanceTransform 段の入力/寸法/種の差。
- **(b)** threshold パイプラインを経ない別経路。case_0023 は **`GPU Rendering=1`** で
  あり、GPU 経路は本 decomp の CPU OpenCV パイプラインと異なる可能性がある
  （memory: "GPU rendering reference caveat"）。加えて lane_state（20260703）と
  provenance（20260702）は、この case で **packaged expected PNG が stale** であり、
  threshold-family triplet では live Windows が Mac と一致（赤）で packaged が古い(青)
  と記録している。65px 側の赤も同種の reference-provenance/GPU 差である可能性が高い。

**確度の高い結論（FACT）:** 65px 乖離は「Mac の field/normalize/合成段のバグ」では
ない。今回 binary-grounding した Windows CPU パイプライン（convert→DT→THRESH_BINARY
→NORM_MINMAX→cvAdd）は、記録済 raw 距離のもとで Mac と同一の field_x=0（青）を出す。
参照の赤は、この CPU パイプライン＋記録距離では構造的に到達不能。

**限定的 INFERENCE（未確定）:** 参照赤の出所は (a) Windows 実距離の差 または
(b) GPU 経路/stale reference。lane_state の provenance-split と `GPU Rendering=1` から
**(b) の可能性が高い**が、Windows CPU 実距離の直接 witness が無いため断定しない。

---

## 残課題

1. **Windows 実 raw 距離の直接取得（最優先）**: 65px の 1 点で Windows 側
   `FUN_181174760` 入力の inside/outside distanceTransform 値を typed で取得すれば、
   (a)（距離差）か (b)（別経路）かを確定できる。現状は Mac 側測定の記録値
   （in=1.0, out=0.0）しか無く、これは strict`>` で必ず青を生む。
2. **GPU vs CPU 経路の切り分け**: case_0023 は `GPU Rendering=1`。CPU .aex（本 decomp）
   と GPU 経路が同じ field を作るかは未証明。CPU software 参照を再取得すれば、赤/青が
   経路依存かを確定できる（lane_state の `current_aex_recapture` 要求と一致）。
3. **8px inside=36.013 系との整合**: 8px は逆向き（Mac 赤／参照青）に食い違う。
   これは DG_FIELD_GEN_REPORT の threshold-scaling ownership（`ds_scale`）で説明が
   進んでおり、本 65px 系とは別系統。今回の 65px 分析は 8px には触れていない。
4. **cvAdd の一般的採用可否は別途**: 65px では cvAdd と max は同値（両側 0）だが、
   inside/outside の support が重なる領域では `inside+outside`（saturate）と
   `max` は異なる。case_0023 の他画素・他 case で Mac を cvAdd へ寄せる判断は本
   タスク範囲外（65px の原因ではないため）。実距離 witness 取得後に評価すべき。

---

## 実行した検算コマンド（要点）
- PE 直読で DAT 定数確定（beta=32768/255/1.0, maxval=1.0, thresh0代替=0.1 等）。
- disasm 181174906-181174942 で cvNormalize 引数（alpha=0, beta=depth, type=0x20=NORM_MINMAX）を直読。
- scipy EDT + 確定各段で合成円マスクを再現 → 1px 内側画素は win_fx==mac_fx==0（差0px）。
- compose を case_0023 実色で駆動 → field_x=0→青(7195,0,61165), field_x=1→赤(65535,0,0) を参照と一致確認。
- enumerate で「記録距離下では cvAdd(0,0)=0 のため field_x=1 到達不能」を確認。

重い distanceTransform 全フレーム emulation は不要（各段が静的確定でき、
記録済 raw 距離で構造再現が閉じたため）。Unicorn 実行は本タスクでは不使用
（compose 段は DG_STRATEGY_A で既に Unicorn 検証済、field 段は静的で決着）。
