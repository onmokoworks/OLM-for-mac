# Mac Parallel Analysis Lanes - 2026-07-03

## Summary

Windows 側の返却待ちとは独立に、Mac 側だけで前に進められる lane を
2026-07-03 時点で整理した。ここでは「いま source を大きくいじるべき
lane」ではなく、「既存証拠を再利用しながら次の bounded step を打てる
lane」を優先する。

## Current parallel picks

### 1. OLMRadialBlur

- 状態:
  - `Zoom` は broad retune ではなく caller-collapse / preserved-validity /
    accumulated polar RGBA の narrow diagnostic lane
  - `tiny Rotation` は upstream RGB / substitute-path / neighboring-row
    ownership lane
  - `Inner` は typed per-cell witness 待ちで、Mac-only では優先度を落とす
- いま Mac だけでやる価値があること:
  - `tiny Rotation case_0010 (1614,6)` の pre-inverse-sample ownership dump を
    さらに絞る
  - row `843..845`, angle `1601..1604` 周辺の source-polar population /
    scatter / normalized polar cells の局所観測を増やす
- やらないこと:
  - final byte tuning
  - validity-alpha を global fix として昇格
  - `Inner` の broad tuning
- 2026-07-03 refresh:
  - `scripts/analyze_radialblur_tiny_rotation_same_row_audit.py`
  - `scripts/analyze_olmradialblur_tiny_rotation_source_polar_probe.py`
  - `scripts/analyze_olmradialblur_tiny_rotation_row_coupling_probe.py`
  - `scripts/analyze_olmradialblur_tiny_rotation_support_envelope.py`
  - `scripts/analyze_olmradialblur_tiny_rotation_lane.py`
  - `scripts/analyze_olmradialblur_tiny_rotation_source_candidates.py`
  を current source で再実行し、smoke も通した。結論は変わらず、
  `tiny-rotation-pending-upstream-rgb-or-substitute-proof` のまま。

### 2. OLMKiraKira

- 状態:
  - historical note では hotspot `(934,118)` は traced Windows と current Mac
    が `144` で一致し、canonical reference が `131` と整理していた
  - ただし 2026-07-03 の live Mac AE probe では exported PNG center が `91`、
    reference が `131`、row above が `186 vs 191`
  - さらに同日、historical request を current binary で 8bpc rerun すると
    hotspot `144` を再現できた
  - つまり old `144` witness は explicit `8bpc` lane、live dark output は
    `16bpc` host lane で、両者は同じ host context ではない
  - しかも installed MediaCore binary は freshly built current binary と
    SHA256 一致
  - なので KiraKira live lane は「provenance-only で押す」より前に、
    `8bpc witness` と `16bpc live host` を分離して扱う必要がある
- いま Mac だけでやる価値があること:
  - hotspot neighborhood probe を少し広げ、placement/class drift の可能性を
    局所的に潰す
  - merge-mode / endgame control coverage は別 lane として source coverage を
    読む
- やらないこと:
  - hotspot lane だけを根拠に `OLMKiraKira.cpp` を retune
  - gain / luma / final quantization の broad tweak

### 3. OLMColorKey

- 状態:
  - normalized 8bpc packaged slice は AE exact
  - covered 16bpc slice も full batch `9/9 exact`
  - 32bpc focused probe request は materialized 済み
  - 2026-07-03 の Windows return は import 済みだが PNG-only のため
    `probe-only`
- いま Mac だけでやる価値があること:
  - bit-depth expansion status/reporting の自動化
  - 32bpc comparison policy を mechanical に扱うための補助更新
  - 次の EXR-first request に向けた request / note / intake 境界の固定

### 4. OLMToonDilate

- 状態:
  - 8bpc packaged slice は AE exact
  - 16bpc focused request は materialized / verified / shared 済み
- いま Mac だけでやる価値があること:
  - request lifecycle の tracking
  - 返却後比較をすぐ走らせるための report refresh 整備

### 5. OLMDistanceGradation

- 状態:
  - 8bpc packaged slice は AE exact
  - 16bpc は `case_0023` が代表 witness lane
- いま Mac だけでやる価値があること:
  - `case_0023` の threshold-family / provenance split を維持する比較更新
  - current-AEX export / boundary family の drift check 継続
- やらないこと:
  - broad PNG tuning
- 2026-07-03 refresh:
  - `scripts/analyze_distancegradation_case0023_source_candidates.py`
  - `scripts/analyze_distancegradation_case0023_threshold_family.py`
  を current source / current reports で再生成し、smoke も通した。
  threshold-family は引き続き historical bounded context で、
  implementation tuning へ戻す根拠にはならない。

### 6. OLMBlur

- 状態:
  - 8bpc packaged slice は AE exact
  - 16bpc `case_0006` は implementation mismatch より provenance/export lane が
    主疑点
- いま Mac だけでやる価値があること:
  - provenance/export watchlist の整理
- 優先度:
  - DistanceGradation より後

## Tooling update added today

以下を追加し、最新 `refs/reports/runtime_trace_summary.json` に依存せず、
既存の archived runtime summaries から比較結果を再生成できるようにした。

- `scripts/refresh_curated_runtime_trace_comparisons.py`
- `refs/scripts/smoke_refresh_curated_runtime_trace_comparisons.py`

初回 curated refresh 対象:

- `OLMDistanceGradation case_0023 refcon-wordmap`
- `OLMRadialBlur tiny Rotation anchor-pointer`
- `OLMKiraKira aggregation/compose BT.709`
- `OLMSmoother2 producer-path diff`

これで Windows 返却待ちの間にも、他プラグインの既存証拠をローカルで
再読・再分類しやすくなった。

加えて、parallel lane 全体を一画面で見るためのレポートを追加した。

- `scripts/report_parallel_olm_lanes.py`
- `refs/scripts/smoke_report_parallel_olm_lanes.py`
- 最新出力:
- `refs/reports/parallel_lane_report.json`
- `refs/reports/parallel_lane_report.md`

このレポートは次の二系統を同時に出す:

- bit-depth expansion の request lifecycle
  - `preview -> materialized -> packaged -> shared -> returned -> compared`
- provenance/export first lane
  - `OLMBlur case_0006`
  - `OLMKiraKira hotspot`
  - `OLMDistanceGradation case_0023`

KiraKira の current live host drift は以下に固定した:

- `refs/conformance/olmkirakira_live_hotspot_probe_20260703.json`
- `refs/conformance/olmkirakira_live_hotspot_probe_20260703.md`

さらに、historical 8bpc witness と live 16bpc host を混ぜないための
split note を追加した:

- `refs/conformance/olmkirakira_witness_path_split_20260703.json`
- `refs/conformance/olmkirakira_witness_path_split_20260703.md`

## Recommended next local steps

1. `OLMRadialBlur tiny Rotation` の upstream ownership lane をさらに狭める
2. `OLMKiraKira` hotspot neighborhood を widened placement probe として再整理
3. `OLMColorKey` / `OLMToonDilate` の bit-depth request lifecycle を summary に反映
4. `OLMDistanceGradation case_0023` の drift/provenance lane を維持
