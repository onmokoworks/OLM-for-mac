status: done
summary:
- Added Japanese release notes and their English translation, with bounded results from merged reports.
- Packaged both languages, READMEs, installation/support/limitations docs and LICENSE; repaired packaged relative links.
- Built ten Release bundles; audited Universal slices, macOS 11.0 minimums, ad-hoc signatures, docs and nested ZIP text.
- Retained an unpublished ZIP in the local durable cache and registered release-R11 in INDEX.json.
- No plugin source, release gate, ledger, MAIN, tag or remote release changed.

facts:
- Baseline: `ebd38e6ced3fd034e6091fbaea1a6ff33fcfa483`; branch `orch/R11-release-package-and-notes`.
- ZIP source identity: `eb9baef7ac9a3361df68e09c4c489e0a8ec6c4aa`; manifest `git_dirty=false`, configuration Release. Later ticket commits contain only audit/report evidence. No `core/` or `mac/` diff from baseline.
- Durable ZIP: `/Users/onmk/.cache/olm-emu/release-R11/OLM_Mac_Plugins_Release_20261026.zip`
- Worktree ZIP: `orchestra/state/R11-release-package-and-notes/OLM_Mac_Plugins_Release_20261026.zip`
- SHA-256: `5bd1481f98124ac3187fdf76791b0a4e97ee720db00fc7000ac6d8fd4de60418`
- `bash orchestra/reports/R11-evidence/build.sh > orchestra/state/R11-release-package-and-notes/package-build.log 2>&1`: all ten Xcode builds succeeded and passed build-time slice/minos/signature verification. The initial packaging stage then exited 1 because the worktree lacked untracked reference assets. The committed recipe now sets OLM_REFERENCE_ROOT to MAIN and limits Xcode to one job. The existing builder's Release mode uses its documented Debug-project configuration with optimization overrides; this ticket does not change that build policy.
- Final packaging command: `TMPDIR="$PWD/orchestra/state/R11-release-package-and-notes" OLM_REFERENCE_ROOT='/Users/onmk/Documents/Projects/Personal/OLM as' scripts/package_mac_plugins.sh --configuration Release --skip-build --output "$PWD/orchestra/state/R11-release-package-and-notes/OLM_Mac_Plugins_Release_20261026.zip"`, exit 0. This reused the ten bundles just built and verified in this session. Plugin/build inputs were unchanged between the build and final package commit.
- First extra text audit found six Windows project paths in nested reference manifests. The request packager now ships only the project filename. Original reference files were read, never edited. Final audit: 76 UTF-8 text files, six nested ZIPs, zero machine-local absolute paths. Portable home-relative installation targets and generic `/path/to` examples are not author-machine paths.
- `python3 orchestra/reports/R11-evidence/check-reference-payloads.py orchestra/state/R11-release-package-and-notes/OLM_Mac_Plugins_Release_20261026.zip '/Users/onmk/Documents/Projects/Personal/OLM as'`: six reference manifests differ only in `project.path`; all 96 PNG payloads unchanged. Legacy validation thresholds were not changed and are not used as bit-exact evidence in the new notes.
- `python3 orchestra/reports/R11-evidence/verify.py /Users/onmk/.cache/olm-emu/release-R11/OLM_Mac_Plugins_Release_20261026.zip`: exit 0; ten bundles, exactly arm64+x86_64, both minos 11.0, `codesign -dv --verbose=4` reports `Signature=adhoc`, and `codesign --verify --deep --strict` passes for each. Binary hashes and architecture/minos/signing manifest fields agree. All public Markdown links resolve within the ZIP. Both canonical note files equal the committed documents. The old August release-note file is absent.
- ZIP contains 132 entries. Complete listing: [R11-evidence/zip-contents.txt](R11-evidence/zip-contents.txt). Per-binary hashes: [R11-evidence/package-audit.json](R11-evidence/package-audit.json). Build log: [R11-evidence/package-build.log.gz](R11-evidence/package-build.log.gz). Final packaging/audit logs are retained beside them.
- Japanese proofreading ran the requested `python3 ~/.claude/skills/yomiyasu/scripts/yomiyasu_check.py run --source orchestra/reports/R11-evidence/draft-ja.md --final docs/RELEASE_NOTES_JA.md --doc-type manual --reader general`, with YOMIYASU_STATE_DIR set to ticket scratch (the executed source was the byte-identical scratch draft). Removed two unnecessary commas, then reran run and `verify --final docs/RELEASE_NOTES_JA.md`. Lint/diff and final hash verification completed; meaning_risk=0. Four remaining candidates are literal image-resolution terminology and a comparison-frame comma before a separate subject. No technical fact was changed by proofreading. Logs retain exact commands' output. These checks do not certify prose quality or factual correctness.
- Cleanup: regenerable Xcode intermediates were removed by the builder; this ticket's ten Release product directories were deleted after retaining the ZIP. Scratch is below 5 GiB. Both build/package sessions ended; no task-owned background process remains. No emulator worker was rebuilt.

