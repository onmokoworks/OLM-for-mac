## Parameter Schema Policy

このリポジトリでは、各 OLM プラグインの UI パラメータについて次の3層を分けて扱う。

### 1. UI schema

これは `PF_ADD_*` 定義から読める範囲で、次を含む。

- パラメータ名
- 型
- 初期値
- 最小値 / 最大値
- UI 上の表示レンジ
- popup の choice 数

この層については、ユーザーが毎回手で教えなくてもソースから自動抽出できる。一次情報は次の2つ。

- `/Users/onmk/Documents/Projects/Personal/OLM as/scripts/extract_mac_plugin_param_schema.py`
- `/Users/onmk/Documents/Projects/Personal/OLM as/refs/reports/mac_plugin_param_schema_20260629.md`

つまり「初期値」「最小最大」「checkbox/popup/slider の型」は、かなりの範囲で既に機械的に確定できる。
ただし 2026-06-29 の Windows fresh range 返却以降は、「Mac source がそう書いてある」
だけでは弱い。Windows AE が expose する `range_metadata` も同列の一次情報として扱う。

### 2. Host parity

Mac 側のプラグインに、その UI schema がちゃんと実装されているかという層。

- Windows 参照 manifest にあるパラメータが Mac 側にも存在するか
- disk ID / label / grouped label が大きくズレていないか
- AE 上で追加・設定・レンダーする前提が壊れていないか

この層の一次情報は次。

- `/Users/onmk/Documents/Projects/Personal/OLM as/scripts/audit_param_schema_vs_windows_refs.py`
- `/Users/onmk/Documents/Projects/Personal/OLM as/refs/reports/param_schema_windows_ref_audit_20260629.md`
- `/Users/onmk/Documents/Projects/Personal/OLM as/scripts/audit_windows_fresh_ranges.py`
- `/Users/onmk/Documents/Projects/Personal/OLM as/refs/reports/windows_fresh_ranges_audit_20260629.md`

### 3. Behavioral equivalence

これは「同じ値を入れたとき Windows AEX と同じ効き方をするか」の層。

ここは UI schema だけでは確定しない。別途必要なのは次。

- Windows Software 参照 PNG
- asm / objdump / Ghidra
- runtime trace
- Mac AE exact 検証

たとえば `0..100` の slider が一致していても、内部の正規化、丸め、分岐、境界処理が違えば出力はズレる。

## Practical rule

### 言えること

- 初期値や min/max は、毎回ユーザーが手入力しなくてもよい
- Mac 側の現実装については、かなりの範囲で自動抽出と監査ができる
- AE 上でデフォルト値を再現したいだけなら、ソースと schema report を正として扱ってよい

### まだ言えないこと

- 「Windows 版も必ず同じ初期値だった」とは、全プラグインでまだ断言しない
- 「max/min が同じだから効き方も同じ」とは言わない
- 「popup の default index が同じだから内部実装も同じ」とは言わない

## Current operating assumption

現時点では次の運用で進める。

1. 初期値は Windows fresh defaults があるならそれを優先する
2. レンジは Windows fresh ranges があるならそれを優先する
3. Windows manifest / request があるケースでは、その明示値を常に優先する
4. behavioral equivalence は別レーンで証拠化する
5. default に頼った検証ケースは、明示値ケースより弱い証拠として扱う

## Request replay policy

Windows 再レンダー request については、さらに次の区別をする。

- `fully-pinned`
  - `params_full` がある、または linked Windows reference case の visible params を request keys が全部カバーしている
- `partially-pinned`
  - linked reference case にある visible params を request が一部省略している
- `unlinked`
  - `source_case_id` ベースで比較できず、古い exploratory request として扱う

一次情報:

- `/Users/onmk/Documents/Projects/Personal/OLM as/scripts/audit_request_param_pinning.py`
- `/Users/onmk/Documents/Projects/Personal/OLM as/refs/reports/request_param_pinning_20260629.md`

2026-06-29 時点の要点:

- `olm_bitdepth_16bpc_normalized_exact_20260625.json` は `45/45 fully-pinned`
- `smoother2_legacy_full_current_aex_recapture_20260621.json` は `12/12 fully-pinned`
- `directionalblur_context_scale_20260606.json` の linked replay 2件は `2/2 fully-pinned`
- `radialblur_inner_20260605.json` の linked replay 3件は `3/3 fully-pinned`
- `smoother2_legacy_current_aex_recapture_20260621.json` は `2/2 fully-pinned`
- 監査全体では `fully-pinned=64`, `partially-pinned=0`, `unlinked=71`

残っている `unlinked` は、元 Windows reference case と 1:1 対応しない synthetic /
exploratory request であり、「暗黙 default に依存している」とは限らない。ただし
linked replay と同じ強さの provenance は持たないので、必要なら将来 `source_case_id`
付きの再パッケージへ寄せる。

したがって、今後 Win 側に再実行を頼むときは、まず `fully-pinned` request を優先し、
exploratory request は「仮説検証便」として別扱いにする。

### Materializing linked replay cases

linked replay で `source_case_id` がある request は、参照 manifest を土台に
`params_full` を自動展開できる。

