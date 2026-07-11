# スモーク監査 + RadialBlur Inner クラッシュ修正 — 2026-07-06(Fable 5)

SESSION_STATUS_20260706_EOD.md の主張を全件再実行して監査した結果。
全て本日の実測(コマンドは各 smoke_*.py そのまま)。FACT のみ、推測は明記。

## 監査結果(SESSION_STATUS の表との照合)

| プラグイン | 記載 | 実測 | 判定 |
|---|---|---|---|
| OLMDistanceGradation | 16/16 PASS | basic 12/12 OK + extended 16/16 OK | ✅ 記載どおり |
| OLMRadialBlur Zoom | 1/1 PASS | 1/1 OK (max=1) | ✅ 記載どおり |
| OLMRadialBlur TinyRotation | 1/1 PASS | 1/1 OK(緩ゲート、max=255 は既知の reference-path-split) | ✅ 記載どおり |
| **OLMRadialBlur Rotation** | **3/3 PASS** | **0/3 FAIL**(cpp/python 両スクリプトとも。case_0001 mean=1.90, case_0002 mean=1.31, max=255) | 🔴 **記載と不一致** |
| OLMRadialBlur Inner | SIGSEGV | 再現 → 原因特定 → **修正済み**(下記) | 🔴→🟡 |
| OLMDirectionalBlur angle-0 | 0/5 FAIL | 0/5 FAIL (max=164/252, mean≈3.8) | ✅ 記載どおり |
| OLMDirectionalBlur rotated-full | 0/2 FAIL | 0/2 FAIL (max=164/251) | ✅ 記載どおり |
| OLMKiraKira | 0/3 FAIL | 0/3 FAIL (case1/2 max=21/24 で惜しい、case3 max=233 mean=53.8 で大破) | ✅ 記載どおり |
| OLMSmoother (v1) | 0/3 未調査 | 0/3 FAIL (max=127/127/128, mean≈1.0-1.4) | ✅ 記載どおり |
| OLMToonDilate | 2/3 | 2/3 (case_0003 max=65280 mean=44015 — 16bpc ケースで比較が桁ごと破綻) | ✅ 記載どおり |

注: OLMBlur / OLMColorKey / OLMSmoother2 の PASS 主張は今回未再実行(スポット対象外)。

### 監査所見 1: Rotation「3/3 PASS」は現ツリーで再現不能(虚偽または陳腐化)

- `smoke_olmradialblur_cpp_rotation_cli.py` と `smoke_olmradialblur_rotation_cli.py`
  の両方で 0/3。HEAD 版 main.cpp に戻して再ビルドしても同一数値 → 本セッションの
  未コミット変更による退行では**ない**。
- cpp 版スクリプト自身が docstring で「intentionally a red measurement scaffold」
  (意図的に厳密ゲートで赤)と明記している。「3/3 PASS」がどの実行を指したのか
  根拠不明。**ステータス文書の PASS 主張は鵜呑みにしないこと。**
