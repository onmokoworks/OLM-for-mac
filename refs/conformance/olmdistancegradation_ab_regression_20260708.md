# OLMDistanceGradation A/B Regression - 2026-07-08

## 結論

FACT: 参照PNGとの優劣判定は行わず、HEAD版(old)と未コミット変更入り現行版(new)の出力PNG同士だけを比較した。45ケース中43ケースで old/new 差分が出た。差分ゼロは `8bpc/case_0029` と `16bpc/olmdistancegradation_extended__case_0008` の2件。

FACT: 差分43ケースについて、HEAD版に a/b/c を単独適用した中間ビルドを実行した。a (`source_mask_owns_alpha` しきい値) は43ケースすべてで old から差分を発生させ、かつ a単独出力は new 出力と全ピクセル一致した。b (`dt_to_normalized` denom) と c (`Both-combine max→min(add)`) は、この43ケースでは old から差分ゼロだった。

INFERENCE: この45ケースセットで観測された new の影響は a (`source_mask_owns_alpha` しきい値) のみで説明できる。したがって「差分ゼロ = case_0023 系以外に影響なし」ではなく、影響ケースは下表の43件。b/c は今回の入力/パラメータ集合では出力に影響しなかった。

## 手法

FACT: 8bpc は `refs/win_references/20260605_extra/OLMDistanceGradation/reference_manifest.json` のDG 29ケース (`case_0001`-`case_0029`) を使用した。16bpc は `refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/reference_manifest.json` の `olmdistancegradation_extended__*` 16ケースを使用した。

FACT: PNGファイルは入力画像としてのみ使用した。判定は `/tmp/olmdg_ab_old/*.png` と `/tmp/olmdg_ab_new/*.png` の同名出力PNG同士の per-case 比較で行った。

FACT: AE SDKヘッダが作業ツリーに無いため、`mac/OLMDistanceGradation/OLMDistanceGradation.cpp` の該当アルゴリズム(EDT/blur/compose)に対応する一時C++ CLIを `/tmp/olmdg_cpp_work/olmdg_core.cpp` として作り、old/new/a/b/c をプリプロセッサスイッチでビルドした。PNG I/OだけはPythonでraw RGBAへ変換し、アルゴリズム実行はC++バイナリで行った。

## 実行コマンドと出力

```console
$ git diff -- mac/OLMDistanceGradation/OLMDistanceGradation.cpp | shasum -a 256
648df3c56881bb55a79b2003c80ed372d8c16457bc3a1b665f0471f938157b79  -

$ shasum -a 256 mac/OLMDistanceGradation/OLMDistanceGradation.cpp
bd9a82702685465f150f6b616d0bf5b8acd0cad521565c83f600c1e82fb9ba30  mac/OLMDistanceGradation/OLMDistanceGradation.cpp
$ git show HEAD:mac/OLMDistanceGradation/OLMDistanceGradation.cpp | shasum -a 256
fcea8bf78724a1e2f0a84e293196f31ebbbb4c6a977bca918ca38252bd43cbda  -

$ clang++ -std=c++17 -O2 /tmp/olmdg_cpp_work/olmdg_core.cpp -o /tmp/olmdg_cpp_work/olmdg_old
$ clang++ -std=c++17 -O2 -DDG_THRESHOLD_MODE=1 -DDG_DENOM_MODE=1 -DDG_BOTH_MODE=1 /tmp/olmdg_cpp_work/olmdg_core.cpp -o /tmp/olmdg_cpp_work/olmdg_new
$ clang++ -std=c++17 -O2 -DDG_THRESHOLD_MODE=1 /tmp/olmdg_cpp_work/olmdg_core.cpp -o /tmp/olmdg_cpp_work/olmdg_a
$ clang++ -std=c++17 -O2 -DDG_DENOM_MODE=1 /tmp/olmdg_cpp_work/olmdg_core.cpp -o /tmp/olmdg_cpp_work/olmdg_b
$ clang++ -std=c++17 -O2 -DDG_BOTH_MODE=1 /tmp/olmdg_cpp_work/olmdg_core.cpp -o /tmp/olmdg_cpp_work/olmdg_c
$ ls -l /tmp/olmdg_cpp_work/olmdg_*
-rwxr-xr-x ... /tmp/olmdg_cpp_work/olmdg_a
-rwxr-xr-x ... /tmp/olmdg_cpp_work/olmdg_b
-rwxr-xr-x ... /tmp/olmdg_cpp_work/olmdg_c
-rwxr-xr-x ... /tmp/olmdg_cpp_work/olmdg_new
-rwxr-xr-x ... /tmp/olmdg_cpp_work/olmdg_old

$ python3 /tmp/olmdg_cpp_work/run_cpp_ab.py
{
  "case_count": 45,
  "changed_count": 43,
  "start_diff_hash": "648df3c56881bb55a79b2003c80ed372d8c16457bc3a1b665f0471f938157b79",
  "end_diff_hash": "648df3c56881bb55a79b2003c80ed372d8c16457bc3a1b665f0471f938157b79"
}

$ python3 - <<'PY'  # a/b/c vs new追加確認
a vs_new_nonzero_px_total 0 max_diff 0 mean_sum 0.0
b vs_new_nonzero_px_total 112671 max_diff 254 mean_sum 0.13783227237654322
c vs_new_nonzero_px_total 112671 max_diff 254 mean_sum 0.13783227237654322
PY

$ git diff -- mac/OLMDistanceGradation/OLMDistanceGradation.cpp | shasum -a 256
648df3c56881bb55a79b2003c80ed372d8c16457bc3a1b665f0471f938157b79  -
```