- `/Users/onmk/Documents/Projects/Personal/OLM as/scripts/materialize_linked_request_params.py`
- smoke:
  `/Users/onmk/Documents/Projects/Personal/OLM as/refs/scripts/smoke_materialize_linked_request_params.py`

この script は linked reference case の visible params を順序付きで取り出し、
request 側の明示 override をその上に重ねて `params_full` を作る。つまり
exact recapture だけでなく、`Smoothness=0` のような control case も
「暗黙 default に頼らない full manifest」として固定できる。

さらに `refs/scripts/package_reference_requests.py` は package 作成時に、
選ばれた request JSON の一時コピーへこの materialize を自動適用する。
そのため、repo内の JSON を手で更新し忘れていても、Windows に渡す zip の
linked replay は package 時点で `params_full` を持つ。

`refs/scripts/check_reference_request_status.py` と
`refs/scripts/next_reference_actions.py` は、この package-time materialize を
踏まえた `current params_full x/y` / `packaged params_full x/y` も出す。
したがって pending request を見るときは、「今のJSONが弱いか」ではなく
「Windowsへ渡る package がどこまで fully-pinned 化されるか」で判断する。

2026-06-29 時点では少なくとも次の request に反映済み:

- `directionalblur_context_scale_20260606.json` linked replay 2件
- `radialblur_inner_20260605.json` linked replay 3件
- `smoother2_legacy_current_aex_recapture_20260621.json` 2件
- `smoother2_legacy_full_current_aex_recapture_20260621.json` 12件

## Examples

- `OLMBlur`
  - `Blur Amount`: default `1.0`, hard min `0.05`, hard max `1000.0`
  - `Number of Repeat`: default `2`, min `1`, max `10`

- `OLMSmoother2`
  - `Smoothness`: default `100`, min `0`, max `1000`
  - `Smoother Version`: popup default `SMOOTHER_V2`

- `OLMRadialBlur`
  - `Outer Strength`: default `212`, min `0`, max `3000`
  - `Inner Strength`: default `0`, min `0`, max `3000`

- `OLMKiraKira`
  - `Vertical Length`: default `50`, min `0`, max `1000`
  - `Glow Opacity`: default `100`, min `0`, max `100`

このメモの目的は、「初期パラメータやレンジは毎回人力確認が必要なのか」を曖昧にしないこと。
答えは「UI schema の範囲では不要。ただし、効き方の一致までは別証拠が要る」。

## Current fixed answer by plug-in

2026-06-29 fresh range return後の時点では、各プラグインの扱いを次で固定する。

| Plug-in | UI defaults/min/max | Windows request replay | 今の運用結論 |
| --- | --- | --- | --- |
| `OLMBlur` | fixed | fixed | 初期値・最小最大は source-backed として確定扱いしてよい |
| `OLMColorKey` | mostly fixed | fixed | request replay では困らない。Windows manifest 上の `Amount / Edge Thin / Edge Blur` は grouped-name 正規化の宿題が残る |
| `OLMDirectionalBlur` | mostly fixed | fixed | 2026-06-29 first-pass range alignmentで `Front/Back Blur Strength`, `Alpha Fade`, `Seed` を Windows 側へ揃えた。残りは grouped-name (`Sharp Tail`) と Windows-no-range 項目 |
| `OLMDistanceGradation` | fixed | fixed | 初期値・最小最大は source-backed として確定扱いしてよい |
| `OLMKiraKira` | range mismatchあり | request replay fixed | `Ramp` 系 name driftに加え、`Blur Mode`, `Strength Multiplier`, `Glow Opacity` などの host range が Windows とズレる |
| `OLMRadialBlur` | mostly fixed | fixed | `Strength`, `Ratio`, `Seed` は Windows 側へ寄せた。`Offset` は duplicate-label 正規化を含む監査宿題が残る |
| `OLMSmoother` | mostly fixed | n/a | `Do Smooth Range` が Windows manifest 側だけに見えており、完全一致はまだ保留 |
| `OLMSmoother2` | fixed | fixed | 2026-06-29 first-pass range alignmentで `Smoothness`, `Extra Smooth`, `Smooth Range`, `Gamma Value` を Windows 側へ揃えた |
| `OLMToonDilate` | fixed | n/a | 2026-06-29 range alignmentで `Search Radius` を Windows `0..100` へ揃えた |

### Meaning of the table

- `fixed`
  - Mac source の `PF_ADD_*` と、現在の Windows reference/request 運用の両方で困らない
- `mostly fixed`
  - request replay には十分だが、Windows manifest 側の grouped label / alias にまだ少数の正規化余地がある

### Practical answer

今後の実務上の答えは次で固定する。

1. 参照 request を投げるだけなら、こちらから毎回「初期値はこれ、max はこれ」と人力で伝えなくてよい
2. linked replay request は `fully-pinned` を優先し、default 依存を避ける
3. もし default 挙動そのものを検証したい場合は、Mac source schema を正として request に明示値を書く
4. 例外的に追加注意が必要なのは、現状では `OLMColorKey` の grouped-name、`OLMDirectionalBlur` の `Sharp Tail`、`OLMKiraKira` の Ramp 系、`OLMSmoother` の `Do Smooth Range`