- case_0010 は tiny-rotation 側の緩ゲートでは OK であり、GPU レンダ参照との
  path-split(GOTCHAS #7)の既知論点と整合(INFERENCE)。

### 監査所見 2: Inner SIGSEGV の真因は「16bpc 対応の中途半端な手術」(修正済み)

SESSION_STATUS の原因仮説(span<=0 / ゼロ除算 / クリップ処理)は**外れ**。実際は:

- 未コミットの 16bpc PNG 対応(read/write + zoom レンダラは完全対応)が、
  **rotation レンダラだけ出力確保(`rgba16`)と `max_val` 導入で止まっており、
  画素書き込みが旧 `out.rgba[...]`(空 vector)のまま**だった。
- Inner ケース(case_0011-0013)の入力は 16-bit RGBA PNG → `out.rgba` が
  空(data()==nullptr)→ `strb w8,[x9,x19]` で NULL 書き込み → SIGSEGV。
  lldb で `render_olmradialblur_rotation` 内クラッシュを確認(FACT)。
  ビルド時警告 `unused variable 'max_val'`(main.cpp:2148)が未完了の証跡。
- **修正**: rotation レンダラの RGB/alpha 書き込みを zoom と同じパターンで
  16bpc ガード化(`max_val` スケール、`rgba16` 書き込み、witness u8 は `>>8`)。
  量子化セマンティクス(rotation は RGB に epsilon なし)は既存のまま維持。
- 修正後: 3 ケースともクラッシュせず完走。Zoom 1/1 / TinyRotation 1/1 の
  PASS 維持を確認(8bpc 退行なし)。

### 監査所見 3: Inner の本丸はアルゴリズム不一致(クラッシュとは別問題)

修正後の Inner 実測: case_0011 mean=20186 / case_0012 mean=9965 /
case_0013 mean=12246(いずれも 16bpc スケール、max=65535)。
出力の 3-9 割の画素が大きく違う = クリップ云々ではなく **Inner モードの
アルゴリズム自体が未確立**。decomp 裏取りからの再実装レーン級の作業。

### 監査所見 4: ToonDilate case_0003 も 16bpc 起因の疑い(INFERENCE、未着手)

max=65280 (=255×256) / mean=44015 は「8bit 相当の出力を 16bit 参照と比較」型の
破綻シグネチャ。cli/OLMToonDilate の PNG 入出力の 16bpc 対応を確認するのが先。

## 委任状況

- gemini CLI: 本体は `npx -y @google/gemini-cli`(0.49.0)で起動可能だが
  **未認証**(GEMINI_API_KEY 無し、~/.gemini に oauth 資格情報無し)。
  委任再開には一度 `gemini` を対話起動して認証するか API キー設定が必要。
- codex(GPT-5.4)レーン: 委任を試みたが **usage limit 到達で即時失敗**
  (リセット 2026-07-07 14:58、resume 用セッション:
  `codex resume 019f37d9-8d3e-7aa2-92ed-a86ff51ecbec`)。
- 両レーン不可のため、Smoother v1 診断は Claude(Fable 5)が直接実施(下記)。

## 監査所見 5: Smoother v1 の主因 — SubHandler8/16 の walk-B 出力 X の取り違え(修正済み)

失敗シグネチャ: R チャネルのみ max=127(=255×0.5、MLAA ブレンド上限)、
浅い斜めエッジの凹コーナーから黒領域へ片側減衰ランプが 30-60px 伸びる。

診断手順(全て FACT、env ゲート式トレース `OLMSMOOTHER_TRACE_X/Y` を
OLMSmoother_port.cpp に追加して取得):
1. 実ケースの 160×160 切り出しで再現(スミア 132px)。
2. トレースで特定: dispatch center=(135,70) が終点 p11=(70,70) を報告 —
   **70 は y 座標であり、X スロットに y が漏れている**。
3. decomp FUN_1800033d0(8bit)の 1565 行: 2 回目の EdgeWalker が out_x を
   `local_res20[0]` に**上書き**し、以降の 3 箇所(1621/1624/1643)は
   walk B の終点 X を読む。port はこの上書きを `(void)` で捨て、
   元の値(= y 座標)を使っていた。
4. 16bit twin(FUN_180002740 の 1126 行)も同族バグ: walk B の out_y が
   `local_res18[0]` に上書きされる仕様を port が無視(*o12 に古い x が入る/
   距離項 b が y−A.y 誤用)。

修正(mac/OLMSmoother/Mac/OLMSmoother_port.cpp):
- 8bit: bVar7 枝と neither 枝の `*o11` と距離項 a を walk B 終点 X に修正。
- 16bit: walk B 終点 Y を local_res18_0 に反映(元 x は saved_x に退避)、
  距離項 a/b/c/d を decomp 1182-1187 どおりに修正。

結果(smoke_olmsmoother_cli.py、before → after):
- case_0001: mean 1.0145 / nz 30687 → **mean 0.0206 / nz 949**
- case_0002: mean 1.3083 / nz 41401 → **mean 0.0431 / nz 1981**
- case_0003: mean 1.4269 / nz 45417 → **mean 0.0699 / nz 2793**

残課題(未解決・別バグ): まだ 0/3 FAIL。残差は R のみ max=127 で双方向
(塗り過ぎ 530px + 塗り漏れ 419px @case_0001)。例: (442,176) は
ref R=127 / cand 0(塗り漏れ)。SubHandler の他分岐か AltHandler /
kernel case0-1 に同族の座標・エイリアシング不一致が残っている疑い。
同じトレース手法((442,176) 等を OLMSMOOTHER_TRACE_X/Y で追う)で
続行可能。トレースは env 無指定時は完全に無効。

作成: 2026-07-06 Fable 5(監査・修正・委任オーケストレーション)
更新: 同日 — Smoother v1 診断と walk-B 修正を追記