Evidence used for the notes (merged at baseline):

| Claim | Report and measured boundary |
|---|---|
| Original AEX comparison | V01: 1,854 exact/2,000; 146 non-renders, including 70 unsupported PF32 and 76 oracle failures |
| Slice equivalence | V01: 3,560 cases, 8,171 rendered pairs and 373 refusal pairs; zero differences; x86_64 under Rosetta |
| Real AE across depths/resolutions | A02h: 132 historical 8bpc outputs, 107/120 effect images exact; 176 depth outputs, 136/160 exact; ColorKeep straight-PNG 4/4 |
| Preview/partial-render fixes | P02h: 200 Blur Smart exact; P04b2: four cropped refusals become exact |
| UI | U02b: 159 dispatches; U04: 2,642 state/reconstruction checks; native visual/reload scope remains incomplete |
| Performance | P05a: 1080p heavy DirectionalBlur 17.75–18.32 s to 1.38–1.43 s; P07a: Kira default 1.59–1.73x; SDK-host measurements |
| Remaining AE boundaries | A02h, S01, S02: export/host boundaries, two Smoother 4K samples, Smoother2 real-AE retest pending |

Plugin names/environment and license language follow the explicit ticket and current README; numerical verification/change claims come only from merged reports. Reports marked blocked/partial are cited for their measured subsets, never promoted to complete acceptance.

inference:
- Packaging and documentation acceptance for R11 is complete. Historical conformance results describe their recorded binaries and cases, not a new all-input or real-Windows-AE guarantee for this ZIP.
- The package remains Beta. Real AE limitations and incomplete oracle cases remain follow-up work; this documentation ticket does not adjudicate them.

changed_files:
- docs/RELEASE_NOTES_JA.md
- docs/RELEASE_NOTES_EN.md
- scripts/package_mac_plugins.sh
- scripts/package_ae_pixel_validation_request.py
- orchestra/reports/R11-evidence/ (build recipe, ZIP verifier, reference-payload check, draft, logs, listing, audit)
- orchestra/reports/R11-release-package-and-notes.md
- Local durable artifact only: ~/.cache/olm-emu/release-R11/ and INDEX.json release-R11 registration (not repository files).

verify:
Run from this worktree:

```sh
mkdir -p orchestra/state/R11-release-package-and-notes
export TMPDIR="$PWD/orchestra/state/R11-release-package-and-notes"
python3 orchestra/reports/R11-evidence/verify.py /Users/onmk/.cache/olm-emu/release-R11/OLM_Mac_Plugins_Release_20261026.zip
python3 orchestra/reports/R11-evidence/check-reference-payloads.py /Users/onmk/.cache/olm-emu/release-R11/OLM_Mac_Plugins_Release_20261026.zip '/Users/onmk/Documents/Projects/Personal/OLM as'
shasum -a 256 /Users/onmk/.cache/olm-emu/release-R11/OLM_Mac_Plugins_Release_20261026.zip
bash -n scripts/package_mac_plugins.sh
git diff --check
```

Expected: audit PASS for ten bundles, 76 text files/six nested ZIPs/no local paths; reference payload PASS for six manifests/96 PNGs; SHA-256 above; shell and diff checks exit 0.

Full rebuild: `bash orchestra/reports/R11-evidence/build.sh > "$TMPDIR/rebuild.log" 2>&1`, expected exit 0 and ten verified bundles. This requires the existing AE SDK and MAIN's untracked reference assets. Build/package timestamps and source commit metadata mean a rebuilt ZIP need not have the retained ZIP hash. Re-run the audit against the new ZIP; remove generated product/intermediate directories afterward.

Proofreading recheck:

```sh
export YOMIYASU_STATE_DIR="$TMPDIR/yomiyasu-recheck"
python3 ~/.claude/skills/yomiyasu/scripts/yomiyasu_check.py run --source orchestra/reports/R11-evidence/draft-ja.md --final docs/RELEASE_NOTES_JA.md --doc-type manual --reader general
python3 ~/.claude/skills/yomiyasu/scripts/yomiyasu_check.py verify --final docs/RELEASE_NOTES_JA.md
```

