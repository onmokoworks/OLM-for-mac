# OLM移植 セッション状況メモ — 2026-07-06 EOD

## 全プラグイン スモークテスト状況（最終確認）

| プラグイン | スモークテスト | 状況 |
|---|---|---|
| OLMBlur | ✅ 7/7 PASS | 完了 |
| OLMColorKey | ✅ 7/7 PASS | 完了 |
| OLMDistanceGradation | ✅ 16/16 PASS | 完了 |
| OLMRadialBlur Rotation | ✅ 3/3 PASS | 完了 |
| OLMRadialBlur Zoom | ✅ 1/1 PASS | 完了 |
| OLMRadialBlur TinyRotation | ✅ 1/1 PASS | 完了 |
| OLMSmoother2 (legacy) | ✅ 12/12 PASS | 完了（残差は許容閾値内） |
| OLMRadialBlur Inner | 🔴 SIGSEGV クラッシュ | 要対応 |
| OLMDirectionalBlur angle-0 | 🔴 0/5 FAIL | 要対応 |
| OLMDirectionalBlur rotated-full | 🔴 0/2 FAIL | 要対応 |
| OLMKiraKira | 🔴 0/3 FAIL | 要対応 |
| OLMSmoother (v1) | 🔴 0/3 FAIL | 未調査 |
| OLMToonDilate | ⚠️ 2/3 PASS | 1ケースFAIL |

---

## 未完了タスク詳細

### 1. 🔴 OLMRadialBlur Inner — SIGSEGV クラッシュ
- **症状**: exit=-11（SIGSEGV）でクラッシュ
- **経緯**: min(base_span, 3000)*fade_factor クリップ実装→max=65535破綻→修正試みでクラッシュ
- **原因仮説**: float/int型不整合、またはspan<=0になりゼロ除算 or 境界外アクセス
- **次アクション**: cli/OLMRadialBlur/main.cpp のInnerモードクリップ処理を再検証

### 2. 🔴 OLMDirectionalBlur — angle-0 / rotated-full FAIL
- **症状**: angle-0が5ケース全FAIL, rotated-full-choreが2ケース全FAIL
- **経緯**: render_scale_x/y をAEプラグイン側+CLIに実装済み。残るmax=241等は「スケール問題ではない」と結論
- **次アクション**: angle-0の残差ピクセルを解析し、ブラーカーネル自体のバグを調査

### 3. 🔴 OLMKiraKira — 3ケース全FAIL
- **経緯**: hotspot compose/merge/normalize各ステージまで調査済み
- **次アクション**: refs/conformance/olmkirakira_hotspot_* レポートを参照し再確認

### 4. 🔴 OLMSmoother (v1) — 0/3 FAIL（未調査）
- **次アクション**: smoke_olmsmoother_cli.py のFAIL内容を確認してから着手

### 5. ⚠️ OLMToonDilate — 1ケースFAIL
- **次アクション**: smoke_olmtoondilate_cpp_cli.py -v で詳細確認

---

## Smoother2 残差（継続調査中）

### case_0001: max=43、case_0004: max=113（PASS判定だが精度向上が望ましい）

- **case_0004 最大差分 (1903,519)**: Mac alpha=0、Win alpha=113 → Macがスキップ
- **(1472,216) 問題**: idx=0x40 → win_cardinal_9 + win_cardinal_6 が呼ばれるが
  poly.count=0 のままpassthroughになっている（cardinal内部のpredicateが失格を返す疑い）
- **デバッグツール**: win_FUN_1800104d0_append に逆トレース追加済み
  次回: g_olmsmoother2_trace_x=1472 g_olmsmoother2_trace_y=216 で再確認

---

## 実装済み修正（本セッション）

| プラグイン | 修正内容 |
|---|---|
| OLMSmoother2 | idx計算のbSE/bSW/uVar7/eR0ビット割り当て精緻化 |
| OLMSmoother2 | cardinal scan境界チェックをリニアオフセットから座標ベースに修正 |
| OLMSmoother2 | win_FUN_1800104d0_appendに逆トレース追加（デバッグ用） |
| OLMSmoother2 | poly._pad_2c = 0 初期化追加 |

---

## 次回セッション開始手順

1. RadialBlur Inner クラッシュ調査
   python3 refs/scripts/smoke_olmradialblur_cpp_inner_cli.py 2>&1 | head -30
   → cli/OLMRadialBlur/main.cpp のInnerモードクリップ処理を確認

2. OLMSmoother v1 FAIL確認
   python3 refs/scripts/smoke_olmsmoother_cli.py 2>&1

3. Smoother2 逆トレース再確認
   bash refs/scripts/build_olmsmoother2_cli.sh
   g_olmsmoother2_trace_x=1472 g_olmsmoother2_trace_y=216 ./cli/OLMSmoother2/olmsmoother2_cli [args] 2>&1 | grep "trace"

---
作成日: 2026-07-06 19:08 JST
