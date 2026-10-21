# OLMKiraKira Mode 2 Rotation 22° Ramp helper boundary（2026-08-12）

Status: **exact**

Rotation 22°の15 ray wordsをBrightness Gain 0.73でfloat32 scaleし、default Rampとともにactual AEX Mode 2 aggregatorへ直接入力した。Ramp helperを含む15/15 RGBAがportable SSE順序とraw exactで、同じglowをactual AEX PF32 compose/writerへ渡した240 bytesもexact。残るPF32 seamはnatural ownerのstate／実引数からaggregator呼出しまでに局在する。Brightness、plane、flags、Ramp payloadのどれかを確定するにはnatural-entry captureが必要。期待値補正や未証明範囲のpromotionは行わない。
