# OLM Tools の Apple Silicon 移植記録：ブログ用ブリーフ

作成日: 2026-07-10  
対象: Windows 版 OLM Tools AEX の macOS / Apple Silicon 移植

## 制作期間と開始点

制作期間: **2026-04-18 から 2026-07-10 までの84日間**。プロジェクトは現在も継続中である。

履歴上は、Claude Code CLIでの最初期の試行、リポジトリへの記録、プロジェクト専用ログを分けて書くと正確である。

- **2026-04-18**: Claude Code CLIのグローバル履歴に、`olm_disasm` をMacで動かしたいという最初の相談が残っている。同日、ダウンロードしたOLM一式を逆アセンブルし、Ghidra/GhidraMCPで解析したいという依頼が記録された。記事上の実質的な制作開始日はここに置く。
- **2026-04-19〜20**: OLMプラグインをmacOSへ移行する方針、ColorKeepやOLMBlurの導入、OLMSmoother2のロード確認、逆アセンブル継続の相談が続いている。
- **2026-05-08**: リポジトリの最初の handoff commit。OLMSmoother2、OLMSmoother v1、DistanceGradation、ColorKeep、OLMBlur のMac側ポートと、逆アセンブル資料・初期検証スクリプトが持ち込まれた。
- **2026-06-04**: プロジェクト専用のClaude Codeセッションログが始まり、Windows参照PNG/manifest、Ghidra/GhidraMCP、AEなしCLIハーネスを前提にした体系的な解析・移植へ移行した。
- **2026-06-05**: Claude CodeセッションからCodexへ引き継ぐための `HANDOFF_CODEX.md` が作成された。以後は複数のエージェントを使った解析、Windows側の参照取得、Mac側の実装と検証を並行して進めている。

したがって、記事では「4月18日にClaude Code CLIで構想と初期作業が始まり、5月にリポジトリへ土台を記録し、6月から体系的な逆解析と検証へ進み、現在まで約3か月継続している」と表現する。4月の詳細な会話本文はすべて残っているわけではないが、Claude Codeのグローバル履歴、Gitの初期commit、6月のプロジェクトログと引き継ぎ文書で開始時期と流れを確認できる。

## 進捗の時系列

ここでいう exact は、Mac AEの出力をWindows AE Software referenceと比較し、宣言されたケースで `max_diff=0` になったものだけを数える。CLI一致、near-miss、known-red、reference-only は含めない。

| 日付 | タスクの節目 | exactの記録 |
|---|---|---:|
| 2026-04-18 | Claude Code CLIでOLM一式の逆アセンブル、Ghidra/GhidraMCP、Mac移植の構想を開始 | まだexactゲートなし |
| 2026-05-08 | 最初のGit handoff。既存ポート、逆アセンブル資料、初期検証スクリプトをリポジトリに記録 | まだ正式なAE exact集計なし |
| 2026-06-04〜06 | Windows参照、manifest、AEなしCLI、Ghidra解析、各プラグインの証拠化を整備 | CLI exact中心。AE exactの母数は未固定 |
| 2026-06-18 | 最初のMac AE host validation return | 33/48 exact |
| 2026-06-19 | 正規化8bpcの初回パッケージ検証 | 59/70 exact |
| 2026-06-20 | Smoother v1の解像度問題を修正し、8bpc exactを更新 | 62/70 exact |
| 2026-06-25 | 16bpc Windows reference returnを取り込み、深度別検証へ移行 | exact判定を深度別に分離 |
| 2026-07-09 | ColorKey / ToonDilateの16bpc covered sliceを確認 | 12/12 exact |
| 2026-07-10 | 32bpc Software / FLOAT EXRのWindows 48ケースを受理 | Mac AE exactは0/48、検証中 |

6/18、6/19、6/20の分母が違うのは、検証対象のケースセットが途中で増えたためである。したがって、この数値は同一母数の単純な成長曲線ではなく、「どの時点でどの検証セットを閉じたか」を示す履歴として扱う。

## 現在のexact数を図にする

2026-07-10時点で、記事に載せやすい最小のグラフはbit depth別である。`#` は exact、`.` は未完了または未判定を表す。

