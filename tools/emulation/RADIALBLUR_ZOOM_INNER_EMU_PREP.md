# RadialBlur Zoom / Inner エミュレーション準備 (M4延長)

Scope: 静的解析のみ。既存 `tools/emulation/` (M1-M5, `aex_loader.py`,
`test_m4_case0010.py`) を Zoom `case_0009` と Inner `case_0011/0012/0013` に
転用するための駆動関数・引数・最小手順の事前確定。読み取り専用。捏造禁止。
事実(binary-grounded)と推測(hypothesis)を明示区別する。

対象 AEX: `aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex`, base `0x180000000`。
Decomp/disasm: `decomp/OLMRadialBlur.aex.c.txt`, `disasm/OLMRadialBlur.aex.asm.txt`。

---

## 0. Blur Type 分岐点 (binary-grounded)

`FUN_180007520` の末尾 (`decomp` 3621-3632 / `disasm` `1800072d3..180007344`)
が Blur Type で分岐する。分岐キーは ctx `+0x20` (= `param_5[4]`, reader
`e5f0 idx1`)。

```
1800072d3  MOV EAX, dword ptr [RBX + 0x20]   ; Blur Type
1800072d6  CMP EAX, 0x1
1800072d9  JNZ 0x18000730e                    ; !=1 -> Rotation 判定へ
1800072df  CALL 0x18000a7e0                    ; Zoom init A (RCX = work +0x40)
1800072f1  CALL 0x18000a810                    ; Zoom init B (XMM1 = [RBX+0x80] strength)
1800072fd  CALL 0x1800056f0                    ; ★ Zoom 本体
180007307  CALL 0x18000a800                    ; Zoom teardown
18000730e  CMP EAX, 0x2
180007311  JNZ 0x180007344
180007317  CALL 0x180001a90                    ; Rotation init A
180007329  CALL 0x180001ac0                    ; Rotation init B (XMM1 = [RBX+0x80] strength)
180007335  CALL 0x180004640                    ; ★ Rotation 本体 (M4 で駆動済み)
18000733f  CALL 0x180001ab0                    ; Rotation teardown
```

事実:
- **Zoom (Blur Type 1) は `FUN_180004640` を通らない。** 別エントリ
  `FUN_1800056f0` を通る。init pair は `FUN_18000a7e0` / `FUN_18000a810`
  (Rotation の `FUN_180001a90` / `FUN_180001ac0` に対応)。両 init は
  `[RBX+0x80]` (ctx `+0x80` = quality-derived strength, reader `e430 idxf`) を
  XMM1 で受ける。
- **Inner (case_0011/0012/0013) は Blur Type = 2 (Rotation)。** よって Inner は
  `FUN_180004640` 経由で、M4 と同じ `FUN_180008690 -> FUN_180007520 ->
  FUN_180004640` チェーンで走る。Inner 専用の別エントリは無い。Inner scatter は
  Rotation scatter driver `FUN_1800024c0` が `FUN_180001c90` を direction=1 で
  呼ぶ形で起きる (下記 §2)。
  - 確認済み manifest (20260604): case_0011 InnerStr=478 OffMode=1,
    case_0012 InnerStr=478 OffMode=3 OuterStr=0, case_0013 InnerStr=18
    OffMode=1 Quality=50。すべて BlurType=2。

---

## 1. Zoom 経路 (case_0009) — `test_m4_case0010.py` 転用の変更点

### 1.1 Zoom 本体 `FUN_1800056f0` の構造 (binary-grounded, decomp 2359-2680)

Rotation `FUN_180004640` と平行だが **働きバッファのレイアウトが別**。

| 役割 | Rotation (`FUN_180004640`) | Zoom (`FUN_1800056f0`) |
|------|----------------------------|-------------------------|
| polar RGBA 入力 | `+0x38` | sampled per-cell (下記) |
| RGBA accumulation | `+0x3c940` / `+0xf250` | `param_1[0x842]` |
| scalar denom/weight | `+0x3c948` / `+0xf252` | `param_1[0x843]` |
| 正規化出力 (final polar) | `+0xe` | `param_1[7]` |
| prepass | `FUN_180002780` | `FUN_18000b150` (decomp 2543) |
| scatter | `FUN_1800024c0` | `FUN_18000a9d0` (decomp 2554) |
| 逆座標マップ | `FUN_180001b10` | `FUN_18000a850` (decomp 2604) |
| 最終逆サンプラ | `FUN_180009d80` | **`FUN_180009d80`** (同一, decomp 2615) |

