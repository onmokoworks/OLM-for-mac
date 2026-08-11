# OLM RadialBlur Type 3 PF32 AEXCompat fixture boundary

2026-08-12 に AEXCompat `40c3348c` で、Type 3 witness v2 の PF32 pilot 4ケースを各2回実行した。

Classic fixture は8回すべて完走した。primary world は全行で一致し、Noise Layer の native PF32 checkpoint は pattern と inverse で異なる値を保持したうえで、それぞれrepeat間でbyte一致した。したがって、このfixtureについてprimary／secondary-layer world I/Oと反復決定性は確認できた。

ただしClassic output worldは8行すべて全ゼロだった。Noise Type 1の対照fixtureも全ゼロだったため、これはType 3の算術結果として扱わない。Smart fixtureは8行ともoutput公開前に `render_error: -40` で停止し、Noise Type 1対照も同じ結果だった。

この結果からproductionのType 3をadmitしない。既存のlayer-span helperの局所一致は維持されるが、実AEXのfull-render outputとproduction outputを結ぶ8/8 exact gateは未成立である。PF8／PF16／PF32を含む`RenderWorld`のType 3 fail-closeは変更しない。

Windows AE固有のNoise Layer bindingは、このMac上のAEXCompat world I/O確認とは別の未証明境界である。