FACT: フルログは `/tmp/olmdg_cpp_work/commands.log`、機械可読結果は `/tmp/olmdg_cpp_work/report.json`。一時C++ CLIハッシュ: core `bb2d92d229c3c3917828c9a7c9e4657db6126794311676acc28cdafd18703861`, old `010439f32dd84270e4d49dabd6be7bfcff5e5a8e1d33ef6c80546f59bd171912`, new `e7d42e68947528b4acc64e81ff305440d17ba9909ad5ab0ee0ddde2ad7a4a17c`, a `3123063a67f7829c2dd6701b8582715d6417f54d503459bb4773093f34f61d9b`, b `bc04053bc9e4d4488cee1f5610461958d838a9616761fa1f65f571c80d7d97f1`, c `76ccb153df230b2778e6a32d223abc2f258bd68bee41293cea496ca9351b7739`。

## Per-Case old vs new

| case | nonzero_px | max_diff | mean |
|---|---:|---:|---:|
| `8bpc/case_0001` | 993 | 2 | 0.000242573 |
| `8bpc/case_0002` | 993 | 2 | 0.000242573 |
| `8bpc/case_0003` | 65 | 1 | 0.000015673 |
| `8bpc/case_0004` | 275 | 1 | 0.000066310 |
| `8bpc/case_0005` | 978 | 6 | 0.000595341 |
| `8bpc/case_0006` | 349 | 1 | 0.000084153 |
| `8bpc/case_0007` | 6797 | 6 | 0.004306520 |
| `8bpc/case_0008` | 65 | 254 | 0.003980999 |
| `8bpc/case_0009` | 6797 | 6 | 0.004306520 |
| `8bpc/case_0010` | 8611 | 6 | 0.004720534 |
| `8bpc/case_0011` | 431 | 254 | 0.004069252 |
| `8bpc/case_0012` | 7871 | 6 | 0.002406081 |
| `8bpc/case_0013` | 1875 | 3 | 0.000541932 |
| `8bpc/case_0014` | 322 | 1 | 0.000077763 |
| `8bpc/case_0015` | 319 | 1 | 0.000078848 |
| `8bpc/case_0016` | 65 | 1 | 0.000007837 |
| `8bpc/case_0017` | 1543 | 2 | 0.000402802 |
| `8bpc/case_0018` | 1564 | 2 | 0.000205440 |
| `8bpc/case_0019` | 2093 | 2 | 0.000359279 |
| `8bpc/case_0020` | 1 | 238 | 0.000056062 |
| `8bpc/case_0021` | 1 | 238 | 0.000056062 |
| `8bpc/case_0022` | 192 | 238 | 0.010763889 |
| `8bpc/case_0023` | 73 | 238 | 0.004092520 |
| `8bpc/case_0024` | 5937 | 80 | 0.008384693 |
| `8bpc/case_0025` | 5702 | 65 | 0.006615910 |
| `8bpc/case_0026` | 4791 | 45 | 0.010349392 |
| `8bpc/case_0027` | 4491 | 48 | 0.005654779 |
| `8bpc/case_0028` | 4558 | 58 | 0.003681641 |
| `8bpc/case_0029` | 0 | 0 | 0.000000000 |
| `16bpc/olmdistancegradation_extended__case_0008` | 0 | 0 | 0.000000000 |
| `16bpc/olmdistancegradation_extended__case_0010` | 8611 | 6 | 0.004720534 |
| `16bpc/olmdistancegradation_extended__case_0011` | 431 | 254 | 0.004069252 |
| `16bpc/olmdistancegradation_extended__case_0012` | 7871 | 6 | 0.002408854 |
| `16bpc/olmdistancegradation_extended__case_0013` | 1875 | 3 | 0.000539280 |
| `16bpc/olmdistancegradation_extended__case_0014` | 318 | 1 | 0.000076678 |
| `16bpc/olmdistancegradation_extended__case_0016` | 65 | 1 | 0.000007837 |
| `16bpc/olmdistancegradation_extended__case_0020` | 1 | 238 | 0.000056062 |
| `16bpc/olmdistancegradation_extended__case_0021` | 1 | 238 | 0.000056062 |
| `16bpc/olmdistancegradation_extended__case_0022` | 192 | 238 | 0.010763889 |
| `16bpc/olmdistancegradation_extended__case_0023` | 73 | 238 | 0.004092520 |
| `16bpc/olmdistancegradation_extended__case_0024` | 5937 | 80 | 0.008384693 |
| `16bpc/olmdistancegradation_extended__case_0025` | 5702 | 65 | 0.006615910 |
| `16bpc/olmdistancegradation_extended__case_0026` | 4791 | 45 | 0.010349392 |
| `16bpc/olmdistancegradation_extended__case_0027` | 4491 | 48 | 0.005654779 |
| `16bpc/olmdistancegradation_extended__case_0028` | 4560 | 57 | 0.003671152 |