サンプラ pair 選択 (decomp 2475-2482): `param_2+0x74`(Repeat Border)==0 なら
`FUN_18000a550`/`FUN_180009fc0`、!=0 なら `FUN_18000a6a0`/`FUN_18000a270`。
Rotation の `FUN_180001270`/`FUN_180001520` とは別関数。**case_0009 は
Repeat Border=1** なので `FUN_18000a6a0`(RGBA)/`FUN_18000a270`(scalar) 経路。

### 1.2 Zoom の caller-collapse / denominator (Zoom lane の核心, decomp 2560-2595)

最終正規化ループ (`FUN_180009d80` の直前) は cell 単位で:
```
w = param_1[0x843][cell]            # scalar 分母/weight plane
if w == 0.0:
    param_1[7][cell].rgb = 0,0,0    # RGB を zero
else:
    param_1[7][cell].rgb = param_1[0x842][cell].rgb / param_1[0x842][cell].alpha
param_1[7][cell].alpha = w          # ★ alpha = scalar weight plane (0x843), not accum alpha
```
これが `notes/*` の "Zoom caller-collapse / denominator state" の binary 実体。
最終 alpha は accumulation alpha ではなく `param_1[0x843]` の scalar weight。
`(6,0)` の `255 vs 254` 残差はこの `0x843` scalar plane の値 (prepass/scatter で
どう積まれるか) に帰着する — final byte writer ではない (既存 note と整合)。
[hypothesis: Rotation `+0xf252` と同様、`0x843` は sampler validity/coverage 由来。
`FUN_18000b150`/`FUN_18000a9d0` の中身 dump で確定要]

### 1.3 `test_m4_case0010.py` から変える必要がある項目

**変更必須 (Zoom は別バッファ/別関数):**

1. **入力 case を case_0009 に切替**: `INPUT_PNG`, manifest 抽出 id を
   `case_0009` へ。`load_case0010_params()` の positional index はそのまま
   使える (case_0009 も同じ param 配列形)。case_0009 値: BlurType=1,
   OuterStr=1717, Repeat Border=1, Quality=5, その他 0。
2. **capture hook を Zoom entry へ**: `add_code_hook(FUN_180004640,...)` を
   `add_code_hook(0x1800056f0, capture_rotation)` に。scatter hook は
   `FUN_180002780/FUN_1800024c0` -> `FUN_18000b150`(0x18000b150) /
   `FUN_18000a9d0`(0x18000a9d0) に。
3. **witness buffer 取り出しを Zoom offset へ**: `work_param1` から
   - accum RGBA = `param_1[0x842]` (= `u64(work_param1 + 0x842*8)`; **注意:
     Zoom は `param_1` を `undefined8*`=8byte 単位で index。`param_1[0x842]` は
     byte offset `0x842*8 = 0x4210`**), scalar weight = `param_1[0x843]`
     (byte `0x4218`), 正規化出力 = `param_1[7]` (byte `0x38`)。
     [検証必須: これらは handle-locked ポインタ。M4 の `u64(loader, ptr+idx*4)`
     は Rotation の float-index 前提。Zoom decomp では `param_1` は
     `undefined8*` なので index 単位が 8byte。実 run で
     `param_1[0x842]/[0x843]/[7]` を u64 として読む。]
   - angular grid: Zoom は `uVar19 = *(param_2[1]+0x28)` 行数、`fVar30 =
     int(_DAT_180021624 / quality_step)` 列数 (decomp 2436,2450)。Rotation の
     `iVar29 = 360/param_1[0]` とは別式。angular_cols は実 run で
     `local_res10`(=fVar30) 相当を dump して確定。
4. **逆座標/最終サンプラ呼びを Zoom へ**: `call_inverse_coords` は
   `FUN_180001B10` -> **`FUN_18000a850`**(0x18000a850) に。ただし
   `FUN_18000a850(param_1, x, y, &radius_out, &angle_out)` の引数順は
   `(longlong, float param_2, float param_3, float* param_4, float* param_5)`
   で、M4 の `FUN_180001b10(param1,0,0,radius_out,angle_out, xmm x,y)` とは
   ABI が異なる (a850 は float 引数が position1/2 = XMM1/XMM2)。呼び直し要。
   最終サンプラ `FUN_180009d80` は Rotation の `FUN_180001000` とは別関数だが
   Zoom はこれを使う (decomp 2615)。M4 の `call_polar_resampler`(FUN_180001000)
   は Rotation direct-sample 用なので、Zoom では `FUN_180009d80` を使う。
   [注意: `FUN_180009d80` の引数は decomp 2615 で
   `(param_1[7], out_ptr, uVar19_cols, int(fVar30)_rows, uVar19*4, radius, angle)`。
   M4 の resampler 呼びと配置が違うので新規に組む。]