Expected: lint/diff executed, meaning_risk=0, verify reports matching final hash. Remaining vocabulary candidates refer literally to image resolution.

next:
- Orchestrator review/merge only; no publishing was requested or performed.
- Follow up on the recorded native-AE export/callback-depth, Smoother 4K and Smoother2 retest boundaries in their existing tickets. No new pixel fix is inferred from this packaging run.

## Notes text — Japanese

# OLM for Mac リリースノート

2026年10月版・Beta

[English](RELEASE_NOTES_EN.md)

Windows版のAfter Effectsプラグイン「OLM Tools」をMacへ移植した非公式版です。Apple Silicon用とIntel用を1つにまとめたUniversalバイナリで、macOS 11以降に対応します。実際のAEでの確認にはAfter Effects 2026を使いました。

## 同梱プラグイン

ColorKeep、OLMBlur、OLMColorKey、OLMDirectionalBlur、OLMDistanceGradation、OLMKiraKira、OLMRadialBlur、OLMSmoother、OLMSmoother2、OLMToonDilateの10本です。

OLMSmootherは8／16 bpcに対応します。ほかの9本は8／16／32 bpcに対応します。

## 8月のBeta版からの変更

- プレビュー解像度を下げたときや、画像の一部だけを描くときに、描画を拒否して黒いフレームになる問題を修正しました。画像の範囲、原点、ぼかし幅の扱いを元のWindows版に合わせています。OLMBlurの範囲処理の検証では200件が一致し、OLMDirectionalBlurの切り出し画像4件も、描画拒否からビット単位の一致に変わりました（P02h、P04b2）。すべての黒い画像が不具合とは限らず、設定によって透明や黒になる場合は残ります。
- KiraKiraのグラデーション編集と、設定に応じて項目を隠したり無効にしたりする処理を修正しました。元のプラグインとの比較では、編集操作など159回と、項目の状態・復元2,642件が一致しました（U02b、U04）。実AEでの見た目や保存後の再読み込みはまだ確かめきれていません。
- 重い処理を高速化しました。DirectionalBlurの重い設定では、1080pの処理時間が17.75〜18.32秒から1.38〜1.43秒へ短くなりました。KiraKiraの既定設定では1.59〜1.73倍の速度になりました（P05a、P07a）。Macの検証用ホストで測った値で、AEでの処理時間やすべての設定での速度を保証するものではありません。

## 検証結果

元のWindows版 `.aex` をUnicornエミュレーターで動かし、同じ入力と設定から出た画素と描画範囲を比べています。1ビットでも違えば一致に数えません。以下はマージ済みレポートに記録された測定結果です。今回のZIPで全件を再実行した結果ではありません。

- 元のプラグインとの比較：V01の2,000件中1,854件で、Intel用バイナリの画素と描画範囲が一致しました。残る146件は元のプラグインが描画できず、比較できませんでした。内訳はOLMSmootherの32 bpc非対応70件と、元のプラグインやエミュレーターの実行失敗76件です。
- Apple Silicon用とIntel用の比較：V01の3,560件で8,171組の描画結果が一致し、373組の描画拒否も一致しました。画素・範囲の差は0件でした。1080p／4K、8／16／32 bpcの重い設定60件を含みます。Intel用はRosettaで動かしており、Intel Mac実機での測定ではありません。
- 実AEでの描画：10本をフル／1/2／1/3／1/4解像度で確認しました。A02hが集計した8 bpcの試験は132出力、16／32 bpcの試験は176出力を生成しました。エフェクト付き画像の比較では、それぞれ120件中107件、160件中136件が元のプラグインと一致しました。解像度を下げた比較には、エフェクトなしで書き出した画像を入力の代わりに使う制約があります。

実AEの残りには、透明画素のRGBが書き出し時に失われる差、OLMSmootherの32 bpc参照不足、4K画像の2サンプルの差があります。ColorKeepの8 bpcは透明画素のRGBを保つPNGで4解像度とも一致しました。Smoother2の別の実AE試験で見つかった描画拒否はソースを修正済みですが、実AEでの再確認は未完了です（A02h、S01、S02）。全入力の一致や、Windows版AEで書き出したファイルとの一致は確認していません。

## 制限とインストール