```text
8bpc   62/70  88.6%  [##################..]
16bpc  12/12 100.0%  [####################]  covered sliceのみ
32bpc   0/48   0.0%  [....................]  Windows EXR受理、Mac AE検証中
```

現在の受理済みケースを単純合算すると `74/130 = 56.9%` になる。ただしこれはリリース完成率ではない。8bpcはパッケージ済みslice、16bpcはColorKey/ToonDilateのcovered slice、32bpcはWindows参照が揃っただけでMac exact未成立という異なる状態を含むためである。記事では、この合算値よりも `8bpc 62/70`、`16bpc 12/12`、`32bpc 0/48` を主表示にする。

## この記事で伝えたいこと

これは、After Effects 用の古い Windows プラグインを、ソースコードなしの状態から Apple Silicon 向けに移植しようとしている記録である。

単に画像を見比べて似た処理を書く話ではない。最終目標は、同じ入力、同じパラメータ、同じ After Effects 設定、同じ bit depth で、Windows 版 AEX の Software render と Mac 版プラグインの出力を一致させることだ。最終的な合格条件は `max_diff=0` の `AE exact` とする。

現在はまだプロジェクト全体の完了には到達していない。しかし、画像差分だけで進めると危険な理由、静的解析と動的解析の役割、Windows と Mac の往復を減らす方法、そして「何が分かったら完了と言えるのか」を整理できる段階まで進んだ。制作の中心は、単なるポート作業から、参照データの provenance、AEXの実行経路、バイナリ由来の仕様、AE上の出力を一つずつ照合する検証プロジェクトへ変化している。

## 1. 最初の発想と最初の壁

当初は、Windows の After Effects でエフェクトを適用した画像とパラメータを集め、Mac 側で同じ処理を再実装し、PNG の差分を見ながら調整する方針だった。

この方法は小さな処理の入口としては有効だった。単純な blur、color key、dilate などは、入力画像と出力画像を並べることでアルゴリズムの候補を絞れる。しかし、次の問題がすぐに現れた。

- 参照画像が GPU 経路で生成されている可能性がある
- `ADBE Force CPU GPU` は実際の実行経路を示さない
- AE のプロジェクト bit depth や renderer 設定が前回の状態を引き継ぐ
- PNG は 16bpc や 32bpc の内部値を保持できない
- パラメータ値が同じでも、AE 上の UI 値、内部構造体、実際の writer の値が一致するとは限らない
- 小さな差分が、アルゴリズムの誤りなのか、丸めなのか、AE のホスト処理なのか判別できない

特に、CUDA と Software Only を切り替えても `ADBE Force CPU GPU = 1` が変わらなかった。したがって、この値を CPU/GPU 判定に使うのはやめ、プロジェクトの renderer 設定と参照生成条件を別々に記録することにした。

## 2. 最初の大きな方針転換：PNG ではなく参照経路を固定する

画像差分は症状を示すが、原因を説明しない。そこで、正となる参照を次のように固定した。

**Windows AE の Software renderer を canonical reference とする。**

参照セットには、少なくとも以下を記録する。

- After Effects のバージョン
- Project renderer とその設定
- color management
- 8bpc / 16bpc / 32bpc
- 入力画像と hash
- パラメータ manifest
- 出力形式と channel order
- 参照画像を生成した AEX のバージョン

GPU 参照は別プロファイルを作らない限り、互換性の合格判定に使わない。古い参照や GPU 経路の画像と CPU AEX を比較して、Mac 実装を誤って合わせ込まないためである。

## 3. 完了条件を作り直す

途中で「何ケース exact だったか」がプラグイン全体の進捗のように見えてしまった。そのため、完了単位をプラグイン名から feature/path/bit depth の組に分解した。

例えば、Smoother2 は一つの行ではなく、次のように分ける。

- no-key
- legacy/key
- gamma correction
- v1/v2 mode
- 8bpc / 16bpc / 32bpc

状態も一語に混ぜない。

- `correctness_status`: 出力の正しさ
- `host_status`: Mac AE で実際に操作・レンダーできるか
- `work_lane`: 次に許される作業

