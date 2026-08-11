# OLM RadialBlur Type 3 PF32 AEXCompat fixture boundary

2026-08-12 に AEXCompat `40c3348c` で、Type 3 witness v2 の PF32 pilot 4ケースを各2回実行した。

Classic fixture は8回すべて完走した。primary world は全行で一致し、Noise Layer の native PF32 checkpoint は pattern と inverse で異なる値を保持したうえで、それぞれrepeat間でbyte一致した。したがって、このfixtureについてprimary／secondary-layer world I/Oと反復決定性は確認できた。

ただしClassic output worldは8行すべて全ゼロだった。Noise Type 1の対照fixtureも全ゼロだったため、これはType 3の算術結果として扱わない。Smart fixtureは8行ともoutput公開前に `render_error: -40` で停止し、Noise Type 1対照も同じ結果だった。

この結果からproductionのType 3をadmitしない。既存のlayer-span helperの局所一致は維持されるが、実AEXのfull-render outputとproduction outputを結ぶ8/8 exact gateは未成立である。PF8／PF16／PF32を含む`RenderWorld`のType 3 fail-closeは変更しない。

Windows AE固有のNoise Layer bindingは、このMac上のAEXCompat world I/O確認とは別の未証明境界である。

再実行には `tools/emulation/run_olmradialblur_type3_aexcompat_fixture_20260812.py` を使う。AEXCompat repository、harness、guest worker、AEXは引数で指定できる。runnerは30-slot ParamsSetupからfixtureを再生成し、4ケース×2回のprimary／secondary／output checkpoint、EXR、repeat決定性を検証する。さらに同じnative PF32 worldsをproduction test seamへ渡し、actual outputとのbyte一致まで成立した場合に限ってadmissionをtrueにする。

```sh
python3 tools/emulation/run_olmradialblur_type3_aexcompat_fixture_20260812.py \
  --aexcompat-repo /path/to/AEXCompat \
  --aex plugins_2025/OLMRadialBlur.aex \
  --report /tmp/olmradial-type3-pilot.json
```

既定ではこのboundary JSONの期待statusも読み込む。修正前の全ゼロoutputは正しく`actual_aex_output_gate: fail`、`production_admission: false`として終了コード0で再現される。AEXCompatまたはproductionの修正でstatusが変わった場合は終了コード2となるため、結果を監査してboundaryを更新する。探索目的でstatus差を許可する場合だけ`--allow-status-change`を指定する。