GPUレンダーには対応していません。RadialBlurの高品質な回転ぼかしなど、処理に時間がかかる設定もあります。[既知の制限](../KNOWN_LIMITATIONS.md)を確認してください。

AEを終了してから、ZIP内の10個の `.plugin` をMediaCoreフォルダーへコピーしてください。[インストールガイド](INSTALL_JA.md)に手順とGatekeeperへの対処をまとめています。バイナリにはアドホック署名があり、AppleのDeveloper ID署名と公証はありません。

## ライセンス

元のOLMプラグインのApache License 2.0を継承しています。本文は[LICENSE](../LICENSE)にあります。OLM Digitalとは関係のない非公式の移植です。

## Notes text — English

# OLM for Mac release notes

October 2026 · Beta

[日本語](RELEASE_NOTES_JA.md)

This is an unofficial Mac port of OLM Tools, the Windows After Effects plugins. Each Universal binary contains Apple Silicon and Intel code and supports macOS 11 or later. Real AE checks used After Effects 2026.

## Included plugins

The package contains ten plugins: ColorKeep, OLMBlur, OLMColorKey, OLMDirectionalBlur, OLMDistanceGradation, OLMKiraKira, OLMRadialBlur, OLMSmoother, OLMSmoother2, and OLMToonDilate.

OLMSmoother supports 8/16 bpc. The other nine support 8/16/32 bpc.

## Changes since the August beta

- Fixed render refusals that produced black frames at reduced preview resolutions or when rendering part of an image. Image bounds, origins, and blur widths now follow the original Windows behavior. OLMBlur's bounds checks matched in 200 cases; four cropped-image DirectionalBlur cases changed from refusals to bit-exact matches (P02h, P04b2). Black images are not always bugs: some settings still produce transparent or black output.
- Fixed KiraKira gradient editing and the controls that become hidden or disabled depending on settings. Comparisons with the original matched 159 editing and related dispatches and 2,642 control-state/reconstruction checks (U02b, U04). Appearance in real AE and saved-project reloads are not yet fully verified.
- Sped up expensive processing. A heavy DirectionalBlur setting at 1080p fell from 17.75–18.32 seconds to 1.38–1.43 seconds. KiraKira's default setting ran 1.59–1.73 times as fast (P05a, P07a). These measurements used a Mac test host; they do not guarantee AE timings or speedups for every setting.

## Verification

We run the original Windows `.aex` in the Unicorn emulator and compare pixels and render bounds for identical inputs and settings. A one-bit difference fails the comparison. The following measurements come from merged reports. They are not a complete rerun against this ZIP.

- Original-plugin comparison: in V01, the Intel binary matched pixels and bounds in 1,854 of 2,000 cases. The original did not render in the other 146 cases, so they could not be compared: 70 unsupported OLMSmoother 32 bpc cases and 76 original-plugin or emulator execution failures.
- Apple Silicon versus Intel: across 3,560 V01 cases, 8,171 rendered pairs matched, as did 373 refusal pairs. There were zero pixel or bounds differences. This included 60 heavy cases at 1080p/4K and 8/16/32 bpc. Intel code ran under Rosetta, not on a physical Intel Mac.
- Real AE renders: all ten plugins were checked at Full/Half/Third/Quarter resolution. The 8 bpc campaign summarized by A02h produced 132 outputs; the 16/32 bpc campaign produced 176. Among images with effects, 107 of 120 and 136 of 160 respectively matched the original plugin. Reduced-resolution comparisons use no-effect exports as input proxies.

The remaining real-AE comparisons include loss of RGB under transparent pixels during export, unavailable OLMSmoother 32 bpc references, and a two-sample difference in a 4K image. ColorKeep at 8 bpc matched at all four resolutions when exported to PNG preserving hidden RGB. A separate real-AE Smoother2 refusal has a source fix, but the real-AE retest is still incomplete (A02h, S01, S02). Equality for every input, or with files exported by Windows AE, has not been established.

## Limitations and installation

GPU rendering is unsupported. Some settings remain slow, including high-quality RadialBlur rotation. See [known limitations](../KNOWN_LIMITATIONS.en.md).

Quit AE, then copy the ten `.plugin` bundles from the ZIP into MediaCore. The [installation guide](INSTALL_EN.md) covers the steps and Gatekeeper. Binaries are ad-hoc signed, without Apple Developer ID signing or notarization.

## License

The port inherits the original OLM plugins' Apache License 2.0. See [LICENSE](../LICENSE). This is an unofficial port, unaffiliated with OLM Digital.