`AE exact` は最終的な完了だけに使う。`CLI exact` は強い中間証拠だが、AE exact の代わりにはしない。`binary-grounded` はコードや trace から規則が説明できる状態、`guarded` や `known-red` は残差を管理しているだけ、`blocked` は追加証拠なしに進めると危険な状態である。

これにより、「AE にはロードできるが処理が正しいか不明」「CLI では一致するが AE では未検証」「一部ケースだけ exact」を区別できるようになった。

## 4. 使った道具と役割

### Ghidra / GhidraMCP

Windows AEX の関数、定数、分岐、OpenCV 呼び出し、ループ構造を読むために使う。Ghidra の decompile は便利だが、プロジェクトやプログラムを取り違える危険があるため、チェックイン済みの disassembly/decomp と照合する。最終的な根拠は、Ghidra の見た目だけでなく objdump、命令列、文字列、呼び出し規約まで確認する。

### objdump / asm / decomp

PNG 差分よりも、次のような仕様を確定する証拠として重視する。

- float / double / integer のどれで計算するか
- floor / ceil / round / truncate
- clamp の位置
- 境界外を skip / clamp / repeat するか
- サンプリング順序
- RGB と alpha の処理順
- writer 前の float と最終 byte の変換

Windows と Mac のバイナリ byte 列を同じにすることは目標にしない。コンパイラ、ABI、最適化、SIMD、CPU 命令が異なるためである。代わりに、定数、分岐、丸め、境界、writeback の意味論を一致させる。

### CDB / WinDbg 系の runtime trace

静的解析だけでは、実際にどの branch が選ばれ、どの値が writer に渡されたか分からない場合がある。そのとき Windows 側で debugger を使い、関数や命令に breakpoint を置き、入力から出力までの typed witness を取る。

ただし、広い範囲に breakpoint を置くとログが膨大になり、処理も遅くなる。現在は、対象ピクセル、対象 branch、対象 intermediate、writer 直前の値だけを定義した「狭い trace contract」を作る方針に変えた。

実際に、RadialBlur では hook を仕掛けたあと AE を resume していなかったため trace が進まない不具合があった。また、live だった命令の直前に hook を置いた結果、関数引数がまだレジスタに入っていない地点を見ていた。命令が実行されたことと、欲しい値が観測できたことは別である。

### Unicorn と AEX CPU simulator

Windows AEX の CPU 処理を Mac 上で動かし、入力構造体や中間値を観測するための橋渡しとして使う。AE の GPU 経路を再現するものではなく、Windows の実バイナリを完全に置き換えるものでもない。

特に重要だった ABI の知見は以下である。

- AE の `PF_Pixel` はメモリ上では RGBA ではなく ARGB
- Win x64 の 5 番目以降の引数は stack にある
- float 引数は XMM レジスタに入る
- AE 16-bit の内部値を単純に 2 倍してはいけない
- 大きな stack frame では `GS` の TEB 設定が必要

これらは、値がもっともらしいのに結果だけが違う原因になりやすい。

### OpenCV detour

DistanceGradation や KiraKira の AEX 内部には OpenCV 4.5.5 系の処理が含まれている。全命令を Unicorn で実行すると、distance transform などは非常に遅い。そこで、プラグイン固有のロジックは emulation し、既知の OpenCV primitive だけを native 実装に差し替える detour 層を設計した。

これはプラグイン全体を再実装するためではない。`cvThreshold` や precise distance transform のような、ライブラリ関数の境界を短絡するためである。detour と完全 emulation の dual-run が一致しても、それだけでは Windows 実機との一致を証明しない。特に float/SIMD 処理は Windows の capture が必要になる。

## 5. bit depth を後回しにしない理由

8bpc では、内部計算の小さな誤差が最終 byte で隠れることがある。16bpc では half-step や PF16 writer の差が表に出やすく、32bpc では float のまま保持されるため、premultiply、clamp、denormal、累積順序、writer の差が露出する。

したがって、8bpc だけの一致は「アルゴリズム全体が正しい」という証明ではない。参照形式も分ける。

- 8bpc: PNG でもよい
- 16bpc: TIFF または EXR を優先
- 32bpc: EXR など float-preserving format が必須