**Zoom witness geometry (要 §3 で確定):**
- witness `(6,0)` の Windows final byte `[20,3,3,254]`
  (`refs/reports/olmradialblur_zoom_witness_20260624/audit.md`)。
- task 記載の `(6,0)=[20,3,3,255]` は現行ローカル(Mac/CLI)側の値
  (`refs/conformance/olmradialblur_local_witness_dumps_20260630.md`)。
  Windows は `254`。AEX emulation で確認したいのはどちらの経路が `254` を出すか。

---

## 2. Inner 経路 (case_0011/0012/0013) — typed witness の駆動

### 2.1 事実: Inner は Rotation entry 内で処理される

Inner cases は BlurType=2。M4 と同じ `FUN_180004640` を走らせれば、その中の
`FUN_1800024c0` (Rotation scatter driver, decomp 835-893) が gated cell 毎に
`FUN_180001c90` を **outer(dir=0) then inner(dir=1)** で呼ぶ (decomp 883-886)。
Inner witness は M4 の Rotation drive に hook を足すだけで取れる。**新エントリ不要。**

### 2.2 駆動関数と引数 (typed sampler/scatter/writeback witness)

`FUN_180001c90 @ 0x180001c90` シグネチャ (decomp 556-558, ASM_FACTS と整合):
```
FUN_180001c90(
  param_1  = ctx (work buffer),
  param_2  = direction        (0=outer / 1=inner)   ; ★ Inner は 1
  param_3  = caller_distance  (R8D; (param_7/2*iVar8)*(1/row+1) resolved)
  param_4  = angle_index,
  param_5  = radius_index,
  param_6  = source_alpha      (fVar5, prepass +0x48 の cell 値)
  param_7,8,9 = source RGB     (polar +0x38.rgb)
  param_10 = span_gate         (fVar1, +0x40 plane 値 = param10)
  param_11 = angular_count,
  param_12 = accum_rgba ptr    (+0x3c940)
  param_13 = max_alpha ptr     (+0x3c948)
)
```
内部 (ASM_FACTS 済): dir で base length を `+0x3a9e8`(outer)/`+0x3a9ec`(inner)
から選び、`R14D = trunc(float(resolved) * span_gate)` (`0x1d18`)、table step
`30000/R14D` (`0x1d33`)、tail loop `offset < R14D` (`0x23e0`)、underflow で
`(radius_row+1, angular_count-1)` へ (`aex-next-row`)。span-31 runtime fact
(`[RCX+0x3a9ec]=0x1f`, `R14D=31`) はこの helper。

### 2.3 witness 取得 hook (推奨)

`test_m4_case0010.py` の capture 機構に追加:
1. `add_code_hook(0x180001c90, capture_inner)`: entry で `param_2==1` の呼びを
   フィルタし、`RCX/RDX/R8/R9` (=param_1..4) と stack (param_5..) を dump。
   これが typed **sampler入力/scatter入力** witness。
2. 同じ hook 内で `+0x3a9ec` (inner base length) と、helper 内 `0x1d18` 通過後の
   `R14D` (effective span) を取るには `0x180001d18` の直後 (`0x180001d1b`) にも
   hook を置き XMM0/R14D を読む。これが effective-span witness (span-31 の確認)。
3. **writeback witness**: helper 復帰後に `param_12`(+0x3c940 accum) と
   `param_13`(+0x3c948 max) の該当 cell を読む。または M4 と同様に走了後の
   `+0xf250`(=`+0x3c940` collapse 前) / `+0xe` を dump。
   [事実: Rotation では走了後に `+0xf252 -> +0xe.alpha` collapse が起きる
   (ASM_FACTS)。Inner も同一 collapse を通る。]

### 2.4 Inner 代表 cell (witness plan 由来)

`notes/IR_OLMRadialBlur.md` / witness_plan_20260625 の代表:
- low-span 代表: `rb_inner_only_strength_large` (別 request set)。20260604 の
  case_0011/0012/0013 を使う場合は case_0013 (InnerStr=18, 低 span 相当) が近い。
- Quality/strong 代表: case_0011 (InnerStr=478) or case_0013 (Quality=50)。
- 目的は "wrong plane/value" の typed 確定 (blocked-no-global-toggle)。
  span-31 は既知。次証拠は per-cell の resolved_span/table_step/loop_limit/
  source_row/accum の typed dump (どの cell が underflow で次行へ行くか等)。

---

## 3. 最小再現手順 (メインセッション実行前提のコマンド案)

前提: venv は `tools/emulation/.venv` (unicorn/capstone/pefile/Pillow 済)。
実行時間目安: M4 で case_0010 (1920x1080, fast=True) は約110s。同解像度の
case_0009/0011/0012/0013 も同オーダー。