## 変更別帰属

FACT: 下表は差分43ケースだけを対象に、old vs a/b/c 単独変更出力を比較した実測値。

| case | a nonzero/max/mean | b nonzero/max/mean | c nonzero/max/mean | attribution |
|---|---:|---:|---:|---|
| `8bpc/case_0001` | 993/2/0.000242573 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0002` | 993/2/0.000242573 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0003` | 65/1/0.000015673 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0004` | 275/1/0.000066310 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0005` | 978/6/0.000595341 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0006` | 349/1/0.000084153 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0007` | 6797/6/0.004306520 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0008` | 65/254/0.003980999 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0009` | 6797/6/0.004306520 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0010` | 8611/6/0.004720534 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0011` | 431/254/0.004069252 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0012` | 7871/6/0.002406081 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0013` | 1875/3/0.000541932 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0014` | 322/1/0.000077763 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0015` | 319/1/0.000078848 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0016` | 65/1/0.000007837 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0017` | 1543/2/0.000402802 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0018` | 1564/2/0.000205440 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0019` | 2093/2/0.000359279 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0020` | 1/238/0.000056062 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0021` | 1/238/0.000056062 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0022` | 192/238/0.010763889 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0023` | 73/238/0.004092520 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0024` | 5937/80/0.008384693 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0025` | 5702/65/0.006615910 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0026` | 4791/45/0.010349392 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0027` | 4491/48/0.005654779 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `8bpc/case_0028` | 4558/58/0.003681641 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `16bpc/olmdistancegradation_extended__case_0010` | 8611/6/0.004720534 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `16bpc/olmdistancegradation_extended__case_0011` | 431/254/0.004069252 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `16bpc/olmdistancegradation_extended__case_0012` | 7871/6/0.002408854 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `16bpc/olmdistancegradation_extended__case_0013` | 1875/3/0.000539280 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `16bpc/olmdistancegradation_extended__case_0014` | 318/1/0.000076678 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `16bpc/olmdistancegradation_extended__case_0016` | 65/1/0.000007837 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `16bpc/olmdistancegradation_extended__case_0020` | 1/238/0.000056062 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `16bpc/olmdistancegradation_extended__case_0021` | 1/238/0.000056062 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `16bpc/olmdistancegradation_extended__case_0022` | 192/238/0.010763889 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `16bpc/olmdistancegradation_extended__case_0023` | 73/238/0.004092520 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `16bpc/olmdistancegradation_extended__case_0024` | 5937/80/0.008384693 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `16bpc/olmdistancegradation_extended__case_0025` | 5702/65/0.006615910 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `16bpc/olmdistancegradation_extended__case_0026` | 4791/45/0.010349392 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `16bpc/olmdistancegradation_extended__case_0027` | 4491/48/0.005654779 | 0/0/0.000000000 | 0/0/0.000000000 | a only |
| `16bpc/olmdistancegradation_extended__case_0028` | 4560/57/0.003671152 | 0/0/0.000000000 | 0/0/0.000000000 | a only |

## 作業ツリー確認

FACT: 終了時の `git diff -- mac/OLMDistanceGradation/OLMDistanceGradation.cpp | shasum -a 256` は `648df3c56881bb55a79b2003c80ed372d8c16457bc3a1b665f0471f938157b79` で、開始時および指定値と一致した。

FACT: `notes/CONFORMANCE_LEDGER.md` はこのタスクでは変更していない。