32bpc では、最近ようやく AE 25.2x131、Software、32bpc、1920x1080、FLOAT EXR の Windows 48 ケースを検証可能な形で受け入れた。ただし、その参照を受け取れたことと、Mac プラグインが exact であることは別である。最初のMac候補比較は、入力画像の世代と解像度が揃っておらず無効だった。その後、Windows returnに含まれる `before_effects EXR` を同じ入力として再レンダーしたが、ColorKey case 0001 は Windows の `0.972549...` に対して Mac が `0.988469...` となり、まだ `AE exact` ではない。現時点では、プラグイン本体の差分と、32bpcのリニアライト／カラーマネジメント設定差を切り分けている段階である。

## 6. プラグインごとの現在地

### OLMBlur

alpha が完全透明でない領域を対象にする blur。Color Key と組み合わせた境界処理、repeat、bias、legacy、writer の丸めが主な論点。既存の exact ケースを壊さず、16/32bpc と residual の provenance を狭く確認する。

### OLMColorKey

core の keying、color space、replace は比較的整理できている。難所は Edge Thin / Edge Blur と距離・matte 処理。公式説明にある RGB、HSV、Lab、YUV、YCrCb や Force Lower Precision は機能の意味を絞る助けになるが、丸めや境界条件の証明にはならない。

### OLMToonDilate

透明領域へ非透明ピクセルを広げる処理。Search Radius という単一パラメータからも、伝播順序、距離 metric、半透明 RGB と premultiply の扱いが重要だと分かる。比較的、静的解析と狭いケースで閉じやすい。

### OLMDistanceGradation

alpha mask の内外距離、threshold、interpolation、blur、background/layer の組み合わせ。16bpc では深度ごとに source mask の判定が異なることが判明し、1-code fringe を除外する depth gate が改善につながった。OpenCV field preparation、distance transform、store/export の境界が残る。

### OLMSmoother / OLMSmoother2

セル画の線を滑らかにする処理。Smoother2 は gamma、color space、diagonal、32-bit 対応を含む。no-key と legacy/key/gamma は分けて扱う。v1 を v2 に曖昧に混ぜず、最後に独立互換として残すか、明示的な mapping を採用するか決める。

### OLMDirectionalBlur

通常の Gaussian blur ではなく、opaque pixel group、front/back strength、size variation、edge fade、sharp tail、noise を含む方向性処理。angle-0 と diagonal を一つの証拠に混ぜず、source、direction、validity、denominator、A/B writeback を別々に確認する。

### OLMRadialBlur

Zoom と Rotation、Outer と Inner、center、ellipse ratio/angle、quality、repeat border を分ける必要がある。極座標変換、sampler、prepass、span、writeback が核心で、広い PNG 探索より typed runtime witness が有効。hook の命令位置を間違えやすい代表例でもある。

### OLMKiraKira

alpha/luminance/RGB などからハイライトを抽出し、縦・横・斜めの blur、色や ramp、merge を組み合わせる。Box、Approximate Gaussian、Gaussian、Exponential の primitive 差が大きく、最後の難物として binary/runtime proof を優先する。

## 7. 現在の標準ワークフロー

1. 公式マニュアルと UI から、エフェクトの意図と feature slice を定義する。
2. Ghidra、objdump、文字列、PiPL、ソースから、パラメータと内部分岐を調べる。
3. `BINARY_GROUNDED_IR` に、確定事項・推測・未知を分けて記録する。
4. Windows の Software render で、同じ case ID、入力、パラメータを取得する。
5. 必要なら、広い画像セットではなく、仮説を分ける狭い runtime trace を依頼する。
6. Mac 側で C++ 実装、CLI harness、必要なら AEX CPU simulator を使って検証する。
7. Mac AE で同じ条件を render queue から出し、8/16/32bpc の比較器で判定する。
8. 差分が残れば、画像を直接合わせず、IR の丸め・境界・channel・writer に戻る。
9. 受け取った zip は、要求した witness が本当に入っているかを検査し、partial は proof に昇格させない。

Windows と Mac の handoff は NAS の `new` / `old` 運用に寄せて、active request と処理済み archive を分ける。ファイル名には日付、用途、対象プラグイン、bit depth、return/failed の区別を含める。

