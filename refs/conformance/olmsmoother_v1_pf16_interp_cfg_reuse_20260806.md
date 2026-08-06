# OLMSmoother v1 PF16 interpolation CFG / PF8再利用監査

対象は SHA-256
`6206f601b645dc915b78269ae403e5cbee642ac2812e320d85838ec72135fe82`
の actual `OLMSmoother.aex` である。

## 関数境界

- `MainInterpKernel16`: `0x180004b80..0x18000556f`、2543 bytes、617命令。
  PE unwind table上は `4b80..4e11`, `4e11..529a`, `529a..54b8`,
  `54b8..556f` の4 spanから成る。末尾は `0x18000556a` から
  `0x1800054b8` への共有epilogue jump。
- `InterpExecutor16`: `0x180005f60..0x180006263`、771 bytes、188命令。
  unwind table上は `5f60..6034`, `6034..6258`, `6258..6263` の3 span。
  `0x180006262` の `ret` で終了する。

単一unwind spanだけを「function end」とすると、どちらもfunclet/共有epilogueを
欠落する。PF8の既存CFG資産と同様、上記の連続spanを一関数として扱う必要がある。

## call target

Main16は `ColorCompare16(0x1800021f0)` を8回、
`InterpExecutor16(0x180005f60)` を5回呼ぶ。ほかに既に移植済みのcurve helper
`0x180001000/1020/1040/1070/1090`、16-bit color blend `0x180001620`、
neighbor extractor `0x180003ff0`、共通helper `0x18000b720` を呼ぶ。

Executor16はcurve objectへの間接callを1回、16-bit alpha blend
`0x180001ed0` を2回呼ぶ。間接callは新しい未知host APIではなく、PF8 Executorにも
同じ位置に存在するweight evaluator virtual callである。

## PF8 CFGの再利用方針

Main16と既存Main8 (`0x180005570..0x180005f5f`) は、長さ2543 bytes、
617命令、mnemonic列、分岐構造が完全に同型である。差は次に限定される。

- `ColorCompare16` / `ColorCompare8`
- `InterpExecutor16` / `InterpExecutor8`
- `ColorBlend16` / `ColorBlend8`
- `NeighborExtract16` / `NeighborExtract8`
- world field `+0x20` / `+0x18` とpixel scale `*8` / `*4`

したがってPF8 generatorをparameterizeし、call mapping、world offset、pixel strideを
PF16 profileへ差し替えるのが最短である。Main16専用の新規制御ロジックは不要。

Executor16とExecutor8はmnemonic列で188対187命令。唯一の制御命令差は
PF16 `0x180006089` のalignment `nop dword ptr [rax]` で、除けば同型である。
一方、pixel load/storeは `word/read16/write16`、channel offset `0/2/4/6`、
pixel stride `8` に変わり、stack local配置もPF8と異なる。Executor generatorでは
CFG emitterを共有できるが、PF8 generated includeの機械的な文字置換は不可。
indirect weight call、word operand、PF16 stack layoutを明示的にprofile化する。

監査は次で再現できる。

```sh
python3 tools/emulation/audit_olmsmoother_v1_pf16_interp_cfg_reuse_20260806.py
```