### 3.1 Zoom `case_0009` witness (6,0)

`test_m4_case0010.py` を複製し §1.3 の変更を当てた新スクリプト
(例 `tools/emulation/test_zoom_case0009.py`, 新規作成可) を用意して:
```bash
cd "/Users/onmk/Documents/Projects/Personal/OLM as"
tools/emulation/.venv/bin/python tools/emulation/test_zoom_case0009.py
```
確認したい出力:
- Zoom entry `FUN_1800056f0` 到達 (`param_1`/`param_2` 捕捉)。
- `param_1[0x842]`(accum), `param_1[0x843]`(weight), `param_1[7]`(final polar)
  の witness cell 値。
- `FUN_18000a850` で `(6,0)` -> (radius, angle) を出し、`FUN_180009d80` で
  direct sample -> u8。Windows `[20,3,3,254]` と比較。
- 特に `0x843` scalar weight が `(6,0)` 寄与 cell で 1.0 未満か
  (=alpha `254` の根拠か) を確認。

### 3.2 Inner `case_0011/0012/0013` typed witness

M4 スクリプトを複製し §1.3(1) の case 切替のみ + §2.3 の
`FUN_180001c90` entry hook (dir==1 フィルタ) と `0x180001d1b` の R14D hook を
足した新スクリプト (例 `tools/emulation/test_inner_witness.py`) で:
```bash
cd "/Users/onmk/Documents/Projects/Personal/OLM as"
tools/emulation/.venv/bin/python tools/emulation/test_inner_witness.py --case case_0013
```
確認したい出力 (typed):
- 各 inner 呼びの `(direction=1, caller_distance, angle_index, radius_index,
  source_alpha, RGB, span_gate, angular_count)`。
- helper 内 effective span `R14D` (span-31 fact の再確認 / 代表 cell での値)。
- underflow で `(row+1, angular_count-1)` へ行った cell の記録。
- 走了後の `+0x3c940`(accum) / `+0x3c948`(max) / `+0xe`(final) 該当 cell。
- 目的: "間違った plane/value" を typed で特定 (どの入力 plane が Windows と
  ずれるか)。global span/wrap/loop toggle は禁止 — cell-level 事実のみ。

### 3.3 注意 (捏造・禁止事項の遵守)

- **禁止**: PNG見た目合わせ / global span・wrap toggle / naive validity masking。
- Zoom `0x842/0x843/7` の index 単位 (8byte vs 4byte) は M4 の Rotation
  (`*4`) と異なる。実 run 前に decomp の `undefined8 *param_1` を根拠に
  8byte 単位で読むこと。誤ると別 offset を掴む。
- `FUN_18000a850` / `FUN_180009d80` の ABI は M4 の
  `FUN_180001b10`/`FUN_180001000` と引数配置が異なる。既存 helper を
  そのまま流用しない。
- task 記載 Zoom witness `(6,0)=[20,3,3,255]` は Mac/CLI 側値。Windows は
  `254`。AEX emulation は "どちらの経路が 254 を生むか" の ground truth 用で
  あり、255 へ寄せる根拠にしない (reference-path split の可能性は
  case_0010 と同様に留意)。

---

## 4. binary-grounded / hypothesis の区別まとめ

**binary-grounded (decomp/disasm 直読で確認済):**
- Blur Type 分岐 (`+0x20`==1 Zoom -> `FUN_1800056f0`; ==2 Rotation ->
  `FUN_180004640`) [disasm 1800072d3..335]。
- Zoom バッファ map (`0x842`=accum, `0x843`=weight, `7`=final polar) と
  正規化式 (alpha=weight plane, RGB=accum.rgb/accum.alpha, weight==0 で RGB
  zero) [decomp 2560-2595]。
- Zoom サンプラ pair 選択 (Repeat Border=`+0x74`) [decomp 2475-2482]。
- Zoom 逆座標=`FUN_18000a850`, 最終サンプラ=`FUN_180009d80` [decomp 2604,2615]。
- Inner は Rotation entry 内 `FUN_1800024c0 -> FUN_180001c90(dir=1)`
  [decomp 883-886]、helper シグネチャ [decomp 556-558]。
- Inner cases 0011/0012/0013 = BlurType 2 [manifest 確認]。

**hypothesis (実 run/追加 dump で確定要):**
- Zoom `0x843` scalar weight が sampler validity/coverage 由来で `(6,0)` の
  `254` を説明するか。
- Zoom `param_1[0x842/0x843/7]` の実 index 単位 (8byte 前提だが実 run で要確認)。
- Inner の "wrong plane/value" が sampler / prepass(+0x48) / span_gate(+0x40) /
  accum(+0x3c940) のどこか — typed cell dump で分離する対象。