## 8. 失敗から得た実務上の教訓

- `ADBE Force CPU GPU` のような名前の分かりやすい値を、実行経路の証拠だと思わない。
- PNG の max diff が小さくても、reference の renderer、解像度、bit depth、AEX 世代が違えば比較は無効。
- 参照画像の provenance はアルゴリズム実装と同じくらい重要。
- breakpoint が発火したことと、欲しい変数がその地点で有効なことは別。
- 5 番目以降の Win x64 引数、XMM float、ARGB、AE 16-bit promotion は最初に検証する。
- runtime trace は広く取るほど良いわけではない。仮説を二分できる最小 witness が最も価値を持つ。
- OpenCV のような既知ライブラリは detour できるが、プラグイン固有の判断ロジックまで置き換えてはいけない。
- 「59/70 exact」のような集計は、対象範囲、reference kind、runner kind、bit depth を伴わないと誤解を生む。
- subagent の結果は、報告文ではなくファイル実在、コマンド、実行結果、evidence classification で受け入れる。
- 古い reference と新しい AEX の output が違う場合、まず「実装が悪い」と決めず、reference-generation split や supersession を確認する。

## 9. 現時点の結論

プロジェクトは、いくつかの feature/depth slice で AE exact の証拠を持つ一方、プラグイン全体の移植完了にはまだ至っていない。特に 32bpc は float-preserving な Windows 参照を整備できた段階であり、全プラグインの Mac AE exact を意味しない。

今後の作業は、未解決の hard path を広い画像探索で埋めることではなく、次の順序で進める。

- canonical Windows Software reference の維持
- 8/16/32bpc の typed manifest と比較器
- feature/path 単位の binary-grounded IR
- RadialBlur / DirectionalBlur / Smoother2 / KiraKira の狭い witness
- 既存 exact slice の回帰防止
- 最後に、全 declared row が `AE exact` になったことの release gate

この「画像差分から仕様を推測する」プロジェクトは、最終的には「参照経路、バイナリ事実、ホスト動作、出力比較を別々に証明し、それを統合する」プロジェクトへ変わった。そこが、この移植作業から後年に再利用できる最大のノウハウである。

## 関連資料

- `notes/PORTING_ROADMAP.md` — 全体スコープ、完了条件、優先順位
- `notes/AE_EXACT_CONFORMANCE.md` — exactness と bit depth の定義
- `notes/PLUGIN_INTENT_MAP.md` — 公式説明と feature 分解
- `notes/FORECAST_FIRST_PORTING_POLICY.md` — Windows 返却待ちの進め方
- `notes/BINARY_GROUNDED_IR_TEMPLATE.md` — 仕様 IR のテンプレート
- `notes/WINDOWS_DENSE_TRACE_STRATEGY.md` — runtime trace の依頼契約
- `tools/emulation/OPENCV_DETOUR_DESIGN.md` — AEX CPU simulation の高速化設計
- `tools/emulation/GOTCHAS.md` — ABI、AE pixel layout、bit depth の注意点
- `refs/conformance/olm_release_scope_evidence_audit_20260710.md` — 現時点の過大主張と未完了範囲の監査

## ブログ化するときの構成案

1. 「PNG を合わせれば移植できる」と考えたところから始める
2. GPU/CPU、bit depth、AE state の罠に遭遇する
3. Ghidra/objdump で binary-grounded IR を作る
4. CDB runtime trace と AEX CPU simulator を導入する
5. OpenCV detour で重い処理を短縮する
6. 失敗した trace と invalid reference を公開する
7. AE exact を release gate にした理由
8. Mac 移植で再利用できるチェックリスト

検索語候補: After Effects AEX reverse engineering、Ghidra、Apple Silicon、Unicorn、CDB、OpenEXR、bit depth、binary-grounded porting、runtime trace、OpenCV detour。

> 注意: この文書は 2026-07-10 時点の会話履歴とリポジトリ内資料から作った中間ブリーフである。後続の accepted intake、ledger、verification report がこの文書と異なる場合は、後続資料を優先して更新する。
